"""Barks over the engine: the 8-bar groove, bars 1-4 one bark per bar
(sparse verse shouts), bars 5-8 the chant cell.  demo_bark.wav.
"""
from __future__ import annotations

import numpy as np

from _common import BAR, SR, out_arg, write_wav
from bark import chant
from demo_groove import groove

GAIN = {"sparse": 0.55, "chant": 0.6}


def demo(bars=8):
    buf = groove(bars)
    half = bars // 2
    n_half = int(half * BAR * SR)
    a = chant("x...........5...", vowels="ao", bars=half)
    buf[:len(a)] += GAIN["sparse"] * a
    b = chant("x..3..x.5...x...", vowels="aaoa", bars=bars - half)
    buf[n_half:n_half + len(b)] += GAIN["chant"] * b
    return buf


if __name__ == "__main__":
    out = out_arg("demo_bark")
    x = demo()
    assert np.all(np.isfinite(x))
    write_wav(out, x)
