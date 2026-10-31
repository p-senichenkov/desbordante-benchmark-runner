import json
from collections import defaultdict

from pydantic import BaseModel, RootModel, TypeAdapter

from .benchmark_output import EpsilonDeltaError, TestResults, AccuracyBenchmarkOutput
from .plot_data import Vertical, PlotPage, PlotData, AccuracyPlots
from .statistics import EpsilonDeltaPlotData, absolute_error_percentiles, relative_error_percentiles

NUMERIC_PARAMETER_NAME = "Histogram bucket count multiplier"
BASELINE_ALGO_NAME = "UCC PAC verifier"
TESTED_ALGO_NAME = "Histogram UCC PAC verifier"


def _make_aggregates(
    numerics: list[int],
    sorted_results: list[TestResults],
    param_name: str,
) -> list[PlotPage]:
    abs_err_percentiles = absolute_error_percentiles(sorted_results)
    rel_err_percentiles = relative_error_percentiles(sorted_results)

    return [
        PlotPage(
            name="Absolute error",
            axis_x_name=param_name,
            axis_x_values=numerics,
            epsilon_plot=abs_err_percentiles.epsilon,
            delta_plot=abs_err_percentiles.delta,
        ),
        PlotPage(
            name="Relative error",
            axis_x_name=param_name,
            axis_x_values=numerics,
            epsilon_plot=rel_err_percentiles.epsilon,
            delta_plot=rel_err_percentiles.delta,
        ),
    ]


def _eps_delta_error_to_verticals(
    eps_delta_error: EpsilonDeltaError,
    baseline_algo: str,
    tested_algo: str,
) -> tuple[Vertical, Vertical]:
    return (
        {
            baseline_algo: eps_delta_error.epsilon.baseline,
            tested_algo: eps_delta_error.epsilon.actual,
        },
        {
            baseline_algo: eps_delta_error.delta.baseline,
            tested_algo: eps_delta_error.delta.actual,
        },
    )


def _make_test_plots(
    numerics: list[int],
    sorted_results: list[TestResults],
    param_name: str,
    baseline_algo: str,
    tested_algo: str,
) -> list[PlotPage]:
    verticals: dict[str, list[tuple[Vertical, Vertical]]] = defaultdict(list)
    for test_res in sorted_results:
        for test_name, eps_delta_error in test_res.items():
            verticals[test_name].append(
                _eps_delta_error_to_verticals(eps_delta_error, baseline_algo, tested_algo)
            )

    result: list[PlotPage] = []
    for name, values in verticals.items():
        epsilon_plot: PlotData = []
        delta_plot: PlotData = []

        for (eps_vert, delta_vert) in values:
            epsilon_plot.append(eps_vert)
            delta_plot.append(delta_vert)
        result.append(
            PlotPage(
                name=name,
                axis_x_name=param_name,
                axis_x_values=numerics,
                epsilon_plot=epsilon_plot,
                delta_plot=delta_plot,
            )
        )
    return result


def process_results(
    results: AccuracyBenchmarkOutput,
    parameter_name: str = NUMERIC_PARAMETER_NAME ,
    baseline_algo: str = BASELINE_ALGO_NAME,
    tested_algo: str = TESTED_ALGO_NAME,
) -> AccuracyPlots:
    numerics = sorted(results.keys())
    sorted_results = [results[num] for num in numerics]

    aggregates = _make_aggregates(numerics, sorted_results, parameter_name)
    test_pages = _make_test_plots(
        numerics,
        sorted_results,
        parameter_name,
        baseline_algo,
        tested_algo,
    )
    return aggregates + test_pages
