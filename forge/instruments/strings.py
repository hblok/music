"""forge.instruments.strings — Karplus-Strong, felt piano, cello, pads.

Note-level instruments; all support the render cache.
"""

from __future__ import annotations

import numpy as np

from forge.core.buffer import AudioBuffer
from forge.core.dsp import bandpass, glide_curve, lowpass, midi_to_hz, raised_cosine_attack
from forge.instruments.base import ParamSchema

SR = 44100


# ---------------------------------------------------------------- Karplus-Strong pluck

KS_PARAMS = [
    ParamSchema("midi", "int", 62, lo=36, hi=96, label="MIDI note"),
    ParamSchema("duration", "float", 1.5, lo=0.1, hi=8.0, unit="s"),
    ParamSchema("damp", "float", 0.9955, lo=0.98, hi=0.9999),
    ParamSchema("lp_cutoff", "float", 4000.0, lo=500.0, hi=20000.0, unit="Hz",
                label="Pick LP"),
]


def karplus_strong(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
    """Warm plucked string via Karplus-Strong synthesis.

    The warm pick excitation is a noise burst low-passed at *lp_cutoff* (soft pick).
    Damping coefficient *damp* controls decay length.
    Cached per (midi, duration, damp, lp_cutoff).
    """
    sr = ctx.get("sr", SR)
    midi = int(params.get("midi", 62))
    dur = float(params.get("duration", 1.5))
    damp = float(params.get("damp", 0.9955))
    lp_cutoff = float(params.get("lp_cutoff", 4000.0))

    freq = midi_to_hz(midi)
    n = int(dur * sr)
    delay = max(1, int(sr / freq))

    # warm noise excitation
    noise = rng.standard_normal(delay)
    noise = lowpass(noise, lp_cutoff, order=2, sr=sr)
    noise /= np.max(np.abs(noise)) + 1e-12

    buf = np.zeros(n)
    buf[:delay] = noise
    for i in range(delay, n):
        buf[i] = damp * 0.5 * (buf[i - delay] + buf[i - delay + 1])

    return AudioBuffer.from_mono(buf, sr=sr)


# ---------------------------------------------------------------- Felt piano

PIANO_PARAMS = [
    ParamSchema("midi", "int", 62, lo=36, hi=96, label="MIDI note"),
    ParamSchema("duration", "float", 2.0, lo=0.2, hi=10.0, unit="s"),
    ParamSchema("detune", "float", 0.0003, lo=0.0, hi=0.002,
                label="String detune (frac)"),
    ParamSchema("inharmonicity", "float", 0.0002, lo=0.0, hi=0.002, label="B"),
    ParamSchema("n_partials", "int", 8, lo=2, hi=20),
    ParamSchema("lp_cutoff", "float", 3500.0, lo=800.0, hi=8000.0, unit="Hz"),
    ParamSchema("felt_thunk", "float", 0.08, lo=0.0, hi=0.3,
                label="Felt hammer thunk"),
]


def piano_note(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
    """Felt piano note: stretched-inharmonic partials, two detuned strings.

    Replicates the felt piano from ambient/lost.py and trance/lost_v3.py.
    """
    sr = ctx.get("sr", SR)
    midi = int(params.get("midi", 62))
    dur = float(params.get("duration", 2.0))
    detune_frac = float(params.get("detune", 0.0003))
    B = float(params.get("inharmonicity", 0.0002))
    n_partials = int(params.get("n_partials", 8))
    lp_cutoff = float(params.get("lp_cutoff", 3500.0))
    thunk_level = float(params.get("felt_thunk", 0.08))

    f0 = midi_to_hz(midi)
    n = int(dur * sr)
    tt = np.arange(n, dtype=np.float64) / sr

    sig = np.zeros(n)
    for string_detune in (-detune_frac, +detune_frac):
        for k in range(1, n_partials + 1):
            fk = f0 * (1.0 + string_detune) * k * np.sqrt(1.0 + B * k * k)
            gain = 1.0 / (k ** 1.3)
            sig += gain * np.sin(2.0 * np.pi * fk * tt)

    # felt hammer thunk: very short bandpassed noise at attack
    if thunk_level > 0:
        thunk_n = int(0.015 * sr)
        noise = rng.standard_normal(thunk_n)
        from scipy import signal as _sig
        sos = _sig.butter(2, [600.0, 3000.0], "bandpass", fs=sr, output="sos")
        thunk = _sig.sosfilt(sos, noise) * np.exp(-np.arange(thunk_n, dtype=np.float64) / thunk_n * 8)
        thunk_len = min(thunk_n, n)
        sig[:thunk_len] += thunk[:thunk_len] * thunk_level

    # soft felt lowpass
    sig = lowpass(sig, lp_cutoff, order=2, sr=sr)

    # envelope: soft attack then exponential decay
    attack_n = int(0.012 * sr)
    env = np.exp(-tt / (dur * 0.3 + 1e-12))
    env[:attack_n] *= raised_cosine_attack(attack_n)
    sig *= env

    return AudioBuffer.from_mono(sig, sr=sr)


# ---------------------------------------------------------------- Bowed cello line

CELLO_PARAMS = [
    ParamSchema("notes", "choice", [(62, 2.0)], label="Notes [(midi, dur_s)...]"),
    ParamSchema("lp_cutoff", "float", 1900.0, lo=500.0, hi=6000.0, unit="Hz"),
    ParamSchema("detune", "float", 0.0015, lo=0.0, hi=0.005),
    ParamSchema("vibrato_depth", "float", 0.004, lo=0.0, hi=0.02),
    ParamSchema("vibrato_rate", "float", 5.5, lo=3.0, hi=8.0, unit="Hz"),
    ParamSchema("n_harmonics", "int", 8, lo=2, hi=20),
]


def cello_line(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
    """Bowed cello: detuned additive saw + bandpassed bow noise + vibrato.

    *notes* is a list of (midi, duration_seconds) pairs, played sequentially.
    """
    sr = ctx.get("sr", SR)
    notes = params.get("notes", [(62, 2.0)])
    lp_cutoff = float(params.get("lp_cutoff", 1900.0))
    detune = float(params.get("detune", 0.0015))
    vib_depth = float(params.get("vibrato_depth", 0.004))
    vib_rate = float(params.get("vibrato_rate", 5.5))
    n_harmonics = int(params.get("n_harmonics", 8))

    total_dur = sum(d for _, d in notes)
    n = int(total_dur * sr)
    tt = np.arange(n, dtype=np.float64) / sr

    # frequency curve from notes (with glide)
    f_curve = glide_curve(notes, n, tau=0.08, sr=sr)
    vib = 1.0 + vib_depth * np.sin(2.0 * np.pi * vib_rate * tt) * np.clip(tt / 0.5, 0, 1)

    sig = np.zeros(n)
    for k in range(1, n_harmonics + 1):
        det = 1.0 + detune * (1 if k % 2 == 0 else -1)
        ph = 2.0 * np.pi * np.cumsum(f_curve * det * vib) / sr
        sig += np.sin(ph) / k

    # bow noise
    from scipy import signal as _sig
    sos_b = _sig.butter(4, [200.0, 2000.0], "bandpass", fs=sr, output="sos")
    bow = _sig.sosfilt(sos_b, rng.standard_normal(n)) * 0.12

    sig = (sig + bow)
    sig = lowpass(sig, lp_cutoff, order=2, sr=sr)

    # slow attack envelope
    attack_n = int(min(0.3 * sr, n // 4))
    env = np.ones(n)
    env[:attack_n] *= raised_cosine_attack(attack_n)
    env[-int(0.05 * sr):] *= np.linspace(1.0, 0.0, int(0.05 * sr))

    return AudioBuffer.from_mono(sig * env, sr=sr)


# ---------------------------------------------------------------- Pad chord

PAD_PARAMS = [
    ParamSchema("midi_notes", "choice", [62, 66, 69], label="Chord MIDI notes"),
    ParamSchema("duration", "float", 4.0, lo=0.5, hi=20.0, unit="s"),
    ParamSchema("attack", "float", 2.5, lo=0.1, hi=8.0, unit="s"),
    ParamSchema("release", "float", 3.0, lo=0.1, hi=8.0, unit="s"),
    ParamSchema("lp_cutoff", "float", 2000.0, lo=400.0, hi=8000.0, unit="Hz"),
    ParamSchema("detune", "float", 0.0012, lo=0.0, hi=0.005),
]


def pad_chord(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
    """Detuned saw-stack sustained chord with slow attack/release envelope."""
    sr = ctx.get("sr", SR)
    notes = params.get("midi_notes", [62, 66, 69])
    dur = float(params.get("duration", 4.0))
    attack = float(params.get("attack", 2.5))
    release = float(params.get("release", 3.0))
    lp_cutoff = float(params.get("lp_cutoff", 2000.0))
    detune = float(params.get("detune", 0.0012))

    n = int(dur * sr)
    tt = np.arange(n, dtype=np.float64) / sr

    sig = np.zeros(n)
    for i, m in enumerate(notes):
        f = midi_to_hz(m)
        det = 1.0 + detune * (i - len(notes) / 2.0)
        for k in (1, 3, 5, 7):
            sig += np.sin(2.0 * np.pi * f * det * k * tt) / k

    sig = lowpass(sig, lp_cutoff, order=2, sr=sr)

    # attack/release envelope
    n_att = min(int(attack * sr), n)
    n_rel = min(int(release * sr), n)
    env = np.ones(n)
    env[:n_att] = raised_cosine_attack(n_att)
    env[-n_rel:] = np.cos(np.pi * np.arange(n_rel) / (2 * n_rel))

    # gentle stereo detune
    det2 = 1.0 + detune * 0.7
    sig_R = np.zeros(n)
    for i, m in enumerate(notes):
        f = midi_to_hz(m) * det2
        for k in (1, 3, 5, 7):
            sig_R += np.sin(2.0 * np.pi * f * k * tt) / k
    sig_R = lowpass(sig_R, lp_cutoff, order=2, sr=sr)

    return AudioBuffer.from_stereo(sig * env, sig_R * env, sr=sr)


# ---------------------------------------------------------------- Tremolo strings

TREMOLO_STRINGS_PARAMS = [
    ParamSchema("midi_notes", "choice", [57, 62, 63],
                label="Chord MIDI notes"),
    ParamSchema("duration", "float", 4.0, lo=0.5, hi=30.0, unit="s"),
    ParamSchema("tremolo_hz", "float", 11.0, lo=4.0, hi=20.0, unit="Hz",
                label="Tremolo rate"),
    ParamSchema("tremolo_depth", "float", 0.95, lo=0.2, hi=1.0,
                label="Tremolo depth (1=silence→peak)"),
    ParamSchema("attack", "float", 1.0, lo=0.1, hi=6.0, unit="s"),
    ParamSchema("detune", "float", 0.0045, lo=0.0, hi=0.015,
                label="Detuning (fraction)"),
    ParamSchema("lp_cutoff", "float", 2600.0, lo=400.0, hi=8000.0, unit="Hz"),
    ParamSchema("n_harmonics", "int", 6, lo=1, hi=12),
]


def tremolo_strings(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
    """Tremolo string section — detuned saw stack with rapid gain oscillation.

    Recipe from ``generate_stillsuit.py``: detuned saw voices (3 detuning
    offsets per note) through a bandpass filter; separate 10–11 Hz tremolo
    LFOs on L and R (slightly different rates for 'wobble') that touch near-
    silence each cycle; slow attack.

    DISTINCT from ``pad_chord``: the tremolo reaches near-zero gain on each
    cycle, giving a flickering string quality rather than a sustained wash.
    """
    sr = ctx.get("sr", SR)
    notes = params.get("midi_notes", [57, 62, 63])
    dur = float(params.get("duration", 4.0))
    tremolo_hz = float(params.get("tremolo_hz", 11.0))
    tremolo_depth = float(params.get("tremolo_depth", 0.95))
    attack = float(params.get("attack", 1.0))
    detune = float(params.get("detune", 0.0045))
    lp_cutoff = float(params.get("lp_cutoff", 2600.0))
    n_harmonics = int(params.get("n_harmonics", 6))

    n = int(dur * sr)
    tt = np.arange(n, dtype=np.float64) / sr

    sig_L = np.zeros(n)
    sig_R = np.zeros(n)

    for i, midi in enumerate(notes):
        f = midi_to_hz(midi)
        g_note = 1.0 - 0.1 * i / max(len(notes) - 1, 1)
        for j, det in enumerate((-detune, 0.0, detune)):
            # initial random phase for each voice
            ph_offset = rng.uniform(0.0, 2.0 * np.pi)
            ph = 2.0 * np.pi * f * (1.0 + det) * tt + ph_offset
            saw = sum(np.sin(k * ph) / k for k in range(1, n_harmonics + 1))
            # pan voices: inner notes centre, detuned voices spread
            pan = 0.5 + 0.35 * det / (detune + 1e-12)
            pan = float(np.clip(pan, 0.0, 1.0))
            sig_L += g_note * saw * np.cos(pan * np.pi / 2.0)
            sig_R += g_note * saw * np.sin(pan * np.pi / 2.0)

    # bandpass to remove extreme lows and harsh highs
    sig_L = bandpass(sig_L, 180.0, lp_cutoff, order=2, sr=sr)
    sig_R = bandpass(sig_R, 180.0, lp_cutoff, order=2, sr=sr)

    # Haas width: small time offset on R for stereo breadth
    haas = int(0.011 * sr)
    sig_R = np.roll(sig_R, haas)

    # tremolo: separate rates L/R, depth parameter, touches near-silence
    lo_gain = 1.0 - tremolo_depth
    trem_L = (lo_gain + (1.0 - lo_gain) * np.sin(np.pi * tremolo_hz * tt) ** 2)
    # slightly different rate for R (the stillsuit recipe uses 10.4 and 10.9)
    trem_R = (lo_gain + (1.0 - lo_gain) * np.sin(np.pi * (tremolo_hz + 0.5) * tt + 1.3) ** 2)
    sig_L *= trem_L
    sig_R *= trem_R

    # slow attack
    n_att = min(int(attack * sr), n)
    env = np.ones(n)
    env[:n_att] = raised_cosine_attack(n_att)

    sig_L *= env
    sig_R *= env

    # normalise peak to ~1 (before external gain staging)
    peak = max(np.max(np.abs(sig_L)), np.max(np.abs(sig_R))) + 1e-12
    sig_L /= peak
    sig_R /= peak

    return AudioBuffer.from_stereo(sig_L, sig_R, sr=sr)


# ---------------------------------------------------------------- Santur (hammered dulcimer)

SANTUR_PARAMS = [
    ParamSchema("midi", "int", 62, lo=36, hi=96, label="MIDI note"),
    ParamSchema("duration", "float", 2.0, lo=0.1, hi=8.0, unit="s"),
    ParamSchema("detune", "float", 0.0015, lo=0.0, hi=0.01,
                label="String pair detune (fraction)"),
    ParamSchema("damp", "float", 0.997, lo=0.98, hi=0.9999,
                label="KS damping"),
    ParamSchema("decay_rate", "float", 1.6, lo=0.2, hi=8.0, unit="1/s",
                label="Exponential decay rate"),
]


def santur(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
    """Hammered santur (dulcimer) — two-course Karplus-Strong struck strings.

    Recipe from ``santur_note`` in spice_must_flow.py:
    Two strings per course at ±*detune* fraction; the excitation is a 2-tap
    smoothed noise burst (hammer blow, not a pick) rather than a single-tap
    lowpassed noise; fast exponential decay envelope simulates the struck
    character.
    """
    sr = ctx.get("sr", SR)
    midi = int(params.get("midi", 62))
    dur = float(params.get("duration", 2.0))
    detune = float(params.get("detune", 0.0015))
    damp = float(params.get("damp", 0.997))
    decay_rate = float(params.get("decay_rate", 1.6))

    freq = midi_to_hz(midi)
    n = int(dur * sr)
    tt = np.arange(n, dtype=np.float64) / sr
    out = np.zeros(n)

    for det, g in [(1.0 - detune, 1.0), (1.0 + detune, 0.85)]:
        period = max(2, int(round(sr / (freq * det))))
        # hammer excitation: short normal noise, 2-tap smoothed (not pick-LP)
        buf = rng.standard_normal(period)
        buf = np.convolve(buf, np.ones(2) / 2.0, mode="same")

        # run KS loop for the full duration
        ks_out = np.zeros(n)
        ks_out[:period] = buf[:min(period, n)]
        for i in range(period, n):
            prev = ks_out[i - period]
            nxt_idx = i - period + 1
            nxt = ks_out[nxt_idx] if nxt_idx < i else 0.0
            ks_out[i] = damp * 0.5 * (prev + nxt)

        out += g * ks_out

    # exponential decay envelope (struck character, not plucked sustain)
    decay_env = np.exp(-decay_rate * tt) * np.clip((dur - tt) / 0.1, 0.0, 1.0)
    out *= decay_env

    peak = np.max(np.abs(out)) + 1e-12
    out /= peak
    return AudioBuffer.from_mono(out, sr=sr)


# ---------------------------------------------------------------- Oud (plucked lute)

OUD_PARAMS = [
    ParamSchema("midi", "int", 62, lo=36, hi=84, label="MIDI note"),
    ParamSchema("duration", "float", 0.55, lo=0.1, hi=4.0, unit="s"),
    ParamSchema("detune", "float", 0.004, lo=0.0, hi=0.01,
                label="Double-course detune (fraction)"),
    ParamSchema("damp", "float", 0.4985, lo=0.48, hi=0.5,
                label="KS damping coefficient"),
    ParamSchema("bp_lo", "float", 200.0, lo=50.0, hi=800.0, unit="Hz",
                label="Body bandpass lo"),
    ParamSchema("bp_hi", "float", 4200.0, lo=1000.0, hi=8000.0, unit="Hz",
                label="Body bandpass hi"),
]


def oud(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
    """Plucked oud — Karplus-Strong double-course with oud body bandpass.

    Recipe from ``oud_note`` in fall_of_arrakeen.py:
    Two strings per course (double-course instrument); uniform noise excitation
    (not lowpassed pick — gives the characteristic thin-then-bloomy oud attack);
    a 200–4200 Hz bandpass models the pear-shaped resonant body; fast tail
    release clips.
    """
    sr = ctx.get("sr", SR)
    midi = int(params.get("midi", 62))
    dur = float(params.get("duration", 0.55))
    detune = float(params.get("detune", 0.004))
    damp = float(params.get("damp", 0.4985))
    bp_lo = float(params.get("bp_lo", 200.0))
    bp_hi = float(params.get("bp_hi", 4200.0))

    freq = midi_to_hz(midi)
    n = int(dur * sr)
    tt = np.arange(n, dtype=np.float64) / sr
    out = np.zeros(n)

    for det in (1.0, 1.0 + detune):
        f_det = freq * det
        period = max(2, int(sr / f_det))
        # uniform noise excitation — characteristic oud pick (no LP)
        buf = rng.uniform(-1.0, 1.0, period)

        idx = 0
        ks = np.zeros(n)
        for i in range(n):
            ks[i] = buf[idx]
            nxt = (idx + 1) % period
            buf[idx] = damp * (buf[idx] + buf[nxt])
            idx = nxt

        out += ks

    # body resonance: pear-shaped cavity bandpass
    out = bandpass(out, bp_lo, bp_hi, order=2, sr=sr)

    # fast tail release (the oud's plucked decay)
    release_n = min(int(0.04 * sr), n)
    release_env = np.ones(n)
    release_env[-release_n:] = np.linspace(1.0, 0.0, release_n)
    out *= release_env

    peak = np.max(np.abs(out)) + 1e-12
    out /= peak
    return AudioBuffer.from_mono(out, sr=sr)
