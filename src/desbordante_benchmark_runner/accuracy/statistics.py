import typing as tp
import json
from collections import defaultdict

import numpy

from ..util import EPSILON, DELTA

from .benchmark_output import AccuracyBenchmarkOutput, TestResults, Error, EpsilonDeltaError


type LinePoints = dict[int, float]
type Lines = dict[str, LinePoints]


def _percentiles(
    results: AccuracyBenchmarkOutput,
    get_value: tp.Callable[[EpsilonDeltaError], float],
) -> Lines:
    PERCENTILE_POINTS = (50, 90, 100)

    result: Lines = defaultdict(dict)
    for numeric, test_results in sorted(results.items()):
        percentile_values = [
            float(value)
            for value in numpy.percentile(
                [get_value(result) for result in test_results.values()],
                PERCENTILE_POINTS,
                method="linear",
            )
        ]

        for percentile_point, percentile_value in zip(PERCENTILE_POINTS, percentile_values):
            result[f"p{percentile_point}"][numeric] = percentile_value
    return result


def _epsilon_delta_percentiles(
    results: AccuracyBenchmarkOutput,
    get_value: tp.Callable[[Error], float],
) -> dict[str, Lines]:
    return {
        EPSILON: _percentiles(results, lambda eps_delta_err: get_value(eps_delta_err.epsilon)),
        DELTA: _percentiles(results, lambda eps_delta_err: get_value(eps_delta_err.delta)),
    }


def _absolute_error(err: Error) -> float:
    return abs(err.actual - err.baseline)


def _relative_error(err: Error) -> float:
    if err.baseline == 0:
        return _absolute_error(err)
    return _absolute_error(err) / err.baseline


def absolute_error_percentiles(results: AccuracyBenchmarkOutput) -> dict[str, Lines]:
    return _epsilon_delta_percentiles(results, _absolute_error)


def relative_error_percentiles(results: AccuracyBenchmarkOutput) -> dict[str, Lines]:
    return _epsilon_delta_percentiles(results, _relative_error)
