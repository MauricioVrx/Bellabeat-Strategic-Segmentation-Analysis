"""Regenerate the figures embedded in the README.

Runs off the published aggregate tables so the README can be rebuilt without
the raw dataset. The notebook writes the same files from live data when it is
executed; the numbers here are exactly the ones it produces.

    python docs/make_readme_figures.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from bellabeat import config as cfg
from bellabeat import plots

OUT = REPO / "docs" / "img"

# Users per (step category, intensity category) -- cohorte activa, n=26.
SEGMENTATION_MATRIX = pd.DataFrame(
    [[3, 0, 1, 0], [3, 2, 0, 0], [0, 0, 0, 2], [0, 0, 0, 8], [0, 0, 0, 7]],
    index=cfg.STEPS_LABELS,
    columns=cfg.INTENSITY_LABELS,
)

# Total days per (step category, intensity compliance level).
INTENSITY_VOLUME = pd.DataFrame(
    [
        [143, 25, 10, 67],
        [151, 40, 27, 88],
        [31, 6, 13, 74],
        [38, 17, 26, 404],
        [22, 1, 1, 402],
    ],
    index=cfg.STEPS_LABELS,
    columns=cfg.INTENSITY_LABELS,
)

COHORTS = pd.DataFrame(
    [
        {"cohorte": "Uso activo", "usuarios": 26, "dias_min": 57, "dias_max": 62,
         "porcentaje": 74.3},
        {"cohorte": "Uso poco recurrente", "usuarios": 5, "dias_min": 49,
         "dias_max": 55, "porcentaje": 14.3},
        {"cohorte": "Muy poco uso", "usuarios": 4, "dias_min": 1, "dias_max": 35,
         "porcentaje": 11.4},
    ]
).set_index("cohorte")


def main() -> None:
    plots.apply_style()
    plots.reset_figure_numbers()
    OUT.mkdir(parents=True, exist_ok=True)

    ax = plots.cohort_flow_chart(COHORTS)
    plots.caption(
        ax,
        "9 de 35 usuarios (26 %) quedaron fuera de la cohorte principal por uso "
        "intermitente del dispositivo.",
    )
    print("escrito:", plots.save(ax, "cohortes.png", OUT))
    plt.close("all")

    ax = plots.segmentation_heatmap(SEGMENTATION_MATRIX)
    plots.caption(
        ax,
        "21 de 26 usuarios (81 %) se concentran en las esquinas opuestas. "
        "El cuadrante 'Viajero' (muchos pasos, baja intensidad) está vacío.",
    )
    print("escrito:", plots.save(ax, "segmentacion_heatmap.png", OUT))
    plt.close("all")

    ax = plots.intensity_volume_bars(INTENSITY_VOLUME)
    plots.caption(
        ax,
        "325 días bajo el umbral mínimo de la OMS provienen de los tres segmentos "
        "de pasos bajos; 806 días de máximo rendimiento, de los dos altos.",
    )
    print("escrito:", plots.save(ax, "volumen_dias.png", OUT))
    plt.close("all")


if __name__ == "__main__":
    main()
