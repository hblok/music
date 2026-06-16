#!/usr/bin/env python3
"""
generate_nachtkind.py — "Nachtkind" (~5:30). Classic early-90s Frankfurt
trance in the Eye Q school, inspired by Synfonica "Brainchild" (1993,
Matthias Hoffmann). 139 BPM, G minor. No supersaws, no snare-roll drops:
hypnotic additive/subtractive layering in 8/16-bar blocks, a gothic piano
theme as the centerpiece, and a soaring detuned analog lead stacked OVER
the piano at the climax. Drums dry and mechanical (909 school); melodic
elements very wet (long dark hall) — the Eye Q dry/wet contrast.

  0:00  Dry kick, closed hats creep in, offbeat open hat, shaker.
  0:42  THE PIANO — the gothic theme enters over the sparse groove.
  1:10  Layering phase: rolling octave bass locks in, claps on 2 & 4,
        left-hand piano octaves; at 1:37 a filtered offbeat chord stab
        and upper-octave piano doubling join (something new every 16 bars).
  2:05  BREAKDOWN — drums drop. Piano and dark pads carry the track;
        the kick walks back in quietly, a reverse cymbal leans into
  2:32  MAIN SECTION — the soaring lead line layered over the piano
        theme: the duet climax. 909 ride enters. 48 bars in three
        16-bar waves (lead alone / +octave shimmer / +chord stab).
  3:55  Deconstruction — layers peel away in reverse: lead gone, piano
        thins, then leaves; pads return; bass filters down and exits.
  4:50  DJ outro: kick, hats, residual atmosphere.
  5:18  The kick stops. Solo piano echoes the theme once — the
        "Transcription" moment — and a final G minor chord rings out.

Harmony: i–VI–VII–V (Gm–Eb–F–D) with the F# of D major as the gothic
leading-tone touch. Instrumental, no vocals.

Output: /workspace/music/nachtkind.wav + nachtkind.mp3 (192k, ffmpeg).
"""

import os
import subprocess
import wave
import numpy as np
from scipy import signal

SR = 44100
DURATION = 331.0
N = int(SR * DURATION)
t = np.arange(N) / SR

rng = np.random.default_rng(1993)    # the year Brainchild came out

BPM = 139.0
BEAT = 60.0 / BPM
BAR = BEAT * 4
STEP = BEAT / 4
GRID0 = 0.5


def bar_t(b, beat=0.0):
    return GRID0 + b * BAR + beat * BEAT


# section boundaries, in bars
B_HATS = 4        # closed hats join the dry kick
B_OPEN = 8        # offbeat open hat
B_PERC = 12       # shaker + atmosphere pad creeping in
B_BASSIN = 16     # rolling bass, dark-filtered
B_THEME = 24      # the gothic piano theme enters
B_LAYER = 40      # bass opens up, claps, LH piano octaves
B_LAYER2 = 56     # + chord stab, + piano octave doubling
B_BREAK = 72      # breakdown: drums drop, piano + pads
B_BREAK2 = 80     # kick walks back in quietly
B_MAIN = 88       # CLIMAX: lead over piano, ride, full groove
B_MAIN2 = 104     # + octave shimmer on the lead
B_MAIN3 = 120     # + chord stab returns
B_DECON = 136     # lead exits, piano continues
B_DECON2 = 152    # piano exits, pads return
B_OUT = 168       # DJ outro: kick + hats + atmosphere
B_BASSOUT = 176   # bass exits
B_STOP = 184      # kick stops; piano transcription coda


# ---------------------------------------------------------------- helpers

def midi_to_hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def fade(x, fade_in=0.4, fade_out=8.0):
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


def glide_curve(notes, n, tau=0.06):
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


# the long dark hall (melodic elements only — drums stay bone dry)
IR_L = make_reverb_ir(6.0, 2.6, 7)
IR_R = make_reverb_ir(6.0, 2.6, 11)

mix_L = np.zeros(N)
mix_R = np.zeros(N)


def commit(layer_L, layer_R, weight, env=None):
    global mix_L, mix_R
    peak = max(np.max(np.abs(layer_L)), np.max(np.abs(layer_R)), 1e-12)
    if env is None:
        mix_L += layer_L * (weight / peak)
        mix_R += layer_R * (weight / peak)
    else:
        mix_L += layer_L * env * (weight / peak)
        mix_R += layer_R * env * (weight / peak)


# ------------------------------------------------------------ the theme
# 8-bar gothic piano theme, G minor: i–VI–VII–V | i–VI–VII–V.
# (beat offset, midi, duration in beats, gain)

THEME_RH = [
    (0, 74, 1, 1.0), (1, 70, 1, .85), (2, 67, 2, .90),    # Gm
    (4, 75, 1, 1.0), (5, 74, 1, .85), (6, 70, 2, .90),    # Eb
    (8, 72, 1, 1.0), (9, 74, 1, .85), (10, 69, 2, .90),   # F
    (12, 66, 1, 1.0), (13, 69, 1, .85), (14, 74, 2, .90),  # D (the F#)
    (16, 67, 1, 1.0), (17, 69, 1, .85), (18, 70, 2, .90),  # Gm
    (20, 75, 1, 1.0), (21, 70, 1, .85), (22, 67, 2, .90),  # Eb
    (24, 65, 1, 1.0), (25, 67, 1, .85), (26, 69, 2, .90),  # F
    (28, 69, 1, .90), (29, 66, 1, .85), (30, 74, 2, 1.0),  # D
]
PHRASE_ROOTS = [43, 39, 41, 38, 43, 39, 41, 38]            # G Eb F D, per bar
THEME_LH = []
for i, root in enumerate(PHRASE_ROOTS):
    THEME_LH += [(4 * i, root, 2, .9), (4 * i, root + 12, 2, .7),
                 (4 * i + 2, root + 7, 2, .8), (4 * i + 2, root + 12, 2, .6)]

# soaring lead counter-line, sits above the piano: (midi, duration in beats)
LEAD_NOTES = [(74, 2), (79, 4), (81, 2), (79, 2), (78, 2), (81, 2),
              (82, 4), (79, 2), (75, 2), (77, 2), (81, 2), (74, 4)]

PAD_CHORDS = [(43, 55, 58, 62), (39, 51, 55, 58),          # Gm  Eb
              (41, 53, 57, 60), (38, 50, 54, 57)]          # F   D


# ---------------------------------------------------------------- drums
# 909 school: punchy kick (not modern-sub-heavy), 16th closed hats,
# accented offbeat open hat, sparse claps on 2 & 4, ride in the main
# sections, crashes/reverse cymbals at phrase boundaries. ALL DRY.

def make_kick():
    n = int(0.26 * SR)
    td = np.arange(n) / SR
    f_curve = 48.0 + 102.0 * np.exp(-td * 50.0)
    body = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    sos_c = signal.butter(2, [1500, 6000], "bandpass", fs=SR, output="sos")
    click = signal.sosfilt(sos_c, rng.standard_normal(n)) * np.exp(-td * 500)
    click /= np.max(np.abs(click)) + 1e-12
    env = (1 - np.exp(-td / 0.001)) * np.exp(-td * 10.0)
    x = (body + 0.30 * click) * env
    return x / (np.max(np.abs(x)) + 1e-12)


def make_hat(open_=False):
    n = int((0.12 if open_ else 0.045) * SR)
    td = np.arange(n) / SR
    sos_h = signal.butter(4, 7000, "high", fs=SR, output="sos")
    x = signal.sosfilt(sos_h, rng.standard_normal(n))
    x *= np.exp(-td * (28 if open_ else 110))
    return x / (np.max(np.abs(x)) + 1e-12)


def make_ride():
    n = int(0.40 * SR)
    td = np.arange(n) / SR
    nz = rng.standard_normal(n)
    sos_a = signal.butter(2, [4000, 7000], "bandpass", fs=SR, output="sos")
    sos_b = signal.butter(2, [8000, 12000], "bandpass", fs=SR, output="sos")
    x = signal.sosfilt(sos_a, nz) * np.exp(-td * 9.0)
    x += 0.7 * signal.sosfilt(sos_b, nz) * np.exp(-td * 6.0)
    x /= np.max(np.abs(x)) + 1e-12
    x += 0.18 * np.sin(2 * np.pi * 5400.0 * td) * np.exp(-td * 8.0)
    x *= 1 - np.exp(-td / 0.001)
    return x / (np.max(np.abs(x)) + 1e-12)


def make_clap():
    n = int(0.30 * SR)
    td = np.arange(n) / SR
    sos_c = signal.butter(2, [900, 4500], "bandpass", fs=SR, output="sos")
    x = np.zeros(n)
    for i, dmp in [(0, 120.0), (1, 120.0), (2, 120.0), (3, 26.0)]:
        i0 = int(i * 0.011 * SR)
        seg = signal.sosfilt(sos_c, rng.standard_normal(n - i0))
        x[i0:] += seg * np.exp(-td[: n - i0] * dmp)
    return x / (np.max(np.abs(x)) + 1e-12)


def make_shaker():
    n = int(0.06 * SR)
    td = np.arange(n) / SR
    sos_s = signal.butter(2, [3500, 9500], "bandpass", fs=SR, output="sos")
    x = signal.sosfilt(sos_s, rng.standard_normal(n)) * np.exp(-td * 70)
    return x / (np.max(np.abs(x)) + 1e-12)


def make_crash():
    n = int(2.0 * SR)
    td = np.arange(n) / SR
    sos_c = signal.butter(2, 5000, "high", fs=SR, output="sos")
    x = signal.sosfilt(sos_c, rng.standard_normal(n)) * np.exp(-td * 2.2)
    x *= 1 - np.exp(-td / 0.002)
    return x / (np.max(np.abs(x)) + 1e-12)


KICK = make_kick()
CHAT = make_hat()
OHAT = make_hat(open_=True)
RIDE = make_ride()
CLAP = make_clap()
SHAKER = make_shaker()
CRASH = make_crash()
RCYM = np.ascontiguousarray(CRASH[::-1] [int(0.5 * SR):])   # 1.5 s reverse


def kick_gain(b):
    if B_BREAK <= b < B_BREAK2:
        return 0.0                       # the breakdown
    if B_BREAK2 <= b < B_MAIN:
        return 0.55                      # walking back in
    if b < B_THEME:
        return 0.78
    if b < B_LAYER:
        return 0.85
    if b < B_BREAK:
        return 0.92                      # hold headroom before the climax
    if b >= B_OUT:
        return 0.95
    return 1.0


lay_L = np.zeros(N)
lay_R = np.zeros(N)
for b in range(B_STOP):
    g = kick_gain(b)
    if g == 0.0:
        continue
    for beat in range(4):
        add_at(lay_L, KICK, bar_t(b, beat), g)
        add_at(lay_R, KICK, bar_t(b, beat), g)
commit(lay_L, lay_R, 0.34)
print("kick committed")

# hats: closed 16ths (skipping the open-hat slot) + accented offbeat open
lay_L[:] = 0.0
lay_R[:] = 0.0
CH_GAINS = [0.50, 0.25, 0.0, 0.30]       # per 16th within each beat
for b in range(B_STOP):
    if b < B_HATS or B_BREAK <= b < B_BREAK2:
        continue
    g = 0.6 if B_BREAK2 <= b < B_MAIN else 1.0
    for beat in range(4):
        for s in range(4):
            if CH_GAINS[s] == 0.0:
                continue
            gg = g * CH_GAINS[s]
            add_at(lay_L, CHAT, bar_t(b, beat + s * 0.25), gg * 0.9)
            add_at(lay_R, CHAT, bar_t(b, beat + s * 0.25), gg)
        if b >= B_OPEN:
            add_at(lay_L, OHAT, bar_t(b, beat + 0.5), g)
            add_at(lay_R, OHAT, bar_t(b, beat + 0.5), g * 0.85)
commit(lay_L, lay_R, 0.085)
print("hats committed")

# ride: the main sections only, straight 8ths, accent on the beat
lay_L[:] = 0.0
lay_R[:] = 0.0
for b in range(B_MAIN, B_DECON):
    for e in range(8):
        g = 0.75 if e % 2 == 0 else 0.5
        add_at(lay_L, RIDE, bar_t(b, e * 0.5), g)
        add_at(lay_R, RIDE, bar_t(b, e * 0.5), g * 0.8)
commit(lay_L, lay_R, 0.065)
print("ride committed")

# claps: sparse, on 2 and 4
lay_L[:] = 0.0
lay_R[:] = 0.0
for b in range(B_STOP):
    if not (B_LAYER <= b < B_BREAK or B_MAIN <= b < B_DECON2):
        continue
    for beat in (1, 3):
        p = 0.42 if beat == 1 else 0.58
        add_at(lay_L, CLAP, bar_t(b, beat), np.cos(p * np.pi / 2))
        add_at(lay_R, CLAP, bar_t(b, beat), np.sin(p * np.pi / 2))
commit(lay_L, lay_R, 0.10)
print("claps committed")

# shaker: subtle 16th motion
lay_L[:] = 0.0
lay_R[:] = 0.0
SH_GAINS = [0.7, 0.3, 0.5, 0.3]
for b in range(B_OUT):
    if b < B_PERC or B_BREAK <= b < B_MAIN:
        continue
    for beat in range(4):
        for s in range(4):
            gg = SH_GAINS[s]
            add_at(lay_L, SHAKER, bar_t(b, beat + s * 0.25), gg * 0.7)
            add_at(lay_R, SHAKER, bar_t(b, beat + s * 0.25), gg)
commit(lay_L, lay_R, 0.045)
print("shaker committed")

# crashes at phrase boundaries; reverse cymbals lean INTO the big entries
lay_L[:] = 0.0
lay_R[:] = 0.0
for b, g in [(B_THEME, 0.7), (B_LAYER, 0.8), (B_LAYER2, 0.6), (B_BREAK, 0.8),
             (B_MAIN, 1.0), (B_MAIN2, 0.7), (B_MAIN3, 0.7), (B_DECON, 0.8),
             (B_DECON2, 0.6), (B_OUT, 0.6)]:
    add_at(lay_L, CRASH, bar_t(b), g * 0.9)
    add_at(lay_R, CRASH, bar_t(b), g)
for b in (B_THEME, B_MAIN):                       # ends exactly on the bar
    add_at(lay_L, RCYM, bar_t(b) - 1.5, 0.8)
    add_at(lay_R, RCYM, bar_t(b) - 1.5, 0.7)
commit(lay_L, lay_R, 0.055)
print("crashes committed")


# ---------------------------------------------------------------- bass
# Rolling early-90s octave bass: root/octave 16ths, hypnotic, rooted on
# the tonic except where the theme's harmony pulls it. Slightly resonant
# lowpass; the cutoff is the transition tool (filter sweeps, not fades).

bass_cache = {}


def bass_note(midi, cutoff, dur=STEP * 0.92):
    key = (midi, int(cutoff // 60))
    if key in bass_cache:
        return bass_cache[key]
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    for k in range(1, min(24, int(3000 / f)) + 1):
        x += np.sin(2 * np.pi * k * f * td) / k
    sos_lp = signal.butter(2, cutoff, "low", fs=SR, output="sos")
    y = signal.sosfilt(sos_lp, x)
    bpk, apk = signal.iirpeak(cutoff, Q=3.5, fs=SR)
    y = y + 0.7 * signal.lfilter(bpk, apk, y)
    y = np.tanh(1.5 * y)
    y *= (1 - np.exp(-td / 0.003)) * np.clip((dur - td) / 0.02, 0, 1)
    y /= np.max(np.abs(y)) + 1e-12
    bass_cache[key] = y
    return y


def bass_cutoff(b):
    if b < B_THEME:
        return 290.0                                  # creeps in dark
    if b < B_LAYER:
        return 360.0
    if b < B_BREAK:                                   # opened up, breathing
        return 540.0 + 80.0 * np.sin(2 * np.pi * (b - B_LAYER) / 16)
    if b < B_DECON:
        return 580.0 + 80.0 * np.sin(2 * np.pi * (b - B_MAIN) / 16)
    if b < B_DECON2:
        return 540.0
    if b < B_OUT:                                     # sweeping back down
        return 540.0 - 200.0 * (b - B_DECON2) / (B_OUT - B_DECON2)
    return 320.0


def bass_root(b):
    if B_THEME <= b < B_DECON2:
        return PHRASE_ROOTS[(b - B_THEME) % 8] - 12   # follow the harmony
    return 31                                         # tonic pedal (G1)


BASS_PAT = [(0, 0, 0.70), (1, 12, 0.95), (2, 0, 0.80), (3, 12, 0.90)]

lay_L[:] = 0.0
lay_R[:] = 0.0
for b in range(B_BASSOUT):
    if b < B_BASSIN or B_BREAK <= b < B_MAIN:
        continue
    root = bass_root(b)
    cut = bass_cutoff(b)
    g = 0.75 if b < B_LAYER else 1.0
    for beat in range(4):
        for s, off, gg in BASS_PAT:
            x = bass_note(root + off, cut)
            add_at(lay_L, x, bar_t(b, beat + s * 0.25), g * gg)
            add_at(lay_R, x, bar_t(b, beat + s * 0.25), g * gg)
commit(lay_L, lay_R, 0.30)
print(f"bass committed ({len(bass_cache)} cached notes)")


# ---------------------------------------------------------------- piano
# The centerpiece: a slightly artificial M1-era piano — inharmonic
# partials, two detuned strings per note, a touch of hammer noise — under
# a LONG dark hall. Stately, funereal, very wet.

piano_cache = {}


def piano_note(midi, dur):
    key = (midi, round(dur, 2))
    if key in piano_cache:
        return piano_cache[key]
    f = midi_to_hz(midi)
    n = int((dur + 0.8) * SR)
    td = np.arange(n) / SR
    out = np.zeros(n)
    B_inh = 0.00035
    for k in range(1, min(14, int(8500 / f)) + 1):
        fk = f * k * np.sqrt(1 + B_inh * k * k)
        dec = 0.9 + 0.45 * k + f * 0.0012
        g = 1.0 / k ** 1.25
        for det in (0.9994, 1.0006):
            out += g * np.sin(2 * np.pi * fk * det * td +
                              rng.uniform(0, 2 * np.pi)) * np.exp(-td * dec)
    sos_h = signal.butter(2, [1500, 4000], "bandpass", fs=SR, output="sos")
    hammer = signal.sosfilt(sos_h, rng.standard_normal(n)) * np.exp(-td * 350)
    hammer /= np.max(np.abs(hammer)) + 1e-12
    out += 0.16 * hammer
    env = (1 - np.exp(-td / 0.0015)) * np.clip((dur + 0.35 - td) / 0.35, 0, 1)
    x = out * env
    piano_cache[key] = x / (np.max(np.abs(x)) + 1e-12)
    return piano_cache[key]


lay_L = np.zeros(N)
lay_R = np.zeros(N)


def place_note(midi, t0, dur, gain):
    x = piano_note(midi, dur)
    p = np.clip(0.5 + (midi - 67) * 0.015, 0.2, 0.8)
    add_at(lay_L, x, t0, gain * np.cos(p * np.pi / 2))
    add_at(lay_R, x, t0, gain * np.sin(p * np.pi / 2))


def place_theme(bar0, gain, lh=True, oct_double=False):
    t0 = bar_t(bar0)
    for beat, m, d, g in THEME_RH:
        place_note(m, t0 + beat * BEAT, d * BEAT, gain * g)
        if oct_double:
            place_note(m + 12, t0 + beat * BEAT, d * BEAT, gain * g * 0.5)
    if lh:
        for beat, m, d, g in THEME_LH:
            place_note(m, t0 + beat * BEAT, d * BEAT, gain * g * 0.8)


place_theme(B_THEME, 0.80, lh=False)                  # first entry: RH alone
place_theme(B_THEME + 8, 0.85)
for b0 in (B_LAYER, B_LAYER + 8):
    place_theme(b0, 0.90)
for b0 in (B_LAYER2, B_LAYER2 + 8):
    place_theme(b0, 0.90, oct_double=True)
for b0 in (B_BREAK, B_BREAK + 8):                     # the piano carries it
    place_theme(b0, 1.00)
for b0 in range(B_MAIN, B_DECON, 8):
    place_theme(b0, 0.95, oct_double=True)
place_theme(B_DECON, 0.80)
place_theme(B_DECON + 8, 0.70, lh=False)              # thinning out

# the "Transcription" coda: solo piano fragment + final G minor chord
t0 = bar_t(B_STOP)
for beat, m, d, g in THEME_RH[:6]:
    place_note(m, t0 + beat * BEAT, d * BEAT, 0.85 * g)
for m in (43, 55, 62, 67, 74):
    place_note(m, bar_t(B_STOP + 2), 6.0, 0.9)

lay_L = reverb(lay_L, IR_L, wet=0.50)
lay_R = reverb(lay_R, IR_R, wet=0.50)
commit(lay_L, lay_R, 0.30)
print(f"piano committed ({len(piano_cache)} cached notes)")


# ---------------------------------------------------------------- pads
# Dark slow-attack string/choir-adjacent pads — they underpin the intro
# creep, the breakdown, the main section and the deconstruction.

def pad_chord(chord, dur, attack=2.5, release=3.0):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    out_L = np.zeros(n)
    out_R = np.zeros(n)
    for m in chord:
        f = midi_to_hz(m)
        amp = 0.8 + 0.2 * np.sin(2 * np.pi * rng.uniform(0.02, 0.06) * tt +
                                 rng.uniform(0, 2 * np.pi))
        for det, gL, gR in [(0.9993, 1.0, 0.65), (1.0007, 0.65, 1.0)]:
            ph = 2 * np.pi * f * det * tt + rng.uniform(0, 2 * np.pi)
            v = (np.sin(ph) + 0.30 * np.sin(2 * ph)) * amp
            out_L += gL * v
            out_R += gR * v
    env = np.minimum(np.clip(tt / attack, 0, 1) ** 1.5,
                     np.clip((dur - tt) / release, 0, 1))
    sos_d = signal.butter(2, 1500, "low", fs=SR, output="sos")
    out_L = signal.sosfilt(sos_d, out_L * env)
    out_R = signal.sosfilt(sos_d, out_R * env)
    peak = max(np.max(np.abs(out_L)), np.max(np.abs(out_R)), 1e-12)
    return out_L / peak, out_R / peak


lay_L = np.zeros(N)
lay_R = np.zeros(N)


def place_pads(bar0, n_bars, gain, bars_per_chord=2):
    for i in range(n_bars // bars_per_chord):
        chord = PAD_CHORDS[i % len(PAD_CHORDS)]
        pL, pR = pad_chord(chord, bars_per_chord * BAR + 2.0,
                           attack=1.2, release=2.0)
        add_at(lay_L, pL, bar_t(bar0 + i * bars_per_chord), gain)
        add_at(lay_R, pR, bar_t(bar0 + i * bars_per_chord), gain)


# intro creep: one long dark Gm swell
pL, pR = pad_chord((31, 43, 50, 55, 58), (B_THEME - B_PERC) * BAR + 4.0,
                   attack=9.0, release=5.0)
add_at(lay_L, pL, bar_t(B_PERC), 0.8)
add_at(lay_R, pR, bar_t(B_PERC), 0.8)
place_pads(B_BREAK, 16, 1.0)                          # the breakdown bed
place_pads(B_MAIN, 48, 0.45)                          # under the climax
place_pads(B_DECON2, 16, 0.8)                         # the return
# outro residue + coda
pL, pR = pad_chord((43, 50, 55, 58), (B_STOP - B_OUT) * BAR + 8.0,
                   attack=6.0, release=8.0)
add_at(lay_L, pL, bar_t(B_OUT), 0.55)
add_at(lay_R, pR, bar_t(B_OUT), 0.55)

lay_L = reverb(lay_L, IR_L, wet=0.55)
lay_R = reverb(lay_R, IR_R, wet=0.55)
commit(lay_L, lay_R, 0.16)
print("pads committed")


# ---------------------------------------------------------------- lead
# The signature move: a warm detuned analog lead (saw stack, NOT a
# supersaw) soaring over the piano theme through the whole main section,
# with a tempo-synced dotted-8th ping-pong delay.

def lead_phrase():
    total = sum(d for _, d in LEAD_NOTES) * BEAT
    n = int((total + 2.5) * SR)
    tt = np.arange(n) / SR
    f_curve = glide_curve([(m, d * BEAT) for m, d in LEAD_NOTES], n, tau=0.06)
    vib = 1.0 + 0.0035 * np.sin(2 * np.pi * 5.5 * tt) * np.clip(tt / 1.5, 0, 1)
    K = max(3, int(7000 / np.max(f_curve)))

    def saw(det):
        ph = 2 * np.pi * np.cumsum(f_curve * det * vib) / SR
        v = np.zeros(n)
        for k in range(1, K + 1):
            v += np.sin(k * ph) / k
        return v

    base = saw(1.0)
    vL = base + saw(0.9965)
    vR = base + saw(1.0038)
    env = np.minimum(np.clip(tt / 0.4, 0, 1),
                     np.clip((total + 0.8 - tt) / 1.5, 0, 1))
    sos_w = signal.butter(2, 4000, "low", fs=SR, output="sos")
    vL = np.tanh(1.2 * signal.sosfilt(sos_w, vL * env))
    vR = np.tanh(1.2 * signal.sosfilt(sos_w, vR * env))
    peak = max(np.max(np.abs(vL)), np.max(np.abs(vR)), 1e-12)
    return vL / peak, vR / peak


LEAD_L, LEAD_R = lead_phrase()
LEAD_HI_L = None

lay_L = np.zeros(N)
lay_R = np.zeros(N)
DELAY = 0.75 * BEAT                                   # dotted 8th
for b0 in range(B_MAIN, B_DECON, 8):
    t0 = bar_t(b0) + 2 * BEAT                         # phrase starts beat 2
    g = 1.0
    add_at(lay_L, LEAD_L, t0, g)
    add_at(lay_R, LEAD_R, t0, g)
    add_at(lay_L, LEAD_R, t0 + DELAY, g * 0.28)       # ping-pong echoes
    add_at(lay_R, LEAD_L, t0 + DELAY, g * 0.28)
    add_at(lay_L, LEAD_L, t0 + 2 * DELAY, g * 0.13)
    add_at(lay_R, LEAD_R, t0 + 2 * DELAY, g * 0.13)
    if b0 >= B_MAIN2:                                 # octave shimmer wave
        if LEAD_HI_L is None:
            hi = [(m + 12, d) for m, d in LEAD_NOTES]
            save = LEAD_NOTES[:]
            LEAD_NOTES[:] = hi
            LEAD_HI_L, LEAD_HI_R = lead_phrase()
            LEAD_NOTES[:] = save
        add_at(lay_L, LEAD_HI_L, t0, 0.30)
        add_at(lay_R, LEAD_HI_R, t0, 0.30)
lay_L = reverb(lay_L, IR_L, wet=0.40)
lay_R = reverb(lay_R, IR_R, wet=0.40)
commit(lay_L, lay_R, 0.24)
print("lead committed")


# ---------------------------------------------------------------- stab
# The "subtle filtered element added every 16 bars": a gated offbeat
# G-minor chord stab, lowpassed dark.

def make_stab():
    dur = STEP * 1.6
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    for m in (55, 58, 62):
        f = midi_to_hz(m)
        for k in range(1, min(12, int(2500 / f)) + 1):
            x += np.sin(2 * np.pi * k * f * td + rng.uniform(0, 2 * np.pi)) / k
    sos_s = signal.butter(2, 900, "low", fs=SR, output="sos")
    x = signal.sosfilt(sos_s, x)
    x *= (1 - np.exp(-td / 0.002)) * np.clip((dur - td) / 0.05, 0, 1)
    return x / (np.max(np.abs(x)) + 1e-12)


STAB = make_stab()

lay_L = np.zeros(N)
lay_R = np.zeros(N)
for b in range(B_STOP):
    if not (B_LAYER2 <= b < B_BREAK or B_MAIN3 <= b < B_DECON):
        continue
    for beat in range(4):
        p = 0.35 if beat % 2 == 0 else 0.65
        add_at(lay_L, STAB, bar_t(b, beat + 0.5), np.cos(p * np.pi / 2))
        add_at(lay_R, STAB, bar_t(b, beat + 0.5), np.sin(p * np.pi / 2))
lay_L = reverb(lay_L, IR_L, wet=0.30)
lay_R = reverb(lay_R, IR_R, wet=0.30)
commit(lay_L, lay_R, 0.09)
print("stab committed")


# ---------------------------------------------------------------- air
# Faint dark atmosphere so the intro/outro aren't clinically empty.

sos_air = signal.butter(4, [150, 1200], "bandpass", fs=SR, output="sos")
air = signal.sosfilt(sos_air, rng.standard_normal(N))
air /= np.max(np.abs(air))
air_env = slow_noise(0.05, 0.4, 1.0)
edge = np.minimum(np.clip((bar_t(B_THEME) - t) / 10.0, 0, 1) +
                  np.clip((t - bar_t(B_DECON2)) / 25.0, 0, 1), 1.0)
commit(air * air_env * edge, air * air_env[::-1] * edge, 0.05)
print("air committed")


# ---------------------------------------------------------------- master

fade(mix_L, fade_in=0.4, fade_out=9.0)
fade(mix_R, fade_in=0.4, fade_out=9.0)

peak = max(np.max(np.abs(mix_L)), np.max(np.abs(mix_R)))
mix_L = mix_L / peak * 0.88
mix_R = mix_R / peak * 0.88

stereo = np.empty((N, 2))
stereo[:, 0] = mix_L
stereo[:, 1] = mix_R
pcm = (stereo * 32767.0).astype(np.int16)

OUT_DIR = "/workspace/music"
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, "nachtkind.wav")
with wave.open(OUT, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())

print(f"\nCreated: {os.path.abspath(OUT)}")
print(f"Duration: {N / SR:.1f} s  |  {SR} Hz stereo, 16-bit PCM  |  {BPM:.0f} BPM, G minor")

MP3 = os.path.join(OUT_DIR, "nachtkind.mp3")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", OUT,
                "-vn", "-ar", "44100", "-ac", "2", "-b:a", "192k", MP3],
               check=True)
print(f"Created: {os.path.abspath(MP3)}  (192k mp3)")

print("\nSection map:")
SECTIONS = [("dry kick intro", 0), ("closed hats", B_HATS),
            ("open hat", B_OPEN), ("shaker + pad creep", B_PERC),
            ("dark bass in", B_BASSIN), ("PIANO THEME enters", B_THEME),
            ("layering: full bass + claps", B_LAYER),
            ("+ stab, octave piano", B_LAYER2),
            ("BREAKDOWN: piano + pads", B_BREAK),
            ("kick walks back in", B_BREAK2),
            ("MAIN: lead over piano", B_MAIN),
            ("+ octave shimmer", B_MAIN2), ("+ stab returns", B_MAIN3),
            ("deconstruction", B_DECON), ("piano exits, pads return", B_DECON2),
            ("DJ outro", B_OUT), ("bass exits", B_BASSOUT),
            ("kick stops; piano coda", B_STOP)]
for name, b in SECTIONS:
    print(f"  {bar_t(b):6.1f} s  bar {b:3d}  {name}")
print(f"  {DURATION:6.1f} s  end")

print("\nPer-section RMS (the main section should be the loudest):")
for (name, b0), (_, b1) in zip(SECTIONS, SECTIONS[1:] + [("end", None)]):
    i0 = int(bar_t(b0) * SR)
    i1 = int(bar_t(b1) * SR) if b1 is not None else N
    rms = np.sqrt(np.mean(mix_L[i0:i1] ** 2 + mix_R[i0:i1] ** 2) / 2)
    print(f"  {name:32s} {rms:.3f}")
