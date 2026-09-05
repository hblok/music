"""The engine together: kick + slam snare + hats + SH-101, 8 bars at 122.

Bars 1-4 the stomp cell (verse: closed hats only); bars 5-8 the gallop
with open hats.  No sidechain, no reverb, no master — by ear, raw.
"""
from __future__ import annotations

import numpy as np

from _common import BAR, SR, out_arg, place, steps_buffer, write_wav
from eps_kick import kick
from eps_snare import snare
from hats import carpet
from sh101_bass import CELLS, render_cell

GAIN = {"kick": 1.0, "snare": 0.9, "hats": 0.3, "bass": 0.75}


def groove(bars=8, root=45):
    buf = steps_buffer(bars)
    k, s = kick(), snare()
    for b in range(bars):
        for beat in range(4):
            place(buf, k, b * 16 + beat * 4, GAIN["kick"])
        place(buf, s, b * 16 + 4, GAIN["snare"])
        place(buf, s, b * 16 + 12, GAIN["snare"])
    half = bars // 2
    n_half = int(half * BAR * SR)
    buf[:len(carpet(half, open_steps=()))] += GAIN["hats"] * carpet(half, open_steps=())
    c2 = carpet(bars - half)
    buf[n_half:n_half + len(c2)] += GAIN["hats"] * c2
    b1 = render_cell(CELLS["stomp"], root=root, bars=half)
    buf[:len(b1)] += GAIN["bass"] * b1
    b2 = render_cell(CELLS["gallop"], root=root, bars=bars - half)
    buf[n_half:n_half + len(b2)] += GAIN["bass"] * b2
    return buf


if __name__ == "__main__":
    out = out_arg("demo_groove")
    x = groove()
    assert np.all(np.isfinite(x))
    write_wav(out, x)
