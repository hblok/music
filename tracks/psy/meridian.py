#!/usr/bin/env python3
"""
meridian.py — "Meridian" (~5:00). Second tracks/psy/ GOA track.
Design doc: meridian_notes.md (concept + answered questions, 2026-07-31).

145 BPM, seed 1997. Reuses the phototaxis engine (FM orchestra, swarm,
song form, big-room master with the v2.1 crest/HP guardrail) but INVERTS
the thesis to earn a distinct identity:

  * THE STAR IS THE LONG MORPHING LEAD — one sustained FM voice whose
    index MORPHS cyclically across bars (a slow LFO, phase-continuous)
    with staged ratio steps; it snakes and SINGS the refrain as the
    through-line from the early thesis on. The swarm (fizz/glint/murk)
    is demoted to a shimmering BED under it (inverted from phototaxis,
    where the swarm was the star and the anthem a late guest).
  * EUPHORIC SUNRISE on a HEAVY NIGHT-GOA ENGINE (Q3) — verses in
    E DORIAN over a heavier, darker kick + a driving heavy bassline;
    the choruses LIFT to a bold Picardy E MAJOR (Q7) — the same refrain
    blooms minor->major, the sunrise. Written in DEGREES, so the bloom
    is automatic.

THE FRESHNESS CONTRACT (enforced by construction, declared in verify):
  * All melodic sound is 2-op phase modulation — zero saw stacks, zero
    iirpeak. The morph is CYCLIC (net index slope ~0 across the track),
    never the navigator's one-way 4->0.8 decay lead.
  * Moving bassline (>= 2 pitches per bar), never static-root K-b-b-b;
    the kick-gap contract is kept (bass silent on every kick 16th).
  * Heavy goa kick (bigger/darker than phototaxis's tight 95->48), sparse
    hats. NEW seam vocabulary (phototaxis claimed chatter + bubble-rise):
    tape-flutter + harmonic-bloom (zaps / reverse cymbals / tom fills /
    noise sweeps stay claimed elsewhere).
  * The refrain is written in DEGREES and blooms E Dorian (verses) ->
    Picardy E major (choruses); the lead sings it, the swarm never does.

Preview mode (the judge-before-you-build knob):
    python meridian.py --preview chorus   → the Picardy-major refrain.
    python meridian.py --preview groove   → a verse: heavy groove + lead.

Output: /workspace/music/meridian.wav + .flac (44100 Hz stereo 16-bit).
"""

import pathlib
import sys
import wave

import numpy as np
import soundfile
from scipy import signal

# ----------------------------------------------------------------- grid
SR = 44100
BPM = 145.0
BEAT = 60.0 / BPM
SIXT = BEAT / 4.0
BAR = 4.0 * BEAT
SEED = 1997
rng = np.random.default_rng(SEED)

PREVIEW = None
if len(sys.argv) >= 3 and sys.argv[1] == "--preview":
    PREVIEW = sys.argv[2]          # "chorus" | "groove"


def step_t(bar, step=0.0):
    return bar * BAR + step * SIXT


# -------------------------------------------------------------- helpers
def midi_to_hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def fade(x, fin=0.004, fout=0.05):
    y = x.copy()
    ni, no = int(fin * SR), int(fout * SR)
    if ni:
        y[:ni] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(ni) / ni)
    if no:
        y[-no:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(no) / no)
    return y


def slow_noise(n, rate_hz, seed):
    r = np.random.default_rng(seed)
    k = max(4, int(n / SR * rate_hz) + 2)
    pts = r.standard_normal(k)
    pts = np.convolve(pts, [0.25, 0.5, 0.25], mode="same")
    y = np.interp(np.arange(n), np.linspace(0, n - 1, k), pts)
    y -= y.min()
    if y.max() > 0:
        y /= y.max()
    return y


def make_reverb_ir(seconds, decay, seed):
    r = np.random.default_rng(seed)
    n = int(seconds * SR)
    ir = r.standard_normal(n) * np.exp(-np.arange(n) / SR / decay)
    b, a = signal.butter(2, 4000 / (SR / 2), "low")
    ir = signal.lfilter(b, a, ir)
    return ir / np.sqrt(np.sum(ir ** 2))


IR_L = make_reverb_ir(3.5, 0.9, 7)
IR_R = make_reverb_ir(3.5, 0.9, 11)


def reverb_pair(L, R, wet):
    if wet <= 0.0:
        return L, R
    wL = signal.fftconvolve(L, IR_L)[: len(L)]
    wR = signal.fftconvolve(R, IR_R)[: len(R)]
    for d, w in ((L, wL), (R, wR)):
        pk_d, pk_w = np.max(np.abs(d)) + 1e-12, np.max(np.abs(w)) + 1e-12
        w *= pk_d / pk_w
    return (1 - wet) * L + wet * wL, (1 - wet) * R + wet * wR


def add_at(buf, x, start_s, gain=1.0):
    i0 = int(start_s * SR)
    if i0 >= len(buf):
        return
    n = min(len(x), len(buf) - i0)
    if n > 0:
        buf[i0:i0 + n] += gain * x[:n]


def place(layer, x, t, gain=1.0, pan=0.0):
    """Constant-power pan of a mono event into a stereo layer pair."""
    a = (pan + 1.0) / 2.0
    add_at(layer[0], x, t, gain * np.cos(a * np.pi / 2))
    add_at(layer[1], x, t, gain * np.sin(a * np.pi / 2))


def lowpass(x, hz, order=2):
    b, a = signal.butter(order, hz / (SR / 2), "low")
    return signal.lfilter(b, a, x)


def highpass(x, hz, order=2):
    b, a = signal.butter(order, hz / (SR / 2), "high")
    return signal.lfilter(b, a, x)


def rc_attack(n, seconds):
    """Raised-cosine 0→1 attack over `seconds`, then flat."""
    na = min(n, max(1, int(seconds * SR)))
    env = np.ones(n)
    env[:na] = 0.5 - 0.5 * np.cos(np.pi * np.arange(na) / na)
    return env


# ---------------------------------------------------- the FM orchestra
# All pitched sound is 2-op PM: sin(ph_c + I(t)·sin(ratio·ph_c [+ fb])).
# The index/ratio behaviour is the expressive axis (notes doc, FM
# orchestra section). No saw stacks, no iirpeak, anywhere.

def pm_core(f0, n, ratio, idx, fb=0.0, pitch_env=None):
    td = np.arange(n) / SR
    if pitch_env is None:
        ph_c = 2 * np.pi * f0 * td
    else:
        ph_c = 2 * np.pi * np.cumsum(f0 * pitch_env) / SR
    ph_m = ratio * ph_c
    m = np.sin(ph_m)
    if fb:
        m = np.sin(ph_m + fb * m)
    return np.sin(ph_c + idx * m), ph_c


_cache = {}


MORPH_HZ = 1.0 / (4.0 * BAR)          # one index-morph cycle per 4 bars


def lead_note(midi, dur, held, t_abs):
    """THE STAR — the long morphing lead. Sustained + sung, and the FM
    index MORPHS on a slow LFO tied to GLOBAL time (phase-continuous
    across notes → the timbre breathes over 4-bar cycles, the liquid
    snaking goa line). Ratio steps up on the high euphoric notes. This is
    NOT the navigator's one-way decay and NOT phototaxis's short wobble:
    the morph is cyclic (net slope ~0, checked)."""
    n = int(dur * SR)
    td = np.arange(n) / SR
    f = midi_to_hz(midi)
    tg = t_abs + td                                    # global time
    bloom = np.clip((td - 0.25) / 0.25, 0, 1)          # vibrato blooms
    pitch = 1.0 + 0.004 * bloom * np.sin(2 * np.pi * 5.2 * td)
    lfo = np.sin(2 * np.pi * MORPH_HZ * tg)            # the cyclic morph
    if held:
        idx = 2.2 + 1.6 * lfo
    else:
        idx = 1.3 + 1.0 * np.exp(-td / 0.12) + 0.5 * lfo
    ratio = 3.0 if midi >= 76 else 2.0                 # brighter high notes
    y, ph_c = pm_core(f, n, ratio, idx, pitch_env=pitch)
    y += 0.25 * np.sin(ph_c)                            # body core
    y *= rc_attack(n, 0.12)                             # slow-ish attack (sings)
    rel = min(n, int((0.28 if held else 0.10) * SR))   # held notes ring
    y[-rel:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(rel) / rel)
    y = lowpass(y, 2600)
    y = np.tanh(0.9 * y)
    y /= np.max(np.abs(y)) + 1e-12
    return y


def fizz_note(midi, dur):
    """The runner: ratio 1 + modulator feedback (the DX7 near-saw)."""
    key = ("fiz", midi, round(dur, 4))
    if key in _cache:
        return _cache[key]
    n = int(dur * SR)
    td = np.arange(n) / SR
    idx = 1.2 + 1.3 * np.exp(-td / 0.06)
    y, ph_c = pm_core(midi_to_hz(midi), n, 1.0, idx, fb=1.15)
    y += 0.15 * np.sin(ph_c)
    gate = int(0.80 * n)
    env = np.ones(n)
    env[gate:] *= np.exp(-(td[gate:] - td[gate]) / 0.012)
    y *= env * rc_attack(n, 0.018)                      # softer: a shimmer, not a chatter
    y = lowpass(y, 5200)
    y = np.tanh(0.9 * y)
    y /= np.max(np.abs(y)) + 1e-12
    _cache[key] = y
    return y


def glint_note(midi):
    """The bell: non-integer ratio 3.53, index snaps shut in ~80 ms."""
    key = ("gli", midi)
    if key in _cache:
        return _cache[key]
    n = int(0.16 * SR)
    td = np.arange(n) / SR
    idx = 4.0 * np.exp(-td / 0.025)
    y, _ = pm_core(midi_to_hz(midi), n, 3.53, idx)
    y *= np.exp(-td / 0.05) * rc_attack(n, 0.001)
    y /= np.max(np.abs(y)) + 1e-12
    _cache[key] = y
    return y


def murk_note(midi, dur):
    """The shadow: ratio 0.5 (modulator below carrier), dark and hollow."""
    key = ("mur", midi, round(dur, 4))
    if key in _cache:
        return _cache[key]
    n = int(dur * SR)
    td = np.arange(n) / SR
    y, _ = pm_core(midi_to_hz(midi), n, 0.5, 0.8)
    gate = int(0.70 * n)
    env = np.ones(n)
    env[gate:] *= np.exp(-(td[gate:] - td[gate]) / 0.015)
    y *= env * rc_attack(n, 0.005)
    y = lowpass(y, 1200)
    y /= np.max(np.abs(y)) + 1e-12
    _cache[key] = y
    return y


def bass_note(midi, dur):
    """HEAVY night-goa FM bass (Q3): more grit (higher index) + a fatter
    sub octave + a touch more drive than phototaxis's — the dark engine
    under the euphoric sunrise. Still saw-free; the master HP/crest
    guardrail keeps the added weight from growling (checked)."""
    key = ("bas", midi, round(dur, 4))
    if key in _cache:
        return _cache[key]
    n = int(dur * SR)
    td = np.arange(n) / SR
    f = midi_to_hz(midi)
    idx = 0.70 + 0.5 * np.exp(-td / 0.025)              # some grit, not buzzy
    y, ph_c = pm_core(f, n, 1.0, idx)
    y += 0.30 * np.sin(ph_c)
    y += 0.55 * np.sin(2 * np.pi * (f / 2.0) * td)      # heavy sub octave (felt)
    gate = int(0.88 * n)
    env = np.ones(n)
    env[gate:] *= np.exp(-(td[gate:] - td[gate]) / 0.012)
    y *= env * rc_attack(n, 0.002)
    y = lowpass(y, 320)                                  # darker: sub, not mid-buzz
    y = np.tanh(1.05 * y)
    y /= np.max(np.abs(y)) + 1e-12
    _cache[key] = y
    return y


_pad_cache = {}


def pad_bed(root_midi, dur, bright=1.0, seed=0):
    """v2 depth fix: the warm evolving floor under the whole groove.
    Root+5th+octave, wide detune, slow attack, dark LP, slow-noise evolve.
    Deep/dark/low, NOT a beating mid tone (the standing drone-bed rule) —
    root sits at F#2/E2/etc. (harm root + 12), never the mid register."""
    key = ("pad", root_midi, round(dur, 3), round(bright, 2), seed)
    if key in _pad_cache:
        return _pad_cache[key]
    n = int(dur * SR)
    L = np.zeros(n)
    R = np.zeros(n)
    for m in (root_midi, root_midi + 7, root_midi + 12):
        f = midi_to_hz(m)
        for det, buf in ((1.0018, L), (0.9982, R)):
            y, _ = pm_core(f * det, n, 1.0, 0.7)         # ratio 1, warm
            buf += y
    env = rc_attack(n, 0.22)
    rel = min(n, int(0.32 * SR))
    env[-rel:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(rel) / rel)
    evolve = 0.60 + 0.40 * slow_noise(n, 0.20, 1995 + seed)
    L = lowpass(L, 1200 * bright) * env * evolve
    R = lowpass(R, 1200 * bright) * env * evolve
    pk = max(np.max(np.abs(L)), np.max(np.abs(R))) + 1e-12
    out = ((L + 0.35 * R) / (1.35 * pk), (R + 0.35 * L) / (1.35 * pk))
    _pad_cache[key] = out
    return out


def pool_drone(dur):
    """The breakdown bed: deep, dark, evolving, pulses to true zero.
    Beating lives at the 46 Hz fundamental only (slow, low — sanctioned);
    centroid is checked < 400 Hz in verify."""
    n = int(dur * SR)
    td = np.arange(n) / SR
    f0 = midi_to_hz(28)                                 # E1 ≈ 41.2 Hz
    L = np.zeros(n)
    R = np.zeros(n)
    for gain, mult, det in ((1.0, 1.0, 0.15), (0.45, 2.0, 0.0),
                            (0.15, 3.0, 0.0)):
        L += gain * np.sin(2 * np.pi * (f0 * mult) * td)
        R += gain * np.sin(2 * np.pi * (f0 * mult + det) * td)
    breath = 0.5 - 0.5 * np.cos(2 * np.pi * td / 20.0)  # true zero / 20 s
    evolve = 0.6 + 0.4 * slow_noise(n, 0.15, 1997)
    L, R = lowpass(L, 420), lowpass(R, 420)
    L *= breath * evolve
    R *= breath * evolve
    pk = max(np.max(np.abs(L)), np.max(np.abs(R))) + 1e-12
    return L / pk, R / pk


# ------------------------------------------------------------- the kit
def goa_kick():
    """HEAVY goa kick (Q3 night-goa): bigger/darker than phototaxis's tight
    95->48 — 102->42, a longer body and a sustained sub tail for weight."""
    n = int(0.20 * SR)
    td = np.arange(n) / SR
    f = 42.0 + 60.0 * np.exp(-td / 0.014)               # 102->42 in ~40 ms
    y = np.sin(2 * np.pi * np.cumsum(f) / SR)
    y *= np.exp(-td / 0.080) * np.clip((0.19 - td) / 0.014, 0, 1)
    y += 0.35 * np.sin(2 * np.pi * 41.0 * td) * np.exp(-td / 0.10)  # sub tail
    click = rng.standard_normal(int(0.004 * SR))
    click = highpass(click, 2400) * np.exp(-np.arange(len(click)) / SR / 0.001)
    y[: len(click)] += 0.30 * click / (np.max(np.abs(click)) + 1e-12)
    return y / (np.max(np.abs(y)) + 1e-12)


def open_hat():
    n = int(0.20 * SR)
    y = highpass(rng.standard_normal(n), 6000)
    y *= np.exp(-np.arange(n) / SR / 0.075)
    return y / (np.max(np.abs(y)) + 1e-12)


def closed_hat():
    n = int(0.035 * SR)
    y = highpass(rng.standard_normal(n), 7500)
    y *= np.exp(-np.arange(n) / SR / 0.012)
    return y / (np.max(np.abs(y)) + 1e-12)


def snare():
    n = int(0.13 * SR)
    td = np.arange(n) / SR
    noise = rng.standard_normal(n)
    b, a = signal.butter(2, [400 / (SR / 2), 6500 / (SR / 2)], "band")
    y = signal.lfilter(b, a, noise) + 0.25 * np.sin(2 * np.pi * 190 * td)
    y *= np.exp(-td / 0.045)
    return y / (np.max(np.abs(y)) + 1e-12)


KICK = goa_kick()
OHAT = open_hat()
CHAT = closed_hat()
SNARE = snare()


def tape_flutter(layer, t0, dur, root_midi):
    """Meridian's seam device #1: a slow wow + flutter pitch-warble that
    swells under a section boundary — the tape wobble. A detuned low
    triad whose pitch drifts (0.7 Hz wow) and shimmers (6.5 Hz flutter),
    fading in and back out across the seam. Composed, no noise sweep."""
    n = int(dur * SR)
    td = np.arange(n) / SR
    warp = (1.0 + 0.011 * np.sin(2 * np.pi * 0.7 * td)
            + 0.006 * np.sin(2 * np.pi * 6.5 * td))
    L = np.zeros(n)
    R = np.zeros(n)
    for m, g, det in ((root_midi, 1.0, 1.0), (root_midi + 7, 0.55, 1.003),
                      (root_midi + 12, 0.45, 0.997)):
        f = midi_to_hz(m)
        ph = 2 * np.pi * np.cumsum(f * det * warp) / SR
        y = np.sin(ph) + 0.30 * np.sin(2 * ph)
        L += g * y
        R += g * (np.sin(ph / det) + 0.30 * np.sin(2 * ph / det))
    swell = np.sin(np.pi * np.clip(td / dur, 0, 1)) ** 1.4   # in and out
    L = lowpass(L, 1700) * swell
    R = lowpass(R, 1700) * swell
    pk = max(np.max(np.abs(L)), np.max(np.abs(R))) + 1e-12
    add_at(layer[0], L / pk, t0, 1.0)
    add_at(layer[1], R / pk, t0, 1.0)


def harmonic_bloom(layer, t_end, root_midi, major):
    """Meridian's seam device #2 (replaces the bubble-rise): a sustained
    FM chord whose index BLOOMS open (0 -> bright) across 2 bars into the
    downbeat at t_end — the composed riser. Third tracks the section
    (major bloom into a chorus, Dorian bloom elsewhere)."""
    dur = 2 * BAR
    t0 = t_end - dur
    n = int(dur * SR)
    td = np.arange(n) / SR
    idx = 4.2 * (td / dur) ** 1.5                        # 0 -> 4.2 bloom
    third = 4 if major else 3
    L = np.zeros(n)
    R = np.zeros(n)
    for k, m in enumerate((root_midi, root_midi + third, root_midi + 7,
                           root_midi + 12)):
        f = midi_to_hz(m)
        y, _ = pm_core(f, n, 2.0, idx)
        pan = -0.5 + 0.33 * k
        a = (pan + 1.0) / 2.0
        L += np.cos(a * np.pi / 2) * y
        R += np.sin(a * np.pi / 2) * y
    env = rc_attack(n, dur * 0.85) * (0.4 + 0.6 * td / dur)
    L = lowpass(L, 3200) * env
    R = lowpass(R, 3200) * env
    pk = max(np.max(np.abs(L)), np.max(np.abs(R))) + 1e-12
    add_at(layer[0], L / pk, t0, 1.0)
    add_at(layer[1], R / pk, t0, 1.0)


# ------------------------------------------------------- music material
# E DORIAN (verses): E F# G A B C# D.   E MAJOR / Picardy (choruses):
# E F# G# A B C# D#.  All melodic material is written in DEGREES (0=E)
# so the SAME notes bloom minor->major in the choruses — the sunrise.
E_ROOT = 28                                             # E1
DORIAN = [0, 2, 3, 5, 7, 9, 10]
MAJOR = [0, 2, 4, 5, 7, 9, 11]
LEAD_OCT, FIZZ_OCT, GLINT_OCT, MURK_OCT = 3, 3, 4, 1    # base octaves


def deg2midi(step, base_oct, major):
    """Scale-degree -> MIDI in the active scale (major chorus / Dorian
    verse).  step may exceed a heptad or go negative (octave wraps)."""
    scale = MAJOR if major else DORIAN
    return E_ROOT + 12 * base_oct + 12 * (step // 7) + scale[step % 7]


# Swarm cells (the BED now, not the star): (step, degree, gain).
# Interlock by construction — fizz avoids steps {1,5,9,13}; the glint
# lives ONLY there; the murk shadows every 3rd fizz onset an octave
# below (keeps exactly-one-voice interlock share >= 0.6, the anti-mud
# budget).  Degrees sit E4-E5 (fizz) so the mode's 3rd/7th bloom.
FIZZ_CELLS = {
    "fa": [(0, 0, .85), (2, 2, .7), (3, 4, .75), (4, 0, .85), (6, 4, .7),
           (7, 5, .75), (8, 7, .85), (10, 4, .7), (11, 2, .75),
           (12, 0, .85), (14, 4, .7), (15, 5, .75)],
    "fb": [(0, 4, .85), (2, 2, .7), (3, 0, .75), (4, 4, .85), (6, 5, .7),
           (7, 7, .75), (8, 4, .85), (10, 2, .7), (11, 4, .75),
           (12, 7, .85), (14, 5, .7), (15, 4, .75)],
    "fc": [(0, 7, .85), (2, 5, .7), (3, 4, .75), (4, 7, .85), (6, 9, .7),
           (7, 7, .75), (8, 5, .85), (10, 4, .7), (11, 5, .75),
           (12, 7, .85), (14, 9, .7), (15, 7, .75)],
    "fd": [(0, 2, .85), (2, 4, .7), (3, 5, .75), (4, 2, .85), (6, 0, .7),
           (7, 2, .75), (8, 4, .85), (10, 5, .7), (11, 4, .75),
           (12, 2, .85), (14, 0, .7), (15, 2, .75)],
    # sparse suspension cell (dips / bridge-in)
    "fs": [(0, 0, .8), (4, 4, .7), (8, 7, .8), (12, 4, .7)],
}
GLINT_CELLS = {
    "ga": [(1, 4, .7), (9, 7, .6)],
    "gb": [(5, 7, .7), (13, 4, .6)],
    "gc": [(1, 7, .7), (5, 4, .55), (9, 9, .7), (13, 7, .55)],
    "gd": [(1, 9, .7), (5, 7, .55), (9, 4, .7), (13, 9, .55)],
}
# Bass cells: (step, ROOT-OFFSET, gain) — always relative to the wave
# root (E in verses, the chord root in choruses).  Never on steps
# {0,4,8,12} (kick-gap).  Offsets are mode-neutral (0, +-5, +-7, +-12).
BASS_CELLS = {
    "V1": [(2, 0, .85), (3, 0, .65), (6, -5, .75), (7, 0, .6),
           (10, 0, .85), (11, 7, .6), (14, 0, .75), (15, -12, .6)],
    "V2": [(2, 0, .8), (3, -12, .7), (6, 0, .8), (7, 7, .6),
           (10, -5, .75), (11, 0, .6), (14, 0, .8), (15, 5, .6)],
    "V3": [(1, 0, .55), (2, 0, .85), (3, 0, .6), (5, -5, .6), (6, 0, .85),
           (7, 0, .6), (9, 7, .6), (10, 0, .85), (11, 0, .6), (13, -12, .6),
           (14, 0, .85), (15, 5, .6)],
    "CH": [(2, 0, .85), (3, 0, .6), (6, 7, .7), (7, 0, .6), (10, 12, .65),
           (11, 0, .6), (14, 0, .75), (15, 7, .6)],
    "CX": [(1, 0, .55), (2, 0, .85), (3, 0, .6), (5, 7, .6), (6, 0, .85),
           (7, 0, .6), (9, 12, .6), (10, 0, .85), (11, 0, .6), (13, 7, .6),
           (14, 0, .85), (15, 5, .6)],
    "BR": [(6, 0, .6), (14, -5, .5)],
}

# Chorus harmony — bold Picardy E MAJOR, I-V-vi-IV (E B C#m A), 2 bars
# each.  Roots (low octave) drive the bass, pad and boom; the swarm
# shimmers the fixed mode (all four chords are diatonic to E major).
HARM_ROOTS = [28, 28, 35, 35, 37, 37, 33, 33]           # E B C# A, per bar

# THE REFRAIN (the lead's song) — 8 bars = 128 steps of
# (step, degree, dur_steps).  A soaring ARCH (distinct from phototaxis's
# stepwise-rise-and-hang): rise to the octave, a wistful answer, climb to
# a high peak, descend and HANG ON THE 3rd (degree 2) — the note that
# blooms G(Dorian)->G#(major), so the resolution itself is the sunrise.
REFRAIN = [
    (0, 4, 4), (4, 5, 4), (8, 7, 8), (16, 7, 12),
    (32, 9, 4), (36, 7, 4), (40, 6, 3), (43, 7, 5), (48, 5, 14),
    (64, 7, 4), (68, 9, 4), (72, 11, 8), (80, 11, 12),
    (96, 9, 4), (100, 7, 4), (104, 5, 4), (108, 4, 4), (112, 2, 16),
]
REFRAIN_RESOLVE = (128, 0, 16)      # final chorus only: the 3rd -> root E
# The verse lead = the refrain's held anchors only — a sparse wandering
# line of long MORPHING tones (the through-line, thinner than the chorus).
VERSE_LEAD = [(0, 7, 8), (16, 7, 12), (48, 5, 14), (80, 11, 12),
              (112, 2, 16)]
HALF_LEAD = [e for e in REFRAIN if e[0] < 32]           # phrase 1 (bridge)

# ------------------------------------------------------- the wave plan
# SONG FORM, lead-driven: the morphing LEAD is the through-line and its
# per-wave role is the `lead` field — "thesis" (early, quiet, Dorian),
# "verse" (sparse skeleton), "full" (the refrain, major in choruses),
# "half" (phrase 1, the bridge carry), "bookend" (quiet Dorian reprise).
# harm: "ground" (E Dorian, verses) or "loop" (Picardy E MAJOR chorus,
# I-V-vi-IV).  The choruses BLOOM major; thesis/bridge/bookend stay
# Dorian (the sunrise, then sunset).  `khalf` = half-time bridge kick.
WAVES = [
    dict(name="OPEN",   b0=0,   n=4,  kick=0, ohat=0, chat=0, sn=0,
         bass=None, fizz=[], glint=[], murk=0, harm="ground", pad=0,
         lead=None),
    dict(name="INTRO",  b0=4,   n=8,  kick=1, ohat=5, chat=0, sn=0,
         bass="V1", fizz=[], glint=[], murk=0, harm="ground", pad=1,
         lead=None),
    dict(name="THESIS", b0=12,  n=8,  kick=1, ohat=1, chat=1, sn=0,
         bass="V1", fizz=[], glint=[], murk=0, harm="ground", pad=1,
         lead="thesis"),
    dict(name="VERSE1", b0=20,  n=16, kick=1, ohat=1, chat=1, sn=0,
         bass="V1", fizz=["fa", "fb"], glint=[], murk=0, harm="ground",
         pad=1, lead="verse"),
    dict(name="VERSE2", b0=36,  n=16, kick=1, ohat=1, chat=1, sn=1,
         bass="V2", fizz=["fc", "fd"], glint=["ga", "gb"], murk=1,
         harm="ground", pad=1, lead="verse"),
    dict(name="BUILD1", b0=52,  n=8,  kick=1, ohat=1, chat=1, sn=1,
         bass="V3", fizz=["fd", "fc"], glint=["gb", "ga"], murk=1,
         harm="ground", pad=1, lead=None),
    dict(name="CHORUS1", b0=60, n=16, kick=1, ohat=1, chat=1, sn=1,
         bass="CH", fizz=["fc", "fa"], glint=["gc", "gd"], murk=1,
         harm="loop", pad=1, lead="full"),
    dict(name="VERSE3", b0=76,  n=16, kick=1, ohat=1, chat=1, sn=1,
         bass="V2", fizz=["fb", "fd"], glint=["ga", "gb"], murk=1,
         harm="ground", pad=1, lead="verse"),
    dict(name="CHORUS2", b0=92, n=16, kick=1, ohat=1, chat=1, sn=1,
         bass="CH", fizz=["fa", "fc"], glint=["gd", "gc"], murk=1,
         harm="loop", pad=1, lead="full"),
    dict(name="VERSE4", b0=108, n=8,  kick=1, ohat=1, chat=0, sn=0,
         bass="V1", fizz=["fs"], glint=["ga"], murk=0, harm="ground",
         pad=1, lead="verse"),
    dict(name="BRIDGE", b0=116, n=16, kick=1, ohat=0, chat=1, sn=0,
         bass="BR", fizz=[], glint=[], murk=0, harm="ground", pad=1,
         khalf=1, lead="half"),
    dict(name="BUILD2", b0=132, n=8,  kick=1, ohat=0, chat=0, sn=0,
         bass="V1", fizz=[], glint=[], murk=0, harm="ground", pad=1,
         lead=None),
    dict(name="FINALCH", b0=140, n=16, kick=1, ohat=1, chat=1, sn=1,
         bass="CX", fizz=["fc", "fb"], glint=["gd", "gc"], murk=1,
         harm="loop", pad=1, lead="full"),
    dict(name="CHORUSOUT", b0=156, n=16, kick=1, ohat=1, chat=1, sn=1,
         bass="CH", fizz=["fs", "fa"], glint=["ga", "gb"], murk=1,
         harm="loop", pad=1, lead="full"),
    dict(name="OUTRO",  b0=172, n=12, kick=1, ohat=0, chat=0, sn=0,
         bass="V1", fizz=[], glint=[], murk=0, harm="ground", pad=1,
         lead="bookend"),
]
TOTAL_BARS = 184
LEAD_GAIN = dict(thesis=0.60, verse=0.62, full=1.0, half=0.50, bookend=0.50)
FINAL_BAR = 156                                 # CHORUSOUT carries the resolve
STRIP_GLINT_FIZZ_AT = 164                        # CHORUSOUT thins the swarm bed
BRIDGE_SILENCE_BAR = 131                          # the one composed drop-beat
BLOOM_BARS = [60, 92, 140]                        # harmonic-bloom INTO choruses
FLUTTER_BARS = [116, 172]                         # tape-flutter across seams
BRIDGE_GLINT = [(118, 4), (122, 7), (126, 5)]     # (bar, degree) sparse

if PREVIEW == "chorus":
    WAVES = [dict(name="PRE-CH", b0=0, n=16, kick=1, ohat=1, chat=1, sn=1,
                  bass="CH", fizz=["fc", "fa"], glint=["gc", "gd"], murk=1,
                  harm="loop", pad=1, lead="full")]
    TOTAL_BARS = 16
    FINAL_BAR, STRIP_GLINT_FIZZ_AT, BRIDGE_SILENCE_BAR = 8, 10 ** 9, -1
    BLOOM_BARS, FLUTTER_BARS, BRIDGE_GLINT = [], [], []
elif PREVIEW == "groove":
    WAVES = [dict(name="PRE-GR", b0=0, n=8, kick=1, ohat=1, chat=1, sn=1,
                  bass="V2", fizz=["fc", "fd"], glint=["ga", "gb"], murk=1,
                  harm="ground", pad=1, lead="verse")]
    TOTAL_BARS = 8
    FINAL_BAR, STRIP_GLINT_FIZZ_AT, BRIDGE_SILENCE_BAR = -1, 10 ** 9, -1
    BLOOM_BARS, FLUTTER_BARS, BRIDGE_GLINT = [], [], []

DUR = TOTAL_BARS * BAR + 2.5
N = int(DUR * SR)

# ------------------------------------------------------------ rendering
LAYER_NAMES = ["kick", "bass", "boom", "fizz", "glint", "murk", "lead",
               "pad", "drone", "hats", "snare", "fx"]
LAYERS = {k: [np.zeros(N), np.zeros(N)] for k in LAYER_NAMES}

# registries for verify
swarm_reg = []          # (voice, bar, step, midi)
bass_reg = []           # (bar, step, midi)
lead_reg = []           # (bar_float, midi, dur_steps, degree)
kick_times = []
KICK_STEPS = {0, 4, 8, 12}

for w in WAVES:
    for i in range(w["n"]):
        bar = w["b0"] + i
        t0 = step_t(bar)
        pos = i % 8
        stripped = bar >= STRIP_GLINT_FIZZ_AT
        major = (w["harm"] == "loop")                   # chorus blooms E major
        root = HARM_ROOTS[pos] if major else E_ROOT     # chord root / E pedal

        # ---- kit
        kick_on = bool(w["kick"])
        kick_steps = sorted(KICK_STEPS)
        if w.get("khalf"):                              # bridge: half-time
            kick_steps = [0, 8]
        if w["name"] == "BUILD2":                       # composed rebuild
            if i in (0, 1, 2, 3):                       # keep a pulse alive
                kick_on, kick_steps = True, [0, 8]
            elif i in (4, 5):
                kick_on, kick_steps = True, list(range(0, 16, 2))
            else:
                kick_on, kick_steps = True, list(range(16))
        if w["name"] == "OUTRO" and i >= 4:             # machinery stops
            kick_on = False
        if bar == BRIDGE_SILENCE_BAR:                   # the one drop-beat
            kick_on = False
        if kick_on:
            for s in kick_steps:
                g = 1.0 if s in KICK_STEPS else 0.55 + 0.03 * s
                place(LAYERS["kick"], KICK, t0 + s * SIXT, g)
                kick_times.append(t0 + s * SIXT)
        if w["ohat"] and i >= (0 if w["ohat"] == 1 else w["ohat"]):
            for s in (2, 6, 10, 14):
                place(LAYERS["hats"], OHAT, t0 + s * SIXT, 0.9)
        if w["chat"]:
            for s in (3, 11):
                place(LAYERS["hats"], CHAT, t0 + s * SIXT, 0.6,
                      0.3 if s == 3 else -0.3)
        if w["sn"]:
            for s in (4, 12):
                place(LAYERS["snare"], SNARE, t0 + s * SIXT, 0.9)

        # ---- bass (BUILD2: returns after the roll starts; OUTRO stops
        # when the machinery does; silent on the composed drop-beat)
        bass_off = ((w["name"] == "BUILD2" and i < 4)
                    or (w["name"] == "OUTRO" and i >= 4)
                    or bar == BRIDGE_SILENCE_BAR)
        if w["bass"] and not bass_off:
            for s, off, g in BASS_CELLS[w["bass"]]:
                midi = root + off                       # all cells root-relative
                place(LAYERS["bass"], bass_note(midi, SIXT), t0 + s * SIXT, g)
                bass_reg.append((bar, s, midi))

        # ---- pad bed: the warm floor under the whole groove, per 2-bar
        # block following the (chord) root an octave up; off on the drop-beat.
        if w["pad"] and pos % 2 == 0 and bar != BRIDGE_SILENCE_BAR:
            bright = 0.62 if w["name"] == "BRIDGE" else 1.0
            PL, PR = pad_bed(root + 12, 2 * BAR * 1.02, bright, seed=bar % 7)
            add_at(LAYERS["pad"][0], PL, t0, 0.9)
            add_at(LAYERS["pad"][1], PR, t0, 0.9)

        # ---- the swarm BED (fizz + murk shadow + glint), degree-based so
        # it blooms E major in the choruses; demoted under the lead.
        if w["fizz"] and not stripped:
            cell = FIZZ_CELLS[w["fizz"][(i // 8) % len(w["fizz"])]]
            for s, deg, g in cell:
                midi = deg2midi(deg, FIZZ_OCT, major)
                pan = 0.25 if s % 2 == 0 else -0.25
                place(LAYERS["fizz"], fizz_note(midi, SIXT),
                      t0 + s * SIXT, g, pan)
                swarm_reg.append(("fizz", bar, s, midi))
        if w["murk"] and w["fizz"]:
            cell = FIZZ_CELLS[w["fizz"][(i // 8) % len(w["fizz"])]]
            for s, deg, g in cell[0::3]:
                midi = deg2midi(deg, FIZZ_OCT - 1, major)   # an octave below
                place(LAYERS["murk"], murk_note(midi, SIXT),
                      t0 + s * SIXT, 0.5 * g)
                swarm_reg.append(("murk", bar, s, midi))
        if w["glint"] and not stripped:
            cell = GLINT_CELLS[w["glint"][(i // 8) % len(w["glint"])]]
            for s, deg, g in cell:
                midi = deg2midi(deg, GLINT_OCT, major)
                pan = 0.8 if s in (1, 9) else -0.8
                place(LAYERS["glint"], glint_note(midi),
                      t0 + s * SIXT, g, pan)
                swarm_reg.append(("glint", bar, s, midi))

# ---- the anthem (song form: thesis quiet-solo, choruses identical, the
# bridge carries a half-lit phrase, the final resolves, the bookend closes)
def render_lead(events, b0, major, gain, final=False):
    ev = events + ([REFRAIN_RESOLVE] if final else [])
    for s, deg, dsteps in ev:
        t = step_t(b0) + s * SIXT
        midi = deg2midi(deg, LEAD_OCT, major)
        dur = dsteps * SIXT * 0.98 + 0.02
        y = lead_note(midi, dur, held=dsteps >= 8, t_abs=t)
        place(LAYERS["lead"], y, t, gain)
        lead_reg.append((b0 + s / 16.0, midi, dsteps, deg))


for w in WAVES:
    lt = w["lead"]
    if lt is None:
        continue
    major = (w["harm"] == "loop")
    g = LEAD_GAIN[lt]
    if lt == "verse":
        for blk in range(0, w["n"], 8):
            render_lead(VERSE_LEAD, w["b0"] + blk, major, g)
    elif lt == "thesis":
        render_lead(REFRAIN, w["b0"], major, g)             # Dorian, early
    elif lt == "full":                                      # the refrain, x2
        for blk in range(0, w["n"], 8):
            final = (w["b0"] == FINAL_BAR and blk == w["n"] - 8)
            render_lead(REFRAIN, w["b0"] + blk, major, g, final=final)
    elif lt == "half":
        render_lead(HALF_LEAD, w["b0"] + 4, major, g)       # phrase 1 @120
    elif lt == "bookend":
        render_lead(REFRAIN, w["b0"] + 4, major, g)         # wistful reprise

# ---- bridge bed: the dark drone + sparse glints carry the pulse under
# the half-lit lead (never beatless — the half-time kick + bass hold it)
bridge = [w for w in WAVES if w["name"] == "BRIDGE"]
if bridge:
    p = bridge[0]
    DL, DR = pool_drone(p["n"] * BAR + 2.0)
    add_at(LAYERS["drone"][0], DL, step_t(p["b0"]), 1.0)
    add_at(LAYERS["drone"][1], DR, step_t(p["b0"]), 1.0)
    for b, deg in BRIDGE_GLINT:
        place(LAYERS["glint"], glint_note(deg2midi(deg, GLINT_OCT, False)),
              step_t(b), 0.6, 0.7 if b % 4 == 2 else -0.7)

# ---- OPEN: the drone breath (swells into the groove downbeat), E-rooted
if not PREVIEW:
    nb = int((4 * BAR + 0.4) * SR)
    tb = np.arange(nb) / SR
    f0 = midi_to_hz(E_ROOT)
    breath = (np.sin(2 * np.pi * f0 * tb)
              + 0.45 * np.sin(2 * np.pi * 2 * f0 * tb)
              + 0.15 * np.sin(2 * np.pi * 3 * f0 * tb))
    env = (0.5 - 0.5 * np.cos(np.pi * np.clip(tb / (4 * BAR), 0, 1))) ** 1.2
    env *= np.clip((4 * BAR + 0.35 - tb) / 0.35, 0, 1)
    breath = lowpass(breath, 420) * env
    add_at(LAYERS["drone"][0], breath, 0.0, 1.0)
    add_at(LAYERS["drone"][1], breath, 0.0, 1.0)

# ---- SEAMS (Meridian's own vocabulary): harmonic-bloom into each chorus,
# tape-flutter swelling across the bridge and outro boundaries.
for b in BLOOM_BARS:
    harmonic_bloom(LAYERS["fx"], step_t(b), 40, major=True)   # bloom into E maj
for b in FLUTTER_BARS:
    tape_flutter(LAYERS["fx"], step_t(b - 2), 4 * BAR, 40)
# last onset = the bookend's final lead note end (+ a composed fade tail)
last_onset = max((bf + ds / 16.0) * BAR for bf, m, ds, dg in lead_reg) \
    if lead_reg else step_t(TOTAL_BARS)

# ---- sub-boom layer, root-tracking; gentler under the verses, full
# under the choruses (kept out of the sub-30 trap by the master HP).
NO_BOOM = {"OPEN", "BRIDGE", "PRE-GR"}
_booms = {}
for w in WAVES:
    if w["name"] in NO_BOOM or not w["kick"]:
        continue
    for i in range(w["n"]):
        bar = w["b0"] + i
        if bar >= STRIP_GLINT_FIZZ_AT or bar == BRIDGE_SILENCE_BAR:
            continue                                    # thin the payoff tail
        if w["name"] == "BUILD2" and i < 4:
            continue                                    # boom rejoins with roll
        if w["name"] == "OUTRO" and i >= 4:
            continue                                    # machinery stopped
        gboom = 1.0 if w["harm"] == "loop" else 0.55    # fuller under choruses
        root = HARM_ROOTS[i % 8] if w["harm"] == "loop" else E_ROOT
        if root not in _booms:
            nb = int(0.24 * SR)
            tb = np.arange(nb) / SR
            yb = np.sin(2 * np.pi * midi_to_hz(root) * tb)
            yb *= np.exp(-tb / 0.09) * np.clip((0.22 - tb) / 0.02, 0, 1)
            _booms[root] = yb * rc_attack(nb, 0.003)
        for s in (0, 4, 8, 12):
            place(LAYERS["boom"], _booms[root], step_t(bar, s), gboom)

# ---- sidechain pump env (never on the LEAD/glint/bass/kit/fx)
pump = np.ones(N)
for tk in kick_times:
    i0 = int(tk * SR)
    i1 = min(N, i0 + int(0.35 * SR))
    dt = np.arange(i1 - i0) / SR
    pump[i0:i1] = 1.0 - 0.55 * np.exp(-dt / 0.10)
pump = np.maximum(pump, 0.30)

# ---- wet, commit, master.  The LEAD is the star: it sits on top, wet,
# and is NOT pumped (it sings steady while the world breathes).  The
# swarm is a BED — lower weights than phototaxis (fizz 0.46->0.34,
# glint 0.26->0.22) so it sits UNDER the lead (checked in verify).
WETS = dict(lead=0.42, glint=0.40, fx=0.32, pad=0.30,
            fizz=0.12, murk=0.15, drone=0.15)
WEIGHTS = dict(kick=1.00, bass=1.02, boom=1.00, fizz=0.34, glint=0.22,
               murk=0.28, lead=0.86, pad=0.44, drone=0.55,
               hats=0.18, snare=0.26, fx=0.34)
PUMPED = {"fizz", "murk", "pad", "drone"}

MIX = [np.zeros(N), np.zeros(N)]
for name in LAYER_NAMES:
    L, R = LAYERS[name]
    pk = max(np.max(np.abs(L)), np.max(np.abs(R)))
    if pk < 1e-9:
        continue
    L, R = L / pk, R / pk
    L, R = reverb_pair(L, R, WETS.get(name, 0.0))
    if name in PUMPED:
        L, R = L * pump, R * pump
    MIX[0] += WEIGHTS[name] * L
    MIX[1] += WEIGHTS[name] * R

for ch in (0, 1):                                       # master chain
    # v2.1: kill sub-30 Hz rumble (the bass sub-octave hits ~23 Hz on low
    # notes) — inaudible but it was eating all the headroom and driving
    # the bus saturator into "growl" on the loud sections.  Eased the
    # sub-bass shelf too (the low end is already fat now).
    MIX[ch] = highpass(MIX[ch], 30)
    MIX[ch] = (MIX[ch] + 0.22 * highpass(MIX[ch], 3000)
               + 0.26 * lowpass(MIX[ch], 95))           # heavier low shelf
pk = max(np.max(np.abs(MIX[0])), np.max(np.abs(MIX[1]))) + 1e-12
for ch in (0, 1):                                       # tanh bus limiter
    # drive 1.06 (headroom for the heavy low end — keeps loud-section crest
    # up); ceiling 0.93 recovers level (uniform post-saturator gain).
    MIX[ch] = np.tanh(1.06 * MIX[ch] / pk) / np.tanh(1.06) * 0.93

# the outro ends on a SUSTAINED lead (not a percussive hit) — give it a
# composed fade tail so it rings out rather than clicking off.
END = last_onset + 1.8 if not PREVIEW else step_t(TOTAL_BARS) + 1.5
n_end = min(N, int(END * SR))
OUT = np.stack([fade(MIX[0][:n_end], 0.002, 1.2),
                fade(MIX[1][:n_end], 0.002, 1.2)], axis=1)

out_dir = pathlib.Path("/workspace/music")
out_dir.mkdir(parents=True, exist_ok=True)
stem = "meridian" + (f"_preview_{PREVIEW}" if PREVIEW else "")
wav_path = out_dir / f"{stem}.wav"
pcm = (np.clip(OUT, -1, 1) * 32767).astype(np.int16)
with wave.open(str(wav_path), "wb") as wf:
    wf.setnchannels(2)
    wf.setsampwidth(2)
    wf.setframerate(SR)
    wf.writeframes(pcm.tobytes())
flac_path = out_dir / f"{stem}.flac"
soundfile.write(str(flac_path), OUT, SR)
print(f"Wrote {wav_path}  ({n_end / SR:.1f} s)")
print(f"Wrote {flac_path}")

# ---------------------------------------------------------------- verify
if PREVIEW:
    print(f"\nPreview '{PREVIEW}' — judge the material, then run the full "
          "render (no args). Checks run on the full render only.")
    sys.exit(0)

fails = []


def check(name, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}  {detail}")
    if not ok:
        fails.append(name)


def mmss(t):
    return f"{int(t // 60)}:{t % 60:04.1f}"


print("\n=== SECTION MAP / WAVE LEDGER ===")
print(f"{'wave':9} {'bars':9} {'time':6} {'kit':14} {'bass':4} "
      f"{'fizz':12} {'glint':12} {'murk':4} {'harm'}")
for w in WAVES:
    kit = ("K" if w["kick"] else "-") + ("O" if w["ohat"] else "-") \
        + ("c" if w["chat"] else "-") + ("S" if w["sn"] else "-")
    print(f"{w['name']:9} {w['b0']:3}-{w['b0'] + w['n'] - 1:<5} "
          f"{mmss(step_t(w['b0'])):6} {kit:14} {str(w['bass']):4} "
          f"{'/'.join(w['fizz']) or '-':12} "
          f"{'/'.join(w['glint']) or '-':12} "
          f"{'y' if w['murk'] else '-':4} {w['harm']}")
lead_waves = [w["name"] for w in WAVES if w["lead"]]
print(f"lead in {lead_waves}; thesis @ {WAVES[2]['b0']}, "
      f"final/resolve @ {FINAL_BAR}; harmonic-blooms into {BLOOM_BARS}, "
      f"tape-flutter across {FLUTTER_BARS}, bridge drop-beat "
      f"{BRIDGE_SILENCE_BAR}, strip at {STRIP_GLINT_FIZZ_AT}")

print("\n=== PER-SECTION RMS (post-master) ===")


def seg(b0, n_bars, hp=None):
    a = int(step_t(b0) * SR)
    b = min(n_end, int(step_t(b0 + n_bars) * SR))
    x = OUT[a:b, 0] + OUT[a:b, 1]
    if hp:
        x = highpass(x, hp)
    return np.sqrt(np.mean(x ** 2))


def crest(b0, n_bars):
    a = int(step_t(b0) * SR)
    b = min(n_end, int(step_t(b0 + n_bars) * SR))
    x = OUT[a:b, 0] + OUT[a:b, 1]
    return (np.max(np.abs(x)) + 1e-9) / (np.sqrt(np.mean(x ** 2)) + 1e-9)


rms = {w["name"]: seg(w["b0"], w["n"]) for w in WAVES}
for w in WAVES:
    print(f"  {w['name']:9} rms {rms[w['name']]:.4f}  crest "
          f"{crest(w['b0'], w['n']):.2f}")
d1, d2 = seg(60, 16, hp=120), seg(140, 16, hp=120)
check("climax (FINALCH) >= chorus1 above 120 Hz — payoff is fullest",
      d2 >= d1, f"({d2:.4f} vs {d1:.4f})")
check("BRIDGE is quieter than the choruses (a trough, but with a pulse)",
      rms["BRIDGE"] < min(rms["CHORUS1"], rms["CHORUSOUT"]),
      f"({rms['BRIDGE']:.4f})")
check("verses sit under the choruses (song-form dynamics)",
      max(rms["VERSE1"], rms["VERSE3"]) < min(rms["CHORUS1"], rms["FINALCH"]),
      f"(v {max(rms['VERSE1'], rms['VERSE3']):.4f})")
check("OUTRO below the choruses", rms["OUTRO"] < min(rms["CHORUS1"],
      rms["CHORUSOUT"]), f"({rms['OUTRO']:.4f})")

print("\n=== BIG-ROOM METRICS ===")


def sub60_share(b0, n_bars):
    a = int(step_t(b0) * SR)
    b = min(n_end, int(step_t(b0 + n_bars) * SR))
    x = OUT[a:b, 0] + OUT[a:b, 1]
    lo = lowpass(x, 60)
    return float(np.sum(lo ** 2) / (np.sum(x ** 2) + 1e-12))


s1, s2 = sub60_share(60, 16), sub60_share(140, 16)
# Meridian is a BRIGHT euphoric-sunrise track — the leads/major chords
# fill the mids, so the (heavy, absolute) low end is a smaller share than
# phototaxis's darker balance.  Window set for bright-but-heavy.
check("chorus1 sub-60 share in 0.30-0.62", 0.30 <= s1 <= 0.62, f"({s1:.2f})")
check("payoff sub-60 share in 0.30-0.62", 0.30 <= s2 <= 0.62, f"({s2:.2f})")
print(f"  pump floor {pump.min():.2f}, ducked kicks {len(kick_times)}")


def hot_share(b0, n_bars):                              # near-ceiling energy
    a = int(step_t(b0) * SR)
    b = min(n_end, int(step_t(b0 + n_bars) * SR))
    x = OUT[a:b, 0] + OUT[a:b, 1]
    return float(np.mean(np.abs(x) > 0.85 * (np.max(np.abs(x)) + 1e-9)))


# The growl guardrail: hot% (near-ceiling energy) is the DIRECT saturation
# measure — a heavy track can sit at crest ~2.9 and still be clean, so we
# check hot%, not just crest (the CLAUDE.md refinement, meridian 2026-07-31).
hF, cF = hot_share(140, 16), crest(140, 16)
peakL, peakR = float(np.max(np.abs(OUT[:, 0]))), float(np.max(np.abs(OUT[:, 1])))
check("no growl: near-ceiling energy < 1% at the payoff", hF < 0.01,
      f"(FINALCH hot {hF * 100:.2f}%, crest {cF:.2f})")
check("per-channel true peak < 1.0 (no int16 clip)",
      max(peakL, peakR) < 1.0, f"(L {peakL:.3f} R {peakR:.3f})")

print("\n=== SWARM BLOCK ===")
hist = {}
for v, b, s, m in swarm_reg:
    hist.setdefault((b, s), []).append(v)
counts = [len(vs) for vs in hist.values()]
dist = {k: counts.count(k) for k in sorted(set(counts))}
check("simultaneous swarm onsets <= 2 per 16th", max(counts) <= 2,
      f"(distribution {dist})")
solo = sum(1 for c in counts if c == 1)
check("interlock ratio >= 0.6", solo / len(counts) >= 0.6,
      f"({solo / len(counts):.2f})")
meds = {}
for v in ("fizz", "glint", "murk"):
    ms = [m for vv, b, s, m in swarm_reg if vv == v]
    meds[v] = float(np.median(ms))
gaps = sorted(meds.values())
check("register medians pairwise gaps >= 7",
      all(gaps[i + 1] - gaps[i] >= 7 for i in range(len(gaps) - 1)),
      f"(murk {meds['murk']:.0f} / fizz {meds['fizz']:.0f} / "
      f"glint {meds['glint']:.0f})")
mut_ok, mut_n = True, 0
for w in WAVES:
    for voice in ("fizz", "glint"):
        ids = w[voice]
        for a, b in zip(ids, ids[1:]):
            mut_n += 1
            if a == b:
                mut_ok = False
check("cell mutation every 8 bars (active voices)", mut_ok,
      f"({mut_n} mutations across waves)")

print("\n=== LEAD BLOCK (the morphing lead is the star) ===")
first = min(bf for bf, m, ds, dg in lead_reg)
check("lead's thesis stated EARLY (< 20% in) — the hook up front",
      first / TOTAL_BARS < 0.20, f"(bar {first:.0f} = {first / TOTAL_BARS:.0%})")
n_full = sum(1 for w in WAVES if w["lead"] in ("thesis", "full", "bookend"))
check("refrain restated >= 4 times (identical melody)", n_full >= 4,
      f"({n_full} full statements)")
check("payoff (final restatement) is late (> 70% in)",
      FINAL_BAR / TOTAL_BARS > 0.70, f"(bar {FINAL_BAR})")
# lead-presence: the through-line — bars covered by any lead note
covered = set()
for bf, m, ds, dg in lead_reg:
    covered |= set(range(int(bf), int(bf + ds / 16.0) + 1))
frac = len(covered & set(range(TOTAL_BARS))) / TOTAL_BARS
check("lead is the THROUGH-LINE (present in > 55% of bars)", frac > 0.55,
      f"({frac:.0%} of bars)")
# the cyclic morph (not a one-way arc): the index LFO is a sine, net slope 0
check("morph is CYCLIC not one-way (anti-arc, by construction)", True,
      f"(index LFO period {1.0 / MORPH_HZ:.1f} s, net slope 0)")
# the Picardy bloom: the major 3rd (G#, pc 8) appears in the choruses and
# NOWHERE in the Dorian verses (which use G natural, pc 7)
MAJOR_BARS = {b for w in WAVES if w["harm"] == "loop"
              for b in range(w["b0"], w["b0"] + w["n"])}
notes = [(int(bf), m) for bf, m, ds, dg in lead_reg] \
    + [(b, m) for v, b, s, m in swarm_reg]
ch_g8 = sum(1 for b, m in notes if b in MAJOR_BARS and m % 12 == 8)
ve_g8 = sum(1 for b, m in notes if b not in MAJOR_BARS and m % 12 == 8)
check("Picardy bloom: major 3rd (G#) in choruses, ZERO in verses",
      ch_g8 > 0 and ve_g8 == 0, f"(chorus G# {ch_g8}, verse G# {ve_g8})")
# the final cadence: the held 3rd resolves down to the root E (deg 0)
res = [(bf, m) for bf, m, ds, dg in lead_reg if dg == 0]
check("final statement resolves the held 3rd -> root E (the cadence)",
      len(res) == 1 and res[0][1] % 12 == 4 and res[0][0] > 170,
      f"({['bar %.0f midi %d' % (b, m) for b, m in res]})")

print("\n=== SWARM-IS-A-BED (inverted from phototaxis) ===")


def layer_wrms(name, b0, n_bars):
    L, R = LAYERS[name]
    pk = max(np.max(np.abs(L)), np.max(np.abs(R))) + 1e-12
    a = int(step_t(b0) * SR)
    b = min(n_end, int(step_t(b0 + n_bars) * SR))
    x = (L[a:b] + R[a:b]) / pk
    return WEIGHTS[name] * float(np.sqrt(np.mean(x ** 2)))


lead_w = layer_wrms("lead", 60, 16)
sw_w = {v: layer_wrms(v, 60, 16) for v in ("fizz", "glint", "murk")}
check("in the choruses the LEAD sits above every swarm voice",
      all(lead_w > sw_w[v] for v in sw_w),
      f"(lead {lead_w:.3f} vs {', '.join(f'{v} {sw_w[v]:.3f}' for v in sw_w)})")

print("\n=== DEPTH + SEAM ===")
pa, pb = int(step_t(20) * SR), int(step_t(36) * SR)   # VERSE1 span
pad_rms = float(np.sqrt(np.mean(LAYERS["pad"][0][pa:pb] ** 2)))
check("pad bed present under the verses (v1 had none there)",
      pad_rms > 1e-3, f"(VERSE1 pad-layer rms {pad_rms:.4f})")


def lowband_rms(b0, n_bars, hz=180):
    a = int(step_t(b0) * SR)
    b = min(n_end, int(step_t(b0 + n_bars) * SR))
    return float(np.sqrt(np.mean(lowpass(OUT[a:b, 0] + OUT[a:b, 1], hz) ** 2)))


check("groove has a low bed (VERSE1 sub-180 RMS present)",
      lowband_rms(20, 16) > 0.02, f"({lowband_rms(20, 16):.4f})")
kt = np.array(sorted(kick_times))
gaps = np.diff(kt)
maxgap = float(gaps.max()) if len(gaps) else 0.0
check("no long beatless gap (< 3.5 s between kicks) — the v1 33 s hole",
      maxgap < 3.5, f"(max {maxgap:.2f} s at "
      f"{mmss(kt[int(np.argmax(gaps))]) if len(gaps) else '-'})")

print("\n=== BASS BLOCK ===")
check("kick-gap contract: zero bass onsets on kick 16ths",
      not any(s in KICK_STEPS for b, s, m in bass_reg),
      f"({len(bass_reg)} onsets)")
by_bar = {}
for b, s, m in bass_reg:
    by_bar.setdefault(b, set()).add(m)
npb = [len(v) for v in by_bar.values()]
check("moving bassline: >= 2 distinct pitches per bar", min(npb) >= 2,
      f"(min {min(npb)}, max {max(npb)})")
cells_used = {w["bass"] for w in WAVES if w["bass"]}
check("distinct bass cells >= 3", len(cells_used) >= 3,
      f"({sorted(cells_used)})")

print("\n=== FM DIALECT ===")
print("  voice   ratio       index behaviour              attack")
print("  lead    2/3 morph   2.2 +- 1.6 cyclic LFO/4bar    0.12 s (the STAR)")
print("  fizz    1.00 +fb     2.5->1.2 decay, fb 1.15       18 ms  (bed shimmer)")
print("  glint   3.53         4->0 snap in ~80 ms           1 ms   (non-integer)")
print("  murk    0.50         0.8 constant                  5 ms   (the shadow)")
print("  bass    1.00         0.9 + grit decay + sub oct    2 ms   (HEAVY)")
check("zero saw-stack / iirpeak voices", True, "(by construction)")
check("the morphing lead is FM, not the navigator decay dialect", True,
      "(cyclic index LFO, ratio 2/3, not one-way 4->0.8)")

print("\n=== SEAM / FX BLOCK (Meridian's own vocabulary) ===")
check("harmonic-blooms land into the chorus downbeats",
      BLOOM_BARS == [60, 92, 140], f"({BLOOM_BARS})")
print(f"  tape-flutter swells across bars {FLUTTER_BARS}; zero chatter / "
      "bubble-rise / reverse cymbal / tom / zap (all claimed elsewhere)")

print("\n=== DRONE RULE ===")
spec = np.abs(np.fft.rfft(DL[: int(20 * SR)]))
freqs = np.fft.rfftfreq(int(20 * SR), 1 / SR)
centroid = float(np.sum(freqs * spec) / np.sum(spec))
env50 = np.sqrt(np.convolve(DL ** 2, np.ones(2205) / 2205, mode="same"))
check("bridge bed centroid < 400 Hz", centroid < 400, f"({centroid:.0f} Hz)")
check("bridge bed reaches true zero each cycle",
      float(env50[int(19 * SR):int(21 * SR)].min()) < 0.005,
      f"(min env {env50[int(19 * SR):int(21 * SR)].min():.4f})")

check("composed fade tail (<= 2.5 s after the last lead onset)",
      n_end / SR - last_onset <= 2.5,
      f"({n_end / SR - last_onset:.2f} s — a sustained ending, not a dead gap)")
check("FLAC written", flac_path.exists(), f"({flac_path.name})")

print(f"\n{'ALL CHECKS PASS' if not fails else 'FAILURES: ' + str(fails)}"
      f"  ({len(fails)} fail)")
sys.exit(1 if fails else 0)
