"""Goa FM bass (saw-free): three variants.

The kick-gap contract lives in the sequencing (bass silent on every kick 16th), not in these voices.

Extracted VERBATIM from the goa/psy track scripts (which are unchanged):
  - `bass_note` <- `phototaxis_v2.py:bass_note` -- FM ratio 1, LP 320 + sub-octave body (v2 fattened)
  - `bass_note_v1` <- `phototaxis.py:bass_note` -- phototaxis v1 bass
  - `bass_note_meridian` <- `meridian.py:bass_note` -- meridian bass

See ../CLAUDE.md and README.md for the identity rules.
Seed 1995 = phototaxis seed (the year); each module seeds once.
"""
from __future__ import annotations

import numpy as np

from _common import SR, lowpass, midi_to_hz, pm_core, rc_attack, run_audition

rng = np.random.default_rng(1995)


_cache = {}


def bass_note(midi, dur):
    """FM bass: ratio 1, small index bite, LP 300 — saw-free by design."""
    key = ("bas", midi, round(dur, 4))
    if key in _cache:
        return _cache[key]
    n = int(dur * SR)
    td = np.arange(n) / SR
    f = midi_to_hz(midi)
    idx = 0.6 + 0.5 * np.exp(-td / 0.02)
    y, ph_c = pm_core(f, n, 1.0, idx)
    y += 0.30 * np.sin(ph_c)
    y += 0.28 * np.sin(2 * np.pi * (f / 2.0) * td)      # v2: sub octave body
    gate = int(0.85 * n)
    env = np.ones(n)
    env[gate:] *= np.exp(-(td[gate:] - td[gate]) / 0.010)
    y *= env * rc_attack(n, 0.002)
    y = lowpass(y, 320)
    y = np.tanh(1.0 * y)
    y /= np.max(np.abs(y)) + 1e-12
    _cache[key] = y
    return y


_cache_v1 = {}


def bass_note_v1(midi, dur):
    """FM bass: ratio 1, small index bite, LP 300 — saw-free by design."""
    key = ("bas", midi, round(dur, 4))
    if key in _cache_v1:
        return _cache_v1[key]
    n = int(dur * SR)
    td = np.arange(n) / SR
    idx = 0.6 + 0.5 * np.exp(-td / 0.02)
    y, ph_c = pm_core(midi_to_hz(midi), n, 1.0, idx)
    y += 0.30 * np.sin(ph_c)
    gate = int(0.85 * n)
    env = np.ones(n)
    env[gate:] *= np.exp(-(td[gate:] - td[gate]) / 0.010)
    y *= env * rc_attack(n, 0.002)
    y = lowpass(y, 300)
    y = np.tanh(1.0 * y)
    y /= np.max(np.abs(y)) + 1e-12
    _cache_v1[key] = y
    return y


_cache_mer = {}


def bass_note_meridian(midi, dur):
    """HEAVY night-goa FM bass (Q3): more grit (higher index) + a fatter
    sub octave + a touch more drive than phototaxis's — the dark engine
    under the euphoric sunrise. Still saw-free; the master HP/crest
    guardrail keeps the added weight from growling (checked)."""
    key = ("bas", midi, round(dur, 4))
    if key in _cache_mer:
        return _cache_mer[key]
    n = int(dur * SR)
    td = np.arange(n) / SR
    f = midi_to_hz(midi)
    idx = 0.70 + 0.5 * np.exp(-td / 0.025)              # some grit, not buzzy
    y, ph_c = pm_core(f, n, 1.0, idx)
    y += 0.30 * np.sin(ph_c)
    y += 0.55 * np.sin(2 * np.pi * (f / 2.0) * td)      # heavy sub octave (felt)
    gate = int(0.88 * n)
    env = np.ones(n)
    env[gate:] *= np.exp(-(td[gate:] - td[gate]) / 0.012)
    y *= env * rc_attack(n, 0.002)
    y = lowpass(y, 320)                                  # darker: sub, not mid-buzz
    y = np.tanh(1.05 * y)
    y /= np.max(np.abs(y)) + 1e-12
    _cache_mer[key] = y
    return y


AUDITION = [
    ("bass_note", lambda: bass_note(30, 0.2)),
    ("bass_note_v1", lambda: bass_note_v1(30, 0.2)),
    ("bass_note_meridian", lambda: bass_note_meridian(28, 0.2)),
]

if __name__ == "__main__":
    run_audition("bass", AUDITION)
