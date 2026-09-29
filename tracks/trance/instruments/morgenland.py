"""Morgenland (Maqam Hijaz 303-goes-east) voices not covered elsewhere: santur, legato acid path, sub boom, open-fifth pad, swell.

Skipped on purpose: `make_doum` / `make_tek` (the darbuka pair) are byte-identical in recipe to `tracks/dune/instruments/darbuka.py:make_doum/make_tek` at their default arguments -- import those instead.  `build_half` / `resolve_slides` / `place_events` are the melody-construction grammar (composition, not a voice).  Sanctioned one-track dune borrow: see ../CLAUDE.md (morgenland Q4 darbuka license).

Extracted VERBATIM from the trance track scripts (which are unchanged):
  - `santur_note` <- `morgenland_v3.py:santur_note` -- hammered santur, additive + hammer bounce -- DIFFERENT recipe from tracks/dune/instruments/strings.py:santur_note (Karplus-Strong)
  - `santur_trem` <- `morgenland_v3.py:santur_trem` -- tremolo roll = the santur's sustain
  - `acid_path` <- `morgenland_v3.py:acid_path` -- v3 LEGATO 303: a slide chain is ONE note along a pitch path (the silver_wire sharper 303 + sung vibrato)
  - `make_sub_boom` <- `morgenland_v3.py:make_sub_boom` -- per-kick sub layer; returns un-normalized (its own commit weight)
  - `swell` <- `morgenland_v3.py:swell` -- 250-2400 Hz single-band swell, t^2.5 (variant of textures.swell)
  - `pad_chord_open` <- `morgenland_v3.py:pad_chord` -- open-fifth pad, wider (det +-0.12 %, cross 0.40)

See ../CLAUDE.md and README.md for the sound-ownership / identity rules.
Seed 1001 = morgenland (C Phrygian dominant, Maqam Hijaz).
"""
from __future__ import annotations

import numpy as np
from scipy import signal

from _common import SR, STEP, midi_to_hz, run_audition

rng = np.random.default_rng(1001)


santur_cache = {}


def santur_note(m, dur=STEP * 0.92):
    key = (m, round(dur, 3))
    if key in santur_cache:
        return santur_cache[key]
    f = midi_to_hz(m)
    n = int((dur + 0.9) * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    B = 2.0e-4
    for det in (0.9994, 1.0006):
        for k in range(1, min(18, int(7500 / f)) + 1):
            fk = f * det * k * np.sqrt(1 + B * k * k)
            x += (np.sin(2 * np.pi * fk * td + rng.uniform(0, 6)) /
                  k ** 1.1) * np.exp(-td * (3.0 + 0.7 * k))
    x += 0.12 * np.sin(2 * np.pi * f * td) * np.exp(-td * 3.0)
    sos_th = signal.butter(2, [1800, 6000], "bandpass", fs=SR, output="sos")
    thunk = signal.sosfilt(sos_th, rng.standard_normal(n))
    thunk *= np.exp(-td * 220)
    x += 0.15 * thunk / (np.max(np.abs(thunk)) + 1e-12)
    # the hammer bounce: a second, softer strike 28 ms later
    nb = int(0.028 * SR)
    x[nb:] += 0.5 * x[: n - nb].copy()
    x *= (1 - np.exp(-td / 0.0012))
    sos_lp = signal.butter(2, 3600, "low", fs=SR, output="sos")
    x = np.tanh(0.8 * signal.sosfilt(sos_lp, x))
    x /= np.max(np.abs(x)) + 1e-12
    santur_cache[key] = x
    return x


def santur_trem(m, dur):
    """Tremolo roll — the santur's sustain."""
    n = int((dur + 0.9) * SR)
    out = np.zeros(n)
    hit = santur_note(m, STEP * 0.9)
    tt = 0.0
    while tt < dur:
        g = (0.65 + 0.35 * np.exp(-tt * 1.5)) * rng.uniform(0.85, 1.0)
        i0 = int(tt * SR)
        end = min(n, i0 + len(hit))
        out[i0:end] += hit[: end - i0] * g
        tt += 1.0 / 16.5 * rng.uniform(0.94, 1.06)
    return out / (np.max(np.abs(out)) + 1e-12)


acid_cache = {}


def acid_path(segments, cutoff, accent=False):
    """One 303 note through a pitch PATH. segments = ((midi, secs),
    ...); glides between segments are a one-pole smooth (~35 ms) —
    portamento, graces and mordents are bends of one note, never
    re-attacks. The sweep runs ONCE, at the attack."""
    key = (tuple((m, round(s, 3)) for m, s in segments),
           int(cutoff // 40), accent)
    if key in acid_cache:
        return acid_cache[key]
    total = sum(s for _, s in segments)
    n = int(total * SR)
    td = np.arange(n) / SR
    f_path = np.empty(n)
    tt = 0.0
    i1 = 0
    for m, s in segments:
        i0 = int(tt * SR)
        i1 = min(n, int((tt + s) * SR))
        f_path[i0:i1] = midi_to_hz(m)
        tt += s
    if i1 < n:
        f_path[i1:] = f_path[max(i1 - 1, 0)]
    a = 1.0 - np.exp(-1.0 / (0.035 * SR))
    f_path = signal.lfilter([a], [1, -(1 - a)], f_path,
                            zi=[(1 - a) * f_path[0]])[0]
    if total > 0.30:            # the sung vibrato, blooming late
        f_path = f_path * (1.0 + 0.006 * np.sin(2 * np.pi * 5.3 * td) *
                           np.clip((td - 0.35) / 0.4, 0, 1))
    ph = 2 * np.pi * np.cumsum(f_path) / SR
    fmin = max(min(midi_to_hz(m) for m, _ in segments), 30.0)
    x = np.zeros(n)
    for k in range(1, min(40, int(9000 / fmin)) + 1):
        x += np.sin(k * ph) / k ** 1.3
    cutoff = float(np.clip(cutoff * (1.5 if accent else 1.0), 200, 6500))

    def res_lp(sig_in, c):
        c = float(min(c, 8000.0))
        sos_lp = signal.butter(2, c, "low", fs=SR, output="sos")
        y = signal.sosfilt(sos_lp, sig_in)
        bpk, apk = signal.iirpeak(min(c, 7500.0), Q=6.0, fs=SR)
        return y + (1.35 if accent else 1.3) * signal.lfilter(bpk, apk, y)

    bright = res_lp(x, cutoff * 2.5)
    dark = res_lp(x, cutoff * 0.75)
    sweep = np.exp(-td / (0.10 if accent else 0.055))
    y = np.tanh(1.5 * (sweep * bright + (1 - sweep) * dark))
    y += 0.30 * np.sin(ph)
    env = (1 - np.exp(-td / 0.0015)) * np.clip((total - td) / 0.02, 0, 1)
    y *= env
    y /= np.max(np.abs(y)) + 1e-12
    acid_cache[key] = y
    return y


def make_sub_boom(f):
    n = int(0.40 * SR)                          # beat at 142 is 0.423 s
    td = np.arange(n) / SR
    f_curve = f * (1.0 + 0.35 * np.exp(-td * 12.0))
    x = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    env = ((1 - np.exp(-td / 0.003)) * np.exp(-td * 1.2) *
           np.clip((0.40 - td) / 0.06, 0, 1))
    return x * env


def swell(dur):
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = signal.sosfilt(signal.butter(2, [250, 2400], "bandpass",
                                     fs=SR, output="sos"),
                       rng.standard_normal(n))
    x *= (td / dur) ** 2.5
    return x / (np.max(np.abs(x)) + 1e-12)


def pad_chord_open(chord, dur, attack=0.35, release=1.0):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    L = np.zeros(n)
    R = np.zeros(n)
    for m in chord:
        f = midi_to_hz(m)
        amp = 0.8 + 0.2 * np.sin(2 * np.pi * rng.uniform(0.02, 0.06) * tt +
                                 rng.uniform(0, 6))
        for det, gL, gR in [(0.9988, 1.0, 0.40), (1.0012, 0.40, 1.0)]:
            ph = 2 * np.pi * f * det * tt + rng.uniform(0, 6)
            v = (np.sin(ph) + 0.30 * np.sin(2 * ph)) * amp
            L += gL * v
            R += gR * v
    env = np.minimum(np.clip(tt / attack, 0, 1) ** 1.5,
                     np.clip((dur - tt) / release, 0, 1))
    sos = signal.butter(2, 800, "low", fs=SR, output="sos")
    L = signal.sosfilt(sos, L * env)
    R = signal.sosfilt(sos, R * env)
    peak = max(np.max(np.abs(L)), np.max(np.abs(R)), 1e-12)
    return L / peak, R / peak


AUDITION = [
    ("santur_note 60", lambda: santur_note(60)),
    ("santur_trem 60 1s", lambda: santur_trem(60, 1.0)),
    ("acid_path plain", lambda: acid_path(((36, 0.2),), 900.0)),
    ("acid_path legato", lambda: acid_path(((36, 0.2), (37, 0.2), (40, 0.4)), 900.0, accent=True)),
    ("make_sub_boom 36 Hz", lambda: make_sub_boom(36.0)),
    ("swell 3s", lambda: swell(3.0)),
    ("pad_chord_open", lambda: pad_chord_open([36, 43, 48], 4.0)),
]

if __name__ == "__main__":
    run_audition("morgenland", AUDITION)
