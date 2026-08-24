import abc
import typing as tp
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import BaseModel

from .algo import EPacAlgo
from .util import capture, run


class PeakMemoryUsage(BaseModel):
    vspace_kb: int
    rss_kb: int


class AlgoMemoryUsage(BaseModel):
    before: PeakMemoryUsage
    after_load: PeakMemoryUsage
    after_execute: PeakMemoryUsage


type Indices = list[int] | tuple[list[int], list[int]]


class AlgoMeta(abc.ABC):
    include_algo: str
    algo_class: str
    other_options: str = ""
    extra_includes: list[str] = field(default_factory=list)

    @abc.abstractmethod
    def _make_indices_options(self, indices: Indices) -> str: ...

    def make_main(self, dataset_constant: str, indices: Indices) -> str:
        options = (
            f"       {{kCsvConfig, {dataset_constant}}},\n"
            + self._make_indices_options(indices)
            + f"{self.other_options}"
        )

        return (
            '#include "core/algorithms/algo_factory.h"\n'
            '#include "core/config/indices/type.h"\n'
            '#include "core/config/names.h"\n'
            '#include "tests/common/all_csv_configs.h"\n'
            '#include "tests/memory/util.h"\n'
            "\n"
            f'#include "{self.include_algo}"\n'
            + "".join([f'#include "{incl}"\n' for incl in self.extra_includes])
            + "\n"
            "int main() {\n"
            "   using namespace config::names;\n"
            "   using namespace tests;\n"
            "\n"
            "   algos::StdParamsMap options{\n"
            f"      {options}\n"
            "   };\n"
            "\n"
            f"  MeasuredRun<algos::pac_verifier::{self.algo_class}>(options);\n"
            "}\n"
        )


def make_column_indices(indices: Indices) -> str:
    assert isinstance(indices, list)

    indices_str = ", ".join(list(map(str, indices)))
    return f"       {{kColumnIndices, config::IndicesType{{{indices_str}}}}},\n"


class DomainPACVerifierMeta(AlgoMeta):
    include_algo = (
        "core/algorithms/pac/pac_verifier/domain_pac_verifier/domain_pac_verifier.h"
    )
    algo_class = "DomainPACVerifier"

    def __init__(self, domain_ctor: str, domain_include: str | None = None) -> None:
        self.other_options = (
            "       {kDomain,\n"
            "        std::shared_ptr<pac::model::IDomain>(\n"
            f"           {domain_ctor}\n"
            "        )\n"
            "       },"
        )

        self.extra_includes = ["core/algorithms/pac/model/idomain.h"]
        if domain_include is not None:
            self.extra_includes.append(domain_include)

    def _make_indices_options(self, indices: Indices) -> str:
        return make_column_indices(indices)


class FDPACVerifierMeta(AlgoMeta):
    include_algo = "core/algorithms/pac/pac_verifier/fd_pac_verifier/fd_pac_verifier.h"
    algo_class = "FDPACVerifier"

    def _make_indices_options(self, indices: Indices) -> str:
        assert isinstance(indices, tuple)

        lhs_indices_str = ", ".join(list(map(str, indices[0])))
        rhs_indices_str = ", ".join(list(map(str, indices[1])))
        return (
            f"{{kLhsIndices, config::IndicesType{{{lhs_indices_str}}}}},\n"
            f"{{kRhsIndices, config::IndicesType{{{rhs_indices_str}}}}},\n"
        )


class UCCPACVerifierMeta(AlgoMeta):
    include_algo = (
        "core/algorithms/pac/pac_verifier/ucc_pac_verifier/uss_pac_verifier.h"
    )
    algo_class = "UCCPACVerifier"

    def _make_indices_options(self, indices: Indices) -> str:
        return make_column_indices(indices)


ALGO_METAS: dict[EPacAlgo, type[AlgoMeta]] = {
    EPacAlgo.DOMAIN_PAC: DomainPACVerifierMeta,
    EPacAlgo.FD_PAC: FDPACVerifierMeta,
    EPacAlgo.UCC_PAC: UCCPACVerifierMeta,
}


@dataclass
class TestArgs:
    indices: Indices
    ctor_args: dict[str, tp.Any] = field(default_factory=dict)


def _run_memory_bench(
    algo: EPacAlgo,
    test_args_dict: dict[EPacAlgo, TestArgs],
    dataset_const: str,
    desbordante_root: Path,
) -> AlgoMemoryUsage:
    test_args = test_args_dict[algo]
    algo_meta = ALGO_METAS[algo](**test_args.ctor_args)
    main_text = algo_meta.make_main(
        dataset_constant=dataset_const, indices=test_args.indices
    )

    with open(
        desbordante_root / "src" / "tests" / "memory" / "main.cpp", "w"
    ) as main_file:
        main_file.write(main_text)

    (desbordante_root / "build" / "CMakeCache.txt").unlink(missing_ok=True)
    run("cmake", "-B", "build", "-S", desbordante_root, cwd=desbordante_root)
    run(
        "cmake",
        "--build",
        "build",
        "--target",
        "Desbordante.memory_bench",
        cwd=desbordante_root,
    )

    build_target = desbordante_root / "build" / "target"
    assert build_target.is_dir()
    output = capture(build_target / "Desbordante.memory_bench", cwd=build_target)
    return AlgoMemoryUsage.model_validate_json(output)


@dataclass
class DatasetMeta:
    dataset_const: str
    # Some numeric characteristic of dataset (displayed on axis X)
    num: int | float


@dataclass
class MemoryBenchmarksResultsSingleChara:
    before: list[int] = field(default_factory=list)
    after_load: list[int] = field(default_factory=list)
    after_execute: list[int] = field(default_factory=list)


@dataclass
class MemoryBenchmarksResults:
    axis_x: list[int | float] = field(default_factory=list)
    vspace_kb: MemoryBenchmarksResultsSingleChara = field(
        default_factory=MemoryBenchmarksResultsSingleChara
    )
    rss_kb: MemoryBenchmarksResultsSingleChara = field(
        default_factory=MemoryBenchmarksResultsSingleChara
    )


def run_memory_benchmarks(
    test_args_dict: dict[EPacAlgo, TestArgs],
    datasets: list[DatasetMeta],
    desbordante_root: Path,
    algorithms: list[EPacAlgo],
) -> dict[EPacAlgo, MemoryBenchmarksResults]:
    results: dict[EPacAlgo, MemoryBenchmarksResults] = {}

    for algo in algorithms:
        algo_result = MemoryBenchmarksResults()
        for dataset in datasets:
            memory_usage = _run_memory_bench(
                algo, test_args_dict, dataset.dataset_const, desbordante_root
            )
            algo_result.axis_x.append(dataset.num)
            vspace = algo_result.vspace_kb
            vspace.before.append(memory_usage.before.vspace_kb)
            vspace.after_load.append(memory_usage.after_load.vspace_kb)
            vspace.after_execute.append(memory_usage.after_execute.vspace_kb)
            rss = algo_result.rss_kb
            rss.before.append(memory_usage.before.rss_kb)
            rss.after_load.append(memory_usage.after_load.rss_kb)
            rss.after_execute.append(memory_usage.after_execute.rss_kb)
        results[algo] = algo_result

    return results
