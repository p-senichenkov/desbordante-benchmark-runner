from pydantic import BaseModel


class Error(BaseModel):
    baseline: float
    actual: float


class EpsilonDeltaError(BaseModel):
    epsilon: Error
    delta: Error


type TestResults = dict[str, EpsilonDeltaError]
type AccuracyBenchmarkOutput = dict[int, TestResults]
