"""Bark — the harsh-vocal slot, instrumental.

A distorted, gated formant voice that SHOUTS one syllable on a pitch:
consonant onset, vowel formants (morphing), shout intonation (the pitch
falls), vocal-fry rasp, distortion, hard gate, sampler dirt.  Not speech
and not TTS (the standing rule) — a rhythmic texture with the shape of a
bark.  Mono, dry, centre.

    from bark import bark, chant
    x = bark(45)                                   # A2 "KAH"
    x = bark(45, vowel="o", vowel2="u", onset="d") # "DOH-oo"
    buf = chant("x..3..x.5...x...", vowels="aaoa") # a chant cell, 2 bars
"""
from __future__ import annotations

import functools

import numpy as np
from scipy import signal

from _common import SR, STEP, audition, bp_noise, dirt, gate, midi_to_hz, norm, out_arg, place, steps_buffer

VOWELS = {"a": (730.0, 1090.0, 2440.0), "e": (530.0, 1840.0, 2480.0), "i": (270.0, 2290.0, 3010.0),
          "o": (570.0, 840.0, 2410.0), "u": (300.0, 870.0, 2240.0)}
_INTERVAL = {"x": 0, "3": 3, "5": 7, "l": -5}


@functools.lru_cache(maxsize=None)
def bark(midi=45, dur=STEP * 2 * 0.6, vowel="a", vowel2=None, onset="k", fall=2.0, rasp=0.5,
         drive=2.0, q=(8.0, 10.0, 12.0), hold=2, lowpass=5000.0):
    """One syllable.  midi: the shout pitch (A2 = a male bark); dur: length
    (s); vowel / vowel2: formant set, morphing to vowel2 over the syllable;
    onset: 'k' (noise burst) | 'd' (thump) | 's' (hiss) | None; fall:
    semitones the pitch drops (shout intonation); rasp: vocal-fry AM depth;
    drive: tanh; q: formant Qs; hold/lowpass: sampler dirt.  Cached."""
    n = int((dur + 0.03) * SR)
    td = np.arange(n) / SR
    f0 = midi_to_hz(midi) * 2 ** (-fall / 12 * np.clip(td / dur, 0, 1))
    ph = 2 * np.pi * np.cumsum(f0) / SR
    src = sum(np.sin(k * ph) / k for k in range(1, int(6000 / midi_to_hz(midi)) + 1))
    if rasp:
        src *= 1 - rasp * 0.5 * (1 + np.sin(2 * np.pi * 38.0 * td))      # the fry rattle
    v1, v2 = VOWELS[vowel], VOWELS[vowel2 or vowel]
    m = np.clip(td / dur, 0, 1)
    y = np.zeros(n)
    for (fa, fb), g, qq in zip(zip(v1, v2), (1.0, 0.5, 0.25), q):
        ba, aa = signal.iirpeak(fa, qq, fs=SR)
        bb, ab = signal.iirpeak(fb, qq, fs=SR)
        y += g * ((1 - m) * signal.lfilter(ba, aa, src) + m * signal.lfilter(bb, ab, src))
    y = norm(y)
    t_on = {"k": 0.015, "d": 0.012, "s": 0.06}.get(onset, 0.0)
    if onset == "k":
        head = 0.9 * bp_noise(n, 1500, 6000) * np.exp(-td * 250)
    elif onset == "d":
        head = 0.9 * np.sin(2 * np.pi * np.cumsum(60 + 90 * np.exp(-td * 120)) / SR) * np.exp(-td * 90)
    elif onset == "s":
        head = 0.5 * bp_noise(n, 3000, 9000) * np.clip((t_on - td) / 0.01, 0, 1)
    else:
        head = 0.0
    vowel_env = (1 - np.exp(-np.clip(td - t_on, 0, None) / 0.008)) * (td >= t_on)
    x = head + y * vowel_env
    x = np.tanh(drive * x)
    x *= gate(td, dur, 0.006)
    return norm(dirt(x, hold=hold, lowpass=lowpass))


def chant(cell="x..3..x.5...x...", root=45, vowels="a", bars=2, gate_frac=0.6, max_dur=0.25, **kw):
    """Sequence barks on a 16-step cell (x root, 3 flat third, 5 fifth,
    l a fourth below); vowels cycle per bark; each bark lasts gate_frac of
    the gap to the next onset, capped at max_dur (shouts are short)."""
    onsets = [i for i, ch in enumerate(cell) if ch != "."]
    buf = steps_buffer(bars)
    k = 0
    for b in range(bars):
        for j, s in enumerate(onsets):
            nxt = (onsets[j + 1] if j + 1 < len(onsets) else onsets[0] + 16) - s
            dur = min(nxt * STEP * gate_frac, max_dur)
            place(buf, bark(root + _INTERVAL[cell[s]], dur, vowel=vowels[k % len(vowels)], **kw), b * 16 + s)
            k += 1
    return buf


if __name__ == "__main__":
    out = out_arg("bark")
    hits = [("KAH A2 (default)", bark(45)),
            ("KAH, no rasp", bark(45, rasp=0.0)),
            ("KAH, drive 4", bark(45, drive=4.0)),
            ("KOH-oo (o->u), d onset", bark(45, vowel="o", vowel2="u", onset="d")),
            ("SAH (s onset), longer", bark(45, dur=0.3, onset="s")),
            ("EH, no fall, E2", bark(40, vowel="e", fall=0.0)),
            ("EE, high A3", bark(57, vowel="i")),
            ("UH, low E2, big fall", bark(40, vowel="u", fall=5.0, dur=0.3)),
            ("clean reference (hold 1, no dirt LP)", bark(45, hold=1, lowpass=None))]
    for label, h in hits:
        assert abs(np.max(np.abs(h)) - 1) < 1e-6 and np.all(np.isfinite(h)), label
    loops = [("LOOP chant x..3..x.5...x... vowels aaoa", chant()),
             ("LOOP chant, o/u, d onsets", chant("x...x...x.x.x...", vowels="ou", onset="d")),
             ("LOOP sparse: one bark per bar", chant("x...........5...", vowels="a", bars=2))]
    audition("bark", hits, loops, out=out)
