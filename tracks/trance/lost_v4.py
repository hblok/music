#!/usr/bin/env python3
"""
lost_v4.py — "Lost (Trance)" (~6:50, 130 BPM). A trance reworking of the
ambient "lost" journey — love, confusion, loss, dread, sadness, hope —
told as ONE cohesive emotional-trance piece rather than six separate
sections.

v4 change: the rolling octave bass was warmed (the "warmth recipe" — see
trance/CLAUDE.md). v3's bass had an acid bite — a raw saw plus a sharp
resonant peak (Q=3.5) screaming at the cutoff, hard-clipped at drive
1.6–1.9. Now the spectrum is rolled off (1/k^1.3), the resonance is
gentle (Q=1.2, low blend), and the drive is soft. Notes/pattern unchanged.

The cohesion comes from three things kept constant across the whole track:
  * ONE chord loop — Bm-G-D-A (vi-IV-I-V). D major and its relative B minor
    share the same seven notes, so the music can read bright (resolving to D)
    or melancholic (resolving to B) WITHOUT changing the harmonic language.
  * ONE recurring theme — stated in every section, bright in love/hope and
    sad in loss/dread/sadness, on lead, piano or cello.
  * ONE set of instruments — a warm detuned lead, a glassy pluck arpeggio,
    pads, piano and cello — reused throughout; no section introduces a
    foreign timbre.

Crucially: the "dread / angst" (Munch's Scream) is SADNESS, not horror — it
is the cathartic minor climax where the theme soars big over a driving but
warm beat, cello doubling underneath. No acid, no dissonant stabs.

  0:00  INTRO         Kick + atmosphere; pluck and warm bass roll in.
  0:30  LOVE  (drop)  Uplifting groove; the theme (bright) on the warm lead.
  1:13  CONFUSION     Same groove, but the D chord flickers major/minor and a
                      borrowed Bb destabilises it; the theme fragments and
                      drifts off the beat.
  2:01  LOSS (break)  The beat drops; piano and cello carry the SAD theme;
                      a lone heartbeat; then a build.
  2:56  DREAD (drop)  The cathartic SAD climax: the theme soars on the lead
                      with cello an octave below, big minor-coloured pads,
                      driving warm beat. A mid-drop dip, then the fullest wave.
  4:11  SADNESS(brk)  Bare aftermath: a theme fragment on solo piano, cello.
  4:41  HOPE  (drop)  The theme reborn bright and resolved; full warm groove,
                      glittering plucks. Then the outro strips back and fades.

Everything is synthesized (numpy + scipy); no samples. Output:
/workspace/music/lost_v5.wav + lost_v5.mp3 (192k, ffmpeg).
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

rng = np.random.default_rng(130)

BPM = 130.0
BEAT = 60.0 / BPM
BAR = BEAT * 4
STEP = BEAT / 4
GRID0 = 0.5


def bar_t(b, beat=0.0):
    return GRID0 + b * BAR + beat * BEAT


# ----------------------------------------------------- section boundaries (bars)
B_INTRO2 = 8
B_LOVE = 16
B_CONF = 40
B_LOSS = 64
B_LBUILD = 88
B_DREAD = 96
B_DDIP = 120
B_DREAD2 = 124
B_SAD = 136
B_HBUILD = 152
B_HOPE = 160
B_OUT = 200
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


# ============================================================= harmony + theme
# ONE progression for the whole track (2 bars per chord). Confusion swaps in a
# minor/borrowed variant to destabilise without leaving the palette.
# chord = (bass_root_midi, mid-register voicing for pads/pluck)

Bm = (35, (54, 59, 62, 66))     # B  D  F#
G = (31, (50, 55, 59, 62))      # G  B  D
DM = (38, (54, 57, 62, 66))     # D  F# A
AM = (33, (52, 57, 61, 64))     # A  C# E
Dm = (38, (53, 57, 62, 65))     # D  F  A   (the confusion flicker)
Bb = (34, (53, 58, 62, 65))     # Bb D  F   (borrowed, destabiliser)

PROG = [Bm, G, DM, AM]
CONF = [Bm, G, Dm, Bb]

CHORD_AT = [Bm] * B_END


def fill(b0, b1, seq, bars_each):
    i, b = 0, b0
    while b < b1:
        for _ in range(bars_each):
            if b < b1:
                CHORD_AT[b] = seq[i % len(seq)]
                b += 1
        i += 1


fill(0, B_CONF, PROG, 2)
fill(B_CONF, B_LOSS, CONF, 2)
fill(B_LOSS, B_END, PROG, 2)

# The recurring theme. Same rhythm/contour in two colourings: BRIGHT resolves
# up to D (love/hope), SAD sinks to B / the relative minor (loss/dread/sad).
# (midi, beats), one 8-bar statement over Bm-G-D-A.
THEME_BRIGHT = [(66, 1), (69, 1), (74, 2), (73, 2), (71, 2),        # Bm
                (71, 1), (67, 1), (69, 2), (66, 2), (62, 2),         # G
                (62, 1), (66, 1), (69, 2), (73, 2), (74, 2),         # D
                (76, 1), (74, 1), (73, 1), (71, 1), (69, 2), (74, 2)]  # A -> D
THEME_SAD = [(62, 1), (66, 1), (69, 2), (67, 2), (66, 2),            # Bm
             (66, 1), (62, 1), (64, 2), (62, 2), (59, 2),            # G
             (59, 1), (62, 1), (66, 2), (64, 2), (62, 2),            # D
             (62, 1), (61, 1), (59, 1), (57, 1), (59, 2), (54, 2)]   # A -> B
FRAG_SAD = [(62, 1), (66, 1), (69, 2), (67, 2), (66, 2)]             # 2-bar hook


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
# a downsweep (reverse-filtered fall) to lead smoothly INTO the breakdowns
DOWN = np.ascontiguousarray(CRASH[::-1])


def kick_gain(b):
    s = section_of(b)
    if s in ("loss", "sad", "hbuild"):
        return 0.0
    if s == "lbuild":
        return 0.0 if b < B_LBUILD + 4 else 0.7
    if s == "intro":
        return 0.0 if b < 4 else 0.78
    if s == "intro2":
        return 0.88
    if s == "out":
        return 0.92 if b < B_OUT + 8 else 0.7
    return 1.0


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

pump = np.ones(N)
for b in range(B_END):
    if kick_gain(b) <= 0:
        continue
    i0, i1 = int(bar_t(b) * SR), int(bar_t(b + 1) * SR)
    seg = (t[i0:i1] - bar_t(b)) % BEAT
    pump[i0:i1] = np.minimum(pump[i0:i1], 0.32 + 0.68 * (1 - np.exp(-seg / 0.085)))

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
commit(lay_L, lay_R, 0.075)
print("hats committed")

clear()
for b in range(B_END):
    s = section_of(b)
    if s not in ("love", "conf", "dread", "hope", "out"):
        continue
    for beat in (1, 3):
        p = 0.42 if beat == 1 else 0.58
        place_pan(lay_L, lay_R, CLAP, bar_t(b, beat), 1.0, p)
commit(lay_L, lay_R, 0.10)
print("clap committed")

clear()
for b in range(B_HOPE, B_OUT):
    for e in range(8):
        g = 0.7 if e % 2 == 0 else 0.45
        place_pan(lay_L, lay_R, RIDE, bar_t(b, e * 0.5), g, 0.5)
for b in range(B_DREAD2, B_SAD):                         # gentle ride in the sad climax too
    for e in range(8):
        place_pan(lay_L, lay_R, RIDE, bar_t(b, e * 0.5), 0.5 if e % 2 == 0 else 0.32, 0.5)
commit(lay_L, lay_R, 0.045)
print("ride committed")

clear()
for b, g in [(B_LOVE, 0.9), (B_CONF, 0.6), (B_DREAD, 1.0), (B_DREAD2, 0.7),
             (B_HOPE, 1.0), (B_OUT, 0.6)]:
    place_pan(lay_L, lay_R, CRASH, bar_t(b), g, 0.5)
for b in (B_LOVE, B_DREAD, B_HOPE):
    add_at(lay_L, RCYM, bar_t(b) - RCYM.shape[0] / SR, 0.8)
    add_at(lay_R, RCYM, bar_t(b) - RCYM.shape[0] / SR, 0.7)
# downsweeps INTO the breakdowns so the beat doesn't just stop dead
for b in (B_LOSS, B_SAD):
    add_at(lay_L, DOWN, bar_t(b) - DOWN.shape[0] / SR, 0.55)
    add_at(lay_R, DOWN, bar_t(b) - DOWN.shape[0] / SR, 0.5)
commit(lay_L, lay_R, 0.05)
print("crashes + downsweeps committed")

clear()
def roll(b0, b1, base):
    nbars = b1 - b0
    for b in range(b0, b1):
        u = (b - b0) / nbars
        div = 4 if u < 0.5 else (8 if u < 0.85 else 16)
        for s in range(div):
            g = base * (0.4 + 0.6 * u) * (0.7 + 0.3 * (s % 2))
            place_pan(lay_L, lay_R, SNARE, bar_t(b, s * 4.0 / div), g, 0.5)
roll(B_LBUILD, B_DREAD, 0.75)
roll(B_HBUILD, B_HOPE, 0.8)
commit(lay_L, lay_R, 0.09)
print("rolls committed")


# ============================================================= bass (unified)

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
        x += np.sin(2 * np.pi * k * f * td) / k ** 1.3      # rolled-off, rounder
    y = signal.sosfilt(signal.butter(2, cutoff, "low", fs=SR, output="sos"), x)
    bpk, apk = signal.iirpeak(cutoff, Q=1.2, fs=SR)         # gentle, not nasal
    y = y + 0.3 * signal.lfilter(bpk, apk, y)
    y += 0.5 * np.sin(2 * np.pi * (f / 2) * td)             # round sub for body
    y = np.tanh(drive * y)                                  # soft, not crunchy
    y *= (1 - np.exp(-td / 0.004)) * np.clip((dur - td) / 0.02, 0, 1)
    bass_cache[key] = y / (np.max(np.abs(y)) + 1e-12)
    return bass_cache[key]


# SAME rolling root+octave pattern in every drop — only cutoff/drive differ.
BASS_PAT = [(0, 0, 0.8), (1, 12, 0.9), (2, 0, 0.8), (3, 12, 0.9)]
BASS_CUT = {"love": 520, "conf": 470, "dread": 440, "hope": 600, "out": 460}
BASS_DRV = {"love": 0.9, "conf": 1.0, "dread": 1.1, "hope": 0.9, "out": 0.9}
clear()
for b in range(B_END):
    s = section_of(b)
    root = CHORD_AT[b][0]
    if s in BASS_CUT:
        cut, drive = BASS_CUT[s], BASS_DRV[s]
    elif s == "lbuild" and b >= B_LBUILD + 4:
        cut, drive, root = 380, 1.0, 38
    else:
        continue
    # filter the last 2 bars down into each breakdown for a smooth exit
    if section_of(b + 2) in ("loss", "sad") and s in BASS_CUT:
        cut *= 0.6
    for beat in range(4):
        for sx, off, gg in BASS_PAT:
            x = bass_note(root + off, cut, drive)
            tt = bar_t(b, beat + sx * 0.25)
            add_at(lay_L, x, tt, gg)
            add_at(lay_R, x, tt, gg)
commit(lay_L, lay_R, 0.30, env=pump)
print(f"bass committed ({len(bass_cache)} cached)")

# a soft sustained sub under the dread for emotional weight (not a hard pedal)
clear()
for b in range(B_DREAD, B_SAD):
    f = midi_to_hz(CHORD_AT[b][0] - 12)
    seg_n = int(BAR * SR)
    td = np.arange(seg_n) / SR
    sub = np.sin(2 * np.pi * f * td) * np.minimum(np.clip(td / 0.05, 0, 1),
                                                  np.clip((BAR - td) / 0.1, 0, 1))
    add_at(lay_L, sub, bar_t(b), 0.8)
    add_at(lay_R, sub, bar_t(b), 0.8)
commit(lay_L, lay_R, 0.10, env=0.5 + 0.5 * pump)
print("dread sub committed")


# ============================================================= pluck arp

pluck_cache = {}


def pluck(midi, dur=STEP * 3):
    if midi in pluck_cache:
        return pluck_cache[midi]
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    v = np.zeros(n)
    for det in (0.998, 1.0, 1.002):
        for k in range(1, min(12, int(7000 / f)) + 1):
            v += np.sin(2 * np.pi * k * f * det * td) / k ** 1.2
    v = signal.sosfilt(signal.butter(2, 3800, "low", fs=SR, output="sos"), v)
    v *= (1 - np.exp(-td / 0.003)) * np.exp(-td * 9.0)
    pluck_cache[midi] = v / (np.max(np.abs(v)) + 1e-12)
    return pluck_cache[midi]


ARP_PAT = [0, 1, 2, 3, 2, 1, 3, 2]
clear()
for b in range(B_END):
    s = section_of(b)
    if s not in ("love", "conf", "dread", "hope", "out"):
        continue
    voicing = CHORD_AT[b][1]
    notes = list(voicing) + [voicing[1] + 12]
    g0 = {"love": 0.7, "conf": 0.65, "dread": 0.6, "hope": 0.8, "out": 0.6}[s]
    for sx in range(16):
        idx = ARP_PAT[sx % len(ARP_PAT)] % len(notes)
        m = notes[idx]
        pan = 0.5 + 0.4 * (idx / (len(notes) - 1) - 0.5)
        place_pan(lay_L, lay_R, pluck(m), bar_t(b, sx * 0.25),
                  g0 * (0.9 if sx % 2 else 1.0), pan)
lay_L = reverb(lay_L, IR_L, 0.3)
lay_R = reverb(lay_R, IR_R, 0.3)
commit(lay_L, lay_R, 0.15, env=0.6 + 0.4 * pump)
print(f"pluck arp committed ({len(pluck_cache)} cached)")


# ============================================================= warm lead
# Fixed from v3: warm detuned saw, harmonics rolled off, low cutoff, a sub
# octave for body, no hard distortion — round and singing, never squeaky.

def lead_phrase(notes, lowpass=2800, detune=(0.996, 1.0, 1.004), sub=0.3):
    total = sum(d for _, d in notes) * BEAT
    n = int((total + 2.0) * SR)
    tt = np.arange(n) / SR
    f = glide_curve([(m, d * BEAT) for m, d in notes], n, tau=0.05)
    vibe = 1.0 + 0.003 * np.sin(2 * np.pi * 5.2 * tt) * np.clip(tt / 1.2, 0, 1)
    K = max(3, int(5000 / np.max(f)))
    L = np.zeros(n)
    R = np.zeros(n)
    for j, det in enumerate(detune):
        ph = 2 * np.pi * np.cumsum(f * det * vibe) / SR
        v = np.zeros(n)
        for k in range(1, K + 1):
            v += np.sin(k * ph) / k ** 1.4               # rolled-off = warm, not buzzy
        pan = (j / (len(detune) - 1) - 0.5)
        L += v * (0.6 + 0.4 * (0.5 - pan))
        R += v * (0.6 + 0.4 * (0.5 + pan))
    ph0 = 2 * np.pi * np.cumsum(f * vibe) / SR
    body = np.sin(ph0 / 2.0) * sub                       # sub octave for warmth
    L += body
    R += body
    env = np.minimum(np.clip(tt / 0.10, 0, 1), np.clip((total + 0.5 - tt) / 1.4, 0, 1))
    sos = signal.butter(2, lowpass, "low", fs=SR, output="sos")
    L = signal.sosfilt(sos, L * env)
    R = signal.sosfilt(sos, R * env)
    peak = max(np.max(np.abs(L)), np.max(np.abs(R)), 1e-12)
    return L / peak, R / peak


DELAY = 0.75 * BEAT


def place_lead(layL, layR, LR, t0, gain):
    L, R = LR
    add_at(layL, L, t0, gain)
    add_at(layR, R, t0, gain)
    add_at(layL, R, t0 + DELAY, gain * 0.26)             # ping-pong echo
    add_at(layR, L, t0 + DELAY, gain * 0.26)


clear()
LEAD_BRIGHT = lead_phrase(THEME_BRIGHT, lowpass=2900)
LEAD_SAD = lead_phrase(THEME_SAD, lowpass=2500)
# love: gentle, mid register
place_lead(lay_L, lay_R, LEAD_BRIGHT, bar_t(B_LOVE + 8), 0.8)
place_lead(lay_L, lay_R, LEAD_BRIGHT, bar_t(B_LOVE + 16), 0.85)
# confusion: the theme, but fragmented and shoved off the beat = unease
CONF_FRAG = lead_phrase(FRAG_SAD, lowpass=2700)
for b0, off in [(B_CONF + 2, 1.5), (B_CONF + 7, 0.5), (B_CONF + 12, 2.5),
                (B_CONF + 17, 1.0), (B_CONF + 21, 0.5)]:
    place_lead(lay_L, lay_R, CONF_FRAG, bar_t(b0, off), 0.6)
# dread: the SAD theme soaring — the cathartic climax (loud but melancholic)
place_lead(lay_L, lay_R, LEAD_SAD, bar_t(B_DREAD + 8), 0.95)
place_lead(lay_L, lay_R, LEAD_SAD, bar_t(B_DREAD2 + 4), 1.0)
place_lead(lay_L, lay_R, LEAD_SAD, bar_t(B_DREAD2 + 12), 1.0)
# hope: the theme reborn bright and resolved
place_lead(lay_L, lay_R, LEAD_BRIGHT, bar_t(B_HOPE + 8), 0.95)
place_lead(lay_L, lay_R, LEAD_BRIGHT, bar_t(B_HOPE + 16), 1.0)
place_lead(lay_L, lay_R, LEAD_BRIGHT, bar_t(B_HOPE + 24), 1.0)
place_lead(lay_L, lay_R, LEAD_BRIGHT, bar_t(B_HOPE + 32), 0.9)
lay_L = reverb(lay_L, IR_L, 0.38)
lay_R = reverb(lay_R, IR_R, 0.38)
commit(lay_L, lay_R, 0.20)
print("warm lead committed")


# ============================================================= cello
# Doubles the theme an octave below in the dread (weight/sorrow); carries the
# lament in the loss & sadness breakdowns.

def cello_line(notes, lowpass=1900):
    total = sum(d for _, d in notes) * BEAT
    n = int((total + 0.8) * SR)
    td = np.arange(n) / SR
    f = glide_curve([(m, d * BEAT) for m, d in notes], n, tau=0.05)
    vib = 1.0 + 0.005 * np.sin(2 * np.pi * 5.0 * td) * np.clip(td / 0.7, 0, 1)
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    out = np.zeros(n)
    for k in range(1, 13):
        out += np.sin(k * ph) / k
    bow = signal.sosfilt(signal.butter(2, [80, 2400], "bandpass", fs=SR, output="sos"),
                         rng.standard_normal(n))
    out = out / (np.max(np.abs(out)) + 1e-12) + 0.07 * bow
    env = np.minimum(np.clip(td / 0.25, 0, 1), np.clip((total + 0.1 - td) / 0.5, 0, 1))
    out = signal.sosfilt(signal.butter(2, lowpass, "low", fs=SR, output="sos"), out * env)
    return out / (np.max(np.abs(out)) + 1e-12)


clear()
SAD_LOW = [(m - 12, d) for m, d in THEME_SAD]
cello_dread = cello_line(SAD_LOW)
add_at(lay_L, cello_dread, bar_t(B_DREAD2 + 4), 0.8)
add_at(lay_R, cello_dread, bar_t(B_DREAD2 + 4), 0.8)
add_at(lay_L, cello_dread, bar_t(B_DREAD2 + 12), 0.8)
add_at(lay_R, cello_dread, bar_t(B_DREAD2 + 12), 0.8)
# loss & sadness laments (the theme, slow, low)
cello_loss = cello_line([(m - 12, d * 1.5) for m, d in FRAG_SAD])
add_at(lay_L, cello_loss, bar_t(B_LOSS + 4), 0.8)
add_at(lay_R, cello_loss, bar_t(B_LOSS + 4), 0.8)
add_at(lay_L, cello_loss, bar_t(B_LOSS + 14), 0.75)
add_at(lay_R, cello_loss, bar_t(B_LOSS + 14), 0.75)
add_at(lay_L, cello_loss, bar_t(B_SAD + 6), 0.75)
add_at(lay_R, cello_loss, bar_t(B_SAD + 6), 0.75)
lay_L = reverb(lay_L, IR_L, 0.45)
lay_R = reverb(lay_R, IR_R, 0.45)
commit(lay_L, lay_R, 0.18)
print("cello committed")


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


clear()
def place_piano_theme(notes, t0, gain, lh_root=None):
    tm = t0
    for m, d in notes:
        place_pan(lay_L, lay_R, piano_note(m, d * BEAT), tm, gain,
                  np.clip(0.5 + (m - 64) * 0.012, 0.25, 0.75))
        tm += d * BEAT
    if lh_root is not None:                              # left-hand octave bed
        place_pan(lay_L, lay_R, piano_note(lh_root, (tm - t0)), t0, gain * 0.5, 0.4)


# loss: the SAD theme on piano, with a slow chordal bed
place_piano_theme(THEME_SAD, bar_t(B_LOSS + 8), 0.85)
place_piano_theme(THEME_SAD, bar_t(B_LOSS + 16), 0.8)
# sadness: just the fragment, bare and slow
place_piano_theme([(m, d * 1.5) for m, d in FRAG_SAD], bar_t(B_SAD + 2), 0.8)
place_piano_theme([(m, d * 1.5) for m, d in FRAG_SAD], bar_t(B_SAD + 9), 0.75)
# outro: a last bright fragment echo
place_piano_theme([(m, d) for m, d in FRAG_SAD[:4]], bar_t(B_OUT + 8), 0.6)
lay_L = reverb(lay_L, IR_L, 0.5)
lay_R = reverb(lay_R, IR_R, 0.5)
commit(lay_L, lay_R, 0.24)
print(f"piano committed ({len(piano_cache)} cached)")


# ============================================================= pads + strings

def pad_chord(chord, dur, attack, release, lowpass, detune=0.0012):
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
LP = {"intro": 1000, "intro2": 1000, "love": 1300, "conf": 900, "loss": 850,
      "lbuild": 800, "dread": 750, "sad": 800, "hbuild": 1100, "hope": 1500, "out": 1300}
PG = {"intro": 0.7, "intro2": 0.7, "love": 0.6, "conf": 0.6, "loss": 0.95,
      "lbuild": 0.85, "dread": 0.8, "sad": 0.95, "hbuild": 0.9, "hope": 0.65, "out": 0.6}
bb = 0
while bb < B_END:
    s = section_of(bb)
    chord = CHORD_AT[bb][1]
    det = 0.006 if s == "conf" else 0.0014
    # pads ring 2.5 s past their 2 bars so chords overlap across boundaries
    pL, pR = pad_chord(chord, 2 * BAR + 2.5, attack=1.5, release=2.5,
                       lowpass=LP[s], detune=det)
    add_at(lay_L, pL, bar_t(bb), PG[s])
    add_at(lay_R, pR, bar_t(bb), PG[s])
    bb += 2
lay_L = reverb(lay_L, IR_L, 0.45)
lay_R = reverb(lay_R, IR_R, 0.45)
pad_env = np.where((t < bar_t(B_LOSS)) | ((t >= bar_t(B_DREAD)) & (t < bar_t(B_SAD))) |
                   (t >= bar_t(B_HOPE)), pump, 1.0)
commit(lay_L, lay_R, 0.17, env=0.6 + 0.4 * pad_env)
print("pads committed")


# ============================================================= heartbeat (breaks)

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
    if section_of(b) not in ("loss", "sad"):
        continue
    for beat in (0, 2):
        add_at(lay_L, THUMP, bar_t(b, beat), 0.9)
        add_at(lay_R, THUMP, bar_t(b, beat), 0.9)
        add_at(lay_L, THUMP, bar_t(b, beat + 0.5), 0.55)
        add_at(lay_R, THUMP, bar_t(b, beat + 0.5), 0.55)
commit(lay_L, lay_R, 0.18)
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
commit(lay_L, lay_R, 0.08)

clear()
air = signal.sosfilt(signal.butter(4, [150, 1400], "bandpass", fs=SR, output="sos"),
                     rng.standard_normal(N))
air /= np.max(np.abs(air)) + 1e-12
air_env = slow_noise(0.05, 0.4, 1.0)
edge = np.clip((bar_t(B_LOVE) - t) / 12.0, 0, 1) + \
    np.where((t >= bar_t(B_LOSS)) & (t < bar_t(B_LBUILD)), 0.6, 0.0) + \
    np.where((t >= bar_t(B_SAD)) & (t < bar_t(B_HBUILD)), 0.6, 0.0)
lay_L[:] = air * air_env * np.clip(edge, 0, 1)
lay_R[:] = air * air_env[::-1] * np.clip(edge, 0, 1)
commit(lay_L, lay_R, 0.05)
print("risers + atmosphere committed")


# ---------------------------------------------------------------- master

fade(mix_L, fade_in=0.4, fade_out=9.0)
fade(mix_R, fade_in=0.4, fade_out=9.0)

for ch in (mix_L, mix_R):
    ch += 0.28 * signal.sosfilt(signal.butter(2, 95, "low", fs=SR, output="sos"), ch)

peak = max(np.max(np.abs(mix_L)), np.max(np.abs(mix_R))) + 1e-12
mix_L = np.tanh(1.3 * mix_L / peak) / np.tanh(1.3) * 0.88
mix_R = np.tanh(1.3 * mix_R / peak) / np.tanh(1.3) * 0.88

stereo = np.empty((N, 2))
stereo[:, 0] = mix_L
stereo[:, 1] = mix_R
pcm = (stereo * 32767.0).astype(np.int16)

OUT_DIR = "/workspace/music"
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, "lost_v5.wav")
with wave.open(OUT, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())

print(f"\nCreated: {os.path.abspath(OUT)}")
print(f"Duration: {N / SR:.1f} s  |  {SR} Hz stereo, 16-bit PCM  |  {BPM:.0f} BPM, Bm-G-D-A")

MP3 = os.path.join(OUT_DIR, "lost_v5.mp3")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", OUT,
                "-vn", "-ar", "44100", "-ac", "2", "-b:a", "192k", MP3],
               check=True)
print(f"Created: {os.path.abspath(MP3)}  (192k mp3)")

print("\nSection map:")
SECTIONS = [("INTRO", 0), ("hats+bass creep", B_INTRO2), ("LOVE drop", B_LOVE),
            ("CONFUSION", B_CONF), ("LOSS breakdown", B_LOSS), ("build", B_LBUILD),
            ("DREAD sad drop", B_DREAD), ("dip", B_DDIP), ("dread wave 2", B_DREAD2),
            ("SADNESS breakdown", B_SAD), ("hope build", B_HBUILD),
            ("HOPE euphoric drop", B_HOPE), ("outro", B_OUT)]
for name, b in SECTIONS:
    print(f"  {bar_t(b):6.1f} s  bar {b:3d}  {name}")
print(f"  {DURATION:6.1f} s  end")

print("\nPer-section RMS (drops loud, breakdowns quiet, dread = climax):")
for (name, b0), (_, b1) in zip(SECTIONS, SECTIONS[1:] + [("end", None)]):
    i0 = int(bar_t(b0) * SR)
    i1 = int(bar_t(b1) * SR) if b1 is not None else N
    r = np.sqrt(np.mean(mix_L[i0:i1] ** 2 + mix_R[i0:i1] ** 2) / 2)
    print(f"  {name:24s} {r:.3f}")
