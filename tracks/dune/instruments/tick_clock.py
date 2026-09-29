"""The tick-tock clock -- the John Wick-style ostinato: bone-dry alternating
tick (left) / tock (right) clicks in straight eighths, constant across
whatever else changes in the arrangement.

Extracted from `generate_night_pursuit.py:make_tick` (identical in
generate_kanly.py and generate_maker_comes.py; generate_base_attack.py and
generate_fall_of_arrakeen.py were not sources for this one -- see
README.md).
"""
from __future__ import annotations

import numpy as np
from scipy import signal

from _common import SR, add_at, norm, out_arg, write_wav

rng = np.random.default_rng(1965)


def tick(tock=False, dur=0.030, ping_gain=0.6, click_decay=240.0,
         ping_decay=180.0):
    """One click: bandpassed-noise burst (2100 Hz tick / 1500 Hz tock)
    plus a damped sine ping (1250 Hz tick / 880 Hz tock). Pan tick left,
    tock right for the alternating ostinato."""
    n = int(dur * SR)
    td = np.arange(n) / SR
    f = 1500.0 if tock else 2100.0
    sos_c = signal.butter(2, [f * 0.8, f * 1.5], "bandpass", fs=SR, output="sos")
    click = norm(signal.sosfilt(sos_c, rng.standard_normal(n))) * np.exp(-td * click_decay)
    ping = ping_gain * np.sin(2 * np.pi * (880.0 if tock else 1250.0) * td) * \
        np.exp(-td * ping_decay)
    x = click + ping
    return norm(x)


def clock_pattern(t0, t1, beat, tick_hit=None, tock_hit=None):
    """Alternating tick(L)/tock(R) events in straight eighths from `t0`
    to `t1` seconds; `beat` is the quarter-note length in seconds.
    Returns a list of (time_s, is_tock) pairs -- place them yourself with
    add_at (panned tick left, tock right) since this is bone dry and
    stays centre-independent of the rest of the mix."""
    events = []
    step = beat / 2.0
    tc = t0
    i = 0
    while tc < t1:
        events.append((tc, i % 2 == 1))
        tc += step
        i += 1
    return events


if __name__ == "__main__":
    out = out_arg("tick_clock")
    from _common import BEAT, concat

    tk = tick(tock=False)
    tc = tick(tock=True)
    hits = [tk, tc]
    demo = concat(hits, gap=0.1)

    # 2 bars of the straight-eighths ostinato, dry, tick panned L / tock R
    dur = 8 * BEAT
    n = int(dur * SR) + len(tk)
    loop_L = np.zeros(n)
    loop_R = np.zeros(n)
    for t_s, is_tock in clock_pattern(0.0, dur, BEAT):
        hit = tc if is_tock else tk
        add_at(loop_L, hit, t_s, 0.3 if is_tock else 1.0)
        add_at(loop_R, hit, t_s, 1.0 if is_tock else 0.3)
    demo = concat([demo, norm(loop_L)], gap=0.2)

    write_wav(out, demo)
    for x in hits:
        assert np.max(np.abs(x)) <= 1.0 + 1e-9
        assert np.isfinite(x).all()
    print("tick_clock.py: peak/finite OK; ostinato loop rendered")
