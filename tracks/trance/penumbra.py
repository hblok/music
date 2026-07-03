#!/usr/bin/env python3
"""
penumbra.py — "Penumbra" (~6:05, 140 BPM, C natural minor). The
single-wave form — design notes: penumbra_notes.md. Blueprint:
../../inspiration/Symmetry_Brainchild.md (Brainchild — Symmetry, C-Mix,
1994 Belgian progressive trance). Dark-euphoric, nocturnal.

THE CONCEPT — the half-shadow at the edge of a light. The two
non-negotiables from the blueprint ARE the track:
  1. The 16th-note GATED LEAD: the melody flickers light/dark sixteen
     times a bar (straight 16ths, ~58% duty, raised-cosine edges).
  2. STATIC MODAL HARMONY: one 8-bar cycle Cm-Cm-Bb-Bb-Ab-Ab-Cm-Cm
     (i-bVII-bVI oscillation) for the whole track; the bass drones the
     C pedal, the pads carry the light.
The whole track is ONE slow opening of the filter (the printable arc);
the payoff is the unfiltering of a melody heard in shadow from bar 0.
The breakdown is the one moment the melody sings UNGATED, free; the
outro strips the layers in exact reverse order of their entry and the
filter lands where it started — the symmetry.

  0:00  intro     Kick + rolling bass + the gated motif, filter ~closed.
  0:14  groove I  + 16th hats, offbeat open hat.        (arc stage 1)
  0:41  groove II + claps 2&4, sparse dark stabs.       (arc stage 2)
  1:09  theme     The refrain reads as a MELODY at last; counted from here.
  1:36  pads      + the dark Juno pad oscillation — harmony arrives.
  2:03  answer    The bell TEASE: one answered hang per statement (x2).
  2:31  lift      Ride in, roll + swell crest, crash ->
  2:45  breakdown Kick+bass out; pads bloom; the refrain UNGATED, once,
                  drowned in the hall; roll + swell -> one silent beat,
                  a gated pickup hanging in it —
  3:19  PEAK I    Filter FULLY OPEN (global max), gate dancing, bell
                  answering every hang — the fusion. (softened slam)
  3:47  dip       Claps/ride out, the arc eases a stage.
  3:53  PEAK II   The fullest wave — loudest section.
  4:27  ride-out  Mirror strip: ride, bell (a farewell answer), pads,
  4:55   I / II   stabs, claps — reverse of the add order.
  5:22  outro     Kick/bass/hats + the motif back at the intro's filter
                  (the bookend is the filter position AND the tune);
                  the kick stops at 5:42.
  5:50  tail      The last gated throb; a Cm pad chord and one bell C6
                  ring out.

Sanctioned era vocabulary: snare rolls + dark bandlimited swells.
Banned by construction: acid resonance, sidechain pump, white-noise
risers, reverse cymbals (nachtkind's), tom fills (ungeschrieben's),
supersaws, borrowed tones (C-natural-minor diatonic, printed/checked).
Everything synthesized (numpy + scipy).
Output: /workspace/music/penumbra.wav + penumbra.mp3 (192k).
"""

import os
import subprocess
import wave
import numpy as np
from scipy import signal

SR = 44100
BPM = 140.0
BEAT = 60.0 / BPM
BAR = BEAT * 4
STEP = BEAT / 4          # 4725 samples exactly at 44100 — the gate grid
GRID0 = 0.5

rng = np.random.default_rng(140)   # the BPM, per lost's precedent

# ----------------------------------------------------- section boundaries (bars)
B_GRV1 = 8       # + hats
B_GRV2 = 24      # + claps, stabs
B_THEME = 40     # the refrain reads as a melody; statements counted from here
B_PADS = 56      # + the pad oscillation
B_ANSW = 72      # + the bell tease
B_LIFT = 88      # + ride; roll + swell crest
B_BRK = 96       # kick+bass out; the UNGATED statement at bar 100
B_PK1 = 116      # filter fully open; the fusion (silent beat = bar 115 beat 3)
B_DIP = 132      # mid-drop dip
B_PK2 = 136      # the fullest wave
B_RO1 = 156      # mirror strip: ride out, bell farewell
B_RO2 = 172      # pads out, stabs out, claps out
B_OUT = 188      # kick/bass/hats + the bookend statement (bar 196)
B_KSTOP = 200    # the kick stops
B_TAIL = 204     # the last throb + rings
B_END = 210

DURATION = GRID0 + B_END * BAR + 6.0
N = int(SR * DURATION)
t = np.arange(N) / SR


def bar_t(b, beat=0.0):
    return GRID0 + b * BAR + beat * BEAT


SECS = [("intro", 0), ("grv1", B_GRV1), ("grv2", B_GRV2), ("theme", B_THEME),
        ("pads", B_PADS), ("answ", B_ANSW), ("lift", B_LIFT), ("brk", B_BRK),
        ("pk1", B_PK1), ("dip", B_DIP), ("pk2", B_PK2), ("ro1", B_RO1),
        ("ro2", B_RO2), ("out", B_OUT), ("tail", B_TAIL)]


def section_of(b):
    for name, b0 in reversed(SECS):
        if b >= b0:
            return name
    return "intro"


# ------------------------------------------------------- the filter arc
# The development engine (ungeschrieben's mechanism, applied to the LEAD):
# one slow opening, frozen through the breakdown core, cresting into the
# drop, global max only inside the peaks, symmetric descent to the intro
# value. Printed at every boundary and checked.
CUT_BARS = [0,     8,   24,  40,  56,   72,   88,   96,   112,  116,
            131,  132,  135, 136, 156,  172,  188,  204,  210]
CUT_HZ = [350,  380,  550, 800, 1150, 1600, 2100, 2400, 2400, 3600,
          3600, 3000, 3000, 3600, 3600, 1600, 700,  350,  350]


def cutoff_at(b):
    return float(np.interp(b, CUT_BARS, CUT_HZ))


ARC_MAX = max(CUT_HZ)

# ---------------------------------------------------------------- helpers


def midi_to_hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def fade(x, fade_in=0.4, fade_out=8.0):
    ni, no = int(fade_in * SR), int(fade_out * SR)
    x[:ni] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(ni) / ni)
    x[-no:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(no) / no)
    return x


def make_reverb_ir(seconds, decay, seed):
    r = np.random.default_rng(seed)
    n = int(seconds * SR)
    ir = r.standard_normal(n) * np.exp(-np.arange(n) / SR / decay)
    sos = signal.butter(2, 4200, "low", fs=SR, output="sos")
    ir = signal.sosfilt(sos, ir)
    return ir / np.sqrt(np.sum(ir ** 2))


IR_L = make_reverb_ir(5.0, 2.6, 7)
IR_R = make_reverb_ir(5.0, 2.6, 11)


def reverb(x, ir, wet=0.5):
    tail = signal.oaconvolve(x, ir)[: len(x)]
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


def glide_curve(notes, n, tau=0.05):
    f_target = np.zeros(n)
    edge = 0.0
    for m, d in notes:
        a, b = int(edge * SR), min(n, int((edge + d) * SR))
        f_target[a:b] = midi_to_hz(m)
        edge += d
    i_end = min(n - 1, int(edge * SR))
    f_target[i_end:] = midi_to_hz(notes[-1][0])
    alpha = 1.0 - np.exp(-1.0 / (tau * SR))
    return signal.lfilter([alpha], [1.0, -(1.0 - alpha)],
                          f_target, zi=[f_target[0] * (1 - alpha)])[0]


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


# ============================================================= harmony
# STATIC MODAL — non-negotiable #2. ONE 8-bar cycle for the whole track:
# Cm Cm Bb Bb Ab Ab Cm Cm (i-bVII-bVI oscillation, 2 bars per chord, no
# functional progressions, no chord stabs carrying it — the pads imply
# it). The bass never leaves the C pedal except two-note bVI->bVII walks
# home. Under the refrain: the circling cells get Cm then Bb (the same
# tune in two lights), the hang floats over Ab (Bb5 = its add9), home
# lands on i. chord = (bass_root_midi, mid-register voicing)

Cm = (36, (48, 55, 60, 63))     # C2 | C3 G3 C4 Eb4
Bb = (34, (46, 53, 58, 62))     # Bb1 | Bb2 F3 Bb3 D4
Ab = (32, (44, 51, 56, 60))     # Ab1 | Ab2 Eb3 Ab3 C4

CYCLE = [Cm, Cm, Bb, Bb, Ab, Ab, Cm, Cm]

CHORD_AT = [Cm] * B_END


def fill(b0, b1, seq):
    for b in range(b0, b1):
        CHORD_AT[b] = seq[(b - b0) % len(seq)]


fill(0, B_BRK, CYCLE)                 # statements at multiples of 8 stay aligned
fill(B_BRK, 100, [Cm])                # breakdown entry: the drone alone
fill(100, B_PK1, CYCLE)               # aligned to the UNGATED statement at 100
fill(B_PK1, B_DIP, CYCLE)             # peak I (two aligned statements)
fill(B_DIP, B_PK2, [Cm, Cm, Bb, Bb])  # the dip rocks i <-> bVII
fill(B_PK2, B_RO1, CYCLE)             # peak II
fill(B_RO1, B_END, CYCLE)             # ride-outs / outro / tail (tail = Cm)

# ============================================================= the melody
# THE REFRAIN — identical in every statement; the filter position is the
# only thing that develops. 8 bars = a circling 2-bar cell x4 on the
# blueprint's five degrees (1 b3 4 5 b7 — hypnotic-modal, it circles
# rather than resolves). Cells 1-2 identical; cell 3 (Q) lifts and hangs
# on the b7; cell 4 (A) answers with the SAME rhythm — its first bar is
# the exact retrograde of the question's (the Symmetry mimicry, checked)
# — and falls home to C.
REFRAIN = [(67, 1.5), (70, 0.5), (72, 2),    # Cm: G4 Bb4 C5   — the circle
           (75, 1.5), (72, 0.5), (70, 2),    # Cm: Eb5 C5 Bb4  — turns back
           (67, 1.5), (70, 0.5), (72, 2),    # Bb: the same circle, new light
           (75, 1.5), (72, 0.5), (70, 2),    # Bb
           (72, 1.5), (75, 0.5), (77, 2),    # Ab: C5 Eb5 F5   — Q rises
           (79, 1.5), (77, 0.5), (82, 2),    # Ab: G5 F5 Bb5   — THE HANG (b7)
           (77, 1.5), (75, 0.5), (72, 2),    # Cm: F5 Eb5 C5   — A: Q mirrored
           (70, 1.5), (67, 0.5), (72, 2)]    # Cm: Bb4 G4 C5   — HOME
BAR_NOTES = [tuple(REFRAIN[3 * i:3 * i + 3]) for i in range(8)]
HANG_BAR, HANG_MIDI = 5, 82          # bar offset + pitch of the hang (b7)

STATEMENTS = []          # (bar, label, gated, counted)
BELL_EVENTS = []         # (bar_float, kind)  kind in tease/peak/farewell/tail

# ============================================================= the layers'
# add/strip discipline — THE SYMMETRY. Placement code obeys these bounds;
# the outro strips in exact reverse order of the entries (checked).
LAYER_SPAN = {"hats": (B_GRV1, 196), "claps": (B_GRV2, 184),
              "stabs": (B_GRV2, 180), "pads": (B_PADS, B_RO2),
              "bell": (B_ANSW, 163), "ride": (B_LIFT, B_RO1)}
ADD_ORDER = ["hats", "claps", "stabs", "pads", "bell", "ride"]


# ============================================================= drum kit (dry)

def make_kick():
    n = int(0.42 * SR)
    td = np.arange(n) / SR
    f_curve = 44.0 + 108.0 * np.exp(-td * 50.0)      # punchy, slightly boomy 909
    body = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    sub = np.sin(2 * np.pi * (38 + 16 * np.exp(-td * 3)) * td) * np.exp(-td * 3.2)
    sos_c = signal.butter(2, [1800, 9000], "bandpass", fs=SR, output="sos")
    click = signal.sosfilt(sos_c, rng.standard_normal(n)) * np.exp(-td * 500)
    click /= np.max(np.abs(click)) + 1e-12
    env = (1 - np.exp(-td / 0.0008)) * np.exp(-td * 8.0)
    x = body * env + 0.5 * sub + 0.42 * click * (1 - np.exp(-td / 0.0008))
    return x / (np.max(np.abs(x)) + 1e-12)


def make_hat(open_=False):
    n = int((0.13 if open_ else 0.04) * SR)
    td = np.arange(n) / SR
    sos_h = signal.butter(4, 7500, "high", fs=SR, output="sos")
    x = signal.sosfilt(sos_h, rng.standard_normal(n)) * np.exp(-td * (26 if open_ else 120))
    return x / (np.max(np.abs(x)) + 1e-12)


def make_clap():
    n = int(0.32 * SR)
    td = np.arange(n) / SR
    sos = signal.butter(2, [900, 5200], "bandpass", fs=SR, output="sos")
    x = np.zeros(n)
    for i, dmp in [(0, 130.0), (1, 130.0), (2, 130.0), (3, 24.0)]:
        i0 = int(i * 0.011 * SR)
        x[i0:] += signal.sosfilt(sos, rng.standard_normal(n - i0)) * np.exp(-td[: n - i0] * dmp)
    return x / (np.max(np.abs(x)) + 1e-12)


def make_ride():
    n = int(0.4 * SR)
    td = np.arange(n) / SR
    nz = rng.standard_normal(n)
    a = signal.butter(2, [4000, 7000], "bandpass", fs=SR, output="sos")
    b = signal.butter(2, [8000, 12000], "bandpass", fs=SR, output="sos")
    x = signal.sosfilt(a, nz) * np.exp(-td * 9) + 0.7 * signal.sosfilt(b, nz) * np.exp(-td * 6)
    x += 0.18 * np.sin(2 * np.pi * 5400 * td) * np.exp(-td * 8)
    return x / (np.max(np.abs(x)) + 1e-12)


def make_crash():
    n = int(2.2 * SR)
    td = np.arange(n) / SR
    x = signal.sosfilt(signal.butter(2, 5000, "high", fs=SR, output="sos"),
                       rng.standard_normal(n)) * np.exp(-td * 2.0)
    x *= 1 - np.exp(-td / 0.002)
    return x / (np.max(np.abs(x)) + 1e-12)


def make_snare():
    n = int(0.22 * SR)
    td = np.arange(n) / SR
    tone = (np.sin(2 * np.pi * 185 * td) + np.sin(2 * np.pi * 330 * td)) * np.exp(-td * 26)
    noise = signal.sosfilt(signal.butter(2, [1500, 9000], "bandpass", fs=SR, output="sos"),
                           rng.standard_normal(n)) * np.exp(-td * 30)
    x = 0.6 * tone + noise
    x *= 1 - np.exp(-td / 0.0008)
    return x / (np.max(np.abs(x)) + 1e-12)


KICK = make_kick()
CHAT = make_hat()
OHAT = make_hat(True)
CLAP = make_clap()
RIDE = make_ride()
CRASH = make_crash()
SNARE = make_snare()
# no reverse cymbal (nachtkind's), no toms (ungeschrieben's) — identity

T_SILENCE = bar_t(B_PK1 - 1, 3)      # the one composed silence: bar 115 beat 3

KICK_G = {"intro": 0.62, "grv1": 0.74, "grv2": 0.84, "theme": 0.9,
          "pads": 0.95, "answ": 0.97, "lift": 1.0, "pk1": 1.0,
          "dip": 0.92, "pk2": 1.0, "ro1": 0.95, "ro2": 0.9, "out": 0.78}

clear()
for b in range(B_END):
    s = section_of(b)
    if s not in KICK_G or (s == "out" and b >= B_KSTOP):
        continue
    for beat in range(4):
        add_at(lay_L, KICK, bar_t(b, beat), KICK_G[s])
        add_at(lay_R, KICK, bar_t(b, beat), KICK_G[s])
commit(lay_L, lay_R, 0.36)
print("kick committed")

clear()
CH = [0.5, 0.28, 0.0, 0.34]          # per-16th gain cell (slot 2 = open hat)
HAT_G = {"grv1": 0.75, "grv2": 0.85, "theme": 0.9, "pads": 0.9,
         "answ": 0.95, "lift": 1.0, "pk1": 1.0, "dip": 0.6, "pk2": 1.0,
         "ro1": 0.9, "ro2": 0.85, "out": 0.6}
for b in range(LAYER_SPAN["hats"][0], LAYER_SPAN["hats"][1]):
    s = section_of(b)
    if s not in HAT_G:
        continue
    g = HAT_G[s]
    for beat in range(4):
        for sx in range(4):
            if CH[sx] <= 0:
                continue
            add_at(lay_L, CHAT, bar_t(b, beat + sx * 0.25), g * CH[sx] * 0.9)
            add_at(lay_R, CHAT, bar_t(b, beat + sx * 0.25), g * CH[sx])
        add_at(lay_L, OHAT, bar_t(b, beat + 0.5), g * 0.9)
        add_at(lay_R, OHAT, bar_t(b, beat + 0.5), g * 0.8)
commit(lay_L, lay_R, 0.075)
print("hats committed")

clear()
CLAP_G = {"grv2": 0.7, "theme": 0.8, "pads": 0.85, "answ": 0.9,
          "lift": 1.0, "pk1": 1.0, "pk2": 1.0, "ro1": 0.85, "ro2": 0.7}
for b in range(LAYER_SPAN["claps"][0], LAYER_SPAN["claps"][1]):
    s = section_of(b)
    if s not in CLAP_G:
        continue
    for beat in (1, 3):
        p = 0.42 if beat == 1 else 0.58
        place_pan(lay_L, lay_R, CLAP, bar_t(b, beat), CLAP_G[s], p)
commit(lay_L, lay_R, 0.10)
print("claps committed")

clear()
RIDE_G = {"lift": 0.8, "pk1": 1.0, "pk2": 1.0}
for b in range(LAYER_SPAN["ride"][0], LAYER_SPAN["ride"][1]):
    s = section_of(b)
    if s not in RIDE_G:
        continue
    for e in range(8):
        g = RIDE_G[s] * (0.7 if e % 2 == 0 else 0.45)
        place_pan(lay_L, lay_R, RIDE, bar_t(b, e * 0.5), g, 0.5)
commit(lay_L, lay_R, 0.045)
print("ride committed")

clear()
for b, g in [(B_THEME, 0.55), (B_PADS, 0.5), (B_ANSW, 0.45), (B_BRK, 0.8),
             (B_PK1, 0.85),                       # the slam, softened (farlight v2)
             (B_PK2, 0.9), (B_RO1, 0.5), (B_RO2, 0.4), (B_OUT, 0.4)]:
    place_pan(lay_L, lay_R, CRASH, bar_t(b), g, 0.5)
commit(lay_L, lay_R, 0.05)
print("crashes committed")

clear()


def roll(b0, b1, base, t_end=None):
    nbars = b1 - b0
    for b in range(b0, b1):
        u = (b - b0) / nbars
        div = 4 if u < 0.5 else (8 if u < 0.85 else 16)
        for s in range(div):
            tt = bar_t(b, s * 4.0 / div)
            if t_end is not None and tt >= t_end:
                continue                         # honors the silent beat
            g = base * (0.4 + 0.6 * u) * (0.7 + 0.3 * (s % 2))
            place_pan(lay_L, lay_R, SNARE, tt, g, 0.5)


roll(B_LIFT + 6, B_BRK, 0.5)                     # crest into the breakdown
roll(B_PK1 - 4, B_PK1, 0.65, t_end=T_SILENCE)    # ends dead at the silence
roll(B_PK2 - 2, B_PK2, 0.5)
commit(lay_L, lay_R, 0.08)
print("rolls committed")


# ============================================================= bass (warmed)
# The engine — rolling offbeat 16ths from bar 0, pinned to the C pedal
# (non-negotiable #2: the harmony oscillates ABOVE it). lost_v4 school:
# rolled-off harmonics, peak Q 1.2 / blend 0.3 (no acid), sine sub, soft
# tanh. The only departures from C: two-note Ab->Bb walks home at each
# cycle's bVI -> i seam. Kick owns beat zero — no sidechain pump.

bass_cache = {}


def bass_note(midi, cutoff, drive=0.9, dur=STEP * 0.92):
    key = (midi, int(cutoff // 60), round(drive, 1))
    if key in bass_cache:
        return bass_cache[key]
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    for k in range(1, min(22, int(3500 / f)) + 1):
        x += np.sin(2 * np.pi * k * f * td) / k ** 1.3
    y = signal.sosfilt(signal.butter(2, cutoff, "low", fs=SR, output="sos"), x)
    bpk, apk = signal.iirpeak(cutoff, Q=1.2, fs=SR)
    y = y + 0.3 * signal.lfilter(bpk, apk, y)
    y += 0.5 * np.sin(2 * np.pi * (f / 2) * td)
    y = np.tanh(drive * y)
    y *= (1 - np.exp(-td / 0.004)) * np.clip((dur - td) / 0.02, 0, 1)
    bass_cache[key] = y / (np.max(np.abs(y)) + 1e-12)
    return bass_cache[key]


BASS_PAT_A = [(1, 0, 0.85), (2, 0, 0.7), (3, 0, 0.95)]     # intro: pure pedal
BASS_PAT_B = [(1, 0, 0.85), (2, 12, 0.75), (3, 0, 0.95)]   # + octave jumps
BASS_WALK = [(1, -4, 0.85), (2, -4, 0.7), (3, -2, 0.95)]   # Ab Ab Bb -> home
BASS_CUT = {"intro": 380, "grv1": 420, "grv2": 460, "theme": 500,
            "pads": 520, "answ": 540, "lift": 560, "pk1": 600,
            "dip": 520, "pk2": 620, "ro1": 560, "ro2": 500, "out": 420}
BASS_G = {"intro": 0.72, "grv1": 0.82, "grv2": 0.9, "theme": 0.95}
clear()
for b in range(B_END):
    s = section_of(b)
    if s not in BASS_CUT or (s == "out" and b >= B_KSTOP + 2):
        continue
    cut = BASS_CUT[s]
    sg = BASS_G.get(s, 1.0)
    walk_bar = (CHORD_AT[b] is Ab and b + 1 < B_END and CHORD_AT[b + 1] is Cm)
    pat = BASS_PAT_A if s in ("intro", "grv1") else BASS_PAT_B
    for beat in range(4):
        this = BASS_WALK if (walk_bar and beat == 3) else pat
        for sx, off, gg in this:
            x = bass_note(36 + off, cut)
            tt = bar_t(b, beat + sx * 0.25)
            add_at(lay_L, x, tt, gg * sg)
            add_at(lay_R, x, tt, gg * sg)
commit(lay_L, lay_R, 0.30)
print(f"bass committed ({len(bass_cache)} cached)")

# the sustained sub — peaks only (the breakdown trough needs the
# contrast). farlight v2's speaker lesson baked in: 0.25 s attacks and a
# per-bar entry bloom 0.55 -> 1.0, so the drop never lurches the woofer.
clear()
for b0, b1, base in [(B_PK1, B_DIP, 0.7), (B_PK2, B_RO1, 0.85)]:
    for i, b in enumerate(range(b0, b1)):
        f = midi_to_hz(24)                       # C1 — the pedal, deepest
        seg_n = int(BAR * SR)
        td = np.arange(seg_n) / SR
        sub = np.sin(2 * np.pi * f * td) * np.minimum(np.clip(td / 0.25, 0, 1),
                                                      np.clip((BAR - td) / 0.1, 0, 1))
        g = base * min(1.0, 0.55 + 0.15 * i)     # the entry bloom
        add_at(lay_L, sub, bar_t(b), g)
        add_at(lay_R, sub, bar_t(b), g)
commit(lay_L, lay_R, 0.10)
print("sustained sub committed (bloomed entries)")


# ============================================================= dark stabs
# The blueprint's "subtle stab accents" — nachtkind's dark gated chord
# stab re-voiced: the cycle chord as band-limited saws, lowpassed hard,
# gated short, on the offbeat, panned alternately. Sparse: every other
# bar. Accent, never harmony-carrier (the pads own the oscillation).

stab_cache = {}


def stab(voicing):
    if voicing in stab_cache:
        return stab_cache[voicing]
    dur = 0.15
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    for m in voicing[1:]:
        f = midi_to_hz(m)
        for k in range(1, min(14, int(4000 / f)) + 1):
            x += np.sin(2 * np.pi * k * f * td + rng.uniform(0, 6)) / k ** 1.15
    x = signal.sosfilt(signal.butter(2, 900, "low", fs=SR, output="sos"), x)
    x = np.tanh(0.9 * x)
    x *= (1 - np.exp(-td / 0.002)) * np.clip((dur - td) / 0.05, 0, 1)
    stab_cache[voicing] = x / (np.max(np.abs(x)) + 1e-12)
    return stab_cache[voicing]


STAB_G = {"grv2": 0.6, "theme": 0.65, "pads": 0.6, "answ": 0.6,
          "lift": 0.7, "pk1": 0.7, "pk2": 0.7, "ro1": 0.6, "ro2": 0.5}
clear()
for b in range(LAYER_SPAN["stabs"][0], LAYER_SPAN["stabs"][1]):
    s = section_of(b)
    if s not in STAB_G or b % 2 == 0:
        continue
    pan = 0.35 if (b // 2) % 2 else 0.65
    place_pan(lay_L, lay_R, stab(CHORD_AT[b][1]), bar_t(b, 2.5), STAB_G[s], pan)
lay_L = reverb(lay_L, IR_L, 0.3)
lay_R = reverb(lay_R, IR_R, 0.3)
commit(lay_L, lay_R, 0.06)
print("stabs committed")


# ============================================================= THE GATED LEAD
# Non-negotiable #1 and the centerpiece. A bright hollow square-saw
# hybrid (odd harmonics weighted — the JP/Korg-era character) with the
# warmth guardrails (1/k^1.3 roll-off, sine body, tanh 0.9). The gate is
# BAKED into the render (tech_noir's lesson): straight 16ths, 58% duty,
# raised-cosine 4 ms edges. Each BAR is rendered at the cutoff the arc
# gives it (cached in 50 Hz buckets) — the gate closes to zero between
# steps, so per-bar filtering leaves no seam. The refrain's bars are
# melodically self-contained, so the whole track's lead is 8 cached bars
# swept through the arc.

STEP_N = int(round(STEP * SR))                   # 4725 exactly
GATE_CELL = np.zeros(STEP_N)
_open = int(0.58 * STEP_N)
_edge = int(0.004 * SR)
GATE_CELL[:_edge] = 0.5 - 0.5 * np.cos(np.pi * np.arange(_edge) / _edge)
GATE_CELL[_edge:_open - _edge] = 1.0
GATE_CELL[_open - _edge:_open] = 0.5 + 0.5 * np.cos(np.pi * np.arange(_edge) / _edge)

lead_cache = {}


def lead_bar(bar_idx, cutoff, gated=True):
    key = (bar_idx, int(cutoff // 50), gated)
    if key in lead_cache:
        return lead_cache[key]
    notes = BAR_NOTES[bar_idx]
    n = int(BAR * SR) + int(0.3 * SR)
    td = np.arange(n) / SR
    f = glide_curve([(m, d * BEAT) for m, d in notes], n, tau=0.03)
    vibe = 1.0 + 0.0025 * np.sin(2 * np.pi * 5.3 * td)
    K = int(np.clip(8800 / np.max(f), 4, 24))
    L = np.zeros(n)
    R = np.zeros(n)
    for j, det in enumerate((0.997, 1.0, 1.003)):
        ph = 2 * np.pi * np.cumsum(f * det * vibe) / SR
        v = np.zeros(n)
        for k in range(1, K + 1):
            w = (1.0 if k % 2 else 0.45) / k ** 1.3   # the square-saw blend
            v += w * np.sin(k * ph)
        pan = (j / 2 - 0.5)
        L += v * (0.6 + 0.4 * (0.5 - pan))
        R += v * (0.6 + 0.4 * (0.5 + pan))
    body = 0.3 * np.sin(2 * np.pi * np.cumsum(f * vibe) / SR)
    L += body
    R += body
    env = (1 - np.exp(-td / 0.006)) * np.clip((BAR + 0.25 - td) / 0.25, 0, 1)
    L = np.tanh(0.9 * L * env)
    R = np.tanh(0.9 * R * env)
    if gated:
        G = np.tile(GATE_CELL, n // STEP_N + 1)[:n]
        L *= G
        R *= G
    sos = signal.butter(2, cutoff, "low", fs=SR, output="sos")
    L = signal.sosfilt(sos, L)
    R = signal.sosfilt(sos, R)
    peak = max(np.max(np.abs(L)), np.max(np.abs(R)), 1e-12)
    lead_cache[key] = (L / peak, R / peak)
    return lead_cache[key]


def place_statement(b0, gain, label=None, counted=False, nbars=8):
    for bi in range(nbars):
        L, R = lead_bar(bi, cutoff_at(b0 + bi))
        add_at(lay_L, L, bar_t(b0 + bi), gain)
        add_at(lay_R, R, bar_t(b0 + bi), gain)
    if label is not None:
        STATEMENTS.append((b0, label, True, counted))


LEAD_G = {"intro": 0.55, "grv1": 0.6, "grv2": 0.65, "theme": 0.75,
          "pads": 0.8, "answ": 0.85, "lift": 0.9, "pk1": 1.0, "dip": 0.8,
          "pk2": 1.0, "ro1": 0.85, "ro2": 0.75, "out": 0.6}

clear()
# the shadow statements: the motif from bar 0, filter ~closed — the
# thesis IS the first one (present in shadow, not withheld)
for b0 in range(0, B_THEME, 8):
    place_statement(b0, LEAD_G[section_of(b0)],
                    "thesis (shadow)" if b0 == 0 else "shadow", counted=False)
# counted from the theme: the melody in the light
for b0 in range(B_THEME, B_BRK, 8):
    place_statement(b0, LEAD_G[section_of(b0)],
                    f"{section_of(b0)} stmt", counted=True)
# the peaks — the fusion statements
for b0 in (B_PK1, B_PK1 + 8, B_PK2, B_PK2 + 8):
    place_statement(b0, 1.0, f"{section_of(b0)} stmt", counted=True)
# the dip: circling cells only (uncounted fragment — the tune breathes)
for bi, b in enumerate(range(B_DIP, B_PK2)):
    L, R = lead_bar(bi % 2, cutoff_at(b))
    add_at(lay_L, L, bar_t(b), LEAD_G["dip"])
    add_at(lay_R, R, bar_t(b), LEAD_G["dip"])
# peak II wind-down: circling cells into the ride-out (uncounted)
for bi, b in enumerate(range(B_PK2 + 16, B_RO1)):
    L, R = lead_bar(bi % 2, cutoff_at(b))
    add_at(lay_L, L, bar_t(b), 0.9)
    add_at(lay_R, R, bar_t(b), 0.9)
# ride-out shadows (descending) and the outro
for b0 in (B_RO1, B_RO1 + 8, B_RO2, B_RO2 + 8, B_OUT):
    place_statement(b0, LEAD_G[section_of(b0)], "shadow (descent)", counted=False)
# THE BOOKEND: the tune at the intro's filter position
place_statement(B_OUT + 8, 0.6, "BOOKEND", counted=True)
# the gated pickup hanging in the composed silence (bar 115 beat 3.5)
Lp, Rp = lead_bar(0, cutoff_at(B_PK1))
add_at(lay_L, Lp[:STEP_N * 2], bar_t(B_PK1 - 1, 3.5), 0.7)
add_at(lay_R, Rp[:STEP_N * 2], bar_t(B_PK1 - 1, 3.5), 0.7)
# the last throb: two circling bars into the tail, fading
for bi, (b, g) in enumerate([(B_TAIL, 0.4), (B_TAIL + 1, 0.28)]):
    L, R = lead_bar(bi, cutoff_at(b))
    add_at(lay_L, L, bar_t(b), g)
    add_at(lay_R, R, bar_t(b), g)

# the era's cascading trail: tempo-synced dotted-8th cross delay
d = int(0.75 * BEAT * SR)
eL = np.zeros(N)
eR = np.zeros(N)
eL[d:] = lay_R[:-d] * 0.22
eR[d:] = lay_L[:-d] * 0.22
lay_L += eL
lay_R += eR
lay_L = reverb(lay_L, IR_L, 0.28)
lay_R = reverb(lay_R, IR_R, 0.28)
commit(lay_L, lay_R, 0.22)
print(f"gated lead committed ({len(lead_cache)} bar renders across the arc)")


# ------------------------------------------------- THE UNGATED STATEMENT
# The one moment the shutter swings wide: in the breakdown the melody
# heard gated for minutes sings FREE, exactly once — legato across the
# barlines, slow bloom, drowned in the hall. The gate snaps back with
# the kick at the peak.

def lead_free(notes):
    total = sum(dd for _, dd in notes) * BEAT
    n = int((total + 2.0) * SR)
    td = np.arange(n) / SR
    f = glide_curve([(m, dd * BEAT) for m, dd in notes], n, tau=0.06)
    vibe = 1.0 + 0.004 * np.sin(2 * np.pi * 5.3 * td) * np.clip(td / 1.5, 0, 1)
    K = int(np.clip(6500 / np.max(f), 4, 18))
    L = np.zeros(n)
    R = np.zeros(n)
    for j, det in enumerate((0.997, 1.0, 1.003)):
        ph = 2 * np.pi * np.cumsum(f * det * vibe) / SR
        v = np.zeros(n)
        for k in range(1, K + 1):
            v += ((1.0 if k % 2 else 0.45) / k ** 1.3) * np.sin(k * ph)
        pan = (j / 2 - 0.5)
        L += v * (0.6 + 0.4 * (0.5 - pan))
        R += v * (0.6 + 0.4 * (0.5 + pan))
    body = 0.3 * np.sin(2 * np.pi * np.cumsum(f * vibe) / SR)
    env = np.minimum(np.clip(td / 0.4, 0, 1), np.clip((total + 1.0 - td) / 1.2, 0, 1))
    sos = signal.butter(2, 2200, "low", fs=SR, output="sos")
    L = signal.sosfilt(sos, np.tanh(0.85 * (L + body)) * env)
    R = signal.sosfilt(sos, np.tanh(0.85 * (R + body)) * env)
    peak = max(np.max(np.abs(L)), np.max(np.abs(R)), 1e-12)
    return L / peak, R / peak


clear()
FREE_BAR = 100
fL, fR = lead_free(REFRAIN)
add_at(lay_L, fL, bar_t(FREE_BAR), 1.0)
add_at(lay_R, fR, bar_t(FREE_BAR), 1.0)
STATEMENTS.append((FREE_BAR, "breakdown — UNGATED, the shutter wide", False, True))
lay_L = reverb(lay_L, IR_L, 0.62)
lay_R = reverb(lay_R, IR_R, 0.62)
commit(lay_L, lay_R, 0.13)
print("the ungated statement committed (breakdown)")


# ============================================================= THE BELL
# farlight's tubular bell, guest-starring as the blueprint's counter-lead
# ("a thinner, brighter bell/pluck-like voice for the answering phrase").
# It answers the hang: the lead suspends on Bb5 (the b7) and the bell
# sings the resolution the lead withheld — Bb5 -> C6, the tonic. Teased
# twice in the answer section, every hang in the peaks, one farewell in
# the ride-out, one last C6 in the tail.

bell_cache = {}


def bell_note(midi, dur):
    key = (midi, round(dur, 2))
    if key in bell_cache:
        return bell_cache[key]
    f = midi_to_hz(midi)
    n = int((dur + 2.5) * SR)
    td = np.arange(n) / SR
    out = np.zeros(n)
    scale = (660.0 / f) ** 0.3          # higher bells ring shorter
    for ratio, g, dec in [(1.0, 1.0, 1.7), (2.0, 0.42, 2.4),
                          (2.76, 0.26, 3.6), (5.40, 0.10, 7.0)]:
        for det in (0.9994, 1.0006):
            out += g * np.sin(2 * np.pi * f * ratio * det * td + rng.uniform(0, 6)) \
                   * np.exp(-td * dec / scale)
    thunk = signal.sosfilt(signal.butter(2, [1200, 4200], "bandpass", fs=SR, output="sos"),
                           rng.standard_normal(n)) * np.exp(-td * 160)
    out = out / (np.max(np.abs(out)) + 1e-12) + 0.10 * thunk / (np.max(np.abs(thunk)) + 1e-12)
    out *= (1 - np.exp(-td / 0.002)) * np.clip((dur + 2.0 - td) / 0.6, 0, 1)
    out = signal.sosfilt(signal.butter(2, 5500, "low", fs=SR, output="sos"), out)
    bell_cache[key] = out / (np.max(np.abs(out)) + 1e-12)
    return bell_cache[key]


def bell_answer(stmt_b0, gain, kind):
    # the answer enters on beat 3 of the hang bar: Bb5 -> C6 (home)
    b = stmt_b0 + HANG_BAR
    tm = bar_t(b, 3)
    for m, dd in [(82, 0.5), (84, 1.5)]:
        pan = np.clip(0.5 + (m - 82) * 0.02, 0.35, 0.65)
        place_pan(lay_L, lay_R, bell_note(m, dd * BEAT), tm, gain, pan)
        tm += dd * BEAT
    BELL_EVENTS.append((b + 0.75, kind))


clear()
bell_answer(B_ANSW, 0.5, "tease")                # the two teases
bell_answer(B_ANSW + 8, 0.55, "tease")
for b0 in (B_PK1, B_PK1 + 8, B_PK2, B_PK2 + 8):  # every hang in the peaks
    bell_answer(b0, 0.85, "peak")
bell_answer(B_RO1, 0.4, "farewell")              # one farewell, then stripped
# the tail ring: a single C6 — home, one last time
place_pan(lay_L, lay_R, bell_note(84, 5.0), bar_t(B_TAIL + 1), 0.5, 0.5)
BELL_EVENTS.append((B_TAIL + 1, "tail"))
lay_L = reverb(lay_L, IR_L, 0.5)
lay_R = reverb(lay_R, IR_R, 0.5)
commit(lay_L, lay_R, 0.18)
print(f"bell committed ({len(bell_cache)} cached)")


# ============================================================= pads
# The Juno/JX dark string-pad — wide, slow ~0.8 s attack, low lowpass,
# long hall. THE harmony carrier: the i-bVII-bVI oscillation, 2 bars per
# chord, drone-oriented (blueprint: the pads imply the chords; no stab
# progression). Blooms big in the breakdown; recedes through ride-out I.

pad_cache = {}


def pad_chord(voicing, dur, attack, lowpass):
    key = (voicing, round(dur, 1), attack, lowpass)
    if key in pad_cache:
        return pad_cache[key]
    n = int(dur * SR)
    td = np.arange(n) / SR
    L = np.zeros(n)
    R = np.zeros(n)
    for m in voicing:
        f = midi_to_hz(m)
        amp = 0.8 + 0.2 * np.sin(2 * np.pi * rng.uniform(0.02, 0.06) * td + rng.uniform(0, 6))
        for dd, gL, gR in [(1 - 0.0014, 1.0, 0.62), (1 + 0.0014, 0.62, 1.0)]:
            ph = 2 * np.pi * f * dd * td + rng.uniform(0, 6)
            v = (np.sin(ph) + 0.3 * np.sin(2 * ph) + 0.1 * np.sin(3 * ph)) * amp
            L += gL * v
            R += gR * v
    env = np.minimum(np.clip(td / attack, 0, 1) ** 1.3, np.clip((dur - td) / 2.0, 0, 1))
    sos = signal.butter(2, lowpass, "low", fs=SR, output="sos")
    L = signal.sosfilt(sos, L * env)
    R = signal.sosfilt(sos, R * env)
    peak = max(np.max(np.abs(L)), np.max(np.abs(R)), 1e-12)
    pad_cache[key] = (L / peak, R / peak)
    return pad_cache[key]


PAD_G = {"pads": 0.6, "answ": 0.65, "lift": 0.7, "brk": 0.95,
         "pk1": 0.7, "dip": 0.75, "pk2": 0.75, "ro1": 0.4}
PAD_LP = {"pads": 850, "answ": 950, "lift": 1000, "brk": 1200,
          "pk1": 1050, "dip": 1000, "pk2": 1100, "ro1": 800}
clear()
for b in range(LAYER_SPAN["pads"][0], LAYER_SPAN["pads"][1], 2):
    s = section_of(b)
    if s not in PAD_G:
        continue
    att = 1.8 if s == "brk" else 0.8
    pL, pR = pad_chord(CHORD_AT[b][1], 2 * BAR + 2.5, att, PAD_LP[s])
    add_at(lay_L, pL, bar_t(b), PAD_G[s])
    add_at(lay_R, pR, bar_t(b), PAD_G[s])
# the composed tail ring: one Cm chord (excluded from the strip order)
pL, pR = pad_chord(Cm[1], 6.0, 1.5, 800)
add_at(lay_L, pL, bar_t(B_TAIL), 0.5)
add_at(lay_R, pR, bar_t(B_TAIL), 0.5)
lay_L = reverb(lay_L, IR_L, 0.5)
lay_R = reverb(lay_R, IR_R, 0.5)
commit(lay_L, lay_R, 0.16)
print("pads committed")


# ============================================================= dark swells
# The sanctioned era riser (farlight's recipe, the agreed caution):
# bandlimited 250-2400 Hz, low commit weight, resolved by a crash — never
# a white-noise wash.

clear()


def swell(b0, b1, gain=1.0, t_end=None):
    t0 = bar_t(b0)
    t1 = t_end if t_end is not None else bar_t(b1)
    n = int((t1 - t0) * SR)
    td = np.arange(n) / SR
    prog = td / (t1 - t0)
    noise = rng.standard_normal(n)
    out = np.zeros(n)
    for k in range(5):
        c = 250 * (2400 / 250) ** (k / 4)
        win = np.clip(1 - np.abs(prog - np.log(c / 250) / np.log(2400 / 250)) * 4, 0, 1)
        out += signal.sosfilt(signal.butter(2, [c * 0.8, c * 1.25], "bandpass",
                                            fs=SR, output="sos"), noise) * win
    out += 0.5 * np.sin(2 * np.pi * np.cumsum(midi_to_hz(48) * 2 ** prog) / SR)
    out *= prog ** 2
    add_at(lay_L, out / (np.max(np.abs(out)) + 1e-12), t0, gain)
    add_at(lay_R, out / (np.max(np.abs(out)) + 1e-12), t0, gain * 0.96)


swell(B_LIFT + 4, B_BRK, 0.7)
swell(B_PK1 - 4, B_PK1, 1.0, t_end=T_SILENCE)    # ends dead at the silence
swell(B_PK2 - 2, B_PK2, 0.6)
commit(lay_L, lay_R, 0.05)
print("dark swells committed")


# ---------------------------------------------------------------- master

fade(mix_L, fade_in=0.05, fade_out=7.0)
fade(mix_R, fade_in=0.05, fade_out=7.0)

for ch in (mix_L, mix_R):
    ch += 0.28 * signal.sosfilt(signal.butter(2, 95, "low", fs=SR, output="sos"), ch)
# no bright shelf — this one stays nocturnal

peak = max(np.max(np.abs(mix_L)), np.max(np.abs(mix_R))) + 1e-12
mix_L = np.tanh(1.3 * mix_L / peak) / np.tanh(1.3) * 0.88
mix_R = np.tanh(1.3 * mix_R / peak) / np.tanh(1.3) * 0.88

stereo = np.empty((N, 2))
stereo[:, 0] = mix_L
stereo[:, 1] = mix_R
pcm = (stereo * 32767.0).astype(np.int16)

OUT_DIR = "/workspace/music"
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, "penumbra.wav")
with wave.open(OUT, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())

print(f"\nCreated: {os.path.abspath(OUT)}")
print(f"Duration: {N / SR:.1f} s  |  {SR} Hz stereo, 16-bit PCM  |  "
      f"{BPM:.0f} BPM, C natural minor, Cm-Bb-Ab modal cycle")

MP3 = os.path.join(OUT_DIR, "penumbra.mp3")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", OUT,
                "-vn", "-ar", "44100", "-ac", "2", "-b:a", "192k", MP3],
               check=True)
print(f"Created: {os.path.abspath(MP3)}  (192k mp3)")

# ---------------------------------------------------------------- verify form

NAMES = {"intro": "intro (thesis in shadow)", "grv1": "groove I",
         "grv2": "groove II", "theme": "theme", "pads": "pads",
         "answ": "answer (bell tease)", "lift": "lift", "brk": "breakdown",
         "pk1": "PEAK I", "dip": "dip", "pk2": "PEAK II",
         "ro1": "ride-out I", "ro2": "ride-out II", "out": "outro",
         "tail": "tail"}
print("\nSection map:")
for name, b in SECS:
    print(f"  {bar_t(b):6.1f} s  bar {b:3d}  {NAMES[name]}")
print(f"  {bar_t(B_KSTOP):6.1f} s  bar {B_KSTOP}  the kick stops")
print(f"  {T_SILENCE:6.1f} s  bar {B_PK1 - 1} beat 3  THE SILENCE "
      f"(gated pickup hangs in it)")
print(f"  {DURATION:6.1f} s  end")

STATEMENTS.sort(key=lambda s: s[0])
counted = [s for s in STATEMENTS if s[3]]
ungated = [s for s in STATEMENTS if not s[2]]
print(f"\nRefrain statements (identical melody; counted = in the light):")
for b, label, gated, cnt in STATEMENTS:
    print(f"  bar {b:3d}  {'gated  ' if gated else 'UNGATED'}  "
          f"{'counted' if cnt else 'shadow '}  {label}")
print(f"  counted: {len(counted)} (target >= 10)   ungated: {len(ungated)}")

print("\nThe filter arc (cutoff at each boundary, from the automation):")
for name, b in SECS:
    print(f"  bar {b:3d} ({NAMES[name]:24s}) {cutoff_at(b):6.0f} Hz")
arc_bars = np.arange(0, B_END + 1)
arc_vals = np.array([cutoff_at(b) for b in arc_bars])
rise_ok = bool(np.all(np.diff(arc_vals[: B_PK1 + 1]) >= -1e-9))
frozen_ok = abs(cutoff_at(B_BRK) - cutoff_at(112)) < 1e-6
max_bars = arc_bars[arc_vals >= ARC_MAX - 1]
max_ok = bool(np.all((max_bars >= B_PK1) & (max_bars <= B_RO1)))
fall_ok = bool(np.all(np.diff(arc_vals[B_RO1: B_TAIL + 1]) <= 1e-9))
book_ok = abs(cutoff_at(B_END) - cutoff_at(0)) < 25

print("\nTHE SYMMETRY (strip order == reverse of add order):")
strip_order = sorted(LAYER_SPAN, key=lambda k: LAYER_SPAN[k][1])
print(f"  add   : {' -> '.join(f'{k}@{LAYER_SPAN[k][0]}' for k in ADD_ORDER)}")
print(f"  strip : {' -> '.join(f'{k}@{LAYER_SPAN[k][1]}' for k in strip_order)}")
print("  (tail rings at bar 204+ — one Cm pad chord, one bell C6 — are the"
      " composed tail, excluded)")
symmetry_ok = strip_order == ADD_ORDER[::-1]

print("\nBell discipline:")
bell_counts = {}
for bb, kind in BELL_EVENTS:
    bell_counts[kind] = bell_counts.get(kind, 0) + 1
    print(f"  bar {bb:6.2f}  {kind}")
bell_windows_ok = all(
    (kind == "tease" and B_ANSW <= bb < B_LIFT) or
    (kind == "peak" and (B_PK1 <= bb < B_DIP or B_PK2 <= bb < B_RO1)) or
    (kind == "farewell" and B_RO1 <= bb < 163) or
    (kind == "tail" and bb >= B_TAIL)
    for bb, kind in BELL_EVENTS)

print("\nSeam checklist (what crosses every boundary):")
for b, dev in [(B_GRV1, "unbroken groove; hats fade the layer in"),
               (B_GRV2, "unbroken groove; claps + first stab inside the bar"),
               (B_THEME, "crash; the arc crosses 800 Hz — the tune steps into half-light"),
               (B_PADS, "crash; the pad oscillation blooms under the running motif"),
               (B_ANSW, "soft crash; first bell answer inside (bar 77)"),
               (B_LIFT, "unbroken groove; ride enters; roll + swell begin inside"),
               (B_BRK, "crest -> crash; kick/bass exit; pads bloom long"),
               (B_PK1, "roll + swell end AT the silence; gated pickup hangs in it; softened slam"),
               (B_DIP, "statement chain unbroken; claps/ride out; the arc eases"),
               (B_PK2, "short roll + swell -> crash; everything returns"),
               (B_RO1, "crash; ride out; the arc starts its long descent"),
               (B_RO2, "pads hand the space back; stabs then claps strip inside"),
               (B_OUT, "soft crash; kick/bass/hats + the motif, arc closing"),
               (B_TAIL, "the bookend's last note rings; throb + tail rings")]:
    print(f"  bar {b:3d} ({bar_t(b):5.1f} s): {dev}")


def rms_between(b0, b1):
    i0 = int(bar_t(b0) * SR)
    i1 = int(bar_t(b1) * SR) if b1 is not None else N
    return np.sqrt(np.mean(mix_L[i0:i1] ** 2 + mix_R[i0:i1] ** 2) / 2)


print("\nPer-section RMS:")
R = {}
for (name, b0), (_, b1) in zip(SECS, SECS[1:] + [("end", None)]):
    R[name] = rms_between(b0, b1)
    print(f"  {NAMES[name]:26s} {R[name]:.3f}")

print("\nBanned-list audit (by construction):")
print("  no acid: bass peak Q=1.2 blend 0.3; the lead's filter is plain butter")
print("  no sidechain pump: the bass rolls offbeat 16ths instead")
print("  no white-noise riser: swells bandlimited 250-2400 Hz, commit 0.05")
print("  no reverse cymbal (nachtkind's); no toms (ungeschrieben's)")
print("  no supersaw: 3-voice detune, chorus-width only (pre-JP-8000)")
print("  the gate: straight 16ths, 58% duty, raised-cosine 4 ms edges")
print("  the harmony: ONE modal cycle (Cm Cm Bb Bb Ab Ab Cm Cm) throughout")
print("  sub entries bloom 0.55->1.0, 0.25 s attacks (farlight v2's lesson)")

# melodic symmetry + diatonic audit
durs_ok = all(tuple(dd for _, dd in BAR_NOTES[i]) == (1.5, 0.5, 2.0)
              for i in range(8))
mirror_ok = [m for m, _ in BAR_NOTES[6]] == [m for m, _ in BAR_NOTES[4]][::-1]
mel_pcs = {m % 12 for m, _ in REFRAIN}
CMIN_PCS = {0, 2, 3, 5, 7, 8, 10}
all_pcs = set(mel_pcs) | {82 % 12, 84 % 12}
for _, voicing in (Cm, Bb, Ab):
    all_pcs |= {m % 12 for m in voicing}
all_pcs |= {(36 + off) % 12 for off in (-4, -2, 0, 12)}

checks = [
    ("development rises: intro<grvI<grvII<theme<pads<answ<=lift",
     R["intro"] < R["grv1"] < R["grv2"] < R["theme"] < R["pads"]
     < R["answ"] <= R["lift"]),
    ("breakdown is the trough",
     R["brk"] < min(R["theme"], R["answ"], R["pk1"], R["pk2"])),
    ("PEAK I > lift (the drop pays)", R["pk1"] > R["lift"]),
    ("PEAK II is the loudest section", R["pk2"] == max(R.values())),
    ("the dip dips", R["dip"] < min(R["pk1"], R["pk2"])),
    ("ride-out descends: roI > roII > outro",
     R["ro1"] > R["ro2"] > R["out"]),
    ("outro lands near the intro level",
     0.5 < R["out"] / R["intro"] < 1.6),
    ("tail falls below the intro", R["tail"] < R["intro"]),
    ("counted statements >= 10", len(counted) >= 10),
    ("exactly ONE ungated statement, inside the breakdown",
     len(ungated) == 1 and B_BRK <= ungated[0][0] < B_PK1),
    ("refrain rhythm identical in all 8 bars (1.5 0.5 2)", durs_ok),
    ("Q/A mirror: answer bar 7 = retrograde of question bar 5", mirror_ok),
    ("melody = the blueprint's five degrees {1 b3 4 5 b7}",
     mel_pcs == {0, 3, 5, 7, 10}),
    ("hang is the b7, home is the tonic",
     REFRAIN[17][0] % 12 == 10 and REFRAIN[-1][0] % 12 == 0),
    ("everything C-natural-minor diatonic", all_pcs <= CMIN_PCS),
    ("arc rises monotonically to the drop (bars 0..116)", rise_ok),
    ("arc frozen through the breakdown core (96..112)", frozen_ok),
    ("arc max only inside the peaks", max_ok),
    ("arc descends monotonically after the peaks (156..204)", fall_ok),
    ("arc bookend: |end - intro| < 25 Hz", book_ok),
    ("THE SYMMETRY: strip order == reverse(add order)", symmetry_ok),
    ("bell: zero before bar 72; windows honored", bell_windows_ok),
    ("bell: 2 teases, 4 peak answers (every hang), 1 farewell, 1 tail",
     bell_counts.get("tease") == 2 and bell_counts.get("peak") == 4
     and bell_counts.get("farewell") == 1 and bell_counts.get("tail") == 1),
    ("the fusion: open arc + gate + bell co-occur only in the peaks",
     max_ok and bell_windows_ok and bell_counts.get("peak") == 4),
]
print("\nForm checks:")
ok = True
for name, passed in checks:
    print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
    ok &= passed
print("all checks passed" if ok else "SOME CHECKS FAILED")
