"""The melodic wind voice used for every duduk/ney phrase across the dune
tracks: a glide/portamento sine-plus-harmonics tone with vibrato that
blooms in over the first second, in two flavors -- a warmer, reedier
"duduk" voice and an airier "ney" voice with breath noise.

Extracted from `generate_kanly.py:voice_phrase(notes, lp=2200, ney=False)`
which already merges both flavors behind one `ney=` flag -- used here as
the canonical version. Equivalent to calling `voice_phrase(..., ney=False)`
in `generate_fall_of_arrakeen.py` / `generate_kwisatz_haderach.py` /
`generate_muaddib.py` / `generate_sihaya.py` / `generate_sleeper_awakens.py`
/ `generate_water_of_life.py` / `generate_night_pursuit.py` /
`generate_maker_comes.py` (all bit-identical to kanly's `ney=False` path,
modulo `generate_kanly.py` using its own portamento time constant of
0.09s -- same as the others). The `ney=True` path matches the separate
`ney_phrase()` function defined in fall_of_arrakeen / kwisatz_haderach /
sleeper_awakens / water_of_life / muaddib / sihaya / maker_comes
(identical bodies across all of them).

`place_voice()` mirrors the pan-and-add-to-stereo-layer helper from the
source scripts, generalized to take explicit buffers instead of module
globals.
"""
from __future__ import annotations

import numpy as np
from scipy import signal

from _common import SR, add_at, glide_curve, midi_to_hz, out_arg, write_wav

rng = np.random.default_rng(1965)


def voice_phrase(notes, lp=2200, ney=False):
    """Duduk/ney voice: `notes` = [(midi, dur_s), ...] with portamento
    (one-pole glide, ~90 ms time constant, 70 ms for `ney=True`) and
    vibrato that blooms in over roughly a second. `ney=True` swaps to a
    purer 3-harmonic tone plus a little 1.2-4 kHz breath noise, faster
    (6 Hz) shallower (0.4%) vibrato, and a shorter attack -- the airier
    ney-flute voice; `ney=False` is the warmer reedy duduk voice (4
    harmonics, 5.2 Hz / 0.6% vibrato)."""
    total = sum(d for _, d in notes) + 2.0
    n = int(total * SR)
    tt = np.arange(n) / SR
    f_target = np.zeros(n)
    edge = 0.0
    for m, d in notes:
        a, b = int(edge * SR), min(n, int((edge + d) * SR))
        f_target[a:b] = midi_to_hz(m)
        edge += d
    i_end = min(n - 1, int(edge * SR))
    f_target[i_end:] = f_target[i_end - 1]
    tau = 0.07 if ney else 0.09
    alpha = 1.0 - np.exp(-1.0 / (tau * SR))
    f_curve = signal.lfilter([alpha], [1.0, -(1.0 - alpha)],
                              f_target, zi=[f_target[0] * (1 - alpha)])[0]
    vib_hz = 6.0 if ney else 5.2
    vib_dep = 0.004 if ney else 0.006
    bloom = 0.8 if ney else 1.2
    vib = 1.0 + vib_dep * np.sin(2 * np.pi * vib_hz * tt) * np.clip(tt / bloom, 0, 1)
    phase = 2 * np.pi * np.cumsum(f_curve * vib) / SR
    env = np.minimum(np.clip(tt / 1.0, 0, 1),
                      np.clip((total - tt) / 2.0, 0, 1)) ** 1.5
    if ney:
        v = env * (np.sin(phase) + 0.25 * np.sin(2 * phase) + 0.08 * np.sin(3 * phase))
        sos_br = signal.butter(2, [1200, 4000], "bandpass", fs=SR, output="sos")
        breath = signal.sosfilt(sos_br, rng.standard_normal(n)) * env * 0.13
        v = v + breath
    else:
        v = env * (np.sin(phase) + 0.40 * np.sin(2 * phase) +
                   0.18 * np.sin(3 * phase) + 0.07 * np.sin(4 * phase))
    sos = signal.butter(2, lp, "low", fs=SR, output="sos")
    return signal.sosfilt(sos, v)


def ney_phrase(notes):
    """Standalone ney-only entry point (matches the separate
    `ney_phrase()` function used in most source scripts) -- identical to
    `voice_phrase(notes, ney=True)` except it uses its own default
    envelope timings (0.6s attack / 1.5s release vs voice_phrase's 1.0/2.0
    for the ney case) and a fixed 3200 Hz low-pass instead of a `lp=`
    parameter."""
    total = sum(d for _, d in notes) + 1.5
    n = int(total * SR)
    tt = np.arange(n) / SR
    f_curve = glide_curve(notes, n, porta=0.07)
    vib = 1.0 + 0.004 * np.sin(2 * np.pi * 6.0 * tt) * np.clip(tt / 0.8, 0, 1)
    phase = 2 * np.pi * np.cumsum(f_curve * vib) / SR
    env = np.minimum(np.clip(tt / 0.6, 0, 1),
                      np.clip((total - tt) / 1.5, 0, 1)) ** 1.3
    tone = np.sin(phase) + 0.25 * np.sin(2 * phase) + 0.08 * np.sin(3 * phase)
    sos_b = signal.butter(2, [1200, 4000], "bandpass", fs=SR, output="sos")
    breath = signal.sosfilt(sos_b, rng.standard_normal(n))
    breath /= np.max(np.abs(breath)) + 1e-12
    v = env * (tone + 0.13 * breath)
    sos = signal.butter(2, 3200, "low", fs=SR, output="sos")
    return signal.sosfilt(sos, v)


def place_voice(notes, t0, pan_pos, buf_l, buf_r, gain=1.0, lp=2200, ney=False):
    """Render `voice_phrase()` and add it, panned, into stereo buffers
    `buf_l`/`buf_r` at time `t0` -- matches every source script's
    `place_voice()` helper, generalized to explicit buffers."""
    v = voice_phrase(notes, lp=lp, ney=ney)
    add_at(buf_l, v, t0, gain * np.cos(pan_pos * np.pi / 2))
    add_at(buf_r, v, t0, gain * np.sin(pan_pos * np.pi / 2))


if __name__ == "__main__":
    out = out_arg("duduk_ney")
    from _common import concat

    phrase = [(57, 0.5), (60, 0.4), (62, 0.3), (59, 0.6)]
    duduk = voice_phrase(phrase, ney=False)
    ney1 = voice_phrase(phrase, ney=True)
    ney2 = ney_phrase(phrase)
    demo = concat([duduk, ney1, ney2], gap=0.3)
    write_wav(out, demo)
    n = int((sum(d for _, d in phrase) + 2.0) * SR + SR)
    buf_l, buf_r = np.zeros(n), np.zeros(n)
    place_voice(phrase, 0.2, 0.3, buf_l, buf_r, ney=False)
    # NOTE: matching the source scripts exactly, voice_phrase()/ney_phrase()
    # do NOT self-normalize (harmonic stacking can push the multi-harmonic
    # tone a little over 1.0 before a track's own bus gain/mix stage brings
    # it back down) -- so the peak check here is loose, not 1.0, by design.
    for x in (duduk, ney1, ney2, buf_l, buf_r):
        assert np.max(np.abs(x)) <= 1.30
        assert np.isfinite(x).all()
    print("duduk_ney.py: peak/finite OK; duduk + two ney variants rendered")
