#!/usr/bin/env python3
"""
generate_samples_pursuit.py — listening glossary for the NEW instruments and
effects introduced by generate_night_pursuit.py. Recipes copied verbatim
from the track generator (scripts are standalone by convention).

Continues the numbering of the original generate_samples.py set and NEVER
overwrites: if a target file already exists the script aborts before
writing anything.

New samples:
  instrument_09_war_drum.wav          taiko-like falling-pitch war drum
  instrument_10_frame_drum_roll.wav   daf hit, then an accelerating roll
  instrument_11_tick_tock_clock.wav   the John Wick clock ostinato
  instrument_12_gated_bass_pulse.wav  tanh-warmed gated sub-bass ostinato
  instrument_13_tremolo_strings.wav   detuned additive tremolo string bed
  effect_05_riser_sweep.wav           swept-band noise riser + rising tone
  rhythm_02_pursuit_groove_104bpm.wav four bars of the assembled groove

Output: /workspace/music/samples/*.wav + README_pursuit.txt
"""

import os
import sys
import wave
import numpy as np
from scipy import signal

SR = 44100
OUT_DIR = "/workspace/music/samples"
os.makedirs(OUT_DIR, exist_ok=True)

rng = np.random.default_rng(1984)

BPM = 104.0
BEAT = 60.0 / BPM

manifest = []

NEW_FILES = [
    "instrument_09_war_drum.wav",
    "instrument_10_frame_drum_roll.wav",
    "instrument_11_tick_tock_clock.wav",
    "instrument_12_gated_bass_pulse.wav",
    "instrument_13_tremolo_strings.wav",
    "effect_05_riser_sweep.wav",
    "rhythm_02_pursuit_groove_104bpm.wav",
    "README_pursuit.txt",
]
existing = [f for f in NEW_FILES if os.path.exists(os.path.join(OUT_DIR, f))]
if existing:
    sys.exit(f"ABORT — would overwrite existing samples: {', '.join(existing)}")


# ---------------------------------------------------------------- plumbing

def midi_to_hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def save(name, desc, L, R=None):
    """Peak-normalize, de-click edges, write 16-bit stereo WAV."""
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
# (verbatim from generate_night_pursuit.py)

def make_war_drum():
    n = int(0.9 * SR)
    td = np.arange(n) / SR
    f_curve = 42.0 + 48.0 * np.exp(-td * 9.0)
    body = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    sos_sk = signal.butter(2, [100, 420], "bandpass", fs=SR, output="sos")
    skin = signal.sosfilt(sos_sk, rng.standard_normal(n)) * np.exp(-td * 22)
    skin /= np.max(np.abs(skin)) + 1e-12
    env = np.exp(-td * 5.5) * (1 - np.exp(-td / 0.006))
    x = body * env + 0.5 * skin * env
    return x / (np.max(np.abs(x)) + 1e-12)


def make_frame_hit():
    n = int(0.12 * SR)
    td = np.arange(n) / SR
    sos_f = signal.butter(2, [180, 1400], "bandpass", fs=SR, output="sos")
    nz = signal.sosfilt(sos_f, rng.standard_normal(n)) * np.exp(-td * 40)
    nz /= np.max(np.abs(nz)) + 1e-12
    tone = 0.5 * np.sin(2 * np.pi * 95.0 * td) * np.exp(-td * 30)
    x = nz + tone
    return x / (np.max(np.abs(x)) + 1e-12)


def frame_roll(frame, dur=2.0):
    out = np.zeros(int((dur + 0.3) * SR))
    tcur = 0.0
    while tcur < dur:
        frac = tcur / dur
        rate = 9.0 + 11.0 * frac
        g = (0.30 + 0.70 * frac) * rng.uniform(0.85, 1.0)
        place(out, frame, tcur, g)
        tcur += 1.0 / rate
    return out


def make_tick(tock=False):
    n = int(0.030 * SR)
    td = np.arange(n) / SR
    f = 1500.0 if tock else 2100.0
    sos_c = signal.butter(2, [f * 0.8, f * 1.5], "bandpass", fs=SR, output="sos")
    click = signal.sosfilt(sos_c, rng.standard_normal(n)) * np.exp(-td * 240)
    click /= np.max(np.abs(click)) + 1e-12
    ping = 0.6 * np.sin(2 * np.pi * (880.0 if tock else 1250.0) * td) * \
        np.exp(-td * 180)
    x = click + ping
    return x / (np.max(np.abs(x)) + 1e-12)


def bass_note(midi, dur):
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * td) + 0.35 * np.sin(2 * np.pi * 2 * f * td + 0.3)
    x = np.tanh(1.6 * x)
    env = (1 - np.exp(-td / 0.005)) * np.clip((dur - td) / 0.05, 0, 1)
    return x * env


def tremolo_strings(chord, dur, trem_hz=10.5):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    out = np.zeros(n)
    for m in chord:
        f = midi_to_hz(m)
        for det, g in [(0.996, 0.6), (1.0, 1.0), (1.005, 0.6)]:
            for k in range(1, 9):
                out += (g / k) * np.sin(2 * np.pi * f * det * k * tt +
                                        rng.uniform(0, 2 * np.pi))
    sos_s = signal.butter(2, [180, 2600], "bandpass", fs=SR, output="sos")
    out = signal.sosfilt(sos_s, out)
    trem = (0.5 + 0.5 * np.sin(2 * np.pi * trem_hz * tt)) ** 1.2
    env = np.minimum(np.clip(tt / 1.5, 0, 1), np.clip((dur - tt) / 2.0, 0, 1))
    out *= trem * env
    return out / (np.max(np.abs(out)) + 1e-12)


def riser(dur=4.0):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    nz = rng.standard_normal(n)
    out = np.zeros(n)
    K = 10
    for k in range(K):
        c = 300.0 * (5500.0 / 300.0) ** (k / (K - 1))
        sos_r = signal.butter(2, [c * 0.7, c * 1.4], "bandpass",
                              fs=SR, output="sos")
        band = signal.sosfilt(sos_r, nz)
        center = (k + 0.5) / K * dur
        w = np.clip(1 - np.abs(tt - center) / (dur / K * 1.6), 0, 1)
        out += band * w
    out /= np.max(np.abs(out)) + 1e-12
    f_curve = 70.0 * 2.0 ** (2.0 * tt / dur)
    tone = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    x = (out + 0.45 * tone) * (tt / dur) ** 2
    return x / (np.max(np.abs(x)) + 1e-12)


# darbuka kit (from generate_base_attack.py, needed for the groove sample)

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

print("Generating pursuit samples:")

WAR = make_war_drum()
buf = np.zeros(int(5.0 * SR))
for at, g in [(0.3, 1.0), (1.6, 0.7), (2.9, 1.0), (3.4, 0.7), (3.9, 1.0)]:
    place(buf, WAR, at, g)
save("instrument_09_war_drum.wav",
     "Taiko-like war drum: sine body falling 90->42 Hz under a 100-420 Hz "
     "bandpassed skin slap, 6 ms attack. Single hits, then the doubled "
     "'cornered' figure.", buf)

FRAME = make_frame_hit()
buf = np.zeros(int(6.0 * SR))
for at, g in [(0.3, 1.0), (1.0, 0.7), (1.7, 1.0)]:
    place(buf, FRAME, at, g)
place(buf, frame_roll(FRAME, 2.4), 2.8, 1.0)
save("instrument_10_frame_drum_roll.wav",
     "Daf/bendir frame drum: 180-1400 Hz bandpassed noise + 95 Hz skin "
     "tone. Three hits, then an accelerating crescendo roll (9->20 hits/s) "
     "as used to launch the chase.", buf)

TICK = make_tick()
TOCK = make_tick(tock=True)
buf_L = np.zeros(int(5.0 * SR))
buf_R = np.zeros(int(5.0 * SR))
for e in range(16):                     # two bars of eighths at 104 BPM
    at = 0.3 + e * 0.5 * BEAT
    if e % 2 == 0:
        place(buf_L, TICK, at, 1.0)
        place(buf_R, TICK, at, 0.55)
    else:
        place(buf_L, TOCK, at, 0.50)
        place(buf_R, TOCK, at, 0.85)
save("instrument_11_tick_tock_clock.wav",
     "The John Wick clock: bone-dry 30 ms tick (2.1 kHz) / tock (1.5 kHz) "
     "clicks in straight eighths at 104 BPM, tick left, tock right.",
     buf_L, buf_R)

GATE16 = [1.0, 0, 0.7, 0, 1.0, 0, 0.7, 0.7,
          1.0, 0, 0.7, 0, 1.0, 0.7, 0, 0.7]
note16 = {m: bass_note(m, BEAT * 0.24) for m in (38, 36, 39)}
buf = np.zeros(int(6.0 * SR))
for bar in range(2):
    for s, g in enumerate(GATE16):
        if g == 0:
            continue
        m = 38
        if bar == 1 and s >= 12:
            m = [36, 39, 38, 38][s - 12]
        place(buf, note16[m], 0.3 + (bar * 16 + s) * 0.25 * BEAT, g)
save("instrument_12_gated_bass_pulse.wav",
     "Gated sub-bass ostinato on D2: sine + soft 2nd harmonic through tanh "
     "(warm, not sawtooth), chopped into accented 16ths. Two bars; the "
     "second walks C2-Eb2-D2 at the cadence.", buf)

buf = tremolo_strings([62, 63], 6.0)
save("instrument_13_tremolo_strings.wav",
     "Tremolo string bed: 3x detuned additive 'bow' tones (8 harmonics, "
     "1/k gains) per note, bandpassed 180-2600 Hz, 10.5 Hz tremolo whose "
     "envelope touches silence each cycle. Chord: D4 + Eb4 minor second.",
     buf)

buf = riser(4.0)
save("effect_05_riser_sweep.wav",
     "Riser: noise crossfaded through 10 rising bandpass bands "
     "(300 Hz -> 5.5 kHz) + a tone climbing two octaves from 70 Hz, "
     "amplitude ramping as t^2. Launches the chase and the climax.", buf)

# four bars of the assembled pursuit groove
MAQSUM = {0: "D", 2: "T", 6: "T", 8: "D", 12: "T"}
DOUM, TEK, KA = make_doum(), make_tek(), make_tek(ghost=True)
dur = 4 * 4 * BEAT + 1.0
g_L = np.zeros(int(dur * SR))
g_R = np.zeros(int(dur * SR))
for bar in range(4):
    bt = bar * 4 * BEAT
    for e in range(8):                               # tick layer
        at = bt + e * 0.5 * BEAT
        if e % 2 == 0:
            place(g_L, TICK, at, 0.30)
            place(g_R, TICK, at, 0.17)
        else:
            place(g_L, TOCK, at, 0.15)
            place(g_R, TOCK, at, 0.26)
    for s, gn in enumerate(GATE16):                  # bass layer
        if gn == 0:
            continue
        m = 38
        if bar == 3 and s >= 12:
            m = [36, 39, 38, 38][s - 12]
        for buf2 in (g_L, g_R):
            place(buf2, note16[m], bt + s * 0.25 * BEAT, gn * 0.9)
    for beat, gn in [(0.0, 0.95), (1.75, 0.5), (3.0, 0.7)]:   # war drum
        for buf2 in (g_L, g_R):
            place(buf2, WAR, bt + beat * BEAT, gn)
    for s in range(16):                              # darbuka maqsum
        at = bt + s * 0.25 * BEAT
        stroke = MAQSUM.get(s)
        if stroke == "D":
            place(g_L, DOUM, at, 0.6)
            place(g_R, DOUM, at, 0.6)
        elif stroke == "T":
            p = 0.35 if s in (2, 12) else 0.65
            place(g_L, TEK, at, 0.6 * np.cos(p * np.pi / 2))
            place(g_R, TEK, at, 0.6 * np.sin(p * np.pi / 2))
        elif s % 2 == 1 and rng.random() < 0.3:
            place(g_L, KA, at, 0.35)
            place(g_R, KA, at, 0.3)
    for s, gn in [(3, 0.18), (7, 0.20), (10, 0.16), (15, 0.23)]:  # frame skips
        p = 0.35 if s in (3, 10) else 0.65
        place(g_L, FRAME, bt + s * 0.25 * BEAT, gn * np.cos(p * np.pi / 2))
        place(g_R, FRAME, bt + s * 0.25 * BEAT, gn * np.sin(p * np.pi / 2))
save("rhythm_02_pursuit_groove_104bpm.wav",
     "Four bars of the full pursuit groove at 104 BPM: tick-tock clock, "
     "gated 16th bass on D2, war-drum accents (1, 2.75, 4), maqsum darbuka "
     "and frame-drum skips. The chase section of night_pursuit.wav.",
     g_L, g_R)


# ---------------------------------------------------------------- manifest

readme = os.path.join(OUT_DIR, "README_pursuit.txt")
with open(readme, "w") as f:
    f.write("Samples added for generate_night_pursuit.py "
            "(continues the original sample set; see README.txt)\n\n")
    for name, desc in manifest:
        f.write(f"{name}\n    {desc}\n\n")

print(f"\nWrote {len(manifest)} samples + README_pursuit.txt to {OUT_DIR}")
