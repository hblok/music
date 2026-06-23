#!/usr/bin/env python3
"""
generate_night_pursuit.py — a chase across the desert at night. More
energetic than the previous tracks — relentless rhythm, not dance music.
Reference: the John Wick 3/4 scores (ticking-clock ostinati, pulsing bass,
percussion-driven momentum) transplanted into the Dune palette.

The track tells a story in five acts (no section repeats verbatim):

  I   Stillness   0:00  Arrakis wind + D1 drone (verbatim recipe, so it
                        crossfades with the other tracks); one duduk call —
                        the scout spots movement on the horizon.
  II  The Tick    0:18  A dry tick-tock clock starts (eighth notes), then a
                        gated sub-bass pulse and a skipping frame drum.
                        Half engaged: stalking, not yet running.
  III The Chase   0:55  Oud states Theme A over a light maqsum; the duduk
                        answers an octave up; a frame-drum roll and a riser
                        slam into the full pursuit — war drums, driving
                        16th-note bass, full darbuka.
      Breakdown   2:04  Everything cuts dead except the tick and a
                        heartbeat: the prey vanishes behind a dune.
  IV  Cornered    2:22  Tonal center shifts to G (D Phrygian dominant is
                        mode 5 of G harmonic minor — same pitches, darker
                        gravity). Theme B on the duduk, heavier saidi drum
                        pattern, tremolo strings.
  V   The Strike  2:50  Back to D for the climax — all layers, drum fills —
                        until at 3:08 the ground itself answers: a worm
                        strike kills the groove dead. Wind, drone, and a
                        descending duduk coda. The desert always wins.

Output: /workspace/music/night_pursuit.wav (stereo, 44100 Hz, 16-bit).
"""

import os
import wave
import numpy as np
from scipy import signal

SR = 44100
DURATION = 225.0
N = int(SR * DURATION)
t = np.arange(N) / SR

rng = np.random.default_rng(1984)    # year of the first Dune film

BPM = 104.0
BEAT = 60.0 / BPM
BAR = BEAT * 4
GRID0 = 18.0                          # bar 0 of the rhythmic grid


def bar_t(b, beat=0.0):
    """Absolute time of beat `beat` in bar `b` of the grid."""
    return GRID0 + b * BAR + beat * BEAT


# section boundaries, in bars (printed at the end)
B_PULSE = 8        # bass pulse + frame drum enter
B_THEME_A = 16     # oud states Theme A
B_THEME_A2 = 24    # duduk answer, darbuka enters
B_BUILD = 32       # frame-drum roll + riser (2 bars)
B_CHASE = 34       # full pursuit
B_BREAK = 46       # the cut: tick + heartbeat only
B_ACT4 = 54        # cornered — tonal center G
B_CLIMAX = 66      # back to D, everything
B_STRIKE = 74      # the worm strike; groove dies


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


def voice_phrase(notes, lp=2200):
    """Duduk-like voice: list of (midi, dur_s) with portamento + vibrato."""
    total = sum(d for _, d in notes) + 2.0
    n = int(total * SR)
    tt = np.arange(n) / SR
    f_target = np.zeros(n)
    edge = 0.0
    for m, d in notes:
        a, b = int(edge * SR), min(n, int((edge + d) * SR))
        f_target[a:b] = midi_to_hz(m)
        edge += d
    i_end = min(n - 1, int(edge * SR))
    f_target[i_end:] = f_target[i_end - 1]
    alpha = 1.0 - np.exp(-1.0 / (0.09 * SR))
    f_curve = signal.lfilter([alpha], [1.0, -(1.0 - alpha)],
                             f_target, zi=[f_target[0] * (1 - alpha)])[0]
    vib = 1.0 + 0.006 * np.sin(2 * np.pi * 5.2 * tt) * np.clip(tt / 1.2, 0, 1)
    phase = 2 * np.pi * np.cumsum(f_curve * vib) / SR
    env = np.minimum(np.clip(tt / 1.0, 0, 1),
                     np.clip((total - tt) / 2.0, 0, 1)) ** 1.5
    v = env * (np.sin(phase) + 0.40 * np.sin(2 * phase) +
               0.18 * np.sin(3 * phase) + 0.07 * np.sin(4 * phase))
    sos = signal.butter(2, lp, "low", fs=SR, output="sos")
    return signal.sosfilt(sos, v)


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


# ---------------------------------------------------------------- tick-tock
# The John Wick clock: a bone-dry alternating tick/tock in straight eighths,
# running from 18 s until the strike. It is the one constant of the hunt —
# everything else changes around it.

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

tick_L = np.zeros(N)
tick_R = np.zeros(N)

for b in range(B_STRIKE):
    # the tick sits forward when the texture is sparse, tucks in when full
    if b < B_PULSE:
        g = 0.55
    elif B_BREAK <= b < B_ACT4:
        g = 0.65                       # alone in the breakdown — loudest
    elif b >= B_CHASE:
        g = 0.30
    else:
        g = 0.42
    for e in range(8):                 # straight eighths
        st = bar_t(b, e * 0.5)
        if e % 2 == 0:
            add_at(tick_L, TICK, st, g)
            add_at(tick_R, TICK, st, g * 0.55)
        else:
            add_at(tick_L, TOCK, st, g * 0.50)
            add_at(tick_R, TOCK, st, g * 0.85)

peak = max(np.max(np.abs(tick_L)), np.max(np.abs(tick_R)), 1e-12)
tick_L /= peak
tick_R /= peak


# ---------------------------------------------------------------- bass pulse
# Gated sub-bass ostinato — the engine of the pursuit. Sine + soft second
# harmonic through tanh for warmth (NOT a sawtooth — the v1 trombone lesson),
# each note a separate gated event so the pulse breathes.

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

bass_L = np.zeros(N)
bass_R = np.zeros(N)

# pre-render the note lengths we use
B16 = {m: bass_note(m, BEAT * 0.24) for m in (D2, C2, Eb2, D3, G1, FS1, Bb1)}
B8 = {m: bass_note(m, BEAT * 0.46) for m in (D2, C2, Eb2, G1, FS1, Bb1)}
B4 = {m: bass_note(m, BEAT * 0.92) for m in (D2, C2, G1)}

# 16th-step gate pattern for the chase (1.0 = accent, 0 = rest)
GATE16 = [1.0, 0, 0.7, 0, 1.0, 0, 0.7, 0.7,
          1.0, 0, 0.7, 0, 1.0, 0.7, 0, 0.7]

for b in range(B_STRIKE):
    if b < B_PULSE:
        continue
    if b < B_THEME_A:
        # sparse: root on the downbeat and a push on 2.5 — stalking
        add_at(bass_L, B4[D2], bar_t(b, 0.0), 1.0)
        add_at(bass_R, B4[D2], bar_t(b, 0.0), 1.0)
        add_at(bass_L, B8[D2], bar_t(b, 2.5), 0.7)
        add_at(bass_R, B8[D2], bar_t(b, 2.5), 0.7)
    elif b < B_BUILD:
        # eighth-note pattern; last beat walks to C or Eb on alternate bars
        walk = C2 if b % 2 == 0 else Eb2
        for e, (m, g) in enumerate([(D2, 1.0), (D2, 0.55), (D2, 0.7), (D2, 0.55),
                                    (D2, 0.9), (D2, 0.55), (walk, 0.85), (D2, 0.6)]):
            note = B8[m] if e % 2 == 0 else B16[m]
            add_at(bass_L, note, bar_t(b, e * 0.5), g)
            add_at(bass_R, note, bar_t(b, e * 0.5), g)
    elif b < B_BREAK:
        # build + chase: driving gated 16ths; every 4th bar walks the cadence
        last_of_four = (b - B_CHASE) % 4 == 3
        for s, g in enumerate(GATE16):
            if g == 0:
                continue
            m = D2
            if last_of_four and s >= 12:
                m = [C2, Eb2, D2, D2][s - 12]
            add_at(bass_L, B16[m], bar_t(b, s * 0.25), g)
            add_at(bass_R, B16[m], bar_t(b, s * 0.25), g)
    elif b < B_ACT4:
        continue                       # breakdown: heartbeat handles the low end
    elif b < B_CLIMAX:
        # cornered: same engine, sunk to G — the floor drops away
        last_of_four = (b - B_ACT4) % 4 == 3
        for s, g in enumerate(GATE16):
            if g == 0:
                continue
            m = G1
            if last_of_four and s >= 12:
                m = [FS1, Bb1, G1, G1][s - 12]
            add_at(bass_L, B16[m], bar_t(b, s * 0.25), g)
            add_at(bass_R, B16[m], bar_t(b, s * 0.25), g)
    else:
        # climax: back on D, full accents, octave jumps on the pushes
        for s, g in enumerate(GATE16):
            if g == 0:
                continue
            m = D3 if s in (7, 13) else D2
            add_at(bass_L, B16[m], bar_t(b, s * 0.25), min(1.0, g + 0.15))
            add_at(bass_R, B16[m], bar_t(b, s * 0.25), min(1.0, g + 0.15))

peak = max(np.max(np.abs(bass_L)), np.max(np.abs(bass_R)), 1e-12)
bass_L /= peak
bass_R /= peak


# ---------------------------------------------------------------- war drum
# Big taiko-like hits: falling-pitch body (90 -> 42 Hz) under a bandpassed
# skin slap, 6 ms attack — weight without harshness.

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

war_L = np.zeros(N)
war_R = np.zeros(N)

for b in range(B_STRIKE):
    if b < B_THEME_A:
        continue
    if b < B_THEME_A2:
        if b % 2 == 0:                                  # distant punctuation
            add_at(war_L, WAR, bar_t(b, 0.0), 0.5)
            add_at(war_R, WAR, bar_t(b, 0.0), 0.5)
    elif b < B_BUILD:
        add_at(war_L, WAR, bar_t(b, 0.0), 0.65)
        add_at(war_R, WAR, bar_t(b, 0.0), 0.65)
        if b % 2 == 1:
            add_at(war_L, WAR, bar_t(b, 2.5), 0.45)
            add_at(war_R, WAR, bar_t(b, 2.5), 0.45)
    elif b < B_BREAK:
        for beat, g in [(0.0, 0.95), (1.75, 0.5), (3.0, 0.7)]:
            add_at(war_L, WAR, bar_t(b, beat), g)
            add_at(war_R, WAR, bar_t(b, beat), g)
    elif b < B_ACT4:
        continue
    elif b < B_CLIMAX:
        # cornered: doubled downbeats — heavier, slower-feeling
        for beat, g in [(0.0, 1.0), (0.5, 0.7), (2.5, 0.8)]:
            add_at(war_L, WAR, bar_t(b, beat), g)
            add_at(war_R, WAR, bar_t(b, beat), g)
    else:
        hits = [(0.0, 1.0), (1.0, 0.6), (2.0, 0.8), (2.5, 0.6), (3.0, 0.85)]
        if b >= B_STRIKE - 2:                           # cascade into the strike
            hits += [(3.25, 0.7), (3.5, 0.85), (3.75, 1.0)]
        for beat, g in hits:
            add_at(war_L, WAR, bar_t(b, beat), g)
            add_at(war_R, WAR, bar_t(b, beat), g)

# triple hit right on the strike
for k, g in [(0, 1.0), (1, 0.85), (2, 1.0)]:
    add_at(war_L, WAR, bar_t(B_STRIKE, k * 0.5), g)
    add_at(war_R, WAR, bar_t(B_STRIKE, k * 0.5), g)

peak = max(np.max(np.abs(war_L)), np.max(np.abs(war_R)), 1e-12)
war_L /= peak
war_R /= peak


# ---------------------------------------------------------------- frame drum
# Daf/bendir: a skipping off-grid pattern in the stalking sections, and
# accelerating buzz rolls that launch the big transitions.

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
    """Accelerating, crescendoing buzz roll."""
    out = np.zeros(int((dur + 0.3) * SR))
    tcur = 0.0
    while tcur < dur:
        frac = tcur / dur
        rate = 9.0 + 11.0 * frac
        g = (0.30 + 0.70 * frac) * rng.uniform(0.85, 1.0)
        add_at(out, FRAME, tcur, g)
        tcur += 1.0 / rate
    return out


frame_L = np.zeros(N)
frame_R = np.zeros(N)

for b in range(B_STRIKE):
    if b < B_PULSE or B_BREAK <= b < B_ACT4 or B_BUILD <= b < B_CHASE:
        continue
    for s, g in [(3, 0.30), (7, 0.34), (10, 0.26), (15, 0.38)]:
        p = 0.35 if s in (3, 10) else 0.65              # skips answer L/R
        add_at(frame_L, FRAME, bar_t(b, s * 0.25), g * np.cos(p * np.pi / 2))
        add_at(frame_R, FRAME, bar_t(b, s * 0.25), g * np.sin(p * np.pi / 2))

# rolls: into the chase, into act IV, and into the strike
for start_bar, dur_bars, g in [(B_BUILD, 2.0, 1.0),
                               (B_ACT4 - 1, 1.0, 0.8),
                               (B_STRIKE - 1, 1.0, 1.0)]:
    roll = frame_roll(dur_bars * BAR)
    add_at(frame_L, roll, bar_t(start_bar), g * 0.9)
    add_at(frame_R, roll, bar_t(start_bar), g)

peak = max(np.max(np.abs(frame_L)), np.max(np.abs(frame_R)), 1e-12)
frame_L /= peak
frame_R /= peak


# ---------------------------------------------------------------- darbuka
# Same kit as base_under_attack. Maqsum for the chase; saidi (double doum)
# for act IV — the heavier pattern reads as "cornered".

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

drum_L = np.zeros(N)
drum_R = np.zeros(N)

for b in range(B_STRIKE):
    if b < B_THEME_A2 or B_BREAK <= b < B_ACT4 or B_BUILD <= b < B_CHASE:
        continue
    if b < B_BUILD:
        pattern, level, ghosts = MAQSUM, 0.55, 0.15     # light entry
    elif b < B_BREAK:
        pattern, level, ghosts = MAQSUM, 1.0, 0.30      # full chase
    elif b < B_CLIMAX:
        pattern, level, ghosts = SAIDI, 1.0, 0.20       # cornered
    else:
        pattern, level, ghosts = SAIDI, 1.0, 0.40       # climax
    fill_bar = b >= B_CHASE and (b - B_CHASE) % 4 == 3
    for s in range(16):
        st = bar_t(b, s * 0.25)
        stroke = pattern.get(s)
        if fill_bar and s >= 10:
            g = (0.45 + 0.55 * (s - 10) / 5.0) * level
            add_at(drum_L, TEK, st, g * 0.9)
            add_at(drum_R, TEK, st, g * 0.7)
            continue
        if stroke == "D":
            add_at(drum_L, DOUM, st, level)
            add_at(drum_R, DOUM, st, level)
        elif stroke == "T":
            p = 0.35 if s in (2, 12) else 0.65
            add_at(drum_L, TEK, st, level * np.cos(p * np.pi / 2))
            add_at(drum_R, TEK, st, level * np.sin(p * np.pi / 2))
        elif s % 2 == 1 and rng.random() < ghosts:
            add_at(drum_L, KA, st, 0.6 * level)
            add_at(drum_R, KA, st, 0.5 * level)

peak = max(np.max(np.abs(drum_L)), np.max(np.abs(drum_R)), 1e-12)
drum_L /= peak
drum_R /= peak


# ---------------------------------------------------------------- oud
# Theme A stated cleanly first (bars 16-23), then the chase riff, then an
# octave-up restatement at the climax. (midi, beat, dur_beats) per phrase.

THEME_A = [
    (50, 0.0, 1), (54, 1.0, 0.5), (51, 1.5, 0.5), (50, 2.0, 1), (48, 3.0, 1),
    (50, 4.0, 1.5), (51, 5.5, 0.5), (54, 6.0, 1), (57, 7.0, 1),
    (55, 8.0, 1), (54, 9.0, 0.5), (51, 9.5, 0.5), (50, 10.0, 2),
    (48, 12.0, 1), (51, 13.0, 1), (50, 14.0, 2),
]
# second statement ends rising to A instead of resolving — unanswered
THEME_A_VAR = THEME_A[:-3] + [(51, 12.0, 1), (54, 13.0, 1), (57, 14.0, 2)]

CHASE_RIFF = [50, 50, 48, 50, 51, 50, 54, 55]           # eighths

oud_L = np.zeros(N)
oud_R = np.zeros(N)

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
        add_at(oud_L, x, t0 + beat * BEAT, gain * 0.95)
        add_at(oud_R, x, t0 + beat * BEAT, gain * 0.8)


play_theme(THEME_A, bar_t(B_THEME_A), gain=1.0)
play_theme(THEME_A_VAR, bar_t(B_THEME_A + 4), gain=1.0)
# under the duduk answer, the oud repeats the theme as accompaniment
play_theme(THEME_A, bar_t(B_THEME_A2), gain=0.7)
play_theme(THEME_A_VAR, bar_t(B_THEME_A2 + 4), gain=0.7)

for b in range(B_CHASE, B_BREAK):
    for e in range(8):
        m = CHASE_RIFF[e]
        if rng.random() < 0.10 and e in (2, 6):
            m += 12
        g = 1.0 if e % 2 == 0 else 0.75
        x = pluck(m, 0.95)
        add_at(oud_L, x, bar_t(b, e * 0.5), g * 0.95)
        add_at(oud_R, x, bar_t(b, e * 0.5), g * 0.8)

# climax: Theme A an octave up, urgent, over the full kit
play_theme(THEME_A, bar_t(B_CLIMAX), transpose=12, gain=1.0)
play_theme(THEME_A_VAR, bar_t(B_CLIMAX + 4), transpose=12, gain=1.0)

peak = max(np.max(np.abs(oud_L)), np.max(np.abs(oud_R)), 1e-12)
oud_L /= peak
oud_R /= peak


# ---------------------------------------------------------------- duduk
# The voice carries the story: a watcher's call, the answer to Theme A, a
# lone held Eb in the breakdown, Theme B when cornered, the coda lament.

voice_L = np.zeros(N)
voice_R = np.zeros(N)


def place_voice(notes, t0, pan_pos, gain=1.0, lp=2200):
    v = voice_phrase(notes, lp=lp)
    add_at(voice_L, v, t0, gain * np.cos(pan_pos * np.pi / 2))
    add_at(voice_R, v, t0, gain * np.sin(pan_pos * np.pi / 2))


b2s = lambda nb: nb * BEAT                              # beats -> seconds

# I. the watcher's call, before any rhythm exists
place_voice([(62, 1.0), (66, 0.8), (63, 0.8), (62, 2.2)], 7.0, 0.62, 1.0)

# III. Theme A answered an octave up (overlapping the oud restatement)
place_voice([(62, b2s(2)), (66, b2s(1)), (63, b2s(1)), (62, b2s(2)),
             (60, b2s(2)), (62, b2s(3)), (63, b2s(1)), (66, b2s(2)),
             (69, b2s(2)), (67, b2s(2)), (66, b2s(1)), (63, b2s(1)),
             (62, b2s(4)), (60, b2s(2)), (63, b2s(2)), (62, b2s(4))],
            bar_t(B_THEME_A2), 0.45, 1.0)

# breakdown: a single held Eb — the flat second, pure unresolved tension
place_voice([(63, 7.0), (62, 3.0)], bar_t(B_BREAK + 1), 0.5, 0.9, lp=1800)

# IV. Theme B, centered on G
place_voice([(67, b2s(2)), (70, b2s(1)), (69, b2s(1)), (67, b2s(2)),
             (66, b2s(2)), (67, b2s(4)), (70, b2s(2)), (72, b2s(2)),
             (74, b2s(4)), (72, b2s(2)), (70, b2s(2)), (69, b2s(2)),
             (67, b2s(4))],
            bar_t(B_ACT4), 0.55, 1.0)
place_voice([(74, b2s(2)), (75, b2s(1)), (74, b2s(1)), (72, b2s(2)),
             (70, b2s(2)), (69, b2s(2)), (67, b2s(2)), (66, b2s(2)),
             (67, b2s(5))],
            bar_t(B_ACT4 + 8), 0.42, 0.95)

# V. coda: a slow descent home to D — the desert closes over the story
place_voice([(74, 1.7), (72, 1.2), (70, 1.2), (69, 1.7), (67, 1.7),
             (66, 1.7), (63, 1.7), (62, 4.5)],
            bar_t(B_STRIKE) + 7.0, 0.5, 1.0, lp=1900)

voice_L = reverb(voice_L, IR_L, wet=0.65)
voice_R = reverb(voice_R, IR_R, wet=0.65)
peak = max(np.max(np.abs(voice_L)), np.max(np.abs(voice_R)), 1e-12)
voice_L /= peak
voice_R /= peak


# ---------------------------------------------------------------- strings
# Tremolo string bed: detuned additive "bow" tone, bandpassed, with a fast
# tremolo whose envelope touches true silence each cycle (anti-tinnitus
# rule) — tension for the build, act IV and the climax only.

def tremolo_strings(chord, dur, trem_hz=10.5):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    out = np.zeros(n)
    for m in chord:
        f = midi_to_hz(m)
        for det, g in [(0.996, 0.6), (1.0, 1.0), (1.005, 0.6)]:
            for k in range(1, 9):                       # saw-ish, controlled top
                out += (g / k) * np.sin(2 * np.pi * f * det * k * tt +
                                        rng.uniform(0, 2 * np.pi))
    sos_s = signal.butter(2, [180, 2600], "bandpass", fs=SR, output="sos")
    out = signal.sosfilt(sos_s, out)
    trem = (0.5 + 0.5 * np.sin(2 * np.pi * trem_hz * tt)) ** 1.2
    env = np.minimum(np.clip(tt / 1.5, 0, 1), np.clip((dur - tt) / 2.0, 0, 1))
    out *= trem * env
    return out / (np.max(np.abs(out)) + 1e-12)


str_L = np.zeros(N)
str_R = np.zeros(N)

# build: D + Eb minor-second swell — two bars of pure friction
sw = tremolo_strings([62, 63], 2 * BAR + 1.0)
add_at(str_L, sw, bar_t(B_BUILD), 0.8)
add_at(str_R, sw, bar_t(B_BUILD), 0.7)
# act IV: G minor with the flat sixth leaning on it
sw = tremolo_strings([55, 62, 63], (B_CLIMAX - B_ACT4) * BAR)
add_at(str_L, sw, bar_t(B_ACT4), 0.9)
add_at(str_R, sw, bar_t(B_ACT4), 0.8)
# climax: D with the flat second on top, brighter and higher
sw = tremolo_strings([62, 69, 75], (B_STRIKE - B_CLIMAX) * BAR, trem_hz=12.0)
add_at(str_L, sw, bar_t(B_CLIMAX), 0.8)
add_at(str_R, sw, bar_t(B_CLIMAX), 0.9)

str_L = reverb(str_L, IR_L, wet=0.45)
str_R = reverb(str_R, IR_R, wet=0.45)
peak = max(np.max(np.abs(str_L)), np.max(np.abs(str_R)), 1e-12)
str_L /= peak
str_R /= peak


# ---------------------------------------------------------------- risers
# Swept-noise risers that launch the chase and the climax.

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
    f_curve = 70.0 * 2.0 ** (2.0 * tt / dur)            # rising tone, 2 octaves
    tone = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    x = (out + 0.45 * tone) * (tt / dur) ** 2
    return x / (np.max(np.abs(x)) + 1e-12)


rise_L = np.zeros(N)
rise_R = np.zeros(N)
for start_bar, dur_bars in [(B_BUILD, 2.0), (B_CLIMAX - 2, 2.0)]:
    rz = riser(dur_bars * BAR)
    add_at(rise_L, rz, bar_t(start_bar), 0.85)
    add_at(rise_R, rz, bar_t(start_bar), 1.0)

peak = max(np.max(np.abs(rise_L)), np.max(np.abs(rise_R)), 1e-12)
rise_L /= peak
rise_R /= peak


# ---------------------------------------------------------------- heartbeat
# Breakdown only: the runner's pulse. Sub-kick pairs (lub-dub) on each bar.

nk = int(0.35 * SR)
tk = np.arange(nk) / SR
fk = 36.0 + 60.0 * np.exp(-tk * 16.0)
SUBKICK = np.sin(2 * np.pi * np.cumsum(fk) / SR) * \
    np.exp(-tk * 10.0) * (1 - np.exp(-tk * 400))

heart_L = np.zeros(N)
heart_R = np.zeros(N)
for b in range(B_BREAK, B_ACT4):
    for beat, g in [(0.0, 1.0), (0.75, 0.6), (2.0, 1.0), (2.75, 0.6)]:
        add_at(heart_L, SUBKICK, bar_t(b, beat), g)
        add_at(heart_R, SUBKICK, bar_t(b, beat), g)

peak = max(np.max(np.abs(heart_L)), np.max(np.abs(heart_R)), 1e-12)
heart_L /= peak
heart_R /= peak


# ---------------------------------------------------------------- the strike
# The worm answers the noise of the hunt: explosion + falling worm thump,
# the biggest low event of the track, then nothing but desert.

strike_L = np.zeros(N)
strike_R = np.zeros(N)
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
add_at(strike_L, body * 0.7 + core * 0.6, T_STRIKE, 1.0)
add_at(strike_R, body * 0.7 + core * 0.6, T_STRIKE, 1.0)

# the worm passes: arrakis thump, twice, receding
n = int(6.0 * SR)
tb = np.arange(n) / SR
f_curve = 27.0 + 28.0 * np.exp(-tb * 2.2)
env = np.exp(-tb * 1.1) * (1 - np.exp(-tb * 30))
thump = env * np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
sos_gr = signal.butter(4, 90, "low", fs=SR, output="sos")
shake = signal.sosfilt(sos_gr, rng.standard_normal(n)) * env * 0.6
for dt, g in [(2.5, 0.8), (9.0, 0.45)]:
    add_at(strike_L, thump + shake, T_STRIKE + dt, g)
    add_at(strike_R, thump + shake, T_STRIKE + dt, g)

strike_L = reverb(strike_L, IR_L, wet=0.4)
strike_R = reverb(strike_R, IR_R, wet=0.4)
peak = max(np.max(np.abs(strike_L)), np.max(np.abs(strike_R)), 1e-12)
strike_L /= peak
strike_R /= peak


# ---------------------------------------------------------------- mix
# Per-section energy curve ducks the calm layers as the hunt intensifies
# and lets them flood back in the breakdown and the coda.

energy_pts = [(0.0, 0.0), (GRID0 - 0.5, 0.0), (GRID0 + 1.0, 0.25),
              (bar_t(B_PULSE), 0.25), (bar_t(B_PULSE) + 1.5, 0.40),
              (bar_t(B_THEME_A), 0.40), (bar_t(B_THEME_A) + 1.5, 0.55),
              (bar_t(B_THEME_A2), 0.55), (bar_t(B_THEME_A2) + 1.5, 0.65),
              (bar_t(B_CHASE), 0.65), (bar_t(B_CHASE) + 0.5, 0.90),
              (bar_t(B_BREAK), 0.90), (bar_t(B_BREAK) + 0.3, 0.30),
              (bar_t(B_ACT4), 0.30), (bar_t(B_ACT4) + 0.5, 0.85),
              (bar_t(B_CLIMAX), 0.85), (bar_t(B_CLIMAX) + 0.5, 1.0),
              (T_STRIKE, 1.0), (T_STRIKE + 2.0, 0.10),
              (DURATION, 0.0)]
energy = np.interp(t, [p[0] for p in energy_pts], [p[1] for p in energy_pts])
calm = 1.0 - 0.45 * energy

L = (0.26 * wind_L * calm + 0.22 * drone * calm +
     0.10 * tick_L + 0.30 * bass_L + 0.34 * war_L + 0.12 * frame_L +
     0.22 * drum_L + 0.20 * oud_L + 0.20 * voice_L + 0.15 * str_L +
     0.12 * rise_L + 0.26 * heart_L + 0.42 * strike_L)
R = (0.26 * wind_R * calm + 0.22 * drone * calm +
     0.10 * tick_R + 0.30 * bass_R + 0.34 * war_R + 0.12 * frame_R +
     0.22 * drum_R + 0.20 * oud_R + 0.20 * voice_R + 0.15 * str_R +
     0.12 * rise_R + 0.26 * heart_R + 0.42 * strike_R)

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
OUT = os.path.join(OUT_DIR, "night_pursuit.wav")
with wave.open(OUT, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())

print(f"Created: {os.path.abspath(OUT)}")
print(f"Duration: {N / SR:.1f} s  |  {SR} Hz stereo, 16-bit PCM  |  {BPM:.0f} BPM")
print("Section map:")
for name, b in [("tick starts", 0), ("bass pulse", B_PULSE),
                ("Theme A (oud)", B_THEME_A), ("duduk answer + darbuka", B_THEME_A2),
                ("build (roll + riser)", B_BUILD), ("full chase", B_CHASE),
                ("breakdown (tick + heartbeat)", B_BREAK),
                ("act IV — cornered, center G", B_ACT4),
                ("climax — back to D", B_CLIMAX), ("the worm strike", B_STRIKE)]:
    print(f"  {bar_t(b):6.1f} s  bar {b:2d}  {name}")
print(f"  {DURATION:6.1f} s  end (coda duduk from {bar_t(B_STRIKE) + 7.0:.0f} s)")
