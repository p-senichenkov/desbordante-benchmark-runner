import typing as tp
from dataclasses import dataclass, field
from pathlib import Path

from ..algo import EPacAlgo
from ..util import capture, build_desbordante

from .statistics import AxisMeta, StatsMeta, PlotStats, process_results
from .algo_meta import ALGO_BUILDERS
from .benchmark_output import UnifiedBenchmarkOutput


def _build_unified_bench(
    algo: EPacAlgo,
    extra_params: list[str],
    dataset_const: str,
    desbordante_root: Path,
) -> Path:
    algo_builder = ALGO_BUILDERS[algo]
    main_text = algo_builder.make_main(dataset_const, extra_params)

    with open(
        desbordante_root / "src" / "tests" / "memory" / "main.cpp", "w"
    ) as main_file:
        main_file.write(main_text)

    return build_desbordante(
        desbordante_root, target="Desbordante.memory_bench"
    )


def _run_unified_bench(build_target: Path) -> UnifiedBenchmarkOutput:
    output = capture(build_target / "Desbordante.memory_bench", cwd=build_target)
    return UnifiedBenchmarkOutput.model_validate_json(output)


@dataclass
class DatasetMeta:
    dataset_const: str
    # Some numeric characteristic of dataset (displayed on axis X)
    num: int


@dataclass
class UnifiedBenchmarksResultsSingleChara:
    before: list[list[float]] = field(default_factory=list)
    after_load: list[list[float]] = field(default_factory=list)
    after_execute: list[list[float]] = field(default_factory=list)


@dataclass
class UnifiedBenchmarksResultsTime:
    load_data: list[list[float]] = field(default_factory=list)
    execute: list[list[float]] = field(default_factory=list)


@dataclass
class UnifiedBenchmarksResults:
    axis_x: list[int] = field(default_factory=list)
    vspace_kb: UnifiedBenchmarksResultsSingleChara = field(
        default_factory=UnifiedBenchmarksResultsSingleChara
    )
    rss_kb: UnifiedBenchmarksResultsSingleChara = field(
        default_factory=UnifiedBenchmarksResultsSingleChara
    )
    time_ms: UnifiedBenchmarksResultsTime = field(
        default_factory=UnifiedBenchmarksResultsTime
    )


def _run_unified_benchs(
    extra_params_dict: dict[EPacAlgo, list[str]],
    datasets: list[DatasetMeta],
    desbordante_root: Path,
    algorithm: EPacAlgo,
    test_from: int,
    test_to: int,
    repeats: int,
) -> tp.Generator[UnifiedBenchmarksResults, None, None]:
    assert repeats >= 3
    assert 1 <= test_from <= test_to

    for dataset in datasets[test_from - 1:test_to]:
        build_target = _build_unified_bench(
            algorithm, extra_params_dict[algorithm], dataset.dataset_const, desbordante_root
        )
        samples = []
        for repeat in range(repeats):
            print(
                f"Running {algorithm}, {dataset.dataset_const} "
                f"({repeat + 1} / {repeats})... ",
                end="",
                flush=True,
            )
            samples.append(_run_unified_bench(build_target))
            print("done")

        algo_result = UnifiedBenchmarksResults(axis_x=[dataset.num])
        for metric in ("vspace_kb", "rss_kb"):
            metric_results = getattr(algo_result, metric)
            metric_results.before.append(
                [getattr(sample.memory.before, metric) for sample in samples]
            )
            metric_results.after_load.append(
                [getattr(sample.memory.after_load, metric) for sample in samples]
            )
            metric_results.after_execute.append(
                [getattr(sample.memory.after_execute, metric) for sample in samples]
            )
        algo_result.time_ms.load_data.append(
            [sample.time.load_data for sample in samples]
        )
        algo_result.time_ms.execute.append(
            [sample.time.execute for sample in samples]
        )
        yield algo_result


VSPACE_Y_META = AxisMeta(name="Peak virtual space", unit="KiB")
RSS_Y_META = AxisMeta(name="Peak resident space", unit="KiB")
TIME_Y_META = AxisMeta(name="Run time", unit="s")


def _process_unified_benchmark_results(
    results: UnifiedBenchmarksResults,
    algorithm: EPacAlgo,
    benchmark_name: str,
    dataset_size_unit: str,
) -> list[PlotStats]:
    def _make_values(ys: list[list[float]]) -> dict[int, list[float]]:
        assert len(ys) == len(results.axis_x)
        return {x: y for x, y in zip(results.axis_x, ys)}

    x_meta = AxisMeta(name="Dataset size", unit=dataset_size_unit)

    return [
        process_results(
            {
                "Before": _make_values(results.vspace_kb.before),
                "After load data": _make_values(results.vspace_kb.after_load),
                "After execute": _make_values(results.vspace_kb.after_execute),
            },
            algorithm,
            x_meta,
            VSPACE_Y_META,
            benchmark_name,
        ),
        process_results(
            {
                "Before": _make_values(results.rss_kb.before),
                "After load data": _make_values(results.rss_kb.after_load),
                "After execute": _make_values(results.rss_kb.after_execute),
            },
            algorithm,
            x_meta,
            RSS_Y_META,
            benchmark_name,
        ),
        process_results(
            {
                "Load data": _make_values(
                    [[time_ms / 1000 for time_ms in samples] for samples in results.time_ms.load_data]
                ),
                "Execute": _make_values(
                    [[time_ms / 1000 for time_ms in samples] for samples in results.time_ms.execute]
                ),
            },
            algorithm,
            x_meta,
            TIME_Y_META,
            benchmark_name,
        ),
    ]


def run_unified_benchmarks(
    extra_params_dict: dict[EPacAlgo, list[str]],
    datasets: list[DatasetMeta],
    desbordante_root: Path,
    algorithm: EPacAlgo,
    test_from: int,
    test_to: int,
    repeats: int,
    benchmark_name: str,
    dataset_size_unit: str,
) -> tp.Generator[list[PlotStats], None, None]:
    for results in _run_unified_benchs(
        extra_params_dict,
        datasets,
        desbordante_root,
        algorithm,
        test_from,
        test_to,
        repeats,
    ):
        yield _process_unified_benchmark_results(
            results,
            algorithm,
            benchmark_name,
            dataset_size_unit,
        )


def write_report(output: Path, results: tp.Iterable[list[PlotStats]]) -> None:
    output.parent.mkdir(exist_ok=True, parents=True)

    report: dict[StatsMeta, PlotStats] = {}
    for stats in results:
        for stat in stats:
            if stat.meta not in report:
                report[stat.meta] = PlotStats(meta=stat.meta, values={})
            for name, values in stat.values.items():
                report[stat.meta].values.setdefault(name, {}).update(values)
        output.write_text(PlotStats.dump(list(report.values())), encoding="utf-8")
