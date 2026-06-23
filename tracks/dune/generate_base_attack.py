#!/usr/bin/env python3
"""
generate_base_attack.py — sequel track to arrakis_winds_v2.wav: the calm
desert ambience is shattered by a sudden assault on the base.

Opens with the same palette as arrakis_winds_v2 (gusting wind, D1 drone)
so the two tracks crossfade cleanly. At 15 s a detonation hits and the
attack begins INSTANTLY — no gradual build:

  * A short, urgent two-tone klaxon announces the attack (fast 120 ms
    beeps, mostly dry — an alarm, not a horror cue), then stops.
  * Darbuka (doumbek) percussion at full 128 BPM from the first bar,
    playing a maqsum rhythm — doum, tek and ghost "ka" strokes, with a
    fill every fourth bar. A deep sub-kick doubles the doum for weight.
  * A plucked oud (Karplus-Strong, double-course detuned strings) drives
    an eighth-note riff in D Phrygian dominant.
  * Enemy flybys: detuned cluster swells sweeping across the field.
  * Explosions — deep and slow, soft 80 ms attacks, lowpassed below
    150 Hz with falling sub-sine cores. Frequent throughout the battle.
  * The final, biggest detonation at ~168 s kills the groove dead;
    wind and drone remain over the aftermath.

Output: /workspace/music/base_under_attack_v2.wav (stereo, 44100 Hz, 16-bit).
"""

import os
import wave
import numpy as np
from scipy import signal

SR = 44100
DURATION = 195.0
N = int(SR * DURATION)
t = np.arange(N) / SR

rng = np.random.default_rng(10191)   # the year the Atreides came to Arrakis

ATTACK = 15.0          # the assault begins — suddenly
BEAT_END = 168.0       # final detonation; groove dies here
BPM = 128.0
STEP = 60.0 / BPM / 4.0              # sixteenth note
BAR = STEP * 16


# ---------------------------------------------------------------- helpers

def midi_to_hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def fade(x, fade_in=10.0, fade_out=14.0):
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


def karplus_strong(freq, dur, damp=0.992, seed_noise=None):
    """Plucked string. Warmed initial buffer = soft pick, gut-string tone."""
    n = int(dur * SR)
    period = max(2, int(SR / freq))
    buf = (seed_noise if seed_noise is not None
           else rng.uniform(-1, 1, period))
    buf = np.convolve(buf, np.ones(3) / 3, mode="same")   # warm the pick
    out = np.empty(n)
    prev = buf.copy()
    i = 0
    while i < n:
        m = min(period, n - i)
        out[i:i + m] = prev[:m]
        prev = damp * 0.5 * (prev + np.roll(prev, 1))
        i += m
    return out


IR_L = make_reverb_ir(5.0, 1.6, 7)
IR_R = make_reverb_ir(5.0, 1.6, 11)


# ---------------------------------------------------------------- wind & drone
# Same recipe as arrakis_winds_v2 so the tracks blend.

raw = rng.standard_normal(N)
sos_whoosh = signal.butter(4, [120, 900], "bandpass", fs=SR, output="sos")
whoosh = signal.sosfilt(sos_whoosh, raw)
whoosh /= np.max(np.abs(whoosh))
sos_hiss = signal.butter(4, [2000, 7000], "bandpass", fs=SR, output="sos")
hiss = signal.sosfilt(sos_hiss, raw)
hiss /= np.max(np.abs(hiss))

gust = slow_noise(0.22) ** 2.2
gust2 = slow_noise(0.07) ** 1.5
wind_env = 0.25 + 0.75 * (0.6 * gust + 0.4 * gust2)
pan = slow_noise(0.05, 0.25, 0.75)
wind_L = wind_env * (whoosh * np.cos(pan * np.pi / 2) +
                     0.30 * hiss * gust * np.cos((1 - pan) * np.pi / 2))
wind_R = wind_env * (whoosh * np.sin(pan * np.pi / 2) +
                     0.30 * hiss * gust * np.sin((1 - pan) * np.pi / 2))

f_D1 = midi_to_hz(26)
breath = 0.7 + 0.3 * np.sin(2 * np.pi * 0.012 * t + 1.0)
drone = (np.sin(2 * np.pi * f_D1 * t) +
         0.55 * np.sin(2 * np.pi * f_D1 * 2 * t + 0.4) +
         0.30 * np.sin(2 * np.pi * f_D1 * 3 * t) +
         0.30 * np.sin(2 * np.pi * f_D1 * 3.003 * t))
drone *= breath
drone /= np.max(np.abs(drone))


# ---------------------------------------------------------------- klaxon
# Urgent and brief: fast alternating two-tone beeps, mostly dry. Fires at
# the attack onset and twice more early on, then never again.

klaxon_L = np.zeros(N)
klaxon_R = np.zeros(N)

nb = int(0.12 * SR)
tb = np.arange(nb) / SR
beep_env = np.minimum(np.clip(tb / 0.008, 0, 1), np.clip((0.12 - tb) / 0.02, 0, 1))
burst = np.zeros(int(1.6 * SR))
for k in range(6):
    f = 740.0 if k % 2 == 0 else 988.0       # F#5 / B5 — alert, not eerie
    beep = beep_env * (np.sin(2 * np.pi * f * tb) +
                       0.35 * np.sin(2 * np.pi * 2 * f * tb))
    i0 = int(k * 0.24 * SR)
    burst[i0:i0 + nb] += beep

for tc, g in [(ATTACK - 0.3, 1.0), (ATTACK + 7.5, 0.7), (ATTACK + 19.5, 0.45)]:
    add_at(klaxon_L, burst, tc, g * 0.8)
    add_at(klaxon_R, burst, tc, g)

klaxon_L = reverb(klaxon_L, IR_L, wet=0.25)   # a touch of hall, mostly dry
klaxon_R = reverb(klaxon_R, IR_R, wet=0.25)
peak = max(np.max(np.abs(klaxon_L)), np.max(np.abs(klaxon_R)), 1e-12)
klaxon_L /= peak
klaxon_R /= peak


# ---------------------------------------------------------------- darbuka
# Maqsum at full tempo from the very first bar — the attack is sudden.
#   doum: deep resonant center-stroke; tek: sharp rim slap; ka: ghost tek.

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


DOUM = make_doum()
TEK = make_tek()
KA = make_tek(ghost=True)

# maqsum in sixteenth steps: D . T . . . T . D . . . T . . .
PATTERN = {0: "D", 2: "T", 6: "T", 8: "D", 12: "T"}

drum_L = np.zeros(N)
drum_R = np.zeros(N)
sub_L = np.zeros(N)
sub_R = np.zeros(N)

# deep sub-kick under the doum for weight
nk = int(0.35 * SR)
tk = np.arange(nk) / SR
fk = 36.0 + 60.0 * np.exp(-tk * 16.0)
SUBKICK = np.sin(2 * np.pi * np.cumsum(fk) / SR) * \
    np.exp(-tk * 10.0) * (1 - np.exp(-tk * 400))

n_bars = int((BEAT_END - ATTACK) / BAR)
for bar_i in range(n_bars):
    bar_t = ATTACK + bar_i * BAR
    fill_bar = (bar_i % 4 == 3)
    for step_i in range(16):
        st = bar_t + step_i * STEP
        stroke = PATTERN.get(step_i)
        if fill_bar and step_i >= 10:
            # fill: driving teks into the next bar
            g = 0.45 + 0.55 * (step_i - 10) / 5.0
            add_at(drum_L, TEK, st, g * 0.9)
            add_at(drum_R, TEK, st, g * 0.7)
            continue
        if stroke == "D":
            add_at(drum_L, DOUM, st, 1.0)
            add_at(drum_R, DOUM, st, 1.0)
            add_at(sub_L, SUBKICK, st, 1.0)
            add_at(sub_R, SUBKICK, st, 1.0)
        elif stroke == "T":
            p = 0.35 if step_i in (2, 12) else 0.65   # teks answer L/R
            add_at(drum_L, TEK, st, np.cos(p * np.pi / 2))
            add_at(drum_R, TEK, st, np.sin(p * np.pi / 2))
        elif step_i % 2 == 1 and rng.random() < 0.30:
            add_at(drum_L, KA, st, 0.6)
            add_at(drum_R, KA, st, 0.5)

for buf in (drum_L, drum_R, sub_L, sub_R):
    buf /= np.max(np.abs(buf)) + 1e-12


# ---------------------------------------------------------------- oud riff
# Plucked double-course strings, eighth-note riff in D Phrygian dominant.
# Full presence from the first bar — no fade-in.

RIFF = [50, 50, 51, 50, 48, 50, 54, 51]   # D3 D3 Eb3 D3 C3 D3 F#3 Eb3

oud_L = np.zeros(N)
oud_R = np.zeros(N)

# pre-render one pluck per distinct pitch (double-course: detuned pair)
plucks = {}
for m in set(RIFF):
    f = midi_to_hz(m)
    p = karplus_strong(f, 0.55) + 0.6 * karplus_strong(f * 1.004, 0.55)
    plucks[m] = p / (np.max(np.abs(p)) + 1e-12)

for bar_i in range(n_bars):
    bar_t = ATTACK + bar_i * BAR
    for e in range(8):                       # eighth notes
        m = RIFF[e]
        # occasional octave jump keeps the riff alive
        if rng.random() < 0.10 and e in (2, 6):
            m += 12
            if m not in plucks:
                f = midi_to_hz(m)
                p = karplus_strong(f, 0.55) + 0.6 * karplus_strong(f * 1.004, 0.55)
                plucks[m] = p / (np.max(np.abs(p)) + 1e-12)
        g = 1.0 if e % 2 == 0 else 0.75
        st = bar_t + e * 2 * STEP
        add_at(oud_L, plucks[m], st, g * 0.95)
        add_at(oud_R, plucks[m], st, g * 0.8)

peak = max(np.max(np.abs(oud_L)), np.max(np.abs(oud_R)), 1e-12)
oud_L /= peak
oud_R /= peak


# ---------------------------------------------------------------- enemy swells

swell_L = np.zeros(N)
swell_R = np.zeros(N)
sos_sw = signal.butter(4, 1200, "low", fs=SR, output="sos")

cursor = ATTACK + 6.0
while cursor < BEAT_END - 12.0:
    dur = rng.uniform(7.0, 10.0)
    n = int(dur * SR)
    ts = np.arange(n) / SR
    f0 = midi_to_hz(int(rng.choice([38, 39, 43])))
    rise = f0 * (1.0 + 0.12 * ts / dur)
    cluster = np.zeros(n)
    for det in (0.994, 1.0, 1.007, 1.013):
        cluster += np.sin(2 * np.pi * np.cumsum(rise * det) / SR +
                          rng.uniform(0, 2 * np.pi))
    env = np.sin(np.pi * ts / dur) ** 2
    cluster = signal.sosfilt(sos_sw, cluster * env)
    direction = rng.choice([1, -1])
    pan_curve = 0.5 + 0.45 * direction * (2 * ts / dur - 1)
    i0 = int(cursor * SR)
    end = min(N, i0 + n)
    seg = end - i0
    swell_L[i0:end] += cluster[:seg] * np.cos(pan_curve[:seg] * np.pi / 2)
    swell_R[i0:end] += cluster[:seg] * np.sin(pan_curve[:seg] * np.pi / 2)
    cursor += dur + rng.uniform(8.0, 16.0)

peak = max(np.max(np.abs(swell_L)), np.max(np.abs(swell_R)), 1e-12)
swell_L /= peak
swell_R /= peak


# ---------------------------------------------------------------- explosions
# Deep and slow: soft 80 ms attacks, brown-noise booms lowpassed below
# 150 Hz, falling sub-sine cores. The FIRST one triggers the attack itself;
# they stay frequent through the whole battle.

boom_L = np.zeros(N)
boom_R = np.zeros(N)
sos_boom = signal.butter(4, 150, "low", fs=SR, output="sos")

expl_times = [ATTACK]                       # the strike that starts it all
cursor = ATTACK + rng.uniform(10.0, 16.0)
while cursor < BEAT_END - 6.0:
    expl_times.append(cursor)
    cursor += rng.uniform(10.0, 18.0)
expl_times.append(BEAT_END)                 # the final, biggest detonation

for ei, tc in enumerate(expl_times):
    dur = 7.0
    n = int(dur * SR)
    tb2 = np.arange(n) / SR
    big = 1.6 if ei in (0, len(expl_times) - 1) else rng.uniform(0.55, 1.0)
    brown = np.cumsum(rng.standard_normal(n))
    brown -= np.linspace(brown[0], brown[-1], n)
    brown /= np.max(np.abs(brown)) + 1e-12
    env = (1 - np.exp(-tb2 / 0.08)) * np.exp(-tb2 / 1.8)
    body = signal.sosfilt(sos_boom, brown * env)
    fsub = 22.0 + 38.0 * np.exp(-tb2 * 1.6)
    core = np.sin(2 * np.pi * np.cumsum(fsub) / SR) * env
    boom = body * 0.7 + core * 0.6
    p = rng.uniform(0.3, 0.7) if 0 < ei < len(expl_times) - 1 else 0.5
    add_at(boom_L, boom, tc, big * np.cos(p * np.pi / 2))
    add_at(boom_R, boom, tc, big * np.sin(p * np.pi / 2))

boom_L = reverb(boom_L, IR_L, wet=0.4)
boom_R = reverb(boom_R, IR_R, wet=0.4)
peak = max(np.max(np.abs(boom_L)), np.max(np.abs(boom_R)), 1e-12)
boom_L /= peak
boom_R /= peak


# ---------------------------------------------------------------- mix
# The calm layers duck HARD and instantly at the attack, then return
# for the aftermath after the last detonation.

battle = np.clip((t - ATTACK) / 1.5, 0, 1) * np.clip((BEAT_END + 5 - t) / 7.0, 0, 1)
battle = np.clip(battle, 0, 1)
calm = 1.0 - 0.40 * battle

L = (0.26 * wind_L * calm + 0.22 * drone * calm +
     0.30 * drum_L + 0.26 * sub_L + 0.22 * oud_L +
     0.07 * klaxon_L + 0.13 * swell_L + 0.42 * boom_L)
R = (0.26 * wind_R * calm + 0.22 * drone * calm +
     0.30 * drum_R + 0.26 * sub_R + 0.22 * oud_R +
     0.07 * klaxon_R + 0.13 * swell_R + 0.42 * boom_R)

fade(L, fade_in=8.0)
fade(R, fade_in=8.0)

peak = max(np.max(np.abs(L)), np.max(np.abs(R)))
L = L / peak * 0.88
R = R / peak * 0.88

stereo = np.empty((N, 2))
stereo[:, 0] = L
stereo[:, 1] = R
pcm = (stereo * 32767.0).astype(np.int16)

OUT_DIR = "/workspace/music"
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, "base_under_attack_v2.wav")
with wave.open(OUT, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())

print(f"Created: {os.path.abspath(OUT)}")
print(f"Duration: {N / SR:.1f} s  |  {SR} Hz stereo, 16-bit PCM")
print(f"Attack hits at {ATTACK:.0f} s — {BPM:.0f} BPM maqsum from the first bar, "
      f"{n_bars} bars until {BEAT_END:.0f} s")
print(f"Explosions at: {', '.join(f'{x:.0f}s' for x in expl_times)}")
