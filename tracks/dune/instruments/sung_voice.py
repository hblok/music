"""The sung human voice -- Sihaya's Paul/Chani vocal engine: a glottal
source (portamento + vibrato) filtered through a pair of per-vowel
`iirpeak` formants, crossfaded between notes, with a closed-"m" hum mode
and a breath/onset "h" layer.

Extracted from `generate_muaddib.py:sing_phrase()` (used here as the
canonical version -- it is a strict superset of `generate_sihaya.py`'s:
identical when every lyric token is a single vowel letter, PLUS support
for `det`/`fs2` fine-tuning and a closed-"m" consonant crossfade that
sihaya's simpler version does not have). `generate_sihaya.py`'s
`sing_phrase(notes, female, hum)` (no `det`/`fs2`/"m"-token support) is
reproduced here as calling this module's `sing_phrase()` with defaults --
it is bit-identical on plain-vowel lyrics.

`notes`: a list of `(midi, dur_s, vowel_token)` triples, where
`vowel_token` is one of `"i" "e" "a" "o" "u"`, or (muaddib-only) a token
whose first character is `"m"` for a closed-mouth hum onset that opens
into the following vowel (e.g. `"ma"`).

`sing()` mirrors the source scripts' pan-and-add-to-a-named-singer-bus
helper, generalized to explicit stereo buffers instead of module-level
`chani_L`/`paul_L` globals.
"""
from __future__ import annotations

import numpy as np
from scipy import signal

from _common import SR, add_at, glide_curve, out_arg, write_wav

rng = np.random.default_rng(1993)   # generate_sihaya.py's seed

VOWELS = {"i": (270, 2300), "e": (530, 1840), "a": (730, 1090),
          "o": (570, 840), "u": (300, 870)}

_cache: dict = {}


def sing_phrase(notes, female=False, hum=False, det=1.0, fs2=1.0):
    """Render one sung phrase. `notes`: `[(midi, dur_s, vowel_token), ...]`.
    `female=True` gives a brighter, faster-vibrato voice (Chani) with
    formants scaled up 18%; `female=False` the darker voice (Paul).
    `hum=True` collapses every vowel to a closed "u" hum with a stronger
    chest/body layer and no breath noise -- for a wordless vocal pad.
    `det`/`fs2` are small fine-tuning multipliers on pitch / formant scale
    (used to detune a second take for a two-voice unison)."""
    key = (tuple(notes), female, hum, round(det, 5), round(fs2, 4))
    if key in _cache:
        return _cache[key]
    seq = [(m, d, ("u" if hum else v)) for m, d, v in notes]
    sung = sum(d for _, d, _ in seq)
    n = int((sung + 0.9) * SR)
    tt = np.arange(n) / SR

    f_curve = glide_curve([(m, d) for m, d, _ in seq], n, porta=0.07) * det
    vr, va = (5.8, 0.0035) if female else (5.0, 0.005)
    vib = 1.0 + va * np.sin(2 * np.pi * vr * tt) * np.clip(tt / 0.8, 0, 1)
    phase = 2 * np.pi * np.cumsum(f_curve * vib) / SR

    p = 1.2 if female else 0.8
    src = np.zeros(n)
    for k in range(1, 15):
        src += np.sin(k * phase) / k ** p

    scale = (1.18 if female else 1.0) * fs2
    xf = int(0.09 * SR)
    edges = np.cumsum([0.0] + [d for _, d, _ in seq])
    win = {}
    m_mask = np.zeros(n)
    n_m = int(0.08 * SR)
    for i, (_, _, tok) in enumerate(seq):
        v = tok[-1]
        s, e = int(edges[i] * SR), int(edges[i + 1] * SR)
        w = np.zeros(n)
        w[s:e] = 1.0
        if i > 0:
            w[s:s + xf] = np.linspace(0, 1, xf)
        if i < len(seq) - 1:
            w[e - xf:e] = np.linspace(1, 0, xf)
        else:
            w[e:] = 1.0
        win[v] = win.get(v, 0.0) + w
        if not hum and len(tok) > 1 and tok.startswith("m"):
            j = min(n, s + n_m)
            m_mask[s:j] = 0.5 + 0.5 * np.cos(np.pi * np.arange(j - s) / n_m)

    out = np.zeros(n)
    for v, w in win.items():
        f1, f2 = VOWELS[v]
        b1, a1 = signal.iirpeak(f1 * scale, Q=8.0, fs=SR)
        b2_, a2 = signal.iirpeak(f2 * scale, Q=8.0, fs=SR)
        y = signal.lfilter(b1, a1, src) + 0.7 * signal.lfilter(b2_, a2, src)
        y /= np.sqrt(np.mean(y ** 2)) + 1e-12
        out += y * w
    sos_body = signal.butter(2, 750 * scale, "low", fs=SR, output="sos")
    body = signal.sosfilt(sos_body, src)
    out += (1.3 if hum else 0.8) * body / (np.sqrt(np.mean(body ** 2)) + 1e-12)

    if np.any(m_mask > 0):
        f1, f2 = VOWELS["u"]
        b1, a1 = signal.iirpeak(f1 * scale, Q=8.0, fs=SR)
        closed = signal.lfilter(b1, a1, src)
        closed = closed / (np.sqrt(np.mean(closed ** 2)) + 1e-12) + \
            1.3 * body / (np.sqrt(np.mean(body ** 2)) + 1e-12)
        sos_m = signal.butter(2, 900, "low", fs=SR, output="sos")
        closed = signal.sosfilt(sos_m, closed)
        closed *= np.sqrt(np.mean(out ** 2)) / \
            (np.sqrt(np.mean(closed ** 2)) + 1e-12)
        out = out * (1 - m_mask) + 0.85 * closed * m_mask

    env = np.minimum(np.clip(tt / 0.10, 0, 1),
                      np.clip((sung + 0.15 - tt) / 0.35, 0, 1))
    env = np.clip(env, 0, 1) ** 1.2
    out *= env

    if not hum:
        nz = rng.standard_normal(n)
        sos_br = signal.butter(2, [2000, 5000], "bandpass", fs=SR, output="sos")
        out += (0.10 if female else 0.03) * signal.sosfilt(sos_br, nz) * env
        f1, f2 = VOWELS[seq[0][2][-1]]
        b1, a1 = signal.iirpeak(f1 * scale, Q=8.0, fs=SR)
        h = signal.lfilter(b1, a1, nz) * np.exp(-tt * 25.0)
        out += 0.5 * h / (np.max(np.abs(h)) + 1e-12)
    lp = 1400 if hum else (4800 if female else 3400)
    sos_lp = signal.butter(2, lp, "low", fs=SR, output="sos")
    out = signal.sosfilt(sos_lp, out)
    out /= np.max(np.abs(out)) + 1e-12
    _cache[key] = out
    return out


def sing(notes, t0, buf_l, buf_r, female=False, gain=1.0, hum=False,
         stretch=1.0):
    """Render `sing_phrase()` and add it, panned (Chani/female to the
    right at 0.56, Paul/male to the left at 0.44 -- matching
    `generate_sihaya.py`), into stereo buffers `buf_l`/`buf_r` at time
    `t0`. `stretch` scales every note's duration (a quick tempo-rubato
    knob)."""
    nb = [(m, d * stretch, v) for m, d, v in notes]
    x = sing_phrase(nb, female=female, hum=hum)
    p = 0.56 if female else 0.44
    add_at(buf_l, x, t0, gain * np.cos(p * np.pi / 2))
    add_at(buf_r, x, t0, gain * np.sin(p * np.pi / 2))


if __name__ == "__main__":
    out = out_arg("sung_voice")
    from _common import concat

    phrase = [(57, 0.4, "a"), (59, 0.3, "i"), (60, 0.5, "o"), (57, 0.6, "u")]
    paul = sing_phrase(phrase, female=False)
    chani = sing_phrase(phrase, female=True)
    hum = sing_phrase(phrase, female=True, hum=True)
    mphrase = [(57, 0.4, "ma"), (59, 0.3, "i"), (60, 0.6, "o")]
    with_m = sing_phrase(mphrase, female=False)
    demo = concat([paul, chani, hum, with_m], gap=0.3)
    write_wav(out, demo)
    for x in (paul, chani, hum, with_m):
        assert np.max(np.abs(x)) <= 1.0 + 1e-6
        assert np.isfinite(x).all()
    print("sung_voice.py: peak/finite OK; Paul/Chani/hum/closed-m variants rendered")
