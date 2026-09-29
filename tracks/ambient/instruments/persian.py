"""Persian / Arabic ambient renderers -- C Phrygian Dominant (Maqam Hijaz).

Extracted from `persian_opus.py` (canonical, unsuffixed names) and
`persian.py` ("qasida", `*_qasida` names where it differs); both scripts
are unchanged.  Unlike the dune/trance/psy libraries these are NOT
standalone DSP: the scripts are thin recipes over the **forge**
instruments (`forge.instruments.{voices,strings,bass,percussion,textures}`),
and the value here is the tuned parameter sets + reverb/bed treatment.  So
this module imports forge (repo root is put on sys.path, as the scripts do).
There is consequently little overlap with `tracks/dune/instruments`
(`duduk_ney`, `strings`, `darbuka`, `frame_drum` are separate standalone
implementations of similar instruments; not merged).

Signatures: the scripts' `render_*(rng: RngContext, ...)` took a forge
`RngContext` and spawned sub-streams from it.  Here the RngContext is
replaced by a module-level seeded `rng = np.random.default_rng(...)` (the
dune convention); a caller wanting per-layer reproducibility can reseed
`persian.rng`.  Everything else -- parameter dicts, reverb wet levels,
tails -- is verbatim.  Returns are (N,) mono or (N, 2) stereo as in the
originals (see each docstring).

Sources (public name <- script:function):
  render_drone <- persian_opus:render_drone (mono sub drone, hard LP 300 Hz;
    the "felt floor" rewrite), render_air <- persian_opus:render_air,
  render_pad, render_choir, render_ney, render_oud_phrase, render_santur_run,
  render_bass_hit, render_darbuka_bar (fill= bars), render_riq_hit
    <- persian_opus (riq is opus-only),
  render_drone_qasida, render_wind_qasida, render_pad_qasida,
  render_ney_qasida, render_santur_run_qasida, render_darbuka_bar_qasida
    <- persian:render_* (the earlier, brighter/louder parameter sets;
    `render_choir`, `render_oud_phrase` and `render_bass_hit` are identical
    in both scripts, so there is only one).
Not peak-normalized: like the scripts, the renderers return raw levels (peaks up to ~2.6) and rely on the final `master()`; the audition allows peak <= 3.0.
Not extracted: `compose()` / `main()` (arrangement), `_edge_fade`, gains.
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from forge.core.dsp import lowpass, midi_to_hz, slow_noise
from forge.core.reverb import make_reverb_ir, reverb
from forge.instruments.bass import psy_bass_note
from forge.instruments.percussion import make_doum, make_frame_hit, make_tek
from forge.instruments.strings import oud, pad_chord, santur
from forge.instruments.textures import drone, wind
from forge.instruments.voices import choir, voice_phrase

from _common import run_audition

SR = 44100
BPM = 96
BEAT = 60.0 / BPM
BAR = 4 * BEAT
STEP = BEAT / 4

rng = np.random.default_rng(42)          # persian*.py compose(seed=42)

# -- C Phrygian Dominant, MIDI (suffix = octave)
C1 = 24
C2, Db2, E2, F2, G2, Ab2, Bb2 = 36, 37, 40, 41, 43, 44, 46
C3, Db3, E3, F3, G3, Ab3, Bb3 = 48, 49, 52, 53, 55, 56, 58
C4, Db4, E4, F4, G4, Ab4, Bb4 = 60, 61, 64, 65, 67, 68, 70
C5, Db5, E5, F5, G5 = 72, 73, 76, 77, 79

IR_ROOM_L = make_reverb_ir(1.8, 1.4, seed=3, sr=SR)
IR_ROOM_R = make_reverb_ir(1.8, 1.4, seed=5, sr=SR)
IR_HALL_L = make_reverb_ir(2.6, 2.1, seed=7, sr=SR)
IR_HALL_R = make_reverb_ir(2.6, 2.1, seed=11, sr=SR)

# -- material the renderers read (persian_opus.py)
PAD_NOTES = [C4, G4, Bb4]
CHOIR_NOTES = [C3, G3, Bb3]
SANTUR_PITCHES = [C4, Db4, E4, F4, G4, Ab4, Bb4, C5]
DOUM_STEPS = {0: 0.95, 3: 0.40, 6: 0.55, 8: 0.70, 11: 0.35}
TEK_STEPS = {4: 0.70, 10: 0.50, 12: 0.70}
GHOST_STEPS = {2: 0.20, 7: 0.24, 14: 0.30, 15: 0.22}
FILL_TEKS = {9: 0.45, 13: 0.45, 14: 0.40, 15: 0.55}      # added on fill bars
THEME_INTRO = [(C4, 3.0), (Db4, 1.5), (E4, 2.5), (Db4, 1.25), (C4, 4.0)]
OUD_TURN = [
    (G3, 0.0, 1.2), (Ab3, 0.5, 1.2), (G3, 1.0, 1.2), (F3, 1.6, 1.2),
    (E3, 2.2, 1.4), (Db3, 2.9, 1.5), (C3, 3.7, 3.0),
]

# -- material the *_qasida renderers read (persian.py)
_PAD_NOTES = [C4, G4, Bb4]
_CHOIR_NOTES = [C3, G3, Bb3]
_SANTUR_PITCHES = [C4, E4, G4, Ab4, Bb4, C5]
_DOUM_STEPS = {0: 0.85, 6: 0.55, 8: 0.70}
_TEK_STEPS = {4: 0.70, 12: 0.65}
_GHOST_STEPS = {14: 0.28}


def render_drone(dur: float, root_midi: int = C1) -> np.ndarray:
    """Deep, dark, slowly-evolving modal drone — the safe replacement.

    • Energy lives in the sub (root) and fundamental (octave); upper partials
      are gentle and the whole thing is HARD low-passed at 300 Hz, so no mid
      tone is ever exposed as an alarm.
    • Amplitude breathes from two layered slow-noise envelopes at different
      slow rates (irregular) — never a fixed beat, so it never reads as
      repetitive, and it never drops out (it is a drone).
    Returns (N,) mono for a solid, centred low end.
    """
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float64) / SR
    f0 = midi_to_hz(root_midi)
    r = rng

    sig = (
        1.00 * np.sin(2.0 * np.pi * f0 * 1 * t)        # sub (C1 ≈ 33 Hz)
        + 0.85 * np.sin(2.0 * np.pi * f0 * 2 * t)       # fundamental (C2 ≈ 65 Hz)
        + 0.22 * np.sin(2.0 * np.pi * f0 * 3 * t)       # gentle
        + 0.12 * np.sin(2.0 * np.pi * f0 * 4 * t)       # gentle
    )

    # organic breathing — two slow, irregular envelopes (NOT a fixed LFO beat)
    b1 = slow_noise(dur, 0.035, lo=0.0, hi=1.0, rng=r, power=1.4, sr=SR)
    b2 = slow_noise(dur, 0.011, lo=0.0, hi=1.0, rng=r, power=1.0, sr=SR)
    sig *= 0.45 + 0.35 * b1 + 0.20 * b2

    # dark: keep it deep, kill anything that could pierce
    sig = lowpass(sig, 300.0, order=4, sr=SR)
    return sig


def render_air(dur: float) -> np.ndarray:
    """Gentle dark desert air — wind with the hiss removed and low-passed.

    Used only at the intro/outro (with fades), never as a constant bed.
    """
    ab = wind(
        {"duration": dur, "whoosh_lo": 60.0, "whoosh_hi": 320.0,
         "hiss_level": 0.0,            # ← the 2–7 kHz "tinnitus" band, gone
         "gust_rate": 0.10, "gust_power": 2.4, "swell_rate": 0.05,
         "pan_rate": 0.04, "pan_lo": 0.38, "pan_hi": 0.62},
        rng, sr=SR,
    )
    d = ab.data
    d[:, 0] = lowpass(d[:, 0], 450.0, order=2, sr=SR)
    d[:, 1] = lowpass(d[:, 1], 450.0, order=2, sr=SR)
    return d


def _breath(dur: float, rng: np.random.Generator,
            lo: float = 0.55, hi: float = 1.0,
            rate: float = 0.03, power: float = 1.2) -> np.ndarray:
    """Slow irregular amplitude envelope in [lo, hi]; keeps sustained layers alive."""
    bn = slow_noise(dur, rate, lo=0.0, hi=1.0, rng=rng, power=power, sr=SR)
    return lo + (hi - lo) * bn


def render_pad(dur: float) -> np.ndarray:
    """Sustained detuned-saw modal pad (dark), with slow breathing so it never
    becomes a flat wall.  Returns (N,2)."""
    ab = pad_chord(
        {"midi_notes": PAD_NOTES, "duration": dur,
         "attack": 6.0, "release": 8.0, "lp_cutoff": 1200.0, "detune": 0.0016},
        rng, sr=SR,
    )
    env = _breath(dur, rng, lo=0.5, hi=1.0, rate=0.025, power=1.3)
    ab.data[:, 0] *= env
    ab.data[:, 1] *= env
    return ab.data


def render_choir(dur: float, notes=CHOIR_NOTES) -> np.ndarray:
    """Choir swell ("oo") with hall reverb; returns (N,2)."""
    tail_s = 3.0
    ab = choir(
        {"midi_notes": notes, "vowel": "oo", "duration": dur,
         "detune": 0.003, "n_harmonics": 8},
        rng, sr=SR,
    )
    L, R = ab.data[:, 0], ab.data[:, 1]
    padL = np.concatenate([L, np.zeros(int(tail_s * SR))])
    padR = np.concatenate([R, np.zeros(int(tail_s * SR))])
    outL = reverb(padL, IR_HALL_L, wet=0.45)[:len(L)]
    outR = reverb(padR, IR_HALL_R, wet=0.45)[:len(R)]
    return np.column_stack([outL, outR])


def render_ney(phrase: list) -> np.ndarray:
    """One ney phrase (breathy, dark) with room reverb; returns (N,2)."""
    tail_s = 2.5
    ab = voice_phrase(
        {"notes": phrase, "ney_mode": True, "breath_level": 0.10,
         "vibrato_depth": 0.006, "vibrato_rate": 5.5, "vibrato_bloom": 1.5,
         "lp_cutoff": 1900.0, "n_harmonics": 4},
        rng, sr=SR,
    )
    mono = (ab.data[:, 0] + ab.data[:, 1]) * 0.5
    padded = np.concatenate([mono, np.zeros(int(tail_s * SR))])
    L = reverb(padded, IR_ROOM_L, wet=0.36)[:len(mono)]
    R = reverb(padded, IR_ROOM_R, wet=0.36)[:len(mono)]
    return np.column_stack([L, R])


def render_oud_phrase(phrase: list) -> np.ndarray:
    """Overlapping oud plucks assembled into one stereo array with room reverb."""
    total = max(t + d for _, t, d in phrase) + 1.0
    n = int(total * SR)
    buf = np.zeros(n)
    r = rng
    for midi, t_off, dur in phrase:
        ab = oud({"midi": midi, "duration": dur, "detune": 0.004, "damp": 0.499},
                 r, sr=SR)
        note = (ab.data[:, 0] + ab.data[:, 1]) * 0.5
        i0 = int(t_off * SR)
        end = min(i0 + len(note), n)
        buf[i0:end] += note[:end - i0]
    padded = np.concatenate([buf, np.zeros(int(2.0 * SR))])
    L = reverb(padded, IR_ROOM_L, wet=0.32)[:n]
    R = reverb(padded, IR_ROOM_R, wet=0.32)[:n]
    return np.column_stack([L, R])


def render_santur_run() -> np.ndarray:
    """Ascending ornamental santur run (staggered); returns (N,2)."""
    r = rng
    stagger = 0.32
    n = int((len(SANTUR_PITCHES) * stagger + 1.6) * SR)
    buf = np.zeros(n)
    pos = 0.0
    for midi in SANTUR_PITCHES:
        ab = santur({"midi": midi, "duration": 1.5, "detune": 0.0015,
                     "damp": 0.997, "decay_rate": 1.8}, r, sr=SR)
        mono = (ab.data[:, 0] + ab.data[:, 1]) * 0.5
        i0 = int(pos * SR)
        end = min(i0 + len(mono), n)
        buf[i0:end] += mono[:end - i0]
        pos += stagger
    padded = np.concatenate([buf, np.zeros(int(2.0 * SR))])
    L = reverb(padded, IR_ROOM_L, wet=0.40)[:n]
    R = reverb(padded, IR_ROOM_R, wet=0.40)[:n]
    return np.column_stack([L, R])


def render_bass_hit(midi: int) -> np.ndarray:
    """Single warm psy sub-bass note; returns (N,) mono."""
    ab = psy_bass_note({"midi": midi, "duration": 0.55, "decay_mult": 5.0},
                       rng, sr=SR)
    return (ab.data[:, 0] + ab.data[:, 1]) * 0.5


def render_darbuka_bar(fill: bool = False,
                       humanise: float = 0.012) -> np.ndarray:
    """One bar of Maqsum-inspired darbuka (humanised); returns (N,) mono."""
    n = int(BAR * SR)
    buf = np.zeros(n)
    r = rng

    def place(mono, step, vel):
        t = step * STEP + r.uniform(-humanise, humanise)
        i0 = max(0, int(t * SR))
        end = min(i0 + len(mono), n)
        buf[i0:end] += mono[:end - i0] * vel

    for step, vel in DOUM_STEPS.items():
        ab = make_doum({"f0": 140.0, "f1": 80.0, "duration": 0.45}, r, sr=SR)
        place((ab.data[:, 0] + ab.data[:, 1]) * 0.5, step, vel)
    teks = dict(TEK_STEPS)
    if fill:
        teks.update(FILL_TEKS)
    for step, vel in teks.items():
        ab = make_tek({"ghost": False, "duration": 0.18}, r, sr=SR)
        place((ab.data[:, 0] + ab.data[:, 1]) * 0.5, step, vel)
    for step, vel in GHOST_STEPS.items():
        ab = make_tek({"ghost": True, "duration": 0.18}, r, sr=SR)
        place((ab.data[:, 0] + ab.data[:, 1]) * 0.5, step, vel)
    return buf


def render_riq_hit() -> np.ndarray:
    """Light frame-drum/riq accent (kept dark, low); returns (N,) mono."""
    ab = make_frame_hit({"f0": 320.0, "duration": 0.18}, rng, sr=SR)
    return ab.L


def render_drone_qasida(dur: float) -> np.ndarray:
    """Sub-bass drone on C2; returns (N,2) stereo array."""
    ab = drone(
        {"duration": dur, "midi_root": C2, "breath_depth": 0.25,
         "breath_rate": 0.008, "beat_detune": 0.002},
        rng, sr=SR,
    )
    return ab.data


def render_wind_qasida(dur: float) -> np.ndarray:
    """Atmospheric wind noise; returns (N,2)."""
    ab = wind(
        {"duration": dur, "whoosh_lo": 80.0, "whoosh_hi": 600.0,
         "hiss_level": 0.15, "gust_rate": 0.18, "swell_rate": 0.07},
        rng, sr=SR,
    )
    return ab.data


def render_pad_qasida(dur: float) -> np.ndarray:
    """Sustained detuned-saw pad chord; returns (N,2). No reverb (too long)."""
    ab = pad_chord(
        {"midi_notes": _PAD_NOTES, "duration": dur,
         "attack": 4.0, "release": 6.0, "lp_cutoff": 1600.0, "detune": 0.0015},
        rng, sr=SR,
    )
    return ab.data


def render_ney_qasida(phrase: list) -> np.ndarray:
    """Single ney phrase with room reverb; returns (N,) mono."""
    tail_s = 2.5
    ab = voice_phrase(
        {"notes": phrase, "ney_mode": True, "breath_level": 0.12,
         "vibrato_depth": 0.005, "vibrato_rate": 5.0, "vibrato_bloom": 1.5,
         "lp_cutoff": 2000.0, "n_harmonics": 4},
        rng, sr=SR,
    )
    mono = (ab.data[:, 0] + ab.data[:, 1]) * 0.5
    padded = np.concatenate([mono, np.zeros(int(tail_s * SR))])
    L = reverb(padded, IR_ROOM_L, wet=0.38)[:len(mono)]
    R = reverb(padded, IR_ROOM_R, wet=0.38)[:len(mono)]
    return np.column_stack([L, R])


def render_santur_run_qasida() -> np.ndarray:
    """Ascending ornamental run; returns stereo (N,2)."""
    r = rng
    buf = None
    pos = 0
    for midi in _SANTUR_PITCHES:
        ab = santur(
            {"midi": midi, "duration": 1.4, "detune": 0.0015,
             "damp": 0.997, "decay_rate": 1.8},
            r, sr=SR,
        )
        mono = (ab.data[:, 0] + ab.data[:, 1]) * 0.5
        if buf is None:
            buf = np.zeros(int((len(_SANTUR_PITCHES) * 0.35 + 1.4) * SR))
        i0 = int(pos * SR)
        end = min(i0 + len(mono), len(buf))
        buf[i0:end] += mono[:end - i0]
        pos += 0.35  # stagger

    tail_s = 2.0
    padded = np.concatenate([buf, np.zeros(int(tail_s * SR))])
    L = reverb(padded, IR_ROOM_L, wet=0.40)[:len(buf)]
    R = reverb(padded, IR_ROOM_R, wet=0.40)[:len(buf)]
    return np.column_stack([L, R])


def render_darbuka_bar_qasida(humanise: float = 0.01) -> np.ndarray:
    """One bar of Maqsum-inspired darbuka; returns (N,) mono."""
    n = int(BAR * SR)
    buf = np.zeros(n)
    r = rng
    for step, vel in _DOUM_STEPS.items():
        ab = make_doum({"f0": 140.0, "f1": 80.0, "duration": 0.45, "gain": vel},
                       r, sr=SR)
        mono = (ab.data[:, 0] + ab.data[:, 1]) * 0.5
        t = step * STEP + r.uniform(-humanise, humanise)
        i0 = max(0, int(t * SR))
        end = min(i0 + len(mono), n)
        buf[i0:end] += mono[:end - i0]
    for step, vel in _TEK_STEPS.items():
        ab = make_tek({"ghost": False, "duration": 0.18}, r, sr=SR)
        mono = (ab.data[:, 0] + ab.data[:, 1]) * 0.5 * vel
        t = step * STEP + r.uniform(-humanise, humanise)
        i0 = max(0, int(t * SR))
        end = min(i0 + len(mono), n)
        buf[i0:end] += mono[:end - i0]
    for step, vel in _GHOST_STEPS.items():
        ab = make_tek({"ghost": True, "duration": 0.18}, r, sr=SR)
        mono = (ab.data[:, 0] + ab.data[:, 1]) * 0.5 * vel
        t = step * STEP + r.uniform(-humanise, humanise)
        i0 = max(0, int(t * SR))
        end = min(i0 + len(mono), n)
        buf[i0:end] += mono[:end - i0]
    return buf


AUDITION = [
    ("render_drone 6s", lambda: render_drone(6.0)),
    ("render_air 4s", lambda: render_air(4.0)),
    ("render_pad 8s", lambda: render_pad(8.0)),
    ("render_choir 6s", lambda: render_choir(6.0)),
    ("render_ney intro", lambda: render_ney(THEME_INTRO)),
    ("render_oud_phrase turn", lambda: render_oud_phrase(OUD_TURN)),
    ("render_santur_run", lambda: render_santur_run()),
    ("render_bass_hit C2", lambda: render_bass_hit(C2)),
    ("render_darbuka_bar", lambda: render_darbuka_bar()),
    ("render_darbuka_bar fill", lambda: render_darbuka_bar(fill=True)),
    ("render_riq_hit", lambda: render_riq_hit()),
    ("render_drone_qasida 6s", lambda: render_drone_qasida(6.0)),
    ("render_wind_qasida 4s", lambda: render_wind_qasida(4.0)),
    ("render_pad_qasida 8s", lambda: render_pad_qasida(8.0)),
    ("render_ney_qasida", lambda: render_ney_qasida(THEME_INTRO)),
    ("render_santur_run_qasida", lambda: render_santur_run_qasida()),
    ("render_darbuka_bar_qasida", lambda: render_darbuka_bar_qasida()),
]

if __name__ == "__main__":
    run_audition("persian", AUDITION, max_peak=3.0)
