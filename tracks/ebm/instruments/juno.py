"""Juno-60 voice — the goth colour: chorused pad, gated offbeat stab, arp.

One DCO voice (saw + sub-octave square) into a resonant lowpass with an
optional pluck envelope, an attack/release envelope, and the Juno chorus
(two short delays modulated in anti-phase at ~0.5 Hz — the BBD).  Six
voices on the real thing: keep voicings to 2-4 notes.  Mono out; a track
pans or widens.  No sampler dirt by default (the Juno went to tape).

    from juno import pad, stab, arp
    p = pad((57, 60, 64), 4 * BEAT)          # Am, one bar
    s = stab((69, 72, 76))                   # Am, high, gated
    buf = arp((57, 60, 64), bars=2)          # 16th arpeggio, 2 bars
"""
from __future__ import annotations

import functools

import numpy as np
from scipy import signal

from _common import BEAT, SR, STEP, audition, dirt, midi_to_hz, norm, out_arg, place, steps_buffer
from sh101_bass import svf_lowpass

AM, F, G = (57, 60, 64), (53, 57, 60), (55, 59, 62)     # the i-VI-VII loop, mid register


def chorus(x, depth=1.0, rate=0.5, base_ms=2.5, mod_ms=1.2):
    """The Juno BBD chorus: dry + two delay taps modulated in anti-phase."""
    n = len(x)
    t = np.arange(n) / SR
    idx = np.arange(n, dtype=float)
    out = x.copy()
    for phase in (0.0, np.pi):
        d = (base_ms + mod_ms * np.sin(2 * np.pi * rate * t + phase)) * SR / 1000.0
        out += 0.5 * depth * np.interp(idx - d, idx, x)
    return out


@functools.lru_cache(maxsize=None)
def voice(notes, dur, attack=0.02, release=0.08, cutoff=1200.0, pluck=0.0, env=0.08,
          res=1.0, sub=0.3, depth=1.0, hold=1):
    """One chord event.  notes: tuple of midi; dur: sounding length (s);
    attack/release: raised-cosine in, exp out; cutoff: 24 dB lowpass floor
    (Hz); pluck: Hz added at the attack, decaying with `env`; res: filter Q;
    sub: sub-octave square mix; depth: chorus amount (0 = off); hold: sampler
    dirt.  Cached — do not modify the result."""
    n = int((dur + 4 * release) * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    for m in notes:
        f = midi_to_hz(m)
        ph = 2 * np.pi * f * td
        x += sum(np.sin(k * ph) / k ** 1.1 for k in range(1, min(40, int(9000 / f)) + 1))
        x += sub * signal.square(ph / 2)
    fc = cutoff + pluck * np.exp(-td / env)
    y = svf_lowpass(norm(x), fc, res)
    y = svf_lowpass(y, fc, 0.7)                       # second 12 dB stage = the 24 dB Juno slope
    a = 0.5 - 0.5 * np.cos(np.pi * np.clip(td / max(attack, 1e-4), 0, 1))
    r = np.where(td < dur, 1.0, np.exp(-(td - dur) / max(release, 1e-4)))
    y = chorus(y * a * r, depth)
    return norm(dirt(y, hold=hold) if hold > 1 else y)


def pad(notes, dur, **kw):
    """Sustained chorused pad: slow attack, long release, dark."""
    kw = {"attack": 0.4, "release": 0.6, "cutoff": 1000.0, **kw}
    return voice(tuple(notes), dur, **kw)


def stab(notes, dur=STEP * 1.2, **kw):
    """The offbeat stab: instant attack, plucked filter, short gate."""
    kw = {"attack": 0.003, "release": 0.03, "cutoff": 700.0, "pluck": 2200.0, "env": 0.06, **kw}
    return voice(tuple(notes), dur, **kw)


def arp(notes, bars=2, octaves=2, pattern="up", gate_frac=0.5, **kw):
    """The Juno arpeggiator: 16ths cycling `notes` over `octaves`, up or
    updown; each step a plucked single note."""
    seq = [m + 12 * o for o in range(octaves) for m in notes]
    if pattern == "updown":
        seq = seq + seq[-2:0:-1]
    kw = {"attack": 0.002, "release": 0.04, "cutoff": 600.0, "pluck": 1800.0, "env": 0.08, "sub": 0.0, **kw}
    buf = steps_buffer(bars)
    for s in range(bars * 16):
        place(buf, voice((seq[s % len(seq)],), STEP * gate_frac, **kw), s)
    return buf


def stab_loop(chords=(AM, F, G, AM), steps=(2, 6, 10, 14), **kw):
    """One bar per chord, stabs on the off-8ths."""
    buf = steps_buffer(len(chords))
    for b, ch in enumerate(chords):
        x = stab(ch, **kw)
        for s in steps:
            place(buf, x, b * 16 + s)
    return buf


def pad_loop(chords=(AM, F, G, AM), **kw):
    buf = steps_buffer(len(chords))
    for b, ch in enumerate(chords):
        place(buf, pad(ch, 4 * BEAT, **kw), b * 16)
    return buf


if __name__ == "__main__":
    out = out_arg("juno")
    hits = [pad(AM, 2.0),                               # the pad, Am, 2 s
            pad(AM, 2.0, depth=0.0),                    # same without chorus (hear what it adds)
            pad((45, 52, 57, 60), 2.0, cutoff=700.0),   # low, dark, four notes
            stab((69, 72, 76)),                         # high stab
            stab(AM, res=2.5),                          # mid stab, more bite
            stab(AM, hold=2)]                           # sampled stab (EPS)
    for h in hits:
        assert abs(np.max(np.abs(h)) - 1) < 1e-6 and np.all(np.isfinite(h))
    loop = np.concatenate([stab_loop(), arp(AM), arp(AM, pattern="updown", octaves=1), pad_loop()])
    audition("juno", hits, loop, out=out)
