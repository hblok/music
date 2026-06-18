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


# ---------------------------------------------------------------- boom (cinematic boom)

BOOM_PARAMS = [
    ParamSchema("duration", "float", 2.5, lo=0.5, hi=10.0, unit="s"),
    ParamSchema("sub_f_start", "float", 60.0, lo=20.0, hi=120.0, unit="Hz",
                label="Sub start Hz"),
    ParamSchema("sub_f_end", "float", 30.0, lo=10.0, hi=80.0, unit="Hz",
                label="Sub end Hz"),
    ParamSchema("lp_cutoff", "float", 150.0, lo=40.0, hi=400.0, unit="Hz"),
    ParamSchema("noise_level", "float", 0.7, lo=0.0, hi=1.5),
    ParamSchema("body_decay", "float", 1.8, lo=0.2, hi=6.0, unit="s"),
]


def _make_boom_core(sr, dur, sub_f_start, sub_f_end, lp_cutoff,
                    noise_level, body_decay, rng):
    """Shared helper: brown-noise body + falling sub core.

    Adapted from the cinematic boom in generate_kanly.py (the duel blow).
    """
    n = int(dur * sr)
    tb = np.arange(n, dtype=np.float64) / sr

    from scipy import signal as _sig

    # brown noise body through lowpass
    brown = np.cumsum(rng.standard_normal(n))
    brown -= np.linspace(brown[0], brown[-1], n)
    brown /= np.max(np.abs(brown)) + 1e-12
    env_body = (1.0 - np.exp(-tb / 0.03)) * np.exp(-tb / body_decay)
    sos_boom = _sig.butter(4, lp_cutoff, "low", fs=sr, output="sos")
    body = _sig.sosfilt(sos_boom, brown * env_body)

    # falling sub-bass core
    fsub = sub_f_end + (sub_f_start - sub_f_end) * np.exp(-tb * 2.0)
    env_sub = (1.0 - np.exp(-tb / 0.005)) * np.exp(-tb / (body_decay * 0.8))
    core = np.sin(2.0 * np.pi * np.cumsum(fsub) / sr) * env_sub

    sig = noise_level * body + core
    return sig


def make_boom(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
    """Cinematic boom — brown-noise burst through ~150 Hz LP + falling sub core.

    Based on the duel-blow boom in generate_kanly.py and the worm strike in
    generate_fall_of_arrakeen.py.
    """
    sr = ctx.get("sr", SR)
    dur = float(params.get("duration", 2.5))
    sub_f_start = float(params.get("sub_f_start", 60.0))
    sub_f_end = float(params.get("sub_f_end", 30.0))
    lp_cutoff = float(params.get("lp_cutoff", 150.0))
    noise_level = float(params.get("noise_level", 0.7))
    body_decay = float(params.get("body_decay", 1.8))

    sig = _make_boom_core(sr, dur, sub_f_start, sub_f_end, lp_cutoff,
                          noise_level, body_decay, rng)
    peak = np.max(np.abs(sig)) + 1e-12
    return AudioBuffer.from_mono(sig / peak, sr=sr)


# ---------------------------------------------------------------- sub_boom (deep sub variant)

SUB_BOOM_PARAMS = [
    ParamSchema("duration", "float", 0.45, lo=0.1, hi=2.0, unit="s"),
    ParamSchema("f_start", "float", 50.0, lo=20.0, hi=100.0, unit="Hz",
                label="Sub start Hz"),
    ParamSchema("f_end", "float", 37.0, lo=10.0, hi=70.0, unit="Hz",
                label="Sub end Hz"),
    ParamSchema("noise_level", "float", 0.15, lo=0.0, hi=0.8),
    ParamSchema("decay", "float", 1.2, lo=0.3, hi=4.0, unit="s"),
]


def make_sub_boom(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
    """Sub-heavy boom variant — deeper falling sub core, less noise body.

    Based on ``make_sub_boom()`` in generate_fall_of_arrakeen.py: a pure
    50→37 Hz falling sine that sustains the whole beat beneath a kick.
    """
    sr = ctx.get("sr", SR)
    dur = float(params.get("duration", 0.45))
    f_start = float(params.get("f_start", 50.0))
    f_end = float(params.get("f_end", 37.0))
    noise_level = float(params.get("noise_level", 0.15))
    decay = float(params.get("decay", 1.2))

    n = int(dur * sr)
    td = np.arange(n, dtype=np.float64) / sr

    # pure falling sub sine
    f_curve = f_end + (f_start - f_end) * np.exp(-td * 12.0)
    sub = np.sin(2.0 * np.pi * np.cumsum(f_curve) / sr)
    # envelope: quick attack, gentle decay, short release at end
    env = ((1.0 - np.exp(-td / 0.003))
           * np.exp(-td * decay)
           * np.clip((dur - td) / 0.06, 0.0, 1.0))
    sig = sub * env

    # optional low noise layer for body
    if noise_level > 0.0:
        from scipy import signal as _sig
        sos_sub = _sig.butter(4, min(80.0, sr * 0.499), "low", fs=sr, output="sos")
        noise_body = _sig.sosfilt(sos_sub, rng.standard_normal(n))
        noise_body *= env * noise_level
        sig = sig + noise_body

    peak = np.max(np.abs(sig)) + 1e-12
    return AudioBuffer.from_mono(sig / peak, sr=sr)


# ---------------------------------------------------------------- machine_chug (harvester loop)

MACHINE_CHUG_PARAMS = [
    ParamSchema("duration", "float", 4.0, lo=0.5, hi=30.0, unit="s"),
    ParamSchema("f0", "float", 73.4, lo=40.0, hi=200.0, unit="Hz",
                label="Engine freq (D2≈73)"),
    ParamSchema("detune", "float", 0.006, lo=0.0, hi=0.03,
                label="Detune ratio"),
    ParamSchema("lp_cutoff", "float", 420.0, lo=100.0, hi=1200.0, unit="Hz"),
    ParamSchema("idle_floor", "float", 0.18, lo=0.0, hi=0.5,
                label="Idle floor"),
    ParamSchema("drive", "float", 1.5, lo=0.5, hi=4.0, label="Tanh drive"),
    ParamSchema("gain", "float", 1.0, lo=0.1, hi=2.0),
]


def make_machine_chug(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
    """Two detuned band-limited square-ish oscillators gated on an 8th-note rhythm.

    An idle floor keeps the engine always-on.  Adapted from the ``machine``
    layer in generate_spice_must_flow.py (harvester chug at 64 BPM).
    Takes a ``duration`` param for a sustained loop.
    """
    sr = ctx.get("sr", SR)
    dur = float(params.get("duration", 4.0))
    f0 = float(params.get("f0", 73.4))          # D2 ≈ 73.4 Hz
    detune = float(params.get("detune", 0.006))
    lp_cutoff = float(params.get("lp_cutoff", 420.0))
    idle_floor = float(params.get("idle_floor", 0.18))
    drive = float(params.get("drive", 1.5))
    gain = float(params.get("gain", 1.0))

    n = int(dur * sr)
    t = np.arange(n, dtype=np.float64) / sr

    # two detuned quasi-square oscillators (odd harmonics up to lp_cutoff)
    engine = np.zeros(n)
    for det, g in [(1.0, 1.0), (1.0 + detune, 0.9)]:
        k = 1
        while f0 * det * k < lp_cutoff and k <= 15:
            if k % 2 == 1:  # odd harmonics only
                engine += (g / k) * np.sin(2.0 * np.pi * f0 * det * k * t)
            k += 1

    from scipy import signal as _sig
    sos_eng = _sig.butter(2, min(lp_cutoff, sr * 0.499), "low", fs=sr, output="sos")
    engine = _sig.sosfilt(sos_eng, engine)
    eng_peak = np.max(np.abs(engine)) + 1e-12
    engine /= eng_peak

    # 8th-note chug gate pattern: accents at [1.0, 0.45, 0.72, 0.45, 0.88, ...]
    CHUG = [1.0, 0.45, 0.72, 0.45, 0.88, 0.45, 0.72, 0.45]
    gate = np.zeros(n)
    # use a default 64-BPM-ish 8th note spacing; ~0.23 s
    # but make it relative: 8th note at 64 BPM = beat/2 = 0.4688/2 s
    # For a general "machine chug" we use a fixed 8th note of ~0.23 s
    n8 = max(1, int(0.234375 * sr))  # 60/(64*2*4) ≈ 0.234 s  (beat/2 at 64 BPM)
    hit_env = ((1.0 - np.exp(-np.arange(n8, dtype=np.float64) / sr / 0.008))
               * np.exp(-np.arange(n8, dtype=np.float64) / sr * 6.0))
    step = 0
    pos = 0
    while pos < n:
        end = min(n, pos + n8)
        length = end - pos
        gate[pos:end] = np.maximum(gate[pos:end],
                                   CHUG[step % 8] * hit_env[:length])
        step += 1
        pos += n8

    gate = idle_floor + (1.0 - idle_floor) * gate
    machine = np.tanh(drive * engine * gate)
    peak = np.max(np.abs(machine)) + 1e-12
    return AudioBuffer.from_mono(machine / peak * gain, sr=sr)


# ---------------------------------------------------------------- thopter (ornithopter flyby)

THOPTER_PARAMS = [
    ParamSchema("duration", "float", 6.0, lo=1.0, hi=20.0, unit="s"),
    ParamSchema("f0_start", "float", 300.0, lo=80.0, hi=800.0, unit="Hz",
                label="Start freq"),
    ParamSchema("f0_end", "float", 170.0, lo=40.0, hi=500.0, unit="Hz",
                label="End freq (descent)"),
    ParamSchema("flut_start", "float", 23.0, lo=5.0, hi=60.0, unit="Hz",
                label="Wing rate start"),
    ParamSchema("flut_end", "float", 13.0, lo=2.0, hi=40.0, unit="Hz",
                label="Wing rate end"),
    ParamSchema("lp_cutoff", "float", 1500.0, lo=300.0, hi=5000.0, unit="Hz"),
    ParamSchema("gain", "float", 1.0, lo=0.1, hi=2.0),
]


def make_thopter(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
    """Descending detuned cluster + decelerating wing-flutter AM.

    Adapted from the cargo thopter flyby in generate_spice_must_flow.py.
    AM rate ramps down from ``flut_start`` to ``flut_end`` Hz.
    L→R panning sweep simulates a flyby.
    """
    sr = ctx.get("sr", SR)
    dur = float(params.get("duration", 6.0))
    f0_start = float(params.get("f0_start", 300.0))
    f0_end = float(params.get("f0_end", 170.0))
    flut_start = float(params.get("flut_start", 23.0))
    flut_end = float(params.get("flut_end", 13.0))
    lp_cutoff = float(params.get("lp_cutoff", 1500.0))
    gain = float(params.get("gain", 1.0))

    n = int(dur * sr)
    tt = np.arange(n, dtype=np.float64) / sr

    # descending frequency curve
    f0 = f0_end + (f0_start - f0_end) * np.exp(-tt / (dur * 0.5))

    # wing-flutter AM: rate decelerates from flut_start → flut_end
    flut_rate = flut_end + (flut_start - flut_end) * (1.0 - tt / dur)
    flut = 0.55 + 0.45 * np.sin(2.0 * np.pi * np.cumsum(flut_rate) / sr)

    # detuned cluster (5 oscillators)
    body = np.zeros(n)
    for det, g in [(0.985, 0.5), (0.995, 0.8), (1.0, 1.0), (1.008, 0.8), (1.017, 0.5)]:
        body += g * np.sin(2.0 * np.pi * np.cumsum(f0 * det) / sr)

    from scipy import signal as _sig
    sos_fb = _sig.butter(2, min(lp_cutoff, sr * 0.499), "low", fs=sr, output="sos")
    body = _sig.sosfilt(sos_fb, body)

    # apply wing flutter + bell-curve amplitude envelope (silence at edges)
    body = body * flut * np.sin(np.pi * tt / dur) ** 1.4
    body_peak = np.max(np.abs(body)) + 1e-12
    body = body / body_peak

    # L→R panning sweep
    u = tt / dur
    buf = AudioBuffer(n, sr=sr)
    buf.data[:, 0] = body * np.cos(u * np.pi / 2.0) * gain  # L fades
    buf.data[:, 1] = body * np.sin(u * np.pi / 2.0) * gain  # R rises
    return buf
