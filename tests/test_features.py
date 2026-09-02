"""Tests for the derived columns the conclusions rest on."""

import numpy as np
import pandas as pd
import pytest

from bellabeat import config as cfg
from bellabeat import features


def test_combined_score_applies_the_who_equivalence():
    """10 vigorous minutes must score the same as 20 moderate ones."""
    df = pd.DataFrame(
        {"VeryActiveMinutes": [10, 0, 5], "ModeratelyActiveMinutes": [0, 20, 10]}
    )
    assert features.combined_activity_score(df).tolist() == [20, 20, 20]


def test_daily_thresholds_match_the_weekly_who_range():
    """The daily bins must be the WHO weekly range divided by seven."""
    minimum, optimal = cfg.INTENSITY_BIN_EDGES[1], cfg.INTENSITY_BIN_EDGES[3]
    assert minimum * cfg.DAYS_PER_WEEK >= cfg.WHO_WEEKLY_MINIMUM_MINUTES
    assert (minimum - 1) * cfg.DAYS_PER_WEEK < cfg.WHO_WEEKLY_MINIMUM_MINUTES
    assert optimal * cfg.DAYS_PER_WEEK >= cfg.WHO_WEEKLY_OPTIMAL_MINUTES
    assert (optimal - 1) * cfg.DAYS_PER_WEEK < cfg.WHO_WEEKLY_OPTIMAL_MINUTES


def test_compliance_flags_are_mutually_exclusive():
    """Every day falls in exactly one band, including the boundaries."""
    df = pd.DataFrame({"combined_activity_score": [0, 21, 22, 31, 32, 42, 43, 500]})
    out = features.add_compliance_flags(df)
    assert out[cfg.INTENSITY_FLAGS].sum(axis=1).eq(1).all()
    # Left-inclusive: 22 is the first "minimum met" day, 21 is still sedentary.
    assert out.loc[1, "flag_sedentary"] == 1
    assert out.loc[2, "flag_meets_min_health"] == 1
    assert out.loc[6, "flag_meets_best_goal"] == 1


def test_compliance_flags_do_not_mutate_the_shared_edges():
    """The module-level edge list must survive repeated calls unchanged."""
    before = list(cfg.INTENSITY_BIN_EDGES)
    df = pd.DataFrame({"combined_activity_score": [10, 50]})
    features.add_compliance_flags(df)
    features.add_compliance_flags(df)
    assert cfg.INTENSITY_BIN_EDGES == before


def test_compliance_flags_reject_mismatched_edges():
    df = pd.DataFrame({"combined_activity_score": [10]})
    with pytest.raises(ValueError, match="bin edges"):
        features.add_compliance_flags(df, bin_edges=[0, 10, np.inf], flag_names=["a"])


def test_activity_calories_never_go_negative():
    """A basal estimate above the daily total must clamp to zero, not below."""
    daily = pd.DataFrame(
        {
            "Id": [1, 1],
            "ActivityDay": pd.to_datetime(["2016-03-14", "2016-03-15"]),
            "Calories": [1000, 3000],
            "minutes_instances": [1440, 1440],
            "VeryActiveMinutes": [0, 30],
            "ModeratelyActiveMinutes": [0, 20],
        }
    )
    minutes = pd.DataFrame(
        {"Id": [1] * 4, "Intensity": [0] * 4, "Steps": [0] * 4, "Calories": [1.5] * 4}
    )
    out = features.add_processing_columns(daily, minutes)
    assert (out["calories_activity"] >= 0).all()
    assert out.loc[0, "calories_activity"] == 0  # 1000 - 2160 would be negative
    assert out.loc[1, "calories_activity"] == 840  # 3000 - 2160


def test_basal_rate_uses_only_fully_at_rest_minutes():
    """Minutes with steps, or with any intensity, must not count as basal."""
    minutes = pd.DataFrame(
        {
            "Id": [1, 1, 1, 1],
            "Intensity": [0, 0, 2, 0],
            "Steps": [0, 0, 50, 30],
            "Calories": [1.0, 2.0, 9.0, 9.0],
        }
    )
    rate = features.sedentary_calories_per_minute(minutes)
    # Only the first two rows qualify -> median of 1.0 and 2.0
    assert rate.loc[1, "sedentary_calories_per_minute"] == 1.5


def test_cohort_summary_reports_sizes_ranges_and_shares():
    """These numbers are quoted in the README, so they are pinned by a test."""
    days = {1: 62, 2: 57, 3: 50, 4: 36, 5: 10}
    df = pd.DataFrame(
        [
            {"Id": uid, "ActivityDay": pd.Timestamp("2016-03-12") + pd.Timedelta(days=i)}
            for uid, n in days.items()
            for i in range(n)
        ]
    )
    summary = features.cohort_summary(df, period_days=62)

    assert list(summary.index) == ["Uso activo", "Uso poco recurrente", "Muy poco uso"]
    assert summary.loc["Uso activo", "usuarios"] == 2
    assert summary.loc["Uso poco recurrente", "usuarios"] == 2
    assert summary.loc["Muy poco uso", "usuarios"] == 1

    assert summary.loc["Uso activo", "dias_min"] == 57
    assert summary.loc["Uso activo", "dias_max"] == 62

    # Shares are over the whole sample and must add up to 100 %.
    assert summary["porcentaje"].sum() == pytest.approx(100.0, abs=0.2)
    assert summary.loc["Uso activo", "porcentaje"] == pytest.approx(40.0)

    # Expected days = users x period, used for the completeness ratio.
    assert summary.loc["Uso activo", "dias_esperados"] == 2 * 62
    assert summary.loc["Uso activo", "dias_registrados"] == 62 + 57


def test_cohorts_partition_every_user_exactly_once():
    """No user may be lost between the three cohorts, or land in two."""
    days = {1: 62, 2: 57, 3: 56, 4: 36, 5: 35, 6: 1}
    rows = [
        {
            "Id": uid,
            "ActivityDay": pd.Timestamp("2016-03-12") + pd.Timedelta(days=i),
        }
        for uid, n in days.items()
        for i in range(n)
    ]
    df = pd.DataFrame(rows)

    active, reeng, dropped = features.split_cohorts(df)
    ids = lambda part: set(part["Id"].unique())

    assert ids(active) == {1, 2}
    assert ids(reeng) == {3, 4}
    assert ids(dropped) == {5, 6}
    assert ids(active) | ids(reeng) | ids(dropped) == set(days)
    assert not (ids(active) & ids(reeng)) and not (ids(reeng) & ids(dropped))
