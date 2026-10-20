from dataclasses import dataclass
from pathlib import Path

from .algo import ALGO_CLASSES, EPacAlgo
from .statistics import AxisMeta, PlotStats, process_results
from .util import IOWAS_SIZES, build_desbordante, capture, iowa_fname, prepare_iowas


def _timed_run(test_name: str, desbordante_root: Path) -> int:
    """
    Returns:
        milliseconds
    """
    build_target = desbordante_root / "build" / "target"
    lines = capture(
        build_target / "Desbordante.benchmark", "--name", test_name, cwd=build_target
    ).splitlines()
    assert len(lines) == 1
    return int(lines[0])


@dataclass
class TimedBenchmarkMeta:
    dataset_name: str
    name_suffix: str
    # Some numeric characteristic of dataset (displayed on axis X)
    num: int


type TimedBenchmarksResults = dict[int, list[float]]


def _make_benchmark_name(algo: EPacAlgo, dataset_name: str, name_suffix: str) -> str:
    return f"{ALGO_CLASSES[algo]}, {dataset_name}, {name_suffix}"


def _run_timed_benchmarks(
    benchmarks: list[TimedBenchmarkMeta],
    desbordante_root: Path,
    algorithm: EPacAlgo,
    test_count: int,
    repeats: int,
) -> TimedBenchmarksResults:
    if repeats < 3:
        raise ValueError("At least three repeats are required for statistics")
    build_desbordante(desbordante_root, benchmarks=True, target="Desbordante.benchmark")

    results: TimedBenchmarksResults = {}
    for bench in benchmarks[:test_count]:
        bench_name = _make_benchmark_name(
            algorithm, bench.dataset_name, bench.name_suffix
        )
        times_ms: list[float] = []
        for i in range(repeats):
            print(f"Running {bench_name} ({i + 1} / {repeats})... ", end="", flush=True)
            result = _timed_run(bench_name, desbordante_root)
            print(f"{result}ms")
            times_ms.append(result)
        results[bench.num] = times_ms
    return results


IOWAS_LOW_ARITIES_METAS = [
    TimedBenchmarkMeta(
        dataset_name=iowa_fname(size).stem,
        name_suffix="low arity",
        num=size,
    )
    for size in IOWAS_SIZES
]


def run_timed_iowas_low_arities(
    desbordante_root: Path,
    algorithm: EPacAlgo,
    test_count: int,
    repeats: int,
) -> TimedBenchmarksResults:
    prepare_iowas(desbordante_root)
    return _run_timed_benchmarks(
        IOWAS_LOW_ARITIES_METAS, desbordante_root, algorithm, test_count, repeats
    )


def process_timed_benchmark_results(
    results: TimedBenchmarksResults,
    algorithm: EPacAlgo,
    benchmark_name: str,
    dataset_size_unit: str,
) -> list[PlotStats]:
    return [
        process_results(
            {"Run time": results},
            algorithm,
            AxisMeta(name="Dataset size", unit=dataset_size_unit),
            AxisMeta(name="Run time", unit="ms"),
            benchmark_name,
        )
    ]
