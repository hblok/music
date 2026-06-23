#!/usr/bin/env python3
"""
generate_fall_of_arrakeen.py — "The Fall of Arrakeen" (~6:05). War psy,
built from listening feedback on the_sleeper_awakens:

  * "we don't have a beat which shakes the entire room" — the kick is
    now a KICK STACK: the punch+click trance kick PLUS a long sub tail
    (60 -> 41 Hz, ~0.42 s — nearly a full beat at 148 BPM) so the low
    end never stops moving, and the master gets a LOW-shelf to match
    the high-shelf. The room-shaker.
  * "could afford more complexity" — ~24 committed layers (~35+ voices
    counting sub-components) vs ~16 in the earlier psy tracks: field
    snare, war horn, battle toms, shaker, reverse cymbals, oud and
    explosions join the established machinery.
  * "we need a new Theme and melody" — Theme WAR, martial and dotted,
    with a Bb->A "war cry" fall (an interval no earlier theme leans
    on); two new acid riffs built on the same cry; and Theme L, the
    dying-fall lament, for the aftermath.

The story: preparation for war — buildup and launch — ATTACK!! FIGHT!!
— then the aftermath: the silence, agony, death.

  0:00  Wind, drone; one distant horn. The army wakes.
  0:10  PREPARATION: the field-snare march (the section's identity),
        slow war drums, the oud war riff assembling, chant every bar.
  0:36  MUSTER: the kick enters (held back), bass at 0:49, the dark
        acid at 1:02 — the horn states the war call.
  1:15  THE RISE: snare rolls, riser, kick rolls — a long horn blast —
  1:28  LAUNCH (48 bars): full war groove on the kick stack. Phases:
        war riff / high acid + horn / mini-dip (bass + snare march —
        a glimpse of the battlefield) / peak.
  2:46  REGROUP: kick gone — march + chant + distant detonations.
  2:59  Second rise: rolls, riser, horn —
  3:12  THE FIGHT (64 bars): war drums + battle toms over the stack.
        Phases: melee / high acid + horn calls / mini-dip (kick +
        chant — the war cry) / peak ride / dip + riser / THE SPRINT
        (kick on 8ths, the fastest music on the album) — ending in
  4:55  THE DEATH BLOW: one huge detonation kills everything. The
        aftermath: wind, falling rumbles, a decelerating heartbeat
        that stops, the duduk lament (Theme L) ending in a dying
        fall, a sinking drone with a faint flat-second shimmer (the
        agony), one far horn over the burning city. Death is quiet.

v2 — "the BASS is still not there. The BAM BAM BAM BAM 4-to-the-floor
which really makes the wall vibrate. It needs to be a lot deeper and
heavier." Five changes, all low-end:

  1. the kick goes DEEPER: punch lands at 44 Hz (was 48), the sub tail
     lands on D1 itself (37 Hz, was 41), hotter and slower to decay;
  2. a dedicated SUB BOOM layer — a pure 50->37 Hz sine on EVERY
     4-on-the-floor beat that sustains the full beat and releases just
     before the next hit, committed as its own layer so peak
     normalization can't trade it against the punch;
  3. sidechain pump: bass and drone duck ~55 % at every kick and
     recover over the beat — the kick owns the sub alone, and the
     pumping itself is the wall-vibrating BAM BAM BAM feel;
  4. kick weight 0.42 -> 0.50;
  5. a second master low shelf at 55 Hz on top of the 95 Hz one
     (~+5 dB total below 55 Hz).

Output: /workspace/music/fall_of_arrakeen_v2.wav (stereo, 44100 Hz, 16-bit).
"""

import os
import wave
import numpy as np
from scipy import signal

SR = 44100
DURATION = 365.0
N = int(SR * DURATION)
t = np.arange(N) / SR

rng = np.random.default_rng(10191)   # the year the war comes

BPM = 148.0
BEAT = 60.0 / BPM
BAR = BEAT * 4
STEP = BEAT / 4
GRID0 = 10.0


def bar_t(b, beat=0.0):
    return GRID0 + b * BAR + beat * BEAT


# section boundaries, in bars
B_PREP = 0        # snare march, war drums, oud, chant (16 bars)
B_MUSTER = 16     # kick enters; bass +8; dark acid +16 (24 bars)
B_RISE = 40       # build (8 bars)
B_LAUNCH = 48     # LAUNCH (48 bars)
B_REGROUP = 96    # march + chant + detonations (8 bars)
B_RISE2 = 104     # build 2 (8 bars)
B_FIGHT = 112     # THE FIGHT (64 bars)
B_AFTER = 176     # the death blow; aftermath to the end

# mini-dips and the sprint
DIP_L = set(range(B_LAUNCH + 32, B_LAUNCH + 36))   # bass + snare march
DIP_F = set(range(B_FIGHT + 32, B_FIGHT + 36))     # kick + chant war cry
DIP_F2 = set(range(B_FIGHT + 52, B_FIGHT + 56))    # bass + snare + riser
SPRINT = set(range(B_FIGHT + 56, B_AFTER))         # kick on 8ths
ALL_DIPS = DIP_L | DIP_F | DIP_F2

N_LAYERS = 0


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
    """NEW — war horn: brassy harmonic stack with a pitch scoop into the
    phrase, a slow 31 Hz growl, and a formant bump around 450-900 Hz.
    Think carnyx / Sardaukar signal horn."""
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


IR_L = make_reverb_ir(5.0, 1.6, 7)
IR_R = make_reverb_ir(5.0, 1.6, 11)

mix_L = np.zeros(N)
mix_R = np.zeros(N)


def commit(layer_L, layer_R, weight, env=None):
    global mix_L, mix_R, N_LAYERS
    N_LAYERS += 1
    peak = max(np.max(np.abs(layer_L)), np.max(np.abs(layer_R)), 1e-12)
    if env is None:
        mix_L += layer_L * (weight / peak)
        mix_R += layer_R * (weight / peak)
    else:
        mix_L += layer_L * env * (weight / peak)
        mix_R += layer_R * env * (weight / peak)


after_t = bar_t(B_AFTER)
energy_pts = [(0.0, 0.0), (GRID0 - 0.5, 0.0), (GRID0 + 0.5, 0.35),
              (bar_t(B_MUSTER), 0.40), (bar_t(B_MUSTER) + 0.5, 0.55),
              (bar_t(B_RISE), 0.65), (bar_t(B_LAUNCH) - 0.1, 0.75),
              (bar_t(B_LAUNCH) + 0.3, 0.95),
              (bar_t(B_REGROUP), 0.95), (bar_t(B_REGROUP) + 0.3, 0.45),
              (bar_t(B_RISE2), 0.55), (bar_t(B_FIGHT) - 0.1, 0.80),
              (bar_t(B_FIGHT) + 0.3, 1.0),
              (after_t, 1.0), (after_t + 0.5, 0.15),
              (after_t + 20.0, 0.10), (DURATION, 0.0)]
energy = np.interp(t, [p[0] for p in energy_pts], [p[1] for p in energy_pts])
calm = 1.0 - 0.45 * energy
# after the death blow the wind/drone must NOT swell back to ambient-track
# level: death is quieter than the march
calm *= np.interp(t, [0.0, after_t, after_t + 4.0, DURATION],
                  [1.0, 1.0, 0.78, 0.70])


def groove_on(b):
    """Bars where the dance machinery plays at all."""
    return B_MUSTER <= b < B_AFTER and not (B_REGROUP <= b < B_RISE2)


# v2 — sidechain pump: every 4-on-the-floor kick ducks the sustained
# low end (bass, drone) by ~55 % and lets it swell back over the beat.
# The kick owns the sub alone, and the pumping IS the wall-shake feel.
pump = np.ones(N)
_dipn = int(0.30 * SR)
_dip = 0.55 * np.exp(-np.arange(_dipn) / SR / 0.10)
for _b in range(B_AFTER):
    if not groove_on(_b):
        continue
    for _beat in range(4):
        _i0 = int(bar_t(_b, _beat) * SR)
        _end = min(N, _i0 + _dipn)
        pump[_i0:_end] = np.minimum(pump[_i0:_end], 1.0 - _dip[: _end - _i0])
np.clip(pump, 0.30, 1.0, out=pump)


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
commit(drone, drone, 0.20, env=calm * pump)   # v2: pumped under the kick
del drone, breath
print("wind + drone committed")


# ---------------------------------------------------------------- kick stack
# NEW — the room-shaker: punch + click as before, PLUS a long sub tail
# (60 -> 41 Hz over ~0.42 s — nearly a full beat at 148) so the low end
# never stops moving between hits. The sprint alternates the full stack
# on the beat with a punch-only kick on the offbeat 8ths.

def make_kick_stack(sub=True):
    n = int(0.42 * SR)
    td = np.arange(n) / SR
    f_curve = 44.0 + 106.0 * np.exp(-td * 50.0)     # v2: lands at 44 Hz
    punch = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    sos_c = signal.butter(2, [1800, 9000], "bandpass", fs=SR, output="sos")
    click = signal.sosfilt(sos_c, rng.standard_normal(n)) * np.exp(-td * 700)
    click /= np.max(np.abs(click)) + 1e-12
    env_p = (1 - np.exp(-td / 0.0008)) * np.exp(-td * 9.0)
    x = (punch + 0.50 * click) * env_p              # v2: click up — the sub is
    if sub:                                         # hotter, the BAM must cut
        f_sub = 37.0 + 18.0 * np.exp(-td * 9.0)    # v2: lands on D1 (36.7 Hz)
        tail = np.sin(2 * np.pi * np.cumsum(f_sub) / SR)
        env_s = (1 - np.exp(-td / 0.004)) * np.exp(-td * 3.0)   # v2: longer
        x = x + 1.15 * tail * env_s                 # v2: 0.85 -> 1.15
    return x / (np.max(np.abs(x)) + 1e-12)


KICK = make_kick_stack()
KICK_P = make_kick_stack(sub=False)

lay_L = np.zeros(N)
lay_R = np.zeros(N)
for b in range(B_AFTER):
    if not groove_on(b) or b in DIP_F2:
        continue
    g = 1.0
    if b in (B_RISE + 6, B_RISE2 + 6):              # 8th-note roll bar
        for e in range(8):
            gg = g * 0.85 * (0.55 + 0.45 * e / 7)   # rolls must peak BELOW
            add_at(lay_L, KICK_P, bar_t(b, e * 0.5), gg)
            add_at(lay_R, KICK_P, bar_t(b, e * 0.5), gg)
        continue
    if b in (B_RISE + 7, B_RISE2 + 7):              # 16th-note roll bar
        for s in range(16):
            gg = g * 0.85 * (0.55 + 0.45 * s / 15)  # the drop, or they steal
            # normalization headroom from the whole track
            add_at(lay_L, KICK_P, bar_t(b, s * 0.25), gg)
            add_at(lay_R, KICK_P, bar_t(b, s * 0.25), gg)
        continue
    if B_RISE <= b < B_RISE + 6 or B_RISE2 <= b < B_RISE2 + 6:
        g *= 0.6                                    # builds: kick held back
    elif b < B_LAUNCH:
        g *= 0.72                                   # pre-launch headroom
    for beat in range(4):
        add_at(lay_L, KICK, bar_t(b, beat), g)
        add_at(lay_R, KICK, bar_t(b, beat), g)
        if b in SPRINT:                             # 8ths: the sprint
            add_at(lay_L, KICK_P, bar_t(b, beat + 0.5), g * 0.65)
            add_at(lay_R, KICK_P, bar_t(b, beat + 0.5), g * 0.65)
commit(lay_L, lay_R, 0.50)                          # v2: 0.42 -> 0.50
print("kick stack committed")


# ---------------------------------------------------------------- sub boom
# v2 NEW — the wall-vibrator: a pure 50 -> 37 Hz sine under EVERY
# 4-on-the-floor kick, sustaining the whole beat and releasing just
# before the next hit. Its own layer, so peak normalization cannot
# trade it against the punch/click — the sub is unconditional.

def make_sub_boom():
    n = int(0.40 * SR)                              # beat at 148 is 0.405 s
    td = np.arange(n) / SR
    f_curve = 37.0 + 13.0 * np.exp(-td * 12.0)
    x = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    env = ((1 - np.exp(-td / 0.003)) * np.exp(-td * 1.2) *
           np.clip((0.40 - td) / 0.06, 0, 1))       # release before next hit
    return x * env


BOOM = make_sub_boom()

lay_L[:] = 0.0
lay_R[:] = 0.0
for b in range(B_AFTER):
    if not groove_on(b) or b in DIP_F2:
        continue
    if b in (B_RISE + 6, B_RISE + 7, B_RISE2 + 6, B_RISE2 + 7):
        continue                                    # roll bars: no boom
    g = 1.0
    if B_RISE <= b < B_RISE + 6 or B_RISE2 <= b < B_RISE2 + 6:
        g *= 0.5
    elif b < B_LAUNCH:
        g *= 0.6
    for beat in range(4):
        add_at(lay_L, BOOM, bar_t(b, beat), g)
        add_at(lay_R, BOOM, bar_t(b, beat), g)
commit(lay_L, lay_R, 0.30)
print("sub boom committed")


# ---------------------------------------------------------------- psy bass

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
for b in range(B_AFTER):
    if b < B_MUSTER + 8 or not groove_on(b) or b in DIP_F:
        continue
    g = 1.0
    if b < B_LAUNCH or B_RISE2 <= b < B_FIGHT:
        g *= 0.65          # pre-drop headroom: sustained bass carries the RMS
    for beat in range(4):
        for s, gg in [(1, 0.8), (2, 0.7), (3, 0.95)]:
            m = 38
            if b % 4 == 3 and beat == 3:
                m = [36, 39, 38][s - 1]             # cadence walk
            elif B_FIGHT <= b and beat == 3 and s == 3:
                m = 50                              # octave flick
            add_at(lay_L, PB[m], bar_t(b, beat + s * 0.25), g * gg)
            add_at(lay_R, PB[m], bar_t(b, beat + s * 0.25), g * gg)
commit(lay_L, lay_R, 0.29, env=pump)   # v2: pumped — the kick owns the sub
print("psy bass committed")


# ---------------------------------------------------------------- hats + shaker

def make_hat(open_=False):
    n = int((0.16 if open_ else 0.045) * SR)
    td = np.arange(n) / SR
    sos_h = signal.butter(4, 6500 if open_ else 7000, "high",
                          fs=SR, output="sos")
    x = signal.sosfilt(sos_h, rng.standard_normal(n))
    x *= np.exp(-td * (24 if open_ else 100))
    return x / (np.max(np.abs(x)) + 1e-12)


def make_shaker():
    """NEW — soft 16th-note shaker: bp 3.5-9.5 kHz, fast but rounded."""
    n = int(0.055 * SR)
    td = np.arange(n) / SR
    sos_s = signal.butter(2, [3500, 9500], "bandpass", fs=SR, output="sos")
    x = signal.sosfilt(sos_s, rng.standard_normal(n))
    x *= np.exp(-td * 55) * (1 - np.exp(-td / 0.003))
    return x / (np.max(np.abs(x)) + 1e-12)


OHAT = make_hat(open_=True)
CHAT = make_hat()
SHAKER = make_shaker()

lay_L[:] = 0.0
lay_R[:] = 0.0
for b in range(B_AFTER):
    if not groove_on(b) or b in ALL_DIPS:
        continue
    for beat in range(4):
        add_at(lay_L, OHAT, bar_t(b, beat + 0.5), 0.8)
        add_at(lay_R, OHAT, bar_t(b, beat + 0.5), 1.0)
    if B_LAUNCH <= b:                               # closed 16th ghosts
        for s in range(16):
            if s % 2 == 0:
                continue
            p = 0.3 + 0.4 * ((s // 2) % 2)
            add_at(lay_L, CHAT, bar_t(b, s * 0.25),
                   0.35 * np.cos(p * np.pi / 2))
            add_at(lay_R, CHAT, bar_t(b, s * 0.25),
                   0.35 * np.sin(p * np.pi / 2))
commit(lay_L, lay_R, 0.12)
print("hats committed")

lay_L[:] = 0.0
lay_R[:] = 0.0
SHK_G = [0.9, 0.4, 0.65, 0.4]
for b in range(B_AFTER):
    if b < B_MUSTER + 8 or not groove_on(b) or b in ALL_DIPS:
        continue
    for s in range(16):
        g = SHK_G[s % 4]
        add_at(lay_L, SHAKER, bar_t(b, s * 0.25), g * 0.95)
        add_at(lay_R, SHAKER, bar_t(b, s * 0.25), g * 0.75)
commit(lay_L, lay_R, 0.07)
print("shaker committed")


# ---------------------------------------------------------------- clap

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


CLAP = make_clap()

lay_L[:] = 0.0
lay_R[:] = 0.0
for b in range(B_AFTER):
    if not (B_LAUNCH <= b < B_REGROUP or B_FIGHT <= b < B_AFTER):
        continue
    if b in ALL_DIPS:
        continue
    for beat in (1, 3):
        p = 0.42 if beat == 1 else 0.58
        add_at(lay_L, CLAP, bar_t(b, beat), np.cos(p * np.pi / 2))
        add_at(lay_R, CLAP, bar_t(b, beat), np.sin(p * np.pi / 2))
commit(lay_L, lay_R, 0.11)
print("clap committed")


# ---------------------------------------------------------------- field snare
# NEW — the military march: tone pair (185 + 330 Hz) + bright snappy
# noise; drag ghosts before accents; buzz-roll crescendos every fourth
# bar and through the rises. The identity of the PREPARATION section.

def make_snare(buzz=False):
    n = int((0.07 if buzz else 0.17) * SR)
    td = np.arange(n) / SR
    sos_n = signal.butter(2, [1500, 9000], "bandpass", fs=SR, output="sos")
    nz = signal.sosfilt(sos_n, rng.standard_normal(n))
    nz /= np.max(np.abs(nz)) + 1e-12
    tone = (np.sin(2 * np.pi * 185.0 * td) +
            0.7 * np.sin(2 * np.pi * 330.0 * td)) * np.exp(-td * 40)
    env = np.exp(-td * (70.0 if buzz else 26.0)) * (1 - np.exp(-td / 0.001))
    x = (0.8 * nz + 0.5 * tone) * env
    return x / (np.max(np.abs(x)) + 1e-12)


SNARE = make_snare()
SBUZZ = make_snare(buzz=True)

# march bar: (step, gain, accent) — accents get a two-ghost drag before
MARCH = [(0, 1.00, True), (2, 0.35, False), (4, 0.55, False),
         (6, 0.35, False), (7, 0.35, False), (8, 0.90, True),
         (10, 0.35, False), (12, 0.60, False), (14, 0.40, False),
         (15, 0.40, False)]


def snare_march_bar(layL, layR, b, level):
    roll_bar = b % 4 == 3
    for s, g, acc in MARCH:
        if roll_bar and s >= 12:
            break
        st = bar_t(b, s * 0.25)
        if acc:
            add_at(layL, SBUZZ, st - 0.060, 0.30 * level)
            add_at(layL, SBUZZ, st - 0.030, 0.35 * level)
            add_at(layR, SBUZZ, st - 0.060, 0.25 * level)
            add_at(layR, SBUZZ, st - 0.030, 0.30 * level)
        add_at(layL, SNARE, st, g * level * 0.95)
        add_at(layR, SNARE, st, g * level * 0.80)
    if roll_bar:                                    # buzz-roll crescendo
        for i in range(8):
            st = bar_t(b, 3.0 + i * 0.125)
            g = (0.3 + 0.7 * i / 7) * level
            add_at(layL, SBUZZ, st, g * 0.9)
            add_at(layR, SBUZZ, st, g * 0.75)


lay_L[:] = 0.0
lay_R[:] = 0.0
for b in range(B_AFTER):
    march_sec = (b < B_MUSTER or B_REGROUP <= b < B_RISE2 or
                 b in DIP_L or b in DIP_F2)
    if march_sec:
        lvl = min(1.0, 0.45 + 0.55 * b / 8) if b < B_MUSTER else 0.9
        snare_march_bar(lay_L, lay_R, b, lvl)
    elif B_RISE <= b < B_LAUNCH or B_RISE2 <= b < B_FIGHT:
        for i in range(16):                         # rise: full-bar roll
            frac = (b % 8 * 16 + i) / 127.0
            add_at(lay_L, SBUZZ, bar_t(b, i * 0.25), (0.25 + 0.45 * frac))
            add_at(lay_R, SBUZZ, bar_t(b, i * 0.25), (0.20 + 0.40 * frac))
    elif groove_on(b) and b not in DIP_F:           # battle: backbeat only
        for s in (4, 12):
            add_at(lay_L, SBUZZ, bar_t(b, s * 0.25) - 0.030, 0.25)
            add_at(lay_L, SNARE, bar_t(b, s * 0.25), 0.50)
            add_at(lay_R, SNARE, bar_t(b, s * 0.25), 0.42)
commit(lay_L, lay_R, 0.14)
print("field snare committed")


# ---------------------------------------------------------------- battle toms
# NEW — three pitched toms (165/110/80 Hz), syncopated two-bar pattern
# through the fight, descending full runs as fills every 8th bar.

def make_tom(f0):
    n = int(0.28 * SR)
    td = np.arange(n) / SR
    f_curve = f0 * (1.0 + 0.4 * np.exp(-td * 30.0))
    body = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    sos_sk = signal.butter(2, [300, 1500], "bandpass", fs=SR, output="sos")
    skin = signal.sosfilt(sos_sk, rng.standard_normal(n)) * np.exp(-td * 35)
    skin /= np.max(np.abs(skin)) + 1e-12
    env = np.exp(-td * 9.0) * (1 - np.exp(-td / 0.004))
    x = (body + 0.4 * skin) * env
    return x / (np.max(np.abs(x)) + 1e-12)


TOM_H, TOM_M, TOM_L = make_tom(165), make_tom(110), make_tom(80)
TOM_PAT = {3: TOM_H, 6: TOM_M, 11: TOM_L, 14: TOM_M}

lay_L[:] = 0.0
lay_R[:] = 0.0
for b in range(B_AFTER):
    in_toms = (B_FIGHT <= b < B_AFTER or B_LAUNCH + 36 <= b < B_REGROUP)
    if not in_toms or b in ALL_DIPS:
        continue
    heavy = 1.0 if b in SPRINT else 0.7
    if b % 8 == 7:                                  # descending fill run
        run = [TOM_H, TOM_H, TOM_M, TOM_M, TOM_L, TOM_M, TOM_L, TOM_L]
        for i, tom in enumerate(run):
            st = bar_t(b, 2.0 + i * 0.25)
            p = 0.3 + 0.4 * (i / 7)
            add_at(lay_L, tom, st, heavy * np.cos(p * np.pi / 2))
            add_at(lay_R, tom, st, heavy * np.sin(p * np.pi / 2))
        continue
    for s, tom in TOM_PAT.items():
        if b % 2 == 1 and s in (3, 11):
            continue                                # alternate-bar variation
        p = 0.35 if s in (3, 14) else 0.65
        add_at(lay_L, tom, bar_t(b, s * 0.25), heavy * 0.8 * np.cos(p * np.pi / 2))
        add_at(lay_R, tom, bar_t(b, s * 0.25), heavy * 0.8 * np.sin(p * np.pi / 2))
commit(lay_L, lay_R, 0.16)
print("battle toms committed")


# ---------------------------------------------------------------- war drums

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
for b in range(B_PREP, B_MUSTER):                   # preparation: slow hits
    add_at(lay_L, WAR, bar_t(b, 0.0), 0.5 + 0.03 * b)
    add_at(lay_R, WAR, bar_t(b, 0.0), 0.5 + 0.03 * b)
for b in range(B_FIGHT, B_AFTER):
    if b in ALL_DIPS:
        continue
    g = 1.0 if b % 8 == 0 else 0.55
    add_at(lay_L, WAR, bar_t(b, 0.0), g)
    add_at(lay_R, WAR, bar_t(b, 0.0), g)
    if b % 4 == 2 or b in SPRINT:
        add_at(lay_L, WAR, bar_t(b, 2.0), 0.5)
        add_at(lay_R, WAR, bar_t(b, 2.0), 0.5)
commit(lay_L, lay_R, 0.22)
print("war drums committed")


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


DOUM = make_doum()
TEK = make_tek()
KA = make_tek(ghost=True)
MAQSUM = {0: "D", 2: "T", 6: "T", 8: "D", 12: "T"}

lay_L[:] = 0.0
lay_R[:] = 0.0
for b in range(B_AFTER):
    in_drop = (B_LAUNCH + 16 <= b < B_REGROUP or B_FIGHT <= b < B_AFTER)
    if not in_drop or b in ALL_DIPS:
        continue
    level = 0.6
    fill_bar = b % 8 == 3                  # offset from the tom fills (b%8==7)
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
commit(lay_L, lay_R, 0.13)
print("darbuka committed")


# ---------------------------------------------------------------- oud
# The war riff — eighth-note drive with the Bb->A cry at the bar's heart.

OUD = {m: oud_note(m) for m in (50, 51, 54, 57, 58, 48)}
OUD_RIFF = [50, None, 50, None, 51, None, 50, None,
            58, 57, None, 50, 54, None, 51, 50]

lay_L[:] = 0.0
lay_R[:] = 0.0
for b in range(B_AFTER):
    in_oud = (4 <= b < B_RISE or B_LAUNCH <= b < B_LAUNCH + 16 or
              B_LAUNCH + 36 <= b < B_REGROUP or
              B_FIGHT + 36 <= b < B_FIGHT + 52 or b in SPRINT)
    if not in_oud or b in ALL_DIPS:
        continue
    g = min(1.0, 0.4 + 0.075 * (b - 4)) if b < B_MUSTER else 1.0
    for s, m in enumerate(OUD_RIFF):
        if m is None:
            continue
        p = 0.40 if s % 4 == 0 else 0.62
        add_at(lay_L, OUD[m], bar_t(b, s * 0.25), g * np.cos(p * np.pi / 2))
        add_at(lay_R, OUD[m], bar_t(b, s * 0.25), g * np.sin(p * np.pi / 2))
commit(lay_L, lay_R, 0.16)
print("oud committed")


# ---------------------------------------------------------------- acid
# The sharp 303 (sleeper_awakens recipe) with two NEW war riffs — both
# built on the Bb->A war cry; nothing borrowed from earlier tracks.

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


RIFF_WAR1 = [(50, 1, None), (None, 0, None), (50, 0, None), (50, 0, None),
             (None, 0, None), (50, 0, None), (51, 1, 50), (None, 0, None),
             (58, 1, 57), (57, 0, None), (None, 0, None), (50, 0, None),
             (54, 0, None), (None, 0, None), (51, 0, 50), (50, 0, None)]
RIFF_WAR2 = [(62, 1, None), (62, 0, None), (70, 0, 69), (69, 0, None),
             (None, 0, None), (66, 0, None), (63, 1, 62), (62, 0, None),
             (74, 1, None), (None, 0, None), (70, 0, None), (69, 0, None),
             (66, 0, None), (63, 0, None), (62, 1, None), (None, 0, None)]

lay_L[:] = 0.0
lay_R[:] = 0.0


def acid_bars(b0, b1, riff, cut_lo, cut_hi, gain=1.0, ramp=False):
    for b in range(b0, b1):
        frac = (b - b0) / max(1, b1 - b0)
        if ramp:
            base = cut_lo + (cut_hi - cut_lo) * frac
        else:
            base = cut_lo + (cut_hi - cut_lo) * \
                (0.5 + 0.5 * np.sin(2 * np.pi * (b - b0) / 16 - np.pi / 2))
        for s, (m, acc, sl) in enumerate(riff):
            if m is None:
                continue
            cut = base * (1.0 + 0.25 * np.sin(2 * np.pi * s / 16))
            x = acid_note(m, cut, accent=bool(acc), slide_to=sl)
            p = 0.5 + 0.18 * np.sin(2 * np.pi * (b * 16 + s) / 24)
            add_at(lay_L, x, bar_t(b, s * 0.25), gain * np.cos(p * np.pi / 2))
            add_at(lay_R, x, bar_t(b, s * 0.25), gain * np.sin(p * np.pi / 2))


acid_bars(B_MUSTER + 16, B_RISE, RIFF_WAR1, 280, 800, gain=0.7)
acid_bars(B_RISE, B_LAUNCH, RIFF_WAR1, 600, 2400, gain=0.8, ramp=True)
acid_bars(B_LAUNCH, B_LAUNCH + 16, RIFF_WAR1, 400, 2400)
acid_bars(B_LAUNCH + 16, B_LAUNCH + 32, RIFF_WAR2, 900, 3600)
#         DIP_L: acid silent — snare march holds the field
acid_bars(B_LAUNCH + 36, B_REGROUP, RIFF_WAR1, 700, 3000)
acid_bars(B_RISE2, B_FIGHT, RIFF_WAR1, 500, 3400, gain=0.8, ramp=True)
acid_bars(B_FIGHT, B_FIGHT + 16, RIFF_WAR1, 600, 3000)
acid_bars(B_FIGHT + 16, B_FIGHT + 32, RIFF_WAR2, 1000, 4200)
#         DIP_F: acid silent — the chant war cry
acid_bars(B_FIGHT + 36, B_FIGHT + 52, RIFF_WAR2, 800, 3400)
#         DIP_F2: silent
acid_bars(B_FIGHT + 56, B_AFTER, RIFF_WAR2, 1400, 5000)
commit(lay_L, lay_R, 0.17)
print(f"acid committed ({len(acid_cache)} cached notes)")


# ---------------------------------------------------------------- zaps

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
zap_bars = [B_LAUNCH, B_LAUNCH + 8, B_LAUNCH + 16, B_LAUNCH + 24,
            B_LAUNCH + 36, B_LAUNCH + 44,
            B_FIGHT, B_FIGHT + 8, B_FIGHT + 16, B_FIGHT + 24,
            B_FIGHT + 36, B_FIGHT + 44, B_FIGHT + 56, B_FIGHT + 60]
for b in zap_bars:
    beat = float(rng.choice([0.0, 1.5, 3.5]))
    p = rng.uniform(0.2, 0.8)
    add_at(lay_L, ZAP, bar_t(b, beat), np.cos(p * np.pi / 2))
    add_at(lay_R, ZAP, bar_t(b, beat), np.sin(p * np.pi / 2))
lay_L = reverb(lay_L, IR_L, wet=0.35)
lay_R = reverb(lay_R, IR_R, wet=0.35)
commit(lay_L, lay_R, 0.08)
print("zaps committed")


# ---------------------------------------------------------------- war horn
# Theme WAR on the horn at the muster; blasts at the launches; calls
# through the fight; one far echo over the burning city at the end.

b2s = lambda nb: nb * BEAT

THEME_WAR = [(62, b2s(1.5)), (62, b2s(0.5)), (63, b2s(1)), (62, b2s(1)),
             (67, b2s(2)), (66, b2s(1)), (63, b2s(1)), (62, b2s(1)),
             (70, b2s(1.5)), (69, b2s(0.5)), (67, b2s(1)), (66, b2s(1)),
             (63, b2s(2)), (62, b2s(3))]
HORN_CALL = [(50, 1.2), (51, 0.6), (50, 2.2)]

lay_L = np.zeros(N)
lay_R = np.zeros(N)


def place_horn(notes, t0, pan_pos, gain=1.0, growl=0.18, lp=1600):
    h = horn_phrase(notes, growl=growl, lp=lp)
    add_at(lay_L, h, t0, gain * np.cos(pan_pos * np.pi / 2))
    add_at(lay_R, h, t0, gain * np.sin(pan_pos * np.pi / 2))


place_horn(HORN_CALL, 2.5, 0.6, 0.5, growl=0.05, lp=1100)   # distant: wake
place_horn([(m - 12, d) for m, d in THEME_WAR[:8]],
           bar_t(B_MUSTER + 8), 0.45, 0.9)                  # the war call
place_horn([(50, 3.2)], bar_t(B_RISE + 4), 0.5, 1.0, growl=0.25)
place_horn([(38, 3.2)], bar_t(B_RISE + 4), 0.5, 0.8, growl=0.25)  # octave stack
place_horn(HORN_CALL, bar_t(B_LAUNCH + 16), 0.62, 0.85)
place_horn(HORN_CALL, bar_t(B_REGROUP + 4), 0.38, 0.5, growl=0.08, lp=1100)
place_horn([(50, 3.2)], bar_t(B_RISE2 + 4), 0.5, 1.0, growl=0.25)
place_horn(HORN_CALL, bar_t(B_FIGHT + 16), 0.40, 0.85)
place_horn(HORN_CALL, bar_t(B_FIGHT + 24), 0.65, 0.85)
place_horn([(50, 2.4), (51, 1.0), (50, 1.6)],
           bar_t(B_FIGHT + 56), 0.5, 1.0, growl=0.3)        # sprint blast
place_horn([(50, 2.5), (51, 1.2), (50, 3.5)],
           after_t + 48.0, 0.55, 0.6, growl=0.05, lp=900)   # over the ruins
lay_L = reverb(lay_L, IR_L, wet=0.5)
lay_R = reverb(lay_R, IR_R, wet=0.5)
commit(lay_L, lay_R, 0.20)
print("war horn committed")


# ---------------------------------------------------------------- explosions
# The base_under_attack recipe: soft 80 ms attacks, lowpassed below
# 150 Hz, falling sub cores. Distant in the regroup, frequent in the
# fight — and THE DEATH BLOW at the end of the sprint.

def explosion(dur=3.5, sub_f=55.0):
    n = int(dur * SR)
    td = np.arange(n) / SR
    sos_e = signal.butter(4, 150, "low", fs=SR, output="sos")
    nz = signal.sosfilt(sos_e, rng.standard_normal(n))
    nz /= np.max(np.abs(nz)) + 1e-12
    env = (1 - np.exp(-td / 0.08)) * np.exp(-td * 1.8)
    f_curve = sub_f * np.exp(-td * 0.7) + 18.0
    sub = np.sin(2 * np.pi * np.cumsum(f_curve) / SR) * env
    x = nz * env + 0.8 * sub
    return x / (np.max(np.abs(x)) + 1e-12)


lay_L = np.zeros(N)
lay_R = np.zeros(N)
for t0, g, p in [(bar_t(B_REGROUP + 2), 0.45, 0.3),
                 (bar_t(B_REGROUP + 5), 0.50, 0.7),
                 (bar_t(B_LAUNCH + 33), 0.40, 0.6),
                 (bar_t(B_FIGHT + 8), 0.45, 0.25),
                 (bar_t(B_FIGHT + 22), 0.50, 0.75),
                 (bar_t(B_FIGHT + 40), 0.55, 0.4),
                 (bar_t(B_FIGHT + 48), 0.45, 0.65),
                 (after_t + 14.0, 0.35, 0.3),
                 (after_t + 31.0, 0.30, 0.7)]:
    x = explosion(rng.uniform(2.8, 4.0), rng.uniform(48, 65))
    add_at(lay_L, x, t0, g * np.cos(p * np.pi / 2))
    add_at(lay_R, x, t0, g * np.sin(p * np.pi / 2))
# THE DEATH BLOW
x = explosion(6.0, 60.0)
add_at(lay_L, x, after_t - 0.05, 1.0)
add_at(lay_R, x, after_t - 0.05, 1.0)
commit(lay_L, lay_R, 0.32)
print("explosions committed")


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
for start_s, dur_s, g in [(bar_t(B_RISE + 6), 2 * BAR, 0.9),
                          (bar_t(B_RISE2 + 6), 2 * BAR, 1.0),
                          (bar_t(B_LAUNCH + 34), 2 * BAR, 0.7),
                          (bar_t(B_FIGHT + 54), 2 * BAR, 0.8)]:
    roll = frame_roll(dur_s)
    add_at(lay_L, roll, start_s, g * 0.9)
    add_at(lay_R, roll, start_s, g)
commit(lay_L, lay_R, 0.08)
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
for b0, dur_bars in [(B_RISE + 4, 4), (B_RISE2 + 4, 4),
                     (B_LAUNCH + 32, 4), (B_FIGHT + 52, 4)]:
    rz = riser(dur_bars * BAR)
    add_at(lay_L, rz, bar_t(b0), 0.85)
    add_at(lay_R, rz, bar_t(b0), 1.0)
commit(lay_L, lay_R, 0.10)
print("risers committed")


# ---------------------------------------------------------------- rev cymbals
# NEW — reversed cymbal swells leading into every drop boundary.

def rev_cymbal(dur=1.6):
    n = int(dur * SR)
    td = np.arange(n) / SR
    sos_c = signal.butter(4, 6000, "high", fs=SR, output="sos")
    x = signal.sosfilt(sos_c, rng.standard_normal(n)) * np.exp(-td * 6.0)
    x = x[::-1].copy()
    return x / (np.max(np.abs(x)) + 1e-12)


lay_L[:] = 0.0
lay_R[:] = 0.0
for b0 in [B_LAUNCH, B_LAUNCH + 36, B_FIGHT, B_FIGHT + 36, B_FIGHT + 56]:
    rc = rev_cymbal(rng.uniform(1.3, 1.9))
    t0 = bar_t(b0) - len(rc) / SR
    p = rng.uniform(0.35, 0.65)
    add_at(lay_L, rc, t0, np.cos(p * np.pi / 2))
    add_at(lay_R, rc, t0, np.sin(p * np.pi / 2))
commit(lay_L, lay_R, 0.07)
print("reverse cymbals committed")


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
        ([62, 63], B_RISE, B_LAUNCH + 2, 11.0, 0.8, 0.7),
        ([62, 69, 63], B_REGROUP, B_FIGHT + 2, 11.0, 0.85, 0.8),
        ([62, 69, 75], B_FIGHT + 36, B_AFTER, 12.5, 0.7, 0.75)]:
    sw = tremolo_strings(chord, (b1 - b0) * BAR, trem_hz=trem)
    add_at(lay_L, sw, bar_t(b0), gL)
    add_at(lay_R, sw, bar_t(b0), gR)
lay_L = reverb(lay_L, IR_L, wet=0.45)
lay_R = reverb(lay_R, IR_R, wet=0.45)
commit(lay_L, lay_R, 0.13)
print("strings committed")


# ---------------------------------------------------------------- duduk
# Theme WAR over the groove; Theme L — the dying-fall lament — after.

THEME_L = [(67, 2.2), (70, 1.4), (69, 2.6), (66, 1.8), (67, 1.2),
           (63, 2.4), (62, 1.8), (58, 4.5)]          # ends in the dying fall

lay_L = np.zeros(N)
lay_R = np.zeros(N)


def place_voice(notes, t0, pan_pos, gain=1.0, lp=2200):
    v = voice_phrase(notes, lp=lp)
    add_at(lay_L, v, t0, gain * np.cos(pan_pos * np.pi / 2))
    add_at(lay_R, v, t0, gain * np.sin(pan_pos * np.pi / 2))


place_voice([(62, 1.0), (63, 0.8), (62, 2.0)], 5.0, 0.6, 0.8)
place_voice(THEME_WAR, bar_t(B_MUSTER + 16), 0.5, 0.9)      # foreshadow
place_voice(THEME_WAR, bar_t(B_LAUNCH + 38), 0.55)          # over the peak
place_voice([(m + 12, d) for m, d in THEME_WAR[:8]],
            bar_t(B_FIGHT + 40), 0.45, 0.9)                 # octave, melee
place_voice(THEME_L, after_t + 9.0, 0.5, 1.0, lp=1900)      # the lament
lay_L = reverb(lay_L, IR_L, wet=0.6)
lay_R = reverb(lay_R, IR_R, wet=0.6)
commit(lay_L, lay_R, 0.20)
print("duduk committed")


# ---------------------------------------------------------------- ney

lay_L = np.zeros(N)
lay_R = np.zeros(N)
v = ney_phrase([(74, 1.2), (72, 0.8), (70, 1.6), (69, 1.0),
                (70, 0.8), (67, 2.4)])                       # smoke drifting
add_at(lay_L, v, bar_t(B_REGROUP + 1), 0.8 * np.cos(0.6 * np.pi / 2))
add_at(lay_R, v, bar_t(B_REGROUP + 1), 0.8 * np.sin(0.6 * np.pi / 2))
v = ney_phrase([(m + 12, d) for m, d in THEME_L[:5]])
add_at(lay_L, v, after_t + 33.0, 0.6 * np.cos(0.4 * np.pi / 2))
add_at(lay_R, v, after_t + 33.0, 0.6 * np.sin(0.4 * np.pi / 2))
lay_L = reverb(lay_L, IR_L, wet=0.55)
lay_R = reverb(lay_R, IR_R, wet=0.55)
commit(lay_L, lay_R, 0.11)
print("ney committed")


# ---------------------------------------------------------------- chant
# Every bar of the preparation (the army assembling), rising through the
# builds, OWNING the fight's war-cry dip, one breath over the dead.

lay_L = np.zeros(N)
lay_R = np.zeros(N)
CH_LONG = {m: chant_note(m, 1.4 * BEAT) for m in (38, 36)}
CH_SHORT = {m: chant_note(m, 0.85 * BEAT) for m in (38, 36)}

for b in range(B_PREP, B_MUSTER):
    g = 0.5 + 0.5 * b / B_MUSTER
    add_at(lay_L, CH_LONG[38], bar_t(b, 0.0), g * 0.8)
    add_at(lay_R, CH_LONG[38], bar_t(b, 0.0), g * 0.9)
for b in range(B_REGROUP, B_RISE2):
    if b % 2 == 0:
        add_at(lay_L, CH_LONG[38], bar_t(b, 0.0), 0.85)
        add_at(lay_R, CH_LONG[38], bar_t(b, 0.0), 0.95)
for b0 in (B_RISE, B_RISE2):
    for b in range(b0, b0 + 8):
        g = 0.5 + 0.5 * (b - b0) / 8
        for beat, gg, bank in [(0.0, 1.0, CH_LONG), (2.0, 0.8, CH_SHORT)]:
            add_at(lay_L, bank[38], bar_t(b, beat), g * gg * 0.9)
            add_at(lay_R, bank[38], bar_t(b, beat), g * gg)
for b in sorted(DIP_F):                              # the war cry
    for beat, gg in [(0.0, 1.0), (1.0, 0.7), (2.0, 0.9), (3.0, 0.7)]:
        root = 36 if beat == 3.0 else 38
        add_at(lay_L, CH_SHORT[root], bar_t(b, beat), gg)
        add_at(lay_R, CH_SHORT[root], bar_t(b, beat), gg)
for b in SPRINT:
    if b % 2 == 0:
        add_at(lay_L, CH_SHORT[38], bar_t(b, 0.0), 0.8)
        add_at(lay_R, CH_SHORT[38], bar_t(b, 0.0), 0.8)
last = chant_note(38, 5.0, pulse=4.0)
add_at(lay_L, last, after_t + 24.0, 0.7)
add_at(lay_R, last, after_t + 24.0, 0.7)
lay_L = reverb(lay_L, IR_L, wet=0.45)
lay_R = reverb(lay_R, IR_R, wet=0.45)
commit(lay_L, lay_R, 0.15)
print("chant committed")


# ---------------------------------------------------------------- aftermath
# The silence, agony, death: a decelerating heartbeat that stops; falling
# worm-rumbles; and a SINKING drone — D with a faint flat-second shimmer
# (the agony), whose pitch sags 6 % over the last half minute (the death).

def heart_thump():
    n = int(0.22 * SR)
    td = np.arange(n) / SR
    f_curve = 40.0 + 18.0 * np.exp(-td * 30.0)
    x = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    x *= (1 - np.exp(-td / 0.01)) * np.exp(-td * 14.0)
    return x / (np.max(np.abs(x)) + 1e-12)


HEART = heart_thump()

lay_L = np.zeros(N)
lay_R = np.zeros(N)
tcur = after_t + 6.0
gap = 1.0
g = 1.0
while gap < 2.6 and tcur < DURATION - 10:           # the heart slows... stops
    add_at(lay_L, HEART, tcur, g)
    add_at(lay_R, HEART, tcur, g)
    add_at(lay_L, HEART, tcur + 0.28, g * 0.55)
    add_at(lay_R, HEART, tcur + 0.28, g * 0.55)
    tcur += gap
    gap *= 1.085
    g *= 0.96
commit(lay_L, lay_R, 0.09)

lay_L[:] = 0.0
lay_R[:] = 0.0
sink_t0 = after_t + 16.0
n_sink = int((DURATION - sink_t0) * SR)
tt = np.arange(n_sink) / SR
sag = 1.0 - 0.06 * np.clip((tt - 14.0) / 28.0, 0, 1)        # the death
f0 = midi_to_hz(26)
ph1 = 2 * np.pi * np.cumsum(f0 * sag) / SR
ph2 = 2 * np.pi * np.cumsum(f0 * 2 * sag) / SR
phb = 2 * np.pi * np.cumsum(f0 * 2 ** (1 / 12.0) * sag) / SR  # flat 2nd: agony
sink = (np.sin(ph1) + 0.5 * np.sin(ph2) + 0.22 * np.sin(phb))
sink *= np.minimum(np.clip(tt / 8.0, 0, 1),
                   np.clip((n_sink / SR - tt) / 8.0, 0, 1))
add_at(lay_L, sink, sink_t0, 1.0)
add_at(lay_R, sink, sink_t0, 1.0)
for t0, g in [(after_t + 3.0, 0.8), (after_t + 20.0, 0.5),
              (after_t + 40.0, 0.35)]:
    x = explosion(6.0, 38.0)                        # falling worm-rumbles
    add_at(lay_L, x, t0, g)
    add_at(lay_R, x, t0, g)
commit(lay_L, lay_R, 0.08)        # death is QUIET — the march must out-weigh it
print("aftermath committed")


# ---------------------------------------------------------------- master
# High-shelf as in sleeper_awakens, PLUS a low-shelf (+~2 dB below
# 95 Hz) — the other half of the room-shake.

del lay_L, lay_R
sos_shelf = signal.butter(2, 3000, "high", fs=SR, output="sos")
mix_L += 0.22 * signal.sosfilt(sos_shelf, mix_L)
mix_R += 0.22 * signal.sosfilt(sos_shelf, mix_R)
sos_sub = signal.butter(2, 95, "low", fs=SR, output="sos")
mix_L += 0.34 * signal.sosfilt(sos_sub, mix_L)
mix_R += 0.34 * signal.sosfilt(sos_sub, mix_R)
# v2: a second, DEEPER shelf — the two compound to ~+5 dB below 55 Hz
sos_deep = signal.butter(2, 55, "low", fs=SR, output="sos")
mix_L += 0.30 * signal.sosfilt(sos_deep, mix_L)
mix_R += 0.30 * signal.sosfilt(sos_deep, mix_R)
print("master shelves applied (high + low + deep)")

fade(mix_L, fade_in=5.0, fade_out=12.0)
fade(mix_R, fade_in=5.0, fade_out=12.0)

# gentle tanh bus limiter: transient stacks (build rolls + riser peaks)
# can no longer steal normalization headroom from the drops, and the
# slight saturation is the psy-master "glue"
peak = max(np.max(np.abs(mix_L)), np.max(np.abs(mix_R)))
mix_L = np.tanh(1.35 * mix_L / peak) / np.tanh(1.35) * 0.88
mix_R = np.tanh(1.35 * mix_R / peak) / np.tanh(1.35) * 0.88

stereo = np.empty((N, 2))
stereo[:, 0] = mix_L
stereo[:, 1] = mix_R
pcm = (stereo * 32767.0).astype(np.int16)

OUT_DIR = "/workspace/music"
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, "fall_of_arrakeen_v2.wav")
with wave.open(OUT, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())

print(f"\nCreated: {os.path.abspath(OUT)}")
print(f"Duration: {N / SR:.1f} s  |  {SR} Hz stereo, 16-bit PCM  |  "
      f"{BPM:.0f} BPM  |  {N_LAYERS} committed layers")
print("Section map:")
for name, b in [("PREPARATION: snare march", B_PREP),
                ("muster: kick enters", B_MUSTER),
                ("  bass joins", B_MUSTER + 8),
                ("  dark acid + war call (horn)", B_MUSTER + 16),
                ("the rise", B_RISE),
                ("LAUNCH", B_LAUNCH),
                ("  phase: high acid + horn", B_LAUNCH + 16),
                ("  mini-dip: bass + snare march", B_LAUNCH + 32),
                ("  phase: peak (toms join)", B_LAUNCH + 36),
                ("REGROUP: march + chant + shells", B_REGROUP),
                ("the second rise", B_RISE2),
                ("THE FIGHT (war drums + toms)", B_FIGHT),
                ("  phase: high acid + horn calls", B_FIGHT + 16),
                ("  mini-dip: kick + chant war cry", B_FIGHT + 32),
                ("  phase: peak ride", B_FIGHT + 36),
                ("  dip: bass + snare + riser", B_FIGHT + 52),
                ("  THE SPRINT (kick on 8ths)", B_FIGHT + 56),
                ("THE DEATH BLOW / aftermath", B_AFTER)]:
    print(f"  {bar_t(b):6.1f} s  bar {b:3d}  {name}")
print(f"  aftermath: heartbeat {after_t+6:.0f}s (slows, stops), lament "
      f"{after_t+9:.0f}s, chant {after_t+24:.0f}s, ney {after_t+33:.0f}s, "
      f"far horn {after_t+48:.0f}s, sinking drone {after_t+16:.0f}s -> end")
print(f"  {DURATION:6.1f} s  end")
