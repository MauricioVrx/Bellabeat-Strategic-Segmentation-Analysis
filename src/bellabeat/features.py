"""Feature engineering on the daily activity frame."""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config as cfg


def combined_activity_score(df: pd.DataFrame) -> pd.Series:
    """Effective exercise volume in "moderate-equivalent" minutes.

    The WHO treats 75 minutes of vigorous activity as equivalent to 150 minutes
    of moderate activity, i.e. a factor of exactly 2. This turns two columns
    that are not comparable on their own into a single ranking-safe measure.

    Args:
        df: Frame with ``VeryActiveMinutes`` and ``ModeratelyActiveMinutes``.

    Returns:
        Moderate-equivalent minutes per row.
    """
    return (
        df["VeryActiveMinutes"] * cfg.VIGOROUS_TO_MODERATE_RATIO
        + df["ModeratelyActiveMinutes"]
    )


def sedentary_calories_per_minute(df_minutes: pd.DataFrame) -> pd.DataFrame:
    """Per-user basal burn rate, from minutes with no movement at all.

    Args:
        df_minutes: Per-minute frame with ``Id``, ``Intensity``, ``Steps``,
            ``Calories``.

    Returns:
        One row per ``Id`` with ``sedentary_calories_per_minute``.
    """
    at_rest = df_minutes[(df_minutes["Intensity"] == 0) & (df_minutes["Steps"] == 0)]
    return at_rest.groupby("Id").agg(
        sedentary_calories_per_minute=("Calories", "median")
    )


def add_compliance_flags(
    df: pd.DataFrame,
    score_column: str = "combined_activity_score",
    bin_edges: list[float] | None = None,
    flag_names: list[str] | None = None,
) -> pd.DataFrame:
    """Add one mutually exclusive 0/1 flag per intensity-compliance band.

    Args:
        df: Frame containing ``score_column``.
        score_column: Column holding the daily activity score.
        bin_edges: ``len(flag_names) + 1`` edges, left-inclusive.
        flag_names: Names of the flag columns to create.

    Returns:
        A copy of ``df`` with the flag columns appended.

    Raises:
        ValueError: If the number of edges does not match the number of flags.
    """
    # Copy the defaults: mutating a module-level list would leak into every
    # later call.
    bin_edges = list(bin_edges if bin_edges is not None else cfg.INTENSITY_BIN_EDGES)
    flag_names = list(flag_names if flag_names is not None else cfg.INTENSITY_FLAGS)

    if bin_edges[-1] != np.inf and len(bin_edges) == len(flag_names):
        bin_edges.append(np.inf)
    if len(bin_edges) != len(flag_names) + 1:
        raise ValueError(
            f"{len(flag_names)} flags need {len(flag_names) + 1} bin edges, "
            f"got {len(bin_edges)}"
        )

    out = df.copy()
    band = pd.cut(
        out[score_column], bins=bin_edges, labels=flag_names, right=False
    )
    for name in flag_names:
        out[name] = (band == name).astype(int)
    return out


def add_processing_columns(
    df: pd.DataFrame,
    df_minutes: pd.DataFrame,
    bin_edges: list[float] | None = None,
    flag_names: list[str] | None = None,
) -> pd.DataFrame:
    """Derive every column the daily analysis depends on.

    Adds the ISO week, the split of calories into basal and activity burn, the
    combined activity score, and the compliance flags.

    Args:
        df: Daily activity frame.
        df_minutes: Per-minute frame, used for the per-user basal burn rate.
        bin_edges: Override for the intensity bands.
        flag_names: Override for the flag column names.

    Returns:
        A new frame; ``df`` is left untouched.
    """
    out = df.copy()

    out["Week_ISO"] = out["ActivityDay"].dt.isocalendar().week.astype(int)

    out = out.merge(sedentary_calories_per_minute(df_minutes), on="Id", how="left")

    # Basal burn is the per-user resting rate applied to the minutes actually
    # recorded that day; the remainder is attributed to activity.
    out["calories_sedentary"] = (
        out["sedentary_calories_per_minute"] * out["minutes_instances"]
    ).round(0)
    out["calories_activity"] = (
        (out["Calories"] - out["calories_sedentary"]).clip(lower=0).astype("Int64")
    )

    out["combined_activity_score"] = combined_activity_score(out)

    if "TotalMinutesAsleep" in out.columns:
        out["has_sleep_record"] = out["TotalMinutesAsleep"].fillna(0).gt(0)
        out["healthy_sleep"] = (
            out["TotalMinutesAsleep"].fillna(0) > cfg.HEALTHY_SLEEP_MINUTES
        )

    return add_compliance_flags(out, bin_edges=bin_edges, flag_names=flag_names)


def split_cohorts(
    df: pd.DataFrame,
    min_days_active: int | None = None,
    reengagement_range: tuple[int, int] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split users into the active, re-engagement and dropped-out cohorts.

    Args:
        df: Daily activity frame for every user.
        min_days_active: Minimum registered days for the main cohort.
        reengagement_range: Inclusive ``(low, high)`` day range for the
            intermittent-use cohort.

    Returns:
        ``(active, reengagement, dropped)`` frames of daily records.
    """
    min_days_active = min_days_active or cfg.MIN_DAYS_ACTIVE_COHORT
    low, high = reengagement_range or cfg.REENGAGEMENT_DAY_RANGE

    days = df.groupby("Id")["ActivityDay"].count()

    active_ids = days[days >= min_days_active].index
    reeng_ids = days[(days >= low) & (days <= high)].index
    dropped_ids = days[days < low].index

    def rows_for(ids) -> pd.DataFrame:
        return df[df["Id"].isin(ids)].copy()

    return rows_for(active_ids), rows_for(reeng_ids), rows_for(dropped_ids)


def cohort_summary(df: pd.DataFrame, period_days: int) -> pd.DataFrame:
    """One row per cohort with its size, day range and share of all users.

    Args:
        df: Daily activity frame for every user, before splitting.
        period_days: Total days spanned by the study window.

    Returns:
        Frame indexed by cohort name.
    """
    active, reeng, dropped = split_cohorts(df)
    total_users = df["Id"].nunique()

    rows = []
    for name, part in [
        ("Uso activo", active),
        ("Uso poco recurrente", reeng),
        ("Muy poco uso", dropped),
    ]:
        days = part.groupby("Id")["ActivityDay"].count()
        rows.append(
            {
                "cohorte": name,
                "usuarios": int(part["Id"].nunique()),
                "dias_min": int(days.min()) if len(days) else 0,
                "dias_max": int(days.max()) if len(days) else 0,
                "porcentaje": round(100 * part["Id"].nunique() / total_users, 1),
                "dias_registrados": int(len(part)),
                "dias_esperados": int(part["Id"].nunique() * period_days),
            }
        )
    return pd.DataFrame(rows).set_index("cohorte")
