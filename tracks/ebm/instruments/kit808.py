"""TR-808 kit — the interlude drums (Arp (808 Edit), the bookends).

Analog circuits modelled the simple way: the kick is a swept sine, the
snare two tones plus filtered noise, the hats and cowbell are summed
square waves through filters (the 808's six-oscillator metal), the clap
retriggered noise bursts.  Clean by default (hold=1, it is analog);
hold=2 if it went through the sampler.  Mono.

    from kit808 import kick, snare, hat, clap, cowbell, rim, clave, maracas, tom, pattern
"""
from __future__ import annotations

import functools

import numpy as np
from scipy import signal

from _common import SR, audition, bp_noise, dirt, hp_noise, norm, out_arg, place, steps_buffer

_HAT_FREQS = (205.3, 304.4, 369.6, 522.7, 540.0, 800.0)      # the 808 metal


def _finish(x, td, hold):
    x = x * (1 - np.exp(-td / 0.0004))
    return norm(dirt(x, hold=hold) if hold > 1 else x)


@functools.lru_cache(maxsize=None)
def kick(decay=0.45, tone=0.2, f0=48.0, sweep=70.0, hold=1):
    """decay: amplitude time constant (s) — 0.2 tight, 1.0+ the boom;
    tone: harmonic drive; f0/sweep: the pitch (Hz) and the initial drop."""
    n = int(min(decay * 5 + 0.05, 3.0) * SR)
    td = np.arange(n) / SR
    f = f0 + sweep * np.exp(-td * 60)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-td / decay)
    click = 0.25 * np.sin(2 * np.pi * 1200 * td) * np.exp(-td * 900)
    x = (1 - tone) * body + tone * np.tanh(4 * body) + click
    return _finish(x, td, hold)


@functools.lru_cache(maxsize=None)
def snare(snappy=0.6, decay=0.08, hold=1):
    """snappy: noise level; decay: noise time constant (s)."""
    n = int(0.4 * SR)
    td = np.arange(n) / SR
    tone = np.sin(2 * np.pi * 184 * td) * np.exp(-td * 14) + 0.65 * np.sin(2 * np.pi * 331 * td) * np.exp(-td * 20)
    noise = bp_noise(n, 900, 9000) * np.exp(-td / decay)
    return _finish(tone + snappy * 1.4 * noise, td, hold)


@functools.lru_cache(maxsize=None)
def hat(open_=False, decay=None, hold=1):
    """Six squares, highpassed; decay in 1/s (closed ~55, open ~8)."""
    n = int((0.6 if open_ else 0.09) * SR)
    td = np.arange(n) / SR
    x = sum(signal.square(2 * np.pi * f * td) for f in _HAT_FREQS)
    x = signal.sosfilt(signal.butter(4, 6500, "high", fs=SR, output="sos"), x)
    x = norm(x) * np.exp(-td * (decay or (8.0 if open_ else 55.0)))
    return _finish(x, td, hold)


@functools.lru_cache(maxsize=None)
def clap(hold=1):
    n = int(0.3 * SR)
    td = np.arange(n) / SR
    b, a = signal.iirpeak(1100, 2.0, fs=SR)
    nz = norm(signal.lfilter(b, a, bp_noise(n, 600, 3000)))
    env = np.zeros(n)
    for t0 in (0.0, 0.010, 0.020):
        i0 = int(t0 * SR)
        env[i0:] = np.maximum(env[i0:], np.exp(-(td[i0:] - t0) * 300))
    i0 = int(0.030 * SR)
    env[i0:] = np.maximum(env[i0:], 0.55 * np.exp(-(td[i0:] - 0.030) * 18))   # the bursts lead, the tail follows
    return _finish(nz * env, td, hold)


@functools.lru_cache(maxsize=None)
def cowbell(hold=1):
    n = int(0.3 * SR)
    td = np.arange(n) / SR
    x = signal.square(2 * np.pi * 540 * td) + signal.square(2 * np.pi * 800 * td)
    x = norm(signal.sosfilt(signal.butter(2, [400, 2600], "bandpass", fs=SR, output="sos"), x))
    x *= np.exp(-td * 22) + 0.5 * np.exp(-td * 120)
    return _finish(x, td, hold)


@functools.lru_cache(maxsize=None)
def rim(hold=1):
    n = int(0.08 * SR)
    td = np.arange(n) / SR
    x = (np.sin(2 * np.pi * 1750 * td) * np.exp(-td * 200) + 0.7 * np.sin(2 * np.pi * 500 * td) * np.exp(-td * 80)
         + 0.6 * bp_noise(n, 1000, 4000) * np.exp(-td * 400))
    return _finish(x, td, hold)


@functools.lru_cache(maxsize=None)
def clave(hold=1):
    n = int(0.06 * SR)
    td = np.arange(n) / SR
    return _finish(np.sin(2 * np.pi * 2500 * td) * np.exp(-td * 120), td, hold)


@functools.lru_cache(maxsize=None)
def maracas(hold=1):
    n = int(0.05 * SR)
    td = np.arange(n) / SR
    return _finish(hp_noise(n, 5000) * np.exp(-td * 120), td, hold)


@functools.lru_cache(maxsize=None)
def tom(f0=80.0, decay=0.25, hold=1):
    """f0 80 lo / 120 mid / 165 hi (the 808 toms, conga-ish higher)."""
    n = int((decay * 5 + 0.05) * SR)
    td = np.arange(n) / SR
    f = f0 * (1 + 0.5 * np.exp(-td * 30))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-td / decay)
    x += 0.15 * bp_noise(n, 300, 1500) * np.exp(-td * 40)
    return _finish(x, td, hold)


PATTERN = {                      # two bars; the interlude backbeat
    "kick":    "x...x...x...x..." "x...x...x...x.x.",
    "snare":   "....x.......x..." "....x.......x...",
    "ch":      "x.x.x.x.x.x.x.x." "x.x.x.x.x.x.x.x.",
    "oh":      "......x.......x." "......x.......x.",
    "cowbell": "................" "..x...x...x...x.",
    "clave":   "................" "...x......x.....",
    "maracas": "..x...x...x...x." "..x...x...x...x.",
}
GAIN = {"kick": 1.0, "snare": 0.8, "ch": 0.35, "oh": 0.4, "cowbell": 0.5, "clave": 0.4, "maracas": 0.2}


def pattern(bars=2, hold=1, steps=PATTERN, gain=GAIN):
    """Render a step pattern dict (16 steps per bar per line)."""
    hits = {"kick": kick(hold=hold), "snare": snare(hold=hold), "ch": hat(hold=hold),
            "oh": hat(open_=True, hold=hold), "cowbell": cowbell(hold=hold),
            "clave": clave(hold=hold), "maracas": maracas(hold=hold)}
    buf = steps_buffer(bars)
    for name, line in steps.items():
        for s in range(bars * 16):
            if line[s % len(line)] == "x":
                g = gain[name] * (1.0 if s % 4 == 0 else 0.7)
                place(buf, hits[name], s, g)
    return buf


if __name__ == "__main__":
    out = out_arg("kit808")
    hits = [("kick (decay 0.45)", kick()),
            ("kick tight (0.2)", kick(decay=0.2)),
            ("kick boom (1.2, tone 0.4)", kick(decay=1.2, tone=0.4)),
            ("snare", snare()),
            ("snare dry (snappy 0.2)", snare(snappy=0.2)),
            ("closed hat", hat()),
            ("open hat", hat(open_=True)),
            ("clap", clap()),
            ("cowbell", cowbell()),
            ("rim", rim()),
            ("clave", clave()),
            ("maracas", maracas()),
            ("toms lo/mid/hi", np.concatenate([tom(80.0), tom(120.0), tom(165.0)])),
            ("sampled kick+snare (hold 2)", np.concatenate([kick(hold=2), snare(hold=2)]))]
    for label, h in hits:
        assert abs(np.max(np.abs(h)) - 1) < 1e-6 and np.all(np.isfinite(h)), label
    audition("kit808", hits, [("LOOP pattern, 4 bars", pattern(4))], out=out)
