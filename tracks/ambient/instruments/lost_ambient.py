"""Lost (ambient) voices: felt piano, Karplus-Strong harp, cello, flute, choir, bell, heart, chirp, dissonant swell, plus a feedback echo.

`heart` is the same recipe as `tracks/trance/instruments/drums.py:heart` (compare before adding a third copy).  Section-level machinery in `lost.py` (`lay_chords`, `arpeggiate`, `harp_offset`, `pad_chord`, `commit`, ...) is arrangement glue and is not extracted.

Extracted VERBATIM from the ambient track scripts (which are unchanged):
  - `piano` <- `lost.py:piano` -- felt piano, stretched-inharmonic partials + hammer
  - `harp` <- `lost.py:harp` -- Karplus-Strong plucked string, warm pick, cached per pitch
  - `cello` <- `lost.py:cello`
  - `cello_line` <- `lost.py:cello_line` -- glided legato line
  - `flute` <- `lost.py:flute` -- glided breathy flute line
  - `choir` <- `lost.py:choir` -- "oo" choir chord (mono)
  - `bell` <- `lost.py:bell`
  - `heart` <- `lost.py:heart` -- the through-line heartbeat; same recipe as trance/instruments/drums.heart
  - `chirp` <- `lost.py:chirp` -- the HOPE-section bird
  - `swell` <- `lost.py:swell` -- swirling dissonant string cluster; stereo (L, R)
  - `feedback_delay` <- `../dune/generate_ambient.py:feedback_delay` -- simple feedback echo (an effect on a caller-supplied array)

See ../CLAUDE.md and README.md for the identity rules.
Seed 1893 = lost.py (the year Munch painted The Scream).
"""
from __future__ import annotations

import numpy as np
from scipy import signal

from _common import SR, midi_to_hz, run_audition

rng = np.random.default_rng(1893)


# --- felt piano: stretched inharmonic partials, two detuned strings per
#     note, a soft felt hammer-thunk, warm lowpass. Cached per pitch.
_piano = {}


def piano(midi, dur=3.6):
    key = (midi, round(dur, 2))
    if key in _piano:
        return _piano[key]
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    out = np.zeros(n)
    B = 0.0004
    for k in range(1, 15):
        fk = f * k * np.sqrt(1 + B * k * k)
        if fk > 16000:
            break
        g = 1.0 / k ** 1.3
        dec = 1.0 + 0.42 * k
        out += g * (np.sin(2 * np.pi * fk * 0.9997 * td) +
                    np.sin(2 * np.pi * fk * 1.0003 * td)) * np.exp(-td * dec)
    sos_h = signal.butter(2, 2600, "low", fs=SR, output="sos")
    ham = signal.sosfilt(sos_h, rng.standard_normal(n)) * np.exp(-td * 60)
    out = out / (np.max(np.abs(out)) + 1e-12) + 0.12 * ham
    sos_f = signal.butter(2, 6500, "low", fs=SR, output="sos")
    out = signal.sosfilt(sos_f, out)
    out *= 1 - np.exp(-td / 0.004)
    _piano[key] = out / (np.max(np.abs(out)) + 1e-12)
    return _piano[key]


# --- harp / plucked string: Karplus-Strong, warm pick. Cached per pitch.
_harp = {}


def harp(midi, dur=2.6):
    if midi in _harp:
        return _harp[midi]
    f = midi_to_hz(midi)
    p = max(2, int(round(SR / f)))
    buf = rng.uniform(-1, 1, p)
    buf = np.convolve(buf, np.ones(3) / 3, mode="same")     # warm pick
    n = int(dur * SR)
    out = np.zeros(n)
    damp = 0.9955
    bi = 0
    for i in range(n):
        out[i] = buf[bi]
        nxt = (bi + 1) % p
        buf[bi] = damp * 0.5 * (buf[bi] + buf[nxt])
        bi = nxt
    td = np.arange(n) / SR
    out *= np.exp(-td * 0.6)
    _harp[midi] = out / (np.max(np.abs(out)) + 1e-12)
    return _harp[midi]


# --- bowed cello: detuned additive saw + bow noise, vibrato, slow attack.
_cello = {}


def cello(midi, dur=4.0):
    key = (midi, round(dur, 2))
    if key in _cello:
        return _cello[key]
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    vib = 1.0 + 0.004 * np.sin(2 * np.pi * 5.0 * td) * np.clip(td / 0.6, 0, 1)
    out = np.zeros(n)
    for det in (0.9985, 1.0015):
        ph = 2 * np.pi * f * det * np.cumsum(vib) / SR
        for k in range(1, 13):
            out += np.sin(k * ph) / k
    sos_b = signal.butter(2, [80, 2500], "bandpass", fs=SR, output="sos")
    bow = signal.sosfilt(sos_b, rng.standard_normal(n))
    out = out / (np.max(np.abs(out)) + 1e-12) + 0.08 * bow
    env = np.minimum(np.clip(td / 0.3, 0, 1),
                     np.clip((dur - td) / 0.5, 0, 1))
    sos_w = signal.butter(2, 2200, "low", fs=SR, output="sos")
    out = signal.sosfilt(sos_w, out * env)
    _cello[key] = out / (np.max(np.abs(out)) + 1e-12)
    return _cello[key]


def glide_curve(notes, n, tau=0.06):
    f_target = np.zeros(n)
    edge = 0.0
    for m, d in notes:
        a, b = int(edge * SR), min(n, int((edge + d) * SR))
        f_target[a:b] = midi_to_hz(m)
        edge += d
    i_end = min(n - 1, int(edge * SR))
    f_target[i_end:] = midi_to_hz(notes[-1][0])
    alpha = 1.0 - np.exp(-1.0 / (tau * SR))
    return signal.lfilter([alpha], [1.0, -(1.0 - alpha)],
                          f_target, zi=[f_target[0] * (1 - alpha)])[0]


def cello_line(notes, lowpass=2000):
    total = sum(d for _, d in notes)
    n = int((total + 0.6) * SR)
    td = np.arange(n) / SR
    f = glide_curve(notes, n, tau=0.05)
    vib = 1.0 + 0.005 * np.sin(2 * np.pi * 5.0 * td) * np.clip(td / 0.7, 0, 1)
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    out = np.zeros(n)
    for k in range(1, 13):
        out += np.sin(k * ph) / k
    sos_b = signal.butter(2, [80, 2400], "bandpass", fs=SR, output="sos")
    out = out / (np.max(np.abs(out)) + 1e-12) + 0.07 * signal.sosfilt(
        sos_b, rng.standard_normal(n))
    env = np.minimum(np.clip(td / 0.3, 0, 1), np.clip((total + 0.1 - td) / 0.5, 0, 1))
    sos_w = signal.butter(2, lowpass, "low", fs=SR, output="sos")
    out = signal.sosfilt(sos_w, out * env)
    return out / (np.max(np.abs(out)) + 1e-12)


# --- flute / ney: nearly pure, breath, blooming vibrato.
def flute(notes, lowpass=2800, vib_depth=0.004, breath=0.08):
    total = sum(d for _, d in notes)
    n = int((total + 1.0) * SR)
    td = np.arange(n) / SR
    f = glide_curve(notes, n, tau=0.05)
    vib = 1.0 + vib_depth * np.sin(2 * np.pi * 5.4 * td) * np.clip(td / 1.0, 0, 1)
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    out = np.sin(ph) + 0.18 * np.sin(2 * ph) + 0.05 * np.sin(3 * ph)
    if breath:
        sos_b = signal.butter(2, [1500, 5000], "bandpass", fs=SR, output="sos")
        out += breath * signal.sosfilt(sos_b, rng.standard_normal(n))
    env = np.minimum(np.clip(td / 0.12, 0, 1), np.clip((total + 0.05 - td) / 0.9, 0, 1))
    sos_w = signal.butter(2, lowpass, "low", fs=SR, output="sos")
    out = signal.sosfilt(sos_w, out * env)
    return out / (np.max(np.abs(out)) + 1e-12)


# --- choir "ooh/ah": glottal source through vowel formants, multiple notes.
def choir(chord, dur, vowel="oo", detune=0.004):
    formants = {"oo": [(320, 0.9), (800, 0.5), (2700, 0.12)],
                "ah": [(700, 1.0), (1150, 0.6), (2600, 0.25)]}[vowel]
    n = int(dur * SR)
    td = np.arange(n) / SR
    out = np.zeros(n)
    for m in chord:
        f = midi_to_hz(m)
        vib = 1.0 + 0.005 * np.sin(2 * np.pi * rng.uniform(4.5, 5.5) * td +
                                   rng.uniform(0, 6))
        for d in (1 - detune, 1 + detune):
            ph = 2 * np.pi * f * d * np.cumsum(vib) / SR
            src = np.zeros(n)
            for k in range(1, 13):
                src += np.sin(k * ph) / k ** 0.9
            voice = np.zeros(n)
            for fc, g in formants:
                sos = signal.butter(2, [max(60, fc * 0.8), fc * 1.25],
                                    "bandpass", fs=SR, output="sos")
                voice += g * signal.sosfilt(sos, src)
            out += voice
    env = np.minimum(np.clip(td / 1.5, 0, 1), np.clip((dur - td) / 2.0, 0, 1))
    out *= env
    return out / (np.max(np.abs(out)) + 1e-12)


# --- bells / glockenspiel / tolling bell: inharmonic damped sines.
def bell(midi, dur=4.0, ratios=((1, 1, 1.4), (2, 0.5, 1.9), (2.76, 0.3, 2.4),
                                (5.4, 0.15, 3.4)), bright=True):
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    out = np.zeros(n)
    for ratio, g, dec in ratios:
        out += g * np.sin(2 * np.pi * f * ratio * td) * np.exp(-td * dec)
    out *= 1 - np.exp(-td / (0.0015 if bright else 0.004))
    return out / (np.max(np.abs(out)) + 1e-12)


def heart():
    n = int(0.26 * SR)
    td = np.arange(n) / SR
    f = 32 + 36 * np.exp(-td * 20)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-td * 13)
    body += 0.5 * np.sin(2 * np.pi * 70 * td) * np.exp(-td * 18)   # midrange punch
    sos = signal.butter(2, 220, "low", fs=SR, output="sos")
    thud = signal.sosfilt(sos, rng.standard_normal(n)) * np.exp(-td * 28)
    thud /= np.max(np.abs(thud)) + 1e-12
    x = body / (np.max(np.abs(body)) + 1e-12) + 0.3 * thud
    x *= 1 - np.exp(-td / 0.004)
    return x / (np.max(np.abs(x)) + 1e-12)


def chirp():
    dur = rng.uniform(0.18, 0.4)
    n = int(dur * SR)
    td = np.arange(n) / SR
    f0 = rng.uniform(2400, 3600)
    f = f0 * (1 + 0.18 * np.sin(2 * np.pi * rng.uniform(14, 22) * td)) * \
        (1 + 0.4 * np.clip(td / dur, 0, 1))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * td / dur) ** 2
    return x / (np.max(np.abs(x)) + 1e-12)


def swell(cluster, dur, trem=0.4):
    n = int(dur * SR)
    td = np.arange(n) / SR
    L = np.zeros(n)
    R = np.zeros(n)
    undu = 1.0 + 0.006 * np.sin(2 * np.pi * 0.13 * td)       # the swirling sky
    for m in cluster:
        f = midi_to_hz(m)
        for d, gL, gR in [(0.994, 1.0, 0.5), (1.006, 0.5, 1.0)]:
            ph = 2 * np.pi * f * d * np.cumsum(undu) / SR
            v = np.zeros(n)
            for k in range(1, 7):
                v += np.sin(k * ph) / k
            L += gL * v
            R += gR * v
    sos = signal.butter(2, [140, 2200], "bandpass", fs=SR, output="sos")
    L = signal.sosfilt(sos, L)
    R = signal.sosfilt(sos, R)
    am = 0.6 + 0.4 * np.sin(2 * np.pi * trem * td)
    env = np.sin(np.pi * np.clip(td / dur, 0, 1)) * am       # swell up and down
    peak = max(np.max(np.abs(L * env)), np.max(np.abs(R * env)), 1e-12)
    return L * env / peak, R * env / peak


def feedback_delay(x, delay_s, feedback, taps=6):
    """Simple feedback echo."""
    y = x.copy()
    d = int(delay_s * SR)
    for k in range(1, taps + 1):
        g = feedback ** k
        y[k * d:] += x[: len(x) - k * d] * g
    return y


AUDITION = [
    ("piano", lambda: piano(62)),
    ("harp", lambda: harp(62)),
    ("cello", lambda: cello(50)),
    ("cello_line", lambda: cello_line([(50, 1.0), (53, 1.0), (57, 2.0)])),
    ("flute", lambda: flute([(69, 1.0), (72, 1.0), (74, 2.0)])),
    ("choir", lambda: choir([50, 57, 62], 4.0)),
    ("bell", lambda: bell(74)),
    ("heart", lambda: heart()),
    ("chirp", lambda: chirp()),
    ("swell", lambda: swell([50, 51, 57], 4.0)),
    ("feedback_delay", lambda: feedback_delay(harp(62), 0.35, 0.5)),
]

if __name__ == "__main__":
    run_audition("lost_ambient", AUDITION)
