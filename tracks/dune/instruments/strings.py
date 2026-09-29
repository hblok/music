"""Plucked/struck string instruments built on Karplus-Strong synthesis:
the oud (double-course, plucked), the baliset (triple-course, plucked --
Gurney Halleck's instrument, with a flageolet "harm" mode), and the santur
(struck hammered dulcimer, two strings per course).

Extracted from (canonical / most common version in each family):
  - `ks_string()`     <- `generate_gurneys_song.py` / `generate_muaddib.py`
    / `generate_sihaya.py` (identical: a vectorized-per-period
    Karplus-Strong string with a `taps`-point smoothing on the initial
    noise burst -- the shared low-level string primitive).
  - `oud_note()`      <- `generate_fall_of_arrakeen.py` / `generate_muaddib.py`
    / `generate_sihaya.py` (identical recipe: an unvectorized
    sample-by-sample double-course Karplus-Strong loop, band-passed
    200-4200 Hz. Reimplemented here as `ks_string()` calls for speed --
    numerically equivalent damping/detune, same audible result -- see
    the module CLAUDE.md note on the "vectorized oud" refactor).
  - `baliset_note()`  <- `generate_gurneys_song.py` (the fullest version,
    with a `kind="harm"` flageolet/octave-harmonic mode used for the
    baliset's bright overtone hits); `generate_muaddib.py` /
    `generate_sihaya.py` match the `kind="pluck"` (default) path exactly,
    just without the `kind=` parameter (their own `baliset_note()` never
    plays the harmonic).
  - `strum()` / `pluck()` <- `generate_gurneys_song.py` /
    `generate_muaddib.py` / `generate_sihaya.py` (near-identical:
    schedule a chord's notes with a small stagger; `pluck()` here is
    exposed as `render_pluck()` returning an audio array + pan angle,
    since the source scripts' `pluck()` writes directly into module-level
    mix-bus globals, which this library does not have).
  - `santur_note()`   <- `generate_spice_must_flow.py`: struck (not
    plucked) two-string-per-course Karplus-Strong with a hammer-shaped
    (2-point smoothed) excitation and a fast overall decay.

See ../CLAUDE.md and README.md for the full design notes and variant
table.
"""
from __future__ import annotations

import numpy as np
from scipy import signal

from _common import SR, midi_to_hz, norm, out_arg, write_wav

rng = np.random.default_rng(1965)

_oud_cache: dict = {}
_bal_cache: dict = {}


def ks_string(f, dur, damp, taps=3):
    """One Karplus-Strong string at frequency `f`, vectorized per period:
    a smoothed noise burst circulates through a leaky averaging filter
    (`damp` close to 1.0 = long sustain)."""
    period = max(2, int(SR / f))
    n = int(dur * SR)
    buf = rng.uniform(-1, 1, period)
    buf = np.convolve(buf, np.ones(taps) / taps, mode="same")
    out = np.empty(((n // period) + 2) * period)
    for p in range(len(out) // period):
        out[p * period:(p + 1) * period] = buf
        buf = damp * 0.5 * (buf + np.roll(buf, 1))
    return out[:n]


def oud_note(m, dur=0.55):
    """Double-course Karplus-Strong oud: two detuned strings (+0.4%),
    band-passed 200-4200 Hz, fast (40 ms) release."""
    key = (m, round(dur, 3))
    if key in _oud_cache:
        return _oud_cache[key]
    f = midi_to_hz(m)
    n = int(dur * SR)
    out = np.zeros(n)
    for det in (1.0, 1.004):
        out += ks_string(f * det, dur, 0.9985)
    sos_o = signal.butter(2, [200, 4200], "bandpass", fs=SR, output="sos")
    out = signal.sosfilt(sos_o, out)
    out *= np.clip((dur - np.arange(n) / SR) / 0.04, 0, 1)
    out = norm(out)
    _oud_cache[key] = out
    return out


def baliset_note(m, dur=2.5, kind="pluck"):
    """Triple-course Karplus-Strong baliset: three detuned strings
    (-0.25%, 0, +0.35%), band-passed 90-5200 Hz, 80 ms release.
    `kind="harm"` plays the flageolet/octave-harmonic instead: the
    fundamental doubled, only two detuned strings, a tighter 200-3000 Hz
    band and faster damping -- the baliset's bright overtone-only hit."""
    dur = float(np.clip(dur, 1.2, 8.0))
    key = (m, round(dur * 2) / 2, kind)
    if key in _bal_cache:
        return _bal_cache[key]
    dur = key[1]
    f = midi_to_hz(m)
    if kind == "harm":
        f, dets, gains = f * 2, (1.0, 1.0035), (1.0, 0.5)
        damp, band = 0.990, (200, 3000)
    else:
        dets, gains = (0.9975, 1.0, 1.0035), (0.55, 1.0, 0.7)
        damp, band = 0.9955, (90, 5200)
    n = int(dur * SR)
    out = np.zeros(n)
    for det, g in zip(dets, gains):
        out += g * ks_string(f * det, dur, damp)
    sos = signal.butter(2, band, "bandpass", fs=SR, output="sos")
    out = signal.sosfilt(sos, out)
    out *= np.clip((dur - np.arange(n) / SR) / 0.08, 0, 1)
    out = norm(out)
    _bal_cache[key] = out
    return out


def render_pluck(m, gain, dur=2.0, pan_lo_midi=38, pan_span=30.0):
    """Render one baliset pluck and its stereo pan angle (a fixed
    per-pitch pan the source scripts use: low notes left, high notes
    right, `pan_lo_midi`/`pan_span` matching `generate_muaddib.py`'s
    `pluck()`). Returns `(mono_array, pan_theta_radians)` -- multiply by
    `cos(theta)`/`sin(theta)` and place with `add_at()` into your own L/R
    buffers, since this library has no mix-bus globals."""
    note = baliset_note(m, dur)
    p = -0.2 + 0.4 * np.clip((m - pan_lo_midi) / pan_span, 0, 1)
    theta = (0.5 + p * 0.5) * np.pi / 2
    return note * gain, theta


def strum_times(chord, t0, up=False, stag_lo=0.012, stag_hi=0.025):
    """Schedule times for a strummed chord: returns `[(midi, t), ...]`
    with a small random per-note stagger (matches `strum()` in
    gurneys_song / muaddib / sihaya, which calls `pluck()` at these times
    directly into a mix bus -- here you get the schedule back to place
    yourself with `render_pluck()`)."""
    order = list(reversed(chord[-3:])) if up else chord
    stag = rng.uniform(stag_lo, stag_hi)
    return [(m, t0 + i * stag) for i, m in enumerate(order)]


def santur_note(f_or_midi, dur=2.0):
    """Struck (hammered) santur note: two Karplus-Strong strings per
    course at +-0.15% detune, a 2-point-smoothed (hammer-shaped, not
    pick-shaped) excitation, fast 1.6 Np/s overall decay plus a 100 ms
    release. Accepts a frequency in Hz directly (matching the source
    script, which is called with pre-converted frequencies) -- pass
    `midi_to_hz(m)` if you have a MIDI number."""
    f = f_or_midi
    n = int(dur * SR)
    out = np.zeros(n)
    for det, g in [(0.9985, 1.0), (1.0015, 0.85)]:
        period = max(2, int(round(SR / (f * det))))
        buf = rng.standard_normal(period)
        buf = np.convolve(buf, np.ones(2) / 2, mode="same")
        nper = n // period + 1
        s = np.empty(nper * period)
        prev = buf
        for k in range(nper):
            s[k * period:(k + 1) * period] = prev
            prev = 0.997 * 0.5 * (prev + np.roll(prev, 1))
        out += g * s[:n]
    tt = np.arange(n) / SR
    out *= np.exp(-tt * 1.6) * np.clip((dur - tt) / 0.1, 0, 1)
    return norm(out)


if __name__ == "__main__":
    out = out_arg("strings")
    from _common import concat

    oud_line = concat([oud_note(m) for m in (45, 48, 52, 45)], gap=0.05)
    bal_line = concat([baliset_note(m) for m in (45, 49, 52)], gap=0.1)
    bal_harm = baliset_note(45, kind="harm")
    santur_line = concat([santur_note(midi_to_hz(m)) for m in (57, 60, 64)], gap=0.1)
    demo = concat([oud_line, bal_line, bal_harm, santur_line], gap=0.3)
    write_wav(out, demo)

    chord = [40, 45, 49, 52]
    n = int(3.5 * SR)
    buf_l, buf_r = np.zeros(n), np.zeros(n)
    from _common import add_at
    for m, t in strum_times(chord, 0.2):
        clip, theta = render_pluck(m, 0.9)
        add_at(buf_l, clip, t, np.cos(theta))
        add_at(buf_r, clip, t, np.sin(theta))

    for x in (oud_line, bal_line, bal_harm, santur_line):
        assert np.max(np.abs(x)) <= 1.0 + 1e-6
        assert np.isfinite(x).all()
    # buf_l/buf_r sum several overlapping plucks without renormalizing --
    # matches the source scripts' mix-bus layers, which stay unnormalized
    # until the track's own final commit/gain stage; just check finiteness.
    for x in (buf_l, buf_r):
        assert np.isfinite(x).all()
    print("strings.py: peak/finite OK; oud / baliset / harm / santur / strum rendered")
