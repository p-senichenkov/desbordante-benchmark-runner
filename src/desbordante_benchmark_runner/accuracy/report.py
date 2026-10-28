import json

from pydantic import BaseModel, RootModel, TypeAdapter

from .benchmark_output import AccuracyBenchmarkOutput
from .statistics import Lines, absolute_error_percentiles, relative_error_percentiles

NUMERIC_PARAMETER_NAME = "Histogram bucket count multiplier"


class PlotValues(BaseModel):
    axis_x: str
    axis_y: str
    values: Lines


class PlotPage(BaseModel):
    name: str
    plots: list[PlotValues]


def _make_page(name: str, parameter_name: str, stats: dict[str, Lines]) -> PlotPage:
    return PlotPage(
        name=name,
        plots=[
            PlotValues(
                axis_x=parameter_name,
                axis_y=metric.capitalize(),
                values=values,
            )
            for metric, values in stats.items()
        ]
    )


def process_results(
    results: AccuracyBenchmarkOutput,
    *,
    parameter_name: str = NUMERIC_PARAMETER_NAME ,
    baseline_algorithm: str = "UCCPACVerifier",
    tested_algorithm: str = "HistogramUCCPACVerifier",
) -> "AccuracyReport":
    numerics = sorted(results)
    test_names = sorted(results[numerics[0]])

    benchmarks = [
        PlotPage(
            name=test_name,
            plots=[
                PlotValues(
                    axis_x=parameter_name,
                    axis_y=metric.capitalize(),
                    values={
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

    abs_err_percentiles = absolute_error_percentiles(results)
    rel_err_percentiles = relative_error_percentiles(results)

    abs_err_percentile_page = _make_page("Absolute error", parameter_name, abs_err_percentiles)
    rel_err_percentile_page = _make_page("Relative error", parameter_name, rel_err_percentiles)

    return AccuracyReport({
        "aggregates": [abs_err_percentile_page, rel_err_percentile_page],
        "benchmarks": benchmarks,
    })


class AccuracyReport(RootModel[dict[str, list[PlotPage]]]):
    pass
