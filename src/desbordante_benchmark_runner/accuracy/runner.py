from pathlib import Path

from pydantic import TypeAdapter

from ..util import build_desbordante, run, check_desbordante_root
from .benchmark_output import AccuracyBenchmarkOutput
from .process_results import process_results
from .plots import build_plots


def _run_accuracy_benchmarks(build_target: Path, numerics: list[int], output: Path) -> None:
    output = output.resolve()
    assert output.is_file() or not output.exists()
    output.parent.mkdir(parents=True, exist_ok=True)

    numeric_args = []
    for numeric in numerics:
        numeric_args += ["--numeric", str(numeric)]
    run(
        build_target / "Desbordante.accuracy",
        "--output", output,
        *numeric_args,
        cwd=build_target,
    )


def run_accuracy_benchmarks(desbordante_root: Path, numerics: list[int], output: Path) -> None:
    assert numerics

    check_desbordante_root(desbordante_root)
    build_target = build_desbordante(desbordante_root, target="Desbordante.accuracy")
    _run_accuracy_benchmarks(build_target, sorted(numerics), output)


def build_accuracy_plots(input: Path, output: Path | None, log_x: bool) -> None:
    bench_out: AccuracyBenchmarkOutput = TypeAdapter(AccuracyBenchmarkOutput).validate_json(
        input.read_text()
    )
    plot_data = process_results(bench_out)
    build_plots(plot_data, output, log_x)
