"""Reading and consolidating the exported FitBit CSV files.

The exports live under ``data/export_<m.d.y-m.d.y>/`` and are stacked into a
single frame.  Two rules are enforced here rather than left implicit:

* dates are parsed before they are compared (never string comparison);
* stacking is a concatenation with an explicit duplicate report, not a merge
  that silently collapses or multiplies rows.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from . import config as cfg


def export_dir(date_range: str, base: str | Path = "data") -> Path:
    """Path of the export folder for one date range."""
    return Path(base) / f"export_{date_range}"


def parse_date_range(date_range: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Split a folder-name date range into two timestamps.

    Args:
        date_range: Range as encoded in the folder name, ``'3.12.16-4.11.16'``.

    Returns:
        ``(first_day, last_day)`` as timestamps, both inclusive.
    """
    start, end = date_range.split("-")

    def to_timestamp(text: str) -> pd.Timestamp:
        return pd.Timestamp(datetime.strptime(text, cfg.DATE_RANGE_FORMAT))

    return to_timestamp(start), to_timestamp(end)


def limit_date_range(
    df: pd.DataFrame, date_range: str, time_column: str = "ActivityDay"
) -> pd.DataFrame:
    """Keep only the rows inside the range encoded in the folder name.

    The time column is converted to datetime *before* filtering. Comparing the
    raw strings would appear to work for ISO dates and silently return the
    wrong rows for any other format.

    Args:
        df: Frame straight from ``read_csv``.
        date_range: Range as encoded in the folder name.
        time_column: Name of the timestamp column to filter on.

    Returns:
        A filtered copy with ``time_column`` parsed as datetime.

    Raises:
        ValueError: If any value in ``time_column`` cannot be parsed.
    """
    first_day, last_day = parse_date_range(date_range)

    # 'mixed' because the corrected export is ISO while the original FitBit
    # files are US-formatted; both must parse without a per-element warning.
    parsed = pd.to_datetime(df[time_column], errors="coerce", format="mixed")
    if parsed.isna().any():
        n_bad = int(parsed.isna().sum())
        raise ValueError(
            f"{n_bad} unparseable values in '{time_column}' for range {date_range}"
        )

    out = df.assign(**{time_column: parsed})
    # ``last_day`` is a date; include the whole of it for per-minute data.
    end_of_last_day = last_day + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    mask = (out[time_column] >= first_day) & (out[time_column] <= end_of_last_day)
    return out.loc[mask].copy()


def load_activity_files(
    date_ranges: list[str] | None = None,
    time_type: str = "daily",
    info_type: str = "Activity",
    time_column: str = "ActivityDay",
    base: str | Path = "data",
    verbose: bool = True,
) -> pd.DataFrame:
    """Read one CSV per date range and stack them into a single frame.

    Args:
        date_ranges: Folder-name ranges to read. Defaults to ``cfg.DATE_RANGES``.
        time_type: File-name prefix (``'daily'``, ``'hourly'``, ``'minute'``).
        info_type: File-name suffix (``'Activity'``, ``'Intensities'``,
            ``'Calories'``, ``'Steps'``).
        time_column: Timestamp column used for filtering.
        base: Root folder holding the ``export_*`` directories.
        verbose: Print a one-line report of rows read and duplicates dropped.

    Returns:
        The concatenated frame, deduplicated on ``(Id, time_column)``.

    Raises:
        FileNotFoundError: If an expected CSV is missing.
    """
    date_ranges = date_ranges or cfg.DATE_RANGES
    frames = []

    for date_range in date_ranges:
        path = export_dir(date_range, base) / f"{time_type}{info_type}.csv"
        if not path.exists():
            raise FileNotFoundError(
                f"Missing {path}. See the 'Cómo ejecutar' section of the README "
                f"for the expected data layout."
            )
        frames.append(limit_date_range(pd.read_csv(path), date_range, time_column))

    stacked = pd.concat(frames, ignore_index=True)

    # Overlapping exports would otherwise duplicate days. Report, don't hide.
    n_dup = int(stacked.duplicated(subset=["Id", time_column]).sum())
    if n_dup:
        stacked = stacked.drop_duplicates(subset=["Id", time_column], keep="first")
    if verbose:
        print(
            f"{time_type}{info_type}: {len(stacked):,} filas · "
            f"{stacked['Id'].nunique()} usuarios · {n_dup:,} duplicados descartados"
        )
    return stacked


def merge_minute_frames(
    intensities: pd.DataFrame,
    calories: pd.DataFrame,
    steps: pd.DataFrame,
    verbose: bool = True,
) -> pd.DataFrame:
    """Join the three per-minute sources on ``(Id, ActivityMinute)``.

    Uses an outer join with ``validate='one_to_one'`` so that unexpected
    duplicate keys raise instead of silently multiplying rows, and reports how
    many minutes were missing from each source instead of dropping them
    unnoticed.

    Args:
        intensities: Per-minute intensity frame.
        calories: Per-minute calories frame.
        steps: Per-minute steps frame.
        verbose: Print the coverage report.

    Returns:
        One row per ``(Id, ActivityMinute)`` with Intensity, Calories, Steps.
    """
    keys = ["Id", "ActivityMinute"]

    merged = intensities.merge(
        calories, on=keys, how="outer", validate="one_to_one", indicator="_src_cal"
    )
    merged = merged.merge(
        steps, on=keys, how="outer", validate="one_to_one", indicator="_src_steps"
    )

    if verbose:
        for col, label in [("_src_cal", "calorías"), ("_src_steps", "pasos")]:
            missing = int((merged[col] != "both").sum())
            print(f"minutos sin pareja en {label}: {missing:,}")

    return merged.drop(columns=["_src_cal", "_src_steps"])
