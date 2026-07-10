#!/usr/bin/env python3
"""
morgenland.py — "Morgenland" (~6:12, 142 BPM, C Phrygian dominant).
THE 303 GOES EAST (design notes: morgenland_notes.md — all seven open
questions answered 2026-07-09). Third station of the machine-voice
arc: maschinenherz was a machine heart LEARNING to sing; silver_wire
was the machine singing SOLO; morgenland is the machine singing an
OLD SONG — the wire channels a folk melody centuries older than any
circuit, in a mode no 303 was ever meant to speak.

THE MODE — C Phrygian dominant / Maqam Hijaz: C-Db-E-F-G-Ab-Bb, from
the Persian trance analysis (declared borrow; the Dune ban stays in
force minus ONE sanctioned instrument, see below). The augmented
second Db-E is the signature — the refrain must CROSS it (counted).
The question hangs on Db5 (the b2 screaming over the C pedal — the
F#/D#/E hang lineage); the answer resolves Db->C ACROSS the barline:
the Phrygian cadence, bII->i, the oldest cadence in the book as the
house seam mechanism. The close: a long held Db->C slide.

THE ORNAMENT VOCABULARY (the new melody-rule ingredient — folk
melisma in 303 dialect, all counted and checked):
  grace flick  = 32nd lower-neighbor before a landing ('g' in map)
  mordent turn = main-upper 32nds at a phrase head ('m' in map)
  melisma      = slide chains through 3+ pitches (the mode's
                 portamento; silver_wire's ties, sung eastern)

DECLARED BORROWS: the silver_wire_v2 acid grammar (cell-built runs,
3-cycle accent roll, slide chains, anti-arc CUT_PROFILE — FROZEN
recipe, new notes); the maschinenherz psy engine + kit split
(darbuka & ghost gait OUTSIDE the drops, straight machine INSIDE);
the big-room master (directory default, calibrated: NO deep 55 Hz
shelf); the Persian analysis (mode, C pedal, b2/G excursions).
Q4 SANCTION: ONE Dune instrument crosses the wall — the darbuka
doum/tak layer (dune maqsum recipe) as groove seasoning. Everything
else on the ban list stays banned (no duduk/ney/chant/wind, no D
Phrygian dominant).

THE SECOND VOICE — the santur (hammered dulcimer, synthesized):
detuned string pair, double-strike hammer bounce, tremolo rolls on
held tones. It answers the wire (the low-answer slots, the
turnarounds, the break) and NEVER carries the refrain alone. Bookend:
wire + santur in octaves state the final Db->C — the fusion's last
word.

HARMONY — verses/drops on the C pedal (authentic to source and psy);
choruses AND DROP 2 (Q5: the summit walks) lap C-Db-G-C, the Db bar
the question bar. Pads voice OPEN FIFTHS + color tones (Q3) — maqam
music doesn't think in triads; E-natural belongs to the melody.

  0:00  thesis    The wire alone: the first hijaz phrase over bare C.
  0:07  engine    Kick locks; bass 8, darbuka 12, hats 16 staircase.
  0:34  verse     One full dark statement (-12), santur answers.
  1:01  build 1   Snare roll + swell; composed silent beat.
  1:15  DROP 1    48 bars, machine + wire on the pedal, EVOLVING:
                  statement / dip (kick+santur) / statement 8va answers
                  / Q-half / turnaround runs.
  3:06  chorus 1  The lap walks C-Db-G-C; pads + darbuka return.
  3:33  break     Engine out: santur loops + low fifths + drone.
  4:00  build 2   Bass re-enters FIRST; rolls; silent beat.
  4:14  DROP 2    48 bars, THE SUMMIT WALKS: statements over the lap,
                  a-cappella dip (the naked hijaz), octave doubling.
  5:34  chorus 2  Fullest; last Db->C rings across the outro seam.
  6:01  outro     Strip; the kick fades.
  6:28  bookend   Wire + santur in octaves: the final Db->C, C stated.

Everything synthesized (numpy + scipy). Seed 1001 (the Nights).
Output: /workspace/music/morgenland.wav + morgenland.flac.
"""

import os
import subprocess
import wave
import numpy as np
from scipy import signal

SR = 44100
DURATION = 374.0
N = int(SR * DURATION)
t = np.arange(N) / SR

rng = np.random.default_rng(1001)

BPM = 142.0
BEAT = 60.0 / BPM
BAR = BEAT * 4
STEP = BEAT / 4
T32 = STEP / 2
GRID0 = 0.5


def bar_t(b, beat=0.0):
    return GRID0 + b * BAR + beat * BEAT


# ---------------------------------------------------- section boundaries (bars)
B_ENGINE = 4
B_VERSE = 20
B_BUILD1 = 36
B_DROP1 = 44
B_CHOR1 = 92
B_BREAK = 108
B_BUILD2 = 124
B_DROP2 = 132
B_CHOR2 = 180
B_OUT = 196
B_KSTOP = 212
B_END = 220

D1_DIP = range(B_DROP1 + 16, B_DROP1 + 20)   # kick + the santur only
D2_DIP = range(B_DROP2 + 16, B_DROP2 + 20)   # the wire a cappella
TURN1 = range(B_DROP1 + 44, B_CHOR1)
TURN2 = range(B_DROP2 + 44, B_CHOR2)
ROLL_8TH = (B_BUILD1 + 6, B_BUILD2 + 6)
ROLL_16TH = (B_BUILD1 + 7, B_BUILD2 + 7)


def section_of(b):
    for name, b0 in [("bookend", B_KSTOP), ("outro", B_OUT),
                     ("chorus2", B_CHOR2), ("drop2", B_DROP2),
                     ("build2", B_BUILD2), ("break", B_BREAK),
                     ("chorus1", B_CHOR1), ("drop1", B_DROP1),
                     ("build1", B_BUILD1), ("verse", B_VERSE),
                     ("engine", B_ENGINE)]:
        if b >= b0:
            return name
    return "thesis"


# ---------------------------------------------------------------- helpers

def midi_to_hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def fade(x, fade_in=0.2, fade_out=5.0):
    ni, no = int(fade_in * SR), int(fade_out * SR)
    x[:ni] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(ni) / ni)
    x[-no:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(no) / no)
    return x


def slow_noise(rate_hz, lo=0.0, hi=1.0):
    k = max(4, int(DURATION * rate_hz))
    pts = rng.standard_normal(k)
    pts = np.convolve(pts, np.ones(3) / 3, mode="same")
    ctrl = np.interp(t, np.linspace(0, DURATION, k), pts)
    ctrl = (ctrl - ctrl.min()) / (ctrl.max() - ctrl.min() + 1e-12)
    return lo + (hi - lo) * ctrl


def make_reverb_ir(seconds, decay, seed):
    r = np.random.default_rng(seed)
    n = int(seconds * SR)
    ir = r.standard_normal(n) * np.exp(-np.arange(n) / SR / decay)
    sos = signal.butter(2, 4000, "low", fs=SR, output="sos")
    ir = signal.sosfilt(sos, ir)
    return ir / np.sqrt(np.sum(ir ** 2))


def reverb(x, ir, wet=0.5):
    tail = signal.fftconvolve(x, ir)[: len(x)]
    tail /= np.max(np.abs(tail)) + 1e-12
    tail *= np.max(np.abs(x)) + 1e-12
    return (1 - wet) * x + wet * tail


def add_at(buf, x, start_s, gain=1.0):
    i0 = int(start_s * SR)
    end = min(len(buf), i0 + len(x))
    if end > i0:
        buf[i0:end] += x[: end - i0] * gain


def place_pan(layL, layR, clip, t0, gain, pan):
    add_at(layL, clip, t0, gain * np.cos(pan * np.pi / 2))
    add_at(layR, clip, t0, gain * np.sin(pan * np.pi / 2))


IR_L = make_reverb_ir(4.5, 2.2, 7)
IR_R = make_reverb_ir(4.5, 2.2, 11)

mix_L = np.zeros(N)
mix_R = np.zeros(N)


def commit(layer_L, layer_R, weight, env=None):
    global mix_L, mix_R
    peak = max(np.max(np.abs(layer_L)), np.max(np.abs(layer_R)), 1e-12)
    s = weight / peak
    if env is None:
        mix_L += layer_L * s
        mix_R += layer_R * s
    else:
        mix_L += layer_L * env * s
        mix_R += layer_R * env * s


lay_L = np.zeros(N)
lay_R = np.zeros(N)


def clear():
    lay_L[:] = 0.0
    lay_R[:] = 0.0


# ------------------------------------------------------------- material
# C Phrygian dominant (Maqam Hijaz): C Db E F G Ab Bb. The pads are
# OPEN FIFTHS + color (Q3); the lap is C-Db-G-C from the source's own
# excursions; the bass walks the same roots in drop 2 and choruses.

SCALE_PC = {0, 1, 4, 5, 7, 8, 10}
SCALE_SORTED = sorted(SCALE_PC)

C_V = (48, 55, 60)
DB_V = (49, 56, 61)
G_V = (43, 50, 55)
PAD_LAP = [C_V, DB_V, G_V, C_V]
BASS_LAP = [36, 37, 43, 36]


def scale_below(m):
    for d in range(1, 12):
        if (m - d) % 12 in SCALE_PC:
            return m - d
    return m - 1


def scale_above(m):
    for d in range(1, 12):
        if (m + d) % 12 in SCALE_PC:
            return m + d
    return m + 1


# THE REFRAIN — 16 bars, the silver_wire grammar in hijaz. Each run
# bar is 16 one-step entries (midi or None); slides are index sets
# (melisma chains); ornaments are index->type dicts. The builder
# applies the 3-cycle accent roll (snapping accented chromatics to
# hijaz) and slide targets resolve after assembly. Bars 8 and 16 are
# the two landmarks: the Db5 hang and the held Db->C close.

Q_STEPS = [
    # bar 1 — the home cell: the hijaz tetrachord winds around C
    [60, 61, 64, 61, 60, 59, 60, 61, 64, 65, 64, 61, 60, 61, 60, 64],
    # bar 2 — the cell restated on E (the color tone as station)
    [64, 65, 64, 61, 64, 65, 67, 65, 64, 61, 60, 61, 64, 65, 67, 68],
    # bar 3 — the chromatic snake pours back down
    [68, 67, 66, 65, 64, 61, 60, 59, 60, 61, 64, 65, 64, 62, 61, 60],
    # bar 4 — the octave-displacement roll
    [60, 72, 60, 72, 61, 73, 61, 60, 64, 60, 64, 60, 65, 64, 61, 64],
    # bar 5 — the cell on F, leaning Ab
    [65, 64, 65, 68, 65, 64, 65, 67, 68, 67, 65, 64, 65, 67, 68, 70],
    # bar 6 — the climbing run
    [67, 68, 70, 68, 67, 65, 67, 68, 70, 72, 70, 68, 67, 68, 70, 72],
    # bar 7 — circling under the hang, sliding in
    [72, 73, 72, 70, 68, 70, 72, 73, 72, 70, 72, 73, 74, 73, 72, 73],
]
Q_SLIDES = [{4, 5}, {5, 6}, {4, 5, 6, 7}, {13, 14}, {4, 5},
            {9, 10, 11}, {4, 5, 6, 13, 14}]
Q_ORNS = [{0: "mordent", 8: "flick"}, {0: "mordent"}, {10: "flick"},
          {8: "flick"}, {0: "mordent", 8: "flick"}, {8: "flick"},
          {0: "mordent"}]

A_STEPS = [
    # bar 9 — the answer opens high, rolling down
    [72, 73, 72, 70, 72, 68, 67, 68, 70, 68, 67, 65, 64, 65, 67, 68],
    # bar 10 — the cell on G, descending restatement
    [67, 68, 67, 72, 67, 68, 67, 70, 65, 64, 62, 61, 64, 65, 64, 61],
    # bar 11 — the long melisma pour (the mode's portamento)
    [70, 68, 67, 66, 65, 64, 63, 61, 60, 59, 60, 61, 64, 61, 60, 61],
    # bar 12 — the low octave roll (mirror of bar 4)
    [60, 48, 60, 48, 61, 49, 61, 60, 59, 60, 61, 64, 62, 61, 60, 58],
    # bar 13 — the cell on Ab, falling home
    [68, 67, 68, 72, 68, 67, 68, 70, 67, 65, 64, 61, 64, 65, 64, 61],
    # bar 14 — pedal circling; the only punctuation rests in the runs
    [60, 61, 60, None, 64, 61, 60, 59, 60, 61, 64, None, 61, 60, 58, 56],
    # bar 15 — winding down into the depth
    [60, 59, 60, 64, 61, 60, 59, 58, 56, 58, 60, 61, 60, 58, 56, 55],
]
A_SLIDES = [{3, 4}, {4, 5}, {3, 4, 5, 6, 7, 8}, {5, 6},
            {8, 9, 10}, {4, 5}, {7, 8, 9, 13, 14}]
A_ORNS = [{0: "mordent", 12: "flick"}, {0: "mordent"}, {12: "flick"},
          {7: "flick"}, {0: "mordent", 8: "flick"}, {8: "flick"},
          {10: "flick"}]

# the two landmarks (events are (midi, d16, accent, slide_to, orn)):
BAR8 = [[73, 10, 1, None, None], [None, 2, 0, None, None],   # THE HANG
        [68, 1, 0, None, None], [70, 1, 0, None, None],      # pickup
        [72, 1, 0, None, None], [73, 1, 0, True, None]]      # ...slides on
BAR16 = [[61, 2, 1, None, None], [None, 1, 0, None, None],   # THE CLOSE
         [49, 1, 0, None, None], [61, 12, 0, 60, None]]      # held Db->C


def build_half(bars_steps, bars_slides, bars_orns):
    ev = []
    g = 0
    for steps, sl, orns in zip(bars_steps, bars_slides, bars_orns):
        for i, m in enumerate(steps):
            if m is None:
                ev.append([None, 1, 0, None, None])
                g += 1
                continue
            acc = 1 if g % 3 == 0 else 0
            if acc and (m % 12) not in SCALE_PC:
                m = m + 1 if ((m + 1) % 12) in SCALE_PC else m - 1
            ev.append([m, 1, acc, True if i in sl else None,
                       orns.get(i)])
            g += 1
    return [ev[i * 16:(i + 1) * 16] for i in range(len(bars_steps))]


def resolve_slides(bars):
    flat = [e for bar in bars for e in bar]
    for i, e in enumerate(flat):
        if e[3] is True:
            e[3] = next((f[0] for f in flat[i + 1:] if f[0] is not None),
                        None)
    return bars


THEME_BARS = resolve_slides(
    build_half(Q_STEPS, Q_SLIDES, Q_ORNS) + [BAR8] +
    build_half(A_STEPS, A_SLIDES, A_ORNS) + [BAR16])
THEME = [tuple(e) for bar in THEME_BARS for e in bar]
assert sum(d for _, d, _, _, _ in THEME) == 256


def bars_ev(a, b):
    return [tuple(e) for bar in THEME_BARS[a:b] for e in bar]


THESIS_EV = bars_ev(0, 4)          # the first 4 Q bars — the hook
QHALF_EV = bars_ev(0, 8)           # the declared half-statement
DIP_EV = bars_ev(0, 4)             # the a-cappella fragment
FRAG = bars_ev(0, 2)               # the low mutter
BOOK_EV = bars_ev(12, 16) + [(60, 10, 0, None, None)]   # C is STATED

# per-statement cutoff expression — the FROZEN silver_wire anti-arc
# contract: identical every statement, peak at the hang, sinking for
# the close; never a track-long ramp.
CUT_PROFILE = [1.00, 1.00, 1.05, 1.05, 1.10, 1.15, 1.25, 1.35,
               1.10, 1.05, 1.00, 0.95, 1.00, 1.05, 1.00, 0.90]

# the santur's answer runs — the same grammar, hammered (no slides;
# the santur's melisma is the tremolo). Full-bar mini-runs under the
# two landmarks: Db-leaning under the hang, C-rooted under the close.
ANSW_Q_EV = [tuple(e) for e in resolve_slides(build_half(
    [[61, 60, 61, 64, 61, 60, 61, 65, 64, 61, 60, 59, 60, 61, 64, 61]],
    [set()], [{0: "flick"}]))[0]]
ANSW_A_EV = [tuple(e) for e in resolve_slides(build_half(
    [[57, 56, 57, 60, 58, 56, 55, 53, 55, 56, 58, 60, 61, 60, 58, 60]],
    [set()], [{4: "flick"}]))[0]]
ANSW_LOOP_EV = [tuple(e) for e in resolve_slides(build_half(
    [[60, 61, 60, 64, 60, 61, 60, 65, 64, 61, 60, 61, 64, 65, 64, 61]],
    [set()], [{0: "flick"}]))[0]]

STMTS = []


# ---------------------------------------------------------------- drums
# The psy kit (frozen recipes) + the Q4-sanctioned darbuka. Kit split:
# darbuka & closed-ghost gait OUTSIDE the drops, straight machine
# INSIDE (open-hat offbeats only, bass on sub duty).

def make_kick():
    n = int(0.30 * SR)
    td = np.arange(n) / SR
    f_curve = 45.0 + 105.0 * np.exp(-td * 55.0)
    body = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    sos_c = signal.butter(2, [1800, 9000], "bandpass", fs=SR, output="sos")
    click = signal.sosfilt(sos_c, rng.standard_normal(n)) * np.exp(-td * 700)
    click /= np.max(np.abs(click)) + 1e-12
    env = (1 - np.exp(-td / 0.0008)) * np.exp(-td * 9.0)
    x = (body + 0.45 * click) * env
    return x / (np.max(np.abs(x)) + 1e-12)


def make_hat(open_=False):
    n = int((0.16 if open_ else 0.045) * SR)
    td = np.arange(n) / SR
    sos_h = signal.butter(4, 6500 if open_ else 7000, "high",
                          fs=SR, output="sos")
    x = signal.sosfilt(sos_h, rng.standard_normal(n))
    x *= np.exp(-td * (24 if open_ else 100))
    return x / (np.max(np.abs(x)) + 1e-12)


def make_clap():
    n = int(0.26 * SR)
    td = np.arange(n) / SR
    sos_c = signal.butter(2, [900, 5200], "bandpass", fs=SR, output="sos")
    nz = signal.sosfilt(sos_c, rng.standard_normal(n))
    nz /= np.max(np.abs(nz)) + 1e-12
    env = np.zeros(n)
    for k, (dt, g) in enumerate([(0.0, 1.0), (0.011, 0.75), (0.023, 0.6),
                                 (0.035, 0.9)]):
        i0 = int(dt * SR)
        env[i0:] = np.maximum(env[i0:],
                              g * np.exp(-(td[: n - i0]) * (24 if k == 3
                                                            else 90)))
    return nz * env


def make_crash():
    n = int(1.6 * SR)
    td = np.arange(n) / SR
    sos_h = signal.butter(4, 5000, "high", fs=SR, output="sos")
    x = signal.sosfilt(sos_h, rng.standard_normal(n)) * np.exp(-td * 3.2)
    return x / (np.max(np.abs(x)) + 1e-12)


def make_zap():
    n = int(0.22 * SR)
    td = np.arange(n) / SR
    f_curve = 2400.0 * np.exp(-td * 26.0) + 90.0
    x = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    x *= np.exp(-td * 20.0)
    return x / (np.max(np.abs(x)) + 1e-12)


def make_snare():
    n = int(0.16 * SR)
    td = np.arange(n) / SR
    tone = 0.5 * np.sin(2 * np.pi * 185.0 * td) * np.exp(-td * 40)
    sos_n = signal.butter(2, [1500, 9000], "bandpass", fs=SR, output="sos")
    nz = signal.sosfilt(sos_n, rng.standard_normal(n)) * np.exp(-td * 30)
    nz /= np.max(np.abs(nz)) + 1e-12
    x = tone + 0.8 * nz
    return x / (np.max(np.abs(x)) + 1e-12)


# the Q4 borrow — the dune darbuka kit, verbatim recipe:
def make_doum():
    n = int(0.30 * SR)
    td = np.arange(n) / SR
    f_curve = 55.0 + 35.0 * np.exp(-td * 28.0)
    body = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    ring = 0.25 * np.sin(2 * np.pi * 190.0 * td) * np.exp(-td * 35)
    env = np.exp(-td * 14.0) * (1 - np.exp(-td / (1.0 / 600)))
    return (body + ring) * env


def make_tek(ghost=False):
    n = int(0.09 * SR)
    td = np.arange(n) / SR
    sos_h = signal.butter(4, [2500, 9000], "bandpass", fs=SR, output="sos")
    slap = signal.sosfilt(sos_h, rng.standard_normal(n))
    ping = 0.4 * np.sin(2 * np.pi * 640.0 * td)
    env = np.exp(-td * (90.0 if ghost else 55.0))
    x = (slap / (np.max(np.abs(slap)) + 1e-12) + ping) * env
    return x * (0.35 if ghost else 1.0)


KICK = make_kick()
OHAT = make_hat(open_=True)
CHAT = make_hat()
CLAP = make_clap()
CRASH = make_crash()
ZAP = make_zap()
SNARE = make_snare()
DOUM = make_doum()
TEK = make_tek()
KA = make_tek(ghost=True)


def kick_on(b):
    s = section_of(b)
    if s in ("thesis", "break", "bookend"):
        return False
    if b in D2_DIP:
        return False
    if B_BUILD2 <= b < B_BUILD2 + 6:
        return False
    return True


def kick_gain(b):
    s = section_of(b)
    if s in ("engine", "verse"):
        return 0.8
    if s == "build1":
        return 0.6
    if s == "chorus1":
        return 0.95
    if s == "outro":
        return 0.9 - 0.45 * (b - B_OUT) / (B_KSTOP - B_OUT)
    return 1.0


clear()
for b in range(B_END):
    if not kick_on(b):
        continue
    if b in ROLL_8TH:
        for e in range(8):
            gg = 0.55 + 0.45 * e / 7
            add_at(lay_L, KICK, bar_t(b, e * 0.5), gg)
            add_at(lay_R, KICK, bar_t(b, e * 0.5), gg)
        continue
    if b in ROLL_16TH:                          # ends on the silent beat
        for s16 in range(12):
            gg = 0.55 + 0.45 * s16 / 11
            add_at(lay_L, KICK, bar_t(b, s16 * 0.25), gg)
            add_at(lay_R, KICK, bar_t(b, s16 * 0.25), gg)
        continue
    g = kick_gain(b)
    for beat in range(4):
        add_at(lay_L, KICK, bar_t(b, beat), g)
        add_at(lay_R, KICK, bar_t(b, beat), g)
commit(lay_L, lay_R, 0.32)
print("kick committed")


# sidechain pump (big-room doctrine): every 4-on-the-floor kick ducks
# the sustained layers ~55 %; roll bars don't pump.
pump = np.ones(N)
_dipn = int(0.30 * SR)
_dip = 0.55 * np.exp(-np.arange(_dipn) / SR / 0.10)
PUMP_BEATS = 0
for _b in range(B_END):
    if not kick_on(_b) or _b in ROLL_8TH or _b in ROLL_16TH:
        continue
    for _beat in range(4):
        _i0 = int(bar_t(_b, _beat) * SR)
        _end = min(N, _i0 + _dipn)
        pump[_i0:_end] = np.minimum(pump[_i0:_end], 1.0 - _dip[: _end - _i0])
        PUMP_BEATS += 1
np.clip(pump, 0.30, 1.0, out=pump)
print(f"pump curve built ({PUMP_BEATS} ducked beats)")


# ---------------------------------------------------------------- bass
# K-b-b-b contract (duty-checked): bass silent on every kick 16th.
# Roll outside the drops, pure-sine sub duty inside.

def psy_bass_note(midi, dur=STEP * 0.88):
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    for k in range(1, min(20, int(7000 / f)) + 1):
        x += np.sin(2 * np.pi * k * f * td) / k
    sos_b = signal.butter(2, 350, "low", fs=SR, output="sos")
    x = np.tanh(2.0 * signal.sosfilt(sos_b, x))
    env = (1 - np.exp(-td / 0.002)) * np.clip((dur - td) / 0.02, 0, 1)
    x *= env
    return x / (np.max(np.abs(x)) + 1e-12)


def sub_note(midi, dur=STEP * 0.88):
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * td) + 0.3 * np.sin(2 * np.pi * 2 * f * td)
    x *= (1 - np.exp(-td / 0.003)) * np.clip((dur - td) / 0.02, 0, 1)
    return x / (np.max(np.abs(x)) + 1e-12)


PB = {m: psy_bass_note(m) for m in (36, 37, 43, 48, 55)}
SB = {m: sub_note(m) for m in (36, 37, 43)}
BASS_GAP_VIOLATIONS = 0
BASS_EVENTS = 0


def bass_mode(b):
    s = section_of(b)
    if s in ("thesis", "break", "bookend") or b < 8:
        return None
    if b in ROLL_16TH or b in D1_DIP or b in D2_DIP:
        return None
    if s in ("drop1", "drop2"):
        return "sub"
    if s == "outro" and b >= B_OUT + 6:
        return None
    return "roll"


def bass_root(b):
    s = section_of(b)
    if s in ("chorus1", "chorus2", "drop2"):
        return BASS_LAP[b % 4]
    return 36


clear()
for b in range(B_END):
    mode = bass_mode(b)
    if mode is None:
        continue
    g = 0.65 if b < B_DROP1 else 1.0
    if mode == "sub":
        g *= 0.85
    if section_of(b) == "build2":
        g *= 0.5
    root = bass_root(b)
    for beat in range(4):
        for s16, gg in [(1, 0.8), (2, 0.7), (3, 0.95)]:
            m = root
            if mode == "roll" and b % 4 == 3 and beat == 3 \
                    and section_of(b) not in ("chorus1", "chorus2"):
                m = [36, 43, 48][s16 - 1]       # cadence climb C2-G2-C3
            elif mode == "roll" and section_of(b) == "chorus2" \
                    and beat == 3 and s16 == 3:
                m = root + 12                   # octave flick
                if m not in PB:
                    PB[m] = psy_bass_note(m)
            smp = PB[m] if mode == "roll" else SB[m]
            add_at(lay_L, smp, bar_t(b, beat + s16 * 0.25), g * gg)
            add_at(lay_R, smp, bar_t(b, beat + s16 * 0.25), g * gg)
            BASS_EVENTS += 1
            if s16 == 0:
                BASS_GAP_VIOLATIONS += 1
commit(lay_L, lay_R, 0.26, env=pump)   # pumped — the kick owns the low end
print("bass committed (roll outside the drops, sub duty inside)")


# ------------------------------------------------------------- sub boom
# Big-room doctrine: pure sine ONE OCTAVE under the bass root on every
# 4-on-the-floor kick, its own layer. Follows bass_root — drop 2 and
# the choruses keep their walk in the sub.

def make_sub_boom(f):
    n = int(0.40 * SR)                          # beat at 142 is 0.423 s
    td = np.arange(n) / SR
    f_curve = f * (1.0 + 0.35 * np.exp(-td * 12.0))
    x = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    env = ((1 - np.exp(-td / 0.003)) * np.exp(-td * 1.2) *
           np.clip((0.40 - td) / 0.06, 0, 1))
    return x * env


BOOM = {m: make_sub_boom(midi_to_hz(m - 12)) for m in set(BASS_LAP)}

clear()
for b in range(B_END):
    if not kick_on(b) or b in ROLL_8TH or b in ROLL_16TH:
        continue
    g = kick_gain(b)
    boom = BOOM[bass_root(b)]
    for beat in range(4):
        add_at(lay_L, boom, bar_t(b, beat), g)
        add_at(lay_R, boom, bar_t(b, beat), g)
commit(lay_L, lay_R, 0.20)
print("sub boom committed")


# ---------------------------------------------------------------- hats

clear()
for b in range(B_END):
    s = section_of(b)
    if s in ("thesis", "break", "bookend") or b < 16:
        continue
    if b in ROLL_16TH or b in D2_DIP:
        continue
    if s == "build2":
        continue
    if s == "outro" and b >= B_OUT + 4:
        continue
    g = 0.8 if b < B_DROP1 else 1.0
    for beat in range(4):
        add_at(lay_L, OHAT, bar_t(b, beat + 0.5), g * 0.8)
        add_at(lay_R, OHAT, bar_t(b, beat + 0.5), g)
    if s in ("engine", "verse", "chorus1", "chorus2"):
        for s16 in range(16):                   # ghost gait OUTSIDE drops
            if s16 % 2 == 0:
                continue
            p = 0.3 + 0.4 * ((s16 // 2) % 2)
            add_at(lay_L, CHAT, bar_t(b, s16 * 0.25),
                   g * 0.35 * np.cos(p * np.pi / 2))
            add_at(lay_R, CHAT, bar_t(b, s16 * 0.25),
                   g * 0.35 * np.sin(p * np.pi / 2))
commit(lay_L, lay_R, 0.12)
print("hats committed")

# --------------------------------------------------------------- darbuka
# THE Q4 BORROW: maqsum in 16th steps {0:D, 2:T, 6:T, 8:D, 12:T},
# random ghost kas on off-16ths (p=0.3), tek fill every 4th bar.
# OUTSIDE the drops only (the kit split): engine (from bar 12),
# verse, choruses, break-lite.

MAQSUM = {0: ("D", 1.0), 2: ("T", 0.9), 6: ("T", 0.8),
          8: ("D", 0.95), 12: ("T", 0.9)}

clear()
for b in range(B_END):
    s = section_of(b)
    on = (s in ("engine", "verse", "chorus1", "chorus2") and b >= 12) or \
         (s == "break" and b >= B_BREAK + 8)
    if not on or b in ROLL_8TH or b in ROLL_16TH:
        continue
    g = 0.5 if s == "break" else (0.8 if b < B_DROP1 else 1.0)
    for s16 in range(16):
        if s16 in MAQSUM:
            kind, gg = MAQSUM[s16]
            smp = DOUM if kind == "D" else TEK
            p = 0.5 if kind == "D" else (0.35 if s16 < 8 else 0.65)
            place_pan(lay_L, lay_R, smp, bar_t(b, s16 * 0.25), g * gg, p)
        elif s16 % 2 == 1 and rng.random() < 0.3:
            place_pan(lay_L, lay_R, KA, bar_t(b, s16 * 0.25),
                      g * 0.7, float(rng.uniform(0.3, 0.7)))
    if b % 4 == 3:                              # the tek fill
        for k, s16 in enumerate((13, 14, 15)):
            place_pan(lay_L, lay_R, TEK, bar_t(b, s16 * 0.25),
                      g * (0.5 + 0.2 * k), 0.4 + 0.1 * k)
commit(lay_L, lay_R, 0.10)
print("darbuka committed (the one sanctioned borrow; outside the drops)")

# claps on 2 & 4 — drops (from +20) and choruses
clear()
for b in range(B_END):
    s = section_of(b)
    on = (B_DROP1 + 20 <= b < B_CHOR1 and b not in TURN1) or \
         (s == "drop2" and b not in D2_DIP) or s in ("chorus1", "chorus2")
    if not on or b in D1_DIP:
        continue
    for beat in (1, 3):
        p = 0.42 if beat == 1 else 0.58
        place_pan(lay_L, lay_R, CLAP, bar_t(b, beat), 1.0, p)
commit(lay_L, lay_R, 0.10)
print("claps committed")

clear()
for b, g in [(B_ENGINE, 0.4), (B_DROP1, 1.0), (B_CHOR1, 0.9),
             (B_BREAK, 0.5), (B_DROP2, 1.0), (B_DROP2 + 20, 0.6),
             (B_CHOR2, 0.9)]:
    place_pan(lay_L, lay_R, CRASH, bar_t(b), g, 0.5)
commit(lay_L, lay_R, 0.05)
print("crashes committed")

clear()
for b in ([B_DROP1 + k for k in (0, 8, 20, 28, 36, 44)] +
          [B_DROP2 + k for k in (0, 8, 20, 28, 36, 44)]):
    beat = float(rng.choice([0.0, 1.5, 3.5]))
    p = rng.uniform(0.2, 0.8)
    add_at(lay_L, ZAP, bar_t(b, beat), np.cos(p * np.pi / 2))
    add_at(lay_R, ZAP, bar_t(b, beat), np.sin(p * np.pi / 2))
lay_L = reverb(lay_L, IR_L, wet=0.35)
lay_R = reverb(lay_R, IR_R, wet=0.35)
commit(lay_L, lay_R, 0.08)
print("zaps committed")

clear()
for b16, b32 in zip(ROLL_8TH, ROLL_16TH):
    for s16 in range(16):
        place_pan(lay_L, lay_R, SNARE, bar_t(b16, s16 * 0.25),
                  0.35 + 0.35 * s16 / 15, 0.45)
    for s32 in range(24):
        place_pan(lay_L, lay_R, SNARE, bar_t(b32, s32 * 0.125),
                  0.6 + 0.4 * s32 / 23, 0.55)
commit(lay_L, lay_R, 0.09)
print("snare rolls committed")

clear()


def swell(dur):
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = signal.sosfilt(signal.butter(2, [250, 2400], "bandpass",
                                     fs=SR, output="sos"),
                       rng.standard_normal(n))
    x *= (td / dur) ** 2.5
    return x / (np.max(np.abs(x)) + 1e-12)


SW = swell(4 * BAR)
add_at(lay_L, SW, bar_t(B_DROP1) - 4 * BAR, 1.0)
add_at(lay_R, SW, bar_t(B_DROP1) - 4 * BAR, 0.9)
add_at(lay_L, SW, bar_t(B_DROP2) - 4 * BAR, 0.9)
add_at(lay_R, SW, bar_t(B_DROP2) - 4 * BAR, 1.0)
commit(lay_L, lay_R, 0.05)
print("swells committed")


# ---------------------------------------------------------------- THE 303
# FROZEN silver_wire voice: Q 6, feedback 1.3/1.35, tanh(1.5), rolled
# partials, sine body core, within-note sweep, slides. Dry, center.

acid_cache = {}


def acid_note(m, cutoff, accent=False, slide_to=None, dur=STEP * 0.92):
    cutoff = float(np.clip(cutoff * (1.5 if accent else 1.0), 200, 6500))
    key = (m, int(cutoff // 40), accent, slide_to, round(dur, 4))
    if key in acid_cache:
        return acid_cache[key]
    f = midi_to_hz(m)
    n = int(dur * SR)
    td = np.arange(n) / SR
    if slide_to is None:
        ph = 2 * np.pi * f * td
    else:
        f2 = midi_to_hz(slide_to)
        fc = f * (f2 / f) ** np.clip((td - 0.45 * dur) / (0.55 * dur), 0, 1)
        ph = 2 * np.pi * np.cumsum(fc) / SR
    x = np.zeros(n)
    for k in range(1, min(40, int(9000 / f)) + 1):
        x += np.sin(k * ph) / k ** 1.3

    def res_lp(sig_in, c):
        c = float(min(c, 8000.0))
        sos_lp = signal.butter(2, c, "low", fs=SR, output="sos")
        y = signal.sosfilt(sos_lp, sig_in)
        bpk, apk = signal.iirpeak(min(c, 7500.0), Q=6.0, fs=SR)
        return y + (1.35 if accent else 1.3) * signal.lfilter(bpk, apk, y)

    bright = res_lp(x, cutoff * 2.5)
    dark = res_lp(x, cutoff * 0.75)
    sweep = np.exp(-td / (0.10 if accent else 0.055))
    y = np.tanh(1.5 * (sweep * bright + (1 - sweep) * dark))
    y += 0.30 * np.sin(ph)
    env = (1 - np.exp(-td / 0.0015)) * np.clip((dur - td) / 0.02, 0, 1)
    y *= env
    y /= np.max(np.abs(y)) + 1e-12
    acid_cache[key] = y
    return y


def place_events(b0, events, octave, base_cut, gain, prof):
    """The wire. Ornaments render INSIDE their slot: flick = 32nd
    lower neighbor then the note; mordent = note+upper as 32nds."""
    cuts = []
    step = 0
    for m, d, acc, sl, orn in events:
        if m is not None:
            cut = base_cut * prof[(step // 16) % len(prof)]
            cut *= 1.0 + 0.10 * np.sin(2 * np.pi * (step % 16) / 16.0)
            cuts.append(cut * (1.5 if acc else 1.0))
            g = gain * (1.1 if acc else 1.0)
            t0 = bar_t(b0, step * 0.25)
            mm = m + octave
            dur = d * STEP * (1.02 if sl else 0.92)
            if orn == "flick":
                lo = scale_below(m) + octave
                x = acid_note(lo, cut, dur=T32 * 0.92)
                add_at(lay_L, x, t0, g * 0.85)
                add_at(lay_R, x, t0, g * 0.85 * 0.97)
                x = acid_note(mm, cut, accent=bool(acc),
                              slide_to=(sl + octave if sl else None),
                              dur=dur - T32)
                add_at(lay_L, x, t0 + T32, g)
                add_at(lay_R, x, t0 + T32, g * 0.97)
            elif orn == "mordent":
                up = scale_above(m) + octave
                x = acid_note(mm, cut, accent=bool(acc), dur=T32 * 0.92)
                add_at(lay_L, x, t0, g)
                add_at(lay_R, x, t0, g * 0.97)
                x = acid_note(up, cut, dur=T32 * 0.92)
                add_at(lay_L, x, t0 + T32, g * 0.85)
                add_at(lay_R, x, t0 + T32, g * 0.85 * 0.97)
                if d >= 2:
                    x = acid_note(mm, cut,
                                  slide_to=(sl + octave if sl else None),
                                  dur=dur - 2 * T32)
                    add_at(lay_L, x, t0 + 2 * T32, g)
                    add_at(lay_R, x, t0 + 2 * T32, g * 0.97)
            else:
                x = acid_note(mm, cut, accent=bool(acc),
                              slide_to=(sl + octave if sl else None),
                              dur=dur)
                add_at(lay_L, x, t0, g)
                add_at(lay_R, x, t0, g * 0.97)
        step += d
    return cuts


def place_statement(b0, stype, octave=0, base=900, gain=1.0,
                    double=False):
    cuts = place_events(b0, THEME, octave, base, gain, CUT_PROFILE)
    if double:
        place_events(b0, THEME, octave + 12, base, gain * 0.38, CUT_PROFILE)
    STMTS.append((b0, stype, float(np.mean(cuts))))


clear()
# thesis: the first 4 Q bars — the hijaz hook, dark
place_events(0, THESIS_EV, 0, 650, 0.9, CUT_PROFILE[:4])
# engine: the low mutters
place_events(8, FRAG, -12, 480, 0.65, CUT_PROFILE[:2])
place_events(14, FRAG, -12, 480, 0.65, CUT_PROFILE[:2])
# verse: ONE full dark statement
place_statement(B_VERSE, "dark", octave=-12, base=620, gain=0.8)
# DROP 1 — two statements + the Q-half, all on the pedal
place_statement(B_DROP1, "home")
place_statement(B_DROP1 + 20, "home")
place_events(B_DROP1 + 36, QHALF_EV, 0, 900, 1.0, CUT_PROFILE[:8])
# chorus 1 — one statement over the walking lap
place_statement(B_CHOR1, "chorus", base=950)
place_events(B_BREAK, [(60, 6, 0, None, None)], 0, 950 * CUT_PROFILE[0],
             0.8, [1.0])                        # the Db->C RESOLVE rings
# break: the wire mutters the pickup at the end
place_events(B_BREAK + 13, FRAG, -12, 500, 0.55, CUT_PROFILE[:2])
# DROP 2 — the summit walks; a-cappella dip; the doubling
place_statement(B_DROP2, "home")
place_events(B_DROP2 + 16, DIP_EV, 0, 900, 1.0,
             CUT_PROFILE[:4])                   # the naked hijaz
place_statement(B_DROP2 + 20, "home", double=True)
place_events(B_DROP2 + 36, QHALF_EV, 0, 900, 1.0, CUT_PROFILE[:8])
# chorus 2 — fullest
place_statement(B_CHOR2, "chorus", base=950, double=True)
place_events(B_OUT, [(60, 6, 0, None, None)], 0, 950 * CUT_PROFILE[0],
             0.8, [1.0])
# outro mutters
place_events(B_OUT + 2, FRAG, -12, 480, 0.5, CUT_PROFILE[:2])
place_events(B_OUT + 6, bars_ev(0, 1), -12, 480, 0.4, CUT_PROFILE[:1])
# bookend: the last 4 A bars + C STATED, at the thesis filter position
place_events(B_KSTOP, BOOK_EV, 0, 650, 0.78, CUT_PROFILE[12:] + [0.9])
commit(lay_L, lay_R, 0.30)
print(f"the wire committed ({len(acid_cache)} cached notes)")


# ---------------------------------------------------------------- santur
# The second voice (Q2): hammered dulcimer — two detuned strings with
# a slight inharmonic stretch, the double-strike hammer bounce, a
# hammer thunk, tremolo rolls on held tones. Answers the wire; never
# the refrain. Warm guardrails: tanh(0.8), sine body, lowpass 3600.

santur_cache = {}


def santur_note(m, dur=STEP * 0.92):
    key = (m, round(dur, 3))
    if key in santur_cache:
        return santur_cache[key]
    f = midi_to_hz(m)
    n = int((dur + 0.9) * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    B = 2.0e-4
    for det in (0.9994, 1.0006):
        for k in range(1, min(18, int(7500 / f)) + 1):
            fk = f * det * k * np.sqrt(1 + B * k * k)
            x += (np.sin(2 * np.pi * fk * td + rng.uniform(0, 6)) /
                  k ** 1.1) * np.exp(-td * (3.0 + 0.7 * k))
    x += 0.12 * np.sin(2 * np.pi * f * td) * np.exp(-td * 3.0)
    sos_th = signal.butter(2, [1800, 6000], "bandpass", fs=SR, output="sos")
    thunk = signal.sosfilt(sos_th, rng.standard_normal(n))
    thunk *= np.exp(-td * 220)
    x += 0.15 * thunk / (np.max(np.abs(thunk)) + 1e-12)
    # the hammer bounce: a second, softer strike 28 ms later
    nb = int(0.028 * SR)
    x[nb:] += 0.5 * x[: n - nb].copy()
    x *= (1 - np.exp(-td / 0.0012))
    sos_lp = signal.butter(2, 3600, "low", fs=SR, output="sos")
    x = np.tanh(0.8 * signal.sosfilt(sos_lp, x))
    x /= np.max(np.abs(x)) + 1e-12
    santur_cache[key] = x
    return x


def santur_trem(m, dur):
    """Tremolo roll — the santur's sustain."""
    n = int((dur + 0.9) * SR)
    out = np.zeros(n)
    hit = santur_note(m, STEP * 0.9)
    tt = 0.0
    while tt < dur:
        g = (0.65 + 0.35 * np.exp(-tt * 1.5)) * rng.uniform(0.85, 1.0)
        i0 = int(tt * SR)
        end = min(n, i0 + len(hit))
        out[i0:end] += hit[: end - i0] * g
        tt += 1.0 / 16.5 * rng.uniform(0.94, 1.06)
    return out / (np.max(np.abs(out)) + 1e-12)


def place_santur(b0, events, octave=0, gain=1.0, pan=0.62):
    step = 0
    for m, d, acc, sl, orn in events:
        if m is not None:
            g = gain * (1.15 if acc else 1.0)
            t0 = bar_t(b0, step * 0.25)
            mm = m + octave
            if d >= 6:
                x = santur_trem(mm, d * STEP * 0.95)
            else:
                x = santur_note(mm, d * STEP * 0.92)
            if orn == "flick":
                lo = santur_note(scale_below(m) + octave, T32 * 0.92)
                place_pan(lay_L, lay_R, lo, t0, g * 0.7, pan)
                place_pan(lay_L, lay_R, x, t0 + T32, g, pan)
            else:
                place_pan(lay_L, lay_R, x, t0, g, pan)
        step += d


clear()
# verse: santur answers under both landmarks (the trades begin)
place_santur(B_VERSE + 7, ANSW_Q_EV, 0, 0.7, 0.6)
place_santur(B_VERSE + 15, ANSW_A_EV, 0, 0.7, 0.4)
# drop 1: the dip is kick + santur; answers under the landmarks
for b in D1_DIP:
    place_santur(b, ANSW_LOOP_EV, 0, 0.9, 0.55)
place_santur(B_DROP1 + 20 + 7, ANSW_Q_EV, 0, 0.85, 0.6)
place_santur(B_DROP1 + 20 + 15, ANSW_A_EV, 0, 0.85, 0.4)
for b in TURN1:
    place_santur(b, ANSW_LOOP_EV, 0, 0.8, 0.45 + 0.1 * (b % 2))
# chorus 1: the trades
place_santur(B_CHOR1 + 7, ANSW_Q_EV, 0, 0.9, 0.62)
place_santur(B_CHOR1 + 15, ANSW_A_EV, 0, 0.9, 0.38)
# THE BREAK: the santur's section — loops and tremolo over the fifths
for k, b in enumerate(range(B_BREAK, B_BREAK + 12)):
    place_santur(b, ANSW_LOOP_EV, 0, 0.68 + 0.03 * k, 0.4 + 0.05 * (k % 4))
for b, m in [(B_BREAK, 60), (B_BREAK + 4, 61), (B_BREAK + 8, 67)]:
    place_santur(b, [(m + 12, 16, 0, None, None)], 0, 0.7, 0.5)
# drop 2: answers + the turnaround
place_santur(B_DROP2 + 7, ANSW_Q_EV, 0, 0.85, 0.6)
place_santur(B_DROP2 + 15, ANSW_A_EV, 0, 0.85, 0.4)
place_santur(B_DROP2 + 20 + 7, ANSW_Q_EV, 0, 0.9, 0.6)
place_santur(B_DROP2 + 20 + 15, ANSW_A_EV, 0, 0.9, 0.4)
for b in TURN2:
    place_santur(b, ANSW_LOOP_EV, 0, 0.85, 0.45 + 0.1 * (b % 2))
# chorus 2: fullest trades, octave up
place_santur(B_CHOR2 + 7, ANSW_Q_EV, 12, 0.85, 0.62)
place_santur(B_CHOR2 + 15, ANSW_A_EV, 12, 0.85, 0.38)
# bookend: the octave double of the wire's last words (the fusion)
place_santur(B_KSTOP, BOOK_EV, 12, 0.4, 0.55)
lay_L = reverb(lay_L, IR_L, 0.4)
lay_R = reverb(lay_R, IR_R, 0.4)
commit(lay_L, lay_R, 0.16)
print(f"santur committed ({len(santur_cache)} cached notes)")


# ------------------------------------------------------------------ pads
# Open fifths + color (Q3): no triads; the melody paints the E/Ab.

def pad_chord(chord, dur, attack=0.35, release=1.0):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    L = np.zeros(n)
    R = np.zeros(n)
    for m in chord:
        f = midi_to_hz(m)
        amp = 0.8 + 0.2 * np.sin(2 * np.pi * rng.uniform(0.02, 0.06) * tt +
                                 rng.uniform(0, 6))
        for det, gL, gR in [(0.9988, 1.0, 0.40), (1.0012, 0.40, 1.0)]:
            ph = 2 * np.pi * f * det * tt + rng.uniform(0, 6)
            v = (np.sin(ph) + 0.30 * np.sin(2 * ph)) * amp
            L += gL * v
            R += gR * v
    env = np.minimum(np.clip(tt / attack, 0, 1) ** 1.5,
                     np.clip((dur - tt) / release, 0, 1))
    sos = signal.butter(2, 800, "low", fs=SR, output="sos")
    L = signal.sosfilt(sos, L * env)
    R = signal.sosfilt(sos, R * env)
    peak = max(np.max(np.abs(L)), np.max(np.abs(R)), 1e-12)
    return L / peak, R / peak


clear()
for b in range(B_CHOR1, B_BREAK):
    pL, pR = pad_chord(PAD_LAP[b % 4], BAR + 0.8)
    add_at(lay_L, pL, bar_t(b), 0.9)
    add_at(lay_R, pR, bar_t(b), 0.9)
for b in range(B_BREAK, B_BUILD2, 4):           # the break: low slow fifths
    v = PAD_LAP[(b // 4) % 4]
    pL, pR = pad_chord(tuple(m - 12 for m in v), 4 * BAR + 1.5,
                       attack=2.0, release=2.5)
    add_at(lay_L, pL, bar_t(b), 0.95)
    add_at(lay_R, pR, bar_t(b), 0.95)
for b in range(B_DROP2, B_CHOR2):
    if b in D2_DIP:
        continue
    pL, pR = pad_chord(PAD_LAP[b % 4], BAR + 0.8)
    add_at(lay_L, pL, bar_t(b), 0.8)
    add_at(lay_R, pR, bar_t(b), 0.8)
for b in range(B_CHOR2, B_OUT):
    v = PAD_LAP[b % 4]
    pL, pR = pad_chord(tuple(v) + (v[-1] + 12,), BAR + 0.8)
    add_at(lay_L, pL, bar_t(b), 0.95)
    add_at(lay_R, pR, bar_t(b), 0.95)
for b in range(B_OUT, B_OUT + 8, 4):
    pL, pR = pad_chord(C_V, 4 * BAR + 1.5, attack=1.5, release=2.5)
    g = 0.8 - 0.35 * (b - B_OUT) / 8
    add_at(lay_L, pL, bar_t(b), g)
    add_at(lay_R, pR, bar_t(b), g)
lay_L = reverb(lay_L, IR_L, 0.5)
lay_R = reverb(lay_R, IR_R, 0.5)
commit(lay_L, lay_R, 0.15, env=pump)   # pumped
print("pads committed")


# ----------------------------------------------------------------- drone
# The low C bed under the thesis/engine and the break.

clear()
drone = (0.6 * np.sin(2 * np.pi * 32.7 * t) +
         1.0 * np.sin(2 * np.pi * 65.4 * t + 0.7) +
         0.25 * np.sin(2 * np.pi * 130.8 * t + 1.9))
drone *= 0.85 + 0.15 * np.sin(2 * np.pi * 0.09 * t)
env_d = (np.clip((t - GRID0) / 4.0, 0, 1) *
         np.clip((bar_t(B_ENGINE + 2) - t) / 5.0, 0, 1) +
         np.clip((t - bar_t(B_BREAK)) / 4.0, 0, 1) *
         np.clip((bar_t(B_BUILD2 + 2) - t) / 4.0, 0, 1))
lay_L += drone * np.clip(env_d, 0, 1)
lay_R += drone * np.clip(env_d, 0, 1)
commit(lay_L, lay_R, 0.07, env=pump)   # pumped
print("drone committed")


# ------------------------------------------------------------------ air

sos_air = signal.butter(4, [150, 1100], "bandpass", fs=SR, output="sos")
air = signal.sosfilt(sos_air, rng.standard_normal(N))
air /= np.max(np.abs(air))
air_env = slow_noise(0.05, 0.4, 1.0)
edge = np.minimum(np.clip((bar_t(B_ENGINE + 2) - t) / 8.0, 0, 1) +
                  np.clip((t - bar_t(B_OUT + 6)) / 16.0, 0, 1), 1.0)
commit(air * air_env * edge, air * air_env[::-1] * edge, 0.04)
print("air committed")


# ---------------------------------------------------------------- master
# The big-room doctrine, calibrated: high + low shelves (NO deep 55 Hz
# shelf — the boom already fills 24-49 Hz), then the tanh bus limiter.

sos_shelf = signal.butter(2, 3000, "high", fs=SR, output="sos")
mix_L += 0.22 * signal.sosfilt(sos_shelf, mix_L)
mix_R += 0.22 * signal.sosfilt(sos_shelf, mix_R)
sos_sub = signal.butter(2, 95, "low", fs=SR, output="sos")
mix_L += 0.34 * signal.sosfilt(sos_sub, mix_L)
mix_R += 0.34 * signal.sosfilt(sos_sub, mix_R)
print("master shelves applied (high + low)")

fade(mix_L)
fade(mix_R)

peak = max(np.max(np.abs(mix_L)), np.max(np.abs(mix_R)))
mix_L = np.tanh(1.35 * mix_L / peak) / np.tanh(1.35) * 0.88
mix_R = np.tanh(1.35 * mix_R / peak) / np.tanh(1.35) * 0.88

stereo = np.empty((N, 2))
stereo[:, 0] = mix_L
stereo[:, 1] = mix_R
pcm = (stereo * 32767.0).astype(np.int16)

OUT_DIR = "/workspace/music"
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, "morgenland.wav")
with wave.open(OUT, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())

print(f"\nCreated: {os.path.abspath(OUT)}")
print(f"Duration: {N / SR:.1f} s  |  {SR} Hz stereo, 16-bit PCM  |  "
      f"{BPM:.0f} BPM, C Phrygian dominant (Maqam Hijaz; the Db-E "
      f"crossing is the color)")

FLAC = os.path.join(OUT_DIR, "morgenland.flac")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", OUT,
                "-vn", "-ar", "44100", "-ac", "2", "-c:a", "flac", FLAC],
               check=True)
print(f"Created: {os.path.abspath(FLAC)}  (lossless flac)")

# ---------------------------------------------------------------- verify form
# silver_wire blocks + the mode/ornament blocks this track exists for.

print("\nSection map:")
SECTIONS = [("thesis", 0), ("engine", B_ENGINE), ("verse (dark)", B_VERSE),
            ("build 1", B_BUILD1), ("DROP 1 (pedal)", B_DROP1),
            ("chorus 1 (lap)", B_CHOR1), ("break (santur)", B_BREAK),
            ("build 2", B_BUILD2), ("DROP 2 (the walk)", B_DROP2),
            ("chorus 2", B_CHOR2), ("outro", B_OUT), ("bookend", B_KSTOP)]
for name, b in SECTIONS:
    print(f"  {bar_t(b):6.1f} s  bar {b:3d}  {name}")
print(f"  {DURATION:6.1f} s  end")

print(f"\nRefrain statements (16 bars, identical maps): {len(STMTS)}")
for b0, stype, mc in STMTS:
    print(f"  bar {b0:3d}  {stype:7s}  mean cutoff {mc:6.1f} Hz")
print("  declared fragments (uncounted): thesis Q bars 1-4, mutters, the "
      f"Q-halves (bars {B_DROP1 + 36}/{B_DROP2 + 36}), the a-cappella dip "
      f"(bar {B_DROP2 + 16}), santur answers, bookend A bars 13-16")

# the melody map + metrics, all from THEME itself
chars = ["."] * 256
pos = 0
SOUNDING = 0
TIED = 0
ONSETS = 0
RESTS = 0
runs = []
cur_run = 0
chains2 = 0
chains3 = 0
cur_chain = 0
FLICKS = 0
MORDENTS = 0
CROSSINGS = 0
prev_m = None
ACC_OFF_SCALE = 0
ACC_COUNT = 0
for m, d, acc, sl, orn in THEME:
    if m is None:
        RESTS += d
        runs.append(cur_run)
        cur_run = 0
        if cur_chain >= 2:
            chains2 += 1
        if cur_chain >= 3:
            chains3 += 1
        cur_chain = 0
    else:
        if acc:
            ACC_COUNT += 1
            if (m % 12) not in SCALE_PC:
                ACC_OFF_SCALE += 1
        if prev_m is not None and {prev_m % 12, m % 12} == {1, 4}:
            CROSSINGS += 1
        prev_m = m
        if orn == "flick":
            FLICKS += 1
            chars[pos] = "g"
        elif orn == "mordent":
            MORDENTS += 1
            chars[pos] = "m"
        else:
            chars[pos] = "O" if acc else "o"
        for k in range(1, d):
            chars[pos + k] = "="
        if sl is not None:
            chars[pos + d - 1] = "/"
        SOUNDING += d
        ONSETS += 1
        if d == 1:
            cur_run += 1
        else:
            runs.append(cur_run)
            cur_run = 0
        if d >= 2 or sl is not None:
            TIED += d
        if sl is not None and d == 1:
            cur_chain += 1
        else:
            if cur_chain >= 2:
                chains2 += 1
            if cur_chain >= 3:
                chains3 += 1
            cur_chain = 0
    pos += d
runs.append(cur_run)
if cur_chain >= 2:
    chains2 += 1
if cur_chain >= 3:
    chains3 += 1
longest_run = max(runs)
tie_frac = TIED / SOUNDING
onset_density = ONSETS / 256.0

# accent cross-rhythm streak (the 3-cycle roll)
bar_res = []
pos = 0
for m, d, acc, sl, orn in THEME:
    if m is not None and acc:
        bar_res.append((pos // 16, pos % 3))
    pos += d
streak = best_streak = 0
prev = None
for bar in range(16):
    res = {r for bb, r in bar_res if bb == bar}
    if len(res) == 1 and (prev is None or res == prev):
        streak += 1
        best_streak = max(best_streak, streak)
    else:
        streak = 1 if len(res) == 1 else 0
    prev = res if len(res) == 1 else None

hang_ok = any(m == 73 and d >= 10 for m, d, _, _, _ in THEME)
close_ok = any(m == 61 and d >= 12 and sl == 60
               for m, d, _, sl, _ in THEME)

print("\nThe refrain map (o/O onset/accent, g flick, m mordent, = held, "
      "'/' slide):")
for bar in range(16):
    print(f"  bar {bar + 1:2d}  {''.join(chars[bar * 16:(bar + 1) * 16])}")
print(f"  onsets {ONSETS}/256 (density {onset_density:.2f}), rests {RESTS}, "
      f"longest run {longest_run}, chains(2+) {chains2}, "
      f"melisma(3+) {chains3}, tied/slid fraction {tie_frac:.2f}")
print(f"  hijaz crossings (Db<->E) {CROSSINGS}, flicks {FLICKS}, "
      f"mordents {MORDENTS}, accents {ACC_COUNT} "
      f"({ACC_OFF_SCALE} off-scale)")

print("\nSeam checklist (what crosses every boundary):")
for b, dev in [(B_ENGINE, "the thesis' last run-note rings; kick enters (crash)"),
               (B_VERSE, "gait unbroken (kick 4 / bass 8 / darbuka 12 / hats 16 staircase done); the dark statement enters mid-groove"),
               (B_BUILD1, "bass keeps rolling; snare roll + swell begin"),
               (B_DROP1, "16th kick roll into the composed silent beat (bar 43 beat 4); swell peaks ON the downbeat"),
               (B_CHOR1, "the santur turnaround (bars 88-91); crash; the lap arrives"),
               (B_BREAK, "chorus close: the Db->C RESOLVE rings across bar 108; engine out, santur takes the floor"),
               (B_BUILD2, "bass re-enters FIRST (the pickup); santur loops hand back to the machine"),
               (B_DROP2, "16th roll + silent beat (bar 131 beat 4); the drop downbeat states C over the WALKING lap"),
               (B_CHOR2, "the santur turnaround (bars 176-179); harmony continuous; crash"),
               (B_OUT, "chorus 2's RESOLVE rings across bar 196; strip begins"),
               (B_KSTOP, "kick stops; wire + santur in octaves at the thesis filter position")]:
    print(f"  bar {b:3d} ({bar_t(b):5.1f} s): {dev}")


def rms_between(b0, b1):
    i0 = int(bar_t(b0) * SR)
    i1 = int(bar_t(b1) * SR) if b1 is not None else N
    return np.sqrt(np.mean(mix_L[i0:i1] ** 2 + mix_R[i0:i1] ** 2) / 2)


print("\nPer-section RMS:")
R = {}
for (name, b0), (_, b1) in zip(SECTIONS, SECTIONS[1:] + [("end", None)]):
    R[name] = rms_between(b0, b1)
    print(f"  {name:18s} {R[name]:.3f}")

# big-room metrics: band shares of the final master + the pump
sos60 = signal.butter(4, 60, "low", fs=SR, output="sos")
sos35 = signal.butter(4, 3500, "high", fs=SR, output="sos")


def band_shares(b0, b1):
    i0 = int(bar_t(b0) * SR)
    i1 = int(bar_t(b1) * SR) if b1 is not None else N
    seg = 0.5 * (mix_L[i0:i1] + mix_R[i0:i1])
    tot = np.sqrt(np.mean(seg ** 2)) + 1e-12
    lo = np.sqrt(np.mean(signal.sosfilt(sos60, seg) ** 2))
    hi = np.sqrt(np.mean(signal.sosfilt(sos35, seg) ** 2))
    return lo / tot, hi / tot


print("\nBig-room metrics (sub-60 Hz / >3.5 kHz share of section RMS):")
SHARES = {}
for (name, b0), (_, b1) in zip(SECTIONS, SECTIONS[1:] + [("end", None)]):
    SHARES[name] = band_shares(b0, b1)
    print(f"  {name:18s} sub {SHARES[name][0]:.2f}   hf {SHARES[name][1]:.2f}")
print(f"  pump: floor {pump.min():.2f}, {PUMP_BEATS} ducked beats, mean in "
      f"drop 1 {np.mean(pump[int(bar_t(B_DROP1) * SR):int(bar_t(B_CHOR1) * SR)]):.2f}")

# the summit comparison lives ABOVE the sub floor (the silver_wire_v3
# practice, declared in the notes): the drops share one machine floor
# by design; >120 Hz is where the added voices live.
sos120 = signal.butter(4, 120, "high", fs=SR, output="sos")
_hp = signal.sosfilt(sos120, 0.5 * (mix_L + mix_R))


def rms_hp(b0, b1):
    return np.sqrt(np.mean(_hp[int(bar_t(b0) * SR):int(bar_t(b1) * SR)] ** 2))


D1_HP = rms_hp(B_DROP1, B_CHOR1)
D2_HP = rms_hp(B_DROP2, B_CHOR2)
print(f"  drops above the sub floor (>120 Hz RMS): "
      f"drop 1 {D1_HP:.3f}, drop 2 {D2_HP:.3f}")

home = [mc for _, s, mc in STMTS if s == "home"]
chor = [mc for _, s, mc in STMTS if s == "chorus"]
rec = [(b, mc) for b, s, mc in STMTS if s in ("home", "chorus")]
xs = np.array([b for b, _ in rec], float)
ys = np.array([mc for _, mc in rec], float)
slope = float(np.polyfit(xs, ys, 1)[0])
checks = [
    ("staircase: engine < verse < drop 1",
     R["engine"] < R["verse (dark)"] < R["DROP 1 (pedal)"]),
    ("the break is the trough between the summits",
     R["break (santur)"] < min(R["chorus 1 (lap)"], R["DROP 2 (the walk)"])),
    (f"drop 2 (the walk) out-sings drop 1 above the sub floor "
     f"(>120 Hz RMS {D2_HP:.3f} > {D1_HP:.3f})", D2_HP > D1_HP),
    ("the summit is drop 2 or chorus 2",
     max(R.values()) in (R["DROP 2 (the walk)"], R["chorus 2"])),
    ("the outro settles; the bookend is the quiet end",
     R["outro"] < R["chorus 2"] and R["bookend"] < R["break (santur)"]),
    (f"refrain count >= 6 (got {len(STMTS)}, 16 bars each)",
     len(STMTS) >= 6),
    ("anti-arc: home statements share one profile "
     f"(spread {max(home) - min(home):.2f} Hz)", max(home) - min(home) < 1.0),
    ("anti-arc: chorus statements share one profile "
     f"(spread {max(chor) - min(chor):.2f} Hz)", max(chor) - min(chor) < 1.0),
    (f"anti-arc: no brightness trend (slope {slope:+.2f} Hz/bar)",
     abs(slope) < 1.0),
    (f"complexity: onset density {onset_density:.2f} >= 0.70",
     onset_density >= 0.70),
    (f"complexity: rests {RESTS} <= 24 of 256", RESTS <= 24),
    (f"complexity: longest unbroken run {longest_run} >= 32",
     longest_run >= 32),
    (f"complexity: accent 3-cycle streak {best_streak} bars >= 4",
     best_streak >= 4),
    (f"complexity: slide chains(2+) {chains2} >= 4", chains2 >= 4),
    (f"sings-not-plinks: tied/slid fraction {tie_frac:.2f} >= 0.25",
     tie_frac >= 0.25),
    (f"mode: all accented onsets in C hijaz ({ACC_COUNT} accents, "
     f"{ACC_OFF_SCALE} off-scale)", ACC_OFF_SCALE == 0),
    (f"mode: hijaz crossings Db<->E {CROSSINGS} >= 4 per 16 bars",
     CROSSINGS >= 4),
    (f"ornaments: flicks {FLICKS} >= 6, mordents {MORDENTS} >= 4, "
     f"melisma chains(3+) {chains3} >= 4",
     FLICKS >= 6 and MORDENTS >= 4 and chains3 >= 4),
    ("landmarks: the Db5 hang (bar 8) and the held Db->C close (bar 16)",
     hang_ok and close_ok),
    (f"K-b-b-b contract: zero bass hits on kick 16ths "
     f"({BASS_EVENTS} bass events)", BASS_GAP_VIOLATIONS == 0),
    (f"big-room: the drops carry the sub (drop1 {SHARES['DROP 1 (pedal)'][0]:.2f}, "
     f"drop2 {SHARES['DROP 2 (the walk)'][0]:.2f} >= 0.55)",
     SHARES["DROP 1 (pedal)"][0] >= 0.55 and
     SHARES["DROP 2 (the walk)"][0] >= 0.55),
    (f"big-room: the top octave is lit (drop1 hf {SHARES['DROP 1 (pedal)'][1]:.2f}, "
     f"drop2 hf {SHARES['DROP 2 (the walk)'][1]:.2f} >= 0.04)",
     SHARES["DROP 1 (pedal)"][1] >= 0.04 and
     SHARES["DROP 2 (the walk)"][1] >= 0.04),
]
print("\nForm checks:")
ok = True
for name, passed in checks:
    print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
    ok &= passed
print("banned by construction: duduk / ney / chant / choir / wind beds / "
      "D Phrygian dominant / gothic piano / rompler strings / TTS / "
      "ladders / ice-cracks / tom fills / reverse cymbal / track-long "
      "filter arc  (darbuka doum/tak = the ONE Q4-sanctioned borrow)")
print("all checks passed" if ok else "SOME CHECKS FAILED")
