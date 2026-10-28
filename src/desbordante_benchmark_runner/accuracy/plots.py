from contextlib import nullcontext
from pathlib import Path
import re

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator
from matplotlib.widgets import Button

from .report import AccuracyReport, PlotPage


def _axis_label(name: str, unit: str) -> str:
    return f"{name}, {unit}" if unit else name


def _draw_page(
    fig: Figure, section: str, page: PlotPage, *, interactive: bool = False
) -> list[Axes]:
    assert page.plots
    axes = list(fig.subplots(1, len(page.plots), squeeze=False)[0])
    fig.suptitle(f"{section.capitalize()} — {page.name}", fontsize=14)
    line_indices = {
        name: index
        for index, name in enumerate(dict.fromkeys(name for plot in page.plots for name in plot.values))
    }
    handles = {}
    for ax, plot in zip(axes, page.plots):
        assert plot.values
        for line_name, points in plot.values.items():
            assert points
            index = line_indices[line_name]
            xs = sorted(points)
            line = ax.plot(
                xs, [points[x] for x in xs],
                color=f"C{index % 10}",
                linestyle=("--", "-", ":", "-.")[index % 4],
                marker=("x", "o", "s", "^")[index % 4],
                markerfacecolor="none", label=line_name,
            )[0]
            handles.setdefault(line_name, line)
        meta = plot.meta
        ax.set_title(meta.name, fontsize=12)
        ax.set_xlabel(_axis_label(meta.axis_x.name, meta.axis_x.unit), fontsize=11)
        ax.set_ylabel(_axis_label(meta.axis_y.name, meta.axis_y.unit), fontsize=11)
        ax.tick_params(labelsize=10)
        ax.ticklabel_format(axis="y", style="plain", useOffset=False)
        xs = sorted({x for points in plot.values.values() for x in points})
        if len(xs) <= 12:
            ax.set_xticks(xs)
        else:
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax.grid(alpha=0.2)
    columns = min(3, len(handles))
    legend = fig.legend(
        list(handles.values()), list(handles), ncols=columns, fontsize=11,
        loc="lower center" if interactive else "outside lower center",
    )
    if interactive:
        legend.set_bbox_to_anchor((0.5, 0.11))
        legend_rows = (len(handles) + columns - 1) // columns
        fig.subplots_adjust(
            left=0.08, right=0.98, bottom=0.23 + 0.045 * legend_rows, top=0.88, wspace=0.24
        )
    return axes


def _build_page_plot(section: str, page: PlotPage) -> Figure:
    fig = plt.figure(figsize=(max(12, 6 * len(page.plots)), 5), layout="constrained")
    _draw_page(fig, section, page)
    return fig


def _show_pages(pages: list[tuple[str, PlotPage]]) -> None:
    fig = plt.figure(figsize=(12, 6), layout="none")
    axes: list[Axes] = []
    previous = Button(fig.add_axes((0.25, 0.025, 0.15, 0.06)), "Previous")
    next_page = Button(fig.add_axes((0.6, 0.025, 0.15, 0.06)), "Next")
    page_label = fig.text(0.5, 0.055, "", ha="center", va="center", fontsize=11)
    current_page = 0

    def show_page(index: int) -> None:
        nonlocal current_page, axes
        current_page = max(0, min(index, len(pages) - 1))
        for ax in axes:
            ax.remove()
        for legend in list(fig.legends):
            legend.remove()
        section, page = pages[current_page]
        fig.set_size_inches(max(12, 6 * len(page.plots)), 6)
        axes = _draw_page(fig, section, page, interactive=True)
        page_label.set_text(f"{current_page + 1} / {len(pages)}")
        previous.set_active(current_page > 0)
        next_page.set_active(current_page < len(pages) - 1)
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
            show_page(len(pages) - 1)

    previous.on_clicked(lambda event: show_page(current_page - 1))
    next_page.on_clicked(lambda event: show_page(current_page + 1))
    fig.canvas.mpl_connect("key_press_event", on_key)
    show_page(0)
    plt.show()


def build_plots(report: AccuracyReport, output: Path | None) -> None:
    pages = [(section, page) for section, entries in report.root.items() for page in entries]
    assert pages

    if not output:
        _show_pages(pages)
        return

    output.parent.mkdir(parents=True, exist_ok=True)
    with PdfPages(output) as pdf:
        for index, (section, page) in enumerate(pages, start=1):
            fig = _build_page_plot(section, page)
            pdf.savefig(fig)
            plt.close(fig)
