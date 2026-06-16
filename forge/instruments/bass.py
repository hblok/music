"""forge.instruments.bass — bass notes, psy-bass, and 303-style acid.

All bass instruments are one-shot note generators; use with the render cache.
"""

from __future__ import annotations

import numpy as np

from forge.core.buffer import AudioBuffer
from forge.core.dsp import glide_curve, lowpass, midi_to_hz, raised_cosine_attack, warm_partials
from forge.instruments.base import ParamSchema

SR = 44100


# ---------------------------------------------------------------- Warm bass note (trance/dune)

BASS_NOTE_PARAMS = [
    ParamSchema("midi", "int", 38, lo=24, hi=60, label="MIDI note"),
    ParamSchema("duration", "float", 0.46, lo=0.05, hi=2.0, unit="s"),
    ParamSchema("lp_cutoff", "float", 1600.0, lo=200.0, hi=6000.0, unit="Hz"),
    ParamSchema("rolloff", "float", 1.3, lo=1.0, hi=2.0),
    ParamSchema("drive", "float", 0.8, lo=0.1, hi=3.0),
    ParamSchema("sub_mix", "float", 0.3, lo=0.0, hi=0.8),
    ParamSchema("detune", "float", 0.003, lo=0.0, hi=0.01),
]


def bass_note(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
    """Warm bass note: rolled-off saw + sine sub (trance warmth recipe).

    Replicates ``bass_note`` from trance/lost_v3.py + lost_v4.py with the
    warmth fixes (rolloff, sub mix, soft attack, lower LP cutoff).
    """
    sr = ctx.get("sr", SR)
    midi = int(params.get("midi", 38))
    dur = float(params.get("duration", 0.46))
    lp_cutoff = float(params.get("lp_cutoff", 1600.0))
    rolloff = float(params.get("rolloff", 1.3))
    drive = float(params.get("drive", 0.8))
    sub_mix = float(params.get("sub_mix", 0.3))
    detune = float(params.get("detune", 0.003))

    f = midi_to_hz(midi)
    n = int(dur * sr)
    tt = np.arange(n, dtype=np.float64) / sr

    # two detuned voices
    sig = np.zeros(n)
    for det in (1.0 - detune, 1.0 + detune):
        ph = 2.0 * np.pi * f * det * tt
        sig += np.tanh(drive * warm_partials(ph, rolloff=rolloff, sub_mix=sub_mix))

    sig = lowpass(sig, lp_cutoff, order=2, sr=sr)

    # bloom-in attack + exponential decay
    attack_n = min(int(0.015 * sr), n)
    env = np.exp(-tt * (3.0 / dur))
    env[:attack_n] = env[:attack_n] * raised_cosine_attack(attack_n)

    return AudioBuffer.from_mono(sig * env, sr=sr)


# ---------------------------------------------------------------- Psy-trance sub bass

PSY_BASS_PARAMS = [
    ParamSchema("midi", "int", 26, lo=18, hi=48, label="MIDI note"),
    ParamSchema("duration", "float", 0.42, lo=0.05, hi=1.0, unit="s"),
    ParamSchema("f_start", "float", 0.0, lo=0.0, hi=100.0, unit="Hz",
                label="Pitch-fall start offset (0=auto)"),
    ParamSchema("decay_mult", "float", 6.0, lo=1.0, hi=20.0),
]


def psy_bass_note(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
    """Psy-trance sub-bass: deep pitch-fall + sine sub.

    Replicates ``psy_bass_note`` from sleeper_awakens, water_of_life, fall_of_arrakeen.
    """
    sr = ctx.get("sr", SR)
    midi = int(params.get("midi", 26))
    dur = float(params.get("duration", 0.42))
    f_note = midi_to_hz(midi)
    f_start = float(params.get("f_start", 0.0)) or f_note * 3.0
    decay_mult = float(params.get("decay_mult", 6.0))

    n = int(dur * sr)
    tt = np.arange(n, dtype=np.float64) / sr

    f_curve = f_note + (f_start - f_note) * np.exp(-tt * decay_mult)
    phase = 2.0 * np.pi * np.cumsum(f_curve) / sr

    env = np.exp(-tt * (4.0 / dur)) * (1.0 - np.exp(-tt * 200.0))
    sig = np.sin(phase) * env

    # sub sine for extra weight
    sub = 0.4 * np.sin(2.0 * np.pi * f_note * tt) * env

    return AudioBuffer.from_mono(sig + sub, sr=sr)


# ---------------------------------------------------------------- 303-style acid note

ACID_PARAMS = [
    ParamSchema("midi", "int", 38, lo=24, hi=60, label="MIDI note"),
    ParamSchema("cutoff", "float", 800.0, lo=100.0, hi=8000.0, unit="Hz"),
    ParamSchema("duration", "float", 0.22, lo=0.05, hi=1.0, unit="s"),
    ParamSchema("accent", "bool", False),
    ParamSchema("slide_to", "int", 0, lo=0, hi=96, label="Slide to MIDI (0=no slide)"),
    ParamSchema("resonance_q", "float", 1.2, lo=0.3, hi=6.0,
                label="Resonance Q (keep ≤2 for warmth)"),
    ParamSchema("drive", "float", 1.2, lo=0.3, hi=3.0),
]


def acid_note(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
    """303-style acid note: resonant filter sweep, low-Q for warmth.

    Replicates ``acid_note`` from sleeper_awakens, water_of_life, fall_of_arrakeen.
    The Q is kept at ≤2 per the trance warmth recipe (resonant but not nasal).
    """
    sr = ctx.get("sr", SR)
    midi = int(params.get("midi", 38))
    cutoff = float(params.get("cutoff", 800.0))
    dur = float(params.get("duration", 0.22))
    accent = bool(params.get("accent", False))
    slide_to_midi = int(params.get("slide_to", 0))
    q = float(params.get("resonance_q", 1.2))
    drive = float(params.get("drive", 1.2))

    f_root = midi_to_hz(midi)
    n = int(dur * sr)
    tt = np.arange(n, dtype=np.float64) / sr

    # slide: one-pole glide if slide_to != 0
    if slide_to_midi:
        notes = [(midi, dur * 0.4), (slide_to_midi, dur * 0.6)]
        f_curve = glide_curve(notes, n, tau=0.03, sr=sr)
    else:
        f_curve = np.full(n, f_root)

    # sawtooth via accumulated phase + odd harmonics
    phase = 2.0 * np.pi * np.cumsum(f_curve) / sr
    sig = sum(np.sin(k * phase) / k for k in (1, 2, 3, 4, 5))

    # sweeping resonant bandpass (low-Q for warmth)
    cutoff_env = cutoff * (2.5 if accent else 1.0) * np.exp(-tt * (4.0 / dur))
    cutoff_env = np.clip(cutoff_env, 80.0, sr * 0.45)

    # apply time-invariant resonant filter at the envelope start frequency
    from scipy import signal as _sig
    sos_bp = _sig.iirpeak(float(cutoff_env[0]), Q=q, fs=sr)
    sos_lp = _sig.butter(2, float(np.clip(cutoff * 1.5, 80, sr * 0.45)), "low",
                         fs=sr, output="sos")
    filtered = _sig.sosfilt(sos_lp, np.tanh(drive * sig))

    env = np.exp(-tt * (5.0 / dur)) * (1.0 - np.exp(-tt * 200.0))
    if accent:
        env *= 1.3

    return AudioBuffer.from_mono(filtered * env, sr=sr)
