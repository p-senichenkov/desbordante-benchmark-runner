from collections.abc import Iterable
from enum import StrEnum
from pathlib import Path

import click

from .algo import EPacAlgo
from .accuracy.cli import accuracy, accuracy_plot
from .statistics import PlotStats, StatsMeta
from .unified.benchmarks import run_unified_iowas_low_arities
from .util import check_desbordante_root
from .plots import build_plots


class ESuite(StrEnum):
    IOWAS_LOW_ARITTIES = "iowas-low-arities"


SUITE_TO_UNIFIED_RUNNER = {ESuite.IOWAS_LOW_ARITTIES: run_unified_iowas_low_arities}

CLICK_PATH = click.Path(path_type=Path)
OUTPUT_PATH = click.Path(path_type=Path, dir_okay=False, allow_dash=False)
INPUT_PATH = click.Path(path_type=Path, dir_okay=False, allow_dash=False, exists=True)


@click.group()
def main() -> None:
    """Benchmark Desbordante and build plots from benchmark reports."""


def _write_report(output: Path, results: Iterable[list[PlotStats]]) -> None:
    output.parent.mkdir(exist_ok=True, parents=True)

    report: dict[StatsMeta, PlotStats] = {}
    for stats in results:
        for stat in stats:
            if stat.meta not in report:
                report[stat.meta] = PlotStats(meta=stat.meta, values={})
            for name, values in stat.values.items():
                report[stat.meta].values.setdefault(name, {}).update(values)
        output.write_text(PlotStats.dump(list(report.values())), encoding="utf-8")


@main.command()
@click.option("-d", "--desbordante-root", type=CLICK_PATH, default=Path.home() / "Desbordante")
@click.option("-s", "--test-suite", type=ESuite, required=True)
@click.option("-a", "--algorithm", type=EPacAlgo, required=True)
@click.option("-o", "--output", type=OUTPUT_PATH, default=Path("unified-report.json"), show_default=True)
@click.option("--test-from", type=click.IntRange(min=1), default=1, show_default=True, help="First benchmark index (1-based, inclusive).")
@click.option("-n", "--test-to", type=click.IntRange(min=1), default=5, show_default=True, help="Last benchmark index (1-based, inclusive).")
@click.option("-r", "--repeats", type=click.IntRange(min=3), default=8, show_default=True)
def unified(desbordante_root: Path, test_suite: ESuite, algorithm: EPacAlgo, output: Path, test_from: int, test_to: int, repeats: int) -> None:
    if test_from > test_to:
        raise click.BadParameter("must be at least --test-from", param_hint="--test-to")
    check_desbordante_root(desbordante_root)
    results = SUITE_TO_UNIFIED_RUNNER[test_suite](desbordante_root, algorithm, test_from, test_to, repeats)
    _write_report(output, results)


@main.command()
@click.option("-i", "--input", type=INPUT_PATH, required=True)
@click.option("-o", "--output", type=OUTPUT_PATH)
def plot(input: Path, output: Path | None) -> None:
    """Build matplotlib plots from a report produced by unified."""

    build_plots(PlotStats.load(input.read_text(encoding="utf-8")), output)


main.add_command(accuracy)
main.add_command(accuracy_plot)


if __name__ == "__main__":
    main()
