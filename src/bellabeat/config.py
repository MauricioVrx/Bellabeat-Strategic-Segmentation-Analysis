"""Project-wide constants.

Every threshold is traced back to its source. Nothing here is a magic number:
if a value cannot be justified from published guidance, it does not belong in
this file.
"""

from __future__ import annotations

import numpy as np

# --------------------------------------------------------------------------
# Data layout
# --------------------------------------------------------------------------

#: Folder names under ``data/`` holding one export each, ``export_<range>``.
DATE_RANGES: list[str] = ["3.12.16-4.11.16", "4.12.16-5.12.16"]

#: Format of the date range encoded in each export folder name.
DATE_RANGE_FORMAT = "%m.%d.%y"

MINUTES_PER_DAY = 1440
DAYS_PER_WEEK = 7

# --------------------------------------------------------------------------
# Health benchmarks
# --------------------------------------------------------------------------
# WHO, "Guidelines on physical activity and sedentary behaviour" (2020):
# adults aged 18-64 should accumulate 150-300 minutes of moderate-intensity
# activity per week, where 1 minute of vigorous activity counts as 2 minutes
# of moderate activity.  https://iris.who.int/items/65310979-92e8-4c98-8092-5a16ca07fc2f

WHO_WEEKLY_MINIMUM_MINUTES = 150
WHO_WEEKLY_OPTIMAL_MINUTES = 300

#: Weight applied to vigorous minutes so they are comparable to moderate ones.
VIGOROUS_TO_MODERATE_RATIO = 2

#: Daily bin edges for ``combined_activity_score``, derived from the weekly WHO
#: range: 150/7 = 21.4 -> 22, and 300/7 = 42.9 -> 43.
INTENSITY_BIN_EDGES: list[float] = [0, 22, 32, 43, np.inf]

INTENSITY_LABELS: list[str] = [
    "Sedentario",
    "Mínimo saludable",
    "Objetivo óptimo",
    "Objetivo máximo",
]

INTENSITY_FLAGS: list[str] = [
    "flag_sedentary",
    "flag_meets_min_health",
    "flag_meets_optimal_goal",
    "flag_meets_best_goal",
]

# Paluch et al., "Daily Steps and All-Cause Mortality", JACC (2023):
# dose-response quartile boundaries for daily step counts.
# https://www.jacc.org/doi/10.1016/j.jacc.2023.07.029
STEPS_BIN_EDGES: list[float] = [0, 2735, 4930, 7126, 10000, np.inf]

STEPS_LABELS: list[str] = [
    "Sedentario",
    "Mínimo",
    "Leve",
    "Óptimo",
    "Muy activo",
]

#: Weekly compliance is measured against the *upper* end of the WHO range
#: (the optimal goal), not the minimum. Stated explicitly so the criterion is
#: never implicit in a report.
WEEKLY_INTENSITY_TARGET = INTENSITY_BIN_EDGES[3] * DAYS_PER_WEEK  # 301 min/week
WEEKLY_INTENSITY_MINIMUM = INTENSITY_BIN_EDGES[1] * DAYS_PER_WEEK  # 154 min/week

#: Weekly step target, from the JACC "óptimo" daily boundary.
WEEKLY_STEPS_TARGET = STEPS_BIN_EDGES[3] * DAYS_PER_WEEK  # 49 882 steps/week

#: National Sleep Foundation: 7-9 h for adults. Lower bound used as the flag.
HEALTHY_SLEEP_MINUTES = 420

# --------------------------------------------------------------------------
# Cohort definitions
# --------------------------------------------------------------------------

#: Minimum registered days to be analysed for habitual behaviour (8 weeks + 1).
MIN_DAYS_ACTIVE_COHORT = 57

#: Inclusive day range for the intermittent-use (re-engagement) cohort.
REENGAGEMENT_DAY_RANGE = (36, 56)

# --------------------------------------------------------------------------
# Segments
# --------------------------------------------------------------------------

STEPS_LOW = STEPS_LABELS[:3]  # Sedentario, Mínimo, Leve
STEPS_HIGH = STEPS_LABELS[3:]  # Óptimo, Muy activo
INTENSITY_LOW = INTENSITY_LABELS[:2]  # Sedentario, Mínimo saludable
INTENSITY_HIGH = INTENSITY_LABELS[2:]  # Objetivo óptimo, Objetivo máximo

#: segment name -> (accepted step categories, accepted intensity categories)
SEGMENTS: dict[str, tuple[list[str], list[str]]] = {
    "Sedentario": (STEPS_LOW, INTENSITY_LOW),
    "Viajero": (STEPS_HIGH, INTENSITY_LOW),
    "Fuerte": (STEPS_LOW, INTENSITY_HIGH),
    "Saludable": (STEPS_HIGH, INTENSITY_HIGH),
}

# --------------------------------------------------------------------------
# Visual system
# --------------------------------------------------------------------------
# Orange/blue instead of red/green: the warm-cool contrast survives every type
# of colour-vision deficiency, which red/green does not.

SEGMENT_COLORS: dict[str, str] = {
    "Sedentario": "#D97706",  # amber
    "Viajero": "#64748B",  # slate (empty segment)
    "Fuerte": "#7C3AED",  # violet
    "Saludable": "#1D4ED8",  # blue
}

#: Ordinal ramp for the four intensity-compliance levels (risk -> target met).
INTENSITY_RAMP: list[str] = ["#D97706", "#F3D6A8", "#A8C8E8", "#1D4ED8"]

#: Secondary encoding, so meaning never rests on colour alone.
INTENSITY_HATCHES: list[str] = ["//", "\\\\", "..", ""]
