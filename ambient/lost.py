#!/usr/bin/env python3
"""
lost.py — "Lost" (~7:30). A long-form emotional ambient journey. Not a
groove track: pads, a singing lead voice, nature, and a soft heartbeat
through-line carry the feeling; the only "beat" is that heartbeat, and it
serves the story (slow in love, quickening into dread, calm again in hope).

The arc, in D, moving major -> minor -> dissonance -> major:

  0:00  LOVE          Warmth out of silence. A tender lead theme over a
                      I-vi-IV-V bed (D F#m... D-Bm-G-A). Slow heartbeat,
                      warm breeze.
  1:24  CONFUSION     The major third starts to flicker against the minor
                      (F# vs F natural); pads detune and beat, the theme
                      wanders and loses its way. bVI creeps in.
  2:36  LOSS          The warmth drains to D minor. A falling, mournful
                      version of the theme; rain begins; the heartbeat
                      hollows and slows.
  3:52  DREAD / SCREAM  The flat-second Eb cluster, tremolo strings, a low
                      growl, distant thunder. The heartbeat quickens. A
                      rising human WAIL (Munch's "Scream") crests ~4:58 and
                      collapses into silence.
  5:18  GRIEF         Bare. A lone voice over the sinking drone. Sadness
                      with space to breathe.
  6:12  HOPE          Light returns: sunrise shimmer carrying the major
                      third F#, a stream, birdsong, warm bells. The love
                      theme comes back transformed and resolved; the
                      heartbeat is calm again. A long, unhurried fade.

Everything is synthesized (numpy + scipy); no samples. Output:
/workspace/music/lost.wav + lost.mp3 (192k, ffmpeg).
"""

import os
import subprocess
import wave
import numpy as np
from scipy import signal

SR = 44100
DURATION = 450.0                       # 7:30
N = int(SR * DURATION)
t = np.arange(N) / SR

rng = np.random.default_rng(1893)      # the year Munch painted The Scream

# ----------------------------------------------------------- section times
T_LOVE = 0.0
T_CONF = 84.0
T_LOSS = 156.0
T_DREAD = 232.0
T_GRIEF = 318.0
T_HOPE = 372.0
T_END = DURATION

SCREAM_CREST = 298.0                   # the wail peaks here, then collapses


# ---------------------------------------------------------------- helpers

def midi_to_hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def fade(x, fade_in=3.0, fade_out=6.0):
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


def ramp(points):
    """piecewise-linear control over the whole track. points: [(t, v), ...]"""
    ts = [p[0] for p in points]
    vs = [p[1] for p in points]
    return np.interp(t, ts, vs)


def make_reverb_ir(seconds, decay, seed):
    r = np.random.default_rng(seed)
    n = int(seconds * SR)
    ir = r.standard_normal(n) * np.exp(-np.arange(n) / SR / decay)
    sos = signal.butter(2, 4200, "low", fs=SR, output="sos")
    ir = signal.sosfilt(sos, ir)
    return ir / np.sqrt(np.sum(ir ** 2))


IR_L = make_reverb_ir(4.0, 2.6, 7)
IR_R = make_reverb_ir(4.0, 2.6, 11)


def reverb_mono(x, ir, wet):
    tail = signal.oaconvolve(x, ir)[: len(x)]
    tail /= np.max(np.abs(tail)) + 1e-12
    tail *= np.max(np.abs(x)) + 1e-12
    return (1 - wet) * x + wet * tail


def add_at(buf, x, start_s, gain=1.0):
    i0 = int(start_s * SR)
    end = min(len(buf), i0 + len(x))
    if end > i0:
        buf[i0:end] += x[: end - i0] * gain


def place_stereo(lay_L, lay_R, clip, t0, gain=1.0, wet=0.4, pan=0.5):
    """reverb a mono clip and place it panned into the stereo layer."""
    L = reverb_mono(clip, IR_L, wet)
    R = reverb_mono(clip, IR_R, wet)
    gL = np.cos(pan * np.pi / 2) * gain
    gR = np.sin(pan * np.pi / 2) * gain
    add_at(lay_L, L, t0, gL)
    add_at(lay_R, R, t0, gR)


def glide_curve(notes, n, tau=0.06):
    """notes: [(midi, dur_s)]. one-pole portamento frequency curve."""
    f_target = np.zeros(n)
    edge = 0.0
    for m, d in notes:
        a, b = int(edge * SR), min(n, int((edge + d) * SR))
        f_target[a:b] = midi_to_hz(m)
        edge += d
    i_end = min(n - 1, int(edge * SR))
    f_target[i_end:] = f_target[i_end - 1] if i_end > 0 else midi_to_hz(notes[0][0])
    alpha = 1.0 - np.exp(-1.0 / (tau * SR))
    return signal.lfilter([alpha], [1.0, -(1.0 - alpha)],
                          f_target, zi=[f_target[0] * (1 - alpha)])[0]


# ------------------------------------------------------------- the mix bus

mix_L = np.zeros(N)
mix_R = np.zeros(N)


def commit(layer_L, layer_R, weight):
    global mix_L, mix_R
    peak = max(np.max(np.abs(layer_L)), np.max(np.abs(layer_R)), 1e-12)
    mix_L += layer_L * (weight / peak)
    mix_R += layer_R * (weight / peak)


lay_L = np.zeros(N)
lay_R = np.zeros(N)


def clear():
    lay_L[:] = 0.0
    lay_R[:] = 0.0


# ================================================================ material
# Chord voicings (MIDI). D is home throughout.

D_MAJ = (50, 54, 57, 62)        # D F# A D     (I)
Bmin = (47, 50, 54, 59)         # B D F# B     (vi)
G_MAJ = (43, 50, 55, 59)        # G D G B      (IV)
A_MAJ = (45, 52, 57, 61)        # A E A C#     (V)

D_SUS = (50, 55, 57, 62)        # D G A D      (suspended, unresolved)
D_MIN = (50, 53, 57, 62)        # D F A D      (i)
Bb_MAJ = (46, 50, 53, 58)       # Bb D F Bb    (bVI)
A_SUS = (45, 50, 52, 57)        # A D E A      (Vsus)

G_MIN = (43, 50, 55, 58)        # G D G Bb     (iv)
DARK = (38, 50, 53, 56)         # D2 D F Ab    (i with the tritone b5 = dread)
DARK_EB = (39, 51, 53, 56)      # Eb cluster shadow over the same band

G_MAJ9 = (43, 50, 57, 59)       # G D A B
D_MAJ9 = (50, 54, 57, 64)       # D F# A E     (add9, glowing)
D_GLOW = (38, 50, 57, 66)       # D2 D A F#5   (root + fifth + high major third)

# The love theme — tender, rising then settling (D major).
THEME_LOVE = [(66, 1.3), (69, 1.0), (71, 1.9), (69, 1.1),
              (66, 1.6), (64, 1.1), (62, 2.6)]
# Confusion — the same opening that loses its footing and wanders chromatically.
THEME_CONF = [(66, 1.2), (69, 1.0), (70, 1.4), (68, 1.2),
              (65, 1.4), (63, 1.6), (62, 2.2)]
# Loss — falling, minor, mournful.
THEME_LOSS = [(69, 1.4), (65, 1.2), (62, 2.0), (60, 1.3), (57, 3.2)]
# Grief — a bare sigh, two notes and silence.
THEME_GRIEF = [(65, 2.4), (62, 3.6)]
# Hope — the love theme returns, lifted and resolved up to D5.
THEME_HOPE = [(66, 1.3), (69, 1.1), (71, 1.7), (73, 1.4),
              (74, 2.2), (69, 1.4), (66, 1.6), (62, 3.2)]


# ----------------------------------------------------------------- voice
# A nearly-pure singing lead (ney/duduk family): portamento between notes,
# vibrato that blooms in, a breath of noise, dark lowpass.

def render_voice(notes, harmonics=(1.0, 0.5, 0.22, 0.09, 0.04),
                 vib_rate=5.2, vib_depth=0.004, vib_bloom=1.2,
                 breath=0.10, lowpass=2600.0, tau=0.06,
                 attack=0.18, release=1.0):
    total = sum(d for _, d in notes)
    n = int((total + release + 0.2) * SR)
    td = np.arange(n) / SR
    f = glide_curve(notes, n, tau=tau)
    vib = 1.0 + vib_depth * np.sin(2 * np.pi * vib_rate * td) * \
        np.clip(td / vib_bloom, 0, 1)
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    v = np.zeros(n)
    for k, g in enumerate(harmonics, start=1):
        v += g * np.sin(k * ph)
    if breath > 0:
        sos_b = signal.butter(2, [1200, 4200], "bandpass", fs=SR, output="sos")
        v += breath * signal.sosfilt(sos_b, rng.standard_normal(n))
    env = np.minimum(np.clip(td / attack, 0, 1),
                     np.clip((total + 0.05 - td) / release, 0, 1))
    sos_w = signal.butter(2, lowpass, "low", fs=SR, output="sos")
    v = signal.sosfilt(sos_w, v * env)
    return v / (np.max(np.abs(v)) + 1e-12)


# ----------------------------------------------------------------- pads
# Warm detuned analog strings. detune widens for "confusion" unease.

def pad_chord(chord, dur, attack=4.0, release=4.0, lowpass=950.0,
              detune=0.0009, amp_lo=0.02, amp_hi=0.06):
    n = int(dur * SR)
    td = np.arange(n) / SR
    out_L = np.zeros(n)
    out_R = np.zeros(n)
    for m in chord:
        f = midi_to_hz(m)
        amp = 0.78 + 0.22 * np.sin(2 * np.pi * rng.uniform(amp_lo, amp_hi) * td +
                                   rng.uniform(0, 2 * np.pi))
        for det, gL, gR in [(1 - detune, 1.0, 0.62), (1 + detune, 0.62, 1.0)]:
            ph = 2 * np.pi * f * det * td + rng.uniform(0, 2 * np.pi)
            v = (np.sin(ph) + 0.32 * np.sin(2 * ph) + 0.11 * np.sin(3 * ph)) * amp
            out_L += gL * v
            out_R += gR * v
    env = np.minimum(np.clip(td / attack, 0, 1) ** 1.4,
                     np.clip((dur - td) / release, 0, 1))
    sos_d = signal.butter(2, lowpass, "low", fs=SR, output="sos")
    out_L = signal.sosfilt(sos_d, out_L * env)
    out_R = signal.sosfilt(sos_d, out_R * env)
    peak = max(np.max(np.abs(out_L)), np.max(np.abs(out_R)), 1e-12)
    return out_L / peak, out_R / peak


def place_pad(lay_L, lay_R, chord, t0, dur, gain, wet=0.45, **kw):
    pL, pR = pad_chord(chord, dur, **kw)
    add_at(lay_L, reverb_mono(pL, IR_L, wet), t0, gain)
    add_at(lay_R, reverb_mono(pR, IR_R, wet), t0, gain)


# build the pad schedule: (t0, dur, chord, gain, kwargs)
clear()
PAD_SCHED = []
# LOVE: I-vi-IV-V, warm, the first chord rises slowly out of silence
love_cycle = [D_MAJ, Bmin, G_MAJ, A_MAJ]
tt = 1.0
i = 0
while tt < T_CONF - 2:
    dur = 12.0 if i == 0 else 11.0
    atk = 7.0 if i == 0 else 3.0
    PAD_SCHED.append((tt, dur, love_cycle[i % 4], 0.95,
                      dict(attack=atk, release=3.5, lowpass=1050)))
    tt += 10.0
    i += 1
# CONFUSION: third flickers, pads detune wider and beat
conf_cycle = [D_SUS, D_MIN, Bb_MAJ, A_SUS]
tt = T_CONF
i = 0
while tt < T_LOSS - 2:
    PAD_SCHED.append((tt, 11.0, conf_cycle[i % 4], 0.9,
                      dict(attack=2.5, release=3.0, lowpass=900,
                           detune=0.0042)))
    tt += 9.0
    i += 1
# LOSS: i-bVI-iv-V minor, darker
loss_cycle = [D_MIN, Bb_MAJ, G_MIN, A_MAJ]
tt = T_LOSS
i = 0
while tt < T_DREAD - 2:
    PAD_SCHED.append((tt, 14.0, loss_cycle[i % 4], 0.92,
                      dict(attack=3.5, release=4.0, lowpass=760)))
    tt += 12.0
    i += 1
# DREAD: two long, dark, static beds (tritone, then the Eb shadow)
PAD_SCHED.append((T_DREAD, 46.0, DARK, 0.85,
                  dict(attack=6.0, release=6.0, lowpass=620, detune=0.0050)))
PAD_SCHED.append((T_DREAD + 40, 38.0, DARK_EB, 0.80,
                  dict(attack=6.0, release=8.0, lowpass=560, detune=0.0070)))
# GRIEF: one faint, hollow Dm
PAD_SCHED.append((T_GRIEF, 56.0, D_MIN, 0.55,
                  dict(attack=8.0, release=8.0, lowpass=720)))
# HOPE: warm, brightening, resolving and glowing to the end
PAD_SCHED.append((T_HOPE, 16.0, G_MAJ9, 0.85,
                  dict(attack=7.0, release=4.0, lowpass=1100)))
PAD_SCHED.append((T_HOPE + 14, 16.0, D_MAJ9, 0.9,
                  dict(attack=4.0, release=4.0, lowpass=1300)))
PAD_SCHED.append((T_HOPE + 28, 14.0, A_MAJ, 0.85,
                  dict(attack=3.5, release=4.0, lowpass=1400)))
PAD_SCHED.append((T_HOPE + 40, T_END - (T_HOPE + 40) + 4, D_GLOW, 0.95,
                  dict(attack=5.0, release=8.0, lowpass=1600)))

for t0, dur, chord, gain, kw in PAD_SCHED:
    place_pad(lay_L, lay_R, chord, t0, dur, gain, **kw)
commit(lay_L, lay_R, 0.30)
print(f"pads committed ({len(PAD_SCHED)} chords)")


# ----------------------------------------------------------------- drone
# A D pedal anchoring the whole journey; sinks ~6% through the dread, and
# its breath fattens/darkens by section. Frequency via cumsum so it can bend.

clear()
drone_bend = ramp([(0, 1.0), (T_DREAD, 1.0), (SCREAM_CREST, 0.945),
                   (T_GRIEF + 20, 0.96), (T_HOPE, 1.0), (T_END, 1.0)])
f0 = midi_to_hz(38) * drone_bend          # D2 base
ph = 2 * np.pi * np.cumsum(f0) / SR
breath = 0.85 + 0.15 * np.sin(2 * np.pi * 0.012 * t)
dr = (np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.28 * np.sin(3 * ph) +
      0.18 * np.sin(3.003 * ph))          # slow beating on the 3rd harmonic
# a flat-second partial that only blooms in the dread = "the agony"
agony = ramp([(0, 0), (T_DREAD, 0), (SCREAM_CREST, 0.30),
              (T_GRIEF + 20, 0.12), (T_HOPE, 0), (T_END, 0)])
dr += agony * np.sin(2 ** (1 / 12) * ph)
dr *= breath
sos_dr = signal.butter(2, 320, "low", fs=SR, output="sos")
dr = signal.sosfilt(sos_dr, dr)
dr /= np.max(np.abs(dr)) + 1e-12
drone_gain = ramp([(0, 0.45), (T_CONF, 0.45), (T_LOSS, 0.6),
                   (T_DREAD, 0.7), (SCREAM_CREST, 0.78), (SCREAM_CREST + 14, 0.35),
                   (T_GRIEF, 0.4), (T_HOPE, 0.5), (T_END, 0.5)])
lay_L[:] = dr * drone_gain
lay_R[:] = dr * drone_gain
commit(lay_L, lay_R, 0.26)
print("drone committed")


# ----------------------------------------------------------- lead voice
# The emotional narrator. Love -> wanders -> mourns -> grieves -> returns.

clear()
V_LOVE = render_voice(THEME_LOVE, lowpass=2700)
V_CONF = render_voice(THEME_CONF, lowpass=2400, vib_depth=0.007, tau=0.10)
V_LOSS = render_voice(THEME_LOSS, lowpass=2100, vib_depth=0.006,
                      attack=0.25, release=1.4)
V_GRIEF = render_voice(THEME_GRIEF, lowpass=1900, vib_depth=0.006,
                       attack=0.4, release=2.0)
V_HOPE = render_voice(THEME_HOPE, lowpass=3000, vib_depth=0.0045)

# LOVE: two warm statements, gentle stereo echo
place_stereo(lay_L, lay_R, V_LOVE, 12.0, gain=0.95, wet=0.5, pan=0.45)
place_stereo(lay_L, lay_R, V_LOVE, 12.0 + 2.0, gain=0.22, wet=0.7, pan=0.6)
place_stereo(lay_L, lay_R, V_LOVE, 48.0, gain=0.9, wet=0.5, pan=0.55)
place_stereo(lay_L, lay_R, V_LOVE, 50.0, gain=0.20, wet=0.7, pan=0.4)
# CONFUSION: the theme falters, answered by a higher, lost echo
place_stereo(lay_L, lay_R, V_CONF, 92.0, gain=0.85, wet=0.6, pan=0.4)
place_stereo(lay_L, lay_R, V_CONF, 120.0, gain=0.8, wet=0.65, pan=0.62)
place_stereo(lay_L, lay_R, V_CONF, 122.5, gain=0.25, wet=0.8, pan=0.3)
# LOSS: the falling, mournful line
place_stereo(lay_L, lay_R, V_LOSS, 166.0, gain=0.9, wet=0.6, pan=0.5)
place_stereo(lay_L, lay_R, V_LOSS, 200.0, gain=0.85, wet=0.65, pan=0.45)
# GRIEF: a bare sigh, alone, very wet
place_stereo(lay_L, lay_R, V_GRIEF, 326.0, gain=0.9, wet=0.78, pan=0.5)
place_stereo(lay_L, lay_R, V_GRIEF, 348.0, gain=0.85, wet=0.8, pan=0.55)
# HOPE: the love theme reborn, fuller, resolved
place_stereo(lay_L, lay_R, V_HOPE, 392.0, gain=0.95, wet=0.55, pan=0.5)
place_stereo(lay_L, lay_R, V_HOPE, 394.5, gain=0.25, wet=0.75, pan=0.6)
place_stereo(lay_L, lay_R, V_HOPE, 424.0, gain=0.85, wet=0.6, pan=0.45)
commit(lay_L, lay_R, 0.24)
print("lead voice committed")


# ------------------------------------------------------- tremolo strings
# The dread harmony: a clustered minor-second bed (D, Eb, E, F) with a
# 7 Hz tremolo that touches silence, swelling into the scream.

clear()
def tremolo_cluster(cluster, dur, swell_to=1.0, trem=7.0):
    n = int(dur * SR)
    td = np.arange(n) / SR
    L = np.zeros(n)
    R = np.zeros(n)
    for m in cluster:
        f = midi_to_hz(m)
        for det, gL, gR in [(0.9955, 1.0, 0.55), (1.0045, 0.55, 1.0)]:
            ph = 2 * np.pi * f * det * td + rng.uniform(0, 2 * np.pi)
            v = np.zeros(n)
            for k in range(1, 7):
                v += np.sin(k * ph) / k
            L += gL * v
            R += gR * v
    sos = signal.butter(2, [150, 2400], "bandpass", fs=SR, output="sos")
    L = signal.sosfilt(sos, L)
    R = signal.sosfilt(sos, R)
    tre = (0.5 + 0.5 * np.sin(2 * np.pi * trem * td)) ** 1.2   # touches silence
    swell = np.clip(td / dur, 0, 1) ** 1.6 * swell_to + (1 - swell_to)
    env = tre * swell
    L *= env
    R *= env
    peak = max(np.max(np.abs(L)), np.max(np.abs(R)), 1e-12)
    return L / peak, R / peak

STR_DUR = SCREAM_CREST - T_DREAD + 6      # builds across dread into the crest
sL, sR = tremolo_cluster((50, 51, 52, 53), STR_DUR, swell_to=0.92)
add_at(lay_L, reverb_mono(sL, IR_L, 0.5), T_DREAD, 1.0)
add_at(lay_R, reverb_mono(sR, IR_R, 0.5), T_DREAD, 1.0)
commit(lay_L, lay_R, 0.16)
print("tremolo strings committed")


# --------------------------------------------------------------- growl
# A low brown-noise growl under the dread, swelling to the crest.

clear()
gn_dur = SCREAM_CREST - T_DREAD + 8
ng = int(gn_dur * SR)
brown = np.cumsum(rng.standard_normal(ng))
brown -= np.linspace(brown[0], brown[-1], ng)              # detrend
sos_g = signal.butter(2, 220, "low", fs=SR, output="sos")
brown = signal.sosfilt(sos_g, brown)
brown /= np.max(np.abs(brown)) + 1e-12
gtd = np.arange(ng) / SR
gswell = np.clip(gtd / gn_dur, 0, 1) ** 2.0
brown *= gswell
add_at(lay_L, brown, T_DREAD, 1.0)
add_at(lay_R, brown, T_DREAD, 0.94)
commit(lay_L, lay_R, 0.12)
print("growl committed")


# ---------------------------------------------------------- the scream
# A rising human WAIL: exponential pitch glide up, vibrato widening,
# glottal harmonics through vocal formants, strained with tanh, swelling
# to the crest then cut. This is the figure on the bridge.

clear()
def scream_wail(dur, m0, m1):
    n = int(dur * SR)
    td = np.arange(n) / SR
    prog = td / dur
    f = midi_to_hz(m0) * (midi_to_hz(m1) / midi_to_hz(m0)) ** prog
    vrate = 4.0 + 5.0 * prog
    vdepth = 0.005 + 0.030 * prog
    vib = 1.0 + vdepth * np.sin(2 * np.pi * np.cumsum(vrate) / SR)
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    src = np.zeros(n)
    for k in range(1, 15):
        src += np.sin(k * ph) / k ** 0.8
    src /= np.max(np.abs(src)) + 1e-12
    # vocal "aah" formants
    out = np.zeros(n)
    for lo, hi, g in [(700, 1100, 1.0), (1200, 1700, 0.6), (2500, 3100, 0.3)]:
        sos = signal.butter(2, [lo, hi], "bandpass", fs=SR, output="sos")
        out += g * signal.sosfilt(sos, src)
    out = np.tanh((1.5 + 2.5 * prog) * out)                # growing strain
    env = (1 - np.exp(-td / 0.4)) * (prog ** 1.4)          # crescendo, no decay
    env *= np.clip((dur - td) / 0.05, 0, 1)
    out *= env
    return out / (np.max(np.abs(out)) + 1e-12)

WAIL_DUR = 7.5
wail = scream_wail(WAIL_DUR, 50, 81)                       # D3 climbing to A5
place_stereo(lay_L, lay_R, wail, SCREAM_CREST - WAIL_DUR + 0.5,
             gain=1.0, wet=0.55, pan=0.5)
commit(lay_L, lay_R, 0.17)
print("scream wail committed")


# --------------------------------------------------------------- riser
# Noise swept through rising bandpass bands + a climbing sine under a t^2
# ramp, ending exactly at the crest — air sucked up into the scream.

clear()
RIS_DUR = 18.0
nr = int(RIS_DUR * SR)
rtd = np.arange(nr) / SR
rprog = rtd / RIS_DUR
noise = rng.standard_normal(nr)
riser = np.zeros(nr)
bands = np.linspace(0, 1, 9)
centers = 350 * (5500 / 350) ** bands
for c in centers:
    win = np.clip(1 - np.abs(rprog - (np.log(c / 350) / np.log(5500 / 350))) * 6, 0, 1)
    sos = signal.butter(2, [c * 0.85, c * 1.18], "bandpass", fs=SR, output="sos")
    riser += signal.sosfilt(sos, noise) * win
fc = midi_to_hz(62) * 2.0 ** (2 * rprog)                   # climbs two octaves
riser += 0.4 * np.sin(2 * np.pi * np.cumsum(fc) / SR)
riser *= rprog ** 2
riser /= np.max(np.abs(riser)) + 1e-12
add_at(lay_L, riser, SCREAM_CREST - RIS_DUR, 1.0)
add_at(lay_R, riser, SCREAM_CREST - RIS_DUR, 0.96)
commit(lay_L, lay_R, 0.09)
print("riser committed")


# -------------------------------------------------------------- heartbeat
# The through-line. lub-dub thump pairs; tempo and gain follow the story.

clear()
def heart_thump():
    n = int(0.24 * SR)
    td = np.arange(n) / SR
    f = 27 + 30 * np.exp(-td * 22)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-td * 15)
    sos = signal.butter(2, 180, "low", fs=SR, output="sos")
    thud = signal.sosfilt(sos, rng.standard_normal(n)) * np.exp(-td * 30)
    thud /= np.max(np.abs(thud)) + 1e-12
    x = body + 0.25 * thud
    x *= 1 - np.exp(-td / 0.004)
    return x / (np.max(np.abs(x)) + 1e-12)

THUMP = heart_thump()

def beat_interval(tm):
    if tm < T_CONF:
        return 1.0                         # ~60 bpm, calm
    if tm < T_LOSS:
        return 0.98
    if tm < T_DREAD:
        return 1.15                        # hollow, slowing
    if tm < SCREAM_CREST - 2:              # quickening into dread
        u = (tm - T_DREAD) / (SCREAM_CREST - 2 - T_DREAD)
        return 1.0 - 0.5 * u               # 1.0 -> 0.5 (~120 bpm)
    if tm < T_GRIEF:
        return None                        # stopped at the crest
    if tm < T_HOPE:
        return 1.7                         # very slow, faint
    return 1.0                             # calm again

heart_gain = ramp([(0, 0.55), (T_CONF, 0.5), (T_LOSS, 0.45), (T_DREAD, 0.6),
                   (SCREAM_CREST - 4, 1.0), (SCREAM_CREST, 0.0),
                   (T_GRIEF, 0.3), (T_HOPE, 0.0), (T_HOPE + 6, 0.5),
                   (T_END, 0.4)])

tm = 0.6
while tm < T_END - 1:
    iv = beat_interval(tm)
    if iv is None:
        tm = T_GRIEF + 1.0
        continue
    g = heart_gain[min(N - 1, int(tm * SR))]
    jit = rng.uniform(-0.01, 0.01)
    if T_CONF <= tm < T_LOSS:
        jit += rng.uniform(-0.04, 0.04)    # the unsteady heart of confusion
    add_at(lay_L, THUMP, tm + jit, g)
    add_at(lay_R, THUMP, tm + jit, g)
    add_at(lay_L, THUMP, tm + jit + 0.20, g * 0.6)        # the "dub"
    add_at(lay_R, THUMP, tm + jit + 0.20, g * 0.6)
    tm += iv
commit(lay_L, lay_R, 0.20)
print("heartbeat committed")


# ----------------------------------------------------------------- wind
# A breeze through the whole piece — warm in love, cold and rising in dread,
# gentle again in hope.

clear()
sos_low = signal.butter(2, [120, 900], "bandpass", fs=SR, output="sos")
sos_hiss = signal.butter(2, [2000, 7000], "bandpass", fs=SR, output="sos")
whoosh = signal.sosfilt(sos_low, rng.standard_normal(N))
hiss = signal.sosfilt(sos_hiss, rng.standard_normal(N))
gust = slow_noise(0.18) ** 2.0
front = slow_noise(0.06) ** 1.5
hiss_amt = ramp([(0, 0.10), (T_DREAD, 0.10), (SCREAM_CREST, 0.45),
                 (T_GRIEF, 0.12), (T_HOPE, 0.10), (T_END, 0.08)])
wind = whoosh * (0.5 + 0.5 * gust) + hiss * hiss_amt * (0.4 + 0.6 * front)
wind /= np.max(np.abs(wind)) + 1e-12
pan = slow_noise(0.05)
wind_gain = ramp([(0, 0.5), (T_CONF, 0.45), (T_LOSS, 0.5), (T_DREAD, 0.7),
                  (SCREAM_CREST, 0.85), (SCREAM_CREST + 16, 0.4),
                  (T_GRIEF, 0.4), (T_HOPE, 0.45), (T_END, 0.4)])
wind *= wind_gain
lay_L[:] = wind * np.cos(pan * np.pi / 2)
lay_R[:] = wind * np.sin(pan * np.pi / 2)
commit(lay_L, lay_R, 0.085)
print("wind committed")


# ----------------------------------------------------------------- rain
# Melancholy rain entering with the loss, peaking in the dread, gone by grief.

clear()
sos_rain = signal.butter(2, [1500, 8000], "bandpass", fs=SR, output="sos")
rain = signal.sosfilt(sos_rain, rng.standard_normal(N))
rain *= 0.6 + 0.4 * slow_noise(2.5)                       # patter shimmer
rain /= np.max(np.abs(rain)) + 1e-12
rain_gain = ramp([(0, 0), (T_LOSS - 4, 0), (T_LOSS + 8, 0.7),
                  (T_DREAD, 0.9), (SCREAM_CREST - 6, 1.0), (SCREAM_CREST + 4, 0.0),
                  (T_END, 0)])
rain *= rain_gain
rpan = slow_noise(0.07)
lay_L[:] = rain * np.cos(rpan * np.pi / 2)
lay_R[:] = rain * np.sin(rpan * np.pi / 2)
commit(lay_L, lay_R, 0.06)
print("rain committed")


# --------------------------------------------------------------- thunder
# Two distant rolls in the dread.

clear()
def thunder_roll(dur):
    n = int(dur * SR)
    td = np.arange(n) / SR
    b = np.cumsum(rng.standard_normal(n))
    b -= np.linspace(b[0], b[-1], n)
    sos = signal.butter(2, 180, "low", fs=SR, output="sos")
    b = signal.sosfilt(sos, b)
    b /= np.max(np.abs(b)) + 1e-12
    env = (1 - np.exp(-td / 0.4)) * np.exp(-td / (dur * 0.4))
    env *= 0.7 + 0.3 * slow_noise(1.2)[:n]
    return b * env
add_at(lay_L, thunder_roll(6.0), 252.0, 0.9)
add_at(lay_R, thunder_roll(6.0), 252.0, 0.8)
add_at(lay_L, thunder_roll(7.0), 283.0, 0.8)
add_at(lay_R, thunder_roll(7.0), 283.0, 0.95)
commit(lay_L, lay_R, 0.10)
print("thunder committed")


# ------------------------------------------------------ stream + birds
# The new beginning: water and birdsong arriving with the hope.

clear()
sos_st = signal.butter(2, [400, 2400], "bandpass", fs=SR, output="sos")
stream = signal.sosfilt(sos_st, rng.standard_normal(N))
stream *= 0.5 + 0.5 * slow_noise(3.0)                     # babble
stream /= np.max(np.abs(stream)) + 1e-12
stream_gain = ramp([(0, 0), (T_HOPE - 2, 0), (T_HOPE + 10, 0.7),
                    (T_END - 8, 0.7), (T_END, 0.3)])
stream *= stream_gain
span = slow_noise(0.06)
lay_L[:] = stream * np.cos(span * np.pi / 2)
lay_R[:] = stream * np.sin(span * np.pi / 2)

def birdsong():
    """a short chirp: a quick high vibrato glide."""
    dur = rng.uniform(0.18, 0.4)
    n = int(dur * SR)
    td = np.arange(n) / SR
    f0 = rng.uniform(2400, 3600)
    f = f0 * (1 + 0.18 * np.sin(2 * np.pi * rng.uniform(14, 22) * td)) * \
        (1 + 0.4 * np.clip(td / dur, 0, 1))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR)
    x *= np.sin(np.pi * td / dur) ** 2
    return x / (np.max(np.abs(x)) + 1e-12)

bt = T_HOPE + 6
while bt < T_END - 6:
    chirp = birdsong()
    pan = rng.uniform(0.2, 0.8)
    g = rng.uniform(0.25, 0.55)
    # little phrases of 1-3 chirps
    for j in range(rng.integers(1, 4)):
        place_stereo(lay_L, lay_R, chirp, bt + j * rng.uniform(0.18, 0.35),
                     gain=g, wet=0.5, pan=pan)
    bt += rng.uniform(3.0, 7.0)
commit(lay_L, lay_R, 0.07)
print("stream + birds committed")


# -------------------------------------------------------------- bells
# Soft tuned bells ringing the major third through the hope section.

clear()
def bell(midi, dur=4.0):
    n = int(dur * SR)
    td = np.arange(n) / SR
    f = midi_to_hz(midi)
    x = np.zeros(n)
    for ratio, g, dec in [(1.0, 1.0, 1.2), (2.0, 0.5, 1.6), (2.76, 0.3, 2.2),
                          (5.4, 0.15, 3.2)]:
        x += g * np.sin(2 * np.pi * f * ratio * td) * np.exp(-td * dec)
    x *= 1 - np.exp(-td / 0.003)
    return x / (np.max(np.abs(x)) + 1e-12)

# D major glow: D5, F#5, A5, and the high D — sparse, gentle, brightening
BELL_NOTES = [(74, 0.6), (78, 0.5), (81, 0.45), (86, 0.35)]
bt = T_HOPE + 8
i = 0
while bt < T_END - 5:
    midi, g = BELL_NOTES[i % len(BELL_NOTES)]
    place_stereo(lay_L, lay_R, bell(midi), bt, gain=g,
                 wet=0.65, pan=rng.uniform(0.35, 0.65))
    bt += rng.uniform(2.6, 4.5)
    i += 1
commit(lay_L, lay_R, 0.08)
print("bells committed")


# ------------------------------------------------- sunrise shimmer (hope)
# A rising swept-noise band + pulsing major-third partials: light spreading.

clear()
SH_T0 = T_HOPE + 4
SH_DUR = 30.0
nsh = int(SH_DUR * SR)
shtd = np.arange(nsh) / SR
shprog = shtd / SH_DUR
noise = rng.standard_normal(nsh)
shimmer = np.zeros(nsh)
for k in range(8):
    c = 700 * (3000 / 700) ** (k / 7)
    center_time = k / 7
    win = np.clip(1 - np.abs(shprog - center_time) * 5, 0, 1)
    sos = signal.butter(2, [c * 0.9, c * 1.15], "bandpass", fs=SR, output="sos")
    shimmer += signal.sosfilt(sos, noise) * win
shimmer /= np.max(np.abs(shimmer)) + 1e-12
# warm major-third partials (D5/F#5/A5) pulsing to silence (anti-tinnitus)
for m in (74, 78, 81):
    f = midi_to_hz(m)
    pulse = np.clip(np.sin(2 * np.pi * 0.4 * shtd + rng.uniform(0, 6)), 0, 1) ** 2
    shimmer += 0.4 * np.sin(2 * np.pi * f * shtd) * pulse
swell = np.sin(np.pi * np.clip(shprog / 0.5, 0, 1)) if False else \
    np.clip(shprog / 0.45, 0, 1) * np.clip((1 - shprog) / 0.5, 0, 1)
shimmer *= swell
shimmer /= np.max(np.abs(shimmer)) + 1e-12
add_at(lay_L, reverb_mono(shimmer, IR_L, 0.4), SH_T0, 1.0)
add_at(lay_R, reverb_mono(shimmer, IR_R, 0.4), SH_T0, 0.95)
commit(lay_L, lay_R, 0.07)
print("sunrise shimmer committed")


# ---------------------------------------------------------------- master

fade(mix_L, fade_in=3.0, fade_out=7.0)
fade(mix_R, fade_in=3.0, fade_out=7.0)

peak = max(np.max(np.abs(mix_L)), np.max(np.abs(mix_R)))
mix_L = mix_L / peak * 0.88
mix_R = mix_R / peak * 0.88

stereo = np.empty((N, 2))
stereo[:, 0] = mix_L
stereo[:, 1] = mix_R
pcm = (stereo * 32767.0).astype(np.int16)

OUT_DIR = "/workspace/music"
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, "lost.wav")
with wave.open(OUT, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())

print(f"\nCreated: {os.path.abspath(OUT)}")
print(f"Duration: {N / SR:.1f} s  |  {SR} Hz stereo, 16-bit PCM  |  D, "
      f"major->minor->dissonance->major")

MP3 = os.path.join(OUT_DIR, "lost.mp3")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", OUT,
                "-vn", "-ar", "44100", "-ac", "2", "-b:a", "192k", MP3],
               check=True)
print(f"Created: {os.path.abspath(MP3)}  (192k mp3)")

print("\nSection map:")
SECTIONS = [("LOVE — warmth out of silence", T_LOVE),
            ("CONFUSION — the third flickers", T_CONF),
            ("LOSS — drains to D minor, rain", T_LOSS),
            ("DREAD / SCREAM — cluster, wail", T_DREAD),
            ("  (the wail crests)", SCREAM_CREST),
            ("GRIEF — bare voice + drone", T_GRIEF),
            ("HOPE — shimmer, stream, rebirth", T_HOPE)]
for name, tm in SECTIONS:
    print(f"  {tm:6.1f} s  {name}")
print(f"  {DURATION:6.1f} s  end")

print("\nPer-section RMS:")
bounds = [T_LOVE, T_CONF, T_LOSS, T_DREAD, T_GRIEF, T_HOPE, T_END]
names = ["love", "confusion", "loss", "dread/scream", "grief", "hope"]
for nm, a, b in zip(names, bounds[:-1], bounds[1:]):
    i0, i1 = int(a * SR), int(b * SR)
    r = np.sqrt(np.mean(mix_L[i0:i1] ** 2 + mix_R[i0:i1] ** 2) / 2)
    print(f"  {nm:14s} {r:.3f}")
