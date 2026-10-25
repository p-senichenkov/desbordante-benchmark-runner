from pathlib import Path

from ..algo import EPacAlgo
from .runner import DatasetMeta, run_memory_benchmarks
from ..util import IOWAS_SIZES, prepare_iowas, toksyntax
from ..statistics import PlotStats

IOWAS_LOW_ARITIES_EXTRA_PARAMS = {
    EPacAlgo.DOMAIN_PAC: ["{2, 3, 8, 9}", "kIowaLowArityBall"],
    EPacAlgo.FD_PAC: ["{2, 3}", "{8, 9}"],
    EPacAlgo.UCC_PAC: ["{2, 3, 8, 9}"],
}


IOWAS_LOW_ARITIES_DATASETS = [
    DatasetMeta(dataset_const=f"kIowa{toksyntax(size)}", num=size)
    for size in IOWAS_SIZES
]


def run_memory_iowas_low_arities(
    desbordante_root: Path,
    algorithm: EPacAlgo,
    test_count: int,
    repeats: int,
) -> list[PlotStats]:
    prepare_iowas(desbordante_root)
    return run_memory_benchmarks(
        IOWAS_LOW_ARITIES_EXTRA_PARAMS,
        IOWAS_LOW_ARITIES_DATASETS,
        desbordante_root,
        algorithm,
        test_count,
        repeats,
        "Iowas low arities",
        "rows",
    )
