from collections.abc import Callable
from statistics import fmean

from pydantic import BaseModel

from .benchmark_output import AccuracyBenchmarkOutput, TestResults


class MeanErrors(BaseModel):
    epsilon: float
    delta: float


def aggregate_results[T](
    results: AccuracyBenchmarkOutput,
    aggregation: Callable[[TestResults], T],
) -> dict[int, T]:
    assert results
    test_names = set(next(iter(results.values())))
    assert test_names
    assert all(set(tests) == test_names for tests in results.values())
    return {numeric: aggregation(tests) for numeric, tests in sorted(results.items())}


def mean_absolute_errors(tests: TestResults) -> MeanErrors:
    return MeanErrors(
        epsilon=fmean(result.epsilon.absolute_error for result in tests.values()),
        delta=fmean(result.delta.absolute_error for result in tests.values()),
    )
