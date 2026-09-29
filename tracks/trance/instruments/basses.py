"""Trance basses.

`bass_note` is reused across scripts with very different characters -- the adrift one is `bass_note_tide`.
The retired lost_v3 bass is deliberately NOT extracted.

Extracted VERBATIM from the trance track scripts (which are unchanged):
  - `bass_note` <- `lost_v6.py:bass_note` -- THE rolling 16th house bass
  - `bass_note_tide` <- `adrift.py:bass_note` -- tide pulse bass, OWNED by adrift
  - `bass_hit` <- `tech_noir_v3.py:bass_hit` -- machine bass, OWNED by tech_noir
  - `thud_bass` <- `eisgang_v3.py:thud_bass` -- run-and-plant, OWNED by eisgang
  - `psy_bass_note` <- `maschinenherz.py:psy_bass_note` -- K-b-b-b psy bass (also silver_wire)
  - `sub_note` <- `silver_wire_v2.py:sub_note` -- sub-duty bass, OWNED by silver_wire

See ../CLAUDE.md and README.md for the identity rules.
Seed 130 = lost_v6.
"""
from __future__ import annotations

import numpy as np
from scipy import signal

from _common import BEAT, SR, STEP, midi_to_hz, run_audition

rng = np.random.default_rng(130)


bass_cache = {}


def bass_note(midi, cutoff, drive=0.9, dur=STEP * 0.92):
    key = (midi, int(cutoff // 60), round(drive, 1))
    if key in bass_cache:
        return bass_cache[key]
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    for k in range(1, min(22, int(3500 / f)) + 1):
        x += np.sin(2 * np.pi * k * f * td) / k ** 1.3      # rolled-off, rounder
    y = signal.sosfilt(signal.butter(2, cutoff, "low", fs=SR, output="sos"), x)
    bpk, apk = signal.iirpeak(cutoff, Q=1.2, fs=SR)         # gentle, not nasal
    y = y + 0.3 * signal.lfilter(bpk, apk, y)
    y += 0.5 * np.sin(2 * np.pi * (f / 2) * td)             # round sub for body
    y = np.tanh(drive * y)                                  # soft, not crunchy
    y *= (1 - np.exp(-td / 0.004)) * np.clip((dur - td) / 0.02, 0, 1)
    bass_cache[key] = y / (np.max(np.abs(y)) + 1e-12)
    return bass_cache[key]


SMEAR_BURST = rng.standard_normal(int(0.035 * SR)) * \
    np.exp(-np.arange(int(0.035 * SR)) / (0.012 * SR))


SMEAR_SOS = signal.butter(2, [80, 700], "bandpass", fs=SR, output="sos")


bass_cache_adrift = {}


def bass_note_tide(midi, dur=BEAT * 0.45):
    key = (midi, round(dur, 3))
    if key in bass_cache_adrift:
        return bass_cache_adrift[key]
    f = midi_to_hz(midi)
    n = int((dur + 0.06) * SR)
    td = np.arange(n) / SR
    core = (np.sin(2 * np.pi * f * td) + 0.35 * np.sin(4 * np.pi * f * td)
            + 0.12 * np.sin(6 * np.pi * f * td))
    core *= (1 - np.exp(-td / 0.008)) * np.clip((dur - td) / 0.05, 0, 1)
    smear = signal.sosfilt(SMEAR_SOS, np.tanh(2.2 * core))
    smear = signal.oaconvolve(smear, SMEAR_BURST)[:n]
    smear /= np.max(np.abs(smear)) + 1e-12
    x = core + 0.25 * smear
    bass_cache_adrift[key] = x / (np.max(np.abs(x)) + 1e-12)
    return bass_cache_adrift[key]


# 13/16: thirteen sixteenths per bar, quarter pulse ~99.5 BPM, one bar
# cycling every ~1.96 s. Grouped 3+3+3+2+2.
SIXT = 60.0 / (99.5 * 4)


bass_cache_technoir = {}


def bass_hit(midi, dur=SIXT * 0.95):
    if midi in bass_cache_technoir:
        return bass_cache_technoir[midi]
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    for k in range(1, min(28, int(3000 / f)) + 1):
        x += np.sin(2 * np.pi * k * f * td) / k
    sos_lp = signal.butter(2, 520, "low", fs=SR, output="sos")
    y = signal.sosfilt(sos_lp, x)
    y += 0.55 * np.sin(2 * np.pi * (f / 2) * td)          # round sub octave
    y = np.tanh(1.8 * y)
    y *= (1 - np.exp(-td / 0.002)) * np.exp(-td * 14.0)
    y *= np.clip((dur - td) / 0.015, 0, 1)
    bass_cache_technoir[midi] = y / (np.max(np.abs(y)) + 1e-12)
    return bass_cache_technoir[midi]


bass_cache_eisgang = {}


def thud_bass(midi, dur, weight=1.0):
    key = (midi, int(dur * 1000))
    if key in bass_cache_eisgang:
        return bass_cache_eisgang[key]
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    body = np.sin(2 * np.pi * f * td) + 0.45 * np.sin(2 * np.pi * 2 * f * td +
                                                      0.7)
    knock = signal.sosfilt(signal.butter(2, [150, 800], "bandpass", fs=SR,
                                         output="sos"),
                           rng.standard_normal(n)) * np.exp(-td * 120)
    knock /= np.max(np.abs(knock)) + 1e-12
    x = body + 0.35 * knock
    env = (1 - np.exp(-td / 0.003)) * \
        (0.5 + 0.5 * np.cos(np.pi * np.clip(td / dur, 0, 1)))
    y = np.tanh(0.9 * x * env) * weight
    bass_cache_eisgang[key] = y / (np.max(np.abs(y)) + 1e-12)
    return bass_cache_eisgang[key]


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


def sub_note(midi, dur=STEP * 0.88):
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * td) + 0.3 * np.sin(2 * np.pi * 2 * f * td)
    x *= (1 - np.exp(-td / 0.003)) * np.clip((dur - td) / 0.02, 0, 1)
    return x / (np.max(np.abs(x)) + 1e-12)


AUDITION = [
    ("bass_note 43", lambda: bass_note(43, 900.0)),
    ("bass_note_tide 43", lambda: bass_note_tide(43)),
    ("bass_hit 38", lambda: bass_hit(38)),
    ("thud_bass 40", lambda: thud_bass(40, 0.25)),
    ("psy_bass_note 38", lambda: psy_bass_note(38)),
    ("sub_note 33", lambda: sub_note(33)),
]

if __name__ == "__main__":
    run_audition("basses", AUDITION)
