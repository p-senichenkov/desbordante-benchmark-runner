import typing as tp

from pydantic import BaseModel, RootModel, model_validator, AllowInfNan, NonNegativeFloat


type NonNegativeFiniteFloat = tp.Annotated[NonNegativeFloat, AllowInfNan(False)]


class Error(BaseModel):
    baseline: NonNegativeFiniteFloat
    actual: NonNegativeFiniteFloat


class EpsilonDeltaError(BaseModel):
    epsilon: Error
    delta: Error


type TestResults = dict[str, EpsilonDeltaError]


class AccuracyBenchmarkOutput(RootModel[dict[int, TestResults]]):
    @model_validator(mode='after')
    def validate(self) -> tp.Self:
        test_names = None
        for test_res in self.values():
            if test_names is None:
                test_names = test_res.keys()
            else:
                if test_names != test_res.keys():
                    raise ValueError("Test name mismatch")
        return self
