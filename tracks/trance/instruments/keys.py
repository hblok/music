"""Trance keys & bells.

The skyline piano (`eisgang_v2.py:piano_note`) is retired (toy-xylophone verdict) and not extracted.

Extracted VERBATIM from the trance track scripts (which are unchanged):
  - `piano_note` <- `nachtkind_v3.py:piano_note` -- M1 gothic piano, OWNED by nachtkind (also lost_v6)
  - `piano_note_dream` <- `adrift.py:piano_note` -- dirty dream piano, OWNED by adrift
  - `bell_note` <- `farlight_v2.py:bell_note` -- OWNED by farlight
  - `bell_note_answer` <- `penumbra.py:bell_note` -- answer bell

See ../CLAUDE.md and README.md for the identity rules.
Seed 1993 = nachtkind_v3.
"""
from __future__ import annotations

import numpy as np
from scipy import signal

from _common import SR, midi_to_hz, run_audition

rng = np.random.default_rng(1993)


piano_cache = {}


def piano_note(midi, dur):
    key = (midi, round(dur, 2))
    if key in piano_cache:
        return piano_cache[key]
    f = midi_to_hz(midi)
    n = int((dur + 0.8) * SR)
    td = np.arange(n) / SR
    out = np.zeros(n)
    B_inh = 0.00035
    for k in range(1, min(14, int(8500 / f)) + 1):
        fk = f * k * np.sqrt(1 + B_inh * k * k)
        dec = 0.9 + 0.45 * k + f * 0.0012
        g = 1.0 / k ** 1.25
        for det in (0.9994, 1.0006):
            out += g * np.sin(2 * np.pi * fk * det * td +
                              rng.uniform(0, 2 * np.pi)) * np.exp(-td * dec)
    sos_h = signal.butter(2, [1500, 4000], "bandpass", fs=SR, output="sos")
    hammer = signal.sosfilt(sos_h, rng.standard_normal(n)) * np.exp(-td * 350)
    hammer /= np.max(np.abs(hammer)) + 1e-12
    out += 0.16 * hammer
    env = (1 - np.exp(-td / 0.0015)) * np.clip((dur + 0.35 - td) / 0.35, 0, 1)
    x = out * env
    piano_cache[key] = x / (np.max(np.abs(x)) + 1e-12)
    return piano_cache[key]


ZOH_FACTOR = 3


WOW_DEPTH = 0.0004


WOW_HZ = 0.3


PIANO_LP = signal.butter(2, 7500, "low", fs=SR, output="sos")


piano_cache_adrift = {}


def piano_note_dream(midi, dur):
    key = (midi, round(dur, 2))
    if key in piano_cache_adrift:
        return piano_cache_adrift[key]
    f = midi_to_hz(midi)
    n = int((dur + 1.0) * SR)
    td = np.arange(n) / SR
    out = np.zeros(n)
    B_inh = 0.00035
    for k in range(1, min(16, int(9000 / f)) + 1):
        fk = f * k * np.sqrt(1 + B_inh * k * k)
        dec = 0.9 + 0.45 * k + f * 0.0012
        g = 1.0 / k ** 1.15
        for det in (0.9994, 1.0006):
            out += g * np.sin(2 * np.pi * fk * det * td +
                              rng.uniform(0, 2 * np.pi)) * np.exp(-td * dec)
    sos_h = signal.butter(2, [1500, 4000], "bandpass", fs=SR, output="sos")
    hammer = signal.sosfilt(sos_h, rng.standard_normal(n)) * np.exp(-td * 350)
    hammer /= np.max(np.abs(hammer)) + 1e-12
    out += 0.20 * hammer
    env = (1 - np.exp(-td / 0.0015)) * np.clip((dur + 0.45 - td) / 0.45, 0, 1)
    x = out * env
    # THE DIRT (warm dial): sampler ZOH, worn-sample wow, soft saturation
    x = np.repeat(x[::ZOH_FACTOR], ZOH_FACTOR)[:n]
    idx = np.arange(n) * (1.0 + WOW_DEPTH * np.sin(
        2 * np.pi * WOW_HZ * td + rng.uniform(0, 2 * np.pi)))
    x = np.interp(np.clip(idx, 0, n - 1), np.arange(n), x)
    x = np.tanh(0.9 * x)
    x = signal.sosfilt(PIANO_LP, x)
    piano_cache_adrift[key] = x / (np.max(np.abs(x)) + 1e-12)
    return piano_cache_adrift[key]


bell_cache = {}


def bell_note(midi, dur):
    key = (midi, round(dur, 2))
    if key in bell_cache:
        return bell_cache[key]
    f = midi_to_hz(midi)
    n = int((dur + 2.5) * SR)
    td = np.arange(n) / SR
    out = np.zeros(n)
    scale = (660.0 / f) ** 0.3          # higher bells ring shorter
    for ratio, g, dec in [(1.0, 1.0, 1.7), (2.0, 0.42, 2.4),
                          (2.76, 0.26, 3.6), (5.40, 0.10, 7.0)]:
        for det in (0.9994, 1.0006):
            out += g * np.sin(2 * np.pi * f * ratio * det * td + rng.uniform(0, 6)) \
                   * np.exp(-td * dec / scale)
    thunk = signal.sosfilt(signal.butter(2, [1200, 4200], "bandpass", fs=SR, output="sos"),
                           rng.standard_normal(n)) * np.exp(-td * 160)
    out = out / (np.max(np.abs(out)) + 1e-12) + 0.10 * thunk / (np.max(np.abs(thunk)) + 1e-12)
    out *= (1 - np.exp(-td / 0.002)) * np.clip((dur + 2.0 - td) / 0.6, 0, 1)
    out = signal.sosfilt(signal.butter(2, 5500, "low", fs=SR, output="sos"), out)
    bell_cache[key] = out / (np.max(np.abs(out)) + 1e-12)
    return bell_cache[key]


bell_cache_penumbra = {}


def bell_note_answer(midi, dur):
    key = (midi, round(dur, 2))
    if key in bell_cache_penumbra:
        return bell_cache_penumbra[key]
    f = midi_to_hz(midi)
    n = int((dur + 2.5) * SR)
    td = np.arange(n) / SR
    out = np.zeros(n)
    scale = (660.0 / f) ** 0.3          # higher bells ring shorter
    for ratio, g, dec in [(1.0, 1.0, 1.7), (2.0, 0.42, 2.4),
                          (2.76, 0.26, 3.6), (5.40, 0.10, 7.0)]:
        for det in (0.9994, 1.0006):
            out += g * np.sin(2 * np.pi * f * ratio * det * td + rng.uniform(0, 6)) \
                   * np.exp(-td * dec / scale)
    thunk = signal.sosfilt(signal.butter(2, [1200, 4200], "bandpass", fs=SR, output="sos"),
                           rng.standard_normal(n)) * np.exp(-td * 160)
    out = out / (np.max(np.abs(out)) + 1e-12) + 0.10 * thunk / (np.max(np.abs(thunk)) + 1e-12)
    out *= (1 - np.exp(-td / 0.002)) * np.clip((dur + 2.0 - td) / 0.6, 0, 1)
    out = signal.sosfilt(signal.butter(2, 5500, "low", fs=SR, output="sos"), out)
    bell_cache_penumbra[key] = out / (np.max(np.abs(out)) + 1e-12)
    return bell_cache_penumbra[key]


AUDITION = [
    ("piano_note", lambda: piano_note(67, 1.5)),
    ("piano_note_dream", lambda: piano_note_dream(67, 1.5)),
    ("bell_note", lambda: bell_note(79, 1.5)),
    ("bell_note_answer", lambda: bell_note_answer(79, 1.5)),
]

if __name__ == "__main__":
    run_audition("keys", AUDITION)
