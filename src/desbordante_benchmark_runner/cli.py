from collections.abc import Iterable
from enum import StrEnum
from pathlib import Path

import click

from .algo import EPacAlgo
from .util import check_desbordante_root

from .unified.plots import build_plots as build_unified_plots
from .unified.statistics import PlotStats
from .unified.runner import write_report
from .unified.benchmarks import run_unified_iowas_low_arities

from .accuracy.plots import build_plots as build_accuracy_plots
from .accuracy.report import NUMERIC_PARAMETER_NAME , AccuracyReport
from .accuracy.runner import run_accuracy_benchmarks


class ESuite(StrEnum):
    IOWAS_LOW_ARITTIES = "iowas-low-arities"


SUITE_TO_UNIFIED_RUNNER = {ESuite.IOWAS_LOW_ARITTIES: run_unified_iowas_low_arities}

DESBORDANTE_ROOT_TYPE = click.Path(path_type=Path, dir_okay=True, file_okay=False, exists=True)
OUTPUT_PATH = click.Path(path_type=Path, dir_okay=False, allow_dash=False)
INPUT_PATH = click.Path(path_type=Path, dir_okay=False, allow_dash=False, exists=True)

DEFAULT_DESBORDANTE_ROOT = Path.home() / "Desbordante"

POSITIVE_INT = click.IntRange(min=1)


@click.group()
def cli() -> None:
    """Benchmark Desbordante and build plots from benchmark reports."""


@cli.command()
@click.option("-d", "--desbordante-root", type=DESBORDANTE_ROOT_TYPE, default=DEFAULT_DESBORDANTE_ROOT)
@click.option("-s", "--test-suite", type=ESuite, required=True)
@click.option("-a", "--algorithm", type=EPacAlgo, required=True)
@click.option("-o", "--output", type=OUTPUT_PATH, required=True)
@click.option("--test-from", type=POSITIVE_INT, default=1, show_default=True)
@click.option("-n", "--test-to", type=POSITIVE_INT, default=5, show_default=True)
@click.option("-r", "--repeats", type=click.IntRange(min=3), default=8, show_default=True)
def unified(desbordante_root: Path, test_suite: ESuite, algorithm: EPacAlgo, output: Path, test_from: int, test_to: int, repeats: int) -> None:
    if test_from > test_to:
        raise click.BadParameter("must be at least --test-from", param_hint="--test-to")
    check_desbordante_root(desbordante_root)
    results = SUITE_TO_UNIFIED_RUNNER[test_suite](desbordante_root, algorithm, test_from, test_to, repeats)
    write_report(output, results)


@cli.command()
@click.option("-i", "--input", type=INPUT_PATH, required=True)
@click.option("-o", "--output", type=OUTPUT_PATH)
def plot(input: Path, output: Path | None) -> None:
    """Build matplotlib plots from a report produced by unified."""

    build_unified_plots(PlotStats.load(input.read_text(encoding="utf-8")), output)


@cli.command()
@click.option("-d", "--desbordante-root", type=DESBORDANTE_ROOT_TYPE, default=DEFAULT_DESBORDANTE_ROOT)
@click.option("-n", "--numeric", type=POSITIVE_INT, multiple=True, required=True, help=f"{NUMERIC_PARAMETER_NAME }; specify once per value.")
@click.option("-o", "--output", type=OUTPUT_PATH, required=True)
def accuracy(desbordante_root: Path, numeric: list[int], output: Path) -> None:
    check_desbordante_root(desbordante_root)
    report = run_accuracy_benchmarks(desbordante_root, list(numeric))
    output.parent.mkdir(exist_ok=True, parents=True)
    output.write_text(report.model_dump_json(indent=2), encoding="utf-8")


@cli.command()
@click.option("-i", "--input", type=INPUT_PATH, required=True)
@click.option("-o", "--output", type=OUTPUT_PATH)
def accuracy_plot(input: Path, output: Path | None) -> None:
    report = AccuracyReport.load(input.read_text(encoding="utf-8"))
    build_accuracy_plots(report, output)


if __name__ == "__main__":
    cli()
