"""The Stitch archetype: half-time at the 122 grid — sparse kick, the
slam on 3 only, no hats, the seethe bed throughout, a dark Juno cluster
pad (A, Bb, E) in the second half, sparse barks.  8 bars.  demo_seethe.wav.
"""
from __future__ import annotations

import numpy as np

from _common import BAR, SR, out_arg, place, steps_buffer, write_wav
from bark import chant
from eps_kick import kick
from eps_snare import snare
from juno import pad_loop
from seethe import seethe

GAIN = {"kick": 0.9, "snare": 0.9, "seethe": 0.55, "pad": 0.25, "bark": 0.5}
KICK = "x.......x.x....."
SNARE = "........x......."


def demo(bars=8):
    buf = steps_buffer(bars)
    k, s = kick(drive=2.2, cut=0.16), snare(plate=0.8, cut=0.2)
    for b in range(bars):
        for st, ch in enumerate(KICK):
            if ch == "x":
                place(buf, k, b * 16 + st, GAIN["kick"])
        for st, ch in enumerate(SNARE):
            if ch == "x":
                place(buf, s, b * 16 + st, GAIN["snare"])
    bed = seethe(45, bars * BAR, throb=0.4)
    buf[:len(bed)] += GAIN["seethe"] * bed
    half = bars // 2
    n_half = int(half * BAR * SR)
    p = pad_loop(((57, 58, 64),) * half, cutoff=600.0)
    buf[n_half:n_half + len(p)] += GAIN["pad"] * p
    bk = chant("x...........l...", vowels="ou", bars=bars, onset="d", fall=4.0)
    buf[:len(bk)] += GAIN["bark"] * bk
    return buf


if __name__ == "__main__":
    out = out_arg("demo_seethe")
    x = demo()
    assert np.all(np.isfinite(x))
    write_wav(out, x)
