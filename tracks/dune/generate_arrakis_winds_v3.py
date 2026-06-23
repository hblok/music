#!/usr/bin/env python3
"""
generate_arrakis_winds_v3.py — Arrakis Winds v3: the deep-desert ambience,
rebuilt with everything learned since v1/v2, as a SEAMLESS LOOP for use as
the background track of the Dune RTS remake.

Design (user brief): quiet, no beats, no psy — background ambience with
subtle small interest along the way. 6 minutes, loops perfectly.

Palette (three families of "interest", all distant and rare):
  * Pure desert nature   — gusting wind (whoosh + sand hiss), D1 planetary
                           drone with a breathing Eb shadow-partial, worm
                           rumbles felt more than heard, granular sand
                           crackle, a brief silent-pulsing starfield.
  * Distant human traces — duduk-like calls kilometres away (75 % wet),
                           a lone baliset (Karplus-Strong pluck) phrase
                           drifting from some sietch, one far-off throat
                           chant.
  * Hints of menace      — a single war horn on the horizon, and one
                           "machinery tremor": sub pulses spaced a little
                           too regularly to be natural.

Seamless loop technique: render DURATION + XF seconds; the final XF seconds
are equal-power crossfaded INTO the first XF seconds (y[0] starts exactly at
x[N], where the last output sample x[N-1] left off). Event tails that spill
past the loop boundary are folded into the head, so rumble/reverb tails
survive the wrap. No fade-in/fade-out. Discrete events are scheduled in
[XF+10, DURATION-12] so none straddles the fold awkwardly.

Output: /workspace/music/arrakis_winds_v3.wav (stereo, 44100 Hz, 16-bit).
"""

import os
import wave
import numpy as np
from scipy import signal

SR = 44100
DURATION = 360.0             # 6 minutes of loop
XF = 10.0                    # loop crossfade length
DUR_TOTAL = DURATION + XF
N = int(SR * DURATION)
M = int(SR * DUR_TOTAL)
t = np.arange(M) / SR

rng = np.random.default_rng(1984)   # the year of the first Dune film


# ---------------------------------------------------------------- helpers

def midi_to_hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def slow_noise(rate_hz, lo=0.0, hi=1.0):
    """Smooth random control signal: sparse normals interpolated to SR."""
    k = max(4, int(DUR_TOTAL * rate_hz))
    pts = rng.standard_normal(k)
    pts = np.convolve(pts, np.ones(3) / 3, mode="same")
    ctrl = np.interp(t, np.linspace(0, DUR_TOTAL, k), pts)
    ctrl = (ctrl - ctrl.min()) / (ctrl.max() - ctrl.min() + 1e-12)
    return lo + (hi - lo) * ctrl


def make_reverb_ir(seconds, decay, seed):
    """Exponentially decaying noise burst — convolution reverb IR."""
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


IR_L = make_reverb_ir(5.0, 1.6, 7)
IR_R = make_reverb_ir(5.0, 1.6, 11)

# mix bus — layers are committed (peak-normalized, weighted) and freed
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

sos_hiss = signal.butter(4, [2000, 7000], "bandpass", fs=SR, output="sos")
hiss = signal.sosfilt(sos_hiss, raw)
hiss /= np.max(np.abs(hiss))
del raw

# gusts + a slower weather front; squared so the lulls are really quiet
gust = slow_noise(0.22) ** 2.2
gust2 = slow_noise(0.07) ** 1.5
wind_env = 0.25 + 0.75 * (0.6 * gust + 0.4 * gust2)

pan = slow_noise(0.05, 0.25, 0.75)
wind_L = wind_env * (whoosh * np.cos(pan * np.pi / 2) +
                     0.30 * hiss * gust * np.cos((1 - pan) * np.pi / 2))
wind_R = wind_env * (whoosh * np.sin(pan * np.pi / 2) +
                     0.30 * hiss * gust * np.sin((1 - pan) * np.pi / 2))
commit(wind_L, wind_R, 0.32)
del wind_L, wind_R, whoosh

# granular sand crackle — only crackles when the wind blows
sos_sand = signal.butter(4, 6000, "high", fs=SR, output="sos")
grains = signal.sosfilt(sos_sand, rng.standard_normal(M))
grains /= np.max(np.abs(grains))
spikes = np.clip(slow_noise(3.0), 0, 1) ** 10
sand = grains * spikes * wind_env
commit(sand, sand, 0.045)
del grains, spikes, sand, hiss


# ---------------------------------------------------------------- drone

f_D1 = midi_to_hz(26)        # D1 ≈ 36.7 Hz
breath = 0.7 + 0.3 * np.sin(2 * np.pi * 0.012 * t + 1.0)
drone = (np.sin(2 * np.pi * f_D1 * t) +
         0.55 * np.sin(2 * np.pi * f_D1 * 2 * t + 0.4) +
         0.30 * np.sin(2 * np.pi * f_D1 * 3 * t) +          # fifth above octave
         0.30 * np.sin(2 * np.pi * f_D1 * 3.003 * t))       # slow beating
drone *= breath

# the Eb shadow: a flat-second partial (the Dune signature interval) that
# swells once mid-track — a cloud passing over the drone — then dissolves
f_Eb2 = f_D1 * 2 * 2 ** (1 / 12)
shadow_env = np.exp(-((t - 205.0) / 22.0) ** 2)             # ~40 s gaussian
drone += 0.34 * np.sin(2 * np.pi * f_Eb2 * t) * shadow_env

commit(drone, drone, 0.26)
del drone, breath


# ---------------------------------------------------------------- worm rumbles

rumble_L = np.zeros(M)
rumble_R = np.zeros(M)

thump_times = []
cursor = 35.0
while cursor < DURATION - 15.0:
    thump_times.append(cursor)
    cursor += rng.uniform(48.0, 75.0)

sos_gr = signal.butter(4, 90, "low", fs=SR, output="sos")
for tc in thump_times:
    dur = 6.0
    n = int(dur * SR)
    tt = np.arange(n) / SR
    # pitch falls 55 -> 27 Hz: something enormous moving under the sand
    f_curve = 27.0 + 28.0 * np.exp(-tt * 2.2)
    phase = 2 * np.pi * np.cumsum(f_curve) / SR
    env = np.exp(-tt * 1.1) * (1 - np.exp(-tt * 30))
    thump = env * np.sin(phase)
    shake = signal.sosfilt(sos_gr, rng.standard_normal(n)) * env * 0.6
    g = rng.uniform(0.7, 1.0)
    add_at(rumble_L, thump + shake, tc, g)
    add_at(rumble_R, thump + shake, tc, g)

commit(rumble_L, rumble_R, 0.28)
del rumble_L, rumble_R


# ---------------------------------------------------------------- distant calls

# D Phrygian dominant: D Eb F# G A Bb C — the desert mode
SCALE = [62, 63, 66, 67, 69, 70, 72]

call_L = np.zeros(M)
call_R = np.zeros(M)
call_times = []

phrase_start = 55.0
while phrase_start < DURATION - 30.0:
    call_times.append(phrase_start)
    n_notes = int(rng.integers(3, 6))
    idx = sorted(rng.choice(len(SCALE), size=n_notes, replace=True))[::-1]
    idx[-1] = int(rng.choice([0, 4]))           # end on root or fifth
    durs = rng.uniform(1.6, 3.4, size=n_notes)
    total = float(np.sum(durs)) + 2.0
    n = int(total * SR)
    tt = np.arange(n) / SR

    f_target = np.zeros(n)
    edges = np.concatenate([[0.0], np.cumsum(durs)])
    for k in range(n_notes):
        a, b = int(edges[k] * SR), min(n, int(edges[k + 1] * SR))
        f_target[a:b] = midi_to_hz(SCALE[idx[k]])
    f_target[int(edges[-1] * SR):] = f_target[int(edges[-1] * SR) - 1]
    alpha = 1.0 - np.exp(-1.0 / (0.09 * SR))    # ~90 ms portamento
    f_curve = signal.lfilter([alpha], [1.0, -(1.0 - alpha)], f_target,
                             zi=[f_target[0] * (1 - alpha)])[0]

    vib = 1.0 + 0.006 * np.sin(2 * np.pi * 5.2 * tt) * np.clip(tt / 1.2, 0, 1)
    phase = 2 * np.pi * np.cumsum(f_curve * vib) / SR
    env = np.minimum(np.clip(tt / 1.5, 0, 1),
                     np.clip((total - tt) / 2.0, 0, 1)) ** 1.5
    voice = env * (np.sin(phase) + 0.40 * np.sin(2 * phase) +
                   0.18 * np.sin(3 * phase) + 0.07 * np.sin(4 * phase))
    sos_v = signal.butter(2, 2200, "low", fs=SR, output="sos")
    voice = signal.sosfilt(sos_v, voice)

    p = rng.uniform(0.3, 0.7)
    add_at(call_L, voice, phrase_start, np.cos(p * np.pi / 2))
    add_at(call_R, voice, phrase_start, np.sin(p * np.pi / 2))
    phrase_start += total + rng.uniform(75.0, 105.0)

call_L = reverb(call_L, IR_L, wet=0.75)
call_R = reverb(call_R, IR_R, wet=0.75)
commit(call_L, call_R, 0.20)
del call_L, call_R


# ---------------------------------------------------------------- baliset

def ks_pluck(f, dur, damp=0.9925):
    """Karplus-Strong pluck, double-course (a second string at f*1.004)."""
    out = np.zeros(int(dur * SR))
    for fk, gk in [(f, 1.0), (f * 1.004, 0.6)]:
        period = max(2, int(round(SR / fk)))
        nper = len(out) // period + 1
        buf = rng.standard_normal(period)
        buf = np.convolve(buf, np.ones(5) / 5, mode="same")   # warm pick
        s = np.empty(nper * period)
        prev = buf
        for k in range(nper):
            s[k * period:(k + 1) * period] = prev
            prev = damp * 0.5 * (prev + np.roll(prev, 1))
        out += gk * s[: len(out)]
    env = np.clip((dur - np.arange(len(out)) / SR) / 0.4, 0, 1)
    return out * env / (np.max(np.abs(out)) + 1e-12)


bal_L = np.zeros(M)
bal_R = np.zeros(M)
# two phrases, far apart: a sietch musician somewhere beyond the dunes.
# Descending lines in D Phrygian dominant, ending on the root.
BAL_PHRASES = [
    (128.0, [69, 67, 66, 62]),          # A3 G3 F#3 D3
    (312.0, [70, 69, 66, 63, 62]),      # Bb3 A3 F#3 Eb3 D3
]
for start, notes in BAL_PHRASES:
    cur = start
    for i, m in enumerate(notes):
        dur = 3.2 if i == len(notes) - 1 else 2.4
        pl = ks_pluck(midi_to_hz(m - 12), dur)   # an octave down: D2 register
        g = rng.uniform(0.8, 1.0)
        add_at(bal_L, pl, cur, g * 0.62)
        add_at(bal_R, pl, cur, g * 0.78)
        cur += rng.uniform(1.1, 1.5)
bal_L = reverb(bal_L, IR_L, wet=0.7)
bal_R = reverb(bal_R, IR_R, wet=0.7)
commit(bal_L, bal_R, 0.085)
del bal_L, bal_R


# ---------------------------------------------------------------- chant

# one far-off throat chant: glottal harmonics through dark "oh" formants,
# a single long syllable swelling out of the wind and back into it
CHANT_T = 232.0
ch_dur = 14.0
n = int(ch_dur * SR)
tt = np.arange(n) / SR
f0 = midi_to_hz(38)                      # D2
vib = 1.0 + 0.004 * np.sin(2 * np.pi * 4.6 * tt)
phase = 2 * np.pi * np.cumsum(f0 * vib * np.ones(n)) / SR
glottal = sum(np.sin((k + 1) * phase) / (k + 1) ** 0.8 for k in range(14))
formant = np.zeros(n)
for lohi, g in [((380, 560), 1.0), ((750, 1000), 0.6), ((2200, 2700), 0.15)]:
    sos_f = signal.butter(2, lohi, "bandpass", fs=SR, output="sos")
    formant += g * signal.sosfilt(sos_f, glottal)
formant += 0.4 * np.sin(phase / 2)       # sub-octave throat weight
env = np.sin(np.pi * np.clip(tt / ch_dur, 0, 1)) ** 1.6      # swell in & out
chant = formant * env
chant /= np.max(np.abs(chant)) + 1e-12
ch_L = np.zeros(M)
ch_R = np.zeros(M)
add_at(ch_L, chant, CHANT_T, 0.9)
add_at(ch_R, chant, CHANT_T, 0.7)
ch_L = reverb(ch_L, IR_L, wet=0.85)
ch_R = reverb(ch_R, IR_R, wet=0.85)
commit(ch_L, ch_R, 0.075)
del ch_L, ch_R, glottal, formant, chant


# ---------------------------------------------------------------- menace

# 1) a single war horn on the horizon — the carnyx recipe, drowned in
#    distance (heavy lowpass + 85 % wet) and very quiet
HORN_T = 268.0
h_dur = 5.0
n = int(h_dur * SR)
tt = np.arange(n) / SR
fh = midi_to_hz(45)                      # A2 — the open fifth, a signal call
scoop = fh * (0.94 + 0.06 * np.clip(tt / 0.15, 0, 1))
phase = 2 * np.pi * np.cumsum(scoop) / SR
horn = sum(np.sin((k + 1) * phase) / (k + 1) ** 0.7 for k in range(12))
horn *= 1.0 + 0.20 * np.sin(2 * np.pi * 31.0 * tt)           # growl AM
sos_fm = signal.butter(2, [450, 900], "bandpass", fs=SR, output="sos")
horn += 0.6 * signal.sosfilt(sos_fm, horn)
sos_far = signal.butter(2, 1100, "low", fs=SR, output="sos")  # distance
horn = signal.sosfilt(sos_far, horn)
env = np.minimum(np.clip(tt / 0.8, 0, 1), np.clip((h_dur - tt) / 2.5, 0, 1))
horn *= env
horn /= np.max(np.abs(horn)) + 1e-12
hn_L = np.zeros(M)
hn_R = np.zeros(M)
add_at(hn_L, horn, HORN_T, 0.55)
add_at(hn_R, horn, HORN_T, 0.95)         # off to the east
hn_L = reverb(hn_L, IR_L, wet=0.85)
hn_R = reverb(hn_R, IR_R, wet=0.85)
commit(hn_L, hn_R, 0.07)
del hn_L, hn_R, horn

# 2) machinery tremor: eight sub pulses spaced EXACTLY 0.9 s apart — too
#    regular to be a worm. Harvester? Thumper? Something is out there.
TREMOR_T = 86.0
tm_L = np.zeros(M)
tm_R = np.zeros(M)
n = int(0.5 * SR)
tt = np.arange(n) / SR
pulse = np.sin(2 * np.pi * 45.0 * tt) * (1 - np.exp(-tt / 0.02)) * np.exp(-tt * 6.0)
sos_tm = signal.butter(2, 120, "low", fs=SR, output="sos")
knock = signal.sosfilt(sos_tm, rng.standard_normal(n)) * np.exp(-tt * 14.0)
pulse = pulse + 0.4 * knock / (np.max(np.abs(knock)) + 1e-12)
for k in range(8):
    g = 0.5 + 0.5 * np.sin(np.pi * (k + 0.5) / 8)            # swell across the 8
    add_at(tm_L, pulse, TREMOR_T + 0.9 * k, g * 0.9)
    add_at(tm_R, pulse, TREMOR_T + 0.9 * k, g * 0.55)        # off to the west
commit(tm_L, tm_R, 0.16)
del tm_L, tm_R


# ---------------------------------------------------------------- starfield

# faint inharmonic partials pulsing to TRUE silence (anti-tinnitus rule),
# present only in two ~40 s night windows so they never overstay
stars = np.zeros(M)
for f, rate in [(1244.5, 0.021), (1864.7, 0.013), (2793.8, 0.017)]:
    pulse = np.clip(np.sin(2 * np.pi * rate * t), 0, 1) ** 2
    stars += np.sin(2 * np.pi * f * t) * pulse
win = (np.exp(-((t - 45.0) / 20.0) ** 2) +
       np.exp(-((t - 295.0) / 20.0) ** 2))
stars *= win
commit(stars, stars, 0.013)
del stars


# ---------------------------------------------------------------- loop fold

# equal-power crossfade of the final XF seconds into the first XF seconds:
# y[0] picks up exactly at x[N] (one sample after the loop's last sample),
# so end -> start is perfectly continuous and event/reverb tails that spill
# past the boundary land in the head of the next pass.
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
OUT = os.path.join(OUT_DIR, "arrakis_winds_v3.wav")
with wave.open(OUT, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())

print(f"Created: {os.path.abspath(OUT)}")
print(f"Duration: {N / SR:.1f} s  |  {SR} Hz stereo, 16-bit PCM  |  "
      f"seamless loop (fold {XF:.0f} s)  |  {N_LAYERS} layers")
print(f"Worm rumbles at:   {', '.join(f'{x:.0f}s' for x in thump_times)}")
print(f"Distant calls at:  {', '.join(f'{x:.0f}s' for x in call_times)}")
print(f"Baliset phrases:   {', '.join(f'{s:.0f}s' for s, _ in BAL_PHRASES)}")
print(f"Machinery tremor:  {TREMOR_T:.0f}s   |  Eb drone shadow: ~205s")
print(f"Throat chant:      {CHANT_T:.0f}s   |  War horn: {HORN_T:.0f}s")
