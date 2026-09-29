"""Shared helpers for tracks/trance/instruments.

The ONE importable helper file in this directory.  Every trance script
(`lost_v6.py`, `adrift.py`, `maschinenherz.py`, ...) predates this library
and follows the "copy, don't import" convention of `../CLAUDE.md`; **this
directory does not change that and no track script was edited to build it.**
Every instrument function in the sibling modules was lifted *verbatim* from
the named `script:function` (see each module docstring), together with the
module-level constants, filters and caches it needs, so a *new* track can
import a tested voice instead of re-copying it.

Import convention (same as tracks/dune and tracks/ebm): flat, script-dir on
sys.path::

    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).parent / "instruments"))
    from basses import bass_note
    from drums import make_kick, make_hat

Contract: an instrument returns ONE event as a mono float array (a few
return a stereo `(L, R)` pair -- said in their docstring), 44100 Hz, peak
~1.0.  The bus (weights, reverb, sidechain, master) stays in the track
script.

Tempo: the trance scripts each set their own BPM (130-145) and several
voices read `BEAT`/`STEP` for their default durations.  Those functions
were copied unchanged, so they read the *reference* tempo below (`BPM`).
Wherever a function takes `dur` explicitly, pass it; otherwise edit `BPM`
here (or copy the function) for a different grid.

Determinism: every module seeds its own module-level
`np.random.default_rng(<track seed>)` at import time, like the scripts.
"""
from __future__ import annotations

import argparse
import pathlib
import wave

import numpy as np

SR = 44100
BPM = 138.0                       # reference tempo (see module docstring)
BEAT = 60.0 / BPM
BAR = BEAT * 4
STEP = BEAT / 4                   # one 16th
OUT_DIR = pathlib.Path(__file__).resolve().parent / "auditions"


def midi_to_hz(m):
    """Pitch from MIDI number. Identical in every trance script."""
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def add_at(buf, x, start_s, gain=1.0):
    """Bounds-safe event placement. Identical in every trance script."""
    i0 = int(start_s * SR)
    end = min(len(buf), i0 + len(x))
    if end > i0:
        buf[i0:end] += x[: end - i0] * gain


def norm(x):
    """Peak-normalize to 1.0."""
    return x / (np.max(np.abs(x)) + 1e-12)


def as_pair(x):
    """Return (L, R) arrays for a mono array or an (L, R) tuple."""
    if isinstance(x, tuple):
        return np.asarray(x[0], dtype=float), np.asarray(x[1], dtype=float)
    x = np.asarray(x, dtype=float)
    return x, x


def write_wav(path, x, sr=SR, peak=0.85):
    """Write a mono array or an (L, R) tuple to a 16-bit stereo WAV."""
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    left, right = as_pair(x)
    pk = max(np.max(np.abs(left)), np.max(np.abs(right)), 1e-12)
    pcm = np.empty((len(left), 2))
    pcm[:, 0], pcm[:, 1] = left / pk * peak, right / pk * peak
    pcm = (pcm * 32767.0).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())
    print(f"wrote {path}  ({len(left) / sr:.2f}s)")


def run_audition(name, cases, gap=0.4, max_peak=1.5):
    """Standard `__main__` for an instrument module.

    `cases` is a list of `(label, zero-arg callable)`.  Each is rendered,
    asserted finite / non-silent / peak <= `max_peak`, and the results are
    concatenated with `gap` seconds of silence into
    `auditions/<name>.wav` (override with `--out`).
    """
    p = argparse.ArgumentParser()
    p.add_argument("--out", default=None)
    args = p.parse_args()
    out = pathlib.Path(args.out) if args.out else OUT_DIR / f"{name}.wav"
    lefts, rights = [], []
    silence = np.zeros(int(gap * SR))
    for label, fn in cases:
        left, right = as_pair(fn())
        for ch in (left, right):
            assert np.isfinite(ch).all(), f"{name}:{label} not finite"
        pk = max(np.max(np.abs(left)), np.max(np.abs(right)))
        assert 0.05 < pk <= max_peak, f"{name}:{label} peak {pk:.3f}"
        lefts += [left, silence]
        rights += [right, silence]
        print(f"  {label:28s} {len(left) / SR:6.2f}s  peak {pk:.2f}")
    write_wav(out, (np.concatenate(lefts), np.concatenate(rights)))
    print(f"{name}.py: finite / peak OK for {len(cases)} cases")
