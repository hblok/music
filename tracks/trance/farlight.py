#!/usr/bin/env python3
"""
farlight.py — "Far Light" (~4:45, 136 BPM, E natural minor). The second
original in a proven shape (song form) — design notes: farlight_notes.md.
1994/95 Berlin/MFS melodic trance: the era-walk continues past Frankfurt,
and the track's own story is the leaving. A LIGHT, HAPPY track.

THE CONCEPT — one refrain, one re-light. The verses rock on a restless
shuttle (Em-D-C-D, i-VII-VI-VII) that never cadences: the familiar ground.
The refrain is THE FAR LIGHT — a glassy bell theme, Q/A at melody level:
the antecedent rises and hangs on F#5 (third of the D chord, and the
leading tone of the G major that only arrives at the very end); the
consequent reaches higher and falls home to a final G5. That G is
harmonized as the minor third of Em in every chorus (home, the departure
not yet taken) and — exactly once, at the last statement — as the ROOT of
G major: the departure taken. The D chord is the pivot (VII of Em, V of
G), so the identical penultimate bar resolves either way. The tune never
changes; the light does.

  0:00  THESIS       Solo bell, the refrain's question phrase, half-voice.
  0:07  intro        Kick enters on a bell pickup; hats; bass; the arp
                     fades up — one element per 4 bars.
  0:36  verse 1      The pluck arp carries low Q/A phrase pairs over the
                     shuttle; open hats join; no cadence anywhere.
  1:04  build 1      First snare roll + dark swell, pads open, crash →
  1:18  CHORUS 1     The bell refrain x2, full kit. Both land home (Em).
  1:46  verse 2      Development: a counter-arp answers each phrase an
                     octave up; bass adds octave jumps; claps join.
  2:14  build 2      Longer roll; a one-bar drum dropout with a lone bell
                     pickup hanging in it →
  2:28  CHORUS 2     Refrain x2 with octave bell doubling. Still Em.
  2:56  bridge       Teardown: kick out, big wet pads on C/D (the tonic
                     avoided); the bell asks the ANTECEDENT ALONE twice —
                     no answer comes; quiet kick walks back in, roll +
                     swell → ONE BEAT of near-silence, a bell pickup
                     hanging in it —
  3:25  FINAL CHORUS The fusion: the warm lead countermelody UNDER the
                     bell refrain x3 (first time they overlap). Mid-drop
                     dip, then the fullest wave with ride and glitter.
                     Statement 3 is THE RE-LIGHT: its final bar lands
                     G MAJOR — the departure taken. Loudest section.
  4:07  outro        Layers peel; the kick stops; the solo bell bookend
                     states the full refrain once more, KEEPING the major
                     light; a G major bell chord rings out.

Sanctioned era vocabulary (the 1995 marker): snare rolls + dark
bandlimited noise swells (250-2400 Hz, low in the mix — never a
white-noise wash). Banned by construction: acid resonance, sidechain
pump, reverse cymbals/downsweeps, tom fills, borrowed leading tones
(everything is E-natural-minor diatonic — printed and checked), supersaw
stacks. Everything synthesized (numpy + scipy).
Output: /workspace/music/farlight.wav + farlight.mp3 (192k, ffmpeg).
"""

import os
import subprocess
import wave
import numpy as np
from scipy import signal

SR = 44100
BPM = 136.0
BEAT = 60.0 / BPM
BAR = BEAT * 4
STEP = BEAT / 4
GRID0 = 0.5

rng = np.random.default_rng(1995)   # the year trance left home

# ----------------------------------------------------- section boundaries (bars)
B_INTRO = 4       # kick enters on a bell pickup
B_V1 = 20         # verse 1: arp Q/A pairs over the shuttle
B_B1 = 36         # build 1: first roll + swell
B_CH1 = 44        # CHORUS 1 — the far light (lands Em)
B_V2 = 60         # verse 2: counter-arp answers
B_B2 = 76         # build 2 (drum dropout in bar 83)
B_CH2 = 84        # CHORUS 2 — octave bells (lands Em)
B_BR = 100        # bridge: the question alone, tonic avoided
B_REB = 110       # rebuild: quiet kick walks back in
B_FIN = 116       # FINAL CHORUS (silent beat 0, slam on beat 2)
B_DIP = 124       # mid-drop dip
B_WAVE = 128      # the fullest wave (+ ride); re-light at bar 139
B_OUT = 140       # outro deconstruction
B_KSTOP = 146     # the kick stops
B_BOOK = 146      # solo bell bookend (keeps the major light)
B_END = 156

DURATION = GRID0 + B_END * BAR + 6.2
N = int(SR * DURATION)
t = np.arange(N) / SR


def bar_t(b, beat=0.0):
    return GRID0 + b * BAR + beat * BEAT


def section_of(b):
    if b < B_INTRO:
        return "thesis"
    if b < B_V1:
        return "intro"
    if b < B_B1:
        return "v1"
    if b < B_CH1:
        return "b1"
    if b < B_V2:
        return "ch1"
    if b < B_B2:
        return "v2"
    if b < B_CH2:
        return "b2"
    if b < B_BR:
        return "ch2"
    if b < B_REB:
        return "br"
    if b < B_FIN:
        return "reb"
    if b < B_DIP:
        return "fin"
    if b < B_WAVE:
        return "dip"
    if b < B_OUT:
        return "wave"
    if b < B_BOOK:
        return "out"
    return "book"


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


IR_L = make_reverb_ir(5.0, 2.6, 7)
IR_R = make_reverb_ir(5.0, 2.6, 11)


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
# ONE family for the whole track: E natural minor, the restless shuttle
# Em-D-C-D (i-VII-VI-VII). The refrain's consequent supplies the only root
# cadences — Em at every chorus, G major exactly once at the re-light.
# D is the pivot: VII of Em AND V of G, so the identical penultimate bar
# resolves either way. chord = (bass_root_midi, mid-register voicing)

Em = (40, (52, 55, 59, 64))     # E2 | E3 G3 B3 E4
DM = (38, (50, 54, 57, 62))     # D2 | D3 F#3 A3 D4
CM = (36, (48, 52, 55, 60))     # C2 | C3 E3 G3 C4
GM = (43, (55, 59, 62, 67))     # G2 | G3 B3 D4 G4  (the re-light, once)

SHUTTLE = [Em, DM, CM, DM]           # verses/intro/builds: rocks, never lands
CH_CELL = [Em, DM, CM, DM, Em, DM, CM, Em]   # refrain harmony, cadences home
CH_CELL_G = CH_CELL[:-1] + [GM]              # the re-light cell
BRIDGE_CELL = [CM, DM]               # the tonic avoided — asking

CHORD_AT = [Em] * B_END


def fill(b0, b1, seq):
    for b in range(b0, b1):
        CHORD_AT[b] = seq[(b - b0) % len(seq)]


fill(0, B_CH1, SHUTTLE)              # thesis / intro / verse 1 / build 1
fill(B_CH1, B_V2, CH_CELL)           # CHORUS 1 (two cells, both land Em)
fill(B_V2, B_CH2, SHUTTLE)           # verse 2 / build 2
fill(B_CH2, B_BR, CH_CELL)           # CHORUS 2
fill(B_BR, B_FIN, BRIDGE_CELL)       # bridge + rebuild: C D C D ... no Em
fill(B_FIN, B_FIN + 16, CH_CELL)     # final chorus statements 1-2
fill(B_FIN + 16, B_OUT, CH_CELL_G)   # statement 3 — THE RE-LIGHT (bar 139 = G)
fill(B_OUT, B_BOOK, SHUTTLE)         # outro: one last look back at the ground
fill(B_BOOK, B_BOOK + 8, CH_CELL_G)  # bookend keeps the major light
fill(B_BOOK + 8, B_END, [GM])        # the final chord's bars

# ============================================================= the melodies
# THE REFRAIN — identical in every statement. 8 bars, Q/A at melody level.
# Antecedent: a bouncing rise (E5 G5 B5) that hangs a whole bar on F#5 —
# third of the D chord, off-tonic, and the leading tone of the G major that
# only arrives at the very end. Consequent: the same rhythm, reaching
# higher (D6), falling home to a final G5 — minor third of Em every chorus,
# root of G major once. All pitches E-natural-minor diatonic.
REFRAIN = [(76, 1.5), (79, 0.5), (83, 2),    # Em: E5 G5 B5 — up, gladly
           (81, 1.5), (78, 0.5), (81, 2),    # D:  A5 F#5 A5 — the bounce
           (79, 1.5), (76, 0.5), (81, 2),    # C:  G5 E5 A5 — bright add6
           (78, 4),                          # D:  F#5 — THE HANG (question)
           (76, 1.5), (79, 0.5), (83, 2),    # Em: the same opening
           (81, 1.5), (83, 0.5), (86, 2),    # D:  A5 B5 D6 — reaches higher
           (83, 1.5), (79, 0.5), (81, 2),    # C:  B5 G5 A5 — turning home
           (79, 4)]                          # G5 — HOME (the re-light note)
ANTE = REFRAIN[:10]                          # the question phrase alone
# final-chorus statement 1 rides in on beat 2 out of the silent beat
REFRAIN_PICKUP = [(76, 0.5)] + REFRAIN[1:]

# THE VERSE — low Q/A pairs carried by the pluck arp (2 bars each): the
# question hangs on F#4 over the shuttle's D, the answer resolves to E4.
VERSE_Q = [(64, 1.5), (67, 0.5), (66, 2), (62, 1), (64, 1), (66, 2)]
VERSE_A = [(64, 1.5), (67, 0.5), (69, 2), (67, 1), (66, 1), (64, 2)]

# THE COUNTERMELODY (the fusion voice, final chorus only) — the warm lead
# under the bell, register a fifth-to-octave below, moving against the
# refrain's long notes and landing G4 under its G5.
COUNTER = [(64, 3), (66, 1),                 # Em/D
           (69, 3), (67, 1),                 # C/D
           (64, 3), (62, 1),                 # Em/D
           (66, 1.5), (64, 0.5), (66, 2),    # moving under THE HANG
           (64, 3), (67, 1),
           (69, 3), (71, 1),
           (72, 3), (71, 1),                 # C5 B4 — turning with the tune
           (67, 4)]                          # G4 home, an octave under

HOOKS = 0                 # full refrain statements
STMT_LIGHT = []           # the chord under each statement's final note
VOICE_SPANS = []          # bell refrain activity (for the duet check)
COUNTER_SPANS = []        # lead countermelody activity


# ============================================================= drum kit (dry)

def make_kick():
    n = int(0.42 * SR)
    td = np.arange(n) / SR
    f_curve = 42.0 + 105.0 * np.exp(-td * 52.0)      # a touch deeper than 1992
    body = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    sub = np.sin(2 * np.pi * (36 + 16 * np.exp(-td * 3)) * td) * np.exp(-td * 3.0)
    sos_c = signal.butter(2, [1800, 9000], "bandpass", fs=SR, output="sos")
    click = signal.sosfilt(sos_c, rng.standard_normal(n)) * np.exp(-td * 500)
    click /= np.max(np.abs(click)) + 1e-12
    env = (1 - np.exp(-td / 0.0008)) * np.exp(-td * 8.0)
    x = body * env + 0.55 * sub + 0.42 * click * (1 - np.exp(-td / 0.0008))
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
# no reverse cymbal, no downsweep — that family is nachtkind's (banned here)


def silent_beat(b, beat):
    # the one composed drop-silence: final-chorus bar 116, beat 1 of 4
    return b == B_FIN and beat < 1.0


KICK_G = {"intro": 0.75, "v1": 0.9, "b1": 0.95, "ch1": 1.0, "v2": 0.95,
          "b2": 0.95, "ch2": 1.0, "fin": 1.0, "dip": 0.85, "wave": 1.0}


def kick_gain(b):
    s = section_of(b)
    if s in KICK_G:
        if s == "b2" and b == B_CH2 - 1:
            return 0.0                                # the one-bar drum dropout
        return KICK_G[s]
    if s == "reb":
        return 0.4 + 0.05 * (b - B_REB)               # walks back in quietly
    if s == "out":
        return 0.85 if b < B_OUT + 3 else 0.7         # thins, then stops
    return 0.0


clear()
for b in range(B_END):
    g = kick_gain(b)
    if g <= 0:
        continue
    for beat in range(4):
        if silent_beat(b, beat):
            continue
        add_at(lay_L, KICK, bar_t(b, beat), g)
        add_at(lay_R, KICK, bar_t(b, beat), g)
commit(lay_L, lay_R, 0.36)
print("kick committed")

clear()
CH = [0.5, 0.28, 0.0, 0.34]
HAT_G = {"v1": 0.7, "b1": 0.85, "ch1": 1.0, "v2": 0.85, "b2": 0.9,
         "ch2": 1.0, "fin": 1.0, "dip": 0.55, "wave": 1.0}
for b in range(B_END):
    s = section_of(b)
    if s == "intro":
        if b < 8:
            continue                                  # hats are element two
        g = 0.6
    elif s in HAT_G:
        if s == "b2" and b == B_CH2 - 1:
            continue                                  # the dropout bar
        g = HAT_G[s]
    elif s == "reb" and b >= B_REB + 2:
        g = 0.4 + 0.075 * (b - B_REB - 2)
    elif s == "out" and b < B_KSTOP - 2:
        g = 0.6
    else:
        continue
    for beat in range(4):
        if silent_beat(b, beat):
            continue
        for sx in range(4):
            if CH[sx] <= 0:
                continue
            add_at(lay_L, CHAT, bar_t(b, beat + sx * 0.25), g * CH[sx] * 0.9)
            add_at(lay_R, CHAT, bar_t(b, beat + sx * 0.25), g * CH[sx])
        add_at(lay_L, OHAT, bar_t(b, beat + 0.5), g * 0.9)
        add_at(lay_R, OHAT, bar_t(b, beat + 0.5), g * 0.8)
commit(lay_L, lay_R, 0.075)
print("hats committed")

clear()
for b in range(B_END):
    s = section_of(b)
    if s not in ("ch1", "v2", "ch2", "fin", "wave", "out"):
        continue
    if s == "out" and b >= B_OUT + 4:
        continue
    g = 0.7 if s == "v2" else 1.0
    for beat in (1, 3):
        if silent_beat(b, beat):
            continue
        p = 0.42 if beat == 1 else 0.58
        place_pan(lay_L, lay_R, CLAP, bar_t(b, beat), g, p)
commit(lay_L, lay_R, 0.10)
print("claps committed")

clear()
for b in range(B_WAVE, B_OUT):                        # ride crowns the wave
    for e in range(8):
        g = 0.7 if e % 2 == 0 else 0.45
        place_pan(lay_L, lay_R, RIDE, bar_t(b, e * 0.5), g, 0.5)
commit(lay_L, lay_R, 0.045)
print("ride committed")

clear()
for b, g in [(B_CH1, 1.0), (B_V2, 0.5), (B_CH2, 1.0), (B_BR, 0.45),
             (B_WAVE, 0.55), (B_FIN + 16, 0.6), (B_OUT, 0.5)]:
    place_pan(lay_L, lay_R, CRASH, bar_t(b), g, 0.5)
place_pan(lay_L, lay_R, CRASH, bar_t(B_FIN, 1), 1.0, 0.5)   # the slam on beat 2
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
roll(B_B1 + 4, B_CH1, 0.5)
roll(B_B2 + 3, B_CH2, 0.6)         # runs through the dropout bar — exposed
roll(B_REB + 2, B_FIN, 0.65)
commit(lay_L, lay_R, 0.08)
print("rolls committed")


# ============================================================= bass (warmed)
# lost_v4 school: rolled-off harmonics, gentle peak (Q 1.2 / blend 0.3 — no
# acid), sine sub, soft tanh. Rolling 16ths OFF the beat (the kick owns
# beat zero — no sidechain pump on this track, the pattern is the space).

bass_cache = {}


def bass_note(midi, cutoff, drive=0.9, dur=STEP * 0.92):
    key = (midi, int(cutoff // 60), round(drive, 1))
    if key in bass_cache:
        return bass_cache[key]
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    for k in range(1, min(22, int(3500 / f)) + 1):
        x += np.sin(2 * np.pi * k * f * td) / k ** 1.3
    y = signal.sosfilt(signal.butter(2, cutoff, "low", fs=SR, output="sos"), x)
    bpk, apk = signal.iirpeak(cutoff, Q=1.2, fs=SR)
    y = y + 0.3 * signal.lfilter(bpk, apk, y)
    y += 0.5 * np.sin(2 * np.pi * (f / 2) * td)
    y = np.tanh(drive * y)
    y *= (1 - np.exp(-td / 0.004)) * np.clip((dur - td) / 0.02, 0, 1)
    bass_cache[key] = y / (np.max(np.abs(y)) + 1e-12)
    return bass_cache[key]


BASS_PAT_A = [(1, 0, 0.85), (2, 0, 0.7), (3, 0, 0.95)]          # verses: rolling root
BASS_PAT_B = [(1, 0, 0.85), (2, 12, 0.75), (3, 0, 0.95)]        # +octave jumps (dev.)
BASS_CUT = {"intro": 420, "v1": 480, "b1": 520, "ch1": 560, "v2": 500,
            "b2": 540, "ch2": 560, "reb": 380, "fin": 600, "dip": 480,
            "wave": 620, "out": 440}
clear()
for b in range(B_END):
    s = section_of(b)
    root = CHORD_AT[b][0]
    if s == "intro" and b < 12:
        continue                                       # bass is element three
    if s == "br":
        # the bridge throb: soft half-notes, filtered low, kick gone
        for beat in (0, 2):
            x = bass_note(root, 320, 0.9, dur=BEAT * 0.9)
            add_at(lay_L, x, bar_t(b, beat), 0.8)
            add_at(lay_R, x, bar_t(b, beat), 0.8)
        continue
    if s not in BASS_CUT:
        continue
    if s == "b2" and b == B_CH2 - 1:
        continue                                       # the dropout bar
    if s == "out" and b >= B_KSTOP - 2:
        continue                                       # bass out before the kick
    cut = BASS_CUT[s]
    pat = BASS_PAT_A if s in ("intro", "v1", "b1") else BASS_PAT_B
    for beat in range(4):
        if silent_beat(b, beat):
            continue
        for sx, off, gg in pat:
            x = bass_note(root + off, cut)
            tt = bar_t(b, beat + sx * 0.25)
            add_at(lay_L, x, tt, gg)
            add_at(lay_R, x, tt, gg)
commit(lay_L, lay_R, 0.30)
print(f"bass committed ({len(bass_cache)} cached)")

# a soft sustained sub for weight — a rising ladder across the choruses
# (ch1 light -> ch2 -> final deepest: the lost_v6 RMS lever), pulled OUT
# during the dip bars so the dip is felt and the wave's return hits
clear()
for b in (list(range(B_CH1, B_V2)) + list(range(B_CH2, B_BR))
          + list(range(B_FIN, B_DIP)) + list(range(B_WAVE, B_OUT))):
    f = midi_to_hz(CHORD_AT[b][0] - 12)
    seg_n = int(BAR * SR)
    td = np.arange(seg_n) / SR
    sub = np.sin(2 * np.pi * f * td) * np.minimum(np.clip(td / 0.05, 0, 1),
                                                  np.clip((BAR - td) / 0.1, 0, 1))
    if b == B_FIN:
        sub *= np.clip((td - BEAT) / 0.05, 0, 1)       # honors the silent beat
    g = 0.85 if b >= B_FIN else (0.6 if b >= B_CH2 else 0.45)
    add_at(lay_L, sub, bar_t(b), g)
    add_at(lay_R, sub, bar_t(b), g)
commit(lay_L, lay_R, 0.10)
print("sustained sub committed")


# ============================================================= pluck arp
# lost's glassy pluck, re-voiced on the shuttle: the 16th texture of the
# verses, AND the carrier of the verse Q/A phrases (louder single notes
# over the pattern). Glitter: octave pings on offbeats in the big sections.

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


ARP_PAT = [0, 2, 1, 3, 0, 2, 4, 3]                     # a bright bounce
ARP_G = {"v1": 0.6, "b1": 0.65, "ch1": 0.7, "v2": 0.65, "b2": 0.7,
         "ch2": 0.7, "fin": 0.75, "dip": 0.6, "wave": 0.8, "out": 0.5}
clear()
for b in range(B_END):
    s = section_of(b)
    if s == "intro":
        if b < 16:
            continue                                   # arp is element four:
        g0 = 0.2 + 0.1 * (b - 16)                      # it fades up into v1
    elif s == "reb" and b >= B_REB + 2:
        g0 = 0.45
    elif s in ARP_G:
        if s == "b2" and b == B_CH2 - 1:
            continue
        if s == "out" and b >= B_KSTOP - 2:
            continue
        g0 = ARP_G[s]
    else:
        continue
    voicing = CHORD_AT[b][1]
    notes = list(voicing) + [voicing[1] + 12]
    for sx in range(16):
        if silent_beat(b, sx * 0.25):
            continue
        idx = ARP_PAT[sx % len(ARP_PAT)] % len(notes)
        m = notes[idx]
        pan = 0.5 + 0.4 * (idx / (len(notes) - 1) - 0.5)
        place_pan(lay_L, lay_R, pluck(m), bar_t(b, sx * 0.25),
                  g0 * (0.9 if sx % 2 else 1.0), pan)
        # the glitter: octave-up pings on offbeats in the big happy sections
        if s in ("ch2", "wave") and sx % 4 == 2:
            place_pan(lay_L, lay_R, pluck(m + 12), bar_t(b, sx * 0.25),
                      0.35, 1.0 - pan)

# the verse Q/A phrases, carried by the arp instrument (louder, panned
# wide); verse 2's development: a counter-arp answers each phrase an
# octave up, two beats late, on the other side — the composed echo
def place_pluck_theme(notes, t0, gain, pan):
    tm = t0
    for m, d in notes:
        place_pan(lay_L, lay_R, pluck(m), tm, gain, pan)
        place_pan(lay_L, lay_R, pluck(m), tm + STEP, gain * 0.45, pan)  # doubled strike
        tm += d * BEAT


for b0 in (B_V1, B_V1 + 8):
    place_pluck_theme(VERSE_Q, bar_t(b0 + 0), 1.0, 0.38)
    place_pluck_theme(VERSE_A, bar_t(b0 + 4), 1.0, 0.38)
for b0 in (B_V2, B_V2 + 8):
    place_pluck_theme(VERSE_Q, bar_t(b0 + 0), 1.0, 0.38)
    place_pluck_theme([(m + 12, d) for m, d in VERSE_Q], bar_t(b0, 2), 0.55, 0.68)
    place_pluck_theme(VERSE_A, bar_t(b0 + 4), 1.0, 0.38)
    place_pluck_theme([(m + 12, d) for m, d in VERSE_A], bar_t(b0 + 4, 2), 0.55, 0.68)

lay_L = reverb(lay_L, IR_L, 0.3)
lay_R = reverb(lay_R, IR_R, 0.3)
commit(lay_L, lay_R, 0.16)
print(f"pluck arp committed ({len(pluck_cache)} cached)")


# ============================================================= THE BELL
# The far light — this track's new recipe and refrain voice. Tubular-bell
# partial family (1 / 2 / 2.76 / 5.40), gains rolled off hard (warmth rule:
# no 2-4 kHz spike — the 5.40 partial is a fast-dying strike shimmer, the
# sustain is fundamental + octave), a soft mallet thunk, a detuned pair for
# slow shimmer beating, long dark hall. Glassy but ROUND.

bell_cache = {}


def bell_note(midi, dur):
    key = (midi, round(dur, 2))
    if key in bell_cache:
        return bell_cache[key]
    f = midi_to_hz(midi)
    n = int((dur + 2.5) * SR)
    td = np.arange(n) / SR
    out = np.zeros(n)
    scale = (660.0 / f) ** 0.3          # higher bells ring shorter
    for ratio, g, dec in [(1.0, 1.0, 1.7), (2.0, 0.42, 2.4),
                          (2.76, 0.26, 3.6), (5.40, 0.10, 7.0)]:
        for det in (0.9994, 1.0006):
            out += g * np.sin(2 * np.pi * f * ratio * det * td + rng.uniform(0, 6)) \
                   * np.exp(-td * dec / scale)
    thunk = signal.sosfilt(signal.butter(2, [1200, 4200], "bandpass", fs=SR, output="sos"),
                           rng.standard_normal(n)) * np.exp(-td * 160)
    out = out / (np.max(np.abs(out)) + 1e-12) + 0.10 * thunk / (np.max(np.abs(thunk)) + 1e-12)
    out *= (1 - np.exp(-td / 0.002)) * np.clip((dur + 2.0 - td) / 0.6, 0, 1)
    out = signal.sosfilt(signal.butter(2, 5500, "low", fs=SR, output="sos"), out)
    bell_cache[key] = out / (np.max(np.abs(out)) + 1e-12)
    return bell_cache[key]


def light_at(b):
    return "G" if CHORD_AT[b] is GM else ("Em" if CHORD_AT[b] is Em else "?")


def place_bell_theme(notes, b0, gain, beat=0.0, count=None):
    global HOOKS
    tm = bar_t(b0, beat)
    for m, d in notes:
        pan = np.clip(0.5 + (m - 79) * 0.015, 0.32, 0.68)
        place_pan(lay_L, lay_R, bell_note(m, d * BEAT), tm, gain, pan)
        tm += d * BEAT
    VOICE_SPANS.append((bar_t(b0, beat), tm))
    if count is not None:
        HOOKS += 1
        STMT_LIGHT.append((count, light_at(int((tm - GRID0) / BAR - 0.01))))


clear()
# THE THESIS: the question phrase alone, half-voice, in the hall
place_bell_theme(ANTE, 0, 0.6)
# bell pickups — this track's seam grammar (fragments, uncounted)
for b, beat, m in [(B_INTRO - 1, 3.5, 79), (B_CH1 - 1, 3.5, 79),
                   (B_CH2 - 1, 3.5, 83)]:              # the dropout-bar pickup
    place_bell_theme([(m, 0.5)], b, 0.5, beat=beat)
# CHORUS 1 — the far light, twice, both landing home (Em)
place_bell_theme(REFRAIN, B_CH1, 0.9, count="chorus 1 stmt 1")
place_bell_theme(REFRAIN, B_CH1 + 8, 0.92, count="chorus 1 stmt 2")
# CHORUS 2 — with the octave double (brighter, bigger)
place_bell_theme(REFRAIN, B_CH2, 0.95, count="chorus 2 stmt 1")
place_bell_theme([(m + 12, d) for m, d in REFRAIN], B_CH2, 0.3)
place_bell_theme(REFRAIN, B_CH2 + 8, 0.95, count="chorus 2 stmt 2")
place_bell_theme([(m + 12, d) for m, d in REFRAIN], B_CH2 + 8, 0.3)
# THE BRIDGE: the antecedent alone, twice — the question with no answer
# (over C/D harmony: the same tune, the ground pulled away — uncounted)
place_bell_theme(ANTE, B_BR + 2, 0.7)
place_bell_theme(ANTE, B_BR + 6, 0.65)
# the pickup hanging in the silent beat
place_bell_theme([(79, 0.5)], B_FIN, 0.55, beat=0.4)
# FINAL CHORUS: statement 1 rides in on beat 2 out of the silence;
# statement 2 holds the chain through the dip; statement 3 is THE RE-LIGHT
place_bell_theme(REFRAIN_PICKUP, B_FIN, 1.0, beat=1.0, count="final stmt 1")
place_bell_theme(REFRAIN, B_FIN + 8, 0.95, count="final stmt 2 (dip)")
place_bell_theme(REFRAIN, B_FIN + 16, 1.0, count="final stmt 3 — RE-LIGHT")
place_bell_theme([(m + 12, d) for m, d in REFRAIN], B_FIN + 16, 0.35)
# THE BOOKEND: the full refrain once more, solo, KEEPING the major light,
# and a G major bell chord rings out
place_bell_theme(REFRAIN, B_BOOK, 0.75, count="bookend")
for m in (67, 71, 74, 79):
    pan = np.clip(0.5 + (m - 79) * 0.015, 0.32, 0.68)
    place_pan(lay_L, lay_R, bell_note(m, 6.0), bar_t(B_BOOK + 8), 0.6, pan)
lay_L = reverb(lay_L, IR_L, 0.5)
lay_R = reverb(lay_R, IR_R, 0.5)
commit(lay_L, lay_R, 0.24)
print(f"bell committed ({len(bell_cache)} cached)")


# ============================================================= warm lead
# THE warmth recipe, unchanged. This voice exists ONLY in the final chorus
# — the fusion is earned: before it, the bell has never had company.

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


DELAY = 0.75 * BEAT                                    # the era's dotted-8th


def place_lead(LR, b0, gain, beat=0.0, dur_beats=32):
    t0 = bar_t(b0, beat)
    L, R = LR
    add_at(lay_L, L, t0, gain)
    add_at(lay_R, R, t0, gain)
    add_at(lay_L, R, t0 + DELAY, gain * 0.26)          # ping-pong echo
    add_at(lay_R, L, t0 + DELAY, gain * 0.26)
    COUNTER_SPANS.append((t0, t0 + dur_beats * BEAT))


clear()
LEAD_COUNTER = lead_phrase(COUNTER)
place_lead(LEAD_COUNTER, B_FIN, 0.85, beat=1.0, dur_beats=31)
place_lead(LEAD_COUNTER, B_FIN + 8, 0.85)              # exposed duet in the dip
place_lead(LEAD_COUNTER, B_FIN + 16, 0.9)              # under the re-light
lay_L = reverb(lay_L, IR_L, 0.38)
lay_R = reverb(lay_R, IR_R, 0.38)
commit(lay_L, lay_R, 0.17)
print("warm lead committed (final chorus only — the fusion)")


# ============================================================= pads

def pad_chord(chord, dur, attack, release, lowpass, detune=0.0014):
    n = int(dur * SR)
    td = np.arange(n) / SR
    L = np.zeros(n)
    R = np.zeros(n)
    for m in chord:
        f = midi_to_hz(m)
        amp = 0.8 + 0.2 * np.sin(2 * np.pi * rng.uniform(0.02, 0.06) * td + rng.uniform(0, 6))
        for d, gL, gR in [(1 - detune, 1.0, 0.62), (1 + detune, 0.62, 1.0)]:
            ph = 2 * np.pi * f * d * td + rng.uniform(0, 6)
            v = (np.sin(ph) + 0.3 * np.sin(2 * ph) + 0.1 * np.sin(3 * ph)) * amp
            L += gL * v
            R += gR * v
    env = np.minimum(np.clip(td / attack, 0, 1) ** 1.3, np.clip((dur - td) / release, 0, 1))
    sos = signal.butter(2, lowpass, "low", fs=SR, output="sos")
    L = signal.sosfilt(sos, L * env)
    R = signal.sosfilt(sos, R * env)
    peak = max(np.max(np.abs(L)), np.max(np.abs(R)), 1e-12)
    return L / peak, R / peak


clear()
LP = {"thesis": 900, "intro": 950, "v1": 1000, "b1": 1200, "ch1": 1400,
      "v2": 1050, "b2": 1250, "ch2": 1450, "br": 1000, "reb": 1150,
      "fin": 1500, "dip": 1300, "wave": 1600, "out": 1200, "book": 1100}
PG = {"thesis": 0.0, "intro": 0.45, "v1": 0.55, "b1": 0.7, "ch1": 0.65,
      "v2": 0.6, "b2": 0.75, "ch2": 0.7, "br": 0.95, "reb": 0.85,
      "fin": 0.75, "dip": 0.8, "wave": 0.8, "out": 0.6, "book": 0.5}
for b in range(B_END):
    s = section_of(b)
    if PG[s] <= 0:
        continue
    beat0 = 1.0 if b == B_FIN else 0.0                 # honors the silent beat
    pL, pR = pad_chord(CHORD_AT[b][1], BAR + 2.5, attack=1.0, release=2.0,
                       lowpass=LP[s])
    add_at(lay_L, pL, bar_t(b, beat0), PG[s])
    add_at(lay_R, pR, bar_t(b, beat0), PG[s])
lay_L = reverb(lay_L, IR_L, 0.45)
lay_R = reverb(lay_R, IR_R, 0.45)
commit(lay_L, lay_R, 0.17)
print("pads committed")


# ============================================================= dark swells
# The sanctioned 1995 riser — with the agreed caution: bandlimited
# 250-2400 Hz, low commit weight, resolved by a crash. Never a wash.

clear()
def swell(b0, b1, gain=1.0):
    t0, t1 = bar_t(b0), bar_t(b1)
    n = int((t1 - t0) * SR)
    td = np.arange(n) / SR
    prog = td / (t1 - t0)
    noise = rng.standard_normal(n)
    out = np.zeros(n)
    for k in range(5):
        c = 250 * (2400 / 250) ** (k / 4)
        win = np.clip(1 - np.abs(prog - np.log(c / 250) / np.log(2400 / 250)) * 4, 0, 1)
        out += signal.sosfilt(signal.butter(2, [c * 0.8, c * 1.25], "bandpass",
                                            fs=SR, output="sos"), noise) * win
    out += 0.5 * np.sin(2 * np.pi * np.cumsum(midi_to_hz(52) * 2 ** prog) / SR)
    out *= prog ** 2
    add_at(lay_L, out / (np.max(np.abs(out)) + 1e-12), t0, gain)
    add_at(lay_R, out / (np.max(np.abs(out)) + 1e-12), t0, gain * 0.96)


swell(B_B1 + 4, B_CH1, 0.9)
swell(B_B2 + 3, B_CH2, 1.0)
swell(B_REB + 2, B_FIN, 0.9)                # ends dead at the silent beat
commit(lay_L, lay_R, 0.05)
print("dark swells committed")


# ---------------------------------------------------------------- master

fade(mix_L, fade_in=0.05, fade_out=8.0)
fade(mix_R, fade_in=0.05, fade_out=8.0)

for ch in (mix_L, mix_R):
    ch += 0.28 * signal.sosfilt(signal.butter(2, 95, "low", fs=SR, output="sos"), ch)
    ch += 0.08 * signal.sosfilt(signal.butter(2, 3200, "high", fs=SR, output="sos"), ch)

peak = max(np.max(np.abs(mix_L)), np.max(np.abs(mix_R))) + 1e-12
mix_L = np.tanh(1.3 * mix_L / peak) / np.tanh(1.3) * 0.88
mix_R = np.tanh(1.3 * mix_R / peak) / np.tanh(1.3) * 0.88

stereo = np.empty((N, 2))
stereo[:, 0] = mix_L
stereo[:, 1] = mix_R
pcm = (stereo * 32767.0).astype(np.int16)

OUT_DIR = "/workspace/music"
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, "farlight.wav")
with wave.open(OUT, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())

print(f"\nCreated: {os.path.abspath(OUT)}")
print(f"Duration: {N / SR:.1f} s  |  {SR} Hz stereo, 16-bit PCM  |  "
      f"{BPM:.0f} BPM, E natural minor, Em-D-C-D shuttle")

MP3 = os.path.join(OUT_DIR, "farlight.mp3")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", OUT,
                "-vn", "-ar", "44100", "-ac", "2", "-b:a", "192k", MP3],
               check=True)
print(f"Created: {os.path.abspath(MP3)}  (192k mp3)")

# ---------------------------------------------------------------- verify form

print("\nSection map:")
SECTIONS = [("THESIS (solo bell)", 0), ("intro", B_INTRO), ("verse 1", B_V1),
            ("build 1", B_B1), ("CHORUS 1", B_CH1), ("verse 2", B_V2),
            ("build 2", B_B2), ("CHORUS 2", B_CH2), ("bridge", B_BR),
            ("rebuild", B_REB), ("FINAL CHORUS", B_FIN), ("dip", B_DIP),
            ("final wave", B_WAVE), ("outro", B_OUT), ("BOOKEND", B_BOOK)]
for name, b in SECTIONS:
    print(f"  {bar_t(b):6.1f} s  bar {b:3d}  {name}")
print(f"  {bar_t(B_KSTOP):6.1f} s  bar {B_KSTOP}  the kick stops")
print(f"  {bar_t(B_FIN + 16, 3):6.1f} s  bar {B_FIN + 16}-{B_OUT - 1}  "
      f"THE RE-LIGHT statement (bar {B_OUT - 1} lands G major)")
print(f"  {DURATION:6.1f} s  end")

print(f"\nRefrain statements: {HOOKS}  (target >= 8; thesis/bridge "
      f"antecedent fragments uncounted)")

print("\nCadence lights (chord under each statement's final note):")
for label, light in STMT_LIGHT:
    print(f"  {label:28s} -> {light}")
relights = [light for _, light in STMT_LIGHT]

print("\nSeam checklist (what crosses every boundary):")
for b, dev in [(B_INTRO, "thesis' hang rings in the hall + bell pickup; kick enters on it"),
               (B_V1, "unbroken groove; the arp has faded up across the seam"),
               (B_B1, "unbroken groove; pads open; roll + dark swell begin inside"),
               (B_CH1, "roll + swell crest -> crash; bell pickup across the barline"),
               (B_V2, "chorus' final Em rings across + soft crash; groove unbroken"),
               (B_B2, "unbroken groove; roll begins inside"),
               (B_CH2, "one-bar DRUM DROPOUT with roll + a lone bell pickup -> crash"),
               (B_BR, "chorus' final chord + bell G5 ring across; kick exits; soft crash"),
               (B_REB, "bridge pads hold; quiet kick walks back in"),
               (B_FIN, "swell ends at the SILENT BEAT; bell pickup hangs in it; slam on beat 2"),
               (B_DIP, "refrain chain unbroken through the dip (exposed bell/lead duet)"),
               (B_WAVE, "refrain statement 2 still sounding + crash; ride enters"),
               (B_OUT, "the re-light G chord rings across the seam + soft crash"),
               (B_BOOK, "pads still ringing under the solo bell bookend")]:
    print(f"  bar {b:3d} ({bar_t(b):5.1f} s): {dev}")


def rms_between(b0, b1):
    i0 = int(bar_t(b0) * SR)
    i1 = int(bar_t(b1) * SR) if b1 is not None else N
    return np.sqrt(np.mean(mix_L[i0:i1] ** 2 + mix_R[i0:i1] ** 2) / 2)


print("\nPer-section RMS:")
R = {}
for (name, b0), (_, b1) in zip(SECTIONS, SECTIONS[1:] + [("end", None)]):
    R[name] = rms_between(b0, b1)
    print(f"  {name:20s} {R[name]:.3f}")

# duet separation: overlap of bell-refrain vs lead-countermelody activity
mask_v = np.zeros(int(DURATION * 100), dtype=bool)
mask_c = np.zeros_like(mask_v)
for spans, mask in [(VOICE_SPANS, mask_v), (COUNTER_SPANS, mask_c)]:
    for t0, t1 in spans:
        mask[int(t0 * 100):int(t1 * 100)] = True


def overlap_in(b0, b1):
    i0, i1 = int(bar_t(b0) * 100), int(bar_t(b1) * 100)
    v = mask_v[i0:i1]
    return (v & mask_c[i0:i1]).sum() / max(v.sum(), 1)


OV = {"chorus 1": overlap_in(B_CH1, B_V2), "chorus 2": overlap_in(B_CH2, B_BR),
      "final chorus": overlap_in(B_FIN, B_OUT)}
print("\nDuet separation (bell refrain / lead countermelody overlap):")
for name, r in OV.items():
    print(f"  {name}: {r:.2f}")

# diatonic audit: every melody pitch and chord tone in E natural minor
EMIN_PCS = {4, 6, 7, 9, 11, 0, 2}                      # E F# G A B C D
pcs = {m % 12 for mel in (REFRAIN, VERSE_Q, VERSE_A, COUNTER) for m, _ in mel}
for _, voicing in (Em, DM, CM, GM):
    pcs |= {m % 12 for m in voicing}
diatonic = pcs <= EMIN_PCS

print("\nBanned-list audit (by construction):")
print("  no acid: bass peak Q=1.2 blend 0.3, swept nothing")
print("  no sidechain pump: bass rolls the offbeat 16ths instead")
print("  no reverse cymbal / downsweep; no tom fills (identity separation)")
print("  no supersaw: the lead is the 3-voice warm recipe")
print("  noise swells bandlimited 250-2400 Hz, commit 0.05 (the caution)")

checks = [
    ("thesis < verse 1 < chorus 1",
     R["THESIS (solo bell)"] < R["verse 1"] < R["CHORUS 1"]),
    ("chorus 1 > build 1", R["CHORUS 1"] > R["build 1"]),
    ("chorus 2 > build 2", R["CHORUS 2"] > R["build 2"]),
    ("chorus 2 >= chorus 1", R["CHORUS 2"] >= R["CHORUS 1"]),
    ("final wave is the loudest section", R["final wave"] == max(R.values())),
    ("bridge is the trough", R["bridge"] < min(R["CHORUS 2"], R["FINAL CHORUS"])),
    ("the dip dips", R["dip"] < min(R["FINAL CHORUS"], R["final wave"])),
    ("outro settles", R["outro"] < R["final wave"]),
    ("bookend lands back near the intro", R["BOOKEND"] < R["verse 1"]),
    ("refrain count >= 8", HOOKS >= 8),
    ("exactly ONE re-light among the chorus statements, at the last",
     relights[:6] == ["Em"] * 6 and relights[6] == "G"),
    ("the bookend keeps the major light", relights[7] == "G"),
    ("choruses 1-2 trade (overlap < 0.10)",
     OV["chorus 1"] < 0.10 and OV["chorus 2"] < 0.10),
    ("the final chorus is the fusion (overlap > 0.40)",
     OV["final chorus"] > 0.40),
    ("everything E-natural-minor diatonic (no borrowed leading tone)",
     diatonic),
]
print("\nForm checks:")
ok = True
for name, passed in checks:
    print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
    ok &= passed
print("all checks passed" if ok else "SOME CHECKS FAILED")
