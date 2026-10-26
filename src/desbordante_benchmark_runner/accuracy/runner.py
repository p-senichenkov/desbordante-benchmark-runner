from pathlib import Path
from tempfile import TemporaryDirectory

from pydantic import TypeAdapter

from ..util import build_desbordante, run
from .benchmark_output import AccuracyBenchmarkOutput
from .report import AccuracyReport, process_results


def _run_accuracy_benchmarks(build_target: Path, numerics: list[int]) -> AccuracyBenchmarkOutput:
    assert numerics
    assert all(numeric > 0 for numeric in numerics)
    with TemporaryDirectory(prefix="desbordante-accuracy-") as temp_dir:
        output = Path(temp_dir) / "results.json"
        numeric_args = []
        for numeric in numerics:
            numeric_args += ["--numeric", str(numeric)]
        run(
            build_target / "Desbordante.accuracy",
            "--output", output,
            *numeric_args,
            cwd=build_target,
        )
        results: AccuracyBenchmarkOutput = TypeAdapter(AccuracyBenchmarkOutput).validate_json(
            output.read_text(encoding="utf-8")
        )
    assert set(results) == set(numerics)
    return results


def run_accuracy_benchmarks(desbordante_root: Path, numerics: list[int]) -> AccuracyReport:
    assert numerics
    assert all(numeric > 0 for numeric in numerics)
    build_target = build_desbordante(desbordante_root, target="Desbordante.accuracy")
    return process_results(_run_accuracy_benchmarks(build_target, sorted(set(numerics))))
