#!/usr/bin/env python3
"""
generate_sihaya.py — "Sihaya" (~6:00). The album's first actual SONG.

Verse / chorus / bridge form, a refrain sung four times, and
question-and-answer at three levels: inside every melody (antecedent
phrases ending off-tonic, consequents resolving to D), between
performers (a male and a female voice trading lines; instruments
echoing every vocal tail), and between sections (dark verses ask, the
major-D chorus answers; the bridge asks Theme A, the final chorus
answers it with the hook and Theme A sounding together).

The two lead voices are new instruments: the Sardaukar glottal source
made melodic (portamento, blooming vibrato, no guttural pulse) and sung
through TIME-INTERPOLATED vowel formants (the litany's i/e/a/o/u table)
— one vowel per note, crossfaded like a singer moving through words.
PAUL: baritone D3–B♭3. CHANI: an octave up, formants ×1.18, breathier.
Lyrics are vowel sequences; the refrain "text" is the title: i–a–a
("si-ha-ya"), identical in every chorus.

96 BPM, D Phrygian dominant, seed 2 (two voices, two moons).

  0:00  intro (4 bars): baliset arpeggio, low wind; Chani hums the hook
        answer half-voice — the thesis in the first ten seconds. Her
        last note rings across the verse downbeat.
  0:10  VERSE 1 (16): Paul sings two Q/A phrase-pairs; the oud echoes
        every tail. Baliset fingerpicking, gated bass, sparse frame drum.
  0:50  pre-chorus (8): 1-bar trades (Paul asks / Chani answers), then
        both rise together; frame roll + bass walk + her pickup note.
  1:10  CHORUS 1 (16): the refrain, 4 statements (Paul, Chani 8va, Paul,
        Chani), ney echoing her tails; full maqsum darbuka, quiet choir.
  1:50  VERSE 2 (16): roles swapped — Chani leads a varied melody, PAUL
        echoes her tails. Darbuka drops to half density, never leaves.
  2:30  pre-chorus (8): the trades overlap and the rise runs in canon,
        Chani one bar behind — development, not a repeat.
  2:50  CHORUS 2 (16): both voices in parallel octaves throughout, war
        drums on the cell downbeats, choir clearly audible.
  3:30  BRIDGE (20): teardown one layer per bar to baliset + wind while
        the duduk drifts Theme A fragments (never resolving); rebuild —
        the voices hum Theme A in alternation, strings swell, riser +
        frame roll crescendo, everything cuts on the last beat:
  4:19  one beat of near-silence — Chani's lone pickup hangs in it —
  4:20  CHORUS 3 (16): the band slams back on the downbeat, both voices
        in octaves, ney descant answering every cell.
  5:00  CHORUS 4 (16): the everything-chorus — choir doubles the hook,
        THEME A on the duduk as counter-line under the refrain, ney
        answers, the last line stretched ritardando across the seam.
  5:40  outro (4 + tail): band stops on one ringing strum; Chani hums
        the hook once more, half-voice over the arpeggio; a final quiet
        strum rings ~6 s into the wind. Fade.

Output: /workspace/music/sihaya.wav (stereo, 44100 Hz, 16-bit).
"""

import os
import wave
import numpy as np
from scipy import signal

SR = 44100
DURATION = 360.0
N = int(SR * DURATION)
t = np.arange(N) / SR

rng = np.random.default_rng(2)   # two voices, two moons

BPM = 96.0
BEAT = 60.0 / BPM
BAR = BEAT * 4
GRID0 = 0.4


def bar_t(b, beat=0.0):
    return GRID0 + b * BAR + beat * BEAT


# Section boundaries, in bars.
B_V1 = 4        # verse 1 (16)
B_PC1 = 20      # pre-chorus (8)
B_CH1 = 28      # CHORUS 1 (16)
B_V2 = 44       # verse 2 (16)
B_PC2 = 60      # pre-chorus 2 (8)
B_CH2 = 68      # CHORUS 2 (16)
B_BR = 84       # bridge teardown (8)
B_RB = 92       # bridge rebuild (12) — cuts on beat 4 of bar 103
B_CH3 = 104     # CHORUS 3 (16)
B_CH4 = 120     # CHORUS 4 (16)
B_OUT = 136     # outro (4 + tail)
B_END = 140

# ---------------------------------------------------------------- helpers

def midi_to_hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def fade(x, fade_in=0.2, fade_out=8.0):
    ni, no = int(fade_in * SR), int(fade_out * SR)
    x[:ni] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(ni) / ni)
    x[-no:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(no) / no)
    return x


def slow_noise(rate_hz, lo=0.0, hi=1.0):
    k = max(4, int(DURATION * rate_hz))
    pts = rng.standard_normal(k)
    pts = np.convolve(pts, np.ones(3) / 3, mode="same")
    ctrl = np.interp(t, np.linspace(0, DURATION, k), pts)
    ctrl = (ctrl - ctrl.min()) / (ctrl.max() - ctrl.min() + 1e-12)
    return lo + (hi - lo) * ctrl


def make_reverb_ir(seconds, decay, seed):
    r = np.random.default_rng(seed)
    n = int(seconds * SR)
    ir = r.standard_normal(n) * np.exp(-np.arange(n) / SR / decay)
    sos = signal.butter(2, 4000, "low", fs=SR, output="sos")
    ir = signal.sosfilt(sos, ir)
    return ir / np.sqrt(np.sum(ir ** 2))


def reverb(x, ir, wet=0.5):
    tail = signal.fftconvolve(x, ir)[: len(x)]
    tail /= np.max(np.abs(tail)) + 1e-12
    tail *= np.max(np.abs(x)) + 1e-12
    return (1 - wet) * x + wet * tail


def add_at(buf, x, start_s, gain=1.0):
    i0 = int(start_s * SR)
    end = min(len(buf), i0 + len(x))
    if end > i0:
        buf[i0:end] += x[: end - i0] * gain


def glide_curve(notes, n, porta=0.09):
    """Step-target pitch curve smoothed one-pole (the duduk portamento)."""
    f_target = np.zeros(n)
    edge = 0.0
    for m, d in notes:
        a, b = int(edge * SR), min(n, int((edge + d) * SR))
        f_target[a:b] = midi_to_hz(m)
        edge += d
    i_end = min(n - 1, int(edge * SR))
    f_target[i_end:] = f_target[i_end - 1]
    alpha = 1.0 - np.exp(-1.0 / (porta * SR))
    return signal.lfilter([alpha], [1.0, -(1.0 - alpha)],
                          f_target, zi=[f_target[0] * (1 - alpha)])[0]


mix_L = np.zeros(N)
mix_R = np.zeros(N)
N_LAYERS = 0


def commit(layer_L, layer_R, weight, env=None):
    global mix_L, mix_R, N_LAYERS
    N_LAYERS += 1
    pk = max(np.max(np.abs(layer_L)), np.max(np.abs(layer_R))) + 1e-12
    L = layer_L / pk * weight
    R = layer_R / pk * weight
    if env is not None:
        L *= env
        R *= env
    mix_L += L
    mix_R += R


IR_L = make_reverb_ir(1.8, 0.9, 7)
IR_R = make_reverb_ir(1.8, 0.9, 11)

# Rubato: correlated rushing/dragging applied to every vocal onset.
WANDER = slow_noise(0.15, -0.025, 0.025)


def when(b, beat=0.0):
    """Vocal onset: grid time + performance wander."""
    tt = bar_t(b, beat)
    return max(0.0, tt + WANDER[min(N - 1, int(tt * SR))])


# --------------------------------------------------------------- material
# One harmony for the whole song (the Gurney songbook voicings).

CHORDS = {"D": [38, 50, 57, 62, 66],
          "Eb": [39, 51, 58, 63, 67],
          "Cm": [36, 48, 55, 60, 63],
          "Gm": [43, 50, 58, 62, 67]}
ROOT = {"D": 38, "Eb": 39, "Cm": 36, "Gm": 31}

CELL = ["D", "Eb", "Gm", "D"]                          # one hook cell
V8 = ["D", "Cm", "D", "Gm", "Eb", "Eb", "Cm", "D"]     # one verse pass
PRE8 = ["Gm", "Eb", "Cm", "Eb"] * 2
CHORD_MAP = (CELL + V8 * 2 + PRE8 + CELL * 4 + V8 * 2 + PRE8 + CELL * 4
             + ["Cm", "Eb"] * 10 + CELL * 4 + CELL * 4 + ["D"] * 4)
assert len(CHORD_MAP) == B_END

# THE HOOK — the refrain. Question ends hanging on G over the Gm/Eb turn;
# answer falls F#–Eb–D onto the major tonic. Vowels: "si-ha-ya ... oh".
HOOK_Q = [(57, 1.5, "i"), (58, 1.5, "a"), (57, 1.0, "a"), (55, 3.0, "o")]
HOOK_A = [(54, 1.5, "i"), (51, 1.5, "a"), (50, 4.5, "a")]

# Verse melody: Q and A share one rhythm (2,1,1 / 2,2 / 2,1,1 / 3);
# Q climbs to an unresolved A over Gm, A falls home to D. Pitches only —
# vowel-"lyrics" are per line below (same tune, different words).
VERSE_Q = [(50, 2), (54, 1), (55, 1), (51, 2), (48, 2),
           (50, 2), (54, 1), (55, 1), (57, 3)]
VERSE_A = [(51, 2), (55, 1), (58, 1), (55, 2), (51, 2),
           (51, 2), (50, 1), (48, 1), (50, 3)]
# verse-2 variants (Chani sings these +12): higher questions, same bones
VERSE_Q2 = [(50, 2), (54, 1), (57, 1), (55, 2), (51, 2),
            (50, 2), (54, 1), (55, 1), (58, 3)]
VERSE_A2 = [(51, 2), (55, 1), (58, 1), (57, 2), (54, 2),
            (51, 2), (50, 1), (51, 1), (50, 3)]

LYR_V1 = ["aeiouaeio", "eaoiaeoua", "oieauoeia", "ueaoiaeoa"]
LYR_V2 = ["ieaouieao", "aoeiuaeoa", "eiouaeioa", "oaeiuoeaa"]

# pre-chorus: 1-bar trade figures + the 4-bar rise (both, then canon)
PC_Q1 = [(55, 1.5, "u"), (57, 1.5, "e"), (58, 1.0, "i")]      # Paul, over Gm
PC_A1 = [(70, 1.5, "u"), (67, 1.5, "e"), (63, 1.0, "a")]      # Chani, falling
PC_Q2 = [(51, 1.5, "u"), (55, 1.5, "e"), (60, 1.0, "i")]      # Paul, over Cm
RISE = [(55, 4, "a"), (58, 4, "o"), (60, 4, "e"), (63, 3, "i")]
PICKUP = [(69, 0.7, "i")]                                     # her lead-in

# THEME_A — the album's main theme; bridge question + chorus-4 answer.
THEME_A = [(62, 2), (66, 1), (63, 1), (62, 2), (60, 2), (62, 3),
           (63, 1), (66, 2), (69, 2), (67, 2), (66, 1), (63, 1),
           (62, 4), (60, 2), (63, 2), (62, 4)]
FRAG = [(62, 2), (66, 1), (63, 1), (62, 2), (60, 3)]          # unresolved
HUM_FRAG = [(50, 2, "u"), (54, 1, "u"), (51, 1, "u"),
            (50, 2, "u"), (48, 2, "u")]

NEY_ANS = [(81, 1.0), (79, 0.75), (78, 1.0), (75, 2.0)]       # descant answer
NEY_ECHO = [(74, 0.9), (75, 0.7), (74, 1.8)]                  # her tail, echoed


def up12(notes):
    return [(m + 12,) + tuple(rest) for m, *rest in notes]


def with_lyr(notes, lyr):
    return [(m, d, v) for (m, d), v in zip(notes, lyr)]


b2s = lambda nb: nb * BEAT

# ------------------------------------------------------- THE SINGING VOICE
# The album's new instrument: the chant's glottal source made melodic and
# sung through time-interpolated vowel formants (the litany table).

VOWELS = {"i": (270, 2300), "e": (530, 1840), "a": (730, 1090),
          "o": (570, 840), "u": (300, 870)}
SING_CACHE = {}


def sing_phrase(notes, female=False, hum=False):
    """notes: list of (midi, dur_beats, vowel). Returns mono, peak 1."""
    key = (tuple(notes), female, hum)
    if key in SING_CACHE:
        return SING_CACHE[key]
    seq = [(m, b2s(d), ("u" if hum else v)) for m, d, v in notes]
    sung = sum(d for _, d, _ in seq)
    n = int((sung + 0.9) * SR)
    tt = np.arange(n) / SR

    # pitch: portamento + vibrato blooming over the first 0.8 s
    f_curve = glide_curve([(m, d) for m, d, _ in seq], n, porta=0.07)
    vr, va = (5.8, 0.0035) if female else (5.0, 0.005)
    vib = 1.0 + va * np.sin(2 * np.pi * vr * tt) * np.clip(tt / 0.8, 0, 1)
    phase = 2 * np.pi * np.cumsum(f_curve * vib) / SR

    # glottal source: softer spectrum for her, no guttural pulse for either
    p = 1.2 if female else 0.8
    src = np.zeros(n)
    for k in range(1, 15):
        src += np.sin(k * phase) / k ** p

    # per-note windows (90 ms crossfades) grouped by vowel
    scale = 1.18 if female else 1.0
    xf = int(0.09 * SR)
    edges = np.cumsum([0.0] + [d for _, d, _ in seq])
    win = {}
    for i, (_, _, v) in enumerate(seq):
        s, e = int(edges[i] * SR), int(edges[i + 1] * SR)
        w = np.zeros(n)
        w[s:e] = 1.0
        if i > 0:
            w[s:s + xf] = np.linspace(0, 1, xf)
        if i < len(seq) - 1:
            w[e - xf:e] = np.linspace(1, 0, xf)
        else:
            w[e:] = 1.0                      # last vowel owns the release
        win[v] = win.get(v, 0.0) + w

    out = np.zeros(n)
    for v, w in win.items():
        f1, f2 = VOWELS[v]
        b1, a1 = signal.iirpeak(f1 * scale, Q=8.0, fs=SR)
        b2_, a2 = signal.iirpeak(f2 * scale, Q=8.0, fs=SR)
        y = signal.lfilter(b1, a1, src) + 0.7 * signal.lfilter(b2_, a2, src)
        y /= np.sqrt(np.mean(y ** 2)) + 1e-12   # equal loudness per vowel
        out += y * w
    # chest/body: keeps the fundamental under the formant resonances
    sos_body = signal.butter(2, 750 * scale, "low", fs=SR, output="sos")
    body = signal.sosfilt(sos_body, src)
    out += (1.3 if hum else 0.8) * body / (np.sqrt(np.mean(body ** 2)) + 1e-12)

    env = np.minimum(np.clip(tt / 0.10, 0, 1),
                     np.clip((sung + 0.15 - tt) / 0.35, 0, 1))
    env = np.clip(env, 0, 1) ** 1.2
    out *= env

    if not hum:
        # breath: her air, and a soft 'h' onset through the first vowel
        nz = rng.standard_normal(n)
        sos_br = signal.butter(2, [2000, 5000], "bandpass", fs=SR, output="sos")
        out += (0.10 if female else 0.03) * signal.sosfilt(sos_br, nz) * env
        f1, f2 = VOWELS[seq[0][2]]
        b1, a1 = signal.iirpeak(f1 * scale, Q=8.0, fs=SR)
        h = signal.lfilter(b1, a1, nz) * np.exp(-tt * 25.0)
        out += 0.5 * h / (np.max(np.abs(h)) + 1e-12)
    lp = 1400 if hum else (4800 if female else 3400)
    sos_lp = signal.butter(2, lp, "low", fs=SR, output="sos")
    out = signal.sosfilt(sos_lp, out)
    out /= np.max(np.abs(out)) + 1e-12
    SING_CACHE[key] = out
    return out


HOOK_COUNT = 0

# ---------------------------------------------------------------- wind & drone
# The album frame. `calm` lifts it in the intro/bridge/outro and ducks it
# (never mutes it) while the song plays.
cp = [(0, 1.0), (bar_t(B_V1), 1.0), (bar_t(B_V1 + 1), 0.35),
      (bar_t(B_BR), 0.35), (bar_t(B_BR + 4), 0.9),
      (bar_t(B_RB), 0.9), (bar_t(B_RB + 4), 0.4),
      (bar_t(B_CH3), 0.35), (bar_t(B_OUT), 0.4),
      (bar_t(B_OUT + 2), 1.0), (DURATION, 1.0)]
calm = np.interp(t, [a for a, _ in cp], [b for _, b in cp])

raw = rng.standard_normal(N)
sos_wh = signal.butter(4, [120, 900], "bandpass", fs=SR, output="sos")
whoosh = signal.sosfilt(sos_wh, raw)
whoosh /= np.max(np.abs(whoosh))
sos_hs = signal.butter(4, [2000, 7000], "bandpass", fs=SR, output="sos")
hiss = signal.sosfilt(sos_hs, raw)
hiss /= np.max(np.abs(hiss))
del raw
gust = slow_noise(0.22) ** 2.2
gust2 = slow_noise(0.07) ** 1.5
wenv = 0.25 + 0.75 * (0.6 * gust + 0.4 * gust2)
pan = slow_noise(0.05, 0.25, 0.75)
w_L = wenv * (whoosh * np.cos(pan * np.pi / 2) +
              0.30 * hiss * gust * np.cos((1 - pan) * np.pi / 2))
w_R = wenv * (whoosh * np.sin(pan * np.pi / 2) +
              0.30 * hiss * gust * np.sin((1 - pan) * np.pi / 2))
del whoosh, hiss, gust, gust2, wenv, pan
commit(w_L, w_R, 0.15, env=calm)
del w_L, w_R
print("wind committed")

f_D1 = midi_to_hz(26)
breath = 0.7 + 0.3 * np.sin(2 * np.pi * 0.012 * t + 1.0)
drone = (np.sin(2 * np.pi * f_D1 * t) +
         0.55 * np.sin(2 * np.pi * f_D1 * 2 * t + 0.4) +
         0.30 * np.sin(2 * np.pi * f_D1 * 3 * t) +
         0.30 * np.sin(2 * np.pi * f_D1 * 3.003 * t))
drone *= breath
commit(drone, drone, 0.09, env=calm)   # set dressing, not a bed
del drone, breath
print("drone committed")

# ---------------------------------------------------------------- baliset
# The layer that never leaves: fingerpicked arpeggios everywhere except
# the choruses, where it strums. Gurney's triple-course Karplus-Strong.

def ks_string(f, dur, damp, taps=3):
    period = max(2, int(SR / f))
    n = int(dur * SR)
    buf = rng.uniform(-1, 1, period)
    buf = np.convolve(buf, np.ones(taps) / taps, mode="same")
    out = np.empty(((n // period) + 2) * period)
    for pp in range(len(out) // period):
        out[pp * period:(pp + 1) * period] = buf
        buf = damp * 0.5 * (buf + np.roll(buf, 1))
    return out[:n]


BAL_CACHE = {}


def baliset_note(m, dur=2.2):
    dur = float(np.clip(dur, 1.2, 8.0))
    key = (m, round(dur * 2) / 2)
    if key in BAL_CACHE:
        return BAL_CACHE[key]
    dur = key[1]
    f = midi_to_hz(m)
    n = int(dur * SR)
    out = np.zeros(n)
    for det, g in zip((0.9975, 1.0, 1.0035), (0.55, 1.0, 0.7)):
        out += g * ks_string(f * det, dur, 0.9955)
    sos = signal.butter(2, [90, 5200], "bandpass", fs=SR, output="sos")
    out = signal.sosfilt(sos, out)
    out *= np.clip((dur - np.arange(n) / SR) / 0.08, 0, 1)
    out /= np.max(np.abs(out)) + 1e-12
    BAL_CACHE[key] = out
    return out


bal_L = np.zeros(N)
bal_R = np.zeros(N)


def pluck(m, t0, gain, dur=2.2):
    note = baliset_note(m, dur)
    p = -0.2 + 0.4 * np.clip((m - 38) / 30.0, 0, 1)
    th = (0.5 + p * 0.5) * np.pi / 2
    add_at(bal_L, note, t0, gain * np.cos(th))
    add_at(bal_R, note, t0, gain * np.sin(th))


def strum(chord, t0, gain, up=False, dur=2.8):
    order = list(reversed(chord[-3:])) if up else chord
    stag = rng.uniform(0.012, 0.025)
    for i, m in enumerate(order):
        pluck(m, t0 + i * stag, gain * rng.uniform(0.85, 1.15), dur)


ARP = [0, 2, 3, 4, 2, 3, 1, 4]          # eighth-note fingerpicking pattern
CHORUS_BARS = (set(range(B_CH1, B_V2)) | set(range(B_CH2, B_BR)) |
               set(range(B_CH3, B_OUT)))
for bb in range(B_END):
    ch = CHORDS[CHORD_MAP[bb]]
    if bb in CHORUS_BARS:                                    # strummed
        strum(ch, bar_t(bb, 0.0), 0.90)
        strum(ch, bar_t(bb, 1.5), 0.40, up=True, dur=1.8)
        strum(ch, bar_t(bb, 2.0), 0.60, dur=2.2)
        strum(ch, bar_t(bb, 3.5), 0.38, up=True, dur=1.8)
        continue
    g = 0.65
    if B_BR <= bb < B_RB:                                    # bridge trough
        g = 0.65 - 0.04 * (bb - B_BR)
    if bb >= B_OUT:
        g = 0.5 - 0.08 * (bb - B_OUT)
    steps = ARP if bb != B_RB + 11 else ARP[:5]              # bar 103: cut
    for i, idx in enumerate(steps):
        gg = g * (0.85 if i % 2 == 0 else 0.55) * rng.uniform(0.9, 1.1)
        pluck(ch[idx], bar_t(bb, i * 0.5) + rng.uniform(-0.008, 0.008),
              gg, dur=1.6)
# the outro's final strum, ringing ~6 s into the wind
strum(CHORDS["D"], bar_t(B_OUT + 3, 0.0), 0.75, dur=6.0)
bal_L = reverb(bal_L, IR_L, wet=0.15)
bal_R = reverb(bal_R, IR_R, wet=0.15)
commit(bal_L, bal_R, 0.26)
del bal_L, bal_R
print("baliset committed")

# ---------------------------------------------------------------- gated bass

BASS_CACHE = {}


def bass_note(m, dur):
    key = (m, round(dur, 2))
    if key in BASS_CACHE:
        return BASS_CACHE[key]
    n = int(dur * SR)
    td = np.arange(n) / SR
    f = midi_to_hz(m)
    x = np.sin(2 * np.pi * f * td) + 0.35 * np.sin(4 * np.pi * f * td)
    x = np.tanh(1.6 * x)
    x *= np.clip(td / 0.005, 0, 1) * np.clip((dur - td) / 0.05, 0, 1)
    BASS_CACHE[key] = x
    return x


lay_L = np.zeros(N)
lay_R = np.zeros(N)
VERSE_HITS = [(0.0, 1.4, 1.0), (2.5, 0.45, 0.55), (3.0, 0.9, 0.8)]
CHOR_HITS = [(0.0, 1.0, 1.0), (1.5, 0.45, 0.6), (2.0, 0.8, 0.85),
             (3.0, 0.45, 0.6), (3.5, 0.45, 0.7)]
BASS_OFF = set(range(B_BR + 3, B_RB)) | set(range(B_OUT + 1, B_END))
for bb in range(B_V1, B_END):
    if bb in BASS_OFF:
        continue
    r = ROOT[CHORD_MAP[bb]]
    hits = CHOR_HITS if bb in CHORUS_BARS else VERSE_HITS
    if bb == B_RB + 11:                       # bar 103: stop before the cut
        hits = [(0.0, 1.4, 1.0), (2.5, 0.45, 0.55)]
    if bb == B_OUT:
        hits = [(0.0, 2.5, 0.9)]
    for beat, dur, g in hits:
        x = bass_note(r, dur)
        add_at(lay_L, x, bar_t(bb, beat), g)
        add_at(lay_R, x, bar_t(bb, beat), g)
    if bb in (B_CH1 - 1, B_CH2 - 1):          # cadence walk C–Eb into D
        for beat, m in [(2.0, 36), (3.0, 39), (3.5, 38)]:
            x = bass_note(m, 0.45)
            add_at(lay_L, x, bar_t(bb, beat), 0.7)
            add_at(lay_R, x, bar_t(bb, beat), 0.7)
commit(lay_L, lay_R, 0.30)
print("bass committed")

# ------------------------------------------------- frame drum + darbuka + war

def make_frame_hit():
    n = int(0.12 * SR)
    td = np.arange(n) / SR
    sos_f = signal.butter(2, [180, 1400], "bandpass", fs=SR, output="sos")
    nz = signal.sosfilt(sos_f, rng.standard_normal(n)) * np.exp(-td * 40)
    nz /= np.max(np.abs(nz)) + 1e-12
    tone = 0.5 * np.sin(2 * np.pi * 95.0 * td) * np.exp(-td * 30)
    x = nz + tone
    return x / (np.max(np.abs(x)) + 1e-12)


FRAME = make_frame_hit()


def frame_roll(dur=2.0):
    out = np.zeros(int((dur + 0.3) * SR))
    tcur = 0.0
    while tcur < dur:
        frac = tcur / dur
        rate = 9.0 + 11.0 * frac
        g = (0.30 + 0.70 * frac) * rng.uniform(0.85, 1.0)
        add_at(out, FRAME, tcur, g)
        tcur += 1.0 / rate
    return out


lay_L[:] = 0.0
lay_R[:] = 0.0
FRAME_BARS = (set(range(B_V1, B_CH1)) | set(range(B_V2, B_CH2)) |
              set(range(B_RB + 4, B_RB + 10)))
for bb in sorted(FRAME_BARS):
    pre = B_PC1 <= bb < B_CH1 or B_PC2 <= bb < B_CH2
    beats = (0.0, 1.0, 2.0, 3.0) if pre else (0.0, 2.0)
    for i, beat in enumerate(beats):
        g = (0.55 if i % 2 == 0 else 0.35) if pre else \
            (0.7 if i % 2 == 0 else 0.45)
        add_at(lay_L, FRAME, bar_t(bb, beat), g)
        add_at(lay_R, FRAME, bar_t(bb, beat), g * 0.85)
# rolls: the launch gesture into each chorus, and the bridge crescendo
for t0, dur in [(bar_t(B_CH1 - 1, 2.0), 2 * BEAT),
                (bar_t(B_CH2 - 1, 2.0), 2 * BEAT),
                (bar_t(B_RB + 10, 0.0), BAR + 3 * BEAT)]:   # ends at 103 b4
    fr = frame_roll(dur)
    add_at(lay_L, fr, t0, 0.85)
    add_at(lay_R, fr, t0, 0.95)
commit(lay_L, lay_R, 0.10)
print("frame drum committed")


def make_doum():
    n = int(0.30 * SR)
    td = np.arange(n) / SR
    f_curve = 55.0 + 35.0 * np.exp(-td * 28.0)
    body = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    ring = 0.25 * np.sin(2 * np.pi * 190.0 * td) * np.exp(-td * 35)
    env = np.exp(-td * 14.0) * (1 - np.exp(-td * 600))
    return (body + ring) * env


def make_tek(ghost=False):
    n = int(0.09 * SR)
    td = np.arange(n) / SR
    sos_h = signal.butter(4, [2800, 10000], "bandpass", fs=SR, output="sos")
    slap = signal.sosfilt(sos_h, rng.standard_normal(n))
    ping = 0.4 * np.sin(2 * np.pi * 640.0 * td)
    env = np.exp(-td * (90.0 if ghost else 55.0))
    x = (slap / (np.max(np.abs(slap)) + 1e-12) + ping) * env
    return x * (0.35 if ghost else 1.0)


DOUM, TEK, KA = make_doum(), make_tek(), make_tek(ghost=True)
MAQSUM = {0: "D", 2: "T", 6: "T", 8: "D", 12: "T"}
HALF_BARS = set(range(B_V2, B_BR - 15)) | set(range(B_RB + 6, B_RB + 10))
DARB_BARS = CHORUS_BARS | HALF_BARS
lay_L[:] = 0.0
lay_R[:] = 0.0
for bb in sorted(DARB_BARS):
    half = bb in HALF_BARS and bb not in CHORUS_BARS
    level = 0.35 if half else 0.6
    fill = (not half) and bb % 4 == 3 and bb + 1 in DARB_BARS
    for s in range(16):
        st = bar_t(bb, s * 0.25)
        stroke = MAQSUM.get(s)
        if half and s not in (0, 8):
            stroke = None
        if fill and s >= 12:
            g = (0.45 + 0.55 * (s - 12) / 3.0) * level
            add_at(lay_L, TEK, st, g * 0.9)
            add_at(lay_R, TEK, st, g * 0.7)
            continue
        if stroke == "D":
            add_at(lay_L, DOUM, st, level)
            add_at(lay_R, DOUM, st, level)
        elif stroke == "T":
            p = 0.35 if s in (2, 12) else 0.65
            add_at(lay_L, TEK, st, level * np.cos(p * np.pi / 2))
            add_at(lay_R, TEK, st, level * np.sin(p * np.pi / 2))
        elif not half and s % 2 == 1 and rng.random() < 0.25:
            add_at(lay_L, KA, st, 0.6 * level)
            add_at(lay_R, KA, st, 0.5 * level)
commit(lay_L, lay_R, 0.13)
print("darbuka committed")


def make_war_drum():
    n = int(0.9 * SR)
    td = np.arange(n) / SR
    f_curve = 42.0 + 48.0 * np.exp(-td * 9.0)
    body = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    sos_sk = signal.butter(2, [100, 420], "bandpass", fs=SR, output="sos")
    skin = signal.sosfilt(sos_sk, rng.standard_normal(n)) * np.exp(-td * 22)
    skin /= np.max(np.abs(skin)) + 1e-12
    env = np.exp(-td * 5.5) * (1 - np.exp(-td / 0.006))
    x = body * env + 0.5 * skin * env
    return x / (np.max(np.abs(x)) + 1e-12)


WAR = make_war_drum()
lay_L[:] = 0.0
lay_R[:] = 0.0
for bb in range(B_CH2, B_END):
    if bb not in CHORUS_BARS or bb % 4 != 0:
        continue
    g = 1.0 + 0.2 * (bb >= B_CH4)
    add_at(lay_L, WAR, bar_t(bb, 0.0), g)
    add_at(lay_R, WAR, bar_t(bb, 0.0), g)
    if bb >= B_CH4:                          # doubled = heavier
        add_at(lay_L, WAR, bar_t(bb, 1.5), g * 0.5)
        add_at(lay_R, WAR, bar_t(bb, 1.5), g * 0.5)
add_at(lay_L, WAR, bar_t(B_OUT, 0.0), 0.9)   # the outro's last hit
add_at(lay_R, WAR, bar_t(B_OUT, 0.0), 0.9)
commit(lay_L, lay_R, 0.16)
print("war drums committed")

# ---------------------------------------------------------------- oud

def oud_note(m, dur=0.55):
    n = int(dur * SR)
    out = np.zeros(n)
    for det in (1.0, 1.004):
        period = max(2, int(SR / (midi_to_hz(m) * det)))
        buf = rng.uniform(-1, 1, period)
        idx = 0
        for i in range(n):
            out[i] += buf[idx]
            nxt = (idx + 1) % period
            buf[idx] = 0.4985 * (buf[idx] + buf[nxt])
            idx = nxt
    sos_o = signal.butter(2, [200, 4200], "bandpass", fs=SR, output="sos")
    out = signal.sosfilt(sos_o, out)
    out *= np.clip((dur - np.arange(n) / SR) / 0.04, 0, 1)
    return out / (np.max(np.abs(out)) + 1e-12)


OUD_CACHE = {}


def place_oud(notes, t0, gain, pan_pos=0.62):
    cur = t0
    for m, d in notes:
        dur = min(0.9, b2s(d) * 0.92)
        key = (m, round(dur, 2))
        if key not in OUD_CACHE:
            OUD_CACHE[key] = oud_note(m, dur)
        x = OUD_CACHE[key]
        add_at(lay_L, x, cur, gain * np.cos(pan_pos * np.pi / 2))
        add_at(lay_R, x, cur, gain * np.sin(pan_pos * np.pi / 2))
        cur += b2s(d)


lay_L[:] = 0.0
lay_R[:] = 0.0
# verse-1 echoes: the tail of each sung line, one octave up, entering on
# the singer's held final note (the composed echo that stitches phrases)
V_TAIL_Q = [(66, 0.75), (67, 0.75), (69, 1.5)]
V_TAIL_A = [(62, 0.75), (60, 0.75), (62, 1.5)]
for cell, tail in [(B_V1, V_TAIL_Q), (B_V1 + 4, V_TAIL_A),
                   (B_V1 + 8, V_TAIL_Q), (B_V1 + 12, V_TAIL_A)]:
    place_oud(tail, bar_t(cell + 3, 1.0), 0.55)
# chorus riff doubling (ch2 on): the hook in unison with the singers
HOOK_OUD_Q = [(69, 1.5), (70, 1.5), (69, 1.0), (67, 3.0)]
HOOK_OUD_A = [(66, 1.5), (63, 1.5), (62, 3.0)]
for b0 in list(range(B_CH2, B_BR, 4)) + list(range(B_CH3, B_OUT, 4)):
    place_oud(HOOK_OUD_Q, bar_t(b0), 0.42)
    place_oud(HOOK_OUD_A, bar_t(b0 + 2), 0.42)
lay_L = reverb(lay_L, IR_L, wet=0.25)
lay_R = reverb(lay_R, IR_R, wet=0.25)
commit(lay_L, lay_R, 0.12)
print("oud committed")

# ---------------------------------------------------------------- choir

def chant_note(midi, dur, scatter=1.0):
    n = int(dur * SR)
    td = np.arange(n) / SR
    f0 = midi_to_hz(midi) * scatter
    phase = 2 * np.pi * np.cumsum(np.full(n, f0)) / SR
    src = np.zeros(n)
    for k in range(1, 15):
        src += np.sin(k * phase) / k ** 0.8
    env = np.minimum(np.clip(td / 0.06, 0, 1), np.clip((dur - td) / 0.30, 0, 1))
    src *= env
    out = np.zeros(n)
    for lo, hi, g in [(380, 560, 1.0), (750, 1000, 0.6), (2200, 2700, 0.15)]:
        sos = signal.butter(2, [lo, hi], "bandpass", fs=SR, output="sos")
        out += g * signal.sosfilt(sos, src)
    out += 0.40 * np.sin(phase * 0.5) * env
    return out / (np.max(np.abs(out)) + 1e-12)


CHOIR_CACHE = {}


def mass_chant(midi, dur, voices=12):
    key = (midi, round(dur, 2))
    if key in CHOIR_CACHE:
        return CHOIR_CACHE[key]
    n = int((dur + 0.16) * SR)
    L = np.zeros(n)
    R = np.zeros(n)
    for v in range(voices):
        det = 1.0 + rng.uniform(-0.008, 0.008)
        jitter = int(rng.uniform(0.0, 0.12) * SR)
        body = chant_note(midi, dur, scatter=det)
        body *= rng.uniform(0.82, 1.05)
        end = min(n, jitter + len(body))
        p = (v + 0.5) / voices
        L[jitter:end] += body[: end - jitter] * np.cos(p * np.pi / 2)
        R[jitter:end] += body[: end - jitter] * np.sin(p * np.pi / 2)
    pk = max(np.max(np.abs(L)), np.max(np.abs(R))) + 1e-12
    CHOIR_CACHE[key] = (L / pk, R / pk)
    return CHOIR_CACHE[key]


lay_L[:] = 0.0
lay_R[:] = 0.0
# ch1: a distant pad (root, one note per cell); ch2/ch3: per 2 bars;
# ch4: the choir DOUBLES the hook, one octave below Paul.
for b0 in range(B_CH1, B_V2, 4):
    L, R = mass_chant(ROOT[CHORD_MAP[b0]] + 12, 2 * BAR)
    add_at(lay_L, L, bar_t(b0), 0.45)
    add_at(lay_R, R, bar_t(b0), 0.45)
for b0 in list(range(B_CH2, B_BR, 2)) + list(range(B_CH3, B_CH4, 2)):
    L, R = mass_chant(ROOT[CHORD_MAP[b0]] + 12, 1.6 * BAR)
    add_at(lay_L, L, bar_t(b0), 0.7)
    add_at(lay_R, R, bar_t(b0), 0.7)
for b0 in range(B_CH4, B_OUT, 4):
    cur = bar_t(b0)
    for m, d, _ in HOOK_Q + HOOK_A:
        L, R = mass_chant(m - 12, b2s(d) * 0.98)
        add_at(lay_L, L, cur, 1.0)
        add_at(lay_R, R, cur, 1.0)
        cur += b2s(d)
lay_L = reverb(lay_L, IR_L, wet=0.55)
lay_R = reverb(lay_R, IR_R, wet=0.55)
commit(lay_L, lay_R, 0.12)
print("choir committed")

# ---------------------------------------------------------------- strings

def tremolo_strings(chord, dur, trem_hz=10.5):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    out = np.zeros(n)
    for m in chord:
        f = midi_to_hz(m)
        for det, g in [(0.996, 0.6), (1.0, 1.0), (1.005, 0.6)]:
            for k in range(1, 9):
                out += (g / k) * np.sin(2 * np.pi * f * det * k * tt +
                                        rng.uniform(0, 2 * np.pi))
    sos_s = signal.butter(2, [180, 2600], "bandpass", fs=SR, output="sos")
    out = signal.sosfilt(sos_s, out)
    trem = (0.5 + 0.5 * np.sin(2 * np.pi * trem_hz * tt)) ** 1.2
    env = np.minimum(np.clip(tt / 1.5, 0, 1), np.clip((dur - tt) / 2.0, 0, 1))
    out *= trem * env
    return out / (np.max(np.abs(out)) + 1e-12)


lay_L[:] = 0.0
lay_R[:] = 0.0
for chord, b0, b1, gL, gR in [
        ([62, 63], B_PC1 + 4, B_CH1, 0.50, 0.44),       # the rise, pc1
        ([62, 63], B_PC2 + 4, B_CH2, 0.50, 0.58),       # the rise, pc2
        ([60, 63, 67], B_RB + 4, B_RB + 12, 0.9, 0.85)]:  # bridge rebuild
    sw = tremolo_strings(chord, (b1 - b0) * BAR)
    add_at(lay_L, sw, bar_t(b0), gL)
    add_at(lay_R, sw, bar_t(b0), gR)
lay_L = reverb(lay_L, IR_L, wet=0.45)
lay_R = reverb(lay_R, IR_R, wet=0.45)
commit(lay_L, lay_R, 0.09)
print("strings committed")

# ---------------------------------------------------------------- riser

def riser(dur=4.0):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    nz = rng.standard_normal(n)
    out = np.zeros(n)
    K = 10
    for k in range(K):
        c = 300.0 * (5500.0 / 300.0) ** (k / (K - 1))
        sos_r = signal.butter(2, [c * 0.7, c * 1.4], "bandpass",
                              fs=SR, output="sos")
        band = signal.sosfilt(sos_r, nz)
        center = (k + 0.5) / K * dur
        w = np.clip(1 - np.abs(tt - center) / (dur / K * 1.6), 0, 1)
        out += band * w
    out /= np.max(np.abs(out)) + 1e-12
    f_curve = 70.0 * 2.0 ** (2.0 * tt / dur)
    tone = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    x = (out + 0.45 * tone) * (tt / dur) ** 2
    return x / (np.max(np.abs(x)) + 1e-12)


lay_L[:] = 0.0
lay_R[:] = 0.0
rz_dur = 2 * BAR + 3 * BEAT                    # ends exactly at bar 103 beat 4
rz = riser(rz_dur)
add_at(lay_L, rz, bar_t(B_RB + 9, 1.0), 0.85)
add_at(lay_R, rz, bar_t(B_RB + 9, 1.0), 1.0)
commit(lay_L, lay_R, 0.09)
print("riser committed")

# ---------------------------------------------------------------- duduk + ney

def voice_phrase(notes, lp=2200):
    total = sum(d for _, d in notes) + 2.0
    n = int(total * SR)
    tt = np.arange(n) / SR
    f_curve = glide_curve(notes, n)
    vib = 1.0 + 0.006 * np.sin(2 * np.pi * 5.2 * tt) * np.clip(tt / 1.2, 0, 1)
    phase = 2 * np.pi * np.cumsum(f_curve * vib) / SR
    env = np.minimum(np.clip(tt / 1.0, 0, 1),
                     np.clip((total - tt) / 2.0, 0, 1)) ** 1.5
    v = env * (np.sin(phase) + 0.40 * np.sin(2 * phase) +
               0.18 * np.sin(3 * phase) + 0.07 * np.sin(4 * phase))
    sos = signal.butter(2, lp, "low", fs=SR, output="sos")
    return signal.sosfilt(sos, v)


def ney_phrase(notes):
    total = sum(d for _, d in notes) + 1.5
    n = int(total * SR)
    tt = np.arange(n) / SR
    f_curve = glide_curve(notes, n)
    vib = 1.0 + 0.004 * np.sin(2 * np.pi * 6.0 * tt) * np.clip(tt / 0.8, 0, 1)
    phase = 2 * np.pi * np.cumsum(f_curve * vib) / SR
    env = np.minimum(np.clip(tt / 0.6, 0, 1),
                     np.clip((total - tt) / 1.5, 0, 1)) ** 1.3
    tone = np.sin(phase) + 0.25 * np.sin(2 * phase) + 0.08 * np.sin(3 * phase)
    sos_b = signal.butter(2, [1200, 4000], "bandpass", fs=SR, output="sos")
    br = signal.sosfilt(sos_b, rng.standard_normal(n))
    br /= np.max(np.abs(br)) + 1e-12
    v = env * (tone + 0.13 * br)
    sos = signal.butter(2, 3200, "low", fs=SR, output="sos")
    return signal.sosfilt(sos, v)


sec = lambda notes: [(m, b2s(d)) for m, d in notes]
lay_L[:] = 0.0
lay_R[:] = 0.0
# bridge: Theme A fragments, far away, never resolving — the question
v = voice_phrase(sec(FRAG), lp=1800)
add_at(lay_L, v, when(B_BR + 1), 0.6 * np.cos(0.62 * np.pi / 2))
add_at(lay_R, v, when(B_BR + 1), 0.6 * np.sin(0.62 * np.pi / 2))
v = voice_phrase(sec(FRAG), lp=1800)
add_at(lay_L, v, when(B_BR + 5), 0.55 * np.cos(0.40 * np.pi / 2))
add_at(lay_R, v, when(B_BR + 5), 0.55 * np.sin(0.40 * np.pi / 2))
# chorus 4: THEME A entire, the counter-line under the refrain — the answer
for b0 in (B_CH4, B_CH4 + 8):
    v = voice_phrase(sec(THEME_A))
    add_at(lay_L, v, bar_t(b0), 0.8 * np.cos(0.55 * np.pi / 2))
    add_at(lay_R, v, bar_t(b0), 0.8 * np.sin(0.55 * np.pi / 2))
lay_L = reverb(lay_L, IR_L, wet=0.6)
lay_R = reverb(lay_R, IR_R, wet=0.6)
commit(lay_L, lay_R, 0.15)
print("duduk committed (bridge question, chorus-4 Theme A)")

lay_L[:] = 0.0
lay_R[:] = 0.0
# ch1: the ney echoes Chani's tails (statements 2 and 4)
for b0 in (B_CH1 + 4, B_CH1 + 12):
    v = ney_phrase(sec(NEY_ECHO))
    add_at(lay_L, v, when(b0 + 3, 1.0), 0.7 * np.cos(0.60 * np.pi / 2))
    add_at(lay_R, v, when(b0 + 3, 1.0), 0.7 * np.sin(0.60 * np.pi / 2))
# ch3 + ch4: a descant answer after every cell
for b0 in list(range(B_CH3, B_OUT, 4)):
    v = ney_phrase(sec(NEY_ANS))
    add_at(lay_L, v, when(b0 + 3, 0.0), 0.65 * np.cos(0.60 * np.pi / 2))
    add_at(lay_R, v, when(b0 + 3, 0.0), 0.65 * np.sin(0.60 * np.pi / 2))
lay_L = reverb(lay_L, IR_L, wet=0.5)
lay_R = reverb(lay_R, IR_R, wet=0.5)
commit(lay_L, lay_R, 0.09)
print("ney committed")

# ---------------------------------------------------------------- THE VOICES
paul_L = np.zeros(N)
paul_R = np.zeros(N)
chani_L = np.zeros(N)
chani_R = np.zeros(N)


def sing(notes, t0, female=False, gain=1.0, hum=False, stretch=1.0):
    nb = [(m, d * stretch, v) for m, d, v in notes]
    x = sing_phrase(nb, female=female, hum=hum)
    p = 0.56 if female else 0.44
    L, R = (chani_L, chani_R) if female else (paul_L, paul_R)
    add_at(L, x, t0, gain * np.cos(p * np.pi / 2))
    add_at(R, x, t0, gain * np.sin(p * np.pi / 2))


def sing_hook(b0, who, gain=1.0, stretch=1.0):
    """One full hook statement (Q at cell, A at cell+2). who: 'P','C','B'."""
    global HOOK_COUNT
    if who in ("P", "B"):
        sing(HOOK_Q, when(b0), gain=gain, stretch=stretch)
        sing(HOOK_A, when(b0 + 2), gain=gain, stretch=stretch)
    if who in ("C", "B"):
        sing(up12(HOOK_Q), when(b0), female=True, gain=gain, stretch=stretch)
        sing(up12(HOOK_A), when(b0 + 2), female=True, gain=gain,
             stretch=stretch)
    HOOK_COUNT += 1


# intro: Chani hums the answer — the thesis; last note rings across bar 4
sing([(66, 1.5, "i"), (63, 1.5, "a"), (62, 5.0, "a")], when(2),
     female=True, gain=0.5, hum=True)
HOOK_COUNT += 1

# verse 1 — Paul, two Q/A pairs (same tune, different vowel-words)
for i, (cell, mel) in enumerate([(B_V1, VERSE_Q), (B_V1 + 4, VERSE_A),
                                 (B_V1 + 8, VERSE_Q), (B_V1 + 12, VERSE_A)]):
    sing(with_lyr(mel, LYR_V1[i]), when(cell), gain=1.0)

# pre-chorus 1 — trades, then the rise together; her pickup into the chorus
sing(PC_Q1, when(B_PC1), gain=0.95)
sing(PC_A1, when(B_PC1 + 1), female=True, gain=0.95)
sing(PC_Q2, when(B_PC1 + 2), gain=0.95)
sing(PC_A1, when(B_PC1 + 3), female=True, gain=0.95)   # same answer: a motto
sing(RISE, when(B_PC1 + 4), gain=0.68)
sing(up12(RISE), when(B_PC1 + 4), female=True, gain=0.62)
sing(PICKUP, when(B_CH1 - 1, 3.3), female=True, gain=0.8)

# CHORUS 1 — alternating statements: him, her, him, her
sing_hook(B_CH1, "P")
sing_hook(B_CH1 + 4, "C")
sing_hook(B_CH1 + 8, "P")
sing_hook(B_CH1 + 12, "C")

# verse 2 — Chani leads (varied tune, new words), PAUL echoes her tails
for i, (cell, mel) in enumerate([(B_V2, VERSE_Q2), (B_V2 + 4, VERSE_A2),
                                 (B_V2 + 8, VERSE_Q2), (B_V2 + 12, VERSE_A2)]):
    sing(up12(with_lyr(mel, LYR_V2[i])), when(cell), female=True, gain=1.0)
ECHO_Q = [(54, 0.75, "o"), (55, 0.75, "a"), (58, 2.0, "a")]
ECHO_A = [(51, 0.75, "o"), (48, 0.75, "a"), (50, 2.0, "a")]
for cell, echo in [(B_V2, ECHO_Q), (B_V2 + 4, ECHO_A),
                   (B_V2 + 8, ECHO_Q), (B_V2 + 12, ECHO_A)]:
    sing(echo, when(cell + 3, 1.0), gain=0.6)

# pre-chorus 2 — development: overlapping trades, the rise in canon
sing(PC_Q1, when(B_PC2), gain=0.95)
sing(PC_A1, when(B_PC2, 3.5), female=True, gain=0.95)      # overlaps him
sing(PC_Q2, when(B_PC2 + 2), gain=0.95)
sing(PC_A1, when(B_PC2 + 2, 3.5), female=True, gain=0.95)
sing(RISE, when(B_PC2 + 4), gain=0.78)
sing(up12(RISE[:3] + [(63, 2, "i")]), when(B_PC2 + 5),     # canon, 1 bar late
     female=True, gain=0.78)
sing(PICKUP, when(B_CH2 - 1, 3.3), female=True, gain=0.8)

# CHORUS 2 — both voices in parallel octaves throughout
for b0 in range(B_CH2, B_BR, 4):
    sing_hook(b0, "B")

# bridge rebuild — the voices hum Theme A fragments in alternation
sing(HUM_FRAG, when(B_RB), gain=0.7, hum=True)
sing(up12(HUM_FRAG), when(B_RB + 2), female=True, gain=0.7, hum=True)
sing(HUM_FRAG, when(B_RB + 4), gain=0.75, hum=True)
sing(up12(HUM_FRAG), when(B_RB + 6), female=True, gain=0.75, hum=True)
# her lone pickup, hanging in the one beat of silence
sing(PICKUP, when(B_CH3 - 1, 3.2), female=True, gain=0.85)

# CHORUS 3 + 4 — both voices; ch4's last statement stretches ritardando
for b0 in range(B_CH3, B_CH4, 4):
    sing_hook(b0, "B")
for b0 in range(B_CH4, B_OUT - 4, 4):
    sing_hook(b0, "B")
sing(HOOK_Q, when(B_OUT - 4), gain=1.0, stretch=1.15)
sing(up12(HOOK_Q), when(B_OUT - 4), female=True, gain=1.0, stretch=1.15)
sing(HOOK_A, when(B_OUT - 2, 0.5), gain=1.0, stretch=1.5)   # the rit tail,
sing(up12(HOOK_A), when(B_OUT - 2, 0.5), female=True, gain=1.0,
     stretch=1.5)                                           # across the seam
HOOK_COUNT += 1

# outro — she hums the answer once more, unaccompanied: the bookend
sing([(66, 1.5, "i"), (63, 1.5, "a"), (62, 5.0, "a")], when(B_OUT + 1, 2.0),
     female=True, gain=0.5, hum=True, stretch=1.4)
HOOK_COUNT += 1

paul_L = reverb(paul_L, IR_L, wet=0.22)
paul_R = reverb(paul_R, IR_R, wet=0.22)
commit(paul_L, paul_R, 0.30)
del paul_L, paul_R
print("PAUL committed")
chani_L = reverb(chani_L, IR_L, wet=0.22)
chani_R = reverb(chani_R, IR_R, wet=0.22)
commit(chani_L, chani_R, 0.28)
del chani_L, chani_R
print("CHANI committed")

# ---------------------------------------------------------------- master
del lay_L, lay_R
sos_hi = signal.butter(2, 3000, "high", fs=SR, output="sos")
mix_L += 0.15 * signal.sosfilt(sos_hi, mix_L)
mix_R += 0.15 * signal.sosfilt(sos_hi, mix_R)
sos_lo = signal.butter(2, 95, "low", fs=SR, output="sos")
mix_L += 0.20 * signal.sosfilt(sos_lo, mix_L)
mix_R += 0.20 * signal.sosfilt(sos_lo, mix_R)

fade(mix_L, fade_in=0.3, fade_out=9.0)
fade(mix_R, fade_in=0.3, fade_out=9.0)

peak = max(np.max(np.abs(mix_L)), np.max(np.abs(mix_R))) + 1e-12
mix_L = np.tanh(1.25 * mix_L / peak) / np.tanh(1.25) * 0.88
mix_R = np.tanh(1.25 * mix_R / peak) / np.tanh(1.25) * 0.88

stereo = np.empty((N, 2))
stereo[:, 0] = mix_L
stereo[:, 1] = mix_R
pcm = (stereo * 32767.0).astype(np.int16)

OUT_DIR = "/workspace/music"
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, "sihaya.wav")
with wave.open(OUT, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())

print(f"\nCreated: {os.path.abspath(OUT)}")
print(f"Duration: {N / SR:.1f} s  |  {SR} Hz stereo, 16-bit PCM  |  "
      f"{BPM:.0f} BPM  |  {N_LAYERS} committed layers")
print(f"Hook statements (sung): {HOOK_COUNT}  (target >= 12)")

SECTIONS = [("intro", 0.0, bar_t(B_V1)),
            ("verse 1", bar_t(B_V1), bar_t(B_PC1)),
            ("pre-chorus 1", bar_t(B_PC1), bar_t(B_CH1)),
            ("CHORUS 1", bar_t(B_CH1), bar_t(B_V2)),
            ("verse 2", bar_t(B_V2), bar_t(B_PC2)),
            ("pre-chorus 2", bar_t(B_PC2), bar_t(B_CH2)),
            ("CHORUS 2", bar_t(B_CH2), bar_t(B_BR)),
            ("bridge: teardown", bar_t(B_BR), bar_t(B_RB)),
            ("bridge: rebuild", bar_t(B_RB), bar_t(B_CH3)),
            ("CHORUS 3", bar_t(B_CH3), bar_t(B_CH4)),
            ("CHORUS 4", bar_t(B_CH4), bar_t(B_OUT)),
            ("outro", bar_t(B_OUT), DURATION)]
print("Section map + per-section RMS:")
rms = {}
for name, t0, t1 in SECTIONS:
    i0, i1 = int(t0 * SR), min(N, int(t1 * SR))
    rms[name] = np.sqrt(np.mean(mix_L[i0:i1] ** 2 + mix_R[i0:i1] ** 2) / 2)
    print(f"  {t0:6.1f} s  rms {rms[name]:.3f}  {name}")

ok = True
for cond, msg in [
        (rms["CHORUS 1"] > rms["verse 1"], "chorus 1 > verse 1"),
        (rms["CHORUS 1"] > rms["pre-chorus 1"], "chorus 1 > pre-chorus 1"),
        (rms["CHORUS 2"] > rms["CHORUS 1"], "chorus 2 > chorus 1"),
        (rms["CHORUS 4"] == max(rms.values()), "chorus 4 is the loudest"),
        (rms["bridge: teardown"] < min(rms["verse 1"], rms["CHORUS 1"]),
         "bridge trough is quiet"),
        (rms["outro"] < rms["verse 1"], "outro settles")]:
    print(f"  {'PASS' if cond else 'WARN'}: {msg}")
    ok = ok and cond
if not ok:
    print("  -> rebalance section gains before shipping")

print("Seam checklist (what crosses each boundary):")
for line in [
        f"{bar_t(B_V1):6.1f} s  intro->v1:    Chani's hum rings across the downbeat",
        f"{bar_t(B_PC1):6.1f} s  v1->pc1:      held D + oud echo overlap; bass unbroken",
        f"{bar_t(B_CH1):6.1f} s  pc1->ch1:     frame roll + bass walk + her pickup (b27.3)",
        f"{bar_t(B_V2):6.1f} s  ch1->v2:      last strum rings; darbuka drops to half, stays",
        f"{bar_t(B_PC2):6.1f} s  v2->pc2:      Paul's echo overlaps her last line",
        f"{bar_t(B_CH2):6.1f} s  pc2->ch2:     canon lands on roll + walk + pickup",
        f"{bar_t(B_BR):6.1f} s  ch2->bridge:  strip one layer per bar (never all at once)",
        f"{bar_t(B_RB):6.1f} s  teardown->rebuild: Paul's hum starts over the same bed",
        f"{bar_t(B_CH3) - BEAT:6.1f} s  THE SILENT BEAT: only her pickup hangs in it",
        f"{bar_t(B_CH3):6.1f} s  ->ch3:        full band on the downbeat",
        f"{bar_t(B_CH4):6.1f} s  ch3->ch4:     continuous groove + Theme A enters",
        f"{bar_t(B_OUT):6.1f} s  ch4->outro:   rit hook line finishes across the seam"]:
    print("  " + line)
