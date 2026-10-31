import typing as tp

from pydantic import BaseModel, model_validator


type Vertical = dict[str, float]
type PlotData = list[Vertical]


class PlotPage(BaseModel):
    name: str

    axis_x_name: str
    axis_x_values: list[int]

    epsilon_plot: PlotData
    delta_plot: PlotData

    @model_validator(mode='after')
    def validate(self) -> tp.Self:  # type: ignore[assignment]
        if len(self.axis_x_values) != len(self.epsilon_plot):
            raise ValueError("Incorrect epsilon plot length")
        if len(self.axis_x_values) != len(self.delta_plot):
            raise ValueError("Incorrect delta plot length")
        return self


type AccuracyPlots = list[PlotPage]
