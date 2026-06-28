"""soundmatch.core.resynth — spectral analysis for resynthesis.

Measures a sound and builds a :class:`~forge.core.resynth.ResynthModel`.
Rendering, saving, and loading are in ``forge.core.resynth`` (no librosa
required there).

Two-component model
-------------------
Additive (tonal)
    Sum of sinusoids at harmonic frequencies, each carrying its own
    per-frame amplitude envelope extracted from the STFT.

Noise (percussive / textural)
    Spectrally-coloured noise shaped by the full-spectrum median envelope
    (not just the HPSS residual — this preserves high-frequency content),
    gated by the RMS amplitude envelope.

``tonal_gain`` and ``noise_gain`` control the mix; both may be non-zero
for hybrid sounds (plucked strings, breath tones, …).
"""

from __future__ import annotations

import logging

import numpy as np

from forge.core.resynth import ResynthModel, load_model, render, save_model  # noqa: F401

log = logging.getLogger(__name__)

_MAX_PARTIAL_HZ = 20000.0   # capture harmonics up to ~20 kHz
_HOP_LENGTH = 256
_N_FFT = 2048
_HNR_TONAL_THRESHOLD = 6.0  # dB — above this → treat as tonal


# ── Analysis ─────────────────────────────────────────────────────────────────

def analyze(y: np.ndarray, sr: int, *, source_name: str = "") -> ResynthModel:
    """Analyse *y* and return a :class:`~forge.core.resynth.ResynthModel`.

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

    # ── Noise spectral shape from full spectrum ───────────────────────
    # Use D (full signal) so high-frequency harmonics and energy above the
    # additive model's partial range are preserved in the noise colour.
    spectral_shape = np.median(np.abs(D), axis=1)   # (n_bins,)
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
        freq_ceil = min(_MAX_PARTIAL_HZ, float(freqs[-1]))
        n_harm = max(1, int(freq_ceil / f0_est) - 1)
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
