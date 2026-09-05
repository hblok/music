"""Juno-60 voice — the goth colour: pads, strings, stabs, organ, brass,
bass, lead, zaps, noise sweeps, and the arpeggiator.

One DCO voice (saw / square / pulse / PWM pulse + sub-octave square +
noise) into the 24 dB resonant lowpass (two SVF stages) with a filter
ENVELOPE (pluck, attack-bloom, sweep, keyboard tracking), the 4-position
HPF, an attack/release amp envelope, the LFO on pitch (delayed vibrato),
and the Juno chorus (I / II / I+II — two BBD taps modulated in
anti-phase).  Six voices on the real thing: keep voicings to 2-4 notes.
Mono out; a track pans or widens.  No sampler dirt by default (the Juno
went to tape).  No portamento, no sync, no FM — the 60 had none.

    from juno import pad, strings, stab, organ, brass, bass, lead, zap, noise_sweep, arp
    p = pad((57, 60, 64), 4 * BEAT)            # Am, one bar
    s = strings((57, 60, 64), 4 * BEAT)        # the PWM strings
    buf = arp((57, 60, 64), bars=2)            # 16th arpeggio, 2 bars
"""
from __future__ import annotations

import functools
import inspect

import numpy as np
from scipy import signal

import _common
from _common import BAR, BEAT, SR, STEP, audition, dirt, midi_to_hz, norm, out_arg, place, steps_buffer
from sh101_bass import svf_lowpass

AM, F, G = (57, 60, 64), (53, 57, 60), (55, 59, 62)     # the i-VI-VII loop, mid register
_HPF_HZ = (150.0, 400.0, 900.0)                        # the 4-position HPF (0 = off)
_CHORUS = {"I": [(0.5, 1.2)], "II": [(0.83, 1.5)], "I+II": [(0.5, 1.2), (0.83, 1.5)]}


def chorus(x, depth=1.0, mode="I", base_ms=2.5, phase=0.0):
    """The Juno BBD chorus: dry + two delay taps modulated in anti-phase.
    mode I ~0.5 Hz, II ~0.83 Hz, I+II both LFOs at once.  The real
    output is stereo with the modulation inverted between channels:
    render L with phase=0 and R with phase=np.pi from the same dry."""
    n = len(x)
    t = np.arange(n) / SR
    idx = np.arange(n, dtype=float)
    out = x.copy()
    for ph0 in (0.0, np.pi):
        d = base_ms + sum(m * np.sin(2 * np.pi * r * t + ph0 + phase) for r, m in _CHORUS[mode])
        out += 0.5 * depth * np.interp(idx - d * SR / 1000.0, idx, x)
    return out


def _osc(wave, ph, f, td, pwm):
    if wave == "saw":
        return sum(np.sin(k * ph) / k ** 1.1 for k in range(1, min(40, int(9000 / f)) + 1))
    if wave == "square":
        return sum(np.sin(k * ph) / k for k in range(1, min(40, int(9000 / f)) + 1, 2))
    if wave == "pulse":
        return signal.square(ph, duty=0.25)
    rate, dep = pwm or (0.6, 0.6)                                  # "pwm": the LFO on the width
    duty = 0.5 + 0.45 * dep * signal.sawtooth(2 * np.pi * rate * td, 0.5)
    return signal.square(ph, duty=duty)


@functools.lru_cache(maxsize=None)
def voice(notes, dur, attack=0.02, release=0.08, cutoff=1200.0, pluck=0.0, env=0.08,
          res=1.0, sub=0.3, depth=1.0, hold=1, wave="saw", pwm=None, noise=0.0, hpf=0,
          fatt=0.0, sweep=None, track=0.0, vib=None, mode="I"):
    """One chord event.  notes: tuple of midi (empty = noise only); dur:
    sounding length (s).  Amp: attack (raised-cosine) / release (exp).
    Filter: cutoff floor (Hz); pluck Hz added at the attack decaying with
    `env`; fatt = filter attack (s, the pad bloom); sweep = (f0, f1) Hz
    exponential over dur (overrides cutoff); track 0-1 = keyboard tracking
    re A3; res = Q.  Source: wave 'saw'|'square'|'pulse'|'pwm' (pwm=(rate,
    depth)), sub = sub-octave square mix, noise 0-1, hpf 0-3.  vib =
    (rate, cents, delay s) LFO to pitch.  depth/mode = chorus.  hold =
    sampler dirt.  Cached — do not modify the result."""
    n = int((dur + 4 * release) * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    for m in notes:
        f = midi_to_hz(m)
        if vib:
            rate, cents, delay = vib
            ramp = 1 - np.exp(-td / delay) if delay > 0 else 1.0
            ft = f * (1 + (2 ** (cents / 1200) - 1) * ramp * np.sin(2 * np.pi * rate * td))
            ph = 2 * np.pi * np.cumsum(ft) / SR
        else:
            ph = 2 * np.pi * f * td
        x += _osc(wave, ph, f, td, pwm)
        x += sub * signal.square(ph / 2)
    if notes:
        x = norm(x)
    if noise:
        x += noise * _common.rng.standard_normal(n)
    fmean = np.mean([midi_to_hz(m) for m in notes]) if notes else 220.0
    if sweep:
        fc = sweep[0] * (sweep[1] / sweep[0]) ** np.clip(td / dur, 0, 1)
    else:
        fc = np.full(n, cutoff * (fmean / 220.0) ** track)
    if fatt > 0:
        fc = fc * (0.2 + 0.8 * (1 - np.exp(-td / fatt)))
    fc = fc + pluck * np.exp(-td / env)
    y = svf_lowpass(x, fc, res)
    y = svf_lowpass(y, fc, 0.7)                       # second 12 dB stage = the 24 dB Juno slope
    if hpf:
        y = signal.sosfilt(signal.butter(2, _HPF_HZ[hpf - 1], "high", fs=SR, output="sos"), y)
    a = 0.5 - 0.5 * np.cos(np.pi * np.clip(td / max(attack, 1e-4), 0, 1))
    r = np.where(td < dur, 1.0, np.exp(-(td - dur) / max(release, 1e-4)))
    y = chorus(y * a * r, depth, mode) if depth > 0 else y * a * r
    return norm(dirt(y, hold=hold) if hold > 1 else y)


# ----------------------------------------------------------- presets
def _preset(defaults):
    """Turn a documented stub into voice() with these defaults; keeps the
    stub's own `dur` default (stab, bass, zap have one)."""
    def wrap(fn):
        dur_default = inspect.signature(fn).parameters["dur"].default

        @functools.wraps(fn)
        def inner(notes, dur=dur_default, **kw):
            notes = tuple(notes) if not isinstance(notes, int) else (notes,)
            return voice(notes, dur, **{**defaults, **kw})
        return inner
    return wrap


@_preset({"attack": 0.4, "release": 0.6, "cutoff": 1000.0})
def pad(notes, dur):
    """Sustained chorused saw pad: slow attack, long release, dark.
    fatt=1.5 for the bloom."""


@_preset({"attack": 0.35, "release": 0.6, "cutoff": 1600.0, "wave": "pwm", "pwm": (0.7, 0.7),
          "sub": 0.0, "hpf": 2})
def strings(notes, dur):
    """The Juno strings: PWM pulse, no sub, HPF up, chorus."""


@_preset({"attack": 0.003, "release": 0.03, "cutoff": 700.0, "pluck": 2200.0, "env": 0.06})
def stab(notes, dur=STEP * 1.2):
    """The offbeat stab: instant attack, plucked filter, short gate."""


@_preset({"attack": 0.004, "release": 0.02, "cutoff": 2600.0, "wave": "square", "sub": 0.6, "hpf": 1})
def organ(notes, dur):
    """Church organ: square + sub, no filter envelope, HPF thinned."""


@_preset({"attack": 0.07, "release": 0.1, "cutoff": 800.0, "pluck": 1400.0, "env": 0.3,
          "res": 1.2, "sub": 0.25, "depth": 0.6})
def brass(notes, dur):
    """Brass: saw, medium attack, slow filter decay, light chorus."""


@_preset({"attack": 0.003, "release": 0.03, "cutoff": 350.0, "pluck": 1400.0, "env": 0.1,
          "res": 1.5, "sub": 0.7, "depth": 0.0})
def bass(notes, dur=STEP):
    """The synth-pop Juno bass: saw + big sub, plucked, no chorus."""


@_preset({"attack": 0.02, "release": 0.12, "cutoff": 1500.0, "pluck": 900.0, "env": 0.2,
          "res": 1.3, "sub": 0.15, "hpf": 1, "vib": (5.5, 10.0, 0.35)})
def lead(notes, dur):
    """Lead with the delayed LFO vibrato (5.5 Hz, 10 cents, 0.35 s in)."""


@_preset({"attack": 0.001, "release": 0.02, "cutoff": 120.0, "pluck": 5000.0, "env": 0.025,
          "res": 14.0, "sub": 0.0, "depth": 0.0})
def zap(notes, dur=0.12):
    """Resonance at self-oscillation + a fast envelope: the pew."""


def noise_sweep(dur=2 * BAR, f0=200.0, f1=6000.0, res=3.0, **kw):
    """The noise source through the swept filter: the swell / riser
    (f0 < f1) or the downsweep (f0 > f1)."""
    kw = {"attack": 0.01, "release": 0.05, "noise": 1.0, "sweep": (f0, f1), "res": res,
          "sub": 0.0, "depth": 0.0, **kw}
    return voice((), dur, **kw)


# ----------------------------------------------------------- sequences
def arp(notes, bars=2, octaves=2, pattern="up", rate=1, gate_frac=0.5, **kw):
    """The Juno arpeggiator: `notes` over `octaves`, pattern up | down |
    updown | random, one note per `rate` 16ths (2 = 8ths); plucked,
    keyboard-tracked so the top brightens."""
    seq = [m + 12 * o for o in range(octaves) for m in notes]
    if pattern == "down":
        seq = seq[::-1]
    elif pattern == "updown":
        seq = seq + seq[-2:0:-1]
    kw = {"attack": 0.002, "release": 0.04, "cutoff": 600.0, "pluck": 1800.0, "env": 0.08,
          "sub": 0.0, "track": 0.6, **kw}
    buf = steps_buffer(bars)
    for i, s in enumerate(range(0, bars * 16, rate)):
        m = int(_common.rng.choice(seq)) if pattern == "random" else seq[i % len(seq)]
        place(buf, voice((m,), STEP * rate * gate_frac, **kw), s)
    return buf


def stab_loop(chords=(AM, F, G, AM), steps=(2, 6, 10, 14), **kw):
    """One bar per chord, stabs on the off-8ths."""
    buf = steps_buffer(len(chords))
    for b, ch in enumerate(chords):
        x = stab(ch, **kw)
        for s in steps:
            place(buf, x, b * 16 + s)
    return buf


def pad_loop(chords=(AM, F, G, AM), fn=pad, **kw):
    """One chord per bar, sustained (fn = pad | strings | organ | brass)."""
    buf = steps_buffer(len(chords))
    for b, ch in enumerate(chords):
        place(buf, fn(ch, 4 * BEAT, **kw), b * 16)
    return buf


def bass_loop(root=45, bars=2, cell="x.x.x.x.x.x.x.o.", **kw):
    """The Juno bass on gated 8ths (the sh101 stomp cell)."""
    buf = steps_buffer(bars)
    for b in range(bars):
        for s, ch in enumerate(cell):
            if ch != ".":
                place(buf, bass(root + (12 if ch == "o" else 0), STEP, **kw), b * 16 + s)
    return buf


if __name__ == "__main__":
    out = out_arg("juno")
    hits = [("pad Am", pad(AM, 2.0)),
            ("pad Am, no chorus", pad(AM, 2.0, depth=0.0)),
            ("pad low dark, 4 notes", pad((45, 52, 57, 60), 2.0, cutoff=700.0)),
            ("pad BLOOM (fatt 1.5, cutoff 1600)", pad(AM, 3.0, fatt=1.5, cutoff=1600.0)),
            ("strings PWM Am", strings(AM, 3.0)),
            ("strings PWM, chorus I+II, slower PWM", strings(AM, 3.0, mode="I+II", pwm=(0.3, 0.8))),
            ("organ Am (4 notes)", organ((57, 60, 64, 69), 1.5)),
            ("brass Am", brass(AM, 0.8)),
            ("bass A2, A1", np.concatenate([bass(45), np.zeros(int(0.1 * SR)), bass(33)])),
            ("lead A4 vibrato", lead(69, 1.5)),
            ("lead A4 vibrato, chorus II", lead(69, 1.5, mode="II")),
            ("stab high", stab((69, 72, 76))),
            ("stab mid, res 2.5", stab(AM, res=2.5)),
            ("stab sampled (hold 2)", stab(AM, hold=2)),
            ("zap A4, A3", np.concatenate([zap(69), np.zeros(int(0.1 * SR)), zap(57)])),
            ("noise sweep up, 1 bar", noise_sweep(BAR)),
            ("noise sweep down, half bar, res 6", noise_sweep(BAR / 2, 6000.0, 150.0, res=6.0))]
    for label, h in hits:
        assert abs(np.max(np.abs(h)) - 1) < 1e-6 and np.all(np.isfinite(h)), label
    loops = [("LOOP stabs Am-F-G-Am", stab_loop()),
             ("LOOP arp up, tracked", arp(AM)),
             ("LOOP arp updown", arp(AM, pattern="updown", octaves=1)),
             ("LOOP arp down, 8ths", arp(AM, pattern="down", rate=2)),
             ("LOOP arp random", arp(AM, pattern="random")),
             ("LOOP Juno bass, stomp cell", bass_loop()),
             ("LOOP pads Am-F-G-Am", pad_loop()),
             ("LOOP strings Am-F-G-Am", pad_loop(fn=strings)),
             ("LOOP organ Am-F-G-Am", pad_loop(fn=organ))]
    audition("juno", hits, loops, out=out)
