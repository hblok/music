#!/usr/bin/env python3
"""
generate_stillsuit.py — Stillsuit: the tension/enemy-sighted state loop for
the Dune RTS. Enemy units spotted, nothing fired yet.

night_pursuit Act II distilled into a SEAMLESS LOOP: 96 BPM, 72 bars =
exactly 3:00, loop-folded over 2 bars on the grid (the spice_must_flow
technique). The loop must be able to run for ten minutes without
resolving, so the KEY DESIGN RULE is: **nothing ever builds** — a build
promises a drop that game logic may never deliver. All variation is
wandering (slow_noise gain drift) or cyclical, never a ramp.

Palette:
  * Tick-tock clock      — the star. Bone-dry 30 ms clicks in straight
                           8ths, tick (2.1 kHz, panned L) answering tock
                           (1.5 kHz, panned R). Constant gain, never
                           varies — the one fixed point of the watch.
  * Gated sub-bass pulse — tanh-warmed sine ostinato in sparse 16ths on
                           D2, the C2–Eb2–D2 cadence walk every 4th bar;
                           gain wanders ±8 %, never ramps.
  * Tremolo strings      — the D+Eb minor second (with A below), 10.5 Hz
                           tremolo touching true silence each cycle;
                           gain wanders on a slow_noise drift, 0.25–1.0.
  * Stillsuit breathing  — YOUR own breath through the mask: one breath
                           per bar (~26/min, slightly too fast), a bright
                           inhale on beats 1–2, a darker exhale on 3–4.
                           Close and dry — it is inside your hood.
  * The unresolved Eb    — twice, a lone held flat-second hangs over the
                           watch for two bars and fades WITHOUT resolving
                           to D. A question with no answer yet.
  * Low wind + D1 drone  — the desert is still there, quieter than ever.

No percussion fills, no risers, no builds, no resolution.

Output: /workspace/music/stillsuit.wav (stereo, 44100 Hz, 16-bit).
"""

import os
import wave
import numpy as np
from scipy import signal

SR = 44100
BPM = 96.0
BEAT = 60.0 / BPM            # 0.625 s
BAR = 4 * BEAT               # 2.5 s
BARS = 72
DURATION = BARS * BAR        # 180.0 s = 3:00
XF = 2 * BAR                 # fold 2 bars, on the grid
DUR_TOTAL = DURATION + XF
N = int(SR * DURATION)
M = int(SR * DUR_TOTAL)
t = np.arange(M) / SR

rng = np.random.default_rng(38)     # D2 — the note this loop sits on


# ---------------------------------------------------------------- helpers

def midi_to_hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def bar_t(b, beat=0.0):
    return (b * 4 + beat) * BEAT


def slow_noise(rate_hz, lo=0.0, hi=1.0):
    k = max(4, int(DUR_TOTAL * rate_hz))
    pts = rng.standard_normal(k)
    pts = np.convolve(pts, np.ones(3) / 3, mode="same")
    ctrl = np.interp(t, np.linspace(0, DUR_TOTAL, k), pts)
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


IR_L = make_reverb_ir(4.0, 1.4, 7)
IR_R = make_reverb_ir(4.0, 1.4, 11)

mix_L = np.zeros(M)
mix_R = np.zeros(M)
N_LAYERS = 0


def commit(layer_L, layer_R, weight):
    global N_LAYERS
    peak = max(np.max(np.abs(layer_L)), np.max(np.abs(layer_R))) + 1e-12
    mix_L[:] += layer_L * (weight / peak)
    mix_R[:] += layer_R * (weight / peak)
    N_LAYERS += 1


# ---------------------------------------------------------------- wind

raw = rng.standard_normal(M)
sos_whoosh = signal.butter(4, [120, 900], "bandpass", fs=SR, output="sos")
whoosh = signal.sosfilt(sos_whoosh, raw)
whoosh /= np.max(np.abs(whoosh))
del raw

gust = slow_noise(0.22) ** 2.2
gust2 = slow_noise(0.07) ** 1.5
wind_env = 0.25 + 0.75 * (0.6 * gust + 0.4 * gust2)
pan = slow_noise(0.05, 0.35, 0.65)
wind_L = wind_env * whoosh * np.cos(pan * np.pi / 2)
wind_R = wind_env * whoosh * np.sin(pan * np.pi / 2)
commit(wind_L, wind_R, 0.11)            # the quietest wind on the album
del wind_L, wind_R, whoosh


# ---------------------------------------------------------------- drone

f_D1 = midi_to_hz(26)
breath_lfo = 0.7 + 0.3 * np.sin(2 * np.pi * 0.012 * t + 1.0)
drone = (np.sin(2 * np.pi * f_D1 * t) +
         0.55 * np.sin(2 * np.pi * f_D1 * 2 * t + 0.4) +
         0.30 * np.sin(2 * np.pi * f_D1 * 3 * t) +
         0.30 * np.sin(2 * np.pi * f_D1 * 3.003 * t))
drone *= breath_lfo
commit(drone, drone, 0.14)
del drone, breath_lfo


# ---------------------------------------------------------------- the tick

def click(bp_lo, bp_hi, f_ping):
    n = int(0.030 * SR)
    tt = np.arange(n) / SR
    sos_c = signal.butter(2, [bp_lo, bp_hi], "bandpass", fs=SR, output="sos")
    burst = signal.sosfilt(sos_c, rng.standard_normal(n)) * np.exp(-tt * 160)
    burst /= np.max(np.abs(burst)) + 1e-12
    ping = np.sin(2 * np.pi * f_ping * tt) * np.exp(-tt * 120)
    x = burst + 0.8 * ping
    return x / (np.max(np.abs(x)) + 1e-12)


tick = click(1700, 2600, 1250)
tock = click(1200, 1900, 880)

tk_L = np.zeros(M)
tk_R = np.zeros(M)
for b in range(BARS + 2):
    for e8 in range(8):
        st = bar_t(b, e8 / 2)
        if e8 % 2 == 0:
            add_at(tk_L, tick, st, 0.85)
            add_at(tk_R, tick, st, 0.25)
        else:
            add_at(tk_L, tock, st, 0.25)
            add_at(tk_R, tock, st, 0.85)
# bone dry, constant gain — the one fixed point of the watch
commit(tk_L, tk_R, 0.155)
del tk_L, tk_R


# ---------------------------------------------------------------- bass

def bass_note(midi, dur_s):
    f = midi_to_hz(midi)
    n = int(dur_s * SR)
    tt = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(2 * np.pi * 2 * f * tt)
    x = np.tanh(1.6 * x)
    env = (1 - np.exp(-tt / 0.005)) * np.clip((dur_s - tt) / 0.05, 0, 1)
    return x * env / (np.max(np.abs(x)) + 1e-12)


STEP = BEAT / 4
# sparse syncopated 16th accents — present, but never busy
BASS_PAT = {0: 1.0, 3: 0.55, 6: 0.75, 10: 0.6, 12: 0.85}
nb = bass_note(38, STEP * 1.5)          # D2
nb_c = bass_note(36, STEP * 1.5)        # C2
nb_eb = bass_note(39, STEP * 1.5)       # Eb2
bs_wander = slow_noise(0.03, 0.86, 1.0) # +/- 8 % drift, never a ramp

ba_L = np.zeros(M)
ba_R = np.zeros(M)
for b in range(BARS + 2):
    cadence = (b % 4 == 3)              # C2–Eb2–(D2 on next downbeat)
    for s16, g in BASS_PAT.items():
        note = nb
        if cadence and s16 == 10:
            note = nb_c
        elif cadence and s16 == 12:
            note = nb_eb
        st = bar_t(b, s16 / 4)
        w = g * bs_wander[min(M - 1, int(st * SR))]
        add_at(ba_L, note, st, w)
        add_at(ba_R, note, st, w)
commit(ba_L, ba_R, 0.22)
del ba_L, ba_R


# ---------------------------------------------------------------- strings

# the minor second held under everything: A3 + D4 + Eb4, tremolo touching
# true silence every cycle (anti-tinnitus), gain WANDERING 0.25-1.0
st_L = np.zeros(M)
st_R = np.zeros(M)
for midi, g_note in [(57, 0.8), (62, 1.0), (63, 0.9)]:
    f = midi_to_hz(midi)
    for det in (-0.0045, 0.0, 0.0045):
        ph = rng.uniform(0, 2 * np.pi)
        saw = sum(np.sin(2 * np.pi * f * (1 + det) * k * t + ph * k) / k
                  for k in range(1, 7))
        st_L += g_note * saw
        st_R += g_note * np.roll(saw, int(0.011 * SR))   # 11 ms Haas width
        del saw
sos_st = signal.butter(2, [180, 2600], "bandpass", fs=SR, output="sos")
st_L = signal.sosfilt(sos_st, st_L)
st_R = signal.sosfilt(sos_st, st_R)
trem_L = (0.5 + 0.5 * np.sin(2 * np.pi * 10.4 * t)) ** 1.2
trem_R = (0.5 + 0.5 * np.sin(2 * np.pi * 10.9 * t + 1.3)) ** 1.2
st_drift = slow_noise(0.02, 0.25, 1.0) ** 1.3            # wander, not ramp
st_L *= trem_L * st_drift
st_R *= trem_R * st_drift
commit(st_L, st_R, 0.095)
del st_L, st_R, trem_L, trem_R


# ---------------------------------------------------------------- breath

# the stillsuit recycles your breath: one cycle per bar (~26/min — a touch
# fast, because you are watching the ridge line). Inhale bright through
# the nose filters, exhale darker. Close, dry, centered: inside the hood.
raw = rng.standard_normal(M)
sos_in = signal.butter(2, [500, 1600], "bandpass", fs=SR, output="sos")
sos_ex = signal.butter(2, [250, 900], "bandpass", fs=SR, output="sos")
br_in = signal.sosfilt(sos_in, raw)
br_ex = signal.sosfilt(sos_ex, raw)
del raw
ph = np.mod(t, BAR)
inh = np.exp(-((ph - 0.55) / 0.30) ** 2)                 # beats 1-2
exh = np.exp(-((ph - 1.80) / 0.42) ** 2)                 # beats 3-4
br_wander = slow_noise(0.04, 0.6, 1.0)
breath = (0.9 * br_in * inh + br_ex * exh) * br_wander
commit(breath, breath, 0.065)
del br_in, br_ex, breath


# ---------------------------------------------------------------- the Eb

# twice, a lone Eb4 hangs over the watch and fades without resolving
EB_BARS = [20, 46]
eb_L = np.zeros(M)
eb_R = np.zeros(M)
for k, qb in enumerate(EB_BARS):
    dur = 2 * BAR
    n = int(dur * SR)
    tt = np.arange(n) / SR
    f = midi_to_hz(63)
    vib = 1.0 + 0.005 * np.sin(2 * np.pi * 4.8 * tt) * np.clip(tt / 1.0, 0, 1)
    phase = 2 * np.pi * np.cumsum(f * vib * np.ones(n)) / SR
    env = np.sin(np.pi * np.clip(tt / dur, 0, 1)) ** 1.8  # swells, fades, gone
    voice = env * (np.sin(phase) + 0.35 * np.sin(2 * phase) +
                   0.12 * np.sin(3 * phase))
    sos_v = signal.butter(2, 2000, "low", fs=SR, output="sos")
    voice = signal.sosfilt(sos_v, voice)
    p = 0.35 if k % 2 == 0 else 0.65                      # alternate sides
    add_at(eb_L, voice, bar_t(qb), np.cos(p * np.pi / 2))
    add_at(eb_R, voice, bar_t(qb), np.sin(p * np.pi / 2))
eb_L = reverb(eb_L, IR_L, wet=0.8)
eb_R = reverb(eb_R, IR_R, wet=0.8)
commit(eb_L, eb_R, 0.07)
del eb_L, eb_R


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
OUT = os.path.join(OUT_DIR, "stillsuit.wav")
with wave.open(OUT, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())

print(f"Created: {os.path.abspath(OUT)}")
print(f"Duration: {N / SR:.1f} s ({BARS} bars at {BPM:.0f} BPM)  |  "
      f"seamless loop (fold {XF:.2f} s = 2 bars)  |  {N_LAYERS} layers")
print(f"Unresolved Eb at: "
      f"{', '.join(f'{bar_t(qb):.0f}s' for qb in EB_BARS)}")
print(f"Breath rate: {60.0 / BAR:.0f}/min  |  cadence walk every 4th bar  |  "
      f"no builds, no fills, no resolution")
