"""Flightpath (the Bumblebee track) voices: square-core buzz path, bass stab, chord stab, wedge, sub boom, run-lane event vocabulary.

Event tuples are `(midi_or_None, length_in_16ths, accent, slide_to)`.  Not extracted: `osc_bar` / `build_sentence` / `resolve_slides` (melody construction), `place_hammer` (writes the layer buffers; its voice is `buzz_path(((p, STEP*0.8),), cut, accent, timbre="B")`).

Extracted VERBATIM from the trance track scripts (which are unchanged):
  - `buzz_path` <- `flightpath.py:buzz_path` -- THE VOICE: the 303's OTHER waveform, square/pulse core (duty 0.30/0.25), reed formant, timbres A/B
  - `cell_timbre` <- `flightpath.py:cell_timbre` -- the RELAY: which timbre a cell uses
  - `bass_stab` <- `flightpath.py:bass_stab` -- offbeat 8th bass stab (no rolling bass)
  - `chord_stab` <- `flightpath.py:chord_stab` -- offbeat 8th chord stab, LP 900
  - `wedge` <- `flightpath.py:wedge` -- contrary-motion seam device; returns a stereo (down, up) pair
  - `make_sub_boom` <- `flightpath.py:make_sub_boom` -- per-kick sub layer; un-normalized
  - `hammer_ev` <- `flightpath.py:hammer_ev` -- run-lane event kind: 16 retriggers on one pitch
  - `chain_ev` <- `flightpath.py:chain_ev` -- event kind: slide chain
  - `trill_ev` <- `flightpath.py:trill_ev` -- event kind: trill
  - `swell_ev` <- `flightpath.py:swell_ev` -- event kind: rising swell figure
  - `transpose_ev` <- `flightpath.py:transpose_ev` -- transpose an event list

See ../CLAUDE.md and README.md for the sound-ownership / identity rules.
Seed 1900 = flightpath (the year of the Bumblebee).
"""
from __future__ import annotations

import numpy as np
from scipy import signal

from _common import BEAT, SR, midi_to_hz, run_audition

rng = np.random.default_rng(1900)


buzz_cache = {}


TIMBRE = {"A": (0.30, 2600.0, 1350.0), "B": (0.25, 1900.0, 1100.0)}


def buzz_path(segments, cutoff, accent=False, timbre="A"):
    duty, lid, formant = TIMBRE[timbre]
    key = (tuple((m, round(s, 4)) for m, s in segments),
           int(cutoff // 40), accent, timbre)
    if key in buzz_cache:
        return buzz_cache[key]
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
    a = 1.0 - np.exp(-1.0 / (0.030 * SR))
    f_path = signal.lfilter([a], [1, -(1 - a)], f_path,
                            zi=[(1 - a) * f_path[0]])[0]
    ph = 2 * np.pi * np.cumsum(f_path) / SR
    fmin = max(min(midi_to_hz(m) for m, _ in segments), 30.0)
    x = np.zeros(n)
    for k in range(1, min(40, int(9000 / fmin)) + 1):
        w = np.sin(np.pi * k * duty)              # the pulse spectrum
        if abs(w) < 1e-3:
            continue
        x += w * np.sin(k * ph) / k ** 1.25
    cutoff = float(np.clip(cutoff * (1.4 if accent else 1.0), 200, 5000))

    def reed(sig_in, c):
        c = float(np.clip(c, 180.0, lid))
        sos_lp = signal.butter(2, c, "low", fs=SR, output="sos")
        y = signal.sosfilt(sos_lp, sig_in)
        bpk, apk = signal.iirpeak(formant, Q=2.8, fs=SR)
        return y + 0.40 * signal.lfilter(bpk, apk, y)

    bright = reed(x, cutoff * 2.2)
    dark = reed(x, cutoff * 0.7)
    sweep = np.exp(-td / (0.09 if accent else 0.045))
    y = np.tanh(1.0 * (sweep * bright + (1 - sweep) * dark))
    y += 0.30 * np.sin(ph)
    env = (1 - np.exp(-td / 0.0015)) * np.clip((total - td) / 0.02, 0, 1)
    y *= env
    y /= np.max(np.abs(y)) + 1e-12
    buzz_cache[key] = y
    return y


def cell_timbre(step):
    return "A" if ((step // 8) // 4) % 2 == 0 else "B"


def bass_stab(midi, dur=BEAT * 0.42):
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    for k in range(1, min(16, int(3000 / f)) + 1):
        x += np.sin(2 * np.pi * k * f * td) / k ** 1.3
    sos_b = signal.butter(2, 420, "low", fs=SR, output="sos")
    x = np.tanh(0.9 * signal.sosfilt(sos_b, x))
    x += 0.5 * np.sin(2 * np.pi * f * td)
    env = (1 - np.exp(-td / 0.003)) * np.clip((dur - td) / 0.05, 0, 1)
    x *= env
    return x / (np.max(np.abs(x)) + 1e-12)


def chord_stab(chord, dur=0.16):
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    for m in chord:
        f = midi_to_hz(m)
        for k in range(1, min(14, int(5000 / f)) + 1):
            x += np.sin(2 * np.pi * k * f * td) / k ** 1.3
    sos_s = signal.butter(2, 900, "low", fs=SR, output="sos")
    x = np.tanh(0.9 * signal.sosfilt(sos_s, x))
    x *= (1 - np.exp(-td / 0.002)) * np.clip((dur - td) / 0.03, 0, 1)
    return x / (np.max(np.abs(x)) + 1e-12)


def wedge(dur, center=67, spread=4.0):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    u = tt / dur
    out = []
    for sgn in (+1.0, -1.0):
        f = midi_to_hz(center) * 2.0 ** (sgn * spread * u / 12.0)
        ph = 2 * np.pi * np.cumsum(f) / SR
        v = np.sin(ph) + 0.30 * np.sin(2 * ph) + 0.15 * np.sin(3 * ph)
        out.append(v)
    sos_w = signal.butter(2, 1400, "low", fs=SR, output="sos")
    env = u ** 2 * (1 - np.exp(-tt / 0.05))
    dn = signal.sosfilt(sos_w, out[1] * env)
    up = signal.sosfilt(sos_w, out[0] * env)
    peak = max(np.max(np.abs(dn)), np.max(np.abs(up)), 1e-12)
    return dn / peak, up / peak


# sub boom under every kick (big-room default; C2/F2/Bb1/G1 register)
def make_sub_boom(f):
    n = int(0.42 * SR)
    td = np.arange(n) / SR
    f_curve = f * (1.0 + 0.35 * np.exp(-td * 12.0))
    x = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    env = ((1 - np.exp(-td / 0.003)) * np.exp(-td * 1.2) *
           np.clip((0.42 - td) / 0.06, 0, 1))
    return x * env


# duel material: the hammer (one-pitch retrigger, pitch STATIONARY
# per bar — the anti-ladder assertion), the trill, the palindrome
# swell. The 303 hammers in timbre B; the stab voice answers.
def hammer_ev(p):
    return [(p, 1, 1 if i % 4 == 0 else 0, None) for i in range(16)]


def chain_ev(seq, accents=4):
    ev = [[q, 1, 1 if i % accents == 0 else 0, True] for i, q in
          enumerate(seq)]
    ev[-1][3] = None
    for i, e in enumerate(ev[:-1]):
        e[3] = ev[i + 1][0]
    return [tuple(e) for e in ev]


def trill_ev(p):
    return chain_ev([p + 1, p, p + 1, p - 1] * 4)


def swell_ev(p, launch=False):
    seq = [p, p + 1, p + 2, p + 3, p + 4, p + 3, p + 2, p + 1] * 2
    if launch:                                    # roll bar: beat 4 silent
        seq = seq[:12]
    return chain_ev(seq)


def transpose_ev(events, semis):
    return [(m + semis if m is not None else None, d, a,
             (sl + semis if isinstance(sl, int) else sl))
            for m, d, a, sl in events]


AUDITION = [
    ("buzz_path A", lambda: buzz_path(((48, 0.2),), 900.0)),
    ("buzz_path B slide", lambda: buzz_path(((48, 0.15), (49, 0.15), (52, 0.3)), 900.0, accent=True, timbre="B")),
    ("bass_stab 36", lambda: bass_stab(36)),
    ("chord_stab", lambda: chord_stab([48, 55, 60])),
    ("wedge 3s", lambda: wedge(3.0)),
    ("make_sub_boom 36 Hz", lambda: make_sub_boom(36.0)),
]

if __name__ == "__main__":
    run_audition("flightpath", AUDITION)
