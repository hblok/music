"""Grid — tempo/bar/beat/16th-step ↔ seconds conversions.

This is the unit all sequencers and schedulers work against.  A Grid is
immutable once created; construct one per track with the track's tempo.

Terminology:
  bar    — 4 beats (one measure in 4/4)
  beat   — one quarter note
  step   — one 16th note (beat / 4)
  grid0  — optional time offset of bar 0 (seconds, default 0.0)
"""

from __future__ import annotations

import numpy as np


class Grid:
    """Tempo grid: converts bar/beat/step positions to seconds (and samples).

    Args:
        bpm:   Beats per minute (quarter-note BPM).
        sr:    Sample rate in Hz (default 44100).
        grid0: Seconds offset for bar 0 (matches legacy GRID0 constant).
    """

    def __init__(self, bpm: float, sr: int = 44100, grid0: float = 0.0) -> None:
        if bpm <= 0:
            raise ValueError(f"BPM must be positive, got {bpm}")
        self.bpm: float = float(bpm)
        self.sr: int = sr
        self.grid0: float = float(grid0)

    # ---------------------------------------------------------------- derived

    @property
    def beat(self) -> float:
        """Duration of one beat (quarter note) in seconds."""
        return 60.0 / self.bpm

    @property
    def bar(self) -> float:
        """Duration of one bar (4 beats) in seconds."""
        return self.beat * 4.0

    @property
    def step(self) -> float:
        """Duration of one 16th-note step in seconds."""
        return self.beat / 4.0

    # ---------------------------------------------------------------- conversion

    def bar_t(self, bar: float, beat: float = 0.0) -> float:
        """Return the absolute time (seconds) of *bar* + *beat* offset.

        Matches the legacy ``bar_t(b, beat=0)`` helper present in all scripts
        with a tempo grid.  The *beat* parameter is a fractional beat count
        (0.0–3.999… within a 4/4 bar).
        """
        return self.grid0 + bar * self.bar + beat * self.beat

    def bar_samples(self, bar: float, beat: float = 0.0) -> int:
        """Return *bar_t* converted to an integer sample index."""
        return int(self.bar_t(bar, beat) * self.sr)

    def step_t(self, bar: float, step: float = 0.0) -> float:
        """Return the absolute time (seconds) of *bar* + *step* 16th-steps."""
        return self.grid0 + bar * self.bar + step * self.step

    def step_samples(self, bar: float, step: float = 0.0) -> int:
        return int(self.step_t(bar, step) * self.sr)

    def seconds_to_bar(self, t: float) -> float:
        """Convert absolute time *t* (seconds) to a fractional bar number."""
        return (t - self.grid0) / self.bar

    def seconds_to_beat(self, t: float) -> float:
        """Convert absolute time *t* to a fractional beat number."""
        return (t - self.grid0) / self.beat

    def duration_bars(self, duration_s: float) -> float:
        """Convert a duration in seconds to bars."""
        return duration_s / self.bar

    def n_samples(self, n_bars: float) -> int:
        """Number of samples for *n_bars* complete bars."""
        return int(n_bars * self.bar * self.sr)

    # ---------------------------------------------------------------- time vector

    def time_vector(self, n_samples: int) -> np.ndarray:
        """Return a (n_samples,) float64 time array t = arange(N)/sr."""
        return np.arange(n_samples, dtype=np.float64) / self.sr
