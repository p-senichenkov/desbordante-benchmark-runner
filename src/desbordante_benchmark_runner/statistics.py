import typing as tp
from dataclasses import asdict, dataclass
import json
import os
import platform

from scipy import stats
import numpy
import math

from .algo import EPacAlgo


def _system_info() -> dict[str, tp.Any]:
    return {
        "logical_cpu_count": os.cpu_count(),
        "total_physical_ram_bytes": (
            os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
        ),
        "uname": platform.uname()._asdict(),
    }


@dataclass(frozen=True)
class PointValues:
    """Values for a single point on X axis"""

    raw_results: list[float]
    normaltest_p_value: float
    shapiro_p_value: float
    mean: float
    std: float
    conf_int_half: float
    dropped_by_iqr: tp.Literal[False] | float


# Values for a single line
type LineValues = dict[int, PointValues]


# All lines displayed on a single plot
type Lines = dict[str, LineValues]


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
class PlotStats:
    """Everything that is displayed on a single plot"""

    meta: StatsMeta
    values: Lines

    def _to_dict(self) -> dict[str, tp.Any]:
        return {
                "meta": self.meta.to_dict(),
                "values": {key: {str(x): asdict(point_values) for x, point_values in value.items()} for key, value in self.values.items()},
                }

    @staticmethod
    def _from_dict(dct: dict[str, tp.Any]) -> "PlotStats":
        def _line_values_from_dict(dct: dict[str, tp.Any]) -> LineValues:
            return {int(x): PointValues(**y_values) for x, y_values in dct.items()}

        values = {
            name: _line_values_from_dict(line_values)
            for name, line_values in dct["values"].items()
        }
        return PlotStats(
                meta=StatsMeta.from_dict(dct["meta"]),
                values=values,
                )

    @staticmethod
    def dump(stats: list["PlotStats"]) -> str:
        return json.dumps(
            {
                "system_info": _system_info(),
                "benchmarks": [stat._to_dict() for stat in stats],
            },
            indent=2,
        )

    @staticmethod
    def load(st: str) -> list["PlotStats"]:
        report = json.loads(st)
        lst = report["benchmarks"]
        assert isinstance(lst, list)
        return [PlotStats._from_dict(stat) for stat in lst]


def _process_results(name: str, results: list[float]) -> PointValues:
    assert len(results) >= 3

    normaltest_p_value = 0.0
    shapiro_p_value = 0.0

    def _normaltest(results: list[float]) -> bool:
        nonlocal normaltest_p_value, shapiro_p_value

        if min(results) == max(results):
            normaltest_p_value = shapiro_p_value = math.nan
            return True

        normaltest_p_value = float(stats.normaltest(results).pvalue) if len(results) >= 8 else math.nan
        shapiro_p_value = float(stats.shapiro(results).pvalue)

        return normaltest_p_value >= 0.05 and (shapiro_p_value is math.nan or shapiro_p_value >= 0.05)



    dropped_by_iqr = False
    if not _normaltest(results) and len(results) >= 4:
        print(f"WARNING: None of normal tests passed for {name}")
        print("Trying to drop outlier")
        # Use interquantile range to determine if outlier can be dropped
        results.sort()
        q25 = numpy.percentile(results, 25)
        q75 = numpy.percentile(results, 75)
        iqr = q75 - q25
        lower = q25 - 1.5 * iqr
        upper = q75 + 1.5 * iqr
        if results[-1] > upper:
            dropped_by_iqr = results[-1]
            del results[-1]
        elif results[0] < lower:
            dropped_by_iqr = results[0]
            del results[0]
        if _normaltest(results):
            print("!!! Still don't pass !!!")
    mean = float(numpy.mean(results))
    std = float(numpy.std(results, ddof=1))
    conf_int_half = float(stats.t.ppf(0.975, df=len(results) - 1) * stats.sem(results))
    return PointValues(
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
    results: dict[str, dict[int, list[float]]],
    algo: EPacAlgo,
    axis_x: AxisMeta,
    axis_y: AxisMeta,
    benchmark_name: str,
) -> PlotStats:
    return PlotStats(
        meta=StatsMeta(
            algo=algo,
            benchmark_name=benchmark_name,
            axis_x=axis_x,
            axis_y=axis_y,
        ),
        values={
            line_name: {x: _process_results(
                f"{algo!s}, {benchmark_name}, {line_name}, x={x}", y_values
            ) for x, y_values in line_results.items()}
            for line_name, line_results in results.items()
        },
    )
