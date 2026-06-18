"""forge.document.channels — channel kinds for the tracker document model.

Three kinds:
  PatternChannel   — a step-grid row (one instrument, N steps with per-step data)
  TextureChannel   — a continuous layer (no steps; driven by an envelope lane)
  AutomationChannel — a control-curve lane bound to a named engine parameter

No Qt, no DSP imports here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class ChannelKind(Enum):
    PATTERN = auto()
    TEXTURE = auto()
    AUTOMATION = auto()


# ---------------------------------------------------------------------------
# Per-step data

@dataclass
class StepData:
    """Data for one step in a PatternChannel."""

    on: bool = False
    accent: bool = False
    ghost: bool = False
    probability: float = 1.0
    params: dict = field(default_factory=dict)
    velocity: float = 1.0

    def _is_plain(self) -> bool:
        """Return True iff the step is plain-on (no non-default fields)."""
        return (
            self.on
            and not self.accent
            and not self.ghost
            and self.probability == 1.0
            and not self.params
            and self.velocity == 1.0
        )

    def to_dict(self) -> dict:
        """Return a PatternSpec-compatible step value (int or dict)."""
        if not self.on:
            return {"on": False}
        d: dict[str, Any] = {"on": True}
        if self.accent:
            d["accent"] = True
        if self.ghost:
            d["ghost"] = True
        if self.probability != 1.0:
            d["probability"] = self.probability
        if self.velocity != 1.0:
            d["velocity"] = self.velocity
        if self.params:
            d["params"] = dict(self.params)
        return d

    def to_step_value(self):
        """Return the compact form used in TrackSpec.steps (0, 1, or dict).

        A plain on-step (no accent, ghost, probability != 1.0, params, or
        velocity != 1.0) is returned as the integer ``1``.  Any non-default
        field causes the full dict form to be returned.
        """
        if not self.on:
            return 0
        if self._is_plain():
            return 1
        return self.to_dict()

    @classmethod
    def from_step_value(cls, v) -> "StepData":
        if v is None or v == 0 or v is False:
            return cls(on=False)
        if v == 1 or v is True:
            return cls(on=True)
        if isinstance(v, dict):
            return cls(
                on=bool(v.get("on", True)),
                accent=bool(v.get("accent", False)),
                ghost=bool(v.get("ghost", False)),
                probability=float(v.get("probability", 1.0)),
                params=dict(v.get("params", {})),
                velocity=float(v.get("velocity", 1.0)),
            )
        return cls(on=bool(v))


# ---------------------------------------------------------------------------
# Channel kinds

@dataclass
class PatternChannel:
    """A step-grid channel: one instrument, N steps."""

    instrument_id: str
    n_steps: int = 16
    steps: list[StepData] = field(default_factory=list)
    params: dict = field(default_factory=dict)  # track-level param overrides
    seed: int = 0
    gain: float = 1.0
    pan: float = 0.0   # −1.0 = hard L, 0.0 = centre, +1.0 = hard R
    reverb_send: float = 0.0  # 0.0 = dry, 1.0 = full send to shared reverb bus

    kind: ChannelKind = field(default=ChannelKind.PATTERN, init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.steps:
            self.steps = [StepData() for _ in range(self.n_steps)]
        elif len(self.steps) < self.n_steps:
            self.steps.extend([StepData() for _ in range(self.n_steps - len(self.steps))])

    def to_track_dict(self) -> dict:
        """Return a TrackSpec-compatible dict for use with control.render_pattern."""
        return {
            "instrument": self.instrument_id,
            "steps": [s.to_step_value() for s in self.steps],
            "params": dict(self.params),
        }

    def to_dict(self) -> dict:
        d: dict[str, Any] = {
            "kind": "pattern",
            "instrument_id": self.instrument_id,
            "n_steps": self.n_steps,
            "steps": [s.to_dict() for s in self.steps],
            "params": dict(self.params),
            "seed": self.seed,
        }
        if self.gain != 1.0:
            d["gain"] = self.gain
        if self.pan != 0.0:
            d["pan"] = self.pan
        if self.reverb_send != 0.0:
            d["reverb_send"] = self.reverb_send
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "PatternChannel":
        steps = [StepData.from_step_value(v) for v in d.get("steps", [])]
        n = int(d.get("n_steps", 16))
        return cls(
            instrument_id=str(d["instrument_id"]),
            n_steps=n,
            steps=steps or [StepData() for _ in range(n)],
            params=dict(d.get("params", {})),
            seed=int(d.get("seed", 0)),
            gain=float(d.get("gain", 1.0)),
            pan=float(d.get("pan", 0.0)),
            reverb_send=float(d.get("reverb_send", 0.0)),
        )

    def copy(self) -> "PatternChannel":
        import copy
        ch = PatternChannel(
            instrument_id=self.instrument_id,
            n_steps=self.n_steps,
            steps=[copy.copy(s) for s in self.steps],
            params=dict(self.params),
            seed=self.seed,
            gain=self.gain,
            pan=self.pan,
            reverb_send=self.reverb_send,
        )
        return ch


# ---------------------------------------------------------------------------

@dataclass
class Breakpoint:
    """A time-value control point (bar, value)."""

    bar: float
    value: float

    def to_tuple(self) -> tuple:
        return (self.bar, self.value)


@dataclass
class TextureChannel:
    """A continuous texture layer driven by an envelope of breakpoints.

    Stub in Phase 1; fleshed out fully in Phase 6.
    """

    instrument_id: str
    params: dict = field(default_factory=dict)
    seed: int = 0
    envelope: list[Breakpoint] = field(default_factory=list)
    gain: float = 1.0
    pan: float = 0.0   # −1.0 = hard L, 0.0 = centre, +1.0 = hard R
    reverb_send: float = 0.0  # 0.0 = dry, 1.0 = full send to shared reverb bus

    kind: ChannelKind = field(default=ChannelKind.TEXTURE, init=False, repr=False)

    def to_dict(self) -> dict:
        d: dict[str, Any] = {
            "kind": "texture",
            "instrument_id": self.instrument_id,
            "params": dict(self.params),
            "seed": self.seed,
            "envelope": [{"bar": b.bar, "value": b.value} for b in self.envelope],
        }
        if self.gain != 1.0:
            d["gain"] = self.gain
        if self.pan != 0.0:
            d["pan"] = self.pan
        if self.reverb_send != 0.0:
            d["reverb_send"] = self.reverb_send
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "TextureChannel":
        envelope = [Breakpoint(float(b["bar"]), float(b["value"])) for b in d.get("envelope", [])]
        return cls(
            instrument_id=str(d["instrument_id"]),
            params=dict(d.get("params", {})),
            seed=int(d.get("seed", 0)),
            envelope=envelope,
            gain=float(d.get("gain", 1.0)),
            pan=float(d.get("pan", 0.0)),
            reverb_send=float(d.get("reverb_send", 0.0)),
        )

    def copy(self) -> "TextureChannel":
        return TextureChannel(
            instrument_id=self.instrument_id,
            params=dict(self.params),
            seed=self.seed,
            envelope=[Breakpoint(b.bar, b.value) for b in self.envelope],
            gain=self.gain,
            pan=self.pan,
            reverb_send=self.reverb_send,
        )


@dataclass
class AutomationChannel:
    """An automation lane binding breakpoints to a named engine parameter.

    When ``target_channel`` is None (default) the lane targets a global/master
    parameter (e.g. ``target_param == "master_gain"``).

    When ``target_channel`` is an int it targets the instrument param named
    ``target_param`` on that PatternChannel index (e.g. acid ``cutoff``).
    """

    target_param: str  # e.g. "master_gain", "cutoff"
    breakpoints: list[Breakpoint] = field(default_factory=list)
    target_channel: int | None = None  # None → global/master; int → per-channel param

    kind: ChannelKind = field(default=ChannelKind.AUTOMATION, init=False, repr=False)

    def to_dict(self) -> dict:
        d: dict[str, Any] = {
            "kind": "automation",
            "target_param": self.target_param,
            "breakpoints": [{"bar": b.bar, "value": b.value} for b in self.breakpoints],
        }
        if self.target_channel is not None:
            d["target_channel"] = self.target_channel
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "AutomationChannel":
        bps = [Breakpoint(float(b["bar"]), float(b["value"])) for b in d.get("breakpoints", [])]
        tc = d.get("target_channel")
        return cls(
            target_param=str(d["target_param"]),
            breakpoints=bps,
            target_channel=int(tc) if tc is not None else None,
        )

    def copy(self) -> "AutomationChannel":
        return AutomationChannel(
            target_param=self.target_param,
            breakpoints=[Breakpoint(b.bar, b.value) for b in self.breakpoints],
            target_channel=self.target_channel,
        )


# ---------------------------------------------------------------------------
# Union type alias

AnyChannel = PatternChannel | TextureChannel | AutomationChannel


def channel_from_dict(d: dict) -> AnyChannel:
    kind = d.get("kind", "pattern")
    if kind == "pattern":
        return PatternChannel.from_dict(d)
    elif kind == "texture":
        return TextureChannel.from_dict(d)
    elif kind == "automation":
        return AutomationChannel.from_dict(d)
    raise ValueError(f"Unknown channel kind: {kind!r}")
