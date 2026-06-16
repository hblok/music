"""forge.analysis.loops — loop-seam discontinuity and RMS flatness checks.

These are the two acceptance criteria from the plan:
  - "loops seamlessly (no audible seam)"  → seam_report()
  - "shows flat RMS trend (no build)"     → rms_flatness_report()

Both return plain dicts with an ``ok`` key so CI can check them with a single
``assert report["ok"]``.
"""

from __future__ import annotations

import numpy as np

from forge.core.buffer import AudioBuffer
from forge.core.loopfold import check_seam


def seam_report(
    buf: AudioBuffer,
    *,
    tolerance: float = 0.05,
) -> dict:
    """Check the loop-seam discontinuity of *buf*.

    *buf* must already have been processed by ``loop_fold`` — this check only
    measures the raw sample-level jump at the start/end boundary.

    Args:
        buf:        looped AudioBuffer.
        tolerance:  maximum acceptable amplitude discontinuity (0–1 scale).

    Returns::

        {
            "start_L", "end_L", "start_R", "end_R",
            "discontinuity": float,   # max(|end - start|) across channels
            "ok": bool,               # discontinuity < tolerance
        }
    """
    return check_seam(buf, tolerance=tolerance)


def rms_flatness_report(
    buf: AudioBuffer,
    n_sections: int = 8,
    *,
    max_slope: float = 0.005,
) -> dict:
    """Check that per-section RMS is flat (suitable for infinite game loops).

    A positive slope means the loop builds energy each pass — not acceptable
    for background game-state music.

    Args:
        buf:        AudioBuffer (ideally a single loop cycle).
        n_sections: number of equal-length sections to analyse.
        max_slope:  maximum RMS/section slope to consider "flat".

    Returns::

        {
            "section_rms": list[float],
            "slope":        float,   # RMS per section (positive = rising)
            "ok":           bool,    # abs(slope) <= max_slope
        }
    """
    from forge.analysis.loudness import rms_trend_slope

    rms_vals = buf.section_rms(n_sections)
    slope = rms_trend_slope(buf, n_sections)
    return {
        "section_rms": rms_vals,
        "slope": slope,
        "ok": abs(slope) <= max_slope,
    }


def full_loop_report(
    buf: AudioBuffer,
    *,
    seam_tolerance: float = 0.05,
    max_slope: float = 0.005,
    n_sections: int = 8,
) -> dict:
    """Combined seam + flatness report for a game-state loop.

    Returns::

        {
            "seam": <seam_report dict>,
            "flatness": <rms_flatness_report dict>,
            "ok": bool,   # both checks pass
        }
    """
    seam = seam_report(buf, tolerance=seam_tolerance)
    flatness = rms_flatness_report(buf, n_sections=n_sections, max_slope=max_slope)
    return {
        "seam": seam,
        "flatness": flatness,
        "ok": seam["ok"] and flatness["ok"],
    }
