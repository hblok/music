#!/usr/bin/env python3
"""
ungeschrieben.py — "Ungeschrieben" (~5:45, 130 BPM, F natural minor).
Early Frankfurt proto-trance in the two-reveal form (design notes:
ungeschrieben_notes.md; inspiration: Zyon "No Fate", Struggle Continues
Mix 1992 — the form and the era palette, not the material).

THE STORY — the future is unwritten. The sequence is the present: one bar,
repeating forever, never changing its notes — only the FILTER changes, i.e.
how brightly it dares to ask. The strings are the future: glimpsed once
(reveal 1), doubted (the reduction), then chosen (reveal 2, the peak).

THE FORM — no verse/chorus, no drop: additive/subtractive layering with two
string REVEALS as the climaxes. The doctrine maps on: the refrain is the
string theme (8 bars, contour Q/A: antecedent rising Fm–Db–Eb to hang on
the VII, consequent peaking higher and falling home to F), identical at
both reveals — reveal 2 is bigger by forces only (octaves, descant, count).
The DELIBERATE DOCTRINE DEVIATION: the thesis is withheld — one drowned
GHOST of the theme's first phrase in the intro, zero full statements before
reveal 1 (checked). The fusion payoff: only at reveal 2 does the sequence
reach fully open at the moment the strings peak.

  0:00  intro       Kick, then hats; the sequence enters with the filter
                    nearly closed — a dark throb, barely a pitch. The GHOST
                    at bar 10: one drowned string voice, first phrase only.
  0:30  groove      Rolling bass on the F pedal; additive 16-bar cycles
                    (+open hat, +claps); the filter opens across the section.
  1:29  pre-reveal  The sweep crests, tom fill, crash →
  1:44  REVEAL 1    THE STRINGS: the theme twice — harmonic movement
                    (Fm–Db–Eb) arrives with them; then sustained chords
                    riding the groove. The sequence stays half-open.
  2:28  reduction   Strings recede to the dark pad; claps/open hat strip;
                    the filter closes back down — doubt. THE SPOKEN LINE
                    drops ONCE here, dry: "Die Zukunft ist ungeschrieben."
  3:12  rebuild     The filter reopens faster than before; the long tom
                    fill, crash →
  3:27  REVEAL 2    The peak: theme 3x in octaves, high descant answering
                    the consequents, the sequence FULLY OPEN at last —
                    question and answer at full voice. Loudest section.
  4:26  ride-out    Peel in reverse: descant, strings to pad, claps out,
                    the filter starts its long descent.
  5:10  outro       Drums and bass, then bass out; the sequence filters
                    down to the intro's throb (the bookend is the FILTER
                    POSITION, not a melody). Kick stops; the throb + one
                    last string chord ring out.

Era rules: 909 drums (punchy, not sub-heavy), rolling 16th mono bass with
octave jumps, moderately resonant swept sequence, rompler strings (M1/D-50
character: fast sampled attack, chorus detune, bow-noise layer, sample-loop
flutter), warm head-roomed master. BANNED: supersaws, sidechain pumping,
white-noise risers, reverse cymbals (nachtkind's), loudness compression.

THE VOICE KNOB: `VOICE_GAIN` below — set it to 0.0 to render the track
fully instrumental (the spoken line is dropped, nothing else changes).
The line is synthesized once via edge-tts (German neural voice) and cached
to /workspace/music/samples/ungeschrieben_voice.wav; after the first run
no network is needed. If TTS and cache are both unavailable, the script
renders instrumental and says so.

Everything else synthesized (numpy + scipy).
Output: /workspace/music/ungeschrieben.wav + ungeschrieben.mp3 (192k).
"""

import asyncio
import os
import subprocess
import wave
import numpy as np
from scipy import signal

SR = 44100
DURATION = 348.0
N = int(SR * DURATION)
t = np.arange(N) / SR

rng = np.random.default_rng(1992)     # the year of No Fate

BPM = 130.0
BEAT = 60.0 / BPM
BAR = BEAT * 4
STEP = BEAT / 4
GRID0 = 0.5

# ------------------------------------------------------------- THE KNOB
# Set to 0.0 for a fully instrumental render (drops the spoken line only).
VOICE_GAIN = 1.0
VOICE_TEXT = "Die Zukunft ist ungeschrieben."
VOICE_ID = "de-DE-KatjaNeural"        # edge-tts neural voice (female, dry)
VOICE_CACHE = "/workspace/music/samples/ungeschrieben_voice.wav"


def bar_t(b, beat=0.0):
    return GRID0 + b * BAR + beat * BEAT


# ----------------------------------------------------- section boundaries (bars)
B_GROOVE = 16     # bass + the sequence proper; additive cycles
B_PREREV = 48     # the sweep crests
B_REV1 = 56       # REVEAL 1: the strings
B_RED = 80        # reduction: doubt; the spoken line
B_REBUILD = 104   # the filter reopens, faster
B_REV2 = 112      # REVEAL 2: the peak / the fusion
B_RIDE = 144      # ride-out: peel in reverse
B_OUT = 168       # outro: back to the throb
B_KSTOP = 180     # kick stops; final string chord
B_END = 184


def section_of(b):
    for name, b0 in [("outro", B_OUT), ("ride", B_RIDE), ("rev2", B_REV2),
                     ("rebuild", B_REBUILD), ("red", B_RED), ("rev1", B_REV1),
                     ("prerev", B_PREREV), ("groove", B_GROOVE)]:
        if b >= b0:
            return name
    return "intro"


# ------------------------------------------------------- the filter arc
# The sequence's development IS this curve (the era's substitute for both
# melodic development and risers). Piecewise-linear cutoff in Hz over bars;
# printed and checked at the end.
CUT_BARS = [0,   16,  48,   54,   56,   80,   100, 104,  112,  126,  140,  144,  168, 184]
CUT_HZ = [250, 350, 900, 1400, 1200, 1200, 320, 320, 1600, 2600, 2600, 2400, 700, 240]


def cutoff_at(b):
    return float(np.interp(b, CUT_BARS, CUT_HZ))


# ---------------------------------------------------------------- helpers

def midi_to_hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def fade(x, fade_in=0.3, fade_out=7.0):
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


def glide_curve(notes, n, tau=0.04):
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


# the long hall for the strings; a shorter room for the rest
IR_L = make_reverb_ir(6.0, 2.8, 7)
IR_R = make_reverb_ir(6.0, 2.8, 11)

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
# F natural minor (Aeolian): F G Ab Bb C Db Eb. i–VI–VII = Fm–Db–Eb.
# The groove sits on the F pedal; the STRINGS bring the harmonic movement.

FM_V = (53, 56, 60, 65)            # F3  Ab3 C4 F4
DB_V = (49, 53, 56, 61)            # Db3 F3  Ab3 Db4
EB_V = (51, 55, 58, 63)            # Eb3 G3  Bb3 Eb4
CH_CELL = [FM_V, FM_V, DB_V, EB_V, FM_V, DB_V, EB_V, FM_V]   # one chord/bar

# THE STRING THEME — 8 bars, identical at both reveals. (midi, beats.)
# Q: a pure ascent F–Ab–C–Db–Eb hanging on the VII (Aeolian: no dominant
# pull — it hangs rather than leads). A: peaks HIGHER (F5) and falls
# stepwise home to F. Contour Q/A, per the tech_noir lesson.
THEME_Q = [(65, 2), (68, 2), (72, 4), (73, 4), (75, 4)]
THEME_A = [(77, 2), (75, 2), (73, 2), (72, 2), (70, 2), (67, 2), (65, 4)]
THEME = THEME_Q + THEME_A
GHOST_NOTES = [(65, 2), (68, 2), (72, 4)]     # the first phrase, drowned

# THE SEQUENCE — one bar, sixteen 16ths, F pedal arpeggio. It NEVER
# changes; only the filter arc develops it.
SEQ_CELL = [53, 60, 56, 60, 65, 60, 56, 60,
            53, 60, 56, 63, 65, 63, 60, 56]

THEME_STMTS = []                   # bars of full theme statements (verified)


# ---------------------------------------------------------------- drums
# 909 school (nachtkind kit recipes — punchy kick, not sub-heavy). Plus
# the one new percussion recipe: 909 toms, used ONLY as transition fills.

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


def make_crash():
    n = int(2.0 * SR)
    td = np.arange(n) / SR
    sos_c = signal.butter(2, 5000, "high", fs=SR, output="sos")
    x = signal.sosfilt(sos_c, rng.standard_normal(n)) * np.exp(-td * 2.2)
    x *= 1 - np.exp(-td / 0.002)
    return x / (np.max(np.abs(x)) + 1e-12)


def make_tom(f0):
    # 909 tom: falling sine body + a soft skin-noise burst
    n = int(0.30 * SR)
    td = np.arange(n) / SR
    f_curve = f0 * 1.6 * np.exp(-td * 9.0) + f0
    body = np.sin(2 * np.pi * np.cumsum(f_curve) / SR) * np.exp(-td * 11.0)
    skin = signal.sosfilt(signal.butter(2, [400, 2500], "bandpass", fs=SR, output="sos"),
                          rng.standard_normal(n)) * np.exp(-td * 60)
    skin /= np.max(np.abs(skin)) + 1e-12
    x = body + 0.25 * skin
    x *= 1 - np.exp(-td / 0.001)
    return x / (np.max(np.abs(x)) + 1e-12)


KICK = make_kick()
CHAT = make_hat()
OHAT = make_hat(open_=True)
CLAP = make_clap()
RIDE = make_ride()
CRASH = make_crash()
TOM_HI, TOM_MID, TOM_LO = make_tom(196.0), make_tom(147.0), make_tom(110.0)


def kick_gain(b):
    if b >= B_KSTOP:
        return 0.0
    s = section_of(b)
    return {"intro": 0.85, "groove": 0.95, "prerev": 1.0, "rev1": 1.0,
            "red": 0.80, "rebuild": 0.90, "rev2": 1.0, "ride": 0.95,
            "outro": 0.90}[s]


clear()
for b in range(B_END):
    g = kick_gain(b)
    if g <= 0:
        continue
    for beat in range(4):
        add_at(lay_L, KICK, bar_t(b, beat), g)
        add_at(lay_R, KICK, bar_t(b, beat), g)
commit(lay_L, lay_R, 0.33)
print("kick committed")

# closed 16th hats (skipping the open slot) + offbeat open hat
clear()
CH_GAINS = [0.50, 0.25, 0.0, 0.30]
for b in range(B_KSTOP):
    if b < 4:
        continue
    s = section_of(b)
    g = {"intro": 0.7, "red": 0.6}.get(s, 1.0)
    if s == "prerev":
        g = 1.1                                  # hats double under the crest
    for beat in range(4):
        for sx in range(4):
            if CH_GAINS[sx] == 0.0:
                continue
            add_at(lay_L, CHAT, bar_t(b, beat + sx * 0.25), g * CH_GAINS[sx] * 0.9)
            add_at(lay_R, CHAT, bar_t(b, beat + sx * 0.25), g * CH_GAINS[sx])
        if (24 <= b < B_RED or B_REBUILD <= b < B_OUT) and s != "red":
            add_at(lay_L, OHAT, bar_t(b, beat + 0.5), g)
            add_at(lay_R, OHAT, bar_t(b, beat + 0.5), g * 0.85)
commit(lay_L, lay_R, 0.08)
print("hats committed")

# claps on 2 & 4 — additive cycle 2 of the groove; out in reduction/ride
clear()
for b in range(B_END):
    if not (32 <= b < B_RED or B_REV2 <= b < B_RIDE + 8):
        continue
    for beat in (1, 3):
        p = 0.42 if beat == 1 else 0.58
        place_pan(lay_L, lay_R, CLAP, bar_t(b, beat), 1.0, p)
commit(lay_L, lay_R, 0.09)
print("claps committed")

# ride: reveal 2 only, light ("occasional" — era discipline)
clear()
for b in range(B_REV2, B_RIDE):
    for e in range(8):
        place_pan(lay_L, lay_R, RIDE, bar_t(b, e * 0.5),
                  0.45 if e % 2 == 0 else 0.30, 0.5)
commit(lay_L, lay_R, 0.035)
print("ride committed")

# tom fills — the era's seam device; exactly three in the whole track
clear()
def tom_fill(b, dense):
    hits = [(2.0, TOM_HI, 0.35), (2.5, TOM_HI, 0.4), (3.0, TOM_MID, 0.5),
            (3.5, TOM_LO, 0.65)]
    if dense:
        hits = [(0.0, TOM_HI, 0.3), (0.5, TOM_HI, 0.35), (1.0, TOM_MID, 0.4),
                (1.5, TOM_MID, 0.45), (2.0, TOM_MID, 0.5), (2.5, TOM_LO, 0.55),
                (3.0, TOM_LO, 0.6), (3.5, TOM_LO, 0.7)]
    for beat, tom, pan in hits:
        g = 0.7 + 0.3 * beat / 4
        place_pan(lay_L, lay_R, tom, bar_t(b, beat), g, pan)
tom_fill(B_REV1 - 1, dense=False)
tom_fill(B_REV2 - 1, dense=True)                 # the long fill
tom_fill(B_RIDE - 1, dense=False)
commit(lay_L, lay_R, 0.11)
print("tom fills committed")

# crashes mark the section changes (NO reverse cymbals, NO risers)
clear()
for b, g in [(B_GROOVE, 0.5), (B_PREREV, 0.6), (B_REV1, 1.0), (B_RED, 0.5),
             (B_REV2, 1.0), (B_RIDE, 0.7), (B_OUT, 0.5)]:
    place_pan(lay_L, lay_R, CRASH, bar_t(b), g, 0.5)
commit(lay_L, lay_R, 0.05)
print("crashes committed")


# ---------------------------------------------------------------- bass
# Rolling 16th mono bass: single-note F pedal, octave jumps on steps 6 and
# 14 — a continuous pulse tight against the kick (no offbeat pattern).
# Warmed recipe (rolled-off spectrum, gentle resonance, soft drive).

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
        x += np.sin(2 * np.pi * k * f * td) / k ** 1.3
    y = signal.sosfilt(signal.butter(2, cutoff, "low", fs=SR, output="sos"), x)
    bpk, apk = signal.iirpeak(cutoff, Q=1.2, fs=SR)
    y = y + 0.3 * signal.lfilter(bpk, apk, y)
    y += 0.4 * np.sin(2 * np.pi * (f / 2) * td)
    y = np.tanh(0.9 * y)
    y *= (1 - np.exp(-td / 0.004)) * np.clip((dur - td) / 0.02, 0, 1)
    bass_cache[key] = y / (np.max(np.abs(y)) + 1e-12)
    return bass_cache[key]


BASS_CUT = {"groove": 420, "prerev": 480, "rev1": 520, "red": 300,
            "rebuild": 380, "rev2": 560, "ride": 480, "outro": 360}
clear()
for b in range(B_GROOVE, 176):                    # bass out mid-outro
    cut = BASS_CUT[section_of(b)]
    for step in range(16):
        midi = 41 + (12 if step in (6, 14) else 0)          # F2 pedal
        g = 0.85 if step % 2 == 0 else 0.72
        if step in (6, 14):
            g = 0.9
        x = bass_note(midi, cut)
        add_at(lay_L, x, bar_t(b, step * 0.25), g)
        add_at(lay_R, x, bar_t(b, step * 0.25), g)
commit(lay_L, lay_R, 0.28)
print(f"bass committed ({len(bass_cache)} cached)")


# ------------------------------------------------------- the sequence
# The hypnotic core and the question voice. One bar, never a new note; a
# real resonant peak (Q 2.2 — era-authentic, per the notes' guardrails:
# soft drive, sine sub, and the resonance SWEEPS, it never parks) riding
# the filter arc. Each hit is rendered at the cutoff the arc gives its
# onset (cached in 40 Hz buckets), so the sweep is baked into the notes.

seq_cache = {}


def seq_pluck(midi, cutoff, dur=0.42):
    key = (midi, int(cutoff // 40))
    if key in seq_cache:
        return seq_cache[key]
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    for k in range(1, min(40, int(9000 / f)) + 1):
        x += np.sin(2 * np.pi * k * f * td) / k ** 1.1      # bright analog pluck
    y = signal.sosfilt(signal.butter(2, cutoff, "low", fs=SR, output="sos"), x)
    bpk, apk = signal.iirpeak(min(cutoff, 5000), Q=2.2, fs=SR)
    y = y + 0.40 * signal.lfilter(bpk, apk, y)              # the era resonance
    y += 0.25 * np.sin(2 * np.pi * (f / 2) * td)            # sub for body
    y = np.tanh(0.8 * y)                                    # soft, never acid
    y *= (1 - np.exp(-td / 0.002)) * np.exp(-td * 9.0)
    seq_cache[key] = y / (np.max(np.abs(y)) + 1e-12)
    return seq_cache[key]


SEQ_G = {"intro": 0.7, "groove": 0.9, "prerev": 1.0, "rev1": 0.85,
         "red": 0.8, "rebuild": 0.95, "rev2": 1.0, "ride": 0.9, "outro": 0.8}
clear()
for b in range(4, B_END):
    g0 = SEQ_G[section_of(b)]
    for step in range(16):
        cut = cutoff_at(b + step / 16.0)
        m = SEQ_CELL[step]
        pan = 0.5 + 0.22 * (1 if step % 4 == 2 else -1) * (0.5 if step % 2 else 1.0)
        place_pan(lay_L, lay_R, seq_pluck(m, cut), bar_t(b, step * 0.25),
                  g0 * (0.85 if step % 2 else 1.0), pan)
# tempo-synced dotted-8th cross delay (the era's sequence treatment)
d = int(0.75 * BEAT * SR)
eL = np.zeros(N)
eR = np.zeros(N)
eL[d:] = lay_R[:-d] * 0.20
eR[d:] = lay_L[:-d] * 0.20
lay_L += eL
lay_R += eR
lay_L = reverb(lay_L, IR_L, 0.18)
lay_R = reverb(lay_R, IR_R, 0.18)
commit(lay_L, lay_R, 0.20)
print(f"sequence committed ({len(seq_cache)} cached across the sweep)")


# ------------------------------------------------------ rompler strings
# THE NEW INSTRUMENT — the emotional centerpiece. M1/D-50-era sampled-
# strings character: rolled-off saw ensemble (three detuned copies), a
# bow-noise layer riding the same envelope, a fast ~120 ms sampled attack,
# and a slow ~5.8 Hz amplitude flutter per voice (the sample-loop wobble
# that makes it read as SAMPLED, not analog). Long hall, very wet.

def _string_voice(f_curve, n, det, flutter_phase):
    tt = np.arange(n) / SR
    flut = 1.0 + 0.05 * np.sin(2 * np.pi * 5.8 * tt + flutter_phase)
    ph = 2 * np.pi * np.cumsum(f_curve * det) / SR
    K = max(3, int(5500 / np.max(f_curve)))
    v = np.zeros(n)
    for k in range(1, K + 1):
        v += np.sin(k * ph) / k ** 1.3
    return v * flut


def strings_line(notes, lowpass=3400):
    total = sum(d for _, d in notes) * BEAT
    n = int((total + 2.5) * SR)
    tt = np.arange(n) / SR
    f = glide_curve([(m, d * BEAT) for m, d in notes], n, tau=0.04)
    L = np.zeros(n)
    R = np.zeros(n)
    for det, gL, gR, phs in [(0.9955, 1.0, 0.55, 0.0),
                             (1.0, 0.8, 0.8, 2.1),
                             (1.0045, 0.55, 1.0, 4.2)]:
        v = _string_voice(f, n, det, phs)
        L += gL * v
        R += gR * v
    bow = signal.sosfilt(signal.butter(2, [2000, 5000], "bandpass", fs=SR, output="sos"),
                         rng.standard_normal(n))
    bow /= np.max(np.abs(bow)) + 1e-12
    atk = 0.5 - 0.5 * np.cos(np.pi * np.clip(tt / 0.12, 0, 1))   # sampled attack
    env = np.minimum(atk, np.clip((total + 0.3 - tt) / 0.8, 0, 1))
    L = (L / (np.max(np.abs(L)) + 1e-12) + 0.10 * bow) * env
    R = (R / (np.max(np.abs(R)) + 1e-12) + 0.10 * bow) * env
    sos = signal.butter(2, lowpass, "low", fs=SR, output="sos")
    L = signal.sosfilt(sos, L)
    R = signal.sosfilt(sos, R)
    peak = max(np.max(np.abs(L)), np.max(np.abs(R)), 1e-12)
    return L / peak, R / peak


def strings_chord(midis, dur, lowpass=3000):
    n = int((dur + 1.2) * SR)
    tt = np.arange(n) / SR
    L = np.zeros(n)
    R = np.zeros(n)
    for m in midis:
        f = midi_to_hz(m) * np.ones(n)
        for det, gL, gR in [(0.9958, 1.0, 0.6), (1.0042, 0.6, 1.0)]:
            L += gL * _string_voice(f, n, det, rng.uniform(0, 6))
            R += gR * _string_voice(f, n, det, rng.uniform(0, 6))
    bow = signal.sosfilt(signal.butter(2, [2000, 5000], "bandpass", fs=SR, output="sos"),
                         rng.standard_normal(n))
    bow /= np.max(np.abs(bow)) + 1e-12
    atk = 0.5 - 0.5 * np.cos(np.pi * np.clip(tt / 0.15, 0, 1))
    env = np.minimum(atk, np.clip((dur + 0.5 - tt) / 0.9, 0, 1))
    L = (L / (np.max(np.abs(L)) + 1e-12) + 0.08 * bow) * env
    R = (R / (np.max(np.abs(R)) + 1e-12) + 0.08 * bow) * env
    sos = signal.butter(2, lowpass, "low", fs=SR, output="sos")
    L = signal.sosfilt(sos, L)
    R = signal.sosfilt(sos, R)
    peak = max(np.max(np.abs(L)), np.max(np.abs(R)), 1e-12)
    return L / peak, R / peak


def place_theme(b0, gain, octaves=False):
    xL, xR = THEME_LINE
    add_at(lay_L, xL, bar_t(b0), gain)
    add_at(lay_R, xR, bar_t(b0), gain)
    if octaves:
        hL, hR = THEME_LINE_HI
        add_at(lay_L, hL, bar_t(b0), gain * 0.45)
        add_at(lay_R, hR, bar_t(b0), gain * 0.45)
    THEME_STMTS.append(b0)


clear()
THEME_LINE = strings_line(THEME)
THEME_LINE_HI = strings_line([(m + 12, d) for m, d in THEME], lowpass=4200)
DESCANT = strings_line([(m + 12, d) for m, d in THEME_A], lowpass=4200)

# THE GHOST (intro, bar 10): the first phrase only, drowned — nearly-closed
# filter, deep in the hall. A fragment; it does not count as a statement.
gL, gR = strings_line(GHOST_NOTES, lowpass=450)
add_at(lay_L, gL, bar_t(10), 0.35)
add_at(lay_R, gR, bar_t(10), 0.35)

# REVEAL 1: the theme twice over its harmony, then chords riding the groove
for b in range(B_REV1, B_RED):
    cL, cR = strings_chord(CH_CELL[(b - B_REV1) % 8], BAR)
    add_at(lay_L, cL, bar_t(b), 0.75)
    add_at(lay_R, cR, bar_t(b), 0.75)
place_theme(B_REV1, 0.95)
place_theme(B_REV1 + 8, 0.95)

# REVEAL 2: the theme three times IN OCTAVES over bigger voicings, the
# descant answering the consequent halves of statements 2 and 3
for b in range(B_REV2, B_RIDE):
    v = CH_CELL[(b - B_REV2) % 8]
    big = list(v) + [v[-1] + 12]
    cL, cR = strings_chord(big, BAR)
    add_at(lay_L, cL, bar_t(b), 0.85)
    add_at(lay_R, cR, bar_t(b), 0.85)
place_theme(B_REV2, 1.0, octaves=True)
place_theme(B_REV2 + 8, 1.0, octaves=True)
place_theme(B_REV2 + 16, 1.0, octaves=True)
for b0 in (B_REV2 + 12, B_REV2 + 20):
    add_at(lay_L, DESCANT[0], bar_t(b0), 0.30)
    add_at(lay_R, DESCANT[1], bar_t(b0), 0.30)

# ride-out: strings hand back — two last quiet chord cycles, thinning
for b in range(B_RIDE, B_RIDE + 8):
    cL, cR = strings_chord(CH_CELL[(b - B_RIDE) % 8], BAR)
    g = 0.6 * (1.0 - 0.6 * (b - B_RIDE) / 8)
    add_at(lay_L, cL, bar_t(b), g)
    add_at(lay_R, cR, bar_t(b), g)

# the outro's one last chord, ringing out over the throb
cL, cR = strings_chord(FM_V, 6.0)
add_at(lay_L, cL, bar_t(B_KSTOP), 0.7)
add_at(lay_R, cR, bar_t(B_KSTOP), 0.7)

lay_L = reverb(lay_L, IR_L, 0.55)
lay_R = reverb(lay_R, IR_R, 0.55)
commit(lay_L, lay_R, 0.30)
print("strings committed")


# ------------------------------------------------------------ dark pad
# The breakdown bed the strings recede into (reduction), returning under
# the ride-out. Dark, sine-heavy, static Fm — no movement without strings.

def pad_chord(chord, dur, attack=2.0, release=2.5):
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
    sos = signal.butter(2, 750, "low", fs=SR, output="sos")
    L = signal.sosfilt(sos, L * env)
    R = signal.sosfilt(sos, R * env)
    peak = max(np.max(np.abs(L)), np.max(np.abs(R)), 1e-12)
    return L / peak, R / peak


clear()
for b in range(B_RED, B_REBUILD, 2):
    pL, pR = pad_chord((41, 53, 56, 60), 2 * BAR + 2.0)
    add_at(lay_L, pL, bar_t(b), 0.95)
    add_at(lay_R, pR, bar_t(b), 0.95)
for b in range(B_RIDE + 8, B_OUT, 2):
    pL, pR = pad_chord((41, 53, 56, 60), 2 * BAR + 2.0)
    add_at(lay_L, pL, bar_t(b), 0.7)
    add_at(lay_R, pR, bar_t(b), 0.7)
lay_L = reverb(lay_L, IR_L, 0.5)
lay_R = reverb(lay_R, IR_R, 0.5)
commit(lay_L, lay_R, 0.12)
print("pad committed")


# ---------------------------------------------------------- spoken word
# "Die Zukunft ist ungeschrieben." — dropped ONCE, in the reduction (the
# classic single movie-sample placement; the doubt, answered in words).
# Cache-first: renders via edge-tts on the first run only. VOICE_GAIN at
# the top of the file silences it entirely.

def get_voice():
    if VOICE_GAIN <= 0:
        return None, "silenced (VOICE_GAIN=0)"
    if not os.path.exists(VOICE_CACHE):
        try:
            import edge_tts
            os.makedirs(os.path.dirname(VOICE_CACHE), exist_ok=True)
            tmp = VOICE_CACHE + ".mp3"

            async def go():
                await edge_tts.Communicate(VOICE_TEXT, voice=VOICE_ID).save(tmp)

            asyncio.run(go())
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp,
                            "-ar", str(SR), "-ac", "1", VOICE_CACHE], check=True)
            os.remove(tmp)
        except Exception as e:                    # no net, no cache: instrumental
            return None, f"unavailable ({type(e).__name__}) — rendered instrumental"
    with wave.open(VOICE_CACHE, "rb") as w:
        v = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(float)
    v /= np.max(np.abs(v)) + 1e-12
    # hardware-sampler pitch-down: resample by 0.94 (~ -1 semitone, 6 % slower)
    idx = np.arange(0, len(v) - 1, 0.94)
    v = v[idx.astype(int)]
    v = signal.sosfilt(signal.butter(2, 6000, "low", fs=SR, output="sos"), v)
    v = signal.sosfilt(signal.butter(2, 120, "high", fs=SR, output="sos"), v)
    return v / (np.max(np.abs(v)) + 1e-12), "placed once at bar 86"


clear()
VOICE, voice_status = get_voice()
if VOICE is not None:
    t0 = bar_t(86)
    add_at(lay_L, VOICE, t0, 1.0)                 # dry, centered
    add_at(lay_R, VOICE, t0, 1.0)
    for i, g in [(1, 0.30), (2, 0.14)]:           # tempo-synced delay tail
        add_at(lay_L, VOICE, t0 + i * 0.75 * BEAT, g if i % 2 else g * 0.6)
        add_at(lay_R, VOICE, t0 + i * 0.75 * BEAT, g * 0.6 if i % 2 else g)
    commit(lay_L, lay_R, 0.13 * VOICE_GAIN)
print(f"spoken word: {voice_status}")


# ------------------------------------------------------------------ air

sos_air = signal.butter(4, [150, 1100], "bandpass", fs=SR, output="sos")
air = signal.sosfilt(sos_air, rng.standard_normal(N))
air /= np.max(np.abs(air))
air_env = slow_noise(0.05, 0.4, 1.0)
edge = np.minimum(np.clip((bar_t(B_GROOVE) - t) / 12.0, 0, 1) +
                  np.clip((t - bar_t(B_OUT)) / 20.0, 0, 1), 1.0)
commit(air * air_env * edge, air * air_env[::-1] * edge, 0.04)
print("air committed")


# ---------------------------------------------------------------- master
# Era master: peak-normalized with headroom. No loudness compression, no
# tanh, no shelf — warm and slightly lo-fi is the identity.

fade(mix_L, fade_in=0.3, fade_out=7.0)
fade(mix_R, fade_in=0.3, fade_out=7.0)

peak = max(np.max(np.abs(mix_L)), np.max(np.abs(mix_R)))
mix_L = mix_L / peak * 0.86
mix_R = mix_R / peak * 0.86

stereo = np.empty((N, 2))
stereo[:, 0] = mix_L
stereo[:, 1] = mix_R
pcm = (stereo * 32767.0).astype(np.int16)

OUT_DIR = "/workspace/music"
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, "ungeschrieben.wav")
with wave.open(OUT, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())

print(f"\nCreated: {os.path.abspath(OUT)}")
print(f"Duration: {N / SR:.1f} s  |  {SR} Hz stereo, 16-bit PCM  |  "
      f"{BPM:.0f} BPM, F natural minor (Fm-Db-Eb)")

MP3 = os.path.join(OUT_DIR, "ungeschrieben.mp3")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", OUT,
                "-vn", "-ar", "44100", "-ac", "2", "-b:a", "192k", MP3],
               check=True)
print(f"Created: {os.path.abspath(MP3)}  (192k mp3)")

# ---------------------------------------------------------------- verify form
# The two-reveal variant of the standard (see ../VERIFY.md).

print("\nSection map:")
SECTIONS = [("intro (the throb)", 0), ("groove", B_GROOVE),
            ("pre-reveal", B_PREREV), ("REVEAL 1", B_REV1),
            ("reduction", B_RED), ("rebuild", B_REBUILD),
            ("REVEAL 2 (the fusion)", B_REV2), ("ride-out", B_RIDE),
            ("outro", B_OUT)]
for name, b in SECTIONS:
    print(f"  {bar_t(b):6.1f} s  bar {b:3d}  {name}")
print(f"  {bar_t(B_KSTOP):6.1f} s  bar {B_KSTOP}  kick stops; final string chord")
print(f"  {DURATION:6.1f} s  end")

first_stmt = min(THEME_STMTS)
print(f"\nString-theme statements: {len(THEME_STMTS)} at bars {THEME_STMTS} "
      f"(target >= 5; first at bar {first_stmt} — the ghost at bar 10 is a "
      f"drowned fragment, uncounted)")

print("\nThe filter arc (the sequence's development — cutoff at boundaries):")
for name, b in SECTIONS:
    print(f"  bar {b:3d}  {name:22s} {cutoff_at(b):6.0f} Hz")
print(f"  bar {B_END - 1}  (end of throb)          {cutoff_at(B_END - 1):6.0f} Hz")

print("\nSeam checklist (what crosses every boundary):")
for b, dev in [(B_GROOVE, "kick + throb unbroken; the filter arc is continuous by construction"),
               (B_PREREV, "the sweep steepens; hats double under it"),
               (B_REV1, "tom fill + crash; the sequence keeps pulsing under the strings"),
               (B_RED, "reveal 1's last chord rings into the pad; crash"),
               (B_REBUILD, "the spoken line's delay tail hangs; the filter starts reopening"),
               (B_REV2, "the long tom fill + crash; the sweep arrives fully open"),
               (B_RIDE, "tom fill; the last theme note rings across"),
               (B_OUT, "the filter descent is continuous; claps already gone"),
               (B_KSTOP, "kick stops; the final chord rings over the still-running throb")]:
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

dense = np.arange(0, B_END, 0.25)
peak_bar = dense[np.argmax([cutoff_at(b) for b in dense])]
checks = [
    ("intro < groove < reveal 1",
     R["intro (the throb)"] < R["groove"] < R["REVEAL 1"]),
    ("REVEAL 2 is the loudest section",
     R["REVEAL 2 (the fusion)"] == max(R.values())),
    ("the reduction is the trough between the reveals",
     R["reduction"] < min(R["REVEAL 1"], R["rebuild"], R["REVEAL 2 (the fusion)"])),
    ("the ride-out descends", R["ride-out"] < R["REVEAL 2 (the fusion)"]),
    ("the outro lands back near the intro", R["outro"] < R["groove"]),
    ("theme count >= 5, none before reveal 1",
     len(THEME_STMTS) >= 5 and first_stmt >= B_REV1),
    ("filter arc: rises across the groove",
     cutoff_at(16) < cutoff_at(32) < cutoff_at(48)),
    ("filter arc: global maximum inside reveal 2",
     B_REV2 <= peak_bar < B_RIDE),
    ("filter arc: outro returns to the intro's throb",
     cutoff_at(B_END - 1) <= cutoff_at(4) * 1.25),
]
print("\nForm checks:")
ok = True
for name, passed in checks:
    print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
    ok &= passed
print("banned by construction: supersaw / sidechain / white-noise riser / reverse cymbal")
print("all checks passed" if ok else "SOME CHECKS FAILED")
