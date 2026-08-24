import typing as tp
from pathlib import Path

import matplotlib.pyplot as plt

from .algo import ALGO_NAMES, EPacAlgo
from .memory import MemoryBenchmarksResults

STAGE_LABELS = ["Before", "After load data", "After execute"]


def _sorted_algos(algos: tp.Iterable[EPacAlgo]) -> list[EPacAlgo]:
    result: list[EPacAlgo] = []
    for algo in EPacAlgo:
        if algo in algos:
            result.append(algo)
    return result


def build_memory_plots(
    results: dict[EPacAlgo, MemoryBenchmarksResults], output: Path
) -> None:
    fig, axs = plt.subplots(len(results), 2, sharex="col", sharey="row")
    if len(results) == 1:
        vspace_axs = [axs[0]]
        rss_axs = [axs[1]]
    else:
        vspace_axs = [ax[0] for ax in axs]
        rss_axs = [ax[1] for ax in axs]

    # So that they appear in order
    for algo_num, algo in enumerate(_sorted_algos(results.keys())):
        algo_results = results[algo]
        algo_name = ALGO_NAMES[algo]

        vspace_ax = vspace_axs[algo_num]
        vspace_ax.set_title(f"{algo_name}, peak virtual space usage")
        rss_ax = rss_axs[algo_num]
        rss_ax.set_title(f"{algo_name}, peak resident space size")

        vspace_ax.plot(
            algo_results.axis_x, algo_results.vspace_kb.before, label=STAGE_LABELS[0]
        )
        vspace_ax.plot(
            algo_results.axis_x,
            algo_results.vspace_kb.after_load,
            label=STAGE_LABELS[1],
        )
        vspace_ax.plot(
            algo_results.axis_x,
            algo_results.vspace_kb.after_execute,
            label=STAGE_LABELS[2],
        )

        rss_ax.plot(
            algo_results.axis_x, algo_results.rss_kb.before, label=STAGE_LABELS[0]
        )
        rss_ax.plot(
            algo_results.axis_x, algo_results.rss_kb.after_load, label=STAGE_LABELS[1]
        )
        rss_ax.plot(
            algo_results.axis_x,
            algo_results.rss_kb.after_execute,
            label=STAGE_LABELS[2],
        )
    fig.tight_layout()
    fig.savefig(output)
