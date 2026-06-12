#!/usr/bin/env python3
"""
generate_maker_comes.py — "The Maker Comes" (~7:20). Extension of
night_pursuit.wav, built from user feedback on that track: the climax
material at 2:50 ("now it really starts!") becomes the MAIN material here,
developed into a long-form story, and the track finally arrives at the
worm-strike ending the short track stopped at. The sparse stalking intro
that read as "odd" is gone — after ten seconds of wind the groove starts
at full commitment.

The story: the hunt never stopped. All that drumming on the open sand has
been heard by something far older than any hunter — and seven minutes of
rhythm is exactly what it takes for a Maker to arrive.

  0:00  Wind + drone (crossfades from night_pursuit's coda), a roll and a
        riser — and at 0:10 the full pursuit groove in D, Theme A high on
        the oud, tremolo strings, war drums. No warm-up.
  1:05  Episode — half-time. A Sardaukar throat chant (new) rises out of
        the bass; a ney flute (new) floats Theme C above it. The hunters
        regroup in the rocks. Distant detonations.
  2:05  Relaunch: full groove again, Theme C driven on the oud, the duduk
        answering with Theme A. Same engine, new melody — development,
        not repetition.
  3:01  Breakdown callback: tick + heartbeat + the lone flat second.
  3:19  Cornered in G (same pitch set, darker gravity): Theme B, saidi
        drums — and this time the chant joins underneath. Bigger.
  4:05  THE LONG CLIMAX — back to D, five 8-bar waves, each adding a
        layer: strings+oud / +duduk / +ney / +chant / +fills everywhere.
  5:38  False ending: one huge hit, then nothing but wind and the tick,
        still counting — and the groove slams back for
  5:42  the final sprint, the fastest music in the track —
  6:19  until the sand erupts. The Maker takes the field. Extended coda:
        receding worm passes, the duduk lament, a ney echo, one last
        chanted breath. The desert always wins.

Output: /workspace/music/the_maker_comes.wav (stereo, 44100 Hz, 16-bit).
"""

import os
import wave
import numpy as np
from scipy import signal

SR = 44100
DURATION = 440.0
N = int(SR * DURATION)
t = np.arange(N) / SR

rng = np.random.default_rng(2024)    # year Part Two arrived

BPM = 104.0
BEAT = 60.0 / BPM
BAR = BEAT * 4
GRID0 = 10.0                          # bar 0: the groove starts here


def bar_t(b, beat=0.0):
    return GRID0 + b * BAR + beat * BEAT


# section boundaries, in bars
B_A1 = 0          # full groove, no melody — establish
B_A2 = 8          # Theme A high on the oud (the 2:50 material)
B_A3 = 16         # Theme A on the duduk, oud riff
B_EP1 = 24        # episode: half-time, chant + ney Theme C
B_ROLL = 48       # 2-bar relaunch (roll + riser)
B_B = 50          # full groove: Theme C on oud, duduk answers
B_BREAK = 74      # breakdown callback: tick + heartbeat
B_G = 82          # cornered in G — Theme B, saidi, chant joins
B_CLIMAX = 102    # the long climax: 5 waves x 8 bars
B_FALSE = 142     # false ending: one hit, wind + tick only
B_SPRINT = 144    # final sprint
B_STRIKE = 160    # the Maker arrives; groove dies


# ---------------------------------------------------------------- helpers

def midi_to_hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def fade(x, fade_in=8.0, fade_out=18.0):
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


def karplus_strong(freq, dur, damp=0.992):
    n = int(dur * SR)
    period = max(2, int(SR / freq))
    buf = rng.uniform(-1, 1, period)
    buf = np.convolve(buf, np.ones(3) / 3, mode="same")
    out = np.empty(n)
    prev = buf.copy()
    i = 0
    while i < n:
        m = min(period, n - i)
        out[i:i + m] = prev[:m]
        prev = damp * 0.5 * (prev + np.roll(prev, 1))
        i += m
    return out


def glide_curve(notes, n):
    """Portamento frequency curve for a contiguous (midi, dur_s) phrase."""
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
    """Duduk-like voice with portamento + vibrato."""
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
    """NEW — ney flute: nearly pure tone + air. Breathy 1.2-4 kHz noise
    rides the same envelope, faster shallower vibrato than the duduk."""
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
    """NEW — Sardaukar throat chant: harmonic-rich glottal source through
    three parallel formant bands (dark 'oh'), guttural amplitude pulse,
    sub-octave underneath for the throat-singing weight."""
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


# ---------------------------------------------------------------- mix bus
# 7+ minutes of stereo float64 layers would not fit in RAM all at once, so
# each layer is normalized and committed to the mix immediately, then freed.

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


# energy curve: ducks the calm layers, snaps down at the cuts
energy_pts = [(0.0, 0.0), (GRID0 - 0.5, 0.0), (GRID0 + 0.5, 0.85),
              (bar_t(B_EP1), 0.85), (bar_t(B_EP1) + 1.5, 0.55),
              (bar_t(B_B), 0.55), (bar_t(B_B) + 0.5, 0.90),
              (bar_t(B_BREAK), 0.90), (bar_t(B_BREAK) + 0.3, 0.30),
              (bar_t(B_G), 0.30), (bar_t(B_G) + 0.5, 0.85),
              (bar_t(B_CLIMAX), 0.85), (bar_t(B_CLIMAX) + 0.5, 0.95),
              (bar_t(B_CLIMAX + 24), 1.0),
              (bar_t(B_FALSE), 1.0), (bar_t(B_FALSE) + 0.3, 0.20),
              (bar_t(B_SPRINT), 0.20), (bar_t(B_SPRINT) + 0.4, 1.0),
              (bar_t(B_STRIKE), 1.0), (bar_t(B_STRIKE) + 2.0, 0.10),
              (DURATION, 0.0)]
energy = np.interp(t, [p[0] for p in energy_pts], [p[1] for p in energy_pts])
calm = 1.0 - 0.45 * energy


# ---------------------------------------------------------------- wind & drone
# Same recipe as the other Dune tracks so everything crossfades.

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
commit(wind_L, wind_R, 0.26, env=calm)
del whoosh, hiss, wind_L, wind_R

f_D1 = midi_to_hz(26)
breath = 0.7 + 0.3 * np.sin(2 * np.pi * 0.012 * t + 1.0)
drone = (np.sin(2 * np.pi * f_D1 * t) +
         0.55 * np.sin(2 * np.pi * f_D1 * 2 * t + 0.4) +
         0.30 * np.sin(2 * np.pi * f_D1 * 3 * t) +
         0.30 * np.sin(2 * np.pi * f_D1 * 3.003 * t))
drone *= breath
drone /= np.max(np.abs(drone))
commit(drone, drone, 0.22, env=calm)
del drone, breath
print("wind + drone committed")


# ---------------------------------------------------------------- tick-tock
# The clock runs from the first groove bar to the strike — INCLUDING the
# false-ending gap, where it is suddenly the loudest thing left.

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

lay_L = np.zeros(N)
lay_R = np.zeros(N)
for b in range(B_STRIKE):
    if b < B_EP1:
        g = 0.35
    elif b < B_ROLL:
        g = 0.45
    elif B_BREAK <= b < B_G:
        g = 0.65
    elif B_FALSE <= b < B_SPRINT:
        g = 0.70                       # alone in the false ending
    else:
        g = 0.32
    for e in range(8):
        st = bar_t(b, e * 0.5)
        if e % 2 == 0:
            add_at(lay_L, TICK, st, g)
            add_at(lay_R, TICK, st, g * 0.55)
        else:
            add_at(lay_L, TOCK, st, g * 0.50)
            add_at(lay_R, TOCK, st, g * 0.85)
commit(lay_L, lay_R, 0.10)
print("tick committed")


# ---------------------------------------------------------------- bass pulse

def bass_note(midi, dur):
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * td) + 0.35 * np.sin(2 * np.pi * 2 * f * td + 0.3)
    x = np.tanh(1.6 * x)
    env = (1 - np.exp(-td / 0.005)) * np.clip((dur - td) / 0.05, 0, 1)
    return x * env


D2, C2, Eb2, D3 = 38, 36, 39, 50
G1, FS1, Bb1 = 31, 30, 34

B16 = {m: bass_note(m, BEAT * 0.24) for m in (D2, C2, Eb2, D3, G1, FS1, Bb1)}
B2 = {m: bass_note(m, BEAT * 1.9) for m in (D2, C2)}

GATE16 = [1.0, 0, 0.7, 0, 1.0, 0, 0.7, 0.7,
          1.0, 0, 0.7, 0, 1.0, 0.7, 0, 0.7]
SPRINT16 = [1.0, 0.6, 0.7, 0.6, 1.0, 0.6, 0.7, 0.7,
            1.0, 0.6, 0.7, 0.6, 1.0, 0.7, 0.8, 0.9]

lay_L[:] = 0.0
lay_R[:] = 0.0


def bass_bar_16(b, root, walk, gates, octave_steps=()):
    last_of_four = b % 4 == 3
    for s, g in enumerate(gates):
        if g == 0:
            continue
        m = root
        if last_of_four and s >= 12:
            m = walk[s - 12]
        elif s in octave_steps:
            m = root + 12
        add_at(lay_L, B16[m], bar_t(b, s * 0.25), g)
        add_at(lay_R, B16[m], bar_t(b, s * 0.25), g)


for b in range(B_STRIKE):
    if B_BREAK <= b < B_G or B_FALSE <= b < B_SPRINT:
        continue                                      # cuts
    if B_EP1 <= b < B_ROLL:
        # episode: half notes, breathing room under the chant. Gain well
        # below the gated sections: sustained sub carries far more RMS
        # than 16ths and would otherwise out-weigh the climax.
        m = C2 if b % 4 == 3 else D2
        for beat in (0.0, 2.0):
            add_at(lay_L, B2[m], bar_t(b, beat), 0.45)
            add_at(lay_R, B2[m], bar_t(b, beat), 0.45)
    elif B_G <= b < B_CLIMAX:
        bass_bar_16(b, G1, [FS1, Bb1, G1, G1], GATE16)
    elif B_CLIMAX <= b < B_FALSE:
        wave_i = (b - B_CLIMAX) // 8
        octs = (7, 13) if wave_i >= 2 else ()
        bass_bar_16(b, D2, [C2, Eb2, D2, D2], GATE16, octave_steps=octs)
    elif b >= B_SPRINT:
        bass_bar_16(b, D2, [C2, Eb2, D2, D2], SPRINT16, octave_steps=(4, 12))
    else:
        bass_bar_16(b, D2, [C2, Eb2, D2, D2], GATE16)
commit(lay_L, lay_R, 0.30)
print("bass committed")


# ---------------------------------------------------------------- war drum

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
for b in range(B_STRIKE):
    if B_BREAK <= b < B_G or B_FALSE <= b < B_SPRINT:
        continue
    if B_EP1 <= b < B_ROLL:
        hits = [(0.0, 0.8), (2.0, 0.5)]               # half-time
    elif B_G <= b < B_CLIMAX:
        hits = [(0.0, 1.0), (0.5, 0.7), (2.5, 0.8)]   # cornered doubles
    elif B_CLIMAX <= b < B_FALSE:
        wave_i = (b - B_CLIMAX) // 8
        if wave_i < 2:
            hits = [(0.0, 1.0), (0.5, 0.7), (2.5, 0.8)]
        else:
            hits = [(0.0, 1.0), (1.0, 0.6), (2.0, 0.8), (2.5, 0.6), (3.0, 0.85)]
        if (b - B_CLIMAX) % 8 == 7:
            hits += [(3.5, 0.8), (3.75, 1.0)]          # wave pickup
    elif b >= B_SPRINT:
        hits = [(0.0, 0.9), (1.0, 0.6), (2.0, 0.75), (3.0, 0.6), (3.75, 0.5)]
        if b >= B_STRIKE - 2:
            hits += [(3.25, 0.7), (3.5, 0.85)]
    else:
        hits = [(0.0, 0.95), (1.75, 0.5), (3.0, 0.7)] # chase pattern
    for beat, g in hits:
        add_at(lay_L, WAR, bar_t(b, beat), g)
        add_at(lay_R, WAR, bar_t(b, beat), g)

# triple hits: the false ending and the strike itself
for b0 in (B_FALSE, B_STRIKE):
    for k, g in [(0, 1.0), (1, 0.85), (2, 1.0)]:
        add_at(lay_L, WAR, bar_t(b0, k * 0.5), g)
        add_at(lay_R, WAR, bar_t(b0, k * 0.5), g)
commit(lay_L, lay_R, 0.34)
print("war drums committed")


# ---------------------------------------------------------------- frame drum

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
for b in range(B_STRIKE):
    if B_EP1 <= b < B_B or B_BREAK <= b < B_G or B_FALSE <= b < B_SPRINT:
        continue
    skips = [(3, 0.30), (7, 0.34), (10, 0.26), (15, 0.38)]
    if b >= B_SPRINT:                                  # doubled skips
        skips += [(5, 0.24), (13, 0.28)]
    for s, g in skips:
        p = 0.35 if s in (3, 10, 5) else 0.65
        add_at(lay_L, FRAME, bar_t(b, s * 0.25), g * np.cos(p * np.pi / 2))
        add_at(lay_R, FRAME, bar_t(b, s * 0.25), g * np.sin(p * np.pi / 2))

# rolls: every launch gets one
ROLLS = [(GRID0 - 3.2, 2.4, 1.0),                      # into the opening groove
         (bar_t(B_ROLL), 2 * BAR, 1.0),                # relaunch
         (bar_t(B_G - 1), BAR, 0.8),                   # into G
         (bar_t(B_CLIMAX - 2), 2 * BAR, 1.0),          # into the climax
         (bar_t(B_FALSE) + 0.5 * BAR + BAR, 0.5 * BAR, 0.9),  # sprint pickup
         (bar_t(B_STRIKE - 1), BAR, 1.0)]              # into the strike
# wave boundaries inside the climax: half-bar rolls
for w in range(1, 5):
    ROLLS.append((bar_t(B_CLIMAX + 8 * w) - 0.5 * BAR, 0.5 * BAR, 0.7))
for start_s, dur_s, g in ROLLS:
    roll = frame_roll(dur_s)
    add_at(lay_L, roll, start_s, g * 0.9)
    add_at(lay_R, roll, start_s, g)
commit(lay_L, lay_R, 0.12)
print("frame drum committed")


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
SAIDI = {0: "D", 2: "T", 6: "D", 8: "D", 12: "T"}

lay_L[:] = 0.0
lay_R[:] = 0.0
for b in range(B_STRIKE):
    if B_EP1 <= b < B_B or B_BREAK <= b < B_G or B_FALSE <= b < B_SPRINT:
        continue
    if b < B_EP1 or b < B_BREAK:
        pattern, ghosts = MAQSUM, 0.30
    if B_G <= b:
        pattern, ghosts = SAIDI, 0.20
    if B_CLIMAX <= b:
        ghosts = 0.20 + 0.05 * ((b - B_CLIMAX) // 8)   # busier per wave
    if b >= B_SPRINT:
        pattern, ghosts = SAIDI, 0.50
    fill_every = 2 if (b >= B_SPRINT or
                       (B_CLIMAX <= b and (b - B_CLIMAX) // 8 == 4)) else 4
    fill_bar = b % fill_every == fill_every - 1
    for s in range(16):
        st = bar_t(b, s * 0.25)
        stroke = pattern.get(s)
        if fill_bar and s >= 10:
            g = 0.45 + 0.55 * (s - 10) / 5.0
            add_at(lay_L, TEK, st, g * 0.9)
            add_at(lay_R, TEK, st, g * 0.7)
            continue
        if stroke == "D":
            add_at(lay_L, DOUM, st, 1.0)
            add_at(lay_R, DOUM, st, 1.0)
        elif stroke == "T":
            p = 0.35 if s in (2, 12) else 0.65
            add_at(lay_L, TEK, st, np.cos(p * np.pi / 2))
            add_at(lay_R, TEK, st, np.sin(p * np.pi / 2))
        elif s % 2 == 1 and rng.random() < ghosts:
            add_at(lay_L, KA, st, 0.6)
            add_at(lay_R, KA, st, 0.5)
commit(lay_L, lay_R, 0.22)
print("darbuka committed")


# ---------------------------------------------------------------- oud
# Theme A is the 2:50 material (played an octave up throughout this track);
# Theme C is the new counter-melody, traded between ney and oud.

THEME_A = [
    (50, 0.0, 1), (54, 1.0, 0.5), (51, 1.5, 0.5), (50, 2.0, 1), (48, 3.0, 1),
    (50, 4.0, 1.5), (51, 5.5, 0.5), (54, 6.0, 1), (57, 7.0, 1),
    (55, 8.0, 1), (54, 9.0, 0.5), (51, 9.5, 0.5), (50, 10.0, 2),
    (48, 12.0, 1), (51, 13.0, 1), (50, 14.0, 2),
]
THEME_A_VAR = THEME_A[:-3] + [(51, 12.0, 1), (54, 13.0, 1), (57, 14.0, 2)]

THEME_C = [
    (57, 0.0, 1.5), (58, 1.5, 0.5), (57, 2.0, 1), (55, 3.0, 1),
    (54, 4.0, 2), (51, 6.0, 1), (54, 7.0, 1),
    (50, 8.0, 2), (55, 10.0, 1), (57, 11.0, 1),
    (58, 12.0, 1.5), (57, 13.5, 0.5), (55, 14.0, 2),
]
THEME_C_VAR = THEME_C[:-3] + [(58, 12.0, 1), (62, 13.0, 1), (57, 14.0, 2)]

CHASE_RIFF = [50, 50, 48, 50, 51, 50, 54, 55]
G_RIFF = [55, 55, 54, 55, 58, 55, 62, 63]

lay_L[:] = 0.0
lay_R[:] = 0.0
plucks = {}


def pluck(m, dur_beats):
    dur = max(0.3, min(1.2, dur_beats * BEAT))
    key = (m, round(dur, 2))
    if key not in plucks:
        f = midi_to_hz(m)
        damp = 0.995 if dur > 0.7 else 0.992
        p = karplus_strong(f, dur, damp) + \
            0.6 * karplus_strong(f * 1.004, dur, damp)
        plucks[key] = p / (np.max(np.abs(p)) + 1e-12)
    return plucks[key]


def play_theme(theme, t0, transpose=0, gain=1.0):
    for m, beat, dur in theme:
        x = pluck(m + transpose, dur)
        add_at(lay_L, x, t0 + beat * BEAT, gain * 0.95)
        add_at(lay_R, x, t0 + beat * BEAT, gain * 0.8)


def play_riff(b0, b1, riff, transpose=0, gain=1.0, jump_p=0.10):
    for b in range(b0, b1):
        for e in range(8):
            m = riff[e] + transpose
            if rng.random() < jump_p and e in (2, 6):
                m += 12
            g = (1.0 if e % 2 == 0 else 0.75) * gain
            x = pluck(m, 0.95)
            add_at(lay_L, x, bar_t(b, e * 0.5), g * 0.95)
            add_at(lay_R, x, bar_t(b, e * 0.5), g * 0.8)


# A: the 2:50 material from the first melodic bar
play_theme(THEME_A, bar_t(B_A2), transpose=12)
play_theme(THEME_A_VAR, bar_t(B_A2 + 4), transpose=12)
play_riff(B_A3, B_EP1, CHASE_RIFF)
# B: Theme C driven on the oud, then riff under the duduk, then C varied
play_theme(THEME_C, bar_t(B_B))
play_theme(THEME_C_VAR, bar_t(B_B + 4))
play_riff(B_B + 8, B_B + 16, CHASE_RIFF)
play_theme(THEME_C, bar_t(B_B + 16), transpose=12, gain=0.9)
play_theme(THEME_C_VAR, bar_t(B_B + 20), transpose=12, gain=0.9)
# G: riff re-rooted on G
play_riff(B_G + 4, B_CLIMAX, G_RIFF, gain=0.8)
# climax: Theme A high in waves 1-2, riff with wild jumps after
play_theme(THEME_A, bar_t(B_CLIMAX), transpose=12)
play_theme(THEME_A_VAR, bar_t(B_CLIMAX + 4), transpose=12)
play_theme(THEME_A, bar_t(B_CLIMAX + 8), transpose=12)
play_theme(THEME_A_VAR, bar_t(B_CLIMAX + 12), transpose=12)
play_riff(B_CLIMAX + 16, B_FALSE, CHASE_RIFF, transpose=12, jump_p=0.20)
# sprint: riff high and relentless
play_riff(B_SPRINT, B_STRIKE, CHASE_RIFF, transpose=12, jump_p=0.25)
commit(lay_L, lay_R, 0.20)
print("oud committed")


# ---------------------------------------------------------------- duduk

lay_L[:] = 0.0
lay_R[:] = 0.0


def place_voice(notes, t0, pan_pos, gain=1.0, lp=2200):
    v = voice_phrase(notes, lp=lp)
    add_at(lay_L, v, t0, gain * np.cos(pan_pos * np.pi / 2))
    add_at(lay_R, v, t0, gain * np.sin(pan_pos * np.pi / 2))


b2s = lambda nb: nb * BEAT

DUDUK_THEME_A = [(62, b2s(2)), (66, b2s(1)), (63, b2s(1)), (62, b2s(2)),
                 (60, b2s(2)), (62, b2s(3)), (63, b2s(1)), (66, b2s(2)),
                 (69, b2s(2)), (67, b2s(2)), (66, b2s(1)), (63, b2s(1)),
                 (62, b2s(4)), (60, b2s(2)), (63, b2s(2)), (62, b2s(4))]
THEME_B_1 = [(67, b2s(2)), (70, b2s(1)), (69, b2s(1)), (67, b2s(2)),
             (66, b2s(2)), (67, b2s(4)), (70, b2s(2)), (72, b2s(2)),
             (74, b2s(4)), (72, b2s(2)), (70, b2s(2)), (69, b2s(2)),
             (67, b2s(4))]
THEME_B_2 = [(74, b2s(2)), (75, b2s(1)), (74, b2s(1)), (72, b2s(2)),
             (70, b2s(2)), (69, b2s(2)), (67, b2s(2)), (66, b2s(2)),
             (67, b2s(5))]

place_voice(DUDUK_THEME_A, bar_t(B_A3), 0.45)
place_voice(DUDUK_THEME_A, bar_t(B_B + 8), 0.45)
place_voice([(63, 7.0), (62, 3.0)], bar_t(B_BREAK + 1), 0.5, 0.9, lp=1800)
place_voice(THEME_B_1, bar_t(B_G), 0.55)
place_voice(THEME_B_2, bar_t(B_G + 8), 0.42, 0.95)
place_voice(DUDUK_THEME_A, bar_t(B_CLIMAX + 8), 0.55)       # wave 2
place_voice(DUDUK_THEME_A, bar_t(B_CLIMAX + 24), 0.40)      # wave 4
# coda lament — the ending the whole track has been walking toward
place_voice([(74, 1.7), (72, 1.2), (70, 1.2), (69, 1.7), (67, 1.7),
             (66, 1.7), (63, 1.7), (62, 4.5)],
            bar_t(B_STRIKE) + 8.0, 0.5, 1.0, lp=1900)

lay_L = reverb(lay_L, IR_L, wet=0.65)
lay_R = reverb(lay_R, IR_R, wet=0.65)
commit(lay_L, lay_R, 0.20)
print("duduk committed")


# ---------------------------------------------------------------- ney
# NEW instrument: floats Theme C above the texture — episode, climax
# wave 3+, and an echo in the coda.

lay_L = np.zeros(N)
lay_R = np.zeros(N)

NEY_THEME_C = [(m + 12, dur * BEAT) for m, beat, dur in THEME_C]
NEY_THEME_C_VAR = [(m + 12, dur * BEAT) for m, beat, dur in THEME_C_VAR]


def place_ney(notes, t0, pan_pos, gain=1.0):
    v = ney_phrase(notes)
    add_at(lay_L, v, t0, gain * np.cos(pan_pos * np.pi / 2))
    add_at(lay_R, v, t0, gain * np.sin(pan_pos * np.pi / 2))


place_ney(NEY_THEME_C, bar_t(B_EP1 + 4), 0.58)
place_ney(NEY_THEME_C_VAR, bar_t(B_EP1 + 14), 0.40)
place_ney(NEY_THEME_C, bar_t(B_CLIMAX + 16), 0.60)          # wave 3
place_ney(NEY_THEME_C_VAR, bar_t(B_CLIMAX + 28), 0.38)      # wave 4/5
# coda echo, answering the duduk from far off
place_ney([(74, 1.5), (72, 1.5), (69, 2.0), (67, 3.0)],
          bar_t(B_STRIKE) + 24.0, 0.65, 0.8)

lay_L = reverb(lay_L, IR_L, wet=0.55)
lay_R = reverb(lay_R, IR_R, wet=0.55)
commit(lay_L, lay_R, 0.15)
print("ney committed")


# ---------------------------------------------------------------- chant
# NEW instrument: the Sardaukar pulse. Episode, the G act, climax waves
# 4-5, and one last breath in the coda.

lay_L = np.zeros(N)
lay_R = np.zeros(N)

CH_LONG = {m: chant_note(m, 1.4 * BEAT) for m in (38, 36, 43)}
CH_SHORT = {m: chant_note(m, 0.85 * BEAT) for m in (38, 36, 43)}


def chant_bar(b, root):
    for beat, g, bank in [(0.0, 1.0, CH_LONG), (2.0, 0.8, CH_SHORT),
                          (3.0, 0.8, CH_SHORT)]:
        add_at(lay_L, bank[root], bar_t(b, beat), g * 0.9)
        add_at(lay_R, bank[root], bar_t(b, beat), g)


for b in range(B_EP1 + 2, B_ROLL):
    chant_bar(b, 36 if b % 4 == 3 else 38)
for b in range(B_G + 8, B_CLIMAX):
    chant_bar(b, 43)
for b in range(B_CLIMAX + 24, B_FALSE):
    chant_bar(b, 36 if b % 4 == 3 else 38)
# the last breath, alone in the aftermath
last = chant_note(38, 6.0, pulse=4.0)
add_at(lay_L, last, bar_t(B_STRIKE) + 34.0, 0.7)
add_at(lay_R, last, bar_t(B_STRIKE) + 34.0, 0.7)

lay_L = reverb(lay_L, IR_L, wet=0.45)
lay_R = reverb(lay_R, IR_R, wet=0.45)
commit(lay_L, lay_R, 0.18)
print("chant committed")


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
        ([62, 63], B_A1, B_EP1, 10.5, 0.8, 0.7),            # opening friction
        ([62, 63], B_B, B_BREAK, 10.5, 0.6, 0.55),
        ([55, 62, 63], B_G, B_CLIMAX, 10.5, 0.9, 0.8),      # G minor + b6
        ([62, 69, 63], B_CLIMAX, B_CLIMAX + 20, 11.0, 0.8, 0.85),
        ([62, 69, 75], B_CLIMAX + 20, B_FALSE, 12.0, 0.8, 0.9),
        ([62, 69, 75], B_SPRINT, B_STRIKE, 13.0, 0.85, 0.95)]:
    sw = tremolo_strings(chord, (b1 - b0) * BAR, trem_hz=trem)
    add_at(lay_L, sw, bar_t(b0), gL)
    add_at(lay_R, sw, bar_t(b0), gR)

lay_L = reverb(lay_L, IR_L, wet=0.45)
lay_R = reverb(lay_R, IR_R, wet=0.45)
commit(lay_L, lay_R, 0.15)
print("strings committed")


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


lay_L = np.zeros(N)
lay_R = np.zeros(N)
for start_s, dur_s in [(GRID0 - 4.0, 4.0),
                       (bar_t(B_ROLL), 2 * BAR),
                       (bar_t(B_CLIMAX - 2), 2 * BAR),
                       (bar_t(B_FALSE) + 0.5 * BAR, 1.5 * BAR),
                       (bar_t(B_STRIKE - 2), 2 * BAR)]:
    rz = riser(dur_s)
    add_at(lay_L, rz, start_s, 0.85)
    add_at(lay_R, rz, start_s, 1.0)
commit(lay_L, lay_R, 0.12)
print("risers committed")


# ---------------------------------------------------------------- heartbeat

nk = int(0.35 * SR)
tk = np.arange(nk) / SR
fk = 36.0 + 60.0 * np.exp(-tk * 16.0)
SUBKICK = np.sin(2 * np.pi * np.cumsum(fk) / SR) * \
    np.exp(-tk * 10.0) * (1 - np.exp(-tk * 400))

lay_L = np.zeros(N)
lay_R = np.zeros(N)
for b in range(B_BREAK, B_G):
    for beat, g in [(0.0, 1.0), (0.75, 0.6), (2.0, 1.0), (2.75, 0.6)]:
        add_at(lay_L, SUBKICK, bar_t(b, beat), g)
        add_at(lay_R, SUBKICK, bar_t(b, beat), g)
commit(lay_L, lay_R, 0.26)
print("heartbeat committed")


# ---------------------------------------------------------------- booms
# Distant detonations during the episode and the B section — the war is
# never far — plus the false-ending hit.

def make_boom(dur=7.0):
    n = int(dur * SR)
    tb = np.arange(n) / SR
    sos_boom = signal.butter(4, 150, "low", fs=SR, output="sos")
    brown = np.cumsum(rng.standard_normal(n))
    brown -= np.linspace(brown[0], brown[-1], n)
    brown /= np.max(np.abs(brown)) + 1e-12
    env = (1 - np.exp(-tb / 0.08)) * np.exp(-tb / 1.8)
    body = signal.sosfilt(sos_boom, brown * env)
    fsub = 22.0 + 38.0 * np.exp(-tb * 1.6)
    core = np.sin(2 * np.pi * np.cumsum(fsub) / SR) * env
    return body * 0.7 + core * 0.6


lay_L = np.zeros(N)
lay_R = np.zeros(N)
for b, g in [(B_EP1 + 6, 0.30), (B_EP1 + 16, 0.35),
             (B_B + 6, 0.35), (B_B + 18, 0.30),
             (B_CLIMAX + 30, 0.50)]:
    bm = make_boom()
    p = rng.uniform(0.3, 0.7)
    add_at(lay_L, bm, bar_t(b, rng.uniform(0, 2)), g * np.cos(p * np.pi / 2))
    add_at(lay_R, bm, bar_t(b, rng.uniform(0, 2)), g * np.sin(p * np.pi / 2))
# the false-ending detonation
bm = make_boom()
add_at(lay_L, bm, bar_t(B_FALSE), 1.0)
add_at(lay_R, bm, bar_t(B_FALSE), 1.0)

lay_L = reverb(lay_L, IR_L, wet=0.4)
lay_R = reverb(lay_R, IR_R, wet=0.4)
commit(lay_L, lay_R, 0.30)
print("booms committed")


# ---------------------------------------------------------------- the strike
# The Maker arrives: explosion + worm thumps, then passes receding into
# the deep desert under the coda.

lay_L = np.zeros(N)
lay_R = np.zeros(N)
T_STRIKE = bar_t(B_STRIKE)

n = int(8.0 * SR)
tb = np.arange(n) / SR
sos_boom = signal.butter(4, 150, "low", fs=SR, output="sos")
brown = np.cumsum(rng.standard_normal(n))
brown -= np.linspace(brown[0], brown[-1], n)
brown /= np.max(np.abs(brown)) + 1e-12
env = (1 - np.exp(-tb / 0.08)) * np.exp(-tb / 2.2)
body = signal.sosfilt(sos_boom, brown * env)
fsub = 22.0 + 38.0 * np.exp(-tb * 1.6)
core = np.sin(2 * np.pi * np.cumsum(fsub) / SR) * env
add_at(lay_L, body * 0.7 + core * 0.6, T_STRIKE, 1.0)
add_at(lay_R, body * 0.7 + core * 0.6, T_STRIKE, 1.0)

n = int(6.0 * SR)
tb = np.arange(n) / SR
f_curve = 27.0 + 28.0 * np.exp(-tb * 2.2)
env = np.exp(-tb * 1.1) * (1 - np.exp(-tb * 30))
thump = env * np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
sos_gr = signal.butter(4, 90, "low", fs=SR, output="sos")
shake = signal.sosfilt(sos_gr, rng.standard_normal(n)) * env * 0.6
for dt, g in [(2.5, 0.8), (10.0, 0.55), (19.0, 0.35), (30.0, 0.2)]:
    add_at(lay_L, thump + shake, T_STRIKE + dt, g)
    add_at(lay_R, thump + shake, T_STRIKE + dt, g)

lay_L = reverb(lay_L, IR_L, wet=0.4)
lay_R = reverb(lay_R, IR_R, wet=0.4)
commit(lay_L, lay_R, 0.42)
print("strike committed")


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
OUT = os.path.join(OUT_DIR, "the_maker_comes.wav")
with wave.open(OUT, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())

print(f"\nCreated: {os.path.abspath(OUT)}")
print(f"Duration: {N / SR:.1f} s  |  {SR} Hz stereo, 16-bit PCM  |  {BPM:.0f} BPM")
print("Section map:")
for name, b in [("full groove (the 2:50 material)", B_A1),
                ("Theme A high on oud", B_A2), ("Theme A on duduk", B_A3),
                ("episode: half-time, chant + ney Theme C", B_EP1),
                ("relaunch roll + riser", B_ROLL),
                ("B: Theme C on oud, duduk answers", B_B),
                ("breakdown callback", B_BREAK),
                ("cornered in G + chant", B_G),
                ("THE LONG CLIMAX (5 waves x 8 bars)", B_CLIMAX),
                ("false ending — wind + tick only", B_FALSE),
                ("final sprint", B_SPRINT),
                ("the Maker arrives", B_STRIKE)]:
    print(f"  {bar_t(b):6.1f} s  bar {b:3d}  {name}")
print(f"  {DURATION:6.1f} s  end (coda: duduk {bar_t(B_STRIKE)+8:.0f} s, "
      f"ney {bar_t(B_STRIKE)+24:.0f} s, last chant {bar_t(B_STRIKE)+34:.0f} s)")
