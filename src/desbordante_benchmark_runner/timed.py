from dataclasses import dataclass
from pathlib import Path

from .algo import ALGO_CLASSES, EPacAlgo
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


type TimedBenchmarksResults = dict[int, int]


def _make_benchmark_name(algo: EPacAlgo, dataset_name: str, name_suffix: str) -> str:
    return f"{ALGO_CLASSES[algo]}, {dataset_name}, {name_suffix}"


def _run_timed_benchmarks(
    benchmarks: list[TimedBenchmarkMeta],
    desbordante_root: Path,
    algorithms: list[EPacAlgo],
    test_count: int,
    repeats: int,
) -> dict[EPacAlgo, TimedBenchmarksResults]:
    build_desbordante(desbordante_root, benchmarks=True, target="Desbordante.benchmark")

    results: dict[EPacAlgo, TimedBenchmarksResults] = {}
    for algo in algorithms:
        algo_results: dict[int, int] = {}
        for bench in benchmarks[:test_count]:
            bench_name = _make_benchmark_name(
                algo, bench.dataset_name, bench.name_suffix
            )
            times_ms = []
            for i in range(repeats):
                print(f"Running {bench_name} ({i} / {repeats})...")
                times_ms.append(_timed_run(bench_name, desbordante_root))
            algo_results[bench.num] = sum(times_ms) // repeats
        results[algo] = algo_results
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
    algorithms: list[EPacAlgo],
    test_count: int,
    repeats: int,
) -> dict[EPacAlgo, TimedBenchmarksResults]:
    prepare_iowas(desbordante_root)
    return _run_timed_benchmarks(
        IOWAS_LOW_ARITIES_METAS, desbordante_root, algorithms, test_count, repeats
    )
