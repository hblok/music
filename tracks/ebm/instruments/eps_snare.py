"""EPS slam snare — the 2-and-4 blow of Soli Deo Gloria.

Two head modes with a snappy pitch drop, a bright noise burst, and a
dense plate tail that the sampler truncation cuts dead: the gated-plate
snare, sampled.  A GROOVE instrument (every 2 & 4), unlike tech_noir's
slam which is punctuation.  Mono.

    from eps_snare import snare
    x = snare()                 # the slam
    x = snare(plate=0.0)        # dry
"""
from __future__ import annotations

import numpy as np

from _common import SR, audition, bp_noise, dirt, gate, norm, out_arg, place, steps_buffer


def snare(body_hz=200.0, body_decay=22.0, snap=0.6, tone=0.6, noise_band=(1500.0, 7000.0),
          noise_decay=18.0, plate=0.5, plate_decay=4.0, drive=1.4, cut=0.14,
          hold=2, lowpass=8000.0):
    """One snare hit.  body_hz/body_decay: the drum tone; snap: pitch-drop
    depth; tone: body vs wires balance; noise_band/noise_decay: the wires; plate/plate_decay: the reverb
    tail that gets GATED at `cut`; drive: tanh; hold/lowpass: sampler dirt."""
    n = int((cut + 0.02) * SR)
    td = np.arange(n) / SR
    f = body_hz * (1 + snap * np.exp(-td * 90))
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = (np.sin(ph) + 0.45 * np.sin(1.62 * ph)) * np.exp(-td * body_decay)
    noise = bp_noise(n, *noise_band) * np.exp(-td * noise_decay)
    tail = bp_noise(n, 400, 6000) * np.exp(-td * plate_decay)
    x = tone * body + noise + plate * tail
    x = np.tanh(drive * x)
    x *= (1 - np.exp(-td / 0.0005)) * gate(td, cut, 0.008)
    return norm(dirt(x, hold=hold, lowpass=lowpass))


def loop(bars=2, **kw):
    """Snare on 2 and 4 for `bars` bars."""
    x = snare(**kw)
    buf = steps_buffer(bars)
    for b in range(bars):
        place(buf, x, b * 16 + 4)
        place(buf, x, b * 16 + 12)
    return buf


if __name__ == "__main__":
    out = out_arg("eps_snare")
    hits = [snare(),                                    # the slam
            snare(plate=0.0),                           # dry
            snare(plate=0.9, cut=0.22),                 # bigger room, longer gate
            snare(body_hz=170, snap=0.3, drive=2.2),    # lower, harder
            snare(tone=1.0),                            # boxier (more body)
            snare(hold=3, lowpass=5000)]                # crunchier sampler
    for h in hits:
        assert abs(np.max(np.abs(h)) - 1) < 1e-6 and len(h) < SR
    audition("eps_snare", hits, loop(), out=out)
