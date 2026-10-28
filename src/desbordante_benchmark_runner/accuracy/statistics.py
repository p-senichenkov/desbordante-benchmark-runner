import typing as tp
from statistics import fmean

import numpy

from .benchmark_output import AccuracyBenchmarkOutput, TestResults


def aggregate_results[T](
    results: AccuracyBenchmarkOutput,
    aggregation: tp.Callable[[TestResults], T],
) -> dict[int, T]:
    assert results
    test_names = set(next(iter(results.values())))
    assert test_names
    assert all(set(tests) == test_names for tests in results.values())
    return {numeric: aggregation(tests) for numeric, tests in sorted(results.items())}


def error_percentiles(tests: TestResults) -> dict[str, dict[str, float]]:
    return {
        metric: {
            f"p{percentile}": float(value)
            for percentile, value in zip(
                (50, 90, 100),
                numpy.percentile(
                    [getattr(result, metric).absolute_error for result in tests.values()],
                    (50, 90, 100),
                    method="linear",
                ),
            )
        }
        for metric in ("epsilon", "delta")
    }
