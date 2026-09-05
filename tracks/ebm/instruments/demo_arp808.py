"""The 'Arp (808 Edit)' archetype: an 808 pattern under a Juno arp, a
Juno pad beneath, 4 bars, 122.  demo_arp808.wav.
"""
from __future__ import annotations

import numpy as np

from _common import out_arg, write_wav
from juno import AM, F, G, arp, pad_loop
from kit808 import pattern

GAIN = {"kit": 0.9, "arp": 0.55, "pad": 0.3}


def demo():
    buf = GAIN["kit"] * pattern(4)
    a = arp(AM, bars=4, pattern="updown", octaves=2)
    buf[:len(a)] += GAIN["arp"] * a
    p = pad_loop((AM, F, G, AM))
    buf[:len(p)] += GAIN["pad"] * p
    return buf


if __name__ == "__main__":
    out = out_arg("demo_arp808")
    x = demo()
    assert np.all(np.isfinite(x))
    write_wav(out, x)
