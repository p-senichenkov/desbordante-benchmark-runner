import typing as tp
from dataclasses import dataclass, asdict
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
    values: StatsValues

    def _to_dict(self) -> dict[str, tp.Any]:
        return {
                "meta": self.meta.to_dict(),
                "values": asdict(self.values),
                }

    @staticmethod
    def _from_dict(dct: dict[str, tp.Any]) -> "Stats":
        return Stats(
                meta=StatsMeta.from_dict(dct["meta"]),
                values=StatsValues(**dct["values"]),
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
    normaltest_p_value = float(stats.normaltest(results.values()).pvalue)
    shapiro_p_value = float(stats.shapiro(results.values()).pvalue)
    dropped_by_iqr = False
    if normaltest_p_value < 0.05 and shapiro_p_value < 0.05:
        print(f"WARNING: None of normal tests passed for {name}")
        print("Trying to drop outlier")
        # Use interquantile range to determine if outlier can be dropped
        values = sorted(results.values())
        q25 = numpy.percentile(values, 25)
        q75 = numpy.percentile(values, 75)
        iqr = q75 - q25
        lower = q25 - 1.5 * iqr
        upper = q75 - 1.5 * iqr
        if values[-1] > upper:
            dropped_by_iqr = values[-1]
            del values[-1]
        elif values[0] < lower:
            dropped_by_iqr = values[0]
            del values[0]
        normaltest_p_value = float(stats.normaltest(values).pvalue)
        shapiro_p_value = float(stats.shapiro(values).pvalue)
        if normaltest_p_value < 0.05 and shapiro_p_value < 0.05:
            print("!!! Still don't pass !!!")
    mean = float(numpy.mean(values))
    std = float(numpy.std(values, ddof=1))
    conf_int_half = stats.t.ppf(0.975, df=len(values) - 1) * stats.sem(values)
    return StatsValues(
            raw_results=results,
            normaltest_p_value=normaltest_p_value,
            shapiro_p_value=shapiro_p_value,
            mean=mean,
            std=std,
            conf_int_half=conf_int_half,
            dropped_by_iqr=dropped_by_iqr,
        )


# Process results from a single benchmark (may have multiple Y-axis lines)
def process_results(results: dict[AxisMeta, dict[float, float]], algo: EPacAlgo, axis_x: AxisMeta, benchmark_name: str) -> list[Stats]:
    return [
        Stats(
            meta=StatsMeta(
                algo=algo,
                benchmark_name=benchmark_name,
                axis_x=axis_x,
                axis_y=axis_y,
            ),
            values=_process_results(f"{algo!s}, {benchmark_name}", res),
        )
        for axis_y, res in results.items()
    ]
