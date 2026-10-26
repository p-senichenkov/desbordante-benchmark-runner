from contextlib import nullcontext
from pathlib import Path
import re

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator
from matplotlib.widgets import Button

from .report import AccuracyReport


def _build_test_plot(
    report: AccuracyReport, numerics: list[int], test_name: str, *, interactive: bool = False
) -> Figure:
    fig, axes = plt.subplots(
        1, 2, figsize=(12, 5), layout="none" if interactive else "constrained"
    )
    fig.suptitle(test_name, fontsize=14)
    for ax, metric in zip(axes, ("epsilon", "delta")):
        pairs = [getattr(report.benchmarks[numeric][test_name], metric) for numeric in numerics]
        ax.plot(
            numerics, [pair.baseline for pair in pairs],
            color="black", linestyle="--", marker="x",
            label=f"Baseline ({report.baseline_algorithm})",
        )
        ax.plot(
            numerics, [pair.actual for pair in pairs],
            marker="o", markerfacecolor="none",
            label=f"Tested ({report.tested_algorithm})",
        )
        ax.set_title(metric.capitalize(), fontsize=12)
        ax.set_xlabel(report.parameter_name, fontsize=11)
        ax.set_ylabel(metric.capitalize(), fontsize=11)
        ax.tick_params(labelsize=10)
        ax.ticklabel_format(axis="y", style="plain", useOffset=False)
        if len(numerics) <= 12:
            ax.set_xticks(numerics)
        else:
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax.grid(alpha=0.2)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncols=2, fontsize=11)
    return fig


def _show_test_plots(report: AccuracyReport, numerics: list[int], test_names: list[str]) -> None:
    fig = _build_test_plot(report, numerics, test_names[0], interactive=True)
    axes = list(fig.axes)
    fig.set_size_inches(12, 6)
    fig.subplots_adjust(left=0.08, right=0.98, bottom=0.27, top=0.88, wspace=0.24)
    fig.legends[0].set_loc("lower center")
    fig.legends[0].set_bbox_to_anchor((0.5, 0.11))

    previous = Button(fig.add_axes((0.25, 0.025, 0.15, 0.06)), "Previous")
    next_page = Button(fig.add_axes((0.6, 0.025, 0.15, 0.06)), "Next")
    page_label = fig.text(0.5, 0.055, "", ha="center", va="center", fontsize=11)
    current_page = 0

    def show_page(index: int) -> None:
        nonlocal current_page
        current_page = max(0, min(index, len(test_names) - 1))
        test_name = test_names[current_page]
        fig.suptitle(test_name, fontsize=14)
        for ax, metric in zip(axes, ("epsilon", "delta")):
            pairs = [getattr(report.benchmarks[numeric][test_name], metric) for numeric in numerics]
            ax.lines[0].set_ydata([pair.baseline for pair in pairs])
            ax.lines[1].set_ydata([pair.actual for pair in pairs])
            ax.relim()
            ax.autoscale(enable=True)
        page_label.set_text(f"{current_page + 1} / {len(test_names)}")
        previous.set_active(current_page > 0)
        next_page.set_active(current_page < len(test_names) - 1)
        for button in (previous, next_page):
            button.label.set_color("black" if button.active else "0.6")
        if fig.canvas.manager.toolbar:
            fig.canvas.manager.toolbar.update()
        fig.canvas.draw_idle()

    def on_key(event) -> None:
        if event.key in ("left", "pageup"):
            show_page(current_page - 1)
        elif event.key in ("right", "pagedown"):
            show_page(current_page + 1)
        elif event.key == "home":
            show_page(0)
        elif event.key == "end":
            show_page(len(test_names) - 1)

    previous.on_clicked(lambda event: show_page(current_page - 1))
    next_page.on_clicked(lambda event: show_page(current_page + 1))
    fig.canvas.mpl_connect("key_press_event", on_key)
    show_page(0)
    plt.show()


def build_plots(report: AccuracyReport, output: Path | None) -> None:
    numerics = sorted(report.benchmarks)
    assert numerics
    test_names = sorted(report.benchmarks[numerics[0]])
    assert test_names
    assert all(set(tests) == set(test_names) for tests in report.benchmarks.values())

    if not output:
        _show_test_plots(report, numerics, test_names)
        return

    output.parent.mkdir(parents=True, exist_ok=True)
    with PdfPages(output) if output and output.suffix.lower() == ".pdf" else nullcontext() as pdf:
        for index, test_name in enumerate(test_names, start=1):
            fig = _build_test_plot(report, numerics, test_name)
            if pdf:
                pdf.savefig(fig)
            elif output:
                safe_name = re.sub(r"[^A-Za-z0-9._-]+", "-", test_name).strip(".") or "test"
                plot_path = output.with_name(f"{output.stem}-{index:02d}-{safe_name}{output.suffix}")
                fig.savefig(plot_path, dpi=150)
            if output:
                plt.close(fig)
