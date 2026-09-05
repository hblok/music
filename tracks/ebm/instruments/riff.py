"""Riff — the one guitar: a distorted power-chord chug, synthesized.

Karplus-Strong strings (root, fifth, octave; double-tracked with a
slight detune) with a pick transient, palm-muted (fast string damping +
a short gate) or open, through a high-gain tanh amp and a cabinet
lowpass with a presence bump.  The Burnin' Heretic texture: a stab, not
a lead — one track only, declared.  Mono.

    from riff import chug, riff
    x = chug(40)                                   # E2 palm-muted chug
    x = chug(40, mute=False, dur=1.5)              # open power chord
    buf = riff("x.x.x.x.x.xbx.x.", root=40)        # 2 bars of chugs
"""
from __future__ import annotations

import functools

import numpy as np
from scipy import signal

import _common
from _common import SR, STEP, audition, bp_noise, gate, midi_to_hz, norm, out_arg, place, steps_buffer

_INTERVAL = {"x": 0, "b": 1, "3": 3, "5": 7, "o": 0}


def _ks(f, dur, damp, bright):
    """Karplus-Strong string: one-period noise burst, repeated with a
    per-period average (the string darkening) scaled by `damp`."""
    period = int(SR / f)
    n = int(dur * SR)
    burst = _common.rng.standard_normal(period)
    w = 1 + int((1 - bright) * 10)
    burst = np.convolve(burst, np.ones(w) / w, "same")
    out = np.empty(n)
    prev = burst
    i = 0
    while i < n:
        m = min(period, n - i)
        out[i:i + m] = prev[:m]
        prev = damp * 0.5 * (prev + np.roll(prev, 1))
        i += period
    return out


@functools.lru_cache(maxsize=None)
def chug(midi=40, dur=0.09, mute=True, chord=(0, 7, 12), drive=6.0, bright=0.6, double=True,
         cab=3800.0, body=0.5, hold=1):
    """One hit.  midi: root (E2 = 40); dur: length (s); mute: palm-muted
    chug (fast damping + gate) or open chord; chord: intervals; drive: amp
    gain; bright: pick brightness; double: second detuned take; cab:
    cabinet lowpass (Hz); body: the root-frequency thump under the chug.  Cached — do not modify."""
    n = int((dur + 0.06) * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    damp = 0.62 if mute else 0.991
    takes = ((1.0, 0.0), (1.003, 0.004)) if double else ((1.0, 0.0),)
    for k, iv in enumerate(chord):
        f = midi_to_hz(midi + iv)
        for det, off in takes:
            s = _ks(f * det, dur + 0.06, damp, bright)
            i0 = int((k * 0.003 + off) * SR)
            x[i0:] += s[: n - i0]
    x = norm(x) + 0.5 * bp_noise(n, 2000, 7000) * np.exp(-td * 600)          # the pick
    x = signal.sosfilt(signal.butter(2, 60, "high", fs=SR, output="sos"), x)
    x = np.tanh(drive * x)                                                    # the amp
    x = signal.sosfilt(signal.butter(2, cab, "low", fs=SR, output="sos"), x)  # the cab
    b, a = signal.iirpeak(2200, 1.0, fs=SR)
    x += 0.3 * signal.lfilter(b, a, x)                                        # presence
    f_root = midi_to_hz(midi)                                                 # the palm-mute thump
    x = norm(x) + body * np.sin(2 * np.pi * f_root * td) * np.exp(-td * (40.0 if mute else 3.0))
    if mute:
        x *= gate(td, dur, 0.01)
    else:
        x *= np.clip((dur + 0.05 - td) / 0.05, 0, 1)
    return norm(_common.dirt(x, hold=hold) if hold > 1 else x)


def riff(cell="x.x.x.x.x.xbx.x.", root=40, bars=2, gate_frac=0.9, max_chug=0.12, **kw):
    """Sequence chugs on a 16-step cell: x root, b flat second, 3 flat
    third, 5 fifth (all palm-muted), o an open chord held to the next hit."""
    onsets = [i for i, ch in enumerate(cell) if ch != "."]
    buf = steps_buffer(bars)
    for b in range(bars):
        for j, s in enumerate(onsets):
            nxt = (onsets[j + 1] if j + 1 < len(onsets) else onsets[0] + 16) - s
            ch = cell[s]
            if ch == "o":
                x = chug(root, nxt * STEP * 0.95, mute=False, **kw)
            else:
                x = chug(root + _INTERVAL[ch], min(nxt * STEP * gate_frac, max_chug), **kw)
            place(buf, x, b * 16 + s)
    return buf


if __name__ == "__main__":
    out = out_arg("riff")
    hits = [("chug E2 (default)", chug(40)),
            ("chug, drive 3", chug(40, drive=3.0)),
            ("chug, no body thump", chug(40, body=0.0)),
            ("chug, drive 14, dark cab", chug(40, drive=14.0, cab=2800.0)),
            ("chug F2 (the flat second)", chug(41)),
            ("chug, single take", chug(40, double=False)),
            ("open E5 chord, 1.5 s", chug(40, 1.5, mute=False)),
            ("open A5 chord, 1.5 s", chug(45, 1.5, mute=False))]
    for label, h in hits:
        assert abs(np.max(np.abs(h)) - 1) < 1e-6 and np.all(np.isfinite(h)), label
    loops = [("LOOP chugs x.x.x.x.x.xbx.x.", riff()),
             ("LOOP gallop chugs + b", riff("x.xxx.xxx.xxx.xb")),
             ("LOOP chugs into an open chord", riff("x.x.x.x.o.......")),
             ("LOOP 8ths, the 3 on the & of 4", riff("x.x.x.x.x.x.x.3.", root=45))]
    audition("riff", hits, loops, out=out)
