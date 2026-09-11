"""ROM orchestra — the strings and the choir of the 1999 dialect.

VNV's *Empires* credits four sample-ROM modules (Roland JV-1080 and
M-OC1, E-mu Proteus 2000, Korg Trinity Rack): its strings, brass and
choir are ROM patches, not an orchestra, which is why they read stacked
and STIFF rather than breathing.  This module is that sound: a detuned
unison saw stack with a slow attack and a static filter, either bowed
(`strings`) or sung through formants (`choir`).  Mono, dry, centre.

The stack is the mechanism nothing else here had.  `eps_hit` stacks
three detuned copies but only inside a 250 ms truncated stab, and
`juno.voice` has no unison at all on purpose (the Juno-60 had none) —
so the 1999 orchestra needed its own voice.

Separated by construction from the neighbouring voices in this repo:
no sample-loop flutter (`../../trance/ungeschrieben.py`'s strings own
that), no drifting voices and no breath (`adrift`'s choir owns those),
no Juno chorus.  The detune phases are FIXED, not random — stiffness is
the point, and a chord renders identically every time.

Era: the 1999 default is `hold=1`, no sampler decimation (the ASR-10 was
16-bit where Groth's EPS was 13-bit mono).  The 13-bit quantise in
`_common.dirt` still runs and is cosmetic; pass `hold=2, lowpass=7000`
to drag a voice back to 1993.

    from rom import strings, choir
    x = strings((57, 60, 64), 4 * BEAT)          # Am, one bar
    x = choir((45, 57, 60, 64), 2.0)             # the Legion chant
    buf = pad_loop(prog, fn=strings)             # juno's helper takes it as is
"""
from __future__ import annotations

import functools

import numpy as np
from scipy import signal

from _common import BEAT, SR, audition, bp_noise, dirt, midi_to_hz, norm, out_arg
from bark import VOWELS                          # the formant table, reused

_FORMANT_GAIN = (1.0, 0.6, 0.25)                 # F1, F2, F3 of the vowel


def _stack(notes, dur_n, voices, detune, roll, octave):
    """The unison stack: `voices` copies per note spread +/- `detune`
    cents, plus `octave` of the same an octave up.  Phases are a fixed
    irrational walk — deterministic, so the patch never drifts."""
    td = np.arange(dur_n) / SR
    x = np.zeros(dur_n)
    for j, m in enumerate(notes):
        for o, g in ((0, 1.0), (12, octave)):
            if g <= 0:
                continue
            f0 = midi_to_hz(m + o)
            for i in range(voices):
                cents = detune * (2.0 * i / max(voices - 1, 1) - 1.0)
                f = f0 * 2 ** (cents / 1200.0)
                ph = 2 * np.pi * f * td + (0.37 * i + 0.11 * j + 0.53 * o)
                kmax = min(40, int(9000 / f))
                x += g * sum(np.sin(k * ph) / k ** roll for k in range(1, kmax + 1))
    return x


@functools.lru_cache(maxsize=None)
def voice(notes, dur, kind="strings", voices=5, detune=9.0, attack=0.3, release=0.6,
          cutoff=3400.0, roll=1.05, octave=0.0, bow=0.18, vowel="o", q=7.0,
          body=0.25, hold=1, lowpass=None):
    """One sustained chord event.  notes: tuple of midi; dur: sounding
    length (s).  kind: 'strings' (a bow layer on top) or 'choir' (the
    stack through three formants of `vowel`, `body` of the raw stack mixed
    back).  voices/detune: the unison stack, +/- cents.  attack: raised
    cosine (s); release: exponential after `dur`.  cutoff: STATIC lowpass
    (Hz) — a ROM patch's filter does not move.  roll: partial rolloff
    exponent (lower = brighter).  octave: mix of the same stack an octave
    up.  bow: bandpassed scrape, strings only.  q: formant Q.  hold/lowpass:
    sampler dirt, 1999 defaults to off.  Cached — do not modify the result."""
    n = int((dur + 4 * release) * SR)
    td = np.arange(n) / SR
    x = norm(_stack(notes, n, voices, detune, roll, octave))
    if kind == "strings":
        x = x + bow * bp_noise(n, 2500, 7000) * (0.5 + 0.5 * np.exp(-td / 0.25))
    else:
        y = np.zeros(n)
        for fc, g in zip(VOWELS[vowel], _FORMANT_GAIN):
            b, a = signal.iirpeak(fc, Q=q, fs=SR)
            y += g * signal.lfilter(b, a, x)
        x = norm(y) + body * x
    x = signal.sosfilt(signal.butter(2, cutoff, "low", fs=SR, output="sos"), x)
    amp = 0.5 - 0.5 * np.cos(np.pi * np.clip(td / max(attack, 1e-4), 0, 1))
    amp = amp * np.where(td < dur, 1.0, np.exp(-(td - dur) / max(release, 1e-4)))
    return norm(dirt(x * amp, hold=hold, lowpass=lowpass))


def _chord(notes):
    return tuple(notes) if not isinstance(notes, int) else (notes,)


def strings(notes, dur, **kw):
    """The ROM string section: 5 detuned saws per note, a 0.3 s bow-in,
    a bright bow layer, static filter.  Chorus-and-bridge material; for
    the registral lift, play the same chord an octave up rather than
    moving the harmony (`VNV_Empires.md` §5)."""
    return voice(_chord(notes), dur, kind="strings", **kw)


def choir(notes, dur, **kw):
    """The wordless chant: the same stack through three formants, static
    and chordal, no drift and no breath.  Octave-double it (`octave=0.5`)
    for the cathedral width.  `vowel` picks the colour — 'o' and 'u' are
    the monkish ones, 'a' is the open 'aah'."""
    kw = {"octave": 0.5, "attack": 0.45, "cutoff": 2600.0, "detune": 6.0, **kw}
    return voice(_chord(notes), dur, kind="choir", **kw)


if __name__ == "__main__":
    out = out_arg("rom")
    AM, F, EM = (57, 60, 64), (53, 57, 60), (52, 55, 59)
    hits = [("strings Am, one bar", strings(AM, 4 * BEAT)),
            ("strings Am, one voice (the stack off)", strings(AM, 4 * BEAT, voices=1)),
            ("strings Am, detune 20 cents", strings(AM, 4 * BEAT, detune=20.0)),
            ("strings Am, an octave up (the lift)", strings(tuple(m + 12 for m in AM), 4 * BEAT)),
            ("strings Am, dragged back to 1993", strings(AM, 4 * BEAT, hold=2, lowpass=7000.0)),
            ("choir Am 'o', octave-doubled", choir(AM, 2.0)),
            ("choir Am 'u'", choir(AM, 2.0, vowel="u")),
            ("choir Am 'a' (the open aah)", choir(AM, 2.0, vowel="a")),
            ("choir Am, no octave", choir(AM, 2.0, octave=0.0))]
    for label, h in hits:
        assert abs(np.max(np.abs(h)) - 1) < 1e-6 and np.all(np.isfinite(h)), label
    assert len(strings(AM, 4 * BEAT)) == len(strings(AM, 4 * BEAT, voices=3)), "length varies with voices"
    assert not np.allclose(strings(AM, 1.0, bow=0.0), choir(AM, 1.0)), "the two kinds render the same"
    assert np.allclose(strings(AM, 1.0, bow=0.0), strings(AM, 1.0, bow=0.0)), "the stack is not deterministic"
    prog = [("strings " + n, strings(c, 4 * BEAT)) for n, c in (("Am", AM), ("F", F), ("Em", EM), ("Am", AM))]
    chant = [("choir " + n, choir(c, 4 * BEAT)) for n, c in (("Am", AM), ("F", F), ("Em", EM), ("Am", AM))]
    audition("rom", hits, prog + chant, gap=0.6, out=out)
