"""forge.instruments.voices — duduk/ney melodic voice, choir, flute, lead.

All voices are phrase-level instruments (they accept a sequence of notes and
render the whole phrase as one buffer).  They use the glide_curve IIR smoother
for portamento between notes.
"""

from __future__ import annotations

import numpy as np

from forge.core.buffer import AudioBuffer
from forge.core.dsp import glide_curve, lowpass, midi_to_hz
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
