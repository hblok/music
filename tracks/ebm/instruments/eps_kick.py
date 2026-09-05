"""EPS kick — the sampled-kick crunch of 1993 EBM.

A 909-family pitch-drop body (the canonical make_kick lineage, minus its
sub layer — the SH-101 owns the low end) driven hard, truncated like a
sampler hit, and decimated.  Mono.

    from eps_kick import kick
    x = kick()                        # the slam kick
    x = kick(drive=2.6, cut=0.12)     # harder, shorter
"""
from __future__ import annotations

import numpy as np

from _common import SR, audition, bp_noise, dirt, gate, norm, out_arg, place, steps_buffer


def kick(f_start=150.0, f_end=46.0, sweep=55.0, decay=8.0, click=0.5,
         drive=1.8, cut=0.20, hold=2, lowpass=6500.0):
    """One kick hit.  f_start/f_end/sweep: the pitch dive (Hz, Hz, 1/s);
    decay: body decay (1/s); click: 1.8-9 kHz transient mix; drive: tanh
    drive (the knock); cut: hard truncation (s); hold/lowpass: sampler
    dirt (see _common.dirt)."""
    n = int((cut + 0.01) * SR)
    td = np.arange(n) / SR
    f = f_end + (f_start - f_end) * np.exp(-td * sweep)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-td * decay)
    x = body + click * bp_noise(n, 1800, 9000) * np.exp(-td * 600)
    x = np.tanh(drive * x)
    x *= (1 - np.exp(-td / 0.0006)) * gate(td, cut, 0.006)
    return norm(dirt(x, hold=hold, lowpass=lowpass))


def loop(bars=2, **kw):
    """Four-on-the-floor for `bars` bars."""
    x = kick(**kw)
    buf = steps_buffer(bars)
    for b in range(bars * 4):
        place(buf, x, b * 4)
    return buf


if __name__ == "__main__":
    out = out_arg("eps_kick")
    hits = [kick(),                                   # default slam
            kick(drive=2.6, cut=0.12),                # harder, shorter
            kick(drive=1.0, hold=1, lowpass=None),    # clean reference
            kick(f_start=120, decay=12, cut=0.30)]    # softer dive, longer
    for h in hits:
        assert abs(np.max(np.abs(h)) - 1) < 1e-6 and len(h) < SR
    audition("eps_kick", hits, loop(), out=out)
