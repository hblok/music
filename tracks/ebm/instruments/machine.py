"""Machine — the vocal-slot treatment: a recorded phrase becomes the 1993
sampler's speech snippet.

The intercom band (a bandpass), cruder EPS dirt than the drums (hold 3,
8 bits — speech was the cheapest sample in the memory), an optional ring
modulator (the robot / computer voice), soft drive, and a sequencer
RETRIGGER (the dark-electro stutter: the first slice re-fired on the
grid, then the whole word).  Takes any mono array — a spoken take from
/workspace/music/vocals/, or a bark for the audition — and returns mono,
peak 1.0.  Not a vocoder; add one only if the ring mod reads as a toy.

    from machine import machine, retrigger
    y = machine(take)                          # band + dirt
    y = machine(take, ring_hz=138.6)           # + the robot, at the root
    y = retrigger(y, STEP, n=3)                # stutter ×3 then the word
"""
from __future__ import annotations

import numpy as np
from scipy import signal

from _common import SR, STEP, audition, dirt, norm, out_arg
from bark import bark


def machine(x, band=(200.0, 3400.0), hold=3, bits=8, ring_hz=0.0, drive=1.5, lowpass=4000.0):
    """band: the intercom bandpass (Hz); hold/bits/lowpass: the sampler
    dirt; ring_hz: ring-modulator carrier (0 = off; the track root works);
    drive: tanh."""
    y = signal.sosfilt(signal.butter(2, band, "bandpass", fs=SR, output="sos"), x)
    if ring_hz:
        y = y * np.sin(2 * np.pi * ring_hz * np.arange(len(y)) / SR)
    y = np.tanh(drive * norm(y))
    return norm(dirt(y, hold=hold, bits=bits, lowpass=lowpass))


def retrigger(x, step_s=STEP, n=3, head=0.10):
    """The first `head` seconds of x re-fired every `step_s`, n times, then
    x whole on the next step."""
    nh = int(head * SR)
    h = x[:nh] * np.clip((nh - np.arange(nh)) / int(0.004 * SR), 0, 1)     # a sampler-style cut
    out = np.zeros(int(n * step_s * SR) + len(x))
    for i in range(n):
        i0 = int(i * step_s * SR)
        out[i0:i0 + nh] += h
    i0 = int(n * step_s * SR)
    out[i0:i0 + len(x)] += x
    return norm(out)


if __name__ == "__main__":
    out = out_arg("machine")
    take = bark(45, dur=0.35, vowel="a", vowel2="e", rasp=0.0, drive=1.0, hold=1, lowpass=None)
    hits = [("bark, untreated", take),
            ("machine: band + dirt", machine(take)),
            ("machine: + ring 110 Hz", machine(take, ring_hz=110.0)),
            ("machine: + ring 110 Hz, hold 5, 6 bits", machine(take, ring_hz=110.0, hold=5, bits=6)),
            ("retrigger x3 on 16ths, then the word", retrigger(machine(take, ring_hz=110.0)))]
    for label, h in hits:
        assert abs(np.max(np.abs(h)) - 1) < 1e-6 and np.all(np.isfinite(h)), label
    audition("machine", hits, out=out)
