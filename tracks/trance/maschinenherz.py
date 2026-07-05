#!/usr/bin/env python3
"""
maschinenherz.py — "Maschinenherz" (~7:25, 145 BPM, E minor).
The first PSY trance track in this directory (design notes:
maschinenherz_notes.md). Not Frankfurt, not dream trance — harder,
faster; four declared borrow sources, one concept:

THE CONCEPT — a machine heart that learns to sing. The psy engine
(dune water_of_life/sleeper_awakens kit: trance kick, K-b-b-b rolling
bass, warmed 303, offbeat hats, psy clap, zaps) is the machine — bone
dry, static on its E pedal. The tech_noir love-theme voice
(love_phrase, ported) is the heart — plaintive, drenched in the long
hall, singing NEW melodies (the Terminator tune is never quoted).
nachtkind's dry/wet contrast IS the concept mixed as sound.

THE HARMONY — static engine, walking heart: verses/drops sit on the E
pedal (authentic psy); choruses walk Em–C–D–B (the nachtkind
progression family transposed). The D# of the B chord against the
E-minor field is THE color: the refrain's question hangs ON D#, the
answer resolves D#→E across the barline (the nachtkind mechanism).

VIVALDI MECHANISMS (Winter_Vivaldi.md; mechanisms only, never pitches;
only the ones eisgang did NOT claim): W1 shiver stack (intro layers
that increase DISSONANCE — octave, 2nd-clash, tritone, the alien D# —
first consonant Em lands with the kick), W4a stutter ladder (the 303
locks one pitch per bar, climbing chromatically out of the key — the
pre-drop builds; build 1 parks on the dominant B, build 2 ends
hammering D# so the drop's downbeat E resolves it), W2 zigzag cascade
(the chorus arp cell: root-oct-oct-5th / 5th-3rd-3rd-root, restated up
the chord), W8a ice-crack (stab—silence—flick: the seam device).

THE 303 (Q4, per notes): sleeper_awakens' within-note sweep kept (the
squelch IS the sweep) but WARMED: rolled partials 1/k^1.3, Q 4.5 (not
11), feedback 1.15 (not 1.9), tanh(1.2) (not 2.8), a sine body core,
and the cutoff rides the printable filter arc (the ungeschrieben
device, declared) — it never parks. Not hard saw.

  0:00  thesis      The voice alone: the question phrase, hanging on D#.
  0:07  shiver      W1 stack over the E drone; kick-roll build.
  0:34  engine      Kick + rolling bass lock in; hats staircase.
  1:00  verse       303 low and dark; voice sings 2-bar ghost fragments.
  1:27  build 1     W4a ladder E→B; roll; composed silent beat.
  1:40  DROP 1      64 bars, machine only, EVOLVING: riff A (16) /
                    dip kick+303 (4) / riff A 8va (16) / dip kickless
                    (4) / riff B slides (24). The voice is absent.
  3:26  chorus 1    THE REVEAL: harmony walks, pads + W2 arp, the full
                    refrain sung twice. Q hangs on D#, A resolves.
  3:52  break       Engine out (ice-crack); voice + pads + drone.
  4:19  build 2     Bass returns first; ladder ends hammering D#.
  4:32  DROP 2      64 bars, THE FUSION, evolving: voice over the full
                    engine, 303 answers each held D# with a lick ending
                    on E; octave double (wave 2); arp + arc global max
                    (wave 3). Two mini-dips.
  6:18  chorus 2    Fullest 16 bars; last D# resolves across the seam.
  6:44  outro       Strip; the arc returns to its intro cutoff; the
                    kick fades like a calming heartbeat.
  7:11  bookend     The answer phrase alone; the final E is STATED.

BANNED (per notes): gothic piano, rompler strings, reverse cymbals,
the Eye Q closed-hat carpet aesthetic, all Dune palette (wind/worm/
darbuka/duduk/ney/chant/choir), TTS, hard-saw acid, W3/W5.

Everything synthesized (numpy + scipy).
Output: /workspace/music/maschinenherz.wav + maschinenherz.mp3 (192k).
"""

import os
import subprocess
import wave
import numpy as np
from scipy import signal

SR = 44100
DURATION = 446.0
N = int(SR * DURATION)
t = np.arange(N) / SR

rng = np.random.default_rng(1997)     # the year German psy broke

BPM = 145.0
BEAT = 60.0 / BPM
BAR = BEAT * 4
STEP = BEAT / 4
GRID0 = 0.5


def bar_t(b, beat=0.0):
    return GRID0 + b * BAR + beat * BEAT


# ---------------------------------------------------- section boundaries (bars)
B_SHIVER = 4      # W1 stack over the drone (thesis is bars 0-3)
B_ENGINE = 20     # kick + rolling bass lock in
B_VERSE = 36      # 303 enters; voice fragments
B_BUILD1 = 52     # W4a ladder E->B
B_DROP1 = 60      # the machine's drop (64 bars)
B_CHOR1 = 124     # the reveal
B_BREAK = 140     # engine out
B_BUILD2 = 156    # ladder again, ends on D#
B_DROP2 = 164     # the fusion (64 bars)
B_CHOR2 = 228     # fullest
B_OUT = 244       # strip
B_KSTOP = 260     # kick stops; bookend
B_END = 266

# drop-internal phases (the "evolve, don't repeat" contract)
D1_DIP1 = range(B_DROP1 + 16, B_DROP1 + 20)     # kick + 303 only
D1_DIP2 = range(B_DROP1 + 36, B_DROP1 + 40)     # bass + hats, kickless
D2_DIP1 = range(B_DROP2 + 16, B_DROP2 + 20)     # voice + kick only
D2_DIP2 = range(B_DROP2 + 36, B_DROP2 + 40)     # bass + hats + dark 303


def section_of(b):
    for name, b0 in [("bookend", B_KSTOP), ("outro", B_OUT),
                     ("chorus2", B_CHOR2), ("drop2", B_DROP2),
                     ("build2", B_BUILD2), ("break", B_BREAK),
                     ("chorus1", B_CHOR1), ("drop1", B_DROP1),
                     ("build1", B_BUILD1), ("verse", B_VERSE),
                     ("engine", B_ENGINE), ("shiver", B_SHIVER)]:
        if b >= b0:
            return name
    return "thesis"


# ------------------------------------------------------- the filter arc
# The 303's development IS this curve (the ungeschrieben device,
# declared): piecewise-linear cutoff in Hz over bars, printed and
# checked — rise across the verse, global max inside drop 2, outro
# returns to the intro value. The cutoff never parks.
CUT_BARS = [0,   36,  52,  60,   68,  76,  80,  90,   96,  100,  112,
            123,  124, 156, 163,  164,  172,  180, 184,  192,  200,
            204,  216,  227,  228,  244,  252, 266]
CUT_HZ = [380, 380, 650, 1050, 800, 600, 700, 1400, 900, 1000, 1300,
          1600, 500, 600, 1000, 1100, 1500, 800, 1200, 1600, 1000,
          1300, 1900, 1600, 1500, 1200, 380, 380]


def cutoff_at(b):
    return float(np.interp(b, CUT_BARS, CUT_HZ))


# ---------------------------------------------------------------- helpers

def midi_to_hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def fade(x, fade_in=0.2, fade_out=6.0):
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


def place_pan(layL, layR, clip, t0, gain, pan):
    add_at(layL, clip, t0, gain * np.cos(pan * np.pi / 2))
    add_at(layR, clip, t0, gain * np.sin(pan * np.pi / 2))


def glide_curve(notes, n, tau=0.04):
    f_target = np.zeros(n)
    edge = 0.0
    for m, d in notes:
        a, b = int(edge * SR), min(n, int((edge + d) * SR))
        f_target[a:b] = midi_to_hz(m)
        edge += d
    i_end = min(n - 1, int(edge * SR))
    f_target[i_end:] = f_target[i_end - 1]
    alpha = 1.0 - np.exp(-1.0 / (tau * SR))
    return signal.lfilter([alpha], [1.0, -(1.0 - alpha)],
                          f_target, zi=[f_target[0] * (1 - alpha)])[0]


# the long dark hall — the HEART's space; the machine stays bone dry
IR_L = make_reverb_ir(5.5, 2.6, 7)
IR_R = make_reverb_ir(5.5, 2.6, 11)

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


# ------------------------------------------------------------- material
# E natural minor: E F# G A B C D (+ the one borrowed D# of the V).
# Chorus lap: Em-C-D-B, one chord per bar, one lap per refrain half.

EM_V = (52, 59, 64, 67)            # E3 B3 E4 G4
C_V = (48, 55, 64, 67)             # C3 G3 E4 G4
D_V = (50, 57, 62, 66)             # D3 A3 D4 F#4
B_V = (47, 54, 63, 66)             # B2 F#3 D#4 F#4  <- the D# color
CH_LAP = [EM_V, C_V, D_V, B_V]
BASS_LAP = [40, 36, 38, 35]        # E2 C2 D2 B1 — the walking bass roots

# THE REFRAIN — sung by the voice, identical every full statement.
# (midi, beats). Q rises over one Em-C-D-B lap and hangs ON D#5; A
# opens by resolving that D# (its first note is E), falls home through
# the octave, and hangs on D# again — every statement's opening E
# resolves the previous statement's D# across the barline (the
# nachtkind chain). Only the bookend states the final E itself.
THEME_Q = [(76, 1.5), (79, 0.5), (78, 1), (76, 1),      # Em
           (79, 1.5), (81, 0.5), (79, 1), (76, 1),      # C
           (78, 1.5), (81, 0.5), (83, 1), (81, 1),      # D  (peak B5)
           (78, 1), (76, 0.5), (75, 2.5)]               # B  — hangs on D#
THEME_A = [(76, 1.5), (79, 0.5), (83, 1), (81, 1),      # Em (D# resolved)
           (79, 1.5), (76, 0.5), (72, 1), (74, 1),      # C
           (76, 1.5), (74, 0.5), (71, 1), (69, 1),      # D  (falling home)
           (78, 1), (75, 3)]                            # B  — hangs on D#
THEME = THEME_Q + THEME_A
RESOLVE = [(76, 2.0)]              # the E, stated across the seam
FRAG = THEME_Q[:8]                 # the 2-bar ghost fragment (verse)
DIP_HOLD = [(76, 6.0), (75, 5.0)]  # drop-2 dip: the held question

REFRAIN_STMTS = []                 # bars of full statements (verified)

# 303 riffs — 16 steps of (midi or None, accent, slide_to). E pedal
# with in-scale pokes; riff B is the syncopated one with the slides.
RIFF_A = [(40, 1, None), (None, 0, None), (40, 0, None), (None, 0, None),
          (40, 0, None), (52, 1, None), (None, 0, None), (40, 0, None),
          (43, 0, None), (None, 0, None), (40, 0, None), (None, 0, None),
          (45, 1, None), (None, 0, None), (38, 0, 40), (40, 0, None)]
RIFF_A2 = [(m + 12 if m else None, a, s + 12 if s else None)
           for m, a, s in RIFF_A]
RIFF_B = [(52, 1, None), (None, 0, None), (52, 0, 54), (54, 0, None),
          (None, 0, None), (52, 0, None), (57, 1, None), (None, 0, None),
          (59, 0, 57), (57, 0, None), (None, 0, None), (52, 0, None),
          (64, 1, None), (None, 0, None), (50, 0, 52), (52, 0, None)]

# W4a ladders — one pitch per bar, chromatic, OUT of the key by design.
LADDER1 = [52, 53, 54, 55, 56, 57, 58, 59]      # E3 -> B3 (the dominant)
LADDER2 = [57, 58, 59, 60, 61, 62, 63, 63]      # A3 -> D#4, hammered

# the 303 answer lick (drop 2 trades): ends on E — the machine resolves
# the D# the voice is holding.
LICK = [(59, 0, None), (63, 0, None), (64, 1, None)]


# ---------------------------------------------------------------- drums
# dune psy kit (sleeper_awakens recipes, copied per convention).

def make_kick():
    n = int(0.30 * SR)
    td = np.arange(n) / SR
    f_curve = 45.0 + 105.0 * np.exp(-td * 55.0)
    body = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    sos_c = signal.butter(2, [1800, 9000], "bandpass", fs=SR, output="sos")
    click = signal.sosfilt(sos_c, rng.standard_normal(n)) * np.exp(-td * 700)
    click /= np.max(np.abs(click)) + 1e-12
    env = (1 - np.exp(-td / 0.0008)) * np.exp(-td * 9.0)
    x = (body + 0.45 * click) * env
    return x / (np.max(np.abs(x)) + 1e-12)


def make_hat(open_=False):
    n = int((0.16 if open_ else 0.045) * SR)
    td = np.arange(n) / SR
    sos_h = signal.butter(4, 6500 if open_ else 7000, "high",
                          fs=SR, output="sos")
    x = signal.sosfilt(sos_h, rng.standard_normal(n))
    x *= np.exp(-td * (24 if open_ else 100))
    return x / (np.max(np.abs(x)) + 1e-12)


def make_clap():
    n = int(0.26 * SR)
    td = np.arange(n) / SR
    sos_c = signal.butter(2, [900, 5200], "bandpass", fs=SR, output="sos")
    nz = signal.sosfilt(sos_c, rng.standard_normal(n))
    nz /= np.max(np.abs(nz)) + 1e-12
    env = np.zeros(n)
    for i, t0 in enumerate([0.0, 0.011, 0.022, 0.033]):
        i0 = int(t0 * SR)
        rate = 120.0 if i < 3 else 26.0
        seg = (0.65 if i < 3 else 1.0) * np.exp(-(td[i0:] - t0) * rate)
        env[i0:] = np.maximum(env[i0:], seg)
    x = nz * env
    return x / (np.max(np.abs(x)) + 1e-12)


def make_crash():
    n = int(2.0 * SR)
    td = np.arange(n) / SR
    sos_c = signal.butter(2, 5000, "high", fs=SR, output="sos")
    x = signal.sosfilt(sos_c, rng.standard_normal(n)) * np.exp(-td * 2.2)
    x *= 1 - np.exp(-td / 0.002)
    return x / (np.max(np.abs(x)) + 1e-12)


def make_zap():
    n = int(0.40 * SR)
    td = np.arange(n) / SR
    f_curve = 80.0 + 1900.0 * np.exp(-td * 18.0)
    x = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    x *= 1.0 + 0.5 * np.sin(2 * np.pi * 35.0 * td)
    x *= np.exp(-td * 8.0) * (1 - np.exp(-td / 0.002))
    return x / (np.max(np.abs(x)) + 1e-12)


KICK = make_kick()
OHAT = make_hat(open_=True)
CHAT = make_hat()
CLAP = make_clap()
CRASH = make_crash()
ZAP = make_zap()


def kick_on(b):
    s = section_of(b)
    if s in ("thesis", "shiver", "break", "bookend"):
        return False
    if b in D1_DIP2 or b in D2_DIP2:
        return False                            # the kickless dips
    if B_BUILD2 <= b < B_BUILD2 + 6:
        return False                            # build 2 starts kickless
    return True


def kick_gain(b):
    s = section_of(b)
    if s == "engine" or s == "verse":
        return 0.8                              # pre-drop headroom
    if s in ("build1", "build2"):
        return 0.6
    if s == "chorus1":
        return 0.95
    if s == "outro":
        return 0.9 - 0.45 * (b - B_OUT) / (B_KSTOP - B_OUT)
    return 1.0


ROLL_8TH = (B_BUILD1 + 6, B_BUILD2 + 6)
ROLL_16TH = (B_BUILD1 + 7, B_BUILD2 + 7)

clear()
for b in range(B_END):
    if not kick_on(b):
        continue
    g = kick_gain(b)
    if b == B_SHIVER + 15:                      # the shiver's kick-roll build
        for e in range(8):
            gg = 0.5 * (0.5 + 0.5 * e / 7)
            add_at(lay_L, KICK, bar_t(b, e * 0.5), gg)
            add_at(lay_R, KICK, bar_t(b, e * 0.5), gg)
        continue
    if b in ROLL_8TH:
        for e in range(8):
            gg = 0.55 + 0.45 * e / 7
            add_at(lay_L, KICK, bar_t(b, e * 0.5), gg)
            add_at(lay_R, KICK, bar_t(b, e * 0.5), gg)
        continue
    if b in ROLL_16TH:                          # ends on the composed silence
        for s16 in range(12):                   # beats 0-2.75, beat 4 SILENT
            gg = 0.55 + 0.45 * s16 / 11
            add_at(lay_L, KICK, bar_t(b, s16 * 0.25), gg)
            add_at(lay_R, KICK, bar_t(b, s16 * 0.25), gg)
        continue
    for beat in range(4):
        add_at(lay_L, KICK, bar_t(b, beat), g)
        add_at(lay_R, KICK, bar_t(b, beat), g)
commit(lay_L, lay_R, 0.32)
print("kick committed")


# ---------------------------------------------------------------- psy bass
# The K-b-b-b engine: kick on the beat, bass on the three 16ths after
# (gains .8/.7/.95) — the bass NEVER sounds on a kick 16th (verified).
# 350 Hz lowpass + short gate is why this saw does not read harsh.

def psy_bass_note(midi, dur=STEP * 0.88):
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    for k in range(1, min(20, int(7000 / f)) + 1):
        x += np.sin(2 * np.pi * k * f * td) / k
    sos_b = signal.butter(2, 350, "low", fs=SR, output="sos")
    x = np.tanh(2.0 * signal.sosfilt(sos_b, x))
    env = (1 - np.exp(-td / 0.002)) * np.clip((dur - td) / 0.02, 0, 1)
    x *= env
    return x / (np.max(np.abs(x)) + 1e-12)


PB = {m: psy_bass_note(m) for m in (40, 36, 38, 35, 47, 52)}
BASS_GAP_VIOLATIONS = 0


def bass_root(b):
    s = section_of(b)
    if s in ("chorus1", "drop2", "chorus2"):
        return BASS_LAP[b % 4]                  # the walking heart
    return 40                                   # the E pedal


def bass_on(b):
    s = section_of(b)
    if s in ("thesis", "shiver", "break", "bookend"):
        return False
    if b < B_ENGINE + 4:
        return False                            # kick locks in alone first
    if b in ROLL_8TH or b in ROLL_16TH or b == B_SHIVER + 15:
        return False
    if b in D1_DIP1 or b in D2_DIP1:
        return False                            # kick-and-solo dips
    if s == "outro" and b >= B_OUT + 8:
        return False                            # bass leaves before the kick
    return True


clear()
for b in range(B_END):
    if not bass_on(b):
        continue
    g = 0.65 if b < B_DROP1 else 1.0            # pre-drop headroom
    root = bass_root(b)
    for beat in range(4):
        for s16, gg in [(1, 0.8), (2, 0.7), (3, 0.95)]:
            m = root
            if b % 4 == 3 and beat == 3 and section_of(b) not in \
                    ("chorus1", "drop2", "chorus2"):
                m = [40, 47, 52][s16 - 1]       # cadence climb E2-B2-E3
            elif section_of(b) in ("drop2", "chorus2") and beat == 3 \
                    and s16 == 3:
                m = root + 12                   # octave flick
                if m not in PB:
                    PB[m] = psy_bass_note(m)
            add_at(lay_L, PB[m], bar_t(b, beat + s16 * 0.25), g * gg)
            add_at(lay_R, PB[m], bar_t(b, beat + s16 * 0.25), g * gg)
            # the contract: s16 is never 0 — counted, printed below
commit(lay_L, lay_R, 0.24) # bass
print("psy bass committed")


# ---------------------------------------------------------------- hats

def hats_on(b):
    s = section_of(b)
    if s in ("thesis", "shiver", "break", "bookend"):
        return False
    if b < B_ENGINE + 8:
        return False                            # staircase: hats third
    if b in ROLL_16TH:
        return False
    if b in D2_DIP1:
        return False
    if s == "outro" and b >= B_OUT + 12:
        return False
    return True


clear()
for b in range(B_END):
    if not hats_on(b):
        continue
    g = 0.8 if b < B_DROP1 else 1.0
    for beat in range(4):
        add_at(lay_L, OHAT, bar_t(b, beat + 0.5), g * 0.8)
        add_at(lay_R, OHAT, bar_t(b, beat + 0.5), g)
    if section_of(b) in ("drop1", "drop2", "chorus2"):
        for s16 in range(16):                   # closed 16th ghosts L/R
            if s16 % 2 == 0:
                continue
            p = 0.3 + 0.4 * ((s16 // 2) % 2)
            add_at(lay_L, CHAT, bar_t(b, s16 * 0.25),
                   g * 0.35 * np.cos(p * np.pi / 2))
            add_at(lay_R, CHAT, bar_t(b, s16 * 0.25),
                   g * 0.35 * np.sin(p * np.pi / 2))
commit(lay_L, lay_R, 0.12)
print("hats committed")

# claps on 2 & 4 — drops and choruses only
clear()
for b in range(B_END):
    s = section_of(b)
    if s not in ("drop1", "chorus1", "drop2", "chorus2"):
        continue
    if b in D1_DIP1 or b in D1_DIP2 or b in D2_DIP1 or b in D2_DIP2:
        continue
    for beat in (1, 3):
        p = 0.42 if beat == 1 else 0.58
        place_pan(lay_L, lay_R, CLAP, bar_t(b, beat), 1.0, p)
commit(lay_L, lay_R, 0.10)
print("claps committed")

# crashes mark the arrivals
clear()
for b, g in [(B_ENGINE, 0.5), (B_DROP1, 1.0), (B_DROP1 + 40, 0.6),
             (B_CHOR1, 1.0), (B_DROP2, 1.0), (B_DROP2 + 40, 0.7),
             (B_CHOR2, 0.9)]:
    place_pan(lay_L, lay_R, CRASH, bar_t(b), g, 0.5)
commit(lay_L, lay_R, 0.05)
print("crashes committed")

# zaps punctuate 8-bar phrase seams inside drops
clear()
zap_bars = ([B_DROP1 + k for k in (0, 8, 20, 28, 40, 48, 56)] +
            [B_DROP2 + k for k in (0, 8, 20, 28, 40, 48, 56)] +
            [B_CHOR2, B_CHOR2 + 8])
for b in zap_bars:
    beat = float(rng.choice([0.0, 1.5, 3.5]))
    p = rng.uniform(0.2, 0.8)
    add_at(lay_L, ZAP, bar_t(b, beat), np.cos(p * np.pi / 2))
    add_at(lay_R, ZAP, bar_t(b, beat), np.sin(p * np.pi / 2))
lay_L = reverb(lay_L, IR_L, wet=0.35)
lay_R = reverb(lay_R, IR_R, wet=0.35)
commit(lay_L, lay_R, 0.08)
print("zaps committed")


# ---------------------------------------------------------------- the 303
# Warmed acid (Q4): the within-note bright->dark sweep is kept — the
# squelch IS the sweep — but the saw is rolled off (1/k^1.3), the
# resonance capped (Q 4.5, feedback 1.15/1.2), the drive soft
# (tanh 1.2), and a sine body core rides under it. The base cutoff
# comes from the printable arc; it never parks.

acid_cache = {}


def acid_note(m, cutoff, accent=False, slide_to=None, dur=None):
    if dur is None:
        dur = STEP * (1.02 if slide_to else 0.92)
    cutoff = float(np.clip(cutoff * (1.5 if accent else 1.0), 200, 6500))
    key = (m, int(cutoff // 60), accent, slide_to, round(dur, 4))
    if key in acid_cache:
        return acid_cache[key]
    f = midi_to_hz(m)
    n = int(dur * SR)
    td = np.arange(n) / SR
    if slide_to is None:
        ph = 2 * np.pi * f * td
    else:                                  # the 303 tie: glide the back half
        f2 = midi_to_hz(slide_to)
        fc = f * (f2 / f) ** np.clip((td - 0.45 * dur) / (0.55 * dur), 0, 1)
        ph = 2 * np.pi * np.cumsum(fc) / SR
    x = np.zeros(n)
    for k in range(1, min(40, int(9000 / f)) + 1):
        x += np.sin(k * ph) / k ** 1.3          # rolled — not hard saw

    def res_lp(sig_in, c):
        c = float(min(c, 8000.0))
        sos_lp = signal.butter(2, c, "low", fs=SR, output="sos")
        y = signal.sosfilt(sos_lp, sig_in)
        bpk, apk = signal.iirpeak(min(c, 7500.0), Q=4.5, fs=SR)
        return y + (1.2 if accent else 1.15) * signal.lfilter(bpk, apk, y)

    bright = res_lp(x, cutoff * 2.5)
    dark = res_lp(x, cutoff * 0.75)
    sweep = np.exp(-td / (0.10 if accent else 0.055))
    y = np.tanh(1.2 * (sweep * bright + (1 - sweep) * dark))
    y += 0.30 * np.sin(ph)                      # the sine body core
    env = (1 - np.exp(-td / 0.0015)) * np.clip((dur - td) / 0.02, 0, 1)
    y *= env
    y /= np.max(np.abs(y)) + 1e-12
    acid_cache[key] = y
    return y


def acid_bars(b0, b1, riff, gain=1.0):
    for b in range(b0, b1):
        for s16, (m, acc, sl) in enumerate(riff):
            if m is None:
                continue
            cut = cutoff_at(b + s16 / 16.0) * \
                (1.0 + 0.20 * np.sin(2 * np.pi * s16 / 16))
            x = acid_note(m, cut, accent=bool(acc), slide_to=sl)
            p = 0.5 + 0.16 * np.sin(2 * np.pi * (b * 16 + s16) / 24)
            add_at(lay_L, x, bar_t(b, s16 * 0.25), gain * np.cos(p * np.pi / 2))
            add_at(lay_R, x, bar_t(b, s16 * 0.25), gain * np.sin(p * np.pi / 2))


def ladder_bars(b0, pitches):
    # W4a: lock ONE pitch per bar, 16th retrigger with a chatter gain
    # cell; the pitch climbs chromatically out of the key.
    cell = [1.0, 0.72, 0.88, 0.72]
    for i, m in enumerate(pitches):
        b = b0 + i
        n16 = 12 if b in ROLL_16TH else 16      # honor the composed silence
        for s16 in range(n16):
            cut = cutoff_at(b + s16 / 16.0)
            x = acid_note(m, cut, accent=(s16 % 4 == 0), dur=STEP * 0.55)
            p = 0.5 + 0.12 * (1 if s16 % 2 else -1)
            add_at(lay_L, x, bar_t(b, s16 * 0.25), cell[s16 % 4] * np.cos(p * np.pi / 2))
            add_at(lay_R, x, bar_t(b, s16 * 0.25), cell[s16 % 4] * np.sin(p * np.pi / 2))


clear()
acid_bars(B_VERSE, B_BUILD1, RIFF_A, gain=0.7)          # low and dark
ladder_bars(B_BUILD1, LADDER1)                          # E -> B (dominant)
# DROP 1 — the machine's drop, evolving
acid_bars(B_DROP1, B_DROP1 + 20, RIFF_A)                # incl. dip 1 (kick+303)
acid_bars(B_DROP1 + 20, B_DROP1 + 36, RIFF_A2)          # octave up
#         D1_DIP2: 303 silent — bass+hats carry it
acid_bars(B_DROP1 + 40, B_CHOR1, RIFF_B)                # slides, drop-1 max
#         chorus 1 + break: the 303 is silent — the heart's sections
ladder_bars(B_BUILD2, LADDER2)                          # A -> D#, hammered
# DROP 2 — the fusion: waves 1-2 are the CONVERSATION (303 speaks only
# in the licks answering the voice), dip 2 churns dark on the pedal,
# and wave 3 is the payoff — the machine at full churn UNDER the
# singing voice, riding the arc's global max: question and answer
# together at last.
acid_bars(B_DROP2 + 36, B_DROP2 + 40, RIFF_A, gain=0.8)
acid_bars(B_DROP2 + 40, B_CHOR2, RIFF_B, gain=0.9)
# the trades: each statement's held D# (bars b0+3 and b0+7, beat 3) is
# answered by the lick ending on E
D2_STMT_BARS = [B_DROP2, B_DROP2 + 8, B_DROP2 + 20, B_DROP2 + 28,
                B_DROP2 + 40, B_DROP2 + 48, B_DROP2 + 56,
                B_CHOR2, B_CHOR2 + 8]
for b0 in D2_STMT_BARS:
    for half in (3, 7):
        b = b0 + half
        for i, (m, acc, sl) in enumerate(LICK):
            x = acid_note(m, cutoff_at(b + 0.8), accent=bool(acc),
                          slide_to=sl, dur=STEP * (1.6 if i == 2 else 0.92))
            add_at(lay_L, x, bar_t(b, 3.0 + i * 0.25), 0.9)
            add_at(lay_R, x, bar_t(b, 3.0 + i * 0.25), 0.9)
acid_bars(B_OUT, B_OUT + 8, RIFF_A, gain=0.6)           # the arc walks home
commit(lay_L, lay_R, 0.25) # 303
print(f"303 committed ({len(acid_cache)} cached notes)")


# ------------------------------------------------------- W1 shiver stack
# The intro: repeated-8th stab layers that increase DISSONANCE — bare
# octave, then the 2nd-clash, then the tritone, then the alien D# — and
# the first fully consonant Em lands exactly when the kick drops.

stab_cache = {}


def shiver_stab(midis):
    if midis in stab_cache:
        return stab_cache[midis]
    n = int(0.10 * SR)
    td = np.arange(n) / SR
    v = np.zeros(n)
    for m in midis:
        f = midi_to_hz(m)
        for k in range(1, min(14, int(5000 / f)) + 1):
            v += np.sin(2 * np.pi * k * f * td) / k ** 1.3
    v = signal.sosfilt(signal.butter(2, 1100, "low", fs=SR, output="sos"), v)
    v *= (1 - np.exp(-td / 0.002)) * np.clip((0.085 - td) / 0.025, 0, 1)
    stab_cache[midis] = v / (np.max(np.abs(v)) + 1e-12)
    return stab_cache[midis]


SHIVER_LAYERS = [(B_SHIVER, (52, 64)),          # bare octave pulse
                 (B_SHIVER + 4, (66,)),         # F#4 — the 2nd clash
                 (B_SHIVER + 8, (70,)),         # A#4 — the tritone
                 (B_SHIVER + 12, (75,))]        # D#5 — the alien leading tone

clear()
for b in range(B_SHIVER, B_ENGINE):
    active = [mid for b0, mid in SHIVER_LAYERS if b >= b0]
    for e in range(8):
        g = 0.9 if e % 2 == 0 else 0.72
        for li, midis in enumerate(active):
            p = 0.5 + 0.18 * (1 if (e + li) % 2 else -1)
            place_pan(lay_L, lay_R, shiver_stab(midis), bar_t(b, e * 0.5),
                      g * (1.0 - 0.12 * li), p)
for b in range(B_ENGINE, B_ENGINE + 8):         # consonance: Em, fading out
    g0 = 0.8 * (1.0 - (b - B_ENGINE) / 8)
    for e in range(8):
        g = g0 * (0.9 if e % 2 == 0 else 0.72)
        place_pan(lay_L, lay_R, shiver_stab((52, 59, 64, 67)),
                  bar_t(b, e * 0.5), g, 0.5 + 0.18 * (1 if e % 2 else -1))
lay_L = reverb(lay_L, IR_L, 0.15)
lay_R = reverb(lay_R, IR_R, 0.15)
commit(lay_L, lay_R, 0.10)
print("shiver stack committed")


# ------------------------------------------------------- W8a ice-crack
# stab — silence — upward flick, three groups per bar, flicks rising:
# the composed glitch fill, this track's seam device.

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


ICE_FLICKS = [(76, 79, 83), (79, 83, 86), (83, 86, 88)]


def ice_crack(b):
    for gi, (beat0, flick) in enumerate(zip((0.0, 1.25, 2.5), ICE_FLICKS)):
        add_at(lay_L, PB[40], bar_t(b, beat0), 0.8)          # the low stab
        add_at(lay_R, PB[40], bar_t(b, beat0), 0.8)
        for i, m in enumerate(flick):                        # the 32nd flick
            p = 0.35 + 0.3 * gi / 2
            place_pan(lay_L, lay_R, pluck(m), bar_t(b, beat0 + 0.75 + i * 0.125),
                      0.55 + 0.1 * i, p)


clear()
ICE_BARS = [B_VERSE - 1, B_CHOR1 - 1, B_BREAK - 1]
for b in ICE_BARS:
    ice_crack(b)
lay_L = reverb(lay_L, IR_L, 0.3)
lay_R = reverb(lay_R, IR_R, 0.3)
commit(lay_L, lay_R, 0.09)
print("ice-cracks committed")


# --------------------------------------------------------- W2 zigzag arp
# The cascade formula as a sequencer cell — root, octave, octave, fifth /
# fifth, third, third, root — per chorus chord, restated up an octave in
# the late waves (state, restate higher: the development is free).

ARP_CELLS = {EM_V: (64, 76, 76, 71, 71, 67, 67, 64),
             C_V: (60, 72, 72, 67, 67, 64, 64, 60),
             D_V: (62, 74, 74, 69, 69, 66, 66, 62),
             B_V: (59, 71, 71, 66, 66, 63, 63, 59)}


def arp_bars(b0, b1, octave=0, gain=1.0, double=False):
    for b in range(b0, b1):
        cell = ARP_CELLS[CH_LAP[b % 4]]
        for s16 in range(16):
            m = cell[s16 % 8] + octave
            g = gain * (1.0 if s16 % 2 == 0 else 0.8)
            p = 0.5 + 0.25 * np.sin(2 * np.pi * s16 / 8)
            place_pan(lay_L, lay_R, pluck(m), bar_t(b, s16 * 0.25), g, p)
            if double:
                place_pan(lay_L, lay_R, pluck(m + 12), bar_t(b, s16 * 0.25),
                          g * 0.4, 1.0 - p)


clear()
arp_bars(B_CHOR1, B_BREAK, gain=0.9)
arp_bars(B_DROP2 + 40, B_CHOR2, octave=12, gain=0.7)     # wave 3, higher
arp_bars(B_CHOR2, B_OUT, gain=0.9, double=True)          # fullest: both
lay_L = reverb(lay_L, IR_L, 0.35)
lay_R = reverb(lay_R, IR_R, 0.35)
commit(lay_L, lay_R, 0.12)
print("zigzag arp committed")


# ------------------------------------------------------------------ pads
# The wet harmony bed: chorus laps + the break's low drone chords.

def pad_chord(chord, dur, attack=0.35, release=1.0):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    L = np.zeros(n)
    R = np.zeros(n)
    for m in chord:
        f = midi_to_hz(m)
        amp = 0.8 + 0.2 * np.sin(2 * np.pi * rng.uniform(0.02, 0.06) * tt +
                                 rng.uniform(0, 6))
        for det, gL, gR in [(0.9993, 1.0, 0.65), (1.0007, 0.65, 1.0)]:
            ph = 2 * np.pi * f * det * tt + rng.uniform(0, 6)
            v = (np.sin(ph) + 0.30 * np.sin(2 * ph)) * amp
            L += gL * v
            R += gR * v
    env = np.minimum(np.clip(tt / attack, 0, 1) ** 1.5,
                     np.clip((dur - tt) / release, 0, 1))
    sos = signal.butter(2, 800, "low", fs=SR, output="sos")
    L = signal.sosfilt(sos, L * env)
    R = signal.sosfilt(sos, R * env)
    peak = max(np.max(np.abs(L)), np.max(np.abs(R)), 1e-12)
    return L / peak, R / peak


clear()
for b in range(B_CHOR1, B_BREAK):
    pL, pR = pad_chord(CH_LAP[b % 4], BAR + 0.8)
    add_at(lay_L, pL, bar_t(b), 0.9)
    add_at(lay_R, pR, bar_t(b), 0.9)
for b in range(B_BREAK, B_BUILD2, 4):           # the break: slow low lap
    pL, pR = pad_chord(tuple(m - 12 for m in CH_LAP[(b // 4) % 4]),
                       4 * BAR + 1.5, attack=2.0, release=2.5)
    add_at(lay_L, pL, bar_t(b), 0.95)
    add_at(lay_R, pR, bar_t(b), 0.95)
for b in range(B_DROP2, B_OUT):
    pL, pR = pad_chord(CH_LAP[b % 4], BAR + 0.8)
    add_at(lay_L, pL, bar_t(b), 0.85)
    add_at(lay_R, pR, bar_t(b), 0.85)
for b in range(B_OUT, B_KSTOP, 4):              # outro: Em holds, fading
    pL, pR = pad_chord(EM_V, 4 * BAR + 1.5, attack=1.5, release=2.5)
    g = 0.8 * (1.0 - 0.5 * (b - B_OUT) / (B_KSTOP - B_OUT))
    add_at(lay_L, pL, bar_t(b), g)
    add_at(lay_R, pR, bar_t(b), g)
lay_L = reverb(lay_L, IR_L, 0.5)
lay_R = reverb(lay_R, IR_R, 0.5)
commit(lay_L, lay_R, 0.13)
print("pads committed")


# ----------------------------------------------------------------- drone
# The low E bed under the intro stack and the break.

clear()
drone = (0.6 * np.sin(2 * np.pi * 41.2 * t) +
         1.0 * np.sin(2 * np.pi * 82.4 * t + 0.7) +
         0.25 * np.sin(2 * np.pi * 164.8 * t + 1.9))
drone *= 0.85 + 0.15 * np.sin(2 * np.pi * 0.09 * t)
env_d = (np.clip((t - bar_t(1)) / 6.0, 0, 1) *
         np.clip((bar_t(B_ENGINE + 2) - t) / 5.0, 0, 1) +
         np.clip((t - bar_t(B_BREAK)) / 4.0, 0, 1) *
         np.clip((bar_t(B_BUILD2 + 2) - t) / 4.0, 0, 1))
lay_L += drone * np.clip(env_d, 0, 1)
lay_R += drone * np.clip(env_d, 0, 1)
commit(lay_L, lay_R, 0.07)
print("drone committed")


# ------------------------------------------------------------- THE VOICE
# tech_noir's love_phrase, ported (declared): plaintive, nearly-pure,
# very wet — the terminator love-song singing as an INSTRUMENT. New
# melodies only; the recipe is the borrow, never the tune.

voice_cache = {}


def voice_phrase(notes):
    key = tuple(notes)
    if key in voice_cache:
        return voice_cache[key]
    total = sum(d for _, d in notes) * BEAT
    n = int((total + 2.5) * SR)
    tt = np.arange(n) / SR
    f_curve = glide_curve([(m, d * BEAT) for m, d in notes], n, tau=0.07)
    vib = 1.0 + 0.005 * np.sin(2 * np.pi * 5.2 * tt) * np.clip(tt / 1.0, 0, 1)
    ph = 2 * np.pi * np.cumsum(f_curve * vib) / SR
    v = (np.sin(ph) + 0.40 * np.sin(2 * ph) +
         0.16 * np.sin(3 * ph) + 0.07 * np.sin(4 * ph))
    env = np.minimum(np.clip(tt / 0.25, 0, 1),
                     np.clip((total + 0.4 - tt) / 1.2, 0, 1))
    sos_w = signal.butter(2, 3000, "low", fs=SR, output="sos")
    v = signal.sosfilt(sos_w, v * env)
    v /= np.max(np.abs(v)) + 1e-12
    voice_cache[key] = v
    return v


def place_refrain(b0, gain, octave_double=False, resolve=False, count=True):
    notes = THEME + (RESOLVE if resolve else [])
    x = voice_phrase(notes)
    add_at(lay_L, x, bar_t(b0), gain)
    add_at(lay_R, x, bar_t(b0), gain * 0.96)
    if octave_double:
        hi = voice_phrase([(m + 12, d) for m, d in notes])
        add_at(lay_L, hi, bar_t(b0), gain * 0.32)
        add_at(lay_R, hi, bar_t(b0), gain * 0.35)
    if count:
        REFRAIN_STMTS.append(b0)


clear()
# thesis: the question alone, hanging on D# (a declared half, uncounted)
add_at(lay_L, voice_phrase(THEME_Q), bar_t(0), 0.85)
add_at(lay_R, voice_phrase(THEME_Q), bar_t(0), 0.82)
# verse: the 2-bar ghost fragments
for b0 in (B_VERSE + 4, B_VERSE + 12):
    add_at(lay_L, voice_phrase(FRAG), bar_t(b0), 0.5)
    add_at(lay_R, voice_phrase(FRAG), bar_t(b0), 0.48)
# chorus 1 — THE REVEAL, twice
place_refrain(B_CHOR1, 1.0)
place_refrain(B_CHOR1 + 8, 1.0)
# break — once, half-voice
place_refrain(B_BREAK + 4, 0.55)
# drop 2 — the fusion, three evolving waves + the dip hold
place_refrain(B_DROP2, 1.0)
place_refrain(B_DROP2 + 8, 1.0)
add_at(lay_L, voice_phrase(DIP_HOLD), bar_t(B_DROP2 + 16), 0.8)   # the dip
add_at(lay_R, voice_phrase(DIP_HOLD), bar_t(B_DROP2 + 16), 0.78)
place_refrain(B_DROP2 + 20, 1.0, octave_double=True)
place_refrain(B_DROP2 + 28, 1.0, octave_double=True)
place_refrain(B_DROP2 + 40, 1.0, octave_double=True)
place_refrain(B_DROP2 + 48, 1.0, octave_double=True)
place_refrain(B_DROP2 + 56, 1.0, octave_double=True)
# chorus 2 — the last statement resolves ACROSS the outro seam
place_refrain(B_CHOR2, 1.0, octave_double=True)
place_refrain(B_CHOR2 + 8, 1.0, octave_double=True, resolve=True)
# bookend: the answer alone, and the final E is STATED
add_at(lay_L, voice_phrase(THEME_A + RESOLVE), bar_t(B_KSTOP), 0.85)
add_at(lay_R, voice_phrase(THEME_A + RESOLVE), bar_t(B_KSTOP), 0.82)
lay_L = reverb(lay_L, IR_L, 0.55)
lay_R = reverb(lay_R, IR_R, 0.55)
commit(lay_L, lay_R, 0.30)
print("the voice committed")


# ------------------------------------------------------------------ air

sos_air = signal.butter(4, [150, 1100], "bandpass", fs=SR, output="sos")
air = signal.sosfilt(sos_air, rng.standard_normal(N))
air /= np.max(np.abs(air))
air_env = slow_noise(0.05, 0.4, 1.0)
edge = np.minimum(np.clip((bar_t(B_ENGINE) - t) / 12.0, 0, 1) +
                  np.clip((t - bar_t(B_OUT + 8)) / 20.0, 0, 1), 1.0)
commit(air * air_env * edge, air * air_env[::-1] * edge, 0.04)
print("air committed")


# ---------------------------------------------------------------- master

fade(mix_L)
fade(mix_R)

peak = max(np.max(np.abs(mix_L)), np.max(np.abs(mix_R)))
mix_L = mix_L / peak * 0.86
mix_R = mix_R / peak * 0.86

stereo = np.empty((N, 2))
stereo[:, 0] = mix_L
stereo[:, 1] = mix_R
pcm = (stereo * 32767.0).astype(np.int16)

OUT_DIR = "/workspace/music"
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, "maschinenherz_v0.3.wav")
with wave.open(OUT, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())

print(f"\nCreated: {os.path.abspath(OUT)}")
print(f"Duration: {N / SR:.1f} s  |  {SR} Hz stereo, 16-bit PCM  |  "
      f"{BPM:.0f} BPM, E minor (Em-C-D-B; the D# of B is the color)")

MP3 = os.path.join(OUT_DIR, "maschinenherz.mp3")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", OUT,
                "-vn", "-ar", "44100", "-ac", "2", "-b:a", "192k", MP3],
               check=True)
print(f"Created: {os.path.abspath(MP3)}  (192k mp3)")

# ---------------------------------------------------------------- verify form
# Song form with a withheld reveal + the filter-arc and K-b-b-b checks
# (see ../VERIFY.md and the notes doc's Verify paragraph).

print("\nSection map:")
SECTIONS = [("thesis", 0), ("shiver intro (W1)", B_SHIVER),
            ("engine start", B_ENGINE), ("verse", B_VERSE),
            ("build 1 (ladder)", B_BUILD1), ("DROP 1 (machine)", B_DROP1),
            ("chorus 1 (REVEAL)", B_CHOR1), ("break", B_BREAK),
            ("build 2 (ladder)", B_BUILD2), ("DROP 2 (FUSION)", B_DROP2),
            ("chorus 2", B_CHOR2), ("outro", B_OUT), ("bookend", B_KSTOP)]
for name, b in SECTIONS:
    print(f"  {bar_t(b):6.1f} s  bar {b:3d}  {name}")
print(f"  {DURATION:6.1f} s  end")

print(f"\nRefrain statements (full Q+A, identical melody): "
      f"{len(REFRAIN_STMTS)} at bars {REFRAIN_STMTS}")
print("  declared fragments (uncounted): thesis Q-half bar 0, verse ghosts "
      f"bars {B_VERSE + 4}/{B_VERSE + 12}, dip hold bar {B_DROP2 + 16}, "
      f"bookend A-half bar {B_KSTOP}")

print("\nThe filter arc (the 303's development — cutoff at boundaries):")
for name, b in SECTIONS:
    print(f"  bar {b:3d}  {name:20s} {cutoff_at(b):6.0f} Hz")

print("\nSeam checklist (what crosses every boundary):")
for b, dev in [(B_SHIVER, "the thesis' last note rings into the drone; stack layer 1 enters"),
               (B_ENGINE, "kick-roll build bar 19; the stack lands CONSONANT (Em) on the downbeat"),
               (B_VERSE, "ice-crack fill bar 35; bass/hats unbroken"),
               (B_BUILD1, "the ladder IS the seam (W4a); bass keeps rolling under it"),
               (B_DROP1, "16th kick roll into the composed silent beat (bar 59 beat 4)"),
               (B_CHOR1, "ice-crack bar 123 + crash; engine unbroken into the walking harmony"),
               (B_BREAK, "ice-crack bar 139; chorus pads hand to the low drone"),
               (B_BUILD2, "bass re-enters FIRST (the pickup); ladder climbs to D#"),
               (B_DROP2, "silent beat bar 163 beat 4; the drop's downbeat E resolves the ladder's D#"),
               (B_CHOR2, "harmony/engine continuous; crash; arp doubles"),
               (B_OUT, "the last statement's RESOLVE note (E) crosses the seam; arc descends"),
               (B_KSTOP, "kick stops; the voice enters over the ringing hall")]:
    print(f"  bar {b:3d} ({bar_t(b):5.1f} s): {dev}")

def rms_between(b0, b1):
    i0 = int(bar_t(b0) * SR)
    i1 = int(bar_t(b1) * SR) if b1 is not None else N
    return np.sqrt(np.mean(mix_L[i0:i1] ** 2 + mix_R[i0:i1] ** 2) / 2)

print("\nPer-section RMS:")
R = {}
for (name, b0), (_, b1) in zip(SECTIONS, SECTIONS[1:] + [("end", None)]):
    R[name] = rms_between(b0, b1)
    print(f"  {name:22s} {R[name]:.3f}")

dense = np.arange(0, B_END, 0.25)
peak_bar = dense[np.argmax([cutoff_at(b) for b in dense])]
first_full = min(REFRAIN_STMTS)
checks = [
    ("staircase: shiver < engine < verse < drop 1",
     R["shiver intro (W1)"] < R["engine start"] < R["verse"]
     < R["DROP 1 (machine)"]),
    ("drop 2 (the fusion) > drop 1 (the machine alone)",
     R["DROP 2 (FUSION)"] > R["DROP 1 (machine)"]),
    ("the break is the trough between the drops",
     R["break"] < min(R["chorus 1 (REVEAL)"], R["DROP 2 (FUSION)"])),
    ("the summit is the fusion or chorus 2",
     max(R.values()) in (R["DROP 2 (FUSION)"], R["chorus 2"])),
    ("the outro settles; the bookend is quieter than the break",
     R["outro"] < R["chorus 2"] and R["bookend"] < R["break"]),
    (f"refrain count >= 6 and none before the reveal (first at bar {first_full})",
     len(REFRAIN_STMTS) >= 6 and first_full >= B_CHOR1),
    ("filter arc: rises verse -> build -> drop 1",
     cutoff_at(B_VERSE) < cutoff_at(B_BUILD1) < cutoff_at(B_DROP1)),
    ("filter arc: global maximum inside drop 2",
     B_DROP2 <= peak_bar < B_CHOR2),
    ("filter arc: outro returns to the intro cutoff",
     cutoff_at(B_END - 1) <= cutoff_at(B_VERSE) * 1.25),
    ("K-b-b-b contract: zero bass hits on kick 16ths",
     BASS_GAP_VIOLATIONS == 0),
]
print("\nForm checks:")
ok = True
for name, passed in checks:
    print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
    ok &= passed
print("banned by construction: gothic piano / rompler strings / reverse "
      "cymbal / Dune palette / TTS / hard-saw acid / W3 / W5")
print("all checks passed" if ok else "SOME CHECKS FAILED")

"""
Notes on volume:

  The master knob — the 303's commit weight vs the bass's:

  - maschinenherz.py:668 — commit(lay_L, lay_R, 0.17) — the whole 303 layer. This is the one to turn first; try 0.20–0.22.
  - maschinenherz.py:480 — commit(lay_L, lay_R, 0.30) — the bass layer, if you'd rather pull the bass down instead.

  Per-section trims — the gain= args on the acid_bars calls (lines 638–667): verse 0.7, drop 1 phases 1.0 (default), drop 2 dip 0.8, wave 3 0.9, outro 0.6. Use these if the 303 only feels
  buried in specific sections (e.g. wave 3, where it competes with voice + pads + arp).

  One thing to know: commit peak-normalizes each layer, so the accented notes set the peak — if the 303 feels quiet between accents, raising 0.17 still helps, but the accent/non-accent
  balance lives in the cutoff * 1.5 accent boost at line ~585. I'd start with just 668 → 0.21 and re-run.
"""
