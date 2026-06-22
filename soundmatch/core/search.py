"""soundmatch.core.search — coarse param search minimizing Scorecard.aggregate.

Given a target Metrics, a Phrase, and an instrument, perform a coarse grid
search over key parameters to find the starting patch that minimizes the
aggregate distance to the target.  Reuses ``render_phrase`` / ``characterize``
/ ``diff`` — never re-implemented.

Runs on a worker thread in the UI; results are returned as the best
``(instrument_id, params, layers, seed)`` tuple.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Any

from inspector.metrics import Metrics, characterize
from soundmatch.core.candidate import render_phrase
from soundmatch.core.phrase import Phrase
from soundmatch.core.scoring import Scorecard, diff


# Default coarse search grid: instrument param → list of values to try.
# This covers the most impactful params across forge instruments.
_DEFAULT_GRID: dict[str, list[Any]] = {
    "f0": [40, 55, 65, 80, 110, 150],
    "perc_decay": [0.04, 0.06, 0.08, 0.11, 0.15, 0.20],
    "drive": [0.0, 0.3, 0.6, 1.0],
    "snap_level": [0.0, 0.06, 0.12, 0.18, 0.30],
    "hp_cutoff": [60, 80, 110, 150, 200],
    "formant_mix": [0.0, 0.15, 0.25, 0.35, 0.50],
    "detune": [0.0, 0.1, 0.3, 0.5],
    "n_voices": [1, 3, 5, 8],
    "tone": [0.2, 0.4, 0.6, 0.8, 1.0],
    "decay": [0.05, 0.10, 0.20, 0.40, 0.80],
}


@dataclass
class SearchResult:
    """Result of a coarse param search.

    Attributes:
        best_params   : Best parameter dict found.
        best_layers   : Best layer list found (same as input layers).
        best_score    : Aggregate distance of the best patch.
        best_scorecard: Full Scorecard of the best patch.
        iterations    : Total number of patches evaluated.
        instrument_id : Instrument used for the search.
        seed          : Seed used for rendering.
    """

    best_params: dict[str, Any]
    best_layers: list[tuple[str, dict[str, Any]]]
    best_score: float
    best_scorecard: Scorecard
    iterations: int
    instrument_id: str
    seed: int


def coarse_search(
    target: Metrics,
    phrase: Phrase,
    instrument_id: str,
    base_params: dict[str, Any],
    layers: list[tuple[str, dict[str, Any]]],
    seed: int,
    *,
    sr: int = 44100,
    grid: dict[str, list[Any]] | None = None,
    max_iterations: int = 200,
    weights: dict[str, float] | None = None,
) -> SearchResult:
    """Perform a coarse grid search over key parameters.

    Parameters
    ----------
    target        : Target Metrics to match.
    phrase        : Phrase to render for each candidate.
    instrument_id : Primary instrument registry key.
    base_params   : Starting parameter dict (provides defaults for params
                    not in the search grid).
    layers        : Additional ``(instrument_id, params)`` layers.
    seed          : Master seed for deterministic rendering.
    sr            : Sample rate.
    grid          : Override the default search grid (param → values).
    max_iterations: Maximum number of candidates to evaluate.
    weights       : Optional scoring weights.

    Returns
    -------
    SearchResult with the best parameter set found.
    """
    search_grid = grid if grid is not None else _DEFAULT_GRID

    # Filter grid to only params that exist in base_params or are
    # common across forge instruments
    active_params: list[str] = []
    param_values: list[list[Any]] = []
    for pname, values in search_grid.items():
        # Only include params that the instrument actually uses
        if pname in base_params or _param_exists_in_registry(instrument_id, pname):
            active_params.append(pname)
            param_values.append(values[:4])  # cap at 4 values per param

    if not active_params:
        # No searchable params — evaluate the base patch and return
        return _evaluate_single(
            target, phrase, instrument_id, base_params, layers,
            seed, sr, weights,
        )

    # Generate all combinations (Cartesian product)
    combos = list(itertools.product(*param_values))

    # Cap iterations
    if len(combos) > max_iterations:
        # Take a stratified sample: evenly spaced indices
        step = len(combos) / max_iterations
        indices = [int(i * step) for i in range(max_iterations)]
        combos = [combos[i] for i in indices]

    best_params = dict(base_params)
    best_score = float("inf")
    best_scorecard = None
    iterations = 0

    for combo in combos:
        candidate_params = dict(base_params)
        for pname, value in zip(active_params, combo):
            candidate_params[pname] = value

        try:
            buf = render_phrase(phrase, instrument_id, candidate_params, layers, seed, sr)
            y = buf.data.mean(axis=1) if buf.data.ndim == 2 else buf.data
            y = __import__("numpy").ascontiguousarray(y)
            cand_m = characterize(y, sr)
            sc = diff(target, cand_m, weights=weights)
            agg = sc.aggregate()
            iterations += 1

            if agg < best_score:
                best_score = agg
                best_params = dict(candidate_params)
                best_scorecard = sc
        except Exception:
            continue

    if best_scorecard is None:
        return _evaluate_single(
            target, phrase, instrument_id, base_params, layers,
            seed, sr, weights,
        )

    return SearchResult(
        best_params=best_params,
        best_layers=list(layers),
        best_score=best_score,
        best_scorecard=best_scorecard,
        iterations=iterations,
        instrument_id=instrument_id,
        seed=seed,
    )


def _evaluate_single(
    target: Metrics,
    phrase: Phrase,
    instrument_id: str,
    params: dict[str, Any],
    layers: list[tuple[str, dict[str, Any]]],
    seed: int,
    sr: int,
    weights: dict[str, float] | None,
) -> SearchResult:
    """Evaluate a single parameter set and return it as a SearchResult."""
    buf = render_phrase(phrase, instrument_id, params, layers, seed, sr)
    y = buf.data.mean(axis=1) if buf.data.ndim == 2 else buf.data
    cand_m = characterize(y, sr)
    sc = diff(target, cand_m, weights=weights)
    return SearchResult(
        best_params=dict(params),
        best_layers=list(layers),
        best_score=sc.aggregate(),
        best_scorecard=sc,
        iterations=1,
        instrument_id=instrument_id,
        seed=seed,
    )


def _param_exists_in_registry(instrument_id: str, param_name: str) -> bool:
    """Check if a param name exists in the instrument's schema."""
    from forge.instruments.registry import REGISTRY
    entry = REGISTRY.get(instrument_id)
    if entry is None:
        return False
    param_names = [p.name for p in entry.get("params", [])]
    return param_name in param_names
