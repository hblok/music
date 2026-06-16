"""forge.core.dsp — canonical DSP helpers extracted from the legacy scripts.

One function per primitive, replacing the per-script duplicates documented in
INVENTORY.md.  No audio I/O here; all functions operate on numpy arrays and
return numpy arrays.

All functions that consumed a global `rng` in the legacy scripts now take an
explicit `np.random.Generator` argument.
"""

from __future__ import annotations

import numpy as np
from scipy import signal


# ---------------------------------------------------------------- pitch

def midi_to_hz(midi: float) -> float:
    """Convert a MIDI note number to frequency in Hz.

    Standard A4=69=440 Hz tuning.
    """
    return 440.0 * 2.0 ** ((midi - 69.0) / 12.0)


# ---------------------------------------------------------------- envelopes / windows

def raised_cosine(n: int) -> np.ndarray:
    """Symmetric raised-cosine window of length *n*: 0 → 1 → 0.

    Matches the legacy ``raised_cosine(n)`` in generate_ambient.py.
    """
    return 0.5 - 0.5 * np.cos(2.0 * np.pi * np.arange(n) / n)


def fade(x: np.ndarray, fade_in: float, fade_out: float, sr: int = 44100) -> np.ndarray:
    """Apply raised-cosine fade-in and fade-out (in seconds) to *x* in place.

    Returns *x* for chaining.  The fade is a half-cosine ramp:
      in:  0 → 1 over the first ``fade_in`` seconds
      out: 1 → 0 over the last ``fade_out`` seconds
    """
    ni = int(fade_in * sr)
    no = int(fade_out * sr)
    if ni > 0:
        x[:ni] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(ni) / ni)
    if no > 0:
        x[-no:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(no) / no)
    return x


def raised_cosine_attack(n: int) -> np.ndarray:
    """Raised-cosine ramp-up of length *n*: 0 → 1.

    Produces a soft bloom-in attack (the "warmth recipe" attack shape).
    Avoids the stab quality of a linear ramp.
    """
    return 0.5 - 0.5 * np.cos(np.pi * np.arange(n) / n)


# ---------------------------------------------------------------- control signals

def slow_noise(
    duration: float,
    rate_hz: float,
    lo: float = 0.0,
    hi: float = 1.0,
    rng: np.random.Generator | None = None,
    power: float = 1.0,
    sr: int = 44100,
) -> np.ndarray:
    """Smooth stochastic control signal.

    Generates sparse normal samples at *rate_hz* events per second, applies
    a 3-point smoothing, interpolates to the full sample grid, then maps to
    [lo, hi].  Raising to *power* > 1 deepens the lulls (the ``**2.2``
    gust pattern in arrakis/spice_must_flow).

    Args:
        duration: Length of the output in seconds.
        rate_hz:  Density of control-point events per second.
        lo, hi:   Output range.
        rng:      Random generator; uses ``np.random.default_rng()`` if None.
        power:    Exponent applied after normalisation (1.0 = no shaping).
        sr:       Sample rate.

    Returns:
        Float64 array of length ``int(duration * sr)``.
    """
    if rng is None:
        rng = np.random.default_rng()
    n_samples = int(duration * sr)
    t = np.arange(n_samples) / sr

    k = max(4, int(duration * rate_hz))
    pts = rng.standard_normal(k)
    pts = np.convolve(pts, np.ones(3) / 3.0, mode="same")
    ctrl = np.interp(t, np.linspace(0.0, duration, k), pts)
    span = ctrl.max() - ctrl.min()
    ctrl = (ctrl - ctrl.min()) / (span + 1e-12)
    if power != 1.0:
        ctrl = ctrl ** power
    return lo + (hi - lo) * ctrl


def ramp(t: np.ndarray, points: list[tuple[float, float]]) -> np.ndarray:
    """Piecewise-linear ramp on time vector *t*.

    *points* is a list of (time_s, value) pairs; identical to the legacy
    ``ramp(points)`` in ambient/lost.py.
    """
    times = [p[0] for p in points]
    values = [p[1] for p in points]
    return np.interp(t, times, values)


# ---------------------------------------------------------------- filters

def lowpass(x: np.ndarray, cutoff: float, order: int = 2, sr: int = 44100) -> np.ndarray:
    """Zero-phase Butterworth low-pass filter."""
    sos = signal.butter(order, cutoff, "low", fs=sr, output="sos")
    return signal.sosfilt(sos, x)


def highpass(x: np.ndarray, cutoff: float, order: int = 2, sr: int = 44100) -> np.ndarray:
    """Zero-phase Butterworth high-pass filter."""
    sos = signal.butter(order, cutoff, "high", fs=sr, output="sos")
    return signal.sosfilt(sos, x)


def bandpass(
    x: np.ndarray,
    lo: float,
    hi: float,
    order: int = 4,
    sr: int = 44100,
) -> np.ndarray:
    """Butterworth band-pass filter matching the wind/body recipes."""
    sos = signal.butter(order, [lo, hi], "bandpass", fs=sr, output="sos")
    return signal.sosfilt(sos, x)


def fft_bandpass(x: np.ndarray, lo: float, hi: float, sr: int = 44100) -> np.ndarray:
    """FFT-domain soft bandpass (scipy-free; matches generate_ambient.py).

    Uses soft edges (linear ramps proportional to the band edges) to avoid
    ringing.  Only needed for generate_ambient.py which predates scipy in the
    project; all other scripts use the Butterworth ``bandpass`` above.
    """
    spec = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(len(x), 1.0 / sr)
    gain = (
        np.clip((freqs - lo) / (lo * 0.5 + 1e-9), 0.0, 1.0)
        * np.clip((hi - freqs) / (hi * 0.5 + 1e-9), 0.0, 1.0)
    )
    return np.fft.irfft(spec * gain, n=len(x))


# ---------------------------------------------------------------- portamento / glide

def glide_curve(
    notes: list[tuple[float | int, float]],
    n: int,
    tau: float = 0.06,
    sr: int = 44100,
) -> np.ndarray:
    """Build a portamento frequency curve (Hz) using a one-pole IIR smoother.

    *notes* is a list of ``(midi_note, duration_seconds)`` pairs placed
    sequentially from t=0.  A first-order IIR with time constant *tau* seconds
    produces the exponential glide between notes that characterises the duduk/
    bass/lead voices.

    Returns a float64 frequency array of length *n*.
    """
    f_target = np.zeros(n, dtype=np.float64)
    edge = 0.0
    for m, dur in notes:
        a = int(edge * sr)
        b = min(n, int((edge + dur) * sr))
        f_target[a:b] = midi_to_hz(m)
        edge += dur
    i_end = min(n - 1, int(edge * sr))
    f_target[i_end:] = f_target[max(0, i_end - 1)]

    alpha = 1.0 - np.exp(-1.0 / (tau * sr))
    return signal.lfilter(
        [alpha], [1.0, -(1.0 - alpha)], f_target, zi=[f_target[0] * (1.0 - alpha)]
    )[0]


# ---------------------------------------------------------------- oscillators

def sine_phase(freq_curve: np.ndarray, sr: int = 44100) -> np.ndarray:
    """Integrate a (possibly time-varying) frequency curve into a phase array.

    Use with ``np.sin(phase)`` to produce a pitch-accurate oscillator.
    """
    return 2.0 * np.pi * np.cumsum(freq_curve) / sr


def feedback_delay(
    x: np.ndarray, delay_s: float, feedback: float, taps: int = 6, sr: int = 44100
) -> np.ndarray:
    """Tapped feedback echo (matches generate_ambient.py).

    Adds *taps* copies of *x* at multiples of *delay_s* with exponentially
    decaying gains.
    """
    y = x.copy()
    d = int(delay_s * sr)
    for k in range(1, taps + 1):
        g = feedback ** k
        end = len(x) - k * d
        if end > 0:
            y[k * d :] += x[:end] * g
    return y


# ---------------------------------------------------------------- warmth helpers (trance recipe)

def warm_partials(
    phase: np.ndarray,
    n_harmonics: int = 12,
    rolloff: float = 1.3,
    sub_mix: float = 0.0,
) -> np.ndarray:
    """Rolled-off harmonic stack — the core of the trance warmth recipe.

    Computes ``sum_k sin(k·phase) / k^rolloff`` for k=1..n_harmonics and
    optionally blends in a pure sine sub (k=1) at *sub_mix* for low-mid body.

    Parameters match the warmth recipe documented in trance/CLAUDE.md:
      - rolloff 1.3 → round brass/reed (vs 1.0 = raw saw = buzzy/nasal)
      - sub_mix 0.30 → sine body under the stack
    """
    stack = np.zeros_like(phase)
    for k in range(1, n_harmonics + 1):
        stack += np.sin(k * phase) / (k ** rolloff)
    if sub_mix > 0.0:
        stack = (1.0 - sub_mix) * stack + sub_mix * np.sin(phase)
    return stack
