#!/usr/bin/env python3
"""
flightpath.py — "Flightpath" (~4:45, 138 BPM, C minor). Seed 1900.

THE BEE TRACK — the run at maximum (design notes:
flightpath_notes.md; blueprint:
../../inspiration/Bumblebee_RimskyKorsakov.md). Silver wire proved
the machine can RUN; Bumblebee is the proof a maximum-density run can
stay a PIECE. This track takes the confirmed run grammar and adds the
blueprint's piece engines — a grammar borrow, never a cover: our own
8-bar sentence from the cell vocabulary, the literal tune and the
plunge-gag banned in the foreground.

THE ENGINES (all mechanisms, no pitches):
  - the ANCHOR SYSTEM: fully chromatic 16th cells pinned to chord
    tones on every half-bar downbeat, circling the chord's FIFTH
    (Q2/Q4: the bass owns the root, the line owns the fifth);
  - the TRANSPOSITION MACHINE: no second theme — the sentence
    restates up a perfect 4th (verse 2 = the iv station), episode in
    the bVII minor, breakdown on the bare V pedal, home (the fourths
    ledger, printed);
  - the i<->IV DORIAN VAMP: Cm alternating F MAJOR — the A natural
    is this track's one borrowed colour — closing iv6->V7;
  - the DUEL: hammer bars (one-pitch 16th retrigger) and trill bars
    traded bar-by-bar between the 303 and the stab voice (Q5), under
    augmented-dominant swells; the hammer stays put and trades —
    never climbs into a seam (that move stays maschinenherz's W4a);
  - the SINK AND THE RAMP: register trough on a bare G drone, then a
    WRITTEN two-octave chromatic riser in the melody itself — the
    build is pitches, not noise automation; the recap is the drop;
  - the REGISTER CODA (Q6: fuse AND lift): the final chorus is the
    refrain +12 over a bare pedal, the duel voice's answer material
    sounding under it for the first time;
  - the WEDGE: contrary-motion chromatic voices fanning around a
    pedal — THE seam device of this track;
  - the RISING COLD EXIT: an unbroken ascent to a single high
    staccato flick, hard stop (third use of the tech_noir cold-end
    license, the first that exits UP).

THE VOICE (the 2026-07-11 amendment — user verdict: the saw-core 303
family all sounds the same): the square-core `buzz_path` — the 303's
OTHER waveform, hardware-true and unused by any track. Pulse core
(duty 0.30 / 0.25), rolled partials 1/k^1.25, a round reed formant
(Q 2.8, blend 0.4, never parked — it rides under the within-note
bright->dark sweep, which every 303 keeps), drive tanh(1.0), sine
body. THE RELAY (Q7, the signature): the line hands between two
timbres — A-bright "violin" / B-hollow "clarinet" — at cell
boundaries only. ANTI-GARBLE (Q4 + the morgenland v3 lesson): a
slide chain is ONE note on a smoothed pitch path — one attack, no
re-attacks inside chains; the line is bone dry, center, unpumped.

Anti-arc rule holds: register IS the filter — the cutoff breathes in
a fixed per-bar profile, identical every statement (spread/slope
printed and checked); all development is the pitch axis.

Everything synthesized (numpy + scipy).
Output: /workspace/music/flightpath.wav + flightpath.flac.
"""

import os
import subprocess
import wave
import numpy as np
from scipy import signal

SR = 44100
BPM = 138.0
BEAT = 60.0 / BPM
BAR = BEAT * 4
STEP = BEAT / 4
GRID0 = 0.5

rng = np.random.default_rng(1900)

# ------------------------------------------------- section boundaries (bars)
B_ENGINE = 4
B_VERSE1 = 16
B_VERSE2 = 32
B_DUEL1 = 48
B_DROP1 = 56
B_EPIS = 88
B_DUEL2 = 96
B_SINK = 104
B_DROP2 = 116
B_CODA = 148
B_WATER = 156
B_EXIT = 160
B_END = 163

D1_DIP = range(B_DROP1 + 16, B_DROP1 + 20)   # kick + the low mutter
D2_DIP = range(B_DROP2 + 16, B_DROP2 + 20)   # the line a cappella
ROLL_BARS = (B_DROP1 - 1, B_SINK + 11)       # 16th roll + composed silent beat

DURATION = GRID0 + B_END * BAR
N = int(SR * DURATION)
t = np.arange(N) / SR


def bar_t(b, beat=0.0):
    return GRID0 + b * BAR + beat * BEAT


SECTIONS = [("thesis", 0), ("engine", B_ENGINE), ("verse 1 (i, low)", B_VERSE1),
            ("verse 2 (iv)", B_VERSE2), ("duel 1", B_DUEL1),
            ("DROP 1 (i)", B_DROP1), ("episode (bVII)", B_EPIS),
            ("duel 2", B_DUEL2), ("sink+ramp (V)", B_SINK),
            ("DROP 2 recap", B_DROP2), ("CODA (+12)", B_CODA),
            ("waterfall", B_WATER), ("exit", B_EXIT)]


def section_of(b):
    name = "thesis"
    for n_, b0 in SECTIONS:
        if b >= b0:
            name = n_
    return name


# ------------------------------------------------------------------ helpers

def midi_to_hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def fade(x, fade_in=0.2, fade_out=0.02):
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


# ----------------------------------------------------------------- material
# C minor, the Dorian vamp: Cm alternating F MAJOR (the A natural is
# the borrowed colour), closing iv6 -> V7. The fourths chain:
# i (Cm) -> iv (Fm, verse 2) -> bVII (Bbm, episode) -> V pedal (sink)
# -> i. The line circles the FIFTH of each chord (anchor system).

CM_PC, F_PC = {0, 3, 7}, {5, 9, 0}
FM_PC, G7_PC = {5, 8, 0}, {7, 11, 2, 5}
SCALE_PC = {0, 2, 3, 5, 7, 8, 10}            # C natural minor

# per half-bar of the 8-bar sentence: (chord pcs, fifth pc)
HALF_CHORDS = [(CM_PC, 7), (CM_PC, 7), (F_PC, 0), (F_PC, 0),
               (CM_PC, 7), (CM_PC, 7), (F_PC, 0), (F_PC, 0),
               (CM_PC, 7), (FM_PC, 0), (CM_PC, 7), (G7_PC, 2),
               (CM_PC, 7), (FM_PC, 0), (CM_PC, 7), (G7_PC, 2)]

# pad voicings (bar-level harmonic colour)
CM_V = (48, 55, 63, 67)
F_V = (41, 53, 60, 65)
FM_V = (41, 56, 60, 65)
G7_V = (43, 55, 62, 65)
BBM_V = (46, 58, 65, 70)
AUG_V = (51, 63, 67, 71)                     # Eb+ = {Eb G B}, = G+ pcs
PEDAL_V = (43, 55, 67, 72)                   # the coda's bare pedal
PAD_BARS = [CM_V, F_V, CM_V, F_V, FM_V, G7_V, FM_V, G7_V]

# THE SENTENCE — 8 bars x 16 steps, OUR cells from the blueprint's
# vocabulary (coil, V-turn, snake, roll, climb), anchored per
# HALF_CHORDS. Q = bars 1-4 (descending shapes ask), A = bars 5-8
# (the climbs answer, closing on the G7 -> Cm barline).
SENT_STEPS = [
    # bar 1 — the coil on G (flick lands the upper neighbour) + V-turn
    [67, 66, 65, 64, 69, 68, 67, 66, 67, 66, 65, 64, 65, 66, 67, 68],
    # bar 2 — the coil restated on C5 (F: the vamp brightens), answer on A nat
    [72, 71, 70, 69, 74, 73, 72, 71, 69, 68, 67, 66, 65, 64, 65, 66],
    # bar 3 — the snake pours down, kinks back
    [67, 66, 65, 64, 63, 62, 61, 60, 63, 62, 61, 60, 59, 60, 61, 62],
    # bar 4 — the octave-displacement roll on C (F), climb peeks
    [72, 60, 72, 60, 72, 65, 69, 60, 65, 64, 63, 62, 63, 64, 65, 66],
    # bar 5 — the climb states DIATONIC (the grid bends), Fm pours
    [60, 62, 63, 65, 67, 68, 67, 66, 72, 71, 70, 69, 68, 67, 66, 65],
    # bar 6 — winding climb through the Dorian A natural; D5 pours home
    [67, 66, 67, 68, 69, 70, 71, 72, 74, 73, 72, 71, 70, 69, 68, 67],
    # bar 7 — the climb sequence rises diatonic to the Eb5 crest
    [67, 69, 70, 72, 74, 72, 71, 70, 72, 73, 74, 75, 74, 73, 72, 71],
    # bar 8 — the close: pour down, then the chain rides G7 home
    [67, 70, 69, 68, 67, 66, 65, 64, 62, 63, 64, 65, 66, 64, 65, 66],
]
SENT_SLIDES = [{4, 5, 12, 13, 14}, {4, 5, 8, 9, 10}, {0, 1, 2, 3, 12, 13, 14},
               {8, 9, 10, 11}, {2, 3, 4, 8, 9, 10, 11}, {4, 5, 6, 12, 13, 14},
               {0, 1, 2, 8, 9, 10, 11}, {4, 5, 6, 12, 13, 14, 15}]

# accent policy (the anchor system as accent): half-bar downbeats and
# flick landings. NOT silver_wire's 3-cycle roll — that device stays
# claimed.
FLICKS = {(0, 4), (1, 4)}                    # (bar, step) flick landings


def build_sentence(steps_bars, slide_bars, check_anchors=True):
    bars = []
    for bi, (steps, sl) in enumerate(zip(steps_bars, slide_bars)):
        bar = []
        for i, m in enumerate(steps):
            if m is None:
                bar.append([None, 1, 0, None])
                continue
            acc = 1 if (i in (0, 8) or (bi, i) in FLICKS) else 0
            if check_anchors and i in (0, 8):
                pcs, _ = HALF_CHORDS[bi * 2 + i // 8]
                assert m % 12 in pcs, f"anchor miss bar {bi + 1} step {i}: {m}"
            bar.append([m, 1, acc, True if i in sl else None])
        bars.append(bar)
    return bars


def resolve_slides(bars):
    flat = [e for bar in bars for e in bar]
    for i, e in enumerate(flat):
        if e[3] is True:
            e[3] = next((f[0] for f in flat[i + 1:] if f[0] is not None), None)
    return bars


THEME_BARS = resolve_slides(build_sentence(SENT_STEPS, SENT_SLIDES))
THEME = [tuple(e) for bar in THEME_BARS for e in bar]
assert sum(d for _, d, _, _ in THEME) == 128

THESIS_EV = [tuple(e) for bar in THEME_BARS[:4] for e in bar]
QHALF_EV = THESIS_EV
FRAG = [tuple(e) for bar in THEME_BARS[:2] for e in bar]

# the anti-arc cutoff profile — one entry per sentence bar, identical
# every statement; the register does the filter's job.
CUT_PROFILE = [1.00, 1.05, 0.95, 1.10, 1.05, 1.15, 1.20, 0.95]

# the licensed plunge-contour DOWNLIFTER (seam only, never foreground)
DOWN_EV = resolve_slides(build_sentence(
    [[79, 77, 76, 75, 74, 73, 72, 71, 67, 66, 65, 64, 63, 62, 61, 60]],
    [{0, 1, 2, 3, 4, 5, 6}, ], check_anchors=False))
DOWN_EV = [tuple(e) for bar in DOWN_EV for e in bar]

# the episode — bVII minor (Bbm), the one harmonically loose zone:
# the cell vocabulary with chromatic slippage, anchors on F (its 5th)
EPIS_STEPS = [
    [65, 64, 63, 62, 67, 66, 65, 64, 65, 64, 63, 62, 61, 62, 63, 64],
    [61, 60, 59, 58, 63, 62, 61, 60, 58, 59, 60, 61, 62, 63, 64, 65],
    [65, 66, 67, 68, 69, 68, 67, 66, 65, 63, 61, 60, 58, 60, 61, 63],
    [70, 58, 70, 58, 70, 65, 68, 58, 61, 62, 63, 64, 65, 66, 67, 68],
]
EPIS_SLIDES = [{4, 5, 12, 13}, {4, 5, 8, 9, 10}, {0, 1, 2, 8, 9, 10},
               {8, 9, 10, 11}]
EPIS_EV = [tuple(e) for bar in resolve_slides(
    build_sentence(EPIS_STEPS, EPIS_SLIDES, check_anchors=False))
    for e in bar]

# the sink oscillation cell (source B5 behaviour, our pitches)
def osc_bar(a):
    ev = resolve_slides(build_sentence(
        [[a, a + 1, a, a - 1, a, a + 1, a, a - 1,
          a, a + 1, a, a - 1, a - 1, a, a + 1, a]],
        [set(range(16))], check_anchors=False))
    return [tuple(e) for bar in ev for e in bar]


# THE RAMP — 23 semitones written out over 3 bars (G2 -> E4), each
# pitch 2 steps, one unbroken slide chain landing G3+12... the drop's
# G. Monotone by construction, printed and checked.
RAMP_PITCHES = list(range(43, 67))           # 43..66, lands 67 at the drop
RAMP_EV = []
for i, m in enumerate(RAMP_PITCHES):
    last = (i == len(RAMP_PITCHES) - 1)
    RAMP_EV.append((m, 2, 1 if i % 4 == 0 else 0, 67 if last else True))
RAMP_EV = [list(e) for e in RAMP_EV]
for i, e in enumerate(RAMP_EV):
    if e[3] is True:
        e[3] = RAMP_EV[i + 1][0]
RAMP_EV = [tuple(e) for e in RAMP_EV]

# the WATERFALL (the coda's licensed plunge use): sawtooth+drop pairs
# re-anchored on C, falling two octaves, over i -> V7/iv -> iv
WATER_EV = resolve_slides(build_sentence(
    [[84, 83, 82, 81, 82, 81, 80, 79, 80, 79, 78, 77, 76, 75, 74, 73],
     [72, 71, 70, 69, 70, 69, 68, 67, 66, 65, 64, 63, 62, 61, 60, 59]],
    [{0, 1, 2, 3, 8, 9, 10, 11}, {0, 1, 2, 3, 8, 9, 10, 11}],
    check_anchors=False))
WATER_EV = [tuple(e) for bar in WATER_EV for e in bar]

# the EXIT RUN — unbroken ascent G2 -> C6 over 2 bars (mixed 1- and
# 2-semitone rises: 41 semitones in 31 moves), land C6, flick C7.
EXIT_PITCHES = [43]
_rise = ([1, 1, 2] * 11)[:31]                # 21 ones + 10 twos = 41
for r in _rise:
    EXIT_PITCHES.append(EXIT_PITCHES[-1] + r)
assert EXIT_PITCHES[-1] == 84
EXIT_EV = []
for i, m in enumerate(EXIT_PITCHES):
    EXIT_EV.append([m, 1, 1 if i % 4 == 0 else 0,
                    True if i < len(EXIT_PITCHES) - 1 else None])
for i, e in enumerate(EXIT_EV):
    if e[3] is True:
        e[3] = EXIT_EV[i + 1][0]
EXIT_EV = [tuple(e) for e in EXIT_EV]

STMTS = []        # (bar, kind, mean cutoff)
LINE_NOTES = []   # (bar_float, midi) — the register ledger
LEDGER = [("thesis", "i"), ("engine", "i"), ("verse 1 (i, low)", "i"),
          ("verse 2 (iv)", "iv"), ("duel 1", "i (hammer C)"),
          ("DROP 1 (i)", "i"), ("episode (bVII)", "bVII"),
          ("duel 2", "iv (hammer F)"), ("sink+ramp (V)", "V pedal"),
          ("DROP 2 recap", "i"), ("CODA (+12)", "i"),
          ("waterfall", "i -> V7/iv -> iv"), ("exit", "i, upward")]

# ------------------------------------------------------------------- drums
# Sparse by construction (blueprint par.6: at 9.2 notes/s the LINE is
# the 16th layer): 909 kick 4/4, offbeat open hat, clap on 2&4, crash
# arrivals, ride in the coda only. NO closed 16th carpet anywhere.

def make_kick():
    n = int(0.30 * SR)
    td = np.arange(n) / SR
    f_curve = 48.0 + 102.0 * np.exp(-td * 50.0)
    body = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    sos_c = signal.butter(2, [1800, 9000], "bandpass", fs=SR, output="sos")
    click = signal.sosfilt(sos_c, rng.standard_normal(n)) * np.exp(-td * 700)
    click /= np.max(np.abs(click)) + 1e-12
    env = (1 - np.exp(-td / 0.0008)) * np.exp(-td * 9.0)
    x = (body + 0.45 * click) * env
    return x / (np.max(np.abs(x)) + 1e-12)


def make_hat(open_=False):
    n = int((0.14 if open_ else 0.045) * SR)
    td = np.arange(n) / SR
    sos_h = signal.butter(4, 6500 if open_ else 7000, "high",
                          fs=SR, output="sos")
    x = signal.sosfilt(sos_h, rng.standard_normal(n))
    x *= np.exp(-td * (26 if open_ else 100))
    return x / (np.max(np.abs(x)) + 1e-12)


def make_clap():
    n = int(0.26 * SR)
    td = np.arange(n) / SR
    sos_c = signal.butter(2, [900, 5200], "bandpass", fs=SR, output="sos")
    nz = signal.sosfilt(sos_c, rng.standard_normal(n))
    nz /= np.max(np.abs(nz)) + 1e-12
    env = np.zeros(n)
    for i, t0 in enumerate([0.0, 0.011, 0.022, 0.033]):
        i0 = int(t0 * SR)
        rate = 120.0 if i < 3 else 26.0
        seg = (0.65 if i < 3 else 1.0) * np.exp(-(td[i0:] - t0) * rate)
        env[i0:] = np.maximum(env[i0:], seg)
    x = nz * env
    return x / (np.max(np.abs(x)) + 1e-12)


def make_crash():
    n = int(2.0 * SR)
    td = np.arange(n) / SR
    sos_c = signal.butter(2, 5000, "high", fs=SR, output="sos")
    x = signal.sosfilt(sos_c, rng.standard_normal(n)) * np.exp(-td * 2.2)
    x *= 1 - np.exp(-td / 0.002)
    return x / (np.max(np.abs(x)) + 1e-12)


def make_ride():
    n = int(0.30 * SR)
    td = np.arange(n) / SR
    a = signal.sosfilt(signal.butter(2, [4000, 9000], "bandpass",
                                     fs=SR, output="sos"),
                       rng.standard_normal(n)) * np.exp(-td * 14)
    ping = np.sin(2 * np.pi * 5400 * td) * np.exp(-td * 20)
    x = a / (np.max(np.abs(a)) + 1e-12) + 0.5 * ping
    return x * (1 - np.exp(-td / 0.001)) / (np.max(np.abs(x)) + 1e-12)


def make_snare():
    n = int(0.16 * SR)
    td = np.arange(n) / SR
    body = np.sin(2 * np.pi * 190.0 * td) * np.exp(-td * 30.0)
    wires = signal.sosfilt(signal.butter(2, [500, 4500], "bandpass",
                                         fs=SR, output="sos"),
                           rng.standard_normal(n)) * np.exp(-td * 40.0)
    wires /= np.max(np.abs(wires)) + 1e-12
    x = (body + 0.9 * wires) * (1 - np.exp(-td / 0.001))
    return x / (np.max(np.abs(x)) + 1e-12)


KICK = make_kick()
OHAT = make_hat(open_=True)
CLAP = make_clap()
CRASH = make_crash()
RIDE = make_ride()
SNARE = make_snare()


def kick_on(b):
    s = section_of(b)
    if s in ("thesis", "waterfall", "exit"):
        return False
    if s == "sink+ramp (V)" and b < B_SINK + 8:
        return False                          # the trough is bare
    if b in D2_DIP:
        return False                          # the a-cappella dip
    return True


def kick_gain(b):
    s = section_of(b)
    return {"engine": 0.8, "verse 1 (i, low)": 0.85, "verse 2 (iv)": 0.85,
            "duel 1": 0.7, "duel 2": 0.7, "episode (bVII)": 0.9,
            "sink+ramp (V)": 0.75}.get(s, 1.0)


clear()
for b in range(B_END):
    if not kick_on(b):
        continue
    if b in ROLL_BARS:
        for s16 in range(12):                 # beats 1-3 roll, beat 4 SILENT
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

# sidechain pump (big-room default; never on the line)
pump = np.ones(N)
_dipn = int(0.30 * SR)
_dip = 0.55 * np.exp(-np.arange(_dipn) / SR / 0.10)
PUMP_BEATS = 0
for _b in range(B_END):
    if not kick_on(_b) or _b in ROLL_BARS:
        continue
    for _beat in range(4):
        _i0 = int(bar_t(_b, _beat) * SR)
        _end = min(N, _i0 + _dipn)
        pump[_i0:_end] = np.minimum(pump[_i0:_end], 1.0 - _dip[: _end - _i0])
        PUMP_BEATS += 1
np.clip(pump, 0.30, 1.0, out=pump)
print(f"pump curve built ({PUMP_BEATS} ducked beats)")


# -------------------------------------------------------------------- bass
# The source's struck-chord behaviour: dark short OFFBEAT-8th stabs
# on the station root — the classic offbeat bass no sibling uses (no
# rolling 16ths, no K-b-b-b, no run-and-plant). The line owns the
# fifth, the bass owns the root (Q4's division of labour).

def bass_stab(midi, dur=BEAT * 0.42):
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    for k in range(1, min(16, int(3000 / f)) + 1):
        x += np.sin(2 * np.pi * k * f * td) / k ** 1.3
    sos_b = signal.butter(2, 420, "low", fs=SR, output="sos")
    x = np.tanh(0.9 * signal.sosfilt(sos_b, x))
    x += 0.5 * np.sin(2 * np.pi * f * td)
    env = (1 - np.exp(-td / 0.003)) * np.clip((dur - td) / 0.05, 0, 1)
    x *= env
    return x / (np.max(np.abs(x)) + 1e-12)


def bass_root(b):
    s = section_of(b)
    if s == "verse 2 (iv)" or s == "duel 2":
        return 41                              # F2 — the iv station
    if s == "episode (bVII)":
        return 46                              # Bb2 — the bVII episode
    if s == "sink+ramp (V)":
        return 43                              # G2 — the V pedal
    if s == "waterfall":
        return [48, 48, 41, 41][b - B_WATER]   # i -> V7/iv -> iv roots
    return 48                                  # C3 home (sub boom owns C2)


BASS_SAMPLES = {m: bass_stab(m) for m in (41, 43, 46, 48)}

clear()
for b in range(B_END):
    s = section_of(b)
    if s in ("thesis", "exit", "waterfall") or b < 8:
        continue
    if s == "sink+ramp (V)" and b < B_SINK + 8:
        continue
    if b in ROLL_BARS or b in D2_DIP:
        continue
    g = 0.7 if b < B_DROP1 else 1.0
    smp = BASS_SAMPLES[bass_root(b)]
    for beat in range(4):
        add_at(lay_L, smp, bar_t(b, beat + 0.5), g)
        add_at(lay_R, smp, bar_t(b, beat + 0.5), g)
commit(lay_L, lay_R, 0.26, env=pump)
print("offbeat stab bass committed")


# sub boom under every kick (big-room default; C2/F2/Bb1/G1 register)
def make_sub_boom(f):
    n = int(0.42 * SR)
    td = np.arange(n) / SR
    f_curve = f * (1.0 + 0.35 * np.exp(-td * 12.0))
    x = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    env = ((1 - np.exp(-td / 0.003)) * np.exp(-td * 1.2) *
           np.clip((0.42 - td) / 0.06, 0, 1))
    return x * env


BOOM = {m: make_sub_boom(midi_to_hz(m - 12)) for m in (41, 43, 46, 48)}

clear()
for b in range(B_END):
    if not kick_on(b) or b in ROLL_BARS:
        continue
    g = kick_gain(b)
    boom = BOOM[bass_root(b) if section_of(b) != "waterfall" else 48]
    for beat in range(4):
        add_at(lay_L, boom, bar_t(b, beat), g)
        add_at(lay_R, boom, bar_t(b, beat), g)
commit(lay_L, lay_R, 0.16)
print("sub boom committed")

# hats / claps / crashes / ride / rolls
clear()
for b in range(B_END):
    s = section_of(b)
    if s in ("thesis", "waterfall", "exit") or b < 10:
        continue
    if b in ROLL_BARS or b in D2_DIP:
        continue
    if s == "sink+ramp (V)" and b < B_SINK + 8:
        continue
    g = 0.8 if b < B_DROP1 else 1.0
    for beat in range(4):
        add_at(lay_L, OHAT, bar_t(b, beat + 0.5), g * 0.8)
        add_at(lay_R, OHAT, bar_t(b, beat + 0.5), g)
commit(lay_L, lay_R, 0.11)
print("offbeat hats committed (no closed carpet — the line is the 16ths)")

clear()
for b in range(B_END):
    s = section_of(b)
    if s not in ("DROP 1 (i)", "DROP 2 recap", "CODA (+12)",
                 "episode (bVII)"):
        continue
    if b in D1_DIP or b in D2_DIP or b in ROLL_BARS:
        continue
    for beat in (1, 3):
        place_pan(lay_L, lay_R, CLAP, bar_t(b, beat), 1.0,
                  0.42 if beat == 1 else 0.58)
commit(lay_L, lay_R, 0.10)
print("claps committed")

clear()
for b, g in [(B_ENGINE, 0.4), (B_VERSE1, 0.4), (B_DUEL1, 0.5),
             (B_DROP1, 1.0), (B_EPIS, 0.6), (B_DUEL2, 0.5),
             (B_DROP2, 1.0), (B_CODA, 1.0), (B_WATER, 0.7)]:
    place_pan(lay_L, lay_R, CRASH, bar_t(b), g, 0.5)
commit(lay_L, lay_R, 0.05)
print("crashes committed")

clear()
for b in range(B_CODA, B_WATER):
    for e in range(8):
        place_pan(lay_L, lay_R, RIDE, bar_t(b, e * 0.5), 0.8, 0.6)
commit(lay_L, lay_R, 0.07)
print("coda ride committed")

clear()
for b in ROLL_BARS:
    for s16 in range(12):
        place_pan(lay_L, lay_R, SNARE, bar_t(b, s16 * 0.25),
                  0.5 + 0.5 * s16 / 11, 0.45)
commit(lay_L, lay_R, 0.09)
print("snare rolls committed (beat 4 stays the composed silent beat)")


# ------------------------------------------------------------------- drone
# the sink's bare dominant pedal: G1 sine + faint octave, breathing
clear()
n_dr = int((B_SINK + 11 - B_SINK + 1.5) * BAR * SR)
td_dr = np.arange(n_dr) / SR
f_g = midi_to_hz(31)
dr = (np.sin(2 * np.pi * f_g * td_dr) +
      0.30 * np.sin(2 * np.pi * 2 * f_g * td_dr) +
      0.12 * np.sin(2 * np.pi * 3 * f_g * td_dr))
dr *= 0.8 + 0.2 * np.sin(2 * np.pi * 0.09 * td_dr)
dr *= np.minimum(np.clip(td_dr / 1.5, 0, 1),
                 np.clip((n_dr / SR - td_dr) / 1.0, 0, 1))
add_at(lay_L, dr, bar_t(B_SINK), 1.0)
add_at(lay_R, dr, bar_t(B_SINK), 1.0)
commit(lay_L, lay_R, 0.14, env=pump)
print("sink drone committed (the bare V pedal)")

# === CHUNK 3: the 303, duels, pads, stabs, wedges ===
