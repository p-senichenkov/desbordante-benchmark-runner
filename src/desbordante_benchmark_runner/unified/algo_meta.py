import abc
from dataclasses import dataclass, field

from ..algo import ALGO_CLASSES, EPacAlgo


@dataclass
class AlgorithmMeta:
    algo_class: str
    extra_includes: list[str] = field(default_factory=list)


class AlgoBuilder(abc.ABC):
    COMMON_INCLUDES = ["tests/common/all_csv_configs.h", "tests/memory/algorithms.h"]

    def __init__(self, algo_meta: AlgorithmMeta) -> None:
        self._algo_meta = algo_meta

    def make_main(self, dataset_constant: str, extra_params: list[str]) -> str:
        assert isinstance(self._algo_meta.extra_includes, list)
        includes = sorted(AlgoBuilder.COMMON_INCLUDES + self._algo_meta.extra_includes)
        include_block = "\n".join(f'#include "{incl}"' for incl in includes)

        params = ", ".join([f"tests::{dataset_constant}"] + extra_params)

        return (
            f"{include_block}\n"
            "\n"
            "int main() {\n"
            f"    memory::{self._algo_meta.algo_class}Memory({params});\n"
            "}\n"
        )


ALGO_BUILDERS = {
    EPacAlgo.DOMAIN_PAC: AlgoBuilder(AlgorithmMeta(algo_class="DomainPACVerifier", extra_includes=["tests/memory/domains.h"])),
    EPacAlgo.FD_PAC: AlgoBuilder(AlgorithmMeta(algo_class="FDPACVerifier")),
    EPacAlgo.UCC_PAC: AlgoBuilder(AlgorithmMeta(algo_class="UCCPACVerifier")),
}
