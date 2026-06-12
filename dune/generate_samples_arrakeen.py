#!/usr/bin/env python3
"""
generate_samples_arrakeen.py — short demo samples of the new instruments
introduced by generate_fall_of_arrakeen.py ("The Fall of Arrakeen"),
written to /workspace/music/samples/. Continues the numbering of the
earlier sample scripts and REFUSES to overwrite existing files.

New here:
  instrument_22_kick_stack_room.wav   the room-shaker: punch + click +
                                      long 55->37 Hz sub tail (v2 kick)
  instrument_23_field_snare_march.wav military snare: march bar with
                                      drag ghosts, then a buzz-roll
  instrument_24_war_horn.wav          carnyx-style horn: scoop attack,
                                      31 Hz growl, formant bump
  instrument_25_battle_toms.wav       three pitched toms 165/110/80 Hz,
                                      pattern then a descending run
  instrument_26_shaker_16ths.wav      soft 16th shaker, bp 3.5-9.5 kHz
  effect_07_reverse_cymbal.wav        reversed cymbal swell into a hit
  rhythm_05_war_groove_148bpm.wav     the assembled war groove
"""

import os
import sys
import wave
import numpy as np
from scipy import signal

SR = 44100
OUT_DIR = "/workspace/music/samples"

NEW_FILES = [
    "instrument_22_kick_stack_room.wav",
    "instrument_23_field_snare_march.wav",
    "instrument_24_war_horn.wav",
    "instrument_25_battle_toms.wav",
    "instrument_26_shaker_16ths.wav",
    "effect_07_reverse_cymbal.wav",
    "rhythm_05_war_groove_148bpm.wav",
    "README_arrakeen.txt",
]

existing = [f for f in NEW_FILES if os.path.exists(os.path.join(OUT_DIR, f))]
if existing:
    sys.exit(f"ABORT — would overwrite existing samples: {', '.join(existing)}")

os.makedirs(OUT_DIR, exist_ok=True)
rng = np.random.default_rng(10191)

BPM = 148.0
BEAT = 60.0 / BPM
BAR = BEAT * 4
STEP = BEAT / 4


def midi_to_hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def add_at(buf, x, start_s, gain=1.0):
    i0 = int(start_s * SR)
    end = min(len(buf), i0 + len(x))
    if end > i0:
        buf[i0:end] += x[: end - i0] * gain


def write_wav(name, x):
    x = x / (np.max(np.abs(x)) + 1e-12) * 0.85
    pcm = (np.repeat(x[:, None], 2, axis=1) * 32767.0).astype(np.int16)
    path = os.path.join(OUT_DIR, name)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(f"wrote {path}  ({len(x) / SR:.1f} s)")


# ---------------------------------------------------------------- kick stack

def make_kick_stack(sub=True):
    n = int(0.42 * SR)
    td = np.arange(n) / SR
    f_curve = 44.0 + 106.0 * np.exp(-td * 50.0)     # v2: lands at 44 Hz
    punch = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    sos_c = signal.butter(2, [1800, 9000], "bandpass", fs=SR, output="sos")
    click = signal.sosfilt(sos_c, rng.standard_normal(n)) * np.exp(-td * 700)
    click /= np.max(np.abs(click)) + 1e-12
    env_p = (1 - np.exp(-td / 0.0008)) * np.exp(-td * 9.0)
    x = (punch + 0.50 * click) * env_p
    if sub:
        f_sub = 37.0 + 18.0 * np.exp(-td * 9.0)     # v2: lands on D1 (36.7 Hz)
        tail = np.sin(2 * np.pi * np.cumsum(f_sub) / SR)
        env_s = (1 - np.exp(-td / 0.004)) * np.exp(-td * 3.0)
        x = x + 1.15 * tail * env_s
    return x / (np.max(np.abs(x)) + 1e-12)


KICK = make_kick_stack()

demo = np.zeros(int(5.5 * SR))
for i in range(4):                                  # four single hits
    add_at(demo, KICK, 0.3 + i * 0.8, 1.0)
for i in range(8):                                  # then four-to-floor
    add_at(demo, KICK, 3.6 + i * BEAT, 1.0)
write_wav("instrument_22_kick_stack_room.wav", demo)


# ---------------------------------------------------------------- field snare

def make_snare(buzz=False):
    n = int((0.07 if buzz else 0.17) * SR)
    td = np.arange(n) / SR
    sos_n = signal.butter(2, [1500, 9000], "bandpass", fs=SR, output="sos")
    nz = signal.sosfilt(sos_n, rng.standard_normal(n))
    nz /= np.max(np.abs(nz)) + 1e-12
    tone = (np.sin(2 * np.pi * 185.0 * td) +
            0.7 * np.sin(2 * np.pi * 330.0 * td)) * np.exp(-td * 40)
    env = np.exp(-td * (70.0 if buzz else 26.0)) * (1 - np.exp(-td / 0.001))
    x = (0.8 * nz + 0.5 * tone) * env
    return x / (np.max(np.abs(x)) + 1e-12)


SNARE = make_snare()
SBUZZ = make_snare(buzz=True)
MARCH = [(0, 1.00, True), (2, 0.35, False), (4, 0.55, False),
         (6, 0.35, False), (7, 0.35, False), (8, 0.90, True),
         (10, 0.35, False), (12, 0.60, False), (14, 0.40, False),
         (15, 0.40, False)]

demo = np.zeros(int((4 * BAR + 1.0) * SR))
for b in range(4):
    roll_bar = b == 3
    for s, g, acc in MARCH:
        if roll_bar and s >= 12:
            break
        st = 0.1 + b * BAR + s * STEP   # 0.1 s lead-in: room for the drags
        if acc:
            add_at(demo, SBUZZ, st - 0.060, 0.30)
            add_at(demo, SBUZZ, st - 0.030, 0.35)
        add_at(demo, SNARE, st, g)
    if roll_bar:
        for i in range(8):
            add_at(demo, SBUZZ, 0.1 + b * BAR + 3 * BEAT + i * 0.125 * BEAT,
                   0.3 + 0.7 * i / 7)
write_wav("instrument_23_field_snare_march.wav", demo)


# ---------------------------------------------------------------- war horn

def glide_curve(notes, n):
    f_target = np.zeros(n)
    edge = 0.0
    for m, d in notes:
        a, b = int(edge * SR), min(n, int((edge + d) * SR))
        f_target[a:b] = midi_to_hz(m)
        edge += d
    i_end = min(n - 1, int(edge * SR))
    f_target[i_end:] = f_target[i_end - 1]
    alpha = 1.0 - np.exp(-1.0 / (0.09 * SR))
    return signal.lfilter([alpha], [1.0, -(1.0 - alpha)],
                          f_target, zi=[f_target[0] * (1 - alpha)])[0]


def horn_phrase(notes, growl=0.18, lp=1600):
    total = sum(d for _, d in notes) + 1.2
    n = int(total * SR)
    tt = np.arange(n) / SR
    f_curve = glide_curve(notes, n)
    scoop = 0.94 + 0.06 * np.clip(tt / 0.15, 0, 1)
    phase = 2 * np.pi * np.cumsum(f_curve * scoop) / SR
    tone = np.zeros(n)
    for k in range(1, 13):
        tone += np.sin(k * phase) / k ** 0.7
    tone *= 1.0 + growl * np.sin(2 * np.pi * 31.0 * tt)
    env = np.minimum(np.clip(tt / 0.10, 0, 1) ** 0.8,
                     np.clip((total - tt) / 1.0, 0, 1))
    tone *= env
    sos_lo = signal.butter(2, lp, "low", fs=SR, output="sos")
    out = signal.sosfilt(sos_lo, tone)
    sos_fm = signal.butter(2, [450, 900], "bandpass", fs=SR, output="sos")
    out += 0.6 * signal.sosfilt(sos_fm, tone)
    return out / (np.max(np.abs(out)) + 1e-12)


demo = np.zeros(int(11.0 * SR))
add_at(demo, horn_phrase([(50, 1.2), (51, 0.6), (50, 2.2)]), 0.3, 1.0)
add_at(demo, horn_phrase([(50, 3.0)], growl=0.28), 5.5, 1.0)   # long blast
add_at(demo, horn_phrase([(38, 3.0)], growl=0.28), 5.5, 0.8)   # octave stack
write_wav("instrument_24_war_horn.wav", demo)


# ---------------------------------------------------------------- battle toms

def make_tom(f0):
    n = int(0.28 * SR)
    td = np.arange(n) / SR
    f_curve = f0 * (1.0 + 0.4 * np.exp(-td * 30.0))
    body = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    sos_sk = signal.butter(2, [300, 1500], "bandpass", fs=SR, output="sos")
    skin = signal.sosfilt(sos_sk, rng.standard_normal(n)) * np.exp(-td * 35)
    skin /= np.max(np.abs(skin)) + 1e-12
    env = np.exp(-td * 9.0) * (1 - np.exp(-td / 0.004))
    x = (body + 0.4 * skin) * env
    return x / (np.max(np.abs(x)) + 1e-12)


TOM_H, TOM_M, TOM_L = make_tom(165), make_tom(110), make_tom(80)

demo = np.zeros(int((4 * BAR + 1.0) * SR))
for tom, t0 in [(TOM_H, 0.2), (TOM_M, 0.7), (TOM_L, 1.2)]:     # the three
    add_at(demo, tom, t0, 1.0)
for b in range(2, 4):                                          # the pattern
    for s, tom in {3: TOM_H, 6: TOM_M, 11: TOM_L, 14: TOM_M}.items():
        add_at(demo, tom, b * BAR + s * STEP, 0.8)
run = [TOM_H, TOM_H, TOM_M, TOM_M, TOM_L, TOM_M, TOM_L, TOM_L]
for i, tom in enumerate(run):                                  # the fill run
    add_at(demo, tom, 3 * BAR + 2 * BEAT + i * STEP, 1.0)
write_wav("instrument_25_battle_toms.wav", demo)


# ---------------------------------------------------------------- shaker

def make_shaker():
    n = int(0.055 * SR)
    td = np.arange(n) / SR
    sos_s = signal.butter(2, [3500, 9500], "bandpass", fs=SR, output="sos")
    x = signal.sosfilt(sos_s, rng.standard_normal(n))
    x *= np.exp(-td * 55) * (1 - np.exp(-td / 0.003))
    return x / (np.max(np.abs(x)) + 1e-12)


SHAKER = make_shaker()
SHK_G = [0.9, 0.4, 0.65, 0.4]

demo = np.zeros(int((4 * BAR + 0.5) * SR))
for b in range(4):
    for s in range(16):
        add_at(demo, SHAKER, b * BAR + s * STEP, SHK_G[s % 4])
write_wav("instrument_26_shaker_16ths.wav", demo)


# ---------------------------------------------------------------- rev cymbal

def rev_cymbal(dur=1.6):
    n = int(dur * SR)
    td = np.arange(n) / SR
    sos_c = signal.butter(4, 6000, "high", fs=SR, output="sos")
    x = signal.sosfilt(sos_c, rng.standard_normal(n)) * np.exp(-td * 6.0)
    x = x[::-1].copy()
    return x / (np.max(np.abs(x)) + 1e-12)


demo = np.zeros(int(5.0 * SR))
for t0 in (0.3, 2.6):
    rc = rev_cymbal()
    add_at(demo, rc, t0, 1.0)
    add_at(demo, KICK, t0 + len(rc) / SR, 1.0)      # swell INTO the hit
write_wav("effect_07_reverse_cymbal.wav", demo)


# ---------------------------------------------------------------- groove
# Eight bars of the assembled war groove: kick stack, rolling bass,
# hats + shaker, clap, snare backbeat, battle toms, war-riff acid.

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


def acid_note(m, cutoff, accent=False, slide_to=None, dur=None):
    if dur is None:
        dur = STEP * (1.02 if slide_to else 0.92)
    cutoff = float(np.clip(cutoff * (1.5 if accent else 1.0), 200, 7500))
    f = midi_to_hz(m)
    n = int(dur * SR)
    td = np.arange(n) / SR
    if slide_to is None:
        ph = 2 * np.pi * f * td
    else:
        f2 = midi_to_hz(slide_to)
        fc = f * (f2 / f) ** np.clip((td - 0.45 * dur) / (0.55 * dur), 0, 1)
        ph = 2 * np.pi * np.cumsum(fc) / SR
    x = np.zeros(n)
    for k in range(1, min(48, int(10500 / min(f, midi_to_hz(slide_to))
                                  if slide_to else 10500 / f)) + 1):
        x += np.sin(k * ph) / k

    def res_lp(sig_in, c):
        c = float(min(c, 9000.0))
        sos_lp = signal.butter(2, c, "low", fs=SR, output="sos")
        y = signal.sosfilt(sos_lp, sig_in)
        bpk, apk = signal.iirpeak(min(c, 8000.0), Q=11.0, fs=SR)
        return y + (1.9 if accent else 1.4) * signal.lfilter(bpk, apk, y)

    bright = res_lp(x, cutoff * 3.0)
    dark = res_lp(x, cutoff * 0.75)
    sweep = np.exp(-td / (0.10 if accent else 0.055))
    y = np.tanh(2.8 * (sweep * bright + (1 - sweep) * dark))
    env = (1 - np.exp(-td / 0.0015)) * np.clip((dur - td) / 0.02, 0, 1)
    y *= env
    return y / (np.max(np.abs(y)) + 1e-12)


PB38 = psy_bass_note(38)
OHAT = make_hat(open_=True)
CHAT = make_hat()
CLAP = make_clap()
RIFF_WAR1 = [(50, 1, None), (None, 0, None), (50, 0, None), (50, 0, None),
             (None, 0, None), (50, 0, None), (51, 1, 50), (None, 0, None),
             (58, 1, 57), (57, 0, None), (None, 0, None), (50, 0, None),
             (54, 0, None), (None, 0, None), (51, 0, 50), (50, 0, None)]
TOM_PAT = {3: TOM_H, 6: TOM_M, 11: TOM_L, 14: TOM_M}

# v2 sub boom — the second half of the kick's wall-shake (see the track
# script): a pure 50->37 Hz sine sustaining the whole beat under every hit
n_bm = int(0.40 * SR)
td_bm = np.arange(n_bm) / SR
f_bm = 37.0 + 13.0 * np.exp(-td_bm * 12.0)
BOOM = np.sin(2 * np.pi * np.cumsum(f_bm) / SR) * (
    (1 - np.exp(-td_bm / 0.003)) * np.exp(-td_bm * 1.2) *
    np.clip((0.40 - td_bm) / 0.06, 0, 1))

NB = 8
demo = np.zeros(int((NB * BAR + 1.0) * SR))
for b in range(NB):
    for beat in range(4):
        t0 = b * BAR + beat * BEAT
        add_at(demo, KICK, t0, 1.0)
        add_at(demo, BOOM, t0, 0.60)
        add_at(demo, OHAT, t0 + 0.5 * BEAT, 0.26)
        for s in (1, 2, 3):
            # sidechain-style: the first bass 16th after the kick ducked
            duck = 0.45 if s == 1 else 1.0
            add_at(demo, PB38, t0 + s * STEP,
                   duck * 0.70 * (0.8, 0.7, 0.95)[s - 1])
    for beat in (1, 3):
        add_at(demo, CLAP, b * BAR + beat * BEAT, 0.30)
        add_at(demo, SNARE, b * BAR + beat * BEAT, 0.22)
    for s in range(16):
        if s % 2 == 1:
            add_at(demo, CHAT, b * BAR + s * STEP, 0.09)
        add_at(demo, SHAKER, b * BAR + s * STEP, 0.10 * SHK_G[s % 4])
    if b >= 2:
        for s, tom in TOM_PAT.items():
            add_at(demo, tom, b * BAR + s * STEP, 0.40)
    if b >= 4:
        base = 1500 + 700 * np.sin(2 * np.pi * (b - 4) / 8)
        for s, (m, acc, sl) in enumerate(RIFF_WAR1):
            if m is None:
                continue
            add_at(demo, acid_note(m, base, accent=bool(acc), slide_to=sl),
                   b * BAR + s * STEP, 0.38)
sos_shelf = signal.butter(2, 3000, "high", fs=SR, output="sos")
demo += 0.22 * signal.sosfilt(sos_shelf, demo)
sos_sub = signal.butter(2, 95, "low", fs=SR, output="sos")
demo += 0.34 * signal.sosfilt(sos_sub, demo)        # the room-shake shelf
sos_deep = signal.butter(2, 55, "low", fs=SR, output="sos")
demo += 0.30 * signal.sosfilt(sos_deep, demo)       # v2: the deep shelf
write_wav("rhythm_05_war_groove_148bpm.wav", demo)


# ---------------------------------------------------------------- README

readme = """\
Samples introduced by generate_fall_of_arrakeen.py ("The Fall of Arrakeen")
===========================================================================

instrument_22_kick_stack_room.wav
    The room-shaker, built from feedback that the album lacked "a beat
    which shakes the entire room" — and deepened again (v2) after "the
    BASS is still not there... a lot deeper and heavier". A stack: the
    punch+click trance kick (punch landing at 44 Hz) PLUS a long sub
    tail (55 -> 37 Hz over ~0.42 s — D1 itself, nearly a full beat at
    148 BPM) so the low end never stops moving between hits. Demo:
    four single hits, then four-to-the-floor. Play this LOUD.

instrument_23_field_snare_march.wav
    Military field snare: tone pair (185 + 330 Hz) + snappy bandpassed
    noise. The march bar has accents preceded by two-ghost drags; every
    fourth bar ends in a buzz-roll crescendo. The identity of the
    track's PREPARATION section.

instrument_24_war_horn.wav
    Carnyx-style war horn: 12 brassy harmonics with a pitch scoop into
    each phrase, a slow 31 Hz growl, and a formant bump at 450-900 Hz.
    Demo: the D-Eb-D war call, then a long growled blast stacked with
    its lower octave.

instrument_25_battle_toms.wav
    Three pitched toms (165 / 110 / 80 Hz, pitch dropping 40 % at the
    attack, with skin noise). Demo: each drum, the syncopated two-bar
    pattern, then the descending eight-hit fill run.

instrument_26_shaker_16ths.wav
    Soft shaker, bandpassed 3.5-9.5 kHz, on 16ths with a
    strong/weak/mid/weak accent cycle — fills the grid between hats.

effect_07_reverse_cymbal.wav
    Reversed cymbal swell (highpassed 6 kHz, exponential decay, time-
    flipped) leading into a kick hit — the standard "inhale" before a
    drop boundary.

rhythm_05_war_groove_148bpm.wav
    The assembled war groove (v2): kick stack + sub boom (a pure
    50->37 Hz sine sustaining each beat), sidechain-ducked rolling
    bass, hats + shaker, clap + snare backbeat, battle toms, and the
    WAR1 acid riff with its Bb->A war-cry fall — finished with all
    three master shelves (high + low + deep). This is the loudest,
    heaviest groove on the album.
"""
with open(os.path.join(OUT_DIR, "README_arrakeen.txt"), "w") as fh:
    fh.write(readme)
print(f"wrote {os.path.join(OUT_DIR, 'README_arrakeen.txt')}")
print("\nAll fall-of-arrakeen samples written — nothing overwritten.")
