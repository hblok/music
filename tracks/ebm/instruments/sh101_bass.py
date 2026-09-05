"""SH-101 bass — the engine of 1993 EBM.

One oscillator (saw / square / pulse) plus the sub-octave square, into a
resonant state-variable lowpass driven by a filter ENVELOPE (the pluck:
cutoff opens on the attack and falls to its floor), hard-gated like a
sequencer step, then the sampler dirt.  Mono, dry, centre.

The declared bite: res=2.5 is above the trance warmth recipe's Q 1.2 —
guardrails per the EBM blueprint: the cutoff is always MOVING (the
envelope), drive stays soft (tanh 1.0), the sub square gives body.
Default register A2 (110 Hz) so the sub square lands at 55 Hz; at A1 it
lands at 27 Hz, inaudible rumble that eats headroom (measured).

    from sh101_bass import note, render_cell, CELLS
    x = note(45)                                  # A2, gated 16th
    buf = render_cell(CELLS["gallop"], root=45)   # 2 bars
"""
from __future__ import annotations

import numpy as np
from scipy import signal

from _common import SR, STEP, audition, dirt, gate, midi_to_hz, norm, out_arg, place, steps_buffer

# 16 steps per bar.  x root, o octave up, 5 fifth, 7 flat seventh, . rest
CELLS = {
    "stomp":   "x.x.x.x.x.x.x.o.",   # 8ths, octave on the & of 4 (the slam)
    "gallop":  "x.xxx.xxx.xxx.xx",   # the Front 242 school (Backdraft)
    "offbeat": ".x.x.x.x.x.x.x.x",   # bass never on the kick
    "rolling": "xoxxxoxxxoxxxoxx",   # root-oct-root-root, the later chorus engine
    "riff":    "x..x..x...x.5...",   # syncopated DAF/Nitzer cell
}
_INTERVAL = {"x": 0, "o": 12, "5": 7, "7": 10}


def svf_lowpass(x, cutoff, q):
    """Chamberlin state-variable lowpass with a per-sample cutoff array.
    ponytail: pure-Python sample loop (~20 ms per note) — cache notes per
    (midi, dur) in a track; vectorise in blocks only if it ever matters."""
    f1 = 2.0 * np.sin(np.pi * np.minimum(cutoff, 5000.0) / SR)   # stability ceiling
    q1 = 1.0 / q
    out = np.empty_like(x)
    low = band = 0.0
    for i in range(len(x)):
        low += f1[i] * band
        high = x[i] - low - q1 * band
        band += f1[i] * high
        out[i] = low
    return out


def note(midi=45, dur=STEP, cutoff=(2400.0, 250.0), env=0.05, res=2.5, sub=0.4,
         wave="saw", drive=1.0, hold=2, lowpass=None):
    """One bass note.  dur: sounding length in s (STEP = a 16th; an 8th
    gated 50 % is also STEP); cutoff: (open, floor) Hz of the filter
    envelope; env: its time constant (s); res: filter Q; sub: sub-octave
    square mix; wave: 'saw' | 'square' | 'pulse'; drive: tanh; hold/lowpass:
    sampler dirt."""
    f = midi_to_hz(midi)
    n = int((dur + 0.02) * SR)
    td = np.arange(n) / SR
    ph = 2 * np.pi * f * td
    if wave == "saw":
        osc = sum(np.sin(k * ph) / k ** 1.1 for k in range(1, min(60, int(9000 / f)) + 1))
    elif wave == "square":
        osc = sum(np.sin(k * ph) / k for k in range(1, min(60, int(9000 / f)) + 1, 2))
    else:
        osc = signal.square(ph, duty=0.25)
    osc = norm(osc) + sub * signal.square(ph / 2)
    fc = cutoff[1] + (cutoff[0] - cutoff[1]) * np.exp(-td / env)
    y = np.tanh(drive * svf_lowpass(osc, fc, res))
    y *= (1 - np.exp(-td / 0.002)) * gate(td, dur, 0.004)
    return norm(dirt(y, hold=hold, lowpass=lowpass))


def render_cell(cell, root=45, bars=2, gate_frac=0.5, **kw):
    """Sequence a 16-step cell for `bars` bars.  Each note sounds for
    gate_frac of the distance to the next onset (0.5 = the EBM stomp)."""
    onsets = [i for i, ch in enumerate(cell) if ch != "."]
    cache = {}
    buf = steps_buffer(bars)
    for b in range(bars):
        for j, s in enumerate(onsets):
            nxt = (onsets[j + 1] if j + 1 < len(onsets) else onsets[0] + 16) - s
            m = root + _INTERVAL[cell[s]]
            key = (m, nxt)
            if key not in cache:
                cache[key] = note(m, dur=nxt * STEP * gate_frac, **kw)
            place(buf, cache[key], b * 16 + s)
    return buf


if __name__ == "__main__":
    out = out_arg("sh101_bass")
    hits = [note(45),                                    # A2 default: the pluck
            note(45, cutoff=(900.0, 250.0)),             # dark
            note(45, cutoff=(4000.0, 400.0), env=0.09),  # open, slower
            note(45, res=1.0),                           # round (no bite)
            note(45, res=4.5),                           # more bite
            note(45, wave="square"),                     # hollow
            note(45, wave="pulse", sub=0.6),             # thin pulse, big sub
            note(33),                                    # A1: sub lands at 27 Hz — too low? judge
            note(45, dur=STEP * 4, env=0.25)]            # a held quarter, slow env
    for h in hits:
        assert abs(np.max(np.abs(h)) - 1) < 1e-6 and np.all(np.isfinite(h))
    loop = np.concatenate([render_cell(CELLS["stomp"]), render_cell(CELLS["gallop"])])
    audition("sh101_bass", hits, loop, out=out)
