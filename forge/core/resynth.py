"""forge.core.resynth — ResynthModel: data model, rendering, and persistence.

The analysis counterpart (``analyze()``) lives in ``soundmatch.core.resynth``
because it requires librosa.  Everything here is pure numpy + stdlib so forge
can use it without depending on soundmatch.

Two-component model
-------------------
Additive (tonal)
    Sum of sinusoids at harmonic frequencies, each with a per-frame amplitude
    envelope extracted from the STFT.

Noise (percussive / textural)
    Spectrally-coloured noise shaped by the measured full-spectrum envelope,
    gated by the RMS amplitude envelope.
"""

from __future__ import annotations

import base64
import json
import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np

log = logging.getLogger(__name__)


@dataclass
class ResynthModel:
    """Compact spectral model for resynthesis.

    All list fields containing float arrays are stored as plain Python lists
    so the object is trivially JSON-serialisable via ``save_model``.
    """

    approach: str           # "additive" | "noise" | "hybrid"
    sr: int
    duration_s: float
    source_f0: float        # Hz; 0.0 = unpitched / could not detect
    env_sr: float           # frames per second of all envelope lists
    hnr_db: float

    # Additive component: (freq_hz, amp_envelope_per_frame)
    partials: list[tuple[float, list[float]]]

    # Noise component
    noise_amp_env: list[float]         # RMS envelope sampled at env_sr
    noise_spectral_shape: list[float]  # normalised |FFT| shape, DC→Nyquist

    # Mix
    tonal_gain: float   # 0–1
    noise_gain: float   # 0–1


# ── Rendering ────────────────────────────────────────────────────────────────

def render(
    model: ResynthModel,
    *,
    target_f0: float | None = None,
    duration_s: float | None = None,
    sr: int | None = None,
    seed: int = 0,
) -> np.ndarray:
    """Render *model* to a float32 audio array.

    Parameters
    ----------
    target_f0  : Transpose to this frequency (Hz).  Scales all harmonic
                 frequencies by ``target_f0 / model.source_f0``.  Ignored
                 for unpitched sounds (``model.source_f0 == 0``).
    duration_s : Output duration in seconds; defaults to ``model.duration_s``.
    sr         : Output sample rate; defaults to ``model.sr``.
    seed       : RNG seed for the noise component (reproducible output).
    """
    out_sr = sr if sr is not None else model.sr
    dur = duration_s if duration_s is not None else model.duration_s
    n = int(dur * out_sr)
    t = np.arange(n, dtype=np.float64) / out_sr

    f0_ratio = 1.0
    if target_f0 is not None and model.source_f0 > 0:
        f0_ratio = target_f0 / model.source_f0

    out = np.zeros(n, dtype=np.float64)
    xs = np.linspace(0.0, 1.0, n)

    # ── Additive component ────────────────────────────────────────────
    if model.tonal_gain > 0 and model.partials:
        for freq_hz, amp_env_frames in model.partials:
            freq_scaled = freq_hz * f0_ratio
            if freq_scaled >= out_sr / 2.0:
                continue
            amp = np.interp(
                xs,
                np.linspace(0.0, 1.0, len(amp_env_frames)),
                np.array(amp_env_frames, dtype=np.float64),
            )
            out += model.tonal_gain * amp * np.sin(2.0 * np.pi * freq_scaled * t)

    # ── Noise component ───────────────────────────────────────────────
    if model.noise_gain > 0:
        rng = np.random.default_rng(seed)
        white = rng.standard_normal(n)

        shape = np.array(model.noise_spectral_shape, dtype=np.float64)
        n_bins = n // 2 + 1
        shape_interp = np.interp(
            np.arange(n_bins, dtype=np.float64),
            np.linspace(0.0, float(n_bins - 1), len(shape)),
            shape,
        )
        fft_white = np.fft.rfft(white)
        fft_white *= shape_interp
        colored = np.fft.irfft(fft_white, n=n)

        amp = np.interp(
            xs,
            np.linspace(0.0, 1.0, len(model.noise_amp_env)),
            np.array(model.noise_amp_env, dtype=np.float64),
        )
        out += model.noise_gain * colored * amp

    # ── Normalise to −3 dBFS ──────────────────────────────────────────
    peak = float(np.max(np.abs(out)))
    if peak > 1e-8:
        out *= (10.0 ** (-3.0 / 20.0)) / peak

    return out.astype(np.float32)


# ── Persistence ──────────────────────────────────────────────────────────────

def save_model(model: ResynthModel, path: Path) -> None:
    """Serialise *model* to a JSON file.  Arrays are base64-encoded float32."""

    def _enc(lst: list[float]) -> str:
        return base64.b64encode(
            np.array(lst, dtype=np.float32).tobytes()
        ).decode()

    d = {
        "approach": model.approach,
        "sr": model.sr,
        "duration_s": model.duration_s,
        "source_f0": model.source_f0,
        "env_sr": model.env_sr,
        "hnr_db": model.hnr_db,
        "tonal_gain": model.tonal_gain,
        "noise_gain": model.noise_gain,
        "partials": [[freq, _enc(env)] for freq, env in model.partials],
        "noise_amp_env": _enc(model.noise_amp_env),
        "noise_spectral_shape": _enc(model.noise_spectral_shape),
    }
    path.write_text(json.dumps(d, indent=2))
    log.info("resynth model saved: %s", path)


def load_model(path: Path) -> ResynthModel:
    """Load a :class:`ResynthModel` previously saved with :func:`save_model`."""

    def _dec(s: str) -> list[float]:
        return np.frombuffer(base64.b64decode(s), dtype=np.float32).tolist()

    d = json.loads(path.read_text())
    return ResynthModel(
        approach=d["approach"],
        sr=d["sr"],
        duration_s=d["duration_s"],
        source_f0=d["source_f0"],
        env_sr=d["env_sr"],
        hnr_db=d.get("hnr_db", 0.0),
        tonal_gain=d["tonal_gain"],
        noise_gain=d["noise_gain"],
        partials=[(freq, _dec(env)) for freq, env in d["partials"]],
        noise_amp_env=_dec(d["noise_amp_env"]),
        noise_spectral_shape=_dec(d["noise_spectral_shape"]),
    )
