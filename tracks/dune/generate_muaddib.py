#!/usr/bin/env python3
"""
generate_muaddib.py — "Muad'Dib" (~4:55). The anthem.

Companion song to Sihaya — same songbook (chorus harmony and voice
engines shared deliberately), same song-form doctrine — but the
intimacy inverted and the energy up: 124 BPM on an ayyub-style gallop,
war drums from chorus 1, a soft four-on-the-floor kick in the final
choruses, and the one new instrument: THE CROWD — the sung vowel voice
massed into a 10-singer roster (6 male at pitch, 4 female an octave up,
per-voice detune / formant scatter / onset jitter, wide and wet). The
leader sings; the sietch answers. Call-and-response at every level.

Voice upgrade: 'm' onsets — a note whose vowel is written "mu"/"ma"
starts as the closed hum and opens into the vowel over 80 ms, so the
hook word lands: "Muad'Dib" = m(u)–a–i. Vowel-language otherwise
(names + desert imagery only; see muaddib_notes.md ground rules).

Story: the first worm ride. The thumper knocks, the maker comes, the
young leader mounts — and the watching sietch sings him up.

96 → no: 124 BPM, D Phrygian dominant, seed 12 (twelve voices in the
crowd).

  0:00  The thumper starts knocking; the crowd hums the name far off.
  0:08  VERSE 1: full gallop from the downbeat; the leader sings two
        Q/A pairs, the crowd echoing every tail (oud doubling them).
  0:39  pre-chorus: leader/Chani trades, rise, tom fill, her pickup —
  0:55  CHORUS 1: the crowd sings the hook 4x, the leader answers the
        tails; war drums on the cell downbeats.
  1:26  VERSE 2: Chani leads a varied tune; leader and crowd alternate
        the echoes — the response grows.
  1:57  pre-chorus in canon (her one bar behind).
  2:12  CHORUS 2: leader + Chani in octaves over the crowd; battle toms.
  2:43  BRIDGE: strip one layer per bar to thumper + wind; the WORM
        RUMBLE answers the knocking from below (2:51, 2:58 — closer);
        the leader calls alone, unanswered. Rebuild: bass, strings,
        frame 8ths, tom fills + riser — cut on the last beat:
  3:13  the silent beat — one crowd breath ("mu—") hangs in it —
  3:14  CHORUS 3: everything slams on the downbeat — the ride. The kick
        enters (four on the floor); ney descants answer every cell.
  3:45  CHORUS 4: crowd + leader + Chani + THEME A on the duduk as the
        counter-line under the name; doubled war drums; the last line
        stretched ritardando across the seam.
  4:16  outro: the groove RIDES OUT — gallop, thumper and bass fade
        into the distance instead of stopping; one last far-off hum of
        the name; wind tail.

Output: /workspace/music/muaddib.wav (stereo, 44100 Hz, 16-bit).
"""

import os
import wave
import numpy as np
from scipy import signal

SR = 44100
DURATION = 296.0
N = int(SR * DURATION)
t = np.arange(N) / SR

rng = np.random.default_rng(12)   # twelve voices in the crowd

BPM = 124.0
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
B_RB = 92       # bridge rebuild (8) — cuts on beat 4 of bar 99
B_CH3 = 100     # CHORUS 3 (16) — the kick enters
B_CH4 = 116     # CHORUS 4 (16)
B_OUT = 132     # outro ride-out (16 + tail)
B_END = 148

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

WANDER = slow_noise(0.15, -0.025, 0.025)


def when(b, beat=0.0):
    tt = bar_t(b, beat)
    return max(0.0, tt + WANDER[min(N - 1, int(tt * SR))])


# --------------------------------------------------------------- material

CHORDS = {"D": [38, 50, 57, 62, 66],
          "Eb": [39, 51, 58, 63, 67],
          "Cm": [36, 48, 55, 60, 63],
          "Gm": [43, 50, 58, 62, 67]}
ROOT = {"D": 38, "Eb": 39, "Cm": 36, "Gm": 31}

CELL = ["D", "Eb", "Gm", "D"]
V8 = ["D", "D", "Cm", "D", "Gm", "Eb", "Cm", "D"]     # tonic-pedal verse
PRE8 = ["Gm", "Eb", "Cm", "Eb"] * 2
CHORD_MAP = (CELL + V8 * 2 + PRE8 + CELL * 4 + V8 * 2 + PRE8 + CELL * 4
             + ["Cm", "Eb"] * 8 + CELL * 4 + CELL * 4 + ["D"] * 16)
assert len(CHORD_MAP) == B_END

# THE HOOK — the name. "mu" = m-onset (hum opening into the vowel).
# Q: Muad'Dib, Muad'Dib — rising, hanging on A. A: Mu-ad-di-ib, falling
# F#–Eb–D onto the major tonic (the album cadence).
HOOK_Q = [(55, 1.0, "mu"), (57, 1.0, "a"), (58, 2.0, "i"),
          (57, 1.0, "mu"), (60, 1.0, "a"), (57, 2.0, "i")]
HOOK_A = [(54, 1.5, "mu"), (51, 1.5, "a"), (50, 2.0, "a"), (50, 3.0, "i")]

# Verse melody: one driving rhythm for Q and A (pushed 8ths on the front).
VERSE_Q = [(50, 1.5), (50, 0.5), (54, 1), (55, 1), (57, 2),
           (55, 1), (54, 1), (55, 1), (57, 1), (58, 3)]
VERSE_A = [(51, 1.5), (51, 0.5), (55, 1), (54, 1), (51, 2),
           (50, 1), (51, 1), (50, 1), (48, 1), (50, 3)]
VERSE_Q2 = [(50, 1.5), (50, 0.5), (54, 1), (57, 1), (58, 2),
            (57, 1), (55, 1), (57, 1), (58, 1), (60, 3)]
VERSE_A2 = [(51, 1.5), (51, 0.5), (55, 1), (54, 1), (51, 2),
            (51, 1), (50, 1), (51, 1), (48, 1), (50, 3)]
LYR_V1 = ["aeiouaeioa", "eaoiaeouaa", "oieauoeiaa", "ueaoiaeoua"]
LYR_V2 = ["ieaouieaoa", "aoeiuaeoaa", "eiouaeioaa", "oaeiuoeaua"]

PC_Q1 = [(55, 1.5, "u"), (57, 1.5, "e"), (58, 1.0, "i")]
PC_A1 = [(70, 1.5, "u"), (67, 1.5, "e"), (63, 1.0, "a")]
PC_Q2 = [(51, 1.5, "u"), (55, 1.5, "e"), (60, 1.0, "i")]
RISE = [(55, 4, "a"), (58, 4, "o"), (60, 4, "e"), (63, 3, "i")]
PICKUP = [(69, 0.7, "i")]

# the crowd's verse echoes (exact tails of the leader's lines)
ECHO_Q = [(57, 0.75, "o"), (58, 1.5, "a")]
ECHO_A = [(48, 0.75, "o"), (50, 1.5, "a")]
ECHO_Q2 = [(58, 0.75, "o"), (60, 1.5, "a")]      # verse-2 tails, his octave
ECHO_A2 = [(48, 0.75, "o"), (50, 1.5, "a")]
# the leader's tail-answer in chorus 1
LEAD_ANS = [(54, 0.75, "u"), (51, 0.75, "a"), (50, 1.5, "a")]
# the leader's lone unanswered bridge calls (verse material, thinned)
CALL_1 = [(50, 1.5, "a"), (54, 1.0, "e"), (55, 2.5, "o")]
CALL_2 = [(50, 1.5, "a"), (54, 1.0, "e"), (57, 2.5, "o")]

THEME_A = [(62, 2), (66, 1), (63, 1), (62, 2), (60, 2), (62, 3),
           (63, 1), (66, 2), (69, 2), (67, 2), (66, 1), (63, 1),
           (62, 4), (60, 2), (63, 2), (62, 4)]
NEY_ANS = [(81, 1.0), (79, 0.75), (78, 1.0), (75, 2.0)]


def up12(notes):
    return [(m + 12,) + tuple(rest) for m, *rest in notes]


def with_lyr(notes, lyr):
    return [(m, d, v) for (m, d), v in zip(notes, lyr)]


b2s = lambda nb: nb * BEAT

# ------------------------------------------------------- THE SINGING VOICE
# The sihaya engine verbatim, plus: 'm' onsets (vowel token "mu"/"ma"/...
# starts as the closed hum, opening over 80 ms) and per-voice det /
# formant-scatter params so the same engine can be massed into a crowd.

VOWELS = {"i": (270, 2300), "e": (530, 1840), "a": (730, 1090),
          "o": (570, 840), "u": (300, 870)}
SING_CACHE = {}


def sing_phrase(notes, female=False, hum=False, det=1.0, fs2=1.0):
    key = (tuple(notes), female, hum, round(det, 5), round(fs2, 4))
    if key in SING_CACHE:
        return SING_CACHE[key]
    seq = [(m, b2s(d), ("u" if hum else v)) for m, d, v in notes]
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
        # the closed 'm': the hum voicing, crossfaded under the vowel onset
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
    SING_CACHE[key] = out
    return out


# The crowd roster: fixed per-voice identities, reused for every line so
# the crowd stays the same ten people all song.
CROWD = []
for v in range(10):
    CROWD.append(dict(
        female=(v >= 6),
        det=1.0 + rng.uniform(-0.006, 0.006),
        fs2=1.0 + rng.uniform(-0.04, 0.04),
        pan=0.08 + 0.84 * v / 9.0,
        jit=rng.uniform(0.0, 0.05),
        g=rng.uniform(0.8, 1.05)))

crowd_L = np.zeros(N)
crowd_R = np.zeros(N)
HOOK_COUNT = 0


def crowd_sing(notes, t0, gain=1.0, hum=False):
    for vc in CROWD:
        nn = up12(notes) if vc["female"] else notes
        x = sing_phrase(nn, female=vc["female"], hum=hum,
                        det=vc["det"], fs2=vc["fs2"])
        g = gain * vc["g"] * (0.8 if vc["female"] else 1.0)
        add_at(crowd_L, x, t0 + vc["jit"], g * np.cos(vc["pan"] * np.pi / 2))
        add_at(crowd_R, x, t0 + vc["jit"], g * np.sin(vc["pan"] * np.pi / 2))


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


# ---------------------------------------------------------------- wind & drone
cp = [(0, 1.0), (bar_t(B_V1), 0.9), (bar_t(B_V1 + 1), 0.35),
      (bar_t(B_BR), 0.35), (bar_t(B_BR + 4), 0.8),
      (bar_t(B_RB), 0.8), (bar_t(B_RB + 4), 0.4),
      (bar_t(B_CH3), 0.3), (bar_t(B_OUT), 0.35),
      (bar_t(B_OUT + 8), 1.0), (DURATION, 1.0)]
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
commit(w_L, w_R, 0.14, env=calm)
del w_L, w_R
print("wind committed")

f_D1 = midi_to_hz(26)
breath = 0.7 + 0.3 * np.sin(2 * np.pi * 0.012 * t + 1.0)
drone = (np.sin(2 * np.pi * f_D1 * t) +
         0.55 * np.sin(2 * np.pi * f_D1 * 2 * t + 0.4) +
         0.30 * np.sin(2 * np.pi * f_D1 * 3 * t) +
         0.30 * np.sin(2 * np.pi * f_D1 * 3.003 * t))
drone *= breath
commit(drone, drone, 0.08, env=calm)
del drone, breath
print("drone committed")

# ---------------------------------------------------------------- thumper
# The planted thumper: a dry wood-knock at half-time. Bone dry, centered,
# constant gain — it owns the intro, the bridge, and the ride-out.

def make_knock():
    n = int(0.09 * SR)
    td = np.arange(n) / SR
    sos_k = signal.butter(2, [120, 600], "bandpass", fs=SR, output="sos")
    nz = signal.sosfilt(sos_k, rng.standard_normal(n)) * np.exp(-td * 50)
    nz /= np.max(np.abs(nz)) + 1e-12
    x = nz + 0.6 * np.sin(2 * np.pi * 72.0 * td) * np.exp(-td * 40)
    return x / (np.max(np.abs(x)) + 1e-12)


KNOCK = make_knock()
lay_L = np.zeros(N)
lay_R = np.zeros(N)
THUMP_BARS = (list(range(0, B_V1)) + list(range(B_BR, B_CH3)) +
              list(range(B_OUT, B_OUT + 12)))
for bb in THUMP_BARS:
    g = 0.9
    if bb >= B_OUT:
        g = 0.9 * max(0.0, 1.0 - (bb - B_OUT) / 12.0)   # walks away
    if bb == B_CH3 - 1:
        beats = (0.0, 2.0)      # keeps knocking right up to the cut
    else:
        beats = (0.0, 2.0)
    for beat in beats:
        add_at(lay_L, KNOCK, bar_t(bb, beat), g)
        add_at(lay_R, KNOCK, bar_t(bb, beat), g)
commit(lay_L, lay_R, 0.07)
print("thumper committed")

# ---------------------------------------------------------------- worm rumble
# The maker answers the thumper from below (bridge only, twice — closer).

def worm_rumble(dur=3.5):
    n = int(dur * SR)
    td = np.arange(n) / SR
    f = 27.0 + 28.0 * np.exp(-td * 1.2)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR)
    nz = np.cumsum(rng.standard_normal(n))
    nz -= np.linspace(nz[0], nz[-1], n)
    sos_r = signal.butter(2, 120, "low", fs=SR, output="sos")
    nz = signal.sosfilt(sos_r, nz)
    nz /= np.max(np.abs(nz)) + 1e-12
    env = (1 - np.exp(-td / 0.30)) * np.exp(-td * 0.9)
    x = (0.8 * sub + 0.5 * nz) * env
    return x / (np.max(np.abs(x)) + 1e-12)


lay_L[:] = 0.0
lay_R[:] = 0.0
add_at(lay_L, worm_rumble(3.5), bar_t(B_BR + 4), 0.7)
add_at(lay_R, worm_rumble(3.5), bar_t(B_BR + 4), 0.7)
add_at(lay_L, worm_rumble(4.0), bar_t(B_RB), 1.0)
add_at(lay_R, worm_rumble(4.0), bar_t(B_RB), 1.0)
commit(lay_L, lay_R, 0.13)
print("worm rumble committed")

# ---------------------------------------------------------------- baliset
# Strummed choruses only — this song doesn't fingerpick.

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


def baliset_note(m, dur=2.0):
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


def pluck(m, t0, gain, dur=2.0):
    note = baliset_note(m, dur)
    p = -0.2 + 0.4 * np.clip((m - 38) / 30.0, 0, 1)
    th = (0.5 + p * 0.5) * np.pi / 2
    add_at(bal_L, note, t0, gain * np.cos(th))
    add_at(bal_R, note, t0, gain * np.sin(th))


def strum(chord, t0, gain, up=False, dur=2.0):
    order = list(reversed(chord[-3:])) if up else chord
    stag = rng.uniform(0.010, 0.020)
    for i, m in enumerate(order):
        pluck(m, t0 + i * stag, gain * rng.uniform(0.85, 1.15), dur)


CHORUS_BARS = (set(range(B_CH1, B_V2)) | set(range(B_CH2, B_BR)) |
               set(range(B_CH3, B_OUT)))
for bb in range(B_END):
    if bb not in CHORUS_BARS:
        continue
    ch = CHORDS[CHORD_MAP[bb]]
    strum(ch, bar_t(bb, 0.0), 0.90)
    strum(ch, bar_t(bb, 1.5), 0.42, up=True, dur=1.2)
    strum(ch, bar_t(bb, 2.0), 0.62, dur=1.6)
    strum(ch, bar_t(bb, 3.5), 0.40, up=True, dur=1.2)
strum(CHORDS["D"], bar_t(B_OUT, 0.0), 0.85, dur=6.0)   # the ride-out ring
bal_L = reverb(bal_L, IR_L, wet=0.15)
bal_R = reverb(bal_R, IR_R, wet=0.15)
commit(bal_L, bal_R, 0.20)
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


lay_L[:] = 0.0
lay_R[:] = 0.0
# root 8ths with the ayyub push (accents on the and-of-2 / and-of-4)
PUSH8 = [(0.0, 0.95), (0.5, 0.5), (1.0, 0.6), (1.5, 0.85),
         (2.0, 0.9), (2.5, 0.5), (3.0, 0.6), (3.5, 0.8)]
BASS_OFF = set(range(B_BR + 2, B_RB))
for bb in range(B_V1, B_END):
    if bb in BASS_OFF:
        continue
    fade_out = 1.0
    if bb >= B_OUT:
        fade_out = max(0.0, 1.0 - (bb - B_OUT) / 10.0)
        if fade_out == 0.0:
            continue
    r = ROOT[CHORD_MAP[bb]]
    if bb == B_CH3 - 1:                      # bar 99: stop before the cut
        hits = PUSH8[:6]
    else:
        hits = PUSH8
    for beat, g in hits:
        x = bass_note(r, 0.22)
        add_at(lay_L, x, bar_t(bb, beat), g * fade_out)
        add_at(lay_R, x, bar_t(bb, beat), g * fade_out)
    if bb in (B_CH1 - 1, B_CH2 - 1):         # cadence walk into the chorus
        for beat, m in [(2.0, 36), (3.0, 39), (3.5, 38)]:
            x = bass_note(m, 0.22)
            add_at(lay_L, x, bar_t(bb, beat), 0.75)
            add_at(lay_R, x, bar_t(bb, beat), 0.75)
commit(lay_L, lay_R, 0.30)
print("bass committed")

# ---------------------------------------------------------------- kick
# User call: a soft four-on-the-floor in choruses 3–4 — the ride.

def make_kick():
    n = int(0.35 * SR)
    td = np.arange(n) / SR
    f = 45.0 + 105.0 * np.exp(-td * 55.0)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR)
    x *= (1 - np.exp(-td / 0.0008)) * np.exp(-td * 9.0)
    nz = rng.standard_normal(n)
    sos_c = signal.butter(2, [1800, 9000], "bandpass", fs=SR, output="sos")
    x += 0.22 * signal.sosfilt(sos_c, nz) * np.exp(-td * 120)
    return x / (np.max(np.abs(x)) + 1e-12)


KICK = make_kick()
lay_L[:] = 0.0
lay_R[:] = 0.0
for bb in range(B_CH3, B_OUT):
    for beat in (0.0, 1.0, 2.0, 3.0):
        add_at(lay_L, KICK, bar_t(bb, beat), 1.0)
        add_at(lay_R, KICK, bar_t(bb, beat), 1.0)
commit(lay_L, lay_R, 0.22)
print("kick committed (choruses 3-4)")

# ------------------------------------------------- ayyub darbuka + frame + war

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
# ayyub gallop, two cycles per 4/4 bar: D..k D.T. | D..k D.T.
AYYUB = {0: ("D", 1.0), 3: ("K", 0.5), 4: ("D", 0.85), 6: ("T", 0.8),
         8: ("D", 0.95), 11: ("K", 0.5), 12: ("D", 0.85), 14: ("T", 0.8)}
GROOVE_BARS = (set(range(B_V1, B_BR)) | set(range(B_CH3, B_OUT + 10)))
lay_L[:] = 0.0
lay_R[:] = 0.0
for bb in sorted(GROOVE_BARS):
    level = 0.62 if bb in CHORUS_BARS else 0.5
    if bb >= B_OUT:
        level = 0.5 * max(0.0, 1.0 - (bb - B_OUT) / 10.0)   # rides away
    if level <= 0.0:
        continue
    fill = bb % 4 == 3 and bb in CHORUS_BARS and bb + 1 in GROOVE_BARS
    for s in range(16):
        st = bar_t(bb, s * 0.25)
        if fill and s >= 12:
            g = (0.45 + 0.55 * (s - 12) / 3.0) * level
            add_at(lay_L, TEK, st, g * 0.9)
            add_at(lay_R, TEK, st, g * 0.7)
            continue
        if s in AYYUB:
            stroke, g = AYYUB[s]
            g *= level
            if stroke == "D":
                add_at(lay_L, DOUM, st, g)
                add_at(lay_R, DOUM, st, g)
            elif stroke == "T":
                p = 0.35 if s == 6 else 0.65
                add_at(lay_L, TEK, st, g * np.cos(p * np.pi / 2))
                add_at(lay_R, TEK, st, g * np.sin(p * np.pi / 2))
            else:
                add_at(lay_L, KA, st, g)
                add_at(lay_R, KA, st, g * 0.8)
        elif bb in CHORUS_BARS and s % 2 == 1 and rng.random() < 0.2:
            add_at(lay_L, KA, st, 0.5 * level)
            add_at(lay_R, KA, st, 0.4 * level)
# the intro pickup fill (bar 3): rising teks announce the groove
for s in range(8, 16):
    g = 0.3 + 0.7 * (s - 8) / 7.0
    add_at(lay_L, TEK, bar_t(3, s * 0.25), g * 0.8)
    add_at(lay_R, TEK, bar_t(3, s * 0.25), g * 0.65)
commit(lay_L, lay_R, 0.15)
print("ayyub darbuka committed")


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
lay_L[:] = 0.0
lay_R[:] = 0.0
FRAME_BARS = (set(range(B_PC1, B_CH1)) | set(range(B_PC2, B_CH2)) |
              set(range(B_RB + 4, B_CH3)))
for bb in sorted(FRAME_BARS):
    for i in range(8):
        g = 0.55 if i % 2 == 0 else 0.32
        add_at(lay_L, FRAME, bar_t(bb, i * 0.5), g)
        add_at(lay_R, FRAME, bar_t(bb, i * 0.5), g * 0.85)
commit(lay_L, lay_R, 0.08)
print("frame drum committed")


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


def make_tom(f0):
    n = int(0.38 * SR)
    td = np.arange(n) / SR
    f = f0 * (1.0 + 0.40 * np.exp(-td * 40.0))
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-td * 8.5)
    skin = signal.sosfilt(signal.butter(2, [300, 1500], "bandpass",
                                        fs=SR, output="sos"),
                          rng.standard_normal(n))
    skin *= np.exp(-td * 22.0)
    x = body + 0.35 * skin
    return x / (np.max(np.abs(x)) + 1e-12)


WAR = make_war_drum()
TOMS = [make_tom(165), make_tom(110), make_tom(80)]
lay_L[:] = 0.0
lay_R[:] = 0.0
for bb in sorted(CHORUS_BARS):
    if bb % 4 != 0:
        continue
    g = 1.0 + 0.2 * (bb >= B_CH4)
    add_at(lay_L, WAR, bar_t(bb, 0.0), g)
    add_at(lay_R, WAR, bar_t(bb, 0.0), g)
    if bb >= B_CH4:
        add_at(lay_L, WAR, bar_t(bb, 1.5), g * 0.5)
        add_at(lay_R, WAR, bar_t(bb, 1.5), g * 0.5)
add_at(lay_L, WAR, bar_t(B_OUT, 0.0), 0.95)
add_at(lay_R, WAR, bar_t(B_OUT, 0.0), 0.95)
commit(lay_L, lay_R, 0.16)
print("war drums committed")


def tom_fill(t0, gain=0.8):
    for i in range(8):
        tom = TOMS[i % 3]
        p = 0.25 + 0.5 * (i % 2)
        add_at(lay_L, tom, t0 + i * 0.25 * BEAT * 2,
               gain * (0.6 + 0.4 * i / 7) * np.cos(p * np.pi / 2))
        add_at(lay_R, tom, t0 + i * 0.25 * BEAT * 2,
               gain * (0.6 + 0.4 * i / 7) * np.sin(p * np.pi / 2))


lay_L[:] = 0.0
lay_R[:] = 0.0
# fills: into each chorus, every 8th chorus bar, and the bridge build
tom_fill(bar_t(B_CH1 - 1, 2.0))
tom_fill(bar_t(B_CH2 - 1, 2.0))
for bb in sorted(CHORUS_BARS):
    if bb % 8 == 7:
        tom_fill(bar_t(bb, 2.0), gain=0.65)
tom_fill(bar_t(B_RB + 6, 0.0), gain=0.75)
tom_fill(bar_t(B_RB + 7, 0.0), gain=0.95)
commit(lay_L, lay_R, 0.11)
print("battle toms committed")

# ---------------------------------------------------------------- oud

def oud_note(m, dur=0.5):
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
# verse 1: the oud doubles the crowd's echoes (an octave up)
for cell, tail in [(B_V1, ECHO_Q), (B_V1 + 4, ECHO_A),
                   (B_V1 + 8, ECHO_Q), (B_V1 + 12, ECHO_A)]:
    place_oud(up12([(m, d) for m, d, _ in tail]), bar_t(cell + 3, 1.5), 0.55)
# chorus riff: the hook in unison, every chorus
for b0 in sorted(b for b in CHORUS_BARS if b % 4 == 0):
    place_oud(up12([(m, d) for m, d, _ in HOOK_Q]), bar_t(b0), 0.40)
    place_oud(up12([(m, d) for m, d, _ in HOOK_A]), bar_t(b0 + 2), 0.40)
lay_L = reverb(lay_L, IR_L, wet=0.25)
lay_R = reverb(lay_R, IR_R, wet=0.25)
commit(lay_L, lay_R, 0.11)
print("oud committed")

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
        ([62, 63], B_PC1 + 4, B_CH1, 0.35, 0.30),
        ([62, 63], B_PC2 + 4, B_CH2, 0.5, 0.58),
        ([60, 63, 67], B_RB + 2, B_CH3, 0.9, 0.85)]:
    sw = tremolo_strings(chord, (b1 - b0) * BAR)
    add_at(lay_L, sw, bar_t(b0), gL)
    add_at(lay_R, sw, bar_t(b0), gR)
lay_L = reverb(lay_L, IR_L, wet=0.45)
lay_R = reverb(lay_R, IR_R, wet=0.45)
commit(lay_L, lay_R, 0.08)
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
rz_dur = 2 * BAR + 3 * BEAT                    # ends exactly at bar 99 beat 4
rz = riser(rz_dur)
add_at(lay_L, rz, bar_t(B_RB + 5, 1.0), 0.85)
add_at(lay_R, rz, bar_t(B_RB + 5, 1.0), 1.0)
commit(lay_L, lay_R, 0.08)
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
for b0 in (B_CH4, B_CH4 + 8):          # Theme A under the name
    v = voice_phrase(sec(THEME_A))
    add_at(lay_L, v, bar_t(b0), 0.8 * np.cos(0.55 * np.pi / 2))
    add_at(lay_R, v, bar_t(b0), 0.8 * np.sin(0.55 * np.pi / 2))
lay_L = reverb(lay_L, IR_L, wet=0.6)
lay_R = reverb(lay_R, IR_R, wet=0.6)
commit(lay_L, lay_R, 0.14)
print("duduk committed (Theme A, chorus 4)")

lay_L[:] = 0.0
lay_R[:] = 0.0
for b0 in list(range(B_CH3, B_OUT, 4)):
    v = ney_phrase(sec(NEY_ANS))
    add_at(lay_L, v, when(b0 + 3, 0.0), 0.65 * np.cos(0.60 * np.pi / 2))
    add_at(lay_R, v, when(b0 + 3, 0.0), 0.65 * np.sin(0.60 * np.pi / 2))
lay_L = reverb(lay_L, IR_L, wet=0.5)
lay_R = reverb(lay_R, IR_R, wet=0.5)
commit(lay_L, lay_R, 0.08)
print("ney committed")

# ---------------------------------------------------------------- THE VOICES

# intro: the crowd hums the name, far off — the name before the man
crowd_sing(HOOK_A, when(1, 2.0), gain=0.45, hum=True)
HOOK_COUNT += 1

# verse 1 — the leader; the crowd echoes every tail (the work-song move)
for i, (cell, mel) in enumerate([(B_V1, VERSE_Q), (B_V1 + 4, VERSE_A),
                                 (B_V1 + 8, VERSE_Q), (B_V1 + 12, VERSE_A)]):
    sing(with_lyr(mel, LYR_V1[i]), when(cell), gain=1.0)
for cell, echo in [(B_V1, ECHO_Q), (B_V1 + 4, ECHO_A),
                   (B_V1 + 8, ECHO_Q), (B_V1 + 12, ECHO_A)]:
    crowd_sing(echo, when(cell + 3, 1.5), gain=0.6)

# pre-chorus 1 — trades, the rise, her pickup
sing(PC_Q1, when(B_PC1), gain=0.82)
sing(PC_A1, when(B_PC1 + 1), female=True, gain=0.82)
sing(PC_Q2, when(B_PC1 + 2), gain=0.82)
sing(PC_A1, when(B_PC1 + 3), female=True, gain=0.82)
sing(RISE, when(B_PC1 + 4), gain=0.55)
sing(up12(RISE), when(B_PC1 + 4), female=True, gain=0.50)
sing(PICKUP, when(B_CH1 - 1, 3.3), female=True, gain=0.8)

# CHORUS 1 — the crowd sings the hook, the leader answers the tails
for b0 in range(B_CH1, B_V2, 4):
    crowd_sing(HOOK_Q, when(b0), gain=1.15)
    crowd_sing(HOOK_A, when(b0 + 2), gain=1.15)
    sing(LEAD_ANS, when(b0 + 3, 1.0), gain=0.85)
    HOOK_COUNT += 1

# verse 2 — Chani leads; leader and crowd alternate the echoes
for i, (cell, mel) in enumerate([(B_V2, VERSE_Q2), (B_V2 + 4, VERSE_A2),
                                 (B_V2 + 8, VERSE_Q2), (B_V2 + 12, VERSE_A2)]):
    sing(up12(with_lyr(mel, LYR_V2[i])), when(cell), female=True, gain=1.0)
sing(ECHO_Q2, when(B_V2 + 3, 1.5), gain=0.6)               # him
crowd_sing(ECHO_A2, when(B_V2 + 7, 1.5), gain=0.6)         # them
sing(ECHO_Q2, when(B_V2 + 11, 1.5), gain=0.6)              # him
crowd_sing(ECHO_A2, when(B_V2 + 15, 1.5), gain=0.65)       # them

# pre-chorus 2 — overlapping trades, the rise in canon
sing(PC_Q1, when(B_PC2), gain=0.82)
sing(PC_A1, when(B_PC2, 3.5), female=True, gain=0.82)
sing(PC_Q2, when(B_PC2 + 2), gain=0.82)
sing(PC_A1, when(B_PC2 + 2, 3.5), female=True, gain=0.82)
sing(RISE, when(B_PC2 + 4), gain=0.68)
sing(up12(RISE[:3] + [(63, 2, "i")]), when(B_PC2 + 5), female=True, gain=0.68)
sing(PICKUP, when(B_CH2 - 1, 3.3), female=True, gain=0.8)

# CHORUS 2 — leader + Chani in octaves over the crowd
for b0 in range(B_CH2, B_BR, 4):
    crowd_sing(HOOK_Q, when(b0), gain=1.0)
    crowd_sing(HOOK_A, when(b0 + 2), gain=1.0)
    sing(HOOK_Q, when(b0), gain=0.85)
    sing(up12(HOOK_Q), when(b0), female=True, gain=0.8)
    sing(HOOK_A, when(b0 + 2), gain=0.85)
    sing(up12(HOOK_A), when(b0 + 2), female=True, gain=0.8)
    HOOK_COUNT += 1

# bridge — the leader calls alone, unanswered (the worm answers instead)
sing(CALL_1, when(B_BR + 2), gain=0.8)
sing(CALL_2, when(B_BR + 6), gain=0.8)
# the crowd's lone breath in the silent beat
crowd_sing([(55, 0.9, "mu")], when(B_CH3 - 1, 3.2), gain=0.5)

# CHORUS 3 + 4 — everyone; ch4's last line stretches across the seam
for b0 in range(B_CH3, B_CH4, 4):
    crowd_sing(HOOK_Q, when(b0), gain=1.0)
    crowd_sing(HOOK_A, when(b0 + 2), gain=1.0)
    sing(HOOK_Q, when(b0), gain=0.9)
    sing(up12(HOOK_Q), when(b0), female=True, gain=0.85)
    sing(HOOK_A, when(b0 + 2), gain=0.9)
    sing(up12(HOOK_A), when(b0 + 2), female=True, gain=0.85)
    HOOK_COUNT += 1
for b0 in range(B_CH4, B_OUT - 4, 4):
    crowd_sing(HOOK_Q, when(b0), gain=1.0)
    crowd_sing(HOOK_A, when(b0 + 2), gain=1.0)
    sing(HOOK_Q, when(b0), gain=0.9)
    sing(up12(HOOK_Q), when(b0), female=True, gain=0.85)
    sing(HOOK_A, when(b0 + 2), gain=0.9)
    sing(up12(HOOK_A), when(b0 + 2), female=True, gain=0.85)
    HOOK_COUNT += 1
crowd_sing(HOOK_Q, when(B_OUT - 4), gain=1.0)
sing(HOOK_Q, when(B_OUT - 4), gain=0.9, stretch=1.1)
sing(up12(HOOK_Q), when(B_OUT - 4), female=True, gain=0.85, stretch=1.1)
crowd_sing(HOOK_A, when(B_OUT - 2, 0.5), gain=1.0)
sing(HOOK_A, when(B_OUT - 2, 0.5), gain=0.95, stretch=1.45)   # the rit,
sing(up12(HOOK_A), when(B_OUT - 2, 0.5), female=True, gain=0.9,
     stretch=1.45)                                            # across the seam
HOOK_COUNT += 1

# outro — the far-off hum again as the gallop walks away: the bookend
crowd_sing(HOOK_A, when(B_OUT + 8), gain=0.45, hum=True)
HOOK_COUNT += 1

paul_L = reverb(paul_L, IR_L, wet=0.22)
paul_R = reverb(paul_R, IR_R, wet=0.22)
commit(paul_L, paul_R, 0.30)
del paul_L, paul_R
print("LEADER committed")
chani_L = reverb(chani_L, IR_L, wet=0.22)
chani_R = reverb(chani_R, IR_R, wet=0.22)
commit(chani_L, chani_R, 0.26)
del chani_L, chani_R
print("CHANI committed")
crowd_L = reverb(crowd_L, IR_L, wet=0.5)
crowd_R = reverb(crowd_R, IR_R, wet=0.5)
commit(crowd_L, crowd_R, 0.24)
del crowd_L, crowd_R
print("THE CROWD committed")

# ---------------------------------------------------------------- master
del lay_L, lay_R
sos_hi = signal.butter(2, 3000, "high", fs=SR, output="sos")
mix_L += 0.15 * signal.sosfilt(sos_hi, mix_L)
mix_R += 0.15 * signal.sosfilt(sos_hi, mix_R)
sos_lo = signal.butter(2, 95, "low", fs=SR, output="sos")
mix_L += 0.22 * signal.sosfilt(sos_lo, mix_L)
mix_R += 0.22 * signal.sosfilt(sos_lo, mix_R)

fade(mix_L, fade_in=0.3, fade_out=8.0)
fade(mix_R, fade_in=0.3, fade_out=8.0)

peak = max(np.max(np.abs(mix_L)), np.max(np.abs(mix_R))) + 1e-12
mix_L = np.tanh(1.25 * mix_L / peak) / np.tanh(1.25) * 0.88
mix_R = np.tanh(1.25 * mix_R / peak) / np.tanh(1.25) * 0.88

stereo = np.empty((N, 2))
stereo[:, 0] = mix_L
stereo[:, 1] = mix_R
pcm = (stereo * 32767.0).astype(np.int16)

OUT_DIR = "/workspace/music"
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, "muaddib.wav")
with wave.open(OUT, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())

print(f"\nCreated: {os.path.abspath(OUT)}")
print(f"Duration: {N / SR:.1f} s  |  {SR} Hz stereo, 16-bit PCM  |  "
      f"{BPM:.0f} BPM  |  {N_LAYERS} committed layers")
print(f"Hook statements (sung): {HOOK_COUNT}  (target >= 14)")

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
            ("outro: the ride-out", bar_t(B_OUT), DURATION)]
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
        (rms["CHORUS 3"] > rms["CHORUS 2"], "chorus 3 > chorus 2 (the kick)"),
        (rms["CHORUS 4"] == max(rms.values()), "chorus 4 is the loudest"),
        (rms["bridge: teardown"] < min(rms["verse 1"], rms["CHORUS 1"]),
         "bridge trough is quiet"),
        (rms["outro: the ride-out"] < rms["verse 1"], "the ride-out settles")]:
    print(f"  {'PASS' if cond else 'WARN'}: {msg}")
    ok = ok and cond
if not ok:
    print("  -> rebalance section gains before shipping")

print("Seam checklist (what crosses each boundary):")
for line in [
        f"{bar_t(B_V1):6.1f} s  intro->v1:    crowd hum rings over the pickup fill",
        f"{bar_t(B_PC1):6.1f} s  v1->pc1:      crowd echo + oud overlap; groove unbroken",
        f"{bar_t(B_CH1):6.1f} s  pc1->ch1:     tom fill + bass walk + her pickup",
        f"{bar_t(B_V2):6.1f} s  ch1->v2:      last strum rings; gallop never stops",
        f"{bar_t(B_PC2):6.1f} s  v2->pc2:      crowd echo overlaps her last line",
        f"{bar_t(B_CH2):6.1f} s  pc2->ch2:     canon lands on fill + walk + pickup",
        f"{bar_t(B_BR):6.1f} s  ch2->bridge:  strip one layer per bar; thumper takes over",
        f"{bar_t(B_RB):6.1f} s  teardown->rebuild: the second (closer) worm rumble",
        f"{bar_t(B_CH3) - BEAT:6.1f} s  THE SILENT BEAT: one crowd breath ('mu-') in it",
        f"{bar_t(B_CH3):6.1f} s  ->ch3:        full band + kick on the downbeat",
        f"{bar_t(B_CH4):6.1f} s  ch3->ch4:     continuous groove + Theme A enters",
        f"{bar_t(B_OUT):6.1f} s  ch4->outro:   rit line finishes over the ride-out"]:
    print("  " + line)
