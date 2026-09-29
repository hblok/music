"""Goa FX vocabulary: chatter, bubble-rise, snap, tape flutter, harmonic bloom.

`snap` is a pitch utility over `SCALE_PCS` (F# natural minor) kept because swarm cells depend on it; it is not audible and is asserted in the __main__ below.

Extracted VERBATIM from the goa/psy track scripts (which are unchanged):
  - `chatter_burst` <- `phototaxis_v2.py:chatter_burst` -- machine-elf FM blips -- CONVERTED to return an event
  - `bubble_rise` <- `phototaxis_v2.py:bubble_rise` -- the accelerating seam device -- CONVERTED
  - `snap` <- `phototaxis_v2.py:snap` -- snap a pitch to F# natural minor (utility, not a sound)
  - `tape_flutter` <- `meridian.py:tape_flutter` -- meridian seam #1 -- CONVERTED
  - `harmonic_bloom` <- `meridian.py:harmonic_bloom` -- meridian seam #2 -- CONVERTED

See ../CLAUDE.md and README.md for the identity rules.
Seed 1995 = phototaxis seed (the year); each module seeds once.
"""
from __future__ import annotations

import numpy as np

from _common import BAR, SR, add_at, lowpass, midi_to_hz, pm_core, rc_attack, run_audition

rng = np.random.default_rng(1995)


def place(layer, x, t, gain=1.0, pan=0.0):
    """Constant-power pan of a mono event into a stereo layer pair."""
    a = (pan + 1.0) / 2.0
    add_at(layer[0], x, t, gain * np.cos(a * np.pi / 2))
    add_at(layer[1], x, t, gain * np.sin(a * np.pi / 2))


def chatter_burst():
    """Machine-elf chatter: 3-6 tiny random-ratio FM blips, panned wide.
    Converted from the layer-writing original: RETURNS a stereo (L, R)
    pair (place it at the burst's start time t0)."""
    L = np.zeros(int(0.6 * SR))
    R = np.zeros(int(0.6 * SR))
    t = 0.0
    for _ in range(int(rng.integers(3, 7))):
        m = float(rng.uniform(90, 103))
        dur = float(rng.uniform(0.04, 0.09))
        n = int(dur * SR)
        td = np.arange(n) / SR
        idx = float(rng.uniform(2.0, 5.0)) * np.exp(-td / 0.02)
        y, _ = pm_core(midi_to_hz(m), n, float(rng.uniform(2.0, 6.0)), idx)
        y *= np.exp(-td / (dur * 0.4)) * rc_attack(n, 0.002)
        y /= np.max(np.abs(y)) + 1e-12
        place((L, R), y, t, 0.8, float(rng.uniform(-0.9, 0.9)))
        t += float(rng.uniform(0.03, 0.08))
    end = int((t + 0.1) * SR)
    return L[:end], R[:end]


def bubble_rise():
    """The seam device: accelerating rising gurgle blips over 2 bars.
    Converted from the layer-writing original `bubble_rise(layer, t_end)`:
    RETURNS a stereo (L, R) pair of length 2 * BAR; place it at
    `t_end - 2 * BAR` (the original wrote blips at that offset itself)."""
    L = np.zeros(int(2 * BAR * SR) + int(0.1 * SR))
    R = np.zeros(len(L))
    n_blips = 22
    u = np.linspace(0, 1, n_blips) ** 1.6
    times = u * (2 * BAR - 0.06)
    for i, tt in enumerate(times):
        frac = i / (n_blips - 1)
        m = 66 + 24 * frac                              # F#4 -> F#6
        nb = int(0.07 * SR)
        td = np.arange(nb) / SR
        y, _ = pm_core(midi_to_hz(m), nb, 2.0, 2.0 * np.exp(-td / 0.03))
        y *= np.exp(-td / 0.03) * rc_attack(nb, 0.002)
        y /= np.max(np.abs(y)) + 1e-12
        place((L, R), y, tt, 0.4 + 0.5 * frac, -0.8 + 1.6 * frac)
    return L, R


SCALE_PCS = {6, 8, 9, 11, 1, 2, 4}          # F# natural minor pitch classes


def snap(midi):
    """Snap a (transposed) swarm pitch into F# natural minor — the harmony
    loop moves cells by chromatic shift, this keeps them diatonic (and
    keeps the track's single E# the underglow V chord's alone)."""
    if midi % 12 in SCALE_PCS:
        return midi
    if (midi - 1) % 12 in SCALE_PCS:
        return midi - 1
    return midi + 1


def tape_flutter(dur, root_midi):
    """Meridian's seam device #1: a slow wow + flutter pitch-warble that
    swells under a section boundary -- the tape wobble. A detuned low
    triad whose pitch drifts (0.7 Hz wow) and shimmers (6.5 Hz flutter),
    fading in and back out across the seam. Composed, no noise sweep.
    Converted from `tape_flutter(layer, t0, dur, root_midi)`: RETURNS the
    stereo (L, R) pair; place it at t0."""
    n = int(dur * SR)
    td = np.arange(n) / SR
    warp = (1.0 + 0.011 * np.sin(2 * np.pi * 0.7 * td)
            + 0.006 * np.sin(2 * np.pi * 6.5 * td))
    L = np.zeros(n)
    R = np.zeros(n)
    for m, g, det in ((root_midi, 1.0, 1.0), (root_midi + 7, 0.55, 1.003),
                      (root_midi + 12, 0.45, 0.997)):
        f = midi_to_hz(m)
        ph = 2 * np.pi * np.cumsum(f * det * warp) / SR
        y = np.sin(ph) + 0.30 * np.sin(2 * ph)
        L += g * y
        R += g * (np.sin(ph / det) + 0.30 * np.sin(2 * ph / det))
    swell = np.sin(np.pi * np.clip(td / dur, 0, 1)) ** 1.4   # in and out
    L = lowpass(L, 1700) * swell
    R = lowpass(R, 1700) * swell
    pk = max(np.max(np.abs(L)), np.max(np.abs(R))) + 1e-12
    return L / pk, R / pk


def harmonic_bloom(root_midi, major):
    """Meridian's seam device #2 (replaces the bubble-rise): a sustained
    FM chord whose index BLOOMS open (0 -> bright) across 2 bars into the
    downbeat -- the composed riser. Third tracks the section (major bloom
    into a chorus, Dorian bloom elsewhere).  Converted from
    `harmonic_bloom(layer, t_end, root_midi, major)`: RETURNS the stereo
    (L, R) pair of length 2 * BAR; place it at `t_end - 2 * BAR`."""
    dur = 2 * BAR
    n = int(dur * SR)
    td = np.arange(n) / SR
    idx = 4.2 * (td / dur) ** 1.5                        # 0 -> 4.2 bloom
    third = 4 if major else 3
    L = np.zeros(n)
    R = np.zeros(n)
    for k, m in enumerate((root_midi, root_midi + third, root_midi + 7,
                           root_midi + 12)):
        f = midi_to_hz(m)
        y, _ = pm_core(f, n, 2.0, idx)
        pan = -0.5 + 0.33 * k
        a = (pan + 1.0) / 2.0
        L += np.cos(a * np.pi / 2) * y
        R += np.sin(a * np.pi / 2) * y
    env = rc_attack(n, dur * 0.85) * (0.4 + 0.6 * td / dur)
    L = lowpass(L, 3200) * env
    R = lowpass(R, 3200) * env
    pk = max(np.max(np.abs(L)), np.max(np.abs(R))) + 1e-12
    return L / pk, R / pk


AUDITION = [
    ("chatter_burst", lambda: chatter_burst()),
    ("bubble_rise", lambda: bubble_rise()),
    ("tape_flutter", lambda: tape_flutter(3.0, 40)),
    ("harmonic_bloom minor", lambda: harmonic_bloom(40, False)),
    ("harmonic_bloom major", lambda: harmonic_bloom(40, True)),
]

if __name__ == "__main__":
    assert snap(66) == 66 and snap(67) == 66     # G -> F# (not in F# minor)
    run_audition("fx", AUDITION)
