#!/usr/bin/env python3
"""
generate_sandstorm_coriolis.py — Sandstorm Coriolis: the weather-event
OVERLAY for the Dune RTS. Not a standalone track — the game engine fades
this in OVER whatever state music is playing (everything is in D, so it
blends), holds it while the storm lasts, and fades it out.

72-second SEAMLESS LOOP (the established fold technique). Overlay rules:
no melody, no discrete events, no lulls (an overlay that goes quiet is a
bug — the storm is either on or off), no fade-in/out of its own. The only
tonal content is a faint D pedal so the wall stays in tune with the music
underneath.

Palette:
  * The noise wall    — dense 300 Hz–8 kHz noise, both channels drawn
                        independently (wide), with fast random flutter AM
                        (8–14 Hz bandpassed noise as the modulator) and
                        gusts at 3x the normal arrakis rate. Floor 0.45 —
                        the storm never lulls.
  * SHEPARD WIND      — the new trick: eight whistle voices (narrowband
                        noise approximated by sines under random FM) that
                        glide perpetually upward through 4 octaves
                        (300 Hz → 4.8 kHz) and renew at the bottom, each
                        silent at the spectral edges — the auditory
                        illusion of endlessly rising fury that never
                        arrives. Each voice also pans in a slow circle:
                        the Coriolis rotation.
  * Storm body        — brown-noise sub rumble below 130 Hz surging with
                        the slow gust front: the weight you feel in the
                        chest.
  * Sand blast        — the granular crackle recipe, but dense and tied
                        to the fast gusts: sand hitting the canopy.
  * D pedal           — faint D2+D3 with slow beating, the tuning anchor.

Loop math: Shepard traverse T = 36 s with DURATION = 72 s = 2T, so every
voice returns exactly to its starting spectral position at the wrap;
rotation period 9 s divides 72. The fold blends the non-periodic noise.

Output: /workspace/music/sandstorm_coriolis.wav (stereo, 44100 Hz, 16-bit).
"""

import os
import wave
import numpy as np
from scipy import signal

SR = 44100
DURATION = 72.0
XF = 6.0
DUR_TOTAL = DURATION + XF
N = int(SR * DURATION)
M = int(SR * DUR_TOTAL)
t = np.arange(M) / SR

rng = np.random.default_rng(360)    # one full rotation


# ---------------------------------------------------------------- helpers

def midi_to_hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def slow_noise(rate_hz, lo=0.0, hi=1.0):
    k = max(4, int(DUR_TOTAL * rate_hz))
    pts = rng.standard_normal(k)
    pts = np.convolve(pts, np.ones(3) / 3, mode="same")
    ctrl = np.interp(t, np.linspace(0, DUR_TOTAL, k), pts)
    ctrl = (ctrl - ctrl.min()) / (ctrl.max() - ctrl.min() + 1e-12)
    return lo + (hi - lo) * ctrl


mix_L = np.zeros(M)
mix_R = np.zeros(M)
N_LAYERS = 0


def commit(layer_L, layer_R, weight):
    global N_LAYERS
    peak = max(np.max(np.abs(layer_L)), np.max(np.abs(layer_R))) + 1e-12
    mix_L[:] += layer_L * (weight / peak)
    mix_R[:] += layer_R * (weight / peak)
    N_LAYERS += 1


# ---------------------------------------------------------------- the wall

# independent noise per channel — a wide, dense wall
sos_wall = signal.butter(2, [300, 8000], "bandpass", fs=SR, output="sos")
wall_L = signal.sosfilt(sos_wall, rng.standard_normal(M))
wall_R = signal.sosfilt(sos_wall, rng.standard_normal(M))
wall_L /= np.max(np.abs(wall_L))
wall_R /= np.max(np.abs(wall_R))

# fast random flutter: 8-14 Hz bandpassed noise as the AM source
sos_fl = signal.butter(2, [8, 14], "bandpass", fs=SR, output="sos")
flut_L = signal.sosfilt(sos_fl, rng.standard_normal(M))
flut_R = signal.sosfilt(sos_fl, rng.standard_normal(M))
flut_L = np.clip(0.70 + 0.30 * flut_L / (3 * flut_L.std()), 0.35, 1.0)
flut_R = np.clip(0.70 + 0.30 * flut_R / (3 * flut_R.std()), 0.35, 1.0)

# gusts at 3x the normal arrakis rate, with a HIGH floor: the storm never
# lulls (an overlay that goes quiet is a bug) — exponents softened too
gust = slow_noise(0.66) ** 1.6
gust2 = slow_noise(0.21) ** 1.2
wall_env = 0.60 + 0.40 * (0.6 * gust + 0.4 * gust2)

commit(wall_L * wall_env * flut_L, wall_R * wall_env * flut_R, 0.34)
del wall_L, wall_R, flut_L, flut_R


# ---------------------------------------------------------------- shepard

# eight whistle voices gliding perpetually upward through 4 octaves and
# renewing at the bottom — endlessly rising fury that never arrives
F_LO = 300.0
OCTAVES = 4.0
T_TRAV = 36.0                # full traverse; DURATION = 2 traversals
N_VOICES = 8
T_ROT = 9.0                  # Coriolis pan rotation, divides DURATION

sh_L = np.zeros(M)
sh_R = np.zeros(M)
for k in range(N_VOICES):
    p = np.mod(t / T_TRAV + k / N_VOICES, 1.0)          # spectral position
    f = F_LO * 2.0 ** (p * OCTAVES)
    # narrowband-noise whistle: sine under slow + fast random FM
    f = f * (1.0 + 0.018 * slow_noise(0.8, -1, 1) + 0.005 * slow_noise(6.0, -1, 1))
    phase = 2 * np.pi * np.cumsum(f) / SR
    voice = np.sin(phase) + 0.20 * np.sin(2 * phase)
    # silent at both spectral edges — this hides the wrap completely
    w = np.sin(np.pi * p) ** 2
    voice *= w * slow_noise(1.5, 0.55, 1.0)             # breathy roughness
    # the rotation: each voice circles the field with its own phase
    pn = 0.5 + 0.4 * np.sin(2 * np.pi * t / T_ROT + 2 * np.pi * k / N_VOICES)
    sh_L += voice * np.cos(pn * np.pi / 2)
    sh_R += voice * np.sin(pn * np.pi / 2)
    del p, f, phase, voice, w, pn
commit(sh_L * (0.7 + 0.3 * gust), sh_R * (0.7 + 0.3 * gust), 0.26)
del sh_L, sh_R


# ---------------------------------------------------------------- body

# brown-noise sub rumble surging with the slow front: chest weight
brown = np.cumsum(rng.standard_normal(M))
brown -= np.linspace(brown[0], brown[-1], M)            # detrend
sos_sub = signal.butter(2, 130, "low", fs=SR, output="sos")
body = signal.sosfilt(sos_sub, brown)
body /= np.max(np.abs(body))
surge = 0.6 + 0.4 * gust2
commit(body * surge, body * surge, 0.24)
del brown, body


# ---------------------------------------------------------------- sand

# sand hitting the canopy: dense granular crackle tied to the fast gusts
sos_cr = signal.butter(4, 5500, "high", fs=SR, output="sos")
crack_L = signal.sosfilt(sos_cr, rng.standard_normal(M))
crack_R = signal.sosfilt(sos_cr, rng.standard_normal(M))
crack_L /= np.max(np.abs(crack_L))
crack_R /= np.max(np.abs(crack_R))
spikes_L = np.clip(slow_noise(8.0), 0, 1) ** 6
spikes_R = np.clip(slow_noise(8.0), 0, 1) ** 6
commit(crack_L * spikes_L * wall_env, crack_R * spikes_R * wall_env, 0.055)
del crack_L, crack_R, spikes_L, spikes_R


# ---------------------------------------------------------------- D pedal

# the only tonal anchor: faint D2 + D3 with slow beating, so the overlay
# stays in tune with whatever plays underneath
f_D2 = midi_to_hz(38)
pedal = (np.sin(2 * np.pi * f_D2 * t) +
         0.50 * np.sin(2 * np.pi * f_D2 * 2 * t + 0.7) +
         0.35 * np.sin(2 * np.pi * f_D2 * 1.002 * t))
pedal *= 0.75 + 0.25 * np.sin(2 * np.pi * 0.05 * t)
commit(pedal, pedal, 0.10)
del pedal


# ---------------------------------------------------------------- slow AGC

# overlay leveler: independent gust/flutter wanders occasionally align low,
# and a storm overlay must NOT lull. A zero-phase 0.5 Hz envelope follower
# levels second-to-second energy (gain clipped 0.75-1.6x) while leaving the
# 8-14 Hz flutter and everything faster fully intact.
env = np.abs(mix_L) + np.abs(mix_R)
sos_agc = signal.butter(2, 0.5, "low", fs=SR, output="sos")
env = signal.sosfiltfilt(sos_agc, env)
env = np.maximum(env, 1e-9)
agc = np.clip(np.median(env) / env, 0.75, 1.6)
mix_L *= agc
mix_R *= agc
del env, agc


# ---------------------------------------------------------------- loop fold

nxf = int(XF * SR)
u = np.arange(nxf) / nxf
w_in, w_out = np.sin(0.5 * np.pi * u), np.cos(0.5 * np.pi * u)
L = mix_L[:N].copy()
R = mix_R[:N].copy()
L[:nxf] = w_in * L[:nxf] + w_out * mix_L[N:N + nxf]
R[:nxf] = w_in * R[:nxf] + w_out * mix_R[N:N + nxf]

peak = max(np.max(np.abs(L)), np.max(np.abs(R)))
L = L / peak * 0.85
R = R / peak * 0.85

stereo = np.empty((N, 2))
stereo[:, 0] = L
stereo[:, 1] = R
pcm = (stereo * 32767.0).astype(np.int16)

OUT_DIR = "/workspace/music"
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, "sandstorm_coriolis.wav")
with wave.open(OUT, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())

print(f"Created: {os.path.abspath(OUT)}")
print(f"Duration: {N / SR:.1f} s  |  seamless loop (fold {XF:.0f} s)  |  "
      f"{N_LAYERS} layers  |  OVERLAY: fade in over any state track")
print(f"Shepard wind: {N_VOICES} voices, {F_LO:.0f} Hz + {OCTAVES:.0f} oct, "
      f"traverse {T_TRAV:.0f} s (= DURATION/2), rotation {T_ROT:.0f} s")
print("No melody, no events, no lulls — only the faint D pedal is tonal")
