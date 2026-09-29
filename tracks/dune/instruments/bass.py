"""Gated sub/bass notes -- the plain two-harmonic saturated bass used under
the trance-side dune tracks, plus the rolling filtered psy-bass engine used
under the psytrance-side tracks (kwisatz_haderach, fall_of_arrakeen,
sleeper_awakens, the_navigator, jihad).

Extracted from (canonical / most common version in each family):
  - `bass_note()`     <- `generate_kanly.py` / `generate_maker_comes.py` /
    `generate_night_pursuit.py` (identical: fundamental + 0.35x 2nd
    harmonic, tanh(1.6x) drive, fast attack/short release gate).
    `generate_muaddib.py` / `generate_sihaya.py` carry a `BASS_CACHE`
    memoizer and a 2nd harmonic written as `sin(4*pi*f*t)` -- numerically
    the same signal, just phase-locked instead of offset; not exposed as
    a separate variant since the audible result matches.
    `generate_spice_agony.py` is a materially different, brighter/darker
    variant (up to 16 harmonics into a driven low-pass, plus a clean sub
    layer) -- kept as `bass_note_agony()`.
    `generate_stillsuit.py` matches the canonical version (parameter named
    `dur_s` instead of `dur`; identical body) -- not split out.
  - `psy_bass_note()` <- `generate_fall_of_arrakeen.py` /
    `generate_kwisatz_haderach.py` / `generate_sleeper_awakens.py` /
    `generate_the_navigator.py` (identical: up to 20 harmonics into a
    350 Hz low-pass, tanh(2.0x) drive, very fast attack/release -- the
    "rolling psy sub" that carries the whole low end in 4-on-the-floor
    sections). `jihad.py` builds the same sound via an explicit running
    phase accumulator instead of `2*pi*f*t` (matters only if you were to
    frequency-modulate mid-note, which none of the tracks do) -- not
    exposed as a separate function, just noted here.

See ../CLAUDE.md and README.md for the full design notes and variant
table.
"""
from __future__ import annotations

import numpy as np
from scipy import signal

from _common import SR, gate, midi_to_hz, norm, out_arg, write_wav

rng = np.random.default_rng(543)   # kanly/maker_comes/night_pursuit family seed


def bass_note(midi, dur):
    """Canonical gated bass: fundamental + 0.35x second harmonic, driven
    through tanh(1.6x), fast attack (5 ms) and a short release ramp over
    the last 50 ms of `dur`. Matches kanly / maker_comes / night_pursuit /
    muaddib / sihaya / stillsuit (all bit-for-bit equivalent modulo the
    cosmetic differences noted in the module docstring)."""
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * td) + 0.35 * np.sin(2 * np.pi * 2 * f * td + 0.3)
    x = np.tanh(1.6 * x)
    env = (1 - np.exp(-td / 0.005)) * gate(td, dur, release=0.05)
    return norm(x * env)


def bass_note_agony(midi, dur):
    """`generate_spice_agony.py`'s bass: up to 16 harmonics summed 1/k,
    driven at 2.2x through a 240 Hz low-pass for a dark, fuzzy body, with
    a clean sub sine layer added back on top so the fundamental stays
    audible on small speakers. Faster attack (4 ms) than the canonical
    bass_note()."""
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    for k in range(1, min(16, int(3000 / f)) + 1):
        x += np.sin(2 * np.pi * k * f * td) / k
    sos = signal.butter(2, 240, "low", fs=SR, output="sos")
    x = np.tanh(2.2 * signal.sosfilt(sos, x))
    x += 0.5 * np.sin(2 * np.pi * f * td)
    env = (1 - np.exp(-td / 0.004)) * gate(td, dur, release=0.05)
    x *= env
    return norm(x)


def psy_bass_note(midi, dur):
    """The rolling psy-trance sub: up to 20 harmonics (1/k) into a 350 Hz
    low-pass, tanh(2.0x) drive, very fast 2 ms attack and 20 ms release --
    the note that carries a whole psy-bass 4-on-the-floor section. Matches
    fall_of_arrakeen / kwisatz_haderach / sleeper_awakens / the_navigator /
    jihad (jihad computes the same phase via a running accumulator instead
    of `2*pi*f*t`; identical output for a fixed-pitch note)."""
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    for k in range(1, min(20, int(7000 / f)) + 1):
        x += np.sin(2 * np.pi * k * f * td) / k
    sos = signal.butter(2, 350, "low", fs=SR, output="sos")
    x = np.tanh(2.0 * signal.sosfilt(sos, x))
    env = (1 - np.exp(-td / 0.002)) * gate(td, dur, release=0.02)
    x *= env
    return norm(x)


if __name__ == "__main__":
    out = out_arg("bass")
    from _common import STEP, concat

    step = STEP if STEP > 0 else 0.117
    notes = [40, 40, 43, 45]  # E1 E1 G1 A1 -ish walking line
    canonical = concat([bass_note(m, step * 3.6) for m in notes], gap=0.02)
    agony = concat([bass_note_agony(m, step * 3.6) for m in notes], gap=0.02)
    psy = concat([psy_bass_note(m, step * 3.6) for m in notes], gap=0.02)
    demo = concat([canonical, agony, psy], gap=0.15)
    write_wav(out, demo)
    for x in (canonical, agony, psy):
        assert np.max(np.abs(x)) <= 1.0 + 1e-9
        assert np.isfinite(x).all()
    print("bass.py: peak/finite OK; canonical / agony / psy bass lines rendered")
