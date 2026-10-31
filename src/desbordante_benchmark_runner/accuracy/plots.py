from contextlib import nullcontext
from pathlib import Path
import re
from collections import defaultdict

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator
from matplotlib.widgets import Button

from ..util import check_dict_match

from .plot_data import PlotData, PlotPage, AccuracyPlots


def _build_plot(
    ax: Axes,
    plot_data: PlotData,
    log_x: bool,
    line_indices: dict[str, int],
    axis_x_name: str,
    xs: list[int],
) -> None:
    assert plot_data and all(len(vert) for vert in plot_data)
    assert all(vert.keys() == line_indices.keys() for vert in plot_data)

    points_by_name: dict[str, list[float]] = defaultdict(list)
    for vert in plot_data:
        for line_name, value in vert.items():
            points_by_name[line_name].append(value)
    check_dict_match(points_by_name, lambda x: len(x), "Lengths")

    for line_name, points in points_by_name.items():
        index = line_indices[line_name]
        ax.plot(
            xs,
            points,
            color=f"C{index % 10}",
            linestyle=("--", "-", ":", "-.")[index % 4],
            marker=("x", "o", "s", "^")[index % 4],
            markerfacecolor="none",
            label=line_name,
        )

    if log_x:
        ax.set_xscale("log")
    ax.set_xlabel(axis_x_name)
    ax.legend()


def _get_line_names(data: PlotData) -> list[str]:
    assert all(vert.keys() == data[0].keys() for vert in data)
    return list(data[0].keys())


def _draw_page(
    fig: Figure,
    page: PlotPage,
    log_x: bool,
    interactive: bool,
) -> tuple[Axes, Axes]:
    assert page.epsilon_plot and len(page.epsilon_plot) == len(page.delta_plot)

    eps_ax, delta_ax = fig.subplots(1, 2, squeeze=True)
    fig.suptitle(page.name, fontsize=14)
    line_indices = {name: index for index, name in enumerate(_get_line_names(page.epsilon_plot))}

    _build_plot(eps_ax, page.epsilon_plot, log_x, line_indices, page.axis_x_name, page.axis_x_values)
    _build_plot(delta_ax, page.delta_plot, log_x, line_indices, page.axis_x_name, page.axis_x_values)

    # if interactive:
    #     fig.subplots_adjust(
    #         left=0.08, right=0.98, bottom=0.23 + 0.045 * legend_rows, top=0.88, wspace=0.24
    #     )
    return eps_ax, delta_ax


def _build_page_plot(page: PlotPage, log_x: bool) -> Figure:
    fig = plt.figure(figsize=(max(12, 12), 5), layout="constrained")
    _draw_page(fig, page, log_x, False)
    return fig


# def _show_pages(pages: list[tuple[str, PlotPage]], log_x: bool) -> None:
#     fig = plt.figure(figsize=(12, 6), layout="none")
#     axes: list[Axes] = []
#     previous = Button(fig.add_axes((0.25, 0.025, 0.15, 0.06)), "Previous")
#     next_page = Button(fig.add_axes((0.6, 0.025, 0.15, 0.06)), "Next")
#     page_label = fig.text(0.5, 0.055, "", ha="center", va="center", fontsize=11)
#     current_page = 0
#
#     def show_page(index: int) -> None:
#         nonlocal current_page, axes
#         current_page = max(0, min(index, len(pages) - 1))
#         for ax in axes:
#             ax.remove()
#         for legend in list(fig.legends):
#             legend.remove()
#         section, page = pages[current_page]
#         fig.set_size_inches(max(12, 6 * len(page.plots)), 6)
#         axes = _draw_page(fig, section, page, log_x, interactive=True)
#         page_label.set_text(f"{current_page + 1} / {len(pages)}")
#         previous.set_active(current_page > 0)
#         next_page.set_active(current_page < len(pages) - 1)
#         for button in (previous, next_page):
#             button.label.set_color("black" if button.active else "0.6")
#         if fig.canvas.manager.toolbar:
#             fig.canvas.manager.toolbar.update()
#         fig.canvas.draw_idle()
#
#     def on_key(event) -> None:
#         if event.key in ("left", "pageup"):
#             show_page(current_page - 1)
#         elif event.key in ("right", "pagedown"):
#             show_page(current_page + 1)
#         elif event.key == "home":
#             show_page(0)
#         elif event.key == "end":
#             show_page(len(pages) - 1)
#
#     previous.on_clicked(lambda event: show_page(current_page - 1))
#     next_page.on_clicked(lambda event: show_page(current_page + 1))
#     fig.canvas.mpl_connect("key_press_event", on_key)
#     show_page(0)
#     plt.show()


def build_plots(plots: AccuracyPlots, output: Path | None, log_x: bool) -> None:
    assert plots

    assert output, "Interactive mode is not supported yet"
    # if not output:
    #     _show_pages(pages, log_x)
    #     return

    output.parent.mkdir(parents=True, exist_ok=True)
    with PdfPages(output) as pdf:
        for index, page in enumerate(plots, start=1):
            fig = _build_page_plot(page, log_x)
            pdf.savefig(fig)
            plt.close(fig)
