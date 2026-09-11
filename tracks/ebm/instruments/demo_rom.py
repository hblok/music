"""The 1999 dialect: the ROM orchestra over the kit with its dirt OFF.

The question this demo exists to answer is whether 1999 actually
arrives — the whole premise of `../../../inspiration/VNV_Empires.md` is
that moving *Empires* into this library is one knob on the existing kit
(`hold=1`, the lowpass ceilings lifted) plus the one voice that was
missing (`rom.py`).  Eight bars at 122 either prove that or don't.

Bars 1-4: the kit clean, the SH-101 on Pro One knobs (less resonance,
no decimation), the strings low and quiet under it.
Bars 5-8: **the registral lift** — the same four chords, the strings an
octave up, the chant entering underneath, one clean orchestral hit on
the downbeat.  The harmony does not move: that is the point
(`VNV_Empires.md` §5, take 4).

Am F Em Am throughout — the minor v, never the flat-VII lift
(`../CLAUDE.md`, the Frankfurt trap).  Raw: no reverb, no master.
"""
from __future__ import annotations

import numpy as np

from _common import BAR, SR, out_arg, place, steps_buffer, write_wav
from eps_hit import hit
from eps_kick import kick
from eps_snare import snare
from hats import carpet
from juno import pad_loop
from rom import choir, strings
from sh101_bass import CELLS, render_cell

AM, F, EM = (57, 60, 64), (53, 57, 60), (52, 55, 59)
PROG = (AM, F, EM, AM)
CLEAN = {"hold": 1, "lowpass": None}                 # 1999: the ASR-10, not the EPS
GAIN = {"kick": 1.0, "snare": 0.85, "hats": 0.25, "bass": 0.75,
        "strings_verse": 0.30, "strings_lift": 0.85, "choir": 0.60, "hit": 0.6}


def demo(bars=8):
    buf = steps_buffer(bars)
    k, s = kick(**CLEAN), snare(**CLEAN)
    for b in range(bars):
        for beat in range(4):
            place(buf, k, b * 16 + beat * 4, GAIN["kick"])
        place(buf, s, b * 16 + 4, GAIN["snare"])
        place(buf, s, b * 16 + 12, GAIN["snare"])

    half = bars // 2
    n_half = int(half * BAR * SR)
    c1 = carpet(half, open_steps=(), hold=1)
    buf[:len(c1)] += GAIN["hats"] * c1
    c2 = carpet(bars - half, hold=1)
    buf[n_half:n_half + len(c2)] += GAIN["hats"] * c2

    # the Pro One reading of the engine: two of the three 1993 knobs off
    bass = render_cell(CELLS["stomp"], root=45, bars=bars, res=1.8, **CLEAN)
    buf[:len(bass)] += GAIN["bass"] * bass

    # the orchestra: juno's own loop helper takes rom's voices unchanged
    v = pad_loop(PROG, fn=strings)
    buf[:len(v)] += GAIN["strings_verse"] * v
    up = pad_loop(tuple(tuple(m + 12 for m in ch) for ch in PROG), fn=strings)
    buf[n_half:n_half + len(up)] += GAIN["strings_lift"] * up
    ch = pad_loop(PROG, fn=choir)
    buf[n_half:n_half + len(ch)] += GAIN["choir"] * ch
    place(buf, hit(AM, **CLEAN), half * 16, GAIN["hit"])
    return buf


def low_share(x, below=400.0):
    """Share of energy under `below` Hz — how the register move is measured
    (RMS cannot see it: the lift is registral, and the drums own the RMS)."""
    X = np.abs(np.fft.rfft(x)) ** 2
    f = np.fft.rfftfreq(len(x), 1 / SR)
    return float(X[f < below].sum() / X.sum())


if __name__ == "__main__":
    out = out_arg("demo_rom")
    x = demo()
    assert np.all(np.isfinite(x))

    rms = lambda y: float(np.sqrt((y ** 2).mean()))
    lo, hi = x[: int(4 * BAR * SR)], x[int(4 * BAR * SR):]
    v = pad_loop(PROG, fn=strings)
    up = pad_loop(tuple(tuple(m + 12 for m in ch) for ch in PROG), fn=strings)
    print(f"  verse rms {rms(lo):.3f}   lift rms {rms(hi):.3f}   ratio {rms(hi) / rms(lo):.3f}")
    print(f"  strings <400 Hz: verse {low_share(v):.3f}   lifted {low_share(up):.3f}")
    assert rms(hi) > rms(lo), "the lift is not louder than the verse"
    assert low_share(up) < 0.5 * low_share(v), "the strings did not actually move up an octave"
    write_wav(out, x)
