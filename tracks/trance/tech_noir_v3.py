#!/usr/bin/env python3
"""
tech_noir_v3.py — "Tech Noir" (~3:20). The Fiedel/Terminator machine score
composed as question and answer (design notes: tech_noir_v3_notes.md). This
is the song doctrine WITHOUT the pop form: no drop, no bridge, no bookend —
the 13/16 machine locks in at ~0:20 and never stops until the cold cut.
What v3 adds over the current tech_noir is the relationship between the two
themes, which previously lived in separate sections and never interacted:

THE QUESTION — the warm Oberheim fanfare, now ending HOLLOW every time (the
fifth-below ending becomes the rule): D F E C ... A. A machine asking the
same thing over and over. An ANVIL answers every phrase-end — the machine's
only reply is metal.

THE ANSWER — the love theme. Contour-level correspondence, not a rhythmic
mirror (the duality lives across dimensions, as the original Terminator put
it between melody and bassline): the theme's first note picks up the
question's hollow final A an octave up, and carries it stepwise home to D.

  0:00  cold open     Isolated anvil clangs in empty space; a dark pad
                      creeps in. (Unchanged — this is the thesis.)
  0:20  THE OSTINATO  13/16 bass pulse + gated slams lock in, never stop.
  0:51  THE QUESTION  The fanfare states the refrain 4x, every ending
                      hollow; the anvil answers each phrase-end.
  1:23  THE ANSWER    The love theme, twice, over i–bVI–bVII; the slams
                      pull back, the pads warm; a slam punctuates each
                      cadence. The fanfare is silent — the two never
                      overlap yet.
  1:54  INTERROGATION 2-bar trades: the question's head (cut short, hanging
                      on E) against the answer's cadence (landing on D) —
                      the harmony trades with them (Dm pedal / warm Bb).
                      Metal taps thicken, clangs every 2 bars. The last two
                      trades go UNANSWERED.
  2:18  THE FUSION    Both together for the first time: octave-doubled
                      fanfare + the love theme as counter-line — over an
                      UNMOVED Dm pedal (the machine does not accommodate).
                      Slams doubled; the fullest the machine gets.
  2:49  outro         Strip to bare pulse + metal; the fanfare asks once
                      more, quieter, unanswered.
  3:13  cold stop     One last slam and anvil ring out. Hard stop.

Fiedel rules unchanged: 13/16 grouped 3+3+3+2+2 (~99.5 BPM quarter pulse),
D minor, dry forward bass + wet metal, no hi-hats, no four-on-the-floor,
no risers, no reverse cymbals, no filter sweeps, no sidechain, ends cold.
Output: /workspace/music/tech_noir_v3.wav + tech_noir_v3.mp3 (192k, ffmpeg).
"""

"""
How the doctrine-without-the-pop-form landed, with your answers steering it:

    Contour duality, not mirroring. The love theme keeps its own rhythm entirely; the correspondence is that its first note is A — the question's hollow ending, picked up an octave above — falling stepwise home to the D the fanfare is denied. And per your Terminator point about melody-vs-bassline, the duality also lives in two other dimensions: in the interrogation the harmony trades along with the voices (Dm pedal under the question fragments, warm Bb under the answers), and in the fusion the pedal deliberately refuses to move under the love theme — the machine does not accommodate.
    The question formalized: one fanfare form only, ending hollow on A every time (D–F–E–C–A), stated identically 9 times. In the question section the anvil answers each phrase-end in the rest bar — the machine's only reply is metal.
    The interrogation (the experiment you approved): six 2-bar trades — the question's head cut short hanging on E, answered twice by the love theme's cadence landing on D, and then the last two questions go unanswered, driving into the fusion.
    The fusion is the first time the themes overlap: octave-doubled fanfare with the love theme as counter-line, doubled slams, taps, insistent clangs — measured as the loudest section (0.165 vs question 0.128).
    Everything banned stayed banned: no risers, no reverse cymbals, no builds — the seam checklist uses only slams, clangs, and rings. It ends cold: final slam + anvil at 3:13, ring decayed to 0.004 RMS in the last second, hard stop.
    Length: per your answer it took only the bars it needed — the structure matches the sketch bar-for-bar, but at the real 13/16 bar length it lands at 3:20 rather than the sketch's rough 4:30 estimate. Nothing was padded to hit a duration.

"""

import os
import subprocess
import wave
import numpy as np
from scipy import signal

SR = 44100
DURATION = 200.0
N = int(SR * DURATION)
t = np.arange(N) / SR

rng = np.random.default_rng(1984)     # the year the machine arrived

# 13/16: thirteen sixteenths per bar, quarter pulse ~99.5 BPM, one bar
# cycling every ~1.96 s. Grouped 3+3+3+2+2.
SIXT = 60.0 / (99.5 * 4)
BAR = 13 * SIXT
GRID0 = 0.5


def bar_t(b, step=0.0):
    return GRID0 + b * BAR + step * SIXT


# section boundaries, in 13/16 bars
B_OST = 10       # the ostinato locks in                    (~0:20)
B_Q = 26         # THE QUESTION: fanfare 4x, anvil answers  (~0:51)
B_A = 42         # THE ANSWER: love theme 2x                (~1:23)
B_INT = 58       # INTERROGATION: 2-bar trades              (~1:54)
B_FUS = 70       # THE FUSION: both together                (~2:18)
B_OUT = 86       # strip to pulse + metal                   (~2:49)
B_END = 98       # final hit, cold ring-out                 (~3:13)


# ---------------------------------------------------------------- helpers

def midi_to_hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def fade(x, fade_in=0.2, fade_out=1.5):
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


def glide_curve(notes, n, tau=0.05):
    """notes: list of (midi, duration_s). One-pole portamento."""
    f_target = np.zeros(n)
    edge = 0.0
    for m, d in notes:
        a, b = int(edge * SR), min(n, int((edge + d) * SR))
        f_target[a:b] = midi_to_hz(m)
        edge += d
    i_end = min(n - 1, int(edge * SR))
    f_target[i_end:] = f_target[i_end - 1]
    alpha = 1.0 - np.exp(-1.0 / (tau * SR))
    return signal.lfilter([alpha], [1.0, -(1.0 - alpha)],
                          f_target, zi=[f_target[0] * (1 - alpha)])[0]


# the big dark 80s plate — for the metal hits and the melodic voices
IR_L = make_reverb_ir(5.0, 2.2, 7)
IR_R = make_reverb_ir(5.0, 2.2, 11)

mix_L = np.zeros(N)
mix_R = np.zeros(N)


def commit(layer_L, layer_R, weight):
    global mix_L, mix_R
    peak = max(np.max(np.abs(layer_L)), np.max(np.abs(layer_R)), 1e-12)
    mix_L += layer_L * (weight / peak)
    mix_R += layer_R * (weight / peak)


# ------------------------------------------------------------- material
# D minor, static and modal.
#
# THE QUESTION: the five-note fanfare, and in v3 EVERY statement ends
# hollow — a fifth below the tonic (D F E C ... A). One form, identical
# each time; the count is verified. Each statement is 3 bars + 1 bar of
# rest — and the rest bar is where the anvil answers.
MOTIF_Q = [(62, 10), (65, 3), (64, 10), (60, 3), (57, 13)]   # D F E C A —

# THE ANSWER: the love theme (8 bars over i–bVI–bVII–i). The contour
# correspondence: its first note is A — the question's hollow ending,
# picked up an octave above — and it falls stepwise home to D, the
# resolution the fanfare is denied.
LOVE_NOTES = [
    (69, 6), (67, 4), (65, 3),     # Dm:  A  G  F
    (62, 13),                      #      D —
    (65, 6), (67, 4), (70, 3),     # Bb:  F  G  Bb
    (65, 10), (62, 3),             #      F —  D
    (64, 6), (67, 4), (64, 3),     # C:   E  G  E
    (60, 13),                      #      C —
    (65, 6), (64, 4), (60, 3),     # Dm:  F  E  C
    (62, 13),                      #      D —
]

# interrogation fragments: the question's head cut short (hanging on E,
# off-tonic) against the answer's cadence (landing on D). 2 bars each.
Q_FRAG = [(62, 10), (65, 3), (64, 13)]                       # D F E —
A_FRAG = [(65, 6), (64, 4), (60, 3), (62, 13)]               # F E C D —

PAD_DM = (50, 53, 57, 62)          # D F A D
PAD_BB = (46, 50, 53, 58)          # Bb D F Bb
PAD_C = (48, 52, 55, 60)           # C E G C
LOVE_PADS = [PAD_DM, PAD_BB, PAD_C, PAD_DM]   # 2 bars each across the phrase

STATEMENTS = 0                     # full fanfare statements (verified)


# ----------------------------------------------------------- bass pulse
# The machine's heartbeat: Prophet-style saw on D, "DUN-dun" doubles on
# the 3+3+3+2+2 grouping. Dry and forward. (v2 recipe verbatim.)

BASS_STEPS = [(0, 0, 1.00), (1, 0, 0.72),     # DUN-dun |
              (3, 0, 0.92), (4, 0, 0.66),     # DUN-dun |
              (6, 0, 0.96), (7, 0, 0.68),     # DUN-dun |
              (9, 0, 0.85),                   # DUN     |
              (11, 0, 0.90)]                  # DUN

bass_cache = {}


def bass_hit(midi, dur=SIXT * 0.95):
    if midi in bass_cache:
        return bass_cache[midi]
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    for k in range(1, min(28, int(3000 / f)) + 1):
        x += np.sin(2 * np.pi * k * f * td) / k
    sos_lp = signal.butter(2, 520, "low", fs=SR, output="sos")
    y = signal.sosfilt(sos_lp, x)
    y += 0.55 * np.sin(2 * np.pi * (f / 2) * td)          # round sub octave
    y = np.tanh(1.8 * y)
    y *= (1 - np.exp(-td / 0.002)) * np.exp(-td * 14.0)
    y *= np.clip((dur - td) / 0.015, 0, 1)
    bass_cache[midi] = y / (np.max(np.abs(y)) + 1e-12)
    return bass_cache[midi]


def bass_gain(b):
    if b < B_OST:
        return 0.0
    if b < B_Q:
        return 0.80
    if b < B_A:
        return 0.90
    if b < B_INT:
        return 0.75                  # the answer floats; the pulse recedes
    if b < B_FUS:
        return 0.85
    if b < B_OUT:
        return 1.00
    if b < B_END - 4:
        return 0.85
    return 0.62                      # the heartbeat thinning at the end


lay_L = np.zeros(N)
lay_R = np.zeros(N)
for b in range(B_END):
    g = bass_gain(b)
    if g == 0.0:
        continue
    for s, off, gg in BASS_STEPS:
        x = bass_hit(38 + off)                            # D2 pedal
        add_at(lay_L, x, bar_t(b, s), g * gg)
        add_at(lay_R, x, bar_t(b, s), g * gg)
    if B_FUS <= b < B_OUT:                                # octave-up flick
        x = bass_hit(50)
        add_at(lay_L, x, bar_t(b, 11), g * 0.45)
        add_at(lay_R, x, bar_t(b, 11), g * 0.45)
commit(lay_L, lay_R, 0.30)
print(f"bass pulse committed ({len(bass_cache)} cached notes)")


# ----------------------------------------------------- metal percussion
# No drum kit. Anvil clangs under a huge dark plate, gated 80s slams
# (the gate baked into the sample). (v2 recipes verbatim.)

def make_anvil():
    n = int(4.0 * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    f0 = 410.0
    for i, (ratio, g) in enumerate(zip(
            [1.0, 2.71, 4.07, 5.43, 7.39, 9.21],
            [1.0, 0.78, 0.55, 0.40, 0.26, 0.16])):
        dec = 1.1 + 0.55 * i
        for det in (0.9991, 1.0009):
            x += g * np.sin(2 * np.pi * f0 * ratio * det * td +
                            rng.uniform(0, 2 * np.pi)) * np.exp(-td * dec)
    sos_s = signal.butter(2, [2500, 9000], "bandpass", fs=SR, output="sos")
    strike = signal.sosfilt(sos_s, rng.standard_normal(n)) * np.exp(-td * 280)
    strike /= np.max(np.abs(strike)) + 1e-12
    x = x / (np.max(np.abs(x)) + 1e-12) + 0.7 * strike
    x *= 1 - np.exp(-td / 0.0006)
    return x / (np.max(np.abs(x)) + 1e-12)


def make_slam():
    n = int(0.55 * SR)
    td = np.arange(n) / SR
    f_curve = 52.0 + 98.0 * np.exp(-td * 26.0)
    body = np.sin(2 * np.pi * np.cumsum(f_curve) / SR) * np.exp(-td * 9.0)
    sos_n = signal.butter(2, [180, 2400], "bandpass", fs=SR, output="sos")
    burst = signal.sosfilt(sos_n, rng.standard_normal(n))
    burst /= np.max(np.abs(burst)) + 1e-12
    x = body + 0.55 * burst * np.exp(-td * 16.0) + 0.30 * burst * np.exp(-td * 3.0)
    gate = np.clip((0.140 - td) / 0.025, 0, 1)            # hard 80s gate
    x *= (1 - np.exp(-td / 0.0015)) * gate
    return x / (np.max(np.abs(x)) + 1e-12)


def make_tap():
    n = int(0.35 * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    for ratio, g in zip([1.0, 2.89, 5.12], [1.0, 0.5, 0.25]):
        x += g * np.sin(2 * np.pi * 1280.0 * ratio * td +
                        rng.uniform(0, 2 * np.pi)) * np.exp(-td * 14.0)
    sos_s = signal.butter(2, [4000, 10000], "bandpass", fs=SR, output="sos")
    strike = signal.sosfilt(sos_s, rng.standard_normal(n)) * np.exp(-td * 220)
    strike /= np.max(np.abs(strike)) + 1e-12
    x = x / (np.max(np.abs(x)) + 1e-12) + 0.5 * strike
    x *= 1 - np.exp(-td / 0.0006)
    return x / (np.max(np.abs(x)) + 1e-12)


ANVIL = make_anvil()
SLAM = make_slam()
TAP = make_tap()

# --- slams: punctuation across the 13 cycle, never a continuous groove
lay_L[:] = 0.0
lay_R[:] = 0.0
add_at(lay_L, SLAM, 12.5, 0.7)                            # one intro thud
add_at(lay_R, SLAM, 12.5, 0.7)
for b in range(B_END):
    if b < B_OST:
        continue
    if b < B_Q:
        hits = [(0, 0.80)]
    elif b < B_A:
        hits = [(0, 0.90)] + ([(6, 0.50)] if b % 4 == 2 else [])
    elif b < B_INT:
        # pulled back; a stronger slam punctuates each love-theme cadence
        hits = [(0, 0.90 if (b - B_A) % 8 == 7 else 0.60)]
    elif b < B_FUS:
        hits = [(0, 0.85)] + ([(6, 0.50)] if b % 2 == 1 else [])
    elif b < B_OUT:
        hits = [(0, 1.00), (6, 0.70)] + ([(9, 0.60)] if b % 4 == 3 else [])
    else:
        hits = [(0, 0.80)] if b % 2 == 0 else []
    for s, g in hits:
        add_at(lay_L, SLAM, bar_t(b, s), g)
        add_at(lay_R, SLAM, bar_t(b, s), g * 0.94)
add_at(lay_L, SLAM, bar_t(B_END), 1.0)                    # the final blow
add_at(lay_R, SLAM, bar_t(B_END), 1.0)
commit(lay_L, lay_R, 0.20)
print("slams committed")

# --- anvils: isolated in the intro; in the question section the anvil
# ANSWERS each fanfare phrase-end (the rest bar) — the machine's reply
lay_L[:] = 0.0
lay_R[:] = 0.0
for t0, g, p in [(1.2, 1.0, 0.30), (5.1, 0.80, 0.68), (9.3, 0.90, 0.42),
                 (14.0, 0.70, 0.75), (17.6, 0.85, 0.55)]:
    add_at(lay_L, ANVIL, t0, g * np.cos(p * np.pi / 2))
    add_at(lay_R, ANVIL, t0, g * np.sin(p * np.pi / 2))
anvil_hits = []
for b in range(12, B_Q, 4):
    anvil_hits.append((b, 0, 0.70))
for b0 in range(B_Q, B_A, 4):                             # the metal answer
    anvil_hits.append((b0 + 3, 0, 0.80))
anvil_hits += [(B_A, 0, 0.60), (B_A + 8, 0, 0.55)]        # sparse; she speaks
for b in range(B_INT, B_FUS, 2):                          # clangs every 2 bars
    anvil_hits.append((b, 0, 0.70))
for b in range(B_FUS, B_OUT, 2):                          # insistent now
    anvil_hits.append((b, 0, 0.80))
    if b % 4 == 1:
        anvil_hits.append((b, 6, 0.60))
anvil_hits += [(B_OUT, 0, 0.80), (B_OUT + 8, 0, 0.80)]
anvil_hits.append((B_END, 0, 1.00))                       # the cold ring-out
for b, s, g in anvil_hits:
    p = 0.38 if (b // 2) % 2 == 0 else 0.62
    add_at(lay_L, ANVIL, bar_t(b, s), g * np.cos(p * np.pi / 2))
    add_at(lay_R, ANVIL, bar_t(b, s), g * np.sin(p * np.pi / 2))
lay_L = reverb(lay_L, IR_L, wet=0.60)
lay_R = reverb(lay_R, IR_R, wet=0.60)
commit(lay_L, lay_R, 0.16)
print("anvils committed")

# --- metal taps: thicken through the interrogation and the fusion
lay_L = np.zeros(N)
lay_R = np.zeros(N)
for b in range(B_INT, B_OUT):
    g = 0.40 if b < B_FUS else 0.55
    add_at(lay_L, TAP, bar_t(b, 3), g)
    add_at(lay_R, TAP, bar_t(b, 3), g * 0.45)
    add_at(lay_L, TAP, bar_t(b, 9), g * 0.45)
    add_at(lay_R, TAP, bar_t(b, 9), g * 0.9)
lay_L = reverb(lay_L, IR_L, wet=0.45)
lay_R = reverb(lay_R, IR_R, wet=0.45)
commit(lay_L, lay_R, 0.05)
print("taps committed")


# ---------------------------------------------------------- brass motif
# The question voice: warm Oberheim poly brass (the warmth recipe — reed
# spectrum 1/k^1.35, sine body core, rounded 0.2 s bloom, low lowpass,
# whisper of drive). v2 recipe verbatim, parameterized by notes.

def brass_phrase(notes, lowpass=1600.0):
    total = sum(d for _, d in notes) * SIXT
    n = int((total + 2.0) * SR)
    tt = np.arange(n) / SR
    f_curve = glide_curve([(m, d * SIXT) for m, d in notes], n, tau=0.05)
    f_curve *= 1.0 - 0.018 * np.exp(-tt / 0.12)           # a gentler scoop
    vib = 1.0 + 0.0024 * np.sin(2 * np.pi * 4.5 * tt) * np.clip(tt / 1.4, 0, 1)
    K = max(3, int(5200 / np.max(f_curve)))

    def reed(det):
        ph = 2 * np.pi * np.cumsum(f_curve * det * vib) / SR
        v = np.zeros(n)
        for k in range(1, K + 1):
            v += np.sin(k * ph) / k ** 1.35
        return v

    base = reed(1.0)
    body = np.sin(2 * np.pi * np.cumsum(f_curve * vib) / SR)   # round core
    vL = base + reed(0.9968) + 0.35 * body
    vR = base + reed(1.0032) + 0.35 * body
    atk = np.clip(tt / 0.20, 0, 1)                        # slow bloom-in
    atk = 0.5 - 0.5 * np.cos(np.pi * atk)                 # rounded, not linear
    env = np.minimum(atk, np.clip((total + 0.35 - tt) / 1.0, 0, 1))
    sos_w = signal.butter(2, lowpass, "low", fs=SR, output="sos")
    vL = np.tanh(0.8 * signal.sosfilt(sos_w, vL * env))   # a whisper of drive
    vR = np.tanh(0.8 * signal.sosfilt(sos_w, vR * env))
    peak = max(np.max(np.abs(vL)), np.max(np.abs(vR)), 1e-12)
    return vL / peak, vR / peak


BRASS_Q = brass_phrase(MOTIF_Q)
BRASS_Q_HI = brass_phrase([(m + 12, d) for m, d in MOTIF_Q], lowpass=2400.0)
BRASS_FRAG = brass_phrase(Q_FRAG)

lay_L = np.zeros(N)
lay_R = np.zeros(N)
# THE QUESTION: four identical hollow statements
for b0 in range(B_Q, B_A, 4):
    add_at(lay_L, BRASS_Q[0], bar_t(b0), 1.0)
    add_at(lay_R, BRASS_Q[1], bar_t(b0), 1.0)
    STATEMENTS += 1
# interrogation: the question's head, cut short — trades at 58/62, then
# twice unanswered (66, 68) driving into the fusion
for b0 in (B_INT, B_INT + 4, B_INT + 8, B_INT + 10):
    add_at(lay_L, BRASS_FRAG[0], bar_t(b0), 0.90)
    add_at(lay_R, BRASS_FRAG[1], bar_t(b0), 0.90)
# THE FUSION: octave-doubled statements over the counter-line
for b0 in range(B_FUS, B_OUT, 4):
    add_at(lay_L, BRASS_Q[0], bar_t(b0), 1.05)
    add_at(lay_R, BRASS_Q[1], bar_t(b0), 1.05)
    add_at(lay_L, BRASS_Q_HI[0], bar_t(b0), 0.30)
    add_at(lay_R, BRASS_Q_HI[1], bar_t(b0), 0.30)
    STATEMENTS += 1
# outro: the question once more, quieter — unanswered
add_at(lay_L, BRASS_Q[0], bar_t(B_OUT + 2), 0.85)
add_at(lay_R, BRASS_Q[1], bar_t(B_OUT + 2), 0.85)
STATEMENTS += 1
lay_L = reverb(lay_L, IR_L, wet=0.38)
lay_R = reverb(lay_R, IR_R, wet=0.38)
commit(lay_L, lay_R, 0.23)
print("brass motif committed")


# ----------------------------------------------------------- love theme
# The answer voice: plaintive, nearly-pure, very wet. (v2 recipe,
# parameterized by notes.)

def love_phrase(notes):
    total = sum(d for _, d in notes) * SIXT
    n = int((total + 2.5) * SR)
    tt = np.arange(n) / SR
    f_curve = glide_curve([(m, d * SIXT) for m, d in notes], n, tau=0.07)
    vib = 1.0 + 0.005 * np.sin(2 * np.pi * 5.2 * tt) * np.clip(tt / 1.0, 0, 1)
    ph = 2 * np.pi * np.cumsum(f_curve * vib) / SR
    v = (np.sin(ph) + 0.40 * np.sin(2 * ph) +
         0.16 * np.sin(3 * ph) + 0.07 * np.sin(4 * ph))
    env = np.minimum(np.clip(tt / 0.25, 0, 1),
                     np.clip((total + 0.4 - tt) / 1.2, 0, 1))
    sos_w = signal.butter(2, 3000, "low", fs=SR, output="sos")
    v = signal.sosfilt(sos_w, v * env)
    v /= np.max(np.abs(v)) + 1e-12
    return v


LOVE = love_phrase(LOVE_NOTES)
LOVE_ANS = love_phrase(A_FRAG)

lay_L = np.zeros(N)
lay_R = np.zeros(N)


def place_love(x, t0, g):
    add_at(lay_L, x, t0, g * 0.92)
    add_at(lay_R, x, t0, g)
    add_at(lay_L, x, t0 + 2 * SIXT, g * 0.22)             # soft echo
    add_at(lay_R, x, t0 + 2 * SIXT, g * 0.18)


# THE ANSWER: the theme twice, alone with the receded machine
place_love(LOVE, bar_t(B_A), 0.85)
place_love(LOVE, bar_t(B_A + 8), 1.0)
# interrogation: the cadence answers the first two fragments — then stops
place_love(LOVE_ANS, bar_t(B_INT + 2), 0.9)
place_love(LOVE_ANS, bar_t(B_INT + 6), 0.9)
# THE FUSION: the counter-line under the doubled fanfare
place_love(LOVE, bar_t(B_FUS), 0.75)
place_love(LOVE, bar_t(B_FUS + 8), 0.80)
lay_L = reverb(lay_L, IR_L, wet=0.55)
lay_R = reverb(lay_R, IR_R, wet=0.55)
commit(lay_L, lay_R, 0.22)
print("love theme committed")


# ----------------------------------------------------------------- pads
# Cold, dark, low-passed analog strings. In the interrogation the HARMONY
# trades along with the voices: Dm pedal under the question fragments,
# the warm Bb under the answers — the duality in another dimension. In
# the fusion the pedal does not move: the machine does not accommodate.

def pad_chord(chord, dur, attack=2.5, release=3.0):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    out_L = np.zeros(n)
    out_R = np.zeros(n)
    for m in chord:
        f = midi_to_hz(m)
        amp = 0.8 + 0.2 * np.sin(2 * np.pi * rng.uniform(0.02, 0.06) * tt +
                                 rng.uniform(0, 2 * np.pi))
        for det, gL, gR in [(0.9991, 1.0, 0.6), (1.0009, 0.6, 1.0)]:
            ph = 2 * np.pi * f * det * tt + rng.uniform(0, 2 * np.pi)
            v = (np.sin(ph) + 0.35 * np.sin(2 * ph) +
                 0.12 * np.sin(3 * ph)) * amp
            out_L += gL * v
            out_R += gR * v
    env = np.minimum(np.clip(tt / attack, 0, 1) ** 1.5,
                     np.clip((dur - tt) / release, 0, 1))
    sos_d = signal.butter(2, 900, "low", fs=SR, output="sos")
    out_L = signal.sosfilt(sos_d, out_L * env)
    out_R = signal.sosfilt(sos_d, out_R * env)
    peak = max(np.max(np.abs(out_L)), np.max(np.abs(out_R)), 1e-12)
    return out_L / peak, out_R / peak


lay_L = np.zeros(N)
lay_R = np.zeros(N)

# intro creep: one long cold Dm swell out of the dark (the thesis bed)
pL, pR = pad_chord((38, 45, 50, 53), (B_OST + 6) * BAR,
                   attack=8.0, release=4.0)
add_at(lay_L, pL, bar_t(2), 0.85)
add_at(lay_R, pR, bar_t(2), 0.85)

# faint pedal bed under the question
for b0 in range(B_Q, B_A, 8):
    pL, pR = pad_chord(PAD_DM, 8 * BAR + 2.0, attack=3.0, release=3.0)
    add_at(lay_L, pL, bar_t(b0), 0.40)
    add_at(lay_R, pR, bar_t(b0), 0.40)

# the answer's harmony, 2 bars per chord across each 8-bar phrase
for b0 in range(B_A, B_INT, 2):
    chord = LOVE_PADS[((b0 - B_A) // 2) % 4]
    pL, pR = pad_chord(chord, 2 * BAR + 1.5, attack=0.9, release=1.6)
    add_at(lay_L, pL, bar_t(b0), 0.95)
    add_at(lay_R, pR, bar_t(b0), 0.95)

# interrogation: the harmony trades with the voices
for b0 in range(B_INT, B_FUS, 2):
    warm = b0 in (B_INT + 2, B_INT + 6)                   # the answered trades
    pL, pR = pad_chord(PAD_BB if warm else PAD_DM, 2 * BAR + 1.5,
                       attack=0.9, release=1.6)
    add_at(lay_L, pL, bar_t(b0), 0.70 if warm else 0.50)
    add_at(lay_R, pR, bar_t(b0), 0.70 if warm else 0.50)

# the fusion: dark unmoved pedal; nothing in the outro — cold
for b0 in range(B_FUS, B_OUT, 8):
    pL, pR = pad_chord((38, 50, 53, 57), 8 * BAR + 2.0,
                       attack=3.0, release=3.0)
    add_at(lay_L, pL, bar_t(b0), 0.50)
    add_at(lay_R, pR, bar_t(b0), 0.50)

lay_L = reverb(lay_L, IR_L, wet=0.50)
lay_R = reverb(lay_R, IR_R, wet=0.50)
commit(lay_L, lay_R, 0.13)
print("pads committed")


# ------------------------------------------------------------------ air

sos_air = signal.butter(4, [200, 900], "bandpass", fs=SR, output="sos")
air = signal.sosfilt(sos_air, rng.standard_normal(N))
air /= np.max(np.abs(air))
air_env = slow_noise(0.05, 0.5, 1.0)
edge = np.minimum(np.clip((bar_t(B_Q) - t) / 12.0, 0, 1) +
                  np.clip((t - bar_t(B_OUT)) / 20.0, 0, 1), 1.0)
commit(air * air_env * edge, air * air_env[::-1] * edge, 0.04)
print("air committed")


# ---------------------------------------------------------------- master

fade(mix_L, fade_in=0.2, fade_out=1.5)
fade(mix_R, fade_in=0.2, fade_out=1.5)

peak = max(np.max(np.abs(mix_L)), np.max(np.abs(mix_R)))
mix_L = mix_L / peak * 0.88
mix_R = mix_R / peak * 0.88

stereo = np.empty((N, 2))
stereo[:, 0] = mix_L
stereo[:, 1] = mix_R
pcm = (stereo * 32767.0).astype(np.int16)

OUT_DIR = "/workspace/music"
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, "tech_noir_v3.wav")
with wave.open(OUT, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())

print(f"\nCreated: {os.path.abspath(OUT)}")
print(f"Duration: {N / SR:.1f} s  |  {SR} Hz stereo, 16-bit PCM  |  "
      f"13/16 at ~99.5 BPM quarter pulse, D minor")

MP3 = os.path.join(OUT_DIR, "tech_noir_v3.mp3")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", OUT,
                "-vn", "-ar", "44100", "-ac", "2", "-b:a", "192k", MP3],
               check=True)
print(f"Created: {os.path.abspath(MP3)}  (192k mp3)")

# ---------------------------------------------------------------- verify form
# The machine-score variant of the standard (see ../VERIFY.md): motif
# statement count instead of hook count; piece-specific ordering instead of
# chorus checks; and the "ends cold" check.

print("\nSection map:")
SECTIONS = [("cold open (the thesis)", 0), ("THE OSTINATO", B_OST),
            ("THE QUESTION", B_Q), ("THE ANSWER", B_A),
            ("INTERROGATION", B_INT), ("THE FUSION", B_FUS),
            ("outro (bare machine)", B_OUT), ("cold stop", B_END)]
for name, b in SECTIONS:
    print(f"  {bar_t(b):6.1f} s  bar {b:3d}  {name}")
print(f"  {DURATION:6.1f} s  end")

print(f"\nFanfare statements: {STATEMENTS}  (target >= 8; interrogation "
      f"fragments not counted)")

print("\nSeam checklist (what crosses every boundary — slams, clangs, rings only):")
for b, dev in [(B_OST, "the 17.6 s anvil's plate ring hangs over the pulse entry"),
               (B_Q, "slam on the downbeat; the machine unbroken"),
               (B_A, "the question's hollow A still ringing; warm pads swell under it"),
               (B_INT, "the answer's final D rings; a clang marks the first trade"),
               (B_FUS, "the twice-unanswered question hangs; doubled slam on the downbeat"),
               (B_OUT, "the fusion's last cadence rings into the bare pulse"),
               (B_END, "one last slam + anvil — the ending, not a seam")]:
    print(f"  bar {b:3d} ({bar_t(b):5.1f} s): {dev}")

def rms_between(b0, b1):
    i0 = int(bar_t(b0) * SR)
    i1 = int(bar_t(b1) * SR) if b1 is not None else N
    return np.sqrt(np.mean(mix_L[i0:i1] ** 2 + mix_R[i0:i1] ** 2) / 2)

print("\nPer-section RMS:")
R = {}
for (name, b0), (_, b1) in zip(SECTIONS, SECTIONS[1:] + [("end", None)]):
    R[name] = rms_between(b0, b1)
    print(f"  {name:24s} {R[name]:.3f}")

final_hit = rms_between(B_END, None)
last_second = np.sqrt(np.mean(mix_L[-SR:] ** 2 + mix_R[-SR:] ** 2) / 2)
checks = [
    ("the question rises above the bare machine",
     R["THE QUESTION"] > R["THE OSTINATO"]),
    ("the answer is quieter than the question",
     R["THE ANSWER"] < R["THE QUESTION"]),
    ("THE FUSION is the loudest section",
     R["THE FUSION"] == max(R.values())),
    ("outro settles below the question",
     R["outro (bare machine)"] < R["THE QUESTION"]),
    ("ends cold: ring-out decays to silence, no music after the blow",
     last_second < 0.02),
    ("fanfare statements >= 8", STATEMENTS >= 8),
]
print("\nForm checks:")
ok = True
for name, passed in checks:
    print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
    ok &= passed
print("all checks passed" if ok else "SOME CHECKS FAILED")
