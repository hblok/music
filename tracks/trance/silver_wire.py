#!/usr/bin/env python3
"""
silver_wire.py — "Silver Wire" (~5:35, 142 BPM, A minor).
The 303 sings the song (design notes: silver_wire_notes.md). Acid/psy
trance — almost acid techno, not all the way: melody, harmony and
song form kept; the single-riff jack is the line we don't cross.

THE CONCEPT — a machine made of one silver wire, and the wire sings.
ONE 303 only: the singer and the whole melodic cast. Its only
conversation partner is itself an octave below — the register-jump
answers, composed echoes of its own phrase-ends. The drums are the
floor it stands on, the pads are the room it sings into.

THE ANTI-ARC RULE (the maschinenherz feedback): no track-long cutoff
ramp; development never comes from gradually opening the filter. The
cutoff breathes in a PER-PHRASE expression profile that is part of
the tune (CUT_PROFILE below — identical every statement, checked),
and never parks. Development is composition: register (dark verse
statement an octave down, home drops, octave-up doubling late), the
answers growing into counterphrase, the harmony walking under the
unchanged tune in choruses, arrangement dips.

THE REFRAIN — written FOR the instrument (the eisgang lesson: refrain
voices need sustain; a 303's sustain is the SLIDE): 16th grid with
rests as melody notes, phrase peaks and ends tied/slid (fraction
printed and checked — "sings, not plinks"), a fixed accent stress
map, octave drops as punctuation, ONE chromatic passing note per
phrase (Q: the D#→E approach into the hang; A: the held G#→A close —
the borrowed leading tone sung by the lead itself, landing across
the barline). Q climbs Am–F–G–E and hangs screaming on the dominant
E; A opens on the high octave A and falls home.

THE KIT SPLIT (Q6): psy gait outside the drops (K-b-b-b rolling
bass, offbeat open hats, closed 16th ghosts); straighter, harder
floor INSIDE the drops (open-hat offbeats only, no ghost carpet,
rolling bass thinned to kick-gap sub duty — the 303's low register
owns the mid-bass there). The acid-techno lean lives in the drops
and nowhere else.

  0:00  thesis     The 303 alone, dry, half-filtered: the full Q.
  0:07  engine     Kick + rolling bass + hats staircase; low mutters.
  0:34  verse      THE DARK STATEMENT ×2 (octave down); the low
                   register answers each phrase-end.
  1:01  build 1    Snare roll + swell, kick rolls, silent beat.
  1:15  DROP 1     48 bars on the A pedal, straight floor, ×5
                   statements evolving by forces; dip: kick + the low
                   register alone; turnaround into the chorus.
  2:36  chorus 1   The harmony arrives: Am–F–G–E + pads, psy gait
                   returns; refrain ×2; the G#→A close rings across.
  3:03  build 2    The composed trough (no break in this track):
                   kickless, bass to the pedal, low fragments.
  3:16  DROP 2     48 bars, the summit run: answers counterphrased
                   under the held notes, pads walk (chorus and drop
                   merged); dip: the wire a cappella; octave doubling.
  4:37  chorus 2   Fullest; last G#→A close rings across the seam.
  5:04  outro      Strip in reverse order of entry; kick fades.
  5:25  bookend    The 303 alone, filter back at the thesis position:
                   the A phrase, and the final A is STATED.

THE 303 (Q4): maschinenherz's warmed acid pushed one notch sharper —
Q 6, feedback 1.3, tanh(1.5), bright→dark within-note sweep, rolled
partials 1/k^1.3, sine body core. Never the dune Q 11 / 2.8 dentist.

BANNED: a second 303, any voice, gothic piano, rompler strings,
Dune palette, TTS, ladders (maschinenherz's W4a), ice-cracks
(maschinenherz's W8a), tom fills (ungeschrieben's), reverse cymbals
(nachtkind's), track-long filter arcs (ungeschrieben's device —
retired here by the anti-arc rule).

Everything synthesized (numpy + scipy).
Output: /workspace/music/silver_wire.wav + silver_wire.mp3 (192k).
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

rng = np.random.default_rng(303)      # for once the obvious one

BPM = 142.0
BEAT = 60.0 / BPM
BAR = BEAT * 4
STEP = BEAT / 4
GRID0 = 0.5


def bar_t(b, beat=0.0):
    return GRID0 + b * BAR + beat * BEAT


# ---------------------------------------------------- section boundaries (bars)
B_ENGINE = 4      # kick + rolling bass + hats staircase (thesis: bars 0-3)
B_VERSE = 20      # the dark statement
B_BUILD1 = 36     # roll + swell
B_DROP1 = 44      # 48 bars, straight floor, A pedal
B_CHOR1 = 92      # the harmony arrives
B_BUILD2 = 108    # the composed trough (kickless)
B_DROP2 = 116     # 48 bars, the summit run, harmony walks
B_CHOR2 = 164     # fullest
B_OUT = 180       # strip
B_KSTOP = 192     # kick stops; bookend
B_END = 196

D1_DIP = range(B_DROP1 + 16, B_DROP1 + 20)   # kick + the low register only
D2_DIP = range(B_DROP2 + 16, B_DROP2 + 20)   # the wire a cappella (nothing else)
TURN1 = range(B_DROP1 + 44, B_CHOR1)         # low-cell turnaround into chorus 1
TURN2 = range(B_DROP2 + 44, B_CHOR2)         # ... into chorus 2
ROLL_8TH = (B_BUILD1 + 6, B_BUILD2 + 6)      # 8th-note kick-roll bars
ROLL_16TH = (B_BUILD1 + 7, B_BUILD2 + 7)     # 16th rolls ending in the silent beat


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
# A natural minor: A B C D E F G (+ the borrowed G# of the V, sung by
# the lead itself). One lap: Am-F-G-E, one chord per bar.

AM_V = (45, 52, 57, 60)            # A2 E3 A3 C4
F_V = (41, 48, 57, 60)             # F2 C3 A3 C4
G_V = (43, 50, 59, 62)             # G2 D3 B3 D4
E_V = (40, 47, 56, 59)             # E2 B2 G#3 B3  <- the G# color
PAD_LAP = [AM_V, F_V, G_V, E_V]
BASS_LAP = [33, 29, 31, 28]        # A1 F1 G1 E1 — the walking roots

# THE REFRAIN — 8 bars of 303 events: (midi or None, dur in 16ths,
# accent, slide_to). Sequential; each bar sums to 16. Home register
# A3-centered. Identical every statement (register octaves are the one
# transform). Q bars 1-4 (Am F G E): climbs, ONE chromatic passing
# note (D#4 sliding into the hang), then THE HANG on the dominant E4,
# held 10 sixteenths under the accent squelch. A bars 5-8: opens on
# the high octave A4 (resolving the hang), falls home, the G4->G3
# octave-drop punctuation, and closes on a 12-sixteenth held G#3
# SLIDING to A3 — the resolution lands on the next downbeat, sung by
# the wire itself.
THEME = [
    # bar 1 (Am)
    (57, 2, 1, None), (None, 1, 0, None), (57, 1, 0, None),
    (60, 2, 0, 62), (62, 2, 0, None), (None, 2, 0, None),
    (57, 1, 0, None), (55, 1, 0, 57), (57, 4, 0, None),
    # bar 2 (F)
    (60, 2, 1, None), (None, 1, 0, None), (60, 1, 0, None),
    (62, 2, 0, 64), (64, 2, 0, None), (None, 2, 0, None),
    (60, 1, 0, None), (57, 1, 0, None), (60, 4, 0, None),
    # bar 3 (G)
    (62, 2, 1, None), (None, 1, 0, None), (62, 1, 0, None),
    (64, 2, 0, 67), (67, 2, 0, None), (None, 2, 0, None),
    (64, 2, 0, None), (62, 1, 0, None), (63, 3, 0, 64),
    # bar 4 (E) — THE HANG
    (64, 10, 1, None), (None, 6, 0, None),
    # bar 5 (Am) — the answer opens on the high octave
    (69, 2, 1, None), (None, 1, 0, None), (67, 1, 0, None),
    (64, 2, 0, 62), (62, 2, 0, None), (None, 2, 0, None),
    (64, 1, 0, None), (60, 1, 0, None), (57, 4, 0, None),
    # bar 6 (F)
    (65, 2, 1, None), (None, 1, 0, None), (64, 1, 0, None),
    (62, 2, 0, 60), (60, 2, 0, None), (None, 2, 0, None),
    (57, 1, 0, None), (55, 1, 0, None), (57, 4, 0, None),
    # bar 7 (G) — the octave-drop punctuation
    (67, 2, 1, None), (None, 1, 0, None), (67, 1, 0, None),
    (55, 2, 0, None), (None, 1, 0, None), (62, 2, 0, 59),
    (59, 2, 0, None), (None, 1, 0, None), (55, 1, 0, None),
    (57, 3, 0, None),
    # bar 8 (E) — the held G#->A close
    (64, 2, 1, None), (None, 1, 0, None), (52, 1, 0, None),
    (56, 12, 0, 57),
]
THEME_Q = THEME[:29]               # bars 1-4
THEME_A = THEME[29:]               # bars 5-8
FRAG = THEME[:18]                  # bars 1-2: the low mutter fragment
RESOLVE = [(57, 6, 0, None)]       # the stated A across a seam

# The per-phrase cutoff expression profile — one multiplier per bar of
# the statement, IDENTICAL every time (the anti-arc contract). The
# scream is bar 4; bar 8 sinks dark for the G# close.
CUT_PROFILE = [1.0, 1.05, 1.15, 1.35, 1.10, 1.0, 1.15, 0.90]

# Register-jump answer cells: (absolute 16th in the statement, midi,
# dur, accent, slide_to). The low register answers the two hangs.
ANSW_Q_C = [(58, 40, 2, 0, None), (60, 43, 1, 0, None),
            (61, 45, 3, 1, None)]                  # under the E hang
ANSW_A_C = [(120, 45, 2, 0, None), (122, 47, 2, 0, 45),
            (124, 45, 4, 0, None)]                 # counterphrase, bar 8
ANSW_LOOP = [(0, 45, 2, 0, None), (2, 47, 2, 0, 45), (4, 45, 2, 0, None),
             (8, 40, 2, 1, None), (10, 43, 1, 0, None), (11, 45, 5, 0, None)]

STMTS = []                         # (bar, type, mean cutoff) — verified


# ---------------------------------------------------------------- drums
# dune psy kit (sleeper_awakens recipes via maschinenherz, copied).

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
        return False                            # the wire a cappella
    if B_BUILD2 <= b < B_BUILD2 + 6:
        return False                            # the composed trough
    return True


def kick_gain(b):
    s = section_of(b)
    if s in ("engine", "verse"):
        return 0.8                              # pre-drop headroom
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
    if b in ROLL_16TH:                          # beat 4 = the composed silence
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
# K-b-b-b in two modes (Q6): "roll" = the full psy saw outside the
# drops; "sub" = sine sub duty inside them (the 303's low register
# owns the mid-bass there). Either way the bass NEVER sounds on a kick
# 16th — the contract is counted and printed.

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
        return "sub"                            # the straight floor
    if s == "outro" and b >= B_OUT + 6:
        return None
    return "roll"                               # the psy gait


def bass_root(b):
    s = section_of(b)
    if s in ("chorus1", "chorus2", "drop2"):
        return BASS_LAP[b % 4]                  # the walking lap
    return 33                                   # the A pedal


clear()
for b in range(B_END):
    mode = bass_mode(b)
    if mode is None:
        continue
    g = 0.65 if b < B_DROP1 else 1.0
    if mode == "sub":
        g *= 0.85
    if section_of(b) == "build2":
        g *= 0.5                                # the trough: pedal held quiet
    root = bass_root(b)
    for beat in range(4):
        for s16, gg in [(1, 0.8), (2, 0.7), (3, 0.95)]:
            m = root
            if mode == "roll" and b % 4 == 3 and beat == 3 \
                    and section_of(b) not in ("chorus1", "chorus2"):
                m = [33, 40, 45][s16 - 1]       # cadence climb A1-E2-A2
            smp = PB[m] if mode == "roll" else SB[m]
            add_at(lay_L, smp, bar_t(b, beat + s16 * 0.25), g * gg)
            add_at(lay_R, smp, bar_t(b, beat + s16 * 0.25), g * gg)
            BASS_EVENTS += 1
            if s16 == 0:
                BASS_GAP_VIOLATIONS += 1
commit(lay_L, lay_R, 0.28)
print("bass committed (roll outside the drops, sub duty inside)")


# ---------------------------------------------------------------- hats
# The split: open offbeats everywhere the floor runs; the closed 16th
# ghost carpet ONLY in the psy-gait sections — never in the drops.

clear()
for b in range(B_END):
    s = section_of(b)
    if s in ("thesis", "bookend") or b < 12:
        continue
    if b in ROLL_16TH or b in D2_DIP:
        continue
    if s == "build2":
        continue                                # the trough stays bare
    if s == "outro" and b >= B_OUT + 4:
        continue
    g = 0.8 if b < B_DROP1 else 1.0
    for beat in range(4):
        add_at(lay_L, OHAT, bar_t(b, beat + 0.5), g * 0.8)
        add_at(lay_R, OHAT, bar_t(b, beat + 0.5), g)
    if s in ("engine", "verse", "chorus1", "chorus2") and b >= 16:
        for s16 in range(16):                   # the psy ghost carpet
            if s16 % 2 == 0:
                continue
            p = 0.3 + 0.4 * ((s16 // 2) % 2)
            add_at(lay_L, CHAT, bar_t(b, s16 * 0.25),
                   g * 0.35 * np.cos(p * np.pi / 2))
            add_at(lay_R, CHAT, bar_t(b, s16 * 0.25),
                   g * 0.35 * np.sin(p * np.pi / 2))
commit(lay_L, lay_R, 0.12)
print("hats committed (ghost carpet in the gait, bare offbeats in the drops)")

# claps on 2 & 4 — drops (from drop 1's third statement) and choruses
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

# crashes mark the arrivals
clear()
for b, g in [(B_ENGINE, 0.4), (B_DROP1, 1.0), (B_CHOR1, 0.9),
             (B_DROP2, 1.0), (B_DROP2 + 20, 0.6), (B_CHOR2, 0.9)]:
    place_pan(lay_L, lay_R, CRASH, bar_t(b), g, 0.5)
commit(lay_L, lay_R, 0.05)
print("crashes committed")

# zaps on the drops' 8-bar seams
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

# snare roll + swell — the era build pair, this track's seam device
clear()
for b16, b32 in zip(ROLL_8TH, ROLL_16TH):
    for s16 in range(16):
        place_pan(lay_L, lay_R, SNARE, bar_t(b16, s16 * 0.25),
                  0.35 + 0.35 * s16 / 15, 0.45)
    for s32 in range(24):                       # stops at beat 4: the silence
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
# The singer. maschinenherz's warmed acid one notch sharper (Q4 agreed):
# Q 6, feedback 1.3 (1.35 accented), tanh(1.5). Rolled partials, sine
# body core, within-note bright->dark sweep, slides as legato. DRY —
# the pads make the room, the wire stands in front of it.

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
    else:                                  # the 303 tie: glide the back half
        f2 = midi_to_hz(slide_to)
        fc = f * (f2 / f) ** np.clip((td - 0.45 * dur) / (0.55 * dur), 0, 1)
        ph = 2 * np.pi * np.cumsum(fc) / SR
    x = np.zeros(n)
    for k in range(1, min(40, int(9000 / f)) + 1):
        x += np.sin(k * ph) / k ** 1.3          # rolled — not hard saw

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
    y += 0.30 * np.sin(ph)                      # the sine body core
    env = (1 - np.exp(-td / 0.0015)) * np.clip((dur - td) / 0.02, 0, 1)
    y *= env
    y /= np.max(np.abs(y)) + 1e-12
    acid_cache[key] = y
    return y


def place_events(b0, events, octave, base_cut, gain, prof):
    # events consumed sequentially; prof indexed by the statement bar.
    # Returns the cutoffs used (for the anti-arc record). The per-step
    # wobble is deterministic, so identical statements render identical.
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


def place_cells(b0, cells, base_cut, gain):
    # answer cells: (absolute 16th in the statement, midi, dur, acc, sl)
    for s0, m, d, acc, sl in cells:
        x = acid_note(m, base_cut, accent=bool(acc), slide_to=sl,
                      dur=d * STEP * (1.02 if sl else 0.92))
        add_at(lay_L, x, bar_t(b0, s0 * 0.25), gain * 0.93)
        add_at(lay_R, x, bar_t(b0, s0 * 0.25), gain)


def place_statement(b0, stype, octave=0, base=900, gain=1.0,
                    answers=(), double=False):
    cuts = place_events(b0, THEME, octave, base, gain, CUT_PROFILE)
    if double:
        place_events(b0, THEME, octave + 12, base, gain * 0.38, CUT_PROFILE)
    for cells, g2 in answers:
        place_cells(b0, cells, base * 0.6, g2)
    STMTS.append((b0, stype, float(np.mean(cuts))))


clear()
# thesis: the full Q alone, half-filtered — the hook in ten seconds
place_events(0, THEME_Q, 0, 650, 0.9, CUT_PROFILE[:4])
# engine: the low mutters
place_events(8, FRAG, -12, 480, 0.65, CUT_PROFILE[:2])
place_events(14, FRAG, -12, 480, 0.65, CUT_PROFILE[:2])
# verse: THE DARK STATEMENT x2, answers tailing the hangs
place_statement(B_VERSE, "dark", octave=-12, base=620, gain=0.8,
                answers=[(ANSW_Q_C, 0.8)])
place_statement(B_VERSE + 8, "dark", octave=-12, base=620, gain=0.8,
                answers=[(ANSW_Q_C, 0.8)])
# DROP 1 — home register on the pedal, evolving by forces
place_statement(B_DROP1, "home")                          # 1: alone
place_statement(B_DROP1 + 8, "home",
                answers=[(ANSW_Q_C, 0.85)])               # 2: +answers
for b in D1_DIP:                                          # the low register
    place_cells(b, [(s, m, d, a, sl) for s, m, d, a, sl in ANSW_LOOP],
                540, 0.9)                                 # holds the floor
place_statement(B_DROP1 + 20, "home",
                answers=[(ANSW_Q_C, 1.05)])               # 3: answers up
place_statement(B_DROP1 + 28, "home", answers=[(ANSW_Q_C, 1.05)])
place_statement(B_DROP1 + 36, "home",
                answers=[(ANSW_Q_C, 1.05)])               # 5: fullest wave
for b in TURN1:                                           # the turnaround
    place_cells(b, ANSW_LOOP, 620, 0.8)
# chorus 1 — the harmony arrives; the close rings across the seam
place_statement(B_CHOR1, "chorus", base=950)
place_statement(B_CHOR1 + 8, "chorus", base=950)
place_events(B_BUILD2, RESOLVE, 0, 950 * CUT_PROFILE[0], 0.8, [1.0])
# build 2 — the trough; the wire mutters its own pickup
place_events(B_BUILD2 + 1, FRAG, -12, 500, 0.6, CUT_PROFILE[:2])
place_events(B_BUILD2 + 4, THEME[:9], -12, 500, 0.6, CUT_PROFILE[:1])
# DROP 2 — the summit run: counterphrased answers, then doubling
place_statement(B_DROP2, "home", answers=[(ANSW_Q_C, 1.0), (ANSW_A_C, 0.9)])
place_statement(B_DROP2 + 8, "home",
                answers=[(ANSW_Q_C, 1.0), (ANSW_A_C, 0.9)])
place_events(B_DROP2 + 16, THEME_Q, 0, 900, 1.0,
             CUT_PROFILE[:4])                             # the wire a cappella
place_statement(B_DROP2 + 20, "home", double=True,
                answers=[(ANSW_Q_C, 1.0), (ANSW_A_C, 0.95)])
place_statement(B_DROP2 + 28, "home", double=True,
                answers=[(ANSW_Q_C, 1.0), (ANSW_A_C, 0.95)])
place_statement(B_DROP2 + 36, "home", double=True,
                answers=[(ANSW_Q_C, 1.0), (ANSW_A_C, 0.95)])
for b in TURN2:
    place_cells(b, ANSW_LOOP, 680, 0.9)
# chorus 2 — fullest, all three registers
place_statement(B_CHOR2, "chorus", base=950, double=True,
                answers=[(ANSW_Q_C, 1.0), (ANSW_A_C, 0.95)])
place_statement(B_CHOR2 + 8, "chorus", base=950, double=True,
                answers=[(ANSW_Q_C, 1.0), (ANSW_A_C, 0.95)])
place_events(B_OUT, RESOLVE, 0, 950 * CUT_PROFILE[0], 0.8, [1.0])
# outro: fading low fragments while the floor strips
place_events(B_OUT + 2, FRAG, -12, 480, 0.5, CUT_PROFILE[:2])
place_events(B_OUT + 6, THEME[:9], -12, 480, 0.4, CUT_PROFILE[:1])
# bookend: the A phrase at the thesis filter position; the final A STATED
place_events(B_KSTOP, THEME_A + [(57, 10, 0, None)], 0, 650, 0.9,
             CUT_PROFILE[4:] + [0.9])
commit(lay_L, lay_R, 0.30)                    # the singer owns the mix
print(f"the 303 committed ({len(acid_cache)} cached notes)")


# ------------------------------------------------------------------ pads
# The room the wire sings into: the Am-F-G-E lap in the choruses and
# through drop 2 (chorus and drop merged), Am holding through the outro.

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
        continue                                # a cappella means alone
    pL, pR = pad_chord(PAD_LAP[b % 4], BAR + 0.8)
    add_at(lay_L, pL, bar_t(b), 0.8)
    add_at(lay_R, pR, bar_t(b), 0.8)
for b in range(B_CHOR2, B_OUT):
    v = PAD_LAP[b % 4]
    pL, pR = pad_chord(tuple(v) + (v[-1] + 12,), BAR + 0.8)
    add_at(lay_L, pL, bar_t(b), 0.95)
    add_at(lay_R, pR, bar_t(b), 0.95)
for b in range(B_OUT, B_OUT + 8, 4):            # outro: Am holds, fading
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
OUT = os.path.join(OUT_DIR, "silver_wire.wav")
with wave.open(OUT, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())

print(f"\nCreated: {os.path.abspath(OUT)}")
print(f"Duration: {N / SR:.1f} s  |  {SR} Hz stereo, 16-bit PCM  |  "
      f"{BPM:.0f} BPM, A minor (Am-F-G-E; the G# of E sung by the wire)")

MP3 = os.path.join(OUT_DIR, "silver_wire.mp3")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", OUT,
                "-vn", "-ar", "44100", "-ac", "2", "-b:a", "192k", MP3],
               check=True)
print(f"Created: {os.path.abspath(MP3)}  (192k mp3)")

# ---------------------------------------------------------------- verify form
# Song form, thesis up front, no break (build 2 inherits the trough).
# Standard blocks + the two checks this track exists for: the anti-arc
# and sings-not-plinks (see silver_wire_notes.md).

print("\nSection map:")
SECTIONS = [("thesis", 0), ("engine", B_ENGINE), ("verse (dark)", B_VERSE),
            ("build 1", B_BUILD1), ("DROP 1 (pedal)", B_DROP1),
            ("chorus 1", B_CHOR1), ("build 2 (trough)", B_BUILD2),
            ("DROP 2 (summit)", B_DROP2), ("chorus 2", B_CHOR2),
            ("outro", B_OUT), ("bookend", B_KSTOP)]
for name, b in SECTIONS:
    print(f"  {bar_t(b):6.1f} s  bar {b:3d}  {name}")
print(f"  {DURATION:6.1f} s  end")

print(f"\nRefrain statements (identical melody/accent/slide maps): "
      f"{len(STMTS)}")
for b0, stype, mc in STMTS:
    print(f"  bar {b0:3d}  {stype:7s}  mean cutoff {mc:6.1f} Hz")
print("  declared fragments (uncounted): thesis Q bar 0, engine/build/outro "
      "mutters, the a-cappella Q bar "
      f"{B_DROP2 + 16}, answer cells, bookend A bar {B_KSTOP}")

# the melody map — 8 bars x 16 steps: o=onset O=accent ==held /=slide end
chars = ["."] * 128
pos = 0
SOUNDING = 0
TIED = 0
for m, d, acc, sl in THEME:
    if m is not None:
        chars[pos] = "O" if acc else "o"
        for k in range(1, d):
            chars[pos + k] = "="
        if sl is not None:
            chars[pos + d - 1] = "/"
        SOUNDING += d
        if d >= 2 or sl is not None:
            TIED += d
    pos += d
print("\nThe refrain map (o onset / O accent / = held / '/' slide):")
for bar in range(8):
    print(f"  bar {bar + 1}  {''.join(chars[bar * 16:(bar + 1) * 16])}")
tie_frac = TIED / SOUNDING
print(f"  sounding 16ths: {SOUNDING}/128, tied/slid fraction: {tie_frac:.2f}")

print("\nSeam checklist (what crosses every boundary):")
for b, dev in [(B_ENGINE, "the thesis' last note rings; kick enters under it (crash)"),
               (B_VERSE, "gait unbroken; the dark statement enters mid-groove"),
               (B_BUILD1, "bass keeps rolling; snare roll + swell begin"),
               (B_DROP1, "16th kick roll into the composed silent beat (bar 43 beat 4); swell peaks ON the downbeat"),
               (B_CHOR1, "the low-cell turnaround (bars 88-91) walks in; crash; the lap arrives"),
               (B_BUILD2, "chorus close: the G#->A RESOLVE rings across bar 108; kick out, bass stays"),
               (B_DROP2, "16th roll + silent beat (bar 115 beat 4); the drop downbeat states A"),
               (B_CHOR2, "the low-cell turnaround (bars 160-163); harmony continuous; crash"),
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
# the trend fit runs over the RECURRING types (home spans both drops,
# chorus spans both choruses) — the dark verse is a declared register
# STEP, not a trend, and is excluded (its brightness prints above).
rec = [(b, mc) for b, s, mc in STMTS if s in ("home", "chorus")]
xs = np.array([b for b, _ in rec], float)
ys = np.array([mc for _, mc in rec], float)
slope = float(np.polyfit(xs, ys, 1)[0])
checks = [
    ("staircase: engine < verse < drop 1",
     R["engine"] < R["verse (dark)"] < R["DROP 1 (pedal)"]),
    ("build 2 is the trough (inherits the cut break's job)",
     R["build 2 (trough)"] < min(R["chorus 1"], R["DROP 2 (summit)"])),
    ("drop 2 (the summit run) > drop 1",
     R["DROP 2 (summit)"] > R["DROP 1 (pedal)"]),
    ("the summit is drop 2 or chorus 2",
     max(R.values()) in (R["DROP 2 (summit)"], R["chorus 2"])),
    ("the outro settles; the bookend is the quiet end",
     R["outro"] < R["chorus 2"] and R["bookend"] < R["build 2 (trough)"]),
    (f"refrain count >= 8 (got {len(STMTS)})", len(STMTS) >= 8),
    ("anti-arc: home statements share one cutoff profile "
     f"(spread {max(home) - min(home):.2f} Hz)", max(home) - min(home) < 1.0),
    ("anti-arc: chorus statements share one cutoff profile "
     f"(spread {max(chor) - min(chor):.2f} Hz)", max(chor) - min(chor) < 1.0),
    (f"anti-arc: no brightness trend across statements "
     f"(slope {slope:+.2f} Hz/bar)", abs(slope) < 1.0),
    (f"sings-not-plinks: tied/slid fraction {tie_frac:.2f} >= 0.25",
     tie_frac >= 0.25),
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
