#!/usr/bin/env python3
"""
lost_v3.py — "Lost (Trance)" (~6:50). A 130 BPM trance reworking of the
ambient "lost" emotional journey (ambient/lost.py). Same arc — love,
confusion, loss, dread/angst, sadness, hope — but told through trance
arrangement: the emotions become sections, with a strong 4/4 kick and
hard-hitting synth lines, and the two minor moods (loss, sadness) handled
as classic trance breakdowns where the beat drops out.

D major / D minor. Drums dry and punchy; melodic elements wet (dark hall).
Sidechain pump on bass + pads under the kick in the drops.

  0:00  INTRO        Kick + atmosphere creep; hats and a warm bass roll in.
  0:30  LOVE  (drop) Uplifting groove: pluck arpeggio + a warm detuned lead
                     theme over rolling bass, D major (I-V-vi-IV).
  1:13  CONFUSION    Restless groove: a wandering acid 303, chromatic-mediant
                     chords (Dm-F-Bb-Eb), filter unease.
  2:01  LOSS (break) The beat drops. D-minor breakdown — emotional piano,
                     strings, a lone heartbeat. Then a build back up.
  2:56  DREAD/ANGST  THE DARK DROP — room-shake kick, distorted psy rolling
                     bass, a screaming resonant acid (the angst), dissonant
                     polytonal stabs. A mid-drop dip, then the fullest, hardest
                     wave. Existential dread as relentless dark energy.
  4:11  SADNESS(brk) Comedown breakdown: sparse piano, lone cello, space.
  4:41  HOPE  (drop) The euphoric finale: a big detuned supersaw lead plays
                     the love theme reborn in major (vi-IV-I-V), full groove,
                     glittering plucks. Then the outro strips back and fades.

Everything is synthesized (numpy + scipy); no samples. Output:
/workspace/music/lost_v3.wav + lost_v3.mp3 (192k, ffmpeg).
"""

import os
import subprocess
import wave
import numpy as np
from scipy import signal

SR = 44100
DURATION = 410.0
N = int(SR * DURATION)
t = np.arange(N) / SR

rng = np.random.default_rng(130)       # the tempo

BPM = 130.0
BEAT = 60.0 / BPM
BAR = BEAT * 4
STEP = BEAT / 4                        # sixteenth
GRID0 = 0.5


def bar_t(b, beat=0.0):
    return GRID0 + b * BAR + beat * BEAT


# ----------------------------------------------------- section boundaries (bars)
B_INTRO2 = 8       # hats + bass creep in
B_LOVE = 16        # LOVE drop — uplifting groove
B_CONF = 40        # CONFUSION groove
B_LOSS = 64        # LOSS breakdown (beat drops)
B_LBUILD = 88      # build back up toward the dark drop
B_DREAD = 96       # DREAD dark drop
B_DDIP = 120       # mid-drop dip
B_DREAD2 = 124     # dread wave 2 — fullest/hardest
B_SAD = 136        # SADNESS comedown breakdown
B_HBUILD = 152     # hope build
B_HOPE = 160       # HOPE euphoric drop
B_OUT = 200        # outro
B_END = 216


def section_of(b):
    if b < B_INTRO2:
        return "intro"
    if b < B_LOVE:
        return "intro2"
    if b < B_CONF:
        return "love"
    if b < B_LOSS:
        return "conf"
    if b < B_LBUILD:
        return "loss"
    if b < B_DREAD:
        return "lbuild"
    if b < B_SAD:
        return "dread"
    if b < B_HBUILD:
        return "sad"
    if b < B_HOPE:
        return "hbuild"
    if b < B_OUT:
        return "hope"
    return "out"


# ---------------------------------------------------------------- helpers

def midi_to_hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def fade(x, fade_in=0.4, fade_out=9.0):
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


# ============================================================= harmony table
# Each bar maps to (bass_root_midi, chord_voicing_tuple).

D = (38, (50, 54, 57, 62))          # D major
A = (33, (52, 57, 61, 64))          # A major
Bm = (35, (50, 54, 59, 62))         # B minor
G = (31, (50, 55, 59, 62))          # G major

Dm = (38, (50, 53, 57, 62))         # D minor
Fc = (41, (48, 53, 57, 60))         # F major
Bb = (34, (50, 53, 58, 62))         # Bb major
Eb = (39, (51, 55, 58, 63))         # Eb major
Gm = (31, (50, 55, 58, 62))         # G minor

Ddark = (38, (50, 53, 56, 62))      # D F Ab D — the tritone, dread
Ebdark = (39, (51, 54, 56, 63))     # Eb Gb Ab — dissonant shadow

Bm_hi = (35, (54, 59, 62, 66))      # higher voicings for the euphoric drop
G_hi = (31, (55, 59, 62, 67))
D_hi = (38, (57, 62, 66, 69))
A_hi = (33, (57, 61, 64, 69))

CHORD_AT = [D] * B_END


def fill(b0, b1, seq, bars_each):
    i = 0
    b = b0
    while b < b1:
        for _ in range(bars_each):
            if b < b1:
                CHORD_AT[b] = seq[i % len(seq)]
                b += 1
        i += 1


fill(0, B_LOVE, [D], 1)
fill(B_LOVE, B_CONF, [D, A, Bm, G], 2)
fill(B_CONF, B_LOSS, [Dm, Fc, Bb, Eb], 2)
fill(B_LOSS, B_LBUILD, [Dm, Bb, Gm, A], 4)
fill(B_LBUILD, B_DREAD, [Dm], 1)
fill(B_DREAD, B_SAD, [Ddark, Ebdark], 4)
fill(B_SAD, B_HBUILD, [Dm, Bb], 8)
fill(B_HBUILD, B_HOPE, [A], 1)
fill(B_HOPE, B_OUT, [Bm_hi, G_hi, D_hi, A_hi], 2)
fill(B_OUT, B_END, [D_hi, G_hi], 4)


# ============================================================= drum kit (dry)

def make_kick():
    n = int(0.42 * SR)
    td = np.arange(n) / SR
    f_curve = 44.0 + 110.0 * np.exp(-td * 55.0)
    body = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    sub = np.sin(2 * np.pi * (37 + 18 * np.exp(-td * 3)) * td) * np.exp(-td * 3.0)
    sos_c = signal.butter(2, [1800, 9000], "bandpass", fs=SR, output="sos")
    click = signal.sosfilt(sos_c, rng.standard_normal(n)) * np.exp(-td * 500)
    click /= np.max(np.abs(click)) + 1e-12
    env = (1 - np.exp(-td / 0.0008)) * np.exp(-td * 8.0)
    x = body * env + 0.55 * sub + 0.45 * click * (1 - np.exp(-td / 0.0008))
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
RCYM = np.ascontiguousarray(CRASH[::-1][int(0.4 * SR):])


def kick_gain(b):
    s = section_of(b)
    if s in ("loss", "sad"):
        return 0.0                                  # breakdowns — beat drops
    if s == "lbuild":
        return 0.0 if b < B_LBUILD + 4 else 0.7     # walks in for the second half
    if s == "hbuild":
        return 0.0
    if s == "intro":
        return 0.0 if b < 4 else 0.78
    if s == "intro2":
        return 0.88
    if B_DDIP <= b < B_DREAD2:
        return 0.95                                 # the dip keeps the kick
    if s == "dread":
        return 1.0
    if s == "out":
        return 0.92 if b < B_OUT + 8 else 0.7
    return 1.0


# kick
clear()
for b in range(B_END):
    g = kick_gain(b)
    if g <= 0:
        continue
    for beat in range(4):
        add_at(lay_L, KICK, bar_t(b, beat), g)
        add_at(lay_R, KICK, bar_t(b, beat), g)
commit(lay_L, lay_R, 0.36)
print("kick committed")

# sidechain pump from the kick grid (applied later to bass/pads in drops)
pump = np.ones(N)
for b in range(B_END):
    if kick_gain(b) <= 0:
        continue
    i0, i1 = int(bar_t(b) * SR), int(bar_t(b + 1) * SR)
    seg = (t[i0:i1] - bar_t(b)) % BEAT
    pump[i0:i1] = np.minimum(pump[i0:i1], 0.30 + 0.70 * (1 - np.exp(-seg / 0.085)))

# hats: 16th closed (offbeat accent open). On in grooves, building in builds.
clear()
CH = [0.5, 0.28, 0.0, 0.34]
for b in range(B_END):
    s = section_of(b)
    if s in ("intro", "loss", "sad"):
        continue
    g = 1.0
    if s == "intro2":
        g = 0.7
    if s in ("lbuild", "hbuild"):
        g = 0.5 + 0.5 * ((b - (B_LBUILD if s == "lbuild" else B_HBUILD)) / 8)
    for beat in range(4):
        for sx in range(4):
            if CH[sx] <= 0:
                continue
            add_at(lay_L, CHAT, bar_t(b, beat + sx * 0.25), g * CH[sx] * 0.9)
            add_at(lay_R, CHAT, bar_t(b, beat + sx * 0.25), g * CH[sx])
        add_at(lay_L, OHAT, bar_t(b, beat + 0.5), g * 0.9)
        add_at(lay_R, OHAT, bar_t(b, beat + 0.5), g * 0.8)
commit(lay_L, lay_R, 0.08)
print("hats committed")

# clap on 2 & 4 in grooves
clear()
for b in range(B_END):
    s = section_of(b)
    if s not in ("love", "conf", "dread", "hope", "out"):
        continue
    for beat in (1, 3):
        p = 0.42 if beat == 1 else 0.58
        place_pan(lay_L, lay_R, CLAP, bar_t(b, beat), 1.0, p)
commit(lay_L, lay_R, 0.11)
print("clap committed")

# ride in the euphoric drop
clear()
for b in range(B_HOPE, B_OUT):
    for e in range(8):
        g = 0.7 if e % 2 == 0 else 0.45
        place_pan(lay_L, lay_R, RIDE, bar_t(b, e * 0.5), g, 0.5)
commit(lay_L, lay_R, 0.05)
print("ride committed")

# crashes at boundaries; reverse cymbals lean into the drops
clear()
for b, g in [(B_LOVE, 0.9), (B_CONF, 0.7), (B_LOSS, 0.8), (B_DREAD, 1.0),
             (B_DREAD2, 0.8), (B_SAD, 0.7), (B_HOPE, 1.0), (B_OUT, 0.7)]:
    place_pan(lay_L, lay_R, CRASH, bar_t(b), g, 0.5)
for b in (B_LOVE, B_DREAD, B_HOPE):
    add_at(lay_L, RCYM, bar_t(b) - RCYM.shape[0] / SR, 0.8)
    add_at(lay_R, RCYM, bar_t(b) - RCYM.shape[0] / SR, 0.7)
commit(lay_L, lay_R, 0.05)
print("crashes committed")

# snare / kick rolls in the build sections
clear()
def roll(b0, b1, base):
    """accelerating snare roll across [b0,b1)."""
    nbars = b1 - b0
    for b in range(b0, b1):
        u = (b - b0) / nbars
        div = 4 if u < 0.5 else (8 if u < 0.85 else 16)
        for s in range(div):
            g = base * (0.4 + 0.6 * u) * (0.7 + 0.3 * (s % 2))
            place_pan(lay_L, lay_R, SNARE, bar_t(b, s * 4.0 / div), g, 0.5)
roll(B_LBUILD, B_DREAD, 0.8)
roll(B_HBUILD, B_HOPE, 0.85)
commit(lay_L, lay_R, 0.10)
print("rolls committed")


# ============================================================= bass

bass_cache = {}


def bass_note(midi, cutoff, drive=1.6, dur=STEP * 0.92, sub=0.5):
    key = (midi, int(cutoff // 60), round(drive, 1), round(sub, 1))
    if key in bass_cache:
        return bass_cache[key]
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    for k in range(1, min(22, int(3500 / f)) + 1):
        x += np.sin(2 * np.pi * k * f * td) / k
    y = signal.sosfilt(signal.butter(2, cutoff, "low", fs=SR, output="sos"), x)
    bpk, apk = signal.iirpeak(cutoff, Q=4.0, fs=SR)
    y = y + 0.8 * signal.lfilter(bpk, apk, y)
    y += sub * np.sin(2 * np.pi * (f / 2) * td)
    y = np.tanh(drive * y)
    y *= (1 - np.exp(-td / 0.002)) * np.clip((dur - td) / 0.02, 0, 1)
    bass_cache[key] = y / (np.max(np.abs(y)) + 1e-12)
    return bass_cache[key]


# rolling bass: root on beat-ish, octave on the 16ths (warm in love/hope,
# hard psy K-b-b-b in dread).
clear()
for b in range(B_END):
    s = section_of(b)
    root, _ = CHORD_AT[b]
    if s in ("love", "out"):
        cut, drive, pat = 520, 1.6, [(0, 0, .7), (1, 12, .95), (2, 0, .8), (3, 12, .9)]
    elif s == "conf":
        cut, drive, pat = 430, 1.8, [(0, 0, .8), (1, 12, .9), (2, 0, .8), (3, 7, .9)]
    elif s == "hope":
        cut, drive, pat = 620, 1.6, [(0, 0, .7), (1, 12, .95), (2, 0, .8), (3, 12, .9)]
    elif s == "dread":
        cut, drive, pat = 380, 2.6, [(1, 0, .9), (2, 0, .85), (3, 0, .95)]   # psy: skip the kick step
        root = 38
    elif s == "lbuild" and b >= B_LBUILD + 4:
        cut, drive, pat = 360, 2.2, [(1, 0, .8), (2, 0, .8), (3, 0, .9)]
        root = 38
    else:
        continue
    for beat in range(4):
        for sx, off, gg in pat:
            x = bass_note(root + off, cut, drive)
            tt = bar_t(b, beat + sx * 0.25)
            add_at(lay_L, x, tt, gg)
            add_at(lay_R, x, tt, gg)
commit(lay_L, lay_R, 0.30, env=pump)
print(f"bass committed ({len(bass_cache)} cached)")

# a sustained sub pedal under the dread for weight
clear()
for b in range(B_DREAD, B_SAD):
    f = midi_to_hz(26)              # D1
    seg_n = int(BEAT * SR)
    td = np.arange(seg_n) / SR
    sub = np.sin(2 * np.pi * f * td) * (np.exp(-td * 1.2))
    sub *= np.clip((BEAT - td) / 0.04, 0, 1)
    for beat in range(4):
        add_at(lay_L, sub, bar_t(b, beat), 0.9)
        add_at(lay_R, sub, bar_t(b, beat), 0.9)
commit(lay_L, lay_R, 0.16, env=pump)
print("sub pedal committed")


# ============================================================= acid 303

acid_cache = {}


def acid_note(midi, cutoff, accent, dur=STEP * 0.95):
    key = (midi, int(cutoff // 70), accent)
    if key in acid_cache:
        return acid_cache[key]
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    saw = np.zeros(n)
    for k in range(1, min(20, int(8000 / f)) + 1):
        saw += np.sin(2 * np.pi * k * f * td) / k

    def filt(c):
        y = signal.sosfilt(signal.butter(2, np.clip(c, 80, 18000), "low", fs=SR, output="sos"), saw)
        bpk, apk = signal.iirpeak(np.clip(c, 80, 18000), Q=11, fs=SR)
        return y + (1.9 if accent else 1.4) * signal.lfilter(bpk, apk, y)

    bright = filt(cutoff * 3)
    dark = filt(cutoff * 0.75)
    xf = np.exp(-td / (0.10 if accent else 0.055))
    y = bright * xf + dark * (1 - xf)
    y = np.tanh(2.8 * y)
    y *= (1 - np.exp(-td / 0.002)) * np.clip((dur - td) / 0.01, 0, 1)
    acid_cache[key] = y / (np.max(np.abs(y)) + 1e-12)
    return acid_cache[key]


# confusion acid: wandering chromatic 16th line, mid cutoff breathing
clear()
CONF_ACID = [62, None, 65, 62, 68, None, 63, 65, 60, None, 62, 67, 63, None, 61, 62]
CONF_ACC = [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0]
for b in range(B_CONF, B_LOSS):
    base = 600 + 350 * np.sin(2 * np.pi * (b - B_CONF) / 16)
    for sx in range(16):
        m = CONF_ACID[sx]
        if m is None:
            continue
        x = acid_note(m, base, CONF_ACC[sx])
        place_pan(lay_L, lay_R, x, bar_t(b, sx * 0.25), 0.8 if CONF_ACC[sx] else 0.55, 0.42)
lay_L = reverb(lay_L, IR_L, 0.25)
lay_R = reverb(lay_R, IR_R, 0.25)
commit(lay_L, lay_R, 0.13)
print("confusion acid committed")

# dread acid: a SCREAMING resonant line — high, dissonant (D minor + b2/tritone),
# accents driving, cutoff ramping up across the drop = the angst.
clear()
DREAD_ACID = [50, 50, 62, 50, 51, 50, 57, 56, 50, 62, 50, 51, 56, 50, 57, 51]
DREAD_ACC = [1, 0, 1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1]
for b in range(B_DREAD, B_SAD):
    if B_DDIP <= b < B_DREAD2:
        oct = 0
    else:
        oct = 12 if b >= B_DREAD2 else 0           # screams an octave up in wave 2
    base = 700 + 1700 * np.clip((b - B_DREAD) / (B_SAD - B_DREAD), 0, 1)
    for sx in range(16):
        m = DREAD_ACID[sx] + oct
        x = acid_note(m, base, DREAD_ACC[sx])
        g = (0.95 if DREAD_ACC[sx] else 0.6) * (1.0 if b >= B_DDIP else 0.85)
        place_pan(lay_L, lay_R, x, bar_t(b, sx * 0.25), g, 0.5 + 0.18 * (sx % 2 - 0.5))
lay_L = reverb(lay_L, IR_L, 0.22)
lay_R = reverb(lay_R, IR_R, 0.22)
commit(lay_L, lay_R, 0.17)
print("dread acid committed")


# ============================================================= pluck arp

pluck_cache = {}


def pluck(midi, dur=STEP * 3):
    if midi in pluck_cache:
        return pluck_cache[midi]
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    v = np.zeros(n)
    for det in (0.997, 1.0, 1.003):
        for k in range(1, min(16, int(9000 / f)) + 1):
            v += np.sin(2 * np.pi * k * f * det * td) / k
    v = signal.sosfilt(signal.butter(2, 4500, "low", fs=SR, output="sos"), v)
    v *= (1 - np.exp(-td / 0.002)) * np.exp(-td * 9.0)
    pluck_cache[midi] = v / (np.max(np.abs(v)) + 1e-12)
    return pluck_cache[midi]


# interlocking up/down 16th arpeggio over the chord, love + hope (+ outro)
clear()
ARP_PAT = [0, 1, 2, 3, 2, 1, 3, 2]
for b in range(B_END):
    s = section_of(b)
    if s not in ("love", "hope", "out"):
        continue
    _, voicing = CHORD_AT[b]
    notes = list(voicing) + [voicing[1] + 12]
    g0 = 0.85 if s == "hope" else 0.7
    for sx in range(16):
        idx = ARP_PAT[sx % len(ARP_PAT)] % len(notes)
        m = notes[idx]
        pan = 0.5 + 0.4 * (idx / (len(notes) - 1) - 0.5)
        place_pan(lay_L, lay_R, pluck(m), bar_t(b, sx * 0.25),
                  g0 * (0.9 if sx % 2 else 1.0), pan)
lay_L = reverb(lay_L, IR_L, 0.3)
lay_R = reverb(lay_R, IR_R, 0.3)
commit(lay_L, lay_R, 0.15, env=0.5 + 0.5 * pump)
print(f"pluck arp committed ({len(pluck_cache)} cached)")


# ============================================================= detuned lead

def lead_phrase(notes, detune=(0.994, 0.997, 1.0, 1.003, 1.006), lowpass=4500,
                drive=1.3, vib=0.0035):
    total = sum(d for _, d in notes) * BEAT
    n = int((total + 2.0) * SR)
    tt = np.arange(n) / SR
    f = glide_curve([(m, d * BEAT) for m, d in notes], n, tau=0.04)
    vibe = 1.0 + vib * np.sin(2 * np.pi * 5.5 * tt) * np.clip(tt / 1.2, 0, 1)
    K = max(3, int(7500 / np.max(f)))
    L = np.zeros(n)
    R = np.zeros(n)
    for j, det in enumerate(detune):
        ph = 2 * np.pi * np.cumsum(f * det * vibe) / SR
        v = np.zeros(n)
        for k in range(1, K + 1):
            v += np.sin(k * ph) / k
        if j % 2 == 0:
            L += v
        else:
            R += v
        L += 0.5 * v
        R += 0.5 * v
    env = np.minimum(np.clip(tt / 0.04, 0, 1), np.clip((total + 0.6 - tt) / 1.2, 0, 1))
    sos = signal.butter(2, lowpass, "low", fs=SR, output="sos")
    L = np.tanh(drive * signal.sosfilt(sos, L * env))
    R = np.tanh(drive * signal.sosfilt(sos, R * env))
    peak = max(np.max(np.abs(L)), np.max(np.abs(R)), 1e-12)
    return L / peak, R / peak


LOVE_THEME = [(66, 1), (69, 1), (73, 2), (71, 2), (69, 2), (66, 1), (64, 1), (62, 4),
              (64, 1), (66, 1), (69, 2), (71, 2), (73, 2), (69, 1), (66, 1), (69, 4)]
HOPE_THEME = [(74, 1), (78, 1), (81, 2), (78, 2), (76, 2), (74, 1), (73, 1), (74, 4),
              (76, 1), (78, 1), (81, 2), (83, 2), (85, 2), (81, 1), (78, 1), (74, 4)]

clear()
# love lead: warmer, fewer voices, softer
LL, LR = lead_phrase(LOVE_THEME, detune=(0.996, 1.0, 1.004), lowpass=3800, drive=1.1)
DELAY = 0.75 * BEAT
for b0 in range(B_LOVE + 8, B_CONF, 16):
    t0 = bar_t(b0)
    add_at(lay_L, LL, t0, 0.9)
    add_at(lay_R, LR, t0, 0.9)
    add_at(lay_L, LR, t0 + DELAY, 0.25)
    add_at(lay_R, LL, t0 + DELAY, 0.25)
# hope lead: big supersaw euphoria, the theme reborn
HL, HR = lead_phrase(HOPE_THEME, lowpass=5200, drive=1.4)
for b0 in range(B_HOPE + 8, B_OUT, 16):
    t0 = bar_t(b0)
    add_at(lay_L, HL, t0, 1.0)
    add_at(lay_R, HR, t0, 1.0)
    add_at(lay_L, HR, t0 + DELAY, 0.3)
    add_at(lay_R, HL, t0 + DELAY, 0.3)
    add_at(lay_L, HL, t0 + 2 * DELAY, 0.14)
    add_at(lay_R, HR, t0 + 2 * DELAY, 0.14)
lay_L = reverb(lay_L, IR_L, 0.35)
lay_R = reverb(lay_R, IR_R, 0.35)
commit(lay_L, lay_R, 0.24)
print("lead committed")


# ============================================================= dark stabs

def make_stab(chord, dark=True):
    dur = STEP * 1.8
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    for m in chord:
        f = midi_to_hz(m)
        for k in range(1, min(14, int(3500 / f)) + 1):
            x += np.sin(2 * np.pi * k * f * td + rng.uniform(0, 6)) / k
    x = signal.sosfilt(signal.butter(2, 1100 if dark else 2600, "low", fs=SR, output="sos"), x)
    x = np.tanh(1.4 * x)
    x *= (1 - np.exp(-td / 0.002)) * np.clip((dur - td) / 0.05, 0, 1)
    return x / (np.max(np.abs(x)) + 1e-12)


clear()
for b in range(B_DREAD, B_SAD):
    _, voicing = CHORD_AT[b]
    stab = make_stab(voicing[:3], dark=True)
    for beat in range(4):
        p = 0.35 if beat % 2 == 0 else 0.65
        place_pan(lay_L, lay_R, stab, bar_t(b, beat + 0.5), 0.9, p)
lay_L = reverb(lay_L, IR_L, 0.3)
lay_R = reverb(lay_R, IR_R, 0.3)
commit(lay_L, lay_R, 0.12, env=pump)
print("dark stabs committed")


# ============================================================= piano (breaks)

piano_cache = {}


def piano_note(midi, dur):
    key = (midi, round(dur, 2))
    if key in piano_cache:
        return piano_cache[key]
    f = midi_to_hz(midi)
    n = int((dur + 0.8) * SR)
    td = np.arange(n) / SR
    out = np.zeros(n)
    for k in range(1, min(14, int(8500 / f)) + 1):
        fk = f * k * np.sqrt(1 + 0.00035 * k * k)
        dec = 0.9 + 0.45 * k
        for det in (0.9994, 1.0006):
            out += np.sin(2 * np.pi * fk * det * td + rng.uniform(0, 6)) / k ** 1.25 * np.exp(-td * dec)
    ham = signal.sosfilt(signal.butter(2, [1500, 4000], "bandpass", fs=SR, output="sos"),
                         rng.standard_normal(n)) * np.exp(-td * 350)
    out = out / (np.max(np.abs(out)) + 1e-12) + 0.16 * ham / (np.max(np.abs(ham)) + 1e-12)
    out *= (1 - np.exp(-td / 0.0015)) * np.clip((dur + 0.35 - td) / 0.35, 0, 1)
    piano_cache[key] = out / (np.max(np.abs(out)) + 1e-12)
    return piano_cache[key]


# emotional piano figure for the loss & sadness breakdowns (D minor)
clear()
def piano_arc(b0, b1, gain):
    # a slow descending broken-chord figure following the chord table
    for b in range(b0, b1):
        _, voicing = CHORD_AT[b]
        notes = list(voicing)
        pat = [0, 2, 3, 2, 1, 3, 2, 1]
        for e in range(8):
            if rng.random() < 0.2:
                continue
            m = notes[pat[e] % len(notes)]
            mm = m if e % 2 == 0 else m + 12
            place_pan(lay_L, lay_R, piano_note(mm, BEAT * 0.9), bar_t(b, e * 0.5),
                      gain * (1.0 if e % 2 == 0 else 0.7),
                      np.clip(0.5 + (mm - 62) * 0.012, 0.25, 0.75))
piano_arc(B_LOSS, B_LBUILD, 0.85)
piano_arc(B_SAD, B_HBUILD, 0.8)
lay_L = reverb(lay_L, IR_L, 0.5)
lay_R = reverb(lay_R, IR_R, 0.5)
commit(lay_L, lay_R, 0.26)
print(f"piano committed ({len(piano_cache)} cached)")


# ============================================================= pads + strings

def pad_chord(chord, dur, attack, release, lowpass, detune=0.001):
    n = int(dur * SR)
    td = np.arange(n) / SR
    L = np.zeros(n)
    R = np.zeros(n)
    for m in chord:
        f = midi_to_hz(m)
        amp = 0.8 + 0.2 * np.sin(2 * np.pi * rng.uniform(0.02, 0.06) * td + rng.uniform(0, 6))
        for d, gL, gR in [(1 - detune, 1.0, 0.62), (1 + detune, 0.62, 1.0)]:
            ph = 2 * np.pi * f * d * td + rng.uniform(0, 6)
            v = (np.sin(ph) + 0.3 * np.sin(2 * ph) + 0.1 * np.sin(3 * ph)) * amp
            L += gL * v
            R += gR * v
    env = np.minimum(np.clip(td / attack, 0, 1) ** 1.3, np.clip((dur - td) / release, 0, 1))
    sos = signal.butter(2, lowpass, "low", fs=SR, output="sos")
    L = signal.sosfilt(sos, L * env)
    R = signal.sosfilt(sos, R * env)
    peak = max(np.max(np.abs(L)), np.max(np.abs(R)), 1e-12)
    return L / peak, R / peak


clear()
# one pad per 2-bar chord region, lowpass/detune by section
bb = 0
while bb < B_END:
    s = section_of(bb)
    span = 2
    chord = CHORD_AT[bb][1]
    lp = {"intro": 900, "intro2": 1000, "love": 1200, "conf": 850, "loss": 800,
          "lbuild": 700, "dread": 560, "sad": 760, "hbuild": 1000, "hope": 1500,
          "out": 1300}[s]
    det = 0.007 if s in ("dread", "conf") else 0.0012
    g = {"intro": 0.7, "intro2": 0.7, "love": 0.55, "conf": 0.55, "loss": 0.95,
         "lbuild": 0.8, "dread": 0.7, "sad": 0.95, "hbuild": 0.85, "hope": 0.6,
         "out": 0.6}[s]
    pL, pR = pad_chord(chord, span * BAR + 2.0, attack=1.5, release=2.2,
                       lowpass=lp, detune=det)
    add_at(lay_L, pL, bar_t(bb), g)
    add_at(lay_R, pR, bar_t(bb), g)
    bb += span
lay_L = reverb(lay_L, IR_L, 0.45)
lay_R = reverb(lay_R, IR_R, 0.45)
# pads pump only in the drops, sustain in breakdowns
pad_env = np.where((t < bar_t(B_LOSS)) | ((t >= bar_t(B_DREAD)) & (t < bar_t(B_SAD))) |
                   (t >= bar_t(B_HOPE)), pump, 1.0)
commit(lay_L, lay_R, 0.17, env=0.6 + 0.4 * pad_env)
print("pads committed")


# ============================================================= heartbeat (breaks)
# the v2 through-line, kept alive where the kick drops out.

clear()
def heart():
    n = int(0.26 * SR)
    td = np.arange(n) / SR
    f = 32 + 36 * np.exp(-td * 20)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-td * 13)
    body += 0.5 * np.sin(2 * np.pi * 70 * td) * np.exp(-td * 18)
    thud = signal.sosfilt(signal.butter(2, 220, "low", fs=SR, output="sos"),
                          rng.standard_normal(n)) * np.exp(-td * 28)
    x = body / (np.max(np.abs(body)) + 1e-12) + 0.3 * thud / (np.max(np.abs(thud)) + 1e-12)
    x *= 1 - np.exp(-td / 0.004)
    return x / (np.max(np.abs(x)) + 1e-12)

THUMP = heart()
for b in range(B_END):
    s = section_of(b)
    if s not in ("loss", "sad"):
        continue
    for beat in (0, 2):
        add_at(lay_L, THUMP, bar_t(b, beat), 0.9)
        add_at(lay_R, THUMP, bar_t(b, beat), 0.9)
        add_at(lay_L, THUMP, bar_t(b, beat + 0.5), 0.55)
        add_at(lay_R, THUMP, bar_t(b, beat + 0.5), 0.55)
commit(lay_L, lay_R, 0.20)
print("heartbeat committed")


# ============================================================= risers + atmos

clear()
def riser(b0, b1):
    t0, t1 = bar_t(b0), bar_t(b1)
    n = int((t1 - t0) * SR)
    td = np.arange(n) / SR
    prog = td / (t1 - t0)
    noise = rng.standard_normal(n)
    out = np.zeros(n)
    for k in range(8):
        c = 350 * (6000 / 350) ** (k / 7)
        win = np.clip(1 - np.abs(prog - np.log(c / 350) / np.log(6000 / 350)) * 6, 0, 1)
        out += signal.sosfilt(signal.butter(2, [c * 0.85, c * 1.18], "bandpass", fs=SR, output="sos"), noise) * win
    out += 0.4 * np.sin(2 * np.pi * np.cumsum(midi_to_hz(50) * 2 ** (2 * prog)) / SR)
    out *= prog ** 2
    add_at(lay_L, out / (np.max(np.abs(out)) + 1e-12), t0, 1.0)
    add_at(lay_R, out / (np.max(np.abs(out)) + 1e-12), t0, 0.96)
riser(B_LBUILD, B_DREAD)
riser(B_HBUILD, B_HOPE)
commit(lay_L, lay_R, 0.09)

# faint atmosphere in the intro/breakdowns so nothing is clinically empty
clear()
air = signal.sosfilt(signal.butter(4, [150, 1400], "bandpass", fs=SR, output="sos"),
                     rng.standard_normal(N))
air /= np.max(np.abs(air)) + 1e-12
air_env = slow_noise(0.05, 0.4, 1.0)
edge = np.clip((bar_t(B_LOVE) - t) / 12.0, 0, 1) + \
    np.where((t >= bar_t(B_LOSS)) & (t < bar_t(B_LBUILD)), 0.7, 0.0) + \
    np.where((t >= bar_t(B_SAD)) & (t < bar_t(B_HBUILD)), 0.7, 0.0)
lay_L[:] = air * air_env * np.clip(edge, 0, 1)
lay_R[:] = air * air_env[::-1] * np.clip(edge, 0, 1)
commit(lay_L, lay_R, 0.05)
print("risers + atmosphere committed")


# ---------------------------------------------------------------- master
# low-end weight + a gentle tanh bus limiter (the psy-master "glue").

fade(mix_L, fade_in=0.4, fade_out=9.0)
fade(mix_R, fade_in=0.4, fade_out=9.0)

for ch in (mix_L, mix_R):
    ch += 0.30 * signal.sosfilt(signal.butter(2, 95, "low", fs=SR, output="sos"), ch)

peak = max(np.max(np.abs(mix_L)), np.max(np.abs(mix_R))) + 1e-12
mix_L = np.tanh(1.35 * mix_L / peak) / np.tanh(1.35) * 0.88
mix_R = np.tanh(1.35 * mix_R / peak) / np.tanh(1.35) * 0.88

stereo = np.empty((N, 2))
stereo[:, 0] = mix_L
stereo[:, 1] = mix_R
pcm = (stereo * 32767.0).astype(np.int16)

OUT_DIR = "/workspace/music"
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, "lost_v3.wav")
with wave.open(OUT, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())

print(f"\nCreated: {os.path.abspath(OUT)}")
print(f"Duration: {N / SR:.1f} s  |  {SR} Hz stereo, 16-bit PCM  |  {BPM:.0f} BPM")

MP3 = os.path.join(OUT_DIR, "lost_v3.mp3")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", OUT,
                "-vn", "-ar", "44100", "-ac", "2", "-b:a", "192k", MP3],
               check=True)
print(f"Created: {os.path.abspath(MP3)}  (192k mp3)")

print("\nSection map:")
SECTIONS = [("INTRO", 0), ("hats+bass creep", B_INTRO2), ("LOVE drop", B_LOVE),
            ("CONFUSION (acid)", B_CONF), ("LOSS breakdown", B_LOSS),
            ("build", B_LBUILD), ("DREAD dark drop", B_DREAD),
            ("dip", B_DDIP), ("dread wave 2", B_DREAD2),
            ("SADNESS breakdown", B_SAD), ("hope build", B_HBUILD),
            ("HOPE euphoric drop", B_HOPE), ("outro", B_OUT)]
for name, b in SECTIONS:
    print(f"  {bar_t(b):6.1f} s  bar {b:3d}  {name}")
print(f"  {DURATION:6.1f} s  end")

print("\nPer-section RMS (dread + hope drops should be loudest):")
for (name, b0), (_, b1) in zip(SECTIONS, SECTIONS[1:] + [("end", None)]):
    i0 = int(bar_t(b0) * SR)
    i1 = int(bar_t(b1) * SR) if b1 is not None else N
    r = np.sqrt(np.mean(mix_L[i0:i1] ** 2 + mix_R[i0:i1] ** 2) / 2)
    print(f"  {name:24s} {r:.3f}")
