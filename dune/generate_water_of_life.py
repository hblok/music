#!/usr/bin/env python3
"""
generate_water_of_life.py — "Water of Life" (~7:20). The Dune palette
taken to goa/psy trance, reference: Juno Reactor (the Matrix scores) —
tribal percussion fused with rolling trance machinery. 140 BPM, still in
D Phrygian dominant, still opening from the same wind so the whole album
crossfades.

The story is the spice agony — the transformation ritual:

  0:00  Wind, drone, a duduk call: the ritual ground.
  0:12  A trance kick alone in the desert. Offbeat hats sneak in.
  0:39  The rolling psy bass starts (kick-b-b-b) — the poison is drunk.
  1:07  A dark acid line begins to twist (the 303 squelch): it works
        through the blood. Sardaukar-style chant pulses underneath.
  1:34  Break: the body fails — kick gone, a duduk prayer (Theme W) over
        tremolo strings — then an 8-bar build with kick-rolls and a riser:
  2:02  DROP 1 — the agony. Full psy groove: kick, rolling bass, hats,
        acid, darbuka. 32 bars, acid cutoff sweeping all the while.
  2:56  Variation: the acid turns melodic, a ney floats above — visions.
  3:24  THE INNER WORLD — the big breakdown: all rhythm gone, strings,
        chant and the duduk vision-theme... then a 16-bar build, chant
        rising, kick rolls accelerating, acid climbing —
  4:19  DROP 2 — the awakening. Everything, plus war drums: the Juno
        Reactor fusion of taiko and trance. Zaps and fills.
  5:14  Four-bar dip (bass + hats only) and straight into
  5:21  the final form: Theme A from Night Pursuit sung over the full
        groove — the album's melody at last over dance machinery.
  6:09  Outro: layers strip away every eight bars; the kick fades like a
        heartbeat calming; at 6:36 it stops. Wind, a duduk lament, one
        chanted breath, a ney echo. The sleeper has awakened — and the
        desert is still there.

Output: /workspace/music/water_of_life.wav (stereo, 44100 Hz, 16-bit).
"""

import os
import wave
import numpy as np
from scipy import signal

SR = 44100
DURATION = 440.0
N = int(SR * DURATION)
t = np.arange(N) / SR

rng = np.random.default_rng(140)     # the tempo is the seed — it IS trance

BPM = 140.0
BEAT = 60.0 / BPM
BAR = BEAT * 4
STEP = BEAT / 4
GRID0 = 12.0


def bar_t(b, beat=0.0):
    return GRID0 + b * BAR + beat * BEAT


# section boundaries, in bars
B_KICK = 0        # kick alone
B_BASS = 16       # rolling bass joins
B_ACID1 = 32      # dark acid + chant pulses
B_BREAK1 = 48     # break: duduk prayer (8 bars)
B_BUILD1 = 56     # build (8 bars)
B_DROP1 = 64      # the agony (32 bars)
B_VAR = 96        # melodic acid + ney (16 bars)
B_BREAK2 = 112    # the inner world (16 bars)
B_BUILD2 = 128    # the long build (16 bars)
B_DROP2 = 144     # the awakening (32 bars)
B_DIP = 176       # bass + hats only (4 bars)
B_FINAL = 180     # Theme A over the groove (28 bars)
B_OUTRO = 208     # layers strip away
B_END = 224       # kick stops; coda


# ---------------------------------------------------------------- helpers

def midi_to_hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def fade(x, fade_in=8.0, fade_out=16.0):
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


def voice_phrase(notes, lp=2200):
    total = sum(d for _, d in notes) + 2.0
    n = int(total * SR)
    tt = np.arange(n) / SR
    f_curve = glide_curve(notes, n)
    vib = 1.0 + 0.006 * np.sin(2 * np.pi * 5.2 * tt) * np.clip(tt / 1.2, 0, 1)
    phase = 2 * np.pi * np.cumsum(f_curve * vib) / SR
    env = np.minimum(np.clip(tt / 1.0, 0, 1),
                     np.clip((total - tt) / 2.0, 0, 1)) ** 1.5
    v = env * (np.sin(phase) + 0.40 * np.sin(2 * phase) +
               0.18 * np.sin(3 * phase) + 0.07 * np.sin(4 * phase))
    sos = signal.butter(2, lp, "low", fs=SR, output="sos")
    return signal.sosfilt(sos, v)


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


IR_L = make_reverb_ir(5.0, 1.6, 7)
IR_R = make_reverb_ir(5.0, 1.6, 11)

mix_L = np.zeros(N)
mix_R = np.zeros(N)


def commit(layer_L, layer_R, weight, env=None):
    global mix_L, mix_R
    peak = max(np.max(np.abs(layer_L)), np.max(np.abs(layer_R)), 1e-12)
    if env is None:
        mix_L += layer_L * (weight / peak)
        mix_R += layer_R * (weight / peak)
    else:
        mix_L += layer_L * env * (weight / peak)
        mix_R += layer_R * env * (weight / peak)


energy_pts = [(0.0, 0.0), (GRID0 - 0.5, 0.0), (GRID0 + 0.5, 0.35),
              (bar_t(B_BASS), 0.35), (bar_t(B_BASS) + 0.5, 0.50),
              (bar_t(B_ACID1), 0.60),
              (bar_t(B_BREAK1), 0.60), (bar_t(B_BREAK1) + 0.3, 0.25),
              (bar_t(B_BUILD1), 0.45), (bar_t(B_DROP1) - 0.1, 0.70),
              (bar_t(B_DROP1) + 0.3, 0.95),
              (bar_t(B_BREAK2), 0.95), (bar_t(B_BREAK2) + 0.3, 0.20),
              (bar_t(B_BUILD2), 0.30), (bar_t(B_DROP2) - 0.1, 0.75),
              (bar_t(B_DROP2) + 0.3, 1.0),
              (bar_t(B_DIP), 1.0), (bar_t(B_DIP) + 0.3, 0.60),
              (bar_t(B_FINAL) + 0.3, 1.0),
              (bar_t(B_OUTRO), 1.0), (bar_t(B_END), 0.30),
              (bar_t(B_END) + 3.0, 0.10), (DURATION, 0.0)]
energy = np.interp(t, [p[0] for p in energy_pts], [p[1] for p in energy_pts])
calm = 1.0 - 0.45 * energy


# helpers for section logic ------------------------------------------------

def rhythm_on(b):
    """Bars where the dance machinery plays at all."""
    return not (B_BREAK1 <= b < B_BUILD1 or B_BREAK2 <= b < B_BUILD2)


def outro_gain(b):
    if b < B_OUTRO:
        return 1.0
    return max(0.25, 1.0 - 0.75 * (b - B_OUTRO) / (B_END - B_OUTRO))


# ---------------------------------------------------------------- wind & drone

raw = rng.standard_normal(N)
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
pan = slow_noise(0.05, 0.25, 0.75)
wind_L = wind_env * (whoosh * np.cos(pan * np.pi / 2) +
                     0.30 * hiss * gust * np.cos((1 - pan) * np.pi / 2))
wind_R = wind_env * (whoosh * np.sin(pan * np.pi / 2) +
                     0.30 * hiss * gust * np.sin((1 - pan) * np.pi / 2))
commit(wind_L, wind_R, 0.24, env=calm)
del whoosh, hiss, wind_L, wind_R

f_D1 = midi_to_hz(26)
breath = 0.7 + 0.3 * np.sin(2 * np.pi * 0.012 * t + 1.0)
drone = (np.sin(2 * np.pi * f_D1 * t) +
         0.55 * np.sin(2 * np.pi * f_D1 * 2 * t + 0.4) +
         0.30 * np.sin(2 * np.pi * f_D1 * 3 * t) +
         0.30 * np.sin(2 * np.pi * f_D1 * 3.003 * t))
drone *= breath
drone /= np.max(np.abs(drone))
commit(drone, drone, 0.20, env=calm)
del drone, breath
print("wind + drone committed")


# ---------------------------------------------------------------- kick
# NEW — trance kick: fast 150->45 Hz drop, sub-millisecond attack, a touch
# of click. Four to the floor; rolls (8ths then 16ths) launch the drops.

def make_kick():
    n = int(0.30 * SR)
    td = np.arange(n) / SR
    f_curve = 45.0 + 105.0 * np.exp(-td * 55.0)
    body = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    click = rng.standard_normal(n) * np.exp(-td * 900)
    env = (1 - np.exp(-td / 0.0008)) * np.exp(-td * 9.0)
    x = (body + 0.25 * click) * env
    return x / (np.max(np.abs(x)) + 1e-12)


KICK = make_kick()

lay_L = np.zeros(N)
lay_R = np.zeros(N)
for b in range(B_END):
    if not rhythm_on(b) or B_DIP <= b < B_FINAL:
        continue
    g = outro_gain(b)
    if b in (B_BUILD1 + 6, B_BUILD2 + 14):          # 8th-note roll bar
        for e in range(8):
            gg = g * (0.55 + 0.45 * e / 7)
            add_at(lay_L, KICK, bar_t(b, e * 0.5), gg)
            add_at(lay_R, KICK, bar_t(b, e * 0.5), gg)
        continue
    if b in (B_BUILD1 + 7, B_BUILD2 + 15):          # 16th-note roll bar
        for s in range(16):
            gg = g * (0.55 + 0.45 * s / 15)
            add_at(lay_L, KICK, bar_t(b, s * 0.25), gg)
            add_at(lay_R, KICK, bar_t(b, s * 0.25), gg)
        continue
    if B_BUILD1 <= b < B_BUILD1 + 6 or B_BUILD2 + 8 <= b < B_BUILD2 + 14:
        g *= 0.6                                    # builds: kick held back
    elif b < B_DROP1:
        g *= 0.8                                    # pre-drop: leave headroom
    if B_BUILD2 <= b < B_BUILD2 + 8:
        continue                                    # build2 starts kickless
    for beat in range(4):
        add_at(lay_L, KICK, bar_t(b, beat), g)
        add_at(lay_R, KICK, bar_t(b, beat), g)
commit(lay_L, lay_R, 0.32)
print("kick committed")


# ---------------------------------------------------------------- psy bass
# NEW — the rolling bass: kick on the beat, bass on the three 16ths after
# (K-b-b-b). Band-limited saw, lowpassed dark, tanh drive, hard gate.

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


PB = {m: psy_bass_note(m) for m in (38, 36, 39, 50)}

lay_L[:] = 0.0
lay_R[:] = 0.0
for b in range(B_END):
    if b < B_BASS or not rhythm_on(b):
        continue
    if B_BUILD2 <= b < B_BUILD2 + 8:
        continue                                    # silent start of build2
    if b >= B_OUTRO + 8:
        continue                                    # bass leaves before kick
    g = outro_gain(b)
    if b < B_DROP1:
        g *= 0.65          # pre-drop headroom: sustained bass carries the RMS
    for beat in range(4):
        for s, gg in [(1, 0.8), (2, 0.7), (3, 0.95)]:
            m = 38
            if b % 4 == 3 and beat == 3:
                m = [36, 39, 38][s - 1]             # cadence walk
            elif B_DROP2 <= b and beat == 3 and s == 3:
                m = 50                              # octave flick
            add_at(lay_L, PB[m], bar_t(b, beat + s * 0.25), g * gg)
            add_at(lay_R, PB[m], bar_t(b, beat + s * 0.25), g * gg)
commit(lay_L, lay_R, 0.30)
print("psy bass committed")


# ---------------------------------------------------------------- hats
# NEW — offbeat open hats + 16th closed ghosts in the drops.

def make_hat(open_=False):
    n = int((0.12 if open_ else 0.045) * SR)
    td = np.arange(n) / SR
    sos_h = signal.butter(4, 7000, "high", fs=SR, output="sos")
    x = signal.sosfilt(sos_h, rng.standard_normal(n))
    x *= np.exp(-td * (30 if open_ else 110))
    return x / (np.max(np.abs(x)) + 1e-12)


OHAT = make_hat(open_=True)
CHAT = make_hat()

lay_L[:] = 0.0
lay_R[:] = 0.0
for b in range(B_END):
    if b < 8 or not rhythm_on(b) or B_BUILD2 <= b < B_BUILD2 + 8:
        continue
    g = outro_gain(b)
    for beat in range(4):
        add_at(lay_L, OHAT, bar_t(b, beat + 0.5), g * 0.8)
        add_at(lay_R, OHAT, bar_t(b, beat + 0.5), g)
    if B_DROP1 <= b:                                # closed 16th ghosts
        for s in range(16):
            if s % 2 == 0:
                continue
            p = 0.3 + 0.4 * ((s // 2) % 2)
            add_at(lay_L, CHAT, bar_t(b, s * 0.25),
                   g * 0.35 * np.cos(p * np.pi / 2))
            add_at(lay_R, CHAT, bar_t(b, s * 0.25),
                   g * 0.35 * np.sin(p * np.pi / 2))
commit(lay_L, lay_R, 0.08)
print("hats committed")


# ---------------------------------------------------------------- acid
# NEW — 303-style line: band-limited saw through a resonant lowpass
# (butter lowpass + iirpeak at the cutoff = the squelch), tanh drive.
# Cutoff breathes over 16-bar cycles and jumps on accents.

acid_cache = {}


def acid_note(m, cutoff, accent=False, dur=STEP * 0.9):
    cutoff = float(np.clip(cutoff * (1.6 if accent else 1.0), 160, 6000))
    key = (m, int(cutoff // 75), accent)
    if key in acid_cache:
        return acid_cache[key]
    f = midi_to_hz(m)
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    for k in range(1, min(30, int(8000 / f)) + 1):
        x += np.sin(2 * np.pi * k * f * td) / k
    sos_lp = signal.butter(2, cutoff, "low", fs=SR, output="sos")
    y = signal.sosfilt(sos_lp, x)
    bpk, apk = signal.iirpeak(cutoff, Q=7.0, fs=SR)
    y = y + (1.5 if accent else 1.1) * signal.lfilter(bpk, apk, y)
    y = np.tanh(2.2 * y)
    env = (1 - np.exp(-td / 0.003)) * np.clip((dur - td) / 0.03, 0, 1)
    y *= env
    y /= np.max(np.abs(y)) + 1e-12
    acid_cache[key] = y
    return y


# 16-step riffs: (midi or None, accent)
RIFF_DARK = [(50, 1), (None, 0), (50, 0), (None, 0),
             (50, 0), (62, 1), (None, 0), (50, 0),
             (51, 0), (None, 0), (50, 0), (None, 0),
             (54, 1), (None, 0), (48, 0), (50, 0)]
RIFF_MELO = [(50, 1), (50, 0), (62, 0), (50, 0),
             (63, 1), (62, 0), (54, 0), (50, 0),
             (57, 1), (None, 0), (55, 0), (54, 0),
             (51, 0), (54, 0), (50, 1), (None, 0)]
RIFF_HIGH = [(m + 12 if m else None, a) for m, a in RIFF_MELO]

lay_L[:] = 0.0
lay_R[:] = 0.0


def acid_bars(b0, b1, riff, cut_lo, cut_hi, gain=1.0, ramp=False):
    for b in range(b0, b1):
        frac = (b - b0) / max(1, b1 - b0)
        if ramp:
            base = cut_lo + (cut_hi - cut_lo) * frac          # one-way climb
        else:
            base = cut_lo + (cut_hi - cut_lo) * \
                (0.5 + 0.5 * np.sin(2 * np.pi * (b - b0) / 16 - np.pi / 2))
        for s, (m, acc) in enumerate(riff):
            if m is None:
                continue
            cut = base * (1.0 + 0.25 * np.sin(2 * np.pi * s / 16))
            x = acid_note(m, cut, accent=bool(acc))
            p = 0.5 + 0.18 * np.sin(2 * np.pi * (b * 16 + s) / 24)
            add_at(lay_L, x, bar_t(b, s * 0.25), gain * np.cos(p * np.pi / 2))
            add_at(lay_R, x, bar_t(b, s * 0.25), gain * np.sin(p * np.pi / 2))


acid_bars(B_ACID1, B_BREAK1, RIFF_DARK, 260, 700, gain=0.8)
acid_bars(B_DROP1, B_VAR, RIFF_DARK, 300, 1800)
acid_bars(B_VAR, B_BREAK2, RIFF_MELO, 600, 2400)
acid_bars(B_BUILD2 + 8, B_DROP2, RIFF_DARK, 400, 3200, ramp=True)
acid_bars(B_DROP2, B_DROP2 + 16, RIFF_HIGH, 900, 3500)
acid_bars(B_DROP2 + 16, B_DIP, RIFF_MELO, 700, 2800)
acid_bars(B_FINAL, B_OUTRO, RIFF_MELO, 600, 2200, gain=0.75)
acid_bars(B_OUTRO, B_OUTRO + 8, RIFF_DARK, 400, 900, gain=0.6)
commit(lay_L, lay_R, 0.16)
print(f"acid committed ({len(acid_cache)} cached notes)")


# ---------------------------------------------------------------- zaps
# NEW — psy zap: fast exponential pitch dive with ring-mod shimmer.

def make_zap():
    n = int(0.40 * SR)
    td = np.arange(n) / SR
    f_curve = 80.0 + 1900.0 * np.exp(-td * 18.0)
    x = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    x *= 1.0 + 0.5 * np.sin(2 * np.pi * 35.0 * td)
    x *= np.exp(-td * 8.0) * (1 - np.exp(-td / 0.002))
    return x / (np.max(np.abs(x)) + 1e-12)


ZAP = make_zap()

lay_L[:] = 0.0
lay_R[:] = 0.0
zap_bars = [B_DROP1, B_DROP1 + 8, B_DROP1 + 16, B_DROP1 + 24,
            B_VAR, B_VAR + 8, B_DROP2, B_DROP2 + 8, B_DROP2 + 16,
            B_DROP2 + 24, B_FINAL, B_FINAL + 8, B_FINAL + 16]
for b in zap_bars:
    beat = float(rng.choice([0.0, 1.5, 3.5]))
    p = rng.uniform(0.2, 0.8)
    add_at(lay_L, ZAP, bar_t(b, beat), np.cos(p * np.pi / 2))
    add_at(lay_R, ZAP, bar_t(b, beat), np.sin(p * np.pi / 2))
lay_L = reverb(lay_L, IR_L, wet=0.35)
lay_R = reverb(lay_R, IR_R, wet=0.35)
commit(lay_L, lay_R, 0.08)
print("zaps committed")


# ---------------------------------------------------------------- darbuka
# The tribal half of the Juno Reactor fusion: light maqsum riding the
# trance grid through the drops and the final.

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
MAQSUM = {0: "D", 2: "T", 6: "T", 8: "D", 12: "T"}

lay_L[:] = 0.0
lay_R[:] = 0.0
for b in range(B_END):
    in_drop = (B_DROP1 <= b < B_BREAK2 or B_DROP2 <= b < B_DIP or
               B_FINAL <= b < B_OUTRO)
    if not in_drop:
        continue
    level = 0.6 * outro_gain(b)
    fill_bar = b % 8 == 7
    for s in range(16):
        st = bar_t(b, s * 0.25)
        stroke = MAQSUM.get(s)
        if fill_bar and s >= 10:
            g = (0.45 + 0.55 * (s - 10) / 5.0) * level
            add_at(lay_L, TEK, st, g * 0.9)
            add_at(lay_R, TEK, st, g * 0.7)
            continue
        if stroke == "D":
            add_at(lay_L, DOUM, st, level)
            add_at(lay_R, DOUM, st, level)
        elif stroke == "T":
            p = 0.35 if s in (2, 12) else 0.65
            add_at(lay_L, TEK, st, level * np.cos(p * np.pi / 2))
            add_at(lay_R, TEK, st, level * np.sin(p * np.pi / 2))
        elif s % 2 == 1 and rng.random() < 0.25:
            add_at(lay_L, KA, st, 0.6 * level)
            add_at(lay_R, KA, st, 0.5 * level)
commit(lay_L, lay_R, 0.14)
print("darbuka committed")


# ---------------------------------------------------------------- war drums
# Drop 2 and the final only — the taiko-over-trance moment.

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


WAR = make_war_drum()

lay_L[:] = 0.0
lay_R[:] = 0.0
for b in range(B_END):
    if not (B_DROP2 <= b < B_DIP or B_FINAL <= b < B_OUTRO + 8):
        continue
    g = outro_gain(b)
    add_at(lay_L, WAR, bar_t(b, 0.0), g * (1.0 if b % 8 == 0 else 0.55))
    add_at(lay_R, WAR, bar_t(b, 0.0), g * (1.0 if b % 8 == 0 else 0.55))
    if b % 4 == 2:
        add_at(lay_L, WAR, bar_t(b, 2.5), g * 0.45)
        add_at(lay_R, WAR, bar_t(b, 2.5), g * 0.45)
commit(lay_L, lay_R, 0.22)
print("war drums committed")


# ---------------------------------------------------------------- frame rolls

def make_frame_hit():
    n = int(0.12 * SR)
    td = np.arange(n) / SR
    sos_f = signal.butter(2, [180, 1400], "bandpass", fs=SR, output="sos")
    nz = signal.sosfilt(sos_f, rng.standard_normal(n)) * np.exp(-td * 40)
    nz /= np.max(np.abs(nz)) + 1e-12
    tone = 0.5 * np.sin(2 * np.pi * 95.0 * td) * np.exp(-td * 30)
    x = nz + tone
    return x / (np.max(np.abs(x)) + 1e-12)


FRAME = make_frame_hit()


def frame_roll(dur=2.0):
    out = np.zeros(int((dur + 0.3) * SR))
    tcur = 0.0
    while tcur < dur:
        frac = tcur / dur
        rate = 9.0 + 11.0 * frac
        g = (0.30 + 0.70 * frac) * rng.uniform(0.85, 1.0)
        add_at(out, FRAME, tcur, g)
        tcur += 1.0 / rate
    return out


lay_L[:] = 0.0
lay_R[:] = 0.0
for start_s, dur_s, g in [(bar_t(B_BUILD1 + 6), 2 * BAR, 0.9),
                          (bar_t(B_BUILD2 + 14), 2 * BAR, 1.0),
                          (bar_t(B_FINAL - 1), BAR, 0.8),
                          (bar_t(B_DROP1 + 16) - 0.5 * BAR, 0.5 * BAR, 0.6),
                          (bar_t(B_DROP2 + 16) - 0.5 * BAR, 0.5 * BAR, 0.6)]:
    roll = frame_roll(dur_s)
    add_at(lay_L, roll, start_s, g * 0.9)
    add_at(lay_R, roll, start_s, g)
commit(lay_L, lay_R, 0.10)
print("frame rolls committed")


# ---------------------------------------------------------------- risers

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


lay_L[:] = 0.0
lay_R[:] = 0.0
for b0, dur_bars in [(B_BUILD1 + 4, 4), (B_BUILD2 + 12, 4),
                     (B_DIP, 4), (B_BASS - 4, 4)]:
    rz = riser(dur_bars * BAR)
    add_at(lay_L, rz, bar_t(b0), 0.85)
    add_at(lay_R, rz, bar_t(b0), 1.0)
commit(lay_L, lay_R, 0.12)
print("risers committed")


# ---------------------------------------------------------------- strings

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


lay_L = np.zeros(N)
lay_R = np.zeros(N)
for chord, b0, b1, trem, gL, gR in [
        ([62, 63], B_BREAK1, B_BUILD1 + 4, 10.5, 0.8, 0.7),
        ([62, 69, 63], B_BREAK2, B_BUILD2 + 8, 10.5, 0.9, 0.8),
        ([62, 69, 75], B_BUILD2 + 8, B_DROP2, 12.0, 0.8, 0.9),
        ([62, 69, 75], B_FINAL, B_OUTRO, 12.0, 0.6, 0.65)]:
    sw = tremolo_strings(chord, (b1 - b0) * BAR, trem_hz=trem)
    add_at(lay_L, sw, bar_t(b0), gL)
    add_at(lay_R, sw, bar_t(b0), gR)
lay_L = reverb(lay_L, IR_L, wet=0.45)
lay_R = reverb(lay_R, IR_R, wet=0.45)
commit(lay_L, lay_R, 0.14)
print("strings committed")


# ---------------------------------------------------------------- duduk
# Theme W: the ritual prayer, new to this track. In the final section the
# duduk sings Theme A from Night Pursuit over the full groove — the
# album's melody finally over dance machinery.

b2s = lambda nb: nb * BEAT

THEME_W_1 = [(62, b2s(2)), (63, b2s(1)), (67, b2s(2)), (66, b2s(1)),
             (67, b2s(1)), (69, b2s(3)), (70, b2s(2)), (69, b2s(1)),
             (67, b2s(2)), (66, b2s(1)), (63, b2s(2)), (62, b2s(4))]
THEME_W_2 = [(69, b2s(2)), (70, b2s(1)), (72, b2s(2)), (70, b2s(1)),
             (69, b2s(2)), (67, b2s(2)), (66, b2s(2)), (63, b2s(2)),
             (62, b2s(5))]
# Theme A as sung in night_pursuit / maker_comes (durations in beats there
# were at 104 BPM; stretched slightly here so it breathes over 140 BPM)
s104 = 60.0 / 104.0
THEME_A_VOICE = [(62, 2 * s104), (66, 1 * s104), (63, 1 * s104),
                 (62, 2 * s104), (60, 2 * s104), (62, 3 * s104),
                 (63, 1 * s104), (66, 2 * s104), (69, 2 * s104),
                 (67, 2 * s104), (66, 1 * s104), (63, 1 * s104),
                 (62, 4 * s104), (60, 2 * s104), (63, 2 * s104),
                 (62, 4 * s104)]

lay_L = np.zeros(N)
lay_R = np.zeros(N)


def place_voice(notes, t0, pan_pos, gain=1.0, lp=2200):
    v = voice_phrase(notes, lp=lp)
    add_at(lay_L, v, t0, gain * np.cos(pan_pos * np.pi / 2))
    add_at(lay_R, v, t0, gain * np.sin(pan_pos * np.pi / 2))


place_voice([(62, 1.0), (66, 0.8), (63, 0.8), (62, 2.2)], 4.0, 0.6)
place_voice(THEME_W_1, bar_t(B_BREAK1), 0.5)
place_voice(THEME_W_1, bar_t(B_BREAK2), 0.55)
place_voice(THEME_W_2, bar_t(B_BREAK2 + 8), 0.42, 0.95)
place_voice(THEME_A_VOICE, bar_t(B_FINAL), 0.5)             # the Navras moment
place_voice(THEME_A_VOICE, bar_t(B_FINAL + 14), 0.58, 0.9)
# coda lament
place_voice([(70, 1.6), (69, 1.6), (67, 1.6), (66, 1.6), (63, 1.6),
             (62, 4.5)], bar_t(B_END) + 4.0, 0.5, 1.0, lp=1900)

lay_L = reverb(lay_L, IR_L, wet=0.6)
lay_R = reverb(lay_R, IR_R, wet=0.6)
commit(lay_L, lay_R, 0.20)
print("duduk committed")


# ---------------------------------------------------------------- ney

lay_L = np.zeros(N)
lay_R = np.zeros(N)
NEY_W = [(m + 12, d) for m, d in THEME_W_1]
v = ney_phrase(NEY_W)
add_at(lay_L, v, bar_t(B_VAR + 2), 0.8 * np.cos(0.6 * np.pi / 2))
add_at(lay_R, v, bar_t(B_VAR + 2), 0.8 * np.sin(0.6 * np.pi / 2))
v = ney_phrase([(74, 1.4), (72, 1.4), (69, 1.8), (67, 2.6)])
add_at(lay_L, v, bar_t(B_END) + 20.0, 0.7 * np.cos(0.4 * np.pi / 2))
add_at(lay_R, v, bar_t(B_END) + 20.0, 0.7 * np.sin(0.4 * np.pi / 2))
lay_L = reverb(lay_L, IR_L, wet=0.55)
lay_R = reverb(lay_R, IR_R, wet=0.55)
commit(lay_L, lay_R, 0.12)
print("ney committed")


# ---------------------------------------------------------------- chant
# Pulses under the dark acid, rising through the long build, and one last
# breath in the coda.

lay_L = np.zeros(N)
lay_R = np.zeros(N)
CH_LONG = {m: chant_note(m, 1.4 * BEAT) for m in (38, 36)}
CH_SHORT = {m: chant_note(m, 0.85 * BEAT) for m in (38, 36)}

for b in range(B_ACID1, B_BREAK1):
    if b % 2 == 0:
        add_at(lay_L, CH_LONG[38], bar_t(b, 0.0), 0.8)
        add_at(lay_R, CH_LONG[38], bar_t(b, 0.0), 0.9)
for b in range(B_BUILD2, B_DROP2):
    root = 36 if b % 4 == 3 else 38
    g = 0.5 + 0.5 * (b - B_BUILD2) / (B_DROP2 - B_BUILD2)   # rising
    for beat, gg, bank in [(0.0, 1.0, CH_LONG), (2.0, 0.8, CH_SHORT),
                           (3.0, 0.8, CH_SHORT)]:
        add_at(lay_L, bank[root], bar_t(b, beat), g * gg * 0.9)
        add_at(lay_R, bank[root], bar_t(b, beat), g * gg)
for b in range(B_DROP2 + 16, B_DIP):
    add_at(lay_L, CH_LONG[38], bar_t(b, 0.0), 0.7)
    add_at(lay_R, CH_LONG[38], bar_t(b, 0.0), 0.8)
last = chant_note(38, 5.0, pulse=4.0)
add_at(lay_L, last, bar_t(B_END) + 13.0, 0.7)
add_at(lay_R, last, bar_t(B_END) + 13.0, 0.7)

lay_L = reverb(lay_L, IR_L, wet=0.45)
lay_R = reverb(lay_R, IR_R, wet=0.45)
commit(lay_L, lay_R, 0.15)
print("chant committed")


# ---------------------------------------------------------------- master

fade(mix_L, fade_in=6.0)
fade(mix_R, fade_in=6.0)

peak = max(np.max(np.abs(mix_L)), np.max(np.abs(mix_R)))
mix_L = mix_L / peak * 0.88
mix_R = mix_R / peak * 0.88

stereo = np.empty((N, 2))
stereo[:, 0] = mix_L
stereo[:, 1] = mix_R
pcm = (stereo * 32767.0).astype(np.int16)

OUT_DIR = "/workspace/music"
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, "water_of_life.wav")
with wave.open(OUT, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())

print(f"\nCreated: {os.path.abspath(OUT)}")
print(f"Duration: {N / SR:.1f} s  |  {SR} Hz stereo, 16-bit PCM  |  {BPM:.0f} BPM")
print("Section map:")
for name, b in [("kick alone", B_KICK), ("rolling bass", B_BASS),
                ("dark acid + chant", B_ACID1), ("break 1: duduk prayer", B_BREAK1),
                ("build 1", B_BUILD1), ("DROP 1 — the agony", B_DROP1),
                ("variation: melodic acid + ney", B_VAR),
                ("the inner world (breakdown)", B_BREAK2),
                ("the long build", B_BUILD2), ("DROP 2 — the awakening", B_DROP2),
                ("dip (bass + hats)", B_DIP),
                ("final: Theme A over the groove", B_FINAL),
                ("outro: layers strip away", B_OUTRO), ("kick stops", B_END)]:
    print(f"  {bar_t(b):6.1f} s  bar {b:3d}  {name}")
print(f"  {DURATION:6.1f} s  end (coda: duduk {bar_t(B_END)+4:.0f} s, "
      f"chant {bar_t(B_END)+13:.0f} s, ney {bar_t(B_END)+20:.0f} s)")
