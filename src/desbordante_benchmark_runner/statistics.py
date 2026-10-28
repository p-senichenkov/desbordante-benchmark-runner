import typing as tp
from dataclasses import dataclass


@dataclass(frozen=True)
class AxisMeta:
    name: str
    unit: str
