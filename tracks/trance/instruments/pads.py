"""Trance pads, rompler strings, choir & cello.


Extracted VERBATIM from the trance track scripts (which are unchanged):
  - `pad_chord` <- `lost_v6.py:pad_chord` -- dark sine pad
  - `pad_chord_juno` <- `penumbra.py:pad_chord` -- Juno pad, OWNED by penumbra
  - `strings_line` <- `ungeschrieben.py:strings_line` -- rompler strings line, OWNED by ungeschrieben
  - `strings_chord` <- `ungeschrieben.py:strings_chord` -- rompler strings chord
  - `choir_voice` <- `adrift.py:choir_voice` -- breath choir, OWNED by adrift
  - `cello_line` <- `lost_v6.py:cello_line` -- solo bowed cello

See ../CLAUDE.md and README.md for the sound-ownership / identity rules.
Seed 130 = lost_v6.
"""
from __future__ import annotations

import numpy as np
from scipy import signal

from _common import BEAT, SR, midi_to_hz, run_audition

rng = np.random.default_rng(130)


def pad_chord(chord, dur, attack, release, lowpass, detune=0.0012):
    n = int(dur * SR)
    td = np.arange(n) / SR
    L = np.zeros(n)
    R = np.zeros(n)
    for m in chord:
        f = midi_to_hz(m)
        amp = 0.8 + 0.2 * np.sin(2 * np.pi * rng.uniform(0.02, 0.06) * td + rng.uniform(0, 6))
        for d, gL, gR in [(1 - detune, 1.0, 0.62), (1 + detune, 0.62, 1.0)]:
            ph = 2 * np.pi * f * d * td + rng.uniform(0, 6)
            v = (np.sin(ph) + 0.3 * np.sin(2 * ph) + 0.1 * np.sin(3 * ph)) * amp
            L += gL * v
            R += gR * v
    env = np.minimum(np.clip(td / attack, 0, 1) ** 1.3, np.clip((dur - td) / release, 0, 1))
    sos = signal.butter(2, lowpass, "low", fs=SR, output="sos")
    L = signal.sosfilt(sos, L * env)
    R = signal.sosfilt(sos, R * env)
    peak = max(np.max(np.abs(L)), np.max(np.abs(R)), 1e-12)
    return L / peak, R / peak


pad_cache = {}


def pad_chord_juno(voicing, dur, attack, lowpass):
    key = (voicing, round(dur, 1), attack, lowpass)
    if key in pad_cache:
        return pad_cache[key]
    n = int(dur * SR)
    td = np.arange(n) / SR
    L = np.zeros(n)
    R = np.zeros(n)
    for m in voicing:
        f = midi_to_hz(m)
        amp = 0.8 + 0.2 * np.sin(2 * np.pi * rng.uniform(0.02, 0.06) * td + rng.uniform(0, 6))
        for dd, gL, gR in [(1 - 0.0014, 1.0, 0.62), (1 + 0.0014, 0.62, 1.0)]:
            ph = 2 * np.pi * f * dd * td + rng.uniform(0, 6)
            v = (np.sin(ph) + 0.3 * np.sin(2 * ph) + 0.1 * np.sin(3 * ph)) * amp
            L += gL * v
            R += gR * v
    env = np.minimum(np.clip(td / attack, 0, 1) ** 1.3, np.clip((dur - td) / 2.0, 0, 1))
    sos = signal.butter(2, lowpass, "low", fs=SR, output="sos")
    L = signal.sosfilt(sos, L * env)
    R = signal.sosfilt(sos, R * env)
    peak = max(np.max(np.abs(L)), np.max(np.abs(R)), 1e-12)
    pad_cache[key] = (L / peak, R / peak)
    return pad_cache[key]


def glide_curve(notes, n, tau=0.04):
    f_target = np.zeros(n)
    edge = 0.0
    for m, d in notes:
        a, b = int(edge * SR), min(n, int((edge + d) * SR))
        f_target[a:b] = midi_to_hz(m)
        edge += d
    i_end = min(n - 1, int(edge * SR))
    f_target[i_end:] = f_target[i_end - 1]
    alpha = 1.0 - np.exp(-1.0 / (tau * SR))
    return signal.lfilter([alpha], [1.0, -(1.0 - alpha)],
                          f_target, zi=[f_target[0] * (1 - alpha)])[0]


def _string_voice(f_curve, n, det, flutter_phase):
    tt = np.arange(n) / SR
    flut = 1.0 + 0.05 * np.sin(2 * np.pi * 5.8 * tt + flutter_phase)
    ph = 2 * np.pi * np.cumsum(f_curve * det) / SR
    K = max(3, int(5500 / np.max(f_curve)))
    v = np.zeros(n)
    for k in range(1, K + 1):
        v += np.sin(k * ph) / k ** 1.3
    return v * flut


def strings_line(notes, lowpass=3400):
    total = sum(d for _, d in notes) * BEAT
    n = int((total + 2.5) * SR)
    tt = np.arange(n) / SR
    f = glide_curve([(m, d * BEAT) for m, d in notes], n, tau=0.04)
    L = np.zeros(n)
    R = np.zeros(n)
    for det, gL, gR, phs in [(0.9955, 1.0, 0.55, 0.0),
                             (1.0, 0.8, 0.8, 2.1),
                             (1.0045, 0.55, 1.0, 4.2)]:
        v = _string_voice(f, n, det, phs)
        L += gL * v
        R += gR * v
    bow = signal.sosfilt(signal.butter(2, [2000, 5000], "bandpass", fs=SR, output="sos"),
                         rng.standard_normal(n))
    bow /= np.max(np.abs(bow)) + 1e-12
    atk = 0.5 - 0.5 * np.cos(np.pi * np.clip(tt / 0.12, 0, 1))   # sampled attack
    env = np.minimum(atk, np.clip((total + 0.3 - tt) / 0.8, 0, 1))
    L = (L / (np.max(np.abs(L)) + 1e-12) + 0.10 * bow) * env
    R = (R / (np.max(np.abs(R)) + 1e-12) + 0.10 * bow) * env
    sos = signal.butter(2, lowpass, "low", fs=SR, output="sos")
    L = signal.sosfilt(sos, L)
    R = signal.sosfilt(sos, R)
    peak = max(np.max(np.abs(L)), np.max(np.abs(R)), 1e-12)
    return L / peak, R / peak


def strings_chord(midis, dur, lowpass=3000):
    n = int((dur + 1.2) * SR)
    tt = np.arange(n) / SR
    L = np.zeros(n)
    R = np.zeros(n)
    for m in midis:
        f = midi_to_hz(m) * np.ones(n)
        for det, gL, gR in [(0.9958, 1.0, 0.6), (1.0042, 0.6, 1.0)]:
            L += gL * _string_voice(f, n, det, rng.uniform(0, 6))
            R += gR * _string_voice(f, n, det, rng.uniform(0, 6))
    bow = signal.sosfilt(signal.butter(2, [2000, 5000], "bandpass", fs=SR, output="sos"),
                         rng.standard_normal(n))
    bow /= np.max(np.abs(bow)) + 1e-12
    atk = 0.5 - 0.5 * np.cos(np.pi * np.clip(tt / 0.15, 0, 1))
    env = np.minimum(atk, np.clip((dur + 0.5 - tt) / 0.9, 0, 1))
    L = (L / (np.max(np.abs(L)) + 1e-12) + 0.08 * bow) * env
    R = (R / (np.max(np.abs(R)) + 1e-12) + 0.08 * bow) * env
    sos = signal.butter(2, lowpass, "low", fs=SR, output="sos")
    L = signal.sosfilt(sos, L)
    R = signal.sosfilt(sos, R)
    peak = max(np.max(np.abs(L)), np.max(np.abs(R)), 1e-12)
    return L / peak, R / peak


F1_BA, F1_AA = signal.iirpeak(650, Q=5, fs=SR)


F2_BA, F2_AA = signal.iirpeak(1080, Q=5, fs=SR)


CHEST_SOS = signal.butter(2, 500, "low", fs=SR, output="sos")


BREATH_SOS = signal.butter(2, [1500, 4000], "bandpass", fs=SR, output="sos")


choir_cache = {}


def choir_voice(midi, dur, attack=0.8):
    key = (midi, round(dur, 2), attack)
    if key in choir_cache:
        return choir_cache[key]
    f = midi_to_hz(midi)
    n = int((dur + 1.4) * SR)
    td = np.arange(n) / SR
    src = np.zeros(n)
    for det in (0.996, 1.0, 1.004):
        drift = 1.0 + 0.04 * np.sin(2 * np.pi * rng.uniform(0.08, 0.14) * td
                                    + rng.uniform(0, 2 * np.pi))
        v = np.zeros(n)
        for k in range(1, min(18, int(4000 / f)) + 1):
            v += np.sin(2 * np.pi * k * f * det * td + rng.uniform(0, 6)) / k ** 1.4
        src += v * drift
    vowel = signal.lfilter(F1_BA, F1_AA, src) + 0.8 * signal.lfilter(F2_BA, F2_AA, src)
    vowel /= np.max(np.abs(vowel)) + 1e-12
    chest = signal.sosfilt(CHEST_SOS, src)
    chest /= np.max(np.abs(chest)) + 1e-12
    x = 0.5 * chest + 0.5 * vowel
    env = np.minimum(0.5 - 0.5 * np.cos(np.pi * np.clip(td / attack, 0, 1)),
                     np.clip((dur + 1.2 - td) / 1.2, 0, 1))
    breath = signal.sosfilt(BREATH_SOS, rng.standard_normal(n))
    breath /= np.max(np.abs(breath)) + 1e-12
    x = (x + 0.08 * breath) * env
    choir_cache[key] = x / (np.max(np.abs(x)) + 1e-12)
    return choir_cache[key]


def glide_curve_lost(notes, n, tau=0.05):
    f_target = np.zeros(n)
    edge = 0.0
    for m, d in notes:
        a, b = int(edge * SR), min(n, int((edge + d) * SR))
        f_target[a:b] = midi_to_hz(m)
        edge += d
    i_end = min(n - 1, int(edge * SR))
    f_target[i_end:] = midi_to_hz(notes[-1][0])
    alpha = 1.0 - np.exp(-1.0 / (tau * SR))
    return signal.lfilter([alpha], [1.0, -(1.0 - alpha)],
                          f_target, zi=[f_target[0] * (1 - alpha)])[0]


def cello_line(notes, lowpass=1900):
    total = sum(d for _, d in notes) * BEAT
    n = int((total + 0.8) * SR)
    td = np.arange(n) / SR
    f = glide_curve_lost([(m, d * BEAT) for m, d in notes], n, tau=0.05)
    vib = 1.0 + 0.005 * np.sin(2 * np.pi * 5.0 * td) * np.clip(td / 0.7, 0, 1)
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    out = np.zeros(n)
    for k in range(1, 13):
        out += np.sin(k * ph) / k
    bow = signal.sosfilt(signal.butter(2, [80, 2400], "bandpass", fs=SR, output="sos"),
                         rng.standard_normal(n))
    out = out / (np.max(np.abs(out)) + 1e-12) + 0.07 * bow
    env = np.minimum(np.clip(td / 0.25, 0, 1), np.clip((total + 0.1 - td) / 0.5, 0, 1))
    out = signal.sosfilt(signal.butter(2, lowpass, "low", fs=SR, output="sos"), out * env)
    return out / (np.max(np.abs(out)) + 1e-12)


AUDITION = [
    ("pad_chord", lambda: pad_chord([50, 57, 62], 4.0, 1.0, 1.5, 800.0)),
    ("pad_chord_juno", lambda: pad_chord_juno((50, 57, 62), 4.0, 1.0, 1200.0)),
    ("strings_line", lambda: strings_line([(67, BEAT * 0.5), (70, BEAT * 0.5), (74, BEAT), (72, BEAT * 1.5)])),
    ("strings_chord", lambda: strings_chord([50, 57, 62], 3.0)),
    ("choir_voice", lambda: choir_voice(62, 3.0)),
    ("cello_line", lambda: cello_line([(67, BEAT * 0.5), (70, BEAT * 0.5), (74, BEAT), (72, BEAT * 1.5)])),
]

if __name__ == "__main__":
    run_audition("pads", AUDITION)
