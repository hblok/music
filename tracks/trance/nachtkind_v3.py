#!/usr/bin/env python3
"""
nachtkind_v3.py — "Nachtkind" (~5:35, 139 BPM, G minor). The Frankfurt / Eye Q
track retold as a SONG (design notes: nachtkind_v3_notes.md). Everything that
makes v2 nachtkind stays — the 909 dry kit, the dry-drums/wet-melodics
contrast, the gothic M1 piano centerpiece, i–VI–VII–V (Gm–Eb–F–D) with the F#
of the D chord as the single gothic color, no supersaws, no snare rolls. What
changes is the composition: v2 was a DJ-tool arc; v3 has the song doctrine.

THE REFRAIN — the gothic piano theme rewritten as a Q/A cell (8 bars, one
loop pass per half): the QUESTION climbs the i–VI rise and hangs on the F#
(the leading tone left unresolved — the gothic color as the question); the
ANSWER, same rhythm, falls through F and resolves F#->G across the barline.
Identical melody in every chorus; all variation lives in the verses.

THE DUET, EARNED — v2 stacked the lead over the piano by default; v3 makes
the relationship progressive: chorus 1 piano alone; chorus 2 the lead enters
ONLY to answer the phrase tails (composed echoes); choruses 3–4 the full
stacked duet — lead soaring the refrain itself, piano under it, octave
shimmer joining in the final wave.

  0:00  THESIS       Solo gothic piano states the refrain once, very wet;
                     the low G rings under the dry kick entry.
  0:14  groove       Kick, hats, open hat, shaker assemble fast (8 bars).
  0:28  verse 1      Dark bass creeps in; the piano sings low Q/A verse
                     pairs (question hangs on D, answer resolves F#->G);
                     claps join halfway.
  0:56  pre-chorus   LH piano octaves + a rising line ending ON the hanging
                     F# — resolved by the chorus' first G across the seam.
  1:10  CHORUS 1     The refrain, piano alone over the full groove.
  1:37  verse 2      Development: the dark chord stab enters offbeat, verse
                     lines gain octave doubling, the bass opens up.
  2:05  pre-chorus   As before, octave-doubled.
  2:18  CHORUS 2     Refrain + the lead answering each phrase tail.
  2:46  bridge       Drums drop; pads + the QUESTION-half only, F# hanging,
                     never answered; the kick walks back in; the build ends
                     at ONE BEAT of near-silence — a reverse cymbal swells
                     into it, a lone piano pickup hangs in it —
  3:14  CHORUS 3     The fusion slams in on beat 2: lead carries the refrain,
                     piano under it, 909 ride enters.
  3:41  CHORUS 4     + octave shimmer + the stab: the fullest wave.
  4:09  deconstruction  Lead exits, the piano carries on, thins; then piano
                     exits, pads return, the bass filters down.
  5:04  DJ outro     Kick, hats, atmosphere.
  5:18  bookend      The kick stops. Solo piano asks the QUESTION once more —
                     and the final G minor chord answers it. Rings out.

Everything synthesized (numpy + scipy); drums bone dry, melodics through the
long dark hall. Output: /workspace/music/nachtkind_v3.wav + .mp3 (192k).
"""

"""
How the song treatment landed:

    The refrain is an 8-bar Q/A cell over one i–VI–VII–V pass per half: the question climbs G→Bb→D→Eb…C→D and hangs on F#5 — the gothic leading tone left unresolved — and the answer, same rhythm, falls back through F and resolves F#→G across the barline. That F#→G semitone does double duty as the track's main seam device: both pre-choruses end on the hanging F# so the chorus's first G resolves them across the seam, and the final chord answers the bookend's question-half the same way.
    The duet is earned, per the notes: chorus 1 is piano alone; chorus 2 the lead appears only as two composed echoes per statement (entering on the piano's last note — answering the hang, then echoing the resolution up high); after the bridge's silent beat, choruses 3–4 are the full stacked duet with the lead carrying the refrain itself, ride entering, and the octave shimmer + stab joining only in the final wave.
    Thesis and bookend: solo wet piano states the full refrain at 0:00 (the low G rings under the dry kick entry at 0:14 — v2 took 42 s to get here); the ending mirrors it, but as the question-half only, so the final G-minor chord is what answers it. The bridge likewise plays only question fragments over pads — the answer is withheld until the fusion.
    Verses are piano, low register, as you chose: Q/A pairs where the question hangs on D4 and the answer resolves F#3→G3; verse 2 develops them with octave doubling, the offbeat stab, and the opened bass — the old "new element every 16 bars" engine now lives inside the verses.
    Eye Q rules intact: 909 kit bone dry, all melodics through the 6 s hall, no snare rolls (the build into the fusion is the walking kick + reverse cymbal swelling into the silent beat, measured 0.066 RMS against 0.199/0.230 around it), long deconstruction kept per your answer.

Statement count is 11 (fragments not counted), RMS arc: thesis 0.040 → chorus 1 0.211 → fusion 0.225 → chorus 4 0.232 loudest → bridge trough 0.054 → bookend 0.036. Ready for a listen — tech_noir_v3 is the remaining note doc whenever you want it.
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

rng = np.random.default_rng(1993)    # the year Brainchild came out

BPM = 139.0
BEAT = 60.0 / BPM
BAR = BEAT * 4
STEP = BEAT / 4
GRID0 = 0.5


def bar_t(b, beat=0.0):
    return GRID0 + b * BAR + beat * BEAT


# ----------------------------------------------------- section boundaries (bars)
B_GROOVE = 8      # dry kick + hats + shaker assemble
B_V1 = 16         # verse 1: dark bass, piano low Q/A pairs
B_PRE1 = 32       # pre-chorus: LH octaves + the rise
B_CH1 = 40        # CHORUS 1: refrain, piano alone
B_V2 = 56         # verse 2: + stab, octave doubling, bass opens
B_PRE2 = 72       # pre-chorus, doubled
B_CH2 = 80        # CHORUS 2: refrain + lead echoes
B_BR = 96         # bridge teardown: drums drop, question fragments
B_BR2 = 104       # kick walks back in; the build
B_CH3 = 112       # CHORUS 3: the fusion (slams on beat 2 after the silence)
B_CH4 = 128       # CHORUS 4: + shimmer + stab
B_DECON = 144     # lead exits, piano continues
B_DECON2 = 160    # piano exits, pads return, bass sweeps down
B_OUT = 176       # DJ outro
B_STOP = 184      # kick stops; solo piano bookend
B_END = 188


def section_of(b):
    for name, b0 in [("bookend", B_STOP), ("outro", B_OUT), ("decon2", B_DECON2),
                     ("decon", B_DECON), ("ch4", B_CH4), ("ch3", B_CH3),
                     ("build", B_BR2), ("bridge", B_BR), ("ch2", B_CH2),
                     ("pre2", B_PRE2), ("v2", B_V2), ("ch1", B_CH1),
                     ("pre1", B_PRE1), ("v1", B_V1), ("groove", B_GROOVE)]:
        if b >= b0:
            return name
    return "thesis"


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


# ------------------------------------------------------------ the melodies
# THE REFRAIN — 8 bars over i–VI–VII–V twice, identical in every chorus.
# (beat offset, midi, duration in beats, gain)

NK_REFRAIN = [
    # Q — climbs the i–VI rise, hangs on the F# (the gothic leading tone)
    (0, 67, 1, 1.0), (1, 70, 1, .85), (2, 74, 2, .90),      # Gm: G Bb D
    (4, 75, 1, 1.0), (5, 74, 1, .85), (6, 70, 2, .90),      # Eb: Eb D Bb
    (8, 72, 1, 1.0), (9, 74, 1, .85), (10, 77, 2, .90),     # F:  C D F
    (12, 72, 1, .90), (13, 74, 1, .90), (14, 78, 2, 1.0),   # D:  C D F# — HANG
    # A — same rhythm, falls through F, resolves F# -> G
    (16, 67, 1, 1.0), (17, 70, 1, .85), (18, 74, 2, .90),   # Gm
    (20, 75, 1, 1.0), (21, 74, 1, .85), (22, 70, 2, .90),   # Eb
    (24, 77, 1, 1.0), (25, 74, 1, .85), (26, 72, 2, .90),   # F:  F D C
    (28, 69, 1, .90), (29, 66, 1, .85), (30, 67, 2, 1.0),   # D:  A F# -> G
]
NK_QHALF = NK_REFRAIN[:12]                    # the question alone (bridge, bookend)

# THE VERSE — same Q/A discipline an octave down (the piano's low register):
# question hangs on D (off-tonic over the V), answer resolves F#3 -> G3.
NK_VERSE_Q = [
    (0, 55, 1, 1.0), (1, 58, 1, .85), (2, 62, 2, .90),      # Gm: G Bb D
    (4, 63, 1, 1.0), (5, 62, 1, .85), (6, 58, 2, .90),      # Eb
    (8, 60, 1, 1.0), (9, 62, 1, .85), (10, 57, 2, .90),     # F
    (12, 57, 1, .90), (13, 54, 1, .85), (14, 62, 2, 1.0),   # D — hangs on D4
]
NK_VERSE_A = NK_VERSE_Q[:9] + [
    (12, 57, 1, .90), (13, 54, 1, .85), (14, 55, 2, 1.0),   # D — F#3 -> G3
]

# pre-chorus rise: 4 bars climbing to end ON the hanging F# — the chorus'
# first G resolves it across the barline (the leading-tone pickup seam)
NK_RISE = [
    (0, 62, 1, .90), (1, 63, 1, .85), (2, 65, 2, .90),      # Gm: D Eb F
    (4, 63, 1, .90), (5, 65, 1, .85), (6, 67, 2, .90),      # Eb: Eb F G
    (8, 67, 1, .90), (9, 69, 1, .85), (10, 72, 2, .90),     # F:  G A C
    (12, 69, 1, .90), (13, 74, 1, .90), (14, 78, 2, 1.0),   # D:  A D F# — hang
]

# chorus-2 lead echoes: composed answers entering ON the piano's last note
ECHO_Q = [(78, 1), (74, 1), (78, 2)]          # answers the hang
ECHO_A = [(79, 1), (78, 1), (79, 2)]          # the F#->G resolution, echoed high

PHRASE_ROOTS = [43, 39, 41, 38, 43, 39, 41, 38]             # G Eb F D, per bar
THEME_LH = []
for i, root in enumerate(PHRASE_ROOTS):
    THEME_LH += [(4 * i, root, 2, .9), (4 * i, root + 12, 2, .7),
                 (4 * i + 2, root + 7, 2, .8), (4 * i + 2, root + 12, 2, .6)]

PAD_CHORDS = [(43, 55, 58, 62), (39, 51, 55, 58),           # Gm  Eb
              (41, 53, 57, 60), (38, 50, 54, 57)]           # F   D

HOOKS = 0                                                   # refrain statements


# ---------------------------------------------------------------- drums
# 909 school, ALL DRY (v2 kit verbatim).

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
RCYM = np.ascontiguousarray(CRASH[::-1][int(0.5 * SR):])    # 1.5 s reverse


def kick_gain(b):
    s = section_of(b)
    if s in ("thesis", "bridge", "bookend"):
        return 0.0
    if s == "build":
        return 0.55                      # walking back in
    if s == "groove":
        return 0.78
    if s in ("v1", "pre1"):
        return 0.85
    if s in ("ch1", "v2", "pre2", "ch2"):
        return 0.92                      # hold headroom before the fusion
    if s == "outro":
        return 0.95
    if s in ("decon", "decon2"):
        return 0.95
    return 1.0                           # ch3 / ch4


def silent_beat(b, beat):
    # the composed drop-silence: bar 112 beat 0 belongs to nobody
    return b == B_CH3 and beat < 1.0


lay_L = np.zeros(N)
lay_R = np.zeros(N)
for b in range(B_STOP):
    g = kick_gain(b)
    if g == 0.0:
        continue
    for beat in range(4):
        if silent_beat(b, beat):
            continue
        add_at(lay_L, KICK, bar_t(b, beat), g)
        add_at(lay_R, KICK, bar_t(b, beat), g)
commit(lay_L, lay_R, 0.34)
print("kick committed")

# hats: closed 16ths (skipping the open-hat slot) + accented offbeat open
lay_L[:] = 0.0
lay_R[:] = 0.0
CH_GAINS = [0.50, 0.25, 0.0, 0.30]
for b in range(B_STOP):
    s = section_of(b)
    if s in ("thesis", "bridge", "bookend"):
        continue
    g = 0.6 if s == "build" else 1.0
    for beat in range(4):
        if silent_beat(b, beat):
            continue
        for sx in range(4):
            if CH_GAINS[sx] == 0.0:
                continue
            gg = g * CH_GAINS[sx]
            add_at(lay_L, CHAT, bar_t(b, beat + sx * 0.25), gg * 0.9)
            add_at(lay_R, CHAT, bar_t(b, beat + sx * 0.25), gg)
        if b >= B_GROOVE + 2:
            add_at(lay_L, OHAT, bar_t(b, beat + 0.5), g)
            add_at(lay_R, OHAT, bar_t(b, beat + 0.5), g * 0.85)
commit(lay_L, lay_R, 0.085)
print("hats committed")

# ride: the fusion choruses only — it crowns the earned duet
lay_L[:] = 0.0
lay_R[:] = 0.0
for b in range(B_CH3, B_DECON):
    for e in range(8):
        if silent_beat(b, e * 0.5):
            continue
        g = 0.75 if e % 2 == 0 else 0.5
        add_at(lay_L, RIDE, bar_t(b, e * 0.5), g)
        add_at(lay_R, RIDE, bar_t(b, e * 0.5), g * 0.8)
commit(lay_L, lay_R, 0.065)
print("ride committed")

# claps: sparse, on 2 and 4
lay_L[:] = 0.0
lay_R[:] = 0.0
for b in range(B_STOP):
    s = section_of(b)
    if not (B_V1 + 8 <= b < B_BR or B_CH3 <= b < B_DECON2):
        continue
    for beat in (1, 3):
        if silent_beat(b, beat):
            continue
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
    if b < B_GROOVE + 4 or B_BR <= b < B_CH3:
        continue
    for beat in range(4):
        for sx in range(4):
            if silent_beat(b, beat + sx * 0.25):
                continue
            gg = SH_GAINS[sx]
            add_at(lay_L, SHAKER, bar_t(b, beat + sx * 0.25), gg * 0.7)
            add_at(lay_R, SHAKER, bar_t(b, beat + sx * 0.25), gg)
commit(lay_L, lay_R, 0.045)
print("shaker committed")

# crashes at boundaries; reverse cymbals lean INTO the big entries
lay_L[:] = 0.0
lay_R[:] = 0.0
for b, g in [(B_V1, 0.6), (B_CH1, 1.0), (B_V2, 0.6), (B_CH2, 0.9),
             (B_BR, 0.8), (B_CH4, 0.7), (B_DECON, 0.8), (B_DECON2, 0.6),
             (B_OUT, 0.6)]:
    add_at(lay_L, CRASH, bar_t(b), g * 0.9)
    add_at(lay_R, CRASH, bar_t(b), g)
add_at(lay_L, CRASH, bar_t(B_CH3, 1), 0.9)                  # the slam on beat 2
add_at(lay_R, CRASH, bar_t(B_CH3, 1), 1.0)
for b in (B_CH1, B_CH2):                                    # end exactly on the bar
    add_at(lay_L, RCYM, bar_t(b) - 1.5, 0.8)
    add_at(lay_R, RCYM, bar_t(b) - 1.5, 0.7)
# the bridge build's reverse cymbal swells INTO the silent beat
add_at(lay_L, RCYM, bar_t(B_CH3) - 1.5, 0.85)
add_at(lay_R, RCYM, bar_t(B_CH3) - 1.5, 0.75)
commit(lay_L, lay_R, 0.055)
print("crashes committed")


# ---------------------------------------------------------------- bass
# The warmed rolling octave bass (v2 recipe verbatim); cutoff = the
# transition tool.

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
        x += np.sin(2 * np.pi * k * f * td) / k ** 1.3      # rolled-off, rounder
    sos_lp = signal.butter(2, cutoff, "low", fs=SR, output="sos")
    y = signal.sosfilt(sos_lp, x)
    bpk, apk = signal.iirpeak(cutoff, Q=1.2, fs=SR)         # gentle, not nasal
    y = y + 0.3 * signal.lfilter(bpk, apk, y)
    y += 0.35 * np.sin(2 * np.pi * (f / 2) * td)            # round sub for body
    y = np.tanh(0.9 * y)                                    # soft, not crunchy
    y *= (1 - np.exp(-td / 0.004)) * np.clip((dur - td) / 0.02, 0, 1)
    y /= np.max(np.abs(y)) + 1e-12
    bass_cache[key] = y
    return y


def bass_cutoff(b):
    s = section_of(b)
    if s == "v1":
        return 290.0                                  # creeps in dark
    if s == "pre1":
        return 360.0
    if s in ("ch1", "v2", "pre2", "ch2"):
        return 540.0 + 80.0 * np.sin(2 * np.pi * (b - B_CH1) / 16)
    if s == "build":
        return 330.0                                  # returns dark
    if s in ("ch3", "ch4"):
        return 580.0 + 80.0 * np.sin(2 * np.pi * (b - B_CH3) / 16)
    if s == "decon":
        return 540.0
    if s == "decon2":                                 # sweeping back down
        return 540.0 - 220.0 * (b - B_DECON2) / (B_OUT - B_DECON2)
    return 320.0


def bass_root(b):
    if B_V1 <= b < B_OUT:
        return PHRASE_ROOTS[(b - B_V1) % 8] - 12      # follow the harmony
    return 31                                         # tonic pedal (G1)


BASS_PAT = [(0, 0, 0.70), (1, 12, 0.95), (2, 0, 0.80), (3, 12, 0.90)]

lay_L[:] = 0.0
lay_R[:] = 0.0
for b in range(B_OUT):
    if b < B_V1 or B_BR <= b < B_BR2 + 2:
        continue
    root = bass_root(b)
    cut = bass_cutoff(b)
    g = 0.75 if b < B_PRE1 else 1.0
    for beat in range(4):
        for sx, off, gg in BASS_PAT:
            if silent_beat(b, beat + sx * 0.25):
                continue
            x = bass_note(root + off, cut)
            add_at(lay_L, x, bar_t(b, beat + sx * 0.25), g * gg)
            add_at(lay_R, x, bar_t(b, beat + sx * 0.25), g * gg)
commit(lay_L, lay_R, 0.30)
print(f"bass committed ({len(bass_cache)} cached notes)")


# ---------------------------------------------------------------- piano
# The centerpiece and, in v3, the song's lead voice: it states the thesis,
# sings the verses low, carries the choruses, asks the bridge's question,
# and bookends the track. M1-era recipe verbatim: inharmonic partials, two
# detuned strings, hammer noise, LONG dark hall.

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


def place_line(notes, bar0, gain, oct_double=False, beat_off=0.0):
    t0 = bar_t(bar0, beat_off)
    for beat, m, d, g in notes:
        place_note(m, t0 + beat * BEAT, d * BEAT, gain * g)
        if oct_double:
            place_note(m + 12, t0 + beat * BEAT, d * BEAT, gain * g * 0.5)


def place_lh(bar0, gain):
    for beat, m, d, g in THEME_LH:
        place_note(m, bar_t(bar0) + beat * BEAT, d * BEAT, gain * g * 0.8)


def refrain(bar0, gain, lh=True, oct_double=False, skip_first=False):
    global HOOKS
    place_line(NK_REFRAIN[1:] if skip_first else NK_REFRAIN, bar0, gain,
               oct_double=oct_double)
    if lh:
        place_lh(bar0, gain)
    HOOKS += 1


# THE THESIS: solo, very wet; the low G rings under the kick entry
refrain(0, 0.85, lh=False)
place_note(43, bar_t(7, 2), 4.0, 0.6)                  # the ringing low G
# verse 1: low Q/A pairs, twice
for b0, notes, g in [(B_V1, NK_VERSE_Q, 0.75), (B_V1 + 4, NK_VERSE_A, 0.75),
                     (B_V1 + 8, NK_VERSE_Q, 0.80), (B_V1 + 12, NK_VERSE_A, 0.80)]:
    place_line(notes, b0, g)
# pre-chorus 1: LH octaves + the rise (twice), ending on the hanging F#
place_lh(B_PRE1, 0.9)
place_line(NK_RISE, B_PRE1, 0.8)
place_line(NK_RISE, B_PRE1 + 4, 0.85)
# CHORUS 1: the refrain, piano alone
refrain(B_CH1, 0.95)
refrain(B_CH1 + 8, 0.95)
# verse 2: development — octave doubling on the pairs
for b0, notes in [(B_V2, NK_VERSE_Q), (B_V2 + 4, NK_VERSE_A),
                  (B_V2 + 8, NK_VERSE_Q), (B_V2 + 12, NK_VERSE_A)]:
    place_line(notes, b0, 0.8, oct_double=True)
# pre-chorus 2: doubled
place_lh(B_PRE2, 0.9)
place_line(NK_RISE, B_PRE2, 0.8, oct_double=True)
place_line(NK_RISE, B_PRE2 + 4, 0.85, oct_double=True)
# CHORUS 2: the refrain (lead echoes placed with the lead)
refrain(B_CH2, 0.95)
refrain(B_CH2 + 8, 0.95)
# bridge: the QUESTION only, hanging, never answered
place_line(NK_QHALF, B_BR + 1, 0.80)
place_line(NK_QHALF, B_BR2 + 1, 0.70)
# the pickup hanging in the silent beat (the refrain's first G, early)
place_note(67, bar_t(B_CH3, 0.4), 1.2 * BEAT, 0.55)
# CHORUS 3: the fusion — statement 1's first note was the pickup
refrain(B_CH3, 0.90, skip_first=True)
refrain(B_CH3 + 8, 0.90)
# CHORUS 4: + octave doubling
refrain(B_CH4, 0.90, oct_double=True)
refrain(B_CH4 + 8, 0.90, oct_double=True)
# deconstruction: the piano carries on alone, thinning
refrain(B_DECON, 0.80)
refrain(B_DECON + 8, 0.70, lh=False)
# THE BOOKEND: the question once more — answered by the final G minor chord
place_line(NK_QHALF, B_STOP, 0.85)
for m in (43, 55, 62, 67, 74):
    place_note(m, bar_t(B_STOP + 4), 6.0, 0.9)

lay_L = reverb(lay_L, IR_L, wet=0.50)
lay_R = reverb(lay_R, IR_R, wet=0.50)
commit(lay_L, lay_R, 0.30)
print(f"piano committed ({len(piano_cache)} cached notes)")


# ---------------------------------------------------------------- pads

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


# a dark creep under verse 1 (the thesis stays truly solo)
pL, pR = pad_chord((31, 43, 50, 55, 58), (B_PRE1 - B_V1) * BAR + 4.0,
                   attack=9.0, release=5.0)
add_at(lay_L, pL, bar_t(B_V1), 0.6)
add_at(lay_R, pR, bar_t(B_V1), 0.6)
place_pads(B_BR, 16, 1.0)                             # the bridge bed
place_pads(B_CH3, 32, 0.45)                           # under the fusion
place_pads(B_DECON2, 16, 0.8)                         # the return
# outro residue ringing through the bookend to the end
pL, pR = pad_chord((43, 50, 55, 58), (B_END - B_OUT) * BAR + 8.0,
                   attack=6.0, release=8.0)
add_at(lay_L, pL, bar_t(B_OUT), 0.55)
add_at(lay_R, pR, bar_t(B_OUT), 0.55)

lay_L = reverb(lay_L, IR_L, wet=0.55)
lay_R = reverb(lay_R, IR_R, wet=0.55)
commit(lay_L, lay_R, 0.16)
print("pads committed")


# ---------------------------------------------------------------- lead
# The warm detuned analog lead (v2 recipe, parameterized by notes). In v3
# it earns its place: silent until chorus 2, where it only answers the
# piano's phrase tails; from chorus 3 it carries the refrain itself over
# the piano — the stacked duet as the payoff. Dotted-8th ping-pong delay.

def lead_phrase(notes):
    total = sum(d for _, d in notes) * BEAT
    n = int((total + 2.5) * SR)
    tt = np.arange(n) / SR
    f_curve = glide_curve([(m, d * BEAT) for m, d in notes], n, tau=0.06)
    vib = 1.0 + 0.003 * np.sin(2 * np.pi * 5.0 * tt) * np.clip(tt / 1.8, 0, 1)
    K = max(3, int(7000 / np.max(f_curve)))

    def reed(det):
        ph = 2 * np.pi * np.cumsum(f_curve * det * vib) / SR
        v = np.zeros(n)
        for k in range(1, K + 1):
            v += np.sin(k * ph) / k ** 1.3
        return v

    base = reed(1.0)
    body = np.sin(2 * np.pi * np.cumsum(f_curve * vib) / SR)
    vL = base + reed(0.9965) + 0.30 * body
    vR = base + reed(1.0038) + 0.30 * body
    env = np.minimum(np.clip(tt / 0.6, 0, 1),
                     np.clip((total + 0.8 - tt) / 1.8, 0, 1))
    sos_w = signal.butter(2, 2600, "low", fs=SR, output="sos")
    vL = np.tanh(0.8 * signal.sosfilt(sos_w, vL * env))
    vR = np.tanh(0.8 * signal.sosfilt(sos_w, vR * env))
    peak = max(np.max(np.abs(vL)), np.max(np.abs(vR)), 1e-12)
    return vL / peak, vR / peak


DELAY = 0.75 * BEAT                                   # dotted 8th


def place_lead(LR, t0, gain):
    L, R = LR
    add_at(lay_L, L, t0, gain)
    add_at(lay_R, R, t0, gain)
    add_at(lay_L, R, t0 + DELAY, gain * 0.28)         # ping-pong echoes
    add_at(lay_R, L, t0 + DELAY, gain * 0.28)
    add_at(lay_L, L, t0 + 2 * DELAY, gain * 0.13)
    add_at(lay_R, R, t0 + 2 * DELAY, gain * 0.13)


lay_L = np.zeros(N)
lay_R = np.zeros(N)

REFRAIN_MD = [(m, d) for _, m, d, _ in NK_REFRAIN]
LEAD_REFRAIN = lead_phrase(REFRAIN_MD)
LEAD_REFRAIN_CUT = lead_phrase(REFRAIN_MD[1:])        # ch3 statement 1
LEAD_HI = lead_phrase([(m + 12, d) for m, d in REFRAIN_MD])
LEAD_EQ = lead_phrase(ECHO_Q)
LEAD_EA = lead_phrase(ECHO_A)

# chorus 2: composed echoes entering ON the piano's last note of each half
for b0 in (B_CH2, B_CH2 + 8):
    place_lead(LEAD_EQ, bar_t(b0 + 3, 2), 0.75)
    place_lead(LEAD_EA, bar_t(b0 + 7, 2), 0.8)
# choruses 3–4: the lead carries the refrain — the duet, earned
place_lead(LEAD_REFRAIN_CUT, bar_t(B_CH3, 1), 0.95)
place_lead(LEAD_REFRAIN, bar_t(B_CH3 + 8), 1.0)
place_lead(LEAD_REFRAIN, bar_t(B_CH4), 1.0)
place_lead(LEAD_REFRAIN, bar_t(B_CH4 + 8), 1.0)
# the octave shimmer joins for the final wave
place_lead(LEAD_HI, bar_t(B_CH4), 0.28)
place_lead(LEAD_HI, bar_t(B_CH4 + 8), 0.30)

lay_L = reverb(lay_L, IR_L, wet=0.45)
lay_R = reverb(lay_R, IR_R, wet=0.45)
commit(lay_L, lay_R, 0.24)
print("lead committed")


# ---------------------------------------------------------------- stab
# The dark gated offbeat chord stab — the groove's own answer. Verse-2
# development element, returning in the final chorus.

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
    if not (B_V2 <= b < B_BR or B_CH4 <= b < B_DECON):
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

sos_air = signal.butter(4, [150, 1200], "bandpass", fs=SR, output="sos")
air = signal.sosfilt(sos_air, rng.standard_normal(N))
air /= np.max(np.abs(air))
air_env = slow_noise(0.05, 0.4, 1.0)
edge = np.minimum(np.clip((bar_t(B_V1) - t) / 10.0, 0, 1) +
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
OUT = os.path.join(OUT_DIR, "nachtkind_v3.wav")
with wave.open(OUT, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())

print(f"\nCreated: {os.path.abspath(OUT)}")
print(f"Duration: {N / SR:.1f} s  |  {SR} Hz stereo, 16-bit PCM  |  {BPM:.0f} BPM, G minor")

MP3 = os.path.join(OUT_DIR, "nachtkind_v3.mp3")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", OUT,
                "-vn", "-ar", "44100", "-ac", "2", "-b:a", "192k", MP3],
               check=True)
print(f"Created: {os.path.abspath(MP3)}  (192k mp3)")

# ---------------------------------------------------------------- verify form

print("\nSection map:")
SECTIONS = [("THESIS (solo piano)", 0), ("groove assembles", B_GROOVE),
            ("verse 1", B_V1), ("pre-chorus 1", B_PRE1),
            ("CHORUS 1 (piano alone)", B_CH1), ("verse 2 (development)", B_V2),
            ("pre-chorus 2", B_PRE2), ("CHORUS 2 (+ lead echoes)", B_CH2),
            ("bridge teardown", B_BR), ("bridge build", B_BR2),
            ("CHORUS 3 (the fusion)", B_CH3), ("CHORUS 4 (+ shimmer)", B_CH4),
            ("deconstruction", B_DECON), ("piano exits, pads return", B_DECON2),
            ("DJ outro", B_OUT), ("bookend (kick stops)", B_STOP)]
for name, b in SECTIONS:
    print(f"  {bar_t(b):6.1f} s  bar {b:3d}  {name}")
print(f"  {DURATION:6.1f} s  end")

print(f"\nRefrain statements: {HOOKS}  (target >= 10; the bridge/bookend "
      f"question-halves are fragments, not counted)")

print("\nSeam checklist (what crosses every boundary):")
for b, dev in [(B_GROOVE, "thesis' answer resolves F#->G; the low G rings under the kick entry"),
               (B_V1, "crash; groove unbroken; bass creeps under"),
               (B_PRE1, "verse answer's F#3->G3 resolution rings across; LH octaves take over"),
               (B_CH1, "the rise ends ON the hanging F# — the chorus' first G resolves it + reverse cymbal + crash"),
               (B_V2, "chorus answer's F#->G rings across + crash; stab enters offbeat"),
               (B_PRE2, "as verse->pre-chorus 1"),
               (B_CH2, "leading-tone pickup + reverse cymbal + crash"),
               (B_BR, "last lead echo (G5) rings into the teardown + crash; pads swell"),
               (B_BR2, "the question-half repeats over the walking kick"),
               (B_CH3, "reverse cymbal swells INTO the silent beat; the pickup G hangs in it; slam on beat 2"),
               (B_CH4, "groove unbroken; shimmer + stab join + crash"),
               (B_DECON, "lead exits mid-ring; the piano statement continues + crash"),
               (B_DECON2, "piano's resolution rings into the returning pads"),
               (B_OUT, "bass filter sweep lands; kick keeps rolling"),
               (B_STOP, "kick stops; outro pad still ringing under the solo piano; the final chord answers the hanging question")]:
    print(f"  bar {b:3d} ({bar_t(b):5.1f} s): {dev}")

def rms_between(b0, b1):
    i0 = int(bar_t(b0) * SR)
    i1 = int(bar_t(b1) * SR) if b1 is not None else N
    return np.sqrt(np.mean(mix_L[i0:i1] ** 2 + mix_R[i0:i1] ** 2) / 2)

print("\nPer-section RMS:")
R = {}
for (name, b0), (_, b1) in zip(SECTIONS, SECTIONS[1:] + [("end", None)]):
    R[name] = rms_between(b0, b1)
    print(f"  {name:28s} {R[name]:.3f}")

checks = [
    ("thesis < verse1 < chorus1",
     R["THESIS (solo piano)"] < R["verse 1"] < R["CHORUS 1 (piano alone)"]),
    ("chorus1 > pre-chorus1",
     R["CHORUS 1 (piano alone)"] > R["pre-chorus 1"]),
    ("chorus2 >= chorus1",
     R["CHORUS 2 (+ lead echoes)"] >= R["CHORUS 1 (piano alone)"]),
    ("chorus4 is the loudest section",
     R["CHORUS 4 (+ shimmer)"] == max(R.values())),
    ("bridge teardown is the trough (after the thesis)",
     R["bridge teardown"] < min(v for k, v in R.items()
                                if k not in ("THESIS (solo piano)",
                                             "bridge teardown",
                                             "bookend (kick stops)"))),
    ("outro settles", R["DJ outro"] < R["CHORUS 4 (+ shimmer)"]),
    ("bookend below verse1", R["bookend (kick stops)"] < R["verse 1"]),
    ("refrain count >= 10", HOOKS >= 10),
]
print("\nForm checks:")
ok = True
for name, passed in checks:
    print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
    ok &= passed
print("all checks passed" if ok else "SOME CHECKS FAILED")
