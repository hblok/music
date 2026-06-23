"""forge.instruments.resynth_instrument — ResynthModel playback instrument.

Loads a saved ResynthModel JSON (produced by soundmatch's Resynthesize Region
dialog) and renders it as a forge note instrument.  This lets any resynth
export be used directly in a track script or the forge tracker.

Usage in a track script::

    from pathlib import Path
    from forge.instruments.resynth_instrument import make_resynth_note

    params = {
        "model_path": str(Path("my_stem.json")),
        "midi": 60,          # transpose to C4 (ignored if model has no f0)
        "duration": 0.0,     # 0 → use model's own duration
        "tonal_gain": -1.0,  # −1 → use model's stored value
        "noise_gain": -1.0,  # −1 → use model's stored value
    }
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

from forge.core.buffer import AudioBuffer
from forge.core.dsp import midi_to_hz
from forge.core.resynth import load_model, render
from forge.instruments.base import ParamSchema

log = logging.getLogger(__name__)

RESYNTH_NOTE_PARAMS = [
    ParamSchema("model_path", "choice", "",   label="Model JSON path"),
    ParamSchema("midi",       "int",    60,   lo=21,  hi=108, label="MIDI note"),
    ParamSchema("duration",   "float",  0.0,  lo=0.0, hi=30.0, unit="s",
                label="Duration (0=model)"),
    ParamSchema("tonal_gain", "float", -1.0,  lo=-1.0, hi=1.0,
                label="Tonal gain (−1=model)"),
    ParamSchema("noise_gain", "float", -1.0,  lo=-1.0, hi=1.0,
                label="Noise gain (−1=model)"),
]

# Module-level cache so repeated renders of the same path don't re-parse JSON.
_model_cache: dict[str, object] = {}


def make_resynth_note(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
    """Render a ResynthModel JSON as a pitched note.

    *model_path* is the only required param; all others fall back to the
    stored model values when left at their defaults (−1 / 0).
    """
    sr = ctx.get("sr", 44100)
    path_str = str(params.get("model_path", ""))
    if not path_str:
        log.warning("resynth_note: no model_path set, returning silence")
        return AudioBuffer.from_mono(np.zeros(sr, dtype=np.float32), sr=sr)

    if path_str not in _model_cache:
        _model_cache[path_str] = load_model(Path(path_str))
    model = _model_cache[path_str]

    midi = int(params.get("midi", 60))
    target_f0 = midi_to_hz(midi) if model.source_f0 > 0 else None

    raw_dur = float(params.get("duration", 0.0))
    duration_s = raw_dur if raw_dur > 0.0 else None

    tg = float(params.get("tonal_gain", -1.0))
    ng = float(params.get("noise_gain", -1.0))

    # Override model gains only when the param departs from the sentinel −1.
    if tg >= 0.0:
        model.tonal_gain = tg
    if ng >= 0.0:
        model.noise_gain = ng

    seed = int(rng.integers(2 ** 31))
    audio = render(model, target_f0=target_f0, duration_s=duration_s, sr=sr, seed=seed)
    return AudioBuffer.from_mono(audio, sr=sr)
