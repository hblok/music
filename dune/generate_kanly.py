#!/usr/bin/env python3
"""
generate_kanly.py — kanly, the war of assassins. The daytime mirror of
night_pursuit: where that track ends with the desert winning (the worm
erases the hunt), this one is the lone rider who completes the kill — and
finds only emptiness on the other side of it.

Reference: Lawrence of Arabia's relentless desert crossings and the
John Wick "I have an appointment" single-minded assassin, transplanted
into the Dune palette. Kanly is the formal blood-feud; the rider crosses
the open sand at dawn to settle one, and the music asks whether the
settling was worth the ride.

The track tells a story in six acts (no section repeats verbatim):

  I   Dawn        0:00  Arrakis wind + D drone (shared recipe, so it
                        crossfades with the other tracks) brightened by a
                        rising sunrise shimmer — the major third F# in the
                        light, warmth the night tracks never allow. A ney
                        call (the world's Theme A) — the rider wakes, the
                        sun crests the dune, the path is clear.
  II  The Ride    0:24  Galloping hoofbeats — the engine. A gated sub on
                        the stride; the oud states Theme R (the rider's
                        theme), Arabic, determined, hypnotic. Relentless,
                        but patient: a long ride across open sand.
  III The Wait    1:15  The gallop cuts dead. Destiny's clock (the
                        night_pursuit tick) counts alone; held breath,
                        tremolo strings on the augmented second (E♭–F#);
                        the duduk asks one question, unanswered. He waits
                        at the elder's door.
  IV  The Hunt    1:41  The gallop slams back, doubled, over war drums,
                        driving 16th bass and full darbuka; Theme R urgent,
                        an octave up. The closing-in.
  V   The Kill    2:28  One decisive blow — the biggest hit of the track, a
                        sub-boom under a blade's metallic ring — and the
                        groove stops dead. Not the worm. A man's blade.
  VI  Emptiness   2:32  The hollow after. The drone sinks 6% (the agony
                        recipe), a lone broken duduk plays Theme R in
                        fragments and lets them die; the wind floods back,
                        colder and emptier than the dawn. One far hoofbeat
                        that never repeats — the horse walking away. The
                        sun is high and pitiless. The kanly is settled and
                        it bought nothing.

Output: /workspace/music/kanly.wav (stereo, 44100 Hz, 16-bit).
"""

import os
import wave
import numpy as np
from scipy import signal

SR = 44100
DURATION = 220.0
N = int(SR * DURATION)
t = np.arange(N) / SR

rng = np.random.default_rng(1962)        # Lawrence of Arabia, 1962

BPM = 112.0
BEAT = 60.0 / BPM
BAR = BEAT * 4
GRID0 = 24.0                             # bar 0 of the rhythmic grid (the ride begins)


def bar_t(b, beat=0.0):
    """Absolute time of beat `beat` in bar `b` of the grid."""
    return GRID0 + b * BAR + beat * BEAT


# section boundaries, in bars (printed at the end)
B_RIDE = 0         # gallop + gated bass + Theme R enter
B_RIDE2 = 8        # fuller ride: war-drum punctuation, duduk answer
B_RIDE3 = 16       # peak of the open ride (light darbuka), relentless
B_WAIT = 24        # the cut: tick + held breath + strings only
B_WAITB = 32       # the wait continues — the duduk's question
B_HUNT = 36        # gallop slams back, war drums, 16th bass, full darbuka
B_HUNT2 = 44       # Theme R octave up, urgent, fills
B_HUNT3 = 52       # peak chase
B_KILL = 58        # the strike; the groove dies


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


def voice_phrase(notes, lp=2200, ney=False):
    """Duduk/ney voice: list of (midi, dur_s) with portamento + vibrato.
    ney=True makes it airier (purer harmonics + breath noise)."""
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
    tau = 0.07 if ney else 0.09
    alpha = 1.0 - np.exp(-1.0 / (tau * SR))
    f_curve = signal.lfilter([alpha], [1.0, -(1.0 - alpha)],
                             f_target, zi=[f_target[0] * (1 - alpha)])[0]
    vib_hz = 6.0 if ney else 5.2
    vib_dep = 0.004 if ney else 0.006
    bloom = 0.8 if ney else 1.2
    vib = 1.0 + vib_dep * np.sin(2 * np.pi * vib_hz * tt) * np.clip(tt / bloom, 0, 1)
    phase = 2 * np.pi * np.cumsum(f_curve * vib) / SR
    env = np.minimum(np.clip(tt / 1.0, 0, 1),
                     np.clip((total - tt) / 2.0, 0, 1)) ** 1.5
    if ney:
        v = env * (np.sin(phase) + 0.25 * np.sin(2 * phase) + 0.08 * np.sin(3 * phase))
        sos_br = signal.butter(2, [1200, 4000], "bandpass", fs=SR, output="sos")
        breath = signal.sosfilt(sos_br, rng.standard_normal(n)) * env * 0.13
        v = v + breath
    else:
        v = env * (np.sin(phase) + 0.40 * np.sin(2 * phase) +
                   0.18 * np.sin(3 * phase) + 0.07 * np.sin(4 * phase))
    sos = signal.butter(2, lp, "low", fs=SR, output="sos")
    return signal.sosfilt(sos, v)


IR_L = make_reverb_ir(5.0, 1.6, 7)
IR_R = make_reverb_ir(5.0, 1.6, 11)


# ---------------------------------------------------------------- wind & drone
# Same recipe as arrakis_winds_v2 / night_pursuit so the tracks blend.

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


# ---------------------------------------------------------------- sunrise shimmer
# DAWN, not night: a warm high band that rises and crests as the sun clears
# the dune, then fades as the ride begins (the light is up; no need to keep
# shimmering). The major third F# in the partials = warmth/hope the night
# tracks deny. Anti-tinnitus: the whole gesture swells then fades within ~28 s.

shimmer_L = np.zeros(N)
shimmer_R = np.zeros(N)

sh_dur = 30.0
ns = int(sh_dur * SR)
ts = np.arange(ns) / SR
# rising bandpassed-noise "light spreading" — center sweeps 700 -> 3000 Hz
nz = rng.standard_normal(ns)
band = np.zeros(ns)
K = 8
for k in range(K):
    c0, c1 = 700.0, 3000.0
    center = c0 * (c1 / c0) ** ((ts / sh_dur))       # rising over the swell
    # approximate a sweeping bandpass with a few fixed bands, time-windowed
    cc = c0 * (c1 / c0) ** (k / (K - 1))
    sos_b = signal.butter(2, [cc * 0.75, cc * 1.4], "bandpass", fs=SR, output="sos")
    b = signal.sosfilt(sos_b, nz)
    w = np.clip(1 - np.abs(ts - (k + 0.5) / K * sh_dur) / (sh_dur / K * 1.8), 0, 1)
    band += b * w
band /= np.max(np.abs(band)) + 1e-12
# warm partials: D5, F#5 (the major third), A5 — gentle, pulsing to silence
warm = np.zeros(ns)
for m, g in [(74, 1.0), (78, 0.7), (81, 0.45)]:
    f = midi_to_hz(m)
    puls = np.clip(np.sin(2 * np.pi * 0.18 * ts + g), 0, 1) ** 2   # touches silence
    warm += g * np.sin(2 * np.pi * f * ts + rng.uniform(0, 6.28)) * puls
warm /= np.max(np.abs(warm)) + 1e-12
swell = np.clip(ts / 14.0, 0, 1) * np.clip((sh_dur - ts) / 12.0, 0, 1)   # crest ~14 s
sh = (0.5 * band + 0.5 * warm) * swell
sh_pan = 0.5 + 0.25 * np.sin(2 * np.pi * 0.05 * ts)
add_at(shimmer_L, sh * np.cos(sh_pan * np.pi / 2), 2.0, 1.0)
add_at(shimmer_R, sh * np.sin(sh_pan * np.pi / 2), 2.0, 1.0)
shimmer_L = reverb(shimmer_L, IR_L, wet=0.55)
shimmer_R = reverb(shimmer_R, IR_R, wet=0.55)
peak = max(np.max(np.abs(shimmer_L)), np.max(np.abs(shimmer_R)), 1e-12)
shimmer_L /= peak
shimmer_R /= peak


# ---------------------------------------------------------------- hoofbeats
# The engine of the ride: a galloping triplet hoof pattern. Each hoof is a
# dry dusty thud — a fast downward pitch-thump (sand-soft, lower than the war
# drum) plus a bandpassed "sand kicked up" transient. Two variants for the
# alternating lead/trail hoof of the gait. The gallop reads as relentless
# forward motion — the rider crossing open sand.

def make_hoof(lead=False):
    n = int(0.12 * SR)
    td = np.arange(n) / SR
    f0, f1, dec = (200.0, 62.0, 40.0) if lead else (170.0, 55.0, 46.0)
    f_curve = f1 + (f0 - f1) * np.exp(-td * 55.0)
    body = np.sin(2 * np.pi * np.cumsum(f_curve) / SR) * np.exp(-td * dec)
    sos_d = signal.butter(2, [220, 1700], "bandpass", fs=SR, output="sos")
    dust = signal.sosfilt(sos_d, rng.standard_normal(n)) * np.exp(-td * 70.0)
    dust /= np.max(np.abs(dust)) + 1e-12
    x = (body + 0.45 * dust) * (1 - np.exp(-td * 900.0))
    return x / (np.max(np.abs(x)) + 1e-12)


HOOF_A = make_hoof(lead=True)
HOOF_B = make_hoof(lead=False)

hoof_L = np.zeros(N)
hoof_R = np.zeros(N)

# triplet gallop cells: gains for the 3 triplet positions within a beat.
CANTER = [[1.0, 0.0, 0.55],     # DUM . da
          [0.85, 0.5, 0.55]]    # DUM da da
GALLOP = [[1.0, 0.6, 0.7],      # busier 4-beat-feel gallop for the hunt
          [0.9, 0.6, 0.75]]


def place_gallop(b, cells, level, pan_lead=0.4):
    """Lay a galloping bar; hooves alternate lead/trail L/R for the gait."""
    flip = 0
    for beat in range(4):
        cell = cells[beat % 2]
        for tp, g in enumerate(cell):
            if g <= 0:
                continue
            st = bar_t(b, beat + tp / 3.0)
            lead = (flip % 2 == 0)
            hoof = HOOF_A if lead else HOOF_B
            p = pan_lead if lead else (1.0 - pan_lead)
            add_at(hoof_L, hoof, st, level * g * np.cos(p * np.pi / 2))
            add_at(hoof_R, hoof, st, level * g * np.sin(p * np.pi / 2))
            flip += 1


for b in range(B_KILL):
    if b < B_RIDE2:
        place_gallop(b, CANTER, 0.7)               # the ride sets out
    elif b < B_RIDE3:
        place_gallop(b, CANTER, 0.85)              # fuller
    elif b < B_WAIT:
        place_gallop(b, CANTER, 1.0)               # peak open ride
    elif b < B_HUNT:
        continue                                   # THE WAIT — no hooves
    elif b < B_HUNT2:
        place_gallop(b, GALLOP, 1.0)               # the hunt — doubled gallop
    else:
        place_gallop(b, GALLOP, 1.0, pan_lead=0.35)  # peak chase, wider

peak = max(np.max(np.abs(hoof_L)), np.max(np.abs(hoof_R)), 1e-12)
hoof_L /= peak
hoof_R /= peak


# ---------------------------------------------------------------- tick-tock
# Destiny's clock — the night_pursuit ostinato, but here it belongs to ONE
# section: the wait. While the rider waits at the door, time counts. Bone
# dry, straight eighths, tick L / tock R.

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
for b in range(B_WAIT, B_HUNT):
    for e in range(8):
        st = bar_t(b, e * 0.5)
        if e % 2 == 0:
            add_at(tick_L, TICK, st, 0.6)
            add_at(tick_R, TICK, st, 0.33)
        else:
            add_at(tick_L, TOCK, st, 0.30)
            add_at(tick_R, TOCK, st, 0.55)

peak = max(np.max(np.abs(tick_L)), np.max(np.abs(tick_R)), 1e-12)
tick_L /= peak
tick_R /= peak


# ---------------------------------------------------------------- bass pulse
# Gated sub on the stride: sine + soft 2nd harmonic through tanh for warmth
# (saw reads as trombone — the v1 lesson). Sparse on the ride (the rider's
# stride), driving 16ths in the hunt.

def bass_note(midi, dur):
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * td) + 0.35 * np.sin(2 * np.pi * 2 * f * td + 0.3)
    x = np.tanh(1.6 * x)
    env = (1 - np.exp(-td / 0.005)) * np.clip((dur - td) / 0.05, 0, 1)
    return x * env


D2, C2, Eb2, D3 = 38, 36, 39, 50
Bb1, A1, G1 = 34, 33, 31

bass_L = np.zeros(N)
bass_R = np.zeros(N)

B16 = {m: bass_note(m, BEAT * 0.24) for m in (D2, C2, Eb2, D3, Bb1, A1, G1)}
B8 = {m: bass_note(m, BEAT * 0.46) for m in (D2, C2, Eb2, Bb1, A1, G1)}
B4 = {m: bass_note(m, BEAT * 0.92) for m in (D2, C2, Bb1, A1)}

# 16th gate for the hunt
GATE16 = [1.0, 0, 0.7, 0, 1.0, 0, 0.7, 0.7,
          1.0, 0, 0.7, 0, 1.0, 0.7, 0, 0.7]

for b in range(B_KILL):
    if b < B_RIDE3:
        # the stride: root on 1, a push on 3.5, walk to Bb/C on alternate bars
        walk = Bb1 if b % 2 == 0 else C2
        add_at(bass_L, B4[D2], bar_t(b, 0.0), 1.0)
        add_at(bass_R, B4[D2], bar_t(b, 0.0), 1.0)
        add_at(bass_L, B8[walk], bar_t(b, 2.5), 0.7)
        add_at(bass_R, B8[walk], bar_t(b, 2.5), 0.7)
    elif b < B_WAIT:
        # fuller ride: eighth-note pattern
        walk = C2 if b % 2 == 0 else Eb2
        for e, (m, g) in enumerate([(D2, 1.0), (D2, 0.55), (D2, 0.7), (D2, 0.55),
                                    (D2, 0.9), (D2, 0.55), (walk, 0.85), (D2, 0.6)]):
            note = B8[m] if e % 2 == 0 else B16[m]
            add_at(bass_L, note, bar_t(b, e * 0.5), g)
            add_at(bass_R, note, bar_t(b, e * 0.5), g)
    elif b < B_HUNT:
        # the wait: a slow, sparse sub heartbeat on 1 and 3 only — held breath
        for beat, g in [(0.0, 0.7), (2.0, 0.55)]:
            add_at(bass_L, B4[D2], bar_t(b, beat), g)
            add_at(bass_R, B4[D2], bar_t(b, beat), g)
    else:
        # the hunt: driving gated 16ths; every 4th bar walks the cadence down
        last_of_four = (b - B_HUNT) % 4 == 3
        for s, g in enumerate(GATE16):
            if g == 0:
                continue
            m = D2
            if last_of_four and s >= 12:
                m = [C2, Bb1, D2, D2][s - 12]
            if b >= B_HUNT2 and s in (7, 13):
                m = D3                         # octave pushes at the peak
            add_at(bass_L, B16[m], bar_t(b, s * 0.25), min(1.0, g + 0.1))
            add_at(bass_R, B16[m], bar_t(b, s * 0.25), min(1.0, g + 0.1))

peak = max(np.max(np.abs(bass_L)), np.max(np.abs(bass_R)), 1e-12)
bass_L /= peak
bass_R /= peak


# ---------------------------------------------------------------- war drum
# Taiko-like weight: falling-pitch body (90 -> 42 Hz) under a bandpassed skin
# slap. Distant punctuation on the ride, full pattern in the hunt.

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

for b in range(B_KILL):
    if b < B_RIDE2:
        continue
    if b < B_WAIT:
        if b % 2 == 0:                              # distant downbeat marker
            add_at(war_L, WAR, bar_t(b, 0.0), 0.5)
            add_at(war_R, WAR, bar_t(b, 0.0), 0.5)
    elif b < B_HUNT:
        continue                                    # the wait: no war drum
    else:
        hits = [(0.0, 0.95), (1.75, 0.5), (3.0, 0.7)]
        if b >= B_HUNT2:
            hits = [(0.0, 1.0), (1.0, 0.6), (2.0, 0.8), (2.5, 0.6), (3.0, 0.85)]
        if b >= B_KILL - 2:                         # cascade into the strike
            hits += [(3.25, 0.7), (3.5, 0.85), (3.75, 1.0)]
        for beat, g in hits:
            add_at(war_L, WAR, bar_t(b, beat), g)
            add_at(war_R, WAR, bar_t(b, beat), g)

peak = max(np.max(np.abs(war_L)), np.max(np.abs(war_R)), 1e-12)
war_L /= peak
war_R /= peak


# ---------------------------------------------------------------- darbuka
# Light maqsum riding the gallop in the open ride's peak, full kit + fills in
# the hunt. Same kit as base_under_attack / night_pursuit.

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

drum_L = np.zeros(N)
drum_R = np.zeros(N)

for b in range(B_KILL):
    if b < B_RIDE3 or B_WAIT <= b < B_HUNT:
        continue
    if b < B_WAIT:
        level, ghosts = 0.55, 0.15                  # light, riding the ride peak
    elif b < B_HUNT2:
        level, ghosts = 0.95, 0.30                  # the hunt
    else:
        level, ghosts = 1.0, 0.40                   # peak chase
    fill_bar = b >= B_HUNT and (b - B_HUNT) % 4 == 3
    for s in range(16):
        st = bar_t(b, s * 0.25)
        stroke = MAQSUM.get(s)
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
# Theme R — the rider's theme. Arabic, determined, in D Phrygian dominant
# (Hijaz): the characteristic augmented second F#–E♭ is the exotic color, the
# B♭ the longing. Stated on the ride, restated an octave up in the hunt, then
# broken into fragments by the duduk in the emptiness coda.

THEME_R = [
    (62, 0.0, 1), (66, 1.0, 1), (67, 2.0, 0.5), (69, 2.5, 1.5),
    (70, 4.0, 1), (69, 5.0, 0.5), (67, 5.5, 0.5), (66, 6.0, 1), (63, 7.0, 1),
    (62, 8.0, 2), (66, 10.0, 1), (69, 11.0, 1),
    (67, 12.0, 1), (66, 13.0, 0.5), (63, 13.5, 0.5), (62, 14.0, 2),
]
# the variant ends rising to B♭, unresolved — the ride does not arrive yet
THEME_R_VAR = THEME_R[:-4] + [(67, 12.0, 1), (69, 13.0, 1), (70, 14.0, 2)]

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


# the ride: Theme R stated, then the rising variant
play_theme(THEME_R, bar_t(B_RIDE), gain=0.95)
play_theme(THEME_R_VAR, bar_t(B_RIDE2), gain=1.0)
play_theme(THEME_R, bar_t(B_RIDE3), gain=1.0)
# the hunt: Theme R an octave up, urgent
play_theme(THEME_R, bar_t(B_HUNT), transpose=12, gain=1.0)
play_theme(THEME_R_VAR, bar_t(B_HUNT2), transpose=12, gain=1.0)
play_theme(THEME_R, bar_t(B_HUNT3), transpose=12, gain=1.0)

peak = max(np.max(np.abs(oud_L)), np.max(np.abs(oud_R)), 1e-12)
oud_L /= peak
oud_R /= peak


# ---------------------------------------------------------------- duduk / ney
# The voice carries the human thread: the dawn ney-call quotes the world's
# Theme A (so the album blends), the duduk answers Theme R on the ride, asks
# the unanswered question in the wait, and plays the broken fragments in the
# emptiness coda.

voice_L = np.zeros(N)
voice_R = np.zeros(N)


def place_voice(notes, t0, pan_pos, gain=1.0, lp=2200, ney=False):
    v = voice_phrase(notes, lp=lp, ney=ney)
    add_at(voice_L, v, t0, gain * np.cos(pan_pos * np.pi / 2))
    add_at(voice_R, v, t0, gain * np.sin(pan_pos * np.pi / 2))


b2s = lambda nb: nb * BEAT

# I. Dawn — the ney-call, Theme A's shape (D F# E♭ D), the world waking
place_voice([(62, 1.1), (66, 0.9), (63, 0.8), (62, 2.4)], 8.5, 0.55, 1.0, ney=True)

# II. the ride — the duduk answers Theme R an octave up, over the oud
place_voice([(74, b2s(2)), (78, b2s(1)), (79, b2s(1)), (81, b2s(2)),
             (82, b2s(2)), (81, b2s(1)), (79, b2s(1)), (78, b2s(2)),
             (75, b2s(2)), (74, b2s(4))],
            bar_t(B_RIDE2 + 2), 0.45, 0.85)

# III. the wait — one question, a held F# leaning toward E♭, never resolving
place_voice([(66, 5.0), (63, 4.0)], bar_t(B_WAITB), 0.5, 0.95, lp=1900)

peak = max(np.max(np.abs(voice_L)), np.max(np.abs(voice_R)), 1e-12)
# (the coda fragments are added AFTER reverb below, into a separate buffer)
voice_dry_peak = peak


# ---------------------------------------------------------------- strings
# Tremolo string bed for the wait and the hunt: detuned additive bow tone,
# bandpassed, fast tremolo touching silence each cycle (anti-tinnitus). The
# augmented-second voicing (E♭ over D, F# above) is the Hijaz tension.

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


str_L = np.zeros(N)
str_R = np.zeros(N)

# the wait: D with the flat second E♭ and the third F# — held Hijaz friction
sw = tremolo_strings([62, 63, 66], (B_HUNT - B_WAIT) * BAR)
add_at(str_L, sw, bar_t(B_WAIT), 0.9)
add_at(str_R, sw, bar_t(B_WAIT), 0.8)
# the hunt: brighter, higher — D with the flat second on top
sw = tremolo_strings([62, 69, 75], (B_KILL - B_HUNT) * BAR, trem_hz=12.0)
add_at(str_L, sw, bar_t(B_HUNT), 0.7)
add_at(str_R, sw, bar_t(B_HUNT), 0.8)

str_L = reverb(str_L, IR_L, wet=0.45)
str_R = reverb(str_R, IR_R, wet=0.45)
peak = max(np.max(np.abs(str_L)), np.max(np.abs(str_R)), 1e-12)
str_L /= peak
str_R /= peak


# ---------------------------------------------------------------- riser
# One riser launches the hunt out of the wait.

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


rise_L = np.zeros(N)
rise_R = np.zeros(N)
rz = riser(2.0 * BAR)
add_at(rise_L, rz, bar_t(B_HUNT - 2), 0.85)
add_at(rise_R, rz, bar_t(B_HUNT - 2), 1.0)
peak = max(np.max(np.abs(rise_L)), np.max(np.abs(rise_R)), 1e-12)
rise_L /= peak
rise_R /= peak


# ---------------------------------------------------------------- the kill
# One decisive blow, then the groove stops. NOT the worm (night_pursuit's
# "the desert wins") — a man's blade: a sub-boom body under a short metallic
# ring. The biggest low event of the track; everything rhythmic has already
# ended at B_KILL, so the silence after the ring is the kill landing.

strike_L = np.zeros(N)
strike_R = np.zeros(N)
T_KILL = bar_t(B_KILL)

# the blow: brown-noise body + falling sub core (60 -> 30 Hz)
n = int(7.0 * SR)
tb = np.arange(n) / SR
sos_boom = signal.butter(4, 150, "low", fs=SR, output="sos")
brown = np.cumsum(rng.standard_normal(n))
brown -= np.linspace(brown[0], brown[-1], n)
brown /= np.max(np.abs(brown)) + 1e-12
env = (1 - np.exp(-tb / 0.03)) * np.exp(-tb / 1.8)
body = signal.sosfilt(sos_boom, brown * env)
fsub = 30.0 + 30.0 * np.exp(-tb * 2.0)
core = np.sin(2 * np.pi * np.cumsum(fsub) / SR) * env
add_at(strike_L, body * 0.7 + core * 0.65, T_KILL, 1.0)
add_at(strike_R, body * 0.7 + core * 0.65, T_KILL, 1.0)

# the blade: a short metallic ring — inharmonic damped partials + a bright
# bandpassed transient, dry-ish (30% reverb), gone in under a second.
nb = int(0.9 * SR)
tbl = np.arange(nb) / SR
blade = np.zeros(nb)
for fr, g, dec in [(2300.0, 1.0, 18.0), (3470.0, 0.6, 22.0),
                   (5150.0, 0.35, 30.0), (6900.0, 0.2, 40.0)]:
    blade += g * np.sin(2 * np.pi * fr * tbl) * np.exp(-tbl * dec)
sos_bl = signal.butter(2, [2000, 8000], "bandpass", fs=SR, output="sos")
shing = signal.sosfilt(sos_bl, rng.standard_normal(nb)) * np.exp(-tbl * 60.0)
shing /= np.max(np.abs(shing)) + 1e-12
blade = (blade / (np.max(np.abs(blade)) + 1e-12) + 0.5 * shing) * (1 - np.exp(-tbl * 1500))
add_at(strike_L, blade, T_KILL, 0.5)
add_at(strike_R, blade, T_KILL + 0.004, 0.45)      # tiny ITD = it cuts across

strike_L = reverb(strike_L, IR_L, wet=0.35)
strike_R = reverb(strike_R, IR_R, wet=0.35)
peak = max(np.max(np.abs(strike_L)), np.max(np.abs(strike_R)), 1e-12)
strike_L /= peak
strike_R /= peak


# ---------------------------------------------------------------- emptiness
# The hollow after. A coda drone that sinks 6% with a faint flat-second
# partial (the agony recipe from fall_of_arrakeen), the lone broken duduk
# playing Theme R in dying fragments, and one far hoofbeat that never repeats.

coda_L = np.zeros(N)
coda_R = np.zeros(N)
T_CODA = T_KILL + 2.0
cd = DURATION - T_CODA
nc = int(cd * SR)
tc = np.arange(nc) / SR
f_sink = midi_to_hz(26) * (1.0 - 0.06 * np.clip(tc / cd, 0, 1))   # sags 6%
sink = (np.sin(2 * np.pi * np.cumsum(f_sink) / SR) +
        0.5 * np.sin(2 * np.pi * np.cumsum(2 * f_sink) / SR + 0.3) +
        0.22 * np.sin(2 * np.pi * np.cumsum(f_sink * 2 ** (1 / 12)) / SR))  # flat-2 agony
sink_env = np.clip(tc / 3.0, 0, 1) * np.clip((cd - tc) / 10.0, 0, 1)
sink *= sink_env
sink /= np.max(np.abs(sink)) + 1e-12
add_at(coda_L, sink, T_CODA, 1.0)
add_at(coda_R, sink, T_CODA, 1.0)

peak = max(np.max(np.abs(coda_L)), np.max(np.abs(coda_R)), 1e-12)
coda_L /= peak
coda_R /= peak

# broken Theme R fragments in the duduk — added into the voice buffer, then
# the whole voice buffer is reverbed together below.
frag_L = np.zeros(N)
frag_R = np.zeros(N)


def place_frag(notes, t0, pan_pos, gain, lp):
    v = voice_phrase(notes, lp=lp)
    add_at(frag_L, v, t0, gain * np.cos(pan_pos * np.pi / 2))
    add_at(frag_R, v, t0, gain * np.sin(pan_pos * np.pi / 2))


# the rider's theme, remembered in pieces, each dying into silence
place_frag([(62, 1.6), (66, 1.3)], T_KILL + 6.0, 0.5, 0.9, 1700)
place_frag([(67, 1.2), (66, 1.0), (63, 2.6)], T_KILL + 16.0, 0.45, 0.8, 1550)
place_frag([(62, 1.4), (66, 1.1)], T_KILL + 30.0, 0.55, 0.65, 1450)
place_frag([(63, 4.5)], T_KILL + 44.0, 0.5, 0.5, 1300)        # the last note: the flat second, alone

# add the dry fragments into the (still dry) voice buffer before reverb
voice_L += frag_L
voice_R += frag_R
voice_L = reverb(voice_L, IR_L, wet=0.68)
voice_R = reverb(voice_R, IR_R, wet=0.68)
peak = max(np.max(np.abs(voice_L)), np.max(np.abs(voice_R)), 1e-12)
voice_L /= peak
voice_R /= peak

# one far hoofbeat near the end — the horse walking away, riderless
far = make_hoof(lead=False)
add_at(coda_L, far, DURATION - 11.0, 0.16)
add_at(coda_R, far, DURATION - 11.0, 0.10)


# ---------------------------------------------------------------- mix
# Energy curve ducks the calm layers (wind/drone/shimmer) as the ride and
# hunt intensify, and floods them back in the wait and the long emptiness.

energy_pts = [(0.0, 0.0), (GRID0 - 1.0, 0.10), (GRID0 + 1.0, 0.45),
              (bar_t(B_RIDE2), 0.45), (bar_t(B_RIDE2) + 1.0, 0.58),
              (bar_t(B_RIDE3), 0.58), (bar_t(B_RIDE3) + 1.0, 0.72),
              (bar_t(B_WAIT) - 0.3, 0.72), (bar_t(B_WAIT) + 0.5, 0.22),
              (bar_t(B_HUNT) - 0.5, 0.30), (bar_t(B_HUNT) + 0.5, 0.92),
              (bar_t(B_HUNT2), 0.92), (bar_t(B_HUNT2) + 0.5, 1.0),
              (T_KILL, 1.0), (T_KILL + 1.5, 0.08),
              (DURATION, 0.0)]
energy = np.interp(t, [p[0] for p in energy_pts], [p[1] for p in energy_pts])
calm = 1.0 - 0.45 * energy
# Aftermath duck: the emptiness must be QUIETER than the dawn (CLAUDE.md
# rule) — ramp the calm bus down to 0.70 over 3 s after the kill and hold.
aft = np.clip((t - (T_KILL + 1.5)) / 3.0, 0, 1)
calm *= (1.0 - 0.30 * aft)

L = (0.26 * wind_L * calm + 0.22 * drone * calm + 0.20 * shimmer_L +
     0.30 * hoof_L + 0.09 * tick_L + 0.28 * bass_L + 0.32 * war_L +
     0.22 * drum_L + 0.20 * oud_L + 0.21 * voice_L + 0.15 * str_L +
     0.11 * rise_L + 0.75 * strike_L + 0.13 * coda_L)
R = (0.26 * wind_R * calm + 0.22 * drone * calm + 0.20 * shimmer_R +
     0.30 * hoof_R + 0.09 * tick_R + 0.28 * bass_R + 0.32 * war_R +
     0.22 * drum_R + 0.20 * oud_R + 0.21 * voice_R + 0.15 * str_R +
     0.11 * rise_R + 0.75 * strike_R + 0.13 * coda_R)

fade(L, fade_in=8.0, fade_out=16.0)
fade(R, fade_in=8.0, fade_out=16.0)

peak = max(np.max(np.abs(L)), np.max(np.abs(R)))
L = L / peak * 0.88
R = R / peak * 0.88

stereo = np.empty((N, 2))
stereo[:, 0] = L
stereo[:, 1] = R
pcm = (stereo * 32767.0).astype(np.int16)

OUT_DIR = "/workspace/music"
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, "kanly.wav")
with wave.open(OUT, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())

print(f"Created: {os.path.abspath(OUT)}")
print(f"Duration: {N / SR:.1f} s  |  {SR} Hz stereo, 16-bit PCM  |  {BPM:.0f} BPM")
print("Section map:")
for name, b in [("the ride (gallop + Theme R)", B_RIDE),
                ("fuller ride + duduk answer", B_RIDE2),
                ("peak open ride (+darbuka)", B_RIDE3),
                ("THE WAIT (tick + strings)", B_WAIT),
                ("the wait — duduk's question", B_WAITB),
                ("THE HUNT (gallop slams back)", B_HUNT),
                ("Theme R octave up, urgent", B_HUNT2),
                ("peak chase", B_HUNT3),
                ("THE KILL", B_KILL)]:
    print(f"  {bar_t(b):6.1f} s  bar {b:2d}  {name}")
print(f"  {T_KILL + 2.0:6.1f} s  emptiness coda (broken Theme R fragments)")
print(f"  {DURATION:6.1f} s  end")
