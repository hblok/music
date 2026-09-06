"""Dark lead — the refrain voice of the 1993 dialect (reliquary v2 / v3.3).

The Juno lead as a hollow pulse (cutoff 1100, HPF 1, NO chorus, a
shallow slow vibrato: 4.5 Hz, 6 cents, 0.6 s in) with an octave-below
saw CHEST under it (cutoff 700, sub 0.5, Q 1.0).  `chest` is the
development knob: 0.8 in a first statement, 1.0 when the voice deepens.
Mono, centre, dry — the track adds its reverb (0.25 wet on reliquary).
Written for the baritone register and the chant vocabulary of
../CLAUDE.md's Frankfurt-trance trap; promoted from reliquary_v2.py on
2026-09-06 so clearance can share it.  Listen verdict on v3.3 pending —
iterate HERE, not in the track scripts.

    from dark_lead import dark_lead
    x = dark_lead(49, 0.5)             # C#3, half a second, chest 0.8
"""
from __future__ import annotations

import numpy as np

from _common import BEAT, audition, out_arg
from juno import lead


def dark_lead(midi, dur, chest=0.8):
    """One note: the hollow top + `chest` of the octave-below saw.  Cached
    upstream (juno.voice); the sum is normalised per call."""
    top = lead(midi, dur, wave="pulse", cutoff=1100.0, pluck=500.0, hpf=1, depth=0.0,
               vib=(4.5, 6.0, 0.6))
    low = lead(midi - 12, dur, wave="saw", cutoff=700.0, pluck=400.0, hpf=0, depth=0.0,
               vib=None, sub=0.5, res=1.0)
    x = top + chest * low[: len(top)]
    return x / (np.max(np.abs(x)) + 1e-12)


if __name__ == "__main__":
    out = out_arg("dark_lead")
    hits = [("C#3 chest 0.8", dark_lead(49, 1.0)),
            ("C#3 chest 1.0", dark_lead(49, 1.0, chest=1.0)),
            ("C#3 no chest", dark_lead(49, 1.0, chest=0.0)),
            ("G#2 (the low hang)", dark_lead(44, 1.2)),
            ("A3 (the ceiling)", dark_lead(57, 1.0)),
            ("A3 (reliquary's centre)", dark_lead(57, 1.0))]
    for label, h in hits:
        assert abs(np.max(np.abs(h)) - 1) < 1e-6 and np.all(np.isfinite(h)), label
    phrase = np.concatenate([dark_lead(m, BEAT / 2 * 0.95) for m in (49, 49, 49, 52, 50, 49)])
    audition("dark_lead", hits, ("PHRASE C#3 C#3 C#3 E3 D3 C#3", phrase), out=out)
