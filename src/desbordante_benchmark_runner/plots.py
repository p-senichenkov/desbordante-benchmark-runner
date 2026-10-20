from pathlib import Path

import matplotlib.pyplot as plt

from .algo import ALGO_NAMES
from .statistics import PlotStats


def _axis_label(name: str, unit: str) -> str:
    return f"{name}, {unit}" if unit else name


def build_plots(results: list[PlotStats], output: Path | None) -> None:
    assert results

    fig, axs = plt.subplots(1, len(results), squeeze=False, figsize=(5 * len(results), 5))
    for ax, result in zip(axs[0], results):
        meta = result.meta
        for line_name, points in result.values.items():
            xs = sorted(points)
            ys = [points[x].mean for x in xs]
            line = ax.plot(xs, ys, marker="o", label=line_name)[0]
            ax.fill_between(
                xs,
                [points[x].mean - points[x].conf_int_half for x in xs],
                [points[x].mean + points[x].conf_int_half for x in xs],
                color=line.get_color(),
                alpha=0.15,
                label=f"{line_name}: 95% CI",
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
