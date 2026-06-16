"""forge.arrange.curves — piecewise-linear automation curves.

Curves drive per-section gain, pan, sidechain duck depth, and similar
continuous parameters.  They are defined as (bar, value) anchor points and
sampled to a per-sample array at render time.

Design principles from the implementation plan:
- "aftermath quieter than intro" → model as an energy curve with a lower tail
- sidechain pumping → a ducking curve triggered every beat
- "wander, never build" → flat RMS trend, not a rising energy curve

Usage::

    # fade in over 4 bars, hold, fade out
    env = Curve([(0, 0.0), (4, 1.0), (28, 1.0), (32, 0.0)])
    samples = env.sample(n_samples=total_n, bpm=138.0, sr=44100)
    buf.data *= samples[:, np.newaxis]
"""

from __future__ import annotations

import numpy as np

from forge.core.grid import Grid


class Curve:
    """Piecewise-linear automation curve defined by (bar, value) anchors.

    Values are interpolated linearly between anchors.  Outside the defined
    range the curve holds the first/last anchor value.
    """

    def __init__(self, points: list[tuple[float, float]]) -> None:
        if len(points) < 2:
            raise ValueError("Curve needs at least 2 anchor points")
        pts = sorted(points, key=lambda p: p[0])
        self._bars = np.array([p[0] for p in pts], dtype=np.float64)
        self._vals = np.array([p[1] for p in pts], dtype=np.float64)

    def at(self, bar: float) -> float:
        """Interpolated value at *bar*."""
        return float(np.interp(bar, self._bars, self._vals))

    def sample(
        self,
        n_samples: int,
        bpm: float,
        *,
        sr: int = 44100,
    ) -> np.ndarray:
        """Return a per-sample float64 array of shape (n_samples,).

        Args:
            n_samples: output length in samples.
            bpm:       tempo used to convert bars to seconds.
            sr:        sample rate.
        """
        grid = Grid(bpm, sr=sr)
        tt = np.arange(n_samples, dtype=np.float64)
        bar_t = tt / (grid.bar * sr)  # fractional bar position per sample
        return np.interp(bar_t, self._bars, self._vals)

    def __repr__(self) -> str:
        pts = list(zip(self._bars.tolist(), self._vals.tolist()))
        return f"Curve({pts})"


# ---------------------------------------------------------------------------
# Factory curves

def constant(value: float) -> Curve:
    """A flat curve holding *value* from bar 0 to bar 1."""
    return Curve([(0.0, value), (1.0, value)])


def fade_in(n_bars: float, *, start: float = 0.0, end: float = 1.0) -> Curve:
    return Curve([(0.0, start), (n_bars, end)])


def fade_out(n_bars: float, *, start: float = 1.0, end: float = 0.0) -> Curve:
    return Curve([(0.0, start), (n_bars, end)])


def fade_in_out(
    n_bars: float,
    *,
    ramp_bars: float = 2.0,
) -> Curve:
    """Hold at 1.0 with *ramp_bars* fade-in/out at both ends."""
    return Curve([
        (0.0, 0.0),
        (ramp_bars, 1.0),
        (n_bars - ramp_bars, 1.0),
        (n_bars, 0.0),
    ])


def sidechain_pump(
    n_bars: float,
    bpm: float,
    *,
    depth: float = 0.6,
    attack_beats: float = 0.05,
    release_beats: float = 0.8,
) -> Curve:
    """Sidechain ducking curve: ducks on every beat, releases over *release_beats*.

    Args:
        n_bars:         total duration in bars.
        bpm:            tempo (for beat timing).
        depth:          how far the level dips (1 = full silence, 0 = no duck).
        attack_beats:   time from beat to floor (fast).
        release_beats:  time from floor back to 1.0 (slower).
    """
    beat_bars = 1.0 / 4.0  # one beat = 1/4 bar
    total_beats = int(n_bars / beat_bars) + 1
    points: list[tuple[float, float]] = [(0.0, 1.0)]
    for beat in range(total_beats):
        t0 = beat * beat_bars
        t_attack = t0 + attack_beats * beat_bars
        t_release = t0 + release_beats * beat_bars
        points.append((t0, 1.0 - depth))
        points.append((t_attack, 1.0 - depth))
        if t_release < n_bars:
            points.append((t_release, 1.0))
    points.append((n_bars, 1.0))
    return Curve(points)
