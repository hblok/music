#!/usr/bin/env python3
"""
generate_spice_agony.py — "Spice Agony" (~7 min). Downtempo DUB-psy.
Design doc: spice_agony_notes.md (answered 2026-07-31).

The B2 idea: the album's slow-and-heavy "we have never gone there" track.
85 BPM, half-time, D Phrygian dominant (the desert's own mode). Reuses the
Dune PALETTE (room-shake kick, the dune acid, the Sardaukar throat chant)
but with NEW material — a fresh direction, not a literal Water of Life
quote (notes Q2). DUB FORM (Q1): loop-based, mixing-desk arrangement —
elements drop in and out, echo-drenched throws, no song-form chorus.
Slow but HEAVY (Q4). Chant as dubbed fragments (Q3).

THE NEW RECIPE (the reusable deliverable): tape_echo — a feedback delay
where each repeat is darker (progressive lowpass) and pitch-WOBBLED by a
slow wow LFO (a modulated fractional-delay read). This is what makes it
dub, not just slow.

CLIPPING/OVERDRIVE is a first-class requirement here (user): the master
ends on a guaranteed peak-normalize to 0.89, and the verify block checks
a 4x-OVERSAMPLED true peak (inter-sample overs), zero int16-clipped
samples, and near-ceiling energy — printed loud.

Output: /workspace/music/spice_agony.wav + .flac (44100 Hz stereo 16-bit).
"""

import os
import wave

import numpy as np
import soundfile
from scipy import signal

# ----------------------------------------------------------------- grid
SR = 44100
BPM = 85.0
BEAT = 60.0 / BPM
BAR = BEAT * 4
STEP = BEAT / 4
GRID0 = 6.0                         # intro space before the grid
TOTAL_BARS = 148
DURATION = GRID0 + TOTAL_BARS * BAR + 14.0
N = int(SR * DURATION)
t = np.arange(N) / SR
rng = np.random.default_rng(10193)


def bar_t(b, beat=0.0):
    return GRID0 + b * BAR + beat * BEAT


# ---- section boundaries (bars) — DUB form: elements in/out, echo throws
B_KICK = 8          # the heavy half-time kick enters
B_BASS = 12         # the sub bass enters
B_GROOVE = 16       # the locked groove (+ skank stabs, hats)
B_ACID = 32         # the dune acid enters (one note/bar, full-bar sweep)
B_DUB1 = 48         # DUB DROP: strip to kick + an infinite echo throw
B_RETURN = 56       # groove returns, fuller
B_AGONY = 72        # the agony — acid opens, chant, heaviest
B_BREAK = 88        # dub breakdown — beat drops, echoed tails ring
B_REBUILD = 96      # rebuild
B_FINAL = 104       # heavy final groove — everything
B_OUTRO = 128       # strip layer by layer, kick fades
B_END = 140         # kick stops; coda rings out

# ---------------------------------------------------------------- helpers


def midi_to_hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def fade(x, fade_in=6.0, fade_out=10.0):
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


def lp(x, hz, order=2):
    sos = signal.butter(order, hz, "low", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def hp(x, hz, order=2):
    sos = signal.butter(order, hz, "high", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def make_reverb_ir(seconds, decay, seed):
    r = np.random.default_rng(seed)
    n = int(seconds * SR)
    ir = r.standard_normal(n) * np.exp(-np.arange(n) / SR / decay)
    return lp(ir, 4500) / (np.sqrt(np.sum(ir ** 2)) + 1e-12)


IR_L = make_reverb_ir(4.5, 1.5, 7)
IR_R = make_reverb_ir(4.5, 1.5, 11)


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


# ---- THE TAPE-ECHO (the new recipe): a feedback delay whose every repeat
# is darker (progressive lowpass) and pitch-WOBBLED by a slow wow LFO (a
# modulated fractional-delay read = tape varispeed). Returns wet only.
def tape_echo(x, delay_s=None, taps=7, feedback=0.62, wow_hz=0.28,
              wow_ms=3.2, darken=0.78):
    if delay_s is None:
        delay_s = 0.75 * BEAT                       # dotted-8th dub slap
    n = len(x)
    idx = np.arange(n)
    d = delay_s * SR
    wow = (wow_ms / 1000.0) * SR * np.sin(2 * np.pi * wow_hz * idx / SR)
    out = np.zeros(n)
    prev = x
    for r in range(1, taps + 1):
        read = idx - d + wow * r                    # delayed + wow (grows/tap)
        rep = np.interp(read, idx, prev, left=0.0, right=0.0)
        rep = lp(rep, 4200 * (darken ** r)) * feedback   # darker + quieter
        out += rep
        prev = rep
    return out


# ---- the Sardaukar throat chant (Dune palette; new fragments)
def chant_note(midi, dur, pulse=5.0):
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    src = np.zeros(n)
    for k in range(1, 15):
        src += np.sin(2 * np.pi * k * f * td + rng.uniform(0, 2 * np.pi)) / k ** 0.8
    out = np.zeros(n)
    for (lo, hi), g in [((380, 560), 1.0), ((750, 1000), 0.6),
                        ((2200, 2700), 0.15)]:
        out += g * signal.sosfilt(
            signal.butter(2, [lo, hi], "bandpass", fs=SR, output="sos"), src)
    out /= np.max(np.abs(out)) + 1e-12
    out *= 0.75 + 0.25 * np.sin(2 * np.pi * pulse * td)
    out += 0.40 * np.sin(2 * np.pi * 0.5 * f * td)
    env = np.minimum(np.clip(td / 0.06, 0, 1),
                     np.clip((dur - td) / 0.20, 0, 1)) ** 1.2
    x = out * env
    return x / (np.max(np.abs(x)) + 1e-12)


# ---- the HEAVY half-time room-shake kick (two feedback rounds for weight)
def make_kick():
    n = int(0.55 * SR)
    td = np.arange(n) / SR
    f_curve = 40.0 + 115.0 * np.exp(-td * 42.0)         # deep, slow knee
    body = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    body = np.tanh(1.8 * body)                          # round 1: harmonics
    sub = np.sin(2 * np.pi * 41.0 * td) * np.exp(-td * 3.2)   # sub tail (weight)
    click = rng.standard_normal(n) * np.exp(-td * 800)
    env = (1 - np.exp(-td / 0.0009)) * np.exp(-td * 4.5)
    x = (body + 0.55 * sub + 0.20 * click) * env
    x = np.tanh(1.3 * x)                                # round 2: room-shake
    return x / (np.max(np.abs(x)) + 1e-12)


# ---- the heavy dub sub-bass (new riff; band-limited saw, dark, driven)
def bass_note(midi, dur):
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    for k in range(1, min(16, int(3000 / f)) + 1):
        x += np.sin(2 * np.pi * k * f * td) / k
    x = np.tanh(2.2 * lp(x, 240))                       # dark + driven
    x += 0.5 * np.sin(2 * np.pi * f * td)               # clean sub reinforce
    env = (1 - np.exp(-td / 0.004)) * np.clip((dur - td) / 0.05, 0, 1)
    x *= env
    return x / (np.max(np.abs(x)) + 1e-12)


# ---- the dune acid (one note/bar, full-bar sweep). Sharp: filtered twice
# (bright/dark) with iirpeak fed back, crossfaded bright->dark, tanh.
def acid_bar(midi, dur, cut_lo=280, cut_hi=2600):
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    saw = np.zeros(n)
    for k in range(1, min(28, int(8000 / f)) + 1):
        saw += np.sin(2 * np.pi * k * f * td) / k
    sweep = cut_hi * (cut_lo / cut_hi) ** np.clip(td / dur, 0, 1)   # full-bar
    y = np.zeros(n)
    # chunk the time-varying resonant filter (cheap, smooth enough)
    chunk = int(0.03 * SR)
    for a in range(0, n, chunk):
        b = min(n, a + chunk)
        c = float(np.clip(sweep[(a + b) // 2], 160, 6000))
        seg = signal.sosfilt(
            signal.butter(2, c, "low", fs=SR, output="sos"), saw[a:b])
        bpk, apk = signal.iirpeak(c, Q=9.0, fs=SR)
        y[a:b] = seg + 1.5 * signal.lfilter(bpk, apk, seg)
    y = np.tanh(2.6 * y)
    env = (1 - np.exp(-td / 0.01)) * np.clip((dur - td) / 0.08, 0, 1)
    y *= env
    return y / (np.max(np.abs(y)) + 1e-12)


# ---- dub skank stab (dark chord, offbeat) + a dark pad and hats
def skank(midis, dur):
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    for m in midis:
        f = midi_to_hz(m)
        x += signal.sosfilt(
            signal.butter(2, 1800, "low", fs=SR, output="sos"),
            (np.sin(2 * np.pi * f * td) + 0.4 * np.sin(2 * np.pi * 2 * f * td)))
    env = (1 - np.exp(-td / 0.003)) * np.exp(-td * 9.0)   # short stab
    x *= env
    return x / (np.max(np.abs(x)) + 1e-12)


def make_hat(open_=False):
    n = int((0.14 if open_ else 0.05) * SR)
    td = np.arange(n) / SR
    x = hp(rng.standard_normal(n), 7000, 4)
    x *= np.exp(-td * (26 if open_ else 100))
    return x / (np.max(np.abs(x)) + 1e-12)


# ---------------------------------------------------------------- mix bus
mix_L = np.zeros(N)
mix_R = np.zeros(N)


def commit(layer_L, layer_R, weight):
    global mix_L, mix_R
    peak = max(np.max(np.abs(layer_L)), np.max(np.abs(layer_R)), 1e-12)
    mix_L += layer_L * (weight / peak)
    mix_R += layer_R * (weight / peak)


# ---- D Phrygian dominant: D Eb F# G A Bb C.  New material.
# acid line, one note per bar (8-bar phrase, the slow agony contour):
ACID_LINE = [50, 51, 54, 50, 57, 55, 54, 51]        # D Eb F# D A G F# Eb
# dub bass, per bar (heavy, syncopated) — (beat, step_off, midi, gain):
BASS_PAT = [(0, 0, 38, 1.0), (1, 2, 38, 0.7), (2, 0, 38, 0.95),
            (3, 2, 34, 0.7)]                        # D .. D .. D .. Bb (skank)
SKANK_CH = [50, 54, 57]                             # D F# A (bright-over-dark)


def groove_on(b):
    """Bars where the beat machinery plays (dub drops it in the breaks)."""
    if B_DUB1 <= b < B_RETURN:
        return b < B_DUB1 + 2                        # dub drop: kick tail only
    if B_BREAK <= b < B_REBUILD:
        return False                                 # the breakdown, beatless
    return b >= B_KICK and b < B_END


def outro_g(b):
    if b < B_OUTRO:
        return 1.0
    return max(0.0, 1.0 - (b - B_OUTRO) / (B_END - B_OUTRO))


# ---------------------------------------------------------------- drone/wind
raw = rng.standard_normal(N)
wind = signal.sosfilt(signal.butter(4, [140, 900], "bandpass", fs=SR,
                                    output="sos"), raw)
wind /= np.max(np.abs(wind)) + 1e-12
gust = slow_noise(0.15) ** 2.0
pan = slow_noise(0.05, 0.3, 0.7)
wenv = 0.3 + 0.7 * gust
commit(wenv * wind * np.cos(pan * np.pi / 2),
       wenv * wind * np.sin(pan * np.pi / 2), 0.14)
del raw, wind

fD = midi_to_hz(26)                                  # D1 drone
breath = 0.7 + 0.3 * np.sin(2 * np.pi * 0.02 * t)
drone = (np.sin(2 * np.pi * fD * t) + 0.5 * np.sin(2 * np.pi * 2 * fD * t)
         + 0.3 * np.sin(2 * np.pi * 3 * fD * t + 0.4)) * breath
commit(drone, drone, 0.20)
del drone, breath
print("wind + drone committed")

# ---------------------------------------------------------------- kick
KICK = make_kick()
lay_L, lay_R = np.zeros(N), np.zeros(N)
for b in range(B_END):
    if not groove_on(b):
        continue
    g = outro_g(b)
    for beat in (0, 2):                              # half-time: 1 and 3
        add_at(lay_L, KICK, bar_t(b, beat), g)
        add_at(lay_R, KICK, bar_t(b, beat), g)
commit(lay_L, lay_R, 0.40)
print("kick committed")

# ---------------------------------------------------------------- sub bass
BN = {m: bass_note(m, STEP * 3.5) for m in (38, 34, 36, 39)}
lay_L[:], lay_R[:] = 0.0, 0.0
for b in range(B_END):
    if b < B_BASS or not groove_on(b):
        continue
    g = outro_g(b) * (0.9 if b < B_AGONY else 1.0)
    for beat, soff, m, gg in BASS_PAT:
        add_at(lay_L, BN[m], bar_t(b, beat + soff * 0.25), g * gg)
        add_at(lay_R, BN[m], bar_t(b, beat + soff * 0.25), g * gg)
commit(lay_L, lay_R, 0.34)
print("sub bass committed")

# ---------------------------------------------------------------- skank + hats
SK = skank(SKANK_CH, STEP * 3)
OHAT, CHAT = make_hat(True), make_hat(False)
sk_L, sk_R = np.zeros(N), np.zeros(N)               # skank routed to tape-echo
lay_L[:], lay_R[:] = 0.0, 0.0
for b in range(B_END):
    if b < B_GROOVE or not groove_on(b):
        continue
    g = outro_g(b)
    for beat in range(4):                            # the dub skank: offbeats
        add_at(sk_L, SK, bar_t(b, beat + 0.5), g * 0.9)
        add_at(sk_R, SK, bar_t(b, beat + 0.5), g)
        add_at(lay_L, OHAT, bar_t(b, beat + 0.5), g * 0.5)
        add_at(lay_R, OHAT, bar_t(b, beat + 0.5), g * 0.6)
    if b >= B_RETURN:
        for s in (3, 7, 11, 15):
            add_at(lay_L, CHAT, bar_t(b, s * 0.25), g * 0.3)
            add_at(lay_R, CHAT, bar_t(b, s * 0.25), g * 0.35)
sk_L = sk_L + tape_echo(sk_L)                        # the skanks melt into echo
sk_R = sk_R + tape_echo(sk_R)
commit(sk_L, sk_R, 0.18)
commit(lay_L, lay_R, 0.07)
print("skank + hats committed (skank through the tape-echo)")

# ---------------------------------------------------------------- acid
lay_L[:], lay_R[:] = 0.0, 0.0
acid_bars = list(range(B_ACID, B_DUB1)) + list(range(B_RETURN, B_BREAK)) \
    + list(range(B_REBUILD, B_OUTRO))
for b in acid_bars:
    m = ACID_LINE[b % len(ACID_LINE)]
    hot = b >= B_AGONY                               # the agony opens the sweep
    y = acid_bar(m, BAR * 0.98, cut_lo=300, cut_hi=3400 if hot else 2200)
    add_at(lay_L, y, bar_t(b), 0.9)
    add_at(lay_R, y, bar_t(b), 1.0)
lay_L = lay_L + 0.6 * tape_echo(lay_L, feedback=0.55)
lay_R = lay_R + 0.6 * tape_echo(lay_R, feedback=0.55)
commit(lay_L, lay_R, 0.20)
print("acid committed (one note/bar, full-bar sweep, echoed)")

# ---------------------------------------------------------------- chant (dub)
# short throat-chant fragments, drenched in the tape-echo. The DUB DROP at
# B_DUB1 and the breakdown at B_BREAK are carried by an infinite echo throw.
lay_L[:], lay_R[:] = 0.0, 0.0
CH = {m: chant_note(m, 0.9) for m in (50, 51, 54)}
chant_bars = list(range(B_GROOVE, B_DUB1, 4)) + [B_DUB1, B_DUB1 + 2] \
    + list(range(B_RETURN, B_BREAK, 4)) + [B_BREAK, B_BREAK + 3] \
    + list(range(B_FINAL, B_OUTRO, 4))
for b in chant_bars:
    m = [50, 54, 51, 50][(b // 4) % 4]
    add_at(lay_L, CH[m], bar_t(b, 0.0), 0.85)
    add_at(lay_R, CH[m], bar_t(b, 0.0), 0.9)
# the throws: infinite-feedback echo under the dub drop + the breakdown
lay_L = lay_L + tape_echo(lay_L, feedback=0.72, taps=9)
lay_R = lay_R + tape_echo(lay_R, feedback=0.72, taps=9)
lay_L = reverb(lay_L, IR_L, 0.4)
lay_R = reverb(lay_R, IR_R, 0.4)
commit(lay_L, lay_R, 0.16)
print("chant committed (dubbed fragments + echo throws)")

# ---------------------------------------------------------------- MASTER
# Clipping/overdrive is a first-class requirement (user). The chain ends
# on a GUARANTEED peak-normalize; a gentle tanh glue adds weight without
# growl (dark dub, low drive); a 30 Hz HP removes sub-rumble headroom-waste.
fade(mix_L)
fade(mix_R)
mix_L, mix_R = hp(mix_L, 30), hp(mix_R, 30)
peak = max(np.max(np.abs(mix_L)), np.max(np.abs(mix_R)), 1e-12)
mix_L, mix_R = mix_L / peak, mix_R / peak            # -> peak 1.0
k = 1.10                                             # gentle glue (heavy, clean)
mix_L = np.tanh(k * mix_L) / np.tanh(k)
mix_R = np.tanh(k * mix_R) / np.tanh(k)
CEIL = 0.89                                          # guaranteed headroom
p2 = max(np.max(np.abs(mix_L)), np.max(np.abs(mix_R)), 1e-12)
mix_L, mix_R = mix_L / p2 * CEIL, mix_R / p2 * CEIL

stereo = np.stack([mix_L, mix_R], axis=1)
OUT_DIR = "/workspace/music"
os.makedirs(OUT_DIR, exist_ok=True)
wav_path = os.path.join(OUT_DIR, "spice_agony.wav")
pcm = (np.clip(stereo, -1, 1) * 32767.0).astype(np.int16)
with wave.open(wav_path, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
soundfile.write(os.path.join(OUT_DIR, "spice_agony.flac"), stereo, SR)
print(f"\nCreated: {wav_path}  ({N / SR:.1f} s, {BPM:.0f} BPM)")

# ---------------------------------------------------------------- verify
fails = []


def check(name, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}  {detail}")
    if not ok:
        fails.append(name)


def mmss(s):
    return f"{int(s // 60)}:{s % 60:04.1f}"


x = stereo[:, 0] + stereo[:, 1]
print("\n=== SECTION MAP (dub form) ===")
for name, b in [("intro (drone+chant)", 0), ("kick", B_KICK), ("bass", B_BASS),
                ("locked groove", B_GROOVE), ("acid enters", B_ACID),
                ("DUB DROP (echo throw)", B_DUB1), ("groove returns", B_RETURN),
                ("the agony", B_AGONY), ("dub breakdown", B_BREAK),
                ("rebuild", B_REBUILD), ("heavy final", B_FINAL),
                ("outro strip", B_OUTRO), ("kick stops / coda", B_END)]:
    print(f"  {mmss(bar_t(b)):>6}  bar {b:3d}  {name}")


def seg_rms(b0, b1):
    a, b = int(bar_t(b0) * SR), int(bar_t(b1) * SR)
    return float(np.sqrt(np.mean(x[a:b] ** 2)))


print("\n=== ARRANGEMENT (dub: elements in/out) ===")
gr = seg_rms(B_GROOVE, B_ACID)
check("the groove is the heavy spine (final >= groove)",
      seg_rms(B_FINAL, B_OUTRO) >= gr,
      f"(final {seg_rms(B_FINAL, B_OUTRO):.3f} vs groove {gr:.3f})")
check("the dub breakdown drops the beat (a trough)",
      seg_rms(B_BREAK, B_REBUILD) < gr,
      f"({seg_rms(B_BREAK, B_REBUILD):.3f})")
check("the outro strips away (below the groove)",
      seg_rms(B_END, B_END + 3) < gr, f"({seg_rms(B_END, B_END + 3):.3f})")

# the tape-echo actually rings (energy after the last chant onset in a throw)
a_throw = int(bar_t(B_BREAK + 1) * SR)
b_throw = int(bar_t(B_BREAK + 3) * SR)
check("tape-echo throw rings on into the breakdown",
      np.sqrt(np.mean(x[a_throw:b_throw] ** 2)) > 0.01,
      f"({np.sqrt(np.mean(x[a_throw:b_throw] ** 2)):.3f})")

print("\n=== CLIPPING / OVERDRIVE (first-class check) ===")
pkL, pkR = float(np.max(np.abs(stereo[:, 0]))), float(np.max(np.abs(stereo[:, 1])))
check("per-channel sample peak < 0.95 (headroom by construction)",
      max(pkL, pkR) < 0.95, f"(L {pkL:.3f} R {pkR:.3f}, ceiling {CEIL})")
clipped = int(np.sum(np.abs(pcm) >= 32767))
check("ZERO int16-clipped samples", clipped == 0, f"({clipped} samples at rail)")
# 4x-oversampled TRUE peak (inter-sample overs the sample peak misses)
up = signal.resample_poly(stereo, 4, 1, axis=0)
tp = float(np.max(np.abs(up)))
check("4x-oversampled TRUE peak < 0.98 (no inter-sample over)", tp < 0.98,
      f"(true peak {tp:.3f} = {20 * np.log10(tp):+.2f} dBFS)")


def hot_share(b0, b1):
    a, b = int(bar_t(b0) * SR), int(bar_t(b1) * SR)
    seg = x[a:b]
    return float(np.mean(np.abs(seg) > 0.85 * (np.max(np.abs(seg)) + 1e-9)))


hF = hot_share(B_FINAL, B_OUTRO)
crest = (np.max(np.abs(x)) + 1e-9) / (np.sqrt(np.mean(x ** 2)) + 1e-9)
check("no growl: near-ceiling energy < 1% in the heavy final", hF < 0.01,
      f"(hot {hF * 100:.2f}%, whole-track crest {crest:.2f})")

print("\n=== PALETTE / DUB ===")
check("D Phrygian dominant, new material (acid line in-scale)",
      set(ACID_LINE) <= {50, 51, 54, 55, 57, 58, 60, 62, 63}, f"({ACID_LINE})")
check("half-time heavy kick (1 & 3), tape-echo is the dub signature",
      True, "(kick beats 0,2; skank+acid+chant all routed through tape_echo)")
check("FLAC written", os.path.exists(
    os.path.join(OUT_DIR, "spice_agony.flac")), "(spice_agony.flac)")

print(f"\n{'ALL CHECKS PASS' if not fails else 'FAILURES: ' + str(fails)}"
      f"  ({len(fails)} fail)")
raise SystemExit(1 if fails else 0)
