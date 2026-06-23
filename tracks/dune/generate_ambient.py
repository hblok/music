#!/usr/bin/env python3
"""
generate_ambient.py — procedurally generates an original electronic ambient track.

Pure numpy synthesis (no samples, no external audio assets), written to a
16-bit stereo WAV via the stdlib `wave` module.

Structure (~3 minutes):
  * A slowly evolving 4-chord pad progression (D minor pentatonic harmony),
    crossfaded with raised-cosine windows.
  * A continuous sub drone on D with slow amplitude breathing.
  * FFT-bandpass-filtered noise swells that drift across the stereo field.
  * Sparse sine "plucks" from the D minor pentatonic scale, fed through a
    feedback delay for a spacious echo tail.

Output: /workspace/music/ambient_track.wav
"""

import wave
import numpy as np

SR = 44100
DURATION = 180.0           # seconds
N = int(SR * DURATION)
t = np.arange(N) / SR

rng = np.random.default_rng(42)


# ---------------------------------------------------------------- helpers

def midi_to_hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def raised_cosine(n):
    """Smooth 0->1->0 window of n samples."""
    return 0.5 - 0.5 * np.cos(2 * np.pi * np.arange(n) / n)


def fade(x, fade_in=8.0, fade_out=15.0):
    """Apply smooth fade-in/out (seconds) to a signal in place."""
    ni, no = int(fade_in * SR), int(fade_out * SR)
    x[:ni] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(ni) / ni)
    x[-no:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(no) / no)
    return x


def fft_bandpass(x, lo, hi):
    """Brick-wall-ish bandpass via FFT (cheap, scipy-free)."""
    spec = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(len(x), 1.0 / SR)
    # soft edges to avoid ringing
    gain = np.clip((freqs - lo) / (lo * 0.5 + 1e-9), 0, 1) * \
           np.clip((hi - freqs) / (hi * 0.5 + 1e-9), 0, 1)
    return np.fft.irfft(spec * gain, n=len(x))


def feedback_delay(x, delay_s, feedback, taps=6):
    """Simple feedback echo."""
    y = x.copy()
    d = int(delay_s * SR)
    for k in range(1, taps + 1):
        g = feedback ** k
        y[k * d:] += x[: len(x) - k * d] * g
    return y


# ---------------------------------------------------------------- pads

# Chord progression in MIDI (Dm9 -> Bbmaj7 -> Fmaj7 -> Cadd9), one octave low
CHORDS = [
    [50, 57, 60, 64, 69],   # D  A  C  E  A   (Dm9)
    [46, 53, 57, 60, 65],   # Bb F  A  C  F   (Bbmaj7)
    [41, 53, 57, 60, 64],   # F  F  A  C  E   (Fmaj7)
    [48, 55, 62, 64, 67],   # C  G  D  E  G   (Cadd9)
]

SECTION = DURATION / len(CHORDS)        # 45 s per chord
XFADE = 8.0                             # crossfade length

pad_L = np.zeros(N)
pad_R = np.zeros(N)

for ci, chord in enumerate(CHORDS):
    start = ci * SECTION
    # section envelope: flat with raised-cosine edges, overlapping neighbours
    env = np.zeros(N)
    s0 = max(0, int((start - XFADE / 2) * SR))
    s1 = min(N, int((start + SECTION + XFADE / 2) * SR))
    seg = s1 - s0
    e = np.ones(seg)
    nf = int(XFADE * SR)
    e[:nf] = 0.5 - 0.5 * np.cos(np.pi * np.arange(nf) / nf)
    e[-nf:] = 0.5 + 0.5 * np.cos(np.pi * np.arange(nf) / nf)
    env[s0:s1] = e

    for vi, m in enumerate(chord):
        f = midi_to_hz(m)
        # each voice: pair of detuned sines + a quiet octave-up partial,
        # breathing on its own slow LFO
        lfo = 0.65 + 0.35 * np.sin(2 * np.pi * (0.02 + 0.013 * vi) * t
                                   + rng.uniform(0, 2 * np.pi))
        det = 1.0 + 0.0007 * (vi - 2)
        vL = (np.sin(2 * np.pi * f * det * t) +
              0.5 * np.sin(2 * np.pi * f * det * 1.002 * t) +
              0.18 * np.sin(2 * np.pi * 2 * f * det * t))
        vR = (np.sin(2 * np.pi * f / det * t + 0.7) +
              0.5 * np.sin(2 * np.pi * f / det * 0.998 * t) +
              0.18 * np.sin(2 * np.pi * 2 * f / det * t + 0.3))
        # gentle constant-power pan per voice
        pan = 0.5 + 0.35 * np.sin(vi * 1.7 + ci)
        pad_L += env * lfo * vL * np.cos(pan * np.pi / 2) * 0.16
        pad_R += env * lfo * vR * np.sin(pan * np.pi / 2) * 0.16

# ---------------------------------------------------------------- sub drone

f_sub = midi_to_hz(38)  # D1 ~ 36.7 Hz... midi 38 = D2 73.4? (38 -> D2)
breath = 0.7 + 0.3 * np.sin(2 * np.pi * 0.015 * t)
sub = breath * (np.sin(2 * np.pi * f_sub / 2 * t) +
                0.4 * np.sin(2 * np.pi * f_sub * t))
pad_L += 0.22 * sub
pad_R += 0.22 * sub

# ---------------------------------------------------------------- noise swells

noise = rng.standard_normal(N)
air = fft_bandpass(noise, 600, 3500)
air /= np.max(np.abs(air)) + 1e-9
# slow swell envelope (period ~28 s) plus drift between channels
swell = (0.5 - 0.5 * np.cos(2 * np.pi * t / 28.0)) ** 2
drift = 0.5 + 0.45 * np.sin(2 * np.pi * 0.009 * t)
pad_L += 0.05 * air * swell * drift
pad_R += 0.05 * air * swell * (1.0 - drift)

# low rumble texture
rumble = fft_bandpass(rng.standard_normal(N), 30, 120)
rumble /= np.max(np.abs(rumble)) + 1e-9
pad_L += 0.04 * rumble
pad_R += 0.04 * rumble

# ---------------------------------------------------------------- plucks

PENTA = [62, 65, 67, 69, 72, 74, 77]   # D minor pentatonic, octave 4-5
pluck_L = np.zeros(N)
pluck_R = np.zeros(N)

time_cursor = 40.0                      # plucks enter after the intro
while time_cursor < DURATION - 25.0:
    note = int(rng.choice(PENTA))
    f = midi_to_hz(note)
    dur = 4.0
    n = int(dur * SR)
    i0 = int(time_cursor * SR)
    tt = np.arange(n) / SR
    envp = np.exp(-tt * 1.8) * (1 - np.exp(-tt * 200))   # soft attack, long decay
    tone = envp * (np.sin(2 * np.pi * f * tt) +
                   0.3 * np.sin(2 * np.pi * 2 * f * tt) * np.exp(-tt * 4))
    pan = rng.uniform(0.2, 0.8)
    end = min(N, i0 + n)
    pluck_L[i0:end] += tone[: end - i0] * np.cos(pan * np.pi / 2) * 0.30
    pluck_R[i0:end] += tone[: end - i0] * np.sin(pan * np.pi / 2) * 0.30
    time_cursor += rng.uniform(5.0, 11.0)

# echo tails, slightly different delay per channel for width
pluck_L = feedback_delay(pluck_L, 0.52, 0.45)
pluck_R = feedback_delay(pluck_R, 0.39, 0.45)

# ---------------------------------------------------------------- mix & write

L = pad_L + pluck_L
R = pad_R + pluck_R
fade(L)
fade(R)

peak = max(np.max(np.abs(L)), np.max(np.abs(R)))
L = L / peak * 0.85
R = R / peak * 0.85

stereo = np.empty((N, 2))
stereo[:, 0] = L
stereo[:, 1] = R
pcm = (stereo * 32767.0).astype(np.int16)

import os
OUT_DIR = "/workspace/music"
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, "ambient_track.wav")
with wave.open(OUT, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())

print(f"Created: {os.path.abspath(OUT)}")
print(f"Duration: {N / SR:.1f} s  |  {SR} Hz stereo, 16-bit PCM")
