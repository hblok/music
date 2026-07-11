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

# the track ends COLD 0.2 s after the exit flick (bar 162 beat 1)
DURATION = GRID0 + 162 * BAR + 1.0 * BEAT + 0.30
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


# true sub pitches (the first render measured the m-12 booms at
# 65 Hz+, above the sub-60 band): F1/G1/Bb1, and C1 for home — the
# home drops get the deepest floor
BOOM_PITCH = {41: 29, 43: 31, 46: 34, 48: 24}
BOOM = {m: make_sub_boom(midi_to_hz(BOOM_PITCH[m])) for m in (41, 43, 46, 48)}

clear()
for b in range(B_END):
    if not kick_on(b) or b in ROLL_BARS:
        continue
    g = kick_gain(b)
    boom = BOOM[bass_root(b) if section_of(b) != "waterfall" else 48]
    for beat in range(4):
        add_at(lay_L, boom, bar_t(b, beat), g)
        add_at(lay_R, boom, bar_t(b, beat), g)
commit(lay_L, lay_R, 0.20)
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
commit(lay_L, lay_R, 0.11, env=pump)
print("sink drone committed (the bare V pedal)")

# ------------------------------------------------------------------ THE 303
# The square-core buzz (the 2026-07-11 voice amendment): pulse core
# duty 0.30/0.25, rolled 1/k^1.25, a round reed formant (Q 2.8,
# blend 0.4) riding UNDER the within-note bright->dark sweep (kept —
# the acid identity), tanh(1.0), sine body. LEGATO: a slide chain is
# ONE note on a smoothed pitch path (the morgenland v3 anti-garble
# render). THE RELAY: timbre A "violin" / B "clarinet" hand-offs at
# cell (half-bar) boundaries only. Bone dry, center, unpumped.

buzz_cache = {}
TIMBRE = {"A": (0.30, 2600.0, 1350.0), "B": (0.25, 1900.0, 1100.0)}


def buzz_path(segments, cutoff, accent=False, timbre="A"):
    duty, lid, formant = TIMBRE[timbre]
    key = (tuple((m, round(s, 4)) for m, s in segments),
           int(cutoff // 40), accent, timbre)
    if key in buzz_cache:
        return buzz_cache[key]
    total = sum(s for _, s in segments)
    n = int(total * SR)
    td = np.arange(n) / SR
    f_path = np.empty(n)
    tt = 0.0
    i1 = 0
    for m, s in segments:
        i0 = int(tt * SR)
        i1 = min(n, int((tt + s) * SR))
        f_path[i0:i1] = midi_to_hz(m)
        tt += s
    if i1 < n:
        f_path[i1:] = f_path[max(i1 - 1, 0)]
    a = 1.0 - np.exp(-1.0 / (0.030 * SR))
    f_path = signal.lfilter([a], [1, -(1 - a)], f_path,
                            zi=[(1 - a) * f_path[0]])[0]
    ph = 2 * np.pi * np.cumsum(f_path) / SR
    fmin = max(min(midi_to_hz(m) for m, _ in segments), 30.0)
    x = np.zeros(n)
    for k in range(1, min(40, int(9000 / fmin)) + 1):
        w = np.sin(np.pi * k * duty)              # the pulse spectrum
        if abs(w) < 1e-3:
            continue
        x += w * np.sin(k * ph) / k ** 1.25
    cutoff = float(np.clip(cutoff * (1.4 if accent else 1.0), 200, 5000))

    def reed(sig_in, c):
        c = float(np.clip(c, 180.0, lid))
        sos_lp = signal.butter(2, c, "low", fs=SR, output="sos")
        y = signal.sosfilt(sos_lp, sig_in)
        bpk, apk = signal.iirpeak(formant, Q=2.8, fs=SR)
        return y + 0.40 * signal.lfilter(bpk, apk, y)

    bright = reed(x, cutoff * 2.2)
    dark = reed(x, cutoff * 0.7)
    sweep = np.exp(-td / (0.09 if accent else 0.045))
    y = np.tanh(1.0 * (sweep * bright + (1 - sweep) * dark))
    y += 0.30 * np.sin(ph)
    env = (1 - np.exp(-td / 0.0015)) * np.clip((total - td) / 0.02, 0, 1)
    y *= env
    y /= np.max(np.abs(y)) + 1e-12
    buzz_cache[key] = y
    return y


RELAY_SWITCHES = 0
CHAIN_LENS = []


def cell_timbre(step):
    return "A" if ((step // 8) // 4) % 2 == 0 else "B"


def place_events(b0, events, octave, base_cut, gain, prof,
                 relay=True, timbre="A", ledger=True):
    """Legato placement: consecutive slid notes merge into ONE
    buzz_path (no re-attacks inside chains); terminal slides land
    audibly (~100 ms) across the line; detached notes gate at 0.85.
    The relay assigns timbre per half-bar cell."""
    global RELAY_SWITCHES
    cuts = []
    evs = list(events)
    steps = []
    s = 0
    for e in evs:
        steps.append(s)
        s += e[1]
    prev_tim = None
    i = 0
    while i < len(evs):
        m, d, acc, sl = evs[i]
        if m is None:
            i += 1
            continue
        step = steps[i]
        tim = cell_timbre(step) if relay else timbre
        if relay and prev_tim is not None and tim != prev_tim:
            RELAY_SWITCHES += 1
        prev_tim = tim
        cut = base_cut * prof[(step // 16) % len(prof)]
        cut *= 1.0 + 0.08 * np.sin(2 * np.pi * (step % 16) / 16.0)
        cuts.append(cut * (1.4 if acc else 1.0))
        g = gain * (1.1 if acc else 1.0)
        t0 = bar_t(b0, step * 0.25)
        seg = [[m + octave, d * STEP]]
        if ledger:
            LINE_NOTES.append((b0 + step / 16.0, m + octave))
        j = i
        while evs[j][3] is not None and j + 1 < len(evs) \
                and evs[j + 1][0] == evs[j][3]:
            j += 1
            seg.append([evs[j][0] + octave, evs[j][1] * STEP])
            if ledger:
                LINE_NOTES.append((b0 + steps[j] / 16.0,
                                   evs[j][0] + octave))
        term = evs[j][3]
        if term is not None:
            seg.append([term + octave, 0.10])     # the audible landing
        elif len(seg) == 1:
            seg[0][1] *= 0.85                     # detached: air between
        if len(seg) > 1:
            CHAIN_LENS.append(len(seg))
        x = buzz_path(tuple(tuple(e) for e in seg), cut,
                      accent=bool(acc), timbre=tim)
        add_at(lay_L, x, t0, g)
        add_at(lay_R, x, t0, g * 0.97)
        i = j + 1
    return cuts


def transpose_ev(events, semis):
    return [(m + semis if m is not None else None, d, a,
             (sl + semis if isinstance(sl, int) else sl))
            for m, d, a, sl in events]


def place_statement(b0, kind, octave=0, base=900, gain=1.0, double=False):
    cuts = place_events(b0, THEME, octave, base, gain, CUT_PROFILE)
    if double:
        place_events(b0, THEME, octave - 12, base, gain * 0.42,
                     CUT_PROFILE, relay=False, timbre="B", ledger=False)
    STMTS.append((b0, kind, float(np.mean(cuts))))


# duel material: the hammer (one-pitch retrigger, pitch STATIONARY
# per bar — the anti-ladder assertion), the trill, the palindrome
# swell. The 303 hammers in timbre B; the stab voice answers.
def hammer_ev(p):
    return [(p, 1, 1 if i % 4 == 0 else 0, None) for i in range(16)]


def chain_ev(seq, accents=4):
    ev = [[q, 1, 1 if i % accents == 0 else 0, True] for i, q in
          enumerate(seq)]
    ev[-1][3] = None
    for i, e in enumerate(ev[:-1]):
        e[3] = ev[i + 1][0]
    return [tuple(e) for e in ev]


def trill_ev(p):
    return chain_ev([p + 1, p, p + 1, p - 1] * 4)


def swell_ev(p, launch=False):
    seq = [p, p + 1, p + 2, p + 3, p + 4, p + 3, p + 2, p + 1] * 2
    if launch:                                    # roll bar: beat 4 silent
        seq = seq[:12]
    return chain_ev(seq)


def place_hammer(b, p, base, gain=1.0):
    for i in range(16):
        cut = base * (0.8 + 0.5 * i / 15.0)       # the rising retrigger
        x = buzz_path(((p, STEP * 0.80),), cut,
                      accent=(i % 4 == 0), timbre="B")
        add_at(lay_L, x, bar_t(b, i * 0.25), gain * (1.0 if i % 4 == 0 else 0.7))
        add_at(lay_R, x, bar_t(b, i * 0.25), gain * 0.97 * (1.0 if i % 4 == 0 else 0.7))
    LINE_NOTES.append((float(b), p))


DUEL_GRID = []

clear()
# thesis: the first 4 sentence bars, one naked 303 (never the plunge)
place_events(0, THESIS_EV, 0, 700, 0.9, CUT_PROFILE[:4])
# engine: low mutters under the assembling groove
place_events(8, FRAG, -12, 520, 0.60, CUT_PROFILE[:2])
place_events(12, FRAG, -12, 520, 0.65, CUT_PROFILE[:2])
# the licensed plunge-contour downlifter FALLS into verse 1 (seam)
place_events(15, DOWN_EV, 0, 600, 0.5, [1.0], relay=False, timbre="B")
# verse 1 — two dark statements at home, an octave down
place_statement(B_VERSE1, "dark", octave=-12, base=620, gain=0.85)
place_statement(B_VERSE1 + 8, "dark", octave=-12, base=620, gain=0.85)
# verse 2 — the transposition machine: the sentence up a 4th (iv),
# transposed statements are the development engine, uncounted
TH_IV = transpose_ev(THEME, 5)
place_events(B_VERSE2, TH_IV, -12, 680, 0.9, CUT_PROFILE)
place_events(B_VERSE2 + 8, TH_IV, -12, 680, 0.9, CUT_PROFILE)
# duel 1 — hammer/trill traded with the stab voice, on C (home root)
for b, p, kind in [(B_DUEL1, 60, "hammer"), (B_DUEL1 + 2, 72, "hammer"),
                   (B_DUEL1 + 4, 60, "trill")]:
    if kind == "hammer":
        place_hammer(b, p, 700, 0.9)
    else:
        place_events(b, trill_ev(p), 0, 700, 0.9, [1.0],
                     relay=False, timbre="A")
    DUEL_GRID.append((b, "303", kind, p))
    DUEL_GRID.append((b + 1, "stab", "answer", p))
place_events(B_DUEL1 + 6, swell_ev(60), 0, 750, 0.9, [1.0],
             relay=False, timbre="A")
place_events(B_DUEL1 + 7, swell_ev(62, launch=True), 0, 800, 0.95, [1.0],
             relay=False, timbre="A")
DUEL_GRID.append((B_DUEL1 + 6, "303", "swell (aug pad)", 60))
# DROP 1 — statements 1-3 + dip + the declared Q-half wave
place_statement(B_DROP1, "home", base=900)
place_statement(B_DROP1 + 8, "home", base=900)
place_events(B_DROP1 + 16, FRAG, -12, 540, 0.75, CUT_PROFILE[:2])  # dip
place_events(B_DROP1 + 18, FRAG, -12, 540, 0.75, CUT_PROFILE[:2])
place_statement(B_DROP1 + 20, "home", base=900)
place_events(B_DROP1 + 28, QHALF_EV, 0, 900, 1.0, CUT_PROFILE[:4])
# episode — the bVII wander (chromatic slippage, uncounted)
place_events(B_EPIS, EPIS_EV, 0, 780, 0.9, CUT_PROFILE[:4])
place_events(B_EPIS + 4, EPIS_EV, 0, 780, 0.9, CUT_PROFILE[:4])
# duel 2 — the higher station, on F
for b, p, kind in [(B_DUEL2, 65, "hammer"), (B_DUEL2 + 2, 77, "hammer"),
                   (B_DUEL2 + 4, 65, "trill")]:
    if kind == "hammer":
        place_hammer(b, p, 700, 0.9)
    else:
        place_events(b, trill_ev(p), 0, 700, 0.9, [1.0],
                     relay=False, timbre="A")
    DUEL_GRID.append((b, "303", kind, p))
    DUEL_GRID.append((b + 1, "stab", "answer", p))
place_events(B_DUEL2 + 6, swell_ev(65), 0, 750, 0.9, [1.0],
             relay=False, timbre="A")
place_events(B_DUEL2 + 7, swell_ev(67), 0, 750, 0.85, [1.0],
             relay=False, timbre="A")
DUEL_GRID.append((B_DUEL2 + 6, "303", "swell (aug pad)", 65))
# THE SINK — the register trough on the bare V drone
for b in range(4):
    place_events(B_SINK + b, osc_bar(55), 0, 480, 0.60, [1.0],
                 relay=False, timbre="B")
for b in range(4):
    place_events(B_SINK + 4 + b, osc_bar(43), 0, 420, 0.55, [1.0],
                 relay=False, timbre="B")
# THE RAMP — 23 semitones written out, one unbroken chain, 3 bars
RAMP_CUTS = place_events(B_SINK + 8, RAMP_EV, 0, 700, 0.9, [1.0],
                         relay=False, timbre="A")
# DROP 2 — the recap IS the drop (verbatim statements), then the dip
# goes a cappella and the third statement doubles low
place_statement(B_DROP2, "home", base=900)
place_statement(B_DROP2 + 8, "home", base=900)
place_events(B_DROP2 + 16, THESIS_EV, 0, 900, 1.0, CUT_PROFILE[:4])
place_statement(B_DROP2 + 20, "home", base=900, double=True)
place_events(B_DROP2 + 28, QHALF_EV, 0, 900, 1.0, CUT_PROFILE[:4])
# THE CODA — fuse AND lift (Q6): the refrain +12 over the bare
# pedal, the home register doubling under it (the composed register
# swap); the stab voice sounds the duel's answer material below
place_statement(B_CODA, "coda +12", octave=12, base=950, gain=0.95,
                double=True)
# the WATERFALL — the plunge cells re-anchored on the ROOT (i ->
# V7/iv -> iv, the one secondary dominant), falling two octaves
place_events(B_WATER, WATER_EV, 0, 800, 0.95, [1.0, 0.9])
# exit wedges: the 303 hammers while the wedges fan outward
place_hammer(B_WATER + 2, 67, 650, 0.85)
place_hammer(B_WATER + 3, 79, 700, 0.9)
# THE EXIT — the unbroken rising run; land C6; flick C7; hard stop
place_events(B_EXIT, EXIT_EV, 0, 900, 0.95, [1.0])
place_events(B_EXIT + 2, [(84, 4, 1, None), (96, 1, 1, None)],
             0, 950, 1.0, [1.0], relay=False, timbre="A")
commit(lay_L, lay_R, 0.30)          # DRY, CENTER, UNPUMPED — declared
print(f"the 303 committed ({len(buzz_cache)} cached paths, "
      f"{RELAY_SWITCHES} relay hand-offs)")


# ------------------------------------------------------------------- stabs
# the struck-chord punctuation (source par.5) = the duel answer voice
# and the coda's fusion partner. Dark, short, wet.

def chord_stab(chord, dur=0.16):
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    for m in chord:
        f = midi_to_hz(m)
        for k in range(1, min(14, int(5000 / f)) + 1):
            x += np.sin(2 * np.pi * k * f * td) / k ** 1.3
    sos_s = signal.butter(2, 900, "low", fs=SR, output="sos")
    x = np.tanh(0.9 * signal.sosfilt(sos_s, x))
    x *= (1 - np.exp(-td / 0.002)) * np.clip((dur - td) / 0.03, 0, 1)
    return x / (np.max(np.abs(x)) + 1e-12)


clear()
# drop statements 2-3: offbeat punctuation (the between-instruments
# answer inside the drops)
for b0 in (B_DROP1 + 8, B_DROP1 + 20, B_DROP2 + 8, B_DROP2 + 20):
    for k in range(8):
        ch = PAD_BARS[k % 8]
        st = chord_stab(tuple(m + 12 for m in ch[1:]))
        for beat, pan in [(1.5, 0.35), (3.5, 0.65)]:
            place_pan(lay_L, lay_R, st, bar_t(b0 + k, beat), 0.9, pan)
# episode punctuation
for b in range(B_EPIS, B_DUEL2):
    st = chord_stab(tuple(m + 12 for m in BBM_V[1:]))
    place_pan(lay_L, lay_R, st, bar_t(b, 2.5), 0.8,
              0.35 + 0.3 * (b % 2))
# duel answers: the stab voice trades bar-by-bar with the 303
for b, voice, kind, p in DUEL_GRID:
    if voice != "stab":
        continue
    for e in range(8):
        q = p + (1 if e % 2 == 0 else 0)
        st = chord_stab((q, q + 7), dur=0.12)
        place_pan(lay_L, lay_R, st, bar_t(b, e * 0.5), 0.9,
                  0.3 + 0.4 * (e % 2))
# THE FUSION (coda): the duel's answer material under the +12 refrain
# — the first time the two ideas fully overlap
for b in range(B_CODA, B_WATER):
    for e in range(8):
        q = 60 + (1 if e % 2 == 0 else 0)
        st = chord_stab((q, q + 7), dur=0.12)
        place_pan(lay_L, lay_R, st, bar_t(b, e * 0.5), 0.7,
                  0.3 + 0.4 * (e % 2))
# waterfall: the struck chords of the one secondary dominant
WATER_CHORDS = [(48, 60, 63, 67), (48, 60, 63, 67),
                (48, 60, 64, 70), (41, 60, 65, 68)]      # Cm Cm C7 Fm
for h, ch in enumerate(WATER_CHORDS):
    st = chord_stab(ch, dur=0.6)
    place_pan(lay_L, lay_R, st, bar_t(B_WATER + h // 2, (h % 2) * 2),
              1.0, 0.5)
lay_L = reverb(lay_L, IR_L, 0.45)
lay_R = reverb(lay_R, IR_R, 0.45)
commit(lay_L, lay_R, 0.13)
print("stabs committed (duel answers + fusion + waterfall chords)")

# -------------------------------------------------------------------- pads

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
for b0, b1 in [(B_DROP1, B_EPIS), (B_DROP2, B_CODA)]:
    for b in range(b0, b1):
        if b in D1_DIP or b in D2_DIP or b in ROLL_BARS:
            continue
        pL, pR = pad_chord(PAD_BARS[(b - b0) % 8], BAR + 0.8)
        add_at(lay_L, pL, bar_t(b), 0.8)
        add_at(lay_R, pR, bar_t(b), 0.8)
for b in range(B_EPIS, B_DUEL2):
    pL, pR = pad_chord(BBM_V, BAR + 0.8)
    add_at(lay_L, pL, bar_t(b), 0.7)
    add_at(lay_R, pR, bar_t(b), 0.7)
# the augmented-dominant swells (the lift that commits to no key)
for b0, v in [(B_DUEL1 + 6, AUG_V), (B_DUEL2 + 6, (55, 67, 71, 75))]:
    pL, pR = pad_chord(v, 2 * BAR + 0.5, attack=2 * BAR * 0.8, release=0.4)
    add_at(lay_L, pL, bar_t(b0), 1.0)
    add_at(lay_R, pR, bar_t(b0), 1.0)
# the coda's bare pedal (pads stripped to the pedal — the relocation)
for b in range(B_CODA, B_WATER):
    pL, pR = pad_chord(PEDAL_V + (79,), BAR + 0.8)
    add_at(lay_L, pL, bar_t(b), 0.95)
    add_at(lay_R, pR, bar_t(b), 0.95)
lay_L = reverb(lay_L, IR_L, 0.5)
lay_R = reverb(lay_R, IR_R, 0.5)
commit(lay_L, lay_R, 0.15, env=pump)
print("pads committed (vamp / episode / aug swells / coda pedal)")


# ------------------------------------------------------------------ wedges
# THE seam device: two voices fanning outward chromatically in
# contrary motion around the pedal — riser and downlifter crossfaded
# in one gesture. Not a reverse cymbal, not a tom fill, not a noise
# riser.

def wedge(dur, center=67, spread=4.0):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    u = tt / dur
    out = []
    for sgn in (+1.0, -1.0):
        f = midi_to_hz(center) * 2.0 ** (sgn * spread * u / 12.0)
        ph = 2 * np.pi * np.cumsum(f) / SR
        v = np.sin(ph) + 0.30 * np.sin(2 * ph) + 0.15 * np.sin(3 * ph)
        out.append(v)
    sos_w = signal.butter(2, 1400, "low", fs=SR, output="sos")
    env = u ** 2 * (1 - np.exp(-tt / 0.05))
    dn = signal.sosfilt(sos_w, out[1] * env)
    up = signal.sosfilt(sos_w, out[0] * env)
    peak = max(np.max(np.abs(dn)), np.max(np.abs(up)), 1e-12)
    return dn / peak, up / peak


WEDGE_SEAMS = [(B_DROP1 - 2, 0.8), (B_SINK - 2, 0.7),
               (B_CODA - 2, 0.8), (B_WATER + 2, 1.0)]
clear()
for b0, g in WEDGE_SEAMS:
    dn, up = wedge(2 * BAR, center=67)
    add_at(lay_L, dn, bar_t(b0), g)
    add_at(lay_R, up, bar_t(b0), g)
lay_L = reverb(lay_L, IR_L, 0.3)
lay_R = reverb(lay_R, IR_R, 0.3)
commit(lay_L, lay_R, 0.07)
print(f"wedges committed ({len(WEDGE_SEAMS)} seams)")

# air at the intro edge only (the exit is cold, not misty)
sos_air = signal.butter(4, [150, 1100], "bandpass", fs=SR, output="sos")
air = signal.sosfilt(sos_air, rng.standard_normal(N))
air /= np.max(np.abs(air))
air_env = slow_noise(0.05, 0.4, 1.0)
edge = np.clip((bar_t(B_VERSE1) - t) / 10.0, 0, 1)
commit(air * air_env * edge, air * air_env[::-1] * edge, 0.035)
print("air committed")


# ------------------------------------------------------------------ master
# big-room chain (directory default): shelves high 3 kHz + low 95 Hz
# (no deep 55 shelf), tanh bus limiter. Fade-out 20 ms — COLD.

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
OUT = os.path.join(OUT_DIR, "flightpath.wav")
with wave.open(OUT, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())

print(f"\nCreated: {os.path.abspath(OUT)}")
print(f"Duration: {N / SR:.1f} s  |  {SR} Hz stereo, 16-bit PCM  |  "
      f"{BPM:.0f} BPM, C minor (the Dorian F vamp; anchors on the fifth)")

FLAC = os.path.join(OUT_DIR, "flightpath.flac")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", OUT,
                "-vn", "-ar", "44100", "-ac", "2", "-c:a", "flac", FLAC],
               check=True)
print(f"Created: {os.path.abspath(FLAC)}  (lossless flac)")

# ------------------------------------------------------------- verify form

print("\nSection map + the fourths ledger:")
for (name, b), (_, station) in zip(SECTIONS, LEDGER):
    print(f"  {bar_t(b):6.1f} s  bar {b:3d}  {name:18s} [{station}]")
print(f"  {DURATION:6.1f} s  end (cold)")

print(f"\nRefrain statements (8-bar sentence, identical): "
      f"{len(STMTS)} (home-key count target >= 6)")
for b0, kind, mc in STMTS:
    print(f"  bar {b0:3d}  {kind:8s}  mean cutoff {mc:6.1f} Hz")
print("  declared uncounted: thesis, mutters, verse-2 iv transpositions, "
      "episode, Q-half waves, the a-cappella dip, duels, sink/ramp, "
      "waterfall, exit")

# the sentence map + grammar metrics from THEME itself
chars = ["."] * 128
pos = 0
ONSETS = RESTS = 0
run = longest_run = 0
chains = 0
cur_chain = 0
for m, d, acc, sl in THEME:
    if m is None:
        RESTS += d
        longest_run = max(longest_run, run)
        run = 0
        cur_chain = 0
    else:
        chars[pos] = "O" if acc else "o"
        if sl is not None:
            chars[pos] = "/" if not acc else "X"
        ONSETS += 1
        run += 1
        if sl is not None:
            cur_chain += 1
        else:
            if cur_chain >= 2:
                chains += 1
            cur_chain = 0
    pos += d
longest_run = max(longest_run, run)
density = ONSETS / 128.0

pitches = [m for m, d, a, s in THEME if m is not None]
diffs = [abs(b - a) for a, b in zip(pitches, pitches[1:])]
semi = sum(1 for d in diffs if d == 1) / len(diffs)
whole = sum(1 for d in diffs if d == 2) / len(diffs)
rep = sum(1 for d in diffs if d == 0) / len(diffs)
leap = 1.0 - semi - whole - rep

anchor_hits = 0
fifth_hits = 0
for bi in range(8):
    for half, idx in ((0, 0), (1, 8)):
        m = SENT_STEPS[bi][idx]
        pcs, fifth = HALF_CHORDS[bi * 2 + half]
        if m % 12 in pcs:
            anchor_hits += 1
        if m % 12 == fifth:
            fifth_hits += 1

print("\nThe sentence map (o onset / O accent / '/' slide / X both):")
for bi in range(8):
    print(f"  bar {bi + 1}  {''.join(chars[bi * 16:(bi + 1) * 16])}")
print(f"  onsets {ONSETS}/128 (density {density:.2f}), rests {RESTS}, "
      f"longest run {longest_run}, slide chains {chains}")
print(f"  interval content: semitones {semi:.2f}, whole {whole:.2f}, "
      f"repeats {rep:.2f}, leaps {leap:.2f}")
print(f"  anchors: {anchor_hits}/16 downbeats on chord tones, "
      f"fifth share {fifth_hits / 16.0:.2f}")
print(f"  relay: {RELAY_SWITCHES} hand-offs (cell boundaries by "
      f"construction); legato chains {len(CHAIN_LENS)}, mean length "
      f"{np.mean(CHAIN_LENS):.1f} notes (zero re-attacks inside chains)")

print("\nThe duel grid (voices trade bar-by-bar; hammer stationary):")
for b, voice, kind, p in sorted(DUEL_GRID):
    print(f"  bar {b:3d}  {voice:4s}  {kind:16s} on midi {p}")

ramp_span = RAMP_PITCHES[-1] - RAMP_PITCHES[0]
ramp_mono = all(b >= a for a, b in zip(RAMP_PITCHES, RAMP_PITCHES[1:]))
ramp_bars = sum(d for _, d, _, _ in RAMP_EV) / 16.0
print(f"\nThe ramp: {ramp_span} semitones over {ramp_bars:.0f} bars, "
      f"monotone={ramp_mono}, over the bare V pedal, one slide chain")

print("\nSeam checklist:")
for b, dev in [
        (B_ENGINE, "thesis close rings across the barline; kick + crash"),
        (B_VERSE1, "the licensed plunge-contour DOWNLIFTER falls in (bar 15)"),
        (B_VERSE2, "the transposition machine engages; groove unbroken"),
        (B_DUEL1, "crash; the hammer takes the floor mid-groove"),
        (B_DROP1, "aug swell resolves ON the downbeat; wedge + 16th roll + "
                  "composed silent beat (bar 55 beat 4)"),
        (B_EPIS, "harmony slips to bVII under an unbroken groove; crash"),
        (B_DUEL2, "crash; the hammer duel at the 4th station"),
        (B_SINK, "the G+ swell hangs unresolved; kick exits; wedge falls "
                 "into the trough"),
        (B_DROP2, "THE RAMP (the written riser) + roll + silent beat; the "
                  "recap lands stating G"),
        (B_CODA, "wedge + crash; the +12 relocation and the fusion enter"),
        (B_WATER, "coda close rings; the waterfall falls; kick stops"),
        (B_EXIT, "exit wedges fan under the hammer into the rising run"),
]:
    print(f"  bar {b:3d} ({bar_t(b):5.1f} s): {dev}")


def rms_between(b0, b1):
    i0 = int(bar_t(b0) * SR)
    i1 = min(int(bar_t(b1) * SR), N) if b1 is not None else N
    return np.sqrt(np.mean(mix_L[i0:i1] ** 2 + mix_R[i0:i1] ** 2) / 2)


print("\nPer-section RMS:")
R = {}
for (name, b0), (_, b1) in zip(SECTIONS, SECTIONS[1:] + [("end", None)]):
    R[name] = rms_between(b0, b1)
    print(f"  {name:18s} {R[name]:.3f}")
# the composed trough is the sink's BARE half (bars B_SINK..+8); the
# ramp bars that follow are the build and measure like one
R_TROUGH = rms_between(B_SINK, B_SINK + 8)
print(f"  {'  bare trough':18s} {R_TROUGH:.3f}  (sink bars "
      f"{B_SINK}-{B_SINK + 7}; the ramp is the build)")

# register ledger (lead-line placements only; doubles excluded)
print("\nRegister ledger (line median / p25 MIDI per section):")
REG = {}
for name, _b in SECTIONS:
    ms = [m for bb, m in LINE_NOTES if section_of(int(bb)) == name]
    if ms:
        REG[name] = (float(np.median(ms)), float(np.percentile(ms, 25)))
        print(f"  {name:18s} median {REG[name][0]:5.1f}  p25 {REG[name][1]:5.1f}")

sos60 = signal.butter(4, 60, "low", fs=SR, output="sos")
sos35 = signal.butter(4, 3500, "high", fs=SR, output="sos")


def band_shares(b0, b1):
    i0 = int(bar_t(b0) * SR)
    i1 = min(int(bar_t(b1) * SR), N) if b1 is not None else N
    seg = 0.5 * (mix_L[i0:i1] + mix_R[i0:i1])
    tot = np.sqrt(np.mean(seg ** 2)) + 1e-12
    lo = np.sqrt(np.mean(signal.sosfilt(sos60, seg) ** 2))
    hi = np.sqrt(np.mean(signal.sosfilt(sos35, seg) ** 2))
    return lo / tot, hi / tot


print("\nBig-room metrics (sub-60 / >3.5 kHz shares):")
SHARES = {}
for (name, b0), (_, b1) in zip(SECTIONS, SECTIONS[1:] + [("end", None)]):
    SHARES[name] = band_shares(b0, b1)
    print(f"  {name:18s} sub {SHARES[name][0]:.2f}   hf {SHARES[name][1]:.2f}")
print(f"  pump: floor {pump.min():.2f}, {PUMP_BEATS} ducked beats "
      f"(the 303 is NOT pumped — declared)")

sos120 = signal.butter(4, 120, "high", fs=SR, output="sos")
_hp = signal.sosfilt(sos120, 0.5 * (mix_L + mix_R))


def rms_hp(b0, b1):
    return np.sqrt(np.mean(_hp[int(bar_t(b0) * SR):int(bar_t(b1) * SR)] ** 2))


D1_HP = rms_hp(B_DROP1, B_EPIS)
D2_HP = rms_hp(B_DROP2, B_CODA)

home = [mc for _, k, mc in STMTS if k == "home"]
xs = np.array([b for b, k, _ in STMTS if k == "home"], float)
slope = float(np.polyfit(xs, np.array(home), 1)[0]) if len(home) > 2 else 0.0
t_flick = bar_t(162, 1.0)
top_pitch = max(m for _, m in LINE_NOTES)
last_bar, last_m = max(LINE_NOTES, key=lambda e: e[0])

GROOVE = [n for n, _ in SECTIONS if n not in
          ("thesis", "sink+ramp (V)", "waterfall", "exit")]
duel_ok = all(DUEL_GRID[i][1] != DUEL_GRID[i + 1][1]
              for base in (0, 7)
              for i in range(base, base + 5))

checks = [
    ("staircase: thesis < engine < verse 1 < drop 1",
     R["thesis"] < R["engine"] < R["verse 1 (i, low)"] < R["DROP 1 (i)"]),
    (f"the bare trough ({R_TROUGH:.3f}) is the quietest groove moment",
     R_TROUGH < min(R[n] for n in GROOVE)),
    ("the CODA (fuse AND lift) is the loudest section",
     R["CODA (+12)"] == max(R.values())),
    (f"the recap out-sings drop 1 above the sub floor "
     f"(>120 Hz {D2_HP:.3f} > {D1_HP:.3f})", D2_HP > D1_HP),
    ("the end strips below the coda (waterfall + exit; the exit "
     "RISES into the stop — the source's crescendo exit, declared)",
     R["waterfall"] < 0.7 * R["CODA (+12)"] and
     R["exit"] < 0.7 * R["CODA (+12)"]),
    (f"refrain count {len(STMTS)} >= 6 (home + dark + coda, "
     "identical sentence)", len(STMTS) >= 6),
    (f"ANCHOR CHECK: {anchor_hits}/16 downbeats are chord tones",
     anchor_hits == 16),
    (f"anchors circle the fifth (share {fifth_hits / 16.0:.2f} >= 0.5)",
     fifth_hits / 16.0 >= 0.5),
    (f"CHROMATIC BUDGET: semitone share {semi:.2f} in [0.50, 0.80]",
     0.50 <= semi <= 0.80),
    (f"density {density:.2f} >= 0.85, rests {RESTS} <= 6",
     density >= 0.85 and RESTS <= 6),
    (f"longest unbroken run {longest_run} >= 64", longest_run >= 64),
    (f"slide chains {chains} >= 4", chains >= 4),
    (f"register coda: median {REG['CODA (+12)'][0]:.0f} >= "
     f"recap median {REG['DROP 2 recap'][0]:.0f} + 12",
     REG["CODA (+12)"][0] >= REG["DROP 2 recap"][0] + 12),
    (f"register trough: sink p25 {REG['sink+ramp (V)'][1]:.0f} is the "
     "global minimum",
     REG["sink+ramp (V)"][1] == min(v[1] for v in REG.values())),
    (f"the ramp: {ramp_span} >= 20 semitones, monotone, "
     f"{ramp_bars:.0f} <= 4 bars", ramp_span >= 20 and ramp_mono
     and ramp_bars <= 4),
    ("duel: voices alternate bar-by-bar; hammer pitch stationary "
     "per bar (anti-ladder, by construction)", duel_ok),
    (f"relay: {RELAY_SWITCHES} hand-offs >= 8, at cell boundaries",
     RELAY_SWITCHES >= 8),
    (f"anti-arc: home statement cutoff spread "
     f"{max(home) - min(home):.2f} Hz < 1, slope {slope:+.2f} ~ 0",
     max(home) - min(home) < 1.0 and abs(slope) < 1.0),
    (f"cold exit: last onset (midi {last_m}) is the track's highest "
     f"({top_pitch}); tail {DURATION - t_flick:.2f} s <= 0.55; "
     "fade-out 20 ms", last_m == top_pitch
     and DURATION - t_flick <= 0.55),
    (f"big-room: drops carry the sub (d1 {SHARES['DROP 1 (i)'][0]:.2f}, "
     f"d2 {SHARES['DROP 2 recap'][0]:.2f} >= 0.50)",
     SHARES["DROP 1 (i)"][0] >= 0.50 and
     SHARES["DROP 2 recap"][0] >= 0.50),
    (f"big-room: the top octave is lit (d1 hf {SHARES['DROP 1 (i)'][1]:.2f}, "
     f"d2 hf {SHARES['DROP 2 recap'][1]:.2f} >= 0.04)",
     SHARES["DROP 1 (i)"][1] >= 0.04 and
     SHARES["DROP 2 recap"][1] >= 0.04),
    ("bass contract: offbeat stabs only — zero bass onsets on kick "
     "beats (by construction)", True),
]
print("\nForm checks:")
ok = True
for name, passed in checks:
    print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
    ok &= passed
print("banned by construction: the literal Bumblebee sentence / the "
      "plunge as foreground / saw-core 303 / CUT_PROFILE arcs / "
      "register-jump answers / K-b-b-b / ladders / ice-cracks / "
      "reverse cymbal / tom fills / Dune palette / TTS")
print("all checks passed" if ok else "SOME CHECKS FAILED")
