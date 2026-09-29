"""Transition/atmosphere FX shared across most dune tracks: the laser
"zap", the noise-band "riser" sweep, the reverse cymbal swell, and the
detuned "tremolo_strings" pad.

Extracted from (canonical / most common version in each family):
  - `zap()`             <- `generate_fall_of_arrakeen.py:make_zap`
    (identical in kwisatz_haderach / sleeper_awakens / the_navigator;
    `jihad.py` is a shorter/faster variant -- exposed here as
    `zap(fast=True)`).
  - `riser()`            <- `generate_fall_of_arrakeen.py:riser` (identical
    in kanly / kwisatz_haderach / maker_comes / muaddib / sihaya /
    sleeper_awakens / water_of_life / night_pursuit / the_navigator, the
    last two only differing by a defensive `min(..., SR/2-100)` band-edge
    clamp that changes nothing below 22 kHz-100 Hz; `jihad.py` builds the
    same shape from a linear-space sweep instead of geomspace bands with
    triangular windows -- exposed here as `riser(style="jihad")`).
  - `rev_cymbal()`       <- `generate_fall_of_arrakeen.py:rev_cymbal`
    (identical in kwisatz_haderach / the_navigator: exp(-t*6) decay before
    reversing; `jihad.py` decays faster, exp(-t*3.2) -- exposed as
    `rev_cymbal(decay=3.2)`).
  - `tremolo_strings()`  <- `generate_fall_of_arrakeen.py:tremolo_strings`
    (identical in kanly / kwisatz_haderach / maker_comes / muaddib /
    sihaya / sleeper_awakens / water_of_life / night_pursuit: 3-voice
    detuned additive saw through a tremolo LFO and a 180-2600 Hz
    bandpass; `jihad.py` builds the saw via an explicit sum-of-partials
    loop per detune voice instead of `rng.uniform` phase offsets --
    audibly the same texture, exposed as `tremolo_strings(style="jihad")`).

See ../CLAUDE.md and README.md for the full design notes and variant
table.
"""
from __future__ import annotations

import numpy as np
from scipy import signal

from _common import SR, midi_to_hz, norm, out_arg, write_wav

rng = np.random.default_rng(10191)


def zap(fast=False):
    """Laser/UI zap: a fast downward-curving pitch sweep (80 Hz <- ~2 kHz)
    ring-modulated by a 35 Hz wobble. `fast=True` gives jihad.py's
    shorter, harder-decaying variant (0.18s vs 0.40s, exp(-t*18) decay
    instead of exp(-t*8))."""
    if fast:
        n = int(0.18 * SR)
        tt = np.arange(n) / SR
        f = 80.0 + (1980.0 - 80.0) * np.exp(-tt * 28.0)
        x = np.sin(2 * np.pi * np.cumsum(f) / SR) * (1 + 0.35 * np.sin(2 * np.pi * 35 * tt))
        x *= np.exp(-tt * 18.0)
        return norm(x)
    n = int(0.40 * SR)
    td = np.arange(n) / SR
    f_curve = 80.0 + 1900.0 * np.exp(-td * 18.0)
    x = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    x *= 1.0 + 0.5 * np.sin(2 * np.pi * 35.0 * td)
    x *= np.exp(-td * 8.0) * (1 - np.exp(-td / 0.002))
    return norm(x)


def riser(dur=4.0, style="default"):
    """Build-up sweep: 10 noise bands sweeping 300 Hz -> 5.5 kHz with a
    parabolic amplitude curve, plus a 2-octave rising tone underneath.
    `style="jihad"` uses jihad.py's linear-sweep/triangle-window
    construction of the same idea -- both land on an audibly similar
    "riser" shape."""
    n = int(dur * SR)
    tt = np.arange(n) / SR
    if style == "jihad":
        white = rng.standard_normal(n)
        out = np.zeros(n)
        centers = np.geomspace(300, 5500, 10)
        x = np.linspace(0, 1, n)
        for i, c in enumerate(centers):
            sos = signal.butter(2, [max(60, c / 1.8), min(12000, c * 1.8)],
                                 "bandpass", fs=SR, output="sos")
            band = signal.sosfilt(sos, white)
            tri = np.maximum(0, 1 - np.abs(x - i / (len(centers) - 1)) * 2.8)
            out += band * tri
        f = 220 * 2 ** (2.0 * x)
        out += 0.35 * np.sin(2 * np.pi * np.cumsum(f) / SR)
        out *= x ** 2
        return norm(out)
    nz = rng.standard_normal(n)
    out = np.zeros(n)
    K = 10
    for k in range(K):
        c = 300.0 * (5500.0 / 300.0) ** (k / (K - 1))
        sos_r = signal.butter(2, [c * 0.7, min(c * 1.4, SR / 2 - 100)],
                               "bandpass", fs=SR, output="sos")
        band = signal.sosfilt(sos_r, nz)
        center = (k + 0.5) / K * dur
        w = np.clip(1 - np.abs(tt - center) / (dur / K * 1.6), 0, 1)
        out += band * w
    out = norm(out)
    f_curve = 70.0 * 2.0 ** (2.0 * tt / dur)
    tone = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    x = (out + 0.45 * tone) * (tt / dur) ** 2
    return norm(x)


def rev_cymbal(dur=1.6, decay=6.0):
    """Reverse cymbal swell: highpassed noise with an exponential decay,
    time-reversed so the "crash" lands right at the end of `dur`.
    `decay=6.0` matches fall_of_arrakeen/kwisatz_haderach/the_navigator;
    `decay=3.2` matches jihad.py's faster/shorter swell."""
    n = int(dur * SR)
    td = np.arange(n) / SR
    sos_c = signal.butter(4, 6000, "high", fs=SR, output="sos")
    x = signal.sosfilt(sos_c, rng.standard_normal(n)) * np.exp(-td * decay)
    x = x[::-1].copy()
    return norm(x)


def tremolo_strings(chord, dur, trem_hz=10.5, style="default"):
    """Detuned tremolo string pad: a 3-voice detuned additive tone per
    chord note (9 partials each), bandpassed 180-2600 Hz, amplitude
    tremolo'd at `trem_hz`, with a slow attack/release envelope.
    `chord`: list of MIDI numbers. `style="jihad"` builds each detuned
    voice as an explicit saw (sum of `sin(k*phase)/k`) instead of the
    canonical version's `sin(2*pi*f*det*k*t + random_phase)` -- same
    texture, slightly different phase-randomization approach."""
    n = int(dur * SR)
    tt = np.arange(n) / SR
    out = np.zeros(n)
    if style == "jihad":
        for m in chord:
            f = midi_to_hz(m)
            for det in (-0.004, 0.0, 0.005):
                ph = 2 * np.pi * f * (1 + det) * tt
                saw = np.zeros(n)
                for k in range(1, 9):
                    saw += np.sin(k * ph) / k
                out += saw / 3.0
        env_lead = np.clip(tt / 2.0, 0, 1)
    else:
        for m in chord:
            f = midi_to_hz(m)
            for det, g in [(0.996, 0.6), (1.0, 1.0), (1.005, 0.6)]:
                for k in range(1, 9):
                    out += (g / k) * np.sin(2 * np.pi * f * det * k * tt +
                                            rng.uniform(0, 2 * np.pi))
        env_lead = np.clip(tt / 1.5, 0, 1)
    sos_s = signal.butter(2, [180, 2600], "bandpass", fs=SR, output="sos")
    out = signal.sosfilt(sos_s, out)
    trem = (0.5 + 0.5 * np.sin(2 * np.pi * trem_hz * tt)) ** 1.2
    env = np.minimum(env_lead, np.clip((dur - tt) / 2.0, 0, 1))
    out *= trem * env
    return norm(out)


if __name__ == "__main__":
    out = out_arg("fx")
    from _common import concat

    chord = [45, 52, 57, 60]
    demo = concat([
        zap(fast=False), zap(fast=True),
        rev_cymbal(decay=6.0), rev_cymbal(decay=3.2),
        riser(dur=2.0, style="default"), riser(dur=2.0, style="jihad"),
        tremolo_strings(chord, 2.5, style="default"),
        tremolo_strings(chord, 2.5, style="jihad"),
    ], gap=0.15)
    write_wav(out, demo)
    assert np.max(np.abs(demo)) <= 1.0 + 1e-9
    assert np.isfinite(demo).all()
    print("fx.py: peak/finite OK; zap/riser/rev_cymbal/tremolo_strings rendered")
