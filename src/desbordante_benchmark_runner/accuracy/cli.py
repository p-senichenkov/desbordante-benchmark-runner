from pathlib import Path

import click

from ..util import check_desbordante_root
from .plots import build_plots
from .report import PARAMETER_NAME, AccuracyReport
from .runner import run_accuracy_benchmarks


@click.command()
@click.option("-d", "--desbordante-root", type=click.Path(path_type=Path), default=Path.home() / "Desbordante")
@click.option("-n", "--numeric", type=click.IntRange(min=1), multiple=True, required=True, help=f"{PARAMETER_NAME}; specify once per value.")
@click.option("-o", "--output", type=click.Path(path_type=Path, dir_okay=False, allow_dash=False), default=Path("accuracy-report.json"), show_default=True)
def accuracy(desbordante_root: Path, numeric: tuple[int, ...], output: Path) -> None:
    check_desbordante_root(desbordante_root)
    report = run_accuracy_benchmarks(desbordante_root, list(numeric))
    output.parent.mkdir(exist_ok=True, parents=True)
    output.write_text(report.model_dump_json(indent=2), encoding="utf-8")


@click.command()
@click.option("-i", "--input", type=click.Path(path_type=Path, dir_okay=False, allow_dash=False, exists=True), required=True)
@click.option("-o", "--output", type=click.Path(path_type=Path, dir_okay=False, allow_dash=False), help="PDF with one page per test, or image filename prefix for numbered per-test files.")
def accuracy_plot(input: Path, output: Path | None) -> None:
    report = AccuracyReport.model_validate_json(input.read_text(encoding="utf-8"))
    build_plots(report, output)
