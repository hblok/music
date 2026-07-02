#!/usr/bin/env python3
"""Gurney's Song — solo baliset (idea C2, design in gurneys_song_notes.md).

The album's only *performed* piece: Gurney Halleck alone with his baliset
between battles. One instrument, one-take feel, fully rubato. He plays the
album's main theme (THEME_A — the duduk line from water_of_life and
kwisatz_haderach) as a song.

Baliset = 9-string, 3 courses x 3 strings: triple-course Karplus-Strong
(the oud recipe extended), body resonance via a two-mode IR (110/220 Hz),
strummed chords with staggered onsets, rubato from correlated slow noise.

v2 (user feedback): one continuous cursor — no dead seams between
sections; tuning intro cut to a breath; the arpeggio figure and the
descant get real development instead of four bars each.

Output: /workspace/music/gurneys_song_v2.wav  (~4:15, D Phrygian dominant)
"""

import wave

import numpy as np
from scipy import signal

SR = 44100
DURATION = 258.0
N = int(SR * DURATION)
t = np.arange(N) / SR

rng = np.random.default_rng(9)  # nine strings

# ---------------------------------------------------------------- helpers


def midi_to_hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def fade(x, fade_in=0.05, fade_out=6.0):
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


# ------------------------------------------------------------- instrument


def ks_string(f, dur, damp, taps=3):
    """One Karplus-Strong string, vectorized per period (CLAUDE.md oud)."""
    period = max(2, int(SR / f))
    n = int(dur * SR)
    buf = rng.uniform(-1, 1, period)
    buf = np.convolve(buf, np.ones(taps) / taps, mode="same")
    out = np.empty(((n // period) + 2) * period)
    for p in range(len(out) // period):
        out[p * period:(p + 1) * period] = buf
        buf = damp * 0.5 * (buf + np.roll(buf, 1))
    return out[:n]


CACHE = {}


def baliset_note(m, dur=2.5, kind="pluck"):
    """Triple-course baliset pluck; 'harm' = flageolet (octave harmonic)."""
    dur = float(np.clip(dur, 1.2, 8.0))
    key = (m, round(dur * 2) / 2, kind)
    if key in CACHE:
        return CACHE[key]
    dur = key[1]
    f = midi_to_hz(m)
    if kind == "harm":
        f, dets, gains = f * 2, (1.0, 1.0035), (1.0, 0.5)
        damp, band = 0.990, (200, 3000)
    else:
        dets, gains = (0.9975, 1.0, 1.0035), (0.55, 1.0, 0.7)
        damp, band = 0.9955, (90, 5200)
    n = int(dur * SR)
    out = np.zeros(n)
    for det, g in zip(dets, gains):
        out += g * ks_string(f * det, dur, damp)
    sos = signal.butter(2, band, "bandpass", fs=SR, output="sos")
    out = signal.sosfilt(sos, out)
    out *= np.clip((dur - np.arange(n) / SR) / 0.08, 0, 1)
    out /= np.max(np.abs(out)) + 1e-12
    CACHE[key] = out
    return out


inst_L = np.zeros(N)
inst_R = np.zeros(N)


def pluck(m, t0, gain, dur=2.5, kind="pluck"):
    """Place one note; pan follows pitch (strings spread across the mic)."""
    note = baliset_note(m, dur, kind)
    pan = -0.2 + 0.4 * np.clip((m - 38) / 30.0, 0, 1)
    th = (0.5 + pan * 0.5) * np.pi / 2
    add_at(inst_L, note, t0, gain * np.cos(th))
    add_at(inst_R, note, t0, gain * np.sin(th))


def strum(chord, t0, gain, up=False, dur=2.8, stag=None):
    order = list(reversed(chord[-3:])) if up else chord
    stag = rng.uniform(0.012, 0.025) if stag is None else stag
    for i, m in enumerate(order):
        pluck(m, t0 + i * stag, gain * rng.uniform(0.85, 1.15), dur)


SQUEAK = None


def add_squeak(t0):
    """Fret-slide squeak before big position shifts (performance dirt)."""
    global SQUEAK
    if SQUEAK is None:
        n = int(0.06 * SR)
        x = rng.standard_normal(n)
        sos = signal.butter(2, 2000, "high", fs=SR, output="sos")
        # ponytail: plain highpassed noise, no pitch sweep — reads fine at
        # this gain; add a swept bandpass if it sounds static
        x = signal.sosfilt(sos, x) * np.hanning(n)
        SQUEAK = x / (np.max(np.abs(x)) + 1e-12)
    if t0 > 0:
        add_at(inst_L, SQUEAK, t0, 0.05)
        add_at(inst_R, SQUEAK, t0, 0.05)


# ----------------------------------------------------------------- rubato

WANDER = slow_noise(0.15, -0.055, 0.055)  # correlated rushing/dragging


class Perf:
    """Rubato cursor: nominal grid + wander + per-note jitter."""

    def __init__(self, t0, tempo=66.0):
        self.cur = t0
        self.spb = 60.0 / tempo

    def note(self, nbeats, rit=1.0):
        onset = self.cur + WANDER[min(N - 1, int(self.cur * SR))] \
            + rng.uniform(-0.012, 0.012)
        self.cur += nbeats * self.spb * rit
        return max(0.0, onset)


# --------------------------------------------------------------- material

# THEME_A — the album's main theme (water_of_life / kwisatz_haderach)
THEME = [(62, 2), (66, 1), (63, 1), (62, 2), (60, 2), (62, 3),
         (63, 1), (66, 2), (69, 2), (67, 2), (66, 1), (63, 1),
         (62, 4), (60, 2), (63, 2), (62, 4)]

CHORDS = {"D": [38, 50, 57, 62, 66],
          "Eb": [39, 51, 58, 63, 67],
          "Cm": [36, 48, 55, 60, 63],
          "Gm": [43, 50, 58, 62, 67]}
PROG = ["D", "D", "Eb", "D", "D", "Cm", "D", "D",
        "Eb", "Eb", "D", "Gm", "Cm", "Eb", "D", "D"]

DESCANT = [(74, 4), (75, 4), (74, 4), (78, 4),
           (75, 4), (81, 4), (79, 4), (74, 4)]  # chorus 2 top line
DESCANT2 = [(81, 3), (79, 1), (78, 2), (75, 2),
            (78, 2), (74, 2), (75, 2), (74, 2)]  # the answer, falling


def play_theme(perf, up=0, gain=0.5, thumb=None, thumb_step=2, ring=1.8):
    prev = None
    for m, nb in THEME:
        rit = 1.25 if nb >= 3 else 1.0  # long note = phrase end = stretch
        on = perf.note(nb, rit)
        if prev is not None and abs(m - prev) >= 5 and rng.random() < 0.4:
            add_squeak(on - 0.09)
        pluck(m + up, on, gain * rng.uniform(0.8, 1.05),
              dur=nb * perf.spb + ring)
        if thumb:
            for k in range(0, nb, thumb_step):
                pluck(thumb[(k // thumb_step) % len(thumb)],
                      on + k * perf.spb, 0.28, dur=1.6)
        prev = m


def play_chorus(perf, g=(0.55, 0.40, 0.30), prog=PROG):
    for i, name in enumerate(prog):
        ch = CHORDS[name]
        strum(ch, perf.note(1), g[0] * rng.uniform(0.9, 1.1))
        strum(ch, perf.note(0.5), g[1] * rng.uniform(0.85, 1.1))
        strum(ch, perf.note(0.5, rit=1.15 if i % 4 == 3 else 1.0),
              g[2] * rng.uniform(0.8, 1.1), up=True)


# -------------------------------------------------------------- sections

SECTIONS = []  # (t0, name) for the RMS report


def section(t0, name):
    SECTIONS.append((t0, name))
    print(f"  {t0:6.1f} s  {name}")


print("performing...")

# One cursor threads the whole piece — sections start where the last one
# ends, chords ring across every seam, pickup runs bridge the joints.
# v1 feedback: fixed section clocks left dead gaps ("ten pieces").
P = Perf(1.5)

# -- settle: a breath, then straight into it (the long tuning intro is gone)
section(0.0, "settle")
pluck(50, P.note(2), 0.40, dur=2.2)
pluck(38, P.note(2), 0.42, dur=2.5)
pluck(62, P.note(2), 0.36, kind="harm", dur=3.0)
pluck(38, P.note(2), 0.32, dur=2.0)                  # the thumb pulse begins

# -- verse 1: the theme, low, over the thumb pedal
section(P.cur, "verse 1: the theme, low")
play_theme(P, up=0, gain=0.58, thumb=[38], thumb_step=2)
for i, m in enumerate([60, 62, 63, 66]):             # pickup run, no gap
    pluck(m, P.note(0.5), 0.40 + 0.03 * i, dur=1.5)

# -- chorus 1: strummed
section(P.cur, "chorus 1: strummed")
play_chorus(P)
strum(CHORDS["D"], P.note(2, rit=1.1), 0.45, dur=3.5)  # rings into verse 2

# -- verse 2: octave up, walking thumb
section(P.cur, "verse 2: octave up")
play_theme(P, up=12, gain=0.55, thumb=[38, 45], thumb_step=1)

# -- development: the arpeggio garden (v1's 4-bar bridge, given room)
section(P.cur, "development: arpeggios")


def arp_bar(name, gain):
    ch = CHORDS[name]
    for m in ch + ch[-2:0:-1]:                       # up and down, 8 eighths
        pluck(m, P.note(0.5), gain * rng.uniform(0.8, 1.05), dur=1.8)


for name in ["Eb", "Cm", "Gm", "D"]:                 # A: the figure alone
    arp_bar(name, 0.34)
Pm = Perf(P.cur)                                     # B: the theme over it
Pm.note(4)                                           # melody waits one bar
for m, nb in THEME[:6]:                              # phrase 1, low
    pluck(m, Pm.note(nb), 0.55, dur=nb * Pm.spb + 1.5)
for m, nb in THEME[6:12]:                            # phrase 2, octave up
    pluck(m + 12, Pm.note(nb), 0.50, dur=nb * Pm.spb + 1.5)
for name in ["D", "Eb", "Cm", "D", "Gm", "Eb", "Cm", "D"]:
    arp_bar(name, 0.36)
for i, (name, m_top) in enumerate(zip(["Eb", "Gm", "Cm", "D"],
                                      [74, 75, 78, 74])):
    pluck(m_top, P.cur, 0.46, dur=3.5)               # C: descant seeds on top
    arp_bar(name, 0.37 + 0.03 * i)

# -- chorus 2: full voice — the descant states, then answers
section(P.cur, "chorus 2: descant")
t_c2 = P.cur
play_chorus(P, g=(0.70, 0.50, 0.38))
pd = Perf(t_c2)
for m, nb in DESCANT:
    pluck(m, pd.note(nb), 0.45 * rng.uniform(0.85, 1.05),
          dur=nb * pd.spb + 1.5)
t_c2b = P.cur
play_chorus(P, g=(0.70, 0.50, 0.38), prog=PROG[8:])  # half again
pd = Perf(t_c2b)
for m, nb in DESCANT2:
    pluck(m, pd.note(nb), 0.46 * rng.uniform(0.85, 1.05),
          dur=nb * pd.spb + 1.5)

# -- arpeggios return, falling away
section(P.cur, "arpeggios return")
for i, name in enumerate(["D", "Eb", "Cm", "D"]):
    arp_bar(name, 0.40 - 0.03 * i)

# -- coda: the theme fragments, one last chord
section(P.cur, "coda: the last chord")
P.spb = 60.0 / 58.0                                  # the song leans back
frag = THEME[:6]
for j, (m, nb) in enumerate(frag):
    rit = 1.0 + 0.8 * j / (len(frag) - 1)            # the big ritardando
    pluck(m, P.note(nb, rit), 0.44 - 0.02 * j, dur=nb * P.spb + 2.0)
t_final = P.note(4)
strum(CHORDS["D"], t_final, 0.70, dur=7.0, stag=0.06)  # slow, deliberate
# hand mute: palm lands on the strings
n_mute = int(0.08 * SR)
tm = np.arange(n_mute) / SR
mute = (np.sin(2 * np.pi * 110 * tm) * np.exp(-tm / 0.02) +
        0.5 * rng.standard_normal(n_mute) * np.exp(-tm / 0.008))
sos_m = signal.butter(2, 500, "low", fs=SR, output="sos")
mute = signal.sosfilt(sos_m, mute)
mute /= np.max(np.abs(mute)) + 1e-12
t_mute = t_final + 6.5
add_at(inst_L, mute, t_mute, 0.18)
add_at(inst_R, mute, t_mute, 0.18)
inst_L[int((t_mute + 0.06) * SR):] = 0.0             # strings stop dead
inst_R[int((t_mute + 0.06) * SR):] = 0.0
SECTIONS.append((t_mute + 0.1, "room tone"))

# ---------------------------------------------------- body + room + mix

print("body resonance + room...")
n_b = int(0.5 * SR)
tb = np.arange(n_b) / SR
BODY_IR = (np.sin(2 * np.pi * 110 * tb) * np.exp(-tb / 0.12) +
           0.7 * np.sin(2 * np.pi * 220 * tb) * np.exp(-tb / 0.09))
BODY_IR /= np.sqrt(np.sum(BODY_IR ** 2))

IR_L = make_reverb_ir(0.9, 0.35, 7)
IR_R = make_reverb_ir(0.9, 0.35, 11)


def body_and_room(x, ir):
    body = signal.fftconvolve(x, BODY_IR)[: len(x)]
    body *= np.max(np.abs(x)) / (np.max(np.abs(body)) + 1e-12)
    return reverb(x + 0.18 * body, ir, wet=0.12)


inst_L = body_and_room(inst_L, IR_L)
inst_R = body_and_room(inst_R, IR_R)
pk = max(np.max(np.abs(inst_L)), np.max(np.abs(inst_R)), 1e-12)
# drive into the tanh so strum peaks glue while solo lines stay linear
inst_L *= 1.30 / pk
inst_R *= 1.30 / pk

# room tone so silence is never digital black
sos_rt = signal.butter(2, 400, "low", fs=SR, output="sos")
rt_L = signal.sosfilt(sos_rt, rng.standard_normal(N))
rt_R = signal.sosfilt(sos_rt, rng.standard_normal(N))
rt_L *= 0.015 / (np.max(np.abs(rt_L)) + 1e-12)
rt_R *= 0.015 / (np.max(np.abs(rt_R)) + 1e-12)

mix_L = np.tanh(1.25 * (inst_L + rt_L))
mix_R = np.tanh(1.25 * (inst_R + rt_R))
fade(mix_L)
fade(mix_R)

# ------------------------------------------------------------------ write

out_path = "/workspace/music/gurneys_song_v2.wav"
stereo = np.empty(2 * N, dtype=np.int16)
stereo[0::2] = (np.clip(mix_L, -1, 1) * 32767).astype(np.int16)
stereo[1::2] = (np.clip(mix_R, -1, 1) * 32767).astype(np.int16)
with wave.open(out_path, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(stereo.tobytes())

print(f"\nCreated: {out_path}")
print(f"Duration: {DURATION:.1f} s  |  {SR} Hz stereo, 16-bit PCM  |  "
      f"rubato ~66 BPM  |  {len(CACHE)} cached plucks")
print("Section map + per-section RMS:")
rms_by_name = {}
bounds = [s for s, _ in SECTIONS] + [DURATION]
for (s0, name), s1 in zip(SECTIONS, bounds[1:]):
    seg = np.concatenate([mix_L[int(s0 * SR):int(s1 * SR)],
                          mix_R[int(s0 * SR):int(s1 * SR)]])
    rms_by_name[name] = float(np.sqrt(np.mean(seg ** 2)))
    print(f"  {s0:6.1f} s  rms {rms_by_name[name]:.3f}  {name}")
loudest = max(rms_by_name, key=rms_by_name.get)
print(f"Loudest section: {loudest} (rms {rms_by_name[loudest]:.3f})")
if not loudest.startswith("chorus 2"):
    print("WARNING: chorus 2 is not the loudest section — rebalance!")
