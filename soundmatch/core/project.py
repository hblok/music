"""soundmatch.core.project — MatchProject dataclass; save/load JSON via pathlib.

A MatchProject captures the full state of a sound-matching session: the
reference audio, selection, stem, target metrics, phrase, instrument patch,
layers, seed, variant specs, and the best score.  Save/load is JSON via
``pathlib.Path.write_text`` / ``read_text``.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger(__name__)
from typing import Any, Optional

from inspector.metrics import Metrics
from soundmatch.core.phrase import Phrase
from soundmatch.core.scoring import Scorecard
from soundmatch.core.variants import VariantResult, VariantSpec


def _file_sha256(p: Path) -> str:
    """SHA-256 hex digest of a file (first 1 MB only for speed)."""
    h = hashlib.sha256()
    with open(p, "rb") as f:
        chunk = f.read(1 << 20)
        h.update(chunk)
    return h.hexdigest()[:16]


@dataclass
class MatchProject:
    """Full state of a sound-matching session.

    Attributes:
        reference_path : Path to the source audio file.
        reference_sha  : Short SHA-256 of the file (for integrity check).
        start_s        : Selection start in seconds.
        end_s          : Selection end in seconds.
        stem           : Stem name (e.g. ``"other"``).
        target_metrics : Measured Metrics of the target.
        phrase         : The Phrase used for candidate rendering.
        instrument_id  : Primary instrument registry key.
        params         : Primary instrument parameters.
        layers         : Additional ``(instrument_id, params)`` pairs.
        seed           : Master seed for deterministic rendering.
        variant_specs  : List of VariantSpecs for the variant grid.
        best_variant   : Best VariantResult (if any).
    """

    reference_path: Path = Path(".")
    reference_sha: str = ""
    start_s: float = 0.0
    end_s: float = 10.0
    stem: str = "other"
    target_metrics: Optional[Metrics] = None
    phrase: Optional[Phrase] = None
    instrument_id: str = ""
    params: dict[str, Any] = field(default_factory=dict)
    layers: list[tuple[str, dict[str, Any]]] = field(default_factory=list)
    seed: int = 42
    variant_specs: list[VariantSpec] = field(default_factory=list)
    best_variant: Optional[VariantResult] = None
    stems_dir: Optional[Path] = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict for JSON save."""
        return {
            "reference_path": str(self.reference_path),
            "reference_sha": self.reference_sha,
            "start_s": self.start_s,
            "end_s": self.end_s,
            "stem": self.stem,
            "target_metrics": self.target_metrics.to_dict() if self.target_metrics else None,
            "phrase": self.phrase.to_dict() if self.phrase else None,
            "instrument_id": self.instrument_id,
            "params": dict(self.params),
            "layers": [{"instrument_id": iid, "params": dict(p)} for iid, p in self.layers],
            "seed": self.seed,
            "variant_specs": [s.to_dict() for s in self.variant_specs],
            "best_variant": self.best_variant.to_dict() if self.best_variant else None,
            "stems_dir": str(self.stems_dir) if self.stems_dir else None,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> MatchProject:
        """Deserialize from a plain dict (project load)."""
        target_metrics = Metrics.from_dict(d["target_metrics"]) if d.get("target_metrics") else None
        phrase = Phrase.from_dict(d["phrase"]) if d.get("phrase") else None
        variant_specs = [VariantSpec.from_dict(s) for s in d.get("variant_specs", [])]
        best_variant = VariantResult.from_dict(d["best_variant"]) if d.get("best_variant") else None

        layers = []
        for layer_d in d.get("layers", []):
            layers.append((layer_d["instrument_id"], dict(layer_d["params"])))

        return cls(
            reference_path=Path(d.get("reference_path", ".")),
            reference_sha=d.get("reference_sha", ""),
            start_s=d.get("start_s", 0.0),
            end_s=d.get("end_s", 10.0),
            stem=d.get("stem", "other"),
            target_metrics=target_metrics,
            phrase=phrase,
            instrument_id=d.get("instrument_id", ""),
            params=dict(d.get("params", {})),
            layers=layers,
            seed=d.get("seed", 42),
            variant_specs=variant_specs,
            best_variant=best_variant,
            stems_dir=Path(d["stems_dir"]) if d.get("stems_dir") else None,
        )

    def save(self, p: Path) -> None:
        """Save project to a JSON file via pathlib.

        Parameters
        ----------
        p : Output path (typically ``*.smatch``).
        """
        data = self.to_dict()
        text = json.dumps(data, indent=2, ensure_ascii=False)
        p.write_text(text, encoding="utf-8")
        log.info("project saved: %s", p)

    @classmethod
    def load(cls, p: Path) -> MatchProject:
        """Load project from a JSON file via pathlib.

        Parameters
        ----------
        p : Input path (typically ``*.smatch``).

        Returns
        -------
        MatchProject with all fields restored.
        """
        text = p.read_text(encoding="utf-8")
        data = json.loads(text)
        proj = cls.from_dict(data)
        log.info("project loaded: %s", p)
        return proj

    def update_sha(self) -> None:
        """Re-compute and store the reference file SHA-256 if the file exists."""
        if self.reference_path.exists():
            self.reference_sha = _file_sha256(self.reference_path)
