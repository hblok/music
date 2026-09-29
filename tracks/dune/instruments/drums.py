"""Western-style drum-kit elements shared across the Dune war-psy tracks:
war drum, tom, hi-hat, snare (with field-snare march helper), clap and
shaker. (Darbuka lives in `darbuka.py`; kicks in `kick.py`.)

Extracted from (canonical version -- see README.md for the per-file hash
table):
  - `war_drum()`  <- `generate_water_of_life.py:make_war_drum` (matches
    fall_of_arrakeen, kanly, kwisatz_haderach, maker_comes, muaddib,
    night_pursuit, sihaya, sleeper_awakens verbatim). `jihad.py` carries a
    faster/brighter variant, exposed via parameters.
  - `tom()`       <- `generate_kwisatz_haderach.py:make_tom` (identical in
    muaddib and jihad; fall_of_arrakeen's is a close cousin, exposed via
    parameters).
  - `hat()`       <- `generate_fall_of_arrakeen.py:make_hat` (closed/open
    highpassed-noise hat; near-identical in kwisatz_haderach and
    sleeper_awakens).
  - `snare()`     <- `generate_fall_of_arrakeen.py:make_snare` (the field
    snare: bandpassed-noise body + a two-tone 185/330 Hz thump; identical
    in kwisatz_haderach, close in jihad) plus `snare_march_bar()`, the
    march pattern + buzz-roll-every-4th-bar helper from the same script.
  - `clap()`      <- `generate_fall_of_arrakeen.py:make_clap` (four
    micro-delayed bursts; identical in kwisatz_haderach).
  - `shaker()`    <- `generate_fall_of_arrakeen.py:make_shaker`.
"""
from __future__ import annotations

import numpy as np
from scipy import signal

from _common import SR, add_at, norm, out_arg, write_wav

rng = np.random.default_rng(10193)   # the fall_of_arrakeen / kwisatz seed

# the field-snare march cell (16th-step index, gain, is-accent) used by
# `snare_march_bar` -- the "PREPARATION" march identity of Fall of Arrakeen.
MARCH = [(0, 1.0, True), (4, 0.6, False), (6, 0.6, False),
         (8, 1.0, True), (12, 0.6, False), (14, 0.75, False)]


def war_drum(dur=0.9, f0=42.0, f1=48.0, sweep=9.0, skin_band=(100, 420),
             skin_gain=0.5, decay=5.5):
    """Taiko-like war drum: sine body falling (f0+f1) -> f0 Hz plus
    bandpassed skin-noise slap, shared decay envelope. `jihad.py` uses a
    faster/brighter variant (f0=42, f1=48 sweep=9 dur=0.7, skin band
    100-420 at gain 0.40, decay 5.5, extra 6 ms attack) -- pass those to
    approximate it; defaults here match the 9 other generators."""
    n = int(dur * SR)
    td = np.arange(n) / SR
    f_curve = f0 + f1 * np.exp(-td * sweep)
    body = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    sos_sk = signal.butter(2, list(skin_band), "bandpass", fs=SR, output="sos")
    skin = signal.sosfilt(sos_sk, rng.standard_normal(n)) * np.exp(-td * 22)
    skin = norm(skin)
    env = np.exp(-td * decay) * (1 - np.exp(-td / 0.006))
    x = body * env + skin_gain * skin * env
    return norm(x)


def tom(f0, dur=0.38, detune=0.40, detune_decay=40.0, body_decay=8.5,
        skin_band=(300, 1500), skin_gain=0.35, skin_decay=22.0):
    """Battle tom: falling-pitch sine body (starts detune*100% sharp,
    settles to f0) plus bandpassed skin noise. Pass f0 in {165, 110, 80}
    Hz for the syncopated battle-tom pattern (fall_of_arrakeen)."""
    n = int(dur * SR)
    td = np.arange(n) / SR
    f = f0 * (1.0 + detune * np.exp(-td * detune_decay))
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-td * body_decay)
    sos_sk = signal.butter(2, list(skin_band), "bandpass", fs=SR, output="sos")
    skin = signal.sosfilt(sos_sk, rng.standard_normal(n)) * np.exp(-td * skin_decay)
    x = body + skin_gain * skin
    return norm(x)


def hat(open_=False, dur=None, hp=None, decay=None):
    """Closed (default 45 ms, 7 kHz HP, decay 100/s) or open (160 ms,
    6.5 kHz HP, decay 24/s) hat -- highpassed noise, mono."""
    dur = dur if dur is not None else (0.16 if open_ else 0.045)
    hp = hp if hp is not None else (6500 if open_ else 7000)
    decay = decay if decay is not None else (24 if open_ else 100)
    n = int(dur * SR)
    td = np.arange(n) / SR
    sos_h = signal.butter(4, hp, "high", fs=SR, output="sos")
    x = signal.sosfilt(sos_h, rng.standard_normal(n))
    x *= np.exp(-td * decay)
    return norm(x)


def snare(buzz=False, tone_freqs=(185.0, 330.0), noise_band=(1500, 9000)):
    """The field snare: bandpassed-noise body (1500-9000 Hz) plus a
    two-tone 185/330 Hz thump. `buzz=True` gives the short (70 ms), fast
    -decaying buzz-drag ghost stroke used before accents and in the
    buzz-roll crescendo."""
    n = int((0.07 if buzz else 0.17) * SR)
    td = np.arange(n) / SR
    sos_n = signal.butter(2, list(noise_band), "bandpass", fs=SR, output="sos")
    nz = norm(signal.sosfilt(sos_n, rng.standard_normal(n)))
    tone = (np.sin(2 * np.pi * tone_freqs[0] * td) +
            0.7 * np.sin(2 * np.pi * tone_freqs[1] * td)) * np.exp(-td * 40)
    env = np.exp(-td * (70.0 if buzz else 26.0)) * (1 - np.exp(-td / 0.001))
    x = (0.8 * nz + 0.5 * tone) * env
    return norm(x)


def snare_march_bar(lay_L, lay_R, bar_t0, beat, snare_hit, buzz_hit,
                     bar_index=0, level=1.0):
    """Place one bar of the field-snare march (see MARCH above) into
    stereo layer buffers at `bar_t0`. `bar_index % 4 == 3` triggers the
    buzz-roll crescendo across beats 3-4 instead of the plain march --
    the section-identity gesture from Fall of Arrakeen."""
    step = beat / 4.0
    roll_bar = bar_index % 4 == 3
    for s, g, acc in MARCH:
        if roll_bar and s >= 12:
            break
        st = bar_t0 + s * step
        if acc:
            add_at(lay_L, buzz_hit, st - 0.060, 0.30 * level)
            add_at(lay_L, buzz_hit, st - 0.030, 0.35 * level)
            add_at(lay_R, buzz_hit, st - 0.060, 0.25 * level)
            add_at(lay_R, buzz_hit, st - 0.030, 0.30 * level)
        add_at(lay_L, snare_hit, st, g * level * 0.95)
        add_at(lay_R, snare_hit, st, g * level * 0.80)
    if roll_bar:
        for i in range(8):
            st = bar_t0 + (3.0 + i * 0.125) * step * 4
            g = (0.3 + 0.7 * i / 7) * level
            add_at(lay_L, buzz_hit, st, g * 0.9)
            add_at(lay_R, buzz_hit, st, g * 0.75)


def clap(bursts=((0.000, 130), (0.011, 130), (0.022, 130), (0.036, 24)),
         band=(900, 5200), dur=0.32):
    """The Frankfurt clap: 4 micro-delayed bandpassed-noise bursts, the
    last ringing longer (24/s vs 130/s) for the wet tail. Identical
    across fall_of_arrakeen and kwisatz_haderach."""
    n = int(dur * SR)
    td = np.arange(n) / SR
    sos = signal.butter(2, list(band), "bandpass", fs=SR, output="sos")
    x = np.zeros(n)
    for i, dmp in enumerate(f for _, f in bursts):
        i0 = int(bursts[i][0] * SR)
        x[i0:] += signal.sosfilt(sos, rng.standard_normal(n - i0)) * np.exp(-td[: n - i0] * dmp)
    return norm(x)


def shaker(dur=0.055, band=(3500, 9500), decay=85.0):
    """Bandpassed-noise shaker tick -- 16th-note groove texture, gain
    cycle [.9,.4,.65,.4] in the source tracks."""
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = signal.sosfilt(signal.butter(2, list(band), "bandpass", fs=SR, output="sos"),
                        rng.standard_normal(n))
    x *= np.exp(-td * decay)
    return norm(x)


if __name__ == "__main__":
    out = out_arg("drums")
    from _common import BEAT, concat

    wd = war_drum()
    t165, t110, t80 = tom(165.0), tom(110.0), tom(80.0)
    hc, ho = hat(), hat(open_=True)
    sn, bz = snare(), snare(buzz=True)
    cl = clap()
    sh = shaker()

    hits = [wd, t165, t110, t80, hc, ho, sn, bz, cl, sh]
    demo = concat(hits, gap=0.12)

    # 2-bar march demo (bar 4 = the buzz-roll bar); a 0.1 s lead-in keeps
    # the accent's pre-roll (-60 ms) from indexing before the buffer start
    lead = 0.1
    bar_len = 4 * BEAT
    m_L = np.zeros(int((lead + 2 * bar_len) * SR) + len(sn))
    m_R = np.zeros_like(m_L)
    snare_march_bar(m_L, m_R, lead, BEAT, sn, bz, bar_index=2, level=0.9)
    snare_march_bar(m_L, m_R, lead + bar_len, BEAT, sn, bz, bar_index=3, level=0.9)
    demo = concat([demo, norm(m_L)], gap=0.2)

    write_wav(out, demo)
    for x in hits:
        assert np.max(np.abs(x)) <= 1.0 + 1e-6
        assert np.isfinite(x).all()
    print("drums.py: peak/finite OK for all hits; march bar rendered")
