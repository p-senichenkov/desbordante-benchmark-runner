from pathlib import Path

from .algo import EPacAlgo
from .memory import (
    DatasetMeta,
    MemoryBenchmarksResults,
    TestArgs,
    run_memory_benchmarks,
)
from .util import IOWAS_SIZES, prepare_iowas, toksyntax

IOWAS_LOW_ARITIES_TEST_ARGS: dict[EPacAlgo, TestArgs] = {
    EPacAlgo.DOMAIN_PAC: TestArgs(
        indices=[2, 3, 8, 9],
        ctor_args={
            "domain_ctor": 'new pac::model::Ball{std::vector<std::string>{"3", "Good Goods", "40", "John Doe"}, 15}',
            "domain_include": "core/algorithms/pac/model/default_domains/ball.h",
        },
    ),
    EPacAlgo.FD_PAC: TestArgs(indices=([2, 3], [8, 9])),
    EPacAlgo.UCC_PAC: TestArgs(indices=[2, 3, 8, 7]),
}


IOWAS_LOW_ARITIES_DATASETS = [
    DatasetMeta(dataset_const=f"kIowa{toksyntax(size)}", num=size)
    for size in IOWAS_SIZES[:5]
]


def run_iowas_low_arities(
    desbordante_root: Path,
    algorithms: list[EPacAlgo],
) -> dict[EPacAlgo, MemoryBenchmarksResults]:
    prepare_iowas(desbordante_root)
    return run_memory_benchmarks(
        IOWAS_LOW_ARITIES_TEST_ARGS,
        IOWAS_LOW_ARITIES_DATASETS,
        desbordante_root,
        algorithms,
    )
