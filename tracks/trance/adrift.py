#!/usr/bin/env python3
"""
adrift.py — "Adrift" (~6:00, 137 BPM, C# natural minor). Dream trance,
the tide form — design notes: adrift_notes.md. Era: 1996 Italian dream
trance (the Children school: Robert Miles, Zhi-Vago, DJ Dado) — not a
cover; the era's signature triangle is the track: the piano theme on a
slightly dirty sampled piano, the wordless breath-choir above it, the
four-to-the-floor beat underneath.

THE CONCEPT — the sky, the ocean, clouds drifting by. The piano is the
drifting: once the theme starts moving it never stops, floating through
every seam. The kick and bass are the tide: they go out and come back
UNDERNEATH the still-playing melody — the kick re-enters on bar 5 of a
statement already in the air (printed and checked). The choir is the
sky. Ocean and clouds are form and texture only — no literal SFX.

  0:00  thesis    Solo dirty piano states the refrain; one cloud swell.
  0:14  intro     Kick @8, bass @12, hats @16, arp fades up @20.
  0:42  verse 1   Pluck-arp Q/A over C#m-A-E-B; open hat at midpoint.
  1:10  build 1   Snare roll + dark swell, piano pickup, crash ->
  1:24  CHORUS 1  The piano refrain x2, full kit; the signal's 1st call.
  1:52  verse 2   Counter-arp answers; claps; THE CHOIR fades in (pad).
  2:20  build 2   Longer roll, swell, one-bar drum dropout ->
  2:34  CHORUS 2  Refrain x2 under the choir sky. From here the piano
                  does not stop until the wave is over.
  3:02  THE DRIFT Tide out: kick+bass exit under the ring. Refrain x2
                  weightless; the signal's most distant call; then the
                  piano begins statement 3 ALONE —
  3:37  THE RETURN — the kick lands on bar 5 of that statement,
                  mid-phrase; bass and kit bloom under the unbroken
                  piano (eased sub); one more full statement.
  3:58  dip       Claps/ride out, one breath.
  4:05  THE WAVE  The fusion: refrain x3, warm lead countermelody
                  underneath, the choir answering every hang. Loudest.
  4:47  ride-out  Layers peel; kick keeps 4/4 — danceable to the edge.
  5:15  outro     Kick stops @184; solo piano bookend over choir breath.
  5:43  tail      Last choir chord, air shimmer, one piano note.

Sanctioned era vocabulary: snare rolls + dark bandlimited swells; the
signal motif (long feedback delay). Banned by construction: the rolling
16th bass (retired here), acid resonance, sidechain pump, white-noise
wash, reverse cymbals, toms, supersaws, trance gates (penumbra's),
bells (farlight's), literal SFX. C#-natural-minor diatonic throughout
(printed/checked). Everything synthesized (numpy + scipy).
Output: /workspace/music/adrift.wav + adrift.mp3 (192k).
"""

import pathlib
import subprocess
import wave
import numpy as np
from scipy import signal

SR = 44100
BPM = 137.0
BEAT = 60.0 / BPM
BAR = BEAT * 4
STEP = BEAT / 4
GRID0 = 0.5

rng = np.random.default_rng(1996)   # the year the dream broke

# ----------------------------------------------------- section boundaries (bars)
B_INTRO = 8      # kick @8, bass @12, hats @16, arp fade @20
B_V1 = 24        # verse 1 (open hat @32)
B_B1 = 40        # build 1
B_CH1 = 48       # chorus 1
B_V2 = 64        # verse 2 (claps, the choir arrives)
B_B2 = 80        # build 2 (drum dropout bar 87)
B_CH2 = 88       # chorus 2 — piano continuous from here to the wave's end
B_DRIFT = 104    # the tide goes out
B_RET = 124      # the kick lands mid-statement (statement began @120)
B_DIP = 136      # one breath
B_WAVE = 140     # the fusion
B_RO = 164       # ride-out (reverse peel)
B_OUT = 180      # outro; kick stops @184; bookend statement @188
B_KSTOP = 184
B_BOOK = 188
B_TAIL = 196
B_END = 202

STRADDLE_B0 = 120                    # the statement the kick lands inside

DURATION = GRID0 + B_END * BAR + 6.0
N = int(SR * DURATION)


def bar_t(b, beat=0.0):
    return GRID0 + b * BAR + beat * BEAT


SECS = [("thesis", 0), ("intro", B_INTRO), ("v1", B_V1), ("b1", B_B1),
        ("ch1", B_CH1), ("v2", B_V2), ("b2", B_B2), ("ch2", B_CH2),
        ("drift", B_DRIFT), ("ret", B_RET), ("dip", B_DIP),
        ("wave", B_WAVE), ("ro", B_RO), ("out", B_OUT), ("tail", B_TAIL)]


def section_of(b):
    for name, b0 in reversed(SECS):
        if b >= b0:
            return name
    return "thesis"


# ---------------------------------------------------------------- helpers


def midi_to_hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def fade(x, fade_in=0.4, fade_out=8.0):
    ni, no = int(fade_in * SR), int(fade_out * SR)
    x[:ni] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(ni) / ni)
    x[-no:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(no) / no)
    return x


def make_reverb_ir(seconds, decay, seed):
    r = np.random.default_rng(seed)
    n = int(seconds * SR)
    ir = r.standard_normal(n) * np.exp(-np.arange(n) / SR / decay)
    sos = signal.butter(2, 4200, "low", fs=SR, output="sos")
    ir = signal.sosfilt(sos, ir)
    return ir / np.sqrt(np.sum(ir ** 2))


IR_L = make_reverb_ir(5.5, 2.8, 7)
IR_R = make_reverb_ir(5.5, 2.8, 11)


def reverb(x, ir, wet=0.5):
    tail = signal.oaconvolve(x, ir)[: len(x)]
    tail /= np.max(np.abs(tail)) + 1e-12
    tail *= np.max(np.abs(x)) + 1e-12
    return (1 - wet) * x + wet * tail


def add_at(buf, x, start_s, gain=1.0):
    i0 = int(start_s * SR)
    end = min(len(buf), i0 + len(x))
    if end > i0:
        buf[i0:end] += x[: end - i0] * gain


def place_pan(layL, layR, clip, t0, gain, pan):
    add_at(layL, clip, t0, gain * np.cos(pan * np.pi / 2))
    add_at(layR, clip, t0, gain * np.sin(pan * np.pi / 2))


def glide_curve(notes, n, tau=0.05):
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


mix_L = np.zeros(N)
mix_R = np.zeros(N)


def commit(layer_L, layer_R, weight, env=None):
    global mix_L, mix_R
    peak = max(np.max(np.abs(layer_L)), np.max(np.abs(layer_R)), 1e-12)
    s = weight / peak
    if env is None:
        mix_L += layer_L * s
        mix_R += layer_R * s
    else:
        mix_L += layer_L * env * s
        mix_R += layer_R * env * s


lay_L = np.zeros(N)
lay_R = np.zeros(N)


def clear():
    lay_L[:] = 0.0
    lay_R[:] = 0.0


# ============================================================= harmony
# ONE progression family: C#m A E B | C#m A B C#m (i-VI-III-VII, the
# dream-era shape, closing home every 8 bars). One chord per bar,
# anchored to the statement grid. chord = (bass_root_midi, pad voicing,
# choir voicing, arp voicing)

CsM = (37, (49, 56, 61, 64), (61, 64, 68), (61, 64, 68))   # C#m
A_ = (33, (45, 52, 57, 61), (61, 64, 69), (57, 61, 64))    # A
E_ = (40, (52, 56, 59, 64), (59, 64, 68), (56, 59, 64))    # E
B_ = (35, (47, 54, 59, 63), (59, 63, 66), (59, 63, 66))    # B

PROG8 = [CsM, A_, E_, B_, CsM, A_, B_, CsM]
APPROACH = {33: 32, 40: 39, 35: 33, 37: 35}   # diatonic step below next root

CHORD_AT = [CsM] * B_END


def fill(b0, b1, seq):
    for b in range(b0, b1):
        CHORD_AT[b] = seq[(b - b0) % len(seq)]


fill(0, B_DRIFT, PROG8)                  # statements at multiples of 8 aligned
fill(B_DRIFT, B_DIP, PROG8)              # drift/return statements aligned
fill(B_DIP, B_WAVE, [CsM, CsM, A_, A_])  # the dip rocks i <-> VI
fill(B_WAVE, B_END, PROG8)               # wave/outro/bookend/tail aligned

# ============================================================= the melody
# THE REFRAIN — identical at every statement. 8 bars, Q/A: the
# antecedent floats up and HANGS on B5 (the b7 — Aeolian, it hangs
# rather than leads, root of the off-tonic VII bar); the consequent
# answers from above and falls HOME to C#5 over the closing i bar.
# Dream-simple: quarters and halves only.
REFRAIN = [(68, 1), (73, 1), (76, 2),    # C#m: G#4 C#5 E5 — floats up
           (78, 1), (76, 1), (73, 2),    # A:   F#5 E5 C#5 — leans back
           (80, 2), (78, 1), (76, 1),    # E:   G#5 F#5 E5 — brightens
           (78, 1), (80, 1), (83, 2),    # B:   F#5 G#5 B5 — THE HANG (b7)
           (81, 1), (80, 1), (76, 2),    # C#m: A5 G#5 E5 — answers from above
           (78, 1), (76, 1), (73, 2),    # A:   the rhyme of bar 2
           (78, 1), (75, 1), (76, 2),    # B:   F#5 D#5 E5 — leaning home
           (75, 1), (73, 3)]             # C#m: D#5 C#5 — HOME
BAR_NOTES = [REFRAIN[3 * i:3 * i + 3] for i in range(7)] + [REFRAIN[21:]]
HANG_BAR, HANG_MIDI = 3, 83              # bar offset + pitch of the hang

# verse Q/A phrases (the pluck-arp carries them; 4 bars each)
VERSE_Q = [(73, 1), (76, 1), (78, 1), (80, 1), (81, 2), (78, 2),
           (80, 1.5), (76, 0.5), (78, 2), (83, 2), (80, 2)]
VERSE_A = [(76, 1), (78, 1), (80, 1), (81, 1), (80, 2), (76, 2),
           (78, 1.5), (75, 0.5), (76, 2), (75, 2), (73, 2)]

# the warm-lead countermelody (THE WAVE only — the fusion): long tones
# under the piano, C#4 register, resolving home with it
COUNTER = [(68, 4), (69, 2), (66, 2), (64, 4), (66, 2), (68, 2),
           (69, 2), (68, 2), (66, 4), (63, 2), (64, 2), (61, 4)]

STATEMENTS = []        # (bar, label, counted)
PIANO_EVENTS = []      # (onset_s, dur_s) — every placed melody note
SIGNAL_EVENTS = []     # (bar, section)
CHOIR_ANSWERS = []     # bar
COUNTER_SPANS = []     # (t0, t1)
BASS_ONSETS = {}       # bar -> count


# ============================================================= drum kit (dry)

def make_kick():
    n = int(0.45 * SR)
    td = np.arange(n) / SR
    f_curve = 42.0 + 100.0 * np.exp(-td * 46.0)      # rounder/deeper — the era drift
    body = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    sub = np.sin(2 * np.pi * (36 + 14 * np.exp(-td * 3)) * td) * np.exp(-td * 3.0)
    sos_c = signal.butter(2, [1600, 8000], "bandpass", fs=SR, output="sos")
    click = signal.sosfilt(sos_c, rng.standard_normal(n)) * np.exp(-td * 480)
    click /= np.max(np.abs(click)) + 1e-12
    env = (1 - np.exp(-td / 0.0009)) * np.exp(-td * 7.2)
    x = body * env + 0.55 * sub + 0.36 * click * (1 - np.exp(-td / 0.0009))
    return x / (np.max(np.abs(x)) + 1e-12)


def make_hat(open_=False):
    n = int((0.13 if open_ else 0.04) * SR)
    td = np.arange(n) / SR
    sos_h = signal.butter(4, 7500, "high", fs=SR, output="sos")
    x = signal.sosfilt(sos_h, rng.standard_normal(n)) * np.exp(-td * (26 if open_ else 120))
    return x / (np.max(np.abs(x)) + 1e-12)


def make_clap():
    n = int(0.32 * SR)
    td = np.arange(n) / SR
    sos = signal.butter(2, [900, 5200], "bandpass", fs=SR, output="sos")
    x = np.zeros(n)
    for i, dmp in [(0, 130.0), (1, 130.0), (2, 130.0), (3, 24.0)]:
        i0 = int(i * 0.011 * SR)
        x[i0:] += signal.sosfilt(sos, rng.standard_normal(n - i0)) * np.exp(-td[: n - i0] * dmp)
    return x / (np.max(np.abs(x)) + 1e-12)


def make_ride():
    n = int(0.4 * SR)
    td = np.arange(n) / SR
    nz = rng.standard_normal(n)
    a = signal.butter(2, [4000, 7000], "bandpass", fs=SR, output="sos")
    b = signal.butter(2, [8000, 12000], "bandpass", fs=SR, output="sos")
    x = signal.sosfilt(a, nz) * np.exp(-td * 9) + 0.7 * signal.sosfilt(b, nz) * np.exp(-td * 6)
    x += 0.18 * np.sin(2 * np.pi * 5400 * td) * np.exp(-td * 8)
    return x / (np.max(np.abs(x)) + 1e-12)


def make_crash():
    n = int(2.2 * SR)
    td = np.arange(n) / SR
    x = signal.sosfilt(signal.butter(2, 5000, "high", fs=SR, output="sos"),
                       rng.standard_normal(n)) * np.exp(-td * 2.0)
    x *= 1 - np.exp(-td / 0.002)
    return x / (np.max(np.abs(x)) + 1e-12)


def make_snare():
    n = int(0.22 * SR)
    td = np.arange(n) / SR
    tone = (np.sin(2 * np.pi * 185 * td) + np.sin(2 * np.pi * 330 * td)) * np.exp(-td * 26)
    noise = signal.sosfilt(signal.butter(2, [1500, 9000], "bandpass", fs=SR, output="sos"),
                           rng.standard_normal(n)) * np.exp(-td * 30)
    x = 0.6 * tone + noise
    x *= 1 - np.exp(-td / 0.0008)
    return x / (np.max(np.abs(x)) + 1e-12)


KICK = make_kick()
CHAT = make_hat()
OHAT = make_hat(True)
CLAP = make_clap()
RIDE = make_ride()
CRASH = make_crash()
SNARE = make_snare()
# no reverse cymbal (nachtkind's), no toms (ungeschrieben's) — identity

DROPOUT_BAR = B_CH2 - 1              # build 2's one-bar drum dropout


def tide_out(b):
    return B_DRIFT <= b < B_RET      # the tide: no drums, no bass


KICK_G = {"intro": 0.72, "v1": 0.8, "b1": 0.88, "ch1": 0.95, "v2": 0.88,
          "b2": 0.92, "ch2": 1.0, "ret": 1.0, "dip": 0.9, "wave": 1.0,
          "ro": 0.95, "out": 0.72}

clear()
for b in range(B_INTRO, B_KSTOP):
    s = section_of(b)
    if tide_out(b) or b == DROPOUT_BAR:
        continue
    g = KICK_G[s]
    if s == "ret":
        g *= min(1.0, 0.7 + 0.12 * (b - B_RET))     # the return blooms in
    for beat in range(4):
        add_at(lay_L, KICK, bar_t(b, beat), g)
        add_at(lay_R, KICK, bar_t(b, beat), g)
commit(lay_L, lay_R, 0.34)
print("kick committed")

clear()
CH = [0.5, 0.28, 0.0, 0.34]          # per-16th gain cell (slot 2 = open hat)
HAT_G = {"intro": 0.7, "v1": 0.8, "b1": 0.85, "ch1": 0.9, "v2": 0.85,
         "b2": 0.9, "ch2": 0.95, "ret": 0.95, "dip": 0.7, "wave": 1.0,
         "ro": 0.85, "out": 0.55}
for b in range(16, B_KSTOP):
    s = section_of(b)
    if tide_out(b) or b == DROPOUT_BAR:
        continue
    g = HAT_G[s]
    for beat in range(4):
        for sx in range(4):
            if CH[sx] <= 0:
                continue
            add_at(lay_L, CHAT, bar_t(b, beat + sx * 0.25), g * CH[sx] * 0.9)
            add_at(lay_R, CHAT, bar_t(b, beat + sx * 0.25), g * CH[sx])
        if 32 <= b < 176:                            # offbeat open hat
            add_at(lay_L, OHAT, bar_t(b, beat + 0.5), g * 0.85)
            add_at(lay_R, OHAT, bar_t(b, beat + 0.5), g * 0.75)
commit(lay_L, lay_R, 0.07)
print("hats committed")

clear()
CLAP_G = {"v2": 0.7, "b2": 0.8, "ch2": 0.9, "ret": 0.9, "wave": 1.0, "ro": 0.7}
for b in range(B_V2, 168):
    s = section_of(b)
    if s not in CLAP_G or tide_out(b) or b == DROPOUT_BAR:
        continue
    for beat in (1, 3):
        p = 0.42 if beat == 1 else 0.58
        place_pan(lay_L, lay_R, CLAP, bar_t(b, beat), CLAP_G[s], p)
commit(lay_L, lay_R, 0.09)
print("claps committed")

clear()
RIDE_G = {"ret": 0.8, "wave": 1.0}
for b in range(B_RET, B_RO):
    s = section_of(b)
    if s not in RIDE_G:
        continue
    for e in range(8):
        g = RIDE_G[s] * (0.7 if e % 2 == 0 else 0.45)
        place_pan(lay_L, lay_R, RIDE, bar_t(b, e * 0.5), g, 0.5)
commit(lay_L, lay_R, 0.04)
print("ride committed")

clear()
for b, g in [(B_CH1, 0.6), (B_CH2, 0.7), (B_DRIFT, 0.45),
             (B_RET, 0.8),                    # the return — softened slam
             (B_WAVE, 0.9), (B_RO, 0.5), (B_OUT, 0.4)]:
    place_pan(lay_L, lay_R, CRASH, bar_t(b), g, 0.5)
commit(lay_L, lay_R, 0.05)
print("crashes committed")

clear()


def roll(b0, b1, base):
    nbars = b1 - b0
    for b in range(b0, b1):
        u = (b - b0) / nbars
        div = 4 if u < 0.5 else (8 if u < 0.85 else 16)
        for s in range(div):
            g = base * (0.4 + 0.6 * u) * (0.7 + 0.3 * (s % 2))
            place_pan(lay_L, lay_R, SNARE, bar_t(b, s * 4.0 / div), g, 0.5)


roll(B_B1 + 4, B_CH1, 0.45)
roll(B_B2 + 4, B_CH2, 0.55)          # rides through the dropout bar
roll(B_WAVE - 2, B_WAVE, 0.5)
commit(lay_L, lay_R, 0.07)
print("rolls committed")


# ============================================================= THE BASS
# The era-shift bass (notes amendment 3): the rolling 16th oscillator is
# retired. A round 8th-note octave-bounce riff — Children-soft core,
# BBE-melodic movement, U96 smear on top. Near-triangle core (sine +
# soft 2nd/3rd harmonic), NO filter resonance anywhere; the SMEAR is a
# parallel tanh(2.2) copy bandpassed 80-700 Hz and diffused through a
# 35 ms noise burst — the smeared-record blur, mixed at 0.25.

SMEAR_BURST = rng.standard_normal(int(0.035 * SR)) * \
    np.exp(-np.arange(int(0.035 * SR)) / (0.012 * SR))
SMEAR_BURST /= np.sqrt(np.sum(SMEAR_BURST ** 2))
SMEAR_SOS = signal.butter(2, [80, 700], "bandpass", fs=SR, output="sos")

bass_cache = {}


def bass_note(midi, dur=BEAT * 0.45):
    key = (midi, round(dur, 3))
    if key in bass_cache:
        return bass_cache[key]
    f = midi_to_hz(midi)
    n = int((dur + 0.06) * SR)
    td = np.arange(n) / SR
    core = (np.sin(2 * np.pi * f * td) + 0.35 * np.sin(4 * np.pi * f * td)
            + 0.12 * np.sin(6 * np.pi * f * td))
    core *= (1 - np.exp(-td / 0.008)) * np.clip((dur - td) / 0.05, 0, 1)
    smear = signal.sosfilt(SMEAR_SOS, np.tanh(2.2 * core))
    smear = signal.oaconvolve(smear, SMEAR_BURST)[:n]
    smear /= np.max(np.abs(smear)) + 1e-12
    x = core + 0.25 * smear
    bass_cache[key] = x / (np.max(np.abs(x)) + 1e-12)
    return bass_cache[key]


# patterns: (eighth_position, offset_from_root, gain); +7 = the fifth
PAT_SOFT = [(0, 0, 0.9), (2, 12, 0.75), (4, 0, 0.9), (6, 12, 0.75)]
PAT_DRIVE = [(0, 0, 0.9), (1, 0, 0.6), (2, 12, 0.8), (4, 0, 0.9),
             (5, 7, 0.6), (6, 12, 0.8)]
BASS_G = {"intro": 0.8, "v1": 0.9, "b1": 0.95, "ch1": 1.0, "v2": 0.95,
          "b2": 1.0, "ch2": 1.0, "ret": 1.0, "dip": 0.9, "wave": 1.0,
          "ro": 0.95, "out": 0.75}
DRIVE_SECS = ("ch1", "ch2", "ret", "wave")

clear()
for b in range(12, B_KSTOP + 2):
    s = section_of(b)
    if s not in BASS_G or tide_out(b):
        continue
    root = CHORD_AT[b][0]
    nxt = CHORD_AT[b + 1][0] if b + 1 < B_END else root
    pat = list(PAT_DRIVE if s in DRIVE_SECS else PAT_SOFT)
    if nxt != root:                                  # the walking approach 8th
        pat.append((7, APPROACH[nxt] - root, 0.7))
    g = BASS_G[s]
    if s == "ret":
        g *= min(1.0, 0.7 + 0.12 * (b - B_RET))     # blooms with the kick
    BASS_ONSETS[b] = len(pat)
    for pos, off, gg in pat:
        x = bass_note(root + off)
        add_at(lay_L, x, bar_t(b, pos * 0.5), gg * g)
        add_at(lay_R, x, bar_t(b, pos * 0.5), gg * g)
commit(lay_L, lay_R, 0.27)
print(f"bass committed ({len(bass_cache)} cached; 8th octave-bounce + smear)")

# the sustained sub — C#1 tonic pedal, return + wave only. farlight v2's
# speaker lesson baked in: 0.25 s attacks + per-bar entry bloom.
clear()
F_SUB = midi_to_hz(25)
for b0, b1, base in [(B_RET, B_DIP, 0.7), (B_WAVE, B_RO, 0.85)]:
    for i, b in enumerate(range(b0, b1)):
        seg_n = int(BAR * SR)
        td = np.arange(seg_n) / SR
        sub = np.sin(2 * np.pi * F_SUB * td) * np.minimum(
            np.clip(td / 0.25, 0, 1), np.clip((BAR - td) / 0.1, 0, 1))
        g = base * min(1.0, 0.55 + 0.15 * i)
        add_at(lay_L, sub, bar_t(b), g)
        add_at(lay_R, sub, bar_t(b), g)
commit(lay_L, lay_R, 0.09)
print("sustained sub committed (bloomed entries)")


# ============================================================= THE PIANO
# The centerpiece: the M1-era recipe (inharmonic partials, two detuned
# strings, hammer) re-voiced BRIGHT (1/k^1.15), then aged — the warm
# dirt dial (notes amendment 1): ZOH resample to SR/3 (~14.7 kHz
# effective, the sampler sheen), wow +/-0.04% at 0.3 Hz (worn-sample
# drift), tanh(0.9), lowpass 7.5 kHz. Upfront: dry-ish center, hall on
# the tail only.

ZOH_FACTOR = 3
WOW_DEPTH = 0.0004
WOW_HZ = 0.3
PIANO_LP = signal.butter(2, 7500, "low", fs=SR, output="sos")

piano_cache = {}


def piano_note(midi, dur):
    key = (midi, round(dur, 2))
    if key in piano_cache:
        return piano_cache[key]
    f = midi_to_hz(midi)
    n = int((dur + 1.0) * SR)
    td = np.arange(n) / SR
    out = np.zeros(n)
    B_inh = 0.00035
    for k in range(1, min(16, int(9000 / f)) + 1):
        fk = f * k * np.sqrt(1 + B_inh * k * k)
        dec = 0.9 + 0.45 * k + f * 0.0012
        g = 1.0 / k ** 1.15
        for det in (0.9994, 1.0006):
            out += g * np.sin(2 * np.pi * fk * det * td +
                              rng.uniform(0, 2 * np.pi)) * np.exp(-td * dec)
    sos_h = signal.butter(2, [1500, 4000], "bandpass", fs=SR, output="sos")
    hammer = signal.sosfilt(sos_h, rng.standard_normal(n)) * np.exp(-td * 350)
    hammer /= np.max(np.abs(hammer)) + 1e-12
    out += 0.20 * hammer
    env = (1 - np.exp(-td / 0.0015)) * np.clip((dur + 0.45 - td) / 0.45, 0, 1)
    x = out * env
    # THE DIRT (warm dial): sampler ZOH, worn-sample wow, soft saturation
    x = np.repeat(x[::ZOH_FACTOR], ZOH_FACTOR)[:n]
    idx = np.arange(n) * (1.0 + WOW_DEPTH * np.sin(
        2 * np.pi * WOW_HZ * td + rng.uniform(0, 2 * np.pi)))
    x = np.interp(np.clip(idx, 0, n - 1), np.arange(n), x)
    x = np.tanh(0.9 * x)
    x = signal.sosfilt(PIANO_LP, x)
    piano_cache[key] = x / (np.max(np.abs(x)) + 1e-12)
    return piano_cache[key]


def place_piano(midi, t0, dur, gain):
    x = piano_note(midi, dur)
    p = np.clip(0.5 + (midi - 76) * 0.012, 0.25, 0.75)
    add_at(lay_L, x, t0, gain * np.cos(p * np.pi / 2))
    add_at(lay_R, x, t0, gain * np.sin(p * np.pi / 2))
    PIANO_EVENTS.append((t0, dur))


LH_DYAD = {37: (49, 56), 33: (45, 52), 40: (52, 59), 35: (47, 54)}


def place_statement(b0, gain, label, counted, lh=False, octave=False):
    tm = bar_t(b0)
    for m, d in REFRAIN:
        place_piano(m, tm, d * BEAT, gain)
        if octave:
            place_piano(m + 12, tm, d * BEAT, gain * 0.35)
        tm += d * BEAT
    if lh:
        for bi in range(8):
            for m in LH_DYAD[CHORD_AT[b0 + bi][0]]:
                place_piano(m, bar_t(b0 + bi), 3.5 * BEAT, gain * 0.4)
    STATEMENTS.append((b0, label, counted))


def place_fragment(b0, nbars, gain):
    tm = bar_t(b0)
    for bi in range(nbars):
        for m, d in BAR_NOTES[bi % 2]:               # the circling bars 1-2
            place_piano(m, tm, d * BEAT, gain)
            tm += d * BEAT


clear()
place_statement(0, 0.95, "THESIS (solo)", counted=True)
for k, b0 in enumerate((B_CH1, B_CH1 + 8)):
    place_statement(b0, 0.9, f"chorus 1 stmt {k + 1}", counted=True, lh=True)
for k, b0 in enumerate((B_CH2, B_CH2 + 8)):
    place_statement(b0, 0.9, f"chorus 2 stmt {k + 1}", counted=True, lh=True)
for k, b0 in enumerate((B_DRIFT, B_DRIFT + 8)):
    place_statement(b0, 1.0, f"THE DRIFT stmt {k + 1} (weightless)", counted=True)
place_statement(STRADDLE_B0, 1.0, "THE STRADDLE (kick lands on its bar 5)",
                counted=True)
place_statement(B_RET + 4, 0.95, "the return stmt (full)", counted=True, lh=True)
place_fragment(B_DIP, 4, 0.65)                       # the dip breathes, unbroken
for k, b0 in enumerate((B_WAVE, B_WAVE + 8, B_WAVE + 16)):
    place_statement(b0, 1.0, f"THE WAVE stmt {k + 1} (fusion)", counted=True,
                    lh=True, octave=True)
place_fragment(B_RO, 16, 0.6)                        # ride-out: the tune dissolves
place_fragment(B_OUT, 8, 0.5)                        # ...into the outro
place_statement(B_BOOK, 0.8, "BOOKEND (solo)", counted=True)
place_piano(73, bar_t(B_TAIL + 2), 4.0, 0.55)        # one last C#5
lay_L = reverb(lay_L, IR_L, 0.4)
lay_R = reverb(lay_R, IR_R, 0.4)
commit(lay_L, lay_R, 0.27)
print(f"piano committed ({len(piano_cache)} cached notes)")


# ============================================================= pluck arp
# lost's glassy pluck on the new progression: the 16th verse texture and
# the carrier of the verse Q/A phrases.

pluck_cache = {}


def pluck(midi, dur=STEP * 3):
    if midi in pluck_cache:
        return pluck_cache[midi]
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    v = np.zeros(n)
    for det in (0.998, 1.0, 1.002):
        for k in range(1, min(12, int(7000 / f)) + 1):
            v += np.sin(2 * np.pi * k * f * det * td) / k ** 1.2
    v = signal.sosfilt(signal.butter(2, 3800, "low", fs=SR, output="sos"), v)
    v *= (1 - np.exp(-td / 0.003)) * np.exp(-td * 9.0)
    pluck_cache[midi] = v / (np.max(np.abs(v)) + 1e-12)
    return pluck_cache[midi]


ARP_PAT = [0, 2, 1, 3, 0, 2, 4, 3]
ARP_G = {"v1": 0.6, "b1": 0.65, "ch1": 0.7, "v2": 0.65, "b2": 0.7,
         "ch2": 0.7, "ret": 0.7, "dip": 0.55, "wave": 0.8, "ro": 0.55}
clear()
for b in range(20, 172):
    s = section_of(b)
    if s == "intro":
        g0 = 0.2 + 0.1 * (b - 20)                    # fades up into verse 1
    elif s in ARP_G:
        if tide_out(b) or b == DROPOUT_BAR:
            continue
        g0 = ARP_G[s]
    else:
        continue
    voicing = CHORD_AT[b][3]
    notes = list(voicing) + [voicing[1] + 12]
    for sx in range(16):
        idx = ARP_PAT[sx % len(ARP_PAT)] % len(notes)
        m = notes[idx]
        pan = 0.5 + 0.4 * (idx / (len(notes) - 1) - 0.5)
        place_pan(lay_L, lay_R, pluck(m), bar_t(b, sx * 0.25),
                  g0 * (0.9 if sx % 2 else 1.0), pan)
        if s == "wave" and sx % 4 == 2:              # glitter in the wave
            place_pan(lay_L, lay_R, pluck(m + 12), bar_t(b, sx * 0.25),
                      0.3, 1.0 - pan)


def place_pluck_theme(notes, t0, gain, pan):
    tm = t0
    for m, d in notes:
        place_pan(lay_L, lay_R, pluck(m), tm, gain, pan)
        place_pan(lay_L, lay_R, pluck(m), tm + STEP, gain * 0.45, pan)
        tm += d * BEAT


for b0 in (B_V1, B_V1 + 8):
    place_pluck_theme(VERSE_Q, bar_t(b0), 1.0, 0.38)
    place_pluck_theme(VERSE_A, bar_t(b0 + 4), 1.0, 0.38)
for b0 in (B_V2, B_V2 + 8):                          # v2: the counter-arp answers
    place_pluck_theme(VERSE_Q, bar_t(b0), 1.0, 0.38)
    place_pluck_theme([(m + 12, d) for m, d in VERSE_Q], bar_t(b0, 2), 0.5, 0.68)
    place_pluck_theme(VERSE_A, bar_t(b0 + 4), 1.0, 0.38)
    place_pluck_theme([(m + 12, d) for m, d in VERSE_A], bar_t(b0 + 4, 2), 0.5, 0.68)
lay_L = reverb(lay_L, IR_L, 0.3)
lay_R = reverb(lay_R, IR_R, 0.3)
commit(lay_L, lay_R, 0.12)
print(f"pluck arp committed ({len(pluck_cache)} cached)")


# ============================================================= THE CHOIR
# The breath choir (notes: the "soft vocals, kept instrumental") — the
# one salvage from unsung's vowel machinery, TTS discarded: a wordless
# "aah" rompler-choir pad. Rolled-off source, two fixed formants, a
# lowpassed chest layer so the fundamental survives, breath noise riding
# the envelope, slow bloom. Harmonic throughout; hang-answers (a single
# held E5) in THE WAVE only.

F1_BA, F1_AA = signal.iirpeak(650, Q=5, fs=SR)
F2_BA, F2_AA = signal.iirpeak(1080, Q=5, fs=SR)
CHEST_SOS = signal.butter(2, 500, "low", fs=SR, output="sos")
BREATH_SOS = signal.butter(2, [1500, 4000], "bandpass", fs=SR, output="sos")

choir_cache = {}


def choir_voice(midi, dur, attack=0.8):
    key = (midi, round(dur, 2), attack)
    if key in choir_cache:
        return choir_cache[key]
    f = midi_to_hz(midi)
    n = int((dur + 1.4) * SR)
    td = np.arange(n) / SR
    src = np.zeros(n)
    for det in (0.996, 1.0, 1.004):
        drift = 1.0 + 0.04 * np.sin(2 * np.pi * rng.uniform(0.08, 0.14) * td
                                    + rng.uniform(0, 2 * np.pi))
        v = np.zeros(n)
        for k in range(1, min(18, int(4000 / f)) + 1):
            v += np.sin(2 * np.pi * k * f * det * td + rng.uniform(0, 6)) / k ** 1.4
        src += v * drift
    vowel = signal.lfilter(F1_BA, F1_AA, src) + 0.8 * signal.lfilter(F2_BA, F2_AA, src)
    vowel /= np.max(np.abs(vowel)) + 1e-12
    chest = signal.sosfilt(CHEST_SOS, src)
    chest /= np.max(np.abs(chest)) + 1e-12
    x = 0.5 * chest + 0.5 * vowel
    env = np.minimum(0.5 - 0.5 * np.cos(np.pi * np.clip(td / attack, 0, 1)),
                     np.clip((dur + 1.2 - td) / 1.2, 0, 1))
    breath = signal.sosfilt(BREATH_SOS, rng.standard_normal(n))
    breath /= np.max(np.abs(breath)) + 1e-12
    x = (x + 0.08 * breath) * env
    choir_cache[key] = x / (np.max(np.abs(x)) + 1e-12)
    return choir_cache[key]


CHOIR_G = {"v2": 0.5, "b2": 0.55, "ch2": 0.65, "drift": 0.95, "ret": 0.6,
           "dip": 0.6, "wave": 0.7, "ro": 0.5, "out": 0.4}
clear()
for b in range(B_V2, B_TAIL):
    s = section_of(b)
    if s not in CHOIR_G:
        continue
    g = CHOIR_G[s]
    if s == "v2":
        g *= min(1.0, 0.3 + 0.06 * (b - B_V2))       # the sky fades in
    for i, m in enumerate(CHORD_AT[b][2]):
        pan = 0.3 + 0.2 * i
        place_pan(lay_L, lay_R, choir_voice(m, BAR * 1.1), bar_t(b), g, pan)
# the hang-answers: one held E5 blooming at each wave hang (amendment 4)
for b0 in (B_WAVE, B_WAVE + 8, B_WAVE + 16):
    hb = b0 + HANG_BAR
    place_pan(lay_L, lay_R, choir_voice(76, 2.0 * BAR, attack=0.5),
              bar_t(hb, 2), 0.85, 0.5)
    CHOIR_ANSWERS.append(hb)
# the tail: one last C#m breath under the ring
for i, m in enumerate(CsM[2]):
    place_pan(lay_L, lay_R, choir_voice(m, 3.5 * BAR, attack=1.5),
              bar_t(B_TAIL), 0.4, 0.3 + 0.2 * i)
lay_L = reverb(lay_L, IR_L, 0.55)
lay_R = reverb(lay_R, IR_R, 0.55)
commit(lay_L, lay_R, 0.13)
print(f"choir committed ({len(choir_cache)} cached voices)")


# ============================================================= pads
# The string-pad sky floor under the choir — per-bar rearticulation
# (the era string feel), dark, wide, wet.

pad_cache = {}


def pad_chord(voicing, dur, attack, lowpass):
    key = (voicing, round(dur, 1), attack, lowpass)
    if key in pad_cache:
        return pad_cache[key]
    n = int(dur * SR)
    td = np.arange(n) / SR
    L = np.zeros(n)
    R = np.zeros(n)
    for m in voicing:
        f = midi_to_hz(m)
        amp = 0.8 + 0.2 * np.sin(2 * np.pi * rng.uniform(0.02, 0.06) * td + rng.uniform(0, 6))
        for dd, gL, gR in [(1 - 0.0014, 1.0, 0.62), (1 + 0.0014, 0.62, 1.0)]:
            ph = 2 * np.pi * f * dd * td + rng.uniform(0, 6)
            v = (np.sin(ph) + 0.3 * np.sin(2 * ph) + 0.1 * np.sin(3 * ph)) * amp
            L += gL * v
            R += gR * v
    env = np.minimum(np.clip(td / attack, 0, 1) ** 1.3, np.clip((dur - td) / 1.5, 0, 1))
    sos = signal.butter(2, lowpass, "low", fs=SR, output="sos")
    L = signal.sosfilt(sos, L * env)
    R = signal.sosfilt(sos, R * env)
    peak = max(np.max(np.abs(L)), np.max(np.abs(R)), 1e-12)
    pad_cache[key] = (L / peak, R / peak)
    return pad_cache[key]


PAD_G = {"b1": 0.4, "ch1": 0.6, "v2": 0.5, "b2": 0.55, "ch2": 0.65,
         "drift": 0.9, "ret": 0.6, "dip": 0.65, "wave": 0.7, "ro": 0.45}
PAD_LP = {"b1": 900, "ch1": 1000, "v2": 950, "b2": 1000, "ch2": 1050,
          "drift": 1200, "ret": 1050, "dip": 1000, "wave": 1100, "ro": 850}
clear()
for b in range(B_B1, 172):
    s = section_of(b)
    if s not in PAD_G:
        continue
    att = 1.5 if s == "drift" else 0.7
    pL, pR = pad_chord(CHORD_AT[b][1], BAR + 2.0, att, PAD_LP[s])
    add_at(lay_L, pL, bar_t(b), PAD_G[s])
    add_at(lay_R, pR, bar_t(b), PAD_G[s])
lay_L = reverb(lay_L, IR_L, 0.5)
lay_R = reverb(lay_R, IR_R, 0.5)
commit(lay_L, lay_R, 0.13)
print("pads committed")


# ============================================================= warm lead
# THE warmth recipe verbatim (farlight school). This voice exists ONLY
# in the wave — the fusion is earned.

def lead_phrase(notes, lowpass=2600, detune=(0.996, 1.0, 1.004), sub=0.3):
    total = sum(d for _, d in notes) * BEAT
    n = int((total + 2.0) * SR)
    tt = np.arange(n) / SR
    f = glide_curve([(m, d * BEAT) for m, d in notes], n, tau=0.05)
    vibe = 1.0 + 0.003 * np.sin(2 * np.pi * 5.2 * tt) * np.clip(tt / 1.2, 0, 1)
    K = max(3, int(5000 / np.max(f)))
    L = np.zeros(n)
    R = np.zeros(n)
    for j, det in enumerate(detune):
        ph = 2 * np.pi * np.cumsum(f * det * vibe) / SR
        v = np.zeros(n)
        for k in range(1, K + 1):
            v += np.sin(k * ph) / k ** 1.4
        pan = (j / (len(detune) - 1) - 0.5)
        L += v * (0.6 + 0.4 * (0.5 - pan))
        R += v * (0.6 + 0.4 * (0.5 + pan))
    ph0 = 2 * np.pi * np.cumsum(f * vibe) / SR
    body = np.sin(ph0 / 2.0) * sub
    L += body
    R += body
    env = np.minimum(np.clip(tt / 0.10, 0, 1), np.clip((total + 0.5 - tt) / 1.4, 0, 1))
    sos = signal.butter(2, lowpass, "low", fs=SR, output="sos")
    L = signal.sosfilt(sos, L * env)
    R = signal.sosfilt(sos, R * env)
    peak = max(np.max(np.abs(L)), np.max(np.abs(R)), 1e-12)
    return L / peak, R / peak


DELAY = 0.75 * BEAT                                   # the era's dotted-8th

clear()
LEAD_COUNTER = lead_phrase(COUNTER)
for b0, g in [(B_WAVE, 0.8), (B_WAVE + 8, 0.8), (B_WAVE + 16, 0.85)]:
    t0 = bar_t(b0)
    L, R = LEAD_COUNTER
    add_at(lay_L, L, t0, g)
    add_at(lay_R, R, t0, g)
    add_at(lay_L, R, t0 + DELAY, g * 0.26)           # ping-pong echo
    add_at(lay_R, L, t0 + DELAY, g * 0.26)
    COUNTER_SPANS.append((t0, t0 + 32 * BEAT))
lay_L = reverb(lay_L, IR_L, 0.38)
lay_R = reverb(lay_R, IR_R, 0.38)
commit(lay_L, lay_R, 0.15)
print("warm lead committed (the wave only — the fusion)")


# ============================================================= THE SIGNAL
# The X-Files school (notes amendment 2): a soft glide-whistle that
# ECHOES the hang — B5 sliding to F#5, never resolving it — on a long
# dotted-8th ping-pong feedback trail. Once per chorus; the drift call
# is the most distant; one last call in the tail.

def make_signal():
    notes = [(83, 0.75 * BEAT), (78, 2.5 * BEAT)]
    total = sum(d for _, d in notes)
    n = int((total + 0.5) * SR)
    td = np.arange(n) / SR
    f = glide_curve(notes, n, tau=0.08)              # the slide IS the voice
    vibe = 1.0 + 0.006 * np.sin(2 * np.pi * 5.0 * td) * np.clip(td / 0.5, 0, 1)
    ph = 2 * np.pi * np.cumsum(f * vibe) / SR
    x = np.sin(ph) + 0.3 * np.sin(2 * ph)
    breath = signal.sosfilt(BREATH_SOS, rng.standard_normal(n))
    breath /= np.max(np.abs(breath)) + 1e-12
    x += 0.05 * breath
    x *= np.minimum(0.5 - 0.5 * np.cos(np.pi * np.clip(td / 0.15, 0, 1)),
                    np.clip((total + 0.2 - td) / 0.6, 0, 1))
    return x / (np.max(np.abs(x)) + 1e-12)


SIGNAL = make_signal()
D_SIG = int(0.75 * BEAT * SR) / SR                   # dotted-8th, seconds

clear()
for b, g, sec in [(B_CH1 + 8 + HANG_BAR, 0.6, "ch1"),
                  (B_CH2 + 8 + HANG_BAR, 0.65, "ch2"),
                  (B_DRIFT + 8 + HANG_BAR, 0.8, "drift"),
                  (B_WAVE + 8 + HANG_BAR, 0.7, "wave"),
                  (B_TAIL + 1, 0.55, "tail")]:
    t0 = bar_t(b, 3)
    for i in range(7):                               # the long feedback trail
        pan = 0.32 if i % 2 else 0.68
        place_pan(lay_L, lay_R, SIGNAL, t0 + i * D_SIG, g * 0.55 ** i, pan)
    SIGNAL_EVENTS.append((b, sec))
lay_L = reverb(lay_L, IR_L, 0.5)
lay_R = reverb(lay_R, IR_R, 0.5)
commit(lay_L, lay_R, 0.07)
print("the signal committed (5 calls, dotted-8th feedback trail)")


# ============================================================= textures
# Cloud swells — symmetric bandlimited washes (300-1800 Hz), the clouds
# passing; never a riser, never white-noise wash. Air shimmer — three
# diatonic high sines (G#6 C#7 E7) with slow AM and pan, felt not heard.

clear()


def cloud(b0, nbars, gain):
    n = int(nbars * BAR * SR)
    prog = np.arange(n) / n
    x = signal.sosfilt(signal.butter(2, [300, 1800], "bandpass", fs=SR, output="sos"),
                       rng.standard_normal(n))
    x *= np.sin(np.pi * prog) ** 2                   # symmetric: it passes by
    x /= np.max(np.abs(x)) + 1e-12
    p0, p1 = (0.3, 0.7) if rng.random() < 0.5 else (0.7, 0.3)
    pan = p0 + (p1 - p0) * prog
    add_at(lay_L, x * np.cos(pan * np.pi / 2), bar_t(b0), gain)
    add_at(lay_R, x * np.sin(pan * np.pi / 2), bar_t(b0), gain)


cloud(2, 4, 0.9)                                     # the thesis cloud
cloud(B_DRIFT + 2, 6, 1.0)
cloud(B_DRIFT + 11, 6, 0.9)
cloud(B_RO + 4, 4, 0.6)
cloud(B_OUT + 2, 6, 0.8)
cloud(B_TAIL, 5, 0.7)
commit(lay_L, lay_R, 0.045)
print("cloud swells committed")

clear()
SHIMMER_SPANS = [(0, B_INTRO), (B_DRIFT, B_RET), (B_OUT, B_END)]
for b0, b1 in SHIMMER_SPANS:
    n = int((b1 - b0) * BAR * SR)
    td = np.arange(n) / SR
    for m in (92, 97, 100):                          # G#6 C#7 E7 — diatonic air
        am = 0.5 + 0.5 * np.sin(2 * np.pi * rng.uniform(0.03, 0.07) * td
                                + rng.uniform(0, 6))
        pan = 0.5 + 0.3 * np.sin(2 * np.pi * rng.uniform(0.02, 0.05) * td
                                 + rng.uniform(0, 6))
        v = np.sin(2 * np.pi * midi_to_hz(m) * td) * am
        edge = np.minimum(np.clip(td / 2.0, 0, 1), np.clip((n / SR - td) / 2.0, 0, 1))
        add_at(lay_L, v * edge * np.cos(pan * np.pi / 2), bar_t(b0), 1.0)
        add_at(lay_R, v * edge * np.sin(pan * np.pi / 2), bar_t(b0), 1.0)
commit(lay_L, lay_R, 0.02)
print("air shimmer committed")

# dark swells — the sanctioned build riser (bandlimited, crash-resolved)
clear()


def swell(b0, b1, gain=1.0):
    t0, t1 = bar_t(b0), bar_t(b1)
    n = int((t1 - t0) * SR)
    prog = np.arange(n) / n
    noise = rng.standard_normal(n)
    out = np.zeros(n)
    for k in range(5):
        c = 250 * (2400 / 250) ** (k / 4)
        win = np.clip(1 - np.abs(prog - np.log(c / 250) / np.log(2400 / 250)) * 4, 0, 1)
        out += signal.sosfilt(signal.butter(2, [c * 0.8, c * 1.25], "bandpass",
                                            fs=SR, output="sos"), noise) * win
    out *= prog ** 2
    out /= np.max(np.abs(out)) + 1e-12
    add_at(lay_L, out, t0, gain)
    add_at(lay_R, out, t0, gain * 0.96)


swell(B_B1 + 4, B_CH1, 0.6)
swell(B_B2 + 4, B_CH2, 0.8)
swell(B_WAVE - 2, B_WAVE, 0.5)
commit(lay_L, lay_R, 0.05)
print("dark swells committed")


# ---------------------------------------------------------------- master

fade(mix_L, fade_in=0.05, fade_out=7.0)
fade(mix_R, fade_in=0.05, fade_out=7.0)

for ch in (mix_L, mix_R):
    ch += 0.26 * signal.sosfilt(signal.butter(2, 95, "low", fs=SR, output="sos"), ch)
    ch += 0.10 * signal.sosfilt(signal.butter(2, 9000, "high", fs=SR, output="sos"), ch)

peak = max(np.max(np.abs(mix_L)), np.max(np.abs(mix_R))) + 1e-12
mix_L = np.tanh(1.3 * mix_L / peak) / np.tanh(1.3) * 0.88
mix_R = np.tanh(1.3 * mix_R / peak) / np.tanh(1.3) * 0.88

stereo = np.empty((N, 2))
stereo[:, 0] = mix_L
stereo[:, 1] = mix_R
pcm = (stereo * 32767.0).astype(np.int16)

OUT_DIR = pathlib.Path("/workspace/music")
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT = OUT_DIR / "adrift.wav"
with wave.open(str(OUT), "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())

print(f"\nCreated: {OUT}")
print(f"Duration: {N / SR:.1f} s  |  {SR} Hz stereo, 16-bit PCM  |  "
      f"{BPM:.0f} BPM, C# natural minor, C#m-A-E-B / ...-B-C#m")

MP3 = OUT_DIR / "adrift.mp3"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(OUT),
                "-vn", "-ar", "44100", "-ac", "2", "-b:a", "192k", str(MP3)],
               check=True)
print(f"Created: {MP3}  (192k mp3)")

# ---------------------------------------------------------------- verify form

NAMES = {"thesis": "thesis (solo piano)", "intro": "intro", "v1": "verse 1",
         "b1": "build 1", "ch1": "CHORUS 1", "v2": "verse 2 (choir in)",
         "b2": "build 2", "ch2": "CHORUS 2", "drift": "THE DRIFT",
         "ret": "THE RETURN", "dip": "dip", "wave": "THE WAVE",
         "ro": "ride-out", "out": "outro", "tail": "tail"}
print("\nSection map:")
for name, b in SECS:
    print(f"  {bar_t(b):6.1f} s  bar {b:3d}  {NAMES[name]}")
print(f"  {bar_t(B_KSTOP):6.1f} s  bar {B_KSTOP}  the kick stops")
print(f"  {bar_t(B_BOOK):6.1f} s  bar {B_BOOK}  the bookend statement")
print(f"  {DURATION:6.1f} s  end")

STATEMENTS.sort(key=lambda s: s[0])
counted = [s for s in STATEMENTS if s[2]]
print("\nRefrain statements (identical melody, all instruments = the piano):")
for b, label, cnt in STATEMENTS:
    print(f"  bar {b:3d}  {label}")
print(f"  counted: {len(counted)} (target >= 12)")

# the unbroken drift: max piano onset gap, chorus 2 -> end of the return
onsets = sorted(t0 for t0, _ in PIANO_EVENTS
                if bar_t(B_CH2) - 1e-6 <= t0 < bar_t(B_DIP))
gaps = np.diff(onsets)
max_gap = float(np.max(gaps)) if len(gaps) else 0.0
print(f"\nThe unbroken drift: max piano onset gap bar {B_CH2}..{B_DIP} = "
      f"{max_gap:.2f} s ({max_gap / BAR:.2f} bars; limit < 1 bar)")

ret_offset = B_RET - STRADDLE_B0
print(f"The mid-phrase return: statement @{STRADDLE_B0}, kick lands @{B_RET} "
      f"-> bar {ret_offset + 1} of 8 (offset {ret_offset}; required 4)")

print("\nThe signal (X-Files school; long dotted-8th feedback trail):")
for b, sec in SIGNAL_EVENTS:
    print(f"  bar {b:3d}  ({sec})")
sig_secs = [sec for _, sec in SIGNAL_EVENTS]
sig_first_ok = min(b for b, _ in SIGNAL_EVENTS) >= B_CH1

print("\nChoir discipline: pad from verse 2; melodic answers in the wave only:")
for b in CHOIR_ANSWERS:
    print(f"  bar {b:3d}  held E5 answers the hang")
choir_ans_ok = all(B_WAVE <= b < B_RO for b in CHOIR_ANSWERS)


def span_overlap(spans_a, spans_b):
    tot = sum(b - a for a, b in spans_a)
    ov = 0.0
    for a0, a1 in spans_a:
        for b0, b1 in spans_b:
            ov += max(0.0, min(a1, b1) - max(a0, b0))
    return ov / (tot + 1e-12)


CH1_SPANS = [(bar_t(B_CH1), bar_t(B_CH1 + 16))]
CH2_SPANS = [(bar_t(B_CH2), bar_t(B_CH2 + 16))]
WAVE_SPANS = [(bar_t(B_WAVE), bar_t(B_WAVE + 24))]
ov1 = span_overlap(CH1_SPANS, COUNTER_SPANS)
ov2 = span_overlap(CH2_SPANS, COUNTER_SPANS)
ovw = span_overlap(WAVE_SPANS, COUNTER_SPANS)
print(f"\nDuet overlap (refrain vs warm-lead counter): "
      f"ch1 {ov1:.2f}  ch2 {ov2:.2f}  wave {ovw:.2f}")

print("\nThe dirt knobs (warm dial, per the review):")
print(f"  piano: ZOH effective rate {SR // ZOH_FACTOR} Hz, wow +/-{WOW_DEPTH * 100:.2f}% "
      f"@ {WOW_HZ} Hz, drive tanh(0.9), lowpass 7500 Hz")
print("  bass smear: tanh(2.2) -> bandpass 80-700 Hz -> 35 ms diffusion burst, mix 0.25")
max_bass_onsets = max(BASS_ONSETS.values())
print(f"  bass onsets per bar: max {max_bass_onsets} (the retired roller was 12-16)")

print("\nSeam checklist (what crosses every boundary):")
for b, dev in [(B_INTRO, "kick enters on the thesis statement's final ring"),
               (B_V1, "unbroken groove; arp already faded up; open hat @32"),
               (B_B1, "unbroken groove; pads swell in; roll + dark swell inside"),
               (B_CH1, "roll crest -> crash; the refrain lands"),
               (B_V2, "chorus chord rings; claps enter; the choir fades in"),
               (B_B2, "unbroken groove; longer roll + swell; bar 87 drum dropout"),
               (B_CH2, "roll through the dropout -> crash; choir sky holds"),
               (B_DRIFT, "soft crash; kick+bass exit UNDER the ringing chord; "
                         "the piano does not stop (checked)"),
               (B_RET, "the kick lands on bar 5 of the running statement; "
                       "eased sub bloom (no roll — the surprise is the seam)"),
               (B_DIP, "statement completes into circling fragments; claps/ride/sub out"),
               (B_WAVE, "short roll + swell -> crash; lead + choir answers join"),
               (B_RO, "soft crash; lead/ride/sub out; the tune dissolves to fragments"),
               (B_OUT, "claps then arp then pads have peeled; kick fades toward @184"),
               (B_TAIL, "the bookend's home chord rings; choir breath + one C#5")]:
    print(f"  bar {b:3d} ({bar_t(b):5.1f} s): {dev}")


def rms_between(b0, b1):
    i0 = int(bar_t(b0) * SR)
    i1 = int(bar_t(b1) * SR) if b1 is not None else N
    return np.sqrt(np.mean(mix_L[i0:i1] ** 2 + mix_R[i0:i1] ** 2) / 2)


print("\nPer-section RMS:")
R = {}
for (name, b0), (_, b1) in zip(SECS, SECS[1:] + [("end", None)]):
    R[name] = rms_between(b0, b1)
    print(f"  {NAMES[name]:24s} {R[name]:.3f}")

print("\nBanned-list audit (by construction):")
print("  the rolling 16th bass RETIRED: 8th octave-bounce, max "
      f"{max_bass_onsets} onsets/bar, no filter resonance anywhere")
print("  no acid, no sidechain pump, no supersaw (3-voice detune only)")
print("  no white-noise wash: swells bandlimited 250-2400, clouds 300-1800")
print("  no reverse cymbal (nachtkind's); no toms (ungeschrieben's)")
print("  no trance gate (penumbra's); no bell (farlight's)")
print("  no literal SFX: the ocean is the tide form, the clouds are swells")

# diatonic audit — every pitched voice
CSM_PCS = {1, 3, 4, 6, 8, 9, 11}
all_pcs = set()
for seq in (REFRAIN, VERSE_Q, VERSE_A, COUNTER):
    all_pcs |= {m % 12 for m, _ in seq}
for _, pad_v, choir_v, arp_v in (CsM, A_, E_, B_):
    all_pcs |= {m % 12 for m in pad_v} | {m % 12 for m in choir_v} \
               | {m % 12 for m in arp_v}
for root, *_ in (CsM, A_, E_, B_):
    all_pcs |= {root % 12, (root + 7) % 12, APPROACH[root] % 12}
all_pcs |= {83 % 12, 78 % 12, 76 % 12, 25 % 12, 92 % 12, 97 % 12, 100 % 12}
for d in LH_DYAD.values():
    all_pcs |= {m % 12 for m in d}

checks = [
    ("opening ascends: thesis < v1 < ch1", R["thesis"] < R["v1"] < R["ch1"]),
    ("chorus 1 > build 1", R["ch1"] > R["b1"]),
    ("chorus 2 >= chorus 1", R["ch2"] >= R["ch1"]),
    ("chorus 2 > build 2", R["ch2"] > R["b2"]),
    ("THE DRIFT is the trough",
     R["drift"] < min(R["ch2"], R["ret"], R["wave"])),
    ("THE RETURN > THE DRIFT (the tide comes back)", R["ret"] > R["drift"]),
    ("the dip dips", R["dip"] < min(R["ret"], R["wave"])),
    ("THE WAVE is the loudest section", R["wave"] == max(R.values())),
    ("ride-out descends: wave > ro > out", R["wave"] > R["ro"] > R["out"]),
    ("the outro settles near the intro", 0.4 < R["out"] / R["intro"] < 1.6),
    ("the tail falls below the outro", R["tail"] < R["out"]),
    ("counted statements >= 12", len(counted) >= 12),
    ("the unbroken drift: max piano gap < 1 bar (ch2 -> return end)",
     max_gap < BAR),
    ("the mid-phrase return: kick lands on bar 5 of 8", ret_offset == 4),
    ("hang is the b7, home is the tonic",
     HANG_MIDI % 12 == 11 and REFRAIN[-1][0] % 12 == 1),
    ("Q/A rhyme: bar 6 identical to bar 2",
     BAR_NOTES[5] == BAR_NOTES[1]),
    ("signal: 5 calls, one per chorus + drift + tail, none before ch1",
     sig_secs == ["ch1", "ch2", "drift", "wave", "tail"] and sig_first_ok),
    ("choir: answers only in the wave, x3",
     choir_ans_ok and len(CHOIR_ANSWERS) == 3),
    ("duet overlap: ~0 before the wave, earned in it",
     ov1 < 0.05 and ov2 < 0.05 and ovw >= 0.5),
    ("bass never the roller: <= 8 onsets per bar", max_bass_onsets <= 8),
    ("everything C#-natural-minor diatonic", all_pcs <= CSM_PCS),
]
print("\nForm checks:")
ok = True
for name, passed in checks:
    print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
    ok &= passed
print("all checks passed" if ok else "SOME CHECKS FAILED")
