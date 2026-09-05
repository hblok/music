"""Shared helpers for tracks/ebm/instruments.

The ONE importable file in this directory — a deliberate departure from
the copy-don't-import rule of tracks/dune and tracks/trance (agreed
2026-09-05): the instruments here are a reusable library, not standalone
tracks.  Keep it small: timing, pitch, sampler dirt, placement, WAV out.

Import convention: flat, script-dir-on-sys.path.  Running any module
directly works; a track script does
    sys.path.insert(0, str(pathlib.Path(__file__).parent / "instruments"))
and then `from sh101_bass import note`.

Contract of every instrument function: returns ONE event as a mono float
array, peak 1.0, at SR — the same thing make_kick()/bass_note() return in
the track scripts, so a track places clips with add_at() into its layer
buffers and commit()s the layer exactly as before.  The bus (weights,
pump, reverb, master) stays in the track script.  Cached functions
return shared arrays: never modify one in place.
"""
from __future__ import annotations

import argparse
import pathlib
import wave

import numpy as np
from scipy import signal

SR = 44100
BPM = 122.0                     # the Soli Deo Gloria "slam" archetype
BEAT = 60.0 / BPM
STEP = BEAT / 4                 # one 16th
BAR = 4 * BEAT
OUT_DIR = pathlib.Path("/workspace/music/ebm/instruments")
rng = np.random.default_rng(1993)


def midi_to_hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def norm(x):
    return x / (np.max(np.abs(x)) + 1e-12)


def dirt(x, hold=2, bits=13, lowpass=None):
    """Ensoniq-EPS flavour: zero-order-hold decimation (aliasing — the
    audible part; hold=2 ~ a 22 kHz sample, hold=3 ~ 15 kHz), 13-bit
    quantisation (mostly cosmetic), optional lowpass for a dull sample.
    hold=1 disables the decimation."""
    y = x
    if hold > 1:
        y = np.repeat(y[::hold], hold)[: len(x)]
    q = 2.0 ** (bits - 1)
    y = np.round(y * q) / q
    if lowpass:
        y = signal.sosfilt(signal.butter(2, lowpass, "low", fs=SR, output="sos"), y)
    return y


def gate(td, dur, release=0.004):
    """Hard sampler-style cut at `dur` seconds (released over `release`)."""
    return np.clip((dur - td) / release, 0.0, 1.0)


def bp_noise(n, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], "bandpass", fs=SR, output="sos")
    return norm(signal.sosfilt(sos, rng.standard_normal(n)))


def hp_noise(n, fc, order=4):
    sos = signal.butter(order, fc, "high", fs=SR, output="sos")
    return norm(signal.sosfilt(sos, rng.standard_normal(n)))


def steps_buffer(bars, tail=0.5):
    return np.zeros(int((bars * BAR + tail) * SR))


def _add(buf, x, i0, gain):
    if i0 >= len(buf):
        return
    n = min(len(x), len(buf) - i0)
    buf[i0:i0 + n] += gain * x[:n]


def add_at(buf, x, start_s, gain=1.0):
    """Add clip `x` at `start_s` seconds, bounds-safe — the track-script
    idiom (same signature as every generate_*.py), so instrument clips drop
    straight into a track's layer buffers ahead of its commit()."""
    _add(buf, x, int(start_s * SR), gain)


def place(buf, x, step, gain=1.0):
    """Add `x` at 16th-step `step` (float ok) on the BPM grid above."""
    _add(buf, x, int(round(step * STEP * SR)), gain)


def seed(n):
    """Reseed the shared noise rng (a track does this once, up top)."""
    global rng
    rng = np.random.default_rng(n)


def write_wav(path, x, peak=0.88):
    """Mono float array -> 16-bit mono WAV, peak-normalised."""
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    y = np.clip(norm(x) * peak, -1, 1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((y * 32767).astype(np.int16).tobytes())
    print(f"wrote {path}  ({len(x) / SR:.2f} s)")
    return path


def audition(name, hits, loop=None, gap=0.35, out=None):
    """Concatenate isolated `hits` (with gaps), then `loop`; write name.wav."""
    parts = []
    for h in hits:
        parts.append(h)
        parts.append(np.zeros(int(gap * SR)))
    if loop is not None:
        parts.append(np.zeros(int(0.5 * SR)))
        parts.append(loop)
    x = np.concatenate(parts)
    assert np.all(np.isfinite(x)), "NaN/inf in audition"
    return write_wav(out or OUT_DIR / f"{name}.wav", x)


def out_arg(name):
    ap = argparse.ArgumentParser(description=f"render the {name} audition")
    ap.add_argument("--out", default=str(OUT_DIR / f"{name}.wav"))
    return pathlib.Path(ap.parse_args().out)
