#!/usr/bin/env python3
"""
generate_arrakis.py — Dune-inspired generative ambient: deep desert, wind
over sand, the cold vastness of space behind it all.

Pure synthesis (numpy + scipy, no samples). Palette:
  * Gusting desert wind   — white noise through Butterworth band filters,
                            gain-modulated by slow stochastic gust envelopes,
                            drifting across the stereo field.
  * Deep planetary drone  — D1/D2 + open fifth, slow beating overtones.
  * Shai-Hulud rumbles    — occasional sub-bass thumps with falling pitch
                            and a rumble tail, felt more than heard.
  * Distant calls         — duduk-like voice in D Phrygian dominant with
                            portamento and vibrato, drowned in convolution
                            reverb so it sounds kilometres away.
  * Sand & stars          — granular high-frequency crackle, and faint
                            shimmering partials as the cosmic backdrop.

Output: /workspace/music/arrakis_winds_v2.wav (stereo, 44100 Hz, 16-bit).
"""

import os
import wave
import numpy as np
from scipy import signal

SR = 44100
DURATION = 210.0            # 3.5 minutes
N = int(SR * DURATION)
t = np.arange(N) / SR

rng = np.random.default_rng(1965)   # year the novel was published


# ---------------------------------------------------------------- helpers

def midi_to_hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def fade(x, fade_in=12.0, fade_out=18.0):
    ni, no = int(fade_in * SR), int(fade_out * SR)
    x[:ni] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(ni) / ni)
    x[-no:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(no) / no)
    return x


def slow_noise(rate_hz, lo=0.0, hi=1.0):
    """Smooth random control signal: sparse normals interpolated to SR."""
    k = max(4, int(DURATION * rate_hz))
    pts = rng.standard_normal(k)
    # light smoothing of the control points themselves
    pts = np.convolve(pts, np.ones(3) / 3, mode="same")
    ctrl = np.interp(t, np.linspace(0, DURATION, k), pts)
    ctrl = (ctrl - ctrl.min()) / (ctrl.max() - ctrl.min() + 1e-12)
    return lo + (hi - lo) * ctrl


def make_reverb_ir(seconds, decay, seed):
    """Exponentially decaying noise burst — convolution reverb IR."""
    r = np.random.default_rng(seed)
    n = int(seconds * SR)
    ir = r.standard_normal(n) * np.exp(-np.arange(n) / SR / decay)
    # soften the IR's top end so the tail sounds dark and distant
    sos = signal.butter(2, 4000, "low", fs=SR, output="sos")
    ir = signal.sosfilt(sos, ir)
    return ir / np.sqrt(np.sum(ir ** 2))


def reverb(x, ir, wet=0.5):
    tail = signal.fftconvolve(x, ir)[: len(x)]
    tail /= np.max(np.abs(tail)) + 1e-12
    tail *= np.max(np.abs(x)) + 1e-12
    return (1 - wet) * x + wet * tail


IR_L = make_reverb_ir(5.0, 1.6, 7)
IR_R = make_reverb_ir(5.0, 1.6, 11)


# ---------------------------------------------------------------- wind

raw = rng.standard_normal(N)

# low whoosh band — the body of the wind
sos_whoosh = signal.butter(4, [120, 900], "bandpass", fs=SR, output="sos")
whoosh = signal.sosfilt(sos_whoosh, raw)
whoosh /= np.max(np.abs(whoosh))

# high hiss band — sand carried on the wind
sos_hiss = signal.butter(4, [2000, 7000], "bandpass", fs=SR, output="sos")
hiss = signal.sosfilt(sos_hiss, raw)
hiss /= np.max(np.abs(hiss))

# gust envelopes: slow stochastic swells, squared so lulls are really quiet
gust = slow_noise(0.22) ** 2.2          # main gust cycle, ~5 s features
gust2 = slow_noise(0.07) ** 1.5          # slower weather front underneath
wind_env = 0.25 + 0.75 * (0.6 * gust + 0.4 * gust2)

# wind drifts across the stereo field with the weather
pan = slow_noise(0.05, 0.25, 0.75)
wind_L = wind_env * (whoosh * np.cos(pan * np.pi / 2) +
                     0.30 * hiss * gust * np.cos((1 - pan) * np.pi / 2))
wind_R = wind_env * (whoosh * np.sin(pan * np.pi / 2) +
                     0.30 * hiss * gust * np.sin((1 - pan) * np.pi / 2))


# ---------------------------------------------------------------- drone

f_D1 = midi_to_hz(26)        # D1 ≈ 36.7 Hz
breath = 0.7 + 0.3 * np.sin(2 * np.pi * 0.012 * t + 1.0)
drone = (np.sin(2 * np.pi * f_D1 * t) +
         0.55 * np.sin(2 * np.pi * f_D1 * 2 * t + 0.4) +
         0.30 * np.sin(2 * np.pi * f_D1 * 3 * t) +          # fifth above octave
         0.30 * np.sin(2 * np.pi * f_D1 * 3.003 * t))       # slow beating
drone *= breath
drone /= np.max(np.abs(drone))


# ---------------------------------------------------------------- worm rumbles

rumble_L = np.zeros(N)
rumble_R = np.zeros(N)

thump_times = []
cursor = 25.0
while cursor < DURATION - 30.0:
    thump_times.append(cursor)
    cursor += rng.uniform(28.0, 45.0)

for tc in thump_times:
    dur = 6.0
    n = int(dur * SR)
    tt = np.arange(n) / SR
    # pitch falls 55 -> 27 Hz: something enormous moving under the sand
    f_curve = 27.0 + 28.0 * np.exp(-tt * 2.2)
    phase = 2 * np.pi * np.cumsum(f_curve) / SR
    env = np.exp(-tt * 1.1) * (1 - np.exp(-tt * 30))
    thump = env * np.sin(phase)
    # ground-shake tail: lowpassed noise
    sos_gr = signal.butter(4, 90, "low", fs=SR, output="sos")
    shake = signal.sosfilt(sos_gr, rng.standard_normal(n)) * env * 0.6
    body = thump + shake
    i0 = int(tc * SR)
    end = min(N, i0 + n)
    g = rng.uniform(0.7, 1.0)
    rumble_L[i0:end] += body[: end - i0] * g
    rumble_R[i0:end] += body[: end - i0] * g

peak = np.max(np.abs(rumble_L)) + 1e-12
rumble_L /= peak
rumble_R /= peak


# ---------------------------------------------------------------- distant calls

# D Phrygian dominant: D Eb F# G A Bb C — the desert mode
SCALE = [62, 63, 66, 67, 69, 70, 72]

call_L = np.zeros(N)
call_R = np.zeros(N)

phrase_start = 45.0
while phrase_start < DURATION - 40.0:
    n_notes = rng.integers(3, 6)
    # phrases lean downward, ending on the root or fifth
    idx = sorted(rng.choice(len(SCALE), size=n_notes, replace=True))[::-1]
    idx[-1] = int(rng.choice([0, 4]))
    durs = rng.uniform(1.6, 3.4, size=n_notes)
    total = float(np.sum(durs)) + 2.0
    n = int(total * SR)
    tt = np.arange(n) / SR

    # frequency curve with portamento between notes
    f_target = np.zeros(n)
    edges = np.concatenate([[0.0], np.cumsum(durs)])
    for k in range(n_notes):
        a, b = int(edges[k] * SR), min(n, int(edges[k + 1] * SR))
        f_target[a:b] = midi_to_hz(SCALE[idx[k]])
    f_target[int(edges[-1] * SR):] = f_target[int(edges[-1] * SR) - 1]
    # exponential glide (one-pole smoother) for the portamento
    alpha = 1.0 - np.exp(-1.0 / (0.09 * SR))
    f_curve = np.empty(n)
    acc = f_target[0]
    bcoef = [alpha]
    acoef = [1.0, -(1.0 - alpha)]
    f_curve = signal.lfilter(bcoef, acoef, f_target, zi=[f_target[0] * (1 - alpha)])[0]

    # vibrato that blooms after each onset
    vib = 1.0 + 0.006 * np.sin(2 * np.pi * 5.2 * tt) * np.clip(tt / 1.2, 0, 1)
    phase = 2 * np.pi * np.cumsum(f_curve * vib) / SR
    env = np.minimum(np.clip(tt / 1.5, 0, 1),
                     np.clip((total - tt) / 2.0, 0, 1)) ** 1.5
    voice = env * (np.sin(phase) + 0.40 * np.sin(2 * phase) +
                   0.18 * np.sin(3 * phase) + 0.07 * np.sin(4 * phase))
    # darken the timbre
    sos_v = signal.butter(2, 2200, "low", fs=SR, output="sos")
    voice = signal.sosfilt(sos_v, voice)

    pan = rng.uniform(0.3, 0.7)
    i0 = int(phrase_start * SR)
    end = min(N, i0 + n)
    call_L[i0:end] += voice[: end - i0] * np.cos(pan * np.pi / 2)
    call_R[i0:end] += voice[: end - i0] * np.sin(pan * np.pi / 2)

    phrase_start += total + rng.uniform(18.0, 30.0)

# drown the calls in reverb — they come from kilometres away
call_L = reverb(call_L, IR_L, wet=0.75)
call_R = reverb(call_R, IR_R, wet=0.75)
peak = max(np.max(np.abs(call_L)), np.max(np.abs(call_R))) + 1e-12
call_L /= peak
call_R /= peak


# ---------------------------------------------------------------- sand & stars

# granular sand crackle: spiky sparse envelope on high-passed noise
sos_sand = signal.butter(4, 6000, "high", fs=SR, output="sos")
grain_noise = signal.sosfilt(sos_sand, rng.standard_normal(N))
grain_noise /= np.max(np.abs(grain_noise))
spikes = np.clip(slow_noise(3.0), 0, 1) ** 10
sand = grain_noise * spikes * wind_env          # only crackles when wind blows

# starfield: very quiet inharmonic high partials — intro texture only.
# Pulses touch full silence, and the whole layer fades away by ~70 s so the
# constant high tone never builds into a tinnitus-like presence.
stars = np.zeros(N)
for f, rate in [(1244.5, 0.021), (1864.7, 0.013), (2793.8, 0.017)]:
    pulse = np.clip(np.sin(2 * np.pi * rate * t), 0, 1) ** 2   # silent half the cycle
    stars += np.sin(2 * np.pi * f * t) * pulse
stars /= np.max(np.abs(stars))
star_fade = np.clip((70.0 - t) / 50.0, 0, 1) ** 2              # gone by 70 s
stars *= star_fade


# ---------------------------------------------------------------- mix

L = (0.32 * wind_L + 0.26 * drone + 0.30 * rumble_L +
     0.22 * call_L + 0.045 * sand + 0.014 * stars)
R = (0.32 * wind_R + 0.26 * drone + 0.30 * rumble_R +
     0.22 * call_R + 0.045 * sand + 0.015 * stars)

fade(L)
fade(R)

peak = max(np.max(np.abs(L)), np.max(np.abs(R)))
L = L / peak * 0.85
R = R / peak * 0.85

stereo = np.empty((N, 2))
stereo[:, 0] = L
stereo[:, 1] = R
pcm = (stereo * 32767.0).astype(np.int16)

OUT_DIR = "/workspace/music"
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, "arrakis_winds_v2.wav")
with wave.open(OUT, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())

print(f"Created: {os.path.abspath(OUT)}")
print(f"Duration: {N / SR:.1f} s  |  {SR} Hz stereo, 16-bit PCM")
print(f"Worm rumbles at: {', '.join(f'{x:.0f}s' for x in thump_times)}")
