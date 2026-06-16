"""forge.core.reverb — convolution reverb IR construction and application.

These are the canonical implementations of ``make_reverb_ir`` and ``reverb``
that appear in virtually every legacy script.  Both use independent fresh RNG
streams (not the track's main rng) so IR shapes are stable across track
changes — the same behaviour as the legacy ``np.random.default_rng(7/11)``
calls.
"""

from __future__ import annotations

import numpy as np
from scipy import signal


def make_reverb_ir(
    seconds: float,
    decay: float,
    seed: int,
    sr: int = 44100,
    lp_cutoff: float = 4000.0,
) -> np.ndarray:
    """Build a mono convolution reverb impulse response.

    Exponentially decaying white noise, low-passed at *lp_cutoff* Hz (dark
    tail), then energy-normalised.

    Args:
        seconds:   IR length in seconds.
        decay:     Decay time constant in seconds (controls reverberation length).
        seed:      RNG seed for this IR (use different values for L/R
                   decorrelation — legacy scripts use seeds 7 and 11).
        sr:        Sample rate.
        lp_cutoff: Low-pass cutoff for the dark tail.

    Returns:
        Float64 mono IR array of length ``int(seconds * sr)``.
    """
    rng = np.random.default_rng(seed)
    n = int(seconds * sr)
    t = np.arange(n, dtype=np.float64)
    ir = rng.standard_normal(n) * np.exp(-t / (sr * decay))
    sos = signal.butter(2, lp_cutoff, "low", fs=sr, output="sos")
    ir = signal.sosfilt(sos, ir)
    energy = np.sqrt(np.sum(ir ** 2))
    return ir / (energy + 1e-12)


def reverb(
    x: np.ndarray,
    ir: np.ndarray,
    wet: float = 0.5,
    use_oaconvolve: bool = False,
) -> np.ndarray:
    """Apply convolution reverb to a mono signal *x*.

    The wet signal is trimmed to ``len(x)``, renormalized to the dry peak,
    then blended at the given wet/dry ratio.

    Args:
        x:               Input mono signal.
        ir:              Impulse response (mono).
        wet:             Wet/dry ratio (0.0 = dry, 1.0 = wet).
        use_oaconvolve:  Use ``scipy.signal.oaconvolve`` (better for long IRs
                         or when latency allows); default is ``fftconvolve``
                         matching most legacy scripts.

    Returns:
        Processed mono signal, same length as *x*.
    """
    convolve = signal.oaconvolve if use_oaconvolve else signal.fftconvolve
    tail = convolve(x, ir)[: len(x)]
    peak_tail = np.max(np.abs(tail)) + 1e-12
    peak_dry = np.max(np.abs(x)) + 1e-12
    tail = tail / peak_tail * peak_dry
    return (1.0 - wet) * x + wet * tail


def reverb_stereo(
    L: np.ndarray,
    R: np.ndarray,
    ir_L: np.ndarray,
    ir_R: np.ndarray,
    wet: float = 0.5,
    use_oaconvolve: bool = False,
) -> tuple[np.ndarray, np.ndarray]:
    """Apply separate convolution reverbs to L and R channels.

    Convenience wrapper matching the ``reverb_layer`` pattern in ambient/lost.py.
    """
    return (
        reverb(L, ir_L, wet, use_oaconvolve),
        reverb(R, ir_R, wet, use_oaconvolve),
    )


def make_stereo_ir_pair(
    seconds: float,
    decay: float,
    seed_L: int = 7,
    seed_R: int = 11,
    sr: int = 44100,
    lp_cutoff: float = 4000.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Build a decorrelated stereo IR pair using the conventional seed pair.

    The legacy scripts universally use seeds 7 and 11 for L/R decorrelation.
    This is the canonical replacement.
    """
    ir_L = make_reverb_ir(seconds, decay, seed_L, sr, lp_cutoff)
    ir_R = make_reverb_ir(seconds, decay, seed_R, sr, lp_cutoff)
    return ir_L, ir_R
