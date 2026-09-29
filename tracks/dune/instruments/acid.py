"""The TB-303-style acid line -- resonant, slide-capable saw lead used
across the psytrance-side dune tracks.

Extracted from (canonical / most common version in each family):
  - `acid_note()`  <- `generate_fall_of_arrakeen.py` /
    `generate_kwisatz_haderach.py` / `generate_sleeper_awakens.py` /
    `generate_the_navigator.py` (identical: up to 48 harmonics, a
    bright/dark dual low-pass blended by an accent-dependent sweep
    envelope, an `iirpeak` resonance bump, `tanh(2.8x)` drive, optional
    `slide_to` glide over the back 55% of the note -- the full "acid
    303" recipe). Accepts an explicit `dur`; when `None` it lands on
    `STEP * (1.02 if slide_to else 0.92)` at each track's own tempo (the
    caller passes an explicit `dur` here since this library has no
    module-level BPM).
  - `jihad.py` is a materially equivalent reimplementation (explicit
    phase accumulator, slightly different harmonic/cutoff constants) --
    kept as `acid_note_jihad()` since the tuning differences are audible
    (brighter accent, sharper resonance peak) even though the structure
    is identical.
  - `generate_water_of_life.py` is a simpler *non-sliding* variant (no
    `slide_to`, single low-pass + one resonance bump, softer 2.2x drive)
    -- kept as `acid_note_simple()`.

All three cache internally exactly as the source scripts do (an
`lru_cache`-style dict keyed on the same quantized-cutoff key), since the
tracks render the same acid step hundreds of times per song.

See ../CLAUDE.md and README.md for the full design notes and variant
table.
"""
from __future__ import annotations

import numpy as np
from scipy import signal

from _common import SR, gate, midi_to_hz, norm, out_arg, write_wav

_cache: dict = {}
_cache_jihad: dict = {}
_cache_simple: dict = {}


def _res_lp(x, c, sr, accent):
    c = float(min(c, 9000.0))
    sos_lp = signal.butter(2, c, "low", fs=SR, output="sos")
    y = signal.sosfilt(sos_lp, x)
    bpk, apk = signal.iirpeak(min(c, 8000.0), Q=11.0, fs=SR)
    return y + (1.9 if accent else 1.4) * signal.lfilter(bpk, apk, y)


def acid_note(m, cutoff, accent=False, slide_to=None, dur=0.117):
    """Canonical acid step (fall_of_arrakeen / kwisatz_haderach /
    sleeper_awakens / the_navigator). `cutoff` in Hz (pre-accent scaling
    is applied internally, +50% when `accent=True`); `slide_to` (a MIDI
    number or None) glides the pitch over the back half of the note for
    a 303-style tie-slide."""
    cutoff = float(np.clip(cutoff * (1.5 if accent else 1.0), 200, 7500))
    key = (m, int(cutoff // 60), accent, slide_to, round(dur, 4))
    if key in _cache:
        return _cache[key]
    f = midi_to_hz(m)
    n = int(dur * SR)
    td = np.arange(n) / SR
    if slide_to is None:
        ph = 2 * np.pi * f * td
        f_max = f
    else:
        f2 = midi_to_hz(slide_to)
        fc = f * (f2 / f) ** np.clip((td - 0.45 * dur) / (0.55 * dur), 0, 1)
        ph = 2 * np.pi * np.cumsum(fc) / SR
        f_max = min(f, f2)
    x = np.zeros(n)
    for k in range(1, min(48, int(10500 / f_max)) + 1):
        x += np.sin(k * ph) / k
    bright = _res_lp(x, cutoff * 3.0, SR, accent)
    dark = _res_lp(x, cutoff * 0.75, SR, accent)
    sweep = np.exp(-td / (0.10 if accent else 0.055))
    y = np.tanh(2.8 * (sweep * bright + (1 - sweep) * dark))
    env = (1 - np.exp(-td / 0.0015)) * gate(td, dur, release=0.02)
    y = norm(y * env)
    _cache[key] = y
    return y


def acid_note_jihad(m, cutoff, accent=False, slide_to=None, dur=0.122):
    """`jihad.py`'s acid step: same structure as `acid_note()` but its own
    constants (brighter bright-cutoff multiplier 2.4-3.2x, sharper
    resonance peak, 18-partial saw) -- gives Jihad's acid line a harder,
    more clipped edge than the other tracks' shared variant."""
    key = (m, int(cutoff // 60), int(accent), slide_to, round(dur, 4))
    if key in _cache_jihad:
        return _cache_jihad[key]
    n = int(dur * SR)
    tt = np.arange(n) / SR
    f0 = midi_to_hz(m)
    f = np.full(n, f0)
    if slide_to is not None:
        f2 = midi_to_hz(slide_to)
        q = np.clip((tt - dur * 0.45) / (dur * 0.45), 0, 1)
        f = f * (f2 / f0) ** q
    phase = 2 * np.pi * np.cumsum(f) / SR
    saw = np.zeros(n)
    for k in range(1, 45):
        if k * f0 < 9000:
            saw += np.sin(k * phase) / k
    bright_c = min(12000, cutoff * (3.2 if accent else 2.4))
    dark_c = max(90, cutoff * 0.72)
    bright = signal.sosfilt(signal.butter(2, bright_c, "low", fs=SR, output="sos"), saw)
    dark = signal.sosfilt(signal.butter(2, dark_c, "low", fs=SR, output="sos"), saw)
    qenv = np.exp(-tt / (0.10 if accent else 0.055))
    x = qenv * bright + (1 - qenv) * dark
    bpk, apk = signal.iirpeak(min(8000, cutoff * (1.8 if accent else 1.25)), 11, fs=SR)
    peak = signal.lfilter(bpk, apk, x)
    env = gate(tt, dur, release=0.018) * np.clip(tt / 0.002, 0, 1)
    x = np.tanh(2.8 * (x + (1.9 if accent else 1.4) * peak)) * env
    x = norm(x)
    _cache_jihad[key] = x
    return x


def acid_note_simple(m, cutoff, accent=False, dur=0.117):
    """`generate_water_of_life.py`'s simpler acid step: one low-pass +
    one resonance bump (no bright/dark blend), softer 2.2x drive, no
    `slide_to` support -- a good default when you want an acid line
    without the extra CPU/complexity of the dual-filter blend."""
    cutoff = float(np.clip(cutoff * (1.6 if accent else 1.0), 160, 6000))
    key = (m, int(cutoff // 75), accent, round(dur, 4))
    if key in _cache_simple:
        return _cache_simple[key]
    f = midi_to_hz(m)
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    for k in range(1, min(30, int(8000 / f)) + 1):
        x += np.sin(2 * np.pi * k * f * td) / k
    sos_lp = signal.butter(2, cutoff, "low", fs=SR, output="sos")
    y = signal.sosfilt(sos_lp, x)
    bpk, apk = signal.iirpeak(cutoff, Q=7.0, fs=SR)
    y = y + (1.5 if accent else 1.1) * signal.lfilter(bpk, apk, y)
    y = np.tanh(2.2 * y)
    env = (1 - np.exp(-td / 0.003)) * gate(td, dur, release=0.03)
    y = norm(y * env)
    _cache_simple[key] = y
    return y


if __name__ == "__main__":
    out = out_arg("acid")
    from _common import concat

    step = 0.117
    line = [(45, 220, False, None), (45, 220, False, None),
            (48, 400, True, None), (45, 220, False, 43),
            (43, 900, True, None)]
    canon = concat([acid_note(m, c, a, s, dur=step * (1.02 if s else 0.92))
                    for m, c, a, s in line], gap=0.0)
    jih = concat([acid_note_jihad(m, c, a, s, dur=step * (1.05 if s else 0.95))
                  for m, c, a, s in line], gap=0.0)
    simp = concat([acid_note_simple(m, c, a, dur=step * 0.9)
                   for m, c, a, s in line], gap=0.0)
    demo = concat([canon, jih, simp], gap=0.15)
    write_wav(out, demo)
    for x in (canon, jih, simp):
        assert np.max(np.abs(x)) <= 1.0 + 1e-9
        assert np.isfinite(x).all()
    print("acid.py: peak/finite OK; canonical / jihad / simple acid lines rendered")
