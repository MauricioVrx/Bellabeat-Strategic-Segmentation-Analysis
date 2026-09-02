"""Tests for the uncertainty helpers."""

import pandas as pd

from bellabeat import stats


def test_wilson_interval_brackets_the_estimate():
    low, high = stats.wilson_interval(8, 26)
    assert low < 8 / 26 < high
    assert 0 <= low and high <= 1


def test_wilson_interval_is_wide_for_tiny_samples():
    """n=3 must produce an interval too wide to report as a point estimate."""
    low, high = stats.wilson_interval(3, 3)
    assert high == 1.0
    assert low < 0.5  # 100 % of 3 tells us almost nothing


def test_wilson_interval_handles_the_zero_cases():
    assert stats.wilson_interval(0, 0) == (0.0, 1.0)
    low, high = stats.wilson_interval(0, 26)
    assert low == 0.0 and high > 0


def test_proportion_report_shows_counts_and_interval():
    report = stats.proportion_report(8, 26)
    assert "8 de 26" in report and "IC 95 %" in report and "31 %" in report


def test_small_segments_are_flagged_as_inconclusive():
    segments = {"Sedentario": [1, 2, 3, 4, 5], "Fuerte": [6, 7, 8]}
    out = stats.segment_sizes_with_ci(segments)
    assert out.loc["Sedentario", "concluyente"] == "sí"
    assert out.loc["Fuerte", "concluyente"] == "no (n < 5)"


def test_pooled_and_per_user_correlations_are_reported_separately():
    """Repeated measures must not be presented as independent observations."""
    rows = []
    for user, offset in enumerate([0, 50, 100], start=1):
        for day in range(20):
            rows.append({"Id": user, "a": day + offset, "b": -day + offset})
    df = pd.DataFrame(rows)

    out = stats.correlation_by_unit(df, ["a", "b"])
    assert out.loc["día-usuario (agrupado)", "n"] == 60
    assert out.loc["usuario (mediana)", "n"] == 3
    # Within each user a and b move in opposite directions; across users they
    # move together. Pooling hides the within-subject relationship entirely.
    assert out.loc["usuario (mediana)", "r"] > 0.9
    assert out.loc["día-usuario (agrupado)", "r"] < out.loc["usuario (mediana)", "r"]
