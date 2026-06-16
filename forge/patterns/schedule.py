"""forge.patterns.schedule — bar-indexed pattern schedules.

A Schedule maps bar indices to lists of StepPattern objects, and optionally
carries fill/variation overrides for specific bars (e.g. every 8th bar).

The modulation helpers here encode the "wander, never build" principle used
by game-state loops: random pitch drift and level variation that stay flat
on average rather than accumulating energy.
"""

from __future__ import annotations

from forge.patterns.step import StepPattern


class Schedule:
    """Bar-indexed collection of StepPatterns.

    Usage::

        sched = Schedule(length_bars=8, bpm=138.0)
        sched.add(0, kick_pattern)   # kick fires every bar
        sched.add(0, hat_pattern)
        sched.add(4, fill_pattern)   # fill on bar 4

    ``add`` with ``every=N`` repeats the pattern every N bars.
    """

    def __init__(self, length_bars: int, bpm: float, sr: int = 44100) -> None:
        if bpm <= 0:
            raise ValueError(f"bpm must be positive, got {bpm}")
        if length_bars <= 0:
            raise ValueError(f"length_bars must be positive, got {length_bars}")
        self.length_bars = length_bars
        self.bpm = bpm
        self.sr = sr
        self._patterns: dict[int, list[StepPattern]] = {}

    # ------------------------------------------------------------------
    # Building

    def add(
        self,
        bar: int,
        pattern: StepPattern,
        *,
        every: int | None = None,
    ) -> "Schedule":
        """Add *pattern* starting at *bar*.

        If *every* is given, the pattern is also added at bar + every,
        bar + 2*every, … up to length_bars - 1.
        """
        bars = range(bar, self.length_bars, every) if every else [bar]
        for b in bars:
            if 0 <= b < self.length_bars:
                self._patterns.setdefault(b, []).append(pattern)
        return self

    def add_all(self, pattern: StepPattern) -> "Schedule":
        """Add *pattern* to every bar in the schedule."""
        return self.add(0, pattern, every=1)

    # ------------------------------------------------------------------
    # Query

    def bars_with_patterns(self) -> list[int]:
        return sorted(self._patterns)

    def get_patterns(self, bar: int) -> list[StepPattern]:
        return self._patterns.get(bar, [])

    def __len__(self) -> int:
        return sum(len(ps) for ps in self._patterns.values())

    # ------------------------------------------------------------------
    # Factory

    @classmethod
    def from_pattern_spec(cls, spec: dict) -> "Schedule":
        """Build a Schedule from a PatternSpec dict.

        See ``forge.patterns.step`` module docstring for the format.
        """
        bpm = float(spec["bpm"])
        length_bars = int(spec["length_bars"])
        n_steps = int(spec.get("n_steps", 16))
        sched = cls(length_bars, bpm)

        for track in spec.get("tracks", []):
            pattern = StepPattern.from_track_dict(track, n_steps=n_steps)
            bars = track.get("bars", None)
            every = track.get("every", None)
            if bars is not None:
                for b in bars:
                    sched.add(b, pattern)
            elif every is not None:
                start = int(track.get("bar", 0))
                sched.add(start, pattern, every=int(every))
            else:
                sched.add_all(pattern)

        return sched
