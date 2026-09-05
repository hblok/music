"""The Burnin' Heretic archetype: the groove with the chug riff as a
texture in the second half (bars 5-8), an open chord on the last bar.
demo_riff.wav.
"""
from __future__ import annotations

import numpy as np

from _common import BAR, SR, out_arg, write_wav
from demo_groove import groove
from riff import riff

GAIN = {"riff": 0.45}


def demo(bars=8):
    buf = groove(bars)
    half = bars // 2
    for bar, r in ((half, riff("x.x.x.x.x.xbx.x.", root=45, bars=half - 1)),
                   (bars - 1, riff("x.x.x.x.o.......", root=45, bars=1))):
        i0 = int(bar * BAR * SR)
        m = min(len(r), len(buf) - i0)
        buf[i0:i0 + m] += GAIN["riff"] * r[:m]
    return buf


if __name__ == "__main__":
    out = out_arg("demo_riff")
    x = demo()
    assert np.all(np.isfinite(x))
    write_wav(out, x)
