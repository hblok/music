"""soundmatch.core.search — coarse param search + cross-instrument ranking.

Two public functions:

``coarse_search``
    Given a target Metrics, Phrase, and a specific instrument, grid-search
    over key params and return the best-scoring patch.

``instrument_search``
    Try every registered instrument with a quick coarse_search, rank by
    aggregate distance, and return the sorted list.  Use this to discover
    which instrument family best matches a target sound.
"""

from __future__ import annotations

import itertools
import logging
from dataclasses import dataclass
from typing import Any, Callable

import numpy as np

log = logging.getLogger(__name__)

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
    on_progress: Callable[[int, int], None] | None = None,
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

    log.info("coarse_search: %d combos, instrument=%s, params=%s",
             len(combos), instrument_id, list(active_params))

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
            y = np.ascontiguousarray(y)
            cand_m = characterize(y, sr)
            sc = diff(target, cand_m, weights=weights)
            agg = sc.aggregate()
            iterations += 1

            if agg < best_score:
                best_score = agg
                best_params = dict(candidate_params)
                best_scorecard = sc
        except Exception as exc:
            log.debug("search iteration failed: %s", exc)
        finally:
            if on_progress is not None:
                on_progress(iterations, len(combos))

    if best_scorecard is None:
        return _evaluate_single(
            target, phrase, instrument_id, base_params, layers,
            seed, sr, weights,
        )

    log.debug("coarse_search done: %d iterations, best=%.4f", iterations, best_score)
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


# ── Cross-instrument search ───────────────────────────────────────────────────


@dataclass
class InstrumentRanking:
    """One entry in an instrument_search result.

    Attributes:
        instrument_id : Registry key.
        family        : Instrument family (percussion, voice, …).
        score         : Aggregate distance from the target (lower = better).
        params        : Best parameter dict found for this instrument.
        seed          : Seed used during evaluation.
    """

    instrument_id: str
    family: str
    score: float
    params: dict[str, Any]
    seed: int


def instrument_search(
    target: Metrics,
    phrase: Phrase,
    seed: int,
    *,
    max_per_instrument: int = 20,
    sr: int = 44100,
    on_result: Callable[[InstrumentRanking], None] | None = None,
    on_progress: Callable[[int, int], None] | None = None,
) -> list[InstrumentRanking]:
    """Try every registered instrument and rank by how well it matches *target*.

    For each instrument a quick ``coarse_search`` (capped at
    *max_per_instrument* iterations) finds the best-scoring parameter set.
    Results are returned sorted by score (ascending — lowest = best match).

    Parameters
    ----------
    target               : Target Metrics to match against.
    phrase               : Phrase to render for each candidate.
    seed                 : Master seed for deterministic rendering.
    max_per_instrument   : Maximum coarse_search iterations per instrument.
    sr                   : Sample rate.
    on_result            : Called once per instrument as results arrive.
                           Useful for streaming results to a UI.
    on_progress          : Called as ``(done, total)`` once per instrument.

    Returns
    -------
    List of :class:`InstrumentRanking` sorted by score (best first).
    """
    from forge.instruments.registry import REGISTRY

    instrument_ids = list(REGISTRY.keys())
    total = len(instrument_ids)
    rankings: list[InstrumentRanking] = []

    log.info("instrument_search: evaluating %d instruments (max %d iters each)",
             total, max_per_instrument)

    for i, iid in enumerate(instrument_ids):
        entry = REGISTRY[iid]
        family = entry.get("family", "?")
        defaults = {s.name: s.default for s in entry.get("params", [])}
        try:
            r = coarse_search(
                target, phrase, iid, defaults, [], seed,
                sr=sr, max_iterations=max_per_instrument,
            )
            ranking = InstrumentRanking(
                instrument_id=iid,
                family=family,
                score=r.best_score,
                params=r.best_params,
                seed=seed,
            )
            rankings.append(ranking)
            log.debug("instrument_search: %s score=%.4f", iid, r.best_score)
            if on_result is not None:
                on_result(ranking)
        except Exception as exc:
            log.debug("instrument_search: %s failed: %s", iid, exc)
        finally:
            if on_progress is not None:
                on_progress(i + 1, total)

    rankings.sort(key=lambda r: r.score)
    log.info("instrument_search done: best=%s score=%.4f",
             rankings[0].instrument_id if rankings else "—",
             rankings[0].score if rankings else float("inf"))
    return rankings
