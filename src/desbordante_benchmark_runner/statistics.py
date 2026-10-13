from __future__ import annotations

import typing as tp
from dataclasses import asdict, dataclass
import json

from scipy import stats
import numpy

from .algo import EPacAlgo


@dataclass(frozen=True)
class StatsValues:
    raw_results: dict[float, float]
    normaltest_p_value: float
    shapiro_p_value: float
    mean: float
    std: float
    conf_int_half: float
    dropped_by_iqr: tp.Literal[False] | float


@dataclass(frozen=True)
class AxisMeta:
    name: str
    unit: str


@dataclass(frozen=True)
class StatsMeta:
    algo: EPacAlgo
    benchmark_name: str
    axis_x: AxisMeta
    axis_y: AxisMeta

    def to_dict(self) -> dict[str, tp.Any]:
        dct = asdict(self)
        dct["algo"] = str(dct["algo"])
        return dct

    @staticmethod
    def from_dict(dct: dict[str, tp.Any]) -> "StatsMeta":
        dct["algo"] = EPacAlgo(dct["algo"])
        dct["axis_x"] = AxisMeta(**dct["axis_x"])
        dct["axis_y"] = AxisMeta(**dct["axis_y"])
        return StatsMeta(**dct)


@dataclass(frozen=True)
class Stats:
    meta: StatsMeta
    values: dict[str, StatsValues]

    def _to_dict(self) -> dict[str, tp.Any]:
        return {
                "meta": self.meta.to_dict(),
                "values": {key: asdict(value) for key, value in self.values.items()},
                }

    @staticmethod
    def _from_dict(dct: dict[str, tp.Any]) -> "Stats":
        # JSON object keys are strings.  Keep the in-memory representation useful
        # for matplotlib and preserve the numeric X axis on a load/dump round trip.
        values = {
            name: StatsValues(
                **{
                    **raw_values,
                    "raw_results": {
                        float(x): float(y)
                        for x, y in raw_values["raw_results"].items()
                    },
                }
            )
            for name, raw_values in dct["values"].items()
        }
        return Stats(
                meta=StatsMeta.from_dict(dct["meta"]),
                values=values,
                )

    @staticmethod
    def dump(stats: list[Stats]) -> str:
        lst = [stat._to_dict() for stat in stats]
        return json.dumps(lst, indent=2)

    @staticmethod
    def load(st: str) -> list["Stats"]:
        lst = json.loads(st)
        assert isinstance(lst, list)
        return [Stats._from_dict(stat) for stat in lst]


def _process_results(name: str, results: dict[float, float]) -> StatsValues:
    if not results:
        raise ValueError(f"No results for {name}")

    values = list(map(float, results.values()))
    # normaltest requires at least eight observations and Shapiro at least three.
    # A small benchmark suite is still a valid report; use NaN for inapplicable
    # tests instead of making the complete benchmark fail.
    normaltest_p_value = (
        float(stats.normaltest(values).pvalue) if len(values) >= 8 else float("nan")
    )
    shapiro_p_value = (
        float(stats.shapiro(values).pvalue) if len(values) >= 3 else float("nan")
    )
    dropped_by_iqr = False
    if normaltest_p_value < 0.05 and shapiro_p_value < 0.05 and len(values) >= 4:
        print(f"WARNING: None of normal tests passed for {name}")
        print("Trying to drop outlier")
        # Use interquantile range to determine if outlier can be dropped
        values = sorted(values)
        q25 = numpy.percentile(values, 25)
        q75 = numpy.percentile(values, 75)
        iqr = q75 - q25
        lower = q25 - 1.5 * iqr
        upper = q75 + 1.5 * iqr
        if values[-1] > upper:
            dropped_by_iqr = values[-1]
            del values[-1]
        elif values[0] < lower:
            dropped_by_iqr = values[0]
            del values[0]
        normaltest_p_value = (
            float(stats.normaltest(values).pvalue)
            if len(values) >= 8
            else float("nan")
        )
        shapiro_p_value = (
            float(stats.shapiro(values).pvalue)
            if len(values) >= 3
            else float("nan")
        )
        if normaltest_p_value < 0.05 and shapiro_p_value < 0.05:
            print("!!! Still don't pass !!!")
    mean = float(numpy.mean(values))
    std = float(numpy.std(values, ddof=1)) if len(values) > 1 else 0.0
    conf_int_half = (
        float(stats.t.ppf(0.975, df=len(values) - 1) * stats.sem(values))
        if len(values) > 1
        else 0.0
    )
    return StatsValues(
            raw_results=results,
            normaltest_p_value=normaltest_p_value,
            shapiro_p_value=shapiro_p_value,
            mean=mean,
            std=std,
            conf_int_half=conf_int_half,
            dropped_by_iqr=dropped_by_iqr,
        )


# Process all lines of a single plot.
def process_results(
    results: dict[str, dict[float, float]],
    algo: EPacAlgo,
    axis_x: AxisMeta,
    axis_y: AxisMeta,
    benchmark_name: str,
) -> Stats:
    return Stats(
        meta=StatsMeta(
            algo=algo,
            benchmark_name=benchmark_name,
            axis_x=axis_x,
            axis_y=axis_y,
        ),
        values={
            line_name: _process_results(
                f"{algo!s}, {benchmark_name}, {line_name}", line_results
            )
            for line_name, line_results in results.items()
        },
    )
