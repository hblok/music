"""
Persian / Arabic ambient trance — "Qasida (Opus)" — inspired by
Persian_Trance_LdGhQaBCbcE.mp3 and reworked from ambient/persian.py.

C Phrygian Dominant (Maqam Hijaz / Dastgah Homayoun): C D♭ E F G A♭ B♭
96 BPM · 192 bars · 480 s ≈ 8 minutes

────────────────────────────────────────────────────────────────────────────
WHAT CHANGED vs. persian.py — and WHY
────────────────────────────────────────────────────────────────────────────
The old track's background "drone" read as a tinnitus-inducing alarm.  The
cause was specific and measurable: forge's stock ``drone()`` builds its 3rd
harmonic from *two* sines a hair apart (beat_detune), so on C2 you got a
~196 Hz tone — the LOUDEST partial (combined amp 0.60, above the fundamental's
weighting) — pulsing every ~2.55 s, committed at gain 0.45 for the full 8 min
with no low-pass and no reverb.  A bare, exposed, never-changing, *pulsing*
mid tone = an alarm.  The stock ``wind()`` added a constant 2–7 kHz hiss band
on top.

The fix here is a purpose-built bed:
  • DRONE — energy concentrated in the sub (C1) + fundamental (C2); upper
    partials gentle and HARD low-passed at 300 Hz so no mid tone is ever
    exposed; amplitude breathes from layered slow-noise (irregular, multi-rate)
    instead of a fixed beat, so it never reads as repetitive; ~⅓ the old level.
  • AIR — replaces "wind": hiss band removed entirely, dark (≤320 Hz whoosh,
    low-passed at 450 Hz), very low gain, and present ONLY in the intro/outro
    with fades — not a constant wall.

Everything else is a richer, cohesive rebuild per the analysis: one recurring
hijaz theme (the C–D♭–E augmented-second cell) stated in every section, one
modal centre with the analysis's brief drone-shift to the fifth (G), one
reused instrument set; sections differ by density/dynamics, not by language.
The mix stays dark and bass-heavy to match the source (centroid ≈ 961 Hz,
44 % of energy below 250 Hz, <9 % above 4 kHz).

Output: /workspace/music/qasida_opus.wav
Run:    python3 -m ambient.persian_opus
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from forge.core.buffer import AudioBuffer
from forge.core.rng import RngContext
from forge.core.dsp import lowpass, midi_to_hz, slow_noise
from forge.core.reverb import make_reverb_ir, reverb
from forge.core.mastering import master
from forge.instruments.voices import voice_phrase, choir
from forge.instruments.strings import pad_chord, santur, oud
from forge.instruments.bass import psy_bass_note
from forge.instruments.percussion import make_doum, make_tek, make_frame_hit
from forge.instruments.textures import wind

# ═══════════════════════════════════════════════════════════════════════════════
# PART 1 — CONSTANTS, SCALE, MATERIAL
# ═══════════════════════════════════════════════════════════════════════════════

SR = 44100

# ── Timing ────────────────────────────────────────────────────────────────────
BPM   = 96
BEAT  = 60.0 / BPM           # 0.625 s
BAR   = 4 * BEAT             # 2.5 s
STEP  = BEAT / 4             # 0.15625 s  (16th note)
TOTAL = 192 * BAR            # 480 s

# ── Section boundaries (seconds) ───────────────────────────────────────────────
T_INTRO  = 0
T_RISE   = 16  * BAR   #  40 s — darbuka + bass enter
T_BUILD  = 48  * BAR   # 120 s — oud, choir, full groove
T_GSHIFT = 76  * BAR   # 190 s — brief drone-shift to the fifth (G)
T_GBACK  = 84  * BAR   # 210 s — back to the C pedal
T_PEAK   = 88  * BAR   # 220 s — densest; santur; theme stated boldly
T_UNWIND = 144 * BAR   # 360 s — thinning plateau
T_OUTRO  = 172 * BAR   # 430 s — drums drop, sparse farewell
T_END    = TOTAL       # 480 s

# ── Scale: C Phrygian Dominant (Maqam Hijaz) ──────────────────────────────────
C1                              = 24
C2, Db2, E2, F2, G2, Ab2, Bb2  = 36, 37, 40, 41, 43, 44, 46
C3, Db3, E3, F3, G3, Ab3, Bb3  = 48, 49, 52, 53, 55, 56, 58
C4, Db4, E4, F4, G4, Ab4, Bb4  = 60, 61, 64, 65, 67, 68, 70
C5, Db5, E5                     = 72, 73, 76

# ── Reverb IRs (short instruments only; the bed gets none) ────────────────────
IR_ROOM_L = make_reverb_ir(1.8, 1.4, seed=3,  sr=SR)
IR_ROOM_R = make_reverb_ir(1.8, 1.4, seed=5,  sr=SR)
IR_HALL_L = make_reverb_ir(2.6, 2.1, seed=7,  sr=SR)
IR_HALL_R = make_reverb_ir(2.6, 2.1, seed=11, sr=SR)

# ── The recurring hijaz theme (all share the C–D♭–E augmented-second identity) ─
# voice_phrase notes = [(midi, dur_s), ...]
THEME_INTRO = [
    (C4, 3.0), (Db4, 1.5), (E4, 2.5), (Db4, 1.25), (C4, 4.0),
]  # ~12 s — first statement of the cell, bare and slow

THEME_MAIN = [
    (C4, 1.25), (Db4, 0.75), (E4, 1.5), (F4, 0.75), (E4, 0.75), (Db4, 1.0), (C4, 2.0),
    (G4, 1.25), (Ab4, 0.75), (G4, 1.25), (F4, 0.75), (E4, 0.75), (Db4, 1.0), (C4, 3.0),
]  # ~16.5 s — the full theme: lower hijaz tetrachord then the upper (G–Ab) turn

THEME_HIGH = [
    (G4, 1.0), (Ab4, 0.75), (Bb4, 0.75), (C5, 1.5), (Bb4, 0.75), (Ab4, 0.75), (G4, 1.5),
    (E4, 1.0), (F4, 0.75), (E4, 0.75), (Db4, 1.0), (C4, 3.0),
]  # ~13.5 s — octave-up answer for the peak, same descent home to C

THEME_OUTRO = [
    (C4, 4.0), (Db4, 2.0), (E4, 2.5), (Db4, 2.0), (C4, 5.5),
]  # ~16 s — the cell again, farewell

# ── Oud lines [(midi, t_offset_within_phrase, note_dur_s), ...] ───────────────
OUD_DESC = [
    (C4, 0.0, 1.2), (Bb3, 0.5, 1.2), (Ab3, 1.0, 1.2), (G3, 1.6, 1.4),
    (F3, 2.3, 1.4), (E3, 3.0, 1.5), (Db3, 3.8, 1.7), (C3, 4.7, 3.0),
]  # full modal descent
OUD_TURN = [
    (G3, 0.0, 1.2), (Ab3, 0.5, 1.2), (G3, 1.0, 1.2), (F3, 1.6, 1.2),
    (E3, 2.2, 1.4), (Db3, 2.9, 1.5), (C3, 3.7, 3.0),
]  # upper-neighbour turn answering the descent

# ── Santur ascending run ──────────────────────────────────────────────────────
SANTUR_PITCHES = [C4, Db4, E4, F4, G4, Ab4, Bb4, C5]

# ── Pad / choir voicings — open 5th + ♭7, no 3rd (modal, sustaining) ──────────
PAD_NOTES   = [C4, G4, Bb4]
CHOIR_NOTES = [C3, G3, Bb3]

# ── Darbuka — Maqsum-inspired, 16 steps/bar; keys=step, values=velocity ───────
DOUM_STEPS  = {0: 0.95, 3: 0.40, 6: 0.55, 8: 0.70, 11: 0.35}
TEK_STEPS   = {4: 0.70, 10: 0.50, 12: 0.70}
GHOST_STEPS = {2: 0.20, 7: 0.24, 14: 0.30, 15: 0.22}
FILL_TEKS   = {9: 0.45, 13: 0.45, 14: 0.40, 15: 0.55}  # added on fill bars

# ── Relative gains (master() peak-normalises afterwards) ──────────────────────
G_DRONE   = 0.10   # was 0.45 — deep & dark, now a felt floor not a heard alarm
G_AIR     = 0.06   # was 0.22 wind — intro/outro only, hiss removed
G_PAD     = 0.02
G_CHOIR   = 0.20
G_NEY     = 0.50
G_OUD     = 0.36
G_SANTUR  = 0.26
G_BASS_DN = 0.62   # downbeat sub
G_BASS_OF = 0.42   # beat-3 sub
G_DARBUKA = 0.50
G_RIQ     = 0.11


# ═══════════════════════════════════════════════════════════════════════════════
# PART 2 — BED RENDERERS (the fix)
# ═══════════════════════════════════════════════════════════════════════════════

def render_drone(rng: RngContext, dur: float, root_midi: int = C1) -> np.ndarray:
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
    r = rng.rng

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


def render_air(rng: RngContext, dur: float) -> np.ndarray:
    """Gentle dark desert air — wind with the hiss removed and low-passed.

    Used only at the intro/outro (with fades), never as a constant bed.
    """
    ab = wind(
        {"duration": dur, "whoosh_lo": 60.0, "whoosh_hi": 320.0,
         "hiss_level": 0.0,            # ← the 2–7 kHz "tinnitus" band, gone
         "gust_rate": 0.10, "gust_power": 2.4, "swell_rate": 0.05,
         "pan_rate": 0.04, "pan_lo": 0.38, "pan_hi": 0.62},
        rng.rng, sr=SR,
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


def _edge_fade(x: np.ndarray, fin: float, fout: float) -> None:
    """In-place raised-cosine fade in/out on a stereo (N,2) array."""
    ni, no = int(fin * SR), int(fout * SR)
    if ni > 0:
        ramp = 0.5 - 0.5 * np.cos(np.pi * np.arange(ni) / ni)
        x[:ni] *= ramp[:, None]
    if no > 0:
        ramp = 0.5 + 0.5 * np.cos(np.pi * np.arange(no) / no)
        x[-no:] *= ramp[:, None]


# ═══════════════════════════════════════════════════════════════════════════════
# PART 3 — INSTRUMENT RENDERERS
# ═══════════════════════════════════════════════════════════════════════════════

def render_pad(rng: RngContext, dur: float) -> np.ndarray:
    """Sustained detuned-saw modal pad (dark), with slow breathing so it never
    becomes a flat wall.  Returns (N,2)."""
    ab = pad_chord(
        {"midi_notes": PAD_NOTES, "duration": dur,
         "attack": 6.0, "release": 8.0, "lp_cutoff": 1200.0, "detune": 0.0016},
        rng.rng, sr=SR,
    )
    env = _breath(dur, rng.spawn("padbr").rng, lo=0.5, hi=1.0, rate=0.025, power=1.3)
    ab.data[:, 0] *= env
    ab.data[:, 1] *= env
    return ab.data


def render_choir(rng: RngContext, dur: float, notes=CHOIR_NOTES) -> np.ndarray:
    """Choir swell ("oo") with hall reverb; returns (N,2)."""
    tail_s = 3.0
    ab = choir(
        {"midi_notes": notes, "vowel": "oo", "duration": dur,
         "detune": 0.003, "n_harmonics": 8},
        rng.rng, sr=SR,
    )
    L, R = ab.data[:, 0], ab.data[:, 1]
    padL = np.concatenate([L, np.zeros(int(tail_s * SR))])
    padR = np.concatenate([R, np.zeros(int(tail_s * SR))])
    outL = reverb(padL, IR_HALL_L, wet=0.45)[:len(L)]
    outR = reverb(padR, IR_HALL_R, wet=0.45)[:len(R)]
    return np.column_stack([outL, outR])


def render_ney(phrase: list, rng: RngContext) -> np.ndarray:
    """One ney phrase (breathy, dark) with room reverb; returns (N,2)."""
    tail_s = 2.5
    ab = voice_phrase(
        {"notes": phrase, "ney_mode": True, "breath_level": 0.10,
         "vibrato_depth": 0.006, "vibrato_rate": 5.5, "vibrato_bloom": 1.5,
         "lp_cutoff": 1900.0, "n_harmonics": 4},
        rng.rng, sr=SR,
    )
    mono = (ab.data[:, 0] + ab.data[:, 1]) * 0.5
    padded = np.concatenate([mono, np.zeros(int(tail_s * SR))])
    L = reverb(padded, IR_ROOM_L, wet=0.36)[:len(mono)]
    R = reverb(padded, IR_ROOM_R, wet=0.36)[:len(mono)]
    return np.column_stack([L, R])


def render_oud_phrase(phrase: list, rng: RngContext) -> np.ndarray:
    """Overlapping oud plucks assembled into one stereo array with room reverb."""
    total = max(t + d for _, t, d in phrase) + 1.0
    n = int(total * SR)
    buf = np.zeros(n)
    r = rng.rng
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


def render_santur_run(rng: RngContext) -> np.ndarray:
    """Ascending ornamental santur run (staggered); returns (N,2)."""
    r = rng.rng
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


def render_bass_hit(midi: int, rng: RngContext) -> np.ndarray:
    """Single warm psy sub-bass note; returns (N,) mono."""
    ab = psy_bass_note({"midi": midi, "duration": 0.55, "decay_mult": 5.0},
                       rng.rng, sr=SR)
    return (ab.data[:, 0] + ab.data[:, 1]) * 0.5


def render_darbuka_bar(rng: RngContext, fill: bool = False,
                       humanise: float = 0.012) -> np.ndarray:
    """One bar of Maqsum-inspired darbuka (humanised); returns (N,) mono."""
    n = int(BAR * SR)
    buf = np.zeros(n)
    r = rng.rng

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


def render_riq_hit(rng: RngContext) -> np.ndarray:
    """Light frame-drum/riq accent (kept dark, low); returns (N,) mono."""
    ab = make_frame_hit({"f0": 320.0, "duration": 0.18}, rng.rng, sr=SR)
    return ab.L


# ═══════════════════════════════════════════════════════════════════════════════
# PART 4 — COMPOSITION
# ═══════════════════════════════════════════════════════════════════════════════

def compose(seed: int = 42) -> AudioBuffer:
    mix = AudioBuffer(int(TOTAL * SR), SR)
    rng = RngContext(seed)

    # ── DEEP DRONE (full track) — the fixed bed ───────────────────────────────
    drone = render_drone(rng.spawn("drone"), TOTAL, root_midi=C1)
    fin = int(12.0 * SR)
    drone[:fin] *= np.linspace(0.0, 1.0, fin)
    mix.add_at(drone, 0.0, gain=G_DRONE)
    del drone

    # ── DARK AIR — intro and outro only, faded (not constant) ─────────────────
    air_rng = rng.spawn("air")
    intro_air = render_air(air_rng.spawn("in"), T_BUILD + 6.0)
    _edge_fade(intro_air, 6.0, 10.0)
    mix.add_at(intro_air, 0.0, gain=G_AIR)
    del intro_air
    outro_air = render_air(air_rng.spawn("out"), (T_END - T_UNWIND) + 6.0)
    _edge_fade(outro_air, 10.0, 12.0)
    mix.add_at(outro_air, T_UNWIND, gain=G_AIR)
    del outro_air

    # ── PAD (intro → unwind), breathing ───────────────────────────────────────
    pad = render_pad(rng.spawn("pad"), (T_UNWIND - T_INTRO) + 8.0)
    mix.add_at(pad, T_INTRO, gain=G_PAD)
    del pad

    # ── CHOIR swells (build → unwind, every 16 bars) ──────────────────────────
    # Voicing stays C–G–B♭ throughout; during the G-shift the bass moves to G
    # under it, which turns the same chord into the suspended-fifth tension that
    # the analysis hears as the brief "drone shift to the fifth".
    choir_rng = rng.spawn("choir")
    swell_dur = 8 * BAR + 4.0
    t = T_BUILD
    while t < T_UNWIND:
        ch = render_choir(choir_rng.spawn(f"c{t:.0f}"), swell_dur)
        _edge_fade(ch, 4.0, 4.0)
        mix.add_at(ch, t, gain=G_CHOIR)
        t += 16 * BAR

    # ── NEY — the recurring theme, in every melodic section ───────────────────
    ney_rng = rng.spawn("ney")
    mix.add_at(render_ney(THEME_INTRO, ney_rng.spawn("intro")),
               T_INTRO + 6 * BAR, gain=G_NEY * 0.85)

    t, i = T_RISE + 4 * BAR, 0
    while t < T_OUTRO:
        if t < T_PEAK:
            phrase = THEME_MAIN
            gap = 10
        elif t < T_UNWIND:
            phrase = THEME_HIGH if (i % 2) else THEME_MAIN   # alternate at the peak
            gap = 9
        else:
            phrase = THEME_MAIN
            gap = 16
        mix.add_at(render_ney(phrase, ney_rng.spawn(f"n{t:.0f}")), t, gain=G_NEY)
        jitter = ney_rng.spawn(f"j{t:.0f}").rng.uniform(-BAR, BAR)
        t += gap * BAR + jitter
        i += 1

    mix.add_at(render_ney(THEME_OUTRO, ney_rng.spawn("outro")),
               T_OUTRO + 3 * BAR, gain=G_NEY * 0.9)

    # ── OUD — call/response (build → unwind), every 12 bars ───────────────────
    oud_rng = rng.spawn("oud")
    t, alt = T_BUILD, False
    while t < T_UNWIND:
        phrase = OUD_TURN if alt else OUD_DESC
        mix.add_at(render_oud_phrase(phrase, oud_rng.spawn(f"o{t:.0f}")),
                   t, gain=G_OUD)
        t += 12 * BAR
        alt = not alt

    # ── SANTUR runs (peak only, every 8 bars) ─────────────────────────────────
    santur_rng = rng.spawn("santur")
    t = T_PEAK
    while t < T_UNWIND:
        mix.add_at(render_santur_run(santur_rng.spawn(f"s{t:.0f}")),
                   t, gain=G_SANTUR)
        t += 8 * BAR

    # ── SUB-BASS pulse (rise → unwind); root follows the pedal (C, briefly G) ─
    bass_rng = rng.spawn("bass")
    for bar in range(int(T_RISE / BAR), int(T_UNWIND / BAR)):
        t_bar = bar * BAR
        in_g = T_GSHIFT <= t_bar < T_GBACK
        g_scale = 1.0 if t_bar < T_UNWIND - 12 * BAR else 0.8
        # downbeat
        root_dn = G2 if in_g else C2
        mix.add_at(render_bass_hit(root_dn, bass_rng.spawn(f"b{bar}_0")),
                   t_bar, gain=G_BASS_DN * g_scale)
        # beat 3 — sits on the fifth (G) in both the C pedal and the G shift
        mix.add_at(render_bass_hit(G2, bass_rng.spawn(f"b{bar}_8")),
                   t_bar + 8 * STEP, gain=G_BASS_OF * g_scale)

    # ── DARBUKA (rise → outro), fades in/out; fills every 8th bar in the body ─
    perc_rng = rng.spawn("perc")
    p_start, p_end = int(T_RISE / BAR), int(T_OUTRO / BAR)
    n_bars = p_end - p_start
    ramp_bars = 12
    for k in range(n_bars):
        bar = p_start + k
        t_bar = bar * BAR
        g = (min(k, ramp_bars) / ramp_bars) * (min(n_bars - k, ramp_bars) / ramp_bars)
        fill = (k % 8 == 7) and (T_BUILD <= t_bar < T_UNWIND)
        mix.add_at(render_darbuka_bar(perc_rng.spawn(f"p{k}"), fill=fill),
                   t_bar, gain=G_DARBUKA * g)

    # ── RIQ accents (peak only) — light backbeat shimmer, kept low/dark ───────
    riq_rng = rng.spawn("riq")
    for bar in range(int(T_PEAK / BAR), int(T_UNWIND / BAR)):
        t_bar = bar * BAR
        for step in (4, 12):
            mix.add_at(render_riq_hit(riq_rng.spawn(f"r{bar}_{step}")),
                       t_bar + step * STEP, gain=G_RIQ)

    return master(mix, target=0.9, fade_in_s=3.0, fade_out_s=6.0)


def main() -> None:
    out_path = Path("/workspace/music/qasida_opus.wav")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    print("Composing qasida (opus) …")
    mix = compose(seed=42)
    sf.write(str(out_path), mix.data, SR, subtype="PCM_24")
    dur = len(mix.data) / SR
    print(f"Written {out_path}  ({dur:.0f} s, {SR} Hz, 24-bit PCM)")
    # quick arc check: per-twelfth RMS should rise to the peak then fall
    rms = mix.section_rms(12)
    print("Section RMS arc:", " ".join(f"{x:.3f}" for x in rms))


if __name__ == "__main__":
    main()
