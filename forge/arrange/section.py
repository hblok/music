"""forge.arrange.section — a named bar range with one or more Schedules.

A Section is the compositional unit above a pattern: it holds patterns for
a fixed time window in the track and an optional per-section gain.  Multiple
sections can overlap (they are simply summed into the track buffer).

Typical use::

    intro = Section("intro", start_bar=0, length_bars=8, gain=0.8)
    intro.add_schedule(kick_schedule)
    intro.add_schedule(bass_schedule)

    drop = Section("drop", start_bar=8, length_bars=16)
    drop.add_schedule(full_schedule)
"""

from __future__ import annotations

from forge.core.buffer import AudioBuffer
from forge.core.grid import Grid
from forge.core.rng import RngContext
from forge.instruments.base import RenderCache
from forge.patterns.groove import render_groove
from forge.patterns.schedule import Schedule


class Section:
    """A bar range containing one or more Schedules.

    Args:
        name:        Human-readable label (used as RNG key).
        start_bar:   Where in the track this section starts (bars).
        length_bars: Duration of the section (bars).
        gain:        Linear gain applied to the mixed section output.
    """

    def __init__(
        self,
        name: str,
        start_bar: int,
        length_bars: int,
        *,
        gain: float = 1.0,
    ) -> None:
        if length_bars <= 0:
            raise ValueError(f"length_bars must be positive, got {length_bars}")
        self.name = name
        self.start_bar = start_bar
        self.length_bars = length_bars
        self.gain = gain
        self._schedules: list[Schedule] = []

    # ------------------------------------------------------------------
    # Building

    def add_schedule(self, schedule: Schedule) -> "Section":
        """Attach a Schedule to this section.  Returns self for chaining."""
        self._schedules.append(schedule)
        return self

    # ------------------------------------------------------------------
    # Rendering

    def render(
        self,
        rng_ctx: RngContext,
        *,
        cache: RenderCache | None = None,
        sr: int = 44100,
    ) -> AudioBuffer:
        """Mix all schedules into one section-length AudioBuffer.

        Each schedule gets its own RNG sub-context via the schedule index,
        so adding/removing schedules doesn't shift other streams.
        """
        grid = Grid(self._bpm(), sr=sr)
        n = grid.n_samples(self.length_bars)
        buf = AudioBuffer(n, sr=sr)

        for idx, sched in enumerate(self._schedules):
            child_ctx = rng_ctx.spawn(f"{self.name}.sched{idx}")
            layer = render_groove(sched, child_ctx, cache=cache, sr=sr)
            # trim or pad to section length
            copy_n = min(len(layer), n)
            buf.data[:copy_n] += layer.data[:copy_n]

        if self.gain != 1.0:
            buf.data *= self.gain

        return buf

    # ------------------------------------------------------------------
    # Helpers

    def _bpm(self) -> float:
        if not self._schedules:
            raise RuntimeError(f"Section '{self.name}' has no schedules")
        return self._schedules[0].bpm

    @property
    def end_bar(self) -> int:
        return self.start_bar + self.length_bars

    def __repr__(self) -> str:
        return (
            f"Section('{self.name}', "
            f"start={self.start_bar}, len={self.length_bars}, "
            f"schedules={len(self._schedules)})"
        )
