#!/usr/bin/env python3
"""
generate_spice_must_flow.py — The Spice Must Flow: the economy/harvesting
state loop for the Dune RTS. "Everything is fine, build your base."

Mid-energy, between the ambient loop and the battle tracks: a harvester
works the open sand. 64 BPM half-time feel, 72 bars = exactly 4:30,
SEAMLESS LOOP (the v3 fold: 2 extra bars rendered and equal-power-folded
into the head, so the seam lands on the beat grid and groove phase matches
across the wrap).

Palette:
  * Machine pulse        — two detuned band-limited squares on D2 beating
                           against each other, amplitude-gated into a chug
                           (idle floor 0.18 — the engine never fully stops),
                           tanh-warmed, with a slow "load" wander.
  * Harvester footfalls  — soft thumps (80→45 Hz, 20 ms attack) on beats
                           1 & 3; piston clanks answering on the off-8ths.
  * Hammered santur      — struck Karplus-Strong, two strings per course
                           at ±0.15 %, playing a hypnotic 8th-note ostinato
                           that alternates every 8 bars and swells on a
                           24-bar wave.
  * Duduk fragments      — two short quotes of Theme A (night_pursuit),
                           an octave up, kilometres wet: the same world.
  * Cargo thopter        — one friendly flyby: descending detuned cluster
                           with wing-flutter AM slowing 23→13 Hz, L→R.
  * THE HARVESTER LISTENS— twice, a worm rumble rolls through and every
                           human-made layer cuts within half a second,
                           holds silent for two bars (only wind, drone and
                           the rumble), then spins back up. Spice paranoia
                           as arrangement.
  * Spice sparkle        — rare high pings (D/F#/A, 7th octave) glittering
                           in the air over the machine; discrete events,
                           anti-tinnitus safe.

Output: /workspace/music/spice_must_flow.wav (stereo, 44100 Hz, 16-bit).
"""

import os
import wave
import numpy as np
from scipy import signal

SR = 44100
BPM = 64.0
BEAT = 60.0 / BPM            # 0.9375 s
BAR = 4 * BEAT               # 3.75 s
BARS = 72
DURATION = BARS * BAR        # 270.0 s = 4:30
XF = 2 * BAR                 # loop crossfade: 2 bars, on the grid
DUR_TOTAL = DURATION + XF
N = int(SR * DURATION)
M = int(SR * DUR_TOTAL)
t = np.arange(M) / SR

rng = np.random.default_rng(1969)   # Dune Messiah publication year


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


IR_L = make_reverb_ir(4.5, 1.5, 7)
IR_R = make_reverb_ir(4.5, 1.5, 11)

mix_L = np.zeros(M)
mix_R = np.zeros(M)
N_LAYERS = 0


def commit(layer_L, layer_R, weight):
    global N_LAYERS
    peak = max(np.max(np.abs(layer_L)), np.max(np.abs(layer_R))) + 1e-12
    mix_L[:] += layer_L * (weight / peak)
    mix_R[:] += layer_R * (weight / peak)
    N_LAYERS += 1


# ------------------------------------------------- the harvester listens

# Twice, a worm rumble rolls through: every human layer (machine, clanks,
# thumps, santur) cuts within ~0.5 s, stays silent two bars, then recovers.
PAUSE_BARS = [24, 56]
listen = np.ones(M)
for pb in PAUSE_BARS:
    tp = bar_t(pb)
    c0 = int((tp + 0.50) * SR)          # the operator hears it...
    c1 = int((tp + 0.85) * SR)          # ...and kills the engine
    r0 = int((tp + 2 * BAR) * SR)       # two bars of held breath
    r1 = int((tp + 2 * BAR + 1.8) * SR) # spin back up
    listen[c0:c1] *= np.linspace(1.0, 0.0, c1 - c0)
    listen[c1:r0] = 0.0
    listen[r0:r1] = 0.5 - 0.5 * np.cos(np.pi * np.arange(r1 - r0) / (r1 - r0))


# ---------------------------------------------------------------- wind

raw = rng.standard_normal(M)
sos_whoosh = signal.butter(4, [120, 900], "bandpass", fs=SR, output="sos")
whoosh = signal.sosfilt(sos_whoosh, raw)
whoosh /= np.max(np.abs(whoosh))
sos_hiss = signal.butter(4, [2000, 7000], "bandpass", fs=SR, output="sos")
hiss = signal.sosfilt(sos_hiss, raw)
hiss /= np.max(np.abs(hiss))
del raw

gust = slow_noise(0.22) ** 2.2
gust2 = slow_noise(0.07) ** 1.5
wind_env = 0.25 + 0.75 * (0.6 * gust + 0.4 * gust2)
pan = slow_noise(0.05, 0.3, 0.7)
wind_L = wind_env * (whoosh * np.cos(pan * np.pi / 2) +
                     0.30 * hiss * gust * np.cos((1 - pan) * np.pi / 2))
wind_R = wind_env * (whoosh * np.sin(pan * np.pi / 2) +
                     0.30 * hiss * gust * np.sin((1 - pan) * np.pi / 2))
commit(wind_L, wind_R, 0.16)            # lower than arrakis — work, not awe
del wind_L, wind_R, whoosh, hiss


# ---------------------------------------------------------------- drone

f_D1 = midi_to_hz(26)
breath = 0.7 + 0.3 * np.sin(2 * np.pi * 0.012 * t + 1.0)
drone = (np.sin(2 * np.pi * f_D1 * t) +
         0.55 * np.sin(2 * np.pi * f_D1 * 2 * t + 0.4) +
         0.30 * np.sin(2 * np.pi * f_D1 * 3 * t) +
         0.30 * np.sin(2 * np.pi * f_D1 * 3.003 * t))
drone *= breath
commit(drone, drone, 0.18)
del drone, breath


# ---------------------------------------------------------------- machine

# two detuned band-limited squares on D2, beating ~0.4 Hz against each other
f_D2 = midi_to_hz(38)
engine = np.zeros(M)
for det, g in [(1.0, 1.0), (1.006, 0.9)]:
    for k in (1, 3, 5, 7):              # odd harmonics to ~510 Hz
        engine += g / k * np.sin(2 * np.pi * f_D2 * det * k * t)
sos_eng = signal.butter(2, 420, "low", fs=SR, output="sos")
engine = signal.sosfilt(sos_eng, engine)
engine /= np.max(np.abs(engine))

# the chug: 8th-note gate with an idle floor — the engine never fully stops
CHUG = [1.0, 0.45, 0.72, 0.45, 0.88, 0.45, 0.72, 0.45]
gate = np.zeros(M)
n8 = int(BEAT / 2 * SR)
hit = (1 - np.exp(-np.arange(n8) / SR / 0.008)) * np.exp(-np.arange(n8) / SR * 6.0)
step = 0
pos = 0.0
while pos < DUR_TOTAL:
    i0 = int(pos * SR)
    end = min(M, i0 + n8)
    gate[i0:end] = np.maximum(gate[i0:end], CHUG[step % 8] * hit[: end - i0])
    step += 1
    pos += BEAT / 2
gate = 0.18 + 0.82 * gate
load = slow_noise(0.05, 0.78, 1.0)      # the harvester works harder, easier
machine = np.tanh(1.5 * engine * gate) * load * listen
commit(machine, machine, 0.30)
del engine, gate, machine, load

# piston clanks on the off-8ths of beats 2 & 4, off to the right
nck = int(0.09 * SR)
tt = np.arange(nck) / SR
sos_ck = signal.butter(2, [1200, 4200], "bandpass", fs=SR, output="sos")
clank = signal.sosfilt(sos_ck, rng.standard_normal(nck)) * np.exp(-tt * 60)
clank += 0.45 * np.sin(2 * np.pi * 810 * tt) * np.exp(-tt * 40)
clank /= np.max(np.abs(clank)) + 1e-12
ck_L = np.zeros(M)
ck_R = np.zeros(M)
for b in range(BARS + 2):
    for beat in (1.5, 3.5):
        add_at(ck_L, clank, bar_t(b, beat), 0.5)
        add_at(ck_R, clank, bar_t(b, beat), 0.9)
commit(ck_L * listen, ck_R * listen, 0.05)
del ck_L, ck_R

# soft footfall thumps on beats 1 & 3 — the press of something heavy
nth = int(0.40 * SR)
tt = np.arange(nth) / SR
f_curve = 45.0 + 35.0 * np.exp(-tt * 18.0)
thump = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
thump *= (1 - np.exp(-tt / 0.020)) * np.exp(-tt * 5.0)   # 20 ms soft attack
th_L = np.zeros(M)
th_R = np.zeros(M)
for b in range(BARS + 2):
    add_at(th_L, thump, bar_t(b, 0), 1.0)
    add_at(th_R, thump, bar_t(b, 0), 1.0)
    add_at(th_L, thump, bar_t(b, 2), 0.8)
    add_at(th_R, thump, bar_t(b, 2), 0.8)
commit(th_L * listen, th_R * listen, 0.14)
del th_L, th_R


# ---------------------------------------------------------------- santur

def santur_note(f, dur=2.0):
    """Struck Karplus-Strong: two strings per course at ±0.15 %."""
    n = int(dur * SR)
    out = np.zeros(n)
    for det, g in [(0.9985, 1.0), (1.0015, 0.85)]:
        period = max(2, int(round(SR / (f * det))))
        buf = rng.standard_normal(period)
        buf = np.convolve(buf, np.ones(2) / 2, mode="same")  # hammer, not pick
        nper = n // period + 1
        s = np.empty(nper * period)
        prev = buf
        for k in range(nper):
            s[k * period:(k + 1) * period] = prev
            prev = 0.997 * 0.5 * (prev + np.roll(prev, 1))
        out += g * s[:n]
    tt = np.arange(n) / SR
    out *= np.exp(-tt * 1.6) * np.clip((dur - tt) / 0.1, 0, 1)
    return out / (np.max(np.abs(out)) + 1e-12)


# two hypnotic patterns (8ths), alternating every 8 bars
PAT1 = [62, 57, 66, 57, 63, 57, 62, 57]      # D4 A3 F#4 A3 Eb4 A3 D4 A3
PAT2 = [62, 57, 67, 57, 66, 57, 63, 57]      # ... reaching up to G4
VEL = [1.0, 0.45, 0.75, 0.45, 0.9, 0.45, 0.75, 0.45]
cache = {m: santur_note(midi_to_hz(m)) for m in sorted(set(PAT1 + PAT2))}

sa_L = np.zeros(M)
sa_R = np.zeros(M)
for b in range(BARS + 2):
    patt = PAT1 if (b // 8) % 2 == 0 else PAT2
    wave_g = 0.70 + 0.30 * np.sin(2 * np.pi * b / 24 - np.pi / 2)  # 24-bar swell
    for s8 in range(8):
        note = cache[patt[s8]]
        g = VEL[s8] * wave_g * rng.uniform(0.92, 1.0)
        p = 0.40 + 0.12 * np.sin(2 * np.pi * s8 / 8)               # gentle weave
        add_at(sa_L, note, bar_t(b, s8 / 2), g * np.cos(p * np.pi / 2))
        add_at(sa_R, note, bar_t(b, s8 / 2), g * np.sin(p * np.pi / 2))
sa_L = reverb(sa_L * listen, IR_L, wet=0.35)
sa_R = reverb(sa_R * listen, IR_R, wet=0.35)
commit(sa_L, sa_R, 0.17)
del sa_L, sa_R


# ---------------------------------------------------------------- duduk

# two fragments of Theme A (night_pursuit), an octave up, kilometres away
FRAG_A = [(62, 0.0, 1), (66, 1.0, 0.5), (63, 1.5, 0.5), (62, 2.0, 1),
          (60, 3.0, 1), (62, 4.0, 2)]
FRAG_B = [(67, 0.0, 1), (66, 1.0, 0.5), (63, 1.5, 0.5), (62, 2.0, 2),
          (60, 4.0, 1), (63, 5.0, 1), (62, 6.0, 2)]
DUDUK_EVENTS = [(16, FRAG_A), (44, FRAG_B)]

du_L = np.zeros(M)
du_R = np.zeros(M)
for db, frag in DUDUK_EVENTS:
    total = max(beat + dur for _, beat, dur in frag) * BEAT + 2.0
    n = int(total * SR)
    tt = np.arange(n) / SR
    f_target = np.full(n, midi_to_hz(frag[0][0]))
    for m, beat, dur in frag:
        f_target[int(beat * BEAT * SR):] = midi_to_hz(m)
    alpha = 1.0 - np.exp(-1.0 / (0.09 * SR))
    f_curve = signal.lfilter([alpha], [1.0, -(1.0 - alpha)], f_target,
                             zi=[f_target[0] * (1 - alpha)])[0]
    vib = 1.0 + 0.006 * np.sin(2 * np.pi * 5.2 * tt) * np.clip(tt / 1.2, 0, 1)
    phase = 2 * np.pi * np.cumsum(f_curve * vib) / SR
    env = np.minimum(np.clip(tt / 1.2, 0, 1),
                     np.clip((total - tt) / 2.0, 0, 1)) ** 1.5
    voice = env * (np.sin(phase) + 0.40 * np.sin(2 * phase) +
                   0.18 * np.sin(3 * phase) + 0.07 * np.sin(4 * phase))
    sos_v = signal.butter(2, 2200, "low", fs=SR, output="sos")
    voice = signal.sosfilt(sos_v, voice)
    p = rng.uniform(0.35, 0.65)
    add_at(du_L, voice, bar_t(db), np.cos(p * np.pi / 2))
    add_at(du_R, voice, bar_t(db), np.sin(p * np.pi / 2))
du_L = reverb(du_L, IR_L, wet=0.8)
du_R = reverb(du_R, IR_R, wet=0.8)
commit(du_L, du_R, 0.10)
del du_L, du_R


# ---------------------------------------------------------------- thopter

# one friendly cargo flyby: descending cluster, wing-flutter AM slowing
# 23 -> 13 Hz as it passes, sweeping left to right
FLYBY_BAR = 36
fd = 6.0
n = int(fd * SR)
tt = np.arange(n) / SR
f0 = 300.0 * (170.0 / 300.0) ** (tt / fd)
flut_rate = 13.0 + 10.0 * (1 - tt / fd)
flut = 0.55 + 0.45 * np.sin(2 * np.pi * np.cumsum(flut_rate) / SR)
body = np.zeros(n)
for det, g in [(0.985, 0.5), (0.995, 0.8), (1.0, 1.0), (1.008, 0.8), (1.017, 0.5)]:
    body += g * np.sin(2 * np.pi * np.cumsum(f0 * det) / SR)
sos_fb = signal.butter(2, 1500, "low", fs=SR, output="sos")
body = signal.sosfilt(sos_fb, body) * flut * np.sin(np.pi * tt / fd) ** 1.4
body /= np.max(np.abs(body)) + 1e-12
u = tt / fd
fb_L = np.zeros(M)
fb_R = np.zeros(M)
add_at(fb_L, body * np.cos(u * np.pi / 2), bar_t(FLYBY_BAR))
add_at(fb_R, body * np.sin(u * np.pi / 2), bar_t(FLYBY_BAR))
fb_L = reverb(fb_L, IR_L, wet=0.5)
fb_R = reverb(fb_R, IR_R, wet=0.5)
commit(fb_L, fb_R, 0.06)
del fb_L, fb_R


# ---------------------------------------------------------------- rumbles

# the two worm passes that stop the work (placed at the pause bars)
ru_L = np.zeros(M)
ru_R = np.zeros(M)
sos_gr = signal.butter(4, 90, "low", fs=SR, output="sos")
for pb in PAUSE_BARS:
    dur = 7.0
    n = int(dur * SR)
    tt = np.arange(n) / SR
    f_curve = 27.0 + 28.0 * np.exp(-tt * 2.2)
    phase = 2 * np.pi * np.cumsum(f_curve) / SR
    env = np.exp(-tt * 0.9) * (1 - np.exp(-tt * 30))
    thump_w = env * np.sin(phase)
    shake = signal.sosfilt(sos_gr, rng.standard_normal(n)) * env * 0.6
    add_at(ru_L, thump_w + shake, bar_t(pb), 1.0)
    add_at(ru_R, thump_w + shake, bar_t(pb), 1.0)
commit(ru_L, ru_R, 0.24)
del ru_L, ru_R


# ---------------------------------------------------------------- sparkle

# spice in the air: rare high pings on the 16th grid, in-key (D/F#/A)
sp_L = np.zeros(M)
sp_R = np.zeros(M)
n_sparkles = 0
nsp = int(0.35 * SR)
tt = np.arange(nsp) / SR
for b in range(BARS + 2):
    for s16 in range(16):
        if rng.random() < 0.045:
            f = float(rng.choice([2349.3, 2960.0, 3520.0]))
            ping = np.sin(2 * np.pi * f * tt) * (1 - np.exp(-tt / 0.002)) * np.exp(-tt * 14)
            p = rng.uniform(0.2, 0.8)
            add_at(sp_L, ping, bar_t(b, s16 / 4), np.cos(p * np.pi / 2))
            add_at(sp_R, ping, bar_t(b, s16 / 4), np.sin(p * np.pi / 2))
            n_sparkles += 1
sp_L = reverb(sp_L, IR_L, wet=0.6)
sp_R = reverb(sp_R, IR_R, wet=0.6)
commit(sp_L, sp_R, 0.022)
del sp_L, sp_R


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
OUT = os.path.join(OUT_DIR, "spice_must_flow.wav")
with wave.open(OUT, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())

print(f"Created: {os.path.abspath(OUT)}")
print(f"Duration: {N / SR:.1f} s ({BARS} bars at {BPM:.0f} BPM)  |  "
      f"seamless loop (fold {XF:.2f} s = 2 bars)  |  {N_LAYERS} layers")
print(f"Harvester listens (worm pause): "
      f"{', '.join(f'{bar_t(pb):.0f}s' for pb in PAUSE_BARS)}")
print(f"Duduk Theme A fragments: "
      f"{', '.join(f'{bar_t(db):.0f}s' for db, _ in DUDUK_EVENTS)}")
print(f"Cargo thopter flyby: {bar_t(FLYBY_BAR):.0f}s  |  "
      f"spice sparkles: {n_sparkles}")
