import typing as tp
import json
from collections import defaultdict
from dataclasses import dataclass

import numpy

from .benchmark_output import TestResults, Error, EpsilonDeltaError
from .plot_data import PlotData


def _percentiles(
    sorted_results: list[TestResults],
    get_value: tp.Callable[[EpsilonDeltaError], float],
) -> PlotData:
    PERCENTILE_POINTS = (50, 90, 100)

    result: PlotData = []
    for test_results in sorted_results:
        percentile_values = [
            float(value)
            for value in numpy.percentile(
                [get_value(result) for result in test_results.values()],
                PERCENTILE_POINTS,
                method="linear",
            )
        ]

        result.append({
            f"{percentile_point}": percentile_value
            for percentile_point, percentile_value in zip(PERCENTILE_POINTS, percentile_values)
        })
    return result


@dataclass
class EpsilonDeltaPlotData:
    epsilon: PlotData
    delta: PlotData


def _epsilon_delta_percentiles(
    sorted_results: list[TestResults],
    get_value: tp.Callable[[Error], float],
) -> EpsilonDeltaPlotData:
    return EpsilonDeltaPlotData(
        epsilon=_percentiles(sorted_results, lambda eps_delta_err: get_value(eps_delta_err.epsilon)),
        delta=_percentiles(sorted_results, lambda eps_delta_err: get_value(eps_delta_err.delta)),
    )


def _absolute_error(err: Error) -> float:
    return abs(err.actual - err.baseline)


def _relative_error(err: Error) -> float:
    if err.baseline == 0:
        return _absolute_error(err)
    return _absolute_error(err) / err.baseline


def absolute_error_percentiles(sorted_results: list[TestResults]) -> EpsilonDeltaPlotData:
    return _epsilon_delta_percentiles(sorted_results, _absolute_error)


def relative_error_percentiles(sorted_results: list[TestResults]) -> EpsilonDeltaPlotData:
    return _epsilon_delta_percentiles(sorted_results, _relative_error)
