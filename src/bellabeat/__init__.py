"""Bellabeat strategic segmentation analysis.

Analysis code for the FitBit proxy dataset, kept out of the notebook so it can
be tested. The notebook holds the narrative and the figures; this package
holds every calculation the conclusions rest on.
"""

from . import config, features, loading, plots, segmentation, stats

__all__ = ["config", "features", "loading", "plots", "segmentation", "stats"]
__version__ = "1.0.0"
