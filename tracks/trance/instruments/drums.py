"""Trance drums & percussion (909 family, psy kit, tech_noir/eisgang signature hits).

Cross-reference: the 909 kick/clap/hat also exist in tracks/dune/instruments (kick.py, drums.py) as tuning variants of the same recipe.

Extracted VERBATIM from the trance track scripts (which are unchanged):
  - `make_kick` <- `lost_v6.py:make_kick` -- 909 kick, canonical
  - `make_hat` <- `lost_v6.py:make_hat` -- closed / open (`open_=True`)
  - `make_clap` <- `lost_v6.py:make_clap` -- Frankfurt clap
  - `make_ride` <- `lost_v6.py:make_ride` -- climax sections only
  - `make_crash` <- `lost_v6.py:make_crash`
  - `make_snare` <- `adrift.py:make_snare` -- exists for the ROLL
  - `make_shaker` <- `nachtkind_v3.py:make_shaker`
  - `make_tom` <- `eisgang_v3.py:make_tom` -- fills only, <=3 per track
  - `make_tick` <- `eisgang_v3.py:make_tick` -- OWNED by eisgang
  - `heart` <- `lost_v6.py:heart` -- breaks only
  - `make_slam` <- `tech_noir_v3.py:make_slam` -- OWNED by tech_noir
  - `make_anvil` <- `tech_noir_v3.py:make_anvil` -- OWNED by tech_noir
  - `make_tap` <- `tech_noir_v3.py:make_tap` -- OWNED by tech_noir
  - `make_kick_psy` <- `maschinenherz.py:make_kick` -- psy kick (maschinenherz / silver_wire)
  - `make_clap_psy` <- `maschinenherz.py:make_clap` -- psy clap
  - `make_zap` <- `maschinenherz.py:make_zap` -- 8-bar phrase punctuation
  - `make_kick_frankfurt` <- `nachtkind_v3.py:make_kick` -- tuning variant: shorter, 48+102 Hz, 1.5-6 kHz click, no sub (nachtkind v1-v3)
  - `make_hat_psy` <- `maschinenherz_v2.py:make_hat` -- tuning variant: 6.5/7 kHz HP, 160 ms open (maschinenherz_v2 / morgenland / silver_wire_v3)

See ../CLAUDE.md and README.md for the sound-ownership / identity rules.
Seed 130 = lost_v6 (the BPM); each script seeds its own, this module seeds once.
"""
from __future__ import annotations

import numpy as np
from scipy import signal

from _common import SR, run_audition

rng = np.random.default_rng(130)


def make_kick():
    n = int(0.42 * SR)
    td = np.arange(n) / SR
    f_curve = 44.0 + 110.0 * np.exp(-td * 55.0)
    body = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    sub = np.sin(2 * np.pi * (37 + 18 * np.exp(-td * 3)) * td) * np.exp(-td * 3.0)
    sos_c = signal.butter(2, [1800, 9000], "bandpass", fs=SR, output="sos")
    click = signal.sosfilt(sos_c, rng.standard_normal(n)) * np.exp(-td * 500)
    click /= np.max(np.abs(click)) + 1e-12
    env = (1 - np.exp(-td / 0.0008)) * np.exp(-td * 8.0)
    x = body * env + 0.55 * sub + 0.45 * click * (1 - np.exp(-td / 0.0008))
    return x / (np.max(np.abs(x)) + 1e-12)


def make_hat(open_=False):
    n = int((0.13 if open_ else 0.04) * SR)
    td = np.arange(n) / SR
    sos_h = signal.butter(4, 7500, "high", fs=SR, output="sos")
    x = signal.sosfilt(sos_h, rng.standard_normal(n)) * np.exp(-td * (26 if open_ else 120))
    return x / (np.max(np.abs(x)) + 1e-12)


def make_clap():
    n = int(0.32 * SR)
    td = np.arange(n) / SR
    sos = signal.butter(2, [900, 5200], "bandpass", fs=SR, output="sos")
    x = np.zeros(n)
    for i, dmp in [(0, 130.0), (1, 130.0), (2, 130.0), (3, 24.0)]:
        i0 = int(i * 0.011 * SR)
        x[i0:] += signal.sosfilt(sos, rng.standard_normal(n - i0)) * np.exp(-td[: n - i0] * dmp)
    return x / (np.max(np.abs(x)) + 1e-12)


def make_ride():
    n = int(0.4 * SR)
    td = np.arange(n) / SR
    nz = rng.standard_normal(n)
    a = signal.butter(2, [4000, 7000], "bandpass", fs=SR, output="sos")
    b = signal.butter(2, [8000, 12000], "bandpass", fs=SR, output="sos")
    x = signal.sosfilt(a, nz) * np.exp(-td * 9) + 0.7 * signal.sosfilt(b, nz) * np.exp(-td * 6)
    x += 0.18 * np.sin(2 * np.pi * 5400 * td) * np.exp(-td * 8)
    return x / (np.max(np.abs(x)) + 1e-12)


def make_crash():
    n = int(2.2 * SR)
    td = np.arange(n) / SR
    x = signal.sosfilt(signal.butter(2, 5000, "high", fs=SR, output="sos"),
                       rng.standard_normal(n)) * np.exp(-td * 2.0)
    x *= 1 - np.exp(-td / 0.002)
    return x / (np.max(np.abs(x)) + 1e-12)


def make_snare():
    n = int(0.22 * SR)
    td = np.arange(n) / SR
    tone = (np.sin(2 * np.pi * 185 * td) + np.sin(2 * np.pi * 330 * td)) * np.exp(-td * 26)
    noise = signal.sosfilt(signal.butter(2, [1500, 9000], "bandpass", fs=SR, output="sos"),
                           rng.standard_normal(n)) * np.exp(-td * 30)
    x = 0.6 * tone + noise
    x *= 1 - np.exp(-td / 0.0008)
    return x / (np.max(np.abs(x)) + 1e-12)


def make_shaker():
    n = int(0.06 * SR)
    td = np.arange(n) / SR
    sos_s = signal.butter(2, [3500, 9500], "bandpass", fs=SR, output="sos")
    x = signal.sosfilt(sos_s, rng.standard_normal(n)) * np.exp(-td * 70)
    return x / (np.max(np.abs(x)) + 1e-12)


def make_tom(f0):
    n = int(0.30 * SR)
    td = np.arange(n) / SR
    f_curve = f0 * 1.6 * np.exp(-td * 9.0) + f0
    body = np.sin(2 * np.pi * np.cumsum(f_curve) / SR) * np.exp(-td * 11.0)
    skin = signal.sosfilt(signal.butter(2, [400, 2500], "bandpass", fs=SR,
                                        output="sos"),
                          rng.standard_normal(n)) * np.exp(-td * 60)
    skin /= np.max(np.abs(skin)) + 1e-12
    x = body + 0.25 * skin
    x *= 1 - np.exp(-td / 0.001)
    return x / (np.max(np.abs(x)) + 1e-12)


def make_tick(fc):
    # the tick pair: a rim/woodblock click — bandpassed snap + a tiny thump
    n = int(0.035 * SR)
    td = np.arange(n) / SR
    sos_c = signal.butter(2, [fc * 0.7, fc * 1.3], "bandpass", fs=SR,
                          output="sos")
    click = signal.sosfilt(sos_c, rng.standard_normal(n)) * np.exp(-td * 300)
    thump = 0.4 * np.sin(2 * np.pi * fc / 3 * td) * np.exp(-td * 180)
    x = click / (np.max(np.abs(click)) + 1e-12) + thump
    x *= 1 - np.exp(-td / 0.0004)
    return x / (np.max(np.abs(x)) + 1e-12)


def heart():
    n = int(0.26 * SR)
    td = np.arange(n) / SR
    f = 32 + 36 * np.exp(-td * 20)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-td * 13)
    body += 0.5 * np.sin(2 * np.pi * 70 * td) * np.exp(-td * 18)
    thud = signal.sosfilt(signal.butter(2, 220, "low", fs=SR, output="sos"),
                          rng.standard_normal(n)) * np.exp(-td * 28)
    x = body / (np.max(np.abs(body)) + 1e-12) + 0.3 * thud / (np.max(np.abs(thud)) + 1e-12)
    x *= 1 - np.exp(-td / 0.004)
    return x / (np.max(np.abs(x)) + 1e-12)


def make_slam():
    n = int(0.55 * SR)
    td = np.arange(n) / SR
    f_curve = 52.0 + 98.0 * np.exp(-td * 26.0)
    body = np.sin(2 * np.pi * np.cumsum(f_curve) / SR) * np.exp(-td * 9.0)
    sos_n = signal.butter(2, [180, 2400], "bandpass", fs=SR, output="sos")
    burst = signal.sosfilt(sos_n, rng.standard_normal(n))
    burst /= np.max(np.abs(burst)) + 1e-12
    x = body + 0.55 * burst * np.exp(-td * 16.0) + 0.30 * burst * np.exp(-td * 3.0)
    gate = np.clip((0.140 - td) / 0.025, 0, 1)            # hard 80s gate
    x *= (1 - np.exp(-td / 0.0015)) * gate
    return x / (np.max(np.abs(x)) + 1e-12)


def make_anvil():
    n = int(4.0 * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    f0 = 410.0
    for i, (ratio, g) in enumerate(zip(
            [1.0, 2.71, 4.07, 5.43, 7.39, 9.21],
            [1.0, 0.78, 0.55, 0.40, 0.26, 0.16])):
        dec = 1.1 + 0.55 * i
        for det in (0.9991, 1.0009):
            x += g * np.sin(2 * np.pi * f0 * ratio * det * td +
                            rng.uniform(0, 2 * np.pi)) * np.exp(-td * dec)
    sos_s = signal.butter(2, [2500, 9000], "bandpass", fs=SR, output="sos")
    strike = signal.sosfilt(sos_s, rng.standard_normal(n)) * np.exp(-td * 280)
    strike /= np.max(np.abs(strike)) + 1e-12
    x = x / (np.max(np.abs(x)) + 1e-12) + 0.7 * strike
    x *= 1 - np.exp(-td / 0.0006)
    return x / (np.max(np.abs(x)) + 1e-12)


def make_tap():
    n = int(0.35 * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    for ratio, g in zip([1.0, 2.89, 5.12], [1.0, 0.5, 0.25]):
        x += g * np.sin(2 * np.pi * 1280.0 * ratio * td +
                        rng.uniform(0, 2 * np.pi)) * np.exp(-td * 14.0)
    sos_s = signal.butter(2, [4000, 10000], "bandpass", fs=SR, output="sos")
    strike = signal.sosfilt(sos_s, rng.standard_normal(n)) * np.exp(-td * 220)
    strike /= np.max(np.abs(strike)) + 1e-12
    x = x / (np.max(np.abs(x)) + 1e-12) + 0.5 * strike
    x *= 1 - np.exp(-td / 0.0006)
    return x / (np.max(np.abs(x)) + 1e-12)


def make_kick_psy():
    n = int(0.30 * SR)
    td = np.arange(n) / SR
    f_curve = 45.0 + 105.0 * np.exp(-td * 55.0)
    body = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    sos_c = signal.butter(2, [1800, 9000], "bandpass", fs=SR, output="sos")
    click = signal.sosfilt(sos_c, rng.standard_normal(n)) * np.exp(-td * 700)
    click /= np.max(np.abs(click)) + 1e-12
    env = (1 - np.exp(-td / 0.0008)) * np.exp(-td * 9.0)
    x = (body + 0.45 * click) * env
    return x / (np.max(np.abs(x)) + 1e-12)


def make_clap_psy():
    n = int(0.26 * SR)
    td = np.arange(n) / SR
    sos_c = signal.butter(2, [900, 5200], "bandpass", fs=SR, output="sos")
    nz = signal.sosfilt(sos_c, rng.standard_normal(n))
    nz /= np.max(np.abs(nz)) + 1e-12
    env = np.zeros(n)
    for i, t0 in enumerate([0.0, 0.011, 0.022, 0.033]):
        i0 = int(t0 * SR)
        rate = 120.0 if i < 3 else 26.0
        seg = (0.65 if i < 3 else 1.0) * np.exp(-(td[i0:] - t0) * rate)
        env[i0:] = np.maximum(env[i0:], seg)
    x = nz * env
    return x / (np.max(np.abs(x)) + 1e-12)


def make_zap():
    n = int(0.40 * SR)
    td = np.arange(n) / SR
    f_curve = 80.0 + 1900.0 * np.exp(-td * 18.0)
    x = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    x *= 1.0 + 0.5 * np.sin(2 * np.pi * 35.0 * td)
    x *= np.exp(-td * 8.0) * (1 - np.exp(-td / 0.002))
    return x / (np.max(np.abs(x)) + 1e-12)


def make_kick_frankfurt():
    n = int(0.26 * SR)
    td = np.arange(n) / SR
    f_curve = 48.0 + 102.0 * np.exp(-td * 50.0)
    body = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    sos_c = signal.butter(2, [1500, 6000], "bandpass", fs=SR, output="sos")
    click = signal.sosfilt(sos_c, rng.standard_normal(n)) * np.exp(-td * 500)
    click /= np.max(np.abs(click)) + 1e-12
    env = (1 - np.exp(-td / 0.001)) * np.exp(-td * 10.0)
    x = (body + 0.30 * click) * env
    return x / (np.max(np.abs(x)) + 1e-12)


def make_hat_psy(open_=False):
    n = int((0.16 if open_ else 0.045) * SR)
    td = np.arange(n) / SR
    sos_h = signal.butter(4, 6500 if open_ else 7000, "high",
                          fs=SR, output="sos")
    x = signal.sosfilt(sos_h, rng.standard_normal(n))
    x *= np.exp(-td * (24 if open_ else 100))
    return x / (np.max(np.abs(x)) + 1e-12)


AUDITION = [
    ("make_kick", lambda: make_kick()),
    ("make_hat closed", lambda: make_hat()),
    ("make_hat open", lambda: make_hat(open_=True)),
    ("make_clap", lambda: make_clap()),
    ("make_ride", lambda: make_ride()),
    ("make_crash", lambda: make_crash()),
    ("make_snare", lambda: make_snare()),
    ("make_shaker", lambda: make_shaker()),
    ("make_tom 110", lambda: make_tom(110.0)),
    ("make_tick 2500", lambda: make_tick(2500.0)),
    ("heart", lambda: heart()),
    ("make_slam", lambda: make_slam()),
    ("make_anvil", lambda: make_anvil()),
    ("make_tap", lambda: make_tap()),
    ("make_kick_psy", lambda: make_kick_psy()),
    ("make_clap_psy", lambda: make_clap_psy()),
    ("make_zap", lambda: make_zap()),
    ("make_kick_frankfurt", lambda: make_kick_frankfurt()),
    ("make_hat_psy open", lambda: make_hat_psy(open_=True)),
]

if __name__ == "__main__":
    run_audition("drums", AUDITION)
