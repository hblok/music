"""Goa pads, beds and drones.

`pad_bed` and `underglow_chord` return stereo (L, R) pairs.  Deep/dark/low bed rule: never a beating mid tone.

Extracted VERBATIM from the goa/psy track scripts (which are unchanged):
  - `pad_bed` <- `phototaxis_v2.py:pad_bed` -- v2 warm evolving floor under every groove wave (stereo)
  - `underglow_chord` <- `phototaxis_v2.py:underglow_chord` -- quiet anthem bed (stereo)
  - `pool_drone` <- `phototaxis_v2.py:pool_drone` -- phototaxis v1/v2 drone
  - `pool_drone_meridian` <- `meridian.py:pool_drone` -- meridian drone

See ../CLAUDE.md and README.md for the identity rules.
Seed 1995 = phototaxis seed (the year); each module seeds once.
"""
from __future__ import annotations

import numpy as np

from _common import SR, lowpass, midi_to_hz, pm_core, rc_attack, slow_noise, run_audition

rng = np.random.default_rng(1995)


_pad_cache = {}


def pad_bed(root_midi, dur, bright=1.0, seed=0):
    """v2 depth fix: the warm evolving floor under the whole groove.
    Root+5th+octave, wide detune, slow attack, dark LP, slow-noise evolve.
    Deep/dark/low, NOT a beating mid tone (the standing drone-bed rule) —
    root sits at F#2/E2/etc. (harm root + 12), never the mid register."""
    key = ("pad", root_midi, round(dur, 3), round(bright, 2), seed)
    if key in _pad_cache:
        return _pad_cache[key]
    n = int(dur * SR)
    L = np.zeros(n)
    R = np.zeros(n)
    for m in (root_midi, root_midi + 7, root_midi + 12):
        f = midi_to_hz(m)
        for det, buf in ((1.0018, L), (0.9982, R)):
            y, _ = pm_core(f * det, n, 1.0, 0.7)         # ratio 1, warm
            buf += y
    env = rc_attack(n, 0.22)
    rel = min(n, int(0.32 * SR))
    env[-rel:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(rel) / rel)
    evolve = 0.60 + 0.40 * slow_noise(n, 0.20, 1995 + seed)
    L = lowpass(L, 1200 * bright) * env * evolve
    R = lowpass(R, 1200 * bright) * env * evolve
    pk = max(np.max(np.abs(L)), np.max(np.abs(R))) + 1e-12
    out = ((L + 0.35 * R) / (1.35 * pk), (R + 0.35 * L) / (1.35 * pk))
    _pad_cache[key] = out
    return out


def underglow_chord(midis, dur):
    """Quiet sustained bed for the anthem waves. Wide (±0.12 % detune)."""
    n = int(dur * SR)
    td = np.arange(n) / SR
    L = np.zeros(n)
    R = np.zeros(n)
    for m in midis:
        f = midi_to_hz(m)
        for det, buf in ((1.0012, L), (0.9988, R)):
            y, _ = pm_core(f * det, n, 2.0, 0.5)
            buf += y
    env = rc_attack(n, 0.30)
    rel = min(n, int(0.25 * SR))
    env[-rel:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(rel) / rel)
    L, R = lowpass(L * env, 900), lowpass(R * env, 900)
    pk = max(np.max(np.abs(L)), np.max(np.abs(R))) + 1e-12
    # cross-blend for width per the big-room pad recipe
    return (L + 0.40 * R) / (1.4 * pk), (R + 0.40 * L) / (1.4 * pk)


def pool_drone(dur):
    """The breakdown bed: deep, dark, evolving, pulses to true zero.
    Beating lives at the 46 Hz fundamental only (slow, low — sanctioned);
    centroid is checked < 400 Hz in verify."""
    n = int(dur * SR)
    td = np.arange(n) / SR
    f0 = midi_to_hz(30)                                 # F#1 ≈ 46.25 Hz
    L = np.zeros(n)
    R = np.zeros(n)
    for gain, mult, det in ((1.0, 1.0, 0.15), (0.45, 2.0, 0.0),
                            (0.15, 3.0, 0.0)):
        L += gain * np.sin(2 * np.pi * (f0 * mult) * td)
        R += gain * np.sin(2 * np.pi * (f0 * mult + det) * td)
    breath = 0.5 - 0.5 * np.cos(2 * np.pi * td / 20.0)  # true zero / 20 s
    evolve = 0.6 + 0.4 * slow_noise(n, 0.15, 1995)
    L, R = lowpass(L, 420), lowpass(R, 420)
    L *= breath * evolve
    R *= breath * evolve
    pk = max(np.max(np.abs(L)), np.max(np.abs(R))) + 1e-12
    return L / pk, R / pk


def pool_drone_meridian(dur):
    """The breakdown bed: deep, dark, evolving, pulses to true zero.
    Beating lives at the 46 Hz fundamental only (slow, low — sanctioned);
    centroid is checked < 400 Hz in verify."""
    n = int(dur * SR)
    td = np.arange(n) / SR
    f0 = midi_to_hz(28)                                 # E1 ≈ 41.2 Hz
    L = np.zeros(n)
    R = np.zeros(n)
    for gain, mult, det in ((1.0, 1.0, 0.15), (0.45, 2.0, 0.0),
                            (0.15, 3.0, 0.0)):
        L += gain * np.sin(2 * np.pi * (f0 * mult) * td)
        R += gain * np.sin(2 * np.pi * (f0 * mult + det) * td)
    breath = 0.5 - 0.5 * np.cos(2 * np.pi * td / 20.0)  # true zero / 20 s
    evolve = 0.6 + 0.4 * slow_noise(n, 0.15, 1997)
    L, R = lowpass(L, 420), lowpass(R, 420)
    L *= breath * evolve
    R *= breath * evolve
    pk = max(np.max(np.abs(L)), np.max(np.abs(R))) + 1e-12
    return L / pk, R / pk


AUDITION = [
    ("pad_bed", lambda: pad_bed(42, 4.0)),
    ("underglow_chord", lambda: underglow_chord([54, 61, 66], 4.0)),
    ("pool_drone", lambda: pool_drone(4.0)),
    ("pool_drone_meridian", lambda: pool_drone_meridian(4.0)),
]

if __name__ == "__main__":
    run_audition("pads", AUDITION)
