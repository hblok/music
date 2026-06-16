"""forge.patterns.step — step patterns: 16th-step grids with per-step events.

A StepPattern maps step indices to Step events.  Steps carry instrument id,
param overrides, and stochastic modifiers (probability, accent, ghost).

The dict-based PatternSpec is the interchange format used by control.render_pattern
and the UI.  format summary::

    {
        "bpm": 138.0,
        "length_bars": 8,
        "n_steps": 16,          # optional, default 16
        "loop": False,          # optional, apply loop_fold after render
        "tracks": [
            {
                "instrument": "kick",
                "steps": [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0],
                "params": {"f0": 55.0},     # applied to every step
                "probability": 1.0,         # per-track default probability
            }
        ]
    }

Each element of ``steps`` may be:
    - ``0`` / ``False`` / ``None``  → silent
    - ``1`` / ``True``              → fire with track defaults
    - dict with optional keys: ``on``, ``params``, ``probability``,
                                ``accent``, ``ghost``
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Step:
    """A single event on the step grid."""

    instrument_id: str
    params: dict = field(default_factory=dict)
    probability: float = 1.0
    accent: bool = False
    ghost: bool = False


class StepPattern:
    """16-step (or n_steps-step) pattern for one instrument layer.

    ``steps`` is a sparse list — ``None`` indices are silent.
    """

    def __init__(
        self,
        instrument_id: str,
        n_steps: int = 16,
        *,
        default_params: dict | None = None,
        default_probability: float = 1.0,
    ) -> None:
        self.instrument_id = instrument_id
        self.n_steps = n_steps
        self.default_params = default_params or {}
        self.default_probability = default_probability
        self._steps: list[Step | None] = [None] * n_steps

    # ------------------------------------------------------------------
    # Building

    def set(
        self,
        idx: int,
        *,
        params: dict | None = None,
        probability: float | None = None,
        accent: bool = False,
        ghost: bool = False,
    ) -> "StepPattern":
        """Set step *idx* to fire.  Returns self for chaining."""
        merged = {**self.default_params, **(params or {})}
        p = probability if probability is not None else self.default_probability
        self._steps[idx] = Step(self.instrument_id, merged, p, accent, ghost)
        return self

    def clear(self, idx: int) -> "StepPattern":
        self._steps[idx] = None
        return self

    # ------------------------------------------------------------------
    # Query

    def hits(self) -> list[tuple[int, Step]]:
        """Return ``(step_index, Step)`` pairs for non-silent steps."""
        return [(i, s) for i, s in enumerate(self._steps) if s is not None]

    def __len__(self) -> int:
        return self.n_steps

    # ------------------------------------------------------------------
    # Factory: build from a PatternSpec track dict

    @classmethod
    def from_track_dict(cls, track: dict, n_steps: int = 16) -> "StepPattern":
        """Parse one entry from PatternSpec ``tracks`` list."""
        iid = track["instrument"]
        base_params = dict(track.get("params", {}))
        base_prob = float(track.get("probability", 1.0))
        raw_steps = track.get("steps", [])

        pat = cls(iid, n_steps=n_steps, default_params=base_params,
                  default_probability=base_prob)

        for idx, raw in enumerate(raw_steps):
            if idx >= n_steps:
                break
            if raw is None or raw == 0 or raw is False:
                continue
            if raw == 1 or raw is True:
                pat.set(idx)
            elif isinstance(raw, dict):
                if not raw.get("on", True):
                    continue
                step_params = {**base_params, **raw.get("params", {})}
                p = float(raw.get("probability", base_prob))
                pat.set(idx,
                        params=step_params,
                        probability=p,
                        accent=bool(raw.get("accent", False)),
                        ghost=bool(raw.get("ghost", False)))
        return pat
