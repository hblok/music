"""forge.instruments.synth — synthesizer patches (saw-based brass stab, …).

Where `voices.lead` is a warm detuned-saw trance lead, these are brighter,
more aggressive synth voices. `synth_brass` is a sawtooth-stack **brass/organ
stab** with a resonant body formant and a thinned fundamental — the chunky
low stab heard in early-90s Italo house.

Phrase-level (a `notes` list) with per-note articulation, like
`reed.sax_phrase` / `voices.make_horn`.
"""

from __future__ import annotations

import numpy as np
from scipy import signal as _signal

from forge.core.buffer import AudioBuffer
from forge.core.dsp import bandpass, glide_curve, highpass, lowpass, raised_cosine_attack, warm_partials
from forge.instruments.base import ParamSchema

SR = 44100


# ---------------------------------------------------------------- Synth brass stab

SYNTH_BRASS_PARAMS = [
    ParamSchema("notes", "choice", [(61, 0.3)], label="Notes [(midi, dur_s)...]"),
    ParamSchema("midi", "int", 61, lo=24, hi=84,
                label="MIDI note (single-note shorthand)"),
    ParamSchema("duration", "float", 0.3, lo=0.05, hi=8.0, unit="s",
                label="Duration (single-note shorthand)"),
    ParamSchema("legato", "bool", False, label="Slur notes (no re-tongue)"),
    ParamSchema("n_voices", "int", 3, lo=1, hi=6, label="Detuned saw voices"),
    ParamSchema("detune", "float", 0.007, lo=0.0, hi=0.02,
                label="Voice detune (fraction)"),
    ParamSchema("n_harmonics", "int", 24, lo=6, hi=48),
    ParamSchema("rolloff", "float", 0.7, lo=0.6, hi=1.6,
                label="Saw rolloff exp (lower = brighter)"),
    ParamSchema("drive", "float", 2.0, lo=0.5, hi=4.0, label="Tanh drive (grit)"),
    ParamSchema("hp_cutoff", "float", 320.0, lo=40.0, hi=800.0, unit="Hz",
                label="Highpass — thins the fundamental"),
    ParamSchema("hp_order", "int", 3, lo=1, hi=6, label="Highpass slope"),
    ParamSchema("formant_hz", "float", 720.0, lo=300.0, hi=2500.0, unit="Hz",
                label="Body formant (the brass honk)"),
    ParamSchema("formant_q", "float", 1.3, lo=0.5, hi=4.0, label="Formant Q"),
    ParamSchema("formant_mix", "float", 1.4, lo=0.0, hi=3.0,
                label="Formant emphasis"),
    ParamSchema("formant2_hz", "float", 1750.0, lo=600.0, hi=4000.0, unit="Hz",
                label="2nd formant (brightness)"),
    ParamSchema("formant2_mix", "float", 0.4, lo=0.0, hi=2.0),
    ParamSchema("lp_cutoff", "float", 8500.0, lo=2000.0, hi=14000.0, unit="Hz"),
    ParamSchema("attack", "float", 0.065, lo=0.002, hi=0.2, unit="s"),
    ParamSchema("release", "float", 0.10, lo=0.02, hi=0.4, unit="s"),
    ParamSchema("bloom", "float", 0.6, lo=0.0, hi=1.0,
                label="Attack brightness bloom"),
    ParamSchema("bloom_cutoff", "float", 1300.0, lo=400.0, hi=4000.0, unit="Hz",
                label="Bloom onset lowpass cutoff"),
    ParamSchema("scoop", "float", 0.02, lo=0.0, hi=0.12,
                label="Pitch scoop into each note"),
    ParamSchema("width", "float", 0.35, lo=0.0, hi=1.0,
                label="Stereo spread of detuned voices"),
    ParamSchema("rasp", "float", 0.50, lo=0.0, hi=1.0,
                label="Breath/buzz rasp (harshness)"),
    ParamSchema("rasp_lo", "float", 1200.0, lo=300.0, hi=4000.0, unit="Hz",
                label="Rasp band low cut"),
    ParamSchema("rasp_hi", "float", 6500.0, lo=1000.0, hi=14000.0, unit="Hz",
                label="Rasp band high cut"),
]


def _stab_env(notes, n, sr, attack, release, legato):
    """Per-note articulation: fast attack + short release (tongued stabs)."""
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


def synth_brass(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
    """Sawtooth-stack brass/organ stab with a resonant body formant.

    Matched to the isolated lead stem of the Black Box "Strike It Up" intro
    (`inspiration/black_box/intro_report.md`): a bright spectrum (centroid
    ~2.5 kHz) with a **suppressed fundamental** and energy peaking around the
    5th–6th harmonic — i.e. a saw stack thinned by a highpass and lifted by an
    ~800 Hz resonant formant, not a mellow additive reed/horn.

    Recipe:
      1. `n_voices` detuned sawtooth voices (`warm_partials`, low `rolloff`).
      2. `tanh(drive)` waveshaping for the synth grit.
      3. Highpass (`hp_cutoff`) to thin the fundamental, then one or two
         `iirpeak` formants added back in for the brass honk.
      4. Bright lowpass; per-note stab articulation; slight detune-spread
         stereo width.

    Accepts a `notes` list of `(midi, dur_s)` pairs, or `midi` + `duration`.
    """
    sr = ctx.get("sr", SR)
    notes = params.get("notes", None)
    if not notes:
        notes = [(int(params.get("midi", 61)), float(params.get("duration", 0.3)))]

    legato = bool(params.get("legato", False))
    n_voices = int(params.get("n_voices", 3))
    detune = float(params.get("detune", 0.007))
    n_harmonics = int(params.get("n_harmonics", 24))
    rolloff = float(params.get("rolloff", 0.7))
    drive = float(params.get("drive", 2.0))
    hp_cutoff = float(params.get("hp_cutoff", 320.0))
    hp_order = int(params.get("hp_order", 3))
    formant_hz = float(params.get("formant_hz", 720.0))
    formant_q = float(params.get("formant_q", 1.3))
    formant_mix = float(params.get("formant_mix", 1.4))
    formant2_hz = float(params.get("formant2_hz", 1750.0))
    formant2_mix = float(params.get("formant2_mix", 0.4))
    lp_cutoff = float(params.get("lp_cutoff", 8500.0))
    attack = float(params.get("attack", 0.065))
    release = float(params.get("release", 0.10))
    bloom = float(params.get("bloom", 0.6))
    bloom_cutoff = float(params.get("bloom_cutoff", 1300.0))
    scoop = float(params.get("scoop", 0.02))
    width = float(params.get("width", 0.35))
    rasp = float(params.get("rasp", 0.50))
    rasp_lo = float(params.get("rasp_lo", 1200.0))
    rasp_hi = float(params.get("rasp_hi", 6500.0))

    total_dur = sum(d for _, d in notes)
    n = int(total_dur * sr)
    if n <= 0:
        return AudioBuffer.from_mono(np.zeros(1), sr=sr)

    f_curve = glide_curve(notes, n, tau=0.05 if legato else 0.012, sr=sr)

    # Per-note pitch scoop into each note.
    scoop_mult = np.ones(n)
    if scoop > 0.0:
        edge = 0.0
        for _m, dur in notes:
            a = int(edge * sr)
            sc_n = min(int(0.06 * sr), max(0, int(dur * sr)))
            if sc_n > 0:
                scoop_mult[a:a + sc_n] = (1.0 - scoop) + scoop * np.linspace(0.0, 1.0, sc_n)
            edge += dur

    detunings = (np.linspace(-detune, detune, n_voices) if n_voices > 1 else [0.0])

    def _shape(sig):
        sig = np.tanh(drive * sig) / np.tanh(drive)
        sig = highpass(sig, hp_cutoff, order=hp_order, sr=sr)   # thin the fundamental
        out = sig.copy()
        if formant_mix > 0.0:
            b, a = _signal.iirpeak(formant_hz, Q=formant_q, fs=sr)
            out = out + formant_mix * _signal.lfilter(b, a, sig)
        if formant2_mix > 0.0:
            b2, a2 = _signal.iirpeak(formant2_hz, Q=formant_q, fs=sr)
            out = out + formant2_mix * _signal.lfilter(b2, a2, sig)
        return lowpass(out, lp_cutoff, order=2, sr=sr)

    L = np.zeros(n)
    R = np.zeros(n)
    for i, det in enumerate(detunings):
        ph = 2.0 * np.pi * np.cumsum(f_curve * (1.0 + det) * scoop_mult) / sr
        voice = _shape(warm_partials(ph, n_harmonics=n_harmonics, rolloff=rolloff))
        pan = 0.5 + width * (det / (detune + 1e-12)) * 0.5 if n_voices > 1 else 0.5
        pan = float(np.clip(pan, 0.0, 1.0))
        L += voice * np.cos(pan * np.pi / 2.0)
        R += voice * np.sin(pan * np.pi / 2.0)

    # Brightness bloom: tone starts dark and opens up over the attack window.
    # xf ramps from 0→1 over n_bloom samples (ease-in); at xf=0 we use the
    # dark (lowpassed) signal, at xf=1 we use the full-bright signal.
    if bloom > 0.0:
        n_bloom = int(attack * sr)
        if n_bloom > 1 and n_bloom <= n:
            xf = np.ones(n)
            xf[:n_bloom] = np.linspace(0.0, 1.0, n_bloom) ** 2
            L_dark = lowpass(L, bloom_cutoff, order=2, sr=sr)
            R_dark = lowpass(R, bloom_cutoff, order=2, sr=sr)
            L = xf * L + (1.0 - xf) * ((1.0 - bloom) * L + bloom * L_dark)
            R = xf * R + (1.0 - xf) * ((1.0 - bloom) * R + bloom * R_dark)

    # Voiced rasp: amplitude-tracked bandpass noise adds brass/reed breath buzz.
    # Decorrelated L/R noise gives width without cancellation in mono.
    # The rasp is scaled relative to the tone's own peak so `rasp=1.0` would
    # contribute noise at the same level as the signal's peak — i.e. `rasp` is
    # a genuine mix fraction between tonal (0) and noisy (1).
    if rasp > 0.0:
        rasp_hi_clamped = min(rasp_hi, sr * 0.49)
        n_L = bandpass(rng.standard_normal(n), rasp_lo, rasp_hi_clamped, order=2, sr=sr)
        n_R = bandpass(rng.standard_normal(n), rasp_lo, rasp_hi_clamped, order=2, sr=sr)
        n_L /= np.max(np.abs(n_L)) + 1e-12
        n_R /= np.max(np.abs(n_R)) + 1e-12
        # Amplitude follower: smooth envelope shapes the noise so rasp tracks
        # the note attack/release.  Normalised to unit peak, then scaled by the
        # tone's own peak so the mix ratio stays constant regardless of L/R gain.
        tone_peak = max(np.max(np.abs(L)), np.max(np.abs(R))) + 1e-12
        amp_L = lowpass(np.abs(L), 80.0, order=2, sr=sr)
        amp_R = lowpass(np.abs(R), 80.0, order=2, sr=sr)
        amp_L = amp_L / (np.max(amp_L) + 1e-12) * tone_peak
        amp_R = amp_R / (np.max(amp_R) + 1e-12) * tone_peak
        L = L + rasp * n_L * amp_L
        R = R + rasp * n_R * amp_R

    env = _stab_env(notes, n, sr, attack, release, legato)
    L *= env
    R *= env
    peak = max(np.max(np.abs(L)), np.max(np.abs(R))) + 1e-12
    return AudioBuffer.from_stereo(L / peak, R / peak, sr=sr)
