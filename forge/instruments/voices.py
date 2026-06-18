"""forge.instruments.voices — duduk/ney melodic voice, choir, flute, lead.

All voices are phrase-level instruments (they accept a sequence of notes and
render the whole phrase as one buffer).  They use the glide_curve IIR smoother
for portamento between notes.
"""

from __future__ import annotations

import numpy as np
from scipy import signal as _signal

from forge.core.buffer import AudioBuffer
from forge.core.dsp import bandpass, glide_curve, lowpass, midi_to_hz
from forge.instruments.base import ParamSchema

SR = 44100


# ---------------------------------------------------------------- Duduk / ney voice

VOICE_PARAMS = [
    ParamSchema("notes", "choice", [(62, 1.5)], label="Notes [(midi, dur_s)...]"),
    ParamSchema("lp_cutoff", "float", 2200.0, lo=800.0, hi=6000.0, unit="Hz"),
    ParamSchema("n_harmonics", "int", 5, lo=1, hi=12),
    ParamSchema("vibrato_depth", "float", 0.006, lo=0.0, hi=0.03),
    ParamSchema("vibrato_rate", "float", 5.2, lo=3.0, hi=8.0, unit="Hz"),
    ParamSchema("vibrato_bloom", "float", 1.2, lo=0.3, hi=3.0, unit="s"),
    ParamSchema("ney_mode", "bool", False, label="Ney (add breath noise)"),
    ParamSchema("breath_level", "float", 0.08, lo=0.0, hi=0.4),
]


def voice_phrase(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
    """Duduk/ney-like melodic phrase: additive harmonics + portamento + vibrato.

    Replicates ``voice_phrase``/``ney_phrase`` present in 6+ legacy scripts.
    The ``ney_mode=True`` variant adds more breath noise (breathy flute character).
    """
    sr = ctx.get("sr", SR)
    notes = params.get("notes", [(62, 1.5)])
    lp_cutoff = float(params.get("lp_cutoff", 2200.0))
    n_harmonics = int(params.get("n_harmonics", 5))
    vib_depth = float(params.get("vibrato_depth", 0.006))
    vib_rate = float(params.get("vibrato_rate", 5.2))
    vib_bloom = float(params.get("vibrato_bloom", 1.2))
    ney_mode = bool(params.get("ney_mode", False))
    breath_level = float(params.get("breath_level", 0.08))

    total_dur = sum(d for _, d in notes)
    n = int(total_dur * sr)
    tt = np.arange(n, dtype=np.float64) / sr

    f_curve = glide_curve(notes, n, tau=0.09, sr=sr)
    vib = 1.0 + vib_depth * np.sin(2.0 * np.pi * vib_rate * tt) * np.clip(tt / vib_bloom, 0, 1)

    sig = np.zeros(n)
    gains = [1.0, 0.40, 0.18, 0.07, 0.04]
    for k in range(1, n_harmonics + 1):
        g = gains[k - 1] if k <= len(gains) else (0.02 / k)
        ph = 2.0 * np.pi * np.cumsum(f_curve * vib * k) / sr
        sig += g * np.sin(ph)

    if ney_mode or breath_level > 0:
        breath = rng.standard_normal(n)
        breath = lowpass(breath, lp_cutoff * 0.6, order=2, sr=sr)
        breath /= np.max(np.abs(breath)) + 1e-12
        sig += breath_level * breath

    sig = lowpass(sig, lp_cutoff, order=2, sr=sr)

    # phrase envelope: smooth ramp from each note onset to offset
    env = np.minimum(
        np.clip(tt / 1.5, 0.0, 1.0),
        np.clip((total_dur - tt) / 2.0, 0.0, 1.0),
    ) ** 1.5

    return AudioBuffer.from_mono(sig * env, sr=sr)


# ---------------------------------------------------------------- Choir

CHOIR_PARAMS = [
    ParamSchema("midi_notes", "choice", [62, 65, 69], label="Chord MIDI notes"),
    ParamSchema("vowel", "choice", "oo", choices=["oo", "ah"],
                label="Vowel formant"),
    ParamSchema("duration", "float", 4.0, lo=0.5, hi=20.0, unit="s"),
    ParamSchema("detune", "float", 0.003, lo=0.0, hi=0.01),
    ParamSchema("n_harmonics", "int", 8, lo=2, hi=16),
]

_FORMANTS = {
    "oo": [(320, 40.0, 1.0), (800, 80.0, 0.5), (2700, 200.0, 0.3)],
    "ah": [(800, 80.0, 1.0), (1200, 100.0, 0.8), (2500, 200.0, 0.6)],
}


def choir(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
    """Choir pad: glottal source through vowel formant bandpasses, polytonal.

    Replicates the choir from ambient/lost.py.  Polytonal note stacking for
    the dread section reads as anguish.
    """
    sr = ctx.get("sr", SR)
    notes = params.get("midi_notes", [62, 65, 69])
    vowel = str(params.get("vowel", "oo"))
    dur = float(params.get("duration", 4.0))
    detune = float(params.get("detune", 0.003))
    n_harmonics = int(params.get("n_harmonics", 8))

    n = int(dur * sr)
    tt = np.arange(n, dtype=np.float64) / sr
    formants = _FORMANTS.get(vowel, _FORMANTS["oo"])

    from scipy import signal as _sig

    L = np.zeros(n)
    R = np.zeros(n)

    for i, m in enumerate(notes):
        f0 = midi_to_hz(m) * (1.0 + detune * (i - len(notes) / 2.0) / len(notes))
        # glottal source: 1/k^0.9 spectrum
        glottal = sum(np.sin(2.0 * np.pi * f0 * k * tt) / (k ** 0.9)
                      for k in range(1, n_harmonics + 1))

        # apply each formant
        voiced = np.zeros(n)
        for f_c, bw, g in formants:
            q = f_c / bw
            sos = _sig.iirpeak(f_c, Q=max(q, 0.5), fs=sr)
            voiced += g * _sig.sosfilt(
                np.array(sos).reshape(1, 6) if np.array(sos).ndim == 1 else np.array(sos),
                glottal
            )

        pan = i / max(len(notes) - 1, 1)
        L += voiced * np.cos(pan * np.pi / 2.0)
        R += voiced * np.sin(pan * np.pi / 2.0)

    # slow attack
    attack_n = min(int(1.0 * sr), n // 4)
    env = np.ones(n)
    env[:attack_n] = 0.5 - 0.5 * np.cos(np.pi * np.arange(attack_n) / attack_n)
    L *= env
    R *= env

    return AudioBuffer.from_stereo(L, R, sr=sr)


# ---------------------------------------------------------------- Lead phrase (trance warmth recipe)

LEAD_PARAMS = [
    ParamSchema("notes", "choice", [(62, 0.5)], label="Notes [(midi, dur_s)...]"),
    ParamSchema("lp_cutoff", "float", 2800.0, lo=500.0, hi=8000.0, unit="Hz"),
    ParamSchema("rolloff", "float", 1.3, lo=1.0, hi=2.0,
                label="Harmonic rolloff"),
    ParamSchema("drive", "float", 0.8, lo=0.1, hi=3.0),
    ParamSchema("sub_mix", "float", 0.3, lo=0.0, hi=0.8),
    ParamSchema("detune_lo", "float", 0.996, lo=0.99, hi=1.0),
    ParamSchema("detune_hi", "float", 1.004, lo=1.0, hi=1.01),
    ParamSchema("n_voices", "int", 3, lo=1, hi=5, label="Detuned voices"),
]


def lead_phrase(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
    """Detuned saw-stack lead — trance warmth recipe applied.

    Implements the lead_phrase from trance/lost_v3.py / lost_v4.py with the
    warmth fixes documented in trance/CLAUDE.md.
    """
    sr = ctx.get("sr", SR)
    notes = params.get("notes", [(62, 0.5)])
    lp_cutoff = float(params.get("lp_cutoff", 2800.0))
    rolloff = float(params.get("rolloff", 1.3))
    drive = float(params.get("drive", 0.8))
    sub_mix = float(params.get("sub_mix", 0.3))
    detune_lo = float(params.get("detune_lo", 0.996))
    detune_hi = float(params.get("detune_hi", 1.004))
    n_voices = int(params.get("n_voices", 3))

    total_dur = sum(d for _, d in notes)
    n = int(total_dur * sr)
    tt = np.arange(n, dtype=np.float64) / sr

    f_curve = glide_curve(notes, n, tau=0.05, sr=sr)

    detunings = np.linspace(detune_lo, detune_hi, n_voices) if n_voices > 1 else [1.0]

    sig_L = np.zeros(n)
    sig_R = np.zeros(n)
    for i, det in enumerate(detunings):
        ph = 2.0 * np.pi * np.cumsum(f_curve * det) / sr
        from forge.core.dsp import warm_partials
        voice = np.tanh(drive * warm_partials(ph, rolloff=rolloff, sub_mix=sub_mix))
        pan = i / max(len(detunings) - 1, 1)
        sig_L += voice * np.cos(pan * np.pi / 2.0)
        sig_R += voice * np.sin(pan * np.pi / 2.0)

    sig_L = lowpass(sig_L, lp_cutoff, order=2, sr=sr)
    sig_R = lowpass(sig_R, lp_cutoff, order=2, sr=sr)

    # bloom-in attack
    attack_n = min(int(0.2 * sr), n)
    from forge.core.dsp import raised_cosine_attack
    env_att = raised_cosine_attack(attack_n)
    env = np.ones(n)
    env[:attack_n] = env_att

    return AudioBuffer.from_stereo(sig_L * env, sig_R * env, sr=sr)


# ---------------------------------------------------------------- Ney (breathy flute)

NEY_PARAMS = [
    ParamSchema("midi", "int", 62, lo=48, hi=84, label="MIDI note"),
    ParamSchema("duration", "float", 1.5, lo=0.2, hi=8.0, unit="s"),
    ParamSchema("breath_level", "float", 0.13, lo=0.0, hi=0.5,
                label="Breath noise level"),
    ParamSchema("lp_cutoff", "float", 3200.0, lo=800.0, hi=8000.0, unit="Hz"),
    ParamSchema("vibrato_depth", "float", 0.004, lo=0.0, hi=0.02),
    ParamSchema("vibrato_rate", "float", 6.0, lo=3.0, hi=10.0, unit="Hz"),
    ParamSchema("vibrato_bloom", "float", 0.8, lo=0.2, hi=2.0, unit="s"),
]


def make_ney(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
    """Breathy ney flute — additive harmonics at 1 / 0.25 / 0.08 + breath noise.

    Recipe from ``ney_phrase`` in maker_comes.py / fall_of_arrakeen.py: nearly
    pure tone (mostly fundamental with thin upper partials) plus bandpassed
    breath noise in the 1.2–4 kHz range; faster and shallower vibrato than the
    duduk; brighter lowpass.

    *midi* and *duration* define a single held note.
    """
    sr = ctx.get("sr", SR)
    midi = int(params.get("midi", 62))
    dur = float(params.get("duration", 1.5))
    breath_level = float(params.get("breath_level", 0.13))
    lp_cutoff = float(params.get("lp_cutoff", 3200.0))
    vib_depth = float(params.get("vibrato_depth", 0.004))
    vib_rate = float(params.get("vibrato_rate", 6.0))
    vib_bloom = float(params.get("vibrato_bloom", 0.8))

    n = int(dur * sr)
    tt = np.arange(n, dtype=np.float64) / sr

    f0 = midi_to_hz(midi)
    vib = 1.0 + vib_depth * np.sin(2.0 * np.pi * vib_rate * tt) * np.clip(tt / vib_bloom, 0, 1)

    # integrate phase for all three partials at once
    ph_base = 2.0 * np.pi * np.cumsum(np.full(n, f0) * vib) / sr
    tone = np.sin(ph_base) + 0.25 * np.sin(2 * ph_base) + 0.08 * np.sin(3 * ph_base)

    # breath noise: bandpassed in upper mid (the air through the embouchure)
    raw_noise = rng.standard_normal(n)
    breath = bandpass(raw_noise, 1200.0, 4000.0, order=2, sr=sr)
    breath_peak = np.max(np.abs(breath)) + 1e-12
    breath /= breath_peak

    sig = tone + breath_level * breath

    # smooth envelope: quicker attack, shorter tail than the duduk
    env = np.minimum(
        np.clip(tt / 0.6, 0.0, 1.0),
        np.clip((dur - tt) / 1.5, 0.0, 1.0),
    ) ** 1.3

    sig = lowpass(sig * env, lp_cutoff, order=2, sr=sr)
    return AudioBuffer.from_mono(sig, sr=sr)


# ---------------------------------------------------------------- Sardaukar Chant

CHANT_PARAMS = [
    ParamSchema("midi", "int", 38, lo=24, hi=60, label="MIDI note (throat pitch)"),
    ParamSchema("duration", "float", 1.5, lo=0.2, hi=8.0, unit="s"),
    ParamSchema("pulse_rate", "float", 5.5, lo=2.0, hi=12.0, unit="Hz",
                label="Glottal pulse rate"),
    ParamSchema("n_harmonics", "int", 14, lo=4, hi=20),
    ParamSchema("sub_level", "float", 0.40, lo=0.0, hi=1.0,
                label="Sub-octave level"),
]


def make_chant(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
    """Sardaukar throat chant — pulsed glottal source through 3 formant bands.

    Recipe from ``chant_note`` in maker_comes.py / fall_of_arrakeen.py:
    14 harmonics (1/k^0.8 rolloff) with random per-harmonic phase; three
    parallel bandpass formants (380–560 Hz, 750–1000 Hz, 2200–2700 Hz);
    amplitude pulse at *pulse_rate* Hz for the guttural flutter; sub-octave
    sine for throat-singing weight.
    """
    sr = ctx.get("sr", SR)
    midi = int(params.get("midi", 38))
    dur = float(params.get("duration", 1.5))
    pulse_rate = float(params.get("pulse_rate", 5.5))
    n_harmonics = int(params.get("n_harmonics", 14))
    sub_level = float(params.get("sub_level", 0.40))

    f = midi_to_hz(midi)
    n = int(dur * sr)
    td = np.arange(n, dtype=np.float64) / sr

    # glottal source: harmonics with random phase
    src = np.zeros(n)
    for k in range(1, n_harmonics + 1):
        ph = rng.uniform(0.0, 2.0 * np.pi)
        src += np.sin(2.0 * np.pi * k * f * td + ph) / (k ** 0.8)

    # three formant bandpasses
    formants = [
        ([380, 560], 1.0),
        ([750, 1000], 0.6),
        ([2200, 2700], 0.15),
    ]
    out = np.zeros(n)
    for (lo_f, hi_f), g in formants:
        out += g * bandpass(src, lo_f, hi_f, order=2, sr=sr)

    peak = np.max(np.abs(out)) + 1e-12
    out /= peak

    # glottal amplitude pulse
    out *= 0.75 + 0.25 * np.sin(2.0 * np.pi * pulse_rate * td)

    # sub-octave for throat-singing weight
    out += sub_level * np.sin(2.0 * np.pi * 0.5 * f * td)

    # sharp attack, short release envelope
    env = np.minimum(
        np.clip(td / 0.06, 0.0, 1.0),
        np.clip((dur - td) / 0.15, 0.0, 1.0),
    ) ** 1.2

    sig = out * env
    sig_peak = np.max(np.abs(sig)) + 1e-12
    sig /= sig_peak

    return AudioBuffer.from_mono(sig, sr=sr)


# ---------------------------------------------------------------- Horn (carnyx / war horn)

HORN_PARAMS = [
    ParamSchema("notes", "choice", [(50, 1.0)], label="Notes [(midi, dur_s)...]"),
    ParamSchema("duration", "float", 1.5, lo=0.2, hi=8.0, unit="s",
                label="Total duration (for single-note shorthand)"),
    ParamSchema("growl", "float", 0.18, lo=0.0, hi=0.6,
                label="AM growl depth (31 Hz)"),
    ParamSchema("lp_cutoff", "float", 1600.0, lo=400.0, hi=4000.0, unit="Hz"),
    ParamSchema("n_harmonics", "int", 12, lo=2, hi=20),
    ParamSchema("scoop", "float", 0.06, lo=0.0, hi=0.2,
                label="Pitch scoop (fraction below target)"),
]


def make_horn(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
    """Carnyx / war horn — brassy harmonic stack with growl AM.

    Recipe from ``horn_phrase`` in fall_of_arrakeen.py:
    12 harmonics (1/k^0.7 rolloff); pitch scoops up 6 % at the attack;
    31 Hz amplitude modulation for the growl; lowpass + formant bump at
    450–900 Hz.  Accepts either a ``notes`` list or a single ``midi``+
    ``duration`` pair.
    """
    sr = ctx.get("sr", SR)
    notes = params.get("notes", None)
    growl = float(params.get("growl", 0.18))
    lp_cutoff = float(params.get("lp_cutoff", 1600.0))
    n_harmonics = int(params.get("n_harmonics", 12))
    scoop_depth = float(params.get("scoop", 0.06))

    # normalise to notes list
    if notes is None:
        midi = int(params.get("midi", 50))
        dur = float(params.get("duration", 1.5))
        notes = [(midi, dur)]

    total_dur = sum(d for _, d in notes) + 1.2
    n = int(total_dur * sr)
    tt = np.arange(n, dtype=np.float64) / sr

    f_curve = glide_curve(notes, n, tau=0.09, sr=sr)

    # pitch scoop into the note (starts 6 % flat, blooms to 100 % in 0.15 s)
    scoop_env = 1.0 - scoop_depth + scoop_depth * np.clip(tt / 0.15, 0, 1)
    phase = 2.0 * np.pi * np.cumsum(f_curve * scoop_env) / sr

    # harmonic stack with 1/k^0.7 rolloff
    tone = np.zeros(n)
    for k in range(1, n_harmonics + 1):
        tone += np.sin(k * phase) / (k ** 0.7)

    # AM growl
    tone *= 1.0 + growl * np.sin(2.0 * np.pi * 31.0 * tt)

    # overall amplitude envelope
    env = np.minimum(
        np.clip(tt / 0.10, 0.0, 1.0) ** 0.8,
        np.clip((total_dur - tt) / 1.0, 0.0, 1.0),
    )
    tone *= env

    # lowpass + formant bump
    out = lowpass(tone, lp_cutoff, order=2, sr=sr)
    out += 0.6 * bandpass(tone, 450.0, 900.0, order=2, sr=sr)

    peak = np.max(np.abs(out)) + 1e-12
    out /= peak
    return AudioBuffer.from_mono(out, sr=sr)
