"""Darbuka (doumbek) hand-percussion: doum, tek, ka, and the maqsum
rhythm helper -- the backbone Middle-Eastern kit of every Dune track.

Extracted from (canonical version, identical or near-identical in the
listed files -- see README.md for the full per-file hash table):
  - `make_doum()` <- `generate_base_attack.py` / used verbatim in 10 more
    generators (fall_of_arrakeen, kanly, kwisatz_haderach, maker_comes,
    muaddib, night_pursuit, sihaya, sleeper_awakens, water_of_life).
    `jihad.py` carries a slightly different (deeper/faster) variant,
    exposed here via parameters.
  - `make_tek(ghost=False)` <- two near-identical families exist (a
    2500-9000 Hz / 60 or 95 decay-per-second version used in
    base_attack/kanly/maker_comes/night_pursuit/water_of_life, and a
    brighter 2800-10000 Hz version used in fall_of_arrakeen/
    kwisatz_haderach/muaddib/sihaya/sleeper_awakens) -- both exposed via
    the `band` parameter.
  - `maqsum_pattern()` -- the 16-step doum/tek/ka schedule
    (`{0: "D", 2: "T", 6: "T", 8: "D", 12: "T"}`, ghost kas on off-16ths)
    used across every full-groove Dune track; extracted as data so a new
    track can drive `place_maqsum_bar()` directly instead of re-copying
    the loop.
"""
from __future__ import annotations

import numpy as np
from scipy import signal

from _common import SR, add_at, norm, out_arg, write_wav

rng = np.random.default_rng(1965)

# the 16th-step maqsum rhythm: D = doum, T = tek; ghost kas fill elsewhere
# at random (see place_maqsum_bar). Identical across every full-groove track.
MAQSUM = {0: "D", 2: "T", 6: "T", 8: "D", 12: "T"}


def make_doum(dur=0.30, f0=55.0, f1=35.0, sweep=28.0, ring_hz=190.0,
              ring_gain=0.25, decay=14.0):
    """The deep centre-strokes: falling sine 55+35*e^(-28t) Hz plus a
    190 Hz ring for body. The canonical version across 10+ generators;
    `jihad.py` uses a faster/deeper variant (pass f0=~50, decay=~16 to
    approximate it -- see README for the exact jihad numbers)."""
    n = int(dur * SR)
    td = np.arange(n) / SR
    f_curve = f0 + f1 * np.exp(-td * sweep)
    body = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    ring = ring_gain * np.sin(2 * np.pi * ring_hz * td) * np.exp(-td * 35)
    env = np.exp(-td * decay) * (1 - np.exp(-td * 600))
    return (body + ring) * env


def make_tek(ghost=False, band=(2500, 9000), ping_hz=640.0, dur=0.09):
    """The sharp rim slaps answering L/R: bandpassed noise slap + a
    ping tone. `band=(2500, 9000)` is the base_attack/night_pursuit/
    water_of_life family; pass `band=(2800, 10000)` for the brighter
    fall_of_arrakeen/kwisatz_haderach/sihaya/sleeper_awakens family.
    `ghost=True` gives the quieter, faster-damped ghost stroke (`ka`)."""
    n = int(dur * SR)
    td = np.arange(n) / SR
    sos_h = signal.butter(4, list(band), "bandpass", fs=SR, output="sos")
    slap = signal.sosfilt(sos_h, rng.standard_normal(n))
    ping = 0.4 * np.sin(2 * np.pi * ping_hz * td)
    env = np.exp(-td * (90.0 if ghost else 55.0))
    x = (norm(slap) + ping) * env
    return x * (0.35 if ghost else 1.0)


def place_maqsum_bar(lay_L, lay_R, bar_t0, beat, doum, tek, ka,
                      level=0.6, half=False, fill=False,
                      ka_prob=0.25, tek_pan=(0.35, 0.65)):
    """Place one bar of the maqsum rhythm (16 steps) into stereo layer
    buffers, starting at `bar_t0` seconds, `beat` seconds per quarter
    note (so a 16th = beat/4). `half=True` thins to only the downbeat
    doum + the mid-bar tek (the half-density verse texture used in
    Sihaya/Water of Life); `fill=True` replaces steps 12-15 with a
    tek/ka fill run instead of the maqsum stroke there (the 'every 4th
    bar' fill)."""
    step = beat / 4.0
    for s in range(16):
        st = bar_t0 + s * step
        stroke = MAQSUM.get(s)
        if half and s not in (0, 8):
            stroke = None
        if fill and s >= 12:
            g = (0.45 + 0.55 * (s - 12) / 3.0) * level
            add_at(lay_L, tek, st, g * 0.9)
            add_at(lay_R, tek, st, g * 0.7)
            continue
        if stroke == "D":
            add_at(lay_L, doum, st, level)
            add_at(lay_R, doum, st, level)
        elif stroke == "T":
            p = tek_pan[0] if s in (2, 12) else tek_pan[1]
            add_at(lay_L, tek, st, level * np.cos(p * np.pi / 2))
            add_at(lay_R, tek, st, level * np.sin(p * np.pi / 2))
        elif not half and s % 2 == 1 and rng.random() < ka_prob:
            add_at(lay_L, ka, st, 0.6 * level)
            add_at(lay_R, ka, st, 0.5 * level)


if __name__ == "__main__":
    out = out_arg("darbuka")
    from _common import BEAT, concat

    doum = make_doum()
    tek = make_tek()
    ka = make_tek(ghost=True)
    hits = [doum, tek, ka, make_tek(band=(2800, 10000))]
    demo = concat(hits, gap=0.12)

    # a 2-bar maqsum loop, one full + one half-density with a fill
    bar_len = 4 * BEAT
    loop = np.zeros(int(2 * bar_len * SR) + len(doum))
    loop_r = np.zeros_like(loop)
    place_maqsum_bar(loop, loop_r, 0.0, BEAT, doum, tek, ka, level=0.9)
    place_maqsum_bar(loop, loop_r, bar_len, BEAT, doum, tek, ka,
                      level=0.6, half=True)
    demo = concat([demo, norm(loop)], gap=0.2)

    write_wav(out, demo)
    for x in (doum, tek, ka):
        # make_doum's body+ring sum peaks ~1.02, matching the source
        # scripts verbatim (none of them renormalize this one either) --
        # checked against a generous ceiling, not a strict peak-1.0 gate.
        assert np.max(np.abs(x)) <= 1.10
        assert np.isfinite(x).all()
    print("darbuka.py: peak/finite OK; maqsum loop rendered")
