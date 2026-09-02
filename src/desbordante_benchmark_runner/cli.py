from enum import StrEnum
from pathlib import Path
import json
from collections import defaultdict

import click

from .algo import EPacAlgo
from .memory_benchmarks import run_iowas_low_arities
from .memory_plots import build_memory_plots
from .timed import run_timed_iowas_low_arities
from .timed_plots import build_timed_plots
from .util import check_desbordante_root


# NOTE: It is not necessary that each suite supports both memory and timed
class ESuite(StrEnum):
    IOWAS_LOW_ARITTIES = "iowas-low-arities"


SUITE_TO_MEMORY_RUNNER = {
    ESuite.IOWAS_LOW_ARITTIES: run_iowas_low_arities,
}


def _xlabel(suite: ESuite) -> str:
    SUITE_TO_XLABEL = {ESuite.IOWAS_LOW_ARITTIES: "Row number"}
    return SUITE_TO_XLABEL.get(suite, "")


CLICK_PATH = click.Path(path_type=Path)
OUTPUT_PATH = click.Path(path_type=Path, dir_okay=False, allow_dash=False, exists=False)
INPUT_PATH = click.Path(path_type=Path, dir_okay=False, allow_dash=True, exists=True)


@click.group()
def main():
    pass


@main.command()
@click.option(
    "-d",
    "--desbordante-root",
    type=CLICK_PATH,
    default=Path.home() / "Desbordante",
)
@click.option("-s", "--test-suite", type=ESuite)
@click.option(
    "-a", "--algorithms", type=EPacAlgo, multiple=True, default=list(EPacAlgo)
)
@click.option("-o", "--output", type=OUTPUT_PATH, default=Path("output.pdf"))
@click.option(
    "-n", "--test-count", default=5, help="Run only N first benchmarks for each algo"
)
# TODO: more options
def memory(
    desbordante_root: Path | None,
    test_suite: ESuite,
    algorithms: list[EPacAlgo],
    output: Path,
    test_count: int,
):
    assert desbordante_root is not None
    check_desbordante_root(desbordante_root)

    results = SUITE_TO_MEMORY_RUNNER[test_suite](
        desbordante_root, algorithms, test_count
    )
    build_memory_plots(results, output, _xlabel(test_suite))


SUITE_TO_TIMED_RUNNER = {ESuite.IOWAS_LOW_ARITTIES: run_timed_iowas_low_arities}


@main.command()
@click.option(
    "-d",
    "--desbordante-root",
    type=CLICK_PATH,
    default=Path.home() / "Desbordante",
)
@click.option("-s", "--test-suite", type=ESuite)
@click.option(
    "-a", "--algorithms", type=EPacAlgo, multiple=True, default=list(EPacAlgo)
)
@click.option("-o", "--output", type=OUTPUT_PATH, default=Path("output.pdf"))
@click.option(
    "-n", "--test-count", default=5, help="Run only N first benchmarks for each algo"
)
@click.option("-r", "--repeats", default=5, help="Repeat each benchmark N times")
def timed(
    desbordante_root: Path | None,
    test_suite: ESuite,
    algorithms: list[EPacAlgo],
    output: Path,
    test_count: int,
    repeats: int,
):
    assert desbordante_root is not None
    check_desbordante_root(desbordante_root)

    results = SUITE_TO_TIMED_RUNNER[test_suite](
        desbordante_root,
        algorithms,
        test_count,
        repeats,
    )
    build_timed_plots(results, output, _xlabel(test_suite))


@main.command()
@click.option(
    "-d",
    "--desbordante-root",
    type=CLICK_PATH,
    default=Path.home() / "Desbordante",
)
@click.option("-s", "--test-suite", type=ESuite)
@click.option(
    "-a", "--algorithms", type=EPacAlgo, multiple=True, default=list(EPacAlgo)
)
@click.option("-o", "--output", type=OUTPUT_PATH, default=Path("output.json"))
@click.option(
    "-n", "--test-count", default=5, help="Run only N first benchmarks for each algo"
)
@click.option("-r", "--repeats", default=5, help="Repeat each benchmark N times")
def write_timed(
    desbordante_root: Path | None,
    test_suite: ESuite,
    algorithms: list[EPacAlgo],
    output: Path,
    test_count: int,
    repeats: int,
):
    assert desbordante_root is not None
    check_desbordante_root(desbordante_root)

    results = SUITE_TO_TIMED_RUNNER[test_suite](
        desbordante_root,
        algorithms,
        test_count,
        repeats,
    )
    flat_results = {algo.value: res for algo, res in results.items()}

    output.parent.mkdir(exist_ok=True, parents=True)
    with open(output, "w") as f:
        json.dump(flat_results, f)


@main.command()
@click.option("-i", "--input", type=INPUT_PATH, multiple=True)
@click.option("-s", "--test-suite", type=ESuite)
@click.option("-o", "--output", type=OUTPUT_PATH)
def read_timed(input: list[Path], test_suite: ESuite | None, output: Path | None):
    assert len(input) > 0, "Must specify at least one input file"
    results: dict[EPacAlgo, dict[int, int]] = defaultdict(dict)
    for inp in input:
        with open(inp, "r") as f:
            res = json.load(f)
        assert isinstance(res, dict)
        for algo, algo_res in res.items():
            assert isinstance(algo_res, dict)
            results[algo].update(algo_res)

    x_label = "" if test_suite is None else _xlabel(test_suite)
    build_timed_plots(results, output, x_label)


if __name__ == "__main__":
    main()
