"""Kick drums for the Dune tracks -- the trance kick and the war psy kick
stack, plus the standalone sub-boom layer.

Extracted from (canonical / most common version in each family):
  - `trance_kick()`     <- `generate_water_of_life.py:make_kick` (identical
    in `generate_samples_water.py`; `generate_sleeper_awakens.py` /
    `generate_samples_sleeper.py` differ only in the click: bandpassed
    1.8-9 kHz instead of raw noise -- exposed here as `click_bp=True`).
  - `kick_stack()`      <- `generate_fall_of_arrakeen.py:make_kick_stack`
    (the room-shake stack: punch + click + a long sub tail; near-identical
    in `generate_kwisatz_haderach.py`, `generate_the_navigator.py`,
    `jihad.py` -- tuning differences exposed as parameters).
  - `sub_boom()`        <- `generate_fall_of_arrakeen.py:make_sub_boom`
    (the dedicated per-beat sub layer that rides under every kick stack
    hit; committed as its OWN mix layer in the tracks so peak
    normalization can't trade it against the punch).
  - `driven_kick()`     <- `generate_spice_agony.py:make_kick` (a
    materially different recipe: sub tail and click are baked INTO the
    same body, and the whole thing is driven through `tanh()` twice --
    once for body harmonics, once for the "room-shake" gain stage --
    giving a rounder, more distorted kick than the trance_kick/kick_stack
    family). `generate_muaddib.py:make_kick` / `generate_sleeper_awakens.py`
    match `trance_kick(click_bp=True)` closely enough that they are not
    split out further.

See ../CLAUDE.md ("Room-shake kick") and README.md for the full design
notes and the file-by-file variant table.
"""
from __future__ import annotations

import numpy as np
from scipy import signal

from _common import BEAT, SR, norm, out_arg, write_wav

rng = np.random.default_rng(10191)   # the samples_water / water_of_life seed


def trance_kick(dur=0.30, f0=45.0, f1=150.0, sweep=55.0, decay=9.0,
                 click_gain=0.25, click_bp=False):
    """The 140-145 BPM trance kick: sine diving f0+f1 -> f0 Hz, 0.8 ms
    attack, decay/s exponential release, plus a short noise click for
    transient snap. `click_bp=False` (default) matches Water of Life's
    raw-noise click; `click_bp=True` matches the brighter, bandpassed
    click used from The Sleeper Awakens onward."""
    n = int(dur * SR)
    td = np.arange(n) / SR
    f_curve = f0 + f1 * np.exp(-td * sweep)
    body = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    if click_bp:
        sos_c = signal.butter(2, [1800, 9000], "bandpass", fs=SR, output="sos")
        click = signal.sosfilt(sos_c, rng.standard_normal(n)) * np.exp(-td * 700)
        click = norm(click)
    else:
        click = rng.standard_normal(n) * np.exp(-td * 900)
    env = (1 - np.exp(-td / 0.0008)) * np.exp(-td * decay)
    x = (body + click_gain * click) * env
    return norm(x)


def kick_stack(dur=0.42, punch_f0=44.0, punch_f1=110.0, punch_sweep=50.0,
               punch_decay=9.0, click_gain=0.50, sub=True,
               sub_f0=37.0, sub_f1=16.0, sub_sweep=9.0, sub_gain=1.05):
    """The war-psy room-shaker: `trance_kick`-style punch (bandpassed
    click, 1800-9000 Hz) PLUS a long sub tail landing on `sub_f0` Hz
    (D1 = 37 Hz in fall_of_arrakeen/jihad's key of D) that sustains
    nearly a full beat at 148 BPM. This is the kick from Fall of
    Arrakeen / Kwisatz Haderach / The Navigator / Jihad -- tune
    `punch_f0`/`sub_f0` per track (44/37 Hz war psy vs 48/48 Hz The
    Navigator's earbud-friendly reset -- see README)."""
    n = int(dur * SR)
    td = np.arange(n) / SR
    f_curve = punch_f0 + punch_f1 * np.exp(-td * punch_sweep)
    punch = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    sos_c = signal.butter(2, [1800, 9000], "bandpass", fs=SR, output="sos")
    click = signal.sosfilt(sos_c, rng.standard_normal(n)) * np.exp(-td * 700)
    click = norm(click)
    env_p = (1 - np.exp(-td / 0.0008)) * np.exp(-td * punch_decay)
    x = (punch + click_gain * click) * env_p
    if sub:
        f_sub = sub_f0 + sub_f1 * np.exp(-td * sub_sweep)
        tail = np.sin(2 * np.pi * np.cumsum(f_sub) / SR)
        env_s = (1 - np.exp(-td / 0.004)) * np.exp(-td * 3.2)
        x = x + sub_gain * tail * env_s
    return norm(x)


def sub_boom(dur=None, f0=52.0, f1=14.0, sweep=13.0, release_frac=0.06):
    """The dedicated sub-boom layer: a pure sine falling f0+f1 -> f0 Hz,
    sustaining the whole beat and releasing just before the next hit so
    booms never overlap/comb. Placed under EVERY 4-on-the-floor kick-stack
    hit as its own committed mix layer (weight ~0.30) so peak
    normalization cannot trade it against the punch. `dur` defaults to
    one beat at the reference tempo (`_common.BEAT`); pass the track's
    own beat length explicitly."""
    if dur is None:
        dur = BEAT
    n = int(dur * SR) + 1
    td = np.arange(n) / SR
    f_curve = f0 + f1 * np.exp(-td * sweep)
    x = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    env = ((1 - np.exp(-td / 0.003)) * np.exp(-td * 1.6) *
           np.clip((dur - td) / (release_frac), 0, 1))
    return x * env


def driven_kick(dur=0.55, f0=40.0, f1=115.0, sweep=42.0, body_decay=4.5,
                sub_f=41.0, sub_decay=3.2, click_gain=0.20,
                drive1=1.8, drive2=1.3):
    """`generate_spice_agony.py`'s deep, doubly-driven kick: sine body
    (40+115 Hz knee) tanh-driven once for harmonic rounding, a sub sine
    tail baked into the same buffer (not a separate layer), a plain
    noise click, then the WHOLE mix driven through `tanh()` again for
    the final room-shake character -- rounder and more distorted than
    `kick_stack()`."""
    n = int(dur * SR)
    td = np.arange(n) / SR
    f_curve = f0 + f1 * np.exp(-td * sweep)
    body = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    body = np.tanh(drive1 * body)
    sub = np.sin(2 * np.pi * sub_f * td) * np.exp(-td * sub_decay)
    click = rng.standard_normal(n) * np.exp(-td * 800)
    env = (1 - np.exp(-td / 0.0009)) * np.exp(-td * body_decay)
    x = (body + 0.55 * sub + click_gain * click) * env
    x = np.tanh(drive2 * x)
    return norm(x)


if __name__ == "__main__":
    out = out_arg("kick")
    from _common import concat
    hits = [
        trance_kick(),
        trance_kick(click_bp=True),
        kick_stack(),
        kick_stack(sub=False),
        sub_boom(dur=0.42),
        driven_kick(),
    ]
    demo = concat(hits, gap=0.15)
    write_wav(out, demo)
    for x in hits:
        assert np.max(np.abs(x)) <= 1.0 + 1e-9
        assert np.isfinite(x).all()
    print("kick.py: peak/finite OK for all 6 hits")
