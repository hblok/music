"""Goa FM leads: the swarm voices and the (dead-end) morphing lead.

`gurgle_note` is not in meridian (its lead is `lead_note`).  Names with `_v2` / `_meridian` mark reconciled variants; the unsuffixed name is the version that is identical across scripts or the first one.

Extracted VERBATIM from the goa/psy track scripts (which are unchanged):
  - `gurgle_note_v2` <- `phototaxis_v2.py:gurgle_note` -- the singer, ratio 2, index wobble; v2: held notes ring (0.22 s release)
  - `gurgle_note` <- `phototaxis.py:gurgle_note` -- v1 release
  - `fizz_note` <- `phototaxis_v2.py:fizz_note` -- the runner: ratio 1 + modulator feedback (DX7 near-saw) -- phototaxis v1 and v2 agree
  - `fizz_note_meridian` <- `meridian.py:fizz_note` -- meridian tuning of the runner
  - `glint_note` <- `phototaxis_v2.py:glint_note` -- the bell, ratio 3.53, LISTEN-CONFIRMED KEEPER -- do not touch (identical in all three scripts)
  - `murk_note` <- `phototaxis_v2.py:murk_note` -- the shadow, ratio 0.5 (identical in all three)
  - `lead_note` <- `meridian.py:lead_note` -- THE STAR of meridian -- a warm sung morphing lead. The recorded verdict on meridian was "country/western harmonica": kept for reference, per ../CLAUDE.md the goa lead SNAKES/GNARLS, it does not sing

See ../CLAUDE.md and README.md for the identity rules.
Seed 1995 = phototaxis seed (the year); each module seeds once.
"""
from __future__ import annotations

import numpy as np

from _common import BAR, SR, lowpass, midi_to_hz, pm_core, rc_attack, run_audition

rng = np.random.default_rng(1995)


_cache = {}


def gurgle_note_v2(midi, dur, held):
    """The singer: ratio 2, index WOBBLES on held notes, sung vibrato."""
    key = ("gur", midi, round(dur, 4), held)
    if key in _cache:
        return _cache[key]
    n = int(dur * SR)
    td = np.arange(n) / SR
    f = midi_to_hz(midi)
    bloom = np.clip((td - 0.30) / 0.25, 0, 1)          # vibrato blooms
    pitch = 1.0 + 0.0035 * bloom * np.sin(2 * np.pi * 5.5 * td)
    if held:
        wob_hz = 6.0 + 3.0 * rng.random()
        idx = 1.8 + 1.5 * np.sin(2 * np.pi * wob_hz * td) * rc_attack(n, 0.25)
    else:
        idx = 1.0 + 1.5 * np.exp(-td / 0.10)
    y, ph_c = pm_core(f, n, 2.0, idx, pitch_env=pitch)
    y += 0.25 * np.sin(ph_c)                            # body core
    y *= rc_attack(n, 0.10)
    rel = min(n, int((0.22 if held else 0.09) * SR))    # v2: held notes ring
    y[-rel:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(rel) / rel)
    y = lowpass(y, 2400)
    y = np.tanh(0.9 * y)
    y /= np.max(np.abs(y)) + 1e-12
    _cache[key] = y
    return y


_cache_v1 = {}


def gurgle_note(midi, dur, held):
    """The singer: ratio 2, index WOBBLES on held notes, sung vibrato."""
    key = ("gur", midi, round(dur, 4), held)
    if key in _cache_v1:
        return _cache_v1[key]
    n = int(dur * SR)
    td = np.arange(n) / SR
    f = midi_to_hz(midi)
    bloom = np.clip((td - 0.30) / 0.25, 0, 1)          # vibrato blooms
    pitch = 1.0 + 0.0035 * bloom * np.sin(2 * np.pi * 5.5 * td)
    if held:
        wob_hz = 6.0 + 3.0 * rng.random()
        idx = 1.8 + 1.5 * np.sin(2 * np.pi * wob_hz * td) * rc_attack(n, 0.25)
    else:
        idx = 1.0 + 1.5 * np.exp(-td / 0.10)
    y, ph_c = pm_core(f, n, 2.0, idx, pitch_env=pitch)
    y += 0.25 * np.sin(ph_c)                            # body core
    y *= rc_attack(n, 0.10)
    rel = min(n, int(0.09 * SR))
    y[-rel:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(rel) / rel)
    y = lowpass(y, 2400)
    y = np.tanh(0.9 * y)
    y /= np.max(np.abs(y)) + 1e-12
    _cache_v1[key] = y
    return y


def fizz_note(midi, dur):
    """The runner: ratio 1 + modulator feedback (the DX7 near-saw)."""
    key = ("fiz", midi, round(dur, 4))
    if key in _cache:
        return _cache[key]
    n = int(dur * SR)
    td = np.arange(n) / SR
    idx = 1.2 + 1.3 * np.exp(-td / 0.06)
    y, ph_c = pm_core(midi_to_hz(midi), n, 1.0, idx, fb=1.15)
    y += 0.15 * np.sin(ph_c)
    gate = int(0.80 * n)
    env = np.ones(n)
    env[gate:] *= np.exp(-(td[gate:] - td[gate]) / 0.012)
    y *= env * rc_attack(n, 0.003)
    y = lowpass(y, 5200)
    y = np.tanh(0.9 * y)
    y /= np.max(np.abs(y)) + 1e-12
    _cache[key] = y
    return y


_cache_mer = {}


def fizz_note_meridian(midi, dur):
    """The runner: ratio 1 + modulator feedback (the DX7 near-saw)."""
    key = ("fiz", midi, round(dur, 4))
    if key in _cache_mer:
        return _cache_mer[key]
    n = int(dur * SR)
    td = np.arange(n) / SR
    idx = 1.2 + 1.3 * np.exp(-td / 0.06)
    y, ph_c = pm_core(midi_to_hz(midi), n, 1.0, idx, fb=1.15)
    y += 0.15 * np.sin(ph_c)
    gate = int(0.80 * n)
    env = np.ones(n)
    env[gate:] *= np.exp(-(td[gate:] - td[gate]) / 0.012)
    y *= env * rc_attack(n, 0.018)                      # softer: a shimmer, not a chatter
    y = lowpass(y, 5200)
    y = np.tanh(0.9 * y)
    y /= np.max(np.abs(y)) + 1e-12
    _cache_mer[key] = y
    return y


def glint_note(midi):
    """The bell: non-integer ratio 3.53, index snaps shut in ~80 ms."""
    key = ("gli", midi)
    if key in _cache:
        return _cache[key]
    n = int(0.16 * SR)
    td = np.arange(n) / SR
    idx = 4.0 * np.exp(-td / 0.025)
    y, _ = pm_core(midi_to_hz(midi), n, 3.53, idx)
    y *= np.exp(-td / 0.05) * rc_attack(n, 0.001)
    y /= np.max(np.abs(y)) + 1e-12
    _cache[key] = y
    return y


def murk_note(midi, dur):
    """The shadow: ratio 0.5 (modulator below carrier), dark and hollow."""
    key = ("mur", midi, round(dur, 4))
    if key in _cache:
        return _cache[key]
    n = int(dur * SR)
    td = np.arange(n) / SR
    y, _ = pm_core(midi_to_hz(midi), n, 0.5, 0.8)
    gate = int(0.70 * n)
    env = np.ones(n)
    env[gate:] *= np.exp(-(td[gate:] - td[gate]) / 0.015)
    y *= env * rc_attack(n, 0.005)
    y = lowpass(y, 1200)
    y /= np.max(np.abs(y)) + 1e-12
    _cache[key] = y
    return y


MORPH_HZ = 1.0 / (4.0 * BAR)          # one index-morph cycle per 4 bars


def lead_note(midi, dur, held, t_abs):
    """THE STAR — the long morphing lead. Sustained + sung, and the FM
    index MORPHS on a slow LFO tied to GLOBAL time (phase-continuous
    across notes → the timbre breathes over 4-bar cycles, the liquid
    snaking goa line). Ratio steps up on the high euphoric notes. This is
    NOT the navigator's one-way decay and NOT phototaxis's short wobble:
    the morph is cyclic (net slope ~0, checked)."""
    n = int(dur * SR)
    td = np.arange(n) / SR
    f = midi_to_hz(midi)
    tg = t_abs + td                                    # global time
    bloom = np.clip((td - 0.25) / 0.25, 0, 1)          # vibrato blooms
    pitch = 1.0 + 0.004 * bloom * np.sin(2 * np.pi * 5.2 * td)
    lfo = np.sin(2 * np.pi * MORPH_HZ * tg)            # the cyclic morph
    if held:
        idx = 2.2 + 1.6 * lfo
    else:
        idx = 1.3 + 1.0 * np.exp(-td / 0.12) + 0.5 * lfo
    ratio = 3.0 if midi >= 76 else 2.0                 # brighter high notes
    y, ph_c = pm_core(f, n, ratio, idx, pitch_env=pitch)
    y += 0.25 * np.sin(ph_c)                            # body core
    y *= rc_attack(n, 0.12)                             # slow-ish attack (sings)
    rel = min(n, int((0.28 if held else 0.10) * SR))   # held notes ring
    y[-rel:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(rel) / rel)
    y = lowpass(y, 2600)
    y = np.tanh(0.9 * y)
    y /= np.max(np.abs(y)) + 1e-12
    return y


AUDITION = [
    ("gurgle_note_v2 held", lambda: gurgle_note_v2(78, 1.0, True)),
    ("gurgle_note_v2 short", lambda: gurgle_note_v2(78, 0.2, False)),
    ("gurgle_note v1 held", lambda: gurgle_note(78, 1.0, True)),
    ("fizz_note", lambda: fizz_note(78, 0.12)),
    ("fizz_note_meridian", lambda: fizz_note_meridian(78, 0.12)),
    ("glint_note", lambda: glint_note(90)),
    ("murk_note", lambda: murk_note(66, 0.25)),
    ("lead_note", lambda: lead_note(72, 1.5, True, 0.0)),
]

if __name__ == "__main__":
    run_audition("leads", AUDITION)
