"""The Sardaukar/Fremen throat-chant choir: a single glottal-harmonic
voice through dark vocal-tract formants (`chant_note`), stacked into a
detuned, jittered 12-voice mass choir (`mass_chant_note` / `mass_chant`).

Extracted from (canonical / most common version in each family):
  - `chant_note()` <- `generate_kwisatz_haderach.py` / `jihad.py`
    (identical: `scatter=` detune parameter, fast 25 ms attack / 80 ms
    release, a `pulse` tremolo, an explicit running-phase accumulator so
    `scatter` can retune the fundamental for the mass choir's per-voice
    detune). `generate_fall_of_arrakeen.py` / `generate_sleeper_awakens.py`
    / `generate_water_of_life.py` use an earlier single-voice-only
    version (no `scatter` arg, per-harmonic `rng.uniform` phase instead
    of a shared running phase) -- kept as `chant_note_simple()`.
    `generate_spice_agony.py` matches the simple version but with a
    slower 200 ms release and `pulse=5.0` default -- close enough to
    `chant_note_simple()` that it is not split out further (pass
    `release=0.20` if you need the exact spice_agony envelope).
    `generate_sihaya.py` / `generate_muaddib.py` have a *third* variant:
    the `scatter=` running-phase source of the canonical version, but
    NO pulse tremolo and NO bandpass-formant gain shaping beyond the
    three formant bands (i.e. `pulse` is not applied) -- kept as
    `chant_note_choir()` since it is the one actually used inside their
    `mass_chant()`.
  - `mass_chant_note()` <- `generate_kwisatz_haderach.py` / `jihad.py`
    (identical 12-voice detune+jitter+pan stack over `chant_note()`).
  - `mass_chant()` <- `generate_sihaya.py` (same recipe, named
    differently and built over `chant_note_choir()`; `generate_muaddib.py`
    is identical). Exposed here as `mass_chant()` calling
    `chant_note_choir()`, matching sihaya/muaddib; call
    `mass_chant_note()` if you want the kwisatz_haderach/jihad flavor
    (built over the tremolo `chant_note()`).

See ../CLAUDE.md and README.md for the full design notes and variant
table.
"""
from __future__ import annotations

import numpy as np
from scipy import signal

from _common import SR, midi_to_hz, norm, out_arg, write_wav

rng = np.random.default_rng(10191)

_FORMANTS = [(380, 560, 1.0), (750, 1000, 0.6), (2200, 2700, 0.15)]


def chant_note(midi, dur, pulse=5.5, scatter=1.0):
    """Canonical single-voice throat chant (kwisatz_haderach / jihad):
    15 glottal harmonics (1/k**0.8) through three dark bandpass formants,
    a tremolo pulse, a sub-octave reinforcement layer, fast attack (25 ms)
    / short release (80 ms). `scatter` detunes the fundamental (used by
    `mass_chant_note()` to build the choir's per-voice spread)."""
    n = int(dur * SR)
    td = np.arange(n) / SR
    f0 = midi_to_hz(midi) * scatter
    phase = 2 * np.pi * np.cumsum(np.full(n, f0)) / SR
    src = np.zeros(n)
    for k in range(1, 15):
        src += np.sin(k * phase) / k ** 0.8
    env = np.minimum(np.clip(td / 0.025, 0, 1), np.clip((dur - td) / 0.08, 0, 1))
    src *= env * (0.70 + 0.30 * np.sin(2 * np.pi * pulse * td))
    out = np.zeros(n)
    for lo, hi, g in _FORMANTS:
        sos = signal.butter(2, [lo, hi], "bandpass", fs=SR, output="sos")
        out += g * signal.sosfilt(sos, src)
    out += 0.40 * np.sin(phase * 0.5) * env
    return norm(out)


def chant_note_simple(midi, dur, pulse=5.5, release=0.15):
    """The earlier single-voice-only variant (fall_of_arrakeen /
    sleeper_awakens / water_of_life; spice_agony matches with
    `release=0.20`, `pulse=5.0`): per-harmonic independent random phase
    instead of a shared running phase (so `scatter`-style retuning isn't
    supported -- this one is not used inside the mass choir)."""
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    src = np.zeros(n)
    for k in range(1, 15):
        src += np.sin(2 * np.pi * k * f * td + rng.uniform(0, 2 * np.pi)) / k ** 0.8
    out = np.zeros(n)
    for (lo, hi), g in [((lo, hi), g) for lo, hi, g in _FORMANTS]:
        out += g * signal.sosfilt(signal.butter(2, [lo, hi], "bandpass",
                                                  fs=SR, output="sos"), src)
    out /= np.max(np.abs(out)) + 1e-12
    out *= 0.75 + 0.25 * np.sin(2 * np.pi * pulse * td)
    out += 0.40 * np.sin(2 * np.pi * 0.5 * f * td)
    env = np.minimum(np.clip(td / 0.06, 0, 1),
                      np.clip((dur - td) / release, 0, 1)) ** 1.2
    return norm(out * env)


def chant_note_choir(midi, dur, scatter=1.0):
    """The plain (no tremolo) chant voice used as the mass-choir building
    block in sihaya/muaddib's `mass_chant()`: same harmonic/formant recipe
    as `chant_note()` but a longer 300 ms release and no pulse
    modulation, since the choir's own detune+jitter stack supplies the
    movement."""
    n = int(dur * SR)
    td = np.arange(n) / SR
    f0 = midi_to_hz(midi) * scatter
    phase = 2 * np.pi * np.cumsum(np.full(n, f0)) / SR
    src = np.zeros(n)
    for k in range(1, 15):
        src += np.sin(k * phase) / k ** 0.8
    env = np.minimum(np.clip(td / 0.06, 0, 1), np.clip((dur - td) / 0.30, 0, 1))
    src *= env
    out = np.zeros(n)
    for lo, hi, g in _FORMANTS:
        sos = signal.butter(2, [lo, hi], "bandpass", fs=SR, output="sos")
        out += g * signal.sosfilt(sos, src)
    out += 0.40 * np.sin(phase * 0.5) * env
    return norm(out)


def _stack_voices(note_fn, midi, dur, voices):
    n = int((dur + 0.16) * SR)
    L = np.zeros(n)
    R = np.zeros(n)
    for v in range(voices):
        det = 1.0 + rng.uniform(-0.008, 0.008)
        jitter = int(rng.uniform(0.0, 0.12) * SR)
        body = note_fn(midi, dur, scatter=det)
        body = body * rng.uniform(0.82, 1.05)
        end = min(n, jitter + len(body))
        pan = (v + 0.5) / voices
        L[jitter:end] += body[: end - jitter] * np.cos(pan * np.pi / 2)
        R[jitter:end] += body[: end - jitter] * np.sin(pan * np.pi / 2)
    pk = max(np.max(np.abs(L)), np.max(np.abs(R))) + 1e-12
    return L / pk, R / pk


def mass_chant_note(midi, dur, voices=12):
    """The 12-voice Sietch-Tabr choir built over the tremolo `chant_note()`
    (kwisatz_haderach / jihad): detuned +-0.8%, time-jittered up to
    120 ms, panned evenly across the stereo field. Returns `(L, R)`."""
    return _stack_voices(chant_note, midi, dur, voices)


def mass_chant(midi, dur, voices=12):
    """The 12-voice choir built over the plain `chant_note_choir()`
    (sihaya / muaddib) -- same stacking recipe as `mass_chant_note()`,
    different base timbre. Returns `(L, R)`."""
    return _stack_voices(chant_note_choir, midi, dur, voices)


if __name__ == "__main__":
    out = out_arg("choir")
    from _common import concat

    solo = concat([chant_note(45, 1.0), chant_note_simple(45, 1.0),
                   chant_note_choir(45, 1.0)], gap=0.2)
    write_wav(out, solo)
    mass_l, mass_r = mass_chant_note(43, 2.0)
    mass2_l, mass2_r = mass_chant(43, 2.0)
    write_wav(out.parent / "choir_mass.wav", (mass_l, mass_r))
    write_wav(out.parent / "choir_mass_sihaya.wav", (mass2_l, mass2_r))
    for x in (solo, mass_l, mass_r, mass2_l, mass2_r):
        assert np.max(np.abs(x)) <= 1.0 + 1e-6
        assert np.isfinite(x).all()
    print("choir.py: peak/finite OK; solo + two mass-choir variants rendered")
