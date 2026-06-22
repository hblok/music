"""soundmatch.core.candidate — the ONE render path (DRY).

``render_phrase`` renders a Phrase through one or more instrument layers,
producing an AudioBuffer.  This is the single shared render path used by
candidate, scorecard, and variants — never re-implemented.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from forge.core.buffer import AudioBuffer
from forge.core.rng import RngContext
from soundmatch.core.phrase import Phrase


def render_phrase(
    phrase: Phrase,
    instrument_id: str,
    params: dict[str, Any],
    layers: list[tuple[str, dict[str, Any]]],
    seed: int,
    sr: int = 44100,
) -> AudioBuffer:
    """Render a phrase through one or more instrument layers, summed.

    Parameters
    ----------
    phrase        : The Phrase (bpm, notes, length) to render.
    instrument_id : Primary instrument registry key.
    params        : Primary instrument parameters.
    layers        : Additional ``(instrument_id, params)`` pairs summed on top.
    seed          : Master seed for deterministic rendering.
    sr            : Sample rate.

    Returns
    -------
    AudioBuffer of length ``phrase.length_s * sr``, summed across all layers.
    """
    from forge.instruments.registry import REGISTRY

    n_samples = int(phrase.length_s * sr)
    mix = np.zeros((n_samples, 2), dtype=np.float64)

    # Collect all layers: primary + extras
    all_layers = [(instrument_id, params)] + list(layers)

    root = RngContext(seed)

    for layer_idx, (inst_id, inst_params) in enumerate(all_layers):
        entry = REGISTRY.get(inst_id)
        if entry is None:
            continue

        fn = entry["fn"]
        layer_rng = root.spawn(f"layer{layer_idx}")

        # Render each note in the phrase
        for note_idx, note in enumerate(phrase.notes):
            note_rng = layer_rng.spawn(f"note{note_idx}")

            # Build per-note params
            note_params = dict(inst_params)
            # For single-note instruments, set midi and duration
            note_params["midi"] = note.midi[0] if len(note.midi) >= 1 else 60
            note_params["duration"] = phrase.length_s  # let envelope shape it
            # For phrase-level instruments, pass notes list
            if "notes" in _get_param_names(inst_id):
                note_params["notes"] = [(m, 0.3) for m in note.midi]
                note_params.pop("midi", None)
                note_params.pop("duration", None)

            try:
                buf = fn(note_params, note_rng.rng, sr=sr)
            except Exception:
                continue

            # Add at the note onset time
            start_sample = int(note.t * sr)
            n = min(len(buf.data), n_samples - start_sample)
            if n > 0 and start_sample >= 0:
                mix[start_sample:start_sample + n, 0] += buf.data[:n, 0]
                mix[start_sample:start_sample + n, 1] += buf.data[:n, 1]

    # Normalize to prevent clipping
    peak = np.max(np.abs(mix))
    if peak > 1e-12:
        mix *= 0.92 / peak

    result = AudioBuffer(n_samples, sr)
    result.data[:] = mix
    return result


def _get_param_names(instrument_id: str) -> list[str]:
    """Get parameter names for an instrument from the registry."""
    from forge.instruments.registry import REGISTRY
    entry = REGISTRY.get(instrument_id)
    if entry is None:
        return []
    return [p.name for p in entry.get("params", [])]
