"""soundmatch.core.variants — VariantSpec, sweep(), and render_and_score().

The variant engine (DRY): given base parameters and a sweep axis, generate
a set of VariantSpecs, render each, characterize the output, and score
against the target.  Used by the Variant Grid and the strike_variants port.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

log = logging.getLogger(__name__)

from inspector.metrics import Metrics, characterize
from soundmatch.core.candidate import render_phrase
from soundmatch.core.phrase import Phrase
from soundmatch.core.scoring import Scorecard, diff

# Named macros: predefined param overrides for common variant axes.
_MACROS: dict[str, dict[str, list[dict[str, Any]]]] = {
    "snare": [
        {"snap_level": 0.06, "snap_hi": 6500},
        {"snap_level": 0.12, "snap_hi": 7500},
        {"snap_level": 0.18, "snap_hi": 8500},
        {"snap_level": 0.30, "snap_hi": 9500},
    ],
    "staccato": [
        {"perc_decay": 0.110, "stab_dur": 0.42},
        {"perc_decay": 0.080, "stab_dur": 0.36},
        {"perc_decay": 0.060, "stab_dur": 0.34},
        {"perc_decay": 0.040, "stab_dur": 0.28},
    ],
    "body": [
        {"hp_cutoff": 60, "formant_mix": 0.35, "rolloff": 0.7},
        {"hp_cutoff": 80, "formant_mix": 0.25, "rolloff": 0.65},
        {"hp_cutoff": 110, "formant_mix": 0.20, "rolloff": 0.60},
        {"hp_cutoff": 150, "formant_mix": 0.15, "rolloff": 0.55},
    ],
}


@dataclass
class VariantSpec:
    """A single variant: a name + param overrides to apply on top of base params.

    Attributes:
        name:           Human-readable variant name.
        param_overrides: Dict of param → value to override in the base params.
    """

    name: str
    param_overrides: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "param_overrides": dict(self.param_overrides)}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> VariantSpec:
        return cls(name=d["name"], param_overrides=dict(d.get("param_overrides", {})))


@dataclass
class VariantResult:
    """A scored variant: the spec, the rendered metrics, and the scorecard.

    Attributes:
        spec:    The VariantSpec that was rendered.
        metrics: The measured Metrics of the rendered audio.
        score:   The Scorecard comparing this variant against the target.
        aggregate: The aggregate distance (convenience copy of score.aggregate()).
    """

    spec: VariantSpec
    metrics: Metrics
    score: Scorecard
    aggregate: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "spec": self.spec.to_dict(),
            "metrics": self.metrics.to_dict(),
            "score": self.score.to_dict(),
            "aggregate": self.aggregate,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> VariantResult:
        return cls(
            spec=VariantSpec.from_dict(d["spec"]),
            metrics=Metrics.from_dict(d["metrics"]),
            score=Scorecard.from_dict(d["score"]),
            aggregate=d["aggregate"],
        )


def sweep(
    base_params: dict[str, Any],
    axis: str,
    values: Optional[list[Any]] = None,
) -> list[VariantSpec]:
    """Generate variant specs by sweeping a param or macro over values.

    Parameters
    ----------
    base_params : The base parameter dict (not modified).
    axis        : Either a param name present in base_params, or a named macro
                 (``"snare"``, ``"staccato"``, ``"body"``).
    values      : For a param axis, the list of values to sweep.  Ignored for
                 macros (they define their own value sets).

    Returns
    -------
    List of VariantSpecs, one per value (or macro entry).
    """
    # Check if axis is a macro
    if axis in _MACROS:
        specs: list[VariantSpec] = []
        for i, overrides in enumerate(_MACROS[axis]):
            name = f"{axis}_{i}"
            specs.append(VariantSpec(name=name, param_overrides=dict(overrides)))
        return specs

    # Single-param sweep
    if values is None:
        return []

    specs = []
    for val in values:
        overrides = {axis: val}
        label = f"{axis}={val}"
        specs.append(VariantSpec(name=label, param_overrides=overrides))
    return specs


def render_and_score(
    phrase: Phrase,
    instrument_id: str,
    base_params: dict[str, Any],
    specs: list[VariantSpec],
    target: Metrics,
    layers: Optional[list[tuple[str, dict[str, Any]]]] = None,
    seed: int = 42,
    sr: int = 44100,
    weights: Optional[dict[str, float]] = None,
) -> list[VariantResult]:
    """Render each VariantSpec, measure, and score against the target.

    Parameters
    ----------
    phrase       : The Phrase to render.
    instrument_id: Primary instrument registry key.
    base_params  : Base parameters; each spec's overrides are merged on top.
    specs        : List of VariantSpecs to evaluate.
    target       : Target Metrics to score against.
    layers       : Additional (instrument_id, params) layers for render_phrase.
    seed         : Master seed for deterministic rendering.
    sr           : Sample rate.
    weights      : Optional scoring weights.

    Returns
    -------
    List of VariantResults sorted by aggregate (best first).
    """
    if layers is None:
        layers = []

    results: list[VariantResult] = []
    for spec in specs:
        # Merge base params with spec overrides
        merged_params = dict(base_params)
        merged_params.update(spec.param_overrides)

        # Render
        buf = render_phrase(phrase, instrument_id, merged_params, layers, seed, sr)

        # Characterize (mono mix for analysis)
        y = buf.data.mean(axis=1)
        candidate_m = characterize(y, sr)

        # Score against target
        sc = diff(target, candidate_m, weights=weights)
        agg = sc.aggregate()

        results.append(VariantResult(
            spec=spec,
            metrics=candidate_m,
            score=sc,
            aggregate=agg,
        ))

    # Sort by aggregate (best = lowest distance first)
    results.sort(key=lambda r: r.aggregate)
    return results
