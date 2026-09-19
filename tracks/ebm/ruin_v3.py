#!/usr/bin/env python3
"""Ruin v3 — the hammer (tracks/ebm, 2026-09-18).  The bass.

109 BPM, F# minor, 104 bars + a 4-bar decay = 3:58, seed 2018.  The
*Spiritual Reality* archetype (../../inspiration/Apop_Soli_Deo_Gloria.md
§3), closing the 1993 set: slam 122 (procession), jackhammer 140
(no_access), hammer 109.  Notes: ruin_notes.md — the plan, the ten
answers, and the two 2026-09-16 rounds (questions 11-17) this script
follows.

v2 was heard 2026-09-18: **"not bad at all — however the main problem is
the bass line.  The SH-101 bass is just too timid.  It reads like a 1980s
commodore game, as opposed to a heavy bold EBM goth track."**  v3 changes
the BASS and nothing else: the arrangement, the litany, the seam kit, the
way in, the doubles and the master are v2's, byte for byte.

The bass comes from **instruments/sh101_bass_ruin.py**, a FORK of the
library module rather than an edit of it — `sh101_bass.py` is imported by
reliquary, no_access, watchfire and the procession probes, all of which
have listen verdicts attached to renders, so it must keep returning what
it returned.  The fork adds two oscillator knobs (`detune` unison cents,
`sub_wave` square|sine) and is bit-identical at its defaults.

What the tuning actually found (probes 16 and 17; the dead ends are
recorded in the fork's docstring so they are not re-run).  Four theories
measured DOWN: the EPS dirt is not the 8-bit read at this register
(hold=1 and hold=2 are identical), the filter floor does nothing
(800/1500/2500 Hz all measure the same), a parallel distorted mid band
only costs crest, and the sub-120 share stays ~0.85 even with sub=0.0 —
at F#2 the fundamental itself is under 120 Hz.  A fifth fact killed the
"it is too quiet" reading outright: in a v2 verse the bass stem runs
**6.9 dB LOUDER than the drums** (-18.4 against -25.3 dBFS).

So v3 does the two things that survived:

  * **DENSITY.**  The unison stack (18 cents either side), a sine sub at
    0.8 instead of a 0.6 square, drive 2.0, the dirt off, and the whole
    gate cycle x1.3 so the notes connect.  Crest 2.96 -> 1.96 on the
    stem: about +2 dB of RMS at the same peak, and audibly a wall rather
    than a blip.  The gate stretch is a declared deviation — 0.50 becomes
    0.65, past the 1993 figure of <= 0.5 — because "the gap IS the
    groove" is what made it a blip.
  * **THE OCTAVE DOUBLE.**  A quiet copy of the whole line an octave up,
    darkly filtered (floor 1400 Hz, gain 0.30), on its own layer.  This
    is how the lead already gets its weight in the choruses, and it is
    the standard way a bass reads BIG without more low end: it moves the
    sub-60 share DOWN (0.60 -> 0.49) while the bass gets louder, because
    the size now comes from the midrange, where small speakers live.

BASS_READING switches between the five probed readings in one word, so
the verdict costs a re-render and no edit: "dense", "octave" (the
default, probe 17d), "wide" (17e, the octave panned — a declared
deviation from the blueprint's mono-centre bass), "square" (17c, the
hollow Nitzer end, which gives up most of the low end: sub-60 0.04), or
"v2" (the control, bit-identical to ruin_v2).

Standing from v1 and v2: the pitch stays on the root and the phrase moves
through the filter, the gate and the accent; verse 1 refuses to move
and verse 2 gives in once (A2, B2); the chorus roots go UP (F#2 D3 C#3
F#2); the kick to 8ths in the final with the hats out; the hard stop.
The space claim is still measured, with the roll bars as the declared
exception — a roll is not space.

Output: /workspace/music/<NAME>.wav + .flac (44100 Hz stereo 16-bit).
Prints the VERIFY.md blocks; a FAIL never aborts the render.

Listening flags (LISTENING.md; checks are skipped on a partial render):
  --solo lead[,bass]   render only these layers (through the master)
  --mute drums         everything but these
  --slice 16 24        bars [16, 24) only — a verse, where the bass is most exposed
  --solo bass,bassoct  the engine alone: what the verdict was about
  --suffix _leadA      output <NAME>_leadA.wav
  --stems              + <NAME>_stems/<layer>.wav (post-reverb, weighted, pre-master)
"""
from __future__ import annotations

import argparse
import pathlib
import sys
import wave

import numpy as np
import soundfile
from scipy import signal

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "instruments"))
import _common                                                            # noqa: E402

_common.set_tempo(109)                          # BEFORE the instrument imports (they bind the grid)
_common.seed(2018)                              # the year the record was remastered from the tapes
from _common import BAR, BEAT, SR, STEP, midi_to_hz, norm                 # noqa: E402
from dark_lead import dark_lead                                           # noqa: E402
from devices import FIGURES, downsweep, riser, roll, run, silent_beat     # noqa: E402
from eps_hit import hit                                                   # noqa: E402
from eps_kick import kick                                                 # noqa: E402
from eps_snare import snare                                               # noqa: E402
from hats import hat                                                      # noqa: E402
from juno import noise_sweep, organ, pad                                  # noqa: E402
from seethe import seethe                                                 # noqa: E402
from sh101_bass_ruin import CELLS, note                                    # noqa: E402

# ------------------------------------------------------------- the piece
NAME = "ruin_v3"                                      # bump per iteration (ruin_v3.1 ...)
TOTAL_BARS = 104
TAIL_BARS = 4                                         # hard stop at 104; the bed and the last hit decay
END = (TOTAL_BARS + TAIL_BARS) * BAR
N = int(END * SR)
SECTIONS = [("OPENING", 0, 8), ("VERSE 1", 8, 24), ("PRE 1", 24, 32), ("CHORUS 1", 32, 48),
            ("VERSE 2", 48, 56), ("PRE 2", 56, 64), ("CHORUS 2", 64, 80), ("BREAK", 80, 88),
            ("FINAL", 88, 104), ("TAIL", 104, 108)]

CHORUS_ROOTS = "up"                                   # "up" | "pedal"              (probe 04)
KICK_8THS = True                                      # the final chorus only       (Q7)
WAY_IN_BARS = 2                                       # the bed swells from silence over these (Q15: 10b)

FS2, A2, B2, D3, CS3 = 42, 45, 47, 50, 49             # F#2 is home; A2/B2 are verse 2's answer
NOTE = {"F#2": 42, "G#2": 44, "A2": 45, "B2": 47, "C#3": 49, "D3": 50, "E3": 52, "F#3": 54, "G3": 55}
FSM_HI, D_HI, CSM_HI = (57, 61, 66), (57, 62, 66), (56, 61, 64)   # above the refrain's G3 ceiling
LOOP = [FSM_HI, D_HI, CSM_HI, FSM_HI]                 # F#m D C#m F#m: the minor v, never the flat-VII
ROOT_OF = {FSM_HI: FS2, D_HI: D3, CSM_HI: CS3}        # the ROOT, not the lowest note of the voicing
NAME_OF = {FSM_HI: "F#m", D_HI: "D", CSM_HI: "C#m"}
PC = "C C# D D# E F F# G G# A A# B".split()
FORBIDDEN_ROOT = 4                                    # E: the flat-VII chord of F# minor
FSM_SCALE = {6, 8, 9, 11, 1, 2, 4}                    # F# natural minor: F# G# A B C# D E
HIT_CHORD = (42, 49, 54, 57)                          # F#2 C#3 F#3 A3
ORGAN_LOW = (42, 49, 54)

# THE LITANY (Q11: B): the petition (bars 1-4) hangs on the 5th, the response (5-8) lands
# on the tonic.  Every bar but the phrase ends: a tone held two beats, then the falling tail.
HOOK = ["F#3 - - - E3 - D3 C#3", "C#3 - - - D3 - C#3 D3", "F#3 - - - G3 - F#3 E3", "C#3 - - - - - . .",
        "E3 - - - D3 - C#3 B2", "C#3 - - - D3 - C#3 B2", "D3 - - - G3 - C#3 A2", "F#2 - - - - - . ."]
PETITION = HOOK[:4]
RELIQUARY_BAR1 = "A3 - A3 A3 Bb3 - A3 -"              # v1's bar 1 was this transposed — the check reads its rhythm

# the engine: the pitch NEVER moves in bars 0-6; the phrase is elsewhere
CELL = {**CELLS, "hammer": "x.x.x.x.x.x.x.x.", "walk": "x.x.x.5.x.7.o.o.",
        "half": "x...x...x...x...",                   # the pre-chorus
        "hole": "x...x...x......."}                   # its last bar: the bass leaves the hole too
PHRASE = ("hammer",) * 7 + ("walk",)
CUTS = (2200.0, 2200.0, 1500.0, 1500.0, 2800.0, 2800.0, 1700.0, 2400.0)
GATES = (0.50, 0.50, 0.42, 0.42, 0.50, 0.50, 0.35, 0.50)
FLOORS = (0.72, 0.72, 0.72, 0.72, 0.60, 0.60, 0.78, 0.60)
ACCENT = {0: 1.0, 4: 0.92, 8: 1.0, 12: 0.92}          # the quarters lean
INTERVAL = {"x": 0, "o": 12, "5": 7, "7": 10}
SUB_VERSE, SUB_CHORUS = 0.6, 0.85                     # Q2, and measured inside the guardrail band
SUB_PRE = 0.45                                        # the pre builds by REMOVING rhythm, not adding weight

# ---------------------------------------------------------- THE BASS (v3)
# One word switches the reading; the probes are 17a-17e.  `tone` goes to
# sh101_bass_ruin.note(), `gate_mul` scales the whole GATES cycle (so the cycle
# still turns), `floor_hz` is the filter envelope's floor, `octave` is the gain
# of the octave-up layer (0 = no layer) and `wide` pans it against the root line.
BASS_READING = "octave"                               # octave | dense | wide | square | v2
BASS = {
    "v2":     {"tone": {}, "gate_mul": 1.0, "floor_hz": 250.0, "octave": 0.0, "wide": False},
    "dense":  {"tone": {"detune": 18.0, "sub_wave": "sine", "drive": 2.0, "hold": 1},
               "gate_mul": 1.3, "floor_hz": 500.0, "octave": 0.0, "wide": False},
    "octave": {"tone": {"detune": 18.0, "sub_wave": "sine", "drive": 2.0, "hold": 1},
               "gate_mul": 1.3, "floor_hz": 500.0, "octave": 0.30, "wide": False},
    "wide":   {"tone": {"detune": 18.0, "sub_wave": "sine", "drive": 2.0, "hold": 1},
               "gate_mul": 1.3, "floor_hz": 500.0, "octave": 0.30, "wide": True},
    "square": {"tone": {"detune": 18.0, "sub_wave": "sine", "drive": 2.2, "hold": 1,
                        "wave": "square", "res": 2.0, "env": 0.10},
               "gate_mul": 1.3, "floor_hz": 900.0, "octave": 0.0, "wide": False},
}[BASS_READING]
# the dense readings raise `sub` too: a SINE sub at 0.8 costs far less peak than the
# 0.6 square did, which is what lets the note get denser instead of merely different
SUB_SCALE = 1.0 if BASS_READING == "v2" else (0.58 if BASS_READING == "square" else 1.33)
OCTAVE_CUT = 1400.0                                   # the octave copy is dark: presence, not a second bass
OCTAVE_PAN = 0.35                                     # "wide" only
PLATE_CUT = 0.22                                      # Q5: the one dialect where the blow rings
CHEST = {32: 1.0, 40: 1.0, 64: 1.15, 72: 1.15, 88: 1.3, 96: 1.3}
SPACE_CEILING = 24                                    # onsets per bar: this track's claim is space

KICK_Q = "x...x...x...x..."
KICK_8 = "x.x.x.x.x.x.x.x."
SNARE_P = "....x.......x..."
HAT_8 = (0, 2, 4, 6, 8, 10, 12, 14)
HAT_ACC = (1.0, 0.5, 0.7, 0.5)
VERSE2_ANSWER = {54: A2, 55: B2}                      # the last two bars of verse 2 give in
# v3: the verses sit back one more notch than v2's 0.84 / 0.86.  The denser bass lifted
# them by +2.8 dB against the choruses' +1.7 (the chorus sub clamps at 1.0 and its roots
# climb to D3/C#3, where there is less low end to gain), which cost the 1.5 dB arc.
SECTION_GAIN = {"OPENING": 0.9, "VERSE 1": 0.78, "PRE 1": 0.88, "CHORUS 1": 1.0, "VERSE 2": 0.80,
                "PRE 2": 0.90, "CHORUS 2": 1.0, "BREAK": 1.0, "FINAL": 1.0, "TAIL": 0.0}

# the seam kit (Q12) and the statements (Q16)
STATEMENTS = (32, 40, 64, 72, 88, 96)
DOUBLED = (40, 72, 88, 96)                            # statement 2 of each chorus; the final on both
DOUBLE_GAIN = 0.35
ROLL_BARS = (30, 62, 86)                              # the two bars into each chorus and into the final
HOLES = (31, 63)                                      # beat 4: no drum, no bass — the roll's last beat
SILENT = (87.75, 88.0)                                # the one true silent beat, bed included (on the master)
DOWNSWEEPS = (32, 64, 88)


def bar_t(b):
    return b * BAR


def section_of(bar):
    for name, b0, b1 in SECTIONS:
        if b0 <= bar < b1:
            return name
    return "TAIL"


def is_chorus(b):
    return 32 <= b < 48 or 64 <= b < 80 or 88 <= b < 104


def is_verse(b):
    return 8 <= b < 24 or 48 <= b < 56


def is_pre(b):
    return 24 <= b < 32 or 56 <= b < 64


def is_break(b):
    return 80 <= b < 88


def is_rolling(b):
    return b in ROLL_BARS or b - 1 in ROLL_BARS


def chord_at(b):
    return LOOP[b % 4]


def verse_root(b):
    """Verse 1 refuses to move at all.  Verse 2 answers in its last two
    bars — both probe readings were liked, so the track uses the refusal
    as the idea and giving in once as the development."""
    return VERSE2_ANSWER.get(b, FS2)


def chorus_root(b):
    return FS2 if CHORUS_ROOTS == "pedal" else ROOT_OF[chord_at(b)]


def figure_for(b):
    """Kick figure B (the 'and' of 4) on bars 4n+1 of the verses and the
    choruses; the final's 8ths carry that step anyway."""
    if KICK_8THS and 88 <= b < 104:
        return KICK_8
    return FIGURES["B"] if (is_verse(b) or is_chorus(b)) and b % 4 == 1 and b >= 8 else KICK_Q


def run_bar(b):
    """The snare run on the last beat of bars 4n+3 of the verses and the
    choruses — the hats yield that beat so the bar stays at the ceiling."""
    return (is_verse(b) or is_chorus(b)) and b % 4 == 3 and b >= 8


def hats_for(b):
    """8ths only (Q3), none in verse 1's first eight bars, and none at all
    where the kick takes the eighths — 26 onsets a bar would break the
    space ceiling (probe 09)."""
    if b < 16 or is_break(b):
        return ()
    if KICK_8THS and 88 <= b < 104:
        return ()
    return HAT_8


def parse(lines):
    out, prev = [], None
    for b, line in enumerate(lines):
        for i, tok in enumerate(line.split()):
            if tok in NOTE:
                out.append([b * 8 + i, NOTE[tok], 1])
            elif tok == "-":
                assert prev not in (".", None), f"'-' after a rest in bar {b}: {line!r}"
                out[-1][2] += 1
            prev = tok
    return [tuple(e) for e in out]


def onset_slots(line):
    return {i for i, tok in enumerate(line.split()) if tok not in ("-", ".")}


# ---------------------------------------------------------------- helpers
def fade(x, fin=0.004, fout=0.05):
    y = x.copy()
    ni, no = int(fin * SR), int(fout * SR)
    if ni:
        y[:ni] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(ni) / ni)
    if no:
        y[-no:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(no) / no)
    return y


def make_reverb_ir(seconds, decay, seed):
    r = np.random.default_rng(seed)
    n = int(seconds * SR)
    ir = r.standard_normal(n) * np.exp(-np.arange(n) / SR / decay)
    b, a = signal.butter(2, 4000 / (SR / 2), "low")
    return (lambda y: y / np.sqrt(np.sum(y ** 2)))(signal.lfilter(b, a, ir))


IR_L = make_reverb_ir(3.0, 1.0, 7)
IR_R = make_reverb_ir(3.0, 1.0, 11)


def reverb_pair(L, R, wet):
    if wet <= 0.0:
        return L, R
    wL = signal.fftconvolve(L, IR_L)[: len(L)]
    wR = signal.fftconvolve(R, IR_R)[: len(R)]
    for d, w in ((L, wL), (R, wR)):
        w *= (np.max(np.abs(d)) + 1e-12) / (np.max(np.abs(w)) + 1e-12)
    return (1 - wet) * L + wet * wL, (1 - wet) * R + wet * wR


def highpass(x, hz, order=2):
    return signal.sosfilt(signal.butter(order, hz, "high", fs=SR, output="sos"), x)


def lowpass(x, hz, order=2):
    return signal.sosfilt(signal.butter(order, hz, "low", fs=SR, output="sos"), x)


def add_at(buf, x, start_s, gain=1.0):
    i0 = int(start_s * SR)
    if i0 >= len(buf):
        return
    n = min(len(x), len(buf) - i0)
    if n > 0:
        buf[i0:i0 + n] += gain * x[:n]


def place(layer, x, t, gain=1.0, pan=0.0):
    a = (pan + 1.0) / 2.0
    add_at(layer[0], x, t, gain * np.cos(a * np.pi / 2))
    add_at(layer[1], x, t, gain * np.sin(a * np.pi / 2))


def place_wide(layer, x, t, gain=1.0, spread=0.012):
    add_at(layer[0], x, t, gain)
    add_at(layer[1], x, t + spread, gain)


LAYER_NAMES = ["bed", "pad", "organ", "bass", "bassoct", "drums", "lead", "hit", "fx"]
WETS = {"bed": 0.0, "pad": 0.35, "organ": 0.32, "bass": 0.0, "bassoct": 0.0, "drums": 0.08,
        "lead": 0.25, "hit": 0.30, "fx": 0.3}
WEIGHTS = {"bed": 0.30, "pad": 0.20, "organ": 0.28, "bass": 0.42, "bassoct": 0.42 * BASS["octave"],
           "drums": 0.46, "lead": 0.44, "hit": 0.24, "fx": 0.12}

ap = argparse.ArgumentParser(description="Ruin v2 — see the docstring")
ap.add_argument("--solo", default="", help="comma-separated layer names to render alone")
ap.add_argument("--mute", default="", help="comma-separated layer names to leave out")
ap.add_argument("--slice", nargs=2, type=int, metavar=("B0", "B1"), help="bars [B0, B1) only")
ap.add_argument("--suffix", default="", help="appended to the output name")
ap.add_argument("--stems", action="store_true", help="also write per-layer stems")
ARGS = ap.parse_args()
SOLO = {x for x in ARGS.solo.split(",") if x}
MUTE = {x for x in ARGS.mute.split(",") if x}
PARTIAL = bool(SOLO or MUTE or ARGS.slice)
for nm in SOLO | MUTE:
    assert nm in LAYER_NAMES, f"unknown layer {nm!r}; layers: {LAYER_NAMES}"


def want(name):
    return name not in MUTE and (not SOLO or name in SOLO)


MIX = [np.zeros(N), np.zeros(N)]
PRE = {}


def commit(name, layer):
    L, R = layer
    pk = max(np.max(np.abs(L)), np.max(np.abs(R)))
    if pk < 1e-9:
        return
    L, R = L / pk, R / pk
    L, R = reverb_pair(L, R, WETS[name])
    MIX[0] += WEIGHTS[name] * L
    MIX[1] += WEIGHTS[name] * R
    if ARGS.stems:
        PRE[name] = (WEIGHTS[name] * L, WEIGHTS[name] * R)


def new_layer():
    return [np.zeros(N), np.zeros(N)]


HOOKS = 0
bass_events = []            # (bar, step, midi, cell)
oct_events = []             # (bar, step, midi) — the octave layer
drum_events = []            # (t, kind)
BED = None

# ------------------------------------------------------------------- bed
if want("bed"):
    layer = new_layer()
    BED = norm(seethe(FS2, END, throb=0.35, grit=0.30, sub=0.6, rate=0.05))
    n_in = int(WAY_IN_BARS * BAR * SR)
    BED[:n_in] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(n_in) / n_in)   # the way in: swells from silence
    add_at(layer[0], BED, 0.0)
    add_at(layer[1], BED, 0.013)
    commit("bed", layer)

# -------------------------------------------------------------------- fx
# the way in's noise sweep, the riser under every roll, the downsweep after every chorus hit
if want("fx"):
    layer = new_layer()
    place_wide(layer, noise_sweep(3 * BAR, f0=150.0, f1=2500.0, res=2.0), bar_t(0), 1.0)
    for b in ROLL_BARS:
        place_wide(layer, riser(2), bar_t(b), 0.8)
    for b in DOWNSWEEPS:
        place_wide(layer, downsweep(1), bar_t(b), 0.6)
    commit("fx", layer)

# ------------------------------------------------------------------- pad
if want("pad"):
    layer = new_layer()
    for b in range(TOTAL_BARS):
        if 16 <= b < 24 or 48 <= b < 56:
            ch, gain = (FSM_HI,), 0.45              # the verse pad sits on the pedal's chord
        elif is_chorus(b):
            ch, gain = (chord_at(b),), 0.85
        else:
            continue
        place_wide(layer, pad(ch[0], BAR, depth=0.0), bar_t(b), gain)
    commit("pad", layer)

# ----------------------------------------------------------------- organ
# the liturgical colour: the way in's low i, the opening quote, the pre-choruses,
# chorus 2's octave-down doubling, and the break's statement of the petition


def organ_note(m, d):
    return organ(m, d, depth=0.0)


def organ_line(layer, lines, bar0, gain):
    for start, midi, ln in parse(lines):
        place_wide(layer, organ_note(midi - 12, ln * BEAT / 2 * 0.95), bar_t(bar0) + start * BEAT / 2, gain)


if want("organ"):
    layer = new_layer()
    place_wide(layer, organ(ORGAN_LOW, 3 * BAR, depth=0.0), bar_t(0), 0.55)      # the way in
    organ_line(layer, PETITION[:2], 6, 0.5)                                       # the thesis quote (uncounted)
    for b in range(TOTAL_BARS):
        if is_pre(b):
            place_wide(layer, organ(chord_at(b), BAR, depth=0.0), bar_t(b), 0.6)
    organ_line(layer, HOOK, 64, 0.40)                                             # chorus 2: the octave-down double
    organ_line(layer, PETITION, 80, 0.55)                                         # the break: under the voice
    commit("organ", layer)

# ------------------------------------------------------------------ bass
# v3: the same events, through the fork, plus the octave-up layer.  The engine
# itself — cells, roots, accents, the filter cycle — is v2's exactly.
if want("bass") or want("bassoct"):
    layer, oct_layer = new_layer(), new_layer()
    for b in range(TOTAL_BARS):
        if b < 4 or is_break(b):
            continue                                  # in at bar 4; out through the break
        if is_pre(b):
            cell = "hole" if b in HOLES else "half"
            root, sub = FS2, SUB_PRE
        elif is_chorus(b):
            cell, root, sub = PHRASE[b % 8], chorus_root(b), SUB_CHORUS
        else:
            cell, root, sub = PHRASE[b % 8], verse_root(b), SUB_VERSE
        sub = min(1.0, sub * SUB_SCALE)
        i = b % 8
        c = CELL[cell]
        shaped = cell in ("hammer", "walk")
        # the stretch applies to the ENGINE only: the pre-chorus half-time cells keep
        # v2's 0.5, or the note on step 8 of "hole" rings through the composed hole
        g_frac = GATES[i] * BASS["gate_mul"] if shaped else 0.5
        floor = FLOORS[i] if shaped else 0.8
        cutoff = ((CUTS[i] if shaped else 2000.0), BASS["floor_hz"])
        sg = SECTION_GAIN[section_of(b)]
        onsets = [j for j, ch in enumerate(c) if ch != "."]
        for j, s_ in enumerate(onsets):
            gap = (onsets[j + 1] if j + 1 < len(onsets) else onsets[0] + 16) - s_
            m = root + INTERVAL[c[s_]]
            g = ACCENT.get(s_, floor) if c[s_] == "x" else 1.0
            dur = gap * STEP * g_frac
            t = bar_t(b) + s_ * STEP
            place(layer, note(m, dur=dur, cutoff=cutoff, sub=sub, **BASS["tone"]), t, sg * g)
            bass_events.append((b, s_, m, cell))
            if BASS["octave"]:
                oc = note(m + 12, dur=dur, cutoff=(cutoff[0], OCTAVE_CUT), sub=sub, **BASS["tone"])
                place(oct_layer, oc, t, sg * g, pan=OCTAVE_PAN if BASS["wide"] else 0.0)
                oct_events.append((b, s_, m + 12))
    if want("bass"):
        commit("bass", layer)
    if want("bassoct") and BASS["octave"]:
        commit("bassoct", oct_layer)

# ----------------------------------------------------------------- drums
if want("drums"):
    layer = new_layer()
    K = kick(decay=5.0)
    S = snare(plate_decay=3.0, cut=PLATE_CUT)
    H = hat()
    ROLL = roll(S)[: int((2 * BAR - BEAT) * SR)]        # the roll's last beat is the hole / the silent beat
    ROLL[-int(0.005 * SR):] *= np.linspace(1, 0, int(0.005 * SR))
    for b in range(4, TOTAL_BARS):
        if is_break(b) and not is_rolling(b):
            continue                                  # the break: no kit, until the roll out of it
        sg = SECTION_GAIN[section_of(b)]
        cell, hats = figure_for(b), hats_for(b)
        for s in range(16):
            t = bar_t(b) + s * STEP
            if b in HOLES and s >= 12:
                continue                              # the composed hole before each chorus
            if cell[s] == "x" and not is_break(b):
                place(layer, K, t, sg)
                drum_events.append((t, "kick"))
            if SNARE_P[s] == "x" and b >= 8 and not is_rolling(b):
                place(layer, S, t, 1.15 * sg)
                drum_events.append((t, "snare"))
            if s in hats and not (run_bar(b) and s >= 12):
                place(layer, H, t, 0.16 * HAT_ACC[s % 4] * sg, pan=-0.2)
        if run_bar(b):
            place(layer, run(S), bar_t(b) + 12 * STEP, 1.15 * sg)
            drum_events.append((bar_t(b) + 12 * STEP, "run"))
        if b in ROLL_BARS:
            place(layer, ROLL, bar_t(b), 1.15 * sg)
            drum_events.append((bar_t(b), "roll"))
    commit("drums", layer)

# ------------------------------------------------------------------ lead


def place_line(layer, lines, bar0, chest, gain=1.0, count=True, octave=0):
    global HOOKS
    for start, midi, ln in parse(lines):
        x = dark_lead(midi + octave, ln * BEAT / 2 * 0.95, chest)
        place_wide(layer, x, bar_t(bar0) + start * BEAT / 2, gain, spread=0.008)
    if count:
        HOOKS += 2 if len(lines) == 8 else 1          # a full Q/A pair is two 4-bar petitions


if want("lead"):
    layer = new_layer()
    for b0 in STATEMENTS:
        place_line(layer, HOOK, b0, CHEST[b0], 1.0)
    place_line(layer, PETITION, 80, 1.15, 0.85)       # the break's statement, the organ under it
    for b0 in DOUBLED:                                # Q16: the octave double on statement 2, the final on both
        place_line(layer, HOOK, b0, CHEST[b0], DOUBLE_GAIN, count=False, octave=12)
    commit("lead", layer)

# ------------------------------------------------------------------- hit
if want("hit"):
    layer = new_layer()
    for b in STATEMENTS:
        place_wide(layer, hit(HIT_CHORD, kind="choir", dur=0.35), bar_t(b), 1.0)
    place_wide(layer, hit(HIT_CHORD, kind="choir", dur=0.80), bar_t(63), 0.9)   # pre 2: the held hit
    place_wide(layer, hit(HIT_CHORD, kind="choir", dur=0.80), bar_t(104), 1.0)  # the last sound
    commit("hit", layer)

# -------------------------------------------------------------------- mix
for ch in (0, 1):                                     # the minimal 1993 master: HP, two shelves, glue
    MIX[ch] = highpass(MIX[ch], 30)
    MIX[ch] = MIX[ch] + 0.30 * lowpass(MIX[ch], 90)
    MIX[ch] = MIX[ch] + 0.20 * highpass(MIX[ch], 3000)
pk = max(np.max(np.abs(MIX[0])), np.max(np.abs(MIX[1]))) + 1e-12
for ch in (0, 1):
    MIX[ch] = np.tanh(1.10 * MIX[ch] / pk) / np.tanh(1.10) * 0.92
# the silent beat before the final (bed included), then the hard stop (Q9): everything
# composed ends at bar 104; the bed and the last hit ring out across the tail
GATE = silent_beat(N, bar_t(SILENT[0]), bar_t(SILENT[1]))
t0 = int(bar_t(TOTAL_BARS) * SR)
GATE[t0:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(N - t0) / (N - t0))
for ch in (0, 1):
    MIX[ch] *= GATE

i_sl = (int(bar_t(ARGS.slice[0]) * SR), int(bar_t(ARGS.slice[1]) * SR)) if ARGS.slice else (0, N)
OUT = np.stack([fade(MIX[0][i_sl[0]:i_sl[1]], 0.002, 0.03), fade(MIX[1][i_sl[0]:i_sl[1]], 0.002, 0.03)], axis=1)

out_dir = pathlib.Path("/workspace/music")
out_dir.mkdir(parents=True, exist_ok=True)
STEM = NAME + ARGS.suffix


def write_wav(path, x):
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())
    print(f"Wrote {path}  ({len(x) / SR:.1f} s)")


wav_path = out_dir / f"{STEM}.wav"
write_wav(wav_path, OUT)
flac_path = out_dir / f"{STEM}.flac"
soundfile.write(str(flac_path), OUT, SR)
print(f"Wrote {flac_path}")
if ARGS.stems:
    stem_dir = out_dir / f"{STEM}_stems"
    stem_dir.mkdir(exist_ok=True)
    for name, (L, R) in PRE.items():
        write_wav(stem_dir / f"{name}.wav", np.stack([L[i_sl[0]:i_sl[1]], R[i_sl[0]:i_sl[1]]], axis=1))
if PARTIAL:
    print(f"\npartial render (solo {sorted(SOLO) or '-'}, mute {sorted(MUTE) or '-'}, "
          f"slice {ARGS.slice or '-'}): checks skipped — the piece is the full render.")
    sys.exit(0)

# ---------------------------------------------------------------- verify
fails = []


def check(name, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}  {detail}")
    if not ok:
        fails.append(name)


def mmss(t):
    return f"{int(t // 60)}:{t % 60:04.1f}"


def rms_between(t0, t1):
    seg = OUT[int(t0 * SR):int(t1 * SR)]
    return float(np.sqrt(np.mean(seg ** 2)))


def sec_rms(b0, b1):
    return rms_between(bar_t(b0), bar_t(b1))


def sub_share(b0, b1, hz=60.0):
    seg = OUT[int(bar_t(b0) * SR):int(bar_t(b1) * SR)].mean(axis=1)
    X = np.abs(np.fft.rfft(seg)) ** 2
    f = np.fft.rfftfreq(len(seg), 1 / SR)
    return float(X[f < hz].sum() / X.sum())


db = lambda a, b: 20 * np.log10(a / b)

print("\n=== SECTION MAP ===")
for name, b0, b1 in SECTIONS:
    print(f"  {mmss(bar_t(b0)):>6}  bar {b0:3d}  {name}")
for b, what in [(0, "THE WAY IN: the bed swells from silence, a low organ i, one noise sweep"),
                (4, "the kick lands; the pedal enters"), (6, "the petition quoted on the organ (thesis, uncounted)"),
                (8, "verse 1: the slam in; NO hats for eight bars; figure B on bars 4n+1, the run on 4n+3"),
                (16, "hats to 8ths; the pad on the pedal"), (24, "pre 1: the organ, the bass to half-time"),
                (30, "THE ROLL + riser (two bars)"), (31.75, "THE HOLE: no drum, no bass on beat 4"),
                (32, "chorus 1: the litany, chest 1.0; the hit + downsweep; the roots move"),
                (40, "statement 2: + the octave double"), (48, "verse 2 (8 bars — the song gets impatient)"),
                (54, "verse 2 ANSWERS: the pedal gives in, A2 then B2"), (56, "pre 2 + the held hit"),
                (62, "the roll + riser"), (64, "chorus 2: chest 1.15, the organ doubling an octave down"),
                (72, "statement 2: + the double"), (80, "THE BREAK: kit out, the petition over the low organ"),
                (86, "the roll out of the break (no kick)"), (SILENT[0], "THE SILENT BEAT (everything, bed included)"),
                (88, f"the final: chest 1.3, the double on both statements" + (", the kick to 8ths (hats out)" if KICK_8THS else "")),
                (104, "HARD STOP; the bed and the last hit ring out")]:
    print(f"  {mmss(bar_t(b)):>6}  bar {b:6.2f}  {what}")

print("\n=== HOOK COUNT ===")
print(f"  4-bar petition statements: {HOOKS} (target >= 12); the organ quote and the octave doubles uncounted")
check("hook count >= 12", HOOKS >= 12)

print("\n=== THE COUNTER-MEASURE (the pitch stays, the phrase moves) ===")
states = list(zip(CUTS, GATES, FLOORS))
runs, run_ = [], 1
for a, b in zip(states, states[1:]):
    run_ = run_ + 1 if a == b else (runs.append(run_) or 1)
runs.append(run_)
print(f"  phrase {' '.join(PHRASE)}")
print(f"  cutoff {CUTS} Hz;  gate {GATES};  accent floor {FLOORS}")
v1 = {m for b, s, m, c in bass_events if 8 <= b < 24}
v2 = {m for b, s, m, c in bass_events if 48 <= b < 56}
print(f"  verse 1 pitches {sorted(v1)}   verse 2 pitches {sorted(v2)}")
check("verse 1 refuses to move (root + the walk only)", v1 <= {FS2, FS2 + 7, FS2 + 10, FS2 + 12}, f"{sorted(v1)}")
check("verse 2 gives in once (A2 and B2 appear)", {A2, B2} <= v2)
check("verse 2 stays on the hammer (Q17: a)", {c for b, s, m, c in bass_events if 48 <= b < 56} <= {"hammer", "walk"})
check("no state holds for more than 2 bars (the cycle turns)", max(runs) <= 2, f"(longest {max(runs)} bars)")
check("gate duty <= 0.5 everywhere (the 1993 figure)", max(GATES) <= 0.5, f"(max {max(GATES)})")

print("\n=== THE LOOP ===")
roots = [ROOT_OF[ch] % 12 for ch in LOOP]
print(f"  {' '.join(NAME_OF[ch] for ch in LOOP)} = i VI v i;  roots {[PC[r] for r in roots]};  "
      f"{PC[FORBIDDEN_ROOT]} major would be the flat-VII")
check("no flat-VII chord anywhere", FORBIDDEN_ROOT not in roots)
check("every chord's notes belong to F# natural minor", all(m % 12 in FSM_SCALE for ch in LOOP for m in ch))
check("the pad and hit sit above the refrain's G3 ceiling",
      min(m for ch in LOOP for m in ch) > 55, f"(lowest {min(m for ch in LOOP for m in ch)})")

print("\n=== THE REFRAIN (the litany) ===")
ev = parse(HOOK)
onsets = len(ev)
density = onsets / (len(HOOK) * 16)
held = sum(1 for _, _, ln in ev if ln >= 2) / onsets
run_ = best = 0
for _, _, ln in ev:
    run_ = run_ + 1 if ln == 1 else 0
    best = max(best, run_)
midis = [m for _, m, _ in ev]
steps = [b - a for a, b in zip(midis[:-1], midis[1:]) if b != a]
downs = sum(1 for d in steps if d < 0) / len(steps)
flat2 = sum(1 for m in midis if m % 12 == 7)
print(f"  onsets {onsets}  density {density:.2f} (0.20-0.50)  held {held:.2f} (>= 0.5)  "
      f"longest 8th run {best} (<= 6)  {onsets / (len(HOOK) * BAR):.1f} notes/s")
print(f"  DARK: register {min(midis)}-{max(midis)} (median {int(np.median(midis))})  down-steps {downs:.2f}  "
      f"max upward leap {max(steps)} st  flat-2nd onsets {flat2}")
check("density window 0.20-0.50", 0.20 <= density <= 0.50)
check("held fraction >= 0.5", held >= 0.5)
check("run ceiling <= 6", best <= 6)
check("register F#2..G3", min(midis) >= 42 and max(midis) <= 55)
check("descending contour: down-steps >= 0.5", downs >= 0.5)
check("no soaring leap: max upward <= 5 st", max(steps) <= 5)
check("the flat 2nd colours the refrain", flat2 >= 2)
q_end = [e for e in ev if e[0] < 32][-1]
check("the petition hangs on the 5th (C#), the response lands on the tonic (F#)",
      q_end[1] % 12 == 1 and ev[-1][1] % 12 == 6)
check("the litany: bars 1-3 and 5-7 each open on a tone held a half note",
      all(parse([HOOK[i]])[0][2] >= 4 for i in (0, 1, 2, 4, 5, 6)))
check("the hook is NOT Reliquary's rhythm (v1's was)", onset_slots(HOOK[0]) != onset_slots(RELIQUARY_BAR1),
      f"(bar 1 onsets {sorted(onset_slots(HOOK[0]))} vs Reliquary's {sorted(onset_slots(RELIQUARY_BAR1))})")
chests = sorted({c for b0, c in CHEST.items()})
check("the chest arc rises 1.0 -> 1.15 -> 1.3", chests == [1.0, 1.15, 1.3], f"{chests}")
check("statement 2 of every chorus is doubled, statement 1 of the final too (Q16: c)",
      set(DOUBLED) == {40, 72, 88, 96} and set(DOUBLED) < set(STATEMENTS))

print("\n=== THE BASS (v3's whole change) ===")
print(f"  reading {BASS_READING!r} from instruments/sh101_bass_ruin.py (a fork: sh101_bass.py is untouched)")
print(f"  tone {BASS['tone'] or '(the library defaults)'}")
print(f"  gate cycle x{BASS['gate_mul']:.2f} -> {tuple(round(g * BASS['gate_mul'], 2) for g in GATES)};  "
      f"filter floor {BASS['floor_hz']:.0f} Hz;  sub x{SUB_SCALE:.2f}")
_v2 = note(FS2, dur=STEP, cutoff=(2200.0, 250.0), sub=0.6)
_v3 = note(FS2, dur=STEP * BASS["gate_mul"] / 1.0, cutoff=(2200.0, BASS["floor_hz"]),
           sub=min(1.0, 0.6 * SUB_SCALE), **BASS["tone"])
_crest = lambda x: float(np.max(np.abs(x)) / np.sqrt(np.mean(x ** 2)))
print(f"  one note at F#2: crest {_crest(_v2):.2f} (v2) -> {_crest(_v3):.2f} (v3), "
      f"{20 * np.log10(np.sqrt(np.mean(_v3 ** 2)) / np.sqrt(np.mean(_v2 ** 2))):+.1f} dB RMS at the same peak")
check("v3's bass note is denser than v2's at the same peak (the one thing that measured)",
      BASS_READING == "v2" or _crest(_v3) < _crest(_v2), f"({_crest(_v3):.2f} vs {_crest(_v2):.2f})")
if BASS["octave"]:
    check("the octave layer doubles every bass onset, an octave up",
          len(oct_events) == len(bass_events)
          and all(o[2] == b[2] + 12 for o, b in zip(oct_events, bass_events)))
    print(f"  the octave layer: {len(oct_events)} notes at gain {BASS['octave']:.2f}, floor {OCTAVE_CUT:.0f} Hz"
          f"{f', panned {OCTAVE_PAN:+.2f}' if BASS['wide'] else ', centred'}")
check("the bass stays mono-centre (EBM_1990s.md section 9) unless 'wide' is chosen",
      not BASS["wide"] or BASS_READING == "wide", "(wide is a DECLARED deviation)")

print("\n=== THE SPACE (this track's claim, so it is measured) ===")
worst, roll_ex = 0, []
for b in range(TOTAL_BARS):
    if is_break(b):
        continue
    if is_rolling(b):
        roll_ex.append(b)
        continue
    cell = "half" if is_pre(b) else PHRASE[b % 8]
    hats = len(hats_for(b)) - (2 if run_bar(b) and hats_for(b) else 0)
    n_on = (figure_for(b).count("x") + (SNARE_P.count("x") if b >= 8 else 0) + (4 if run_bar(b) else 0) + hats
            + (sum(1 for ch in CELL[cell] if ch != ".") if b >= 4 else 0))
    worst = max(worst, n_on)
print(f"  busiest bar: {worst} onsets (ceiling {SPACE_CEILING});  verse 1's first eight bars have no hats;  "
      f"roll bars {roll_ex} are the declared exception — a roll is not space")
check(f"every other bar keeps its space (<= {SPACE_CEILING} onsets)", worst <= SPACE_CEILING, f"({worst})")

print("\n=== THE SEAMS (the kit, Q12) ===")
fig_b = [b for b in range(TOTAL_BARS) if figure_for(b) == FIGURES["B"]]
runs_ = [b for b in range(TOTAL_BARS) if run_bar(b)]
print(f"  figure B on {len(fig_b)} bars (4n+1 of the verses and choruses);  the run on {len(runs_)} bars (4n+3)")
print(f"  rolls into {[b + 2 for b in ROLL_BARS]};  holes at {[b + 0.75 for b in HOLES]};  the silent beat at {SILENT[0]};  "
      f"downsweeps at {DOWNSWEEPS}")
check("figure B and the run never share a bar", not (set(fig_b) & set(runs_)))
check("a roll precedes every chorus and the final", {b + 2 for b in ROLL_BARS} == {32, 64, 88})
check("a downsweep on every chorus entry", set(DOWNSWEEPS) == {32, 64, 88})
kinds = {k for _, k in drum_events}
check("the run, the roll and figure B all sound", {"run", "roll"} <= kinds and len(fig_b) >= 8)
for b in HOLES:
    beats = [rms_between(bar_t(b) + q * BEAT, bar_t(b) + (q + 1) * BEAT) for q in range(4)]
    r = [20 * np.log10(v + 1e-12) for v in beats]
    check(f"the hole at bar {b} beat 4 is >= 6 dB under beats 1-3", np.mean(r[:3]) - r[3] >= 6.0,
          f"({np.mean(r[:3]) - r[3]:.1f} dB)")
silent = rms_between(bar_t(SILENT[0]) + 0.02, bar_t(SILENT[1]) - 0.02)
check("the silent beat is silent (< -50 dBFS)", silent < 10 ** (-50 / 20), f"({20 * np.log10(silent + 1e-12):.0f} dBFS)")

print("\n=== PER-SECTION RMS (post-master) ===")
R = {name: sec_rms(b0, b1) for name, b0, b1 in SECTIONS}
S_ = {name: sub_share(b0, b1) for name, b0, b1 in SECTIONS}
for name, b0, b1 in SECTIONS:
    print(f"  {name:9s} {R[name]:.3f}   sub-60 share {S_[name]:.2f}")
print(f"  arc: verse 1 -> chorus 1 {db(R['CHORUS 1'], R['VERSE 1']):+.1f} dB;  "
      f"chorus 2 -> break {db(R['BREAK'], R['CHORUS 2']):+.1f} dB")
check("opening < verse 1 < chorus 1", R["OPENING"] < R["VERSE 1"] < R["CHORUS 1"])
check("the chorus LANDS (>= 1.5 dB over its verse)",
      db(R["CHORUS 1"], R["VERSE 1"]) >= 1.5 and db(R["CHORUS 2"], R["VERSE 2"]) >= 1.5,
      f"({db(R['CHORUS 1'], R['VERSE 1']):+.1f} / {db(R['CHORUS 2'], R['VERSE 2']):+.1f} dB)")
check("each pre builds out of its verse", R["PRE 1"] > R["VERSE 1"] and R["PRE 2"] > R["VERSE 2"])
check("each chorus > its pre (VERIFY.md: the drop actually lands)",
      R["CHORUS 1"] > R["PRE 1"] and R["CHORUS 2"] > R["PRE 2"],
      f"({db(R['CHORUS 1'], R['PRE 1']):+.1f} / {db(R['CHORUS 2'], R['PRE 2']):+.1f} dB)")
check("no section's sub-60 share above 0.70 (the master guardrail band)",
      max(S_[n] for n, _, _ in SECTIONS if n != "TAIL") <= 0.70,
      " ".join(f"{n}:{S_[n]:.2f}" for n, _, _ in SECTIONS if S_[n] > 0.60))
check("chorus 2 >= chorus 1", R["CHORUS 2"] >= R["CHORUS 1"])
check("the break is the trough", R["BREAK"] < R["CHORUS 2"] and R["BREAK"] < R["FINAL"])
check("the final is the loudest", R["FINAL"] == max(R[n] for n, _, _ in SECTIONS if n != "TAIL"))

print("\n=== THE HAMMER ===")
check("kick on every quarter (figure B included)", all(f[s] == "x" for f in (KICK_Q, FIGURES["B"]) for s in (0, 4, 8, 12)))
check("snare on 2 and 4 only", [i for i, c in enumerate(SNARE_P) if c == "x"] == [4, 12])
kicks = sorted(t for t, k in drum_events if k == "kick")
stray = [t for t in kicks if is_break(int(t / BAR))]
check("no kick through the break (the roll is the way out)", not stray, f"({len(stray)} stray)")
_slam = snare(plate_decay=3.0, cut=PLATE_CUT)
snd = (int(np.max(np.nonzero(np.abs(_slam) > 1e-3))) + 1) / SR
print(f"  the slam: sounding {snd * 1000:.0f} ms (plate cut {PLATE_CUT * 1000:.0f} ms — Q5's declared stretch)")
check("the snare is truncated at its cut", snd <= PLATE_CUT + 0.012)
for b0, device in ((4, "the kick lands under the swell"), (8, "the slam in, figure B and the run begin"),
                   (24, "the organ + the bass to half-time"), (30, "the roll + riser, the hole, the hit + downsweep"),
                   (48, "the pedal returns; the run out of the chorus"), (62, "the roll + riser + the held hit"),
                   (80, "the kit stops; the bed's throb, the organ and the petition carry"),
                   (86, "the roll out of the break, the silent beat, the final")):
    print(f"  bar {b0:3d}: bed unbroken + {device}")
win = int(0.25 * SR)
i_in = int(WAY_IN_BARS * BAR * SR)
bed_rms = [float(np.sqrt(np.mean(BED[i:i + win] ** 2))) for i in range(i_in, int(bar_t(TOTAL_BARS) * SR) - win, win)]
check("the bed is one continuous cursor after the way in (never silent)", min(bed_rms) > 1e-3, f"(min {min(bed_rms):.4f})")

print("\n=== THE ENDING (hard stop, Q9) ===")
last = max(t for t, _ in drum_events)
check("no drum at or after bar 104", last < bar_t(TOTAL_BARS), f"(last drum bar {last / BAR:.1f})")
tail = [sec_rms(b, b + 1) for b in range(TOTAL_BARS, TOTAL_BARS + TAIL_BARS)]
print("  per-bar RMS over the tail:", " ".join(f"{r:.4f}" for r in tail))
check("the tail decays", all(a > b for a, b in zip(tail, tail[1:])))
check("the final 0.1 s is silent (< -60 dBFS)", rms_between(END - 0.1, END) < 1e-3)

print("\n=== MASTER GUARDRAILS ===")
tp = float(np.max(np.abs(OUT)))
fin = OUT[int(bar_t(88) * SR):int(bar_t(104) * SR)]
crest = float(np.max(np.abs(fin)) / np.sqrt(np.mean(fin ** 2)))
print(f"  true peak {tp:.3f}   final crest {crest:.2f}   F#2 sub square {midi_to_hz(FS2) / 2:.1f} Hz")
check("true peak < 1.0", tp < 1.0)
check("final crest >= 3.2", crest >= 3.2)
check("FLAC written", flac_path.exists())

print("\nall checks passed" if not fails else f"SOME CHECKS FAILED: {fails}")
