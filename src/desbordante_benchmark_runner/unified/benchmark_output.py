from pydantic import BaseModel


class PeakMemoryUsage(BaseModel):
    vspace_kb: int
    rss_kb: int


class AlgoMemoryUsage(BaseModel):
    before: PeakMemoryUsage
    after_load: PeakMemoryUsage
    after_execute: PeakMemoryUsage


class AlgoRunTime(BaseModel):
    load_data: int
    execute: int


class UnifiedBenchmarkOutput(BaseModel):
    memory: AlgoMemoryUsage
    time: AlgoRunTime
