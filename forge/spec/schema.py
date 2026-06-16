"""forge.spec.schema — dataclass-based project spec.

All spec classes are plain Python dataclasses (no Pydantic).  They carry
the type and default information needed to validate user-supplied dicts and
to round-trip through JSON.

The canonical format is the dict form (used by control.render_track and the
UI serializer).  The dataclasses here add type checking on top.

Hierarchy::

    ProjectSpec
      └── SectionSpec[]
            └── PatternSpec (schedule)
                  └── TrackSpec[]
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TrackSpec:
    """One instrument row in a step pattern."""

    instrument: str
    steps: list = field(default_factory=lambda: [0] * 16)
    params: dict = field(default_factory=dict)
    probability: float = 1.0
    bars: list[int] | None = None
    every: int | None = None

    def to_dict(self) -> dict:
        d: dict[str, Any] = {
            "instrument": self.instrument,
            "steps": self.steps,
        }
        if self.params:
            d["params"] = self.params
        if self.probability != 1.0:
            d["probability"] = self.probability
        if self.bars is not None:
            d["bars"] = self.bars
        if self.every is not None:
            d["every"] = self.every
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "TrackSpec":
        return cls(
            instrument=str(d["instrument"]),
            steps=list(d.get("steps", [0] * 16)),
            params=dict(d.get("params", {})),
            probability=float(d.get("probability", 1.0)),
            bars=list(d["bars"]) if "bars" in d else None,
            every=int(d["every"]) if "every" in d else None,
        )


@dataclass
class PatternSpec:
    """A step-grid schedule (used as a section's schedule)."""

    bpm: float
    length_bars: int
    tracks: list[TrackSpec] = field(default_factory=list)
    n_steps: int = 16
    loop: bool = False
    xf_bars: float = 2.0

    def to_dict(self) -> dict:
        return {
            "bpm": self.bpm,
            "length_bars": self.length_bars,
            "n_steps": self.n_steps,
            "loop": self.loop,
            "xf_bars": self.xf_bars,
            "tracks": [t.to_dict() for t in self.tracks],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PatternSpec":
        return cls(
            bpm=float(d["bpm"]),
            length_bars=int(d["length_bars"]),
            tracks=[TrackSpec.from_dict(t) for t in d.get("tracks", [])],
            n_steps=int(d.get("n_steps", 16)),
            loop=bool(d.get("loop", False)),
            xf_bars=float(d.get("xf_bars", 2.0)),
        )


@dataclass
class SectionSpec:
    """A named bar range with one or more PatternSpec schedules."""

    name: str
    start_bar: int
    length_bars: int
    schedules: list[PatternSpec] = field(default_factory=list)
    gain: float = 1.0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "start_bar": self.start_bar,
            "length_bars": self.length_bars,
            "gain": self.gain,
            "schedules": [s.to_dict() for s in self.schedules],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SectionSpec":
        return cls(
            name=str(d["name"]),
            start_bar=int(d["start_bar"]),
            length_bars=int(d["length_bars"]),
            gain=float(d.get("gain", 1.0)),
            schedules=[PatternSpec.from_dict(s) for s in d.get("schedules", [])],
        )


@dataclass
class ProjectSpec:
    """Top-level project document."""

    title: str
    bpm: float
    sections: list[SectionSpec] = field(default_factory=list)
    seed: int = 0
    sr: int = 44100
    normalize: bool = True
    target: float = 0.85
    fade_out_s: float = 2.0
    master_gain_curve: list[list[float]] | None = None

    def to_dict(self) -> dict:
        d: dict[str, Any] = {
            "title": self.title,
            "bpm": self.bpm,
            "seed": self.seed,
            "sr": self.sr,
            "normalize": self.normalize,
            "target": self.target,
            "fade_out_s": self.fade_out_s,
            "sections": [s.to_dict() for s in self.sections],
        }
        if self.master_gain_curve is not None:
            d["master_gain_curve"] = self.master_gain_curve
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "ProjectSpec":
        return cls(
            title=str(d["title"]),
            bpm=float(d["bpm"]),
            sections=[SectionSpec.from_dict(s) for s in d.get("sections", [])],
            seed=int(d.get("seed", 0)),
            sr=int(d.get("sr", 44100)),
            normalize=bool(d.get("normalize", True)),
            target=float(d.get("target", 0.85)),
            fade_out_s=float(d.get("fade_out_s", 2.0)),
            master_gain_curve=d.get("master_gain_curve"),
        )
