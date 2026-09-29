"""The Sardaukar/Fremen war horn -- a carnyx-style brassy harmonic stack
with a pitch scoop into each phrase, a slow growl, and a formant bump,
plus a more extreme "screamed" variant with chaotic vibrato and a scream
formant for the jihad's battle-horn calls.

Extracted from:
  - `horn_phrase()` <- `generate_fall_of_arrakeen.py` (identical in
    `generate_kwisatz_haderach.py`): 13-partial harmonic stack (1/k**0.7),
    a small pitch "scoop" over the first 150 ms, a 31 Hz growl tremolo, a
    low-pass plus a 450-900 Hz formant bump.
  - `screamed_horn_phrase()` <- `jihad.py`: the same scoop/growl idea
    pushed harder -- chaotic vibrato driven by a `slow_noise` control
    signal, 14 partials (1/k**0.68), an added scream formant (1.8-3.5 kHz)
    and a sub-octave layer, the whole thing driven through `tanh(3.0x)`,
    with an optional `octave` transpose and a `distant` low-pass option
    for far-off calls.
  - `place_horn()` <- both source scripts (identical): pan-and-add helper,
    generalized here to explicit buffers.

See ../CLAUDE.md and README.md for the full design notes and variant
table.
"""
from __future__ import annotations

import numpy as np
from scipy import signal

from _common import SR, add_at, glide_curve, norm, out_arg, slow_noise, write_wav

rng = np.random.default_rng(10191)


def horn_phrase(notes, growl=0.18, lp=1600):
    """Canonical war horn call: `notes` = [(midi, dur_s), ...], glide
    between notes, a brassy 13-partial harmonic stack, a small upward
    pitch scoop at the start of the phrase, a slow 31 Hz growl tremolo,
    low-passed at `lp` Hz with a 450-900 Hz formant bump added back."""
    total = sum(d for _, d in notes) + 1.2
    n = int(total * SR)
    tt = np.arange(n) / SR
    f_curve = glide_curve(notes, n)
    scoop = 0.94 + 0.06 * np.clip(tt / 0.15, 0, 1)
    phase = 2 * np.pi * np.cumsum(f_curve * scoop) / SR
    tone = np.zeros(n)
    for k in range(1, 13):
        tone += np.sin(k * phase) / k ** 0.7
    tone *= 1.0 + growl * np.sin(2 * np.pi * 31.0 * tt)
    env = np.minimum(np.clip(tt / 0.10, 0, 1) ** 0.8,
                      np.clip((total - tt) / 1.0, 0, 1))
    tone *= env
    sos_lo = signal.butter(2, lp, "low", fs=SR, output="sos")
    out = signal.sosfilt(sos_lo, tone)
    sos_fm = signal.butter(2, [450, 900], "bandpass", fs=SR, output="sos")
    out += 0.6 * signal.sosfilt(sos_fm, tone)
    return norm(out)


def screamed_horn_phrase(notes, octave=0, distant=False):
    """jihad.py's extreme "screamed" carnyx call: chaotic vibrato (a
    `slow_noise`-driven rate wobble), 14-partial stack, an added scream
    formant (1.8-3.5 kHz) plus a sub-octave layer, all pushed through
    `tanh(3.0x)` for a driven, distorted edge. `octave` transposes the
    whole phrase (e.g. `-12` for a call an octave down); `distant=True`
    low-passes the result at 1 kHz for a far-off, muffled call."""
    notes = [(m + octave, d) for m, d in notes]
    total = sum(d for _, d in notes) + 1.2
    n = int(total * SR)
    tt = np.arange(n) / SR
    f_curve = glide_curve(notes, n)
    rate = 5.0 + 3.0 * slow_noise(rng, total, 0.8, -1.0, 1.0)[:n]
    vib = 1.0 + 0.020 * np.sin(2 * np.pi * np.cumsum(rate) / SR)
    scoop = 0.93 + 0.07 * np.clip(tt / 0.12, 0, 1)
    phase = 2 * np.pi * np.cumsum(f_curve * vib * scoop) / SR
    tone = np.zeros(n)
    for k in range(1, 14):
        tone += np.sin(k * phase) / k ** 0.68
    tone *= 1.0 + 0.24 * np.sin(2 * np.pi * 31.0 * tt)
    env = np.minimum(np.clip(tt / 0.08, 0, 1) ** 0.7,
                      np.clip((total - tt) / 0.9, 0, 1))
    tone *= env
    sub = 0.4 * np.sin(0.5 * phase) * env
    sos_body = signal.butter(2, [450, 900], "bandpass", fs=SR, output="sos")
    sos_scream = signal.butter(2, [1800, 3500], "bandpass", fs=SR, output="sos")
    out = (tone + 0.7 * signal.sosfilt(sos_body, tone)
           + 0.7 * signal.sosfilt(sos_scream, tone) + sub)
    out = np.tanh(3.0 * out)
    if distant:
        out = signal.sosfilt(signal.butter(2, 1000, "low", fs=SR, output="sos"), out)
    return norm(out)


def place_horn(notes, t0, pan_pos, buf_l, buf_r, gain=1.0, growl=0.18, lp=1600):
    """Render `horn_phrase()` and add it, panned, into stereo buffers
    `buf_l`/`buf_r` at time `t0` -- matches both source scripts'
    `place_horn()`, generalized to explicit buffers."""
    h = horn_phrase(notes, growl=growl, lp=lp)
    add_at(buf_l, h, t0, gain * np.cos(pan_pos * np.pi / 2))
    add_at(buf_r, h, t0, gain * np.sin(pan_pos * np.pi / 2))


if __name__ == "__main__":
    out = out_arg("war_horn")
    from _common import concat

    call = [(38, 0.5), (38, 0.3), (45, 0.9)]
    canon = horn_phrase(call)
    scream = screamed_horn_phrase(call)
    scream_low = screamed_horn_phrase(call, octave=-12, distant=True)
    demo = concat([canon, scream, scream_low], gap=0.3)
    write_wav(out, demo)
    for x in (canon, scream, scream_low):
        assert np.max(np.abs(x)) <= 1.0 + 1e-6
        assert np.isfinite(x).all()
    print("war_horn.py: peak/finite OK; canonical + screamed variants rendered")
