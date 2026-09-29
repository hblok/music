"""Shared helpers for tracks/ambient/instruments.

The ONE importable helper file in this directory.  `lost.py` and
`persian*.py` predate this library (`lost.py` is a top-level render script,
so importing it would render the whole track); **no track script was
edited to build it.**  `lost_ambient.py` holds voices lifted verbatim from
`lost.py` (and one effect from `../dune/generate_ambient.py`);
`persian.py` holds the parameter recipes of `persian.py` / `persian_opus.py`
as callable renderers over the forge instruments.

Import convention (same as the other instrument libraries): flat, script-dir
on sys.path::

    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).parent / "instruments"))
    from lost_ambient import piano, cello_line

Contract: mono float array unless a docstring says stereo `(L, R)` / `(N, 2)`;
44100 Hz; the audition asserts finite / non-silent / peak <= 1.5.
Determinism: each module seeds its own module-level
`np.random.default_rng(<seed>)`.
"""
from __future__ import annotations

import argparse
import pathlib
import wave

import numpy as np

SR = 44100
BPM = 96.0                        # the qasida / persian tempo (lost_ambient has none)
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
    """Return (L, R) arrays for a mono array, an (L, R) tuple or (N, 2)."""
    if isinstance(x, np.ndarray) and x.ndim == 2:
        return x[:, 0].astype(float), x[:, 1].astype(float)
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
