"""Goa kit: 95->48 Hz kick, sparse hats, snare.


Extracted VERBATIM from the goa/psy track scripts (which are unchanged):
  - `goa_kick` <- `phototaxis_v2.py:goa_kick` -- 95->48 Hz in ~35 ms (not the trance 150->45 dive) -- phototaxis v1/v2 agree
  - `goa_kick_meridian` <- `meridian.py:goa_kick` -- meridian tuning
  - `open_hat` <- `phototaxis_v2.py:open_hat` -- identical in all three
  - `closed_hat` <- `phototaxis_v2.py:closed_hat` -- identical in all three
  - `snare` <- `phototaxis_v2.py:snare` -- identical in all three

See ../CLAUDE.md and README.md for the identity rules.
Seed 1995 = phototaxis seed (the year); each module seeds once.
"""
from __future__ import annotations

import numpy as np
from scipy import signal

from _common import SR, highpass, run_audition

rng = np.random.default_rng(1995)


# ------------------------------------------------------------- the kit
def goa_kick():
    n = int(0.14 * SR)
    td = np.arange(n) / SR
    f = 48.0 + 47.0 * np.exp(-td / 0.012)               # 95→48 in ~35 ms
    y = np.sin(2 * np.pi * np.cumsum(f) / SR)
    y *= np.exp(-td / 0.055) * np.clip((0.13 - td) / 0.012, 0, 1)
    click = rng.standard_normal(int(0.004 * SR))
    click = highpass(click, 2500) * np.exp(-np.arange(len(click)) / SR / 0.001)
    y[: len(click)] += 0.35 * click / (np.max(np.abs(click)) + 1e-12)
    return y / (np.max(np.abs(y)) + 1e-12)


# ------------------------------------------------------------- the kit
def goa_kick_meridian():
    """HEAVY goa kick (Q3 night-goa): bigger/darker than phototaxis's tight
    95->48 — 102->42, a longer body and a sustained sub tail for weight."""
    n = int(0.20 * SR)
    td = np.arange(n) / SR
    f = 42.0 + 60.0 * np.exp(-td / 0.014)               # 102->42 in ~40 ms
    y = np.sin(2 * np.pi * np.cumsum(f) / SR)
    y *= np.exp(-td / 0.080) * np.clip((0.19 - td) / 0.014, 0, 1)
    y += 0.35 * np.sin(2 * np.pi * 41.0 * td) * np.exp(-td / 0.10)  # sub tail
    click = rng.standard_normal(int(0.004 * SR))
    click = highpass(click, 2400) * np.exp(-np.arange(len(click)) / SR / 0.001)
    y[: len(click)] += 0.30 * click / (np.max(np.abs(click)) + 1e-12)
    return y / (np.max(np.abs(y)) + 1e-12)


def open_hat():
    n = int(0.20 * SR)
    y = highpass(rng.standard_normal(n), 6000)
    y *= np.exp(-np.arange(n) / SR / 0.075)
    return y / (np.max(np.abs(y)) + 1e-12)


def closed_hat():
    n = int(0.035 * SR)
    y = highpass(rng.standard_normal(n), 7500)
    y *= np.exp(-np.arange(n) / SR / 0.012)
    return y / (np.max(np.abs(y)) + 1e-12)


def snare():
    n = int(0.13 * SR)
    td = np.arange(n) / SR
    noise = rng.standard_normal(n)
    b, a = signal.butter(2, [400 / (SR / 2), 6500 / (SR / 2)], "band")
    y = signal.lfilter(b, a, noise) + 0.25 * np.sin(2 * np.pi * 190 * td)
    y *= np.exp(-td / 0.045)
    return y / (np.max(np.abs(y)) + 1e-12)


AUDITION = [
    ("goa_kick", lambda: goa_kick()),
    ("goa_kick_meridian", lambda: goa_kick_meridian()),
    ("open_hat", lambda: open_hat()),
    ("closed_hat", lambda: closed_hat()),
    ("snare", lambda: snare()),
]

if __name__ == "__main__":
    run_audition("drums", AUDITION)
