#!/usr/bin/env python3
"""
generate_samples_water.py — listening glossary for the NEW instruments and
effects introduced by generate_water_of_life.py (the goa/psy track).
Recipes copied verbatim from the track generator. Continues the sample
numbering and NEVER overwrites: aborts if any target file exists.

New samples:
  instrument_16_trance_kick.wav       150->45 Hz four-to-the-floor kick
  instrument_17_psy_rolling_bass.wav  the K-b-b-b rolling bass engine
  instrument_18_acid_line_303.wav     resonant squelch line, cutoff sweep
  instrument_19_offbeat_hats.wav      open offbeats + closed 16th ghosts
  effect_06_zap_laser.wav             psy zap: pitch dive + ring mod
  rhythm_03_psy_groove_140bpm.wav     four bars of the assembled groove

Output: /workspace/music/samples/*.wav + README_water.txt
"""

import os
import sys
import wave
import numpy as np
from scipy import signal

SR = 44100
OUT_DIR = "/workspace/music/samples"
os.makedirs(OUT_DIR, exist_ok=True)

rng = np.random.default_rng(140)

BPM = 140.0
BEAT = 60.0 / BPM
STEP = BEAT / 4

manifest = []

NEW_FILES = [
    "instrument_16_trance_kick.wav",
    "instrument_17_psy_rolling_bass.wav",
    "instrument_18_acid_line_303.wav",
    "instrument_19_offbeat_hats.wav",
    "effect_06_zap_laser.wav",
    "rhythm_03_psy_groove_140bpm.wav",
    "README_water.txt",
]
existing = [f for f in NEW_FILES if os.path.exists(os.path.join(OUT_DIR, f))]
if existing:
    sys.exit(f"ABORT — would overwrite existing samples: {', '.join(existing)}")


# ---------------------------------------------------------------- plumbing

def midi_to_hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def save(name, desc, L, R=None):
    if R is None:
        R = L
    L, R = np.asarray(L, float).copy(), np.asarray(R, float).copy()
    ne = int(0.03 * SR)
    for x in (L, R):
        x[:ne] *= np.linspace(0, 1, ne)
        x[-ne:] *= np.linspace(1, 0, ne)
    peak = max(np.max(np.abs(L)), np.max(np.abs(R)), 1e-12)
    L, R = L / peak * 0.85, R / peak * 0.85
    pcm = np.empty((len(L), 2))
    pcm[:, 0], pcm[:, 1] = L, R
    pcm = (pcm * 32767.0).astype(np.int16)
    path = os.path.join(OUT_DIR, name)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    manifest.append((name, desc))
    print(f"  {name}")


def place(buf, x, at_s, gain=1.0):
    i0 = int(at_s * SR)
    end = min(len(buf), i0 + len(x))
    buf[i0:end] += x[: end - i0] * gain


# ---------------------------------------------------------------- recipes
# (verbatim from generate_water_of_life.py)

def make_kick():
    n = int(0.30 * SR)
    td = np.arange(n) / SR
    f_curve = 45.0 + 105.0 * np.exp(-td * 55.0)
    body = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    click = rng.standard_normal(n) * np.exp(-td * 900)
    env = (1 - np.exp(-td / 0.0008)) * np.exp(-td * 9.0)
    x = (body + 0.25 * click) * env
    return x / (np.max(np.abs(x)) + 1e-12)


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


def acid_note(m, cutoff, accent=False, dur=STEP * 0.9):
    cutoff = float(np.clip(cutoff * (1.6 if accent else 1.0), 160, 6000))
    f = midi_to_hz(m)
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    for k in range(1, min(30, int(8000 / f)) + 1):
        x += np.sin(2 * np.pi * k * f * td) / k
    sos_lp = signal.butter(2, cutoff, "low", fs=SR, output="sos")
    y = signal.sosfilt(sos_lp, x)
    bpk, apk = signal.iirpeak(cutoff, Q=7.0, fs=SR)
    y = y + (1.5 if accent else 1.1) * signal.lfilter(bpk, apk, y)
    y = np.tanh(2.2 * y)
    env = (1 - np.exp(-td / 0.003)) * np.clip((dur - td) / 0.03, 0, 1)
    y *= env
    return y / (np.max(np.abs(y)) + 1e-12)


def make_hat(open_=False):
    n = int((0.12 if open_ else 0.045) * SR)
    td = np.arange(n) / SR
    sos_h = signal.butter(4, 7000, "high", fs=SR, output="sos")
    x = signal.sosfilt(sos_h, rng.standard_normal(n))
    x *= np.exp(-td * (30 if open_ else 110))
    return x / (np.max(np.abs(x)) + 1e-12)


def make_zap():
    n = int(0.40 * SR)
    td = np.arange(n) / SR
    f_curve = 80.0 + 1900.0 * np.exp(-td * 18.0)
    x = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    x *= 1.0 + 0.5 * np.sin(2 * np.pi * 35.0 * td)
    x *= np.exp(-td * 8.0) * (1 - np.exp(-td / 0.002))
    return x / (np.max(np.abs(x)) + 1e-12)


def make_doum():
    n = int(0.30 * SR)
    td = np.arange(n) / SR
    f_curve = 55.0 + 35.0 * np.exp(-td * 28.0)
    body = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    ring = 0.25 * np.sin(2 * np.pi * 190.0 * td) * np.exp(-td * 35)
    env = np.exp(-td * 14.0) * (1 - np.exp(-td * 600))
    return (body + ring) * env


def make_tek(ghost=False):
    n = int(0.09 * SR)
    td = np.arange(n) / SR
    sos_h = signal.butter(4, [2500, 9000], "bandpass", fs=SR, output="sos")
    slap = signal.sosfilt(sos_h, rng.standard_normal(n))
    ping = 0.4 * np.sin(2 * np.pi * 640.0 * td)
    env = np.exp(-td * (90.0 if ghost else 55.0))
    x = (slap / (np.max(np.abs(slap)) + 1e-12) + ping) * env
    return x * (0.35 if ghost else 1.0)


# ---------------------------------------------------------------- samples

print("Generating water-of-life samples:")

KICK = make_kick()
buf = np.zeros(int(4.0 * SR))
for k in range(8):
    place(buf, KICK, 0.3 + k * BEAT, 1.0)
save("instrument_16_trance_kick.wav",
     "Trance kick: sine body diving 150->45 Hz (exp, rate 55), 0.8 ms "
     "attack, 25 % noise click. Eight hits four-to-the-floor at 140 BPM.",
     buf)

PB = {38: psy_bass_note(38), 36: psy_bass_note(36), 39: psy_bass_note(39)}
buf = np.zeros(int(4.5 * SR))
for bar in range(2):
    for beat in range(4):
        bt = 0.3 + (bar * 4 + beat) * BEAT
        place(buf, KICK, bt, 1.0)
        for s, g in [(1, 0.8), (2, 0.7), (3, 0.95)]:
            m = 38
            if bar == 1 and beat == 3:
                m = [36, 39, 38][s - 1]
            place(buf, PB[m], bt + s * STEP, g * 0.9)
save("instrument_17_psy_rolling_bass.wav",
     "Psy rolling bass: kick on the beat, bass on the three 16ths after "
     "(K-b-b-b). Band-limited saw on D2, lowpassed at 350 Hz, tanh drive, "
     "2 ms gate. Two bars; the second walks C2-Eb2-D2.", buf)

RIFF_MELO = [(50, 1), (50, 0), (62, 0), (50, 0),
             (63, 1), (62, 0), (54, 0), (50, 0),
             (57, 1), (None, 0), (55, 0), (54, 0),
             (51, 0), (54, 0), (50, 1), (None, 0)]
buf = np.zeros(int(6.0 * SR))
for bar in range(3):
    base = 350.0 + 1100.0 * bar / 2                   # cutoff opens per bar
    for s, (m, acc) in enumerate(RIFF_MELO):
        if m is None:
            continue
        cut = base * (1.0 + 0.25 * np.sin(2 * np.pi * s / 16))
        x = acid_note(m, cut, accent=bool(acc))
        place(buf, x, 0.3 + (bar * 16 + s) * STEP, 1.0)
save("instrument_18_acid_line_303.wav",
     "303-style acid line: band-limited saw through a resonant lowpass "
     "(butter lowpass + iirpeak Q=7 at the cutoff = the squelch), tanh "
     "drive, accents lift the cutoff 1.6x. Three bars with the cutoff "
     "opening 350 Hz -> 1.4 kHz.", buf)

OHAT = make_hat(open_=True)
CHAT = make_hat()
buf_L = np.zeros(int(4.0 * SR))
buf_R = np.zeros(int(4.0 * SR))
for bar in range(2):
    for beat in range(4):
        bt = 0.3 + (bar * 4 + beat) * BEAT
        place(buf_L, KICK, bt, 0.5)                   # quiet kick for context
        place(buf_R, KICK, bt, 0.5)
        place(buf_L, OHAT, bt + 0.5 * BEAT, 0.8)
        place(buf_R, OHAT, bt + 0.5 * BEAT, 1.0)
        for s in (1, 3):
            p = 0.3 + 0.4 * (s == 3)
            place(buf_L, CHAT, bt + s * STEP, 0.4 * np.cos(p * np.pi / 2))
            place(buf_R, CHAT, bt + s * STEP, 0.4 * np.sin(p * np.pi / 2))
save("instrument_19_offbeat_hats.wav",
     "Psytrance hats: open hat (7 kHz highpassed noise, 120 ms) on every "
     "offbeat, closed 16th ghosts answering L/R. Quiet kick included for "
     "the groove context.", buf_L, buf_R)

ZAP = make_zap()
buf = np.zeros(int(3.5 * SR))
for at, g in [(0.3, 1.0), (1.4, 0.8), (2.5, 1.0)]:
    place(buf, ZAP, at, g)
save("effect_06_zap_laser.wav",
     "Psy zap: sine diving 1980->80 Hz in ~150 ms with 35 Hz ring-mod "
     "shimmer. Punctuates phrase boundaries in the drops.", buf)

# four bars of the full groove
MAQSUM = {0: "D", 2: "T", 6: "T", 8: "D", 12: "T"}
DOUM, TEK, KA = make_doum(), make_tek(), make_tek(ghost=True)
RIFF_DARK = [(50, 1), (None, 0), (50, 0), (None, 0),
             (50, 0), (62, 1), (None, 0), (50, 0),
             (51, 0), (None, 0), (50, 0), (None, 0),
             (54, 1), (None, 0), (48, 0), (50, 0)]
PB[50] = psy_bass_note(50)
dur = 4 * 4 * BEAT + 1.0
g_L = np.zeros(int(dur * SR))
g_R = np.zeros(int(dur * SR))
for bar in range(4):
    bt = bar * 4 * BEAT
    for beat in range(4):
        place(g_L, KICK, bt + beat * BEAT, 1.0)
        place(g_R, KICK, bt + beat * BEAT, 1.0)
        place(g_L, OHAT, bt + (beat + 0.5) * BEAT, 0.35)
        place(g_R, OHAT, bt + (beat + 0.5) * BEAT, 0.45)
        for s, g in [(1, 0.8), (2, 0.7), (3, 0.95)]:
            m = 38
            if bar % 4 == 3 and beat == 3:
                m = [36, 39, 38][s - 1]
            for buf2 in (g_L, g_R):
                place(buf2, PB[m], bt + beat * BEAT + s * STEP, g * 0.85)
    base = 700.0 + 500.0 * np.sin(2 * np.pi * bar / 4)
    for s, (m, acc) in enumerate(RIFF_DARK):          # acid layer
        if m is None:
            continue
        x = acid_note(m, base * (1.0 + 0.25 * np.sin(2 * np.pi * s / 16)),
                      accent=bool(acc))
        p = 0.5 + 0.18 * np.sin(2 * np.pi * s / 16)
        place(g_L, x, bt + s * STEP, 0.5 * np.cos(p * np.pi / 2))
        place(g_R, x, bt + s * STEP, 0.5 * np.sin(p * np.pi / 2))
    for s in range(16):                               # darbuka layer
        at = bt + s * STEP
        stroke = MAQSUM.get(s)
        if stroke == "D":
            place(g_L, DOUM, at, 0.4)
            place(g_R, DOUM, at, 0.4)
        elif stroke == "T":
            p = 0.35 if s in (2, 12) else 0.65
            place(g_L, TEK, at, 0.4 * np.cos(p * np.pi / 2))
            place(g_R, TEK, at, 0.4 * np.sin(p * np.pi / 2))
        elif s % 2 == 1 and rng.random() < 0.25:
            place(g_L, KA, at, 0.22)
            place(g_R, KA, at, 0.2)
save("rhythm_03_psy_groove_140bpm.wav",
     "Four bars of the full Water of Life groove at 140 BPM: trance kick, "
     "rolling K-b-b-b bass, offbeat hats, dark acid line, light maqsum "
     "darbuka — the Juno Reactor-style tribal/trance fusion.", g_L, g_R)


# ---------------------------------------------------------------- manifest

readme = os.path.join(OUT_DIR, "README_water.txt")
with open(readme, "w") as f:
    f.write("Samples added for generate_water_of_life.py (continues the "
            "sample set; see README.txt, README_pursuit.txt, README_maker.txt)\n\n")
    for name, desc in manifest:
        f.write(f"{name}\n    {desc}\n\n")

print(f"\nWrote {len(manifest)} samples + README_water.txt to {OUT_DIR}")
