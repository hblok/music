"""soundmatch.core.resynth — spectral resynthesis from analysis.

Converts a sound into a compact spectral model and resynthesises it from
scratch.  The output shares only the *measured* spectral/temporal structure
with the input — no original bytes are stored or played back.

Two-component model
-------------------
Additive (tonal)
    Sum of sinusoids at harmonic frequencies, each carrying its own
    per-frame amplitude envelope extracted from the STFT.

Noise (percussive / textural)
    Spectrally-coloured noise (shaped by the measured residual spectral
    envelope) gated by the RMS amplitude envelope.

``tonal_gain`` and ``noise_gain`` control the mix; both may be non-zero
for hybrid sounds (plucked strings, breath tones, …).
"""

from __future__ import annotations

import base64
import json
import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np

log = logging.getLogger(__name__)

_MAX_PARTIALS = 16
_HOP_LENGTH = 256
_N_FFT = 2048
_HNR_TONAL_THRESHOLD = 6.0  # dB — above this → treat as tonal


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


# ── Analysis ─────────────────────────────────────────────────────────────────

def analyze(y: np.ndarray, sr: int, *, source_name: str = "") -> ResynthModel:
    """Analyse *y* and return a :class:`ResynthModel`.

    Parameters
    ----------
    y           : Mono float audio array.
    sr          : Sample rate of *y*.
    source_name : Used only for log messages.
    """
    import librosa

    y = np.asarray(y, dtype=float)
    duration_s = len(y) / sr

    # ── STFT ─────────────────────────────────────────────────────────
    D = librosa.stft(y, n_fft=_N_FFT, hop_length=_HOP_LENGTH)
    mag = np.abs(D)                                    # (n_bins, n_frames)
    freqs = librosa.fft_frequencies(sr=sr, n_fft=_N_FFT)
    env_sr = float(sr) / _HOP_LENGTH

    # ── F0 estimation via pyin ────────────────────────────────────────
    f0_est = 0.0
    try:
        f0_seq, _, _ = librosa.pyin(
            y,
            fmin=librosa.note_to_hz("C2"),
            fmax=librosa.note_to_hz("C7"),
            sr=sr,
            hop_length=_HOP_LENGTH,
        )
        voiced = f0_seq[~np.isnan(f0_seq)]
        if len(voiced) > 3:
            f0_est = float(np.median(voiced))
    except Exception as exc:
        log.debug("resynth pyin failed: %s", exc)

    # ── HNR to decide approach ────────────────────────────────────────
    is_tonal = False
    hnr_db = 0.0
    if f0_est > 50:
        total_power = float(np.sum(mag ** 2)) + 1e-20
        harm_power = 0.0
        n_check = min(8, max(1, int(freqs[-1] / f0_est) - 1))
        for k in range(1, n_check + 1):
            bidx = int(np.argmin(np.abs(freqs - k * f0_est)))
            lo = max(0, bidx - 2)
            hi = min(mag.shape[0], bidx + 3)
            harm_power += float(np.sum(mag[lo:hi, :] ** 2))
        noise_power = max(total_power - harm_power, 1e-20)
        hnr_db = 10.0 * np.log10(max(harm_power, 1e-20) / noise_power)
        is_tonal = hnr_db >= _HNR_TONAL_THRESHOLD

    # ── Noise spectral shape from HPSS residual ───────────────────────
    try:
        y_harm, _ = librosa.effects.hpss(y)
        y_noise = (y - y_harm) if is_tonal else y
    except Exception:
        y_noise = y

    D_noise = librosa.stft(y_noise, n_fft=_N_FFT, hop_length=_HOP_LENGTH)
    mag_noise = np.abs(D_noise)
    spectral_shape = np.median(mag_noise, axis=1)   # (n_bins,)
    peak_shape = spectral_shape.max()
    if peak_shape > 1e-10:
        spectral_shape = spectral_shape / peak_shape

    # ── RMS amplitude envelope ────────────────────────────────────────
    rms = librosa.feature.rms(
        y=y, frame_length=_HOP_LENGTH * 2, hop_length=_HOP_LENGTH,
    )[0]
    noise_amp_env = np.maximum(rms, 0.0).tolist()

    # ── Harmonic amplitude envelopes ──────────────────────────────────
    partials: list[tuple[float, list[float]]] = []
    if is_tonal and f0_est > 0:
        n_harm = min(_MAX_PARTIALS, max(1, int(freqs[-1] / f0_est) - 1))
        for k in range(1, n_harm + 1):
            target_hz = k * f0_est
            bidx = int(np.argmin(np.abs(freqs - target_hz)))
            lo = max(0, bidx - 2)
            hi = min(mag.shape[0], bidx + 3)
            amp_env = mag[lo:hi, :].max(axis=0)   # (n_frames,)
            if float(amp_env.max()) < 1e-10:
                continue
            partials.append((target_hz, amp_env.tolist()))

    # ── Mix gains ─────────────────────────────────────────────────────
    if is_tonal:
        tonal_gain = float(np.clip(
            (hnr_db - _HNR_TONAL_THRESHOLD) / 20.0 + 0.6, 0.3, 1.0
        ))
    else:
        tonal_gain = 0.0
    noise_gain = max(0.0, 1.0 - tonal_gain * 0.5)

    if tonal_gain >= 0.7:
        approach = "additive"
    elif tonal_gain <= 0.2:
        approach = "noise"
    else:
        approach = "hybrid"

    log.info(
        "resynth analyze: %s — f0=%.1f Hz, HNR=%.1f dB, "
        "approach=%s, partials=%d",
        source_name or "?", f0_est, hnr_db, approach, len(partials),
    )

    return ResynthModel(
        approach=approach,
        sr=sr,
        duration_s=duration_s,
        source_f0=f0_est,
        env_sr=env_sr,
        hnr_db=hnr_db,
        partials=partials,
        noise_amp_env=noise_amp_env,
        noise_spectral_shape=spectral_shape.tolist(),
        tonal_gain=tonal_gain,
        noise_gain=noise_gain,
    )


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
