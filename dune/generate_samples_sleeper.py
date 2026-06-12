#!/usr/bin/env python3
"""
generate_samples_sleeper.py — short demo samples of the new instruments
introduced by generate_sleeper_awakens.py ("The Sleeper Awakens"), written
to /workspace/music/samples/. Continues the numbering of the earlier
sample scripts and REFUSES to overwrite existing files.

New here:
  instrument_20_psy_clap.wav        four-burst flam clap, bp 900-5200 Hz,
                                    last burst rings out — beats 2 & 4
  instrument_21_acid_303_sharp.wav  the sharpened 303: per-note filter
                                    sweep (bright -> dark squelch), Q 11,
                                    tanh(2.8x) drive, slide notes —
                                    compare instrument_18_acid_line_303
  rhythm_04_psy_groove_145bpm_bright.wav
                                    the assembled brighter groove: hot
                                    kick click, louder hats, clap, sharp
                                    acid, brighter teks + master shelf
"""

import os
import sys
import wave
import numpy as np
from scipy import signal

SR = 44100
OUT_DIR = "/workspace/music/samples"

NEW_FILES = [
    "instrument_20_psy_clap.wav",
    "instrument_21_acid_303_sharp.wav",
    "rhythm_04_psy_groove_145bpm_bright.wav",
    "README_sleeper.txt",
]

existing = [f for f in NEW_FILES if os.path.exists(os.path.join(OUT_DIR, f))]
if existing:
    sys.exit(f"ABORT — would overwrite existing samples: {', '.join(existing)}")

os.makedirs(OUT_DIR, exist_ok=True)
rng = np.random.default_rng(303)

BPM = 145.0
BEAT = 60.0 / BPM
BAR = BEAT * 4
STEP = BEAT / 4


def midi_to_hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def add_at(buf, x, start_s, gain=1.0):
    i0 = int(start_s * SR)
    end = min(len(buf), i0 + len(x))
    if end > i0:
        buf[i0:end] += x[: end - i0] * gain


def write_wav(name, x):
    x = x / (np.max(np.abs(x)) + 1e-12) * 0.85
    pcm = (np.repeat(x[:, None], 2, axis=1) * 32767.0).astype(np.int16)
    path = os.path.join(OUT_DIR, name)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(f"wrote {path}  ({len(x) / SR:.1f} s)")


# ---------------------------------------------------------------- psy clap

def make_clap():
    n = int(0.26 * SR)
    td = np.arange(n) / SR
    sos_c = signal.butter(2, [900, 5200], "bandpass", fs=SR, output="sos")
    nz = signal.sosfilt(sos_c, rng.standard_normal(n))
    nz /= np.max(np.abs(nz)) + 1e-12
    env = np.zeros(n)
    for i, t0 in enumerate([0.0, 0.011, 0.022, 0.033]):
        i0 = int(t0 * SR)
        rate = 120.0 if i < 3 else 26.0
        seg = (0.65 if i < 3 else 1.0) * np.exp(-(td[i0:] - t0) * rate)
        env[i0:] = np.maximum(env[i0:], seg)
    x = nz * env
    return x / (np.max(np.abs(x)) + 1e-12)


CLAP = make_clap()

demo = np.zeros(int(4.0 * SR))
for i in range(5):
    add_at(demo, CLAP, 0.3 + i * 0.7, 1.0)
write_wav("instrument_20_psy_clap.wav", demo)


# ---------------------------------------------------------------- sharp 303

def acid_note(m, cutoff, accent=False, slide_to=None, dur=None):
    if dur is None:
        dur = STEP * (1.02 if slide_to else 0.92)
    cutoff = float(np.clip(cutoff * (1.5 if accent else 1.0), 200, 7500))
    f = midi_to_hz(m)
    n = int(dur * SR)
    td = np.arange(n) / SR
    if slide_to is None:
        ph = 2 * np.pi * f * td
    else:
        f2 = midi_to_hz(slide_to)
        fc = f * (f2 / f) ** np.clip((td - 0.45 * dur) / (0.55 * dur), 0, 1)
        ph = 2 * np.pi * np.cumsum(fc) / SR
    x = np.zeros(n)
    for k in range(1, min(48, int(10500 / min(f, midi_to_hz(slide_to))
                                  if slide_to else 10500 / f)) + 1):
        x += np.sin(k * ph) / k

    def res_lp(sig_in, c):
        c = float(min(c, 9000.0))
        sos_lp = signal.butter(2, c, "low", fs=SR, output="sos")
        y = signal.sosfilt(sos_lp, sig_in)
        bpk, apk = signal.iirpeak(min(c, 8000.0), Q=11.0, fs=SR)
        return y + (1.9 if accent else 1.4) * signal.lfilter(bpk, apk, y)

    bright = res_lp(x, cutoff * 3.0)
    dark = res_lp(x, cutoff * 0.75)
    sweep = np.exp(-td / (0.10 if accent else 0.055))
    y = np.tanh(2.8 * (sweep * bright + (1 - sweep) * dark))
    env = (1 - np.exp(-td / 0.0015)) * np.clip((dur - td) / 0.02, 0, 1)
    y *= env
    return y / (np.max(np.abs(y)) + 1e-12)


RIFF_SYNC = [(50, 1, None), (None, 0, None), (50, 0, 51), (51, 0, None),
             (None, 0, None), (50, 0, None), (54, 1, None), (None, 0, None),
             (57, 0, 55), (55, 0, None), (None, 0, None), (50, 0, None),
             (62, 1, None), (None, 0, None), (48, 0, 50), (50, 0, None)]

demo = np.zeros(int((8 * BAR + 1.0) * SR))
for b in range(8):
    base = 500 + (3200 - 500) * b / 7              # cutoff climbs bar by bar
    for s, (m, acc, sl) in enumerate(RIFF_SYNC):
        if m is None:
            continue
        cut = base * (1.0 + 0.25 * np.sin(2 * np.pi * s / 16))
        add_at(demo, acid_note(m, cut, accent=bool(acc), slide_to=sl),
               b * BAR + s * STEP, 1.0)
write_wav("instrument_21_acid_303_sharp.wav", demo)


# ---------------------------------------------------------------- groove
# Eight bars of the assembled bright psy groove: kick, rolling bass, hats,
# clap on 2 & 4, the sharp acid, brighter darbuka teks — with the master
# high-shelf, exactly as in the track's drops.

def make_kick():
    n = int(0.30 * SR)
    td = np.arange(n) / SR
    f_curve = 45.0 + 105.0 * np.exp(-td * 55.0)
    body = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    sos_c = signal.butter(2, [1800, 9000], "bandpass", fs=SR, output="sos")
    click = signal.sosfilt(sos_c, rng.standard_normal(n)) * np.exp(-td * 700)
    click /= np.max(np.abs(click)) + 1e-12
    env = (1 - np.exp(-td / 0.0008)) * np.exp(-td * 9.0)
    x = (body + 0.45 * click) * env
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


def make_hat(open_=False):
    n = int((0.16 if open_ else 0.045) * SR)
    td = np.arange(n) / SR
    sos_h = signal.butter(4, 6500 if open_ else 7000, "high",
                          fs=SR, output="sos")
    x = signal.sosfilt(sos_h, rng.standard_normal(n))
    x *= np.exp(-td * (24 if open_ else 100))
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
    sos_h = signal.butter(4, [2800, 10000], "bandpass", fs=SR, output="sos")
    slap = signal.sosfilt(sos_h, rng.standard_normal(n))
    ping = 0.4 * np.sin(2 * np.pi * 640.0 * td)
    env = np.exp(-td * (90.0 if ghost else 55.0))
    x = (slap / (np.max(np.abs(slap)) + 1e-12) + ping) * env
    return x * (0.35 if ghost else 1.0)


KICK = make_kick()
PB38 = psy_bass_note(38)
OHAT = make_hat(open_=True)
CHAT = make_hat()
DOUM = make_doum()
TEK = make_tek()
MAQSUM = {0: "D", 2: "T", 6: "T", 8: "D", 12: "T"}

NB = 8
demo = np.zeros(int((NB * BAR + 1.0) * SR))
for b in range(NB):
    for beat in range(4):
        t0 = b * BAR + beat * BEAT
        add_at(demo, KICK, t0, 0.95)
        add_at(demo, OHAT, t0 + 0.5 * BEAT, 0.30)
        for s in (1, 2, 3):
            add_at(demo, PB38, t0 + s * STEP, 0.75 * (0.8, 0.7, 0.95)[s - 1])
    for beat in (1, 3):                              # the clap
        add_at(demo, CLAP, b * BAR + beat * BEAT, 0.35)
    for s in range(16):                              # closed-hat ghosts
        if s % 2 == 1:
            add_at(demo, CHAT, b * BAR + s * STEP, 0.10)
    if b >= 2:                                       # darbuka rides the grid
        for s in range(16):
            stroke = MAQSUM.get(s)
            if stroke == "D":
                add_at(demo, DOUM, b * BAR + s * STEP, 0.5)
            elif stroke == "T":
                add_at(demo, TEK, b * BAR + s * STEP, 0.4)
    if b >= 4:                                       # the sharp acid joins
        base = 1400 + 600 * np.sin(2 * np.pi * (b - 4) / 8)
        for s, (m, acc, sl) in enumerate(RIFF_SYNC):
            if m is None:
                continue
            add_at(demo, acid_note(m, base, accent=bool(acc), slide_to=sl),
                   b * BAR + s * STEP, 0.40)
sos_shelf = signal.butter(2, 3000, "high", fs=SR, output="sos")
demo += 0.22 * signal.sosfilt(sos_shelf, demo)       # the master shelf
write_wav("rhythm_04_psy_groove_145bpm_bright.wav", demo)


# ---------------------------------------------------------------- README

readme = """\
Samples introduced by generate_sleeper_awakens.py ("The Sleeper Awakens")
=========================================================================

instrument_20_psy_clap.wav
    Psy trance clap: four noise bursts 11 ms apart (the "many hands"
    flam), bandpassed 900-5200 Hz; the first three are damped fast, the
    last rings out. Sits on beats 2 & 4 through the drops — a big part
    of un-muting the groove.

instrument_21_acid_303_sharp.wav
    The sharpened 303 line, built from feedback that the original
    (instrument_18) sounded flat. Three changes: (1) the filter SWEEPS
    within every note — each note opens ~3x brighter than its base
    cutoff and squelches down over ~55 ms (accents deeper and slower),
    the actual TB-303 envelope behavior; (2) resonance Q 7 -> 11 with a
    hotter peak feed and drive tanh(2.2x) -> tanh(2.8x); (3) SLIDE
    notes that glide into the next pitch (the 303 tie). The demo climbs
    its base cutoff over eight bars of the syncopated slide riff.

rhythm_04_psy_groove_145bpm_bright.wav
    The assembled brightened groove at 145 BPM: trance kick with a
    hotter bandpassed click, rolling K-b-b-b bass, offbeat open hats
    (louder, longer), closed-hat 16th ghosts, the clap on 2 & 4,
    brighter darbuka teks (bp up to 10 kHz), and the sharp acid joining
    halfway — finished with the track's master high-shelf (+~1.7 dB
    above 3 kHz). Compare rhythm_03_psy_groove_140bpm to hear the
    "muted -> bright" fix directly.
"""
with open(os.path.join(OUT_DIR, "README_sleeper.txt"), "w") as fh:
    fh.write(readme)
print(f"wrote {os.path.join(OUT_DIR, 'README_sleeper.txt')}")
print("\nAll sleeper-awakens samples written — nothing overwritten.")
