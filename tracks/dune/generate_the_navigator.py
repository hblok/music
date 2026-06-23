#!/usr/bin/env python3
"""
generate_the_navigator.py — "The Navigator" (~6:05). Dune + Goa Trance.
Guild Navigator consuming the spice, folding space — consciousness dilating
until past and future collapse into one fold. Void, mind and machine.

What's genuinely new vs the rest of the album:
  * E Hijaz Kar (E F G# A B C D#) — the album's first major-third-resolving
    key; breaks the D-Phrygian-dominant rut of all 11 earlier tracks.
  * FM Goa lead: two-operator PM synthesis (carrier + I·sin(fm·t), ratio=3),
    index decaying 4→0.8, vibrato blooming 0.4 s, bright→warm filter sweep,
    detuned stereo second voice. The nasal Juno Reactor melody lead that the
    codebase has never had.
  * Choir-formant pad: 6-harmonic glottal source → three "ah"-vowel formant
    bandpasses (700/1100/2600 Hz), pulsing to true zero at 0.065 Hz
    (anti-tinnitus rule), as the "cosmic consciousness" layer.
  * Crystalline arpeggio: short FM plucks (ratio 1), hard L/R ping-pong per
    16th step, doubling to 32nds in builds.
  * Tabla tarang: extended darbuka with tuned E2/B2 resonator rings.
  * THEME_FOLD: 4-bar hook in E Hijaz Kar, resolves UP to G# (the major
    third) — the album's first ecstatic, non-shadowed resolution.

Bass mastering (earbud-friendly, target ~+2 dB below 100 Hz, not +5):
  * Sub boom: 66→52 Hz (was 50→37), weight 0.22 (was 0.30).
  * Kick sub tail bottoms at 48 Hz (was 37 Hz).
  * Master: single +0.18× butter(105 Hz) shelf; the deep 55 Hz shelf is
    REMOVED — that was the primary earbud-clipping culprit.
  * Sidechain pump: 45 % duck (was 55 %), floor 0.40 (was 0.30).

Story:
  0:00  The spice-gas tank. Orange, alien, weightless. The Navigator breathes.
  0:10  SUBMERSION: E drone + choir swells, sparse tabla. Consciousness
        starts to dilate.
  0:36  AWARENESS: kick 4-on-floor enters, rolling bass joins, arp glints.
        The futures multiply.
  1:03  THE LATTICE (build): riser + acid ramps + off-beat hats.
  1:16  PRESCIENCE (DROP 1): FM lead states THEME_FOLD. All paths visible.
        Mini-dip 1:43 (bass + arp only; the paths branch, not collapse).
  2:09  THE HELD BREATH: kick drops. Choir + tarang + lone lead fragment.
        The instant before the fold.
  2:22  CONVERGENCE (build 2): slam back, 32nd arps, acid climbing.
  2:36  THE FOLD (DROP 2 — peak): THEME_FOLD an octave up + counter-voice.
        Both acid lines + full FM. Choir at full. Mini-dips at 3:02 and 3:28.
  3:55  STILLPOINT: one vast resonant hit — then dead air. The ship has
        arrived. Only drone and a reversed shimmer remain.
  4:08  ARRIVAL (final drop): groove returns warmer. THEME_FOLD one last time,
        resolved to the long G# hold.
  4:48  THE VOID BEYOND: strip layer by layer. Drone → choir → silence.

Output: /workspace/music/the_navigator.wav (stereo, 44100 Hz, 16-bit).
"""

import os
import wave
import numpy as np
from scipy import signal

SR = 44100
DURATION = 365.0
N = int(SR * DURATION)
t = np.arange(N) / SR

rng = np.random.default_rng(21000)   # Spacing Guild founding era

BPM = 145.0
BEAT = 60.0 / BPM
BAR = BEAT * 4
STEP = BEAT / 4
GRID0 = 10.0


def bar_t(b, beat=0.0):
    return GRID0 + b * BAR + beat * BEAT


# ── section boundaries (bars) ─────────────────────────────────────────────────
B_SUBM   = 0    # Submersion        0–15   (16 bars ≈ 26.5 s)
B_AWARE  = 16   # Awareness         16–31
B_LATT   = 32   # Lattice build     32–39
B_PRESC  = 40   # Prescience DROP 1 40–71  (32 bars)
B_BREATH = 72   # Held Breath       72–79
B_CONV   = 80   # Convergence build 80–87
B_FOLD   = 88   # THE FOLD DROP 2   88–135 (48 bars)
B_STILL  = 136  # Stillpoint        136–143
B_ARR    = 144  # Arrival           144–167 (24 bars)
B_VOID   = 168  # The Void Beyond   168+

DIP_P  = set(range(56, 60))
DIP_F1 = set(range(104, 108))
DIP_F2 = set(range(120, 124))
ALL_DIPS = DIP_P | DIP_F1 | DIP_F2

N_LAYERS = 0


# ── helpers ───────────────────────────────────────────────────────────────────

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


def glide_curve(notes_s, n):
    """notes_s: list of (midi, dur_in_seconds)"""
    f_target = np.zeros(n)
    edge = 0.0
    for m, d in notes_s:
        a, b = int(edge * SR), min(n, int((edge + d) * SR))
        f_target[a:b] = midi_to_hz(m)
        edge += d
    i_end = min(n - 1, int(edge * SR))
    f_target[i_end:] = f_target[i_end - 1]
    alpha = 1.0 - np.exp(-1.0 / (0.09 * SR))
    return signal.lfilter([alpha], [1.0, -(1.0 - alpha)],
                          f_target, zi=[f_target[0] * (1 - alpha)])[0]


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


IR_L = make_reverb_ir(5.0, 1.6, 7)
IR_R = make_reverb_ir(5.0, 1.6, 11)

# ── energy envelope ───────────────────────────────────────────────────────────
still_t = bar_t(B_STILL)
energy_pts = [
    (0.0, 0.0), (GRID0 - 0.5, 0.0), (GRID0 + 0.5, 0.20),
    (bar_t(B_AWARE), 0.30), (bar_t(B_LATT), 0.48),
    (bar_t(B_PRESC) - 0.1, 0.62), (bar_t(B_PRESC) + 0.3, 0.82),
    (bar_t(B_BREATH), 0.82), (bar_t(B_BREATH) + 0.3, 0.38),
    (bar_t(B_CONV), 0.52), (bar_t(B_FOLD) - 0.1, 0.78),
    (bar_t(B_FOLD) + 0.3, 1.0),
    (still_t, 1.0), (still_t + 0.5, 0.08),
    (bar_t(B_ARR), 0.18), (bar_t(B_ARR) + 0.3, 0.78),
    (bar_t(B_VOID), 0.65), (DURATION, 0.0),
]
energy = np.interp(t, [p[0] for p in energy_pts], [p[1] for p in energy_pts])
calm = 1.0 - 0.38 * energy
calm *= np.interp(t, [0.0, still_t, still_t + 4.0, bar_t(B_ARR), DURATION],
                  [1.0, 1.0, 0.82, 0.82, 1.0])


def groove_on(b):
    """Bars where the trance grid plays."""
    return (B_AWARE <= b < B_STILL and not (B_BREATH <= b < B_CONV))


def arr_on(b):
    """Bars where the arrival groove plays."""
    return B_ARR <= b < B_VOID


# ── sidechain pump ────────────────────────────────────────────────────────────
# Earbud-friendly: 45 % duck (was 55 %), floor 0.40 (was 0.30)
pump = np.ones(N)
_dipn = int(0.30 * SR)
_dip = 0.45 * np.exp(-np.arange(_dipn) / SR / 0.11)
for _b in range(B_VOID):
    if not (groove_on(_b) or arr_on(_b)):
        continue
    for _beat in range(4):
        _i0 = int(bar_t(_b, _beat) * SR)
        _end = min(N, _i0 + _dipn)
        pump[_i0:_end] = np.minimum(pump[_i0:_end], 1.0 - _dip[: _end - _i0])
np.clip(pump, 0.40, 1.0, out=pump)


# ─────────────────────────────────────────────────────────────────────────────
# SPICE-GAS ATMOSPHERE
# Not Arrakis desert wind — a sealed pressurised tank of orange spice gas.
# Resonances tuned to E root harmonics; no sand-hiss frequency palette.
# ─────────────────────────────────────────────────────────────────────────────

raw = rng.standard_normal(N)
sos_body = signal.butter(4, [40, 200], "bandpass", fs=SR, output="sos")
sos_mid  = signal.butter(4, [200, 900], "bandpass", fs=SR, output="sos")
sos_shim = signal.butter(4, [1500, 5000], "bandpass", fs=SR, output="sos")
gas_body = signal.sosfilt(sos_body, raw)
gas_mid  = signal.sosfilt(sos_mid,  raw)
gas_shim = signal.sosfilt(sos_shim, raw)
gas_body /= np.max(np.abs(gas_body)) + 1e-12
gas_mid  /= np.max(np.abs(gas_mid))  + 1e-12
gas_shim /= np.max(np.abs(gas_shim)) + 1e-12
del raw

gust  = slow_noise(0.14) ** 2.0
gust2 = slow_noise(0.05) ** 1.6
atm_env = 0.28 + 0.72 * (0.62 * gust + 0.38 * gust2)
pan_g   = slow_noise(0.04, 0.28, 0.72)
gas_L = atm_env * (gas_body * np.cos(pan_g * np.pi / 2) +
                   0.48 * gas_mid  * np.cos((1 - pan_g) * np.pi / 2) +
                   0.14 * gas_shim * np.cos(pan_g * np.pi / 2))
gas_R = atm_env * (gas_body * np.sin(pan_g * np.pi / 2) +
                   0.48 * gas_mid  * np.sin((1 - pan_g) * np.pi / 2) +
                   0.14 * gas_shim * np.sin(pan_g * np.pi / 2))
commit(gas_L, gas_R, 0.19, env=calm)
del gas_body, gas_mid, gas_shim, gas_L, gas_R
print("spice-gas atmosphere committed")

# E1 drone with Hijaz Kar colour: E1 + fifth (B1) + b2 tension shimmer (F1)
f_E1 = midi_to_hz(28)   # E1 ≈ 41.2 Hz
f_B1 = midi_to_hz(35)   # B1 ≈ 61.7 Hz (perfect 5th)
f_F1 = midi_to_hz(29)   # F1 ≈ 43.7 Hz (b2: Hijaz tension shimmer)
breath = 0.70 + 0.30 * np.sin(2 * np.pi * 0.011 * t + 0.8)
drone = (np.sin(2 * np.pi * f_E1 * t) +
         0.52 * np.sin(2 * np.pi * f_E1 * 2 * t + 0.3) +
         0.32 * np.sin(2 * np.pi * f_B1 * t) +
         0.18 * np.sin(2 * np.pi * f_B1 * 2 * t) +
         0.10 * np.sin(2 * np.pi * f_F1 * t))
drone *= breath
drone /= np.max(np.abs(drone))
commit(drone, drone, 0.17, env=calm * pump)
del drone, breath
print("drone committed")


# ─────────────────────────────────────────────────────────────────────────────
# KICK STACK  (earbud-friendly: sub tail bottoms at 48 Hz, not 37 Hz)
# ─────────────────────────────────────────────────────────────────────────────

def make_kick_stack(sub=True):
    n = int(0.42 * SR)
    td = np.arange(n) / SR
    f_curve = 48.0 + 102.0 * np.exp(-td * 50.0)   # punch, lands at 48 Hz
    punch = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    sos_c = signal.butter(2, [1800, 9000], "bandpass", fs=SR, output="sos")
    click = signal.sosfilt(sos_c, rng.standard_normal(n)) * np.exp(-td * 700)
    click /= np.max(np.abs(click)) + 1e-12
    env_p = (1 - np.exp(-td / 0.0008)) * np.exp(-td * 9.0)
    x = (punch + 0.50 * click) * env_p
    if sub:
        f_sub = 48.0 + 16.0 * np.exp(-td * 9.0)   # sub tail 64→48 Hz
        tail = np.sin(2 * np.pi * np.cumsum(f_sub) / SR)
        env_s = (1 - np.exp(-td / 0.004)) * np.exp(-td * 3.2)
        x = x + 1.05 * tail * env_s
    return x / (np.max(np.abs(x)) + 1e-12)


KICK   = make_kick_stack()
KICK_P = make_kick_stack(sub=False)

lay_L = np.zeros(N)
lay_R = np.zeros(N)
for b in range(B_STILL):
    if not groove_on(b):
        continue
    g = 1.0
    if b in (B_LATT + 6, B_CONV + 6):
        for e in range(8):
            gg = g * 0.80 * (0.55 + 0.45 * e / 7)
            add_at(lay_L, KICK_P, bar_t(b, e * 0.5), gg)
            add_at(lay_R, KICK_P, bar_t(b, e * 0.5), gg)
        continue
    if b in (B_LATT + 7, B_CONV + 7):
        for s in range(16):
            gg = g * 0.80 * (0.55 + 0.45 * s / 15)
            add_at(lay_L, KICK_P, bar_t(b, s * 0.25), gg)
            add_at(lay_R, KICK_P, bar_t(b, s * 0.25), gg)
        continue
    if B_LATT <= b < B_LATT + 6 or B_CONV <= b < B_CONV + 6:
        g *= 0.60
    elif b < B_PRESC:
        g *= 0.72
    for beat in range(4):
        add_at(lay_L, KICK, bar_t(b, beat), g)
        add_at(lay_R, KICK, bar_t(b, beat), g)
for b in range(B_ARR, B_VOID):
    g = max(0.45, 1.0 - (b - B_ARR) / max(1, B_VOID - B_ARR) * 0.50)
    for beat in range(4):
        add_at(lay_L, KICK, bar_t(b, beat), g)
        add_at(lay_R, KICK, bar_t(b, beat), g)
commit(lay_L, lay_R, 0.46)
print("kick stack committed")


# ─────────────────────────────────────────────────────────────────────────────
# SUB BOOM  (earbud-friendly: 66→52 Hz, weight 0.22 vs 0.30)
# ─────────────────────────────────────────────────────────────────────────────

def make_sub_boom():
    n = int(BEAT * SR) + 1
    td = np.arange(n) / SR
    f_curve = 52.0 + 14.0 * np.exp(-td * 13.0)   # 66→52 Hz
    x = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    env = ((1 - np.exp(-td / 0.003)) * np.exp(-td * 1.6) *
           np.clip((BEAT - td) / 0.06, 0, 1))
    return x * env


BOOM = make_sub_boom()

lay_L[:] = 0.0
lay_R[:] = 0.0
for b in range(B_STILL):
    if not groove_on(b) or b in ALL_DIPS:
        continue
    if b in (B_LATT + 6, B_LATT + 7, B_CONV + 6, B_CONV + 7):
        continue
    g = 1.0
    if B_LATT <= b < B_LATT + 6 or B_CONV <= b < B_CONV + 6:
        g *= 0.50
    elif b < B_PRESC:
        g *= 0.60
    for beat in range(4):
        add_at(lay_L, BOOM, bar_t(b, beat), g)
        add_at(lay_R, BOOM, bar_t(b, beat), g)
for b in range(B_ARR, B_VOID):
    g = max(0.40, 1.0 - (b - B_ARR) / max(1, B_VOID - B_ARR) * 0.55)
    for beat in range(4):
        add_at(lay_L, BOOM, bar_t(b, beat), g)
        add_at(lay_R, BOOM, bar_t(b, beat), g)
commit(lay_L, lay_R, 0.22)
print("sub boom committed")


# ─────────────────────────────────────────────────────────────────────────────
# MELODIC ROLLING BASS — E Hijaz Kar walk
# K-b-b-b engine; off-beats walk the mode: E2→G#2→A2→B2
# ─────────────────────────────────────────────────────────────────────────────

E2, F2, GS2, A2, B2, C3, DS3 = 40, 41, 44, 45, 47, 48, 51


def psy_bass_note(midi, dur=STEP * 0.88):
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    for k in range(1, min(20, int(7000 / f)) + 1):
        x += np.sin(2 * np.pi * k * f * td) / k
    sos_b = signal.butter(2, 350, "low", fs=SR, output="sos")
    x = np.tanh(2.0 * signal.sosfilt(sos_b, x))
    env = (1 - np.exp(-td / 0.002)) * np.clip((dur - td) / 0.020, 0, 1)
    x *= env
    return x / (np.max(np.abs(x)) + 1e-12)


BASS = {m: psy_bass_note(m) for m in (E2, GS2, A2, B2, C3, DS3)}

lay_L[:] = 0.0
lay_R[:] = 0.0
for b in range(B_STILL):
    if b < B_AWARE + 4 or not groove_on(b) or b in DIP_F1:
        continue
    g = 1.0
    if b < B_PRESC or (B_CONV <= b < B_FOLD):
        g *= 0.65
    for beat in range(4):
        if b % 4 == 3 and beat == 3:
            walk = [DS3, A2, GS2]   # cadence: leading tone + fall
        elif b % 8 == 7 and beat >= 2:
            walk = [B2, C3, B2]     # upper chromatic neighbour
        else:
            walk = [GS2, A2, B2]   # standard E Hijaz Kar walk
        for s, m in enumerate(walk):
            gg = [0.80, 0.70, 0.95][s]
            add_at(lay_L, BASS[m], bar_t(b, beat + (s + 1) * 0.25), g * gg)
            add_at(lay_R, BASS[m], bar_t(b, beat + (s + 1) * 0.25), g * gg)
for b in range(B_ARR, B_VOID - 6):
    g = max(0.30, 1.0 - (b - B_ARR) / max(1, B_VOID - 6 - B_ARR) * 0.70)
    for beat in range(4):
        walk = [GS2, A2, B2]
        for s, m in enumerate(walk):
            gg = [0.80, 0.70, 0.95][s]
            add_at(lay_L, BASS[m], bar_t(b, beat + (s + 1) * 0.25), g * gg)
            add_at(lay_R, BASS[m], bar_t(b, beat + (s + 1) * 0.25), g * gg)
commit(lay_L, lay_R, 0.26, env=pump)
print("melodic rolling bass committed")


# ─────────────────────────────────────────────────────────────────────────────
# HATS
# ─────────────────────────────────────────────────────────────────────────────

def make_hat(open_=False):
    n = int((0.16 if open_ else 0.045) * SR)
    td = np.arange(n) / SR
    sos_h = signal.butter(4, 6500 if open_ else 7200, "high", fs=SR, output="sos")
    x = signal.sosfilt(sos_h, rng.standard_normal(n))
    x *= np.exp(-td * (22 if open_ else 100))
    return x / (np.max(np.abs(x)) + 1e-12)


OHAT = make_hat(open_=True)
CHAT = make_hat()

lay_L[:] = 0.0
lay_R[:] = 0.0
for b in range(B_STILL):
    if not groove_on(b) or b in ALL_DIPS:
        continue
    for beat in range(4):
        add_at(lay_L, OHAT, bar_t(b, beat + 0.5), 0.80)
        add_at(lay_R, OHAT, bar_t(b, beat + 0.5), 1.00)
    if B_PRESC <= b:
        for s in range(16):
            if s % 2 == 0:
                continue
            p = 0.30 + 0.40 * ((s // 2) % 2)
            add_at(lay_L, CHAT, bar_t(b, s * 0.25),
                   0.28 * np.cos(p * np.pi / 2))
            add_at(lay_R, CHAT, bar_t(b, s * 0.25),
                   0.28 * np.sin(p * np.pi / 2))
for b in range(B_ARR, B_VOID - 4):
    g = max(0.30, 1.0 - (b - B_ARR) / max(1, B_VOID - 4 - B_ARR) * 0.60)
    for beat in range(4):
        add_at(lay_L, OHAT, bar_t(b, beat + 0.5), 0.80 * g)
        add_at(lay_R, OHAT, bar_t(b, beat + 0.5), 1.00 * g)
commit(lay_L, lay_R, 0.11)
print("hats committed")


# ─────────────────────────────────────────────────────────────────────────────
# CLAP
# ─────────────────────────────────────────────────────────────────────────────

def make_clap():
    n = int(0.26 * SR)
    td = np.arange(n) / SR
    sos_c = signal.butter(2, [900, 5200], "bandpass", fs=SR, output="sos")
    nz = signal.sosfilt(sos_c, rng.standard_normal(n))
    nz /= np.max(np.abs(nz)) + 1e-12
    env = np.zeros(n)
    for i, t0c in enumerate([0.0, 0.011, 0.022, 0.033]):
        i0 = int(t0c * SR)
        rate = 120.0 if i < 3 else 26.0
        seg = (0.65 if i < 3 else 1.0) * np.exp(-(td[i0:] - t0c) * rate)
        env[i0:] = np.maximum(env[i0:], seg)
    x = nz * env
    return x / (np.max(np.abs(x)) + 1e-12)


CLAP = make_clap()

lay_L[:] = 0.0
lay_R[:] = 0.0
for b in range(B_STILL):
    if not groove_on(b) or b in ALL_DIPS:
        continue
    if b < B_PRESC:
        continue
    for beat in (1, 3):
        p = 0.42 if beat == 1 else 0.58
        add_at(lay_L, CLAP, bar_t(b, beat), np.cos(p * np.pi / 2))
        add_at(lay_R, CLAP, bar_t(b, beat), np.sin(p * np.pi / 2))
for b in range(B_ARR, B_VOID - 4):
    for beat in (1, 3):
        p = 0.42 if beat == 1 else 0.58
        add_at(lay_L, CLAP, bar_t(b, beat), np.cos(p * np.pi / 2))
        add_at(lay_R, CLAP, bar_t(b, beat), np.sin(p * np.pi / 2))
commit(lay_L, lay_R, 0.09)
print("clap committed")


# ─────────────────────────────────────────────────────────────────────────────
# TABLA TARANG — extended darbuka with tuned E2/B2 resonator rings
# Polyrhythm feel in THE FOLD (extra TEK hits every 3 steps).
# ─────────────────────────────────────────────────────────────────────────────

def make_tarang_doum():
    n = int(0.35 * SR)
    td = np.arange(n) / SR
    f_curve = midi_to_hz(40) + 30.0 * np.exp(-td * 22.0)   # E2: 112→82 Hz
    body = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    ring_b = 0.28 * np.sin(2 * np.pi * midi_to_hz(47) * td) * np.exp(-td * 26)
    f_sub  = 50.0 + 22.0 * np.exp(-td * 18.0)
    sub    = 0.35 * np.sin(2 * np.pi * np.cumsum(f_sub) / SR)
    env = np.exp(-td * 11.0) * (1 - np.exp(-td * 400))
    x = (body + ring_b + sub) * env
    return x / (np.max(np.abs(x)) + 1e-12)


def make_tek(ghost=False):
    n = int(0.09 * SR)
    td = np.arange(n) / SR
    sos_h = signal.butter(4, [2800, 10000], "bandpass", fs=SR, output="sos")
    slap = signal.sosfilt(sos_h, rng.standard_normal(n))
    ping = 0.4 * np.sin(2 * np.pi * 680.0 * td)
    env = np.exp(-td * (90.0 if ghost else 55.0))
    x = (slap / (np.max(np.abs(slap)) + 1e-12) + ping) * env
    return x * (0.35 if ghost else 1.0)


TARANG = make_tarang_doum()
TEK    = make_tek()
KA     = make_tek(ghost=True)
MAQSUM = {0: "D", 2: "T", 6: "T", 8: "D", 12: "T"}

lay_L[:] = 0.0
lay_R[:] = 0.0
# Submersion: sparse tabla, every 4th bar
for b in range(B_SUBM, B_AWARE):
    if b % 4 == 0:
        add_at(lay_L, TARANG, bar_t(b, 0.0), 0.42)
        add_at(lay_R, TARANG, bar_t(b, 0.0), 0.42)
    elif b % 4 == 2:
        add_at(lay_L, TEK, bar_t(b, 2.0), 0.30)
        add_at(lay_R, TEK, bar_t(b, 2.0), 0.24)
# Main groove sections
for b in range(B_STILL):
    in_groove = groove_on(b) and b >= B_AWARE
    if not in_groove or b in ALL_DIPS:
        continue
    level = 0.55 if b < B_PRESC else 0.65
    fill_bar = b % 8 == 5
    poly = B_FOLD <= b     # polyrhythm extra hits in THE FOLD
    for s in range(16):
        st = bar_t(b, s * 0.25)
        stroke = MAQSUM.get(s)
        if fill_bar and s >= 10:
            g = (0.38 + 0.62 * (s - 10) / 5.0) * level
            add_at(lay_L, TEK, st, g * 0.90)
            add_at(lay_R, TEK, st, g * 0.70)
            continue
        if stroke == "D":
            add_at(lay_L, TARANG, st, level)
            add_at(lay_R, TARANG, st, level)
        elif stroke == "T":
            p = 0.35 if s in (2, 12) else 0.65
            add_at(lay_L, TEK, st, level * np.cos(p * np.pi / 2))
            add_at(lay_R, TEK, st, level * np.sin(p * np.pi / 2))
        elif s % 2 == 1 and rng.random() < 0.20:
            add_at(lay_L, KA, st, 0.50 * level)
            add_at(lay_R, KA, st, 0.45 * level)
        if poly and s % 3 == 2:   # extra TEK triplet
            add_at(lay_L, TEK, st + STEP * 0.5, level * 0.30)
            add_at(lay_R, TEK, st + STEP * 0.5, level * 0.28)
for b in range(B_ARR, B_VOID - 4):
    level = max(0.35, 1.0 - (b - B_ARR) / max(1, B_VOID - 4 - B_ARR) * 0.60)
    for s, stroke in MAQSUM.items():
        st = bar_t(b, s * 0.25)
        if stroke == "D":
            add_at(lay_L, TARANG, st, level)
            add_at(lay_R, TARANG, st, level)
        elif stroke == "T":
            p = 0.35 if s in (2, 12) else 0.65
            add_at(lay_L, TEK, st, level * np.cos(p * np.pi / 2))
            add_at(lay_R, TEK, st, level * np.sin(p * np.pi / 2))
commit(lay_L, lay_R, 0.14)
print("tabla tarang committed")


# ─────────────────────────────────────────────────────────────────────────────
# CHOIR-FORMANT PAD — cosmic consciousness shimmer
# 6-harmonic glottal source → "ah"-vowel formants (700/1100/2600 Hz);
# pulsing to true zero at 0.065 Hz (anti-tinnitus rule).
# ─────────────────────────────────────────────────────────────────────────────

# E major triad in E3 register: E3 G#3 B3 E4
E3, GS3, B3, E4, C4 = 52, 56, 59, 64, 60

def make_choir_pad(notes_midi, dur, pulse_hz=0.065, seed_off=0):
    r2 = np.random.default_rng(3000 + seed_off)
    n = int(dur * SR)
    tt = np.arange(n) / SR
    out = np.zeros(n)
    for m in notes_midi:
        f = midi_to_hz(m)
        src = np.zeros(n)
        for k in range(1, 7):
            src += np.sin(2 * np.pi * k * f * tt +
                          r2.uniform(0, 2 * np.pi)) / k ** 0.75
        for (lo, hi), g in [((650, 760), 1.0),
                             ((1000, 1200), 0.60),
                             ((2400, 2800), 0.18)]:
            sos_f = signal.butter(2, [lo, hi], "bandpass", fs=SR, output="sos")
            out += g * signal.sosfilt(sos_f, src)
        for det in (0.993, 1.007):
            src2 = np.zeros(n)
            for k in range(1, 5):
                src2 += np.sin(2 * np.pi * k * f * det * tt +
                               r2.uniform(0, 2 * np.pi)) / k
            sos_lo2 = signal.butter(2, 1500, "low", fs=SR, output="sos")
            out += 0.22 * signal.sosfilt(sos_lo2, src2)
    # Pulse to true zero — anti-tinnitus
    pulse = np.clip(np.sin(2 * np.pi * pulse_hz * tt), 0, 1) ** 2
    env = np.minimum(np.clip(tt / 4.0, 0, 1),
                     np.clip((dur - tt) / 4.0, 0, 1))
    out *= pulse * env
    return out / (np.max(np.abs(out)) + 1e-12)


lay_L = np.zeros(N)
lay_R = np.zeros(N)

def place_choir(notes, b_start, n_bars, gL=1.0, gR=1.0, pulse_hz=0.065, seed_off=0):
    dur = n_bars * BAR
    pad = make_choir_pad(notes, dur, pulse_hz, seed_off)
    pad_rv_L = reverb(pad, IR_L, wet=0.55)
    pad_rv_R = reverb(pad, IR_R, wet=0.55)
    add_at(lay_L, pad_rv_L, bar_t(b_start), gL)
    add_at(lay_R, pad_rv_R, bar_t(b_start), gR)

# Submersion: root + fifth only (sparse)
place_choir([E3, B3], B_SUBM, 16, gL=0.75, gR=0.82, seed_off=0)
# Awareness: triad (adds colour as kick enters)
place_choir([E3, GS3, B3], B_AWARE, 8, gL=0.65, gR=0.72, seed_off=1)
# Prescience DROP 1: full triad
place_choir([E3, GS3, B3, E4], B_PRESC, B_BREATH - B_PRESC,
            gL=0.90, gR=0.90, seed_off=2)
# Held Breath: root + fifth (minimal)
place_choir([E3, B3], B_BREATH, 8, gL=0.88, gR=0.92, seed_off=3)
# THE FOLD: triad + b6 tension (C4 = the alien shimmer)
place_choir([E3, GS3, B3, C4], B_FOLD, B_STILL - B_FOLD,
            gL=1.0, gR=1.0, seed_off=4)
# Arrival: full triad, warmer
place_choir([E3, GS3, B3, E4], B_ARR, B_VOID - B_ARR,
            gL=0.88, gR=0.82, seed_off=5)
# Void: root + fifth, long fade (slower pulse)
place_choir([E3, B3], B_VOID, int((DURATION - bar_t(B_VOID)) / BAR) + 1,
            gL=0.55, gR=0.60, pulse_hz=0.040, seed_off=6)

commit(lay_L, lay_R, 0.18)
del lay_L, lay_R
print("choir pad committed")


# ─────────────────────────────────────────────────────────────────────────────
# ARPEGGIO GLINTS — crystalline FM plucks, hard L/R ping-pong
# E G# B E ascending, 16th notes (32nds in builds)
# ─────────────────────────────────────────────────────────────────────────────

GS4, B4, E5 = 68, 71, 76   # E4=64 already defined

ARP_SEQ = [E4, GS4, B4, E5, B4, GS4]  # up-down arpeggio


def arp_pluck(midi):
    f = midi_to_hz(midi)
    n = int(0.13 * SR)
    td = np.arange(n) / SR
    idx = 2.0 * np.exp(-td / 0.032) + 0.22
    ph_m = 2 * np.pi * f * td          # ratio 1 = warm FM pluck
    ph_c = 2 * np.pi * f * td + idx * np.sin(ph_m)
    y = np.sin(ph_c)
    sos_bp = signal.butter(2, [900, 8000], "bandpass", fs=SR, output="sos")
    y = signal.sosfilt(sos_bp, y)
    env = np.exp(-td * 22.0) * (1 - np.exp(-td / 0.002))
    y *= env
    return y / (np.max(np.abs(y)) + 1e-12)


ARP_PLUCK = {m: arp_pluck(m) for m in set(ARP_SEQ)}

lay_L = np.zeros(N)
lay_R = np.zeros(N)

def place_arp_bar(b, double_speed=False, gain=1.0):
    step_sz = 0.125 if double_speed else 0.25
    n_steps = int(4 / step_sz)
    for s in range(n_steps):
        m = ARP_SEQ[s % len(ARP_SEQ)]
        p = 0.10 if s % 2 == 0 else 0.90   # hard L/R ping-pong
        add_at(lay_L, ARP_PLUCK[m], bar_t(b, s * step_sz),
               gain * np.cos(p * np.pi / 2))
        add_at(lay_R, ARP_PLUCK[m], bar_t(b, s * step_sz),
               gain * np.sin(p * np.pi / 2))

# Awareness: 16th arps, starts quiet
for b in range(B_AWARE + 8, B_LATT):
    place_arp_bar(b, gain=0.55)
# Lattice build: 32nds ramp up
for b in range(B_LATT, B_PRESC):
    g = 0.55 + 0.45 * (b - B_LATT) / max(1, B_PRESC - B_LATT)
    place_arp_bar(b, double_speed=True, gain=g)
# Prescience: 16ths, except dips
for b in range(B_PRESC, B_BREATH):
    if b in DIP_P:
        place_arp_bar(b, gain=1.0)   # arp STAYS in dip (bass goes silent)
        continue
    place_arp_bar(b, gain=0.75)
# Convergence: 32nds again
for b in range(B_CONV, B_FOLD):
    g = 0.60 + 0.40 * (b - B_CONV) / max(1, B_FOLD - B_CONV)
    place_arp_bar(b, double_speed=True, gain=g)
# THE FOLD: 16ths, slightly quieter (lead is louder)
for b in range(B_FOLD, B_STILL):
    if b in ALL_DIPS:
        place_arp_bar(b, gain=0.85)
        continue
    place_arp_bar(b, gain=0.60)
# Arrival: fading
for b in range(B_ARR, B_VOID - 8):
    g = max(0.20, 1.0 - (b - B_ARR) / max(1, B_VOID - 8 - B_ARR) * 0.75)
    place_arp_bar(b, gain=g)

lay_L = reverb(lay_L, IR_L, wet=0.28)
lay_R = reverb(lay_R, IR_R, wet=0.28)
commit(lay_L, lay_R, 0.10)
del lay_L, lay_R
print("arpeggio committed")


# ─────────────────────────────────────────────────────────────────────────────
# FM GOA LEAD — the Juno Reactor signature
# Two-operator PM: y = sin(φ_c + I·sin(φ_m)), φ_m = 2π·f·ratio·t,
# ratio=3 (nasal/hollow). Index 4→0.8 decay → bright attack mellows.
# Detuned second voice (×1.004) panned opposite for stereo width.
# Filter sweep: bright attack (4 kHz) → warm sustain (1.5 kHz).
# ─────────────────────────────────────────────────────────────────────────────

THEME_FOLD = [
    (E4, 1.0), (65, 0.5), (GS4, 1.5), (B4, 1.0),          # bar 1
    (72, 0.5), (B4, 0.5), (GS4, 1.0), (69, 0.5), (GS4, 0.5), (E4, 1.0),  # bar 2
    (72, 0.5), (75, 1.0), (E5, 1.5),  (75, 0.5), (72, 0.5),  # bar 3
    (B4, 1.0), (GS4, 3.0),                                  # bar 4: long G# resolution
]

fm_cache = {}


def fm_lead_note(midi, dur_s, idx0=4.0, idx1=0.8, ratio=3.0):
    key = (midi, round(dur_s, 3))
    if key in fm_cache:
        return fm_cache[key]
    f = midi_to_hz(midi)
    n = int((dur_s + 0.10) * SR)
    td = np.arange(n) / SR
    vib = 1.0 + 0.006 * np.sin(2 * np.pi * 5.5 * td) * np.clip(td / 0.4, 0, 1)
    idx = idx0 * np.exp(-td / 0.18) + idx1 * (1 - np.exp(-td / 0.18))
    ph_c  = 2 * np.pi * np.cumsum(f * vib) / SR
    ph_c2 = 2 * np.pi * np.cumsum(f * 1.004 * vib) / SR
    ph_m  = 2 * np.pi * f * ratio * td
    y1 = np.sin(ph_c  + idx * np.sin(ph_m))
    y2 = np.sin(ph_c2 + idx * np.sin(ph_m * 1.004))
    # Filter sweep: bright attack → warm sustain
    sos_hi = signal.butter(2, min(4200, SR // 2 - 100), "low", fs=SR, output="sos")
    sos_lo = signal.butter(2, 1500, "low", fs=SR, output="sos")
    bpk_hi, apk_hi = signal.iirpeak(min(3800, SR // 2 - 100), Q=8.0, fs=SR)
    bpk_lo, apk_lo = signal.iirpeak(1300, Q=7.0, fs=SR)
    def filt(y):
        yh = signal.sosfilt(sos_hi, y); yh += 1.2 * signal.lfilter(bpk_hi, apk_hi, yh)
        yl = signal.sosfilt(sos_lo, y); yl += 1.1 * signal.lfilter(bpk_lo, apk_lo, yl)
        sw = np.exp(-td / 0.12)
        return np.tanh(1.8 * (sw * yh + (1 - sw) * yl))
    y1 = filt(y1)
    y2 = filt(y2)
    env = (1 - np.exp(-td / 0.003)) * np.clip((dur_s - td) / 0.025, 0, 1)
    y1 *= env; y2 *= env
    pk = max(np.max(np.abs(y1)), np.max(np.abs(y2)), 1e-12)
    fm_cache[key] = (y1 / pk, y2 / pk)
    return fm_cache[key]


def place_lead(notes, t0, pan_c=0.50, gain=1.0, octave_up=False):
    tcur = t0
    for m, dur_beats in notes:
        dur_s = dur_beats * BEAT
        m_play = (m + 12) if octave_up else m
        vL, vR = fm_lead_note(m_play, dur_s)
        p = pan_c
        add_at(lay_L, vL, tcur, gain * np.cos(p * np.pi / 2))
        add_at(lay_R, vL, tcur, gain * np.sin(p * np.pi / 2))
        p2 = 1.0 - pan_c
        add_at(lay_L, vR, tcur, gain * 0.50 * np.cos(p2 * np.pi / 2))
        add_at(lay_R, vR, tcur, gain * 0.50 * np.sin(p2 * np.pi / 2))
        tcur += dur_s


lay_L = np.zeros(N)
lay_R = np.zeros(N)

# Distant call (intro): lone phrase before the drop
vL, vR = fm_lead_note(E4, 2.0, idx0=2.0, idx1=0.4)
add_at(lay_L, vL, 3.5, 0.45 * np.cos(0.55 * np.pi / 2))
add_at(lay_R, vL, 3.5, 0.45 * np.sin(0.55 * np.pi / 2))

# Prescience DROP 1 (bars 40–71): THEME_FOLD every 4 bars, skip DIP_P
for b_start in range(B_PRESC, B_BREATH, 4):
    if any(b in DIP_P for b in range(b_start, b_start + 4)):
        continue
    pan = 0.48 + 0.06 * ((b_start - B_PRESC) // 8 % 2)
    gain = 0.85 if b_start == B_PRESC else 1.0
    place_lead(THEME_FOLD, bar_t(b_start), pan_c=pan, gain=gain)

# DIP_P: lone fragment (keeps energy alive)
vL, vR = fm_lead_note(GS4, 2 * BEAT, idx0=2.5, idx1=0.6)
t_dip = bar_t(min(DIP_P)) + BEAT
add_at(lay_L, vL, t_dip, 0.70 * np.cos(0.5 * np.pi / 2))
add_at(lay_R, vL, t_dip, 0.70 * np.sin(0.5 * np.pi / 2))

# Held Breath (bars 72–79): fragment only
vL, vR = fm_lead_note(B4, 1.5 * BEAT, idx0=2.0, idx1=0.5)
add_at(lay_L, vL, bar_t(B_BREATH) + BAR, 0.55 * np.cos(0.52 * np.pi / 2))
add_at(lay_R, vL, bar_t(B_BREATH) + BAR, 0.55 * np.sin(0.52 * np.pi / 2))

# THE FOLD (bars 88–135): THEME_FOLD octave up; add counter-voice at some phrases
for b_start in range(B_FOLD, B_STILL, 4):
    if any(b in DIP_F1 or b in DIP_F2 for b in range(b_start, b_start + 4)):
        continue
    pan = 0.52 - 0.06 * ((b_start - B_FOLD) // 8 % 2)
    place_lead(THEME_FOLD, bar_t(b_start), pan_c=pan, gain=1.0, octave_up=True)
    # Every other 8-bar phrase: add counter-voice at original octave
    if (b_start - B_FOLD) % 8 == 4:
        place_lead(THEME_FOLD, bar_t(b_start) + BEAT * 0.5,
                   pan_c=1.0 - pan, gain=0.55, octave_up=False)

# DIP_F1 fragment
vL, vR = fm_lead_note(E5, 1.5 * BEAT, idx0=3.0, idx1=0.7)
add_at(lay_L, vL, bar_t(min(DIP_F1)) + BEAT, 0.75 * np.cos(0.48 * np.pi / 2))
add_at(lay_R, vL, bar_t(min(DIP_F1)) + BEAT, 0.75 * np.sin(0.48 * np.pi / 2))

# DIP_F2 fragment
vL, vR = fm_lead_note(GS4 + 12, 2.0 * BEAT, idx0=3.0, idx1=0.7)
add_at(lay_L, vL, bar_t(min(DIP_F2)) + BEAT * 0.5, 0.75 * np.cos(0.5 * np.pi / 2))
add_at(lay_R, vL, bar_t(min(DIP_F2)) + BEAT * 0.5, 0.75 * np.sin(0.5 * np.pi / 2))

# ARRIVAL (bars 144–167): THEME_FOLD at original register, resolved and warm
for b_start in range(B_ARR, B_VOID - 4, 4):
    g = max(0.45, 1.0 - (b_start - B_ARR) / max(1, B_VOID - 4 - B_ARR) * 0.55)
    place_lead(THEME_FOLD, bar_t(b_start), pan_c=0.50, gain=g)

lay_L = reverb(lay_L, IR_L, wet=0.35)
lay_R = reverb(lay_R, IR_R, wet=0.35)
commit(lay_L, lay_R, 0.22)
del lay_L, lay_R
print(f"FM Goa lead committed ({len(fm_cache)} cached notes)")


# ─────────────────────────────────────────────────────────────────────────────
# 303 ACID — subordinate counter-voice (the lead is the melody here)
# E Hijaz Kar riffs; no Bb→A war cry.
# ─────────────────────────────────────────────────────────────────────────────

# RIFF_NAV1: low bass register, E2 territory; F2→G#2 aug-2nd slide prominent
# RIFF_NAV2: mid register E3→E4; counter to the FM lead
# (E3/GS3/B3/C4 already defined from choir section; F3 needed here)
F3 = 53   # F3 in E Hijaz Kar (the lower aug-2nd step)
RIFF_NAV1 = [
    (E2, 1, None),  (None, 0, None), (E2, 0, None),  (F2, 1, GS2),
    (GS2, 0, None), (None, 0, None), (B2, 0, None),  (None, 0, None),
    (E2, 1, None),  (None, 0, None), (C3, 0, None),  (GS2, 0, None),
    (B2, 0, None),  (None, 0, None), (A2, 1, GS2),   (GS2, 0, None),
]
RIFF_NAV2 = [
    (E3, 1, None),  (None, 0, None), (E3, 0, None),  (F3, 0, GS3),
    (GS3, 0, None), (None, 0, None), (B3, 0, None),  (GS3, 1, E3),
    (C4, 1, None),  (None, 0, None), (B3, 0, None),  (GS3, 0, None),
    (F3, 0, None),  (GS3, 0, None),  (E3, 1, None),  (None, 0, None),
]

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
    for k in range(1, min(48, int(10500 / min(f, midi_to_hz(slide_to) if slide_to else f))) + 1):
        x += np.sin(k * ph) / k

    def res_lp(sig_in, c):
        c = float(min(c, 9000.0))
        sos_lp = signal.butter(2, c, "low", fs=SR, output="sos")
        y = signal.sosfilt(sos_lp, sig_in)
        bpk, apk = signal.iirpeak(min(c, 8000.0), Q=11.0, fs=SR)
        return y + (1.9 if accent else 1.4) * signal.lfilter(bpk, apk, y)

    bright = res_lp(x, cutoff * 3.0)
    dark   = res_lp(x, cutoff * 0.75)
    sweep  = np.exp(-td / (0.10 if accent else 0.055))
    y = np.tanh(2.8 * (sweep * bright + (1 - sweep) * dark))
    env = (1 - np.exp(-td / 0.0015)) * np.clip((dur - td) / 0.02, 0, 1)
    y *= env
    y /= np.max(np.abs(y)) + 1e-12
    acid_cache[key] = y
    return y


lay_L = np.zeros(N)
lay_R = np.zeros(N)


def acid_bars(b0, b1, riff, cut_lo, cut_hi, gain=1.0, ramp=False):
    for b in range(b0, b1):
        frac = (b - b0) / max(1, b1 - b0)
        if ramp:
            base = cut_lo + (cut_hi - cut_lo) * frac
        else:
            base = cut_lo + (cut_hi - cut_lo) * (
                0.5 + 0.5 * np.sin(2 * np.pi * (b - b0) / 16 - np.pi / 2))
        for s, (m, acc, sl) in enumerate(riff):
            if m is None:
                continue
            cut = base * (1.0 + 0.22 * np.sin(2 * np.pi * s / 16))
            x = acid_note(m, cut, accent=bool(acc), slide_to=sl)
            p = 0.50 + 0.18 * np.sin(2 * np.pi * (b * 16 + s) / 24)
            add_at(lay_L, x, bar_t(b, s * 0.25), gain * np.cos(p * np.pi / 2))
            add_at(lay_R, x, bar_t(b, s * 0.25), gain * np.sin(p * np.pi / 2))


# Lattice build: acid ramps in
acid_bars(B_LATT, B_PRESC, RIFF_NAV1, 250, 1000, gain=0.65, ramp=True)
# Prescience: RIFF_NAV1 drives (subordinate to lead)
# DIP_P = bars 56-59 = B_PRESC+16 .. B_PRESC+19 — acid silent there
acid_bars(B_PRESC, B_PRESC + 16, RIFF_NAV1, 350, 1800, gain=0.65)    # bars 40-55
acid_bars(B_PRESC + 20, B_BREATH, RIFF_NAV1, 500, 2200, gain=0.70)   # bars 60-71
# Convergence build: acid climbs
acid_bars(B_CONV, B_FOLD, RIFF_NAV1, 400, 3000, gain=0.72, ramp=True)
# THE FOLD: both riffs at once — NAV1 low, NAV2 high counter
# DIP_F1 = bars 104-107 = B_FOLD+16 .. B_FOLD+19
# DIP_F2 = bars 120-123 = B_FOLD+32 .. B_FOLD+35
acid_bars(B_FOLD, B_FOLD + 16, RIFF_NAV1, 500, 2500, gain=0.60)      # bars 88-103
acid_bars(B_FOLD, B_FOLD + 16, RIFF_NAV2, 800, 3000, gain=0.55)      # bars 88-103
acid_bars(B_FOLD + 20, B_FOLD + 32, RIFF_NAV1, 700, 3200, gain=0.65) # bars 108-119
acid_bars(B_FOLD + 20, B_FOLD + 32, RIFF_NAV2, 1000, 3800, gain=0.58)# bars 108-119
acid_bars(B_FOLD + 36, B_STILL, RIFF_NAV1, 700, 3000, gain=0.62)     # bars 124-135
acid_bars(B_FOLD + 36, B_STILL, RIFF_NAV2, 1200, 4500, gain=0.68)    # bars 124-135
# Arrival: warmer cutoffs (resolved feel)
acid_bars(B_ARR, B_ARR + 16, RIFF_NAV1, 400, 1600, gain=0.55)
acid_bars(B_ARR + 16, B_VOID - 4, RIFF_NAV1, 300, 1200, gain=0.45)

commit(lay_L, lay_R, 0.14)
del lay_L, lay_R
print(f"acid committed ({len(acid_cache)} cached notes)")


# ─────────────────────────────────────────────────────────────────────────────
# ZAPS
# ─────────────────────────────────────────────────────────────────────────────

def make_zap():
    n = int(0.40 * SR)
    td = np.arange(n) / SR
    f_curve = 80.0 + 1900.0 * np.exp(-td * 18.0)
    x = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    x *= 1.0 + 0.5 * np.sin(2 * np.pi * 35.0 * td)
    x *= np.exp(-td * 8.0) * (1 - np.exp(-td / 0.002))
    return x / (np.max(np.abs(x)) + 1e-12)


ZAP = make_zap()

lay_L = np.zeros(N)
lay_R = np.zeros(N)
zap_bars = ([B_PRESC, B_PRESC + 8, B_PRESC + 16, B_PRESC + 24] +
            [B_FOLD, B_FOLD + 8, B_FOLD + 16, B_FOLD + 24,
             B_FOLD + 32, B_FOLD + 44] +
            [B_ARR, B_ARR + 8])
for b in zap_bars:
    beat = float(rng.choice([0.0, 1.5, 3.5]))
    p = rng.uniform(0.2, 0.8)
    add_at(lay_L, ZAP, bar_t(b, beat), np.cos(p * np.pi / 2))
    add_at(lay_R, ZAP, bar_t(b, beat), np.sin(p * np.pi / 2))
lay_L = reverb(lay_L, IR_L, wet=0.32)
lay_R = reverb(lay_R, IR_R, wet=0.32)
commit(lay_L, lay_R, 0.07)
del lay_L, lay_R
print("zaps committed")


# ─────────────────────────────────────────────────────────────────────────────
# RISERS
# ─────────────────────────────────────────────────────────────────────────────

def riser(dur=4.0):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    nz = rng.standard_normal(n)
    out = np.zeros(n)
    K = 10
    for k in range(K):
        c = 300.0 * (5500.0 / 300.0) ** (k / (K - 1))
        sos_r = signal.butter(2, [c * 0.7, min(c * 1.4, SR / 2 - 100)],
                              "bandpass", fs=SR, output="sos")
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
for b0, dur_bars in [(B_LATT + 4, 4), (B_CONV + 4, 4),
                     (B_PRESC + 28, 4), (B_FOLD + 48, 4)]:
    rz = riser(dur_bars * BAR)
    add_at(lay_L, rz, bar_t(b0), 0.85)
    add_at(lay_R, rz, bar_t(b0), 1.00)
commit(lay_L, lay_R, 0.09)
del lay_L, lay_R
print("risers committed")


# ─────────────────────────────────────────────────────────────────────────────
# REVERSE CYMBALS / FOLD WHOOSH
# ─────────────────────────────────────────────────────────────────────────────

def rev_cymbal(dur=1.6):
    n = int(dur * SR)
    td = np.arange(n) / SR
    sos_c = signal.butter(4, 6000, "high", fs=SR, output="sos")
    x = signal.sosfilt(sos_c, rng.standard_normal(n)) * np.exp(-td * 6.0)
    return (x[::-1].copy()) / (np.max(np.abs(x)) + 1e-12)


def fold_whoosh(dur=3.5):
    """Long reversed noise sweep — the space fold completing."""
    n = int(dur * SR)
    td = np.arange(n) / SR
    sos_w = signal.butter(4, 2500, "high", fs=SR, output="sos")
    x = signal.sosfilt(sos_w, rng.standard_normal(n)) * np.exp(-td * 2.5)
    f_mod = 150.0 * 2.0 ** (2.5 * td / dur)
    x *= 1.0 + 0.45 * np.sin(2 * np.pi * np.cumsum(f_mod) / SR)
    x = x[::-1].copy()
    return x / (np.max(np.abs(x)) + 1e-12)


lay_L = np.zeros(N)
lay_R = np.zeros(N)
for b0 in [B_PRESC, B_PRESC + 32, B_FOLD, B_FOLD + 32, B_FOLD + 48, B_ARR]:
    rc = rev_cymbal(rng.uniform(1.2, 1.8))
    t0 = bar_t(b0) - len(rc) / SR
    p = rng.uniform(0.32, 0.68)
    add_at(lay_L, rc, t0, np.cos(p * np.pi / 2))
    add_at(lay_R, rc, t0, np.sin(p * np.pi / 2))
# Fold whoosh: ends exactly at the STILLPOINT (climax moment)
wh = fold_whoosh(3.5)
t_wh = still_t - len(wh) / SR
add_at(lay_L, wh, t_wh, 0.90)
add_at(lay_R, wh, t_wh, 0.90)
commit(lay_L, lay_R, 0.08)
del lay_L, lay_R
print("reverse cymbals + fold whoosh committed")


# ─────────────────────────────────────────────────────────────────────────────
# GAS BUBBLE TEXTURES — sparse events in Submersion and Held Breath
# ─────────────────────────────────────────────────────────────────────────────

def gas_bubble(dur_ms=22):
    n = int(dur_ms * SR / 1000)
    td = np.arange(n) / SR
    sos_b = signal.butter(2, [400, 3000], "bandpass", fs=SR, output="sos")
    x = signal.sosfilt(sos_b, rng.standard_normal(n))
    f_curve = 280.0 + 900.0 * np.exp(-td * 90.0)
    x += 0.55 * (np.sin(2 * np.pi * np.cumsum(f_curve) / SR) *
                 np.exp(-td * 75.0))
    env = np.exp(-td * 55.0) * (1 - np.exp(-td * 900.0))
    x *= env
    return x / (np.max(np.abs(x)) + 1e-12)


lay_L = np.zeros(N)
lay_R = np.zeros(N)
bubble_times = (
    [GRID0 + rng.uniform(0.5, 1.5) + i * rng.uniform(1.8, 3.2)
     for i in range(12)] +
    [bar_t(B_BREATH) + 1.5 + i * rng.uniform(2.0, 4.0) for i in range(5)]
)
for t0 in bubble_times:
    bub = gas_bubble(rng.uniform(15, 30))
    p = rng.uniform(0.25, 0.75)
    g = rng.uniform(0.35, 0.75)
    add_at(lay_L, bub, t0, g * np.cos(p * np.pi / 2))
    add_at(lay_R, bub, t0, g * np.sin(p * np.pi / 2))
commit(lay_L, lay_R, 0.05)
del lay_L, lay_R
print("gas bubbles committed")


# ─────────────────────────────────────────────────────────────────────────────
# STILLPOINT HIT — the fold completes; one vast metallic ring, then silence
# ─────────────────────────────────────────────────────────────────────────────

def make_stillpoint_hit():
    n = int(9.0 * SR)
    td = np.arange(n) / SR
    f = midi_to_hz(E3)   # E3 ≈ 164 Hz
    # Inharmonic metallic partials
    partials = [(1.0, 1.0), (2.756, 0.52), (5.404, 0.32), (8.933, 0.18)]
    x = np.zeros(n)
    for ratio, amp in partials:
        x += amp * np.sin(2 * np.pi * f * ratio * td +
                          rng.uniform(0, 2 * np.pi))
    sos_hi = signal.butter(2, 400, "high", fs=SR, output="sos")
    x = signal.sosfilt(sos_hi, x)
    env = (1 - np.exp(-td / 0.018)) * np.exp(-td * 0.55)
    x *= env
    return x / (np.max(np.abs(x)) + 1e-12)


lay_L = np.zeros(N)
lay_R = np.zeros(N)
hit = make_stillpoint_hit()
hit_rv_L = reverb(hit, IR_L, wet=0.65)
hit_rv_R = reverb(hit, IR_R, wet=0.65)
add_at(lay_L, hit_rv_L, still_t, 1.0)
add_at(lay_R, hit_rv_R, still_t, 1.0)
commit(lay_L, lay_R, 0.20)
del lay_L, lay_R
print("stillpoint hit committed")


# ─────────────────────────────────────────────────────────────────────────────
# MASTER CHAIN
# High shelf +0.24 (unchanged), single low shelf +0.18 @ 105 Hz.
# Deep 55 Hz shelf REMOVED — that was the earbud-clipping culprit.
# Bus tanh: 1.45×, 0.90 out (slightly more glue vs 1.35/0.88).
# ─────────────────────────────────────────────────────────────────────────────

sos_shelf = signal.butter(2, 3000, "high", fs=SR, output="sos")
mix_L += 0.24 * signal.sosfilt(sos_shelf, mix_L)
mix_R += 0.24 * signal.sosfilt(sos_shelf, mix_R)

sos_sub = signal.butter(2, 105, "low", fs=SR, output="sos")
mix_L += 0.18 * signal.sosfilt(sos_sub, mix_L)
mix_R += 0.18 * signal.sosfilt(sos_sub, mix_R)

print("master shelves applied (high + single low, no deep 55 Hz shelf)")

fade(mix_L, fade_in=5.0, fade_out=18.0)
fade(mix_R, fade_in=5.0, fade_out=18.0)

peak = max(np.max(np.abs(mix_L)), np.max(np.abs(mix_R)))
mix_L = np.tanh(1.45 * mix_L / peak) / np.tanh(1.45) * 0.90
mix_R = np.tanh(1.45 * mix_R / peak) / np.tanh(1.45) * 0.90

stereo = np.empty((N, 2))
stereo[:, 0] = mix_L
stereo[:, 1] = mix_R
pcm = (stereo * 32767.0).astype(np.int16)

OUT_DIR = "/workspace/music"
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, "the_navigator.wav")
with wave.open(OUT, "wb") as wf:
    wf.setnchannels(2)
    wf.setsampwidth(2)
    wf.setframerate(SR)
    wf.writeframes(pcm.tobytes())

print(f"\nCreated: {os.path.abspath(OUT)}")
print(f"Duration: {N / SR:.1f} s  |  {SR} Hz stereo, 16-bit PCM  |  "
      f"{BPM:.0f} BPM  |  {N_LAYERS} committed layers")
print("Section map:")
for name, b in [
    ("SUBMERSION: drone + choir + sparse tabla", B_SUBM),
    ("  kick enters 4-on-floor", B_AWARE),
    ("  rolling bass joins", B_AWARE + 4),
    ("  arp glints begin", B_AWARE + 8),
    ("THE LATTICE (build): riser + acid ramps", B_LATT),
    ("PRESCIENCE DROP 1: FM lead + THEME_FOLD", B_PRESC),
    ("  mini-dip: arp holds, bass silent", min(DIP_P)),
    ("  re-entrance after dip", max(DIP_P) + 1),
    ("THE HELD BREATH: kick drops", B_BREATH),
    ("CONVERGENCE (build 2): 32nd arps + acid climb", B_CONV),
    ("THE FOLD DROP 2: THEME_FOLD octave up", B_FOLD),
    ("  mini-dip 1", min(DIP_F1)),
    ("  mini-dip 2", min(DIP_F2)),
    ("STILLPOINT: one hit, then dead air", B_STILL),
    ("ARRIVAL: final drop, resolved", B_ARR),
    ("THE VOID BEYOND: strip layer by layer", B_VOID),
]:
    print(f"  {bar_t(b):6.1f} s  bar {b:3d}  {name}")
print(f"  {DURATION:6.1f} s  end")
