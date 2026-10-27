from collections.abc import Generator
from pathlib import Path

from ..algo import EPacAlgo
from ..statistics import PlotStats
from ..util import IOWAS_SIZES, prepare_iowas, toksyntax
from .runner import DatasetMeta, run_unified_benchmarks


IOWAS_LOW_ARITIES_EXTRA_PARAMS = {
    EPacAlgo.DOMAIN_PAC: ["{2, 3, 8, 9}", "memory::kIowaLowArityBall"],
    EPacAlgo.FD_PAC: ["{2, 3}", "{8, 9}"],
    EPacAlgo.UCC_PAC: ["{2, 3, 8, 9}"],
}

IOWAS_LOW_ARITIES_DATASETS = [
    DatasetMeta(dataset_const=f"kIowa{toksyntax(size)}", num=size)
    for size in IOWAS_SIZES
]


def run_unified_iowas_low_arities(
    desbordante_root: Path,
    algorithm: EPacAlgo,
    test_from: int,
    test_to: int,
    repeats: int,
) -> Generator[list[PlotStats], None, None]:
    prepare_iowas(desbordante_root)
    return run_unified_benchmarks(
        IOWAS_LOW_ARITIES_EXTRA_PARAMS,
        IOWAS_LOW_ARITIES_DATASETS,
        desbordante_root,
        algorithm,
        test_from,
        test_to,
        repeats,
        "Iowas low arities",
        "rows",
    )
