"""Tests for the charting layer.

Charts are checked for the properties the analysis depends on -- the data that
reaches the axes, the ordering, the accessibility guarantees -- not for their
appearance.
"""

import matplotlib

matplotlib.use("Agg")  # no display needed in CI

import matplotlib.pyplot as plt
import pandas as pd
import pytest

from bellabeat import config as cfg
from bellabeat import plots


@pytest.fixture(autouse=True)
def _close_figures():
    plots.apply_style()
    plots.reset_figure_numbers()
    yield
    plt.close("all")


@pytest.fixture
def weekly():
    rows = []
    for user in (1, 2, 3):
        for week in range(11, 19):
            rows.append(
                {
                    "Id": user,
                    "Week_ISO": week,
                    "sum_all_calories": 10000 + 500 * user + week,
                    "mean_steps": 5000 * user,
                    "combined_activity_score": 100 * user + week,
                }
            )
    return pd.DataFrame(rows)


def test_style_removes_the_top_and_right_spines():
    plots.apply_style()
    assert matplotlib.rcParams["axes.spines.top"] is False
    assert matplotlib.rcParams["axes.spines.right"] is False
    # Dashed grids read as thresholds; the grid must stay solid and recessive.
    assert matplotlib.rcParams["grid.linestyle"] == "-"
    assert matplotlib.rcParams["grid.alpha"] < 0.5


def test_band_chart_plots_the_median_not_the_raw_users(weekly):
    """One median line plus one band -- never one line per user."""
    ax = plots.weekly_band_chart(weekly, "Saludable")
    assert len(ax.lines) == 1, "debería haber una sola línea (la mediana)"
    assert len(ax.collections) == 1, "debería haber una sola banda (P25-P75)"

    median_y = ax.lines[0].get_ydata()
    expected = weekly.groupby("Week_ISO")["sum_all_calories"].median().sort_index()
    assert list(median_y) == list(expected)


def test_band_chart_uses_the_segment_colour(weekly):
    """Colour follows the entity, so a segment keeps its hue across figures."""
    for segment, colour in cfg.SEGMENT_COLORS.items():
        ax = plots.weekly_band_chart(weekly, segment)
        assert ax.lines[0].get_color() == colour
        plt.close("all")


def test_band_chart_ticks_are_sorted(weekly):
    shuffled = weekly.sample(frac=1, random_state=0)
    ax = plots.weekly_band_chart(shuffled, "Saludable")
    ticks = list(ax.get_xticks())
    assert ticks == sorted(ticks)


def test_small_multiples_share_the_y_axis_per_row(weekly):
    """The whole point of the grid: segments must be comparable by eye."""
    segments = {"Sedentario": [1], "Viajero": [], "Fuerte": [2], "Saludable": [3]}
    fig = plots.weekly_small_multiples(weekly, segments)

    axes = fig.get_axes()
    assert len(axes) == 3 * 3, "3 métricas x 3 segmentos poblados (Viajero está vacío)"

    for row in range(3):
        row_axes = axes[row * 3 : (row + 1) * 3]
        limits = {ax.get_ylim() for ax in row_axes}
        assert len(limits) == 1, "los paneles de una fila deben compartir escala"


def test_small_multiples_skips_empty_segments(weekly):
    segments = {"Sedentario": [1], "Viajero": [], "Fuerte": [], "Saludable": [3]}
    fig = plots.weekly_small_multiples(weekly, segments)
    titles = [ax.get_title() for ax in fig.get_axes() if ax.get_title()]
    assert "Viajero" not in titles and "Fuerte" not in titles


def test_heatmap_keeps_the_declared_category_order():
    matrix = pd.DataFrame(
        [[1, 0, 0, 0]] * 5, index=cfg.STEPS_LABELS, columns=cfg.INTENSITY_LABELS
    )
    ax = plots.segmentation_heatmap(matrix)
    ylabels = [t.get_text() for t in ax.get_yticklabels()]
    assert ylabels == cfg.STEPS_LABELS
    # Long labels are wrapped, not rotated into a collision.
    xlabels = [t.get_text().replace("\n", " ") for t in ax.get_xticklabels()]
    assert xlabels == cfg.INTENSITY_LABELS
    assert all(t.get_rotation() == 0 for t in ax.get_xticklabels())


def test_stacked_bars_carry_a_secondary_encoding():
    """Meaning must not rest on colour alone."""
    volume = pd.DataFrame(
        [[10, 20, 30, 40]] * 5, index=cfg.STEPS_LABELS, columns=cfg.INTENSITY_LABELS
    )
    ax = plots.intensity_volume_bars(volume)

    hatches = {
        patch.get_hatch()
        for container in ax.containers
        for patch in container.patches[: len(volume)]
    }
    assert len(hatches) > 1, "los segmentos deben distinguirse también por trama"

    colours = [c.patches[0].get_facecolor() for c in ax.containers]
    assert len(set(colours)) == len(cfg.INTENSITY_LABELS)


def test_stacked_bars_stack_in_the_declared_order():
    volume = pd.DataFrame(
        [[10, 20, 30, 40]] * 5,
        index=cfg.STEPS_LABELS,
        # Deliberately shuffled: the function must reorder.
        columns=cfg.INTENSITY_LABELS[::-1],
    )
    ax = plots.intensity_volume_bars(volume)
    legend_labels = [t.get_text() for t in ax.get_legend().get_texts()]
    assert legend_labels == cfg.INTENSITY_LABELS


def test_cohort_chart_labels_every_bar(tmp_path):
    summary = pd.DataFrame(
        [
            {"cohorte": "Uso activo", "usuarios": 26, "dias_min": 57, "dias_max": 62,
             "porcentaje": 74.3},
            {"cohorte": "Uso poco recurrente", "usuarios": 5, "dias_min": 49,
             "dias_max": 55, "porcentaje": 14.3},
            {"cohorte": "Muy poco uso", "usuarios": 4, "dias_min": 20, "dias_max": 20,
             "porcentaje": 11.4},
        ]
    ).set_index("cohorte")

    ax = plots.cohort_flow_chart(summary)
    texts = [t.get_text() for t in ax.texts]
    assert len(texts) == 3
    assert any("26 usuarios" in t for t in texts)
    # A single-value range collapses instead of reading "20-20 días".
    assert any("20 días" in t and "20-20" not in t for t in texts)


def test_captions_are_numbered_sequentially(weekly):
    ax1 = plots.weekly_band_chart(weekly, "Saludable")
    plots.caption(ax1, "primera")
    ax2 = plots.weekly_band_chart(weekly, "Sedentario")
    plots.caption(ax2, "segunda")

    assert any("Figura 1" in t.get_text() for t in ax1.figure.texts)
    assert any("Figura 2" in t.get_text() for t in ax2.figure.texts)

    plots.reset_figure_numbers()
    ax3 = plots.weekly_band_chart(weekly, "Fuerte")
    plots.caption(ax3, "reiniciada")
    assert any("Figura 1" in t.get_text() for t in ax3.figure.texts)


def test_save_writes_the_file_and_returns_its_path(weekly, tmp_path):
    ax = plots.weekly_band_chart(weekly, "Saludable")
    path = plots.save(ax, "prueba.png", str(tmp_path))
    assert (tmp_path / "prueba.png").exists()
    assert path.endswith("prueba.png")
