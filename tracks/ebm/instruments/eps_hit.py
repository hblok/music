"""EPS hit — the sampled orchestral / choir stab, chopped short.

The 1993 sampler hit: a big chord (brass-string saw stack, or a formant
choir) with a fast attack, decaying, then TRUNCATED to fit the memory —
the abrupt end is the sound.  Crunchier dirt than the drums (hold=3, a
~15 kHz sample).  Mono.

    from eps_hit import hit
    x = hit()                     # orchestral Am
    x = hit(kind="choir")         # 'aah' Am
"""
from __future__ import annotations

import functools

import numpy as np
from scipy import signal

from _common import SR, audition, bp_noise, dirt, gate, midi_to_hz, norm, out_arg, place, steps_buffer


@functools.lru_cache(maxsize=None)
def hit(chord=(45, 52, 57, 60), dur=0.25, kind="orch", decay=6.0, drive=1.2, hold=3, lowpass=7000.0):
    """One hit.  chord: midi tuple; dur: truncation (s); kind: 'orch' (saw
    stack + bow noise) or 'choir' (two formants, breath); decay: 1/s;
    drive: tanh; hold/lowpass: sampler dirt.  Cached — do not modify."""
    n = int((dur + 0.01) * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    for m in chord:
        f = midi_to_hz(m)
        for det in (0.997, 1.0, 1.003):                      # the section, not one player
            ph = 2 * np.pi * f * det * td
            roll = 1.0 if kind == "orch" else 1.4
            x += sum(np.sin(k * ph) / k ** roll for k in range(1, min(30, int(8000 / f)) + 1))
    x = norm(x)
    if kind == "orch":
        x += 0.25 * bp_noise(n, 2000, 5000) * np.exp(-td * 12)     # bow/breath scrape on the attack
    else:
        y = np.zeros(n)
        for fc, g in ((650.0, 1.0), (1080.0, 0.6)):            # 'aah'
            b, a = signal.iirpeak(fc, Q=5, fs=SR)
            y += g * signal.lfilter(b, a, x)
        x = norm(y) + 0.05 * bp_noise(n, 800, 3000)
    x = np.tanh(drive * x) * np.exp(-td * decay)
    x *= (1 - np.exp(-td / 0.005)) * gate(td, dur, 0.006)
    return norm(dirt(x, hold=hold, lowpass=lowpass))


def loop(bars=2, **kw):
    """The hit on beat 1 and the 'and' of 3 of each bar."""
    x = hit(**kw)
    buf = steps_buffer(bars)
    for b in range(bars):
        place(buf, x, b * 16)
        place(buf, x, b * 16 + 10)
    return buf


if __name__ == "__main__":
    out = out_arg("eps_hit")
    hits = [hit(),                                      # orch Am, 250 ms
            hit(dur=0.6, decay=3.0),                    # longer, hear the tail before the chop
            hit(kind="choir"),                          # choir Am
            hit(kind="choir", dur=0.6, decay=2.0),
            hit(chord=(45, 48, 52, 57), hold=4)]        # Am7-ish, cruder sample
    for h in hits:
        assert abs(np.max(np.abs(h)) - 1) < 1e-6 and np.all(np.isfinite(h))
    audition("eps_hit", hits, loop(), out=out)
