"""Classifying users into behavioural categories and business segments.

Selection is by *label*, never by position. ``groupby(observed=True)`` drops
categories nobody falls into, so a positional slice such as ``iloc[:3, :2]``
silently assigns users to the wrong segment the moment a quadrant empties --
which already happens on the re-engagement cohort.
"""

from __future__ import annotations

import pandas as pd

from . import config as cfg


def categorize_users(user_activity: pd.DataFrame) -> pd.DataFrame:
    """Add the step and intensity categories used by the segmentation.

    Args:
        user_activity: One row per user, with ``median_steps`` and
            ``median_activity_score``.

    Returns:
        A copy with ``steps_category`` and ``intensity_category`` added.
    """
    out = user_activity.copy()
    out["steps_category"] = pd.cut(
        out["median_steps"],
        bins=cfg.STEPS_BIN_EDGES,
        labels=cfg.STEPS_LABELS,
        right=False,  # left edge inclusive: [0, 2735)
    )
    out["intensity_category"] = pd.cut(
        out["median_activity_score"],
        bins=cfg.INTENSITY_BIN_EDGES,
        labels=cfg.INTENSITY_LABELS,
        right=False,
    )
    return out


def segment_ids(
    user_activity: pd.DataFrame,
    steps_categories: list[str],
    intensity_categories: list[str],
) -> list:
    """Ids whose step and intensity categories both fall in the given sets.

    Args:
        user_activity: Frame indexed by ``Id`` with the two category columns.
        steps_categories: Accepted values of ``steps_category``.
        intensity_categories: Accepted values of ``intensity_category``.

    Returns:
        The matching ids, in index order.
    """
    mask = user_activity["steps_category"].isin(steps_categories) & user_activity[
        "intensity_category"
    ].isin(intensity_categories)
    return user_activity.index[mask].tolist()


def assign_segments(user_activity: pd.DataFrame) -> dict[str, list]:
    """Split every user into exactly one of the four business segments.

    Args:
        user_activity: Frame indexed by ``Id``, already categorised.

    Returns:
        Mapping of segment name to the list of ids in it.

    Raises:
        AssertionError: If the segments do not partition the users exactly.
            Failing loudly beats returning a plausible but wrong split.
    """
    segments = {
        name: segment_ids(user_activity, steps, intensities)
        for name, (steps, intensities) in cfg.SEGMENTS.items()
    }

    assigned = [uid for ids in segments.values() for uid in ids]
    n_expected = len(user_activity)

    assert len(assigned) == n_expected, (
        f"La segmentación no cubre a todos los usuarios: "
        f"{len(assigned)} asignados de {n_expected}. "
        f"Revisa que las categorías de config.SEGMENTS cubran todas las etiquetas."
    )
    assert len(set(assigned)) == len(assigned), (
        "Hay usuarios asignados a más de un segmento; las categorías de "
        "config.SEGMENTS se solapan."
    )
    return segments


def segment_of(user_activity: pd.DataFrame) -> pd.Series:
    """Segment name per user, as a column rather than a dict.

    Args:
        user_activity: Frame indexed by ``Id``, already categorised.

    Returns:
        Series of segment names indexed by ``Id``.
    """
    labels = pd.Series(index=user_activity.index, dtype="object")
    for name, ids in assign_segments(user_activity).items():
        labels.loc[ids] = name
    return labels


def segmentation_matrix(user_activity: pd.DataFrame) -> pd.DataFrame:
    """Cross-tabulation of step category against intensity category.

    Args:
        user_activity: Frame with both category columns.

    Returns:
        Counts, reindexed so every declared category appears even when empty.
    """
    matrix = pd.crosstab(
        user_activity["steps_category"], user_activity["intensity_category"]
    )
    return matrix.reindex(
        index=cfg.STEPS_LABELS, columns=cfg.INTENSITY_LABELS, fill_value=0
    )


def flags_by_steps_category(
    user_activity: pd.DataFrame, how: str = "sum"
) -> pd.DataFrame:
    """Aggregate the intensity-compliance flags per step category.

    Always reindexed to every declared step category, because
    ``groupby(observed=True)`` drops the empty ones and any later selection by
    label would then raise -- or, worse, silently return a shorter frame.

    Args:
        user_activity: Frame with ``steps_category`` and the flag columns.
        how: Aggregation passed to ``groupby.agg`` (``'sum'`` for total days,
            ``'median'`` for the typical user).

    Returns:
        Rows = every step category, columns = the intensity labels. Missing
        categories are 0 for ``'sum'`` and NaN otherwise, since "no users"
        means zero days but no median at all.
    """
    grouped = user_activity.groupby("steps_category", observed=True)[
        cfg.INTENSITY_FLAGS
    ].agg(how)
    grouped.columns = cfg.INTENSITY_LABELS
    fill = 0 if how == "sum" else float("nan")
    return grouped.reindex(index=cfg.STEPS_LABELS, fill_value=fill)


def segment_sizes(segments: dict[str, list], decimals: int = 0) -> pd.DataFrame:
    """Size and share of each segment, with the raw count kept alongside.

    Reporting ``31 % (8 de 26)`` instead of ``30.77 %`` avoids implying a
    precision the sample cannot support: with n=26 one user is 3.8 points.

    Args:
        segments: Mapping of segment name to ids.
        decimals: Decimals for the percentage.

    Returns:
        Frame with ``usuarios``, ``porcentaje`` and a printable ``etiqueta``.
    """
    total = sum(len(ids) for ids in segments.values())
    rows = []
    for name, ids in segments.items():
        pct = round(100 * len(ids) / total, decimals) if total else 0.0
        rows.append(
            {
                "segmento": name,
                "usuarios": len(ids),
                "porcentaje": pct,
                "etiqueta": f"{pct:.0f} % ({len(ids)} de {total})",
            }
        )
    return pd.DataFrame(rows).set_index("segmento")
