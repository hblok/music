#!/usr/bin/env python3
"""
lost_v6.py — "Lost (Trance)" (~5:30, 130 BPM). The emotional-trance journey
— love, confusion, loss, dread, sadness, hope — retold as a SONG (design
notes: lost_v6_notes.md). v4 had the cohesion trinity (one chord loop, one
theme, one instrument set); v6 adds the song doctrine from the dune songbook:
a refrain with a fixed identity, question/answer at every level, a seam
device at every boundary, the thesis stated in the first ten seconds.

THE CONCEPT — one refrain, three lights. The refrain melody is IDENTICAL in
every chorus; the emotion comes entirely from how the harmony lights it.
Bm-G-D-A shares all seven notes between D major and B minor, so the same
4-chord loop is entered at three rotation points:

    ROT_Q  Bm G D A   ends on the V  — open, asking   (verses, breaks)
    ROT_D  A Bm G D   ends on D      — bright landing (LOVE / HOPE / fusion)
    ROT_B  G D A Bm   ends on Bm     — sad landing    (DREAD)

The refrain's final note is D: over the D chord it is home (bright); over
the Bm chord the very same note is the minor third (sad). Same tune,
different light. The refrain itself is a Q/A cell — 2-bar question rising
to hang on A (the V, alive over every rotation), 2-bar answer with the same
rhythm reaching higher and falling home through C# to D.

  0:00  THESIS       Solo piano states the refrain once, half-voice, wet;
                     the last chord rings under the kick entry.
  0:08  verse 1      Groove assembles fast; the lead sings low Q/A verse
                     pairs, piano echoing each phrase tail (composed echo).
  0:37  pre-chorus   1-bar trades lead/piano rising together; roll + riser.
  0:52  CHORUS 1 — LOVE    The refrain, bright D cadences. Statement 3 is
                     sung by the piano (the performer answer), lead returns.
  1:22  verse 2 — CONFUSION (24 bars)  Piano leads, lead echoes; the D chord
                     flickers minor and a borrowed Bb pulls the answer down
                     to land on Bb — the tune losing its footing; phrases
                     shoved off the beat.
  2:06  LOSS (break) Beat drops dead (downsweep). Piano asks the refrain's
                     question, cello answers, bare; the heartbeat; build.
  2:36  CHORUS 2 — DREAD (24 bars)  The refrain IDENTICAL but landing on Bm:
                     the cathartic sad climax — lead soaring, cello an octave
                     below, big minor pads, driving warm beat. Mid-drop dip
                     at 2:50, then the fullest wave with ride.
  3:20  SADNESS (break)  The most broken fragment on solo piano, cello
                     answering; layers to near-nothing; rebuild — quiet kick
                     walks in, roll + riser → ONE BEAT of near-silence, a
                     lone piano pickup hanging in it —
  3:49  CHORUS 3 — HOPE   The full band slams in on beat 2; refrain back in
                     the bright light, glittering octave plucks.
  4:19  CHORUS 4 — fusion The everything-chorus: refrain on the lead with
                     the VERSE MELODY as a cello counter-line under it (the
                     question sounding with its answer), ride, glitter.
                     The last statement stretches ritardando across the seam.
  4:48  outro        Deconstruction; the kick stops at 5:03; solo piano
                     bookends the refrain once more, a final chord rings out.

No new timbres, no acid, no vocals: the v4 five (warm lead, glassy pluck,
pads, piano, cello) + the dry kit and the warmed rolling octave bass.
Dread is SADNESS, not horror. Everything synthesized (numpy + scipy).
Output: /workspace/music/lost_v6.wav + lost_v6.mp3 (192k, ffmpeg).
"""

"""
How the "one refrain, three lights" concept landed in the implementation:

    The light is literally a rotation. One loop (Bm–G–D–A) entered at three points: verses/breaks use the rotation ending on A (the open question), LOVE/HOPE/fusion end the cell on D, DREAD ends it on Bm. The refrain's final melody note is always D — root of the D chord in the bright choruses, minor third of Bm in the dread. Not a single note of the tune changes between choruses; 19 refrain statements total, all identical (plus the ritardando tail on the last fusion statement).
    Q/A at the three levels from the notes: the refrain is itself a question hanging on A answered through C#→D; the piano echoes the lead's verse tails and takes over statement 3 of chorus 1; piano asks / cello answers bare over the heartbeat in LOSS; and the fusion chorus puts the verse melody (the question voice) on cello under the refrain.
    CONFUSION as "the tune losing its footing": piano leads the verse melody, but in the flicker cells the third flattens (F#→F over Dm), the answer phrase slides down to land on Bb instead of D, phrases get shoved a half-beat late, and the arp runs backwards.
    Seams: every boundary is crossed by something (printed as a checklist); the one true drop-silence beat before HOPE measured 0.048 RMS against 0.28/0.31 around it, with the lone piano pickup hanging in it and the slam on beat 2.

Two balance iterations were needed: the dread wave initially out-loudened the fusion chorus (0.33 vs 0.30). Pumping chorus 4 harder mostly self-defeated because commit() peak-normalizes each layer, so the fix was giving the fusion the deeper sustained sub (0.85 vs dread's 0.62 — it feeds the 95 Hz shelf) plus the octave shimmer, while thinning the dread's hats slightly. Final ordering: fusion 0.332 > dread wave 0.327 > chorus 1 0.301, breaks at ~0.10.

Ready for a listen. If the dread no longer feels like enough of a climax after the trim, the sub split (0.62/0.85) is the knob to revisit.
"""

import os
import subprocess
import wave
import numpy as np
from scipy import signal

SR = 44100
DURATION = 332.0
N = int(SR * DURATION)
t = np.arange(N) / SR

rng = np.random.default_rng(130)

BPM = 130.0
BEAT = 60.0 / BPM
BAR = BEAT * 4
STEP = BEAT / 4
GRID0 = 0.5


def bar_t(b, beat=0.0):
    return GRID0 + b * BAR + beat * BEAT


# ----------------------------------------------------- section boundaries (bars)
B_V1 = 4          # verse 1: groove assembles, lead verse pairs
B_PRE = 20        # pre-chorus trades + rise
B_CH1 = 28        # CHORUS 1 — LOVE (bright light)
B_CONF = 44       # verse 2 — CONFUSION (24 bars)
B_LOSS = 68       # LOSS breakdown (piano asks / cello answers, heartbeat)
B_DREAD = 84      # CHORUS 2 — DREAD (sad light)
B_DIP = 92        # mid-drop dip
B_DREAD2 = 96     # dread fullest wave (+ ride)
B_SAD = 108       # SADNESS breakdown
B_REBUILD = 116   # rebuild: quiet kick, roll, riser
B_HOPE = 124      # CHORUS 3 — HOPE (slams on beat 2 after the silent beat)
B_CH4 = 140       # CHORUS 4 — the fusion
B_OUT = 156       # outro deconstruction
B_KSTOP = 164     # the kick stops
B_BOOK = 165      # solo piano bookend
B_END = 172


def section_of(b):
    if b < B_V1:
        return "thesis"
    if b < B_PRE:
        return "v1"
    if b < B_CH1:
        return "pre"
    if b < B_CONF:
        return "ch1"
    if b < B_LOSS:
        return "conf"
    if b < B_DREAD:
        return "loss"
    if b < B_DIP:
        return "dread"
    if b < B_DREAD2:
        return "dip"
    if b < B_SAD:
        return "dread2"
    if b < B_REBUILD:
        return "sad"
    if b < B_HOPE:
        return "rebuild"
    if b < B_CH4:
        return "hope"
    if b < B_OUT:
        return "ch4"
    return "out"


# ---------------------------------------------------------------- helpers

def midi_to_hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def fade(x, fade_in=0.4, fade_out=10.0):
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
# ONE loop for the whole track — Bm G D A (vi-IV-I-V), one bar per chord —
# entered at three rotation points. The rotation IS the emotional light:
# which chord the 4-bar refrain cell lands on.
# chord = (bass_root_midi, mid-register voicing for pads/pluck)

Bm = (35, (54, 59, 62, 66))     # B  D  F#
G = (31, (50, 55, 59, 62))      # G  B  D
DM = (38, (54, 57, 62, 66))     # D  F# A
AM = (33, (52, 57, 61, 64))     # A  C# E
Dm = (38, (53, 57, 62, 65))     # D  F  A   (the confusion flicker)
Bb = (34, (53, 58, 62, 65))     # Bb D  F   (borrowed, destabiliser)

ROT_Q = [Bm, G, DM, AM]          # ends on the V — the question rotation
ROT_D = [AM, Bm, G, DM]          # cell lands on D — bright (LOVE/HOPE)
ROT_B = [G, DM, AM, Bm]          # cell lands on Bm — sad (DREAD)
FLICK = [Bm, G, Dm, Bb]          # confusion cells: D goes minor, Bb pulls down

CHORD_AT = [Bm] * B_END


def fill(b0, b1, seq, bars_each=1):
    i, b = 0, b0
    while b < b1:
        for _ in range(bars_each):
            if b < b1:
                CHORD_AT[b] = seq[i % len(seq)]
                b += 1
        i += 1


fill(0, B_V1, ROT_D)                 # thesis carries the chorus light
fill(B_V1, B_CH1, ROT_Q)             # verse 1 + pre-chorus ask
fill(B_CH1, B_CONF, ROT_D)           # LOVE
fill(B_CONF, B_CONF + 8, ROT_Q)      # confusion: footing still firm...
fill(B_CONF + 8, B_CONF + 20, FLICK)  # ...then the flicker cells
fill(B_CONF + 20, B_LOSS, ROT_Q)     # ...and a failed return
fill(B_LOSS, B_DREAD, ROT_Q, 2)      # LOSS: half-speed harmony, asking
fill(B_DREAD, B_SAD, ROT_B)          # DREAD: the sad light
fill(B_SAD, B_HOPE, ROT_Q, 2)        # SADNESS: asking again, slow
fill(B_HOPE, B_END, ROT_D)           # HOPE / fusion / outro: home light

# ============================================================= the melodies
# THE REFRAIN — identical in every chorus. A Q/A cell over one 4-bar loop
# pass: question rises D-F#-A-B-D' and falls back to HANG on A (the V);
# answer, same rhythm, reaches higher (E') and falls home C#->D. The final D
# is the root of the D chord (bright light) and the minor third of the Bm
# chord (sad light) — the same note, re-lit.
REFRAIN = [(62, 1), (66, 1), (69, 1.5), (71, 0.5), (74, 1.5), (71, 0.5), (69, 2),
           (62, 1), (66, 1), (69, 1.5), (71, 0.5), (76, 1.5), (73, 0.5), (74, 2)]
# ritardando variant for the very last statement (tail stretched across the seam)
REFRAIN_RIT = REFRAIN[:-2] + [(73, 1.0), (74, 3.0)]
# hope statement 1 starts on beat 2 after the silent beat; tail shortened so
# it releases before statement 2
REFRAIN_PICKUP = REFRAIN[:-1] + [(74, 1)]

# THE VERSE — the question voice, low register, same Q/A discipline: the
# question pair hangs on E (off-tonic), the answer pair resolves C#->D.
VERSE_Q = [(59, 1.5), (62, 0.5), (64, 2), (62, 1.5), (59, 0.5), (62, 2),
           (57, 1.5), (62, 0.5), (66, 2), (64, 1), (62, 1), (64, 2)]
VERSE_A = VERSE_Q[:-3] + [(64, 1), (61, 1), (62, 2)]
# confusion variants: the third flattens (F#->F) over the minor flicker and
# the answer loses its footing — it slides down to land on Bb, not D.
VERSE_Q_FLAT = [(m - 1 if m == 66 else m, d) for m, d in VERSE_Q]
VERSE_A_FLAT = VERSE_Q_FLAT[:-3] + [(62, 1), (60, 1), (58, 2)]

# pre-chorus: 1-bar trades climbing into the refrain's register, then the rise
PRE_CALL1 = [(62, 1), (64, 1), (66, 2)]
PRE_ANS1 = [(64, 1), (66, 1), (67, 2)]
PRE_CALL2 = [(66, 1), (67, 1), (69, 2)]
PRE_ANS2 = [(67, 1), (69, 1), (73, 2)]
PRE_RISE = [(69, 2), (71, 2), (74, 2), (76, 2)]

# breakdown material — the refrain taken apart
Q_HALF = REFRAIN[:7]                                   # the question, alone
Q_SLOW = [(m, d * 1.5) for m, d in Q_HALF]             # loss: piano asks
A_SLOW = [(m - 12, d * 1.5) for m, d in REFRAIN[7:]]   # loss: cello answers, low
FRAG_BROKEN = [(62, 2), (66, 2), (69, 3), (71, 1)]     # sadness: the first four
                                                       # notes, twice as slow —
                                                       # the tune barely walking
TAIL_LOW = [(64, 2), (61, 1), (62, 5)]                 # sadness: cello answer

HOOKS = 0                                              # refrain statement count


# ============================================================= drum kit (dry)

def make_kick():
    n = int(0.42 * SR)
    td = np.arange(n) / SR
    f_curve = 44.0 + 110.0 * np.exp(-td * 55.0)
    body = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    sub = np.sin(2 * np.pi * (37 + 18 * np.exp(-td * 3)) * td) * np.exp(-td * 3.0)
    sos_c = signal.butter(2, [1800, 9000], "bandpass", fs=SR, output="sos")
    click = signal.sosfilt(sos_c, rng.standard_normal(n)) * np.exp(-td * 500)
    click /= np.max(np.abs(click)) + 1e-12
    env = (1 - np.exp(-td / 0.0008)) * np.exp(-td * 8.0)
    x = body * env + 0.55 * sub + 0.45 * click * (1 - np.exp(-td / 0.0008))
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
RCYM = np.ascontiguousarray(CRASH[::-1][int(0.4 * SR):])
DOWN = np.ascontiguousarray(CRASH[::-1])


def kick_gain(b):
    s = section_of(b)
    if s in ("thesis", "loss", "sad"):
        return 0.0
    if s == "rebuild":
        return 0.0 if b < B_REBUILD + 2 else 0.45     # walks back in quietly
    if s == "v1":
        return 0.8
    if s == "pre":
        return 0.9
    if s == "conf":
        return 0.85 if b >= B_LOSS - 4 else 0.95      # thins into the loss
    if s == "dip":
        return 0.85
    if s == "out":
        if b >= B_KSTOP:
            return 0.0
        return 0.9 if b < B_OUT + 4 else 0.72
    return 1.0


def silent_beat(b, beat):
    # the composed drop-silence: bar 124 beat 0 belongs to nobody
    return b == B_HOPE and beat < 1.0


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

pump = np.ones(N)
for b in range(B_END):
    if kick_gain(b) <= 0:
        continue
    i0, i1 = int(bar_t(b) * SR), int(bar_t(b + 1) * SR)
    seg = (t[i0:i1] - bar_t(b)) % BEAT
    pump[i0:i1] = np.minimum(pump[i0:i1], 0.32 + 0.68 * (1 - np.exp(-seg / 0.085)))

clear()
CH = [0.5, 0.28, 0.0, 0.34]
HAT_G = {"v1": 0.7, "pre": 0.85, "ch1": 1.0, "conf": 0.9, "dread": 0.9,
         "dip": 0.6, "dread2": 0.9, "hope": 1.0, "ch4": 1.0}
for b in range(B_END):
    s = section_of(b)
    if s in HAT_G:
        g = HAT_G[s]
    elif s == "rebuild" and b >= B_REBUILD + 4:
        g = 0.4 + 0.3 * (b - B_REBUILD - 4) / 4
    elif s == "out" and b < B_KSTOP - 4:
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
    if s not in ("ch1", "conf", "dread", "dip", "dread2", "hope", "ch4", "out"):
        continue
    if s == "out" and b >= B_OUT + 4:
        continue
    for beat in (1, 3):
        p = 0.42 if beat == 1 else 0.58
        place_pan(lay_L, lay_R, CLAP, bar_t(b, beat), 1.0, p)
commit(lay_L, lay_R, 0.10)
print("clap committed")

clear()
for b in range(B_CH4, B_OUT):                            # ride crowns the fusion
    for e in range(8):
        g = 0.7 if e % 2 == 0 else 0.45
        place_pan(lay_L, lay_R, RIDE, bar_t(b, e * 0.5), g, 0.5)
for b in range(B_DREAD2, B_SAD):                         # gentle in the sad wave
    for e in range(8):
        place_pan(lay_L, lay_R, RIDE, bar_t(b, e * 0.5), 0.5 if e % 2 == 0 else 0.32, 0.5)
commit(lay_L, lay_R, 0.045)
print("ride committed")

clear()
for b, g in [(B_CH1, 0.9), (B_CONF, 0.6), (B_DREAD, 1.0), (B_DIP, 0.5),
             (B_DREAD2, 0.7), (B_CH4, 1.0), (B_OUT, 0.6)]:
    place_pan(lay_L, lay_R, CRASH, bar_t(b), g, 0.5)
place_pan(lay_L, lay_R, CRASH, bar_t(B_HOPE, 1), 1.0, 0.5)   # HOPE slams on beat 2
for b in (B_CH1, B_DREAD, B_CH4):
    add_at(lay_L, RCYM, bar_t(b) - RCYM.shape[0] / SR, 0.8)
    add_at(lay_R, RCYM, bar_t(b) - RCYM.shape[0] / SR, 0.7)
# downsweeps INTO the breakdowns so the beat doesn't just stop dead
for b in (B_LOSS, B_SAD):
    add_at(lay_L, DOWN, bar_t(b) - DOWN.shape[0] / SR, 0.55)
    add_at(lay_R, DOWN, bar_t(b) - DOWN.shape[0] / SR, 0.5)
commit(lay_L, lay_R, 0.05)
print("crashes + downsweeps committed")

clear()
def roll(b0, b1, base):
    nbars = b1 - b0
    for b in range(b0, b1):
        u = (b - b0) / nbars
        div = 4 if u < 0.5 else (8 if u < 0.85 else 16)
        for s in range(div):
            g = base * (0.4 + 0.6 * u) * (0.7 + 0.3 * (s % 2))
            place_pan(lay_L, lay_R, SNARE, bar_t(b, s * 4.0 / div), g, 0.5)
roll(B_PRE + 4, B_CH1, 0.55)
roll(B_DREAD - 4, B_DREAD, 0.75)
roll(B_REBUILD + 2, B_HOPE, 0.8)
commit(lay_L, lay_R, 0.09)
print("rolls committed")


# ============================================================= bass (unified)

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
        x += np.sin(2 * np.pi * k * f * td) / k ** 1.3      # rolled-off, rounder
    y = signal.sosfilt(signal.butter(2, cutoff, "low", fs=SR, output="sos"), x)
    bpk, apk = signal.iirpeak(cutoff, Q=1.2, fs=SR)         # gentle, not nasal
    y = y + 0.3 * signal.lfilter(bpk, apk, y)
    y += 0.5 * np.sin(2 * np.pi * (f / 2) * td)             # round sub for body
    y = np.tanh(drive * y)                                  # soft, not crunchy
    y *= (1 - np.exp(-td / 0.004)) * np.clip((dur - td) / 0.02, 0, 1)
    bass_cache[key] = y / (np.max(np.abs(y)) + 1e-12)
    return bass_cache[key]


# SAME rolling root+octave pattern in every drop — only cutoff/drive differ.
BASS_PAT = [(0, 0, 0.8), (1, 12, 0.9), (2, 0, 0.8), (3, 12, 0.9)]
BASS_CUT = {"v1": 480, "pre": 520, "ch1": 560, "conf": 470, "dread": 440,
            "dip": 380, "dread2": 460, "hope": 600, "ch4": 620, "out": 440}
BASS_DRV = {"v1": 0.9, "pre": 0.9, "ch1": 0.9, "conf": 1.0, "dread": 1.1,
            "dip": 1.0, "dread2": 1.1, "hope": 0.9, "ch4": 0.9, "out": 0.9}
clear()
for b in range(B_END):
    s = section_of(b)
    root = CHORD_AT[b][0]
    if s in BASS_CUT:
        cut, drive = BASS_CUT[s], BASS_DRV[s]
        if s == "v1" and b < B_V1 + 2:
            continue                                       # bass joins 2 bars in
        if s == "out" and b >= B_KSTOP:
            continue
    elif s == "rebuild" and b >= B_REBUILD + 2:
        cut, drive = 340, 1.0
    else:
        continue
    # filter the last 2 bars down into each breakdown for a smooth exit
    if section_of(b + 2) in ("loss", "sad") and s in BASS_CUT:
        cut *= 0.6
    for beat in range(4):
        if silent_beat(b, beat):
            continue
        for sx, off, gg in BASS_PAT:
            x = bass_note(root + off, cut, drive)
            tt = bar_t(b, beat + sx * 0.25)
            add_at(lay_L, x, tt, gg)
            add_at(lay_R, x, tt, gg)
commit(lay_L, lay_R, 0.30, env=pump)
print(f"bass committed ({len(bass_cache)} cached)")

# a soft sustained sub for emotional weight (not a hard pedal) — under the
# dread, and under the fusion chorus so the everything-chorus is the peak
clear()
for b in list(range(B_DREAD, B_SAD)) + list(range(B_CH4, B_OUT)):
    f = midi_to_hz(CHORD_AT[b][0] - 12)
    seg_n = int(BAR * SR)
    td = np.arange(seg_n) / SR
    sub = np.sin(2 * np.pi * f * td) * np.minimum(np.clip(td / 0.05, 0, 1),
                                                  np.clip((BAR - td) / 0.1, 0, 1))
    g = 0.85 if b >= B_CH4 else 0.62      # the fusion owns the deepest weight
    add_at(lay_L, sub, bar_t(b), g)
    add_at(lay_R, sub, bar_t(b), g)
commit(lay_L, lay_R, 0.10, env=0.5 + 0.5 * pump)
print("sustained sub committed")


# ============================================================= pluck arp

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


ARP_PAT = [0, 1, 2, 3, 2, 1, 3, 2]
ARP_G = {"v1": 0.6, "pre": 0.65, "ch1": 0.7, "conf": 0.65, "dread": 0.6,
         "dip": 0.5, "dread2": 0.6, "hope": 0.8, "ch4": 0.8, "out": 0.5}
clear()
for b in range(B_END):
    s = section_of(b)
    if s not in ARP_G:
        continue
    if s == "out" and b >= B_KSTOP:
        continue
    voicing = CHORD_AT[b][1]
    notes = list(voicing) + [voicing[1] + 12]
    g0 = ARP_G[s]
    # confusion development: the figure runs backwards in the flicker cells,
    # and every other bar it slips a 16th late — the arp losing its footing
    pat = ARP_PAT
    shove = 0.0
    if s == "conf" and B_CONF + 8 <= b < B_CONF + 20:
        pat = ARP_PAT[::-1]
        shove = 0.25 if b % 2 else 0.0
    for sx in range(16):
        if silent_beat(b, sx * 0.25):
            continue
        idx = pat[sx % len(pat)] % len(notes)
        m = notes[idx]
        pan = 0.5 + 0.4 * (idx / (len(notes) - 1) - 0.5)
        place_pan(lay_L, lay_R, pluck(m), bar_t(b, (sx + shove) * 0.25),
                  g0 * (0.9 if sx % 2 else 1.0), pan)
        # the glitter: octave-up pings on the offbeats in the bright choruses
        if s in ("hope", "ch4") and sx % 4 == 2:
            place_pan(lay_L, lay_R, pluck(m + 12), bar_t(b, sx * 0.25),
                      0.35, 1.0 - pan)
lay_L = reverb(lay_L, IR_L, 0.3)
lay_R = reverb(lay_R, IR_R, 0.3)
commit(lay_L, lay_R, 0.15, env=0.6 + 0.4 * pump)
print(f"pluck arp committed ({len(pluck_cache)} cached)")


# ============================================================= warm lead
# The v4 recipe unchanged: warm detuned saw, harmonics rolled off, low
# cutoff, a sub octave for body — round and singing, never squeaky.

def lead_phrase(notes, lowpass=2800, detune=(0.996, 1.0, 1.004), sub=0.3):
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
            v += np.sin(k * ph) / k ** 1.4               # rolled-off = warm
        pan = (j / (len(detune) - 1) - 0.5)
        L += v * (0.6 + 0.4 * (0.5 - pan))
        R += v * (0.6 + 0.4 * (0.5 + pan))
    ph0 = 2 * np.pi * np.cumsum(f * vibe) / SR
    body = np.sin(ph0 / 2.0) * sub                       # sub octave for warmth
    L += body
    R += body
    env = np.minimum(np.clip(tt / 0.10, 0, 1), np.clip((total + 0.5 - tt) / 1.4, 0, 1))
    sos = signal.butter(2, lowpass, "low", fs=SR, output="sos")
    L = signal.sosfilt(sos, L * env)
    R = signal.sosfilt(sos, R * env)
    peak = max(np.max(np.abs(L)), np.max(np.abs(R)), 1e-12)
    return L / peak, R / peak


DELAY = 0.75 * BEAT


def place_lead(layL, layR, LR, t0, gain):
    L, R = LR
    add_at(layL, L, t0, gain)
    add_at(layR, R, t0, gain)
    add_at(layL, R, t0 + DELAY, gain * 0.26)             # ping-pong echo
    add_at(layR, L, t0 + DELAY, gain * 0.26)


def tail_of(notes, k=3, up=12):
    return [(m + up, d) for m, d in notes[-k:]]


def onset_of_tail(notes, k=3):
    return sum(d for _, d in notes[:-k])


clear()
LEAD_REFRAIN = lead_phrase(REFRAIN, lowpass=2900)
LEAD_REFRAIN_SAD = lead_phrase(REFRAIN, lowpass=2500)    # same notes, darker felt
LEAD_RIT = lead_phrase(REFRAIN_RIT, lowpass=2900)
LEAD_PICKUP = lead_phrase(REFRAIN_PICKUP, lowpass=2900)
LEAD_VQ = lead_phrase(VERSE_Q, lowpass=2400)
LEAD_VA = lead_phrase(VERSE_A, lowpass=2400)

# verse 1: the lead sings low Q/A pairs (piano echoes are placed with the piano)
place_lead(lay_L, lay_R, LEAD_VQ, bar_t(B_V1 + 4), 0.7)
place_lead(lay_L, lay_R, LEAD_VA, bar_t(B_V1 + 8), 0.72)
# pre-chorus: 1-bar calls (piano answers), then the rise; pickup into chorus 1
for frag, b0, g in [(PRE_CALL1, B_PRE, 0.7), (PRE_CALL2, B_PRE + 2, 0.72),
                    (PRE_RISE, B_PRE + 4, 0.8)]:
    place_lead(lay_L, lay_R, lead_phrase(frag, lowpass=2600), bar_t(b0), g)
place_lead(lay_L, lay_R, lead_phrase([(69, 0.5)], lowpass=2600), bar_t(B_CH1 - 1, 3.5), 0.6)

# CHORUS 1 — LOVE: statements 1, 2, 4 on the lead (statement 3 is the piano's)
place_lead(lay_L, lay_R, LEAD_REFRAIN, bar_t(B_CH1), 0.85); HOOKS += 1
place_lead(lay_L, lay_R, LEAD_REFRAIN, bar_t(B_CH1 + 4), 0.9); HOOKS += 1
place_lead(lay_L, lay_R, LEAD_REFRAIN, bar_t(B_CH1 + 12), 0.9); HOOKS += 1

# confusion: the lead only echoes the piano's tails, drifting off the beat
for src, b0, off in [(VERSE_Q, B_CONF, 0.0), (VERSE_A, B_CONF + 4, 0.0),
                     (VERSE_Q_FLAT, B_CONF + 8, 0.5), (VERSE_A_FLAT, B_CONF + 12, 0.5)]:
    e = lead_phrase(tail_of(src), lowpass=2500)
    place_lead(lay_L, lay_R, e, bar_t(b0, onset_of_tail(src) + off + 0.5), 0.55)
# ...and states lone question fragments in the darkest cells
FRAG_Q = lead_phrase(REFRAIN[:4], lowpass=2500)
place_lead(lay_L, lay_R, FRAG_Q, bar_t(B_CONF + 16, 1.5), 0.55)
place_lead(lay_L, lay_R, FRAG_Q, bar_t(B_CONF + 18, 0.5), 0.5)

# CHORUS 2 — DREAD: the refrain IDENTICAL, landing in the Bm light
place_lead(lay_L, lay_R, LEAD_REFRAIN_SAD, bar_t(B_DREAD), 0.95); HOOKS += 1
place_lead(lay_L, lay_R, LEAD_REFRAIN_SAD, bar_t(B_DREAD + 4), 0.95); HOOKS += 1
place_lead(lay_L, lay_R, LEAD_REFRAIN_SAD, bar_t(B_DREAD2), 1.0); HOOKS += 1
place_lead(lay_L, lay_R, LEAD_REFRAIN_SAD, bar_t(B_DREAD2 + 4), 1.0); HOOKS += 1
place_lead(lay_L, lay_R, LEAD_REFRAIN_SAD, bar_t(B_DREAD2 + 8), 1.0); HOOKS += 1

# CHORUS 3 — HOPE: statement 1 rides in on beat 2 out of the silence
place_lead(lay_L, lay_R, LEAD_PICKUP, bar_t(B_HOPE, 1), 0.95); HOOKS += 1
place_lead(lay_L, lay_R, LEAD_REFRAIN, bar_t(B_HOPE + 4), 1.0); HOOKS += 1
place_lead(lay_L, lay_R, LEAD_REFRAIN, bar_t(B_HOPE + 8), 1.0); HOOKS += 1
place_lead(lay_L, lay_R, LEAD_REFRAIN, bar_t(B_HOPE + 12), 0.95); HOOKS += 1

# CHORUS 4 — the fusion (cello counter-line placed with the cello); an
# octave-up shimmer copy joins from statement 2 — the fullest wave
LEAD_HI = lead_phrase([(m + 12, d) for m, d in REFRAIN], lowpass=2900)
LEAD_HI_RIT = lead_phrase([(m + 12, d) for m, d in REFRAIN_RIT], lowpass=2900)
place_lead(lay_L, lay_R, LEAD_REFRAIN, bar_t(B_CH4), 1.0); HOOKS += 1
place_lead(lay_L, lay_R, LEAD_REFRAIN, bar_t(B_CH4 + 4), 1.0); HOOKS += 1
place_lead(lay_L, lay_R, LEAD_HI, bar_t(B_CH4 + 4), 0.45)
place_lead(lay_L, lay_R, LEAD_REFRAIN, bar_t(B_CH4 + 8), 1.0); HOOKS += 1
place_lead(lay_L, lay_R, LEAD_HI, bar_t(B_CH4 + 8), 0.45)
place_lead(lay_L, lay_R, LEAD_RIT, bar_t(B_CH4 + 12), 0.95); HOOKS += 1
place_lead(lay_L, lay_R, LEAD_HI_RIT, bar_t(B_CH4 + 12), 0.42)

lay_L = reverb(lay_L, IR_L, 0.38)
lay_R = reverb(lay_R, IR_R, 0.38)
commit(lay_L, lay_R, 0.20)
print("warm lead committed")


# ============================================================= cello
# The low answering voice: answers the piano in the breaks, doubles the
# refrain an octave below in the dread, and carries the verse melody as the
# counter-line under the fusion chorus.

def cello_line(notes, lowpass=1900):
    total = sum(d for _, d in notes) * BEAT
    n = int((total + 0.8) * SR)
    td = np.arange(n) / SR
    f = glide_curve([(m, d * BEAT) for m, d in notes], n, tau=0.05)
    vib = 1.0 + 0.005 * np.sin(2 * np.pi * 5.0 * td) * np.clip(td / 0.7, 0, 1)
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    out = np.zeros(n)
    for k in range(1, 13):
        out += np.sin(k * ph) / k
    bow = signal.sosfilt(signal.butter(2, [80, 2400], "bandpass", fs=SR, output="sos"),
                         rng.standard_normal(n))
    out = out / (np.max(np.abs(out)) + 1e-12) + 0.07 * bow
    env = np.minimum(np.clip(td / 0.25, 0, 1), np.clip((total + 0.1 - td) / 0.5, 0, 1))
    out = signal.sosfilt(signal.butter(2, lowpass, "low", fs=SR, output="sos"), out * env)
    return out / (np.max(np.abs(out)) + 1e-12)


def place_cello(x, t0, gain):
    add_at(lay_L, x, t0, gain)
    add_at(lay_R, x, t0, gain)


clear()
# loss: the cello ANSWERS the piano's question (the bare trade)
cello_answer = cello_line(A_SLOW)
place_cello(cello_answer, bar_t(B_LOSS + 4), 0.8)
place_cello(cello_answer, bar_t(B_LOSS + 10), 0.75)
# dread: the refrain doubled an octave below — weight and sorrow
cello_dread = cello_line([(m - 12, d) for m, d in REFRAIN])
place_cello(cello_dread, bar_t(B_DREAD + 4), 0.7)
place_cello(cello_dread, bar_t(B_DREAD2), 0.72)
place_cello(cello_dread, bar_t(B_DREAD2 + 4), 0.72)
place_cello(cello_dread, bar_t(B_DREAD2 + 8), 0.72)
# sadness: answering the broken piano fragment
cello_tail = cello_line([(m - 12, d) for m, d in TAIL_LOW])
place_cello(cello_tail, bar_t(B_SAD + 3), 0.75)
place_cello(cello_tail, bar_t(B_SAD + 7), 0.7)
# the fusion: the VERSE melody (the question voice) under the refrain
cello_vq = cello_line([(m - 12, d) for m, d in VERSE_Q])
cello_va = cello_line([(m - 12, d) for m, d in VERSE_A])
place_cello(cello_vq, bar_t(B_CH4), 0.8)
place_cello(cello_va, bar_t(B_CH4 + 4), 0.8)
place_cello(cello_vq, bar_t(B_CH4 + 8), 0.82)
place_cello(cello_va, bar_t(B_CH4 + 12), 0.82)
lay_L = reverb(lay_L, IR_L, 0.45)
lay_R = reverb(lay_R, IR_R, 0.45)
commit(lay_L, lay_R, 0.18)
print("cello committed")


# ============================================================= piano
# The second voice of the duet: states the thesis, echoes the verse tails,
# leads the confusion, asks in the breaks, and bookends the track.

piano_cache = {}


def piano_note(midi, dur):
    key = (midi, round(dur, 2))
    if key in piano_cache:
        return piano_cache[key]
    f = midi_to_hz(midi)
    n = int((dur + 0.8) * SR)
    td = np.arange(n) / SR
    out = np.zeros(n)
    for k in range(1, min(14, int(8500 / f)) + 1):
        fk = f * k * np.sqrt(1 + 0.00035 * k * k)
        dec = 0.9 + 0.45 * k
        for det in (0.9994, 1.0006):
            out += np.sin(2 * np.pi * fk * det * td + rng.uniform(0, 6)) / k ** 1.25 * np.exp(-td * dec)
    ham = signal.sosfilt(signal.butter(2, [1500, 4000], "bandpass", fs=SR, output="sos"),
                         rng.standard_normal(n)) * np.exp(-td * 350)
    out = out / (np.max(np.abs(out)) + 1e-12) + 0.16 * ham / (np.max(np.abs(ham)) + 1e-12)
    out *= (1 - np.exp(-td / 0.0015)) * np.clip((dur + 0.35 - td) / 0.35, 0, 1)
    piano_cache[key] = out / (np.max(np.abs(out)) + 1e-12)
    return piano_cache[key]


clear()
def place_piano_theme(notes, t0, gain, lh_root=None):
    tm = t0
    for m, d in notes:
        place_pan(lay_L, lay_R, piano_note(m, d * BEAT), tm, gain,
                  np.clip(0.5 + (m - 64) * 0.012, 0.25, 0.75))
        tm += d * BEAT
    if lh_root is not None:                              # left-hand octave bed
        place_pan(lay_L, lay_R, piano_note(lh_root, (tm - t0)), t0, gain * 0.5, 0.4)


# THE THESIS: the refrain, solo, half-voice; the low D rings under the kick entry
place_piano_theme(REFRAIN, bar_t(0), 0.7, lh_root=50); HOOKS += 1
# verse 1: piano echoes each lead phrase's tail (enters on the last note)
place_piano_theme(tail_of(VERSE_Q), bar_t(B_V1 + 4, onset_of_tail(VERSE_Q) + 0.5), 0.5)
place_piano_theme(tail_of(VERSE_A), bar_t(B_V1 + 8, onset_of_tail(VERSE_A) + 0.5), 0.5)
# pre-chorus: the piano's 1-bar answers, and the rise doubled an octave down
place_piano_theme(PRE_ANS1, bar_t(B_PRE + 1), 0.6)
place_piano_theme(PRE_ANS2, bar_t(B_PRE + 3), 0.6)
place_piano_theme([(m - 12, d) for m, d in PRE_RISE], bar_t(B_PRE + 4), 0.5)
# CHORUS 1, statement 3: the piano sings the refrain — the performer answer
place_piano_theme(REFRAIN, bar_t(B_CH1 + 8), 0.85, lh_root=38); HOOKS += 1
# confusion: the piano LEADS (roles swapped); the flicker cells flatten the
# third and the answer lands on Bb — same tune, footing gone
place_piano_theme(VERSE_Q, bar_t(B_CONF), 0.8)
place_piano_theme(VERSE_A, bar_t(B_CONF + 4), 0.8)
place_piano_theme(VERSE_Q_FLAT, bar_t(B_CONF + 8, 0.5), 0.78)
place_piano_theme(VERSE_A_FLAT, bar_t(B_CONF + 12, 0.5), 0.78)
place_piano_theme(VERSE_Q, bar_t(B_CONF + 20), 0.7)
# loss: the piano ASKS — the refrain's question, slowed, alone
place_piano_theme(Q_SLOW, bar_t(B_LOSS + 1), 0.85)
place_piano_theme(Q_SLOW, bar_t(B_LOSS + 7), 0.8)
# sadness: the most broken fragment, barely walking
place_piano_theme(FRAG_BROKEN, bar_t(B_SAD + 1), 0.8)
place_piano_theme(FRAG_BROKEN, bar_t(B_SAD + 5), 0.75)
# the pickup hanging in the silent beat before HOPE
place_piano_theme([(69, 0.5)], bar_t(B_HOPE, 0.4), 0.55)
# THE BOOKEND: the refrain once more, solo, and the final chord rings out
place_piano_theme(REFRAIN, bar_t(B_BOOK), 0.75, lh_root=50); HOOKS += 1
for m in (50, 57, 62, 66, 74):
    place_pan(lay_L, lay_R, piano_note(m, 6.0), bar_t(B_BOOK + 4), 0.7,
              np.clip(0.5 + (m - 64) * 0.012, 0.25, 0.75))
lay_L = reverb(lay_L, IR_L, 0.5)
lay_R = reverb(lay_R, IR_R, 0.5)
commit(lay_L, lay_R, 0.24)
print(f"piano committed ({len(piano_cache)} cached)")


# ============================================================= pads

def pad_chord(chord, dur, attack, release, lowpass, detune=0.0012):
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
LP = {"thesis": 900, "v1": 1000, "pre": 1100, "ch1": 1300, "conf": 900,
      "loss": 850, "dread": 750, "dip": 700, "dread2": 750, "sad": 800,
      "rebuild": 1100, "hope": 1500, "ch4": 1500, "out": 1300}
PG = {"thesis": 0.5, "v1": 0.6, "pre": 0.7, "ch1": 0.6, "conf": 0.6,
      "loss": 0.95, "dread": 0.72, "dip": 0.82, "dread2": 0.72, "sad": 0.95,
      "rebuild": 0.9, "hope": 0.65, "ch4": 0.78, "out": 0.6}
# pads change with the harmony (1 bar) but ring 2.5 s past it so chords
# overlap every boundary; breaks hold 2-bar chords via CHORD_AT
bb = 0
while bb < B_END:
    s = section_of(bb)
    hold = 2 if s in ("loss", "sad") else 1
    chord = CHORD_AT[bb][1]
    det = 0.006 if (s == "conf" and B_CONF + 8 <= bb < B_CONF + 20) else 0.0014
    pL, pR = pad_chord(chord, hold * BAR + 2.5, attack=1.2, release=2.0,
                       lowpass=LP[s], detune=det)
    add_at(lay_L, pL, bar_t(bb), PG[s])
    add_at(lay_R, pR, bar_t(bb), PG[s])
    bb += hold
lay_L = reverb(lay_L, IR_L, 0.45)
lay_R = reverb(lay_R, IR_R, 0.45)
pad_env = np.where((t < bar_t(B_LOSS)) | ((t >= bar_t(B_DREAD)) & (t < bar_t(B_SAD))) |
                   (t >= bar_t(B_HOPE)), pump, 1.0)
commit(lay_L, lay_R, 0.17, env=0.6 + 0.4 * pad_env)
print("pads committed")


# ============================================================= heartbeat (breaks)

clear()
def heart():
    n = int(0.26 * SR)
    td = np.arange(n) / SR
    f = 32 + 36 * np.exp(-td * 20)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-td * 13)
    body += 0.5 * np.sin(2 * np.pi * 70 * td) * np.exp(-td * 18)
    thud = signal.sosfilt(signal.butter(2, 220, "low", fs=SR, output="sos"),
                          rng.standard_normal(n)) * np.exp(-td * 28)
    x = body / (np.max(np.abs(body)) + 1e-12) + 0.3 * thud / (np.max(np.abs(thud)) + 1e-12)
    x *= 1 - np.exp(-td / 0.004)
    return x / (np.max(np.abs(x)) + 1e-12)

THUMP = heart()
for b in range(B_END):
    if section_of(b) not in ("loss", "sad"):
        continue
    for beat in (0, 2):
        add_at(lay_L, THUMP, bar_t(b, beat), 0.9)
        add_at(lay_R, THUMP, bar_t(b, beat), 0.9)
        add_at(lay_L, THUMP, bar_t(b, beat + 0.5), 0.55)
        add_at(lay_R, THUMP, bar_t(b, beat + 0.5), 0.55)
commit(lay_L, lay_R, 0.18)
print("heartbeat committed")


# ============================================================= risers + atmos

clear()
def riser(b0, b1, gain=1.0):
    t0, t1 = bar_t(b0), bar_t(b1)
    n = int((t1 - t0) * SR)
    td = np.arange(n) / SR
    prog = td / (t1 - t0)
    noise = rng.standard_normal(n)
    out = np.zeros(n)
    for k in range(8):
        c = 350 * (6000 / 350) ** (k / 7)
        win = np.clip(1 - np.abs(prog - np.log(c / 350) / np.log(6000 / 350)) * 6, 0, 1)
        out += signal.sosfilt(signal.butter(2, [c * 0.85, c * 1.18], "bandpass", fs=SR, output="sos"), noise) * win
    out += 0.4 * np.sin(2 * np.pi * np.cumsum(midi_to_hz(50) * 2 ** (2 * prog)) / SR)
    out *= prog ** 2
    add_at(lay_L, out / (np.max(np.abs(out)) + 1e-12), t0, gain)
    add_at(lay_R, out / (np.max(np.abs(out)) + 1e-12), t0, gain * 0.96)
riser(B_PRE + 4, B_CH1, 0.6)
riser(B_DREAD - 4, B_DREAD)
riser(B_REBUILD, B_HOPE)                # ends dead at the silent beat
commit(lay_L, lay_R, 0.08)

clear()
air = signal.sosfilt(signal.butter(4, [150, 1400], "bandpass", fs=SR, output="sos"),
                     rng.standard_normal(N))
air /= np.max(np.abs(air)) + 1e-12
air_env = slow_noise(0.05, 0.4, 1.0)
edge = np.clip((bar_t(B_CH1) - t) / 12.0, 0, 1) + \
    np.where((t >= bar_t(B_LOSS)) & (t < bar_t(B_DREAD)), 0.6, 0.0) + \
    np.where((t >= bar_t(B_SAD)) & (t < bar_t(B_REBUILD)), 0.6, 0.0)
lay_L[:] = air * air_env * np.clip(edge, 0, 1)
lay_R[:] = air * air_env[::-1] * np.clip(edge, 0, 1)
commit(lay_L, lay_R, 0.05)
print("risers + atmosphere committed")


# ---------------------------------------------------------------- master

fade(mix_L, fade_in=0.05, fade_out=10.0)
fade(mix_R, fade_in=0.05, fade_out=10.0)

for ch in (mix_L, mix_R):
    ch += 0.28 * signal.sosfilt(signal.butter(2, 95, "low", fs=SR, output="sos"), ch)

peak = max(np.max(np.abs(mix_L)), np.max(np.abs(mix_R))) + 1e-12
mix_L = np.tanh(1.3 * mix_L / peak) / np.tanh(1.3) * 0.88
mix_R = np.tanh(1.3 * mix_R / peak) / np.tanh(1.3) * 0.88

stereo = np.empty((N, 2))
stereo[:, 0] = mix_L
stereo[:, 1] = mix_R
pcm = (stereo * 32767.0).astype(np.int16)

OUT_DIR = "/workspace/music"
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, "lost_v6.wav")
with wave.open(OUT, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())

print(f"\nCreated: {os.path.abspath(OUT)}")
print(f"Duration: {N / SR:.1f} s  |  {SR} Hz stereo, 16-bit PCM  |  {BPM:.0f} BPM, Bm-G-D-A (three rotations)")

MP3 = os.path.join(OUT_DIR, "lost_v6.mp3")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", OUT,
                "-vn", "-ar", "44100", "-ac", "2", "-b:a", "192k", MP3],
               check=True)
print(f"Created: {os.path.abspath(MP3)}  (192k mp3)")

# ---------------------------------------------------------------- verify form

print("\nSection map:")
SECTIONS = [("THESIS (solo piano)", 0), ("verse 1", B_V1), ("pre-chorus", B_PRE),
            ("CHORUS 1 — LOVE", B_CH1), ("verse 2 — CONFUSION", B_CONF),
            ("LOSS breakdown", B_LOSS), ("CHORUS 2 — DREAD", B_DREAD),
            ("dip", B_DIP), ("dread fullest wave", B_DREAD2),
            ("SADNESS breakdown", B_SAD), ("rebuild", B_REBUILD),
            ("CHORUS 3 — HOPE", B_HOPE), ("CHORUS 4 — fusion", B_CH4),
            ("outro", B_OUT)]
for name, b in SECTIONS:
    print(f"  {bar_t(b):6.1f} s  bar {b:3d}  {name}")
print(f"  {bar_t(B_KSTOP):6.1f} s  bar {B_KSTOP}  the kick stops")
print(f"  {bar_t(B_BOOK):6.1f} s  bar {B_BOOK}  piano bookend")
print(f"  {DURATION:6.1f} s  end")

print(f"\nRefrain statements: {HOOKS}  (target >= 10)")

print("\nSeam checklist (what crosses every boundary):")
for b, dev in [(B_V1, "thesis' low D chord rings under the kick entry"),
               (B_PRE, "verse tail echo overlaps the first trade"),
               (B_CH1, "roll + riser + lead pickup note + reverse cymbal"),
               (B_CONF, "chorus refrain's last note rings across + crash"),
               (B_LOSS, "downsweep into the break (beat exits filtered)"),
               (B_DREAD, "roll + riser + reverse cymbal"),
               (B_SAD, "downsweep into the break"),
               (B_HOPE, "riser ends at the SILENT BEAT; piano pickup hangs in it; slam on beat 2"),
               (B_CH4, "refrain chain unbroken + reverse cymbal + crash"),
               (B_OUT, "ritardando refrain tail rings across the seam"),
               (B_BOOK, "pads still ringing under the solo piano")]:
    print(f"  bar {b:3d} ({bar_t(b):5.1f} s): {dev}")

def rms_between(b0, b1):
    i0 = int(bar_t(b0) * SR)
    i1 = int(bar_t(b1) * SR) if b1 is not None else N
    return np.sqrt(np.mean(mix_L[i0:i1] ** 2 + mix_R[i0:i1] ** 2) / 2)

print("\nPer-section RMS:")
R = {}
for (name, b0), (_, b1) in zip(SECTIONS, SECTIONS[1:] + [("end", None)]):
    R[name] = rms_between(b0, b1)
    print(f"  {name:24s} {R[name]:.3f}")

dread_all = rms_between(B_DREAD, B_SAD)
checks = [
    ("thesis < verse1 < chorus1",
     R["THESIS (solo piano)"] < R["verse 1"] < R["CHORUS 1 — LOVE"]),
    ("dread (all) >= chorus1", dread_all >= R["CHORUS 1 — LOVE"]),
    ("chorus4 is the loudest section", R["CHORUS 4 — fusion"] == max(R.values())),
    ("LOSS is a trough", R["LOSS breakdown"] < min(R["verse 2 — CONFUSION"], dread_all)),
    ("SADNESS is a trough", R["SADNESS breakdown"] < min(dread_all, R["CHORUS 3 — HOPE"])),
    ("outro settles", R["outro"] < R["CHORUS 4 — fusion"]),
    ("refrain count >= 10", HOOKS >= 10),
]
print("\nForm checks:")
ok = True
for name, passed in checks:
    print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
    ok &= passed
print("all checks passed" if ok else "SOME CHECKS FAILED")
