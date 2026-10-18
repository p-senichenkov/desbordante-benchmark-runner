from pathlib import Path

import matplotlib.pyplot as plt

from .algo import ALGO_NAMES
from .statistics import PlotStatstats


def _axis_label(name: str, unit: str) -> str:
    return f"{name}, {unit}" if unit else name


def build_plots(results: list[PlotStatstats], output: Path | None) -> None:
    if not results:
        raise ValueError("The report does not contain any statistics")

    fig, axs = plt.subplots(1, len(results), squeeze=False, figsize=(5 * len(results), 5))
    for ax, result in zip(axs[0], results):
        meta = result.meta
        for line_name, stats in result.values.items():
            values = stats.raw_results
            xs = list(values)
            ys = list(values.values())
            line = ax.plot(xs, ys, marker="o", label=line_name)[0]
            ax.fill_between(
                xs,
                [value - stats.conf_int_half for value in ys],
                [value + stats.conf_int_half for value in ys],
                color=line.get_color(),
                alpha=0.15,
            )
        ax.set_title(f"{ALGO_NAMES[meta.algo]} — {meta.benchmark_name}")
        ax.set_xlabel(_axis_label(meta.axis_x.name, meta.axis_x.unit))
        ax.set_ylabel(_axis_label(meta.axis_y.name, meta.axis_y.unit))
        ax.legend()
    fig.tight_layout()
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output)
    else:
        plt.show()
