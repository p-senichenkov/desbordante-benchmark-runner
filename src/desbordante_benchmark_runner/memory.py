import abc
import typing as tp
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import BaseModel

from .algo import ALGO_CLASSES, EPacAlgo
from .util import capture, run, build_desbordante
from .statistics import AxisMeta, PlotStats, process_results


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

        extra_includes = ""
        # Somehow it's `field` sometimes
        if isinstance(self.extra_includes, list) and self.extra_includes:
            extra_includes = "\n".join(
                f'#include "{incl}"' for incl in self.extra_includes
            )

        return (
            '#include "core/algorithms/algo_factory.h"\n'
            '#include "core/config/indices/type.h"\n'
            '#include "core/config/names.h"\n'
            '#include "tests/common/all_csv_configs.h"\n'
            '#include "tests/memory/util.h"\n'
            "\n"
            f'#include "{self.include_algo}"\n'
            f"{extra_includes}"
            "\n"
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
    algo_class = ALGO_CLASSES[EPacAlgo.DOMAIN_PAC]

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
    algo_class = ALGO_CLASSES[EPacAlgo.FD_PAC]

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
        "core/algorithms/pac/pac_verifier/ucc_pac_verifier/ucc_pac_verifier.h"
    )
    algo_class = ALGO_CLASSES[EPacAlgo.UCC_PAC]

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


def _build_memory_bench(
    algo: EPacAlgo,
    test_args_dict: dict[EPacAlgo, TestArgs],
    dataset_const: str,
    desbordante_root: Path,
) -> Path:
    test_args = test_args_dict[algo]
    algo_meta = ALGO_METAS[algo](**test_args.ctor_args)
    main_text = algo_meta.make_main(
        dataset_constant=dataset_const, indices=test_args.indices
    )

    with open(
        desbordante_root / "src" / "tests" / "memory" / "main.cpp", "w"
    ) as main_file:
        main_file.write(main_text)

    return build_desbordante(
        desbordante_root, target="Desbordante.memory_bench"
    )


def _run_memory_bench(build_target: Path) -> AlgoMemoryUsage:
    output = capture(build_target / "Desbordante.memory_bench", cwd=build_target)
    return AlgoMemoryUsage.model_validate_json(output)


@dataclass
class DatasetMeta:
    dataset_const: str
    # Some numeric characteristic of dataset (displayed on axis X)
    num: int


@dataclass
class MemoryBenchmarksResultsSingleChara:
    # Currently ignored. TODO: remove
    before: list[list[float]] = field(default_factory=list)
    after_load: list[list[float]] = field(default_factory=list)
    after_execute: list[list[float]] = field(default_factory=list)


@dataclass
class MemoryBenchmarksResults:
    axis_x: list[int] = field(default_factory=list)
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
    algorithm: EPacAlgo,
    test_count: int,
    repeats: int,
) -> MemoryBenchmarksResults:
    assert repeats >= 3

    algo_result = MemoryBenchmarksResults()
    for dataset in datasets[:test_count]:
        build_target = _build_memory_bench(
            algorithm, test_args_dict, dataset.dataset_const, desbordante_root
        )
        samples = []
        for repeat in range(repeats):
            print(
                f"Running {algorithm}, {dataset.dataset_const} "
                f"({repeat + 1} / {repeats})... ",
                end="",
                flush=True,
            )
            samples.append(_run_memory_bench(build_target))
            print("done")
        algo_result.axis_x.append(dataset.num)
        for metric in ("vspace_kb", "rss_kb"):
            metric_results = getattr(algo_result, metric)
            metric_results.after_load.append(
                [getattr(sample.after_load, metric) for sample in samples]
            )
            metric_results.after_execute.append(
                [getattr(sample.after_execute, metric) for sample in samples]
            )
    return algo_result


VSPACE_Y_META = AxisMeta(name="Peak virtual space", unit="KiB")
RSS_Y_META = AxisMeta(name="Peak resident space", unit="KiB")


def process_memory_benchmark_results(
    results: MemoryBenchmarksResults,
    algorithm: EPacAlgo,
    benchmark_name: str,
    dataset_size_unit: str,
) -> list[PlotStats]:
    def _make_values(ys: list[list[float]]) -> dict[int, list[float]]:
        assert len(ys) == len(results.axis_x)
        return {x: y for x, y in zip(results.axis_x, ys)}

    x_meta = AxisMeta(name="Dataset size", unit=dataset_size_unit)

    return [
        process_results(
            {
                "After load data": _make_values(results.vspace_kb.after_load),
                "After execute": _make_values(results.vspace_kb.after_execute),
            },
            algorithm,
            x_meta,
            VSPACE_Y_META,
            benchmark_name,
        ),
        process_results(
            {
                "After load data": _make_values(results.rss_kb.after_load),
                "After execute": _make_values(results.rss_kb.after_execute),
            },
            algorithm,
            x_meta,
            RSS_Y_META,
            benchmark_name,
        ),
    ]
