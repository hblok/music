"""Devices — the arrangement events no_access v3 proved, as library calls.

The blueprint's seam kit (EBM_1990s.md section 6 and 9): the kick FIGURES
that rotate under a stomp, the snare RUN on the last beat of a phrase,
the two-bar ROLL (8ths, then 16ths to 32nds, rising) with the noise
RISER under it, the DOWNSWEEP after the chorus hit, the one composed
SILENT BEAT, and the dotted-8th DELAY the 1999 dialect puts on leads and
stabs.  Extracted 2026-09-16 after the flat-and-similar verdict on the
tracks that were built without any of them.  Each takes an already
rendered hit (render once, place many) and returns one mono event on
the grid — except the two treatments at the end, which return WET taps
at the input's scale (`pingpong` a left/right pair) for the track to add
at its own gain.

    from devices import FIGURES, run, roll, riser, downsweep, silent_beat, delay, pingpong
    fig = FIGURES["B"]                    # "x...x...x...x.x." on every 4th bar
    place(buf, run(S), b * 16 + 12)       # the last beat of bar 4n+3
    place(buf, roll(S), b * 16)           # two bars into the chorus
    place(buf, riser(), b * 16)           # under the roll
    gate = silent_beat(N, t0, t1)         # multiply the mastered mix by it
    L, R = pingpong(x, DOTTED_8TH)        # the VNV tail on a lead layer
"""
from __future__ import annotations

import numpy as np
from scipy import signal

from _common import BAR, BEAT, SR, STEP, audition, norm, out_arg, place, steps_buffer
from juno import noise_sweep

FIGURES = {"A": "x...x...x...x...",       # four on the floor
           "B": "x...x...x...x.x.",       # + the "and" of 4: every 4th bar (the stumble)
           "C": "x..xx...x...x.x."}       # + the "a" of 1: no_access's bar 4n+3, never under an offbeat bass
RUN = "............xxxx"                  # the snare run: 16ths on the last beat
DOTTED_8TH = 3 * STEP


def run(hit, n=4, gain=0.55):
    """The snare run: `n` 16ths ending on the bar line, quieter than the
    slam.  One beat long when n=4; place it at step 12."""
    buf = np.zeros(int(n * STEP * SR) + len(hit))
    for i in range(n):
        place(buf, hit, i, gain)
    return buf


def roll(hit, gain=(0.4, 0.65, 1.0)):
    """The two-bar roll into a chorus: bar 1 on 8ths rising gain[0] ->
    gain[1], bar 2 on 16ths then 32nds rising gain[1] -> gain[2].  Replaces
    the 2-and-4 snare for those two bars; the kick keeps going."""
    buf = steps_buffer(2)
    first = np.arange(0, 16, 2)
    second = np.concatenate([np.arange(0, 8, 1), np.arange(8, 16, 0.5)])
    for i, s in enumerate(first):
        place(buf, hit, s, gain[0] + (gain[1] - gain[0]) * i / len(first))
    for i, s in enumerate(second):
        place(buf, hit, 16 + s, gain[1] + (gain[2] - gain[1]) * i / len(second))
    return buf


def riser(bars=2, f0=200.0, f1=6000.0, res=3.0):
    """The white-noise swell under the roll (juno.noise_sweep, the
    no_access settings)."""
    return noise_sweep(bars * BAR, f0, f1, res=res)


def downsweep(bars=1, f0=6000.0, f1=150.0, res=4.0):
    """The sweep DOWN after the chorus hit."""
    return noise_sweep(bars * BAR, f0, f1, res=res)


def silent_beat(n, t0, t1, edge=0.005):
    """A gain curve of length n: 1 everywhere, 0 between t0 and t1 seconds
    with `edge`-second linear ramps.  Multiply the MASTERED mix by it —
    the silence has to be total, bed included."""
    g = np.ones(n)
    i0, i1, e = int(t0 * SR), int(t1 * SR), int(edge * SR)
    g[i0:i1] = 0.0
    g[i0 - e:i0] = np.linspace(1, 0, e)
    g[i1:i1 + e] = np.linspace(0, 1, e)
    return g


def delay(x, time_s=DOTTED_8TH, feedback=0.45, taps=6, damp=4000.0):
    """WET taps only, at x's scale: x repeated every `time_s`, each tap
    `feedback` times the last and lowpassed at `damp` (the BBD darkens).
    Add to the layer at the track's gain."""
    d = int(time_s * SR)
    out = np.zeros(len(x) + taps * d)
    y = x.copy()
    sos = signal.butter(1, damp, "low", fs=SR, output="sos")
    for k in range(1, taps + 1):
        y = signal.sosfilt(sos, y) * feedback
        out[k * d:k * d + len(x)] += y
    return out


def pingpong(x, time_s=DOTTED_8TH, feedback=0.45, taps=6, damp=4000.0):
    """The stereo version: odd taps left, even taps right.  Returns (L, R),
    wet only, at x's scale."""
    d = int(time_s * SR)
    L, R = np.zeros(len(x) + taps * d), np.zeros(len(x) + taps * d)
    y = x.copy()
    sos = signal.butter(1, damp, "low", fs=SR, output="sos")
    for k in range(1, taps + 1):
        y = signal.sosfilt(sos, y) * feedback
        (L if k % 2 else R)[k * d:k * d + len(x)] += y
    return L, R


if __name__ == "__main__":
    from eps_hit import hit
    from eps_kick import kick
    from eps_snare import snare
    from juno import stab

    out = out_arg("devices")
    K, S = kick(), snare()
    parts = []
    # the figures: two bars each, kick + slam, figure named
    for name, fig in FIGURES.items():
        buf = steps_buffer(2)
        for b in range(2):
            for s in range(16):
                if fig[s] == "x":
                    place(buf, K, b * 16 + s)
                if s in (4, 12):
                    place(buf, S, b * 16 + s, 1.1)
        parts.append((f"figure {name}  {fig}", buf))
    # the run on bar 4 of a 4-bar stomp
    buf = steps_buffer(4)
    for b in range(4):
        for s in range(0, 16, 4):
            place(buf, K, b * 16 + s)
        for s in (4, 12):
            place(buf, S, b * 16 + s, 1.1)
    place(buf, run(S), 3 * 16 + 12)
    parts.append(("stomp x4, the run on the last beat", buf))
    # two verse bars, the roll + riser, the hit + downsweep, two chorus bars
    buf = steps_buffer(6)
    for b in range(6):
        for s in range(0, 16, 4):
            place(buf, K, b * 16 + s)
        if b not in (2, 3):
            for s in (4, 12):
                place(buf, S, b * 16 + s, 1.1)
    place(buf, roll(S), 2 * 16, 1.1)
    place(buf, riser(), 2 * 16, 0.5)
    place(buf, hit(dur=0.35), 4 * 16, 0.8)
    place(buf, downsweep(), 4 * 16, 0.4)
    parts.append(("2 bars, ROLL + riser (2 bars), the hit + downsweep, 2 bars", buf))
    # the silent beat: a stomp with beat 4 of bar 2 cut dead
    buf = steps_buffer(3)
    for b in range(3):
        for s in range(0, 16, 4):
            place(buf, K, b * 16 + s)
        for s in (4, 12):
            place(buf, S, b * 16 + s, 1.1)
    buf *= silent_beat(len(buf), 2 * BAR - BEAT, 2 * BAR)
    parts.append(("the silent beat (beat 4 of bar 2)", buf))
    # a stab through the dotted-8th delay, mono sum of the ping-pong
    st = stab((57, 60, 64))
    L, R = pingpong(st)
    buf = np.zeros(len(L))
    buf[: len(st)] += st
    buf += 0.7 * (L + R)
    parts.append(("one stab + dotted-8th ping-pong (mono sum)", norm(buf)))
    for label, x in parts:
        assert np.all(np.isfinite(x)) and np.max(np.abs(x)) > 0.5, label
    assert abs(len(roll(S)) - int((2 * BAR + 0.5) * SR)) < 2
    assert len(delay(st)) == len(st) + 6 * int(DOTTED_8TH * SR)
    audition("devices", parts, out=out)
