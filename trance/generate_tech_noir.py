#!/usr/bin/env python3
"""
generate_tech_noir.py — "Tech Noir" (~4:25). Early-80s dark analog synth
film score in the style of Brad Fiedel's Terminator theme (1984): not
dance music — an industrial-tinged machine ostinato in 13/16 time
(grouped 3+3+3+2+2, the famous "herky-jerky" limp) at ~100 BPM quarter
pulse, D minor. Prophet-style punchy saw bass pulse, anvil clangs and
gated metallic drum slams (no hi-hats, no four-on-the-floor), a brassy
Oberheim-style five-note fanfare motif, and a mournful lyrical
counter-theme floating over the relentless rhythm. Big dark plate
reverb on the metal, dry forward bass, no filter sweeps, no risers,
no sidechain. Ends cold.

  0:00  Isolated anvil clangs in empty space; a dark pad creeps in.
  0:20  THE OSTINATO — the 13/16 bass pulse + gated slams lock in,
        machine-like, and never stop.
  0:51  Main motif: the stark five-note brass fanfare, repeated and
        varied (alternate statements end hollow, a fifth below).
  1:42  Lyrical middle — the mournful love theme (i–bVI–bVII) floats
        over the unchanged machine; slams pull back, pads warm.
  2:53  Return / intensification: the motif comes back with octave
        doubling; clangs every 2 bars, metal taps, slams doubled.
  3:52  Outro: layers strip to the bare pulse and metallic hits.
  4:19  One last slam and anvil ring out. Cold stop.

Harmony: static modal D minor — tonic pedal under the motif, i–bVI–bVII
under the love theme. Instrumental, no vocals.

Output: /workspace/music/tech_noir.wav + tech_noir.mp3 (192k, ffmpeg).
"""

import os
import subprocess
import wave
import numpy as np
from scipy import signal

SR = 44100
DURATION = 265.0
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
B_OST = 10       # the ostinato locks in            (~0:20)
B_THEME = 26     # main motif statement             (~0:51)
B_LYR = 52       # lyrical middle / love theme      (~1:42)
B_RET = 88       # return / intensification         (~2:53)
B_OUT = 118      # strip back to pulse + metal      (~3:52)
B_END = 132      # final hit, cold ring-out         (~4:19)


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
# D minor, static and modal. The motif: five long declamatory notes,
# stepwise + small leaps, leaning on 1, b3, b7 — a fanfare for a machine.
# Durations are in sixteenths; each statement is 3 bars + 1 bar of rest.

MOTIF_A = [(62, 10), (65, 3), (64, 10), (60, 3), (62, 13)]   # D F E C D
MOTIF_B = [(62, 10), (65, 3), (64, 10), (60, 3), (57, 13)]   # ...ends on A3

# the love theme: lyrical, descending, diatonic — 8 bars over i–bVI–bVII–i
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

PAD_DM = (50, 53, 57, 62)          # D F A D
PAD_BB = (46, 50, 53, 58)          # Bb D F Bb
PAD_C = (48, 52, 55, 60)           # C E G C
LOVE_PADS = [PAD_DM, PAD_BB, PAD_C, PAD_DM]   # 2 bars each across the phrase


# ----------------------------------------------------------- bass pulse
# The machine's heartbeat: a punchy Prophet-style saw on D, quick decay,
# double-hit "DUN-dun" figures riding the 3+3+3+2+2 grouping. Dry and
# forward; minimal pitch movement — a limping heartbeat, not a groove.

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
    if b < B_THEME:
        return 0.80
    if b < B_LYR:
        return 0.90
    if b < B_RET:
        return 0.75                  # the love theme floats; pulse recedes
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
    if B_RET <= b < B_OUT:                                # octave-up flick
        x = bass_hit(50)
        add_at(lay_L, x, bar_t(b, 11), g * 0.45)
        add_at(lay_R, x, bar_t(b, 11), g * 0.45)
commit(lay_L, lay_R, 0.30)
print(f"bass pulse committed ({len(bass_cache)} cached notes)")


# ----------------------------------------------------- metal percussion
# No drum kit. Anvil clangs (inharmonic partials + strike noise) under a
# huge dark plate, and gated 80s drum slams (the gate is baked into the
# sample: reverb-dense body cut dead at 140 ms).

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
    # the "reverb" the gate will cut: dense noise sustaining, then dead
    x = body + 0.55 * burst * np.exp(-td * 16.0) + 0.30 * burst * np.exp(-td * 3.0)
    gate = np.clip((0.140 - td) / 0.025, 0, 1)            # hard 80s gate
    x *= (1 - np.exp(-td / 0.0015)) * np.maximum(gate, np.exp(-td * 28.0) * 0.0)
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
    if b < B_THEME:
        hits = [(0, 0.80)]
    elif b < B_LYR:
        hits = [(0, 0.90)] + ([(6, 0.50)] if b % 4 == 2 else [])
    elif b < B_RET:
        hits = [(0, 0.60)]
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

# --- anvils: isolated in the intro, phrase punctuation later
lay_L[:] = 0.0
lay_R[:] = 0.0
for t0, g, p in [(1.2, 1.0, 0.30), (5.1, 0.80, 0.68), (9.3, 0.90, 0.42),
                 (14.0, 0.70, 0.75), (17.6, 0.85, 0.55)]:
    add_at(lay_L, ANVIL, t0, g * np.cos(p * np.pi / 2))
    add_at(lay_R, ANVIL, t0, g * np.sin(p * np.pi / 2))
anvil_hits = []
for b in range(12, B_THEME, 4):
    anvil_hits.append((b, 0, 0.70))
for b in range(B_THEME, B_LYR, 8):
    anvil_hits.append((b, 0, 0.80))
    anvil_hits.append((b + 6, 9, 0.45))
anvil_hits += [(B_LYR, 0, 0.60), (B_LYR + 16, 0, 0.60)]
for b in range(B_RET, B_OUT, 2):                          # insistent now
    anvil_hits.append((b, 0, 0.80))
    if b % 4 == 1:
        anvil_hits.append((b, 6, 0.60))
for b in range(B_OUT + 2, B_END, 4):
    anvil_hits.append((b, 0, 0.80))
anvil_hits.append((B_END, 0, 1.00))                       # the cold ring-out
for b, s, g in anvil_hits:
    p = 0.38 if (b // 2) % 2 == 0 else 0.62
    add_at(lay_L, ANVIL, bar_t(b, s), g * np.cos(p * np.pi / 2))
    add_at(lay_R, ANVIL, bar_t(b, s), g * np.sin(p * np.pi / 2))
lay_L = reverb(lay_L, IR_L, wet=0.60)
lay_R = reverb(lay_R, IR_R, wet=0.60)
commit(lay_L, lay_R, 0.16)
print("anvils committed")

# --- metal taps: only in the intensification, answering L/R
lay_L = np.zeros(N)
lay_R = np.zeros(N)
for b in range(B_RET, B_OUT):
    add_at(lay_L, TAP, bar_t(b, 3), 0.55)
    add_at(lay_R, TAP, bar_t(b, 3), 0.25)
    add_at(lay_L, TAP, bar_t(b, 9), 0.25)
    add_at(lay_R, TAP, bar_t(b, 9), 0.50)
lay_L = reverb(lay_L, IR_L, wet=0.45)
lay_R = reverb(lay_R, IR_R, wet=0.45)
commit(lay_L, lay_R, 0.05)
print("taps committed")


# ---------------------------------------------------------- brass motif
# Oberheim-style poly brass: three detuned saws, a pitch scoop into each
# phrase, dark lowpass, gentle chorus width via reciprocal detune split.

def brass_phrase(notes, lowpass=2200.0):
    total = sum(d for _, d in notes) * SIXT
    n = int((total + 2.0) * SR)
    tt = np.arange(n) / SR
    f_curve = glide_curve([(m, d * SIXT) for m, d in notes], n, tau=0.045)
    f_curve *= 1.0 - 0.035 * np.exp(-tt / 0.09)           # the scoop
    vib = 1.0 + 0.0028 * np.sin(2 * np.pi * 4.7 * tt) * np.clip(tt / 1.2, 0, 1)
    K = max(3, int(6500 / np.max(f_curve)))

    def saw(det):
        ph = 2 * np.pi * np.cumsum(f_curve * det * vib) / SR
        v = np.zeros(n)
        for k in range(1, K + 1):
            v += np.sin(k * ph) / k
        return v

    base = saw(1.0)
    vL = base + saw(0.9955)
    vR = base + saw(1.0045)
    env = np.minimum(np.clip(tt / 0.12, 0, 1),
                     np.clip((total + 0.30 - tt) / 0.8, 0, 1))
    sos_w = signal.butter(2, lowpass, "low", fs=SR, output="sos")
    vL = np.tanh(1.3 * signal.sosfilt(sos_w, vL * env))
    vR = np.tanh(1.3 * signal.sosfilt(sos_w, vR * env))
    peak = max(np.max(np.abs(vL)), np.max(np.abs(vR)), 1e-12)
    return vL / peak, vR / peak


BRASS_A = brass_phrase(MOTIF_A)
BRASS_B = brass_phrase(MOTIF_B)
BRASS_A_HI = brass_phrase([(m + 12, d) for m, d in MOTIF_A], lowpass=3200.0)
BRASS_B_HI = brass_phrase([(m + 12, d) for m, d in MOTIF_B], lowpass=3200.0)

lay_L = np.zeros(N)
lay_R = np.zeros(N)
statements = [(B_THEME + 4 * i, i) for i in range(6)]            # 0:51–1:42
statements += [(B_RET + 4 * i, i) for i in range(7)]             # 2:53–3:48
for b0, i in statements:
    xL, xR = (BRASS_A if i % 2 == 0 else BRASS_B)
    g = 1.0 if b0 < B_RET else 1.05
    add_at(lay_L, xL, bar_t(b0), g)
    add_at(lay_R, xR, bar_t(b0), g)
    if b0 >= B_RET:                                       # octave doubling
        hL, hR = (BRASS_A_HI if i % 2 == 0 else BRASS_B_HI)
        add_at(lay_L, hL, bar_t(b0), 0.38)
        add_at(lay_R, hR, bar_t(b0), 0.38)
lay_L = reverb(lay_L, IR_L, wet=0.35)
lay_R = reverb(lay_R, IR_R, wet=0.35)
commit(lay_L, lay_R, 0.26)
print("brass motif committed")


# ----------------------------------------------------------- love theme
# The humanizing counterweight: a plaintive, nearly-pure lead floating
# over the machine. Blooming vibrato, very wet.

def love_phrase():
    total = sum(d for _, d in LOVE_NOTES) * SIXT
    n = int((total + 2.5) * SR)
    tt = np.arange(n) / SR
    f_curve = glide_curve([(m, d * SIXT) for m, d in LOVE_NOTES], n, tau=0.07)
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


LOVE = love_phrase()

lay_L = np.zeros(N)
lay_R = np.zeros(N)
for i, b0 in enumerate(range(B_LYR, B_LYR + 32, 8)):      # four statements
    g = 0.85 if i == 0 else 1.0
    t0 = bar_t(b0)
    add_at(lay_L, LOVE, t0, g * 0.92)
    add_at(lay_R, LOVE, t0, g)
    add_at(lay_L, LOVE, t0 + 2 * SIXT, g * 0.22)          # soft echo
    add_at(lay_R, LOVE, t0 + 2 * SIXT, g * 0.18)
lay_L = reverb(lay_L, IR_L, wet=0.55)
lay_R = reverb(lay_R, IR_R, wet=0.55)
commit(lay_L, lay_R, 0.22)
print("love theme committed")


# ----------------------------------------------------------------- pads
# Cold, dark, low-passed analog strings — distant, filling the back.

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

# intro creep: one long cold Dm swell out of the dark
pL, pR = pad_chord((38, 45, 50, 53), (B_OST + 6) * BAR,
                   attack=8.0, release=4.0)
add_at(lay_L, pL, bar_t(2), 0.85)
add_at(lay_R, pR, bar_t(2), 0.85)

# faint pedal bed under the motif sections
for b0 in range(B_THEME, B_LYR, 8):
    pL, pR = pad_chord(PAD_DM, 8 * BAR + 2.0, attack=3.0, release=3.0)
    add_at(lay_L, pL, bar_t(b0), 0.40)
    add_at(lay_R, pR, bar_t(b0), 0.40)

# the love theme's harmony, 2 bars per chord across each 8-bar phrase
for b0 in range(B_LYR, B_LYR + 32, 2):
    chord = LOVE_PADS[((b0 - B_LYR) // 2) % 4]
    pL, pR = pad_chord(chord, 2 * BAR + 1.5, attack=0.9, release=1.6)
    add_at(lay_L, pL, bar_t(b0), 0.95)
    add_at(lay_R, pR, bar_t(b0), 0.95)
# the machine grinds on alone for 4 bars before the return
for b0 in range(B_LYR + 32, B_RET, 2):
    pL, pR = pad_chord(PAD_DM, 2 * BAR + 1.5, attack=0.9, release=1.6)
    add_at(lay_L, pL, bar_t(b0), 0.55)
    add_at(lay_R, pR, bar_t(b0), 0.55)

# dark pedal under the intensification; nothing in the outro — cold
for b0 in range(B_RET, B_OUT, 8):
    pL, pR = pad_chord((38, 50, 53, 57), 8 * BAR + 2.0,
                       attack=3.0, release=3.0)
    add_at(lay_L, pL, bar_t(b0), 0.50)
    add_at(lay_R, pR, bar_t(b0), 0.50)

lay_L = reverb(lay_L, IR_L, wet=0.50)
lay_R = reverb(lay_R, IR_R, wet=0.50)
commit(lay_L, lay_R, 0.13)
print("pads committed")


# ------------------------------------------------------------------ air
# A faint cold-room noise floor so the negative space isn't digital-dead.

sos_air = signal.butter(4, [200, 900], "bandpass", fs=SR, output="sos")
air = signal.sosfilt(sos_air, rng.standard_normal(N))
air /= np.max(np.abs(air))
air_env = slow_noise(0.05, 0.5, 1.0)
edge = np.minimum(np.clip((bar_t(B_THEME) - t) / 12.0, 0, 1) +
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
OUT = os.path.join(OUT_DIR, "tech_noir.wav")
with wave.open(OUT, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())

print(f"\nCreated: {os.path.abspath(OUT)}")
print(f"Duration: {N / SR:.1f} s  |  {SR} Hz stereo, 16-bit PCM  |  "
      f"13/16 at ~99.5 BPM quarter pulse, D minor")

MP3 = os.path.join(OUT_DIR, "tech_noir.mp3")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", OUT,
                "-vn", "-ar", "44100", "-ac", "2", "-b:a", "192k", MP3],
               check=True)
print(f"Created: {os.path.abspath(MP3)}  (192k mp3)")

print("\nSection map:")
SECTIONS = [("anvils in space, pad creep", 0),
            ("OSTINATO locks in (13/16)", B_OST),
            ("main motif statements", B_THEME),
            ("lyrical middle: love theme", B_LYR),
            ("return / intensification", B_RET),
            ("outro: bare pulse + metal", B_OUT),
            ("final hit, cold ring-out", B_END)]
for name, b in SECTIONS:
    print(f"  {bar_t(b):6.1f} s  bar {b:3d}  {name}")
print(f"  {DURATION:6.1f} s  end")

print("\nPer-section RMS (intensification should be the loudest):")
for (name, b0), (_, b1) in zip(SECTIONS, SECTIONS[1:] + [("end", None)]):
    i0 = int(bar_t(b0) * SR)
    i1 = int(bar_t(b1) * SR) if b1 is not None else N
    rms = np.sqrt(np.mean(mix_L[i0:i1] ** 2 + mix_R[i0:i1] ** 2) / 2)
    print(f"  {name:32s} {rms:.3f}")
