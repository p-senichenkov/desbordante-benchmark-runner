import json

from pydantic import BaseModel, RootModel, TypeAdapter

from ..statistics import AxisMeta
from .benchmark_output import AccuracyBenchmarkOutput
from .statistics import aggregate_results, error_percentiles


NUMERIC_PARAMETER_NAME = "Histogram bucket count multiplier"


class PlotMeta(BaseModel):
    name: str
    axis_x: AxisMeta
    axis_y: AxisMeta


class PlotValues(BaseModel):
    meta: PlotMeta
    values: dict[str, dict[int, float]]


class PlotPage(BaseModel):
    name: str
    plots: list[PlotValues]


class AccuracyReport(RootModel[dict[str, list[PlotPage]]]):
    @staticmethod
    def load(st: str) -> "AccuracyReport":
        report = json.loads(st)
        if isinstance(report.get("benchmarks"), dict):
            return process_results(
                TypeAdapter(AccuracyBenchmarkOutput).validate_python(report["benchmarks"]),
                parameter_name=report.get("parameter_name", NUMERIC_PARAMETER_NAME ),
                baseline_algorithm=report.get("baseline_algorithm", "UCCPACVerifier"),
                tested_algorithm=report.get("tested_algorithm", "HistogramUCCPACVerifier"),
            )
        return AccuracyReport.model_validate(report)


def _make_plot(name: str, parameter_name: str, values: dict[str, dict[int, float]]) -> PlotValues:
    return PlotValues(
        meta=PlotMeta(
            name=name,
            axis_x=AxisMeta(name=parameter_name, unit=""),
            axis_y=AxisMeta(name=name, unit=""),
        ),
        values=values,
    )


def process_results(
    results: AccuracyBenchmarkOutput,
    *,
    parameter_name: str = NUMERIC_PARAMETER_NAME ,
    baseline_algorithm: str = "UCCPACVerifier",
    tested_algorithm: str = "HistogramUCCPACVerifier",
) -> AccuracyReport:
    percentiles = aggregate_results(results, error_percentiles)
    numerics = sorted(results)
    test_names = sorted(results[numerics[0]])

    percentile_page = PlotPage(
        name="Absolute error",
        plots=[
            _make_plot(
                f"Absolute {metric} error",
                parameter_name,
                {
                    percentile: {
                        numeric: percentiles[numeric][metric][percentile] for numeric in numerics
                    }
                    for percentile in ("p50", "p90", "p100")
                },
            )
            for metric in ("epsilon", "delta")
        ],
    )
    benchmarks = [
        PlotPage(
            name=test_name,
            plots=[
                _make_plot(
                    metric.capitalize(),
                    parameter_name,
                    {
                        label: {
                            numeric: getattr(getattr(results[numeric][test_name], metric), field)
                            for numeric in numerics
                        }
                        for label, field in (
                            (f"Baseline ({baseline_algorithm})", "baseline"),
                            (f"Tested ({tested_algorithm})", "actual"),
                        )
                    },
                )
                for metric in ("epsilon", "delta")
            ],
        )
        for test_name in test_names
    ]
    return AccuracyReport({"aggregates": [percentile_page], "benchmarks": benchmarks})
