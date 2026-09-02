"""Charts.

Three rules are applied throughout:

* one visual system, set once in :func:`apply_style`, instead of per-chart
  styling;
* colour follows the entity, so a segment keeps its hue across every figure;
* meaning never rests on colour alone -- warm/cool hues that survive colour
  vision deficiency, plus hatching and the printed table as a second channel.
"""

from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from . import config as cfg

# Figure counter so captions can be referenced from the narrative.
_FIGURE_N = 0


def apply_style() -> None:
    """Install the project's visual defaults on matplotlib."""
    mpl.rcParams.update(
        {
            "figure.figsize": (10, 5.5),
            "figure.dpi": 110,
            "savefig.dpi": 150,
            "savefig.bbox": "tight",
            "axes.titlesize": 14,
            "axes.titleweight": "semibold",
            "axes.labelsize": 11,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.25,
            "grid.linewidth": 0.6,
            "grid.linestyle": "-",  # solid: dashed grids read as thresholds
            "legend.frameon": False,
            "font.size": 11,
        }
    )


def caption(ax: plt.Axes, text: str) -> None:
    """Add a numbered caption under the axes.

    Args:
        ax: Axes to caption.
        text: Caption body, without the figure number.
    """
    global _FIGURE_N
    _FIGURE_N += 1
    fig = ax.figure
    # Reserve room below the axis labels so the caption never sits on top of
    # them, whatever the figure height.
    fig.tight_layout()
    fig.subplots_adjust(bottom=fig.subplotpars.bottom + 0.11)
    fig.text(
        0.5,
        0.015,
        f"Figura {_FIGURE_N} — {text}",
        ha="center",
        va="bottom",
        fontsize=9.5,
        color="#555555",
        wrap=True,
    )


def reset_figure_numbers() -> None:
    """Restart figure numbering; call once at the top of a full run."""
    global _FIGURE_N
    _FIGURE_N = 0


def weekly_band_chart(
    weekly: pd.DataFrame,
    segment_name: str,
    value_column: str = "sum_all_calories",
    y_label: str = "Calorías quemadas totales",
    title: str = "Calorías quemadas semanales",
    ax: plt.Axes | None = None,
) -> plt.Axes:
    """Median line with an interquartile band, one segment per chart.

    Replaces a per-user "spaghetti" chart. With 15 overlapping lines and the
    legend hidden, colour carried no decodable information; the band shows the
    thing the narrative actually claims -- how consistent the segment is. A
    wide band means erratic, a narrow one means stable.

    Args:
        weekly: Long frame with ``Week_ISO`` and ``value_column``.
        segment_name: Segment being plotted; selects the colour.
        value_column: Metric to summarise.
        y_label: Y-axis label.
        title: Chart title, prefixed with the segment name.
        ax: Existing axes to draw on; a new figure is created when omitted.

    Returns:
        The axes drawn on.
    """
    ax = ax or plt.subplots()[1]
    color = cfg.SEGMENT_COLORS.get(segment_name, "#1D4ED8")

    summary = (
        weekly.groupby("Week_ISO")[value_column]
        .agg(
            p25=lambda s: s.quantile(0.25),
            mediana="median",
            p75=lambda s: s.quantile(0.75),
        )
        .sort_index()
    )

    ax.fill_between(
        summary.index,
        summary["p25"],
        summary["p75"],
        alpha=0.20,
        color=color,
        linewidth=0,
        label="Rango intercuartílico (P25-P75)",
    )
    ax.plot(
        summary.index,
        summary["mediana"],
        color=color,
        linewidth=2,
        marker="o",
        markersize=5,
        label="Mediana",
    )

    ax.set_title(f"{segment_name} — {title}")
    ax.set_xlabel("Semana ISO")
    ax.set_ylabel(y_label)
    ax.set_xticks(sorted(summary.index.unique()))
    ax.legend(loc="best")
    return ax


def weekly_small_multiples(
    weekly: pd.DataFrame,
    segments: dict[str, list],
    metrics: list[tuple[str, str]] | None = None,
) -> plt.Figure:
    """Grid of segments x metrics with a shared y-axis per metric.

    Sharing the y-axis across a row is the point: the previous layout gave
    every segment its own scale, so comparing them by eye produced false
    conclusions.

    Args:
        weekly: Long frame with ``Id``, ``Week_ISO`` and the metric columns.
        segments: Mapping of segment name to ids. Empty segments are skipped.
        metrics: ``(column, label)`` pairs, one row of the grid each.

    Returns:
        The figure containing the grid.
    """
    metrics = metrics or [
        ("sum_all_calories", "Calorías totales"),
        ("mean_steps", "Pasos (promedio)"),
        ("combined_activity_score", "Puntaje de actividad (min. efectivos)"),
    ]
    populated = {name: ids for name, ids in segments.items() if ids}

    fig, axes = plt.subplots(
        len(metrics),
        len(populated),
        figsize=(4.6 * len(populated), 3.4 * len(metrics)),
        sharex=True,
        sharey="row",
        squeeze=False,
    )

    for row, (column, label) in enumerate(metrics):
        for col, (name, ids) in enumerate(populated.items()):
            ax = axes[row][col]
            weekly_band_chart(
                weekly[weekly["Id"].isin(ids)],
                name,
                value_column=column,
                y_label=label if col == 0 else "",
                title="",
                ax=ax,
            )
            ax.set_title(name if row == 0 else "")
            ax.set_xlabel("Semana ISO" if row == len(metrics) - 1 else "")
            ax.get_legend().remove()

    # Neutral swatches: the legend explains the *shape* encoding, while the
    # column title carries the segment identity. Reusing one segment's hue
    # here would suggest the whole grid is that colour.
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    fig.legend(
        handles=[
            Line2D([], [], color="#475569", lw=2, marker="o", label="Mediana"),
            Patch(facecolor="#475569", alpha=0.20, label="Rango intercuartílico (P25-P75)"),
        ],
        loc="lower center",
        ncol=2,
        bbox_to_anchor=(0.5, -0.02),
    )
    fig.suptitle(
        "Consistencia semanal por segmento (mediana y rango intercuartílico)",
        fontsize=15,
        fontweight="semibold",
    )
    fig.tight_layout()
    return fig


def segmentation_heatmap(matrix: pd.DataFrame, ax: plt.Axes | None = None) -> plt.Axes:
    """Users per step-category x intensity-category cell.

    Uses a single-hue ramp because the encoded quantity is magnitude, and a
    white gap rather than a black border between cells. The risk quadrant is
    called out with an annotation instead of by spending the colour scale.

    Args:
        matrix: Counts from :func:`~bellabeat.segmentation.segmentation_matrix`.
        ax: Existing axes; a new figure is created when omitted.

    Returns:
        The axes drawn on.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(9, 5.2))

    sns.heatmap(
        matrix,
        annot=True,
        fmt="g",
        cmap="Blues",
        linewidths=2,
        linecolor="white",
        cbar_kws={"label": "Número de clientes"},
        ax=ax,
    )
    ax.grid(False)  # the global grid would show through the cells
    ax.set_title(
        "Segmentación de clientes: pasos típicos vs. intensidad típica", pad=12
    )
    ax.set_xlabel("Intensidad típica (mediana del puntaje diario)", labelpad=8)
    ax.set_ylabel("Pasos típicos (mediana diaria)")
    # Two-word labels wrap instead of colliding with their neighbours.
    ax.set_xticklabels(
        [t.get_text().replace(" ", "\n") for t in ax.get_xticklabels()], rotation=0
    )
    ax.tick_params(axis="y", rotation=0)

    # Call out the chronic-risk quadrant without recolouring the scale.
    ax.add_patch(
        plt.Rectangle(
            (0, 0),
            len(cfg.INTENSITY_LOW),
            len(cfg.STEPS_LOW),
            fill=False,
            edgecolor="#B45309",
            linewidth=2.5,
            zorder=5,
        )
    )
    ax.text(
        0.08,
        len(cfg.STEPS_LOW) - 0.12,
        "Riesgo crónico",
        color="#B45309",
        fontsize=10,
        fontweight="semibold",
        va="bottom",
    )
    return ax


def intensity_volume_bars(
    volume: pd.DataFrame, ax: plt.Axes | None = None
) -> plt.Axes:
    """Stacked days per step category, split by intensity compliance.

    Args:
        volume: Rows = step categories, columns = intensity labels.
        ax: Existing axes; a new figure is created when omitted.

    Returns:
        The axes drawn on.
    """
    if ax is None:
        _, ax = plt.subplots()

    ordered = volume.reindex(columns=cfg.INTENSITY_LABELS)
    ordered.plot(
        kind="bar",
        stacked=True,
        color=cfg.INTENSITY_RAMP,
        ax=ax,
        width=0.62,
        edgecolor="white",
        linewidth=2,  # surface gap between segments, not a border
        legend=False,
    )

    # Secondary encoding so the chart survives colour-vision deficiency.
    # Kept light: dense hatching on large blocks reads as noise.
    with mpl.rc_context({"hatch.linewidth": 0.5}):
        n_rows = len(ordered)
        for i, container in enumerate(ax.containers):
            hatch = cfg.INTENSITY_HATCHES[i % len(cfg.INTENSITY_HATCHES)]
            for patch in container.patches[:n_rows]:
                patch.set_hatch(hatch)

    ax.set_title("Volumen total de días: pasos típicos vs. calidad de la intensidad")
    ax.set_xlabel("Categoría de pasos típicos (mediana)")
    ax.set_ylabel("Suma total de días registrados")
    ax.tick_params(axis="x", rotation=0)
    ax.grid(axis="x", visible=False)
    # Outside the plot area: inside it covered the tallest bar.
    ax.legend(
        title="Cumplimiento de intensidad",
        loc="upper left",
        bbox_to_anchor=(1.01, 1.0),
    )
    return ax


def cohort_flow_chart(summary: pd.DataFrame, ax: plt.Axes | None = None) -> plt.Axes:
    """Users per cohort, replacing the two-slice completeness pie.

    A pie split 98/2 hides the interesting number. What matters for the
    business is how many users had to be excluded for intermittent use.

    Args:
        summary: Output of :func:`~bellabeat.features.cohort_summary`.
        ax: Existing axes; a new figure is created when omitted.

    Returns:
        The axes drawn on.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(9, 3.4))

    colors = ["#1D4ED8", "#D97706", "#94A3B8"]
    bars = ax.barh(summary.index[::-1], summary["usuarios"][::-1], color=colors[::-1])

    for bar, (name, row) in zip(bars, list(summary.iterrows())[::-1]):
        low, high = int(row["dias_min"]), int(row["dias_max"])
        span = f"{low}" if low == high else f"{low}-{high}"
        ax.text(
            bar.get_width() + 0.3,
            bar.get_y() + bar.get_height() / 2,
            f"{int(row['usuarios'])} usuarios · {row['porcentaje']:.1f} % "
            f"· {span} días",
            va="center",
            fontsize=10,
        )

    ax.set_title("Cohortes por constancia de uso del dispositivo")
    ax.set_xlabel("Número de usuarios")
    ax.set_xlim(0, summary["usuarios"].max() * 1.75)
    ax.grid(axis="y", visible=False)
    return ax


def save(fig_or_ax, filename: str, directory: str = "docs/img") -> str:
    """Write a figure to ``docs/img`` for embedding in the README.

    Args:
        fig_or_ax: A figure or any axes belonging to it.
        filename: File name including extension.
        directory: Destination folder, created if missing.

    Returns:
        The path written.
    """
    from pathlib import Path

    fig = getattr(fig_or_ax, "figure", fig_or_ax)
    Path(directory).mkdir(parents=True, exist_ok=True)
    path = str(Path(directory) / filename)
    fig.savefig(path)
    return path
