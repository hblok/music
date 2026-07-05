#!/usr/bin/env python3
"""
silver_wire_v2.py — "Silver Wire" v2 (~5:38, 142 BPM, A minor).
The melody goes acid (design notes: silver_wire_v2_notes.md; v1 =
silver_wire.py -> silver_wire.wav, kept untouched). Scope of the
revision: THE 303 MELODY ONLY — the v1 listen test validated the
structure, the question/low-answer device, the bassline and the
volumes, and all of that is FROZEN. The fail was the melody: too
simple, vocal-phrased, read as pop/funk ("Rocksteady") instead of
acid & psy.

THE V2 REFRAIN — 16 bars (Q1: "the point is to extend the tune"),
built from the acid grammar instead of vocal phrasing, CONSTRUCTED
in code from per-bar cells so every rule is enforced and checked:

  1. near-continuous 16ths — rests are punctuation (5 of 256 steps;
     v1 had 25 of 128); onset density ~0.90 (v1: 0.37); bars 1-7 are
     one unbroken 112-onset run (v1's longest run: 3);
  2. cell sequencing — winding 3-4 note cells (circle the center,
     chromatic lower neighbor, re-attack) restated up and down the
     scale, octave-displacement roll bars (4 and 12);
  3. cross-rhythm accents — every 3rd 16th, phase-locked per half
     (the acid roll), accents snapped to A-minor scale tones;
  4. slide chains mid-run — 2-4 consecutive slid notes bending
     through the turns (the 303 tie as motion-blur);
  5. free chromatics on weak 16ths (Q2), scale tones on accents;
  6. cadences avoided except the two KEPT v1 landmarks: the
     screaming hang on the dominant E (bar 8) and the long held
     G#->A slide close (bar 16, landing across the barline).

Q = bars 1-8 winding UP to the hang; A = bars 9-16 winding DOWN home
to the close. The low-register answers speak the SAME grammar now
(Q3): full-bar mini-runs under the two held landmarks (the E-rooted
run under the hang, the A-rooted run under the close — both
registers land A together across the barline). The turnaround/dip
loop is a running bar too.

Statement slots (structure bars unchanged from v1): verse = 1 full
dark statement (-12), drop 1 = 2 full + a declared Q-half, chorus 1
= 1, drop 2 = 2 (the a-cappella dip = the first 4 Q bars naked),
chorus 2 = 1 -> 7 full statements, target >= 6 (was 8 x 8-bar).
Thesis = the first 4 Q bars; bookend = the last 4 A bars + the
stated A, at the thesis filter position.

FROZEN from v1: all section bars, the kit and its psy/straight
split, the K-b-b-b bass (roll/sub modes), the Am-F-G-E laps, pads,
volumes and commit weights, the anti-arc rule + CUT_PROFILE
mechanics (now 16 entries, same contract), the 303 voice (Q 6 /
fb 1.3 / tanh 1.5), BPM 142, A minor, seed 303.

Everything synthesized (numpy + scipy).
Output: /workspace/music/silver_wire_v2.wav + silver_wire_v2.mp3.
"""

import os
import subprocess
import wave
import numpy as np
from scipy import signal

SR = 44100
DURATION = 338.0
N = int(SR * DURATION)
t = np.arange(N) / SR

rng = np.random.default_rng(303)

BPM = 142.0
BEAT = 60.0 / BPM
BAR = BEAT * 4
STEP = BEAT / 4
GRID0 = 0.5


def bar_t(b, beat=0.0):
    return GRID0 + b * BAR + beat * BEAT


# ---------------------------------------------------- section boundaries (bars)
B_ENGINE = 4
B_VERSE = 20
B_BUILD1 = 36
B_DROP1 = 44
B_CHOR1 = 92
B_BUILD2 = 108
B_DROP2 = 116
B_CHOR2 = 164
B_OUT = 180
B_KSTOP = 192
B_END = 196

D1_DIP = range(B_DROP1 + 16, B_DROP1 + 20)   # kick + the low register only
D2_DIP = range(B_DROP2 + 16, B_DROP2 + 20)   # the wire a cappella
TURN1 = range(B_DROP1 + 44, B_CHOR1)
TURN2 = range(B_DROP2 + 44, B_CHOR2)
ROLL_8TH = (B_BUILD1 + 6, B_BUILD2 + 6)
ROLL_16TH = (B_BUILD1 + 7, B_BUILD2 + 7)


def section_of(b):
    for name, b0 in [("bookend", B_KSTOP), ("outro", B_OUT),
                     ("chorus2", B_CHOR2), ("drop2", B_DROP2),
                     ("build2", B_BUILD2), ("chorus1", B_CHOR1),
                     ("drop1", B_DROP1), ("build1", B_BUILD1),
                     ("verse", B_VERSE), ("engine", B_ENGINE)]:
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
# A natural minor + free chromatics on weak 16ths (Q2). One lap:
# Am-F-G-E under the choruses; the line itself circles A — modal, per
# the acid grammar, with accents pinned to scale tones.

AM_V = (45, 52, 57, 60)
F_V = (41, 48, 57, 60)
G_V = (43, 50, 59, 62)
E_V = (40, 47, 56, 59)
PAD_LAP = [AM_V, F_V, G_V, E_V]
BASS_LAP = [33, 29, 31, 28]

SCALE_PC = {9, 11, 0, 2, 4, 5, 7}              # A B C D E F G

# THE V2 REFRAIN — constructed from per-bar cells. Each run bar is 16
# one-step entries (midi or None); slides are index sets (chains).
# The builder applies the 3-cycle accent roll (snapping accented
# chromatics to scale) and slide targets resolve to the next sounding
# note after assembly. Bars 8 and 16 are the two v1 landmarks, kept
# as literal events.

Q_STEPS = [
    # bar 1 — the home winding cell (A + chromatic lower neighbor)
    [57, 56, 57, 60, 57, 56, 57, 62, 60, 59, 57, 56, 57, 60, 62, 64],
    # bar 2 — the cell restated a third up (on C)
    [60, 59, 60, 64, 60, 59, 60, 65, 64, 62, 60, 59, 60, 62, 64, 65],
    # bar 3 — the chromatic snake pours back down
    [64, 63, 62, 61, 60, 59, 57, 56, 57, 59, 60, 62, 64, 62, 60, 59],
    # bar 4 — the octave-displacement roll
    [57, 69, 57, 69, 57, 69, 60, 57, 62, 57, 62, 57, 62, 64, 62, 60],
    # bar 5 — the cell on D (the sequence keeps climbing)
    [62, 61, 62, 65, 62, 61, 62, 67, 65, 64, 62, 61, 62, 64, 65, 67],
    # bar 6 — the climbing run
    [64, 62, 64, 65, 67, 65, 64, 62, 64, 65, 67, 68, 69, 67, 65, 64],
    # bar 7 — circling under the dominant, sliding into the hang
    [62, 63, 64, 59, 64, 63, 62, 61, 62, 63, 64, 66, 67, 66, 64, 63],
]
Q_SLIDES = [{4, 5}, {4, 5}, {0, 1, 2, 3, 12, 13, 14}, {13, 14},
            {8, 9, 10}, {10, 11, 12}, {4, 5, 6, 13, 14, 15}]

A_STEPS = [
    # bar 9 — the answer opens on the high octave, rolling
    [69, 68, 69, 72, 69, 68, 69, 71, 69, 67, 65, 64, 65, 67, 69, 67],
    # bar 10 — the cell on G, descending restatement
    [67, 66, 67, 71, 67, 66, 67, 69, 65, 64, 62, 61, 62, 64, 65, 67],
    # bar 11 — the chromatic pour-down (the long slide chains)
    [69, 67, 65, 64, 63, 62, 61, 60, 59, 58, 57, 56, 57, 59, 60, 62],
    # bar 12 — the low octave roll (mirror of bar 4)
    [57, 45, 57, 45, 57, 45, 60, 57, 55, 57, 59, 60, 62, 60, 59, 57],
    # bar 13 — the cell on F, falling
    [65, 64, 65, 69, 65, 64, 65, 67, 64, 62, 60, 59, 60, 62, 64, 65],
    # bar 14 — pedal circling; the only punctuation rests in the runs
    [57, 59, 60, None, 62, 60, 59, 57, 56, 57, 59, None, 60, 59, 57, 55],
    # bar 15 — winding down into the depth, sliding at the close
    [57, 56, 57, 60, 59, 57, 56, 55, 56, 57, 59, 57, 56, 55, 53, 52],
]
A_SLIDES = [{4, 5}, {8, 9}, {4, 5, 6, 7, 8, 9, 10}, {12, 13},
            {4, 5}, {4, 5}, {12, 13, 14, 15}]

# the two kept landmarks (v1, verbatim in spirit):
BAR8 = [[64, 10, 1, None], [None, 2, 0, None],          # THE HANG
        [62, 1, 0, None], [64, 1, 0, None],             # pickup climbs
        [66, 1, 0, None], [68, 1, 0, True]]             # ... sliding to A4
BAR16 = [[64, 2, 1, None], [None, 1, 0, None],          # THE CLOSE
         [52, 1, 0, None], [56, 12, 0, 57]]             # held G# -> A


def build_half(bars_steps, bars_slides):
    # one-step events with the 3-cycle accent roll, phase-locked per
    # half; accented chromatics snap to the nearest scale tone.
    ev = []
    g = 0
    for steps, sl in zip(bars_steps, bars_slides):
        for i, m in enumerate(steps):
            if m is None:
                ev.append([None, 1, 0, None])
                g += 1
                continue
            acc = 1 if g % 3 == 0 else 0
            if acc and (m % 12) not in SCALE_PC:
                m = m + 1 if ((m + 1) % 12) in SCALE_PC else m - 1
            ev.append([m, 1, acc, True if i in sl else None])
            g += 1
    return [ev[i * 16:(i + 1) * 16] for i in range(len(bars_steps))]


def resolve_slides(bars):
    flat = [e for bar in bars for e in bar]
    for i, e in enumerate(flat):
        if e[3] is True:
            e[3] = next((f[0] for f in flat[i + 1:] if f[0] is not None),
                        None)
    return bars


THEME_BARS = resolve_slides(build_half(Q_STEPS, Q_SLIDES) + [BAR8] +
                            build_half(A_STEPS, A_SLIDES) + [BAR16])
THEME = [tuple(e) for bar in THEME_BARS for e in bar]
assert sum(d for _, d, _, _ in THEME) == 256


def bars_ev(a, b):
    return [tuple(e) for bar in THEME_BARS[a:b] for e in bar]


THESIS_EV = bars_ev(0, 4)          # the first 4 Q bars — the hook
QHALF_EV = bars_ev(0, 8)           # the declared half-statement
DIP_EV = bars_ev(0, 4)             # the a-cappella fragment
FRAG = bars_ev(0, 2)               # the low mutter
BOOK_EV = bars_ev(12, 16) + [(57, 10, 0, None)]   # ... and A is STATED

# The per-statement cutoff expression profile — 16 entries now, same
# anti-arc contract: identical every statement, peak at the hang,
# sinking for the close. Never a track-long ramp.
CUT_PROFILE = [1.00, 1.00, 1.05, 1.05, 1.10, 1.15, 1.25, 1.35,
               1.10, 1.05, 1.00, 0.95, 1.00, 1.05, 1.00, 0.90]

# The low-register answers — the new grammar too (Q3): full-bar
# mini-runs under the two held landmarks. E-rooted under the hang,
# A-rooted under the close (both registers land A together).
ANSW_Q_EV = [tuple(e) for bar in resolve_slides(build_half(
    [[40, 39, 40, 43, 40, 39, 40, 45, 43, 41, 40, 39, 40, 43, 45, 47]],
    [{4, 5, 12, 13}])) for e in bar]
ANSW_A_EV = [tuple(e) for bar in resolve_slides(build_half(
    [[45, 44, 45, 47, 45, 43, 41, 40, 43, 41, 40, 39, 40, 43, 44, 45]],
    [{8, 9, 13, 14}])) for e in bar]
ANSW_LOOP_EV = [tuple(e) for bar in resolve_slides(build_half(
    [[45, 44, 45, 48, 45, 44, 45, 50, 48, 47, 45, 44, 45, 47, 48, 50]],
    [{4, 5, 12, 13}])) for e in bar]

STMTS = []


# ---------------------------------------------------------------- drums
# FROZEN v1 kit (dune psy recipes via maschinenherz).

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


def make_zap():
    n = int(0.40 * SR)
    td = np.arange(n) / SR
    f_curve = 80.0 + 1900.0 * np.exp(-td * 18.0)
    x = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    x *= 1.0 + 0.5 * np.sin(2 * np.pi * 35.0 * td)
    x *= np.exp(-td * 8.0) * (1 - np.exp(-td / 0.002))
    return x / (np.max(np.abs(x)) + 1e-12)


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
CHAT = make_hat()
CLAP = make_clap()
CRASH = make_crash()
ZAP = make_zap()
SNARE = make_snare()


def kick_on(b):
    s = section_of(b)
    if s in ("thesis", "bookend"):
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
    if b in ROLL_16TH:
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


# ---------------------------------------------------------------- bass

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


PB = {m: psy_bass_note(m) for m in (33, 29, 31, 28, 40, 45)}
SB = {m: sub_note(m) for m in (33, 29, 31, 28)}
BASS_GAP_VIOLATIONS = 0
BASS_EVENTS = 0


def bass_mode(b):
    s = section_of(b)
    if s in ("thesis", "bookend") or b < 8:
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
    return 33


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
                m = [33, 40, 45][s16 - 1]
            smp = PB[m] if mode == "roll" else SB[m]
            add_at(lay_L, smp, bar_t(b, beat + s16 * 0.25), g * gg)
            add_at(lay_R, smp, bar_t(b, beat + s16 * 0.25), g * gg)
            BASS_EVENTS += 1
            if s16 == 0:
                BASS_GAP_VIOLATIONS += 1
commit(lay_L, lay_R, 0.28)
print("bass committed (roll outside the drops, sub duty inside)")


# ---------------------------------------------------------------- hats

clear()
for b in range(B_END):
    s = section_of(b)
    if s in ("thesis", "bookend") or b < 12:
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
    if s in ("engine", "verse", "chorus1", "chorus2") and b >= 16:
        for s16 in range(16):
            if s16 % 2 == 0:
                continue
            p = 0.3 + 0.4 * ((s16 // 2) % 2)
            add_at(lay_L, CHAT, bar_t(b, s16 * 0.25),
                   g * 0.35 * np.cos(p * np.pi / 2))
            add_at(lay_R, CHAT, bar_t(b, s16 * 0.25),
                   g * 0.35 * np.sin(p * np.pi / 2))
commit(lay_L, lay_R, 0.12)
print("hats committed")

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
             (B_DROP2, 1.0), (B_DROP2 + 20, 0.6), (B_CHOR2, 0.9)]:
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
# FROZEN v1 voice: Q 6, feedback 1.3/1.35, tanh(1.5), rolled partials,
# sine body core, within-note sweep, slides. Dry.

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
    cuts = []
    step = 0
    for m, d, acc, sl in events:
        if m is not None:
            cut = base_cut * prof[(step // 16) % len(prof)]
            cut *= 1.0 + 0.10 * np.sin(2 * np.pi * (step % 16) / 16.0)
            cuts.append(cut * (1.5 if acc else 1.0))
            dur = d * STEP * (1.02 if sl else 0.92)
            x = acid_note(m + octave, cut, accent=bool(acc),
                          slide_to=(sl + octave if sl else None), dur=dur)
            g = gain * (1.1 if acc else 1.0)
            add_at(lay_L, x, bar_t(b0, step * 0.25), g)
            add_at(lay_R, x, bar_t(b0, step * 0.25), g * 0.97)
        step += d
    return cuts


def place_statement(b0, stype, octave=0, base=900, gain=1.0,
                    answers=(), double=False):
    cuts = place_events(b0, THEME, octave, base, gain, CUT_PROFILE)
    if double:
        place_events(b0, THEME, octave + 12, base, gain * 0.38, CUT_PROFILE)
    for off, ev, g2 in answers:
        place_events(b0 + off, ev, 0, base * 0.6, g2, [1.0])
    STMTS.append((b0, stype, float(np.mean(cuts))))


ANSW_BOTH = [(7, ANSW_Q_EV, 0.9), (15, ANSW_A_EV, 0.9)]

clear()
# thesis: the first 4 Q bars — the cell and its first sequence steps
place_events(0, THESIS_EV, 0, 650, 0.9, CUT_PROFILE[:4])
# engine: the low mutters
place_events(8, FRAG, -12, 480, 0.65, CUT_PROFILE[:2])
place_events(14, FRAG, -12, 480, 0.65, CUT_PROFILE[:2])
# verse: ONE full dark statement, 16 bars, answers under both landmarks
place_statement(B_VERSE, "dark", octave=-12, base=620, gain=0.8,
                answers=[(7, ANSW_Q_EV, 0.8), (15, ANSW_A_EV, 0.8)])
# DROP 1 — two full statements + the declared Q-half
place_statement(B_DROP1, "home",
                answers=[(15, ANSW_A_EV, 0.85)])         # 1: nearly alone
for b in D1_DIP:
    place_events(b, ANSW_LOOP_EV, 0, 540, 0.9, [1.0])    # the low register
place_statement(B_DROP1 + 20, "home", answers=ANSW_BOTH)  # 2: the trades
place_events(B_DROP1 + 36, QHALF_EV, 0, 900, 1.0,
             CUT_PROFILE[:8])                            # the Q-half
place_events(B_DROP1 + 43, ANSW_Q_EV, 0, 540, 1.05, [1.0])
for b in TURN1:
    place_events(b, ANSW_LOOP_EV, 0, 620, 0.8, [1.0])
# chorus 1 — one full statement over the walking lap
place_statement(B_CHOR1, "chorus", base=950)
place_events(B_BUILD2, [(57, 6, 0, None)], 0, 950 * CUT_PROFILE[0],
             0.8, [1.0])                                 # the RESOLVE
# build 2 — the trough; the wire mutters its own pickup
place_events(B_BUILD2 + 1, FRAG, -12, 500, 0.6, CUT_PROFILE[:2])
place_events(B_BUILD2 + 4, bars_ev(0, 1), -12, 500, 0.6, CUT_PROFILE[:1])
# DROP 2 — two full statements; the a-cappella dip; the doubling
place_statement(B_DROP2, "home", answers=ANSW_BOTH)
place_events(B_DROP2 + 16, DIP_EV, 0, 900, 1.0,
             CUT_PROFILE[:4])                            # a cappella
place_statement(B_DROP2 + 20, "home", double=True, answers=ANSW_BOTH)
place_events(B_DROP2 + 36, QHALF_EV, 0, 900, 1.0, CUT_PROFILE[:8])
place_events(B_DROP2 + 43, ANSW_Q_EV, 0, 540, 1.0, [1.0])
for b in TURN2:
    place_events(b, ANSW_LOOP_EV, 0, 680, 0.9, [1.0])
# chorus 2 — one full statement, all registers
place_statement(B_CHOR2, "chorus", base=950, double=True,
                answers=ANSW_BOTH)
place_events(B_OUT, [(57, 6, 0, None)], 0, 950 * CUT_PROFILE[0],
             0.8, [1.0])
# outro mutters
place_events(B_OUT + 2, FRAG, -12, 480, 0.5, CUT_PROFILE[:2])
place_events(B_OUT + 6, bars_ev(0, 1), -12, 480, 0.4, CUT_PROFILE[:1])
# bookend: the last 4 A bars at the thesis filter; the A is stated
place_events(B_KSTOP, BOOK_EV, 0, 650, 0.9,
             CUT_PROFILE[12:] + [0.9])
commit(lay_L, lay_R, 0.30)
print(f"the 303 committed ({len(acid_cache)} cached notes)")


# ------------------------------------------------------------------ pads

def pad_chord(chord, dur, attack=0.35, release=1.0):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    L = np.zeros(n)
    R = np.zeros(n)
    for m in chord:
        f = midi_to_hz(m)
        amp = 0.8 + 0.2 * np.sin(2 * np.pi * rng.uniform(0.02, 0.06) * tt +
                                 rng.uniform(0, 6))
        for det, gL, gR in [(0.9993, 1.0, 0.65), (1.0007, 0.65, 1.0)]:
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
for b in range(B_CHOR1, B_BUILD2):
    pL, pR = pad_chord(PAD_LAP[b % 4], BAR + 0.8)
    add_at(lay_L, pL, bar_t(b), 0.9)
    add_at(lay_R, pR, bar_t(b), 0.9)
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
    pL, pR = pad_chord(AM_V, 4 * BAR + 1.5, attack=1.5, release=2.5)
    g = 0.8 - 0.35 * (b - B_OUT) / 8
    add_at(lay_L, pL, bar_t(b), g)
    add_at(lay_R, pR, bar_t(b), g)
lay_L = reverb(lay_L, IR_L, 0.5)
lay_R = reverb(lay_R, IR_R, 0.5)
commit(lay_L, lay_R, 0.13)
print("pads committed")


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

fade(mix_L)
fade(mix_R)

peak = max(np.max(np.abs(mix_L)), np.max(np.abs(mix_R)))
mix_L = mix_L / peak * 0.86
mix_R = mix_R / peak * 0.86

stereo = np.empty((N, 2))
stereo[:, 0] = mix_L
stereo[:, 1] = mix_R
pcm = (stereo * 32767.0).astype(np.int16)

OUT_DIR = "/workspace/music"
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, "silver_wire_v2.wav")
with wave.open(OUT, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())

print(f"\nCreated: {os.path.abspath(OUT)}")
print(f"Duration: {N / SR:.1f} s  |  {SR} Hz stereo, 16-bit PCM  |  "
      f"{BPM:.0f} BPM, A minor (Am-F-G-E; the G# of E sung by the wire)")

MP3 = os.path.join(OUT_DIR, "silver_wire_v2.mp3")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", OUT,
                "-vn", "-ar", "44100", "-ac", "2", "-b:a", "192k", MP3],
               check=True)
print(f"Created: {os.path.abspath(MP3)}  (192k mp3)")

# ---------------------------------------------------------------- verify form
# v1 blocks + the COMPLEXITY block this revision exists for.

print("\nSection map:")
SECTIONS = [("thesis", 0), ("engine", B_ENGINE), ("verse (dark)", B_VERSE),
            ("build 1", B_BUILD1), ("DROP 1 (pedal)", B_DROP1),
            ("chorus 1", B_CHOR1), ("build 2 (trough)", B_BUILD2),
            ("DROP 2 (summit)", B_DROP2), ("chorus 2", B_CHOR2),
            ("outro", B_OUT), ("bookend", B_KSTOP)]
for name, b in SECTIONS:
    print(f"  {bar_t(b):6.1f} s  bar {b:3d}  {name}")
print(f"  {DURATION:6.1f} s  end")

print(f"\nRefrain statements (16 bars, identical maps): {len(STMTS)}")
for b0, stype, mc in STMTS:
    print(f"  bar {b0:3d}  {stype:7s}  mean cutoff {mc:6.1f} Hz")
print("  declared fragments (uncounted): thesis Q bars 1-4, mutters, the "
      f"Q-halves (bars {B_DROP1 + 36}/{B_DROP2 + 36}), the a-cappella dip "
      f"(bar {B_DROP2 + 16}), answer runs, bookend A bars 13-16")

# the melody map + the complexity metrics, all from THEME itself
chars = ["."] * 256
pos = 0
SOUNDING = 0
TIED = 0
ONSETS = 0
RESTS = 0
runs = []
cur_run = 0
slide_groups = 0
cur_chain = 0
for m, d, acc, sl in THEME:
    if m is None:
        RESTS += d
        runs.append(cur_run)
        cur_run = 0
        if cur_chain >= 2:
            slide_groups += 1
        cur_chain = 0
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
                slide_groups += 1
            cur_chain = 0
    pos += d
runs.append(cur_run)
longest_run = max(runs)
tie_frac = TIED / SOUNDING
onset_density = ONSETS / 256.0

# accent cross-rhythm: consecutive bars whose accents share one residue
# mod 3 with their neighbours (the roll window)
bar_res = []
pos = 0
for m, d, acc, sl in THEME:
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

hang_ok = any(m == 64 and d >= 10 for m, d, _, _ in THEME)
close_ok = any(m == 56 and d >= 12 and sl == 57 for m, d, _, sl in THEME)

print("\nThe refrain map (o onset / O accent / = held / '/' slide):")
for bar in range(16):
    print(f"  bar {bar + 1:2d}  {''.join(chars[bar * 16:(bar + 1) * 16])}")
print(f"  onsets {ONSETS}/256 (density {onset_density:.2f}), rests {RESTS}, "
      f"longest run {longest_run}, slide chains {slide_groups}, "
      f"tied/slid fraction {tie_frac:.2f}")

print("\nSeam checklist (what crosses every boundary):")
for b, dev in [(B_ENGINE, "the thesis' last run-note rings; kick enters (crash)"),
               (B_VERSE, "gait unbroken; the dark statement enters mid-groove"),
               (B_BUILD1, "bass keeps rolling; snare roll + swell begin"),
               (B_DROP1, "16th kick roll into the composed silent beat (bar 43 beat 4); swell peaks ON the downbeat"),
               (B_CHOR1, "the low-run turnaround (bars 88-91); crash; the lap arrives"),
               (B_BUILD2, "chorus close: the G#->A RESOLVE rings across bar 108; kick out, bass stays"),
               (B_DROP2, "16th roll + silent beat (bar 115 beat 4); the drop downbeat states A"),
               (B_CHOR2, "the low-run turnaround (bars 160-163); harmony continuous; crash"),
               (B_OUT, "chorus 2's RESOLVE rings across bar 180; strip begins"),
               (B_KSTOP, "kick stops; the wire alone at the thesis filter position")]:
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

home = [mc for _, s, mc in STMTS if s == "home"]
chor = [mc for _, s, mc in STMTS if s == "chorus"]
rec = [(b, mc) for b, s, mc in STMTS if s in ("home", "chorus")]
xs = np.array([b for b, _ in rec], float)
ys = np.array([mc for _, mc in rec], float)
slope = float(np.polyfit(xs, ys, 1)[0])
checks = [
    ("staircase: engine < verse < drop 1",
     R["engine"] < R["verse (dark)"] < R["DROP 1 (pedal)"]),
    ("build 2 is the trough",
     R["build 2 (trough)"] < min(R["chorus 1"], R["DROP 2 (summit)"])),
    ("drop 2 (the summit run) > drop 1",
     R["DROP 2 (summit)"] > R["DROP 1 (pedal)"]),
    ("the summit is drop 2 or chorus 2",
     max(R.values()) in (R["DROP 2 (summit)"], R["chorus 2"])),
    ("the outro settles; the bookend is the quiet end",
     R["outro"] < R["chorus 2"] and R["bookend"] < R["build 2 (trough)"]),
    (f"refrain count >= 6 (got {len(STMTS)}, 16 bars each)",
     len(STMTS) >= 6),
    ("anti-arc: home statements share one profile "
     f"(spread {max(home) - min(home):.2f} Hz)", max(home) - min(home) < 1.0),
    ("anti-arc: chorus statements share one profile "
     f"(spread {max(chor) - min(chor):.2f} Hz)", max(chor) - min(chor) < 1.0),
    (f"anti-arc: no brightness trend (slope {slope:+.2f} Hz/bar)",
     abs(slope) < 1.0),
    (f"complexity: onset density {onset_density:.2f} >= 0.70 (v1: 0.37)",
     onset_density >= 0.70),
    (f"complexity: rests {RESTS} <= 24 of 256 (v1: 25 of 128)", RESTS <= 24),
    (f"complexity: longest unbroken run {longest_run} >= 32 (v1: 3)",
     longest_run >= 32),
    (f"complexity: accent 3-cycle streak {best_streak} bars >= 4",
     best_streak >= 4),
    (f"complexity: slide chains {slide_groups} >= 4", slide_groups >= 4),
    (f"sings-not-plinks: tied/slid fraction {tie_frac:.2f} >= 0.25",
     tie_frac >= 0.25),
    ("landmarks kept: the E hang (bar 8) and the G#->A close (bar 16)",
     hang_ok and close_ok),
    (f"K-b-b-b contract: zero bass hits on kick 16ths "
     f"({BASS_EVENTS} bass events)", BASS_GAP_VIOLATIONS == 0),
]
print("\nForm checks:")
ok = True
for name, passed in checks:
    print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
    ok &= passed
print("banned by construction: second 303 / any voice / gothic piano / "
      "rompler strings / Dune palette / TTS / ladders / ice-cracks / "
      "tom fills / reverse cymbal / track-long filter arc")
print("all checks passed" if ok else "SOME CHECKS FAILED")
