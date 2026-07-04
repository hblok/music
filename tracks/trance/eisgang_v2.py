#!/usr/bin/env python3
"""
eisgang_v2.py — "Eisgang" v2 (~4:55, 138 BPM, F minor). Hard
techno-trance in the CIRCLE form (design notes: eisgang_notes.md + its
v2 amendments; inspiration: W3 "stamping feet" from Vivaldi's Winter,
../../inspiration/Winter_Vivaldi.md — behaviors, none of its pitches).

v2 — two changes from eisgang.py (user feedback after listening; bass,
drums, structure and stab are UNTOUCHED — the run-and-plant bass was
the verdict's keeper):
  1. THE MELODY VOICE. The hollow-pulse glide lead read as a toy — "a
     christmas tune played on a xylophone". The skyline now speaks on
     THE SKYLINE PIANO (an M1-school synth piano, de-gothed: softer
     hammer, LP 5000, mid register, LH octaves) over THE UNDERGLOW —
     the old glide voice sunk an octave and darkened to LP 1600, quiet:
     the D-50 trick, percussive attack + breathing sustain as one
     instrument. Deeper and darker, NOT full goth.
  2. THE MELODY DEVELOPS. A piano cannot hold a two-bar stone, so the
     refrain gains development, built from two Winter MECHANISMS (the
     second sanctioned borrow — mechanisms, never pitches; see the
     notes doc): the LADDER (W5 b3-4: climb chord tones into each stone
     as a pickup — the melody arrives early, like the bass) and the
     SIGH (W5 b5-6: dip to the diatonic lower neighbor and return).
     Statements develop: chorus 1 plain stones + sighs, chorus 2 adds
     the ladder pickups (its first pickup hangs in the stripped held-V
     bar — a new seam), the final chorus adds octave dyads and answered
     sighs. Printed as the development map, checked never-decreasing.

THE STORY — Eisgang: the frozen river breaks and the ice starts moving.
Keep moving or freeze. The harmony can never sit still: it walks the
diatonic circle of fifths, verses on the near side (Fm-Bbm-Eb-Ab),
choruses all the way around (…Db-Gø-C(E natural!)-Fm) — completing the
journey IS the chorus. The one time the track stops moving (the freeze,
16 bars on the held V) is its coldest moment; the final chorus is the
biggest V->i resolution and the thaw.

THE CELL — everything phrases in two-bar hammer/oscillation pairs (the
W3 behavior): bar A hammers one pitch, bar B rocks it against the chord
root below. The bass RUNS AND PLANTS (octave bounce, land on the next
root early, then REST — a real hole every bar; duty cycle printed and
checked <= 0.6). The kick closes every cell with THE STAMP (a 4& double).
No 16th hat carpet anywhere: the top end is the tick pair, percussion
that performs the cell (hammer bars: one rim, center; oscillation bars:
two rims trading L/R).

THE REFRAIN (the skyline) — hammered ONE pitch per chord from bar 1, in
augmentation (thesis hidden in plain sight); the choruses sing the same
pitches as a connected glide line: C Db Bb C | Ab Bb G-> , hanging on G
over the V, resolved by the next section's downbeat. The verses only
ever know the first four notes. The fusion (final chorus only): lead AND
hammer stab together.

  0:00  intro      the naked cell on Fm: kick+stamp+thud-bass+stab;
                   ticks enter bar 5
  0:14  verse 1    half circle x2; +open hat, +claps on lap 2
  0:42  crossing 1 walks past Ab into Db, Gø — breaks off; tom fill ->
  0:56  CHORUS 1   full circle: the lead sings the whole skyline; E nat
                   at bar 44 pulls the loop home; last note G hangs ->
  1:23  verse 2    resolution lands on C-over-Fm; ticks echo the stab
  1:51  crossing 2 reaches C and refuses to resolve — the held V; crash ->
  2:05  CHORUS 2   full circle, lead + octave shimmer, boot toms
  2:33  the freeze the STOP, on the HELD V (C, E natural exposed): no
                   kick, no ticks; pad + pianissimo half-time hammering;
                   one heartbeat plant every 4 bars
  3:01  the thaw   bass wakes on C, ticks L then R, kick at bar 108,
                   long tom riser ->
  3:15  FINAL      the resolution V->i and the fusion: lead in octaves
                   AND the stab under it, two full laps, loudest
  4:11  ride-out   the RETROGRADE: the bass walks the circle backwards
                   (walking home the way you came); peel in reverse
  4:39  outro      the naked cell again, Fm only; the last event is one
                   run-and-plant onto a low F with the final stamp under
                   it — one boot, then nothing. Ends cold.

Era rules kept: 4/4 909 base (danceable, per review), warmth recipe on
every voice, no supersaw / no sidechain / no acid Q / no white-noise
riser. Rules deliberately broken (declared in the notes): no static
pedal (the harmony walks), no rolling 16th mono bass (duty check), no
closed-hat carpet (there is NO closed hat in this script), a functional
V-major dominant (the one borrowed note: E natural).

Everything synthesized (numpy + scipy), seeded, standalone.
Output: /workspace/music/eisgang_v2.wav + eisgang_v2.mp3 (192k).
"""

import os
import subprocess
import wave
import numpy as np
from scipy import signal

SR = 44100
DURATION = 295.5
N = int(SR * DURATION)
t = np.arange(N) / SR

rng = np.random.default_rng(1725)     # Op. 8 published

BPM = 138.0
BEAT = 60.0 / BPM
BAR = BEAT * 4
STEP = BEAT / 4                        # one 16th
GRID0 = 0.5


def bar_t(b, beat=0.0):
    return GRID0 + b * BAR + beat * BEAT


# ------------------------------------------------- section boundaries (bars)
B_V1 = 8
B_X1 = 24
B_CH1 = 32
B_V2 = 48
B_X2 = 64
B_CH2 = 72
B_FRZ = 88
B_THAW = 104
B_FIN = 112
B_RIDE = 144
B_OUT = 160
B_END = 168

SECTIONS = [("intro", 0), ("verse 1", B_V1), ("crossing 1", B_X1),
            ("CHORUS 1", B_CH1), ("verse 2", B_V2), ("crossing 2", B_X2),
            ("CHORUS 2", B_CH2), ("the freeze", B_FRZ), ("the thaw", B_THAW),
            ("FINAL CHORUS", B_FIN), ("ride-out", B_RIDE), ("outro", B_OUT)]


def section_of(b):
    for name, b0 in reversed(SECTIONS):
        if b >= b0:
            return name
    return "intro"


# --------------------------------------------------------- the circle
# Stations of the diatonic circle of fifths in F minor. Station 6 (C major)
# carries the track's single borrowed note: E natural, the V that pulls the
# loop home. One station = 2 bars = one hammer/oscillation cell.
ST_NAME = ["Fm", "Bbm", "Eb", "Ab", "Db", "G0", "C"]
ST_ROOT2 = [41, 46, 39, 44, 37, 43, 36]          # bass register (F2..C2)
SKY = [84, 85, 82, 84, 80, 82, 79]                # the skyline (stab, C5-C6)
PARTNER = [77, 77, 75, 75, 73, 73, 72]            # oscillation partners
LEAD_SKY = [72, 73, 70, 72, 68, 70, 67]           # lead, an octave below

HALF_LAP = [0, 1, 2, 3]                           # the near side
FULL_LAP = [0, 1, 2, 3, 4, 5, 6, 6]               # all the way around (V held)
RETRO_LAP = [0, 6, 5, 4, 3, 2, 1, 0]              # walking home backwards

# per-section 2-bar units; None = suspended (breakoff / the held V / freeze)
SECT_UNITS = [
    (0,      [0, 0, 0, 0]),                       # intro: home
    (B_V1,   HALF_LAP + HALF_LAP),                # verse 1
    (B_X1,   [3, 4, 5, None]),                    # crossing 1: breaks off
    (B_CH1,  FULL_LAP),                           # chorus 1
    (B_V2,   HALF_LAP + HALF_LAP),                # verse 2
    (B_X2,   [4, 5, 6, None]),                    # crossing 2: the held V
    (B_CH2,  FULL_LAP),                           # chorus 2
    (B_FRZ,  [None] * 8),                         # the freeze (harmony = C)
    (B_THAW, [6, 6, 6, 6]),                       # the thaw: cell wakes on C
    (B_FIN,  FULL_LAP + FULL_LAP),                # final chorus, two laps
    (B_RIDE, RETRO_LAP),                          # ride-out: retrograde
    (B_OUT,  [0, 0, 0, 0]),                       # outro: home
]

STATION = [None] * B_END                          # station index per bar
BARTYPE = [None] * B_END                          # 'A' hammer / 'B' osc
for b0, units in SECT_UNITS:
    for u, st in enumerate(units):
        for half, typ in ((0, "A"), (1, "B")):
            b = b0 + 2 * u + half
            if st is not None:
                STATION[b] = st
                BARTYPE[b] = typ
for b in range(B_FRZ, B_THAW):
    STATION[b] = 6                                # the freeze holds the V
for b in range(B_X2 + 6, B_CH2):
    STATION[b] = 6                                # the held V, cell suspended


def next_root2(b):
    """The root the bass plants toward (the written pickup)."""
    for bb in range(b + 1, B_END):
        if BARTYPE[bb] is not None:
            return ST_ROOT2[STATION[bb]]
    return ST_ROOT2[0]


CELL_BARS = [b for b in range(B_END) if BARTYPE[b] is not None]
CHORUS_BARS = set(range(B_CH1, B_V2)) | set(range(B_CH2, B_FRZ)) | \
    set(range(B_FIN, B_RIDE))

# ---------------------------------------------------------------- helpers


def midi_to_hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def fade(x, fade_in=0.3, fade_out=1.0):
    ni, no = int(fade_in * SR), int(fade_out * SR)
    x[:ni] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(ni) / ni)
    x[-no:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(no) / no)
    return x


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


# ---------------------------------------------------------------- drums
# 909 school, but NO closed hat exists in this script (the carpet is one of
# the declared rule breaks). Kick + THE STAMP, offbeat open hat, claps,
# crash, toms (fills + the chorus boot).

def make_kick():
    n = int(0.26 * SR)
    td = np.arange(n) / SR
    f_curve = 48.0 + 102.0 * np.exp(-td * 50.0)
    body = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    sos_c = signal.butter(2, [1500, 6000], "bandpass", fs=SR, output="sos")
    click = signal.sosfilt(sos_c, rng.standard_normal(n)) * np.exp(-td * 500)
    click /= np.max(np.abs(click)) + 1e-12
    env = (1 - np.exp(-td / 0.001)) * np.exp(-td * 10.0)
    x = (body + 0.30 * click) * env
    return x / (np.max(np.abs(x)) + 1e-12)


def make_hat_open():
    n = int(0.12 * SR)
    td = np.arange(n) / SR
    sos_h = signal.butter(4, 7000, "high", fs=SR, output="sos")
    x = signal.sosfilt(sos_h, rng.standard_normal(n)) * np.exp(-td * 28)
    return x / (np.max(np.abs(x)) + 1e-12)


def make_clap():
    n = int(0.30 * SR)
    td = np.arange(n) / SR
    sos_c = signal.butter(2, [900, 4500], "bandpass", fs=SR, output="sos")
    x = np.zeros(n)
    for i, dmp in [(0, 120.0), (1, 120.0), (2, 120.0), (3, 26.0)]:
        i0 = int(i * 0.011 * SR)
        seg = signal.sosfilt(sos_c, rng.standard_normal(n - i0))
        x[i0:] += seg * np.exp(-td[: n - i0] * dmp)
    return x / (np.max(np.abs(x)) + 1e-12)


def make_crash():
    n = int(2.0 * SR)
    td = np.arange(n) / SR
    sos_c = signal.butter(2, 5000, "high", fs=SR, output="sos")
    x = signal.sosfilt(sos_c, rng.standard_normal(n)) * np.exp(-td * 2.2)
    x *= 1 - np.exp(-td / 0.002)
    return x / (np.max(np.abs(x)) + 1e-12)


def make_tom(f0):
    n = int(0.30 * SR)
    td = np.arange(n) / SR
    f_curve = f0 * 1.6 * np.exp(-td * 9.0) + f0
    body = np.sin(2 * np.pi * np.cumsum(f_curve) / SR) * np.exp(-td * 11.0)
    skin = signal.sosfilt(signal.butter(2, [400, 2500], "bandpass", fs=SR,
                                        output="sos"),
                          rng.standard_normal(n)) * np.exp(-td * 60)
    skin /= np.max(np.abs(skin)) + 1e-12
    x = body + 0.25 * skin
    x *= 1 - np.exp(-td / 0.001)
    return x / (np.max(np.abs(x)) + 1e-12)


def make_tick(fc):
    # the tick pair: a rim/woodblock click — bandpassed snap + a tiny thump
    n = int(0.035 * SR)
    td = np.arange(n) / SR
    sos_c = signal.butter(2, [fc * 0.7, fc * 1.3], "bandpass", fs=SR,
                          output="sos")
    click = signal.sosfilt(sos_c, rng.standard_normal(n)) * np.exp(-td * 300)
    thump = 0.4 * np.sin(2 * np.pi * fc / 3 * td) * np.exp(-td * 180)
    x = click / (np.max(np.abs(click)) + 1e-12) + thump
    x *= 1 - np.exp(-td / 0.0004)
    return x / (np.max(np.abs(x)) + 1e-12)


KICK = make_kick()
STAMP_K = KICK[: int(0.15 * SR)].copy()           # the stamp: shortened kick
STAMP_K[-int(0.02 * SR):] *= np.linspace(1, 0, int(0.02 * SR))
OHAT = make_hat_open()
CLAP = make_clap()
CRASH = make_crash()
TOM_HI, TOM_MID, TOM_LO = make_tom(196.0), make_tom(147.0), make_tom(110.0)
BOOT = make_tom(85.0)                             # under the chorus stamps
TICK_A = make_tick(2500.0)                        # hammer-bar rim
TICK_B = make_tick(1800.0)                        # its oscillation partner
TICK_HI = make_tick(3400.0)                       # the final-lap descant


KICK_G = {"intro": 0.80, "verse 1": 0.90, "crossing 1": 0.95, "CHORUS 1": 1.0,
          "verse 2": 0.90, "crossing 2": 0.95, "CHORUS 2": 1.0,
          "the freeze": 0.0, "the thaw": 0.90, "FINAL CHORUS": 1.0,
          "ride-out": 0.92, "outro": 0.82}

clear()
for b in range(B_END):
    s = section_of(b)
    g = KICK_G[s]
    if s == "the thaw" and b < B_THAW + 4:
        g = 0.0                                   # kick returns at bar 108
    if g <= 0:
        continue
    beats = (0, 1) if b == B_END - 1 else (0, 1, 2, 3)   # the last bar stops
    for beat in beats:
        add_at(lay_L, KICK, bar_t(b, beat), g)
        add_at(lay_R, KICK, bar_t(b, beat), g)
    # THE STAMP: the 4& double closing every cell (every bar in choruses)
    if BARTYPE[b] == "B" or (b in CHORUS_BARS):
        if b != B_END - 1:
            add_at(lay_L, STAMP_K, bar_t(b, 3.5), g * 0.72)
            add_at(lay_R, STAMP_K, bar_t(b, 3.5), g * 0.72)
            if b in CHORUS_BARS:                  # the boot
                add_at(lay_L, BOOT, bar_t(b, 3.5), g * 0.5)
                add_at(lay_R, BOOT, bar_t(b, 3.5), g * 0.5)
# the final stamp: one boot on beat 2 of the last bar, then nothing
add_at(lay_L, STAMP_K, bar_t(B_END - 1, 2.0), 0.95)
add_at(lay_R, STAMP_K, bar_t(B_END - 1, 2.0), 0.95)
add_at(lay_L, BOOT, bar_t(B_END - 1, 2.0), 0.6)
add_at(lay_R, BOOT, bar_t(B_END - 1, 2.0), 0.6)
commit(lay_L, lay_R, 0.34)
print("kick + stamps committed")

# offbeat open hat (no closed-hat carpet exists)
clear()
OHAT_ON = [(B_V1, 30), (B_CH1, 70), (B_CH2, B_FRZ), (B_FIN, B_RIDE + 8)]
for a, z in OHAT_ON:
    for b in range(a, z):
        for beat in range(4):
            add_at(lay_L, OHAT, bar_t(b, beat + 0.5), 0.9)
            add_at(lay_R, OHAT, bar_t(b, beat + 0.5), 0.78)
commit(lay_L, lay_R, 0.055)
print("open hat committed")

# claps on 2 & 4
clear()
CLAP_ON = [(16, 30), (B_CH1, 70), (B_CH2, B_FRZ), (B_FIN, B_RIDE + 4)]
for a, z in CLAP_ON:
    for b in range(a, z):
        for beat in (1, 3):
            place_pan(lay_L, lay_R, CLAP, bar_t(b, beat), 1.0,
                      0.42 if beat == 1 else 0.58)
commit(lay_L, lay_R, 0.085)
print("claps committed")

# the tick pair — the cell made audible in percussion alone
clear()


def ticks_for_bar(b):
    s = section_of(b)
    if s in ("the freeze", "outro") or BARTYPE[b] is None:
        # breakoff bars keep ONE tick with the kick (crossing 1's gap)
        if B_X1 + 6 <= b < B_CH1:
            return [(e * 0.5, TICK_A, 0.8, 0.45) for e in range(8)]
        return []
    if s == "the thaw":                            # ticks wake L then R
        ev = [(e * 0.5, TICK_A, 0.6, 0.35) for e in range(8)]
        if b >= B_THAW + 4:
            ev += [(e * 0.5 + 0.25, TICK_B, 0.5, 0.65) for e in range(8)]
        return ev
    g = 0.7 if s == "ride-out" else 1.0
    if BARTYPE[b] == "A":                          # hammer bar: one rim
        return [(e * 0.5, TICK_A, g * (1.0 if e % 2 == 0 else 0.7), 0.45)
                for e in range(8)]
    if s == "verse 2":                             # the composed echo
        return [(e * 0.5 + 0.25, (TICK_A if e % 2 == 0 else TICK_B),
                 g * 0.8, 0.35 if e % 2 == 0 else 0.65) for e in range(8)]
    return [(e * 0.5, (TICK_A if e % 2 == 0 else TICK_B), g * 0.9,
             0.32 if e % 2 == 0 else 0.68) for e in range(8)]


for b in range(5, B_END):
    for beat, tk, g, pan in ticks_for_bar(b):
        place_pan(lay_L, lay_R, tk, bar_t(b, beat), g, pan)
# the final-lap descant: a high tick answering the lead (lap 2 only)
for b in range(B_FIN + 16, B_RIDE):
    for sx in (3, 7, 11, 15):
        place_pan(lay_L, lay_R, TICK_HI, bar_t(b, sx * 0.25), 0.45, 0.8)
commit(lay_L, lay_R, 0.05)
print("tick pair committed")

# tom fills — two seams only (crossing 1's breakoff, the thaw riser)
clear()
for beat, tom, pan in [(2.0, TOM_HI, 0.35), (2.5, TOM_HI, 0.4),
                       (3.0, TOM_MID, 0.5), (3.5, TOM_LO, 0.65)]:
    place_pan(lay_L, lay_R, tom, bar_t(B_CH1 - 1, beat),
              0.7 + 0.3 * beat / 4, pan)
for i in range(16):                                # the long thaw riser
    tom = TOM_HI if i < 6 else (TOM_MID if i < 11 else TOM_LO)
    place_pan(lay_L, lay_R, tom, bar_t(B_FIN - 2, i * 0.5),
              0.45 + 0.55 * i / 15, 0.35 + 0.3 * (i % 3) / 2)
commit(lay_L, lay_R, 0.11)
print("tom fills committed")

# crashes on the arrivals
clear()
for b, g in [(B_CH1, 0.85), (B_CH2, 1.0), (B_FRZ, 0.45), (B_FIN, 1.0),
             (B_RIDE, 0.55)]:
    place_pan(lay_L, lay_R, CRASH, bar_t(b), g, 0.5)
commit(lay_L, lay_R, 0.05)
print("crashes committed")


# ------------------------------------------------------------- thud-bass
# THE FEET — the anti-rolling bass. No saw stack: sine body + octave
# partial + a soft knock, closer to a tom than a synth. Runs (octave
# bounce, 16ths), PLANTS (lands the next root early — a written pickup),
# then RESTS. Duty cycle printed and checked <= 0.6.

bass_cache = {}
BASS_EVENTS = []                                   # (bar, slot, nslots)


def thud_bass(midi, dur, weight=1.0):
    key = (midi, int(dur * 1000))
    if key in bass_cache:
        return bass_cache[key]
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    body = np.sin(2 * np.pi * f * td) + 0.45 * np.sin(2 * np.pi * 2 * f * td +
                                                      0.7)
    knock = signal.sosfilt(signal.butter(2, [150, 800], "bandpass", fs=SR,
                                         output="sos"),
                           rng.standard_normal(n)) * np.exp(-td * 120)
    knock /= np.max(np.abs(knock)) + 1e-12
    x = body + 0.35 * knock
    env = (1 - np.exp(-td / 0.003)) * \
        (0.5 + 0.5 * np.cos(np.pi * np.clip(td / dur, 0, 1)))
    y = np.tanh(0.9 * x * env) * weight
    bass_cache[key] = y / (np.max(np.abs(y)) + 1e-12)
    return bass_cache[key]


def bass_cell(b, gain):
    st = STATION[b]
    hi, lo = ST_ROOT2[st] + 12, ST_ROOT2[st]
    for sx in range(6):                            # the run: six 16ths
        m = hi if sx % 2 == 0 else lo
        x = thud_bass(m, STEP * 0.92)
        g = gain * (0.9 if sx % 2 == 0 else 0.75)
        add_at(lay_L, x, bar_t(b, sx * 0.25), g)
        add_at(lay_R, x, bar_t(b, sx * 0.25), g)
        BASS_EVENTS.append((b, sx, 1))
    if BARTYPE[b] == "A":                          # plant on beat 3, own root
        x = thud_bass(lo, 0.32)
        add_at(lay_L, x, bar_t(b, 2.0), gain)
        add_at(lay_R, x, bar_t(b, 2.0), gain)
        BASS_EVENTS.append((b, 8, 3))
    else:                                          # plant on beat 4: the
        x = thud_bass(next_root2(b), 0.32)         # PICKUP onto the next root
        add_at(lay_L, x, bar_t(b, 3.0), gain * 1.05)
        add_at(lay_R, x, bar_t(b, 3.0), gain * 1.05)
        BASS_EVENTS.append((b, 12, 3))


clear()
BASS_G = {"intro": 0.85, "verse 1": 0.88, "crossing 1": 0.9, "CHORUS 1": 0.92,
          "verse 2": 0.88, "crossing 2": 0.9, "CHORUS 2": 0.95,
          "the thaw": 0.8, "FINAL CHORUS": 1.0, "ride-out": 0.9,
          "outro": 0.82}
for b in CELL_BARS:
    if b == B_END - 1:
        continue                                   # the last bar is special
    s = section_of(b)
    g = BASS_G[s]
    if s == "the thaw":
        g *= 0.75 + 0.25 * (b - B_THAW) / 8        # waking up
    bass_cell(b, g)
# the freeze: one heartbeat plant every 4 bars (C, long, soft)
for b in range(B_FRZ, B_THAW, 4):
    x = thud_bass(36, 0.8)
    add_at(lay_L, x, bar_t(b), 0.5)
    add_at(lay_R, x, bar_t(b), 0.5)
# the last bar: the run, then ONE plant onto a low F under the final stamp
for sx in range(6):
    m = 53 if sx % 2 == 0 else 41
    x = thud_bass(m, STEP * 0.92)
    add_at(lay_L, x, bar_t(B_END - 1, sx * 0.25), 0.85)
    add_at(lay_R, x, bar_t(B_END - 1, sx * 0.25), 0.85)
    BASS_EVENTS.append((B_END - 1, sx, 1))
x = thud_bass(29, 0.9)                             # F1: the landing
add_at(lay_L, x, bar_t(B_END - 1, 2.0), 1.1)
add_at(lay_R, x, bar_t(B_END - 1, 2.0), 1.1)
BASS_EVENTS.append((B_END - 1, 8, 4))
commit(lay_L, lay_R, 0.30)
print(f"thud-bass committed ({len(bass_cache)} cached)")


# ------------------------------------------------------- the hammer stab
# THE COLD — W3's behavior voice. Hollow pulse-wave pluck (odd harmonics —
# a new timbre family here; the saws belong to the other tracks), gated
# 16th retrigger with a per-16th gain cell so it chatters, dry-ish and
# close. Hammer bars: the skyline pitch. Oscillation bars: skyline vs the
# chord root below, on 8ths.

stab_cache = {}


def stab_hit(midi, dur=0.20):
    if midi in stab_cache:
        return stab_cache[midi]
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    k = 1
    while k * f < 5200:
        x += np.sin(2 * np.pi * k * f * td) / k ** 1.25
        k += 2                                     # odd only: hollow
    x += 0.28 * np.sin(2 * np.pi * f * td)
    y = signal.sosfilt(signal.butter(2, 2000, "low", fs=SR, output="sos"), x)
    y = np.tanh(0.85 * y)
    y *= (1 - np.exp(-td / 0.0015)) * np.exp(-td * 15.0)
    stab_cache[midi] = y / (np.max(np.abs(y)) + 1e-12)
    return stab_cache[midi]


G_CELL = [1.0, 0.45, 0.7, 0.0]                     # the chatter (a hole/beat)
STAB_G = {"intro": 0.5, "verse 1": 0.8, "crossing 1": 0.85, "CHORUS 1": 0.0,
          "verse 2": 0.8, "crossing 2": 0.85, "CHORUS 2": 0.0,
          "the thaw": 0.55, "FINAL CHORUS": 0.85, "ride-out": 0.75,
          "outro": 0.4}
STAB_HAMMER_BARS = []

clear()
for b in CELL_BARS:
    s = section_of(b)
    g = STAB_G[s]
    if g <= 0:
        continue
    if s == "outro" and b >= B_END - 2:
        continue                                   # the naked ending
    st = STATION[b]
    if BARTYPE[b] == "A":
        STAB_HAMMER_BARS.append(b)
        for sx in range(16):
            gc = G_CELL[sx % 4]
            if gc == 0.0:
                continue
            x = stab_hit(SKY[st])
            place_pan(lay_L, lay_R, x, bar_t(b, sx * 0.25), g * gc, 0.5)
    else:
        for e in range(8):
            m = SKY[st] if e % 2 == 0 else PARTNER[st]
            x = stab_hit(m)
            place_pan(lay_L, lay_R, x, bar_t(b, e * 0.5),
                      g * (0.95 if e % 2 == 0 else 0.72),
                      0.44 if e % 2 == 0 else 0.56)
# the freeze: pianissimo half-time hammering of the half-skyline over the
# held V — Db over C is the track's coldest interval (a written flat 9)
FRZ_SKY = [84, 85, 82, 84]
for b in range(B_FRZ, B_THAW):
    m = FRZ_SKY[(b - B_FRZ) // 4]
    for e in range(8):
        x = stab_hit(m)
        place_pan(lay_L, lay_R, x, bar_t(b, e * 0.5),
                  0.22 * (1.0 if e % 2 == 0 else 0.7), 0.5)
lay_L = reverb(lay_L, IR_L, 0.18)
lay_R = reverb(lay_R, IR_R, 0.18)
commit(lay_L, lay_R, 0.17)
print(f"hammer stab committed ({len(stab_cache)} pitches cached)")


# ------------------------------------- the skyline piano + the underglow
# THE WARM, re-voiced for v2 — chorus-only. The stones (the same seven
# skyline pitches) now spoken by an M1-school synth piano (source:
# nachtkind_v3.py:piano_note per instruments/README.md, de-gothed:
# softer/lower hammer, LP 5000, mid register, LH octaves), with the v1
# glide voice surviving as THE UNDERGLOW: an octave down, LP 1600,
# quiet — the sustain under the piano's attack (and it still carries
# the hanging G across the held V). The refrain develops by two Winter
# mechanisms — the LADDER pickup and the SIGH (mechanisms, not pitches).

LEAD_NOTES = [(72, 8), (73, 8), (70, 8), (72, 8), (68, 8), (70, 8), (67, 16)]
LEAD_STMTS = []
STMT_LEVELS = []

# per station: the ladder into its stone (triad tones + the leading step,
# Vivaldi's 8th+16th+16th lilt) and the stone's diatonic lower neighbor
LADDER = [[65, 68, 70], [65, 70, 72], [63, 67, 68], [63, 68, 70],
          [61, 65, 67], [61, 67, 68], [60, 64, 65]]
SIGH_LN = [70, 72, 68, 70, 67, 68, 65]

piano_cache = {}


def piano_note(midi, dur):
    key = (midi, round(dur, 2))
    if key in piano_cache:
        return piano_cache[key]
    f = midi_to_hz(midi)
    n = int((dur + 1.2) * SR)
    td = np.arange(n) / SR
    out = np.zeros(n)
    B_inh = 0.00032                                # gentle string stretch
    for k in range(1, min(16, int(8000 / f)) + 1):
        fk = f * k * np.sqrt(1 + B_inh * k * k)
        dec = 0.9 + 0.45 * k + f * 0.0012
        g = 1.0 / k ** 1.25
        for det in (0.9994, 1.0006):               # two strings
            out += g * np.sin(2 * np.pi * fk * det * td +
                              rng.uniform(0, 2 * np.pi)) * np.exp(-td * dec)
    sos_h = signal.butter(2, [1200, 3600], "bandpass", fs=SR, output="sos")
    hammer = signal.sosfilt(sos_h, rng.standard_normal(n)) * np.exp(-td * 350)
    hammer /= np.max(np.abs(hammer)) + 1e-12
    out += 0.14 * hammer                           # soft thunk, not gothic
    env = (1 - np.exp(-td / 0.0015)) * np.clip((dur + 0.5 - td) / 0.5, 0, 1)
    x = np.tanh(0.9 * out * env)
    x = signal.sosfilt(signal.butter(2, 5000, "low", fs=SR, output="sos"), x)
    piano_cache[key] = x / (np.max(np.abs(x)) + 1e-12)
    return piano_cache[key]


def pno(midi, b, beat, dur_beats, gain):
    x = piano_note(midi, dur_beats * BEAT)
    p = float(np.clip(0.5 + (midi - 70) * 0.012, 0.3, 0.7))
    place_pan(lay_L, lay_R, x, bar_t(b, beat), gain, p)


def ladder_pickup(b, st, gain):
    # the climb into the next stone: last beat of the bar, 8th + two 16ths
    for m, beat, dur in zip(LADDER[st], (3.0, 3.5, 3.75), (0.5, 0.25, 0.25)):
        pno(m, b, beat, dur, gain)


def skyline_piano(b0, level, gain=1.0):
    """One statement over a chorus lap. Levels: 1 = the stones + sighs
    (plain); 2 = + ladder pickups into every stone (the first hangs in
    the bar BEFORE the chorus — a seam); 3 = + octave dyads and the
    answered sigh an octave above."""
    if level >= 2:
        ladder_pickup(b0 - 1, FULL_LAP[0], gain * 0.6)
    for u in range(8):
        st = FULL_LAP[u]
        S = LEAD_SKY[st]
        b = b0 + 2 * u
        if u == 7:                                  # the hang: fading sighs
            for i, g in ((0, 0.7), (1, 0.5)):
                pno(S, b + i, 0.0, 0.5, gain * g)
                pno(SIGH_LN[st], b + i, 0.5, 0.25, gain * g * 0.8)
                pno(S, b + i, 0.75, 1.5, gain * g)
            continue
        # bar 1: the stone, LH octave under it (dyad above at level 3)
        pno(S, b, 0.0, 3.2, gain)
        pno(S - 12, b, 0.0, 3.2, gain * 0.7)
        if level >= 3:
            pno(S + 12, b, 0.0, 3.2, gain * 0.5)
        # bar 2: the sigh (dip to the lower neighbor and return)
        pno(S, b + 1, 0.0, 0.5, gain * 0.9)
        pno(SIGH_LN[st], b + 1, 0.5, 0.25, gain * 0.75)
        pno(S, b + 1, 0.75, 1.6, gain * 0.9)
        if level >= 3:                              # the answered sigh
            pno(S + 12, b + 1, 2.0, 0.4, gain * 0.45)
            pno(SIGH_LN[st] + 12, b + 1, 2.5, 0.25, gain * 0.38)
            pno(S + 12, b + 1, 2.75, 1.0, gain * 0.45)
        if level >= 2 and u < 6:                    # climb to the next stone
            ladder_pickup(b + 1, FULL_LAP[u + 1], gain * 0.6)
    LEAD_STMTS.append(b0)
    STMT_LEVELS.append(level)


def lead_line(notes, transpose=0, lowpass=2600):
    total = sum(d for _, d in notes) * BEAT
    n = int((total + 2.0) * SR)
    tt = np.arange(n) / SR
    f = glide_curve([(m + transpose, d * BEAT) for m, d in notes], n, tau=0.07)
    vib = 1.0 + 0.0035 * np.sin(2 * np.pi * 5.5 * tt) * \
        np.clip(tt / 0.6, 0, 1)
    ph_base = 2 * np.pi * np.cumsum(f * vib) / SR
    L = np.zeros(n)
    R = np.zeros(n)
    for det, gL, gR in [(0.997, 1.0, 0.6), (1.003, 0.6, 1.0)]:
        K = max(3, int(2600 / np.min(f)))
        v = np.zeros(n)
        for k in range(1, K + 1, 2):               # odd: the hollow core
            v += np.sin(k * ph_base * det) / k ** 1.3
        v += 0.30 * np.sin(ph_base * det)
        L += gL * v
        R += gR * v
    atk = 0.5 - 0.5 * np.cos(np.pi * np.clip(tt / 0.15, 0, 1))
    env = np.minimum(atk, np.clip((total + 0.4 - tt) / 1.2, 0, 1))
    sos = signal.butter(2, lowpass, "low", fs=SR, output="sos")
    L = signal.sosfilt(sos, np.tanh(0.8 * L) * env)
    R = signal.sosfilt(sos, np.tanh(0.8 * R) * env)
    peak = max(np.max(np.abs(L)), np.max(np.abs(R)), 1e-12)
    return L / peak, R / peak


clear()
UNDERGLOW = lead_line(LEAD_NOTES, transpose=-12, lowpass=1600)


def place_statement(b0, level, gain=1.0, glow=0.5):
    add_at(lay_L, UNDERGLOW[0], bar_t(b0), glow)
    add_at(lay_R, UNDERGLOW[1], bar_t(b0), glow)
    skyline_piano(b0, level, gain)


place_statement(B_CH1, 1, 0.9)                     # state: stones + sighs
place_statement(B_CH2, 2, 0.95)                    # vary: + the ladders
place_statement(B_FIN, 3, 1.0, glow=0.55)          # the fusion, lap 1
place_statement(B_FIN + 16, 3, 1.0, glow=0.55)     # the fusion, lap 2
lay_L = reverb(lay_L, IR_L, 0.5)
lay_R = reverb(lay_R, IR_R, 0.5)
commit(lay_L, lay_R, 0.27)
print(f"skyline piano + underglow committed "
      f"({len(piano_cache)} piano notes cached)")


# ------------------------------------------------------------- dark pad
# The held V made audible: C major with the E natural exposed. Crossing 2's
# refusal, then the whole freeze. Dark sine pad, nothing else moves.

def pad_chord(chord, dur, attack=1.8, release=2.2):
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
    sos = signal.butter(2, 850, "low", fs=SR, output="sos")
    L = signal.sosfilt(sos, L * env)
    R = signal.sosfilt(sos, R * env)
    peak = max(np.max(np.abs(L)), np.max(np.abs(R)), 1e-12)
    return L / peak, R / peak


C_HELD = (48, 55, 64, 67)                          # C3 G3 E4 G4 — E exposed
clear()
pL, pR = pad_chord(C_HELD, 4 * BAR + 2.0)          # crossing 2: the refusal
add_at(lay_L, pL, bar_t(B_X2 + 4), 0.8)
add_at(lay_R, pR, bar_t(B_X2 + 4), 0.8)
for b in range(B_FRZ, B_THAW, 4):                  # the freeze
    pL, pR = pad_chord(C_HELD, 4 * BAR + 2.0)
    add_at(lay_L, pL, bar_t(b), 0.95)
    add_at(lay_R, pR, bar_t(b), 0.95)
pL, pR = pad_chord(C_HELD, 4 * BAR + 1.0, release=3.5)   # fading into the thaw
add_at(lay_L, pL, bar_t(B_THAW), 0.55)
add_at(lay_R, pR, bar_t(B_THAW), 0.55)
lay_L = reverb(lay_L, IR_L, 0.5)
lay_R = reverb(lay_R, IR_R, 0.5)
commit(lay_L, lay_R, 0.11)
print("pad committed")


# ------------------------------------------------------------------ air
# Cold air: the intro's edge, the freeze (the coldest place), the outro.

sos_air = signal.butter(4, [150, 1100], "bandpass", fs=SR, output="sos")
air = signal.sosfilt(sos_air, rng.standard_normal(N))
air /= np.max(np.abs(air))
env_air = (np.clip((bar_t(B_V1) - t) / 10.0, 0, 1) * 0.7 +
           np.clip((t - bar_t(B_FRZ)) / 4.0, 0, 1) *
           np.clip((bar_t(B_THAW + 2) - t) / 4.0, 0, 1) +
           np.clip((t - bar_t(B_OUT)) / 10.0, 0, 1) * 0.8 *
           np.clip((bar_t(B_END - 1, 1.5) - t) / 2.5, 0, 1))  # dies before
                                                              # the stamp
env_air = np.clip(env_air, 0, 1)
commit(air * env_air, air[::-1] * env_air, 0.035)
print("air committed")


# ---------------------------------------------------------------- master
# Era master: peak-normalized with headroom, no compression. Ends COLD:
# the fade exists only to kill residue, the last event is the stamp.

fade(mix_L, fade_in=0.3, fade_out=1.0)
fade(mix_R, fade_in=0.3, fade_out=1.0)

peak = max(np.max(np.abs(mix_L)), np.max(np.abs(mix_R)))
mix_L = mix_L / peak * 0.86
mix_R = mix_R / peak * 0.86

stereo = np.empty((N, 2))
stereo[:, 0] = mix_L
stereo[:, 1] = mix_R
pcm = (stereo * 32767.0).astype(np.int16)

OUT_DIR = "/workspace/music"
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, "eisgang_v2.wav")
with wave.open(OUT, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())

print(f"\nCreated: {os.path.abspath(OUT)}")
print(f"Duration: {N / SR:.1f} s  |  {SR} Hz stereo, 16-bit PCM  |  "
      f"{BPM:.0f} BPM, F minor, the circle of fifths")

MP3 = os.path.join(OUT_DIR, "eisgang_v2.mp3")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", OUT,
                "-vn", "-ar", "44100", "-ac", "2", "-b:a", "192k", MP3],
               check=True)
print(f"Created: {os.path.abspath(MP3)}  (192k mp3)")

# ------------------------------------------------------------ verify form
# The circle variant (see ../VERIFY.md and eisgang_notes.md).

print("\nSection map:")
for name, b in SECTIONS:
    print(f"  {bar_t(b):6.1f} s  bar {b:3d}  {name}")
print(f"  {bar_t(B_END - 1, 2.0):6.1f} s  bar {B_END - 1}  the final stamp "
      f"(one boot, then nothing)")

print("\nThe harmonic odometer (station at each boundary, and the walk):")
for (name, b0), (_, b1) in zip(SECTIONS, SECTIONS[1:] + [("end", B_END)]):
    sts = []
    for b in range(b0, b1):
        st = STATION[b]
        nm = ST_NAME[st] if st is not None else "--"
        if not sts or sts[-1] != nm:
            sts.append(nm)
    print(f"  bar {b0:3d}  {name:14s} {' '.join(sts)}")

verse_sts = [STATION[b] for b in list(range(B_V1, B_X1)) +
             list(range(B_V2, B_X2)) if STATION[b] is not None]
g0_bars = [b for b in range(B_END) if STATION[b] == 5]
g0_ok = all(B_X1 <= b < B_V2 or B_X2 <= b < B_FRZ or B_FIN <= b < B_OUT
            for b in g0_bars)
lap_ok = all([STATION[b0 + 2 * u] for u in range(8)] == FULL_LAP
             for b0 in (B_CH1, B_CH2, B_FIN, B_FIN + 16))
retro_ok = [STATION[B_RIDE + 2 * u] for u in range(8)] == RETRO_LAP

print("\nThe cell map (A=hammer, B=oscillation, .=suspended):")
for name, b0 in SECTIONS:
    b1 = dict(zip([n for n, _ in SECTIONS] + ["end"],
                  [b for _, b in SECTIONS][1:] + [B_END]))[name]
    row = "".join(BARTYPE[b] if BARTYPE[b] else "." for b in range(b0, b1))
    print(f"  {name:14s} {row}")
cell_ok = all(BARTYPE[b] == ("A" if (b - CELL_START) % 2 == 0 else "B")
              for b0, units in SECT_UNITS
              for CELL_START in [b0]
              for b in range(b0, b0 + 2 * len(units))
              if BARTYPE[b] is not None)
frz_ok = all(BARTYPE[b] is None for b in range(B_FRZ, B_THAW))

occ = {}
for b, slot, ns in BASS_EVENTS:
    occ.setdefault(b, set()).update(range(slot, min(16, slot + ns)))
duties = [len(occ.get(b, ())) / 16.0 for b in CELL_BARS]
duty_avg = float(np.mean(duties))
duty_max = float(np.max(duties))
rest_min = min(16 - len(occ.get(b, ())) for b in CELL_BARS)
print(f"\nBass duty cycle: avg {duty_avg:.3f}, max {duty_max:.3f} "
      f"(rolling bass = 1.0; the contract: avg <= 0.6). "
      f"Min rest slots/bar: {rest_min}")

ham_cov = 100.0 * len(STAB_HAMMER_BARS) / len([b for b in CELL_BARS
                                               if BARTYPE[b] == "A"])
print(f"Skyline: piano statements {len(LEAD_STMTS)} at bars {LEAD_STMTS} "
      f"(target >= 4); stab hammer-bar coverage {ham_cov:.0f}% of A bars "
      f"(the augmented refrain)")
LVL_DESC = {1: "stones + sighs", 2: "+ ladder pickups",
            3: "+ dyads & answered sighs"}
print("Statement development map: " +
      ", ".join(f"bar {b}: L{lv} ({LVL_DESC[lv]})"
                for b, lv in zip(LEAD_STMTS, STMT_LEVELS)))
fusion_bars = [b for b in STAB_HAMMER_BARS if B_FIN <= b < B_RIDE]
print(f"The fusion: stab + lead overlap only in the final chorus "
      f"({len(fusion_bars)} shared hammer bars; choruses 1-2 have zero)")

print("\nSeam checklist (what crosses every boundary):")
for b, dev in [
        (B_V1, "the cell unbroken; the bass pickup plants verse 1's root"),
        (B_X1, "the walk simply continues past Ab — the seam IS the harmony"),
        (B_CH1, "the breakoff gap + tom fill + crash; pickup plant onto Fm"),
        (B_V2, "the hanging G resolves to C-over-Fm across the barline"),
        (B_X2, "the walk heads out again (Db); claps/hat continue"),
        (B_CH2, "the held V refuses, then resolves; crash"),
        (B_FRZ, "chorus 2's hanging V BECOMES the freeze (same chord); "
                "soft crash"),
        (B_THAW, "the pad sustains; the bass wakes on the same C"),
        (B_FIN, "the long tom riser + crash; V->i, the track's one big "
                "resolution"),
        (B_RIDE, "the hanging G resolves into the retrograde's home Fm"),
        (B_OUT, "the retrograde arrives home; the cell just keeps walking"),
        (B_END, "the final stamp on beat 2 — one boot, then nothing")]:
    print(f"  bar {b:3d} ({bar_t(b):5.1f} s): {dev}")


def rms_between(b0, b1):
    i0 = int(bar_t(b0) * SR)
    i1 = int(bar_t(b1) * SR) if b1 is not None else N
    return np.sqrt(np.mean(mix_L[i0:i1] ** 2 + mix_R[i0:i1] ** 2) / 2)


print("\nPer-section RMS:")
R = {}
for (name, b0), (_, b1) in zip(SECTIONS, SECTIONS[1:] + [("end", None)]):
    R[name] = rms_between(b0, b1)
    print(f"  {name:14s} {R[name]:.3f}")

i0 = int((DURATION - 1.5) * SR)
end_rms = np.sqrt(np.mean(mix_L[i0:] ** 2 + mix_R[i0:] ** 2) / 2)

checks = [
    ("intro < verse 1 < CHORUS 1",
     R["intro"] < R["verse 1"] < R["CHORUS 1"]),
    ("CHORUS 1 > crossing 1 (the drop lands)",
     R["CHORUS 1"] > R["crossing 1"]),
    ("CHORUS 2 >= CHORUS 1", R["CHORUS 2"] >= R["CHORUS 1"]),
    ("FINAL CHORUS is the loudest section",
     R["FINAL CHORUS"] == max(R.values())),
    ("the freeze is the global trough", R["the freeze"] == min(R.values())),
    ("the outro settles below verse 1", R["outro"] < R["verse 1"]),
    ("skyline sung statements >= 4", len(LEAD_STMTS) >= 4),
    ("the refrain develops (statement levels never decrease)",
     STMT_LEVELS == sorted(STMT_LEVELS) and STMT_LEVELS[-1] > STMT_LEVELS[0]),
    ("bass duty cycle <= 0.6 (not a rolling bass)", duty_avg <= 0.6),
    ("every cell bar has a bass rest", rest_min >= 1),
    ("odometer: verses never pass station 4 (Ab)", max(verse_sts) <= 3),
    ("odometer: Gø only in crossings/choruses/ride-out", g0_ok),
    ("odometer: every chorus lap completes the full circle", lap_ok),
    ("odometer: the freeze holds the V (C)",
     all(STATION[b] == 6 for b in range(B_FRZ, B_THAW))),
    ("odometer: the ride-out is the exact retrograde", retro_ok),
    ("cell integrity: A/B alternation in all cell bars", cell_ok),
    ("cell integrity: suspended through the freeze", frz_ok),
    ("ends cold (last 1.5 s is silence)", end_rms < 0.005),
]
print("\nForm checks:")
ok = True
for name, passed in checks:
    print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
    ok &= passed
print("banned by construction: 16th hat carpet (no closed hat exists) / "
      "rolling bass (duty-checked) / supersaw / sidechain / acid Q / "
      "white-noise riser")
print("all checks passed" if ok else "SOME CHECKS FAILED")
