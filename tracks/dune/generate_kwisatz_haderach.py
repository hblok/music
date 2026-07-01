#!/usr/bin/env python3
"""
generate_kwisatz_haderach.py — "Kwisatz Haderach" (~9:00). The album closer.

A track that contains the whole album: the one who can be many places at
once sees every timeline the psy line has visited. Three "visions of
possible futures" cycle the signature groove of each previous psy track —
Water of Life's rolling bass, The Sleeper Awakens' sliding 303, The Fall of
Arrakeen's room-shake kick — each vision interrupted by the night_pursuit
tick-tock (the breakdown clock: time itself changing the channel). Then the
still point, the long build, and THE FUSION: all three engines at once —
two basses sidechained against the arrakeen kick stack, both 303 riffs in
call-and-response, choir, war drums, Theme A and the war theme together.

146 BPM, D Phrygian dominant, seed 10193 (Paul takes the throne; all
futures converge). Ending: one final stab and every layer stops except the
original arrakis wind — the first sound of the album is also the last.

  0:00  Wind, D1 drone, one duduk call (the album's opening, quoted).
  0:14  The tick starts. Bar 4: the Water of Life trance kick, alone.
  0:47  VISION 1 — WATER (40 bars): rolling K-b-b-b bass, dark acid
        (water's riff), darbuka, chant pulses, Theme W on the duduk.
  1:53  Interrupt: everything dead — tick + heartbeat. The vision shifts.
  1:59  VISION 2 — SLEEPER (40 bars): brighter kick, the sharp sliding
        303 (RIFF_SYNC), psy clap, ney calls, Theme S.
  3:05  Interrupt 2.
  3:12  VISION 3 — ARRAKEEN (40 bars): the room-shake kick stack +
        sub-boom + sidechain pump take over; oud war riff, field-snare
        march, war drums, battle toms, THEME_WAR on the carnyx horn.
  4:17  THE STILL POINT (16 bars): rhythm gone; the tick; ghosts of all
        three themes drift past, far away. The choice is made.
  4:44  The long build (24 bars): chant rising the whole way, acid
        climbing one-way, snare buzz crescendo, kick rolls.
  5:23  THE FUSION (104 bars):
          +0   all three engines fuse — arrakeen kick, rolling bass +
               offbeat bass (both pumped), water/sleeper 303 riffs in
               2-bar call-and-response L/R
          +16  the album stack: war drums, darbuka, shaker, 12-voice choir
          +32  mini-dip A: kick + chant + tick
          +36  Theme A over the machine — the destination
          +52  mini-dip B: bass + hats + riser
          +56  high phase: both riffs an octave up, toms, ney calls
          +72  FALSE ENDING: one huge hit, then wind + tick for 2 bars
          +74  THE LAST WAVE: everything at once — Theme A doubled by the
               ney, THEME_WAR on the horn over it, choir every bar,
               8th-note kick sprint for the final 10 bars
  8:14  THE CUT: one stab. Every layer stops — except the wind.
  8:14 → 9:00  The original arrakis wind, alone, fading. He sees.

Output: /workspace/music/kwisatz_haderach.wav (stereo, 44100 Hz, 16-bit).
"""

import os
import wave
import numpy as np
from scipy import signal

SR = 44100
DURATION = 540.0
N = int(SR * DURATION)
t = np.arange(N) / SR

rng = np.random.default_rng(10193)   # Paul takes the throne; futures converge

BPM = 146.0
BEAT = 60.0 / BPM
BAR = BEAT * 4
STEP = BEAT / 4
GRID0 = 14.0


def bar_t(b, beat=0.0):
    return GRID0 + b * BAR + beat * BEAT


# Section boundaries, in bars.
B_TICK = 0        # tick alone over wind + drone (4 bars)
B_KICK = 4        # water trance kick staircase (8 bars)
B_TEASE = 12      # rolling bass sneaks in (8 bars)
B_V1 = 20         # VISION 1 — WATER (40 bars)
B_INT1 = 60       # interrupt: tick + heartbeat (4 bars)
B_V2 = 64         # VISION 2 — SLEEPER (40 bars)
B_INT2 = 104      # interrupt 2 (4 bars)
B_V3 = 108        # VISION 3 — ARRAKEEN (40 bars)
B_STILL = 148     # the still point (16 bars)
B_BUILD = 164     # the long build (24 bars)
B_FUSION = 188    # THE FUSION (104 bars)
B_CUT = 292       # the final stab; only the wind survives

# fusion internal landmarks
F_STACK = B_FUSION + 16      # 204: the album stack piles on
DIPA = set(range(B_FUSION + 32, B_FUSION + 36))    # 220..223 kick+chant+tick
F_THEME = B_FUSION + 36      # 224: Theme A over the machine
DIPB = set(range(B_FUSION + 52, B_FUSION + 56))    # 240..243 bass+hats+riser
F_HIGH = B_FUSION + 56       # 244: both riffs octave up
FALSE_BARS = {B_FUSION + 72, B_FUSION + 73}        # 260..261 false ending
F_WAVE = B_FUSION + 74       # 262: the last wave
F_SPRINT = B_FUSION + 94     # 282: 8th-note kick sprint

INT1 = set(range(B_INT1, B_V2))
INT2 = set(range(B_INT2, B_V3))
N_LAYERS = 0

# ------------------------------------------------------------- quoted themes
# Every melody in this track is a quotation. Sources noted per line.
b2s = lambda nb: nb * BEAT
# water_of_life — Theme W (the ritual prayer)
THEME_W = [(62, b2s(2)), (63, b2s(1)), (67, b2s(2)), (66, b2s(1)),
           (67, b2s(1)), (69, b2s(3)), (70, b2s(2)), (69, b2s(1)),
           (67, b2s(2)), (66, b2s(1)), (63, b2s(2)), (62, b2s(4))]
# sleeper_awakens — Theme S (rising, hanging on the dominant)
THEME_S = [(62, b2s(2)), (63, b2s(1)), (66, b2s(2)), (67, b2s(1)),
           (69, b2s(2)), (70, b2s(1)), (69, b2s(1)), (67, b2s(2)),
           (66, b2s(1)), (67, b2s(1)), (69, b2s(4))]
# fall_of_arrakeen — THEME_WAR + its horn call
THEME_WAR = [(62, b2s(1.5)), (62, b2s(0.5)), (63, b2s(1)), (62, b2s(1)),
             (67, b2s(2)), (66, b2s(1)), (63, b2s(1)), (62, b2s(1)),
             (70, b2s(1.5)), (69, b2s(0.5)), (67, b2s(1)), (66, b2s(1)),
             (63, b2s(2)), (62, b2s(3))]
HORN_CALL = [(50, 1.2), (51, 0.6), (50, 2.2)]
# night_pursuit — Theme A, the album's melody (native 104 BPM phrasing)
s104 = 60.0 / 104.0
THEME_A = [(62, 2 * s104), (66, 1 * s104), (63, 1 * s104),
           (62, 2 * s104), (60, 2 * s104), (62, 3 * s104),
           (63, 1 * s104), (66, 2 * s104), (69, 2 * s104),
           (67, 2 * s104), (66, 1 * s104), (63, 1 * s104),
           (62, 4 * s104), (60, 2 * s104), (63, 2 * s104),
           (62, 4 * s104)]
# the album's very first duduk call (water/sleeper opening)
OPEN_CALL = [(62, 1.0), (66, 0.8), (63, 0.8), (62, 2.2)]

# 16-step acid riffs: (midi or None, accent, slide_to)
# water_of_life originals (no slides — its acid predates the tie)
RIFF_DARK_W = [(50, 1, None), (None, 0, None), (50, 0, None), (None, 0, None),
               (50, 0, None), (62, 1, None), (None, 0, None), (50, 0, None),
               (51, 0, None), (None, 0, None), (50, 0, None), (None, 0, None),
               (54, 1, None), (None, 0, None), (48, 0, None), (50, 0, None)]
RIFF_MELO_W = [(50, 1, None), (50, 0, None), (62, 0, None), (50, 0, None),
               (63, 1, None), (62, 0, None), (54, 0, None), (50, 0, None),
               (57, 1, None), (None, 0, None), (55, 0, None), (54, 0, None),
               (51, 0, None), (54, 0, None), (50, 1, None), (None, 0, None)]
# sleeper_awakens originals (the slide riffs)
RIFF_SYNC = [(50, 1, None), (None, 0, None), (50, 0, 51), (51, 0, None),
             (None, 0, None), (50, 0, None), (54, 1, None), (None, 0, None),
             (57, 0, 55), (55, 0, None), (None, 0, None), (50, 0, None),
             (62, 1, None), (None, 0, None), (48, 0, 50), (50, 0, None)]
RIFF_HIGH = [(m + 12 if m else None, a, s + 12 if s else None)
             for m, a, s in [(50, 1, None), (50, 0, None), (62, 0, None),
                             (50, 0, None), (63, 1, 62), (62, 0, None),
                             (54, 0, None), (50, 0, None), (57, 1, None),
                             (None, 0, None), (55, 0, 54), (54, 0, None),
                             (51, 0, None), (54, 0, None), (50, 1, None),
                             (None, 0, None)]]
# fall_of_arrakeen originals
RIFF_WAR1 = [(50, 1, None), (None, 0, None), (50, 0, None), (50, 0, None),
             (None, 0, None), (50, 0, None), (51, 1, 50), (None, 0, None),
             (58, 1, 57), (57, 0, None), (None, 0, None), (50, 0, None),
             (54, 0, None), (None, 0, None), (51, 0, 50), (50, 0, None)]
RIFF_WAR2 = [(62, 1, None), (62, 0, None), (70, 0, 69), (69, 0, None),
             (None, 0, None), (66, 0, None), (63, 1, 62), (62, 0, None),
             (74, 1, None), (None, 0, None), (70, 0, None), (69, 0, None),
             (66, 0, None), (63, 0, None), (62, 1, None), (None, 0, None)]
RIFF_DARK_W12 = [(m + 12 if m else None, a, None) for m, a, _ in RIFF_DARK_W]
RIFF_MELO_W12 = [(m + 12 if m else None, a, None) for m, a, _ in RIFF_MELO_W]
OUD_RIFF = [50, None, 50, None, 51, None, 50, None,
            58, 57, None, 50, 54, None, 51, 50]


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


def horn_phrase(notes, growl=0.18, lp=1600):
    """fall_of_arrakeen war horn: brassy stack, pitch scoop, 31 Hz growl."""
    total = sum(d for _, d in notes) + 1.2
    n = int(total * SR)
    tt = np.arange(n) / SR
    f_curve = glide_curve(notes, n)
    scoop = 0.94 + 0.06 * np.clip(tt / 0.15, 0, 1)
    phase = 2 * np.pi * np.cumsum(f_curve * scoop) / SR
    tone = np.zeros(n)
    for k in range(1, 13):
        tone += np.sin(k * phase) / k ** 0.7
    tone *= 1.0 + growl * np.sin(2 * np.pi * 31.0 * tt)
    env = np.minimum(np.clip(tt / 0.10, 0, 1) ** 0.8,
                     np.clip((total - tt) / 1.0, 0, 1))
    tone *= env
    sos_lo = signal.butter(2, lp, "low", fs=SR, output="sos")
    out = signal.sosfilt(sos_lo, tone)
    sos_fm = signal.butter(2, [450, 900], "bandpass", fs=SR, output="sos")
    out += 0.6 * signal.sosfilt(sos_fm, tone)
    return out / (np.max(np.abs(out)) + 1e-12)


def chant_note(midi, dur, pulse=5.5, scatter=1.0):
    """Sardaukar throat chant: glottal harmonics through dark formants."""
    n = int(dur * SR)
    td = np.arange(n) / SR
    f0 = midi_to_hz(midi) * scatter
    phase = 2 * np.pi * np.cumsum(np.full(n, f0)) / SR
    src = np.zeros(n)
    for k in range(1, 15):
        src += np.sin(k * phase) / k ** 0.8
    env = np.minimum(np.clip(td / 0.025, 0, 1), np.clip((dur - td) / 0.08, 0, 1))
    src *= env * (0.70 + 0.30 * np.sin(2 * np.pi * pulse * td))
    out = np.zeros(n)
    for lo, hi, g in [(380, 560, 1.0), (750, 1000, 0.6), (2200, 2700, 0.15)]:
        sos = signal.butter(2, [lo, hi], "bandpass", fs=SR, output="sos")
        out += g * signal.sosfilt(sos, src)
    out += 0.40 * np.sin(phase * 0.5) * env
    return out / (np.max(np.abs(out)) + 1e-12)


def mass_chant_note(midi, dur, voices=12):
    """jihad's 12-voice choir (the Choir of Sietch Tabr recipe)."""
    n = int((dur + 0.16) * SR)
    L = np.zeros(n)
    R = np.zeros(n)
    for v in range(voices):
        det = 1.0 + rng.uniform(-0.008, 0.008)
        jitter = int(rng.uniform(0.0, 0.12) * SR)
        body = chant_note(midi, dur, scatter=det)
        body *= rng.uniform(0.82, 1.05)
        end = min(n, jitter + len(body))
        pan = (v + 0.5) / voices
        L[jitter:end] += body[: end - jitter] * np.cos(pan * np.pi / 2)
        R[jitter:end] += body[: end - jitter] * np.sin(pan * np.pi / 2)
    pk = max(np.max(np.abs(L)), np.max(np.abs(R))) + 1e-12
    return L / pk, R / pk


def oud_note(m, dur=0.55):
    """Karplus-Strong double-course oud (the base_under_attack recipe)."""
    n = int(dur * SR)
    out = np.zeros(n)
    for det in (1.0, 1.004):
        period = max(2, int(SR / (midi_to_hz(m) * det)))
        buf = rng.uniform(-1, 1, period)
        idx = 0
        for i in range(n):
            out[i] += buf[idx]
            nxt = (idx + 1) % period
            buf[idx] = 0.4985 * (buf[idx] + buf[nxt])
            idx = nxt
    sos_o = signal.butter(2, [200, 4200], "bandpass", fs=SR, output="sos")
    out = signal.sosfilt(sos_o, out)
    out *= np.clip((dur - np.arange(n) / SR) / 0.04, 0, 1)
    return out / (np.max(np.abs(out)) + 1e-12)


def commit(layer_L, layer_R, weight, env=None):
    global mix_L, mix_R, N_LAYERS
    N_LAYERS += 1
    pk = max(np.max(np.abs(layer_L)), np.max(np.abs(layer_R))) + 1e-12
    L = layer_L / pk * weight
    R = layer_R / pk * weight
    if env is not None:
        L *= env
        R *= env
    mix_L += L
    mix_R += R


IR_L = make_reverb_ir(5.0, 1.6, 7)
IR_R = make_reverb_ir(5.0, 1.6, 11)
mix_L = np.zeros(N)
mix_R = np.zeros(N)

# Energy curve: three plateaus (the visions), a deep still point, then the
# fusion holds the ceiling until the cut.
points = [(0.0, 0.0), (GRID0 - 0.5, 0.10), (bar_t(B_KICK), 0.30),
          (bar_t(B_V1), 0.55), (bar_t(B_V1) + 0.5, 0.85),
          (bar_t(B_INT1), 0.85), (bar_t(B_INT1) + 0.3, 0.20),
          (bar_t(B_V2) + 0.3, 0.90), (bar_t(B_INT2), 0.90),
          (bar_t(B_INT2) + 0.3, 0.20), (bar_t(B_V3) + 0.3, 0.95),
          (bar_t(B_STILL), 0.95), (bar_t(B_STILL) + 0.3, 0.15),
          (bar_t(B_BUILD), 0.25), (bar_t(B_FUSION) - 0.1, 0.70),
          (bar_t(B_FUSION) + 0.3, 1.00),
          (bar_t(min(FALSE_BARS)), 1.00), (bar_t(min(FALSE_BARS)) + 0.2, 0.30),
          (bar_t(F_WAVE) + 0.3, 1.10), (bar_t(B_CUT), 1.10),
          (bar_t(B_CUT) + 1.5, 0.05), (DURATION, 0.0)]
energy = np.interp(t, [p[0] for p in points], [p[1] for p in points])
calm = 1.0 - 0.55 * np.clip(energy, 0, 1)


# ------------------------------------------------------ section-logic helpers

def stack_on(b):
    """Bars where the arrakeen kick stack plays four-to-the-floor."""
    if B_V3 <= b < B_STILL:
        return True
    if B_BUILD + 16 <= b < B_BUILD + 22:        # held back through the build
        return True
    if B_FUSION <= b < B_CUT:
        return b not in DIPB and b not in FALSE_BARS
    return False


def bass_on(b):
    if b in INT1 or b in INT2 or b in DIPA or b in FALSE_BARS:
        return False
    if B_STILL <= b < B_BUILD + 8:
        return False
    return B_TEASE <= b < B_CUT


def hats_on(b):
    if b < 8 or b >= B_CUT:
        return False
    if b in INT1 or b in INT2 or b in DIPA or b in FALSE_BARS:
        return False
    if B_STILL <= b < B_BUILD + 8:
        return False
    return True


def groove_full(b):
    """Bars with the full dance machinery (claps, darbuka, etc.)."""
    return (hats_on(b) and b not in DIPB and
            not (B_BUILD <= b < B_FUSION))


# Sidechain pump — active wherever the stack kick owns the floor. The fusion
# is only readable because the kick ducks both basses and the drone 55 %.
pump = np.ones(N)
for _b in range(B_V3, B_CUT):
    if not stack_on(_b):
        continue
    for _beat in (0.0, 1.0, 2.0, 3.0):
        i0 = int(bar_t(_b, _beat) * SR)
        n = min(int(BEAT * SR), N - i0)
        if n > 0:
            duck = 1.0 - 0.55 * np.exp(-np.arange(n) / SR / 0.10)
            pump[i0:i0+n] = np.minimum(pump[i0:i0+n], np.maximum(duck, 0.28))

# ---------------------------------------------------------------- wind & drone
# The album wind, verbatim — it plays under everything and it alone
# survives the cut. Its weighted signal is kept for the coda restore.
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
del whoosh, hiss
wpk = max(np.max(np.abs(wind_L)), np.max(np.abs(wind_R))) + 1e-12
windw_L = wind_L / wpk * 0.23          # kept: the survivor layer
windw_R = wind_R / wpk * 0.23
del wind_L, wind_R
N_LAYERS += 1
mix_L += windw_L * calm
mix_R += windw_R * calm
print("wind committed (survivor copy kept)")

f_D1 = midi_to_hz(26)
breath = 0.7 + 0.3 * np.sin(2 * np.pi * 0.012 * t + 1.0)
drone = (np.sin(2 * np.pi * f_D1 * t) +
         0.55 * np.sin(2 * np.pi * f_D1 * 2 * t + 0.4) +
         0.30 * np.sin(2 * np.pi * f_D1 * 3 * t) +
         0.30 * np.sin(2 * np.pi * f_D1 * 3.003 * t))
drone *= breath
commit(drone, drone, 0.20, env=calm * pump)
del drone, breath
print("drone committed")

# ---------------------------------------------------------------- the tick
# night_pursuit's clock, verbatim: the interrupter. It opens the grid, cuts
# off every vision, owns the still point, and haunts the dips.

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


TICK = make_tick()
TOCK = make_tick(tock=True)
TICK_BARS = (set(range(B_TICK, B_KICK)) | INT1 | INT2 |
             set(range(B_STILL, B_BUILD)) | DIPA | FALSE_BARS)
lay_L = np.zeros(N)
lay_R = np.zeros(N)
for b in sorted(TICK_BARS):
    for e in range(8):
        x = TICK if e % 2 == 0 else TOCK
        p = 0.32 if e % 2 == 0 else 0.68
        add_at(lay_L, x, bar_t(b, e * 0.5), 0.9 * np.cos(p * np.pi / 2))
        add_at(lay_R, x, bar_t(b, e * 0.5), 0.9 * np.sin(p * np.pi / 2))
commit(lay_L, lay_R, 0.05)                       # bone dry, always
print("tick committed")

# ---------------------------------------------------------------- heartbeat

def make_thump():
    n = int(0.30 * SR)
    td = np.arange(n) / SR
    f = 32.0 + 28.0 * np.exp(-td * 30.0)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR)
    x *= (1 - np.exp(-td / 0.004)) * np.exp(-td * 9.0)
    return x / (np.max(np.abs(x)) + 1e-12)


THUMP = make_thump()
lay_L[:] = 0.0
lay_R[:] = 0.0
for b in sorted(INT1 | INT2 | set(range(B_STILL, B_STILL + 8))):
    for beat in (0.0, 2.0):
        add_at(lay_L, THUMP, bar_t(b, beat), 1.0)
        add_at(lay_R, THUMP, bar_t(b, beat), 1.0)
        add_at(lay_L, THUMP, bar_t(b, beat) + 0.28, 0.55)
        add_at(lay_R, THUMP, bar_t(b, beat) + 0.28, 0.55)
commit(lay_L, lay_R, 0.13)
print("heartbeat committed")

# ---------------------------------------------------------------- kicks
# Three kicks, one per engine. Vision 1: water_of_life's trance kick (raw
# noise click). Vision 2: sleeper's brighter kick. Vision 3 + fusion: the
# arrakeen room-shake stack + dedicated sub-boom + pump.

def make_kick_water():
    n = int(0.30 * SR)
    td = np.arange(n) / SR
    f_curve = 45.0 + 105.0 * np.exp(-td * 55.0)
    body = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    click = rng.standard_normal(n) * np.exp(-td * 900)
    env = (1 - np.exp(-td / 0.0008)) * np.exp(-td * 9.0)
    x = (body + 0.25 * click) * env
    return x / (np.max(np.abs(x)) + 1e-12)


def make_kick_sleeper():
    n = int(0.30 * SR)
    td = np.arange(n) / SR
    f_curve = 45.0 + 105.0 * np.exp(-td * 55.0)
    body = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    sos_c = signal.butter(2, [1800, 9000], "bandpass", fs=SR, output="sos")
    click = signal.sosfilt(sos_c, rng.standard_normal(n)) * np.exp(-td * 700)
    click /= np.max(np.abs(click)) + 1e-12
    env = (1 - np.exp(-td / 0.0008)) * np.exp(-td * 9.0)
    x = (body + 0.45 * click) * env
    return x / (np.max(np.abs(x)) + 1e-12)


def make_kick_stack(sub=True):
    n = int(0.55 * SR)
    td = np.arange(n) / SR
    f = 44.0 + (150.0 - 44.0) * np.exp(-td * 55.0)
    punch = np.sin(2 * np.pi * np.cumsum(f) / SR) * \
        (1 - np.exp(-td / 0.0008)) * np.exp(-td * 9.0)
    click_noise = rng.standard_normal(n) * np.exp(-td * 85.0)
    click = signal.sosfilt(signal.butter(2, [1800, 9000], "bandpass",
                                         fs=SR, output="sos"), click_noise)
    out = punch + 0.50 * click
    if sub:
        fsu = 37.0 + (55.0 - 37.0) * np.exp(-td * 3.0)
        tail = np.sin(2 * np.pi * np.cumsum(fsu) / SR) * np.exp(-td * 3.0)
        out += 1.15 * tail
    return out / (np.max(np.abs(out)) + 1e-12)


def make_sub_boom():
    n = int(BEAT * SR)
    td = np.arange(n) / SR
    f = 37.0 + (50.0 - 37.0) * np.exp(-td * 2.4)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR)
    rel = np.minimum(1.0, np.clip((BEAT - td) / 0.06, 0, 1))
    x *= (1 - np.exp(-td / 0.018)) * np.exp(-td * 1.2) * rel
    return x / (np.max(np.abs(x)) + 1e-12)


KICK_W = make_kick_water()
KICK_S = make_kick_sleeper()
KICK_ST = make_kick_stack(True)
KICK_P = make_kick_stack(False)
BOOM = make_sub_boom()

# vision 1 kick (water): staircase in, full through the vision
lay_L[:] = 0.0
lay_R[:] = 0.0
for b in range(B_KICK, B_INT1):
    if b < B_TEASE:
        g = 0.70
    elif b < B_V1:
        g = 0.78
    else:
        g = 0.95 + 0.05 * (b >= B_V1 + 32)
    for beat in range(4):
        add_at(lay_L, KICK_W, bar_t(b, beat), g)
        add_at(lay_R, KICK_W, bar_t(b, beat), g)
commit(lay_L, lay_R, 0.32)
print("water kick committed")

# vision 2 kick (sleeper)
lay_L[:] = 0.0
lay_R[:] = 0.0
for b in range(B_V2, B_INT2):
    g = 0.95 + 0.05 * (b >= B_V2 + 32)
    for beat in range(4):
        add_at(lay_L, KICK_S, bar_t(b, beat), g)
        add_at(lay_R, KICK_S, bar_t(b, beat), g)
commit(lay_L, lay_R, 0.32)
print("sleeper kick committed")

# vision 3 + fusion kick (arrakeen stack) — with build rolls and the sprint
lay_L[:] = 0.0
lay_R[:] = 0.0
for b in range(B_V3, B_CUT):
    if stack_on(b):
        kg = 0.86 if b in DIPA else (0.60 if B_BUILD <= b < B_FUSION
                                     else 0.95 + 0.10 * (b >= F_WAVE))
        for beat in (0.0, 1.0, 2.0, 3.0):
            add_at(lay_L, KICK_ST, bar_t(b, beat), kg)
            add_at(lay_R, KICK_ST, bar_t(b, beat), kg)
            if b >= F_SPRINT:
                add_at(lay_L, KICK_P, bar_t(b, beat + 0.5), kg * 0.72)
                add_at(lay_R, KICK_P, bar_t(b, beat + 0.5), kg * 0.72)
    elif b == B_BUILD + 22:                        # 8th-note roll bar
        for e in range(8):
            gg = 0.50 * (0.55 + 0.45 * e / 7)      # rolls peak BELOW the drop
            add_at(lay_L, KICK_ST, bar_t(b, e * 0.5), gg)
            add_at(lay_R, KICK_ST, bar_t(b, e * 0.5), gg)
    elif b == B_BUILD + 23:                        # 16th-note roll bar
        for s in range(16):
            gg = 0.50 * (0.55 + 0.45 * s / 15)
            add_at(lay_L, KICK_ST, bar_t(b, s * 0.25), gg)
            add_at(lay_R, KICK_ST, bar_t(b, s * 0.25), gg)
commit(lay_L, lay_R, 0.50)
print("arrakeen kick stack committed")

lay_L[:] = 0.0
lay_R[:] = 0.0
for b in range(B_V3, B_CUT):
    if not stack_on(b) or B_BUILD <= b < B_FUSION:
        continue
    for beat in (0.0, 1.0, 2.0, 3.0):
        add_at(lay_L, BOOM, bar_t(b, beat), 1.0)
        add_at(lay_R, BOOM, bar_t(b, beat), 1.0)
commit(lay_L, lay_R, 0.30)
print("sub boom committed")

# ---------------------------------------------------------------- basses
# Bass 1: the water_of_life rolling bass (K-b-b-b), the whole track's spine.
# Bass 2: an offbeat D3 stab, fusion only — the second engine the spec asks
# for; both ride the pump so the arrakeen kick owns the sub alone.

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
for b in range(B_TEASE, B_CUT):
    if not bass_on(b):
        continue
    if b < B_V1:
        g = 0.62
    elif b < B_INT1 or B_V2 <= b < B_INT2:
        g = 1.0
    elif B_V3 <= b < B_STILL:
        g = 0.85                                  # the oud carries vision 3
    elif B_BUILD <= b < B_FUSION:
        g = 0.65
    else:
        g = 1.0
    for beat in range(4):
        for s, gg in [(1, 0.8), (2, 0.7), (3, 0.95)]:
            m = 38
            if b % 4 == 3 and beat == 3:
                m = [36, 39, 38][s - 1]           # cadence walk
            elif (B_V2 + 32 <= b < B_INT2 or b >= F_WAVE) and beat == 3 and s == 3:
                m = 50                            # octave flick
            add_at(lay_L, PB[m], bar_t(b, beat + s * 0.25), g * gg)
            add_at(lay_R, PB[m], bar_t(b, beat + s * 0.25), g * gg)
commit(lay_L, lay_R, 0.30, env=pump)
print("rolling bass committed")

lay_L[:] = 0.0
lay_R[:] = 0.0
for b in range(B_FUSION, B_CUT):
    if not stack_on(b) or b in DIPA:
        continue
    for beat in range(4):
        add_at(lay_L, PB[50], bar_t(b, beat + 0.5), 0.9)
        add_at(lay_R, PB[50], bar_t(b, beat + 0.5), 0.9)
commit(lay_L, lay_R, 0.12, env=pump)
print("offbeat bass committed")

# ---------------------------------------------------------------- acid
# One acid engine — the sleeper's sharp per-note-sweeping 303 (arrakeen used
# it too) — but each vision plays its OWN track's riffs and cutoff ranges.

acid_cache = {}


def acid_note(m, cutoff, accent=False, slide_to=None, dur=None):
    if dur is None:
        dur = STEP * (1.02 if slide_to else 0.92)
    cutoff = float(np.clip(cutoff * (1.5 if accent else 1.0), 200, 7500))
    key = (m, int(cutoff // 60), accent, slide_to)
    if key in acid_cache:
        return acid_cache[key]
    f = midi_to_hz(m)
    n = int(dur * SR)
    td = np.arange(n) / SR
    if slide_to is None:
        ph = 2 * np.pi * f * td
    else:
        f2 = midi_to_hz(slide_to)
        fc = f * (f2 / f) ** np.clip((td - 0.45 * dur) / (0.55 * dur), 0, 1)
        ph = 2 * np.pi * np.cumsum(fc) / SR
    x = np.zeros(n)
    for k in range(1, min(48, int(10500 / min(f, midi_to_hz(slide_to))
                                  if slide_to else 10500 / f)) + 1):
        x += np.sin(k * ph) / k

    def res_lp(sig_in, c):
        c = float(min(c, 9000.0))
        sos_lp = signal.butter(2, c, "low", fs=SR, output="sos")
        y = signal.sosfilt(sos_lp, sig_in)
        bpk, apk = signal.iirpeak(min(c, 8000.0), Q=11.0, fs=SR)
        return y + (1.9 if accent else 1.4) * signal.lfilter(bpk, apk, y)

    bright = res_lp(x, cutoff * 3.0)
    dark = res_lp(x, cutoff * 0.75)
    sweep = np.exp(-td / (0.10 if accent else 0.055))
    y = np.tanh(2.8 * (sweep * bright + (1 - sweep) * dark))
    env = (1 - np.exp(-td / 0.0015)) * np.clip((dur - td) / 0.02, 0, 1)
    y *= env
    y /= np.max(np.abs(y)) + 1e-12
    acid_cache[key] = y
    return y


def acid_bars(b0, b1, riff, cut_lo, cut_hi, gain=1.0, ramp=False,
              pan_c=0.5, phase_b0=None):
    if phase_b0 is None:
        phase_b0 = b0
    for b in range(b0, b1):
        frac = (b - b0) / max(1, b1 - b0)
        if ramp:
            base = cut_lo + (cut_hi - cut_lo) * frac
        else:
            base = cut_lo + (cut_hi - cut_lo) * \
                (0.5 + 0.5 * np.sin(2 * np.pi * (b - phase_b0) / 16 - np.pi / 2))
        for s, (m, acc, sl) in enumerate(riff):
            if m is None:
                continue
            cut = base * (1.0 + 0.25 * np.sin(2 * np.pi * s / 16))
            x = acid_note(m, cut, accent=bool(acc), slide_to=sl)
            p = pan_c + 0.15 * np.sin(2 * np.pi * (b * 16 + s) / 24)
            add_at(lay_L, x, bar_t(b, s * 0.25), gain * np.cos(p * np.pi / 2))
            add_at(lay_R, x, bar_t(b, s * 0.25), gain * np.sin(p * np.pi / 2))


# vision 1 — water's riffs, water's cutoffs
lay_L[:] = 0.0
lay_R[:] = 0.0
acid_bars(B_V1 + 8, B_V1 + 32, RIFF_DARK_W, 300, 1800)
acid_bars(B_V1 + 32, B_INT1, RIFF_MELO_W, 600, 2400)
commit(lay_L, lay_R, 0.16)
print(f"water acid committed")

# vision 2 — sleeper's slide riffs
lay_L[:] = 0.0
lay_R[:] = 0.0
acid_bars(B_V2, B_V2 + 16, RIFF_SYNC, 500, 2600)
acid_bars(B_V2 + 16, B_V2 + 32, RIFF_HIGH, 900, 3600)
acid_bars(B_V2 + 32, B_INT2, RIFF_SYNC, 1200, 4200)
commit(lay_L, lay_R, 0.17)
print(f"sleeper acid committed")

# vision 3 — arrakeen's war riffs
lay_L[:] = 0.0
lay_R[:] = 0.0
acid_bars(B_V3 + 8, B_V3 + 24, RIFF_WAR1, 400, 2400)
acid_bars(B_V3 + 24, B_STILL, RIFF_WAR2, 1000, 4200)
commit(lay_L, lay_R, 0.17)
print(f"arrakeen acid committed")

# build ramp + THE FUSION: water riff answers sleeper riff, 2 bars each,
# panned to opposite sides; the last wave plays both at once, climbing
# one-way into the cut.
lay_L[:] = 0.0
lay_R[:] = 0.0
acid_bars(B_BUILD + 8, B_FUSION, RIFF_DARK_W, 400, 3600, gain=0.8, ramp=True)
for b in range(B_FUSION, B_FUSION + 32):
    if (b - B_FUSION) % 4 < 2:
        acid_bars(b, b + 1, RIFF_DARK_W, 600, 3000, pan_c=0.32,
                  phase_b0=B_FUSION)
    else:
        acid_bars(b, b + 1, RIFF_SYNC, 600, 3000, pan_c=0.68,
                  phase_b0=B_FUSION)
for b in range(F_THEME, F_THEME + 16):
    if (b - F_THEME) % 4 < 2:
        acid_bars(b, b + 1, RIFF_MELO_W, 600, 2400, gain=0.75, pan_c=0.32,
                  phase_b0=F_THEME)
    else:
        acid_bars(b, b + 1, RIFF_SYNC, 600, 2400, gain=0.75, pan_c=0.68,
                  phase_b0=F_THEME)
for b in range(F_HIGH, F_HIGH + 16):
    if (b - F_HIGH) % 4 < 2:
        acid_bars(b, b + 1, RIFF_DARK_W12, 1000, 4500, pan_c=0.32,
                  phase_b0=F_HIGH)
    else:
        acid_bars(b, b + 1, RIFF_HIGH, 1000, 4500, pan_c=0.68,
                  phase_b0=F_HIGH)
for b in range(F_WAVE, B_CUT):                    # both riffs at once
    frac = (b - F_WAVE) / (B_CUT - F_WAVE)
    base = 1200 + (5000 - 1200) * frac
    acid_bars(b, b + 1, RIFF_MELO_W, base, base, gain=0.95, pan_c=0.30)
    acid_bars(b, b + 1, RIFF_SYNC, base, base, gain=0.95, pan_c=0.70)
commit(lay_L, lay_R, 0.18)
print(f"fusion acid committed ({len(acid_cache)} cached notes)")

# ---------------------------------------------------------------- oud
lay_L[:] = 0.0
lay_R[:] = 0.0
OUD = {m: oud_note(m) for m in (50, 51, 54, 57, 58)}
for b in list(range(B_V3, B_V3 + 16)) + list(range(B_V3 + 24, B_STILL)) + \
        list(range(F_WAVE + 8, F_SPRINT)):
    for s, m in enumerate(OUD_RIFF):
        if m is None:
            continue
        p = 0.40 if s % 4 == 0 else 0.62
        add_at(lay_L, OUD[m], bar_t(b, s * 0.25), np.cos(p * np.pi / 2))
        add_at(lay_R, OUD[m], bar_t(b, s * 0.25), np.sin(p * np.pi / 2))
commit(lay_L, lay_R, 0.15)
print("oud committed")

# ---------------------------------------------------------------- hats, clap, shaker

def make_hat(open_=False):
    n = int((0.16 if open_ else 0.045) * SR)
    td = np.arange(n) / SR
    sos_h = signal.butter(4, 6500 if open_ else 7000, "high",
                          fs=SR, output="sos")
    x = signal.sosfilt(sos_h, rng.standard_normal(n))
    x *= np.exp(-td * (24 if open_ else 100))
    return x / (np.max(np.abs(x)) + 1e-12)


def make_clap():
    n = int(0.26 * SR)
    td = np.arange(n) / SR
    sos_c = signal.butter(2, [900, 5200], "bandpass", fs=SR, output="sos")
    nz = signal.sosfilt(sos_c, rng.standard_normal(n))
    nz /= np.max(np.abs(nz)) + 1e-12
    env = np.zeros(n)
    for i, t0 in enumerate([0.0, 0.011, 0.022, 0.033]):
        i0 = int(t0 * SR)
        rate = 120.0 if i < 3 else 26.0
        seg = (0.65 if i < 3 else 1.0) * np.exp(-(td[i0:] - t0) * rate)
        env[i0:] = np.maximum(env[i0:], seg)
    x = nz * env
    return x / (np.max(np.abs(x)) + 1e-12)


def make_shaker():
    n = int(0.055 * SR)
    td = np.arange(n) / SR
    x = signal.sosfilt(signal.butter(2, [3500, 9500], "bandpass",
                                     fs=SR, output="sos"),
                       rng.standard_normal(n))
    x *= np.exp(-td * 85.0)
    return x / (np.max(np.abs(x)) + 1e-12)


OHAT, CHAT, CLAP, SHAKER = make_hat(True), make_hat(False), make_clap(), make_shaker()

lay_L[:] = 0.0
lay_R[:] = 0.0
for b in range(8, B_CUT):
    if not hats_on(b):
        continue
    for beat in range(4):
        add_at(lay_L, OHAT, bar_t(b, beat + 0.5), 0.8)
        add_at(lay_R, OHAT, bar_t(b, beat + 0.5), 1.0)
    if b >= B_V1 + 16 and b not in DIPB:           # closed 16th ghosts
        for s in range(16):
            if s % 2 == 0:
                continue
            p = 0.3 + 0.4 * ((s // 2) % 2)
            add_at(lay_L, CHAT, bar_t(b, s * 0.25), 0.35 * np.cos(p * np.pi / 2))
            add_at(lay_R, CHAT, bar_t(b, s * 0.25), 0.35 * np.sin(p * np.pi / 2))
commit(lay_L, lay_R, 0.12)
print("hats committed")

lay_L[:] = 0.0
lay_R[:] = 0.0
for b in range(B_V2, B_CUT):
    if not groove_full(b) or b < B_V2:
        continue
    for beat in (1, 3):
        p = 0.42 if beat == 1 else 0.58
        add_at(lay_L, CLAP, bar_t(b, beat), np.cos(p * np.pi / 2))
        add_at(lay_R, CLAP, bar_t(b, beat), np.sin(p * np.pi / 2))
commit(lay_L, lay_R, 0.11)
print("clap committed")

lay_L[:] = 0.0
lay_R[:] = 0.0
for b in range(F_STACK, B_CUT):
    if not groove_full(b):
        continue
    for s in range(16):
        g = [0.9, 0.4, 0.65, 0.4][s % 4]
        add_at(lay_L, SHAKER, bar_t(b, s * 0.25), g * 0.90)
        add_at(lay_R, SHAKER, bar_t(b, s * 0.25), g * 0.75)
commit(lay_L, lay_R, 0.07)
print("shaker committed")

# ---------------------------------------------------------------- darbuka

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
    sos_h = signal.butter(4, [2800, 10000], "bandpass", fs=SR, output="sos")
    slap = signal.sosfilt(sos_h, rng.standard_normal(n))
    ping = 0.4 * np.sin(2 * np.pi * 640.0 * td)
    env = np.exp(-td * (90.0 if ghost else 55.0))
    x = (slap / (np.max(np.abs(slap)) + 1e-12) + ping) * env
    return x * (0.35 if ghost else 1.0)


DOUM, TEK, KA = make_doum(), make_tek(), make_tek(ghost=True)
MAQSUM = {0: "D", 2: "T", 6: "T", 8: "D", 12: "T"}
DARBUKA_BARS = (set(range(B_V1 + 16, B_INT1)) | set(range(B_V2 + 16, B_INT2)) |
                set(range(B_V3 + 16, B_STILL)) | set(range(F_STACK, B_CUT)))
lay_L[:] = 0.0
lay_R[:] = 0.0
for b in sorted(DARBUKA_BARS):
    if not groove_full(b):
        continue
    level = 0.6
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

# ---------------------------------------------------------------- war drums + toms

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


def make_tom(f0):
    n = int(0.38 * SR)
    td = np.arange(n) / SR
    f = f0 * (1.0 + 0.40 * np.exp(-td * 40.0))
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-td * 8.5)
    skin = signal.sosfilt(signal.butter(2, [300, 1500], "bandpass",
                                        fs=SR, output="sos"),
                          rng.standard_normal(n))
    skin *= np.exp(-td * 22.0)
    x = body + 0.35 * skin
    return x / (np.max(np.abs(x)) + 1e-12)


WAR = make_war_drum()
TOMS = [make_tom(165), make_tom(110), make_tom(80)]
WAR_BARS = set(range(B_V3 + 16, B_STILL)) | set(range(F_STACK, B_CUT))
lay_L[:] = 0.0
lay_R[:] = 0.0
for b in sorted(WAR_BARS):
    if not groove_full(b):
        continue
    g = 0.85 + 0.25 * (b >= F_WAVE)
    add_at(lay_L, WAR, bar_t(b, 0.0), g)
    add_at(lay_R, WAR, bar_t(b, 0.0), g)
    add_at(lay_L, WAR, bar_t(b, 2.0), g * 0.55)
    add_at(lay_R, WAR, bar_t(b, 2.0), g * 0.55)
commit(lay_L, lay_R, 0.22)
print("war drums committed")

tom_pat = [(0, 0.0, 0.7, 0.35), (1, 1.5, 0.55, 0.65),
           (2, 2.25, 0.65, 0.25), (1, 3.25, 0.50, 0.75)]
TOM_BARS = set(range(B_V3 + 16, B_STILL)) | set(range(F_HIGH, B_CUT))
lay_L[:] = 0.0
lay_R[:] = 0.0
for b in sorted(TOM_BARS):
    if not groove_full(b):
        continue
    heavy = 0.80 + 0.30 * (b >= F_WAVE)
    if b % 8 == 7:
        for i in range(8):
            tom = TOMS[i % 3]
            p = 0.25 + 0.5 * (i % 2)
            add_at(lay_L, tom, bar_t(b, 2.0 + i * 0.25),
                   heavy * 0.8 * np.cos(p * np.pi / 2))
            add_at(lay_R, tom, bar_t(b, 2.0 + i * 0.25),
                   heavy * 0.8 * np.sin(p * np.pi / 2))
    for idx, beat, g, p in tom_pat:
        add_at(lay_L, TOMS[idx], bar_t(b, beat), heavy * g * np.cos(p * np.pi / 2))
        add_at(lay_R, TOMS[idx], bar_t(b, beat), heavy * g * np.sin(p * np.pi / 2))
commit(lay_L, lay_R, 0.15)
print("battle toms committed")

# ---------------------------------------------------------------- field snare

def make_snare(buzz=False):
    n = int((0.22 if not buzz else 0.10) * SR)
    td = np.arange(n) / SR
    tone = np.sin(2 * np.pi * 185 * td) * np.exp(-td * 35) + \
        0.55 * np.sin(2 * np.pi * 330 * td) * np.exp(-td * 42)
    noise = signal.sosfilt(signal.butter(2, [1500, 9000], "bandpass",
                                         fs=SR, output="sos"),
                           rng.standard_normal(n))
    noise *= np.exp(-td * (55 if not buzz else 95))
    x = tone + 0.75 * noise
    return x / (np.max(np.abs(x)) + 1e-12)


SNARE, SBUZZ = make_snare(False), make_snare(True)
lay_L[:] = 0.0
lay_R[:] = 0.0
for b in range(B_V3, B_STILL):                    # the arrakeen march
    for s in (4, 12):
        add_at(lay_L, SBUZZ, bar_t(b, s * 0.25) - 0.030, 0.25)
        add_at(lay_L, SNARE, bar_t(b, s * 0.25), 0.50)
        add_at(lay_R, SNARE, bar_t(b, s * 0.25), 0.42)
for b in range(B_BUILD, B_FUSION):                # buzz crescendo
    frac = (b - B_BUILD) / (B_FUSION - B_BUILD)
    for s in range(16):
        add_at(lay_L, SBUZZ, bar_t(b, s * 0.25), 0.20 + 0.45 * frac)
        add_at(lay_R, SBUZZ, bar_t(b, s * 0.25), 0.16 + 0.42 * frac)
commit(lay_L, lay_R, 0.12)
print("field snare committed")

# ---------------------------------------------------------------- chant + choir
lay_L[:] = 0.0
lay_R[:] = 0.0
CH_LONG = {m: chant_note(m, 1.4 * BEAT) for m in (38, 36)}
CH_SHORT = {m: chant_note(m, 0.85 * BEAT) for m in (38, 36)}
for b in range(B_V1 + 16, B_V1 + 32):             # pulses under water's acid
    if b % 2 == 0:
        add_at(lay_L, CH_LONG[38], bar_t(b, 0.0), 0.8)
        add_at(lay_R, CH_LONG[38], bar_t(b, 0.0), 0.9)
for b in range(B_BUILD, B_FUSION):                # rising the whole build
    root = 36 if b % 4 == 3 else 38
    g = 0.5 + 0.5 * (b - B_BUILD) / (B_FUSION - B_BUILD)
    for beat, gg, bank in [(0.0, 1.0, CH_LONG), (2.0, 0.8, CH_SHORT),
                           (3.0, 0.8, CH_SHORT)]:
        add_at(lay_L, bank[root], bar_t(b, beat), g * gg * 0.9)
        add_at(lay_R, bank[root], bar_t(b, beat), g * gg)
for b in sorted(DIPA):                            # the chant owns dip A
    for beat, gg in [(0.0, 1.0), (1.0, 0.7), (2.0, 0.9), (3.0, 0.7)]:
        add_at(lay_L, CH_SHORT[38 if beat != 3.0 else 36], bar_t(b, beat), gg)
        add_at(lay_R, CH_SHORT[38 if beat != 3.0 else 36], bar_t(b, beat), gg)
lay_L = reverb(lay_L, IR_L, wet=0.45)
lay_R = reverb(lay_R, IR_R, wet=0.45)
commit(lay_L, lay_R, 0.15)
print("chant committed")

CHOIR38_L, CHOIR38_R = mass_chant_note(38, 1.35 * BEAT)
CHOIR36_L, CHOIR36_R = mass_chant_note(36, 1.35 * BEAT)
lay_L = np.zeros(N)
lay_R = np.zeros(N)
for b in range(F_STACK, B_FUSION + 32):           # every 2 bars in the stack
    if b % 2 == 0:
        add_at(lay_L, CHOIR38_L, bar_t(b, 0.0), 0.8)
        add_at(lay_R, CHOIR38_R, bar_t(b, 0.0), 0.8)
for b in range(F_WAVE, B_CUT):                    # every bar in the last wave
    CL, CR = (CHOIR36_L, CHOIR36_R) if b % 4 == 3 else (CHOIR38_L, CHOIR38_R)
    for beat in (0.0, 2.0):
        add_at(lay_L, CL, bar_t(b, beat), 0.95 if beat == 0.0 else 0.7)
        add_at(lay_R, CR, bar_t(b, beat), 0.95 if beat == 0.0 else 0.7)
lay_L = reverb(lay_L, IR_L, wet=0.30)
lay_R = reverb(lay_R, IR_R, wet=0.30)
commit(lay_L, lay_R, 0.16, env=np.maximum(pump, 0.52))
print("choir committed")

# ---------------------------------------------------------------- horn
lay_L = np.zeros(N)
lay_R = np.zeros(N)


def place_horn(notes, t0, pan_pos, gain=1.0, growl=0.18, lp=1600):
    h = horn_phrase(notes, growl=growl, lp=lp)
    add_at(lay_L, h, t0, gain * np.cos(pan_pos * np.pi / 2))
    add_at(lay_R, h, t0, gain * np.sin(pan_pos * np.pi / 2))


place_horn([(m - 12, d) for m, d in THEME_WAR[:8]],
           bar_t(B_V3 + 8), 0.45, 0.85)                       # the war call
place_horn(THEME_WAR, bar_t(B_V3 + 24), 0.42, 1.0)
place_horn(HORN_CALL, bar_t(B_V3 + 32), 0.62, 0.9)
place_horn(HORN_CALL, bar_t(B_STILL + 9), 0.55, 0.5,
           growl=0.05, lp=1000)                               # still-point ghost
place_horn(THEME_WAR, bar_t(F_WAVE + 12), 0.40, 1.05)         # over Theme A
lay_L = reverb(lay_L, IR_L, wet=0.35)
lay_R = reverb(lay_R, IR_R, wet=0.35)
commit(lay_L, lay_R, 0.18)
print("horn committed")

# ---------------------------------------------------------------- duduk
lay_L = np.zeros(N)
lay_R = np.zeros(N)


def place_voice(notes, t0, pan_pos, gain=1.0, lp=2200):
    v = voice_phrase(notes, lp=lp)
    add_at(lay_L, v, t0, gain * np.cos(pan_pos * np.pi / 2))
    add_at(lay_R, v, t0, gain * np.sin(pan_pos * np.pi / 2))


place_voice(OPEN_CALL, 5.0, 0.6)                              # the album opens
place_voice(THEME_W, bar_t(B_V1 + 24), 0.5)                   # water's prayer
place_voice(THEME_S, bar_t(B_V2 + 24), 0.55)                  # sleeper's vision
place_voice(THEME_W[:6], bar_t(B_STILL + 1), 0.42, 0.7, lp=1700)   # ghost
place_voice(THEME_A, bar_t(F_THEME), 0.5)                     # the destination
place_voice(THEME_A, bar_t(F_WAVE), 0.5)                      # the last wave
place_voice(THEME_A, bar_t(B_CUT - 12), 0.55, 0.95)           # ends at the cut
lay_L = reverb(lay_L, IR_L, wet=0.6)
lay_R = reverb(lay_R, IR_R, wet=0.6)
commit(lay_L, lay_R, 0.20)
print("duduk committed")

# ---------------------------------------------------------------- ney
lay_L = np.zeros(N)
lay_R = np.zeros(N)
for b0, notes in [(B_V2 + 18, [(74, 0.8), (75, 0.6), (74, 1.2)]),
                  (B_V2 + 26, [(79, 0.8), (78, 0.6), (74, 1.4)]),
                  (F_HIGH + 4, [(74, 0.8), (75, 0.6), (74, 1.2)]),
                  (F_HIGH + 12, [(79, 0.8), (78, 0.6), (74, 1.4)])]:
    v = ney_phrase(notes)
    add_at(lay_L, v, bar_t(b0), 0.7 * np.cos(0.35 * np.pi / 2))
    add_at(lay_R, v, bar_t(b0), 0.7 * np.sin(0.35 * np.pi / 2))
v = ney_phrase([(m + 12, d) for m, d in THEME_S[:6]])         # still-point ghost
add_at(lay_L, v, bar_t(B_STILL + 5), 0.6 * np.cos(0.65 * np.pi / 2))
add_at(lay_R, v, bar_t(B_STILL + 5), 0.6 * np.sin(0.65 * np.pi / 2))
v = ney_phrase([(m + 12, d) for m, d in THEME_A])             # doubles the wave
add_at(lay_L, v, bar_t(F_WAVE), 0.55 * np.cos(0.62 * np.pi / 2))
add_at(lay_R, v, bar_t(F_WAVE), 0.55 * np.sin(0.62 * np.pi / 2))
lay_L = reverb(lay_L, IR_L, wet=0.55)
lay_R = reverb(lay_R, IR_R, wet=0.55)
commit(lay_L, lay_R, 0.12)
print("ney committed")

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
        ([62, 63], B_STILL, B_BUILD + 4, 10.5, 0.8, 0.7),
        ([62, 69, 63], B_BUILD + 8, B_FUSION, 12.0, 0.8, 0.9),
        ([62, 69, 75], F_THEME, F_THEME + 16, 12.0, 0.55, 0.6),
        ([62, 69, 75], F_WAVE, B_CUT - 2, 12.0, 0.5, 0.55)]:
    sw = tremolo_strings(chord, (b1 - b0) * BAR, trem_hz=trem)
    add_at(lay_L, sw, bar_t(b0), gL)
    add_at(lay_R, sw, bar_t(b0), gR)
lay_L = reverb(lay_L, IR_L, wet=0.45)
lay_R = reverb(lay_R, IR_R, wet=0.45)
commit(lay_L, lay_R, 0.13)
print("strings committed")

# ---------------------------------------------------------------- zaps, risers,
# reverse cymbals, frame rolls

def make_zap():
    n = int(0.40 * SR)
    td = np.arange(n) / SR
    f_curve = 80.0 + 1900.0 * np.exp(-td * 18.0)
    x = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    x *= 1.0 + 0.5 * np.sin(2 * np.pi * 35.0 * td)
    x *= np.exp(-td * 8.0) * (1 - np.exp(-td / 0.002))
    return x / (np.max(np.abs(x)) + 1e-12)


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


def rev_cymbal(dur=1.6):
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = signal.sosfilt(signal.butter(2, 6000, "high", fs=SR, output="sos"),
                       rng.standard_normal(n))
    x *= np.exp(-td * 3.2)
    x = x[::-1]
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


ZAP = make_zap()
lay_L = np.zeros(N)
lay_R = np.zeros(N)
zap_bars = [B_V1 + 32, B_V1 + 36, B_V2 + 32, B_V2 + 36, B_V3 + 32, B_V3 + 36,
            B_FUSION, B_FUSION + 8, F_STACK, F_STACK + 8, F_THEME, F_THEME + 8,
            F_HIGH, F_HIGH + 8, F_WAVE, F_WAVE + 8, F_WAVE + 16, F_SPRINT]
for b in zap_bars:
    beat = float(rng.choice([0.0, 1.5, 3.5]))
    p = rng.uniform(0.2, 0.8)
    add_at(lay_L, ZAP, bar_t(b, beat), np.cos(p * np.pi / 2))
    add_at(lay_R, ZAP, bar_t(b, beat), np.sin(p * np.pi / 2))
lay_L = reverb(lay_L, IR_L, wet=0.35)
lay_R = reverb(lay_R, IR_R, wet=0.35)
commit(lay_L, lay_R, 0.08)
print("zaps committed")

lay_L = np.zeros(N)
lay_R = np.zeros(N)
for b0, dur_bars in [(B_INT1 + 2, 2), (B_INT2 + 2, 2), (B_BUILD + 20, 4),
                     (min(DIPB), 4), (min(FALSE_BARS), 2)]:
    rz = riser(dur_bars * BAR)
    add_at(lay_L, rz, bar_t(b0), 0.85)
    add_at(lay_R, rz, bar_t(b0), 1.0)
commit(lay_L, lay_R, 0.11)
print("risers committed")

lay_L[:] = 0.0
lay_R[:] = 0.0
for b0 in (B_V1, B_V2, B_V3, B_FUSION, F_WAVE):
    rc = rev_cymbal(1.8)
    add_at(lay_L, rc, bar_t(b0) - 1.8, 0.70)
    add_at(lay_R, rc, bar_t(b0) - 1.8, 0.80)
for b0, dur_b in [(B_BUILD + 22, 2), (B_V3 - 1, 1)]:
    fr = frame_roll(dur_b * BAR)
    add_at(lay_L, fr, bar_t(b0), 0.80)
    add_at(lay_R, fr, bar_t(b0), 0.88)
commit(lay_L, lay_R, 0.08)
print("reverse cymbals + frame rolls committed")

# ---------------------------------------------------------------- big hits

def explosion(dur=2.8, sub_f=50.0):
    n = int(dur * SR)
    td = np.arange(n) / SR
    brown = np.cumsum(rng.standard_normal(n))
    brown -= np.mean(brown)
    brown = signal.sosfilt(signal.butter(2, 150, "low", fs=SR, output="sos"),
                           brown)
    f = 22.0 + (sub_f - 22.0) * np.exp(-td * 2.0)
    core = np.sin(2 * np.pi * np.cumsum(f) / SR)
    env = (1 - np.exp(-td / 0.08)) * np.exp(-td / 1.8)
    x = (0.7 * brown / (np.max(np.abs(brown)) + 1e-12) + 0.7 * core) * env
    return x / (np.max(np.abs(x)) + 1e-12)


lay_L = np.zeros(N)
lay_R = np.zeros(N)
for b, g in [(B_FUSION, 1.0), (min(FALSE_BARS), 1.0)]:        # arrival + false end
    ex = explosion(3.0, 50.0)
    add_at(lay_L, ex, bar_t(b), g)
    add_at(lay_R, ex, bar_t(b), g)
    add_at(lay_L, KICK_ST, bar_t(b), g)
    add_at(lay_R, KICK_ST, bar_t(b), g)
commit(lay_L, lay_R, 0.22)
print("detonations committed")

# ---------------------------------------------------------------- THE CUT
# One final stab on the downbeat of bar 292, then every layer is silenced —
# except the wind, which is restored below and plays the album out alone.
cut_i = int(bar_t(B_CUT) * SR)
mix_L[cut_i:] = 0.0
mix_R[cut_i:] = 0.0

stab_L = np.zeros(N)
stab_R = np.zeros(N)
add_at(stab_L, KICK_ST, bar_t(B_CUT), 1.05)
add_at(stab_R, KICK_ST, bar_t(B_CUT), 1.05)
add_at(stab_L, BOOM, bar_t(B_CUT), 1.00)
add_at(stab_R, BOOM, bar_t(B_CUT), 1.00)
ex = explosion(3.5, 55.0)
add_at(stab_L, ex, bar_t(B_CUT), 0.85)
add_at(stab_R, ex, bar_t(B_CUT), 0.85)
commit(stab_L, stab_R, 0.30)
del stab_L, stab_R
print("final stab committed")

# The wind returns to full presence over 4 s (it was ducked by `calm`) and
# carries the last 45 s alone: the first sound of the album is the last.
coda_ramp = np.clip((t[cut_i:] - t[cut_i]) / 4.0, 0, 1)
g_wind = calm[cut_i] + (1.0 - calm[cut_i]) * coda_ramp
mix_L[cut_i:] += windw_L[cut_i:] * g_wind
mix_R[cut_i:] += windw_R[cut_i:] * g_wind
del windw_L, windw_R, coda_ramp, g_wind
print("wind restored for the coda")

# ---------------------------------------------------------------- master
del lay_L, lay_R
sos_shelf = signal.butter(2, 3000, "high", fs=SR, output="sos")
mix_L += 0.24 * signal.sosfilt(sos_shelf, mix_L)
mix_R += 0.24 * signal.sosfilt(sos_shelf, mix_R)
sos_sub = signal.butter(2, 95, "low", fs=SR, output="sos")
mix_L += 0.34 * signal.sosfilt(sos_sub, mix_L)
mix_R += 0.34 * signal.sosfilt(sos_sub, mix_R)
sos_deep = signal.butter(2, 55, "low", fs=SR, output="sos")
mix_L += 0.30 * signal.sosfilt(sos_deep, mix_L)
mix_R += 0.30 * signal.sosfilt(sos_deep, mix_R)
print("master shelves applied (high + low + deep)")

fade(mix_L, fade_in=6.0, fade_out=14.0)
fade(mix_R, fade_in=6.0, fade_out=14.0)

peak = max(np.max(np.abs(mix_L)), np.max(np.abs(mix_R))) + 1e-12
mix_L = np.tanh(1.38 * mix_L / peak) / np.tanh(1.38) * 0.88
mix_R = np.tanh(1.38 * mix_R / peak) / np.tanh(1.38) * 0.88

stereo = np.empty((N, 2))
stereo[:, 0] = mix_L
stereo[:, 1] = mix_R
pcm = (stereo * 32767.0).astype(np.int16)

OUT_DIR = "/workspace/music"
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, "kwisatz_haderach.wav")
with wave.open(OUT, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())

print(f"\nCreated: {os.path.abspath(OUT)}")
print(f"Duration: {N / SR:.1f} s  |  {SR} Hz stereo, 16-bit PCM  |  "
      f"{BPM:.0f} BPM  |  {N_LAYERS} committed layers")

SECTIONS = [("intro: wind + tick + kick staircase", 0.0, bar_t(B_V1)),
            ("VISION 1 — WATER", bar_t(B_V1), bar_t(B_INT1)),
            ("interrupt 1: tick + heartbeat", bar_t(B_INT1), bar_t(B_V2)),
            ("VISION 2 — SLEEPER", bar_t(B_V2), bar_t(B_INT2)),
            ("interrupt 2", bar_t(B_INT2), bar_t(B_V3)),
            ("VISION 3 — ARRAKEEN", bar_t(B_V3), bar_t(B_STILL)),
            ("the still point", bar_t(B_STILL), bar_t(B_BUILD)),
            ("the long build", bar_t(B_BUILD), bar_t(B_FUSION)),
            ("FUSION: engines fuse", bar_t(B_FUSION), bar_t(F_STACK)),
            ("FUSION: the album stack", bar_t(F_STACK), bar_t(min(DIPA))),
            ("  dip A: kick + chant + tick", bar_t(min(DIPA)), bar_t(F_THEME)),
            ("FUSION: Theme A over the machine", bar_t(F_THEME), bar_t(min(DIPB))),
            ("  dip B: bass + hats + riser", bar_t(min(DIPB)), bar_t(F_HIGH)),
            ("FUSION: high phase", bar_t(F_HIGH), bar_t(min(FALSE_BARS))),
            ("  FALSE ENDING", bar_t(min(FALSE_BARS)), bar_t(F_WAVE)),
            ("THE LAST WAVE", bar_t(F_WAVE), bar_t(B_CUT)),
            ("coda: the wind alone", bar_t(B_CUT), DURATION)]
print("Section map + per-section RMS:")
rms_by_name = {}
for name, t0, t1 in SECTIONS:
    i0, i1 = int(t0 * SR), min(N, int(t1 * SR))
    rms = np.sqrt(np.mean(mix_L[i0:i1] ** 2 + mix_R[i0:i1] ** 2) / 2)
    rms_by_name[name] = rms
    print(f"  {t0:6.1f} s  rms {rms:.3f}  {name}")
groove_secs = [n for n in rms_by_name if n.startswith(("VISION", "FUSION", "THE LAST"))]
loudest = max(groove_secs, key=lambda n: rms_by_name[n])
print(f"Loudest groove section: {loudest} (rms {rms_by_name[loudest]:.3f})")
if loudest != "THE LAST WAVE":
    print("WARNING: the last wave is not the loudest section — rebalance!")
