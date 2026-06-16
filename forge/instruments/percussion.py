"""forge.instruments.percussion — darbuka, kick, hat, clap, snare, war drum.

All percussion instruments are one-shot hit generators returning short
AudioBuffers.  They should be used with the render cache via
``forge.instruments.base.render_cached``.
"""

from __future__ import annotations

import numpy as np

from forge.core.buffer import AudioBuffer
from forge.core.dsp import lowpass, bandpass
from forge.instruments.base import ParamSchema

SR = 44100


# ---------------------------------------------------------------- darbuka doum

DOUM_PARAMS = [
    ParamSchema("f0", "float", 140.0, lo=80.0, hi=300.0, unit="Hz"),
    ParamSchema("f1", "float", 80.0, lo=40.0, hi=180.0, unit="Hz",
                label="End freq"),
    ParamSchema("duration", "float", 0.45, lo=0.1, hi=1.0, unit="s"),
    ParamSchema("attack", "float", 0.008, lo=0.001, hi=0.05, unit="s"),
    ParamSchema("gain", "float", 1.0, lo=0.1, hi=2.0),
]


def make_doum(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
    """Darbuka doum stroke: pitch-falling sine + narrow bandpass body.

    Present in 11 legacy scripts; this is the canonical extraction.
    """
    sr = ctx.get("sr", SR)
    f0 = float(params.get("f0", 140.0))
    f1 = float(params.get("f1", 80.0))
    dur = float(params.get("duration", 0.45))
    attack_s = float(params.get("attack", 0.008))
    gain = float(params.get("gain", 1.0))

    n = int(dur * sr)
    tt = np.arange(n, dtype=np.float64) / sr

    # exponential pitch fall
    f_curve = f1 + (f0 - f1) * np.exp(-tt * 12.0)
    phase = 2.0 * np.pi * np.cumsum(f_curve) / sr

    n_att = max(1, int(attack_s * sr))
    env = np.exp(-tt * 8.0)
    env[:n_att] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(n_att) / n_att)

    sig = env * np.sin(phase) * gain
    return AudioBuffer.from_mono(sig, sr=sr)


# ---------------------------------------------------------------- darbuka tek

TEK_PARAMS = [
    ParamSchema("ghost", "bool", False, label="Ghost (half gain)"),
    ParamSchema("f_click", "float", 800.0, lo=400.0, hi=2000.0, unit="Hz"),
    ParamSchema("f_ring", "float", 1400.0, lo=600.0, hi=3000.0, unit="Hz"),
    ParamSchema("duration", "float", 0.18, lo=0.05, hi=0.4, unit="s"),
]


def make_tek(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
    """Darbuka tek stroke: high-band click + ring.

    ``ghost=True`` halves the gain (for probability-based ghost notes).
    """
    sr = ctx.get("sr", SR)
    f_click = float(params.get("f_click", 800.0))
    f_ring = float(params.get("f_ring", 1400.0))
    dur = float(params.get("duration", 0.18))
    ghost = bool(params.get("ghost", False))

    n = int(dur * sr)
    tt = np.arange(n, dtype=np.float64) / sr

    click_env = np.exp(-tt * 60.0)
    ring_env = np.exp(-tt * 25.0)
    sig = (click_env * np.sin(2.0 * np.pi * f_click * tt)
           + 0.5 * ring_env * np.sin(2.0 * np.pi * f_ring * tt))
    if ghost:
        sig *= 0.5

    return AudioBuffer.from_mono(sig, sr=sr)


# ---------------------------------------------------------------- kick drum

KICK_PARAMS = [
    ParamSchema("f0", "float", 55.0, lo=30.0, hi=120.0, unit="Hz",
                label="Start freq"),
    ParamSchema("f1", "float", 27.0, lo=15.0, hi=60.0, unit="Hz",
                label="End freq"),
    ParamSchema("duration", "float", 0.55, lo=0.2, hi=1.2, unit="s"),
    ParamSchema("drive", "float", 1.5, lo=0.5, hi=4.0, label="Tanh drive"),
    ParamSchema("sub_level", "float", 0.5, lo=0.0, hi=1.0),
    ParamSchema("attack", "float", 0.005, lo=0.001, hi=0.02, unit="s"),
]


def make_kick(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
    """909-style kick: pitch-falls from f0 → f1, tanh drive, layered sub."""
    sr = ctx.get("sr", SR)
    f0 = float(params.get("f0", 55.0))
    f1 = float(params.get("f1", 27.0))
    dur = float(params.get("duration", 0.55))
    drive = float(params.get("drive", 1.5))
    sub_level = float(params.get("sub_level", 0.5))
    attack_s = float(params.get("attack", 0.005))

    n = int(dur * sr)
    tt = np.arange(n, dtype=np.float64) / sr

    # falling pitch curve
    f_curve = f1 + (f0 - f1) * np.exp(-tt * 40.0)
    phase = 2.0 * np.pi * np.cumsum(f_curve) / sr

    n_att = max(1, int(attack_s * sr))
    env = np.exp(-tt * 6.0)
    env[:n_att] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(n_att) / n_att)

    kick = np.tanh(drive * np.sin(phase)) * env
    sub = sub_level * np.sin(2.0 * np.pi * f1 * tt) * np.exp(-tt * 10.0)

    sig = kick + sub
    return AudioBuffer.from_mono(sig, sr=sr)


# ---------------------------------------------------------------- hi-hat

HAT_PARAMS = [
    ParamSchema("open_", "bool", False, label="Open hat"),
    ParamSchema("decay_closed", "float", 0.05, lo=0.01, hi=0.2, unit="s"),
    ParamSchema("decay_open", "float", 0.35, lo=0.1, hi=0.8, unit="s"),
    ParamSchema("hp_cutoff", "float", 7000.0, lo=3000.0, hi=18000.0, unit="Hz"),
]


def make_hat(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
    """Closed/open hi-hat via high-passed noise."""
    sr = ctx.get("sr", SR)
    open_ = bool(params.get("open_", False))
    decay = float(params.get("decay_open" if open_ else "decay_closed",
                              0.35 if open_ else 0.05))
    hp_cutoff = float(params.get("hp_cutoff", 7000.0))

    n = max(int(decay * 4 * sr), 100)
    tt = np.arange(n, dtype=np.float64) / sr

    noise = rng.standard_normal(n)
    from scipy import signal as _sig
    sos = _sig.butter(4, hp_cutoff, "high", fs=sr, output="sos")
    noise = _sig.sosfilt(sos, noise)
    noise /= np.max(np.abs(noise)) + 1e-12

    env = np.exp(-tt / (decay + 1e-12))
    return AudioBuffer.from_mono(noise * env, sr=sr)


# ---------------------------------------------------------------- clap

CLAP_PARAMS = [
    ParamSchema("n_layers", "int", 3, lo=1, hi=6),
    ParamSchema("jitter_ms", "float", 5.0, lo=0.0, hi=20.0, unit="ms"),
    ParamSchema("decay", "float", 0.12, lo=0.05, hi=0.5, unit="s"),
    ParamSchema("bp_lo", "float", 800.0, lo=200.0, hi=3000.0, unit="Hz"),
    ParamSchema("bp_hi", "float", 4000.0, lo=1000.0, hi=12000.0, unit="Hz"),
]


def make_clap(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
    """Layered noise bursts with slight timing scatter."""
    sr = ctx.get("sr", SR)
    n_layers = int(params.get("n_layers", 3))
    jitter_s = float(params.get("jitter_ms", 5.0)) / 1000.0
    decay = float(params.get("decay", 0.12))
    bp_lo = float(params.get("bp_lo", 800.0))
    bp_hi = float(params.get("bp_hi", 4000.0))

    dur = decay * 4.0 + jitter_s * n_layers + 0.01
    n = int(dur * sr)
    buf = AudioBuffer(n, sr=sr)

    from scipy import signal as _sig
    sos = _sig.butter(4, [bp_lo, bp_hi], "bandpass", fs=sr, output="sos")

    for _ in range(n_layers):
        burst_n = int((0.02 + decay) * sr)
        noise = rng.standard_normal(burst_n)
        noise = _sig.sosfilt(sos, noise)
        noise /= np.max(np.abs(noise)) + 1e-12
        tt = np.arange(burst_n, dtype=np.float64) / sr
        env = np.exp(-tt / (decay + 1e-12))
        noise *= env
        offset = rng.uniform(0, jitter_s)
        buf.add_at(noise, offset)

    return buf


# ---------------------------------------------------------------- snare

SNARE_PARAMS = [
    ParamSchema("f_body", "float", 200.0, lo=80.0, hi=500.0, unit="Hz"),
    ParamSchema("decay_body", "float", 0.12, lo=0.05, hi=0.5, unit="s"),
    ParamSchema("decay_rattle", "float", 0.18, lo=0.05, hi=0.6, unit="s"),
    ParamSchema("body_level", "float", 0.4, lo=0.0, hi=1.0),
    ParamSchema("buzz", "bool", False, label="Buzz roll variant"),
]


def make_snare(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
    """Tonal body + noise rattle snare."""
    sr = ctx.get("sr", SR)
    f_body = float(params.get("f_body", 200.0))
    d_body = float(params.get("decay_body", 0.12))
    d_rattle = float(params.get("decay_rattle", 0.18))
    body_level = float(params.get("body_level", 0.4))
    buzz = bool(params.get("buzz", False))

    dur = max(d_body, d_rattle) * 4.0
    n = int(dur * sr)
    tt = np.arange(n, dtype=np.float64) / sr

    # tonal body
    body = body_level * np.sin(2.0 * np.pi * f_body * tt) * np.exp(-tt / (d_body + 1e-12))

    # noise rattle (bandpassed)
    from scipy import signal as _sig
    sos = _sig.butter(4, [1500.0, 8000.0], "bandpass", fs=sr, output="sos")
    rattle = _sig.sosfilt(sos, rng.standard_normal(n))
    rattle /= np.max(np.abs(rattle)) + 1e-12
    rattle_mult = 2.0 if buzz else 1.0
    rattle = rattle * np.exp(-tt / (d_rattle * rattle_mult + 1e-12))

    return AudioBuffer.from_mono(body + rattle, sr=sr)


# ---------------------------------------------------------------- war drum

WAR_DRUM_PARAMS = [
    ParamSchema("f0", "float", 80.0, lo=40.0, hi=180.0, unit="Hz"),
    ParamSchema("f1", "float", 40.0, lo=20.0, hi=100.0, unit="Hz"),
    ParamSchema("duration", "float", 0.8, lo=0.3, hi=2.0, unit="s"),
    ParamSchema("resonance_decay", "float", 0.5, lo=0.1, hi=2.0, unit="s"),
]


def make_war_drum(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
    """Large membrane strike: deep pitch-fall + resonant body."""
    sr = ctx.get("sr", SR)
    f0 = float(params.get("f0", 80.0))
    f1 = float(params.get("f1", 40.0))
    dur = float(params.get("duration", 0.8))
    res_decay = float(params.get("resonance_decay", 0.5))

    n = int(dur * sr)
    tt = np.arange(n, dtype=np.float64) / sr

    f_curve = f1 + (f0 - f1) * np.exp(-tt * 8.0)
    phase = 2.0 * np.pi * np.cumsum(f_curve) / sr
    env = np.exp(-tt * 3.0) * (1.0 - np.exp(-tt * 200.0))

    strike = env * np.sin(phase)

    # resonant ring: bandpassed noise
    from scipy import signal as _sig
    sos = _sig.butter(2, [f1 * 0.8, f1 * 1.2], "bandpass", fs=sr, output="sos")
    ring = _sig.sosfilt(sos, rng.standard_normal(n)) * np.exp(-tt / (res_decay + 1e-12))

    return AudioBuffer.from_mono(strike + 0.4 * ring, sr=sr)


# ---------------------------------------------------------------- frame drum

FRAME_HIT_PARAMS = [
    ParamSchema("f0", "float", 180.0, lo=80.0, hi=400.0, unit="Hz"),
    ParamSchema("duration", "float", 0.25, lo=0.05, hi=0.8, unit="s"),
]


def make_frame_hit(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
    """Frame drum single stroke: bandpassed noise + tone."""
    sr = ctx.get("sr", SR)
    f0 = float(params.get("f0", 180.0))
    dur = float(params.get("duration", 0.25))

    n = int(dur * sr)
    tt = np.arange(n, dtype=np.float64) / sr

    from scipy import signal as _sig
    sos = _sig.butter(4, [f0 * 0.5, f0 * 2.0], "bandpass", fs=sr, output="sos")
    noise = _sig.sosfilt(sos, rng.standard_normal(n))
    noise /= np.max(np.abs(noise)) + 1e-12

    tone = np.sin(2.0 * np.pi * f0 * tt)
    env = np.exp(-tt * 20.0)

    return AudioBuffer.from_mono((noise * 0.6 + tone * 0.4) * env, sr=sr)


def frame_roll(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
    """Frame drum roll: rapid repeated hits."""
    sr = ctx.get("sr", SR)
    duration = float(params.get("duration", ctx.get("duration", 2.0)))
    rate_hz = float(params.get("rate_hz", 14.0))
    f0 = float(params.get("f0", 180.0))

    n = int(duration * sr)
    buf = AudioBuffer(n, sr=sr)

    hit_params = {"f0": f0, "duration": 0.08}
    interval = 1.0 / rate_hz
    t = 0.0
    while t < duration:
        hit = make_frame_hit(hit_params, rng, sr=sr)
        gain = 0.6 + 0.4 * rng.random()
        buf.add_at(hit.L, t, gain=gain)
        t += interval * rng.uniform(0.85, 1.15)

    return buf
