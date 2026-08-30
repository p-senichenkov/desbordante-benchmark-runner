from pathlib import Path

import matplotlib.pyplot as plt

from .algo import ALGO_NAMES, EPacAlgo, sorted_algos
from .timed import TimedBenchmarksResults


def _to_s(ms: list[int]) -> list[float]:
    return [val / 1000 for val in ms]


def build_timed_plots(
    results: dict[EPacAlgo, TimedBenchmarksResults], output: Path, x_label: str = ""
) -> None:
    fig, axs = plt.subplots(len(results), 1, sharex="col")
    if len(results) == 1:
        axs = [axs]

    for algo_num, algo in enumerate(sorted_algos(results.keys())):
        algo_results = results[algo]
        algo_name = ALGO_NAMES[algo]

        ax = axs[algo_num]
        ax.set_title(algo_name)

        ax.plot(algo_results.keys(), algo_results.values())
        if x_label:
            ax.set_xlabel(x_label)
        ax.set_ylabel("Run time, sec")
    fig.tight_layout()
    fig.savefig(output)
