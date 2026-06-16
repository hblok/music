"""forge.instruments.textures — wind, drone, and dissonant swell.

Full-duration texture instruments: they require a ``duration`` context kwarg
and return a buffer of that length.  These are rendered once and committed
into the mix bus; they do not use the per-note cache.
"""

from __future__ import annotations

import numpy as np

from forge.core.buffer import AudioBuffer
from forge.core.dsp import slow_noise
from forge.core.reverb import make_stereo_ir_pair, reverb
from forge.instruments.base import ParamSchema

SR = 44100


# ---------------------------------------------------------------------------
# Wind

WIND_PARAMS = [
    ParamSchema("duration", "float", 60.0, lo=1.0, hi=600.0, unit="s"),
    ParamSchema("whoosh_lo", "float", 120.0, lo=50.0, hi=500.0, unit="Hz"),
    ParamSchema("whoosh_hi", "float", 900.0, lo=300.0, hi=3000.0, unit="Hz"),
    ParamSchema("hiss_lo", "float", 2000.0, lo=800.0, hi=8000.0, unit="Hz"),
    ParamSchema("hiss_hi", "float", 7000.0, lo=2000.0, hi=20000.0, unit="Hz"),
    ParamSchema("hiss_level", "float", 0.30, lo=0.0, hi=1.0),
    ParamSchema("gust_rate", "float", 0.22, lo=0.01, hi=2.0, unit="Hz"),
    ParamSchema("gust_power", "float", 2.2, lo=1.0, hi=4.0),
    ParamSchema("swell_rate", "float", 0.07, lo=0.01, hi=0.5, unit="Hz"),
    ParamSchema("pan_rate", "float", 0.05, lo=0.01, hi=0.5, unit="Hz"),
    ParamSchema("pan_lo", "float", 0.25, lo=0.0, hi=0.5),
    ParamSchema("pan_hi", "float", 0.75, lo=0.5, hi=1.0),
]


def wind(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
    """Desert wind: two-band filtered noise with stochastic gusts and stereo pan drift.

    Replicates the wind recipe used in arrakis, spice_must_flow, and all dune tracks.

    Params: see WIND_PARAMS.
    """
    from scipy import signal as _signal

    sr = ctx.get("sr", SR)
    duration = float(params.get("duration", ctx.get("duration", 60.0)))
    n = int(duration * sr)

    # noise source — shared for both bands to maintain correlation
    raw = rng.standard_normal(n)

    # whoosh band (body of the wind)
    whoosh_lo = float(params.get("whoosh_lo", 120.0))
    whoosh_hi = float(params.get("whoosh_hi", 900.0))
    sos_w = _signal.butter(4, [whoosh_lo, whoosh_hi], "bandpass", fs=sr, output="sos")
    whoosh = _signal.sosfilt(sos_w, raw)
    whoosh /= np.max(np.abs(whoosh)) + 1e-12

    # hiss band (sand carried on the wind)
    hiss_lo = float(params.get("hiss_lo", 2000.0))
    hiss_hi = float(params.get("hiss_hi", 7000.0))
    sos_h = _signal.butter(4, [hiss_lo, hiss_hi], "bandpass", fs=sr, output="sos")
    hiss = _signal.sosfilt(sos_h, raw)
    hiss /= np.max(np.abs(hiss)) + 1e-12
    hiss_level = float(params.get("hiss_level", 0.30))

    # gust envelopes
    gust_rate = float(params.get("gust_rate", 0.22))
    gust_power = float(params.get("gust_power", 2.2))
    swell_rate = float(params.get("swell_rate", 0.07))
    gust = slow_noise(duration, gust_rate, rng=rng, power=gust_power, sr=sr)
    gust2 = slow_noise(duration, swell_rate, rng=rng, power=1.5, sr=sr)
    wind_env = 0.25 + 0.75 * (0.6 * gust + 0.4 * gust2)

    # stereo pan drift
    pan_rate = float(params.get("pan_rate", 0.05))
    pan_lo = float(params.get("pan_lo", 0.25))
    pan_hi = float(params.get("pan_hi", 0.75))
    pan = slow_noise(duration, pan_rate, lo=pan_lo, hi=pan_hi, rng=rng, sr=sr)

    ang = pan * np.pi / 2.0
    ang_inv = (1.0 - pan) * np.pi / 2.0
    L = wind_env * (whoosh * np.cos(ang) + hiss_level * hiss * gust * np.cos(ang_inv))
    R = wind_env * (whoosh * np.sin(ang) + hiss_level * hiss * gust * np.sin(ang_inv))

    return AudioBuffer.from_stereo(L, R, sr=sr)


# ---------------------------------------------------------------------------
# Drone

DRONE_PARAMS = [
    ParamSchema("duration", "float", 60.0, lo=1.0, hi=600.0, unit="s"),
    ParamSchema("midi_root", "int", 26, lo=12, hi=48, label="Root MIDI (D1=26)"),
    ParamSchema("breath_depth", "float", 0.3, lo=0.0, hi=0.8),
    ParamSchema("breath_rate", "float", 0.012, lo=0.001, hi=0.1, unit="Hz"),
    ParamSchema("beat_detune", "float", 0.003, lo=0.0, hi=0.02,
                label="Beating detune (oct 3×)"),
]


def drone(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
    """Deep additive drone on root + overtones with slow amplitude breathing.

    Replicates the planetary drone from arrakis, spice_must_flow, and all dune tracks.
    Mono (same signal to L and R).
    """
    from forge.core.dsp import midi_to_hz

    sr = ctx.get("sr", SR)
    duration = float(params.get("duration", ctx.get("duration", 60.0)))
    n = int(duration * sr)
    t = np.arange(n, dtype=np.float64) / sr

    midi_root = int(params.get("midi_root", 26))
    f0 = midi_to_hz(midi_root)

    breath_depth = float(params.get("breath_depth", 0.30))
    breath_rate = float(params.get("breath_rate", 0.012))
    beat_det = float(params.get("beat_detune", 0.003))

    breath = (1.0 - breath_depth) + breath_depth * np.sin(2.0 * np.pi * breath_rate * t + 1.0)

    sig = (
        np.sin(2.0 * np.pi * f0 * t)
        + 0.55 * np.sin(2.0 * np.pi * f0 * 2 * t + 0.4)
        + 0.30 * np.sin(2.0 * np.pi * f0 * 3 * t)
        + 0.30 * np.sin(2.0 * np.pi * f0 * 3 * (1.0 + beat_det) * t)
    )
    sig *= breath
    return AudioBuffer.from_mono(sig, sr=sr)


# ---------------------------------------------------------------------------
# Dissonant swell (used in ambient/lost.py "dread" section)

SWELL_PARAMS = [
    ParamSchema("duration", "float", 30.0, lo=1.0, hi=120.0, unit="s"),
    ParamSchema("midi_notes", "choice", [62, 63, 65, 68, 70],
                label="Cluster MIDI notes"),
    ParamSchema("detune_cents", "float", 0.6, lo=0.0, hi=2.0, unit="%",
                label="Detune (%)"),
    ParamSchema("rolloff", "float", 1.0, lo=0.5, hi=2.0,
                label="Harmonic rolloff"),
    ParamSchema("n_harmonics", "int", 8, lo=1, hi=20),
    ParamSchema("wet", "float", 0.5, lo=0.0, hi=1.0, label="Reverb wet"),
]


def swell(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
    """Dissonant detuned string cluster — the 'Scream/dread' texture from lost.py.

    A dense cluster of detuned additive saws providing swirling tonal dissonance.
    """
    from forge.core.dsp import midi_to_hz
    from forge.core.reverb import make_stereo_ir_pair, reverb

    sr = ctx.get("sr", SR)
    duration = float(params.get("duration", ctx.get("duration", 30.0)))
    n = int(duration * sr)
    t = np.arange(n, dtype=np.float64) / sr

    notes = params.get("midi_notes", [62, 63, 65, 68, 70])
    detune_frac = float(params.get("detune_cents", 0.6)) / 100.0
    rolloff = float(params.get("rolloff", 1.0))
    n_harmonics = int(params.get("n_harmonics", 8))

    L = np.zeros(n)
    R = np.zeros(n)

    for i, m in enumerate(notes):
        f = midi_to_hz(m)
        det = 1.0 + detune_frac * (i - len(notes) / 2.0) / len(notes)
        ph = 2.0 * np.pi * f * det * t + rng.uniform(0, 2 * np.pi)
        voice = sum(np.sin(k * ph) / (k ** rolloff) for k in range(1, n_harmonics + 1))
        pan = i / max(len(notes) - 1, 1)
        L += voice * np.cos(pan * np.pi / 2.0)
        R += voice * np.sin(pan * np.pi / 2.0)

    wet = float(params.get("wet", 0.5))
    if wet > 0.0:
        ir_L, ir_R = make_stereo_ir_pair(3.0, 1.5, sr=sr)
        L = reverb(L, ir_L, wet=wet)
        R = reverb(R, ir_R, wet=wet)

    return AudioBuffer.from_stereo(L, R, sr=sr)
