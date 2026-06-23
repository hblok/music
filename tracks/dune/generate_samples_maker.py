#!/usr/bin/env python3
"""
generate_samples_maker.py — listening glossary for the NEW instruments
introduced by generate_maker_comes.py. Recipes copied verbatim from the
track generator. Continues the sample numbering and NEVER overwrites: if
a target file already exists the script aborts before writing anything.

New samples:
  instrument_14_ney_flute.wav       breathy ney playing Theme C
  instrument_15_sardaukar_chant.wav formant-filtered throat-chant pulse

Output: /workspace/music/samples/*.wav + README_maker.txt
"""

import os
import sys
import wave
import numpy as np
from scipy import signal

SR = 44100
OUT_DIR = "/workspace/music/samples"
os.makedirs(OUT_DIR, exist_ok=True)

rng = np.random.default_rng(2024)

BPM = 104.0
BEAT = 60.0 / BPM

manifest = []

NEW_FILES = [
    "instrument_14_ney_flute.wav",
    "instrument_15_sardaukar_chant.wav",
    "README_maker.txt",
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
# (verbatim from generate_maker_comes.py)

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


def ney_phrase(notes):
    total = sum(d for _, d in notes) + 1.5
    n = int(total * SR)
    tt = np.arange(n) / SR
    f_curve = glide_curve(notes, n)
    vib = 1.0 + 0.004 * np.sin(2 * np.pi * 6.0 * tt) * np.clip(tt / 0.8, 0, 1)
    phase = 2 * np.pi * np.cumsum(f_curve * vib) / SR
    env = np.minimum(np.clip(tt / 0.6, 0, 1),
                     np.clip((total - tt) / 1.5, 0, 1)) ** 1.3
    tone = np.sin(phase) + 0.25 * np.sin(2 * phase) + 0.08 * np.sin(3 * phase)
    sos_b = signal.butter(2, [1200, 4000], "bandpass", fs=SR, output="sos")
    breath = signal.sosfilt(sos_b, rng.standard_normal(n))
    breath /= np.max(np.abs(breath)) + 1e-12
    v = env * (tone + 0.13 * breath)
    sos = signal.butter(2, 3200, "low", fs=SR, output="sos")
    return signal.sosfilt(sos, v)


def chant_note(midi, dur, pulse=5.5):
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    src = np.zeros(n)
    for k in range(1, 15):
        src += np.sin(2 * np.pi * k * f * td + rng.uniform(0, 2 * np.pi)) / k ** 0.8
    out = np.zeros(n)
    for (lo, hi), g in [((380, 560), 1.0), ((750, 1000), 0.6),
                        ((2200, 2700), 0.15)]:
        sos_f = signal.butter(2, [lo, hi], "bandpass", fs=SR, output="sos")
        out += g * signal.sosfilt(sos_f, src)
    out /= np.max(np.abs(out)) + 1e-12
    out *= 0.75 + 0.25 * np.sin(2 * np.pi * pulse * td)
    out += 0.40 * np.sin(2 * np.pi * 0.5 * f * td)
    env = np.minimum(np.clip(td / 0.06, 0, 1),
                     np.clip((dur - td) / 0.15, 0, 1)) ** 1.2
    x = out * env
    return x / (np.max(np.abs(x)) + 1e-12)


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


IR = make_reverb_ir(5.0, 1.6, 7)


# ---------------------------------------------------------------- samples

print("Generating maker samples:")

# ney: opening of Theme C, octave up, with the track's 55 % reverb
THEME_C_OPEN = [(69, 1.5 * BEAT), (70, 0.5 * BEAT), (69, 1.0 * BEAT),
                (67, 1.0 * BEAT), (66, 2.0 * BEAT), (63, 1.0 * BEAT),
                (66, 1.0 * BEAT), (62, 2.0 * BEAT)]
v = ney_phrase(THEME_C_OPEN)
v = reverb(v, IR, wet=0.55)
save("instrument_14_ney_flute.wav",
     "Ney flute: nearly pure tone (weak 2nd/3rd harmonics) + 13 % "
     "bandpassed breath noise riding the same envelope, fast shallow "
     "vibrato, portamento between notes. Playing the opening of Theme C "
     "with the track's 55 % reverb.", v)

# chant: two bars of the Sardaukar pulse on D2, with the C2 cadence
buf = np.zeros(int(6.5 * SR))
CH_LONG = {m: chant_note(m, 1.4 * BEAT) for m in (38, 36)}
CH_SHORT = {m: chant_note(m, 0.85 * BEAT) for m in (38, 36)}
for bar in range(2):
    root = 36 if bar == 1 else 38
    bt = 0.3 + bar * 4 * BEAT
    for beat, g, bank in [(0.0, 1.0, CH_LONG), (2.0, 0.8, CH_SHORT),
                          (3.0, 0.8, CH_SHORT)]:
        place(buf, bank[root], bt + beat * BEAT, g)
buf = reverb(buf, IR, wet=0.45)
save("instrument_15_sardaukar_chant.wav",
     "Sardaukar throat chant: 14-harmonic glottal source through three "
     "parallel formant bands (380-560 / 750-1000 / 2200-2700 Hz, dark "
     "'oh'), 5.5 Hz guttural amplitude pulse, sub-octave sine underneath. "
     "Two bars on D2, dropping to C2.", buf)


# ---------------------------------------------------------------- manifest

readme = os.path.join(OUT_DIR, "README_maker.txt")
with open(readme, "w") as f:
    f.write("Samples added for generate_maker_comes.py "
            "(continues the sample set; see README.txt, README_pursuit.txt)\n\n")
    for name, desc in manifest:
        f.write(f"{name}\n    {desc}\n\n")

print(f"\nWrote {len(manifest)} samples + README_maker.txt to {OUT_DIR}")
