#!/usr/bin/env python3
"""Ruin — the hammer (tracks/ebm, 2026-09-12).  Working title Litany.

109 BPM, F# minor, 104 bars + a 4-bar decay = 3:58, seed 2018.  The
*Spiritual Reality* archetype from ../../inspiration/Apop_Soli_Deo_Gloria.md
§3: "hammering beat and mechanical bassline" in the Project Pitchfork
manner, and the blueprint's own brief for it — **"the weight comes from
the tempo, not density."**  This closes the 1993 set: slam 122
(procession), jackhammer 140 (no_access), hammer 109.  Notes:
ruin_notes.md — the plan, the probe amendments and the ten answers.

The load-bearing decision: **the pitch stays on the root; the phrase
happens in the filter, the gate and the accent.**  That is what a real
SH-101 hammer is — the sequencer holds one note and the hands are on the
cutoff — so the verse engine moves four parameters and zero pitches,
with bar 7's walk the only pitch event.  The choruses are where pitch is
finally allowed to move, and that release after 24 bars of refusal is
the track's one harmonic event.

Three anti-drag measures, because every verdict this directory has
collected was about something dragging and 109 is the drag tempo: the
petition is 4 bars so the hook comes round twelve times; verse 2 is half
the length of verse 1 (the song gets impatient); and the engine is a
phrase from bar 1 rather than a repeated cell.

FOUR CHOICES MADE WITHOUT AN ANSWER — flagged for the verdict, all cheap
to change (grep the constant, re-render):
  * OPENING = "blow".  The toll was rejected and no replacement was to
    hand, so probe 10 rendered three; this takes (a) the naked blow,
    the only one that belongs to this archetype alone and the only
    opening in the directory that is a bare drum.  "way_in" and "none"
    are the other two, wired below.
  * The verse pedal.  Both probe readings were liked ("drone-as-phrase
    is good, phrase with moving pitch is als good"), so the track uses
    BOTH as development: verse 1 refuses to move at all, verse 2 answers
    A2 - B2 in its last two bars.  The refusal is the idea; giving in
    once is the development.
  * CHORUS_ROOTS = "up" (F#2 D3 C#3 F#2).  The "down" reading puts D2
    and C#2 sub squares at 37 and 35 Hz, well under the measured-good
    55; "pedal" is procession's answer and would waste the one harmonic
    event.  Fallback is "pedal".
  * KICK_8THS = True in the final chorus (Q7 was "unsure").  The probe
    found it only fits if the hats give up their eighths — 26 onsets a
    bar against this track's ceiling of 24 — so they do.

Output: /workspace/music/<NAME>.wav + .flac (44100 Hz stereo 16-bit).
Prints the VERIFY.md blocks; a FAIL never aborts the render.

Listening flags (LISTENING.md; checks are skipped on a partial render):
  --solo lead[,bass]   render only these layers (through the master)
  --mute drums         everything but these
  --slice 32 48        bars [32, 48) only — chorus 1
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
from eps_hit import hit                                                   # noqa: E402
from eps_kick import kick                                                 # noqa: E402
from eps_snare import snare                                               # noqa: E402
from hats import hat                                                      # noqa: E402
from juno import noise_sweep, organ, pad                                  # noqa: E402
from seethe import seethe                                                 # noqa: E402
from sh101_bass import CELLS, note                                        # noqa: E402

# ------------------------------------------------------------- the piece
NAME = "ruin"                                         # bump per iteration (ruin_v1.1 ...)
TOTAL_BARS = 104
TAIL_BARS = 4                                         # hard stop at 104; the bed and the last hit decay
END = (TOTAL_BARS + TAIL_BARS) * BAR
N = int(END * SR)
SECTIONS = [("OPENING", 0, 8), ("VERSE 1", 8, 24), ("PRE 1", 24, 32), ("CHORUS 1", 32, 48),
            ("VERSE 2", 48, 56), ("PRE 2", 56, 64), ("CHORUS 2", 64, 80), ("BREAK", 80, 88),
            ("FINAL", 88, 104), ("TAIL", 104, 108)]

OPENING = "blow"                                      # "blow" | "way_in" | "none"  (probe 10)
CHORUS_ROOTS = "up"                                   # "up" | "pedal"              (probe 04)
KICK_8THS = True                                      # the final chorus only       (Q7)

FS2, A2, B2, D3, CS3 = 42, 45, 47, 50, 49             # F#2 is home; A2/B2 are verse 2's answer
NOTE = {"F#2": 42, "A2": 45, "C#3": 49, "D3": 50, "E3": 52, "F#3": 54, "G3": 55}
FSM_HI, D_HI, CSM_HI = (57, 61, 66), (57, 62, 66), (56, 61, 64)   # above the refrain's G3 ceiling
LOOP = [FSM_HI, D_HI, CSM_HI, FSM_HI]                 # F#m D C#m F#m: the minor v, never the flat-VII
ROOT_OF = {FSM_HI: FS2, D_HI: D3, CSM_HI: CS3}        # the ROOT, not the lowest note of the voicing
NAME_OF = {FSM_HI: "F#m", D_HI: "D", CSM_HI: "C#m"}
PC = "C C# D D# E F F# G G# A A# B".split()
FORBIDDEN_ROOT = 4                                    # E: the flat-VII chord of F# minor
FSM_SCALE = {6, 8, 9, 11, 1, 2, 4}                    # F# natural minor: F# G# A B C# D E
HIT_CHORD = (42, 49, 54, 57)                          # F#2 C#3 F#3 A3
ORGAN_LOW = (42, 49, 54)

# the petition (bars 1-4) and its response (bars 5-8)
HOOK = ["F#3 - F#3 F#3 G3 - F#3 -", "E3 - - - . F#3 E3 C#3", "D3 - C#3 D3 E3 - D3 -", "C#3 - - - - - . .",
        "F#3 - F#3 F#3 G3 - F#3 -", "E3 - - - . D3 C#3 D3", "E3 - D3 C#3 A2 - - -", "F#2 - - - - - . ."]
PETITION = HOOK[:4]

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
SUB_PRE = 0.45                                        # the pre builds by REMOVING rhythm, not adding weight:
#   at SUB_CHORUS the half-time bass made the pre louder and boomier than the chorus it leads into
PLATE_CUT = 0.22                                      # Q5: the one dialect where the blow rings
CHEST = {32: 1.0, 40: 1.0, 64: 1.15, 72: 1.15, 88: 1.3, 96: 1.3}
SPACE_CEILING = 24                                    # onsets per bar: this track's claim is space

KICK_Q = "x...x...x...x..."
KICK_8 = "x.x.x.x.x.x.x.x."
SNARE_P = "....x.......x..."
HAT_8 = (0, 2, 4, 6, 8, 10, 12, 14)
HAT_ACC = (1.0, 0.5, 0.7, 0.5)
VERSE2_ANSWER = {54: A2, 55: B2}                      # the last two bars of verse 2 give in
SECTION_GAIN = {"OPENING": 0.9, "VERSE 1": 0.84, "PRE 1": 0.90, "CHORUS 1": 1.0, "VERSE 2": 0.86,
                "PRE 2": 0.92, "CHORUS 2": 1.0, "BREAK": 0.0, "FINAL": 1.0, "TAIL": 0.0}


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


def chord_at(b):
    return LOOP[b % 4]


def verse_root(b):
    """Verse 1 refuses to move at all.  Verse 2 answers in its last two
    bars — both probe readings were liked, so the track uses the refusal
    as the idea and giving in once as the development."""
    return VERSE2_ANSWER.get(b, FS2)


def chorus_root(b):
    return FS2 if CHORUS_ROOTS == "pedal" else ROOT_OF[chord_at(b)]


def kick_cell_for(b):
    return KICK_8 if (KICK_8THS and 88 <= b < 104) else KICK_Q


def hats_for(b):
    """8ths only (Q3), none in verse 1's first eight bars, and none at all
    where the kick takes the eighths — 26 onsets a bar would break the
    space ceiling (probe 09)."""
    if b < 8 or (8 <= b < 16) or 80 <= b < 88:
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


LAYER_NAMES = ["bed", "pad", "organ", "bass", "drums", "lead", "hit", "fx"]
WETS = {"bed": 0.0, "pad": 0.35, "organ": 0.32, "bass": 0.0, "drums": 0.08, "lead": 0.25, "hit": 0.30, "fx": 0.3}
WEIGHTS = {"bed": 0.30, "pad": 0.20, "organ": 0.28, "bass": 0.42, "drums": 0.46, "lead": 0.44,
           "hit": 0.24, "fx": 0.12}

ap = argparse.ArgumentParser(description="Ruin — see the docstring")
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
lead_events = []            # (t, midi, dur, bar0, carrier)
bass_events = []            # (bar, step, midi, cell)
drum_events = []            # (t, kind)
BED = None

# ------------------------------------------------------------------- bed
if want("bed"):
    layer = new_layer()
    BED = norm(seethe(FS2, END, throb=0.35, grit=0.30, sub=0.6, rate=0.05))
    add_at(layer[0], BED, 0.0)
    add_at(layer[1], BED, 0.013)
    commit("bed", layer)

# -------------------------------------------------------------------- fx
# only the "way_in" opening uses it; kept wired so switching OPENING is one word
if want("fx") and OPENING == "way_in":
    layer = new_layer()
    place_wide(layer, noise_sweep(3 * BAR, f0=150.0, f1=2500.0, res=2.0), bar_t(0), 1.0)
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
# the liturgical colour: the opening quote, the pre-choruses, chorus 2's
# octave-down doubling, and the break's solo statement of the petition


def organ_note(m, d):
    return organ(m, d, depth=0.0)


if want("organ"):
    layer = new_layer()
    if OPENING == "way_in":
        place_wide(layer, organ(ORGAN_LOW, 3 * BAR, depth=0.0), bar_t(0), 0.55)
    for start, midi, ln in parse(PETITION[:2]):       # the thesis quote, bars 6-8 (uncounted)
        place_wide(layer, organ_note(midi - 12, ln * BEAT / 2 * 0.95), bar_t(6) + start * BEAT / 2, 0.5)
    for b in range(TOTAL_BARS):
        if is_pre(b):
            place_wide(layer, organ(chord_at(b), BAR, depth=0.0), bar_t(b), 0.6)
    for start, midi, ln in parse(HOOK):               # chorus 2: the octave-down double
        place_wide(layer, organ_note(midi - 12, ln * BEAT / 2 * 0.95), bar_t(64) + start * BEAT / 2, 0.40)
    commit("organ", layer)

# ------------------------------------------------------------------ bass
if want("bass"):
    layer = new_layer()
    for b in range(TOTAL_BARS):
        if b < 4 or 80 <= b < 88:
            continue                                  # in at bar 4; out through the break
        if is_pre(b):
            cell = "hole" if b in (31, 63) else "half"
            root, sub = FS2, SUB_PRE
        elif is_chorus(b):
            cell, root, sub = PHRASE[b % 8], chorus_root(b), SUB_CHORUS
        else:
            cell, root, sub = PHRASE[b % 8], verse_root(b), SUB_VERSE
        i = b % 8
        c = CELL[cell]
        g_frac = GATES[i] if cell in ("hammer", "walk") else 0.5
        floor = FLOORS[i] if cell in ("hammer", "walk") else 0.8
        cutoff = (CUTS[i] if cell in ("hammer", "walk") else 2000.0, 250.0)
        sg = SECTION_GAIN[section_of(b)]
        onsets = [j for j, ch in enumerate(c) if ch != "."]
        for j, s in enumerate(onsets):
            gap = (onsets[j + 1] if j + 1 < len(onsets) else onsets[0] + 16) - s
            m = root + INTERVAL[c[s]]
            g = ACCENT.get(s, floor) if c[s] == "x" else 1.0
            place(layer, note(m, dur=gap * STEP * g_frac, cutoff=cutoff, sub=sub),
                  bar_t(b) + s * STEP, sg * g)
            bass_events.append((b, s, m, cell))
    commit("bass", layer)

# ----------------------------------------------------------------- drums
if want("drums"):
    layer = new_layer()
    K = kick(decay=5.0)
    S = snare(plate_decay=3.0, cut=PLATE_CUT)
    H = hat()
    if OPENING == "blow":                             # (a) the hammer announces itself
        for b in range(2):
            for st in (0, 8):
                place(layer, K, bar_t(b) + st * STEP, 1.0)
                place(layer, S, bar_t(b) + st * STEP, 1.15)
                drum_events.append((bar_t(b) + st * STEP, "blow"))
    first = {"blow": 4, "way_in": 4, "none": 0}[OPENING]
    for b in range(TOTAL_BARS):
        if b < first or 80 <= b < 88:
            continue                                  # the break: no kit at all
        sg = SECTION_GAIN[section_of(b)]
        cell, hats = kick_cell_for(b), hats_for(b)
        for s in range(16):
            t = bar_t(b) + s * STEP
            if b in (31, 63) and s >= 12:
                continue                              # the composed hole before each chorus
            if cell[s] == "x":
                place(layer, K, t, sg)
                drum_events.append((t, "kick"))
            if SNARE_P[s] == "x" and b >= 8:
                place(layer, S, t, 1.15 * sg)
                drum_events.append((t, "snare"))
            if s in hats:
                place(layer, H, t, 0.16 * HAT_ACC[s % 4] * sg, pan=-0.2)
    commit("drums", layer)

# ------------------------------------------------------------------ lead


def place_line(layer, lines, bar0, chest, gain=1.0, count=True, octave=0, carrier="dark_lead"):
    global HOOKS
    for start, midi, ln in parse(lines):
        dur = ln * BEAT / 2 * 0.95
        x = dark_lead(midi + octave, dur, chest)
        t = bar_t(bar0) + start * BEAT / 2
        place_wide(layer, x, t, gain, spread=0.008)
        lead_events.append((t, midi + octave, dur, bar0, carrier))
    if count:
        HOOKS += 2 if len(lines) == 8 else 1          # a full Q/A pair is two 4-bar petitions


if want("lead"):
    layer = new_layer()
    for b0 in (32, 40, 64, 72, 88, 96):
        place_line(layer, HOOK, b0, CHEST[b0], 1.0)
    place_line(layer, PETITION, 80, 1.15, 0.85, carrier="organ-doubled")   # the break's statement
    for b0 in (88, 96):                               # the final: + the octave double (the fusion)
        place_line(layer, HOOK, b0, CHEST[b0], 0.30, count=False, octave=12)
    commit("lead", layer)

# ------------------------------------------------------------------- hit
if want("hit"):
    layer = new_layer()
    for b in (32, 40, 64, 72, 88, 96):
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
# the hard stop (Q9): everything composed ends at bar 104; the bed and the
# last hit ring out across the tail and are gone by the end
t0 = int(bar_t(TOTAL_BARS) * SR)
ramp = np.ones(N)
ramp[t0:] = 0.5 + 0.5 * np.cos(np.pi * np.arange(N - t0) / (N - t0))
for ch in (0, 1):
    MIX[ch] *= ramp

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


print("\n=== SECTION MAP ===")
for name, b0, b1 in SECTIONS:
    print(f"  {mmss(bar_t(b0)):>6}  bar {b0:3d}  {name}")
opening_line = {"blow": "the naked blow: kick and slam together, 1.1 s of silence between",
                "way_in": "the way in: the bed swells, a low organ i, one noise sweep",
                "none": "no opening: the engine starts cold"}[OPENING]
for b, what in [(0, f"OPENING = {OPENING!r} — {opening_line}"), (4, "the kick lands; the pedal enters"),
                (6, "the petition quoted on the organ (thesis, uncounted)"),
                (8, "verse 1: the slam in; NO hats for eight bars"), (16, "hats to 8ths; the pad on the pedal"),
                (24, "pre 1: the organ, the bass to half-time"), (31.75, "THE HOLE: no drum, no bass on beat 4"),
                (32, "chorus 1: the petition x4, chest 1.0, the roots move"), (48, "verse 2 (8 bars — the song gets impatient)"),
                (54, "verse 2 ANSWERS: the pedal gives in, A2 then B2"), (56, "pre 2 + the held hit"),
                (64, "chorus 2: chest 1.15, the organ doubling an octave down"),
                (80, "THE BREAK: kit out, the organ states the petition alone"),
                (88, f"the final: chest 1.3, + the octave double" + (", the kick to 8ths (hats out)" if KICK_8THS else "")),
                (104, "HARD STOP; the bed and the last hit ring out")]:
    print(f"  {mmss(bar_t(b)):>6}  bar {b:6.2f}  {what}")

print("\n=== HOOK COUNT ===")
print(f"  4-bar petition statements: {HOOKS} (target >= 12); the organ quote and the octave double uncounted")
check("hook count >= 12", HOOKS >= 12)

print("\n=== THE COUNTER-MEASURE (the pitch stays, the phrase moves) ===")
states = list(zip(CUTS, GATES, FLOORS))
runs, run = [], 1
for a, b in zip(states, states[1:]):
    run = run + 1 if a == b else (runs.append(run) or 1)
runs.append(run)
print(f"  phrase {' '.join(PHRASE)}")
print(f"  cutoff {CUTS} Hz;  gate {GATES};  accent floor {FLOORS}")
v1 = {m for b, s, m, c in bass_events if 8 <= b < 24}
v2 = {m for b, s, m, c in bass_events if 48 <= b < 56}
print(f"  verse 1 pitches {sorted(v1)}   verse 2 pitches {sorted(v2)}")
check("verse 1 refuses to move (root + the walk only)", v1 <= {FS2, FS2 + 7, FS2 + 10, FS2 + 12}, f"{sorted(v1)}")
check("verse 2 gives in once (A2 and B2 appear)", {A2, B2} <= v2)
check("no state holds for more than 2 bars (the cycle turns)", max(runs) <= 2, f"(longest {max(runs)} bars)")
check("gate duty <= 0.5 everywhere (the 1993 figure)", max(GATES) <= 0.5, f"(max {max(GATES)})")

print("\n=== THE LOOP ===")
roots = [ROOT_OF[ch] % 12 for ch in LOOP]
print(f"  {' '.join(NAME_OF[ch] for ch in LOOP)} = i VI v i;  roots {[PC[r] for r in roots]};  "
      f"{PC[FORBIDDEN_ROOT]} major would be the flat-VII")
for ch in set(LOOP):
    if min(ch) % 12 != ROOT_OF[ch] % 12:
        print(f"    {NAME_OF[ch]} is voiced as an inversion (lowest {PC[min(ch) % 12]}, root {PC[ROOT_OF[ch] % 12]})"
              f" — the check reads ROOT_OF, not min()")
check("no flat-VII chord anywhere", FORBIDDEN_ROOT not in roots)
check("every chord's notes belong to F# natural minor", all(m % 12 in FSM_SCALE for ch in LOOP for m in ch))
check("the pad and hit sit above the refrain's G3 ceiling",
      min(m for ch in LOOP for m in ch) > 55, f"(lowest {min(m for ch in LOOP for m in ch)})")

print("\n=== THE REFRAIN ===")
ev = parse(HOOK)
onsets = len(ev)
density = onsets / (len(HOOK) * 16)
held = sum(1 for _, _, ln in ev if ln >= 2) / onsets
run = best = 0
for _, _, ln in ev:
    run = run + 1 if ln == 1 else 0
    best = max(best, run)
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
chests = sorted({c for b0, c in CHEST.items()})
check("the chest arc rises 1.0 -> 1.15 -> 1.3", chests == [1.0, 1.15, 1.3], f"{chests}")

print("\n=== THE SPACE (this track's claim, so it is measured) ===")
worst = 0
for b in range(TOTAL_BARS):
    if 80 <= b < 88:
        continue
    cell = "half" if is_pre(b) else PHRASE[b % 8]
    n_on = (kick_cell_for(b).count("x") + (SNARE_P.count("x") if b >= 8 else 0) + len(hats_for(b))
            + (sum(1 for ch in CELL[cell] if ch != ".") if b >= 4 else 0))
    worst = max(worst, n_on)
print(f"  busiest bar: {worst} onsets (ceiling {SPACE_CEILING});  "
      f"verse 1 first eight bars have no hats at all")
check(f"every bar keeps its space (<= {SPACE_CEILING} onsets)", worst <= SPACE_CEILING, f"({worst})")

print("\n=== PER-SECTION RMS (post-master) ===")
R = {name: sec_rms(b0, b1) for name, b0, b1 in SECTIONS}
S = {name: sub_share(b0, b1) for name, b0, b1 in SECTIONS}
for name, b0, b1 in SECTIONS:
    print(f"  {name:9s} {R[name]:.3f}   sub-60 share {S[name]:.2f}")
db = lambda a, b: 20 * np.log10(a / b)
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
      max(S[n] for n, _, _ in SECTIONS if n != "TAIL") <= 0.70,
      " ".join(f"{n}:{S[n]:.2f}" for n, _, _ in SECTIONS if S[n] > 0.60))
check("chorus 2 >= chorus 1", R["CHORUS 2"] >= R["CHORUS 1"])
check("the break is the trough", R["BREAK"] < R["CHORUS 2"] and R["BREAK"] < R["FINAL"])
check("the final is the loudest", R["FINAL"] == max(R[n] for n, _, _ in SECTIONS if n != "TAIL"))

print("\n=== THE HAMMER ===")
check("kick on every quarter", all(KICK_Q[s] == "x" for s in (0, 4, 8, 12)), KICK_Q)
check("snare on 2 and 4 only", [i for i, c in enumerate(SNARE_P) if c == "x"] == [4, 12])
kicks = sorted(t for t, k in drum_events if k == "kick")
stray = [t for t in kicks if 80 <= t / BAR < 88]
check("no kit through the break", not stray, f"({len(stray)} stray)")
_slam = snare(plate_decay=3.0, cut=PLATE_CUT)
snd = (int(np.max(np.nonzero(np.abs(_slam) > 1e-3))) + 1) / SR
print(f"  the slam: sounding {snd * 1000:.0f} ms (plate cut {PLATE_CUT * 1000:.0f} ms — Q5's declared stretch)")
check("the snare is truncated at its cut", snd <= PLATE_CUT + 0.012)
for b0, device in ((8, "the blow becomes the groove"), (24, "the organ + the bass to half-time"),
                   (32, "the hole, then the hit and the petition"), (48, "the pedal returns"),
                   (64, "the held hit"), (80, "the kit stops; the bed's throb and the organ carry"),
                   (88, "the octave double and the kick to 8ths")):
    print(f"  bar {b0:3d}: bed unbroken + {device}")
win = int(0.25 * SR)
bed_rms = [float(np.sqrt(np.mean(BED[i:i + win] ** 2))) for i in range(0, int(bar_t(TOTAL_BARS) * SR) - win, win)]
check("the bed is one continuous cursor (never silent)", min(bed_rms) > 1e-3, f"(min {min(bed_rms):.4f})")

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
