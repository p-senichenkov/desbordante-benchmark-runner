from pydantic import BaseModel

from .benchmark_output import AccuracyBenchmarkOutput
from .statistics import MeanErrors, aggregate_results, mean_absolute_errors


PARAMETER_NAME = "Histogram bucket count multiplier"


class AccuracyReport(BaseModel):
    parameter_name: str = PARAMETER_NAME
    baseline_algorithm: str = "UCCPACVerifier"
    tested_algorithm: str = "HistogramUCCPACVerifier"
    benchmarks: AccuracyBenchmarkOutput
    mean_absolute_errors: dict[int, MeanErrors]


def process_results(results: AccuracyBenchmarkOutput) -> AccuracyReport:
    return AccuracyReport(
        benchmarks=results,
        mean_absolute_errors=aggregate_results(results, mean_absolute_errors),
    )
