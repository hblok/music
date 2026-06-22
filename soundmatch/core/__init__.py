"""soundmatch.core — headless core; NO Qt imports."""
from __future__ import annotations

from soundmatch.core.target import Target
from soundmatch.core.phrase import Note, Phrase, seed_from_metrics
from soundmatch.core.candidate import render_phrase
from soundmatch.core.scoring import MetricDelta, Scorecard, diff
from soundmatch.core.variants import VariantSpec, VariantResult, sweep, render_and_score
from soundmatch.core.project import MatchProject

__all__ = [
    "Target",
    "Note",
    "Phrase",
    "seed_from_metrics",
    "render_phrase",
    "MetricDelta",
    "Scorecard",
    "diff",
    "VariantSpec",
    "VariantResult",
    "sweep",
    "render_and_score",
    "MatchProject",
]
