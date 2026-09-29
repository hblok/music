"""Trance builds, washes and seam devices.

Extracted from the trance track scripts (which are unchanged):
  - `swell`     <- `adrift.py:swell`  -- 250-2400 Hz bandlimited swell, the
    era build partner of a snare roll (never white noise).
  - `roll_hits` <- `adrift.py:roll`   -- the 16th -> 32nd snare-roll *grid*.
  - `riser`     <- `lost_v6.py:riser` -- lost's own noise riser (banned by
    construction in the era-strict tracks).
  - `cloud`     <- `adrift.py:cloud`  -- OWNED by adrift: symmetric wash
    that passes by (sin^2 envelope), a non-riser.  Returns a stereo pair.
  - `shiver_stab` <- `maschinenherz.py:shiver_stab` -- OWNED by
    maschinenherz: additive-dissonance intro stab.
  - `cutoff_at` <- `penumbra.py:cutoff_at` -- the printable filter arc.

**Layer-writing functions converted.**  In the scripts `swell`, `riser`,
`cloud` and `roll` write straight into the global `lay_L`/`lay_R` layer
buffers at `bar_t(b)`.  Here they return an event instead (like every other
voice in this library): `swell(dur)`, `riser(dur)` return a mono array,
`cloud(dur)` a stereo `(L, R)` pair with the random pan sweep applied, and
`roll_hits(nbars, base)` returns `[(beat_offset, gain)]` for the caller to
place with a snare (`drums.make_snare`).  The DSP bodies are unchanged; only
the `n = ...` length source and the final `add_at` calls differ.  `bar_t` /
`place_pan` are arrangement glue and are not extracted.

Not extracted (arrangement glue, not voices): `silent_beat`, `tide_out`
(bar-number predicates on a track's own constants), `ice_crack`,
`ladder_bars`, `arp_bars` (`maschinenherz.py` sequencing loops over
`pluck`/`acid_note`/`bar_t`; the voices they call are in `plucks.py` /
`leads.py`).
"""
from __future__ import annotations

import numpy as np
from scipy import signal

from _common import BAR, SR, midi_to_hz, run_audition

rng = np.random.default_rng(1996)   # adrift's seed (the year the dream broke)

stab_cache = {}


def swell(dur):
    n = int(dur * SR)
    prog = np.arange(n) / n
    noise = rng.standard_normal(n)
    out = np.zeros(n)
    for k in range(5):
        c = 250 * (2400 / 250) ** (k / 4)
        win = np.clip(1 - np.abs(prog - np.log(c / 250) / np.log(2400 / 250)) * 4, 0, 1)
        out += signal.sosfilt(signal.butter(2, [c * 0.8, c * 1.25], "bandpass",
                                            fs=SR, output="sos"), noise) * win
    out *= prog ** 2
    out /= np.max(np.abs(out)) + 1e-12
    return out


def roll_hits(nbars, base):
    """Snare-roll grid over `nbars` bars: [(beat offset from start, gain)]."""
    hits = []
    for b in range(nbars):
        u = b / nbars
        div = 4 if u < 0.5 else (8 if u < 0.85 else 16)
        for s in range(div):
            g = base * (0.4 + 0.6 * u) * (0.7 + 0.3 * (s % 2))
            hits.append((b * 4.0 + s * 4.0 / div, g))
    return hits


def riser(dur):
    n = int(dur * SR)
    td = np.arange(n) / SR
    prog = td / dur
    noise = rng.standard_normal(n)
    out = np.zeros(n)
    for k in range(8):
        c = 350 * (6000 / 350) ** (k / 7)
        win = np.clip(1 - np.abs(prog - np.log(c / 350) / np.log(6000 / 350)) * 6, 0, 1)
        out += signal.sosfilt(signal.butter(2, [c * 0.85, c * 1.18], "bandpass", fs=SR, output="sos"), noise) * win
    out += 0.4 * np.sin(2 * np.pi * np.cumsum(midi_to_hz(50) * 2 ** (2 * prog)) / SR)
    out *= prog ** 2
    return out / (np.max(np.abs(out)) + 1e-12)


def cloud(nbars):
    n = int(nbars * BAR * SR)
    prog = np.arange(n) / n
    x = signal.sosfilt(signal.butter(2, [300, 1800], "bandpass", fs=SR, output="sos"),
                       rng.standard_normal(n))
    x *= np.sin(np.pi * prog) ** 2                   # symmetric: it passes by
    x /= np.max(np.abs(x)) + 1e-12
    p0, p1 = (0.3, 0.7) if rng.random() < 0.5 else (0.7, 0.3)
    pan = p0 + (p1 - p0) * prog
    return x * np.cos(pan * np.pi / 2), x * np.sin(pan * np.pi / 2)


def shiver_stab(midis):
    if midis in stab_cache:
        return stab_cache[midis]
    n = int(0.10 * SR)
    td = np.arange(n) / SR
    v = np.zeros(n)
    for m in midis:
        f = midi_to_hz(m)
        for k in range(1, min(14, int(5000 / f)) + 1):
            v += np.sin(2 * np.pi * k * f * td) / k ** 1.3
    v = signal.sosfilt(signal.butter(2, 1100, "low", fs=SR, output="sos"), v)
    v *= (1 - np.exp(-td / 0.002)) * np.clip((0.085 - td) / 0.025, 0, 1)
    stab_cache[midis] = v / (np.max(np.abs(v)) + 1e-12)
    return stab_cache[midis]


def cutoff_at(b, cut_bars, cut_hz):
    """Piecewise-linear filter arc: cutoff (Hz) at bar `b` for the
    breakpoints `cut_bars` -> `cut_hz` (penumbra's `CUT_BARS`/`CUT_HZ` were
    module globals; here they are arguments)."""
    return float(np.interp(b, cut_bars, cut_hz))


AUDITION = [
    ("swell 4s", lambda: swell(4.0)),
    ("riser 4s", lambda: riser(4.0)),
    ("cloud 2 bars", lambda: cloud(2)),
    ("shiver_stab octave", lambda: shiver_stab((38, 50))),
    ("shiver_stab tritone", lambda: shiver_stab((38, 44, 50))),
]

if __name__ == "__main__":
    hits = roll_hits(4, 1.0)
    assert len(hits) == 24
    assert cutoff_at(4, [0, 8], [300.0, 700.0]) == 500.0
    run_audition("textures", AUDITION)
