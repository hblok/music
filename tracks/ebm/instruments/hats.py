"""Hats — closed and open, mono, sampled-crunchy.

The canonical make_hat lineage through the sampler dirt: the hold=2
decimation folds the >11 kHz content down, which is exactly the EPS hat.

    from hats import hat, carpet
    c = hat(); o = hat(open_=True)
"""
from __future__ import annotations

import numpy as np

from _common import SR, audition, dirt, gate, hp_noise, norm, out_arg, place, steps_buffer


def hat(open_=False, length=None, decay=None, hp=7500.0, hold=2):
    """One hat.  open_: the offbeat 'tss'; length/decay default per type;
    hp: highpass corner; hold: sampler decimation (1 = clean)."""
    length = length or (0.13 if open_ else 0.04)
    decay = decay or (26.0 if open_ else 120.0)
    n = int(length * SR)
    td = np.arange(n) / SR
    x = hp_noise(n, hp) * np.exp(-td * decay)
    x *= (1 - np.exp(-td / 0.0003)) * gate(td, length, 0.003)
    return norm(dirt(x, hold=hold))


def carpet(bars=2, accents=(1.0, 0.5, 0.7, 0.5), open_steps=(2, 6, 10, 14), **kw):
    """Closed 16ths with a per-16th accent cell; open hats on `open_steps`
    (the off-8ths by default; pass () for verses)."""
    c = hat(**kw)
    o = hat(open_=True, **kw)
    buf = steps_buffer(bars)
    for s in range(bars * 16):
        if (s % 16) in open_steps:
            place(buf, o, s)
        else:
            place(buf, c, s, accents[s % 4])
    return buf


if __name__ == "__main__":
    out = out_arg("hats")
    hits = [hat(), hat(decay=60), hat(hold=1), hat(open_=True), hat(open_=True, hold=3)]
    for h in hits:
        assert abs(np.max(np.abs(h)) - 1) < 1e-6
    audition("hats", hits, np.concatenate([carpet(open_steps=()), carpet()]), out=out)
