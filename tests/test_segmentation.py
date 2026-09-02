"""Tests for the segmentation, including the empty-quadrant case that broke
the previous positional implementation."""

import pandas as pd
import pytest

from bellabeat import config as cfg
from bellabeat import segmentation


def _users(rows):
    """Build a categorised user frame from ``(id, median_steps, median_score)``."""
    df = pd.DataFrame(
        rows, columns=["Id", "median_steps", "median_activity_score"]
    ).set_index("Id")
    return segmentation.categorize_users(df)


def test_categories_use_left_inclusive_edges():
    users = _users([(1, 0, 0), (2, 2735, 22), (3, 10000, 43), (4, 2734, 21)])
    assert users.loc[1, "steps_category"] == "Sedentario"
    assert users.loc[2, "steps_category"] == "Mínimo"
    assert users.loc[3, "steps_category"] == "Muy activo"
    assert users.loc[4, "steps_category"] == "Sedentario"
    assert users.loc[2, "intensity_category"] == "Mínimo saludable"
    assert users.loc[3, "intensity_category"] == "Objetivo máximo"


def test_each_quadrant_receives_the_right_users():
    users = _users(
        [
            (1, 1000, 5),  # pocos pasos, baja intensidad -> Sedentario
            (2, 12000, 5),  # muchos pasos, baja intensidad -> Viajero
            (3, 1000, 60),  # pocos pasos, alta intensidad -> Fuerte
            (4, 12000, 60),  # muchos pasos, alta intensidad -> Saludable
        ]
    )
    segments = segmentation.assign_segments(users)
    assert segments == {
        "Sedentario": [1],
        "Viajero": [2],
        "Fuerte": [3],
        "Saludable": [4],
    }


def test_empty_quadrant_does_not_shift_the_others():
    """The regression test for the positional-slicing bug.

    Nobody here falls in 'Mínimo saludable' or 'Objetivo óptimo', so a
    ``groupby(observed=True)`` pivot loses two columns. Selecting by position
    would then classify high-intensity users as low-intensity.
    """
    users = _users([(1, 1000, 0), (2, 1000, 90), (3, 12000, 90)])
    segments = segmentation.assign_segments(users)

    assert segments["Sedentario"] == [1]
    assert segments["Fuerte"] == [2]  # NOT swallowed into 'Sedentario'
    assert segments["Saludable"] == [3]
    assert segments["Viajero"] == []


def test_segments_partition_the_users():
    users = _users([(i, 1000 * i, 10 * i) for i in range(1, 12)])
    segments = segmentation.assign_segments(users)
    assigned = [uid for ids in segments.values() for uid in ids]
    assert sorted(assigned) == sorted(users.index.tolist())
    assert len(set(assigned)) == len(assigned)


def test_uncategorisable_user_raises_instead_of_disappearing():
    """A NaN median leaves a user outside every category; that must fail loudly."""
    users = _users([(1, 1000, 10), (2, float("nan"), 10)])
    with pytest.raises(AssertionError, match="no cubre a todos"):
        segmentation.assign_segments(users)


def test_matrix_keeps_every_declared_category():
    users = _users([(1, 1000, 0), (2, 12000, 90)])
    matrix = segmentation.segmentation_matrix(users)
    assert list(matrix.index) == cfg.STEPS_LABELS
    assert list(matrix.columns) == cfg.INTENSITY_LABELS
    assert matrix.to_numpy().sum() == 2


def test_flag_aggregation_keeps_unobserved_step_categories():
    """Empty step categories must survive the aggregation, not vanish.

    ``groupby(observed=True)`` drops them, so a later ``.loc[STEPS_LOW]``
    raises KeyError on any dataset where a category happens to be empty.
    """
    users = _users([(1, 1000, 5), (2, 12000, 60)])  # only Sedentario + Muy activo
    for flag in cfg.INTENSITY_FLAGS:
        users[flag] = 1

    totals = segmentation.flags_by_steps_category(users, "sum")
    assert list(totals.index) == cfg.STEPS_LABELS
    assert list(totals.columns) == cfg.INTENSITY_LABELS
    assert totals.loc["Mínimo"].sum() == 0  # empty category, zero days
    # The selection that used to raise:
    assert totals.loc[cfg.STEPS_LOW, cfg.INTENSITY_LABELS[0]].sum() == 1

    medians = segmentation.flags_by_steps_category(users, "median")
    assert medians.loc["Mínimo"].isna().all()  # no users -> no median, not 0


def test_sizes_report_counts_alongside_percentages():
    segments = {"Sedentario": [1, 2], "Viajero": [], "Fuerte": [3], "Saludable": [4]}
    sizes = segmentation.segment_sizes(segments)
    assert sizes.loc["Sedentario", "usuarios"] == 2
    assert sizes.loc["Sedentario", "etiqueta"] == "50 % (2 de 4)"
    assert sizes["usuarios"].sum() == 4


def test_segment_of_labels_every_user():
    users = _users([(1, 1000, 5), (2, 12000, 5), (3, 1000, 60), (4, 12000, 60)])
    labels = segmentation.segment_of(users)
    assert labels.tolist() == ["Sedentario", "Viajero", "Fuerte", "Saludable"]
    assert labels.notna().all()


def test_segment_ids_filters_on_both_axes():
    users = _users([(1, 1000, 5), (2, 12000, 5), (3, 1000, 60)])
    assert segmentation.segment_ids(users, cfg.STEPS_LOW, cfg.INTENSITY_LOW) == [1]
    assert segmentation.segment_ids(users, cfg.STEPS_HIGH, cfg.INTENSITY_LOW) == [2]
    assert segmentation.segment_ids(users, cfg.STEPS_LOW, cfg.INTENSITY_HIGH) == [3]
    assert segmentation.segment_ids(users, [], cfg.INTENSITY_LOW) == []
