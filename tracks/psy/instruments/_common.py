"""Shared helpers for tracks/psy/instruments.

The ONE importable helper file in this directory.  The goa scripts
(`meridian.py`, `phototaxis.py`, `phototaxis_v2.py`) predate this library and
follow the "copy, don't import" convention of `../CLAUDE.md`; **this
directory does not change that and no track script was edited to build it.**
Every voice in the sibling modules was lifted *verbatim* from the named
`script:function`.  The DSP primitives that all three scripts share
byte-for-byte (`pm_core`, `rc_attack`, `lowpass`, `highpass`, `slow_noise`,
`make_reverb_ir`) live here once instead of in every module.

Import convention (same as tracks/trance, tracks/dune, tracks/ebm): flat,
script-dir on sys.path::

    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).parent / "instruments"))
    from leads import gurgle_note_v2
    from drums import goa_kick

Contract: an instrument returns ONE event as a mono float array, 44100 Hz,
peak ~1.0.  Pads (`pad_bed`, `underglow_chord`) and the FX (`chatter_burst`,
`bubble_rise`, `tape_flutter`, `harmonic_bloom`) return a stereo `(L, R)`
pair.  **Layer-writing originals converted:** in the scripts the four FX
functions write into a caller-supplied stereo `layer` pair at an absolute
time (`chatter_burst(layer, t0)` etc.); here they RETURN the event (plus its
length is `len(L)`), and the caller places it -- see each docstring for the
offset it must be placed at.

Tempo: `BPM` is phototaxis' 147 (meridian ran 145); functions reading
`BAR` (`bubble_rise`, `harmonic_bloom`) use it.  Determinism: every module
seeds its own module-level `np.random.default_rng(1995)`.
"""
from __future__ import annotations

import argparse
import pathlib
import wave

import numpy as np
from scipy import signal

SR = 44100
BPM = 147.0
BEAT = 60.0 / BPM
SIXT = BEAT / 4.0
BAR = 4.0 * BEAT
OUT_DIR = pathlib.Path(__file__).resolve().parent / "auditions"


def midi_to_hz(m):
    """Pitch from MIDI number. Identical in every goa script."""
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def add_at(buf, x, start_s, gain=1.0):
    """Bounds-safe event placement (same behaviour as the scripts' add_at)."""
    i0 = int(start_s * SR)
    end = min(len(buf), i0 + len(x))
    if end > i0:
        buf[i0:end] += x[: end - i0] * gain


def lowpass(x, hz, order=2):
    b, a = signal.butter(order, hz / (SR / 2), "low")
    return signal.lfilter(b, a, x)


def highpass(x, hz, order=2):
    b, a = signal.butter(order, hz / (SR / 2), "high")
    return signal.lfilter(b, a, x)


def rc_attack(n, seconds):
    """Raised-cosine 0→1 attack over `seconds`, then flat."""
    na = min(n, max(1, int(seconds * SR)))
    env = np.ones(n)
    env[:na] = 0.5 - 0.5 * np.cos(np.pi * np.arange(na) / na)
    return env


def pm_core(f0, n, ratio, idx, fb=0.0, pitch_env=None):
    td = np.arange(n) / SR
    if pitch_env is None:
        ph_c = 2 * np.pi * f0 * td
    else:
        ph_c = 2 * np.pi * np.cumsum(f0 * pitch_env) / SR
    ph_m = ratio * ph_c
    m = np.sin(ph_m)
    if fb:
        m = np.sin(ph_m + fb * m)
    return np.sin(ph_c + idx * m), ph_c


def slow_noise(n, rate_hz, seed):
    r = np.random.default_rng(seed)
    k = max(4, int(n / SR * rate_hz) + 2)
    pts = r.standard_normal(k)
    pts = np.convolve(pts, [0.25, 0.5, 0.25], mode="same")
    y = np.interp(np.arange(n), np.linspace(0, n - 1, k), pts)
    y -= y.min()
    if y.max() > 0:
        y /= y.max()
    return y


def make_reverb_ir(seconds, decay, seed):
    r = np.random.default_rng(seed)
    n = int(seconds * SR)
    ir = r.standard_normal(n) * np.exp(-np.arange(n) / SR / decay)
    b, a = signal.butter(2, 4000 / (SR / 2), "low")
    ir = signal.lfilter(b, a, ir)
    return ir / np.sqrt(np.sum(ir ** 2))


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
