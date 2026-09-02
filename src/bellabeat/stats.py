"""Uncertainty helpers.

With n=26 a point estimate on its own is misleading: one user is 3.8
percentage points. Everything reported as a proportion should carry an
interval, and every correlation should say what its unit of observation is.
"""

from __future__ import annotations

import math

import pandas as pd


def wilson_interval(
    successes: int, total: int, z: float = 1.96
) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion.

    Preferred over the normal approximation because it stays inside [0, 1] and
    behaves sensibly for small samples and proportions near 0 or 1 -- which is
    exactly this project's situation.

    Args:
        successes: Number of successes.
        total: Number of trials.
        z: Normal quantile; 1.96 gives a 95 % interval.

    Returns:
        ``(low, high)`` as proportions in [0, 1]. ``(0.0, 1.0)`` if ``total``
        is zero.
    """
    if total <= 0:
        return (0.0, 1.0)

    p = successes / total
    denom = 1 + z**2 / total
    center = (p + z**2 / (2 * total)) / denom
    margin = z * math.sqrt(p * (1 - p) / total + z**2 / (4 * total**2)) / denom
    return (max(0.0, center - margin), min(1.0, center + margin))


def proportion_report(successes: int, total: int, z: float = 1.96) -> str:
    """One-line proportion with its confidence interval and raw counts.

    Args:
        successes: Number of successes.
        total: Number of trials.
        z: Normal quantile.

    Returns:
        For example ``'31 % (IC 95 %: 16-51 %) · 8 de 26'``.
    """
    if total <= 0:
        return "sin datos"
    low, high = wilson_interval(successes, total, z)
    return (
        f"{100 * successes / total:.0f} % "
        f"(IC 95 %: {100 * low:.0f}-{100 * high:.0f} %) · {successes} de {total}"
    )


def segment_sizes_with_ci(segments: dict[str, list]) -> pd.DataFrame:
    """Segment sizes with a Wilson interval on each share.

    Args:
        segments: Mapping of segment name to ids.

    Returns:
        Frame indexed by segment with counts, share, interval bounds and a
        printable label.
    """
    total = sum(len(ids) for ids in segments.values())
    rows = []
    for name, ids in segments.items():
        low, high = wilson_interval(len(ids), total)
        rows.append(
            {
                "segmento": name,
                "usuarios": len(ids),
                "porcentaje": round(100 * len(ids) / total, 1) if total else 0.0,
                "ic_inferior": round(100 * low, 1),
                "ic_superior": round(100 * high, 1),
                "reporte": proportion_report(len(ids), total),
                "concluyente": "sí" if len(ids) >= 5 else "no (n < 5)",
            }
        )
    return pd.DataFrame(rows).set_index("segmento")


def correlation_by_unit(
    df: pd.DataFrame, columns: list[str], group: str = "Id"
) -> pd.DataFrame:
    """Compare a pooled correlation with one computed on per-user medians.

    Pooling day-level rows treats ~61 repeated measurements of each of 26
    people as 1 586 independent observations. That is pseudo-replication: it
    inflates how solid the correlation looks. Aggregating to one row per user
    first gives an estimate whose n really is the number of people.

    Args:
        df: Day-level frame.
        columns: Exactly two column names to correlate.
        group: Column identifying the subject.

    Returns:
        Frame with one row per unit of observation, its n and its r.

    Raises:
        ValueError: If ``columns`` does not hold exactly two names.
    """
    if len(columns) != 2:
        raise ValueError(f"Se esperaban 2 columnas, se recibieron {len(columns)}")

    a, b = columns
    pooled = df[a].corr(df[b])
    per_user = df.groupby(group)[[a, b]].median()
    subject = per_user[a].corr(per_user[b])

    return pd.DataFrame(
        [
            {
                "unidad": "día-usuario (agrupado)",
                "n": len(df),
                "r": round(pooled, 3),
                "nota": "pseudorreplicación: n efectivo ≈ nº de usuarios",
            },
            {
                "unidad": "usuario (mediana)",
                "n": len(per_user),
                "r": round(subject, 3),
                "nota": "observaciones independientes",
            },
        ]
    ).set_index("unidad")
