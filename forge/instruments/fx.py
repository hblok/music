"""forge.instruments.fx — zap, riser, explosion, heartbeat, crash, rev cymbal."""

from __future__ import annotations

import numpy as np

from forge.core.buffer import AudioBuffer
from forge.core.dsp import lowpass
from forge.instruments.base import ParamSchema

SR = 44100


# ---------------------------------------------------------------- Zap

ZAP_PARAMS = [
    ParamSchema("f_start", "float", 2000.0, lo=500.0, hi=8000.0, unit="Hz"),
    ParamSchema("f_end", "float", 200.0, lo=30.0, hi=1000.0, unit="Hz"),
    ParamSchema("duration", "float", 0.18, lo=0.05, hi=0.5, unit="s"),
    ParamSchema("noise_level", "float", 0.3, lo=0.0, hi=1.0),
]


def make_zap(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
    """Laser/zap: exponential pitch fall + noise burst."""
    sr = ctx.get("sr", SR)
    f_start = float(params.get("f_start", 2000.0))
    f_end = float(params.get("f_end", 200.0))
    dur = float(params.get("duration", 0.18))
    noise_level = float(params.get("noise_level", 0.3))

    n = int(dur * sr)
    tt = np.arange(n, dtype=np.float64) / sr

    f_curve = f_end + (f_start - f_end) * np.exp(-tt * 20.0)
    phase = 2.0 * np.pi * np.cumsum(f_curve) / sr
    env = np.exp(-tt * 15.0)

    tone = env * np.sin(phase)
    noise = noise_level * env * rng.standard_normal(n)
    sig = tone + noise

    return AudioBuffer.from_mono(sig, sr=sr)


# ---------------------------------------------------------------- Riser

RISER_PARAMS = [
    ParamSchema("duration", "float", 4.0, lo=0.5, hi=16.0, unit="s"),
    ParamSchema("f_start", "float", 60.0, lo=20.0, hi=500.0, unit="Hz"),
    ParamSchema("f_end", "float", 2000.0, lo=200.0, hi=8000.0, unit="Hz"),
    ParamSchema("noise_level", "float", 0.5, lo=0.0, hi=1.0),
]


def riser(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
    """White noise + pitch-rising tone building into a drop."""
    sr = ctx.get("sr", SR)
    dur = float(params.get("duration", ctx.get("duration", 4.0)))
    f_start = float(params.get("f_start", 60.0))
    f_end = float(params.get("f_end", 2000.0))
    noise_level = float(params.get("noise_level", 0.5))

    n = int(dur * sr)
    tt = np.arange(n, dtype=np.float64) / sr

    # exponential sweep upward
    f_curve = f_start * (f_end / f_start) ** (tt / dur)
    phase = 2.0 * np.pi * np.cumsum(f_curve) / sr

    env = (tt / dur) ** 2.0  # builds from silence to full

    tone = env * np.sin(phase)
    noise = noise_level * env * rng.standard_normal(n)
    noise = lowpass(noise, f_end * 0.8, order=2, sr=sr)

    return AudioBuffer.from_mono(tone + noise, sr=sr)


# ---------------------------------------------------------------- Explosion

EXPLOSION_PARAMS = [
    ParamSchema("duration", "float", 3.5, lo=1.0, hi=10.0, unit="s"),
    ParamSchema("sub_f", "float", 55.0, lo=20.0, hi=120.0, unit="Hz"),
    ParamSchema("body_decay", "float", 0.8, lo=0.1, hi=3.0, unit="s"),
]


def explosion(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
    """Layered noise burst + pitch-fall + low rumble tail.

    Replicates ``explosion`` from fall_of_arrakeen.
    """
    sr = ctx.get("sr", SR)
    dur = float(params.get("duration", 3.5))
    sub_f = float(params.get("sub_f", 55.0))
    body_decay = float(params.get("body_decay", 0.8))

    n = int(dur * sr)
    tt = np.arange(n, dtype=np.float64) / sr

    # body: wideband noise burst
    noise = rng.standard_normal(n)
    from scipy import signal as _sig
    sos_body = _sig.butter(4, [80.0, 6000.0], "bandpass", fs=sr, output="sos")
    body = _sig.sosfilt(sos_body, noise) * np.exp(-tt / body_decay)

    # sub thump: falling pitch
    f_curve = 30.0 + (sub_f - 30.0) * np.exp(-tt * 5.0)
    phase = 2.0 * np.pi * np.cumsum(f_curve) / sr
    sub_env = np.exp(-tt * 3.0) * (1.0 - np.exp(-tt * 80.0))
    sub = sub_env * np.sin(phase)

    # rumble tail
    sos_rumble = _sig.butter(4, 120.0, "low", fs=sr, output="sos")
    rumble = _sig.sosfilt(sos_rumble, rng.standard_normal(n)) * np.exp(-tt / (body_decay * 2))

    sig = body + 0.6 * sub + 0.4 * rumble
    return AudioBuffer.from_mono(sig, sr=sr)


# ---------------------------------------------------------------- Heartbeat

HEART_PARAMS = [
    ParamSchema("duration", "float", 60.0, lo=1.0, hi=600.0, unit="s"),
    ParamSchema("bpm", "float", 60.0, lo=40.0, hi=100.0, unit="BPM"),
    ParamSchema("thump_f", "float", 55.0, lo=30.0, hi=120.0, unit="Hz"),
    ParamSchema("level", "float", 0.6, lo=0.1, hi=1.0),
]


def heart(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
    """Soft two-thump heartbeat running under the whole duration.

    The through-line in ambient/lost.py — audible and present, not subliminal.
    """
    sr = ctx.get("sr", SR)
    dur = float(params.get("duration", ctx.get("duration", 60.0)))
    bpm = float(params.get("bpm", 60.0))
    thump_f = float(params.get("thump_f", 55.0))
    level = float(params.get("level", 0.6))

    n = int(dur * sr)
    buf = AudioBuffer(n, sr=sr)

    beat_s = 60.0 / bpm
    thump_dur = 0.15
    thump_n = int(thump_dur * sr)

    tt_t = np.arange(thump_n, dtype=np.float64) / sr
    thump = (np.sin(2.0 * np.pi * thump_f * tt_t)
             * np.exp(-tt_t * 20.0)
             * (1.0 - np.exp(-tt_t * 200.0)))
    thump2 = thump * 0.7  # the second softer beat

    t = 0.0
    while t < dur - thump_dur:
        buf.add_at(thump, t, gain=level)
        t2 = t + beat_s * 0.45
        if t2 + thump_dur < dur:
            buf.add_at(thump2, t2, gain=level)
        t += beat_s

    return buf


# ---------------------------------------------------------------- Reversed cymbal

REV_CYMBAL_PARAMS = [
    ParamSchema("duration", "float", 1.6, lo=0.3, hi=4.0, unit="s"),
    ParamSchema("hp_cutoff", "float", 4000.0, lo=1000.0, hi=12000.0, unit="Hz"),
]


def rev_cymbal(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
    """Reversed cymbal swell for build transitions."""
    sr = ctx.get("sr", SR)
    dur = float(params.get("duration", 1.6))
    hp_cutoff = float(params.get("hp_cutoff", 4000.0))

    n = int(dur * sr)
    tt = np.arange(n, dtype=np.float64) / sr

    from scipy import signal as _sig
    sos = _sig.butter(4, hp_cutoff, "high", fs=sr, output="sos")
    noise = _sig.sosfilt(sos, rng.standard_normal(n))
    noise /= np.max(np.abs(noise)) + 1e-12

    # reversed: builds to a hit
    env = (tt / dur) ** 2.0
    return AudioBuffer.from_mono(noise * env, sr=sr)
