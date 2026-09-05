"""The engine + the colour: the 8-bar groove with Juno stabs, a Juno pad
under the second half, and an orchestral hit on the halfway downbeat.
Bars 1-4 stabs quiet (verse), bars 5-8 stabs up + pad + hit (chorus).
Raw, no reverb, no master.  demo_groove.wav stays untouched: this is
demo_colour.wav.
"""
from __future__ import annotations

import numpy as np

from _common import BAR, SR, out_arg, place, write_wav
from demo_groove import groove
from eps_hit import hit
from juno import AM, F, G, pad_loop, stab_loop

GAIN = {"stab_verse": 0.22, "stab_chorus": 0.4, "pad": 0.3, "hit": 0.55}


def colour(bars=8):
    buf = groove(bars)
    half = bars // 2
    n_half = int(half * BAR * SR)
    prog = (AM, F, G, AM)
    s1 = stab_loop(prog)
    buf[:len(s1)] += GAIN["stab_verse"] * s1
    s2 = stab_loop(prog, res=2.5)
    buf[n_half:n_half + len(s2)] += GAIN["stab_chorus"] * s2
    p = pad_loop(prog)
    buf[n_half:n_half + len(p)] += GAIN["pad"] * p
    place(buf, hit(), half * 16, GAIN["hit"])
    return buf


if __name__ == "__main__":
    out = out_arg("demo_colour")
    x = colour()
    assert np.all(np.isfinite(x))
    write_wav(out, x)
