"""SH-101 bass, the RUIN fork — the same engine with two more oscillator knobs.

A fork, not an edit: `sh101_bass.py` is imported by reliquary, no_access,
watchfire and the procession probes, and every one of those has a listen
verdict attached to a render.  Changing that module risks changing what
those tracks sound like when they are re-rendered, so this file exists
instead (2026-09-18, after ruin_v2's bass was called timid — "it reads
like a 1980s commodore game, as opposed to a heavy bold EBM goth track").

Only `note()` is forked; `CELLS` and `svf_lowpass` are imported from the
original, so the filter and the cell vocabulary stay in one place.  With
`detune=0.0, sub_wave="square"` this returns output bit-identical to
`sh101_bass.note` (asserted in the audition below), so the fork is a
superset and a track can move to it without any other change.

What is new:
  * detune — unison spread in CENTS.  0 keeps the single 101 oscillator;
    12-25 stacks two more copies either side.  A doubled-101 / Pro One
    thickness the real SH-101 cannot do, which is why it is a fork knob
    and not a library default.  This is TODO.md section 6's deferred
    "second oscillator", triggered by exactly the verdict above.
  * sub_wave — 'square' (the 101's own buzzy sub-octave) or 'sine'.  A
    sine sub adds far less PEAK for the same low-end energy, and under
    this module's peak-1.0 contract that is what lets the note get denser
    as `sub` rises instead of merely different.

Measured while tuning, and worth keeping so the next person does not
re-run the experiments (all at F#2, a 138 ms step):
  * The EPS dirt is NOT the 8-bit read at this register — hold=1 and
    hold=2 measure identically (crest 2.96, centroid ~130 Hz), because
    the note is lowpassed long before the decimation has anything to
    alias.
  * The filter FLOOR barely matters: 800 / 1500 / 2500 Hz all give the
    same spectrum, because a 1/k**1.1 saw at 92.5 Hz has very little
    harmonic energy for the filter to pass in the first place.
  * sub-120 share is ~0.85 even with sub=0.0 — at F#2 the FUNDAMENTAL is
    itself under 120 Hz, so that share is not a fault to fix.
  * A parallel band-passed distorted "grind" layer only cost crest.
  * In a ruin_v2 verse the bass stem is 6.9 dB LOUDER than the drums
    (-18.4 against -25.3 dBFS), so "timid" was never a level problem.
  * What DID move: detune + a sine sub + drive 2.0 takes the crest from
    2.96 to ~1.36, about 4 dB more RMS at the same peak.

    from sh101_bass_ruin import note
    x = note(42, detune=18.0, sub=0.8, sub_wave="sine", drive=2.0, hold=1)
"""
from __future__ import annotations

import functools

import numpy as np
from scipy import signal

from _common import SR, STEP, audition, dirt, gate, midi_to_hz, norm, out_arg, place, steps_buffer
from sh101_bass import CELLS, svf_lowpass                                 # noqa: F401  (CELLS re-exported)
from sh101_bass import note as _note_101

_INTERVAL = {"x": 0, "o": 12, "5": 7, "7": 10}


def _osc(wave, ph, f):
    if wave == "saw":
        return sum(np.sin(k * ph) / k ** 1.1 for k in range(1, min(60, int(9000 / f)) + 1))
    if wave == "square":
        return sum(np.sin(k * ph) / k for k in range(1, min(60, int(9000 / f)) + 1, 2))
    return signal.square(ph, duty=0.25)


@functools.lru_cache(maxsize=None)
def note(midi=45, dur=STEP, cutoff=(2400.0, 250.0), env=0.05, res=2.5, sub=0.4,
         wave="saw", drive=1.0, hold=2, lowpass=None, detune=0.0, sub_wave="square"):
    """One bass note — `sh101_bass.note` plus `detune` (unison cents) and
    `sub_wave` ('square' | 'sine').  All other arguments behave exactly as
    they do there; the defaults reproduce it sample for sample.  Cached
    (pass cutoff as a tuple); do not modify the result."""
    f = midi_to_hz(midi)
    n = int((dur + 0.02) * SR)
    td = np.arange(n) / SR
    ph = 2 * np.pi * f * td
    osc = _osc(wave, ph, f)
    if detune:
        for c in (-detune, detune):                  # the unison pair, cents either side
            osc = osc + _osc(wave, ph * 2.0 ** (c / 1200.0), f)
    sub_osc = np.sin(ph / 2) if sub_wave == "sine" else signal.square(ph / 2)
    osc = norm(osc) + sub * sub_osc
    fc = cutoff[1] + (cutoff[0] - cutoff[1]) * np.exp(-td / env)
    y = np.tanh(drive * svf_lowpass(osc, fc, res))
    y *= (1 - np.exp(-td / 0.002)) * gate(td, dur, 0.004)
    return norm(dirt(y, hold=hold, lowpass=lowpass))


def render_cell(cell, root=45, bars=2, gate_frac=0.5, **kw):
    """As sh101_bass.render_cell, through this module's note()."""
    onsets = [i for i, ch in enumerate(cell) if ch != "."]
    buf = steps_buffer(bars)
    for b in range(bars):
        for j, s in enumerate(onsets):
            nxt = (onsets[j + 1] if j + 1 < len(onsets) else onsets[0] + 16) - s
            place(buf, note(root + _INTERVAL[cell[s]], dur=nxt * STEP * gate_frac, **kw), b * 16 + s)
    return buf


if __name__ == "__main__":
    out = out_arg("sh101_bass_ruin")
    FS2 = 42
    rms = lambda x: float(np.sqrt(np.mean(x ** 2)))
    # the fork must BE the original at its defaults, or the other tracks could not move to it
    for d in (STEP, STEP * 2, STEP * 4):
        assert np.array_equal(note(FS2, dur=d), _note_101(FS2, dur=d)), f"fork diverges at dur={d}"
    print("  defaults are bit-identical to sh101_bass.note  (checked at 3 durations)")
    hits = [("v2 as shipped", note(FS2, cutoff=(2200.0, 250.0), sub=0.6)),
            ("+ the dirt off (measures the same — not the 8-bit read)", note(FS2, cutoff=(2200.0, 250.0), sub=0.6, hold=1)),
            ("+ a sine sub at 0.8", note(FS2, cutoff=(2200.0, 250.0), sub=0.8, sub_wave="sine", hold=1)),
            ("+ the unison stack (18 cents)", note(FS2, cutoff=(2200.0, 250.0), sub=0.8, sub_wave="sine", detune=18.0, hold=1)),
            ("+ drive 2.0 — THE DENSE READING", note(FS2, cutoff=(2200.0, 500.0), sub=0.8, sub_wave="sine", detune=18.0, drive=2.0, hold=1)),
            ("the square reading (hollow, Nitzer end)", note(FS2, cutoff=(2600.0, 900.0), sub=0.35, sub_wave="sine",
                                                             wave="square", detune=18.0, drive=2.2, res=2.0, env=0.10, hold=1)),
            ("the octave copy, as the track layers it", note(FS2 + 12, cutoff=(2600.0, 1400.0), sub=0.8, sub_wave="sine",
                                                             detune=18.0, drive=2.0, hold=1))]
    for label, h in hits:
        assert abs(np.max(np.abs(h)) - 1) < 1e-6 and np.all(np.isfinite(h)), label
    thin = note(FS2, cutoff=(2200.0, 250.0), sub=0.6)
    dense = note(FS2, cutoff=(2200.0, 500.0), sub=0.8, sub_wave="sine", detune=18.0, drive=2.0, hold=1)
    print(f"  crest: v2 {1 / rms(thin):.2f} -> dense {1 / rms(dense):.2f}  "
          f"({20 * np.log10(rms(dense) / rms(thin)):+.1f} dB RMS at the same peak)")
    assert rms(dense) > rms(thin), "the dense read must be denser at peak 1.0, not just different"
    loop = np.concatenate([render_cell("x.x.x.x.x.x.x.x.", root=FS2, sub=0.6),
                           render_cell("x.x.x.x.x.x.x.x.", root=FS2, cutoff=(2200.0, 500.0), sub=0.8,
                                       sub_wave="sine", detune=18.0, drive=2.0, hold=1, gate_frac=0.65)])
    audition("sh101_bass_ruin", hits, loop, out=out)
