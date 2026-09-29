"""Big low-end impact/atmosphere FX: the explosion (two variants), the
sandworm's sub-bass rumble, and the Sardaukar anvil-strike hit.

Extracted from (canonical / most common version in each family):
  - `explosion()` <- `generate_kwisatz_haderach.py` (identical in
    `jihad.py`: a brown-noise rumble low-passed at 150 Hz plus a rising
    sub-sine core, slow attack/decay). `generate_fall_of_arrakeen.py`'s
    is a slightly earlier variant (white noise low-passed instead of
    integrated brown noise, a falling instead of rising sub-curve) --
    kept as `explosion_arrakeen()`.
  - `worm_rumble()` <- `generate_muaddib.py`: a slow rising-then-settling
    sub-sine plus a detrended-integrated-noise (brown-noise-ish) rumble
    layer, long slow attack -- the sandworm approach/passing-under
    rumble.
  - `anvil()` <- `jihad.py`: four inharmonic partials (bell-like ratios)
    over a fast highpassed-noise transient -- the Sardaukar forge/anvil
    strike.

See ../CLAUDE.md and README.md for the full design notes and variant
table.
"""
from __future__ import annotations

import numpy as np
from scipy import signal

from _common import SR, norm, out_arg, write_wav

rng = np.random.default_rng(10191)


def explosion(dur=2.8, sub_f=50.0):
    """Canonical explosion (kwisatz_haderach / jihad): brown noise
    (integrated white noise, detrended) low-passed at 150 Hz, mixed with
    a sub-sine core falling from `sub_f` Hz toward 22 Hz, a slow 80 ms
    attack and a ~1.8s decay."""
    n = int(dur * SR)
    tt = np.arange(n) / SR
    brown = np.cumsum(rng.standard_normal(n))
    brown -= np.mean(brown)
    brown = signal.sosfilt(signal.butter(2, 150, "low", fs=SR, output="sos"), brown)
    f = 22.0 + (sub_f - 22.0) * np.exp(-tt * 2.0)
    core = np.sin(2 * np.pi * np.cumsum(f) / SR)
    env = (1 - np.exp(-tt / 0.08)) * np.exp(-tt / 1.8)
    x = (0.7 * brown / (np.max(np.abs(brown)) + 1e-12) + 0.7 * core) * env
    return norm(x)


def explosion_arrakeen(dur=3.5, sub_f=55.0):
    """`generate_fall_of_arrakeen.py`'s earlier explosion variant: plain
    white noise low-passed (4th order) at 150 Hz instead of integrated
    brown noise, and the sub-core falls from `sub_f` toward 18 Hz with a
    faster 0.7 Np/s time constant -- a slightly punchier, less rumbly
    explosion than the canonical version."""
    n = int(dur * SR)
    td = np.arange(n) / SR
    sos_e = signal.butter(4, 150, "low", fs=SR, output="sos")
    nz = signal.sosfilt(sos_e, rng.standard_normal(n))
    nz /= np.max(np.abs(nz)) + 1e-12
    env = (1 - np.exp(-td / 0.08)) * np.exp(-td * 1.8)
    f_curve = sub_f * np.exp(-td * 0.7) + 18.0
    sub = np.sin(2 * np.pi * np.cumsum(f_curve) / SR) * env
    x = nz * env + 0.8 * sub
    return norm(x)


def worm_rumble(dur=3.5):
    """The sandworm's sub-bass approach rumble: a sub-sine settling from
    ~55 Hz toward 27 Hz plus a detrended-integrated-noise (brown-ish)
    low rumble (120 Hz low-pass), a slow 0.30s attack and a long, gentle
    0.9 Np/s decay -- built to sit under a track for several seconds
    without spiking."""
    n = int(dur * SR)
    td = np.arange(n) / SR
    f = 27.0 + 28.0 * np.exp(-td * 1.2)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR)
    nz = np.cumsum(rng.standard_normal(n))
    nz -= np.linspace(nz[0], nz[-1], n)
    sos_r = signal.butter(2, 120, "low", fs=SR, output="sos")
    nz = signal.sosfilt(sos_r, nz)
    nz /= np.max(np.abs(nz)) + 1e-12
    env = (1 - np.exp(-td / 0.30)) * np.exp(-td * 0.9)
    x = (0.8 * sub + 0.5 * nz) * env
    return norm(x)


def anvil():
    """The Sardaukar forge/anvil strike: four inharmonic bell-like
    partials (ratios 1, 2.756, 5.404, 8.933) at random phase, plus a
    fast highpassed-noise transient (>400 Hz) for the strike's metallic
    edge, ~0.7s total."""
    n = int(0.70 * SR)
    tt = np.arange(n) / SR
    base = 580.0
    x = np.zeros(n)
    for r, d, g in [(1.0, 18, 1.0), (2.756, 24, 0.55),
                    (5.404, 30, 0.38), (8.933, 36, 0.25)]:
        x += g * np.sin(2 * np.pi * base * r * tt) * np.exp(-tt * d)
    x += 0.35 * signal.sosfilt(signal.butter(2, 400, "high", fs=SR, output="sos"),
                               rng.standard_normal(n)) * np.exp(-tt * 55)
    return norm(x)


if __name__ == "__main__":
    out = out_arg("impact_fx")
    from _common import concat

    demo = concat([explosion(dur=2.0), explosion_arrakeen(dur=2.0),
                   worm_rumble(dur=2.0), anvil()], gap=0.3)
    write_wav(out, demo)
    for x in (explosion(dur=1.0), explosion_arrakeen(dur=1.0),
              worm_rumble(dur=1.0), anvil()):
        assert np.max(np.abs(x)) <= 1.0 + 1e-9
        assert np.isfinite(x).all()
    print("impact_fx.py: peak/finite OK; explosion x2 / worm_rumble / anvil rendered")
