#!/usr/bin/env python3
"""Litany Against Fear — the beatless psy track (idea B4).

Design: litany_against_fear_notes.md (reviewed). Eight sections, one per
litany line. The D drone is "I": it fades in first, holds steady while
fear peaks around it, and is the only thing left after the silence.
Everything else is fear — it approaches, densifies, passes through the
stereo field, recedes, is gone.

Fear material: sleeper_awakens' 303 engine at 1/8 speed (RIFF_DARK /
RIFF_SYNC quoted verbatim), the chant's formant stack stretched into
drones, whispered-noise vowels that almost say the words, Eb/E pads
beating against D.

Output: /workspace/music/litany_against_fear.wav  (6:00, beatless)
"""

import wave

import numpy as np
from scipy import signal

SR = 44100
DURATION = 360.0
N = int(SR * DURATION)
t = np.arange(N) / SR

rng = np.random.default_rng(0)  # where the fear has gone: nothing

# 1/8-speed sleeper time base: 145 BPM 16th x 8 -> one slow bar = 13.24 s
SSTEP = 60.0 / 145.0 / 4.0 * 8.0
SBAR = SSTEP * 16

# section boundaries in slow bars (one per litany line)
B_MUST, B_MIND, B_DEATH, B_FACE, B_PASS, B_GONE, B_SIL = 0, 3, 6, 10, 14, 17, 21
T_SIL = B_SIL * SBAR          # 278.1 s — the silence
SIL_LEN = 3.5                 # a held breath, not an ending (user review)
T_REMAIN = T_SIL + SIL_LEN
T_FADE = 330.0                # the drone starts leaving


def bar_t(b):
    return b * SBAR


# ---------------------------------------------------------------- helpers


def midi_to_hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


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


def env_interp(pts):
    """Piecewise-linear gain envelope over the whole track."""
    xs, ys = zip(*pts)
    return np.interp(t, xs, ys)


def pan_gains(pan):
    th = (0.5 + np.clip(pan, -1, 1) * 0.5) * np.pi / 2
    return np.cos(th), np.sin(th)


IR_L = make_reverb_ir(5.0, 1.6, 7)
IR_R = make_reverb_ir(5.0, 1.6, 11)

mix_L = np.zeros(N)
mix_R = np.zeros(N)
fear_L = np.zeros(N)          # the fear bus — traversed in the pass-through
fear_R = np.zeros(N)
N_LAYERS = 0


def commit(dst_L, dst_R, layer_L, layer_R, weight, env=None):
    global N_LAYERS
    N_LAYERS += 1
    peak = max(np.max(np.abs(layer_L)), np.max(np.abs(layer_R)), 1e-12)
    g = weight / peak
    if env is not None:
        dst_L += layer_L * g * env
        dst_R += layer_R * g * env
    else:
        dst_L += layer_L * g
        dst_R += layer_R * g


# ------------------------------------------------- 1. the D drone ("I")

# Purely tonal detuned partials, breathing via slow_noise — a presence,
# not a vacuum cleaner (user review). Dry: it is inside the listener.
drone = np.zeros(N)
for f0, g in [(36.71, 1.0), (73.42, 0.75), (146.83, 0.28)]:
    for det in (0.9985, 1.0015):
        breath = slow_noise(0.035, 0.80, 1.0)
        drone += g * breath * np.sin(2 * np.pi * f0 * det * t
                                     + rng.uniform(0, 2 * np.pi))
sos_d = signal.butter(2, 300, "low", fs=SR, output="sos")
drone = signal.sosfilt(sos_d, drone)
drone_env = env_interp([(0, 0), (22, 1), (T_FADE, 1), (358, 0), (360, 0)])
dr_L = drone * slow_noise(0.03, 0.92, 1.0)
dr_R = drone * slow_noise(0.03, 0.92, 1.0)
DRONE_W = 0.09
commit(mix_L, mix_R, dr_L, dr_R, DRONE_W, drone_env)
# kept for check (c): the drone's own committed signal
dpk = max(np.max(np.abs(dr_L)), np.max(np.abs(dr_R)), 1e-12)
drone_sig = dr_L * (DRONE_W / dpk) * drone_env
print("drone committed (the I)")

# ------------------------------------------- 2. the slowed 303s (fear)

acid_cache = {}


def acid_note8(m, cutoff, accent=False, slide_to=None, dur=None, bloom=0.0):
    """sleeper_awakens' acid engine, time base x8. bloom>0 = single long
    note whose filter opens and closes over `bloom` seconds (rise-only
    if bloom<0: the unresolved final note)."""
    if dur is None:
        dur = SSTEP * (1.02 if slide_to else 0.92)
    cutoff = float(np.clip(cutoff * (1.5 if accent else 1.0), 200, 7500))
    key = (m, int(cutoff // 60), accent, slide_to, round(dur, 2), round(bloom, 1))
    if key in acid_cache:
        return acid_cache[key]
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
    fmin = min(f, midi_to_hz(slide_to)) if slide_to else f
    for k in range(1, min(48, int(10500 / fmin)) + 1):
        x += np.sin(k * ph) / k

    def res_lp(sig_in, c):
        c = float(min(c, 9000.0))
        sos_lp = signal.butter(2, c, "low", fs=SR, output="sos")
        y = signal.sosfilt(sos_lp, sig_in)
        bpk, apk = signal.iirpeak(min(c, 8000.0), Q=11.0, fs=SR)
        return y + (1.9 if accent else 1.4) * signal.lfilter(bpk, apk, y)

    bright = res_lp(x, cutoff * 3.0)
    dark = res_lp(x, cutoff * 0.75)
    if bloom > 0:
        sweep = np.sin(np.pi * np.clip(td / bloom, 0, 1)) ** 1.5
    elif bloom < 0:
        sweep = np.clip(td / -bloom, 0, 1) ** 1.5      # opens, never closes
    else:
        sweep = np.exp(-td / ((0.10 if accent else 0.055) * 8))
    y = np.tanh(2.8 * (sweep * bright + (1 - sweep) * dark))
    env = (1 - np.exp(-td / 0.003)) * np.clip((dur - td) / 0.06, 0, 1)
    y *= env
    y /= np.max(np.abs(y)) + 1e-12
    acid_cache[key] = y
    return y


# 16-step riffs quoted verbatim from sleeper_awakens: (midi, accent, slide)
RIFF_DARK = [(50, 1, None), (None, 0, None), (50, 0, None), (None, 0, None),
             (50, 0, None), (62, 1, None), (None, 0, None), (50, 0, None),
             (51, 0, None), (None, 0, None), (50, 0, None), (None, 0, None),
             (54, 1, None), (None, 0, None), (48, 0, 50), (50, 0, None)]
RIFF_SYNC = [(50, 1, None), (None, 0, None), (50, 0, 51), (51, 0, None),
             (None, 0, None), (50, 0, None), (54, 1, None), (None, 0, None),
             (57, 0, 55), (55, 0, None), (None, 0, None), (50, 0, None),
             (62, 1, None), (None, 0, None), (48, 0, 50), (50, 0, None)]

# per-section cutoff ceilings: the fear's filter opens as it approaches
CUT_HI = env_interp([(0, 700), (bar_t(B_MIND), 900), (bar_t(B_DEATH), 1400),
                     (bar_t(B_FACE), 1800), (bar_t(B_PASS), 2600),
                     (bar_t(B_GONE), 1400), (T_SIL, 900)])


def acid_bars(dst_L, dst_R, b0, b1, riff, pan, offset=0.0):
    for b in range(b0, b1):
        for s, (m, acc, sl) in enumerate(riff):
            if m is None:
                continue
            t0 = bar_t(b) + s * SSTEP + offset
            if t0 >= bar_t(b1) - 0.01:
                continue
            p = s / 16.0                       # bar-position cutoff arc
            hi = CUT_HI[min(N - 1, int(t0 * SR))]
            cut = 250 + (hi - 250) * np.sin(np.pi * p) ** 1.3
            note = acid_note8(m, cut, bool(acc), sl)
            g = 1.0 if acc else 0.75
            gl, gr = pan_gains(pan)
            add_at(dst_L, note, t0, g * gl)
            add_at(dst_R, note, t0, g * gr)


aA_L, aA_R = np.zeros(N), np.zeros(N)
for b in range(B_MUST, B_MIND):                # intro: one bloom per bar
    note = acid_note8(50, 600, dur=SBAR * 0.95, bloom=SBAR * 0.9)
    gl, gr = pan_gains(-0.15)
    add_at(aA_L, note, bar_t(b) + 0.4, 0.55 * gl)
    add_at(aA_R, note, bar_t(b) + 0.4, 0.55 * gr)
acid_bars(aA_L, aA_R, B_MIND, B_SIL - 1, RIFF_DARK, pan=-0.25)
# the last note: 1/16 speed, a slide 48->50 whose filter never resolves —
# cut off by the silence
note = acid_note8(48, 1100, slide_to=50, dur=T_SIL - 0.02 - (bar_t(B_SIL - 1) + 4 * SSTEP * 2),
                  bloom=-(T_SIL - (bar_t(B_SIL - 1) + 4 * SSTEP * 2)))
for st, (m, acc) in enumerate([(50, 1), (50, 0), (51, 0), (50, 0)]):
    nt = acid_note8(m, 900, bool(acc), dur=SSTEP * 2 * 0.92)
    add_at(aA_L, nt, bar_t(B_SIL - 1) + st * SSTEP * 2, (1.0 if acc else 0.75) * 0.7)
    add_at(aA_R, nt, bar_t(B_SIL - 1) + st * SSTEP * 2, (1.0 if acc else 0.75) * 0.75)
add_at(aA_L, note, bar_t(B_SIL - 1) + 4 * SSTEP * 2, 0.8)
add_at(aA_R, note, bar_t(B_SIL - 1) + 4 * SSTEP * 2, 0.85)
aA_env = env_interp([(0, 0.55), (bar_t(B_MIND), 0.6), (bar_t(B_MIND) + 8, 1),
                     (bar_t(B_PASS), 1), (bar_t(B_GONE), 0.75), (T_SIL, 0.75)])
aA_L = reverb(aA_L, IR_L, 0.30)
aA_R = reverb(aA_R, IR_R, 0.30)
commit(fear_L, fear_R, aA_L, aA_R, 0.135, aA_env)
print("acid A committed (RIFF_DARK at 1/8)")

aB_L, aB_R = np.zeros(N), np.zeros(N)
acid_bars(aB_L, aB_R, B_DEATH, B_GONE + 1, RIFF_SYNC, pan=0.3, offset=SBAR / 2)
aB_env = env_interp([(bar_t(B_DEATH), 0), (bar_t(B_DEATH) + 10, 0.8),
                     (bar_t(B_FACE), 1), (bar_t(B_PASS), 1),
                     (bar_t(B_GONE) - 4, 0.6), (bar_t(B_GONE) + 7, 0)])
aB_L = reverb(aB_L, IR_L, 0.30)
aB_R = reverb(aB_R, IR_R, 0.30)
commit(fear_L, fear_R, aB_L, aB_R, 0.10, aB_env)
print("acid B committed (RIFF_SYNC, offset, opposite)")

# --------------------------- 3. formant drones (the chant, stretched)


def formant_drone(midi, t0, t1, seed_off=0):
    """chant_note's formant stack minus the pulse; slow pitch drift so
    the timbre never sits still (user review)."""
    n = int((t1 - t0) * SR)
    td = np.arange(n) / SR
    f = midi_to_hz(midi)
    k_dr = max(4, int((t1 - t0) * 0.05))
    pts = np.random.default_rng(1000 + seed_off).standard_normal(k_dr)
    drift = np.interp(td, np.linspace(0, t1 - t0, k_dr), pts)
    drift = 1.0 + 0.003 * drift / (np.max(np.abs(drift)) + 1e-12)
    src = np.zeros(n)
    ph0 = 2 * np.pi * np.cumsum(f * drift) / SR
    for k in range(1, 15):
        src += np.sin(k * ph0 + rng.uniform(0, 2 * np.pi)) / k ** 0.8
    out = np.zeros(n)
    for (lo, hi), g in [((380, 560), 1.0), ((750, 1000), 0.6),
                        ((2200, 2700), 0.10)]:
        sos_f = signal.butter(2, [lo, hi], "bandpass", fs=SR, output="sos")
        out += g * signal.sosfilt(sos_f, src)
    out += 0.30 * np.sin(0.5 * ph0)
    breath = 0.62 + 0.38 * np.sin(2 * np.pi * 0.05 * td
                                  + rng.uniform(0, 2 * np.pi))
    edge = np.minimum(np.clip(td / 4.0, 0, 1),
                      np.clip((t1 - t0 - td) / 6.0, 0, 1))
    out *= breath * edge
    return out / (np.max(np.abs(out)) + 1e-12)


fdD_L, fdD_R = np.zeros(N), np.zeros(N)
v = formant_drone(50, bar_t(B_MIND), T_SIL - 1.0)
add_at(fdD_L, v, bar_t(B_MIND), 1.0)
add_at(fdD_R, v, bar_t(B_MIND), 1.0)
fdD_L = reverb(fdD_L, IR_L, 0.35)
fdD_R = reverb(fdD_R, IR_R, 0.35)
commit(mix_L, mix_R, fdD_L, fdD_R, 0.08)      # on D: stays with the self
print("formant drone D committed")

fdF_L, fdF_R = np.zeros(N), np.zeros(N)
v = formant_drone(51, bar_t(B_DEATH), bar_t(19), 1)      # Eb — the fear
gl, gr = pan_gains(-0.35)
add_at(fdF_L, v, bar_t(B_DEATH), gl)
add_at(fdF_R, v, bar_t(B_DEATH), gr)
v = formant_drone(52, bar_t(B_FACE), bar_t(18), 2)       # E — closer still
gl, gr = pan_gains(0.4)
add_at(fdF_L, v, bar_t(B_FACE), gl)
add_at(fdF_R, v, bar_t(B_FACE), gr)
fdF_L = reverb(fdF_L, IR_L, 0.35)
fdF_R = reverb(fdF_R, IR_R, 0.35)
commit(fear_L, fear_R, fdF_L, fdF_R, 0.11)
print("formant drones Eb/E committed (the flat seconds)")

# ------------------------------- 4. whispers (the litany, almost said)

VOWELS = {"i": (270, 2300), "e": (530, 1840), "a": (730, 1090),
          "o": (570, 840), "u": (300, 870)}
LINES = {0: ["a", "i", "u", "o", "i"],            # I must not fear
         1: ["i", "i", "e", "a", "i", "e"],       # fear is the mind-killer
         2: ["i", "i", "e", "i", "e", "a"],       # fear is the little-death
         3: ["a", "i", "e", "a", "i"],            # I will face my fear
         4: ["a", "o", "e", "a", "u", "i"],       # pass over me, through me
         5: ["e", "i", "a", "o", "a"]}            # when it has gone past

# pink-weighted noise (user review: not white)
PINK_B = [0.049922035, -0.095993537, 0.050612699, -0.004408786]
PINK_A = [1.0, -2.494956002, 2.017265875, -0.522189400]
SOS_BREATH = signal.butter(2, [2000, 4000], "bandpass", fs=SR, output="sos")
SOS_W_LP = signal.butter(2, 5000, "low", fs=SR, output="sos")


def whisper_phrase(seq, dur):
    n = int(dur * SR)
    td = np.arange(n) / SR
    noise = signal.lfilter(PINK_B, PINK_A, rng.standard_normal(n))
    out = np.zeros(n)
    seg = n // len(seq)
    xf = int(0.08 * SR)
    for i, vw in enumerate(seq):
        f1, f2 = VOWELS[vw]
        b1, a1 = signal.iirpeak(f1, Q=8.0, fs=SR)
        b2, a2 = signal.iirpeak(f2, Q=8.0, fs=SR)
        y = signal.lfilter(b1, a1, noise) + 0.7 * signal.lfilter(b2, a2, noise)
        w = np.zeros(n)
        i0, i1 = i * seg, min(n, (i + 1) * seg + xf)
        w[i0:i1] = 1.0
        if i0 > 0:
            w[i0:i0 + xf] = np.linspace(0, 1, xf)
        if i1 < n:
            w[i1 - xf:i1] = np.linspace(1, 0, xf)
        out += y * w
    out += 0.12 * signal.sosfilt(SOS_BREATH, noise)
    syl = rng.uniform(2.5, 4.0)
    out *= 1.0 - 0.35 * (0.5 + 0.5 * np.sin(2 * np.pi * syl * td
                                            + rng.uniform(0, 2 * np.pi)))
    a, r = 0.25 * dur, 0.35 * dur
    out *= np.minimum(np.clip(td / a, 0, 1), np.clip((dur - td) / r, 0, 1)) ** 1.2
    out = signal.sosfilt(SOS_W_LP, out)
    return out / (np.max(np.abs(out)) + 1e-12)


wh_L, wh_R = np.zeros(N), np.zeros(N)
SCHED = [(bar_t(B_MUST) + 8, bar_t(B_MIND), 7, 11, 0.30, 0),
         (bar_t(B_MIND), bar_t(B_DEATH), 5, 8, 0.50, 1),
         (bar_t(B_DEATH), bar_t(B_FACE), 4, 6, 0.70, 2),
         (bar_t(B_FACE), bar_t(B_PASS), 2.5, 4.5, 1.00, 3),
         (bar_t(B_PASS), bar_t(B_GONE), 4, 7, 0.65, 4),
         (bar_t(B_GONE), T_SIL - 6, 8, 11, 0.35, 5)]
side = 1
for t0s, t1s, glo, ghi, gain, line in SCHED:
    cur = t0s + rng.uniform(0, 2)
    while cur < t1s - 3:
        dur = rng.uniform(2.2, 3.8)
        seq = LINES[line] if line != 5 else ["u", "o", "u"]  # just breath
        ph = whisper_phrase(seq, dur)
        pan = side * rng.uniform(0.4, 0.7)
        gl, gr = pan_gains(pan)
        g = gain * rng.uniform(0.8, 1.0)
        add_at(wh_L, ph, cur, g * gl)
        add_at(wh_R, ph, cur, g * gr)
        side = -side
        if line == 3 and rng.random() < 0.35:          # both ears at the peak
            ph2 = whisper_phrase(LINES[3], dur * 0.9)
            gl2, gr2 = pan_gains(-pan)
            add_at(wh_L, ph2, cur + 0.8, g * 0.8 * gl2)
            add_at(wh_R, ph2, cur + 0.8, g * 0.8 * gr2)
        cur += dur + rng.uniform(glo, ghi)
wh_L = reverb(wh_L, IR_L, 0.35)
wh_R = reverb(wh_R, IR_R, 0.35)
commit(fear_L, fear_R, wh_L, wh_R, 0.135)
print("whispers committed (the litany, almost said)")

# ---------------------------------- 5. fear pads (flat seconds beating)


def pad(midi_pair, t0, t1, pan, seed_off):
    n = int((t1 - t0) * SR)
    td = np.arange(n) / SR
    out = np.zeros(n)
    for midi, g in midi_pair:
        f = midi_to_hz(midi)
        for det in (0.997, 1.0, 1.003):
            out += g * np.sin(2 * np.pi * f * det * td
                              + rng.uniform(0, 2 * np.pi)) / 3
    breath = 0.55 + 0.45 * np.sin(2 * np.pi * 0.045 * td + seed_off)
    edge = np.minimum(np.clip(td / 6.0, 0, 1),
                      np.clip((t1 - t0 - td) / 6.0, 0, 1))
    out *= breath * edge
    return out / (np.max(np.abs(out)) + 1e-12)


pd_L, pd_R = np.zeros(N), np.zeros(N)
x = pad([(39, 1.0), (51, 0.5)], bar_t(B_DEATH), bar_t(19), -0.3, 0.0)
gl, gr = pan_gains(-0.3)
add_at(pd_L, x, bar_t(B_DEATH), gl)
add_at(pd_R, x, bar_t(B_DEATH), gr)
x = pad([(40, 1.0), (52, 0.5)], bar_t(B_FACE), bar_t(18), 0.35, 2.0)
gl, gr = pan_gains(0.35)
add_at(pd_L, x, bar_t(B_FACE), gl)
add_at(pd_R, x, bar_t(B_FACE), gr)
pd_L = reverb(pd_L, IR_L, 0.30)
pd_R = reverb(pd_R, IR_R, 0.30)
commit(fear_L, fear_R, pd_L, pd_R, 0.11)
print("fear pads committed (Eb, E against D)")

# ------------------------------------------------- 6. heartbeat (body)


def doum():
    n = int(0.5 * SR)
    td = np.arange(n) / SR
    f = 35 + 20 * np.exp(-td / 0.06)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR)
    x *= (1 - np.exp(-td / 0.008)) * np.exp(-td / 0.13)
    sos_h = signal.butter(2, 120, "low", fs=SR, output="sos")
    x = signal.sosfilt(sos_h, x)
    return x / (np.max(np.abs(x)) + 1e-12)


DOUM = doum()
hb_L, hb_R = np.zeros(N), np.zeros(N)
BPM_CURVE = [(bar_t(B_DEATH), 50), (bar_t(B_FACE), 62), (158, 72),
             (bar_t(B_PASS), 68), (bar_t(B_GONE), 55), (250, 48), (262, 45)]
cur = bar_t(B_DEATH)
while cur < 262:
    bpm = np.interp(cur, *zip(*BPM_CURVE))
    g = min(1.0, (cur - bar_t(B_DEATH)) / 20.0)        # eases in
    add_at(hb_L, DOUM, cur, g)
    add_at(hb_R, DOUM, cur, g)
    add_at(hb_L, DOUM, cur + 0.35, g * 0.55)           # lub... dub
    add_at(hb_R, DOUM, cur + 0.35, g * 0.55)
    cur += 60.0 / bpm
for tb, g in [(274.3, 0.9), (275.9, 0.7)]:             # the two last beats
    add_at(hb_L, DOUM, tb, g)
    add_at(hb_R, DOUM, tb, g)
    add_at(hb_L, DOUM, tb + 0.35, g * 0.55)
    add_at(hb_R, DOUM, tb + 0.35, g * 0.55)
commit(mix_L, mix_R, hb_L, hb_R, 0.14)
print("heartbeat committed (52 -> 72 -> two last beats)")

# --------------------------------------------------- 7. texture dust


def grain():
    if rng.random() < 0.6:                              # tiny chime
        dur = rng.uniform(0.06, 0.15)
        n = int(dur * SR)
        td = np.arange(n) / SR
        x = np.sin(2 * np.pi * rng.uniform(1200, 3200) * td)
        x *= (td / dur) ** 2                            # reversed: swells, cut
        return x
    dur = rng.uniform(0.3, 0.8)                         # reverse shimmer
    n = int(dur * SR)
    x = rng.standard_normal(n)
    sos_g = signal.butter(2, [500, 2000], "bandpass", fs=SR, output="sos")
    x = signal.sosfilt(sos_g, x)
    return x * (np.arange(n) / n) ** 1.5


du_L, du_R = np.zeros(N), np.zeros(N)
DENS = [(bar_t(B_DEATH), 0.08), (bar_t(B_FACE), 0.3), (158, 0.5),
        (bar_t(B_PASS), 0.4), (210, 0.15), (bar_t(B_GONE), 0.02)]
cur = bar_t(B_DEATH)
while cur < bar_t(B_GONE):
    d = max(0.01, np.interp(cur, *zip(*DENS)))
    g = grain()
    g /= np.max(np.abs(g)) + 1e-12
    gl, gr = pan_gains(rng.uniform(-0.8, 0.8))
    add_at(du_L, g, cur, gl)
    add_at(du_R, g, cur, gr)
    cur += rng.exponential(1.0 / d)
du_L = reverb(du_L, IR_L, 0.5)
du_R = reverb(du_R, IR_R, 0.5)
commit(fear_L, fear_R, du_L, du_R, 0.07)
print("dust committed")

# ------------------------- the pass-through: fear traverses the field

trav0, trav1 = bar_t(B_PASS), bar_t(B_PASS) + 20.0
i0, i1 = int(trav0 * SR), int(trav1 * SR)
seg = slice(i0, i1)
a = np.linspace(-1, 1, i1 - i0)                        # hard L -> hard R
th = (a + 1) * np.pi / 4
w = np.sin(np.pi * np.clip((np.arange(i1 - i0) / (i1 - i0)), 0, 1)) ** 0.5
mono = 0.5 * (fear_L[seg] + fear_R[seg])
fear_L[seg] = (1 - w) * fear_L[seg] + w * mono * np.cos(th) * 1.4
fear_R[seg] = (1 - w) * fear_R[seg] + w * mono * np.sin(th) * 1.4
print("pass-through applied (fear traverses L -> R; the drone holds)")

mix_L += fear_L
mix_R += fear_R

# --------------------------------------------------- master + silence

# no upward normalization — the quiet arc IS the design; only guard peaks
pk = max(np.max(np.abs(mix_L)), np.max(np.abs(mix_R)), 1e-12)
g = min(1.0, 0.95 / pk)
mix_L = np.tanh(1.1 * mix_L * g)
mix_R = np.tanh(1.1 * mix_R * g)

# the silence: 3.5 s of exact digital zero, 40 ms cosine edges
e = int(0.04 * SR)
iS, iE = int(T_SIL * SR), int((T_SIL + SIL_LEN) * SR)
ramp = 0.5 + 0.5 * np.cos(np.pi * np.arange(e) / e)
for buf in (mix_L, mix_R):
    buf[iS - e:iS] *= ramp
    buf[iS:iE] = 0.0
    buf[iE:iE + e] *= ramp[::-1]
print("the silence: where the fear has gone there will be nothing")

ni = int(0.05 * SR)
for buf in (mix_L, mix_R):
    buf[:ni] *= np.linspace(0, 1, ni)
    buf[-ni:] *= np.linspace(1, 0, ni)

# ------------------------------------------------------------------ write

out_path = "/workspace/music/litany_against_fear.wav"
stereo = np.empty(2 * N, dtype=np.int16)
stereo[0::2] = (np.clip(mix_L, -1, 1) * 32767).astype(np.int16)
stereo[1::2] = (np.clip(mix_R, -1, 1) * 32767).astype(np.int16)
with wave.open(out_path, "wb") as w_:
    w_.setnchannels(2)
    w_.setsampwidth(2)
    w_.setframerate(SR)
    w_.writeframes(stereo.tobytes())

print(f"\nCreated: {out_path}")
print(f"Duration: {DURATION:.1f} s  |  {SR} Hz stereo, 16-bit PCM  |  "
      f"beatless (slow bar {SBAR:.2f} s)  |  {N_LAYERS} committed layers")

SECT = [(0.0, "I must not fear"),
        (bar_t(B_MIND), "Fear is the mind-killer"),
        (bar_t(B_DEATH), "Fear is the little-death"),
        (bar_t(B_FACE), "I will face my fear  [peak]"),
        (bar_t(B_PASS), "I will permit it to pass through me"),
        (bar_t(B_GONE), "And when it has gone past"),
        (T_SIL, "there will be nothing  [silence]"),
        (T_REMAIN, "Only I will remain")]
print("Section map + per-section RMS:")
rms = {}
bounds = [s for s, _ in SECT] + [DURATION]
for (s0, name), s1 in zip(SECT, bounds[1:]):
    seg_ = np.concatenate([mix_L[int(s0 * SR):int(s1 * SR)],
                           mix_R[int(s0 * SR):int(s1 * SR)]])
    rms[name] = float(np.sqrt(np.mean(seg_ ** 2)))
    print(f"  {s0:6.1f} s  rms {rms[name]:.3f}  {name}")

loudest = max(rms, key=rms.get)
print(f"\nCheck a — loudest section: {loudest} (rms {rms[loudest]:.3f})")
if "face" not in loudest:
    print("WARNING: the peak is not 'I will face my fear' — rebalance!")
sil = np.sqrt(np.mean(mix_L[iS:iE] ** 2 + mix_R[iS:iE] ** 2))
print(f"Check b — silence RMS: {sil:.6f}" + ("  OK" if sil == 0 else "  FAIL"))
w1 = drone_sig[int(150 * SR):int(165 * SR)]
w2 = drone_sig[int(290 * SR):int(305 * SR)]
r1, r2 = np.sqrt(np.mean(w1 ** 2)), np.sqrt(np.mean(w2 ** 2))
db = 20 * np.log10(r1 / (r2 + 1e-12))
print(f"Check c — drone steadiness (peak vs alone): {db:+.2f} dB"
      + ("  OK" if abs(db) < 1.5 else "  FAIL — the I flinched"))
