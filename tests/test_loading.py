"""Tests for date handling and file stacking."""

import pandas as pd
import pytest

from bellabeat import loading


def test_range_is_filtered_on_parsed_dates_not_strings():
    """US-format dates must filter correctly.

    Comparing raw strings happens to work for ISO dates and silently returns
    the wrong rows for '3/12/2016'-style input, which is the format of the
    original FitBit export.
    """
    df = pd.DataFrame(
        {
            "Id": [1, 1, 1, 1],
            "ActivityDay": [
                "3/11/2016 12:00:00 AM",  # before the range
                "3/12/2016 12:00:00 AM",  # first day, inclusive
                "4/11/2016 12:00:00 AM",  # last day, inclusive
                "4/12/2016 12:00:00 AM",  # after the range
            ],
        }
    )
    out = loading.limit_date_range(df, "3.12.16-4.11.16")

    assert len(out) == 2
    assert out["ActivityDay"].min() == pd.Timestamp("2016-03-12")
    assert out["ActivityDay"].max() == pd.Timestamp("2016-04-11")
    assert pd.api.types.is_datetime64_any_dtype(out["ActivityDay"])


def test_last_day_includes_its_minutes():
    """Per-minute rows late on the final day must not be dropped."""
    df = pd.DataFrame(
        {"Id": [1, 1], "ActivityMinute": ["4/11/2016 11:59:00 PM", "4/12/2016 00:01:00"]}
    )
    out = loading.limit_date_range(df, "3.12.16-4.11.16", "ActivityMinute")
    assert len(out) == 1


def test_unparseable_dates_raise():
    df = pd.DataFrame({"Id": [1], "ActivityDay": ["no es una fecha"]})
    with pytest.raises(ValueError, match="unparseable"):
        loading.limit_date_range(df, "3.12.16-4.11.16")


def test_ranges_are_stacked_and_deduplicated(tmp_path):
    """Two exports stack into one frame; an overlapping day is kept once."""
    for folder, days in [
        ("export_3.12.16-4.11.16", ["3/12/2016", "3/13/2016"]),
        ("export_4.12.16-5.12.16", ["4/12/2016", "4/13/2016"]),
    ]:
        d = tmp_path / folder
        d.mkdir()
        pd.DataFrame({"Id": [1] * len(days), "ActivityDay": days, "Steps": [10, 20]}).to_csv(
            d / "dailyActivity.csv", index=False
        )

    out = loading.load_activity_files(base=tmp_path, verbose=False)
    assert len(out) == 4
    assert out["ActivityDay"].is_monotonic_increasing


def test_missing_file_names_the_readme(tmp_path):
    with pytest.raises(FileNotFoundError, match="Cómo ejecutar"):
        loading.load_activity_files(base=tmp_path, verbose=False)


def test_duplicate_keys_in_minute_merge_raise(tmp_path):
    """A duplicated (Id, minute) key must fail rather than multiply rows."""
    good = pd.DataFrame(
        {"Id": [1, 1], "ActivityMinute": ["2016-03-12 00:00", "2016-03-12 00:01"]}
    )
    intensities = good.assign(Intensity=[0, 1])
    calories = good.assign(Calories=[1.0, 1.2])
    steps = pd.concat([good, good.head(1)]).assign(Steps=[0, 5, 9])

    with pytest.raises(pd.errors.MergeError):
        loading.merge_minute_frames(intensities, calories, steps, verbose=False)


def test_export_dir_and_range_parsing():
    assert loading.export_dir("3.12.16-4.11.16").as_posix() == "data/export_3.12.16-4.11.16"
    assert loading.export_dir("3.12.16-4.11.16", "otro").as_posix().startswith("otro/")

    first, last = loading.parse_date_range("3.12.16-4.11.16")
    assert first == pd.Timestamp("2016-03-12")
    assert last == pd.Timestamp("2016-04-11")
