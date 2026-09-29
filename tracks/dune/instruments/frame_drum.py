"""Frame drum (daf) hit and roll -- the accelerating-roll section-launch
gesture used throughout the Dune tracks.

Extracted from `generate_water_of_life.py:make_frame_hit` / `frame_roll`
(identical in fall_of_arrakeen, kwisatz_haderach, maker_comes, sihaya,
sleeper_awakens; night_pursuit and jihad carry small local variants
exposed via parameters).
"""
from __future__ import annotations

import numpy as np
from scipy import signal

from _common import SR, add_at, norm, out_arg, write_wav

rng = np.random.default_rng(10191)


def frame_hit(dur=0.12, noise_band=(180, 1400), noise_decay=40.0,
              tone_hz=95.0, tone_gain=0.5, tone_decay=30.0):
    """One frame-drum stroke: bandpassed noise (180-1400 Hz) plus a
    95 Hz skin tone."""
    n = int(dur * SR)
    td = np.arange(n) / SR
    sos_f = signal.butter(2, list(noise_band), "bandpass", fs=SR, output="sos")
    nz = norm(signal.sosfilt(sos_f, rng.standard_normal(n))) * np.exp(-td * noise_decay)
    tone = tone_gain * np.sin(2 * np.pi * tone_hz * td) * np.exp(-td * tone_decay)
    x = nz + tone
    return norm(x)


def frame_roll(hit, dur=2.0, rate0=9.0, rate1=11.0, gain0=0.30, gain1=0.70):
    """The accelerating roll: hit density rises `rate0` -> `rate0+rate1`
    strokes/second and gain rises `gain0` -> `gain0+gain1` across `dur`
    seconds -- the standard section-launch gesture (build into a chorus,
    launch, drop). `hit` is a pre-rendered `frame_hit()` array (render
    once, call `frame_roll` many times against it)."""
    out = np.zeros(int((dur + 0.3) * SR))
    tcur = 0.0
    while tcur < dur:
        frac = tcur / dur
        rate = rate0 + rate1 * frac
        g = (gain0 + gain1 * frac) * rng.uniform(0.85, 1.0)
        add_at(out, hit, tcur, g)
        tcur += 1.0 / rate
    return out


if __name__ == "__main__":
    out = out_arg("frame_drum")
    from _common import concat

    hit = frame_hit()
    roll = frame_roll(hit, dur=2.0)
    demo = concat([hit, hit, norm(roll)], gap=0.2)
    write_wav(out, demo)
    assert np.max(np.abs(hit)) <= 1.0 + 1e-9
    assert np.isfinite(hit).all()
    assert np.isfinite(roll).all()
    print("frame_drum.py: peak/finite OK; roll rendered")
