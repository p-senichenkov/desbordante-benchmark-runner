from pydantic import BaseModel


class Error(BaseModel):
    baseline: float
    actual: float

    @property
    def absolute_error(self) -> float:
        return abs(self.actual - self.baseline)


class EpsilonDeltaError(BaseModel):
    epsilon: Error
    delta: Error


type TestResults = dict[str, EpsilonDeltaError]
type AccuracyBenchmarkOutput = dict[int, TestResults]
