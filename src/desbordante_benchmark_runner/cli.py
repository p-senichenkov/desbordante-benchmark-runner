from enum import StrEnum
from pathlib import Path

import click

from .algo import EPacAlgo
from .memory_benchmarks import run_iowas_low_arities
from .memory_plots import build_memory_plots
from .util import check_desbordante_root


class ESuite(StrEnum):
    IOWAS_LOW_ARITTIES = "iowas-low-arities"


SUITE_TO_RUNNER = {
    ESuite.IOWAS_LOW_ARITTIES: run_iowas_low_arities,
}

CLICK_PATH = click.Path(path_type=Path)
OUTPUT_PATH = click.Path(path_type=Path, dir_okay=False, allow_dash=False, exists=False)


@click.command()
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
# TODO: more options
def main(
    desbordante_root: Path | None,
    test_suite: ESuite,
    algorithms: list[EPacAlgo],
    output: Path,
):
    assert desbordante_root is not None
    check_desbordante_root(desbordante_root)

    results = SUITE_TO_RUNNER[test_suite](desbordante_root, algorithms)
    build_memory_plots(results, output)


if __name__ == "__main__":
    main()
