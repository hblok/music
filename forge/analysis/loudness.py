"""forge.analysis.loudness — per-section RMS reports and build-headroom checks.

These encode the lessons from the listening sessions in machine-checkable form:
  - "aftermath quieter than intro"       → intro_vs_aftermath()
  - "no audible energy build in a loop"  → rms_trend_slope()
  - "headroom for the mix"               → peak_headroom_db()

All functions accept an AudioBuffer and return plain dicts or floats so they
can be printed, logged, or compared in tests without extra dependencies.
"""

from __future__ import annotations

import math

import numpy as np

from forge.core.buffer import AudioBuffer
from forge.core.grid import Grid


def section_rms_report(
    buf: AudioBuffer,
    n_sections: int = 8,
) -> dict:
    """Per-section RMS values and summary statistics.

    Returns::

        {
            "section_rms": [float, ...],   # one per section
            "mean_rms": float,
            "max_rms":  float,
            "min_rms":  float,
            "peak":     float,
            "peak_db":  float,
        }
    """
    rms_vals = buf.section_rms(n_sections)
    arr = np.array(rms_vals)
    peak = buf.peak()
    return {
        "section_rms": rms_vals,
        "mean_rms": float(arr.mean()),
        "max_rms": float(arr.max()),
        "min_rms": float(arr.min()),
        "peak": peak,
        "peak_db": 20.0 * math.log10(max(peak, 1e-12)),
    }


def rms_trend_slope(
    buf: AudioBuffer,
    n_sections: int = 8,
) -> float:
    """Linear regression slope of per-section RMS (positive = building energy).

    For game loops the ideal slope is near zero (flat).  A positive slope
    indicates the loop builds energy each cycle — the "never build" anti-pattern.

    Returns slope in RMS/section (positive = rising).
    """
    rms_vals = np.array(buf.section_rms(n_sections), dtype=np.float64)
    x = np.arange(len(rms_vals), dtype=np.float64)
    slope = float(np.polyfit(x, rms_vals, 1)[0])
    return slope


def peak_headroom_db(buf: AudioBuffer) -> float:
    """Headroom below 0 dBFS in dB (positive = below peak)."""
    peak = buf.peak()
    if peak < 1e-12:
        return 96.0
    return -20.0 * math.log10(peak)


def spectral_centroid(buf: AudioBuffer, *, sr: int = 44100) -> float:
    """Magnitude-weighted mean frequency (Hz) of *buf* summed to mono.

    Uses a real FFT over the entire buffer.  Both channels are summed before
    analysis so stereo content is treated equally.

    Args:
        buf: AudioBuffer to analyse (any length).
        sr:  Sample rate in Hz (default 44100).

    Returns:
        Spectral centroid in Hz (scalar float).
    """
    mono = buf.data[:, 0] + buf.data[:, 1]  # sum to mono
    magnitude = np.abs(np.fft.rfft(mono))
    freqs = np.fft.rfftfreq(len(mono), d=1.0 / sr)
    total = magnitude.sum()
    if total < 1e-12:
        return 0.0
    return float(np.dot(freqs, magnitude) / total)


def intro_vs_aftermath(
    buf: AudioBuffer,
    bpm: float,
    *,
    intro_bars: int = 4,
    aftermath_start_bar: int | None = None,
    aftermath_bars: int = 4,
    sr: int = 44100,
) -> dict:
    """Compare intro loudness to aftermath (end-of-track) loudness.

    The "aftermath quieter than intro" principle means the track should end
    softer than it starts — the aftermath RMS should be lower than the intro.

    Args:
        buf:                   AudioBuffer of the full rendered track.
        bpm:                   Tempo (to convert bars to samples).
        intro_bars:            Length of intro window in bars.
        aftermath_start_bar:   Bar at which aftermath begins (default: from end).
        aftermath_bars:        Length of aftermath window in bars.
        sr:                    Sample rate.

    Returns::

        {
            "intro_rms":         float,
            "aftermath_rms":     float,
            "ratio_db":          float,   # aftermath - intro in dB (<0 = quieter)
            "aftermath_quieter": bool,
        }
    """
    grid = Grid(bpm, sr=sr)
    intro_n = min(int(intro_bars * grid.bar * sr), len(buf))
    intro_data = buf.data[:intro_n]
    intro_rms = float(np.sqrt(np.mean(intro_data ** 2)))

    if aftermath_start_bar is None:
        aftermath_n = min(int(aftermath_bars * grid.bar * sr), len(buf))
        aftermath_data = buf.data[len(buf) - aftermath_n:]
    else:
        start_s = int(aftermath_start_bar * grid.bar * sr)
        end_s = min(start_s + int(aftermath_bars * grid.bar * sr), len(buf))
        aftermath_data = buf.data[start_s:end_s]

    aftermath_rms = float(np.sqrt(np.mean(aftermath_data ** 2)))

    intro_db = 20.0 * math.log10(max(intro_rms, 1e-12))
    aftermath_db = 20.0 * math.log10(max(aftermath_rms, 1e-12))
    ratio_db = aftermath_db - intro_db

    return {
        "intro_rms": intro_rms,
        "aftermath_rms": aftermath_rms,
        "ratio_db": ratio_db,
        "aftermath_quieter": aftermath_rms < intro_rms,
    }
