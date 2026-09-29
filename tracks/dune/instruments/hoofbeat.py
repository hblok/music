"""Galloping hoofbeats -- the sandworm/steed gait ostinato from Kanly.

Extracted from `generate_kanly.py:make_hoof` (used to build a `HOOF_A` /
`HOOF_B` lead/trail pair, placed by `place_gallop` in alternating L/R pans
to sell the four-beat gait). Not reused verbatim elsewhere in the dune
catalog (a one-off, but a clean, reusable "instrument" in its own right),
so this module has a single source and no variant table.
"""
from __future__ import annotations

import numpy as np
from scipy import signal

from _common import SR, add_at, norm, out_arg, write_wav

rng = np.random.default_rng(1965)   # generate_kanly.py's seed


def hoof(lead=False):
    """One hoofbeat hit: a short pitched thump (200->62 Hz or 170->55 Hz)
    plus a bandpassed dust burst, gated by a fast attack.

    `lead=True` gives the brighter/faster-decaying "lead foot" hit;
    `lead=False` the darker "trail foot" -- alternate them to build a
    gallop with `gallop_pattern()`.
    """
    n = int(0.12 * SR)
    td = np.arange(n) / SR
    f0, f1, dec = (200.0, 62.0, 40.0) if lead else (170.0, 55.0, 46.0)
    f_curve = f1 + (f0 - f1) * np.exp(-td * 55.0)
    body = np.sin(2 * np.pi * np.cumsum(f_curve) / SR) * np.exp(-td * dec)
    sos_d = signal.butter(2, [220, 1700], "bandpass", fs=SR, output="sos")
    dust = signal.sosfilt(sos_d, rng.standard_normal(n)) * np.exp(-td * 70.0)
    dust /= np.max(np.abs(dust)) + 1e-12
    x = (body + 0.45 * dust) * (1 - np.exp(-td * 900.0))
    return norm(x)


def gallop_pattern(t0, cells, level=1.0, beat=0.5, pan_lead=0.4,
                    buf_l=None, buf_r=None):
    """Lay one bar of galloping hoofbeats into stereo buffers `buf_l` /
    `buf_r`, alternating lead/trail foot L/R for the gait, matching
    `generate_kanly.py:place_gallop`.

    `cells`: a 2-tuple of per-beat triplet-subdivision gain lists, e.g.
    `([1, 0, 0.6], [0, 1, 0])` -- one cell for even beats, one for odd,
    each of length 3 (a hit every 1/3 beat slot, 0 = silent).
    `t0`: bar start time in seconds. `beat`: seconds per beat.
    Returns `(buf_l, buf_r)` (freshly allocated if not passed in, sized to
    fit the bar with a little tail room).
    """
    if buf_l is None:
        n = int((t0 + 4 * beat + 0.2) * SR)
        buf_l = np.zeros(n)
        buf_r = np.zeros(n)
    hoof_a, hoof_b = hoof(lead=True), hoof(lead=False)
    flip = 0
    for b in range(4):
        cell = cells[b % 2]
        for tp, g in enumerate(cell):
            if g <= 0:
                continue
            st = t0 + (b + tp / 3.0) * beat
            lead = (flip % 2 == 0)
            h = hoof_a if lead else hoof_b
            p = pan_lead if lead else (1.0 - pan_lead)
            add_at(buf_l, h, st, level * g * np.cos(p * np.pi / 2))
            add_at(buf_r, h, st, level * g * np.sin(p * np.pi / 2))
            flip += 1
    return buf_l, buf_r


if __name__ == "__main__":
    out = out_arg("hoofbeat")
    beat = 0.5  # 120 BPM reference
    cells = ([1, 0, 0.6], [0.8, 0, 1])
    buf_l, buf_r = gallop_pattern(0.1, cells, level=0.9, beat=beat)
    buf_l, buf_r = gallop_pattern(0.1 + 4 * beat, cells, level=0.9, beat=beat,
                                   buf_l=buf_l, buf_r=buf_r)
    write_wav(out, (buf_l, buf_r))
    for x in (buf_l, buf_r, hoof(True), hoof(False)):
        assert np.max(np.abs(x)) <= 1.0 + 1e-9
        assert np.isfinite(x).all()
    print("hoofbeat.py: peak/finite OK; two-bar gallop rendered")
