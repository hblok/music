#!/usr/bin/env python3
"""Watchfire v2 — the ascent, darker (tracks/ebm, 2026-09-23).

Verdict on v1: "not bad, but still lands a bit flat; the lead is in a happy /
jolly scale; the stompy beat / bass is still commodore-like."  v2 changes:

  * THE HARMONY: Bm G D Em -> Bm G Em F#m (i VI iv v).  The D major III was
    the relative-major chord that made the loop read jolly; the minor v
    (no A#) leans back into the i without a leading tone.
  * THE HOOK: a descending recitation F#4..F#3 instead of the B3->A4 climb,
    with C natural (the flat-2) as the dark neighbour.  Each phrase ends
    lower than it starts; statements lean on F#, the last resolves to B
    (bar 135 plays Bm under it).  The strings are darker (cutoff, bow).
  * THE LOW END: the kick + a sub-boom own the downbeat (no_access's recipe,
    heard and kept); the bass leaves the kick alone in the verses and rises
    (the offbeat cell).  `--bass dense|juno|v1` picks the bass voice:
    dense = sh101_bass_ruin detuned + sine sub, juno = the Juno bass preset,
    v1 = the old sound.  Gate 0.65 on the new readings.
  * THE SEAMS (TODO.md 2b): roll + riser into each chorus and out of the
    trough, the silent beat before the final, a downsweep after the chorus
    hits, kick figure B every 4th bar, a snare run closing each 8-bar phrase,
    the dotted-8th ping-pong on each statement's tail, a quarter-note delay
    on the trough's half-speed phrase, open hats in verse 2.

v1's docstring follows.

Watchfire — the ascent (tracks/ebm, 2026-09-11).  The first 1999-dialect track.

126 BPM, B natural minor, 136 bars + a tail = 4:22, seed 1999.  The
*Saviour* archetype from ../../inspiration/VNV_Empires.md §6: the one
track on *Empires* whose emotional centre is carried without a voice
("warm, compassionate synthesizers conveying melody without vocals"),
which is what this repo is anyway.  Notes: watchfire_notes.md — the
plan, the probe amendments, and the eight answers this script follows.

The load-bearing decision: **the ascent is not an intro.**  Bars 0-16
are the refrain arriving in pieces — one sustained tone, then two, then
the first phrase, then its answer — with the kick entering underneath at
bar 8 and the bass at 12.  The thesis is what is being built, so it
lands early without a swell in front of it.

Four mechanisms keep a rising line peaking at A4 off the Frankfurt arch
(../CLAUDE.md, the trap): the carrier is a detuned SECTION with no
vibrato and no chorus; every note is octave-doubled downward by voicing,
so its centre of mass sits an octave below the trance register; there is
NO ARP anywhere; and the loop has no flat-VII.  Bm G D Em ends on the iv
and leans back into the i, so the harmony is the momentum and the track
never lands — except once, on the very last statement, which resolves to
B.  That is the only resolution in the piece and the verify block checks
it happens once and last.

The era move is one knob: every sampled voice runs `hold=1` with its
lowpass ceiling lifted (the ASR-10, not Groth's 13-bit EPS), and the one
new voice is instruments/rom.py's detuned stack.

Declared beyond the notes: a light sidechain pump (0.30) on the
sustained layers only — bed, orchestra, chant — never the refrain
carrier and never the bass, per EBM_1990s.md §9's lighter-duck rule for
this era.  1999 is pre-loudness-war, so the master stays gentle.

Output: /workspace/music/<NAME>.wav + .flac (44100 Hz stereo 16-bit).
Prints the VERIFY.md blocks; a FAIL never aborts the render.

Listening flags (LISTENING.md; checks are skipped on a partial render):
  --solo lead[,orch]   render only these layers (through the master)
  --mute drums         everything but these
  --slice 40 56        bars [40, 56) only — chorus 1
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

_common.set_tempo(126)                          # BEFORE the instrument imports (they bind the grid)
_common.seed(1999)                              # Empires
from _common import BAR, BEAT, SR, STEP, midi_to_hz, norm                 # noqa: E402
from eps_hit import hit                                                   # noqa: E402
from eps_kick import kick                                                 # noqa: E402
from eps_snare import snare                                               # noqa: E402
from hats import hat                                                      # noqa: E402
from devices import DOTTED_8TH, FIGURES, delay, downsweep, pingpong, riser, roll, run, silent_beat  # noqa: E402
from juno import bass as juno_bass                                        # noqa: E402
from rom import choir, strings                                            # noqa: E402
from seethe import seethe                                                 # noqa: E402
from sh101_bass_ruin import CELLS, note                                   # noqa: E402  (defaults == sh101_bass)

# ------------------------------------------------------------- the piece
NAME = "watchfire_v2"                                 # bump per iteration (watchfire_v2.1 ...)
TOTAL_BARS = 136
TAIL = 3.0                                            # the resolution rings out; no fade-to-nothing
END = TOTAL_BARS * BAR + TAIL
N = int(END * SR)
SECTIONS = [("ASCENT", 0, 16), ("VERSE 1", 16, 32), ("RISE 1", 32, 40), ("CHORUS 1", 40, 56),
            ("VERSE 2", 56, 72), ("RISE 2", 72, 80), ("CHORUS 2", 80, 96), ("TROUGH", 96, 112),
            ("FINAL", 112, 136)]

B2, G2, D3, E3, FS3 = 47, 43, 50, 52, 54             # the chorus roots — they RISE through the loop
BM, G, EM, FSM = (54, 59, 62), (55, 59, 62), (55, 59, 64), (54, 57, 61)
LOOP = [BM, G, EM, FSM]                               # i VI iv v — no D major (III), no A major (flat-VII)
ROOT_OF = {BM: B2, G: G2, EM: E3, FSM: FS3}           # the ROOT, not the lowest note: most chords are inversions
NAME_OF = {BM: "Bm", G: "G", EM: "Em", FSM: "F#m"}
PC = "C C# D D# E F F# G G# A A# B".split()
FORBIDDEN_ROOTS = {9: "A major, the flat-VII", 2: "D major, the relative-major III (v1's jolly chord)"}
BM_SCALE = {11, 1, 2, 4, 6, 7, 9}                     # B natural minor
FLAT_2 = 0                                            # C natural: the Phrygian colour, melody only
HIT_CHORD = (47, 54, 59, 62)                          # B2 F#3 B3 D4
LIFT = 12                                             # the registral lift: a whole octave, so no pitch class moves
LAST_BAR = 135                                        # the resolution bar: Bm under the B, not F#m

NOTE = {"F#3": 54, "G3": 55, "A3": 57, "B3": 59, "C4": 60, "D4": 62, "E4": 64, "F#4": 66}
# one bar per chord: Bm G Em F#m | Bm G Em F#m.  Recitation, stepwise, falling.
HOOK = ["D4 - - - D4 - B3 -", "C4 - B3 - A3 - B3 -", "G3 - - G3 A3 - B3 -", "A3 - - A3 F#3 - - -",
        "F#4 - - - E4 - D4 -", "D4 - C4 - B3 - C4 -", "B3 - G3 - A3 - G3 -", "F#3 - - - - - - -"]
HOOK_RESOLVED = HOOK[:7] + ["F#3 - - - B3 - - -"]     # the last pass, and the only resolution in the track
PHRASE_A, PHRASE_B = HOOK[:4], HOOK[4:]
LEAD_TONE = {"cutoff": 2400.0, "bow": 0.08}           # darker than rom's 3400 / 0.18

CLEAN = {"hold": 1, "lowpass": None}                  # 1999: the ASR-10, not the 13-bit EPS
BASS_RES = 1.8                                        # the Pro One reading: less bite than the SH-101's 2.5
SUB_VERSE, SUB_CHORUS = 0.5, 0.7
# the bass voice, one flag: dense (the ruin fork's unison + sine sub), juno, or v1's sound
BASS_READINGS = {
    "dense": {"gate": 0.65, "tone": {"detune": 18.0, "sub_wave": "sine", "drive": 2.0}},
    "juno":  {"gate": 0.65, "tone": {"cutoff": 300.0, "pluck": 1100.0, "res": 1.3}},
    "v1":    {"gate": 0.50, "tone": {}},
}
VERSE_CELL, RISE_CELL, CHORUS_CELL = "offbeat", "offbeat", "rolling"   # the kick owns the downbeat until the chorus
BOOM_LEN, BOOM_BAND = 0.42, (45.0, 90.0)              # the sub-boom: a beat long, folded into this band
KICK_Q = "x...x...x...x..."
ROLL_BARS = {38, 39, 78, 79, 110, 111}                # 2-bar rolls into chorus 1, chorus 2 and the final
RUN_BARS = {23, 31, 47, 55, 63, 71, 87, 119, 127}     # the snare run closing an 8-bar phrase (no roll there)
SILENT = (112 * BAR - BEAT, 112 * BAR)                # the one silent beat: the last beat before the final
SNARE_P = "....x.......x..."
HAT_ACC = (1.0, 0.5, 0.7, 0.5)
OPEN_STEPS = (2, 6, 10, 14)
KICK_OUT = [(0, 8), (96, 112)]                        # the ascent's first half, and the trough
# the engine sits back in the verses so the chorus is the destination; the stomp
# never stops, it just leans.  Without this the arc measured 0.3 dB verse-to-chorus.
SECTION_GAIN = {"ASCENT": 0.80, "VERSE 1": 0.82, "RISE 1": 0.97, "CHORUS 1": 1.0,
                "VERSE 2": 0.84, "RISE 2": 0.99, "CHORUS 2": 1.0, "TROUGH": 0.0, "FINAL": 1.0}
PUMP_DEPTH, PUMP_TAU, PUMP_FLOOR = 0.30, 0.09, 0.70   # lighter duck (EBM_1990s.md §9), sustained layers only


def bar_t(b):
    return b * BAR


def section_of(bar):
    for name, b0, b1 in SECTIONS:
        if b0 <= bar < b1:
            return name
    return "TAIL"


def is_chorus(b):
    return 40 <= b < 56 or 80 <= b < 96 or 112 <= b < 136


def is_verse(b):
    return 16 <= b < 32 or 56 <= b < 72


def is_rise(b):
    return 32 <= b < 40 or 72 <= b < 80


def chord_at(b):
    return BM if b == LAST_BAR else LOOP[b % 4]


def kick_plays(b):
    return not any(b0 <= b < b1 for b0, b1 in KICK_OUT)


def parse(lines):
    """8th-note token lines -> [(start_8th, midi, len_8ths)]."""
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
    ir = signal.lfilter(b, a, ir)
    return ir / np.sqrt(np.sum(ir ** 2))


IR_L = make_reverb_ir(3.5, 1.3, 7)                    # a longer hall than 1993: the cathedral end of the era
IR_R = make_reverb_ir(3.5, 1.3, 11)


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
    """Constant-power pan of a mono event into a stereo layer pair."""
    a = (pan + 1.0) / 2.0
    add_at(layer[0], x, t, gain * np.cos(a * np.pi / 2))
    add_at(layer[1], x, t, gain * np.sin(a * np.pi / 2))


def place_wide(layer, x, t, gain=1.0, spread=0.012):
    """The section's width: the same mono event, a few ms apart between the
    channels.  No chorus — the detune inside the stack is the movement."""
    add_at(layer[0], x, t, gain)
    add_at(layer[1], x, t + spread, gain)


LAYER_NAMES = ["bed", "orch", "chant", "bass", "boom", "drums", "lead", "hit", "fx"]
WETS = {"bed": 0.0, "orch": 0.40, "chant": 0.45, "bass": 0.0, "boom": 0.0, "drums": 0.06, "lead": 0.30,
        "hit": 0.30, "fx": 0.30}
WEIGHTS = {"bed": 0.24, "orch": 0.34, "chant": 0.26, "bass": 0.36, "boom": 0.18, "drums": 0.42, "lead": 0.46,
           "hit": 0.22, "fx": 0.12}
PUMPED = {"bed", "orch", "chant"}                     # never the refrain carrier, never the bass

ap = argparse.ArgumentParser(description="Watchfire v2 — see the docstring")
ap.add_argument("--bass", default="dense", choices=sorted(BASS_READINGS), help="the bass voice (default dense)")
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

BASS_READING = BASS_READINGS[ARGS.bass]
GATE_FRAC = BASS_READING["gate"]
KICKS = [bar_t(b) + beat * BEAT for b in range(TOTAL_BARS) if kick_plays(b) for beat in range(4)]
PUMP = np.ones(N)
_dip_n = int(0.40 * SR)
_dip = PUMP_DEPTH * np.exp(-np.arange(_dip_n) / SR / PUMP_TAU)
for _t in KICKS:
    _i0 = int(_t * SR)
    _i1 = min(N, _i0 + _dip_n)
    PUMP[_i0:_i1] = np.minimum(PUMP[_i0:_i1], 1.0 - _dip[: _i1 - _i0])
np.clip(PUMP, PUMP_FLOOR, 1.0, out=PUMP)


def commit(name, layer):
    L, R = layer
    pk = max(np.max(np.abs(L)), np.max(np.abs(R)))
    if pk < 1e-9:
        return
    L, R = L / pk, R / pk
    if name in PUMPED:
        L, R = L * PUMP, R * PUMP
    L, R = reverb_pair(L, R, WETS[name])
    MIX[0] += WEIGHTS[name] * L
    MIX[1] += WEIGHTS[name] * R
    if ARGS.stems:
        PRE[name] = (WEIGHTS[name] * L, WEIGHTS[name] * R)


def new_layer():
    return [np.zeros(N), np.zeros(N)]


HOOKS = 0
lead_events = []            # (t, midi, dur, bar, resolved)
orch_events = []            # (bar, chord, octave)
bass_events = []            # (bar, step, midi, cell)
drum_events = []            # (t, kind)
BED = None

# ------------------------------------------------------------------- bed
if want("bed"):
    layer = new_layer()
    BED = norm(seethe(B2, END, throb=0.35, grit=0.25, sub=0.5, rate=0.05))
    add_at(layer[0], BED, 0.0)
    add_at(layer[1], BED, 0.013)                      # the bed is the only width trick here
    commit("bed", layer)

# ---------------------------------------------------------------- the orchestra
# the pad bed under the choruses, and the ONE registral lift: chorus 2 and the
# final's later passes play the same chords an octave up.  The harmony never moves.
if want("orch"):
    layer = new_layer()
    for b in range(TOTAL_BARS):
        if 8 <= b < 16:
            oct_, gain = 0, 0.30                      # under the ascent's second half, thin
        elif is_verse(b):
            oct_, gain = 0, 0.34                      # low and thin
        elif is_rise(b):
            oct_, gain = 0, 0.55                      # the orchestra climbs
        elif 40 <= b < 56:
            oct_, gain = 0, 0.80                      # chorus 1
        elif 80 <= b < 96:
            oct_, gain = LIFT, 0.90                   # chorus 2: THE LIFT
        elif 96 <= b < 112:
            oct_, gain = 0, 0.40                      # the trough, under the chant
        elif 112 <= b < 120:
            oct_, gain = 0, 0.85                      # the final, pass 1
        elif b >= 120:
            oct_, gain = LIFT, 0.95                   # passes 2 and 3: the fusion
        else:
            continue
        ch = chord_at(b)
        place_wide(layer, strings(tuple(m + oct_ for m in ch), BAR), bar_t(b), gain)
        orch_events.append((b, ch, oct_))
    commit("orch", layer)

# ------------------------------------------------------------------ chant
# the Legion take: static, chordal, wordless — and the arp's replacement.
# The probe found it 14.5 dB under the bed at gain 0.42; it sits up here.
if want("chant"):
    layer = new_layer()
    for b in range(TOTAL_BARS):
        if 40 <= b < 56:
            gain = 0.70                               # chorus 1: it enters
        elif 80 <= b < 96:
            gain = 0.80
        elif 96 <= b < 112:
            gain = 1.00                               # the trough: the chant carries it alone
        elif b >= 120:
            gain = 0.90                               # the fusion
        else:
            continue
        place_wide(layer, choir(chord_at(b), BAR), bar_t(b), gain, spread=0.018)
    commit("chant", layer)

# ------------------------------------------------------------------- bass
# verses pedal on B (the EBM tell); rises and choruses follow the loop roots,
# which RISE B2 G2 D3 E3 — the ascent in the low end (Q5).
def bass_note(m, dur, sub):
    tone = BASS_READING["tone"]
    if ARGS.bass == "juno":
        return juno_bass((m,), dur=dur, sub=sub, **tone)
    return note(m, dur=dur, res=BASS_RES, sub=sub, **CLEAN, **tone)


if want("bass"):
    layer = new_layer()
    for b in range(TOTAL_BARS):
        if b < 12 or 96 <= b < 112:
            continue                                  # the bass enters at 12; out through the trough
        if is_verse(b) or b < 16:
            cell, root = VERSE_CELL, B2
        elif is_rise(b):
            cell, root = RISE_CELL, ROOT_OF[chord_at(b)]
        elif is_chorus(b):
            cell, root = CHORUS_CELL, ROOT_OF[chord_at(b)]
        else:
            continue
        sub = SUB_CHORUS if is_chorus(b) else SUB_VERSE
        c = CELLS[cell]
        onsets = [j for j, ch in enumerate(c) if ch != "."]
        for j, s in enumerate(onsets):
            gap = (onsets[j + 1] if j + 1 < len(onsets) else onsets[0] + 16) - s
            m = root + {"x": 0, "o": 12, "5": 7, "7": 10}[c[s]]
            g = SECTION_GAIN[section_of(b)]
            place(layer, bass_note(m, gap * STEP * GATE_FRAC, sub),
                  bar_t(b) + s * STEP, g * (1.0 if s % 4 == 0 else 0.86))
            bass_events.append((b, s, m, cell))
    commit("bass", layer)

# ------------------------------------------------------------------- boom
# no_access's sub-boom: a sine with a short pitch drop under every kick quarter,
# on the chord root folded into 45-90 Hz.  The kick's low end, so the bass
# does not have to be the whole floor.


def boom_hz(root):
    f = midi_to_hz(root)
    while f >= BOOM_BAND[1]:
        f /= 2
    while f < BOOM_BAND[0]:
        f *= 2
    return f


def make_sub_boom(f):
    n = int(BOOM_LEN * SR)
    td = np.arange(n) / SR
    x = np.sin(2 * np.pi * np.cumsum(f * (1.0 + 0.35 * np.exp(-td * 12.0))) / SR)
    return x * (1 - np.exp(-td / 0.003)) * np.exp(-td * 1.2) * np.clip((BOOM_LEN - td) / 0.06, 0, 1)


boom_count = 0
if want("boom"):
    layer = new_layer()
    for t in KICKS:
        b = int(t / BAR + 1e-9)
        if b in ROLL_BARS:
            continue                                  # crescendos don't boom
        root = B2 if is_verse(b) or b < 16 else ROOT_OF[chord_at(b)]
        place(layer, make_sub_boom(boom_hz(root)), t, SECTION_GAIN[section_of(b)])
        boom_count += 1
    commit("boom", layer)

# ------------------------------------------------------------------ drums
if want("drums"):
    layer = new_layer()
    K, S = kick(decay=7.0, **CLEAN), snare(**CLEAN)
    CH, OH = hat(hold=1), hat(open_=True, hold=1)
    ROLL, RUN = roll(S), run(S)
    for b in range(TOTAL_BARS):
        if b in (38, 78, 110):                        # the roll replaces the snare for two bars
            place(layer, ROLL, bar_t(b), 0.9 * (1.0 if b == 110 else SECTION_GAIN[section_of(b)]))
            drum_events.append((bar_t(b), "roll"))
        if 96 <= b < 112:
            continue                                  # the trough: no kit (the roll out of it is above)
        g = SECTION_GAIN[section_of(b)]
        fig = FIGURES["B"] if b % 4 == 3 and b not in ROLL_BARS else KICK_Q
        for s in range(16):
            t = bar_t(b) + s * STEP
            if fig[s] == "x" and kick_plays(b):
                place(layer, K, t, g * (1.0 if s % 4 == 0 else 0.7))
                drum_events.append((t, "kick"))
            if SNARE_P[s] == "x" and b >= 16 and b not in ROLL_BARS and not (b in RUN_BARS and s == 12):
                place(layer, S, t, 0.9 * g)
                drum_events.append((t, "snare"))
            if b >= 16:
                place(layer, CH, t, 0.22 * HAT_ACC[s % 4] * g, pan=-0.2)
                if (is_rise(b) or is_chorus(b) or 56 <= b < 72) and s in OPEN_STEPS:
                    place(layer, OH, t, 0.26 * g, pan=0.25)      # verse 2 gets them too: denser than verse 1
        if b in RUN_BARS:
            place(layer, RUN, bar_t(b) + 12 * STEP, 1.4 * g)     # run() is already at 0.55 of the hit
            drum_events.append((bar_t(b) + 12 * STEP, "run"))
    commit("drums", layer)

# --------------------------------------------------------------------- fx
# the riser under each roll, the downsweep after each chorus-opening hit
if want("fx"):
    layer = new_layer()
    for b in (38, 78, 110):
        place_wide(layer, riser(2), bar_t(b), 1.0)
    for b in (40, 80, 112):
        place_wide(layer, downsweep(1), bar_t(b), 0.8)
    commit("fx", layer)

# ------------------------------------------------------------------- lead
# the refrain, carried by the SECTION: every note voiced (m-12, m) so the
# line plays in two octaves at once — anti-trap mechanism 2.


PINGPONG_GAIN, TROUGH_DELAY_GAIN = 0.45, 0.40
tails = 0


def place_line(layer, lines, bar0, gain=1.0, count=True, slow=1, echo=None):
    """One statement.  slow=2 halves the speed (the trough's reading).
    echo='tail': the dotted-8th ping-pong on the last note; 'quarter': a
    quarter-note delay on every note (the trough's different sound)."""
    global HOOKS, tails
    resolved = lines is HOOK_RESOLVED
    ev = parse(lines)
    for i, (start, midi, ln) in enumerate(ev):
        dur = ln * BEAT / 2 * 0.95 * slow
        x = strings((midi - 12, midi), dur, attack=0.22, **LEAD_TONE)
        t = bar_t(bar0) + start * BEAT / 2 * slow
        place_wide(layer, x, t, gain, spread=0.010)
        lead_events.append((t, midi, dur, bar0, resolved))
        if echo == "tail" and i == len(ev) - 1:
            wl, wr = pingpong(x, DOTTED_8TH, feedback=0.5, taps=6)
            add_at(layer[0], wl, t, gain * PINGPONG_GAIN)
            add_at(layer[1], wr, t, gain * PINGPONG_GAIN)
            tails += 1
        elif echo == "quarter":
            w = delay(x, BEAT, feedback=0.5, taps=4, damp=2500.0)
            add_at(layer[0], w, t, gain * TROUGH_DELAY_GAIN)
            add_at(layer[1], w, t + 0.012, gain * TROUGH_DELAY_GAIN)
    if count:
        HOOKS += 1


if want("lead"):
    layer = new_layer()
    # the ASCENT: the refrain arriving in pieces (not an intro)
    place_wide(layer, strings((B2, 59), 4 * BAR, attack=0.9, **LEAD_TONE), bar_t(0), 0.55)
    place_wide(layer, strings((B2, 59), 2 * BAR, attack=0.6, **LEAD_TONE), bar_t(4), 0.65)
    place_wide(layer, strings((D3, 62), 2 * BAR, attack=0.6, **LEAD_TONE), bar_t(6), 0.65)
    place_line(layer, PHRASE_A, 8, 0.80, count=False)
    place_line(layer, PHRASE_B, 12, 0.85, count=False)
    # the choruses: two statements each, the tails thrown into the ping-pong
    for b0 in (40, 48):
        place_line(layer, HOOK, b0, 0.95, echo="tail")
    for b0 in (80, 88):
        place_line(layer, HOOK, b0, 1.0, echo="tail")
    # the trough: one statement, half speed, alone over the chant, through a quarter-note delay
    place_line(layer, PHRASE_A, 96, 0.75, slow=2, echo="quarter")
    # the final: three passes, the last one resolved
    place_line(layer, HOOK, 112, 1.0, echo="tail")
    place_line(layer, HOOK, 120, 1.0, echo="tail")
    place_line(layer, HOOK_RESOLVED, 128, 1.0)
    commit("lead", layer)

# -------------------------------------------------------------------- hit
if want("hit"):
    layer = new_layer()
    for b in (40, 48, 80, 88, 112, 120, 128):
        place_wide(layer, hit(HIT_CHORD, dur=0.35, **CLEAN), bar_t(b), 1.0)
    commit("hit", layer)

# -------------------------------------------------------------------- mix
for ch in (0, 1):                                     # 1999 is pre-loudness-war: a gentle master
    MIX[ch] = highpass(MIX[ch], 30)
    MIX[ch] = MIX[ch] + 0.20 * lowpass(MIX[ch], 90)
    MIX[ch] = MIX[ch] + 0.18 * highpass(MIX[ch], 3000)
pk = max(np.max(np.abs(MIX[0])), np.max(np.abs(MIX[1]))) + 1e-12
for ch in (0, 1):
    MIX[ch] = np.tanh(1.05 * MIX[ch] / pk) / np.tanh(1.05) * 0.92
# the tail: the resolution rings out over the last 2 s, nothing else composed
t0 = int((TOTAL_BARS * BAR - 0.5) * SR)
ramp = np.ones(N)
ramp[t0:] = 0.5 + 0.5 * np.cos(np.pi * np.arange(N - t0) / (N - t0))
ramp *= silent_beat(N, *SILENT)                       # total silence, bed and reverb tails included
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
for b, what in [(0, "one sustained tone, octave-doubled, over the bed"), (4, "two tones"),
                (8, "the first phrase at speed; the KICK enters"), (12, "its answer; the BASS enters"),
                (16, "verse 1: the B pedal on the offbeats, kick + boom on the beat, snare and hats in"),
                (32, "rise 1: the roots start moving, open hats"), (38, "the roll + riser"),
                (40, "chorus 1: the refrain x2 (ping-pong tails), the chant enters, the hit, the downsweep"),
                (56, "verse 2: open hats (denser than verse 1)"), (72, "rise 2"), (78, "the roll + riser"),
                (80, "chorus 2: THE LIFT — the orchestra an octave up, harmony unchanged"),
                (96, "THE TROUGH: kit out, the chant alone, the refrain at half speed through a quarter delay"),
                (110, "the roll out of the trough, no kick"), (111.75, "THE SILENT BEAT"),
                (112, "the final: pass 1"), (120, "pass 2, the orchestra lifted"),
                (128, "pass 3 — THE ONE RESOLUTION, the line lands on B over Bm"), (136, "the tail rings out")]:
    print(f"  {mmss(bar_t(b)):>6}  bar {b:6.2f}  {what}")

print("\n=== HOOK COUNT ===")
print(f"  full refrain statements: {HOOKS} (target >= 8); the ascent's assembly uncounted")
check("hook count >= 8", HOOKS >= 8)

print("\n=== THE ERA (the dirt ledger) ===")
print(f"  every sampled voice: hold={CLEAN['hold']}, lowpass={CLEAN['lowpass']}  (the ASR-10, not the 13-bit EPS)")
check("decimation off on every sampled voice", CLEAN["hold"] == 1 and CLEAN["lowpass"] is None)
check("no arp layer exists", "arp" not in LAYER_NAMES and "arp" not in globals(),
      "(juno comes in for noise_sweep and the bass preset only — the arp is the trap this dialect leaves out)")

print("\n=== THE LOOP ===")
roots = [ROOT_OF[ch] % 12 for ch in LOOP]
print(f"  {' '.join(NAME_OF[ch] for ch in LOOP)} = i VI iv v;  roots {[PC[r] for r in roots]}")
for ch in LOOP:
    if min(ch) % 12 != ROOT_OF[ch] % 12:
        print(f"    {NAME_OF[ch]} is voiced as an inversion (lowest note {PC[min(ch) % 12]}, "
              f"root {PC[ROOT_OF[ch] % 12]}) — the check reads ROOT_OF, not min()")
for r, why in FORBIDDEN_ROOTS.items():
    check(f"no {why}", r not in roots)
check("every chord's notes belong to B natural minor", all(m % 12 in BM_SCALE for ch in LOOP for m in ch))
check("the loop ends on the MINOR v (no A#, no leading tone) and leans back", LOOP[-1] is FSM and 10 not in FSM)
mel_pcs = {m % 12 for _, m, _ in parse(HOOK)}
check("the hook uses B natural minor + the flat-2 only", mel_pcs <= BM_SCALE | {FLAT_2},
      f"{sorted(PC[p] for p in mel_pcs)}")
check("the flat-2 (C natural) is in the hook", FLAT_2 in mel_pcs)
check("the natural 2 (C#, v1's bright step) is gone from the hook", 1 not in mel_pcs)

print("\n=== THE ASCENT BUILDS ===")
blocks = [{59}, {59, 62}, {m for _, m, _ in parse(PHRASE_A)}, {m for _, m, _ in parse(PHRASE_B)}]
sizes = [len(b) for b in blocks]
print(f"  distinct melody pitches per 4-bar block, bars 0-16: {sizes}")
check("the ascent builds (pitch count never decreases)", all(a <= b for a, b in zip(sizes, sizes[1:])))
first_full = min(t for t, _, _, b0, _ in lead_events if b0 >= 40)
print(f"  first FULL refrain statement at {mmss(first_full)} (bar {first_full / BAR:.0f})")
check("the instrumental centre lands inside the first third",
      first_full < TOTAL_BARS * BAR / 3, f"(first third ends {mmss(TOTAL_BARS * BAR / 3)})")

print("\n=== THE REFRAIN SINGS ===")
ev = parse(HOOK)
onsets = len(ev)
density = onsets / (len(HOOK) * 16)
held = sum(1 for _, _, ln in ev if ln >= 2) / onsets
run = best = 0
for _, _, ln in ev:
    run = run + 1 if ln == 1 else 0
    best = max(best, run)
midis = [m for _, m, _ in ev]
phrases = [[m for _, m, _ in parse(p)] for p in (PHRASE_A, PHRASE_B)]
steps = [b - a for ph in phrases for a, b in zip(ph[:-1], ph[1:]) if b != a]   # within a phrase
downs = sum(1 for d in steps if d < 0) / len(steps)
print(f"  onsets {onsets}  density {density:.2f} (0.20-0.50)  held {held:.2f} (>= 0.5)  "
      f"longest 8th run {best} (<= 6)  {onsets / (len(HOOK) * BAR):.1f} notes/s")
print(f"  DESCENT: register {min(midis)}-{max(midis)}, doubled down to {min(midis) - 12};  "
      f"down-steps {downs:.2f};  max step {max(abs(d) for d in steps)} st;  "
      f"phrases {[(PC[p[0] % 12], PC[p[-1] % 12]) for p in phrases]}")
check("density window 0.20-0.50", 0.20 <= density <= 0.50)
check("held fraction >= 0.5", held >= 0.5)
check("run ceiling <= 6", best <= 6)
check("the line falls: down-steps >= 0.6", downs >= 0.6, f"({downs:.2f})")
check("every phrase ends lower than it starts", all(p[-1] < p[0] for p in phrases))
check("stepwise inside a phrase (max step <= 4 st)", max(abs(d) for d in steps) <= 4)
check("register inside the declared 54-66 (a fifth below v1's ceiling)", min(midis) >= 54 and max(midis) <= 66)

print("\n=== THE ONE RESOLUTION ===")
resolved_bars = sorted({b0 for _, _, _, b0, r in lead_events if r})
last_notes = {b0: max((t, m) for t, m, _, bb, _ in lead_events if bb == b0)[1]
              for b0 in (40, 48, 80, 88, 112, 120, 128)}
print("  last note of each statement: " + "  ".join(f"bar {b}:{PC[m % 12]}" for b, m in sorted(last_notes.items())))
check("exactly one statement resolves to the tonic", len(resolved_bars) == 1, f"{resolved_bars}")
check("and it is the last one", resolved_bars == [128])
check("every other statement leans on the fifth (F#, over the minor v)",
      all(m % 12 == 6 for b, m in last_notes.items() if b != 128))
check("the resolution sits on Bm (bar 135), not F#m", chord_at(LAST_BAR) is BM and last_notes[128] % 12 == 11)

print("\n=== PER-SECTION RMS (post-master) ===")
R = {name: sec_rms(b0, b1) for name, b0, b1 in SECTIONS}
S = {name: sub_share(b0, b1) for name, b0, b1 in SECTIONS}
for name, b0, b1 in SECTIONS:
    print(f"  {name:9s} {R[name]:.3f}   sub-60 share {S[name]:.2f}")
db = lambda a, b: 20 * np.log10(a / b)
print(f"  arc: verse 1 -> chorus 1 {db(R['CHORUS 1'], R['VERSE 1']):+.1f} dB;  "
      f"verse 1 -> rise 1 {db(R['RISE 1'], R['VERSE 1']):+.1f} dB;  "
      f"chorus 2 -> trough {db(R['TROUGH'], R['CHORUS 2']):+.1f} dB")
check("ascent < verse 1 < chorus 1", R["ASCENT"] < R["VERSE 1"] < R["CHORUS 1"])
check("the chorus LANDS, not just wins (>= 1.5 dB over its verse)",
      db(R["CHORUS 1"], R["VERSE 1"]) >= 1.5 and db(R["CHORUS 2"], R["VERSE 2"]) >= 1.5,
      f"({db(R['CHORUS 1'], R['VERSE 1']):+.1f} / {db(R['CHORUS 2'], R['VERSE 2']):+.1f} dB)")
check("each rise builds out of its verse, not down from it",
      R["RISE 1"] > R["VERSE 1"] and R["RISE 2"] > R["VERSE 2"])
check("each chorus > its rise", R["CHORUS 1"] > R["RISE 1"] and R["CHORUS 2"] > R["RISE 2"])
check("chorus 2 >= chorus 1", R["CHORUS 2"] >= R["CHORUS 1"])
check("the trough is the trough", R["TROUGH"] < R["CHORUS 2"] and R["TROUGH"] < R["FINAL"])
check("the final is the loudest", R["FINAL"] == max(R.values()))

print("\n=== THE REGISTRAL LIFT ===")
med = {}
for tag, b0, b1 in (("chorus 1", 40, 56), ("chorus 2", 80, 96)):
    ps = [m for b, ch, o in orch_events if b0 <= b < b1 for m in ch]
    os_ = [o for b, _, o in orch_events if b0 <= b < b1]
    med[tag] = float(np.median(ps)) + float(np.median(os_))
    print(f"  {tag}: orchestra median pitch {med[tag]:.0f} (octave offset {int(np.median(os_))})")
c1 = [tuple(sorted(ROOT_OF[ch] % 12 for _ in (0,))) for b, ch, o in orch_events if 40 <= b < 56]
c2 = [tuple(sorted(ROOT_OF[ch] % 12 for _ in (0,))) for b, ch, o in orch_events if 80 <= b < 96]
check("chorus 2 sits an octave above chorus 1", med["chorus 2"] - med["chorus 1"] >= 12,
      f"(+{med['chorus 2'] - med['chorus 1']:.0f} semitones)")
check("the lift is a whole octave, so no pitch class changes", LIFT % 12 == 0, f"(+{LIFT})")
check("the chord roots are unchanged between the two choruses", c1 == c2)

print("\n=== THE STOMP ===")
check("kick on every quarter", all(KICK_Q[s] == "x" for s in (0, 4, 8, 12)), KICK_Q)
check("snare on 2 and 4 only", [i for i, c in enumerate(SNARE_P) if c == "x"] == [4, 12])
kicks = sorted(t for t, k in drum_events if k == "kick")
stray = [t for t in kicks if not kick_plays(int(t / BAR))]
check("no kick in the ascent's first half or the trough", not stray, f"({len(stray)} stray)")
print(f"  drum onsets {len(drum_events)};  first kick bar {kicks[0] / BAR:.0f};  "
      f"last drum bar {max(t for t, _ in drum_events) / BAR:.0f}")

print("\n=== BASS ===")
per_bar = {}
for b, s, m, c in bass_events:
    per_bar.setdefault(b, []).append((s, m, c))
ok_count = all(len(v) == sum(1 for ch in CELLS[v[0][2]] if ch != ".") for v in per_bar.values())
check("onsets per bar == the declared cell, every bar", ok_count)
print(f"  reading {ARGS.bass!r}: {BASS_READING}")
check("gate duty <= 0.65 (0.5 was the blip; the ruin v3 stretch)", GATE_FRAC <= 0.65, f"(gate {GATE_FRAC})")
check("the verse bass leaves the downbeat to the kick",
      all(s % 4 != 0 for b, s, m, c in bass_events if is_verse(b)))
ledger = [(b, per_bar[b][0][1], ROOT_OF[chord_at(b)]) for b in sorted(per_bar) if is_chorus(b)]
bad = [(b, m, r) for b, m, r in ledger if m != r]
check("chorus root ledger: bass root == chord root every chorus bar", not bad, f"{bad[:3]}" if bad else "")
pedal = {m for b, s, m, c in bass_events if is_verse(b)}
check("the verses pedal on B (the EBM tell)", pedal <= {B2, B2 + 12}, f"{sorted(pedal)}")
for r in (B2, G2, E3, FS3):
    flag = "  <- under the measured-good 55 Hz" if midi_to_hz(r) / 2 < 50 else ""
    print(f"  root {r}: {midi_to_hz(r):.1f} Hz, sub square {midi_to_hz(r) / 2:.1f} Hz{flag}")

print("\n=== THE SEAMS (devices.py) ===")
rolls = sorted(t / BAR for t, k in drum_events if k == "roll")
runs = sorted(int(t / BAR) for t, k in drum_events if k == "run")
sil = rms_between(SILENT[0] + 0.01, SILENT[1] - 0.01)
print(f"  rolls at bars {rolls};  runs at bars {runs};  ping-pong tails {tails};  booms {boom_count}")
check("a roll into every chorus and out of the trough", rolls == [38.0, 78.0, 110.0])
check("every chorus statement but the resolution throws a tail", tails == 6, f"({tails})")
check("the silent beat is silent", sil < 1e-4, f"(rms {sil:.1e})")
check("the boom follows the kick", boom_count > 0 and boom_count <= len(KICKS))
check("verse 2 is denser than verse 1", R["VERSE 2"] > R["VERSE 1"],
      f"({db(R['VERSE 2'], R['VERSE 1']):+.1f} dB)")

print("\n=== MASTER GUARDRAILS ===")
tp = float(np.max(np.abs(OUT)))
fin = OUT[int(bar_t(112) * SR):int(bar_t(136) * SR)]
crest = float(np.max(np.abs(fin)) / np.sqrt(np.mean(fin ** 2)))
print(f"  true peak {tp:.3f}   final crest {crest:.2f}   pump depth {PUMP_DEPTH} on {sorted(PUMPED)}")
check("true peak < 1.0", tp < 1.0)
check("final crest >= 3.2", crest >= 3.2)
check("the pump never touches the refrain carrier or the bass", not ({"lead", "bass"} & PUMPED))
check("FLAC written", flac_path.exists())

print("\nall checks passed" if not fails else f"SOME CHECKS FAILED: {fails}")
