from pathlib import Path

import matplotlib.pyplot as plt

from .algo import ALGO_NAMES, EPacAlgo, sorted_algos
from .memory import MemoryBenchmarksResults

STAGE_LABELS = ["Before", "After load data", "After execute"]


def _to_mb(kb: list[int]) -> list[float]:
    return [val / 1024 for val in kb]


def build_memory_plots(
    results: dict[EPacAlgo, MemoryBenchmarksResults], output: Path, x_label: str = ""
) -> None:
    fig, axs = plt.subplots(len(results), 2, sharex="col")
    if len(results) == 1:
        vspace_axs = [axs[0]]
        rss_axs = [axs[1]]
    else:
        vspace_axs = [ax[0] for ax in axs]
        rss_axs = [ax[1] for ax in axs]

    for algo_num, algo in enumerate(sorted_algos(results.keys())):
        algo_results = results[algo]
        algo_name = ALGO_NAMES[algo]

        vspace_ax = vspace_axs[algo_num]
        vspace_ax.set_title(algo_name)
        rss_ax = rss_axs[algo_num]
        rss_ax.set_title(algo_name)

        vspace_ax.plot(
            algo_results.axis_x,
            _to_mb(algo_results.vspace_kb.before),
            label=STAGE_LABELS[0],
        )
        vspace_ax.plot(
            algo_results.axis_x,
            _to_mb(algo_results.vspace_kb.after_load),
            label=STAGE_LABELS[1],
        )
        vspace_ax.plot(
            algo_results.axis_x,
            _to_mb(algo_results.vspace_kb.after_execute),
            label=STAGE_LABELS[2],
        )
        vspace_ax.legend()
        if x_label:
            vspace_ax.set_xlabel(x_label)
        vspace_ax.set_ylabel("Peak virtual space, MiB")

        rss_ax.plot(
            algo_results.axis_x,
            _to_mb(algo_results.rss_kb.before),
            label=STAGE_LABELS[0],
        )
        rss_ax.plot(
            algo_results.axis_x,
            _to_mb(algo_results.rss_kb.after_load),
            label=STAGE_LABELS[1],
        )
        rss_ax.plot(
            algo_results.axis_x,
            _to_mb(algo_results.rss_kb.after_execute),
            label=STAGE_LABELS[2],
        )
        rss_ax.legend()
        if x_label:
            rss_ax.set_xlabel(x_label)
        rss_ax.set_ylabel("Peak resident space, MiB")
    fig.tight_layout()
    fig.savefig(output)
