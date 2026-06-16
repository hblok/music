"""forge.core.mastering — final mix processing and WAV output.

Peak normalize → soft limiter → optional shelf EQ → fade → write 16-bit WAV.
Keeps the project constraint: output via stdlib ``wave``, no external audio
libraries.
"""

from __future__ import annotations

import wave
from pathlib import Path

import numpy as np
from scipy import signal

from forge.core.buffer import AudioBuffer
from forge.core.dsp import fade


def soft_limiter(x: np.ndarray, threshold: float = 0.95) -> np.ndarray:
    """Tanh soft-clipper above *threshold*.

    Samples below *threshold* are unchanged; above it, a tanh smoothly limits
    to 1.0.  Applied per-channel; does not alter the input array.
    """
    y = x.copy()
    over = np.abs(y) > threshold
    sign = np.sign(y[over])
    exc = (np.abs(y[over]) - threshold) / (1.0 - threshold + 1e-12)
    y[over] = sign * (threshold + (1.0 - threshold) * np.tanh(exc))
    return y


def high_shelf(
    x: np.ndarray,
    freq: float,
    gain_db: float,
    q: float = 0.707,
    sr: int = 44100,
) -> np.ndarray:
    """Second-order high-shelf filter (positive gain_db → boost)."""
    b, a = signal.bilinear_transform_hs(freq, gain_db, q, sr) if hasattr(signal, "bilinear_transform_hs") else _hs_coeffs(freq, gain_db, q, sr)
    return signal.lfilter(b, a, x)


def low_shelf(
    x: np.ndarray,
    freq: float,
    gain_db: float,
    q: float = 0.707,
    sr: int = 44100,
) -> np.ndarray:
    """Second-order low-shelf filter."""
    b, a = _ls_coeffs(freq, gain_db, q, sr)
    return signal.lfilter(b, a, x)


def _hs_coeffs(
    freq: float, gain_db: float, q: float, sr: int
) -> tuple[np.ndarray, np.ndarray]:
    A = 10.0 ** (gain_db / 40.0)
    w0 = 2.0 * np.pi * freq / sr
    alpha = np.sin(w0) / (2.0 * q)
    cw = np.cos(w0)
    b0 = A * ((A + 1) + (A - 1) * cw + 2.0 * np.sqrt(A) * alpha)
    b1 = -2.0 * A * ((A - 1) + (A + 1) * cw)
    b2 = A * ((A + 1) + (A - 1) * cw - 2.0 * np.sqrt(A) * alpha)
    a0 = (A + 1) - (A - 1) * cw + 2.0 * np.sqrt(A) * alpha
    a1 = 2.0 * ((A - 1) - (A + 1) * cw)
    a2 = (A + 1) - (A - 1) * cw - 2.0 * np.sqrt(A) * alpha
    return np.array([b0, b1, b2]) / a0, np.array([1.0, a1 / a0, a2 / a0])


def _ls_coeffs(
    freq: float, gain_db: float, q: float, sr: int
) -> tuple[np.ndarray, np.ndarray]:
    A = 10.0 ** (gain_db / 40.0)
    w0 = 2.0 * np.pi * freq / sr
    alpha = np.sin(w0) / (2.0 * q)
    cw = np.cos(w0)
    b0 = A * ((A + 1) - (A - 1) * cw + 2.0 * np.sqrt(A) * alpha)
    b1 = 2.0 * A * ((A - 1) - (A + 1) * cw)
    b2 = A * ((A + 1) - (A - 1) * cw - 2.0 * np.sqrt(A) * alpha)
    a0 = (A + 1) + (A - 1) * cw + 2.0 * np.sqrt(A) * alpha
    a1 = -2.0 * ((A - 1) + (A + 1) * cw)
    a2 = (A + 1) + (A - 1) * cw - 2.0 * np.sqrt(A) * alpha
    return np.array([b0, b1, b2]) / a0, np.array([1.0, a1 / a0, a2 / a0])


def master(
    buf: AudioBuffer,
    target: float = 0.85,
    fade_in_s: float = 0.0,
    fade_out_s: float = 0.0,
    limit: bool = True,
    limit_threshold: float = 0.95,
) -> AudioBuffer:
    """Apply the mastering chain to an AudioBuffer and return a new buffer.

    Steps:
      1. Optional fade in/out.
      2. Peak normalize to *target*.
      3. Optional soft limiter above *limit_threshold*.

    Does not modify *buf* in place.
    """
    out = buf.copy()
    if fade_in_s > 0.0 or fade_out_s > 0.0:
        fade(out.L, fade_in_s, fade_out_s, out.sr)
        fade(out.R, fade_in_s, fade_out_s, out.sr)
    out.normalize(target)
    if limit:
        out.data[:, 0] = soft_limiter(out.L, limit_threshold)
        out.data[:, 1] = soft_limiter(out.R, limit_threshold)
    return out


def write_wav(buf: AudioBuffer, path: Path, normalize: bool = True, target: float = 0.85) -> None:
    """Write an AudioBuffer to a 16-bit stereo WAV file via stdlib ``wave``.

    Args:
        buf:       Source buffer.
        path:      Output path (created including missing parents).
        normalize: Peak-normalize to *target* before writing.
        target:    Normalization target amplitude (default 0.85).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = buf.data.copy()
    if normalize:
        pk = np.max(np.abs(data))
        if pk > 1e-12:
            data *= target / pk

    pcm = (data * 32767.0).clip(-32767, 32767).astype(np.int16)

    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(buf.sr)
        wf.writeframes(pcm.tobytes())
