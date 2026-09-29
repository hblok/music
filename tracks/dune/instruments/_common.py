"""Shared helpers for tracks/dune/instruments.

The ONE importable file in this directory. Every `generate_*.py` script in
`tracks/dune/` predates this library and follows the "copy, don't import"
convention documented in `../CLAUDE.md` (each track script is a standalone,
self-contained file with its own copies of these helpers) -- **this
directory does not change that**. None of the existing track scripts were
edited to build this library; every function below was extracted (copied
verbatim, or reconciled from near-identical duplicates) from the canonical
version of each instrument as it appears across the 20 dune generators, so
a *new* track can import a tested instrument instead of re-copying it by
hand. See `README.md` for the source-script table and the "same instrument,
which file" pointers for every entry.

Import convention (matches tracks/ebm/instruments): flat, script-dir on
sys.path.  Running any module directly works standalone; a track script
does

    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).parent / "instruments"))
    from darbuka import make_doum, make_tek

Contract of every instrument function here: returns ONE event as a mono
(or, for a few wide ambient beds, a stereo (L, R) pair) float array, peak
1.0, at SR -- the same thing every `make_*()` / `*_note()` helper returns
in the track scripts, so a track places clips with `add_at()` into its own
layer buffers and mixes/commits exactly as the generators already do. The
bus (weights, reverb, sidechain, master) stays in the track script; nothing
here is stereo-panned, reverbed or mastered except the few ambient bed
functions that say so explicitly in their docstring.

Determinism: every module seeds its own `rng = np.random.default_rng(...)`
at import time (the dune convention -- each generator seeds once, thematically:
1965, 10191, 1993...). Two calls to a cached function return the identical
array; two calls to an uncached noise-based one (e.g. `make_tek()`) differ,
exactly as in the original scripts -- render once, place many.
"""
from __future__ import annotations

import argparse
import pathlib
import wave

import numpy as np
from scipy import signal

SR = 44100
BPM = 128.0                      # a representative dune-track tempo; a
                                  # track sets its own and passes explicit
                                  # `dur`/`STEP` values into these functions
                                  # (none of them read a module-level tempo)
STEP = 60.0 / BPM / 4             # one 16th at the reference BPM, for demos
BEAT = 60.0 / BPM
BAR = 4 * BEAT
OUT_DIR = pathlib.Path("/workspace/music/tracks/dune/instruments/auditions")


def midi_to_hz(m):
    """Pitch from MIDI number. Identical in all 20+ dune generators."""
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def norm(x):
    """Peak-normalize to 1.0 (the `x / (np.max(np.abs(x)) + 1e-12)` idiom
    repeated at the end of nearly every instrument function in every
    generator -- extracted here once for the new modules to call, though
    each instrument still normalizes explicitly to keep the audition's
    'return peak 1.0' contract obvious at a glance)."""
    return x / (np.max(np.abs(x)) + 1e-12)


def add_at(buf, x, start_s, gain=1.0):
    """Bounds-safe event placement -- identical across every generator."""
    i0 = int(start_s * SR)
    end = min(len(buf), i0 + len(x))
    if end > i0:
        buf[i0:end] += x[: end - i0] * gain


def fade(x, fade_in=0.02, fade_out=0.05):
    """Raised-cosine fade in/out, used on final mixes and on audition
    concatenations in this library (the generators' `fade()` scaled to
    track length; here scaled to a demo clip)."""
    x = np.asarray(x, dtype=float).copy()
    ni, no = int(fade_in * SR), int(fade_out * SR)
    if ni > 0:
        x[:ni] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(ni) / ni)
    if no > 0:
        x[-no:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(no) / no)
    return x


def slow_noise(rng, duration, rate_hz, lo=0.0, hi=1.0):
    """Smooth random control signal: sparse normals at `rate_hz`
    points/second, lightly smoothed, `np.interp`'d to SR, min-max
    normalized -- the gust/weather/pan LFO used throughout the wind,
    drone and ambient-bed recipes. `rng` is passed explicitly (each
    generator uses its own seeded rng; this helper does not own one)."""
    n = int(duration * SR)
    t = np.arange(n) / SR
    k = max(4, int(duration * rate_hz))
    pts = rng.standard_normal(k)
    pts = np.convolve(pts, np.ones(3) / 3, mode="same")
    ctrl = np.interp(t, np.linspace(0, duration, k), pts)
    ctrl = (ctrl - ctrl.min()) / (ctrl.max() - ctrl.min() + 1e-12)
    return lo + (hi - lo) * ctrl


def make_reverb_ir(seconds, decay, seed):
    """Exponentially decaying noise burst, lowpassed at 4 kHz (dark tail)
    -- convolution reverb IR, identical across nearly every generator."""
    r = np.random.default_rng(seed)
    n = int(seconds * SR)
    ir = r.standard_normal(n) * np.exp(-np.arange(n) / SR / decay)
    sos = signal.butter(2, 4000, "low", fs=SR, output="sos")
    ir = signal.sosfilt(sos, ir)
    return ir / np.sqrt(np.sum(ir ** 2))


def reverb(x, ir, wet=0.5):
    """Convolve, tail renormalized to the dry peak, then wet/dry mix --
    identical across every generator."""
    tail = signal.fftconvolve(x, ir)[: len(x)]
    tail /= np.max(np.abs(tail)) + 1e-12
    tail *= np.max(np.abs(x)) + 1e-12
    return (1 - wet) * x + wet * tail


def glide_curve(notes, n, sr=SR, porta=0.09):
    """Portamento pitch curve: a per-note frequency target track smoothed
    by a one-pole filter (time constant `porta` seconds). `notes`:
    [(midi, dur_s), ...]. Used by every melodic wind/voice instrument
    (duduk, ney, sung voice, war horn) to glide between notes instead of
    stepping. Canonical version (fall_of_arrakeen / kwisatz_haderach /
    sleeper_awakens / water_of_life / jihad all match; sihaya/muaddib/
    maker_comes/the_navigator carry small local variants for their own
    voice -- see README)."""
    f_target = np.zeros(n)
    edge = 0.0
    for m, d in notes:
        a, b = int(edge * sr), min(n, int((edge + d) * sr))
        f_target[a:b] = midi_to_hz(m)
        edge += d
    i_end = min(n - 1, int(edge * sr))
    f_target[i_end:] = f_target[i_end - 1]
    alpha = 1.0 - np.exp(-1.0 / (porta * sr))
    return signal.lfilter([alpha], [1.0, -(1.0 - alpha)],
                          f_target, zi=[f_target[0] * (1 - alpha)])[0]


def gate(td, dur, release=0.02):
    """Hard release gate: 1.0 until `dur - release`, then a linear ramp to
    0 -- the 'hard-gated like a sequencer step' shape used by the gated
    bass and the acid/psy-bass engines."""
    return np.clip((dur - td) / release, 0, 1)


def write_wav(path, x_or_stereo, sr=SR, peak=0.85):
    """Write a mono array or an (L, R) tuple/stack to a 16-bit PCM WAV,
    peak-normalized to `peak`. Used by every module's __main__ audition."""
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(x_or_stereo, tuple):
        L, R = x_or_stereo
    else:
        L = R = np.asarray(x_or_stereo, dtype=float)
    L = np.asarray(L, dtype=float)
    R = np.asarray(R, dtype=float)
    pk = max(np.max(np.abs(L)), np.max(np.abs(R)), 1e-12)
    L, R = L / pk * peak, R / pk * peak
    pcm = np.empty((len(L), 2))
    pcm[:, 0], pcm[:, 1] = L, R
    pcm = (pcm * 32767.0).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())
    print(f"wrote {path}  ({len(L) / sr:.2f}s)")


def out_arg(default_name):
    """Standard `--out` CLI flag for a module's __main__ audition,
    matching tracks/ebm/instruments' `_common.out_arg`."""
    p = argparse.ArgumentParser()
    p.add_argument("--out", default=None)
    args = p.parse_args()
    return pathlib.Path(args.out) if args.out else OUT_DIR / f"{default_name}.wav"


def concat(clips, gap=0.0):
    """Concatenate a list of mono clips with `gap` seconds of silence
    between them -- used to build an audition sequence of several hits."""
    if gap <= 0:
        return np.concatenate(clips) if clips else np.zeros(1)
    silence = np.zeros(int(gap * SR))
    out = []
    for i, c in enumerate(clips):
        out.append(c)
        if i < len(clips) - 1:
            out.append(silence)
    return np.concatenate(out)
