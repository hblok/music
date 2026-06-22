"""soundmatch.core.scoring — Scorecard and diff between target and candidate metrics.

``Scorecard`` holds per-metric target/candidate/Δ values.  ``diff()`` computes
a Scorecard from two Metrics objects.  ``Scorecard.aggregate`` returns a
weighted normalized distance (0 = perfect, 1 = worst).  ``Scorecard.worst()``
identifies the metric to chase next.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from inspector.metrics import Metrics

# Default weights: each metric axis contributes equally by default.
# Band-balance and band-decay are aggregated into single numbers.
_DEFAULT_WEIGHTS: dict[str, float] = {
    "percussive_ratio": 1.0,
    "centroid_hz": 1.0,
    "band_balance": 1.0,
    "onset_count": 1.0,
    "onset_density": 1.0,
    "median_ioi_s": 1.0,
    "band_decay_ms": 1.0,
}

# Normalization scales — rough "full range" for each metric so that
# raw differences map to [0, 1] in a meaningful way.
_NORM_SCALES: dict[str, float] = {
    "percussive_ratio": 50.0,    # 0–100 % → full range 50
    "centroid_hz": 3000.0,       # 0–6000 Hz → full range 3000
    "band_balance": 30.0,        # per-band % → full range 30
    "onset_count": 20.0,         # count → full range 20
    "onset_density": 10.0,       # events/sec → full range 10
    "median_ioi_s": 0.5,         # seconds → full range 0.5
    "band_decay_ms": 200.0,      # ms → full range 200
}


@dataclass(frozen=True)
class MetricDelta:
    """Per-metric comparison: target value, candidate value, and Δ."""
    target: float
    candidate: float
    delta: float  # absolute difference

    def to_dict(self) -> dict[str, float]:
        return {"target": self.target, "candidate": self.candidate, "delta": self.delta}

    @classmethod
    def from_dict(cls, d: dict[str, float]) -> MetricDelta:
        return cls(target=d["target"], candidate=d["candidate"], delta=d["delta"])


@dataclass
class Scorecard:
    """Per-metric target/candidate/Δ comparison with aggregate scoring.

    Attributes:
        percussive_ratio: Δ for percussive ratio (%).
        centroid_hz:      Δ for spectral centroid (Hz).
        band_balance:     Per-band Δ dict (band label → MetricDelta).
        onset_count:      Δ for onset count.
        onset_density:    Δ for onset density (events/sec).
        median_ioi_s:     Δ for median inter-onset interval (s).
        band_decay_ms:    Per-band Δ dict (band label → MetricDelta).
    """

    percussive_ratio: MetricDelta
    centroid_hz: MetricDelta
    band_balance: dict[str, MetricDelta]
    onset_count: MetricDelta
    onset_density: MetricDelta
    median_ioi_s: MetricDelta
    band_decay_ms: dict[str, MetricDelta]
    _weights: dict[str, float] = field(default_factory=lambda: dict(_DEFAULT_WEIGHTS))

    def aggregate(self) -> float:
        """Weighted normalized distance (0 = perfect match, 1 = worst)."""
        contributions: list[float] = []
        weight_sum = 0.0

        # Scalar metrics
        for name in ("percussive_ratio", "centroid_hz", "onset_count",
                      "onset_density", "median_ioi_s"):
            md: MetricDelta = getattr(self, name)
            w = self._weights.get(name, 1.0)
            scale = _NORM_SCALES.get(name, 1.0)
            norm_delta = min(abs(md.delta) / scale, 1.0)
            contributions.append(w * norm_delta)
            weight_sum += w

        # band_balance: average of per-band normalized deltas
        if self.band_balance:
            w = self._weights.get("band_balance", 1.0)
            scale = _NORM_SCALES.get("band_balance", 1.0)
            band_deltas = [min(abs(v.delta) / scale, 1.0) for v in self.band_balance.values()]
            contributions.append(w * (sum(band_deltas) / len(band_deltas)))
            weight_sum += w

        # band_decay_ms: average of per-band normalized deltas
        if self.band_decay_ms:
            w = self._weights.get("band_decay_ms", 1.0)
            scale = _NORM_SCALES.get("band_decay_ms", 1.0)
            decay_deltas = [min(abs(v.delta) / scale, 1.0) for v in self.band_decay_ms.values()]
            contributions.append(w * (sum(decay_deltas) / len(decay_deltas)))
            weight_sum += w

        if weight_sum < 1e-12:
            return 0.0
        return sum(contributions) / weight_sum

    def worst(self) -> str:
        """Name of the metric with the largest weighted normalized Δ.

        Returns one of: ``"percussive_ratio"``, ``"centroid_hz"``,
        ``"band_balance"``, ``"onset_count"``, ``"onset_density"``,
        ``"median_ioi_s"``, ``"band_decay_ms"``.
        """
        worst_name = "percussive_ratio"
        worst_val = -1.0

        for name in ("percussive_ratio", "centroid_hz", "onset_count",
                      "onset_density", "median_ioi_s"):
            md: MetricDelta = getattr(self, name)
            w = self._weights.get(name, 1.0)
            scale = _NORM_SCALES.get(name, 1.0)
            norm_delta = min(abs(md.delta) / scale, 1.0)
            weighted = w * norm_delta
            if weighted > worst_val:
                worst_val = weighted
                worst_name = name

        # band_balance aggregate
        if self.band_balance:
            w = self._weights.get("band_balance", 1.0)
            scale = _NORM_SCALES.get("band_balance", 1.0)
            band_deltas = [min(abs(v.delta) / scale, 1.0) for v in self.band_balance.values()]
            weighted = w * (sum(band_deltas) / len(band_deltas))
            if weighted > worst_val:
                worst_val = weighted
                worst_name = "band_balance"

        # band_decay_ms aggregate
        if self.band_decay_ms:
            w = self._weights.get("band_decay_ms", 1.0)
            scale = _NORM_SCALES.get("band_decay_ms", 1.0)
            decay_deltas = [min(abs(v.delta) / scale, 1.0) for v in self.band_decay_ms.values()]
            weighted = w * (sum(decay_deltas) / len(decay_deltas))
            if weighted > worst_val:
                worst_val = weighted
                worst_name = "band_decay_ms"

        return worst_name

    def to_dict(self) -> dict[str, Any]:
        """Serialize for project save."""
        return {
            "percussive_ratio": self.percussive_ratio.to_dict(),
            "centroid_hz": self.centroid_hz.to_dict(),
            "band_balance": {k: v.to_dict() for k, v in self.band_balance.items()},
            "onset_count": self.onset_count.to_dict(),
            "onset_density": self.onset_density.to_dict(),
            "median_ioi_s": self.median_ioi_s.to_dict(),
            "band_decay_ms": {k: v.to_dict() for k, v in self.band_decay_ms.items()},
            "weights": dict(self._weights),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Scorecard:
        """Deserialize from project load."""
        return cls(
            percussive_ratio=MetricDelta.from_dict(d["percussive_ratio"]),
            centroid_hz=MetricDelta.from_dict(d["centroid_hz"]),
            band_balance={k: MetricDelta.from_dict(v) for k, v in d.get("band_balance", {}).items()},
            onset_count=MetricDelta.from_dict(d["onset_count"]),
            onset_density=MetricDelta.from_dict(d["onset_density"]),
            median_ioi_s=MetricDelta.from_dict(d["median_ioi_s"]),
            band_decay_ms={k: MetricDelta.from_dict(v) for k, v in d.get("band_decay_ms", {}).items()},
            _weights=d.get("weights", dict(_DEFAULT_WEIGHTS)),
        )


def diff(
    target: Metrics,
    cand: Metrics,
    weights: Optional[dict[str, float]] = None,
) -> Scorecard:
    """Compute a Scorecard comparing target and candidate Metrics.

    Parameters
    ----------
    target  : The reference target Metrics.
    cand    : The candidate Metrics.
    weights : Optional dict of metric name → weight (overrides defaults).

    Returns
    -------
    Scorecard with per-metric deltas and the specified weights.
    """
    w = dict(_DEFAULT_WEIGHTS)
    if weights is not None:
        w.update(weights)

    # Scalar metrics
    perc = MetricDelta(
        target=target.percussive_ratio,
        candidate=cand.percussive_ratio,
        delta=abs(target.percussive_ratio - cand.percussive_ratio),
    )
    cent = MetricDelta(
        target=target.centroid_hz,
        candidate=cand.centroid_hz,
        delta=abs(target.centroid_hz - cand.centroid_hz),
    )
    onsets = MetricDelta(
        target=float(target.onset_count),
        candidate=float(cand.onset_count),
        delta=abs(float(target.onset_count) - float(cand.onset_count)),
    )
    density = MetricDelta(
        target=target.onset_density,
        candidate=cand.onset_density,
        delta=abs(target.onset_density - cand.onset_density),
    )
    ioi = MetricDelta(
        target=target.median_ioi_s,
        candidate=cand.median_ioi_s,
        delta=abs(target.median_ioi_s - cand.median_ioi_s),
    )

    # Per-band balance deltas
    bb: dict[str, MetricDelta] = {}
    all_band_keys = set(target.band_balance) | set(cand.band_balance)
    for key in all_band_keys:
        t_val = target.band_balance.get(key, 0.0)
        c_val = cand.band_balance.get(key, 0.0)
        bb[key] = MetricDelta(target=t_val, candidate=c_val, delta=abs(t_val - c_val))

    # Per-band decay deltas
    bd: dict[str, MetricDelta] = {}
    all_decay_keys = set(target.band_decay_ms) | set(cand.band_decay_ms)
    for key in all_decay_keys:
        t_val = target.band_decay_ms.get(key, 0.0)
        c_val = cand.band_decay_ms.get(key, 0.0)
        bd[key] = MetricDelta(target=t_val, candidate=c_val, delta=abs(t_val - c_val))

    return Scorecard(
        percussive_ratio=perc,
        centroid_hz=cent,
        band_balance=bb,
        onset_count=onsets,
        onset_density=density,
        median_ioi_s=ioi,
        band_decay_ms=bd,
        _weights=w,
    )
