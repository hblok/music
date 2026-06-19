#!/usr/bin/env python3
"""
jihad.py — "Jihad" (~5:55). Relentless Dune war psy-trance.

A direct energy successor to generate_fall_of_arrakeen.py: same standalone
legacy architecture, same room-shake low end, but weaponised into the holy war
Paul foresaw. The pulse never fully stops; the Sardaukar chant is chopped into
rhythm and carries every recharge. The piece escalates through three waves,
then sprints, then hard-cuts mid-fury.

Output: /workspace/music/jihad.wav (stereo, 44100 Hz, 16-bit).
"""

import os
import wave
import numpy as np
from scipy import signal

SR = 44100
DURATION = 355.0
N = int(SR * DURATION)
t = np.arange(N) / SR

rng = np.random.default_rng(10191)   # Atreides arrival year; the war follows

BPM = 152.0
BEAT = 60.0 / BPM
BAR = BEAT * 4
STEP = BEAT / 4
GRID0 = 10.0


def bar_t(b, beat=0.0):
    return GRID0 + b * BAR + beat * BEAT


# Section boundaries, in bars. The plan's three waves + sprint + hard cut.
B_GATHER = 0
B_MUSTER = 12
B_RISE1 = 24
B_DROP1 = 32
B_RECHARGE1 = 72
B_RISE2 = 80
B_DROP2 = 88
B_RECHARGE2 = 136
B_RISE3 = 144
B_DROP3 = 152
B_SPRINT = 200
B_CUT = 216

RECHARGES = set(range(B_RECHARGE1, B_RISE2)) | set(range(B_RECHARGE2, B_RISE3))
DIP1 = set(range(56, 60))
DIP2A = set(range(112, 116))
DIP2B = set(range(124, 128))
DIP3A = set(range(172, 176))
DIP3B = set(range(188, 192))
WAR_DIPS = DIP1 | DIP2A | DIP2B | DIP3A | DIP3B
ALL_DIPS = WAR_DIPS | RECHARGES
N_LAYERS = 0

THEME_JIHAD = [
    (62, 1.5), (62, 0.5), (63, 1.0), (66, 1.0),
    (67, 1.0), (66, 1.0), (63, 1.0), (62, 1.0),
    (69, 1.5), (70, 0.5), (73, 1.0), (74, 1.0),
    (73, 1.0), (74, 2.0), (62, 1.0),
]
HORN_CALL = [(50, 1.2), (51, 0.4), (54, 0.6), (50, 2.0)]
RIFF_HOLY1 = [
    (38, 1, None), (None, 0, None), (38, 0, None), (39, 1, 42),
    (42, 0, None), (None, 0, None), (45, 0, None), (None, 0, None),
    (49, 1, 50), (50, 0, None), (None, 0, None), (38, 0, None),
    (46, 0, None), (None, 0, None), (49, 1, 50), (38, 0, None),
]
RIFF_HOLY2 = [
    (62, 1, None), (62, 0, None), (63, 0, 66), (66, 0, None),
    (None, 0, None), (69, 0, None), (70, 1, None), (69, 0, None),
    (73, 1, 74), (74, 0, None), (None, 0, None), (66, 0, None),
    (63, 0, None), (61, 0, 62), (62, 1, None), (None, 0, None),
]


# ---------------------------------------------------------------- helpers

def midi_to_hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def fade_in_only(x, fade_in=5.0):
    ni = int(fade_in * SR)
    x[:ni] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(ni) / ni)
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


def glide_curve(notes, n):
    f_target = np.zeros(n)
    edge = 0.0
    for m, d in notes:
        a, b = int(edge * SR), min(n, int((edge + d) * SR))
        f_target[a:b] = midi_to_hz(m)
        edge += d
    i_end = min(n - 1, int(edge * SR))
    f_target[i_end:] = f_target[i_end - 1]
    alpha = 1.0 - np.exp(-1.0 / (0.09 * SR))
    return signal.lfilter([alpha], [1.0, -(1.0 - alpha)],
                          f_target, zi=[f_target[0] * (1 - alpha)])[0]


def chant_note(midi, dur, pulse=5.5, scatter=1.0):
    """Sardaukar throat chant body: glottal harmonics through dark formants."""
    n = int(dur * SR)
    tt = np.arange(n) / SR
    f0 = midi_to_hz(midi) * scatter
    phase = 2 * np.pi * np.cumsum(np.full(n, f0)) / SR
    src = np.zeros(n)
    for k in range(1, 15):
        src += np.sin(k * phase) / k ** 0.8
    env = np.minimum(np.clip(tt / 0.025, 0, 1), np.clip((dur - tt) / 0.08, 0, 1))
    src *= env * (0.70 + 0.30 * np.sin(2 * np.pi * pulse * tt))
    out = np.zeros(n)
    for lo, hi, g in [(380, 560, 1.0), (750, 1000, 0.6), (2200, 2700, 0.15)]:
        sos = signal.butter(2, [lo, hi], "bandpass", fs=SR, output="sos")
        out += g * signal.sosfilt(sos, src)
    out += 0.40 * np.sin(phase * 0.5) * env
    return out / (np.max(np.abs(out)) + 1e-12)


def mass_chant_note(midi, dur, voices=12):
    """Wide 12-voice chant used before the gate chops it into battle-breath."""
    n = int((dur + 0.16) * SR)
    L = np.zeros(n)
    R = np.zeros(n)
    for v in range(voices):
        det = 1.0 + rng.uniform(-0.008, 0.008)
        jitter = int(rng.uniform(0.0, 0.12) * SR)
        body = chant_note(midi, dur, scatter=det)
        body *= rng.uniform(0.82, 1.05)
        end = min(n, jitter + len(body))
        pan = (v + 0.5) / voices
        L[jitter:end] += body[: end - jitter] * np.cos(pan * np.pi / 2)
        R[jitter:end] += body[: end - jitter] * np.sin(pan * np.pi / 2)
    pk = max(np.max(np.abs(L)), np.max(np.abs(R))) + 1e-12
    return L / pk, R / pk


def screamed_horn_phrase(notes, octave=0, distant=False):
    """Carnyx horn pushed into chaotic vibrato, scream formant, and tanh drive."""
    notes = [(m + octave, d) for m, d in notes]
    total = sum(d for _, d in notes) + 1.2
    n = int(total * SR)
    tt = np.arange(n) / SR
    f_curve = glide_curve(notes, n)
    rate = 5.0 + 3.0 * slow_noise(0.8, -1.0, 1.0)[:n]
    vib = 1.0 + 0.020 * np.sin(2 * np.pi * np.cumsum(rate) / SR)
    scoop = 0.93 + 0.07 * np.clip(tt / 0.12, 0, 1)
    phase = 2 * np.pi * np.cumsum(f_curve * vib * scoop) / SR
    tone = np.zeros(n)
    for k in range(1, 14):
        tone += np.sin(k * phase) / k ** 0.68
    tone *= 1.0 + 0.24 * np.sin(2 * np.pi * 31.0 * tt)
    env = np.minimum(np.clip(tt / 0.08, 0, 1) ** 0.7,
                     np.clip((total - tt) / 0.9, 0, 1))
    tone *= env
    sub = 0.4 * np.sin(0.5 * phase) * env
    sos_body = signal.butter(2, [450, 900], "bandpass", fs=SR, output="sos")
    sos_scream = signal.butter(2, [1800, 3500], "bandpass", fs=SR, output="sos")
    out = tone + 0.7 * signal.sosfilt(sos_body, tone) + 0.7 * signal.sosfilt(sos_scream, tone) + sub
    out = np.tanh(3.0 * out)
    if distant:
        out = signal.sosfilt(signal.butter(2, 1000, "low", fs=SR, output="sos"), out)
    return out / (np.max(np.abs(out)) + 1e-12)


def commit(layer_L, layer_R, weight, env=None):
    global mix_L, mix_R, N_LAYERS
    N_LAYERS += 1
    pk = max(np.max(np.abs(layer_L)), np.max(np.abs(layer_R))) + 1e-12
    L = layer_L / pk * weight
    R = layer_R / pk * weight
    if env is not None:
        L *= env
        R *= env
    mix_L += L
    mix_R += R


IR_L = make_reverb_ir(2.8, 1.1, 7)
IR_R = make_reverb_ir(2.9, 1.2, 11)
mix_L = np.zeros(N)
mix_R = np.zeros(N)

# Energy is front-loaded and climbs, but the recharges pull the mix darker.
points = [(0, 0.22), (bar_t(B_GATHER), 0.34), (bar_t(B_MUSTER), 0.52),
          (bar_t(B_RISE1), 0.70), (bar_t(B_DROP1), 0.92),
          (bar_t(B_RECHARGE1), 0.55), (bar_t(B_DROP2), 0.98),
          (bar_t(B_RECHARGE2), 0.50), (bar_t(B_DROP3), 1.00),
          (bar_t(B_SPRINT), 1.08), (bar_t(B_CUT), 1.12), (DURATION, 0.0)]
energy = np.interp(t, [p[0] for p in points], [p[1] for p in points])
calm = 1.0 - 0.55 * np.clip(energy, 0, 1)


def groove_on(b):
    return B_MUSTER <= b < B_CUT and b not in RECHARGES


# Sidechain pump: stronger and deeper than Navigator; the kick owns D1.
pump = np.ones(N)
for _b in range(B_MUSTER, B_CUT):
    if not groove_on(_b):
        continue
    for _beat in (0.0, 1.0, 2.0, 3.0):
        i0 = int(bar_t(_b, _beat) * SR)
        n = min(int(BEAT * SR), N - i0)
        if n > 0:
            duck = 1.0 - 0.55 * np.exp(-np.arange(n) / SR / 0.10)
            pump[i0:i0+n] = np.minimum(pump[i0:i0+n], np.maximum(duck, 0.28))

# ---------------------------------------------------------------- legions atmosphere + drone
# The war is not desert wind: low massed feet/engines, mid roar, and far screams.
low = signal.sosfilt(signal.butter(2, [40, 200], "bandpass", fs=SR, output="sos"), rng.standard_normal(N))
mid = signal.sosfilt(signal.butter(2, [200, 900], "bandpass", fs=SR, output="sos"), rng.standard_normal(N))
high = signal.sosfilt(signal.butter(2, [2000, 6000], "bandpass", fs=SR, output="sos"), rng.standard_normal(N))
bursts = (slow_noise(0.35, 0, 1) ** 8) * high
roar = 0.8 * low * slow_noise(0.18, 0.35, 1.0) + 0.45 * mid * slow_noise(0.11, 0.25, 0.9) + 0.28 * bursts
roar /= np.max(np.abs(roar)) + 1e-12
pan = slow_noise(0.04, 0.25, 0.75)
commit(roar * np.cos(pan * np.pi / 2), roar * np.sin(pan * np.pi / 2), 0.20, env=calm)
print("legions atmosphere committed")

fD = midi_to_hz(26)
fEb = midi_to_hz(27)
fCs = midi_to_hz(37)
breath = 0.72 + 0.28 * np.sin(2 * np.pi * 0.018 * t + 0.4)
drone = breath * (np.sin(2*np.pi*fD*t) + 0.45*np.sin(2*np.pi*2*fD*t) +
                  0.28*np.sin(2*np.pi*3*fD*t) + 0.20*np.sin(2*np.pi*fEb*t) +
                  0.10*np.sin(2*np.pi*fCs*t))
commit(drone, drone, 0.24, env=pump)
print("D/Eb/C# drone committed")

# ---------------------------------------------------------------- kick stack + sub boom

def make_kick_stack(sub=True):
    n = int(0.55 * SR)
    tt = np.arange(n) / SR
    f = 44.0 + (150.0 - 44.0) * np.exp(-tt * 55.0)
    punch = np.sin(2 * np.pi * np.cumsum(f) / SR) * (1 - np.exp(-tt / 0.0008)) * np.exp(-tt * 9.0)
    click_noise = rng.standard_normal(n) * np.exp(-tt * 85.0)
    click = signal.sosfilt(signal.butter(2, [1800, 9000], "bandpass", fs=SR, output="sos"), click_noise)
    out = punch + 0.50 * click
    if sub:
        fsu = 37.0 + (55.0 - 37.0) * np.exp(-tt * 3.0)
        tail = np.sin(2 * np.pi * np.cumsum(fsu) / SR) * np.exp(-tt * 3.0)
        out += 1.15 * tail
    return out / (np.max(np.abs(out)) + 1e-12)


def make_sub_boom():
    n = int(BEAT * SR)
    tt = np.arange(n) / SR
    f = 37.0 + (50.0 - 37.0) * np.exp(-tt * 2.4)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR)
    rel = np.minimum(1.0, np.clip((BEAT - tt) / 0.06, 0, 1))
    x *= (1 - np.exp(-tt / 0.018)) * np.exp(-tt * 1.2) * rel
    return x / (np.max(np.abs(x)) + 1e-12)

KICK = make_kick_stack(True)
KICK_P = make_kick_stack(False)
BOOM = make_sub_boom()
lay_L = np.zeros(N); lay_R = np.zeros(N)
for b in range(B_MUSTER, B_CUT):
    if not groove_on(b):
        continue
    if b in WAR_DIPS and b not in DIP1:
        # Dips keep the kick, but with less ornament: chant + BAM only.
        kg = 0.86
    else:
        kg = 0.95 + 0.15 * (b >= B_DROP3)
    for beat in (0.0, 1.0, 2.0, 3.0):
        add_at(lay_L, KICK, bar_t(b, beat), kg)
        add_at(lay_R, KICK, bar_t(b, beat), kg)
        if b >= B_SPRINT:
            add_at(lay_L, KICK_P, bar_t(b, beat + 0.5), kg * 0.72)
            add_at(lay_R, KICK_P, bar_t(b, beat + 0.5), kg * 0.72)
commit(lay_L, lay_R, 0.50)
print("kick stack committed")

lay_L = np.zeros(N); lay_R = np.zeros(N)
for b in range(B_MUSTER, B_CUT):
    if not groove_on(b):
        continue
    for beat in (0.0, 1.0, 2.0, 3.0):
        add_at(lay_L, BOOM, bar_t(b, beat), 1.0)
        add_at(lay_R, BOOM, bar_t(b, beat), 1.0)
commit(lay_L, lay_R, 0.30)
print("sub boom committed")

# ---------------------------------------------------------------- psy bass: D Hijaz Kar off-beat walk

def psy_bass_note(midi, dur=STEP * 0.88):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    f = midi_to_hz(midi)
    phase = 2 * np.pi * np.cumsum(np.full(n, f)) / SR
    saw = np.zeros(n)
    for k in range(1, 18):
        if k * f < 7000:
            saw += np.sin(k * phase) / k
    saw = signal.sosfilt(signal.butter(2, 350, "low", fs=SR, output="sos"), saw)
    env = np.minimum(np.clip(tt / 0.002, 0, 1), np.clip((dur - tt) / 0.03, 0, 1))
    x = np.tanh(2.0 * saw) * env
    return x / (np.max(np.abs(x)) + 1e-12)

PB = {m: psy_bass_note(m) for m in (38, 39, 42, 43, 45, 46, 49, 50)}
lay_L = np.zeros(N); lay_R = np.zeros(N)
for b in range(B_MUSTER + 4, B_CUT):
    if not groove_on(b) or b in WAR_DIPS:
        continue
    for beat in range(4):
        walk = [42, 43, 45]
        if b % 4 == 3 and beat == 3:
            walk = [46, 49, 50]        # Bb -> C# -> D jihad cry cadence
        if b >= B_DROP3 and beat in (1, 3):
            walk[-1] = 50             # octave flick in slaughter/sprint
        for j, m in enumerate(walk):
            add_at(lay_L, PB[m], bar_t(b, beat + (j + 1) * 0.25), [0.78, 0.70, 0.96][j])
            add_at(lay_R, PB[m], bar_t(b, beat + (j + 1) * 0.25), [0.78, 0.70, 0.96][j])
commit(lay_L, lay_R, 0.30, env=pump)
print("psy bass committed")

# ---------------------------------------------------------------- hats, shaker, clap, field snare

def make_hat(open_=False):
    dur = 0.13 if open_ else 0.045
    n = int(dur * SR)
    tt = np.arange(n) / SR
    x = signal.sosfilt(signal.butter(2, 6500, "high", fs=SR, output="sos"), rng.standard_normal(n))
    x *= np.exp(-tt * (24.0 if open_ else 110.0))
    return x / (np.max(np.abs(x)) + 1e-12)


def make_shaker():
    n = int(0.055 * SR)
    tt = np.arange(n) / SR
    x = signal.sosfilt(signal.butter(2, [3500, 9500], "bandpass", fs=SR, output="sos"), rng.standard_normal(n))
    x *= np.exp(-tt * 85.0)
    return x / (np.max(np.abs(x)) + 1e-12)


def make_clap():
    n = int(0.30 * SR)
    x = np.zeros(n)
    for off, dec in [(0.000, 130), (0.011, 120), (0.022, 105), (0.036, 26)]:
        i = int(off * SR)
        nn = n - i
        tt = np.arange(nn) / SR
        burst = signal.sosfilt(signal.butter(2, [900, 5200], "bandpass", fs=SR, output="sos"), rng.standard_normal(nn))
        x[i:] += burst * np.exp(-tt * dec)
    return x / (np.max(np.abs(x)) + 1e-12)


def make_snare(buzz=False):
    n = int((0.22 if not buzz else 0.10) * SR)
    tt = np.arange(n) / SR
    tone = np.sin(2*np.pi*185*tt) * np.exp(-tt*35) + 0.55*np.sin(2*np.pi*330*tt) * np.exp(-tt*42)
    noise = signal.sosfilt(signal.butter(2, [1500, 9000], "bandpass", fs=SR, output="sos"), rng.standard_normal(n))
    noise *= np.exp(-tt * (55 if not buzz else 95))
    x = tone + 0.75 * noise
    return x / (np.max(np.abs(x)) + 1e-12)

OHAT, CHAT, SHAKER, CLAP = make_hat(True), make_hat(False), make_shaker(), make_clap()
SNARE, SBUZZ = make_snare(False), make_snare(True)

lay_L = np.zeros(N); lay_R = np.zeros(N)
for b in range(B_MUSTER, B_CUT):
    if not groove_on(b) or b in ALL_DIPS:
        continue
    for beat in range(4):
        add_at(lay_L, OHAT, bar_t(b, beat + 0.5), 0.80)
        add_at(lay_R, OHAT, bar_t(b, beat + 0.5), 1.00)
    for s in range(16):
        if s % 2 == 1 or b >= B_DROP2:
            g = [0.9, 0.35, 0.62, 0.35][s % 4]
            add_at(lay_L, CHAT, bar_t(b, s * 0.25), g * 0.42)
            add_at(lay_R, CHAT, bar_t(b, s * 0.25), g * 0.36)
commit(lay_L, lay_R, 0.12)
print("hats committed")

lay_L = np.zeros(N); lay_R = np.zeros(N)
for b in range(B_MUSTER + 4, B_CUT):
    if not groove_on(b) or b in ALL_DIPS:
        continue
    for s in range(16):
        g = [0.9, 0.4, 0.65, 0.4][s % 4]
        add_at(lay_L, SHAKER, bar_t(b, s * 0.25), g * 0.90)
        add_at(lay_R, SHAKER, bar_t(b, s * 0.25), g * 0.75)
commit(lay_L, lay_R, 0.07)
print("shaker committed")

lay_L = np.zeros(N); lay_R = np.zeros(N)
for b in range(B_DROP1, B_CUT):
    if not groove_on(b) or b in ALL_DIPS:
        continue
    for beat, pan_pos in [(1.0, 0.42), (3.0, 0.62)]:
        add_at(lay_L, CLAP, bar_t(b, beat), np.cos(pan_pos*np.pi/2))
        add_at(lay_R, CLAP, bar_t(b, beat), np.sin(pan_pos*np.pi/2))
commit(lay_L, lay_R, 0.11)
print("clap committed")

lay_L = np.zeros(N); lay_R = np.zeros(N)
for b in range(B_GATHER, B_CUT):
    if b in range(B_RISE1, B_DROP1) or b in range(B_RISE2, B_DROP2) or b in range(B_RISE3, B_DROP3):
        frac = (b % 8) / 8.0
        for s in range(16):
            add_at(lay_L, SBUZZ, bar_t(b, s * 0.25), 0.22 + 0.45 * frac)
            add_at(lay_R, SBUZZ, bar_t(b, s * 0.25), 0.18 + 0.42 * frac)
    elif groove_on(b) and b not in ALL_DIPS:
        for s in (4, 12):
            add_at(lay_L, SBUZZ, bar_t(b, s*0.25) - 0.030, 0.25)
            add_at(lay_L, SNARE, bar_t(b, s*0.25), 0.50)
            add_at(lay_R, SNARE, bar_t(b, s*0.25), 0.42)
commit(lay_L, lay_R, 0.13)
print("field snare committed")

# ---------------------------------------------------------------- war drums, toms, darbuka

def make_war_drum():
    n = int(0.70 * SR)
    tt = np.arange(n) / SR
    f = 42.0 + (90.0 - 42.0) * np.exp(-tt * 9.0)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * (1 - np.exp(-tt / 0.006)) * np.exp(-tt * 5.5)
    skin = signal.sosfilt(signal.butter(2, [100, 420], "bandpass", fs=SR, output="sos"), rng.standard_normal(n))
    skin *= np.exp(-tt * 14.0)
    x = body + 0.40 * skin
    return x / (np.max(np.abs(x)) + 1e-12)


def make_tom(f0):
    n = int(0.38 * SR)
    tt = np.arange(n) / SR
    f = f0 * (1.0 + 0.40 * np.exp(-tt * 40.0))
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 8.5)
    skin = signal.sosfilt(signal.butter(2, [300, 1500], "bandpass", fs=SR, output="sos"), rng.standard_normal(n))
    skin *= np.exp(-tt * 22.0)
    x = body + 0.35 * skin
    return x / (np.max(np.abs(x)) + 1e-12)


def make_doum():
    n = int(0.42 * SR)
    tt = np.arange(n) / SR
    x = np.sin(2*np.pi*np.cumsum(55 + 35*np.exp(-28*tt))/SR) * np.exp(-tt*7)
    x += 0.55*np.sin(2*np.pi*190*tt) * np.exp(-tt*16)
    return x / (np.max(np.abs(x)) + 1e-12)


def make_tek(ghost=False):
    n = int(0.16 * SR)
    tt = np.arange(n) / SR
    x = signal.sosfilt(signal.butter(2, [2500, 10000], "bandpass", fs=SR, output="sos"), rng.standard_normal(n))
    x *= np.exp(-tt * (60 if not ghost else 95))
    x += 0.35*np.sin(2*np.pi*640*tt) * np.exp(-tt*55)
    return x / (np.max(np.abs(x)) + 1e-12)

WAR, TOMS = make_war_drum(), [make_tom(165), make_tom(110), make_tom(80)]
DOUM, TEK, KA = make_doum(), make_tek(False), make_tek(True)

lay_L = np.zeros(N); lay_R = np.zeros(N)
for b in range(B_GATHER, B_CUT):
    if b < B_MUSTER:
        g = 0.35 + 0.035 * b
        add_at(lay_L, WAR, bar_t(b, 0.0), g)
        add_at(lay_R, WAR, bar_t(b, 0.0), g)
    elif groove_on(b) and b not in WAR_DIPS:
        g = 0.78 + 0.15 * (b >= B_DROP2) + 0.18 * (b >= B_DROP3)
        add_at(lay_L, WAR, bar_t(b, 0.0), g)
        add_at(lay_R, WAR, bar_t(b, 0.0), g)
        add_at(lay_L, WAR, bar_t(b, 2.0), g * 0.55)
        add_at(lay_R, WAR, bar_t(b, 2.0), g * 0.55)
commit(lay_L, lay_R, 0.21)
print("war drums committed")

lay_L = np.zeros(N); lay_R = np.zeros(N)
tom_pat = [(0, 0.0, 0.7, 0.35), (1, 1.5, 0.55, 0.65), (2, 2.25, 0.65, 0.25), (1, 3.25, 0.50, 0.75)]
for b in range(B_DROP1, B_CUT):
    if not groove_on(b) or b in ALL_DIPS:
        continue
    heavy = 0.75 + 0.20 * (b >= B_DROP2) + 0.30 * (b >= B_DROP3)
    if b % 8 == 7:
        for i in range(8):
            tom = TOMS[i % 3]
            p = 0.25 + 0.5 * (i % 2)
            add_at(lay_L, tom, bar_t(b, 2.0 + i * 0.25), heavy * 0.8 * np.cos(p*np.pi/2))
            add_at(lay_R, tom, bar_t(b, 2.0 + i * 0.25), heavy * 0.8 * np.sin(p*np.pi/2))
    for idx, beat, g, p in tom_pat:
        add_at(lay_L, TOMS[idx], bar_t(b, beat), heavy * g * np.cos(p*np.pi/2))
        add_at(lay_R, TOMS[idx], bar_t(b, beat), heavy * g * np.sin(p*np.pi/2))
commit(lay_L, lay_R, 0.15)
print("battle toms committed")

lay_L = np.zeros(N); lay_R = np.zeros(N)
maqsum = {0: DOUM, 2: TEK, 6: TEK, 8: DOUM, 12: TEK}
for b in range(B_MUSTER, B_CUT):
    if not groove_on(b) or b in ALL_DIPS:
        continue
    for s in range(16):
        hit = maqsum.get(s)
        g = 0.75
        if hit is None and rng.random() < 0.22 and s % 2 == 1:
            hit, g = KA, 0.28
        if hit is not None:
            p = 0.40 if s < 8 else 0.60
            add_at(lay_L, hit, bar_t(b, s * 0.25), g * np.cos(p*np.pi/2))
            add_at(lay_R, hit, bar_t(b, s * 0.25), g * np.sin(p*np.pi/2))
commit(lay_L, lay_R, 0.12)
print("darbuka committed")

# ---------------------------------------------------------------- Sardaukar chant-gate: the pulse that never stops
CH16_L, CH16_R = mass_chant_note(38, STEP * 0.64)
CH16B_L, CH16B_R = mass_chant_note(49, STEP * 0.62)
CH32_L, CH32_R = mass_chant_note(38, STEP * 0.33)
CH32B_L, CH32B_R = mass_chant_note(49, STEP * 0.31)
CH_SUS_L, CH_SUS_R = mass_chant_note(38, 1.35 * BEAT)
lay_L = np.zeros(N); lay_R = np.zeros(N)
for b in range(B_GATHER, B_CUT):
    if b < B_MUSTER:
        base = 0.20 + 0.055 * b
        div = 16
    elif b in RECHARGES:
        base = 0.52
        div = 16
    elif b in range(B_RISE1, B_DROP1) or b in range(B_RISE2, B_DROP2) or b in range(B_RISE3, B_DROP3):
        base = 0.58 + 0.05 * ((b % 8) / 8)
        div = 32
    elif b >= B_DROP3:
        base = 0.82 if b < B_SPRINT else 0.95
        div = 32
    else:
        base = 0.70
        div = 16
    steps = 32 if div == 32 else 16
    for s in range(steps):
        beat_pos = s * (4.0 / steps)
        accent = 1.0 if s % (steps // 4) == 0 else (0.72 if s % 2 == 0 else 0.55)
        bite = (s % 8 == 7) or (b % 4 == 3 and s >= steps - 4)
        L, R = (CH32B_L, CH32B_R) if (div == 32 and bite) else (CH32_L, CH32_R) if div == 32 else (CH16B_L, CH16B_R) if bite else (CH16_L, CH16_R)
        add_at(lay_L, L, bar_t(b, beat_pos), base * accent)
        add_at(lay_R, R, bar_t(b, beat_pos), base * accent)
    if b in WAR_DIPS and b % 2 == 0:
        add_at(lay_L, CH_SUS_L, bar_t(b, 0.0), 0.45)
        add_at(lay_R, CH_SUS_R, bar_t(b, 0.0), 0.45)
lay_L = reverb(lay_L, IR_L, wet=0.28)
lay_R = reverb(lay_R, IR_R, wet=0.28)
commit(lay_L, lay_R, 0.18, env=np.maximum(pump, 0.52))
print("Sardaukar chant-gate committed")

# ---------------------------------------------------------------- acid riffs
acid_cache = {}

def acid_note(m, cutoff, accent=False, slide_to=None, dur=None):
    dur = STEP * 1.04 if dur is None else dur
    key = (m, int(cutoff // 60), int(accent), slide_to)
    if key in acid_cache:
        return acid_cache[key]
    n = int(dur * SR)
    tt = np.arange(n) / SR
    f0 = midi_to_hz(m)
    f = np.full(n, f0)
    if slide_to is not None:
        f2 = midi_to_hz(slide_to)
        q = np.clip((tt - dur * 0.45) / (dur * 0.45), 0, 1)
        f *= (f2 / f0) ** q
    phase = 2 * np.pi * np.cumsum(f) / SR
    saw = np.zeros(n)
    for k in range(1, 45):
        if k * f0 < 9000:
            saw += np.sin(k * phase) / k
    bright_c = min(12000, cutoff * (3.2 if accent else 2.4))
    dark_c = max(90, cutoff * 0.72)
    bright = signal.sosfilt(signal.butter(2, bright_c, "low", fs=SR, output="sos"), saw)
    dark = signal.sosfilt(signal.butter(2, dark_c, "low", fs=SR, output="sos"), saw)
    qenv = np.exp(-tt / (0.10 if accent else 0.055))
    x = qenv * bright + (1 - qenv) * dark
    peak = signal.sosfilt(signal.iirpeak(min(8000, cutoff * (1.8 if accent else 1.25)), 11, fs=SR), x)
    env = np.minimum(np.clip(tt / 0.002, 0, 1), np.clip((dur - tt) / 0.018, 0, 1))
    x = np.tanh(2.8 * (x + (1.9 if accent else 1.4) * peak)) * env
    x /= np.max(np.abs(x)) + 1e-12
    acid_cache[key] = x
    return x

lay_L = np.zeros(N); lay_R = np.zeros(N)
for b in range(B_MUSTER + 8, B_CUT):
    if b in RECHARGES or b in WAR_DIPS:
        continue
    if b < B_DROP1:
        riffs = [(RIFF_HOLY1, 420, 1150, 0.78)]
    elif b < B_DROP2:
        riffs = [(RIFF_HOLY1, 520, 1900, 1.00)]
    elif b < B_DROP3:
        riffs = [(RIFF_HOLY1, 650, 2400, 1.05), (RIFF_HOLY2, 900, 3200, 0.58)]
    else:
        riffs = [(RIFF_HOLY1, 800, 3300, 1.10), (RIFF_HOLY2, 1100, 4800, 0.74)]
    if b >= B_SPRINT:
        riffs = [(RIFF_HOLY1, 1100, 5000, 1.16), (RIFF_HOLY2, 1400, 6200, 0.86)]
    for riff, lo, hi, gain in riffs:
        cutoff = lo + (hi - lo) * ((b % 16) / 15.0)
        for s, (m, acc, slide) in enumerate(riff):
            if m is None:
                continue
            x = acid_note(m, cutoff * (1.6 if acc else 1.0), bool(acc), slide)
            p = 0.35 + 0.30 * ((s + b) % 4) / 3.0
            add_at(lay_L, x, bar_t(b, s * 0.25), gain * np.cos(p*np.pi/2))
            add_at(lay_R, x, bar_t(b, s * 0.25), gain * np.sin(p*np.pi/2))
commit(lay_L, lay_R, 0.17)
print(f"acid committed ({len(acid_cache)} cached notes)")

# ---------------------------------------------------------------- screamed carnyx horn
lay_L = np.zeros(N); lay_R = np.zeros(N)

def place_horn(notes, t0, pan_pos, gain=1.0, octave=0, distant=False):
    x = screamed_horn_phrase(notes, octave=octave, distant=distant)
    wet = 0.62 if distant else 0.35
    xL = reverb(x, IR_L, wet=wet)
    xR = reverb(x, IR_R, wet=wet)
    add_at(lay_L, xL, t0, gain * np.cos(pan_pos*np.pi/2))
    add_at(lay_R, xR, t0, gain * np.sin(pan_pos*np.pi/2))

place_horn([(50, 3.4)], 2.5, 0.50, 0.35, distant=True)
place_horn(HORN_CALL, bar_t(B_MUSTER + 4), 0.46, 0.85)
place_horn(THEME_JIHAD, bar_t(B_DROP1), 0.42, 0.95)
place_horn(THEME_JIHAD, bar_t(B_DROP1 + 16), 0.62, 0.80)
place_horn(HORN_CALL, bar_t(B_RECHARGE1 + 4), 0.55, 0.55, distant=True)
place_horn(THEME_JIHAD, bar_t(B_DROP2), 0.35, 1.00)
place_horn(THEME_JIHAD, bar_t(B_DROP2 + 24), 0.68, 0.90)
place_horn(HORN_CALL, bar_t(B_DROP2 + 40), 0.50, 0.95)
place_horn(HORN_CALL, bar_t(B_RECHARGE2 + 2), 0.48, 0.48, distant=True)
place_horn(THEME_JIHAD, bar_t(B_DROP3), 0.36, 1.05, octave=12)
place_horn(HORN_CALL, bar_t(B_DROP3 + 16), 0.65, 1.05, octave=12)
place_horn(THEME_JIHAD, bar_t(B_DROP3 + 28), 0.50, 1.00, octave=12)
place_horn(HORN_CALL, bar_t(B_SPRINT), 0.50, 1.12, octave=12)
commit(lay_L, lay_R, 0.20)
print("screamed carnyx horn committed")

# ---------------------------------------------------------------- zaps, risers, reverse cymbals, frame rolls

def make_zap():
    n = int(0.18 * SR)
    tt = np.arange(n) / SR
    f = 80.0 + (1980.0 - 80.0) * np.exp(-tt * 28.0)
    x = np.sin(2*np.pi*np.cumsum(f)/SR) * (1 + 0.35*np.sin(2*np.pi*35*tt))
    x *= np.exp(-tt * 18.0)
    return x / (np.max(np.abs(x)) + 1e-12)


def riser(dur=4.0):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    white = rng.standard_normal(n)
    out = np.zeros(n)
    centers = np.geomspace(300, 5500, 10)
    x = np.linspace(0, 1, n)
    for i, c in enumerate(centers):
        band = signal.sosfilt(signal.butter(2, [max(60, c/1.8), min(12000, c*1.8)], "bandpass", fs=SR, output="sos"), white)
        tri = np.maximum(0, 1 - np.abs(x - i/(len(centers)-1)) * 2.8)
        out += band * tri
    f = 220 * 2 ** (2.0 * x)
    out += 0.35 * np.sin(2*np.pi*np.cumsum(f)/SR)
    out *= x ** 2
    return out / (np.max(np.abs(out)) + 1e-12)


def frame_roll(dur=2.0):
    n = int(dur * SR)
    out = np.zeros(n)
    hit_n = int(0.12 * SR)
    tt = np.arange(hit_n) / SR
    hit = signal.sosfilt(signal.butter(2, [180, 1400], "bandpass", fs=SR, output="sos"), rng.standard_normal(hit_n))
    hit += 0.5*np.sin(2*np.pi*95*tt) * np.exp(-tt*18)
    hit *= np.exp(-tt*20)
    hit /= np.max(np.abs(hit)) + 1e-12
    cur = 0.0
    while cur < dur:
        frac = cur / dur
        i = int(cur * SR)
        end = min(n, i + hit_n)
        out[i:end] += hit[:end-i] * (0.3 + 0.7 * frac)
        rate = 9 + 11 * frac
        cur += 1.0 / rate
    return out / (np.max(np.abs(out)) + 1e-12)


def rev_cymbal(dur=1.6):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    x = signal.sosfilt(signal.butter(2, 6000, "high", fs=SR, output="sos"), rng.standard_normal(n))
    x *= np.exp(-tt * 3.2)
    x = x[::-1]
    return x / (np.max(np.abs(x)) + 1e-12)

ZAP = make_zap()
lay_L = np.zeros(N); lay_R = np.zeros(N)
for b in [B_DROP1, B_DROP1+8, B_DROP1+24, B_DROP2, B_DROP2+16, B_DROP2+32, B_DROP3, B_DROP3+8, B_DROP3+24, B_SPRINT]:
    p = 0.25 + 0.5 * ((b // 8) % 2)
    add_at(lay_L, ZAP, bar_t(b), np.cos(p*np.pi/2))
    add_at(lay_R, ZAP, bar_t(b), np.sin(p*np.pi/2))
commit(lay_L, lay_R, 0.08)
print("zaps committed")

lay_L = np.zeros(N); lay_R = np.zeros(N)
for b0 in (B_RISE1, B_RISE2, B_RISE3):
    rz = riser(8 * BAR)
    add_at(lay_L, rz, bar_t(b0), 0.86)
    add_at(lay_R, rz, bar_t(b0), 1.00)
for b0 in (B_DROP1+36, B_DROP2+36, B_DROP3+36):
    rz = riser(4 * BAR)
    add_at(lay_L, rz, bar_t(b0), 0.48)
    add_at(lay_R, rz, bar_t(b0), 0.55)
commit(lay_L, lay_R, 0.10)
print("risers committed")

lay_L = np.zeros(N); lay_R = np.zeros(N)
for b0 in (B_DROP1, B_DROP2, B_DROP3, B_SPRINT):
    rc = rev_cymbal(1.8)
    add_at(lay_L, rc, bar_t(b0) - len(rc)/SR, 0.70)
    add_at(lay_R, rc, bar_t(b0) - len(rc)/SR, 0.80)
for b0 in (B_RISE1+6, B_RISE2+6, B_RISE3+6, B_SPRINT-2):
    fr = frame_roll(2 * BAR)
    add_at(lay_L, fr, bar_t(b0), 0.78)
    add_at(lay_R, fr, bar_t(b0), 0.86)
commit(lay_L, lay_R, 0.08)
print("reverse cymbals + frame rolls committed")

# ---------------------------------------------------------------- detonations, anvil steel, tremolo strings

def explosion(dur=2.8, sub_f=50.0):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    brown = np.cumsum(rng.standard_normal(n)); brown -= np.mean(brown)
    brown = signal.sosfilt(signal.butter(2, 150, "low", fs=SR, output="sos"), brown)
    f = 22.0 + (sub_f - 22.0) * np.exp(-tt * 2.0)
    core = np.sin(2*np.pi*np.cumsum(f)/SR)
    env = (1 - np.exp(-tt/0.08)) * np.exp(-tt/1.8)
    x = (0.7 * brown/(np.max(np.abs(brown))+1e-12) + 0.7 * core) * env
    return x / (np.max(np.abs(x)) + 1e-12)


def anvil():
    n = int(0.70 * SR)
    tt = np.arange(n) / SR
    base = 580.0
    x = np.zeros(n)
    for r, d, g in [(1.0, 18, 1.0), (2.756, 24, 0.55), (5.404, 30, 0.38), (8.933, 36, 0.25)]:
        x += g * np.sin(2*np.pi*base*r*tt) * np.exp(-tt*d)
    x += 0.35 * signal.sosfilt(signal.butter(2, 400, "high", fs=SR, output="sos"), rng.standard_normal(n)) * np.exp(-tt*55)
    return x / (np.max(np.abs(x)) + 1e-12)


def tremolo_strings(chord, dur, trem_hz=11.0):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    out = np.zeros(n)
    for m in chord:
        f = midi_to_hz(m)
        for det in (-0.004, 0.0, 0.005):
            ph = 2*np.pi*f*(1+det)*tt
            saw = np.zeros(n)
            for k in range(1, 9):
                saw += np.sin(k*ph) / k
            out += saw / 3.0
    out = signal.sosfilt(signal.butter(2, [180, 2600], "bandpass", fs=SR, output="sos"), out)
    trem = (0.5 + 0.5*np.sin(2*np.pi*trem_hz*tt)) ** 1.2
    env = np.minimum(np.clip(tt/2.0, 0, 1), np.clip((dur-tt)/2.0, 0, 1))
    out *= trem * env
    return out / (np.max(np.abs(out)) + 1e-12)

lay_L = np.zeros(N); lay_R = np.zeros(N)
for b, g, p in [(B_RECHARGE1, 0.55, 0.38), (B_RECHARGE1+5, 0.45, 0.70),
                (B_DROP2+8, 0.42, 0.25), (B_DROP2+30, 0.48, 0.65),
                (B_RECHARGE2+2, 0.50, 0.45), (B_DROP3+12, 0.55, 0.28),
                (B_DROP3+32, 0.58, 0.72), (B_SPRINT+8, 0.62, 0.50)]:
    ex = explosion(3.0, 50.0)
    add_at(lay_L, ex, bar_t(b), g*np.cos(p*np.pi/2))
    add_at(lay_R, ex, bar_t(b), g*np.sin(p*np.pi/2))
commit(lay_L, lay_R, 0.20)
print("detonations committed")

lay_L = np.zeros(N); lay_R = np.zeros(N)
AV = anvil()
for b, g in [(B_DROP1, 0.55), (B_DROP2, 0.65), (B_DROP3, 0.78), (B_SPRINT, 0.85), (B_CUT, 1.05)]:
    add_at(lay_L, AV, bar_t(b), g)
    add_at(lay_R, AV, bar_t(b) + 0.004, g)
commit(lay_L, lay_R, 0.10)
print("anvil steel committed")

lay_L = np.zeros(N); lay_R = np.zeros(N)
for b0, b1, g, chord in [(B_GATHER, B_RISE1, 0.38, [38, 39, 49]),
                         (B_RECHARGE1, B_DROP2, 0.45, [38, 39, 50]),
                         (B_RECHARGE2, B_DROP3, 0.50, [37, 38, 39]),
                         (B_DROP3, B_CUT, 0.36, [38, 39, 49])]:
    sw = tremolo_strings(chord, (b1 - b0) * BAR)
    add_at(lay_L, sw, bar_t(b0), g * 0.92)
    add_at(lay_R, sw, bar_t(b0), g)
commit(lay_L, lay_R, 0.10, env=np.maximum(calm, 0.35))
print("tremolo strings committed")

# ---------------------------------------------------------------- hard-cut downbeat stab
# One final downbeat stab, then every continuous layer is zeroed: no fade-out,
# no aftermath, only the immediate tail of the stab and true silence to EOF.
cut_i = int(bar_t(B_CUT) * SR)
stab_len = int(1.15 * SR)
stab_L = np.zeros(N); stab_R = np.zeros(N)
add_at(stab_L, KICK, bar_t(B_CUT), 1.05); add_at(stab_R, KICK, bar_t(B_CUT), 1.05)
add_at(stab_L, BOOM, bar_t(B_CUT), 1.00); add_at(stab_R, BOOM, bar_t(B_CUT), 1.00)
add_at(stab_L, AV, bar_t(B_CUT), 1.10); add_at(stab_R, AV, bar_t(B_CUT)+0.004, 1.10)
stab_horn = screamed_horn_phrase([(74, 0.75)], octave=0)
add_at(stab_L, stab_horn, bar_t(B_CUT), 0.85); add_at(stab_R, stab_horn, bar_t(B_CUT), 0.85)
commit(stab_L, stab_R, 0.30)
print("hard-cut stab committed")

end_i = min(N, cut_i + stab_len)
mix_L[end_i:] = 0.0
mix_R[end_i:] = 0.0

# ---------------------------------------------------------------- master
sos_shelf = signal.butter(2, 3000, "high", fs=SR, output="sos")
mix_L += 0.26 * signal.sosfilt(sos_shelf, mix_L)
mix_R += 0.26 * signal.sosfilt(sos_shelf, mix_R)
sos_sub = signal.butter(2, 95, "low", fs=SR, output="sos")
mix_L += 0.34 * signal.sosfilt(sos_sub, mix_L)
mix_R += 0.34 * signal.sosfilt(sos_sub, mix_R)
sos_deep = signal.butter(2, 55, "low", fs=SR, output="sos")
mix_L += 0.30 * signal.sosfilt(sos_deep, mix_L)
mix_R += 0.30 * signal.sosfilt(sos_deep, mix_R)
print("master shelves applied (high + low + deep)")

fade_in_only(mix_L, fade_in=5.0)
fade_in_only(mix_R, fade_in=5.0)
# Re-assert the hard cut after filtering/fade operations.
mix_L[end_i:] = 0.0
mix_R[end_i:] = 0.0

peak = max(np.max(np.abs(mix_L)), np.max(np.abs(mix_R))) + 1e-12
mix_L = np.tanh(1.40 * mix_L / peak) / np.tanh(1.40) * 0.88
mix_R = np.tanh(1.40 * mix_R / peak) / np.tanh(1.40) * 0.88
mix_L[end_i:] = 0.0
mix_R[end_i:] = 0.0

stereo = np.empty((N, 2))
stereo[:, 0] = mix_L
stereo[:, 1] = mix_R
pcm = (stereo * 32767.0).astype(np.int16)

OUT_DIR = "/workspace/music"
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, "jihad.wav")
with wave.open(OUT, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())

print(f"\nCreated: {os.path.abspath(OUT)}")
print(f"Duration: {N / SR:.1f} s  |  {SR} Hz stereo, 16-bit PCM  |  "
      f"{BPM:.0f} BPM  |  {N_LAYERS} committed layers")
print("Section map:")
for name, b in [("THE GATHERING: legions + chant-gate", B_GATHER),
                ("THE MUSTER: kick enters", B_MUSTER),
                ("RISE 1", B_RISE1),
                ("THE FIRST WAVE", B_DROP1),
                ("  war-cry dip: chant + kick", 56),
                ("RECHARGE 1: pulse never stops", B_RECHARGE1),
                ("RISE 2", B_RISE2),
                ("THE SECOND WAVE", B_DROP2),
                ("  dip", 112), ("  dip", 124),
                ("RECHARGE 2: darkest breath", B_RECHARGE2),
                ("RISE 3", B_RISE3),
                ("THE SLAUGHTER", B_DROP3),
                ("  dip", 172), ("  dip", 188),
                ("THE SPRINT: 8th kicks + 32nd chant", B_SPRINT),
                ("HARD CUT STAB", B_CUT)]:
    print(f"  {bar_t(b):6.1f} s  bar {b:3d}  {name}")
print(f"  {bar_t(B_CUT) + 1.15:6.1f} s  true silence begins")
print(f"  {DURATION:6.1f} s  end")
