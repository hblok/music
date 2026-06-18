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


# ---------------------------------------------------------------------------
# Worm Rumble (falling sub tone + lowpassed noise shake)

WORM_RUMBLE_PARAMS = [
    ParamSchema("duration", "float", 7.0, lo=1.0, hi=30.0, unit="s"),
    ParamSchema("f_start", "float", 55.0, lo=20.0, hi=120.0, unit="Hz",
                label="Start frequency (Hz)"),
    ParamSchema("f_end", "float", 27.0, lo=10.0, hi=80.0, unit="Hz",
                label="End frequency (Hz)"),
    ParamSchema("glide_rate", "float", 2.2, lo=0.1, hi=10.0, unit="1/s",
                label="Exponential glide rate"),
    ParamSchema("noise_level", "float", 0.6, lo=0.0, hi=1.5,
                label="Low-noise shake level"),
    ParamSchema("noise_cutoff", "float", 90.0, lo=20.0, hi=200.0, unit="Hz",
                label="Brown-noise LP cutoff"),
    ParamSchema("attack_rate", "float", 30.0, lo=5.0, hi=200.0, unit="1/s"),
    ParamSchema("decay_rate", "float", 0.9, lo=0.1, hi=5.0, unit="1/s"),
]


def worm_rumble(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
    """Sub-bass worm pass — falling glide tone + lowpassed brown-noise shake.

    Recipe from the rumble section of spice_must_flow.py and night_pursuit.py:
    a sine tone falling from ~55 Hz to ~27 Hz (exponential glide) forms the
    sub impact; a second layer of lowpassed brown noise (<90 Hz) provides the
    shake texture.  The combined envelope is a fast-attack / slow-decay shape.
    """
    from forge.core.dsp import lowpass as _lp

    sr = ctx.get("sr", SR)
    dur = float(params.get("duration", ctx.get("duration", 7.0)))
    f_start = float(params.get("f_start", 55.0))
    f_end = float(params.get("f_end", 27.0))
    glide_rate = float(params.get("glide_rate", 2.2))
    noise_level = float(params.get("noise_level", 0.6))
    noise_cutoff = float(params.get("noise_cutoff", 90.0))
    attack_rate = float(params.get("attack_rate", 30.0))
    decay_rate = float(params.get("decay_rate", 0.9))

    n = int(dur * sr)
    tt = np.arange(n, dtype=np.float64) / sr

    # falling sub glide: exponential frequency ramp
    f_curve = f_end + (f_start - f_end) * np.exp(-glide_rate * tt)
    phase = 2.0 * np.pi * np.cumsum(f_curve) / sr
    thump = np.sin(phase)

    # brown-noise shake layer (lowpassed far below 100 Hz)
    raw = rng.standard_normal(n)
    brown = np.cumsum(raw)
    brown -= np.linspace(brown[0], brown[-1], n)  # detrend
    shake = _lp(brown, noise_cutoff, order=4, sr=sr)
    shake_peak = np.max(np.abs(shake)) + 1e-12
    shake /= shake_peak

    # combined amplitude envelope: fast onset, slow exponential tail
    env = np.exp(-decay_rate * tt) * (1.0 - np.exp(-attack_rate * tt))

    sig = (thump + noise_level * shake) * env
    return AudioBuffer.from_mono(sig, sr=sr)


# ---------------------------------------------------------------------------
# Shepard Wind (perpetually rising/falling whistle voices)

SHEPARD_WIND_PARAMS = [
    ParamSchema("duration", "float", 30.0, lo=1.0, hi=300.0, unit="s"),
    ParamSchema("n_voices", "int", 8, lo=2, hi=16, label="Number of Shepard voices"),
    ParamSchema("f_lo", "float", 300.0, lo=80.0, hi=1000.0, unit="Hz",
                label="Spectral range bottom"),
    ParamSchema("octaves", "float", 4.0, lo=1.0, hi=6.0,
                label="Spectral range width (octaves)"),
    ParamSchema("traverse_time", "float", 36.0, lo=4.0, hi=180.0, unit="s",
                label="Time for one full octave traverse"),
    ParamSchema("pan_rate", "float", 0.111, lo=0.01, hi=1.0, unit="Hz",
                label="Coriolis pan rotation rate"),
    ParamSchema("fm_depth", "float", 0.018, lo=0.0, hi=0.1,
                label="Slow FM depth"),
    ParamSchema("fm_rate", "float", 0.8, lo=0.1, hi=4.0, unit="Hz",
                label="Slow FM rate"),
]


def shepard_wind(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
    """Shepard-tone wind — K voices on a wrapping spectral position.

    Recipe from ``sandstorm_coriolis.py``: N voices each occupy a fractional
    position in a log-frequency range [f_lo, f_lo * 2^octaves].  Each voice
    glides upward at the same rate (traverse_time seconds per full cycle) but
    starts at a different offset, so the ensemble appears to rise forever while
    individual voices wrap silently at the bottom (Shepard tone principle).

    The per-voice amplitude window is ``sin(π·p)^2`` (zero at both spectral
    edges) so the wrap is inaudible.  Slow FM adds roughness.  Stereo rotation
    (Coriolis pan) gives the twisting feel.
    """
    sr = ctx.get("sr", SR)
    dur = float(params.get("duration", ctx.get("duration", 30.0)))
    n_voices = int(params.get("n_voices", 8))
    f_lo = float(params.get("f_lo", 300.0))
    octaves = float(params.get("octaves", 4.0))
    t_trav = float(params.get("traverse_time", 36.0))
    pan_rate = float(params.get("pan_rate", 0.111))
    fm_depth = float(params.get("fm_depth", 0.018))
    fm_rate = float(params.get("fm_rate", 0.8))

    n = int(dur * sr)
    tt = np.arange(n, dtype=np.float64) / sr

    sh_L = np.zeros(n)
    sh_R = np.zeros(n)

    for k in range(n_voices):
        # spectral position: 0→1 wrapping with each voice offset by k/N
        p = np.mod(tt / t_trav + k / n_voices, 1.0)
        # log-frequency glide
        f_voice = f_lo * (2.0 ** (p * octaves))

        # slow random FM for roughness (deterministic via passed rng)
        fm_slow = slow_noise(dur, fm_rate, lo=-1.0, hi=1.0, rng=rng, sr=sr)
        f_voice = f_voice * (1.0 + fm_depth * fm_slow[:n])

        phase = 2.0 * np.pi * np.cumsum(f_voice) / sr
        # sine + first harmonic for whistle timbre
        voice = np.sin(phase) + 0.20 * np.sin(2 * phase)

        # amplitude window: silent at spectral edges (hides wrap)
        w = np.sin(np.pi * p) ** 2
        voice *= w

        # Coriolis pan: each voice rotates at its own phase
        pan_sig = 0.5 + 0.4 * np.sin(2.0 * np.pi * pan_rate * tt
                                       + 2.0 * np.pi * k / n_voices)
        sh_L += voice * np.cos(pan_sig * np.pi / 2.0)
        sh_R += voice * np.sin(pan_sig * np.pi / 2.0)

    # normalise
    peak = max(np.max(np.abs(sh_L)), np.max(np.abs(sh_R))) + 1e-12
    sh_L /= peak
    sh_R /= peak
    return AudioBuffer.from_stereo(sh_L, sh_R, sr=sr)


# ---------------------------------------------------------------------------
# Breath (stillsuit mask breathing — inhale then exhale)

BREATH_PARAMS = [
    ParamSchema("duration", "float", 2.5, lo=0.5, hi=8.0, unit="s"),
    ParamSchema("inhale_cutoff_lo", "float", 500.0, lo=100.0, hi=2000.0, unit="Hz"),
    ParamSchema("inhale_cutoff_hi", "float", 1600.0, lo=500.0, hi=6000.0, unit="Hz"),
    ParamSchema("exhale_cutoff_lo", "float", 250.0, lo=80.0, hi=1000.0, unit="Hz"),
    ParamSchema("exhale_cutoff_hi", "float", 900.0, lo=200.0, hi=3000.0, unit="Hz"),
    ParamSchema("inhale_level", "float", 0.9, lo=0.1, hi=2.0),
    ParamSchema("exhale_level", "float", 1.0, lo=0.1, hi=2.0),
    ParamSchema("inhale_centre", "float", 0.35, lo=0.1, hi=0.6,
                label="Inhale envelope centre (fraction of duration)"),
    ParamSchema("exhale_centre", "float", 0.72, lo=0.5, hi=0.9,
                label="Exhale envelope centre (fraction of duration)"),
]


def breath(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
    """Stillsuit breath cycle — one inhale then one exhale per call.

    Recipe from ``generate_stillsuit.py``:
    A single noise source is bandpassed twice (different passbands for the
    bright inhale vs the darker exhale).  Each phase has a Gaussian amplitude
    envelope centred at a fraction of the total duration.  The result is a
    close, dry, centred breathing sound suitable for inside-the-hood ambience.
    """
    from forge.core.dsp import bandpass as _bp

    sr = ctx.get("sr", SR)
    dur = float(params.get("duration", ctx.get("duration", 2.5)))
    inh_lo = float(params.get("inhale_cutoff_lo", 500.0))
    inh_hi = float(params.get("inhale_cutoff_hi", 1600.0))
    exh_lo = float(params.get("exhale_cutoff_lo", 250.0))
    exh_hi = float(params.get("exhale_cutoff_hi", 900.0))
    inh_level = float(params.get("inhale_level", 0.9))
    exh_level = float(params.get("exhale_level", 1.0))
    inh_centre = float(params.get("inhale_centre", 0.35))
    exh_centre = float(params.get("exhale_centre", 0.72))

    n = int(dur * sr)
    tt = np.arange(n, dtype=np.float64) / sr

    # shared noise source (same room air through two filters)
    raw = rng.standard_normal(n)
    br_in = _bp(raw, inh_lo, inh_hi, order=2, sr=sr)
    br_ex = _bp(raw, exh_lo, exh_hi, order=2, sr=sr)

    # Gaussian amplitude envelopes (σ ~= 15 % of duration)
    sigma = 0.15 * dur
    inh_env = np.exp(-0.5 * ((tt - inh_centre * dur) / sigma) ** 2)
    exh_env = np.exp(-0.5 * ((tt - exh_centre * dur) / sigma) ** 2)

    sig = inh_level * br_in * inh_env + exh_level * br_ex * exh_env
    return AudioBuffer.from_mono(sig, sr=sr)
