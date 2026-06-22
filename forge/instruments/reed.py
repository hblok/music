"""forge.instruments.reed — single-reed aerophones (saxophone, …).

Reed instruments couple a vibrating cane reed to a conical/cylindrical bore.
The synthesis recipe here is: a rich all-harmonic source (the buzzing reed)
shaped by tanh waveshaping, then coloured by a body **formant** resonance —
the trick that separates a sax's vocal "honk" from a plain saw lead.

Phrase-level: like ``voices.make_horn`` / ``voices.voice_phrase``, these take a
``notes`` list and render a whole melodic line in one buffer, with per-note
tonguing (articulation) and a delayed vibrato bloom.
"""

from __future__ import annotations

import numpy as np
from scipy import signal as _signal

from forge.core.buffer import AudioBuffer
from forge.core.dsp import bandpass, glide_curve, lowpass, midi_to_hz, raised_cosine_attack
from forge.instruments.base import ParamSchema

SR = 44100


# ---------------------------------------------------------------- Alto saxophone

SAX_PARAMS = [
    ParamSchema("notes", "choice", [(68, 1.0)], label="Notes [(midi, dur_s)...]"),
    ParamSchema("midi", "int", 68, lo=44, hi=84,
                label="MIDI note (single-note shorthand)"),
    ParamSchema("duration", "float", 1.0, lo=0.1, hi=8.0, unit="s",
                label="Duration (single-note shorthand)"),
    ParamSchema("legato", "bool", False, label="Slur notes (no re-tongue)"),
    ParamSchema("n_harmonics", "int", 16, lo=4, hi=28),
    ParamSchema("bright", "float", 0.95, lo=0.4, hi=1.4,
                label="Harmonic rolloff exponent (lower = brighter)"),
    ParamSchema("reed", "float", 1.4, lo=0.5, hi=4.0,
                label="Reed buzz (tanh drive)"),
    ParamSchema("formant_hz", "float", 1050.0, lo=600.0, hi=2200.0, unit="Hz",
                label="Body formant centre (alto 'honk')"),
    ParamSchema("formant_q", "float", 1.4, lo=0.5, hi=4.0, label="Formant Q"),
    ParamSchema("formant_mix", "float", 0.55, lo=0.0, hi=1.5,
                label="Formant emphasis"),
    ParamSchema("lp_cutoff", "float", 3800.0, lo=1500.0, hi=12000.0, unit="Hz"),
    ParamSchema("breath_level", "float", 0.05, lo=0.0, hi=0.3,
                label="Continuous breath noise"),
    ParamSchema("chiff", "float", 0.14, lo=0.0, hi=0.5,
                label="Reed-speak chiff at each onset"),
    ParamSchema("vibrato_depth", "float", 0.005, lo=0.0, hi=0.02),
    ParamSchema("vibrato_rate", "float", 5.4, lo=3.0, hi=8.0, unit="Hz"),
    ParamSchema("vibrato_bloom", "float", 0.8, lo=0.1, hi=3.0, unit="s",
                label="Vibrato onset delay (straight attack)"),
    ParamSchema("attack", "float", 0.025, lo=0.005, hi=0.2, unit="s"),
    ParamSchema("release", "float", 0.08, lo=0.02, hi=0.5, unit="s"),
    ParamSchema("scoop", "float", 0.03, lo=0.0, hi=0.15,
                label="Pitch scoop into each note (fraction flat)"),
]


def _articulation_env(notes, n, sr, attack, release, legato):
    """Per-note amplitude envelope.

    Tongued (legato=False): every note gets a raised-cosine attack and a short
    linear release, so notes are detached/re-articulated.  Legato: only the
    first note attacks and only the last note releases; the level rides through
    the interior note boundaries unbroken.
    """
    env = np.zeros(n)
    edge = 0.0
    last = len(notes) - 1
    for idx, (_m, dur) in enumerate(notes):
        a = int(edge * sr)
        seg_n = min(int(dur * sr), n - a)
        if seg_n <= 0:
            edge += dur
            continue
        seg = np.ones(seg_n)
        att_n = 0 if (legato and idx > 0) else min(int(attack * sr), seg_n)
        if att_n > 0:
            seg[:att_n] = raised_cosine_attack(att_n)
        rel_n = 0 if (legato and idx < last) else min(int(release * sr), seg_n - att_n)
        if rel_n > 0:
            seg[-rel_n:] *= np.linspace(1.0, 0.0, rel_n)
        env[a:a + seg_n] = seg
        edge += dur
    return env


def sax_phrase(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
    """Alto saxophone — reed-buzz harmonic source through a body formant.

    Modelled on the Black Box "Strike It Up" intro analysis
    (``inspiration/black_box/intro_report.md``): a near-pure harmonic tone with
    spectral energy peaking around the 2nd harmonic, a vocal body formant near
    1 kHz, a straight attack with vibrato blooming in only on the sustain, and a
    soft reed-speak chiff at each onset.

    Recipe:
      1. Harmonic stack (``1/k**bright``) with a boosted 2nd harmonic — the
         alto's centroid sits on the 2nd partial, not the fundamental.
      2. ``tanh(reed * x)`` waveshaping for the buzzing reed edge.
      3. A peaking ``iirpeak`` body formant (``formant_hz``) added back in — the
         sax "honk" that no plain saw lead has.
      4. Bandpassed breath: a low continuous bed plus a decaying chiff burst at
         each note onset (the reed starting to speak).
      5. Per-note tonguing envelope; phrase-global vibrato bloom.

    Accepts a ``notes`` list of ``(midi, dur_s)`` pairs, or a single
    ``midi`` + ``duration`` shorthand.
    """
    sr = ctx.get("sr", SR)
    notes = params.get("notes", None)
    if not notes:
        notes = [(int(params.get("midi", 68)), float(params.get("duration", 1.0)))]

    legato = bool(params.get("legato", False))
    n_harmonics = int(params.get("n_harmonics", 16))
    bright = float(params.get("bright", 0.95))
    reed = float(params.get("reed", 1.4))
    formant_hz = float(params.get("formant_hz", 1050.0))
    formant_q = float(params.get("formant_q", 1.4))
    formant_mix = float(params.get("formant_mix", 0.55))
    lp_cutoff = float(params.get("lp_cutoff", 3800.0))
    breath_level = float(params.get("breath_level", 0.05))
    chiff = float(params.get("chiff", 0.14))
    vib_depth = float(params.get("vibrato_depth", 0.005))
    vib_rate = float(params.get("vibrato_rate", 5.4))
    vib_bloom = float(params.get("vibrato_bloom", 0.8))
    attack = float(params.get("attack", 0.025))
    release = float(params.get("release", 0.08))
    scoop = float(params.get("scoop", 0.03))

    total_dur = sum(d for _, d in notes)
    n = int(total_dur * sr)
    if n <= 0:
        return AudioBuffer.from_mono(np.zeros(1), sr=sr)
    tt = np.arange(n, dtype=np.float64) / sr

    # Pitch curve: short glide (legato slur) or near-instant note jumps.
    f_curve = glide_curve(notes, n, tau=0.06 if legato else 0.012, sr=sr)

    # Per-note pitch scoop: start each note a touch flat, bloom up in ~80 ms.
    scoop_mult = np.ones(n)
    if scoop > 0.0:
        edge = 0.0
        for _m, dur in notes:
            a = int(edge * sr)
            sc_n = min(int(0.08 * sr), max(0, int(dur * sr)))
            if sc_n > 0:
                scoop_mult[a:a + sc_n] = (1.0 - scoop) + scoop * np.linspace(0.0, 1.0, sc_n)
            edge += dur

    # Vibrato blooms in after vib_bloom seconds (straight attack, like a player).
    vib = 1.0 + vib_depth * np.sin(2.0 * np.pi * vib_rate * tt) * np.clip(tt / vib_bloom, 0.0, 1.0)

    phase = 2.0 * np.pi * np.cumsum(f_curve * vib * scoop_mult) / sr

    # Harmonic stack with the alto's 2nd-harmonic emphasis.
    tone = np.zeros(n)
    for k in range(1, n_harmonics + 1):
        g = 1.0 / (k ** bright)
        if k == 2:
            g *= 1.35
        tone += g * np.sin(k * phase)
    tone /= np.max(np.abs(tone)) + 1e-12

    # Reed buzz: tanh waveshaping adds the cane's edge and upper partials.
    tone = np.tanh(reed * tone) / np.tanh(reed)

    # Body formant resonance — the sax "honk".
    if formant_mix > 0.0:
        b, a = _signal.iirpeak(formant_hz, Q=formant_q, fs=sr)
        tone = tone + formant_mix * _signal.lfilter(b, a, tone)

    # Breath: continuous air bed + per-onset reed-speak chiff.
    if breath_level > 0.0 or chiff > 0.0:
        air = bandpass(rng.standard_normal(n), 1500.0, 5000.0, order=2, sr=sr)
        air /= np.max(np.abs(air)) + 1e-12
        chiff_env = np.zeros(n)
        if chiff > 0.0:
            edge = 0.0
            for _m, dur in notes:
                a = int(edge * sr)
                ch_n = min(int(0.05 * sr), n - a)
                if ch_n > 0:
                    chiff_env[a:a + ch_n] = np.exp(-np.linspace(0.0, 1.0, ch_n) * 6.0)
                edge += dur
        tone = tone + breath_level * air + chiff * air * chiff_env

    tone = lowpass(tone, lp_cutoff, order=2, sr=sr)

    sig = tone * _articulation_env(notes, n, sr, attack, release, legato)
    sig /= np.max(np.abs(sig)) + 1e-12
    return AudioBuffer.from_mono(sig, sr=sr)
