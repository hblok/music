"""Seethe — the slow, dark, evolving drone bed under Stitch.

Brown noise banded low, a slowly swept resonant lowpass (never parked),
a sub root with a very slow beat, a distorted low pulse for the
industrial grit, a breathing amplitude LFO, and an optional 8th-note
throb gate on the BPM grid.  Deep, low, moving — no static mid tone (the
tinnitus rule).  Rendered as a long bed, not an event.  Mono.

    from seethe import seethe
    bed = seethe(45, 8 * BAR)                   # A2 root, 8 bars
    bed = seethe(45, 8 * BAR, throb=0.6)        # with the 8th-note throb
"""
from __future__ import annotations

import numpy as np
from scipy import signal

import _common
from _common import BAR, BEAT, SR, audition, midi_to_hz, norm, out_arg
from sh101_bass import svf_lowpass


def seethe(midi=45, dur=4 * BAR, sweep=(120.0, 900.0), rate=0.06, res=3.0, noise=1.0,
           sub=0.6, grit=0.35, breath=0.3, breath_rate=0.11, throb=0.0, hold=1):
    """midi: root (the sub sits an octave below it); dur: length (s);
    sweep: (lo, hi) Hz of the slow resonant lowpass; rate: its LFO (Hz);
    res: Q; noise: brown-noise mix; sub: root sine mix (slow beat inside);
    grit: distorted low pulse mix; breath/breath_rate: amplitude LFO;
    throb: depth of an 8th-note gate on the BPM grid (0 = none)."""
    n = int(dur * SR)
    td = np.arange(n) / SR
    f = midi_to_hz(midi)
    brown = np.cumsum(_common.rng.standard_normal(n))
    brown -= np.linspace(brown[0], brown[-1], n)
    brown = signal.sosfilt(signal.butter(1, 150, "high", fs=SR, output="sos"), brown)   # tilt brown -> pink-ish
    brown = norm(signal.sosfilt(signal.butter(2, [40, 1500], "bandpass", fs=SR, output="sos"), brown))
    lo, hi = sweep
    fc = lo * (hi / lo) ** (0.5 - 0.5 * np.cos(2 * np.pi * rate * td))          # log sweep, never parked
    x = noise * svf_lowpass(brown, fc, res)
    x += sub * 0.5 * (np.sin(2 * np.pi * f / 2 * td) + np.sin(2 * np.pi * f / 2 * 1.002 * td + 1.0))
    pulse = signal.sosfilt(signal.butter(2, 250, "low", fs=SR, output="sos"), signal.square(2 * np.pi * f / 2 * td))
    x += grit * np.tanh(3.0 * pulse) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.037 * td))
    x *= 1 - breath * 0.5 * (1 + np.sin(2 * np.pi * breath_rate * td + 4.0))
    if throb:
        g = 0.5 + 0.5 * np.cos(2 * np.pi * td / (BEAT / 2))                      # 8th-note gate
        x *= 1 - throb * (1 - g) ** 0.5
    x *= np.minimum(np.clip(td / 0.5, 0, 1), np.clip((dur - td) / 1.0, 0, 1))
    return norm(_common.dirt(x, hold=hold) if hold > 1 else x)


if __name__ == "__main__":
    out = out_arg("seethe")
    hits = [("seethe A2, 4 bars (default)", seethe()),
            ("seethe, faster sweep + more res", seethe(rate=0.15, res=4.0)),
            ("seethe, throb 0.7", seethe(throb=0.7)),
            ("seethe E2, noise only (no sub, no grit)", seethe(40, sub=0.0, grit=0.0)),
            ("seethe, grit up, sampled", seethe(grit=0.7, hold=2))]
    for label, h in hits:
        assert abs(np.max(np.abs(h)) - 1) < 1e-6 and np.all(np.isfinite(h)), label
    audition("seethe", hits, None, gap=1.0, out=out)
