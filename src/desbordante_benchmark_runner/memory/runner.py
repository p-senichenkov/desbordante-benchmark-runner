import abc
import typing as tp
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import BaseModel

from ..algo import EPacAlgo
from ..util import capture, run, build_desbordante
from ..statistics import AxisMeta, PlotStats, process_results
from .algo_meta import ALGO_BUILDERS


class PeakMemoryUsage(BaseModel):
    vspace_kb: int
    rss_kb: int


class AlgoMemoryUsage(BaseModel):
    before: PeakMemoryUsage
    after_load: PeakMemoryUsage
    after_execute: PeakMemoryUsage


def _build_memory_bench(
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


def _run_memory_bench(build_target: Path) -> AlgoMemoryUsage:
    output = capture(build_target / "Desbordante.memory_bench", cwd=build_target)
    return AlgoMemoryUsage.model_validate_json(output)


@dataclass
class DatasetMeta:
    dataset_const: str
    # Some numeric characteristic of dataset (displayed on axis X)
    num: int


@dataclass
class MemoryBenchmarksResultsSingleChara:
    # Currently ignored. TODO: remove
    before: list[list[float]] = field(default_factory=list)
    after_load: list[list[float]] = field(default_factory=list)
    after_execute: list[list[float]] = field(default_factory=list)


@dataclass
class MemoryBenchmarksResults:
    axis_x: list[int] = field(default_factory=list)
    vspace_kb: MemoryBenchmarksResultsSingleChara = field(
        default_factory=MemoryBenchmarksResultsSingleChara
    )
    rss_kb: MemoryBenchmarksResultsSingleChara = field(
        default_factory=MemoryBenchmarksResultsSingleChara
    )


def _run_memory_benchs(
    extra_params_dict: dict[EPacAlgo, list[str]],
    datasets: list[DatasetMeta],
    desbordante_root: Path,
    algorithm: EPacAlgo,
    test_count: int,
    repeats: int,
) -> MemoryBenchmarksResults:
    assert repeats >= 3

    algo_result = MemoryBenchmarksResults()
    for dataset in datasets[:test_count]:
        build_target = _build_memory_bench(
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
            samples.append(_run_memory_bench(build_target))
            print("done")

        algo_result.axis_x.append(dataset.num)
        for metric in ("vspace_kb", "rss_kb"):
            metric_results = getattr(algo_result, metric)
            metric_results.before.append(
                [getattr(sample.before, metric) for sample in samples]
            )
            metric_results.after_load.append(
                [getattr(sample.after_load, metric) for sample in samples]
            )
            metric_results.after_execute.append(
                [getattr(sample.after_execute, metric) for sample in samples]
            )
    return algo_result


VSPACE_Y_META = AxisMeta(name="Peak virtual space", unit="KiB")
RSS_Y_META = AxisMeta(name="Peak resident space", unit="KiB")


def _process_memory_benchmark_results(
    results: MemoryBenchmarksResults,
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
    ]


def run_memory_benchmarks(
    extra_params_dict: dict[EPacAlgo, list[str]],
    datasets: list[DatasetMeta],
    desbordante_root: Path,
    algorithm: EPacAlgo,
    test_count: int,
    repeats: int,
    benchmark_name: str,
    dataset_size_unit: str,
) -> list[PlotStats]:
    return _process_memory_benchmark_results(
        _run_memory_benchs(
            extra_params_dict,
            datasets,
            desbordante_root,
            algorithm,
            test_count,
            repeats,
        ),
        algorithm,
        benchmark_name,
        dataset_size_unit,
    )
