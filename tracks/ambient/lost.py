#!/usr/bin/env python3
"""
lost.py — "Lost" (v2, ~7:50). A long-form emotional ambient journey built
from interlocking instruments rather than one melody: a felt piano running
evolving arpeggio patterns, a Karplus-Strong harp answering in counterpoint,
a bowed cello carrying the bass and the laments, a choir pad, glockenspiel
and bells, with a flute as one voice among many. A soft heartbeat is the
through-line. Nature (wind, rain, a stream, birds) frames the scenes.

The "Scream" section is NOT a literal scream — it is Munch's painting:
existential dread and angst, rendered as a slow tolling bell, swirling
dissonant detuned string clusters, a relentless dark piano ostinato that
will not resolve, a polytonal choir, and a sub rumble that swells and recedes
like the painting's undulating sky.

The arc, in D, moving major -> ambiguous -> minor -> dissonance -> major:

  0:00  LOVE        Felt-piano arpeggios over Dmaj9-Bm7-G6/9-A7sus, harp
                    interlocking an eighth behind, cello pedal, flute theme.
  1:30  CONFUSION   Chromatic-mediant harmony (D-F-Bb-Eb-A7b9), the arpeggio
                    leaps and regroups, two voices drift out of phase.
  2:45  LOSS        D minor. Piano thins to slow chords; the cello sings a
                    falling lament; rain.
  4:00  DREAD/ANGST Existential dread: a low tolling bell, swirling dissonant
                    string clusters, a relentless dark piano ostinato, a
                    polytonal choir, sub rumble. Builds in density, never a
                    scream, then dissolves.
  5:30  SADNESS     Bare aftermath: sparse piano, a lone cello, space.
  6:20  HOPE        Light returns: the love arpeggio reborn in major and
                    fuller, glockenspiel and bells, a stream and birdsong,
                    flute and cello in duet. Builds, then a long fade.

Everything is synthesized (numpy + scipy); no samples. Output:
/workspace/music/lost_v2.wav + lost_v2.mp3 (192k, ffmpeg).
"""

import os
import subprocess
import wave
import numpy as np
from scipy import signal

SR = 44100
DURATION = 470.0                       # 7:50
N = int(SR * DURATION)
t = np.arange(N) / SR

rng = np.random.default_rng(1893)      # the year Munch painted The Scream

# ----------------------------------------------------------- section times
T_LOVE = 0.0
T_CONF = 90.0
T_LOSS = 165.0
T_DREAD = 240.0
T_SAD = 330.0
T_HOPE = 380.0
T_END = DURATION


# ---------------------------------------------------------------- helpers

def midi_to_hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def fade(x, fade_in=3.0, fade_out=8.0):
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
    return np.interp(t, [p[0] for p in points], [p[1] for p in points])


def make_reverb_ir(seconds, decay, seed):
    r = np.random.default_rng(seed)
    n = int(seconds * SR)
    ir = r.standard_normal(n) * np.exp(-np.arange(n) / SR / decay)
    sos = signal.butter(2, 4200, "low", fs=SR, output="sos")
    ir = signal.sosfilt(sos, ir)
    return ir / np.sqrt(np.sum(ir ** 2))


IR_L = make_reverb_ir(3.2, 2.4, 7)
IR_R = make_reverb_ir(3.2, 2.4, 11)


def reverb_mono(x, ir, wet):
    tail = signal.oaconvolve(x, ir)[: len(x)]
    tail /= np.max(np.abs(tail)) + 1e-12
    tail *= np.max(np.abs(x)) + 1e-12
    return (1 - wet) * x + wet * tail


def reverb_layer(layL, layR, wet):
    return reverb_mono(layL, IR_L, wet), reverb_mono(layR, IR_R, wet)


def add_at(buf, x, start_s, gain=1.0):
    i0 = int(start_s * SR)
    end = min(len(buf), i0 + len(x))
    if end > i0:
        buf[i0:end] += x[: end - i0] * gain


def place_pan(layL, layR, clip, t0, gain, pan):
    add_at(layL, clip, t0, gain * np.cos(pan * np.pi / 2))
    add_at(layR, clip, t0, gain * np.sin(pan * np.pi / 2))


def place_stereo(layL, layR, clip, t0, gain=1.0, wet=0.4, pan=0.5):
    L = reverb_mono(clip, IR_L, wet)
    R = reverb_mono(clip, IR_R, wet)
    add_at(layL, L, t0, gain * np.cos(pan * np.pi / 2))
    add_at(layR, R, t0, gain * np.sin(pan * np.pi / 2))


def glide_curve(notes, n, tau=0.06):
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


# ============================================================= instruments

# --- felt piano: stretched inharmonic partials, two detuned strings per
#     note, a soft felt hammer-thunk, warm lowpass. Cached per pitch.
_piano = {}


def piano(midi, dur=3.6):
    key = (midi, round(dur, 2))
    if key in _piano:
        return _piano[key]
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    out = np.zeros(n)
    B = 0.0004
    for k in range(1, 15):
        fk = f * k * np.sqrt(1 + B * k * k)
        if fk > 16000:
            break
        g = 1.0 / k ** 1.3
        dec = 1.0 + 0.42 * k
        out += g * (np.sin(2 * np.pi * fk * 0.9997 * td) +
                    np.sin(2 * np.pi * fk * 1.0003 * td)) * np.exp(-td * dec)
    sos_h = signal.butter(2, 2600, "low", fs=SR, output="sos")
    ham = signal.sosfilt(sos_h, rng.standard_normal(n)) * np.exp(-td * 60)
    out = out / (np.max(np.abs(out)) + 1e-12) + 0.12 * ham
    sos_f = signal.butter(2, 6500, "low", fs=SR, output="sos")
    out = signal.sosfilt(sos_f, out)
    out *= 1 - np.exp(-td / 0.004)
    _piano[key] = out / (np.max(np.abs(out)) + 1e-12)
    return _piano[key]


# --- harp / plucked string: Karplus-Strong, warm pick. Cached per pitch.
_harp = {}


def harp(midi, dur=2.6):
    if midi in _harp:
        return _harp[midi]
    f = midi_to_hz(midi)
    p = max(2, int(round(SR / f)))
    buf = rng.uniform(-1, 1, p)
    buf = np.convolve(buf, np.ones(3) / 3, mode="same")     # warm pick
    n = int(dur * SR)
    out = np.zeros(n)
    damp = 0.9955
    bi = 0
    for i in range(n):
        out[i] = buf[bi]
        nxt = (bi + 1) % p
        buf[bi] = damp * 0.5 * (buf[bi] + buf[nxt])
        bi = nxt
    td = np.arange(n) / SR
    out *= np.exp(-td * 0.6)
    _harp[midi] = out / (np.max(np.abs(out)) + 1e-12)
    return _harp[midi]


# --- bowed cello: detuned additive saw + bow noise, vibrato, slow attack.
_cello = {}


def cello(midi, dur=4.0):
    key = (midi, round(dur, 2))
    if key in _cello:
        return _cello[key]
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    vib = 1.0 + 0.004 * np.sin(2 * np.pi * 5.0 * td) * np.clip(td / 0.6, 0, 1)
    out = np.zeros(n)
    for det in (0.9985, 1.0015):
        ph = 2 * np.pi * f * det * np.cumsum(vib) / SR
        for k in range(1, 13):
            out += np.sin(k * ph) / k
    sos_b = signal.butter(2, [80, 2500], "bandpass", fs=SR, output="sos")
    bow = signal.sosfilt(sos_b, rng.standard_normal(n))
    out = out / (np.max(np.abs(out)) + 1e-12) + 0.08 * bow
    env = np.minimum(np.clip(td / 0.3, 0, 1),
                     np.clip((dur - td) / 0.5, 0, 1))
    sos_w = signal.butter(2, 2200, "low", fs=SR, output="sos")
    out = signal.sosfilt(sos_w, out * env)
    _cello[key] = out / (np.max(np.abs(out)) + 1e-12)
    return _cello[key]


def cello_line(notes, lowpass=2000):
    total = sum(d for _, d in notes)
    n = int((total + 0.6) * SR)
    td = np.arange(n) / SR
    f = glide_curve(notes, n, tau=0.05)
    vib = 1.0 + 0.005 * np.sin(2 * np.pi * 5.0 * td) * np.clip(td / 0.7, 0, 1)
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    out = np.zeros(n)
    for k in range(1, 13):
        out += np.sin(k * ph) / k
    sos_b = signal.butter(2, [80, 2400], "bandpass", fs=SR, output="sos")
    out = out / (np.max(np.abs(out)) + 1e-12) + 0.07 * signal.sosfilt(
        sos_b, rng.standard_normal(n))
    env = np.minimum(np.clip(td / 0.3, 0, 1), np.clip((total + 0.1 - td) / 0.5, 0, 1))
    sos_w = signal.butter(2, lowpass, "low", fs=SR, output="sos")
    out = signal.sosfilt(sos_w, out * env)
    return out / (np.max(np.abs(out)) + 1e-12)


# --- flute / ney: nearly pure, breath, blooming vibrato.
def flute(notes, lowpass=2800, vib_depth=0.004, breath=0.08):
    total = sum(d for _, d in notes)
    n = int((total + 1.0) * SR)
    td = np.arange(n) / SR
    f = glide_curve(notes, n, tau=0.05)
    vib = 1.0 + vib_depth * np.sin(2 * np.pi * 5.4 * td) * np.clip(td / 1.0, 0, 1)
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    out = np.sin(ph) + 0.18 * np.sin(2 * ph) + 0.05 * np.sin(3 * ph)
    if breath:
        sos_b = signal.butter(2, [1500, 5000], "bandpass", fs=SR, output="sos")
        out += breath * signal.sosfilt(sos_b, rng.standard_normal(n))
    env = np.minimum(np.clip(td / 0.12, 0, 1), np.clip((total + 0.05 - td) / 0.9, 0, 1))
    sos_w = signal.butter(2, lowpass, "low", fs=SR, output="sos")
    out = signal.sosfilt(sos_w, out * env)
    return out / (np.max(np.abs(out)) + 1e-12)


# --- choir "ooh/ah": glottal source through vowel formants, multiple notes.
def choir(chord, dur, vowel="oo", detune=0.004):
    formants = {"oo": [(320, 0.9), (800, 0.5), (2700, 0.12)],
                "ah": [(700, 1.0), (1150, 0.6), (2600, 0.25)]}[vowel]
    n = int(dur * SR)
    td = np.arange(n) / SR
    out = np.zeros(n)
    for m in chord:
        f = midi_to_hz(m)
        vib = 1.0 + 0.005 * np.sin(2 * np.pi * rng.uniform(4.5, 5.5) * td +
                                   rng.uniform(0, 6))
        for d in (1 - detune, 1 + detune):
            ph = 2 * np.pi * f * d * np.cumsum(vib) / SR
            src = np.zeros(n)
            for k in range(1, 13):
                src += np.sin(k * ph) / k ** 0.9
            voice = np.zeros(n)
            for fc, g in formants:
                sos = signal.butter(2, [max(60, fc * 0.8), fc * 1.25],
                                    "bandpass", fs=SR, output="sos")
                voice += g * signal.sosfilt(sos, src)
            out += voice
    env = np.minimum(np.clip(td / 1.5, 0, 1), np.clip((dur - td) / 2.0, 0, 1))
    out *= env
    return out / (np.max(np.abs(out)) + 1e-12)


# --- bells / glockenspiel / tolling bell: inharmonic damped sines.
def bell(midi, dur=4.0, ratios=((1, 1, 1.4), (2, 0.5, 1.9), (2.76, 0.3, 2.4),
                                (5.4, 0.15, 3.4)), bright=True):
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    out = np.zeros(n)
    for ratio, g, dec in ratios:
        out += g * np.sin(2 * np.pi * f * ratio * td) * np.exp(-td * dec)
    out *= 1 - np.exp(-td / (0.0015 if bright else 0.004))
    return out / (np.max(np.abs(out)) + 1e-12)


# ============================================================= harmony

# chord = (arp_notes_tuple, bass_midi)
Dmaj9 = ((57, 62, 66, 69, 73), 38)
Bm7 = ((54, 59, 62, 66, 69), 35)
Gmaj69 = ((55, 59, 62, 64, 67), 43)
A7sus = ((57, 62, 64, 67, 69), 45)

Dmaj7c = ((62, 66, 69, 73), 38)
Fmaj7 = ((60, 64, 65, 69), 41)
Bbmaj7 = ((58, 62, 65, 69), 34)
Ebmaj7 = ((63, 67, 70, 74), 39)
A7b9 = ((61, 64, 67, 70), 45)

Dm9 = ((62, 65, 69, 72), 38)
Gm7 = ((55, 58, 62, 65), 43)
A7 = ((57, 61, 64, 67), 45)

Dsad = ((62, 65, 69), 38)
Bbsad = ((58, 62, 65), 34)

G69 = ((55, 59, 62, 64), 43)
Amaj = ((57, 61, 64, 69), 45)
Em7 = ((52, 55, 59, 62), 40)
Dmaj9_hi = ((62, 66, 69, 73, 76), 38)

LOVE_SEQ = [(Dmaj9, 11), (Bm7, 10), (Gmaj69, 10), (A7sus, 9)]
CONF_SEQ = [(Dmaj7c, 10), (Fmaj7, 9), (Bbmaj7, 9), (Ebmaj7, 9), (A7b9, 8)]
LOSS_SEQ = [(Dm9, 14), (Bbmaj7, 12), (Gm7, 12), (A7, 11)]
SAD_SEQ = [(Dsad, 16), (Bbsad, 14)]
HOPE_SEQ = [(G69, 11), (Dmaj9, 11), (Amaj, 10), (Bm7, 10),
            (Em7, 10), (A7sus, 9), (Dmaj9_hi, 14)]


def lay_chords(start, end, seq, tag):
    events = []
    tm, i = start, 0
    while tm < end - 0.5:
        ch, d = seq[i % len(seq)]
        d = min(d, end - tm)
        events.append((tm, d, ch[0], ch[1], tag))
        tm += d
        i += 1
    return events


TIMELINE = (lay_chords(2, 88, LOVE_SEQ, "love") +
            lay_chords(90, 163, CONF_SEQ, "conf") +
            lay_chords(165, 238, LOSS_SEQ, "loss") +
            lay_chords(240, 328, [(Dm9, 16)], "dread") +
            lay_chords(330, 378, SAD_SEQ, "sad") +
            lay_chords(380, 468, HOPE_SEQ, "hope"))


def events_of(tag):
    return [e for e in TIMELINE if e[4] == tag]


# ============================================================= layers

# --- pads: warm bed following the harmony ---------------------------------
def pad_chord(chord, dur, attack, release, lowpass, detune=0.001):
    n = int(dur * SR)
    td = np.arange(n) / SR
    L = np.zeros(n)
    R = np.zeros(n)
    for m in chord:
        f = midi_to_hz(m)
        amp = 0.78 + 0.22 * np.sin(2 * np.pi * rng.uniform(0.02, 0.06) * td +
                                   rng.uniform(0, 6))
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


PAD_PARAMS = {"love": (1100, 0.001, 3.0), "conf": (900, 0.0045, 2.0),
              "loss": (760, 0.001, 3.0), "dread": (560, 0.007, 5.0),
              "sad": (720, 0.001, 5.0), "hope": (1400, 0.001, 3.0)}
clear()
for t0, dur, arp, bass, tag in TIMELINE:
    lp, det, atk = PAD_PARAMS[tag]
    voicing = (bass, bass + 12) + tuple(arp[:3])
    pL, pR = pad_chord(voicing, dur + atk + 2.0, attack=atk, release=atk + 1.0,
                       lowpass=lp, detune=det)
    add_at(lay_L, pL, t0, 0.9)
    add_at(lay_R, pR, t0, 0.9)
lay_L, lay_R = reverb_layer(lay_L, lay_R, 0.4)
commit(lay_L, lay_R, 0.24)
print("pads committed")


# --- piano arpeggios ------------------------------------------------------
def arpeggiate(layL, layR, events, render_fn, step, pattern, gain,
               oct=0, vel=(1.0,), skip=0.0, jitter=0.0, swing=0.0,
               pan_spread=0.5, dur=None):
    for t0, edur, arp, bass, tag in events:
        notes = [m + 12 * oct for m in arp]
        tm, k = t0, 0
        while tm < t0 + edur - step * 0.4:
            idx = pattern[k % len(pattern)] % len(notes)
            if rng.random() >= skip:
                m = notes[idx]
                clip = render_fn(m) if dur is None else render_fn(m, dur)
                g = gain * vel[k % len(vel)]
                pan = 0.5 + pan_spread * (idx / max(1, len(notes) - 1) - 0.5)
                place_pan(layL, layR, clip, tm, g, pan)
            sw = swing * step if k % 2 == 1 else 0.0
            tm += step + sw + rng.uniform(-jitter, jitter)
            k += 1


STEP = 60.0 / 70 / 2          # eighth note at 70 BPM
clear()
# love: flowing up-down arpeggio
arpeggiate(lay_L, lay_R, events_of("love"), piano, STEP,
           [0, 1, 2, 3, 4, 3, 2, 1], gain=0.7, vel=(1.0, 0.7, 0.85, 0.7),
           jitter=0.006, swing=0.06)
# confusion: jumpy, regrouping pattern, faster, more jitter (out of phase)
arpeggiate(lay_L, lay_R, events_of("conf"), piano, STEP * 0.85,
           [0, 2, 3, 1, 2, 0, 3, 1, 2], gain=0.62, vel=(1.0, 0.65, 0.8),
           jitter=0.018, swing=0.0)
# loss: sparse descending quarter-ish notes
arpeggiate(lay_L, lay_R, events_of("loss"), piano, STEP * 2,
           [3, 2, 1, 0, 1, 0], gain=0.6, vel=(1.0, 0.7), skip=0.25, jitter=0.01)
# sad: very sparse single tones
arpeggiate(lay_L, lay_R, events_of("sad"), piano, STEP * 3,
           [0, 2, 1], gain=0.55, skip=0.45, jitter=0.02)
# hope: ascending, building to sixteenths in the final chord
hope_ev = events_of("hope")
arpeggiate(lay_L, lay_R, hope_ev[:-1], piano, STEP,
           [0, 1, 2, 3, 4, 2], gain=0.7, vel=(1.0, 0.7, 0.85, 0.7),
           jitter=0.006, swing=0.05)
arpeggiate(lay_L, lay_R, hope_ev[-1:], piano, STEP * 0.5,
           [0, 1, 2, 3, 4, 3], gain=0.62, vel=(1.0, 0.6, 0.8, 0.6),
           jitter=0.004)
lay_L, lay_R = reverb_layer(lay_L, lay_R, 0.32)
commit(lay_L, lay_R, 0.26)
print("piano arpeggios committed")


# --- harp: interlocking counterpoint, an eighth behind the piano ----------
clear()
def harp_offset(events, step, pattern, gain, oct, skip=0.0):
    for t0, edur, arp, bass, tag in events:
        notes = [m + 12 * oct for m in arp]
        tm, k = t0 + step * 0.5, 0                          # offset behind piano
        while tm < t0 + edur - step * 0.4:
            idx = pattern[k % len(pattern)] % len(notes)
            if rng.random() >= skip:
                m = notes[idx]
                pan = 0.5 + 0.45 * (idx / max(1, len(notes) - 1) - 0.5)
                pan = 1.0 - pan                              # mirror the piano
                place_pan(lay_L, lay_R, harp(m), tm, gain, pan)
            tm += step
            k += 1

harp_offset(events_of("love"), STEP, [4, 3, 2, 1, 0, 1], 0.5, oct=1, skip=0.15)
harp_offset(events_of("conf"), STEP * 0.85, [4, 2, 3, 0], 0.42, oct=1, skip=0.35)
harp_offset(events_of("hope")[:-1], STEP, [4, 3, 2, 1, 0], 0.55, oct=1, skip=0.1)
harp_offset(events_of("hope")[-1:], STEP * 0.5, [4, 3, 2, 1, 0, 1], 0.5, oct=1)
lay_L, lay_R = reverb_layer(lay_L, lay_R, 0.4)
commit(lay_L, lay_R, 0.15)
print("harp committed")


# --- cello: bowed bass pedal under love/conf/hope, laments in loss/sad -----
clear()
for t0, dur, arp, bass, tag in TIMELINE:
    if tag in ("love", "conf", "hope"):
        c = cello(bass, min(dur + 0.8, 6.0))
        place_pan(lay_L, lay_R, c, t0, 0.7, 0.5)
        if tag == "hope":                                   # add the fifth, warmer
            c2 = cello(bass + 7, min(dur + 0.8, 6.0))
            place_pan(lay_L, lay_R, c2, t0 + 0.4, 0.35, 0.5)
# loss lament — a falling cello melody over the section
LAMENT = [(57, 2.4), (55, 2.0), (53, 3.0), (50, 2.2), (53, 2.0), (50, 2.6),
          (48, 3.4), (45, 4.0)]
add_at(lay_L, cello_line(LAMENT), 172.0, 0.85)
add_at(lay_R, cello_line(LAMENT), 172.0, 0.85)
LAMENT2 = [(53, 2.6), (50, 2.2), (48, 3.2), (50, 2.0), (45, 4.4)]
add_at(lay_L, cello_line(LAMENT2), 210.0, 0.8)
add_at(lay_R, cello_line(LAMENT2), 210.0, 0.8)
# sad — a lone, slow cello sigh
SIGH = [(53, 3.0), (50, 4.0), (48, 5.0)]
add_at(lay_L, cello_line(SIGH), 338.0, 0.8)
add_at(lay_R, cello_line(SIGH), 338.0, 0.8)
lay_L, lay_R = reverb_layer(lay_L, lay_R, 0.45)
commit(lay_L, lay_R, 0.20)
print("cello committed")


# --- flute: one voice among many — themes in love and hope, a sigh in sad -
clear()
LOVE_THEME = [(74, 1.6), (76, 1.2), (78, 2.2), (76, 1.2), (73, 1.8),
              (71, 1.4), (69, 2.8)]
HOPE_THEME = [(74, 1.5), (78, 1.2), (81, 1.8), (83, 1.4), (85, 2.4),
              (81, 1.4), (78, 1.6), (74, 3.0)]
SAD_FLUTE = [(69, 3.0), (65, 4.5)]
place_stereo(lay_L, lay_R, flute(LOVE_THEME), 18.0, 0.85, wet=0.5, pan=0.45)
place_stereo(lay_L, lay_R, flute(LOVE_THEME), 58.0, 0.8, wet=0.55, pan=0.55)
place_stereo(lay_L, lay_R, flute(SAD_FLUTE, vib_depth=0.006), 356.0, 0.7,
             wet=0.75, pan=0.5)
place_stereo(lay_L, lay_R, flute(HOPE_THEME), 398.0, 0.9, wet=0.5, pan=0.5)
place_stereo(lay_L, lay_R, flute(HOPE_THEME), 438.0, 0.85, wet=0.55, pan=0.55)
commit(lay_L, lay_R, 0.17)
print("flute committed")


# --- choir pad: warm "oo" in love/hope, dissonant "ah" cluster in dread ----
clear()
place_stereo(lay_L, lay_R, choir((57, 62, 66), 14, "oo"), 24.0, 0.5, wet=0.5)
place_stereo(lay_L, lay_R, choir((55, 59, 62), 12, "oo"), 64.0, 0.45, wet=0.5)
# hope: a rising warm choir behind the rebirth
place_stereo(lay_L, lay_R, choir((57, 62, 66), 18, "oo"), 392.0, 0.55, wet=0.5)
place_stereo(lay_L, lay_R, choir((62, 66, 69), 18, "oo"), 430.0, 0.55, wet=0.5)
commit(lay_L, lay_R, 0.13)
print("choir committed")


# ====================================================== DREAD / ANGST block
# Existential dread (Munch): a tolling bell, swirling dissonant string
# clusters, a relentless dark piano ostinato, a polytonal "ah" choir, and a
# sub rumble that swells and recedes. Density builds, then dissolves.

# 1) tolling low bell, slowly closing in
clear()
toll_t = T_DREAD + 4
i = 0
while toll_t < T_SAD - 6:
    g = 0.5 + 0.5 * min(1.0, (toll_t - T_DREAD) / (T_SAD - T_DREAD))
    place_stereo(lay_L, lay_R, bell(38, dur=6.0, ratios=(
        (1, 1, 0.7), (2.0, 0.6, 1.0), (2.76, 0.4, 1.4), (4.2, 0.2, 2.0),
        (5.4, 0.12, 2.6)), bright=False), toll_t, gain=g, wet=0.6, pan=0.5)
    toll_t += 5.0 - 1.2 * min(1.0, (toll_t - T_DREAD) / 70)   # speeds up slightly
    i += 1
commit(lay_L, lay_R, 0.16)
print(f"tolling bell committed ({i} tolls)")

# 2) swirling dissonant string clusters — slow swells, undulating, panned
clear()
def swell(cluster, dur, trem=0.4):
    n = int(dur * SR)
    td = np.arange(n) / SR
    L = np.zeros(n)
    R = np.zeros(n)
    undu = 1.0 + 0.006 * np.sin(2 * np.pi * 0.13 * td)       # the swirling sky
    for m in cluster:
        f = midi_to_hz(m)
        for d, gL, gR in [(0.994, 1.0, 0.5), (1.006, 0.5, 1.0)]:
            ph = 2 * np.pi * f * d * np.cumsum(undu) / SR
            v = np.zeros(n)
            for k in range(1, 7):
                v += np.sin(k * ph) / k
            L += gL * v
            R += gR * v
    sos = signal.butter(2, [140, 2200], "bandpass", fs=SR, output="sos")
    L = signal.sosfilt(sos, L)
    R = signal.sosfilt(sos, R)
    am = 0.6 + 0.4 * np.sin(2 * np.pi * trem * td)
    env = np.sin(np.pi * np.clip(td / dur, 0, 1)) * am       # swell up and down
    peak = max(np.max(np.abs(L * env)), np.max(np.abs(R * env)), 1e-12)
    return L * env / peak, R * env / peak

clusters = [(50, 51, 56), (49, 50, 56), (51, 52, 57), (50, 51, 54, 56)]
swt = T_DREAD + 2
i = 0
while swt < T_SAD:
    cl = clusters[i % len(clusters)]
    dur = rng.uniform(12, 18)
    sL, sR = swell(cl, dur, trem=rng.uniform(0.25, 0.55))
    g = 0.55 + 0.45 * min(1.0, (swt - T_DREAD) / 70)
    sL = reverb_mono(sL, IR_L, 0.5)
    sR = reverb_mono(sR, IR_R, 0.5)
    add_at(lay_L, sL, swt, g)
    add_at(lay_R, sR, swt, g)
    swt += rng.uniform(7, 11)
    i += 1
commit(lay_L, lay_R, 0.17)
print(f"swirling clusters committed ({i})")

# 3) relentless dark piano ostinato that will not resolve (D-Eb-D-Ab)
clear()
OST = [38, 39, 38, 32]            # D2 Eb2 D2 Ab1 — semitone & tritone, no home
ost_t = T_DREAD + 8
k = 0
ost_gain = 0.0
while ost_t < T_SAD - 4:
    ost_gain = 0.4 + 0.55 * min(1.0, (ost_t - T_DREAD) / 75)
    m = OST[k % len(OST)]
    place_pan(lay_L, lay_R, piano(m, 2.2), ost_t, ost_gain * (1.0 if k % 4 == 0 else 0.7), 0.5)
    ost_t += STEP * 1.2
    k += 1
lay_L, lay_R = reverb_layer(lay_L, lay_R, 0.3)
commit(lay_L, lay_R, 0.18)
print(f"dark ostinato committed ({k} notes)")

# 4) polytonal "ah" choir (Dm against Eb), swelling
clear()
place_stereo(lay_L, lay_R, choir((50, 53, 57), 22, "ah"), T_DREAD + 10, 0.5, wet=0.55)
place_stereo(lay_L, lay_R, choir((51, 55, 58), 24, "ah", detune=0.008),
             T_DREAD + 34, 0.55, wet=0.6)
place_stereo(lay_L, lay_R, choir((50, 51, 56, 57), 26, "ah", detune=0.009),
             T_DREAD + 58, 0.6, wet=0.65)
commit(lay_L, lay_R, 0.12)
print("polytonal choir committed")

# 5) sub rumble swelling and receding
clear()
sub = np.cumsum(rng.standard_normal(N))
sub -= np.linspace(sub[0], sub[-1], N)
sos_sub = signal.butter(2, 90, "low", fs=SR, output="sos")
sub = signal.sosfilt(sos_sub, sub)
sub /= np.max(np.abs(sub)) + 1e-12
sub_env = ramp([(0, 0), (T_DREAD, 0), (T_DREAD + 50, 1.0), (T_SAD - 6, 0.7),
                (T_SAD + 6, 0.0), (T_END, 0)])
sub_env *= 0.6 + 0.4 * slow_noise(0.08)
lay_L[:] = sub * sub_env
lay_R[:] = sub * sub_env
commit(lay_L, lay_R, 0.14)
print("sub rumble committed")


# --- glockenspiel + bells: sparkle through the hope section ----------------
clear()
GLOCK = [86, 90, 93, 81, 78]      # high D F# A glints
gt = T_HOPE + 8
i = 0
while gt < T_END - 5:
    m = GLOCK[i % len(GLOCK)]
    place_stereo(lay_L, lay_R, bell(m, dur=2.2), gt, gain=rng.uniform(0.4, 0.7),
                 wet=0.6, pan=rng.uniform(0.3, 0.7))
    gt += rng.uniform(1.6, 3.2)
    i += 1
# a couple of warm low bells marking the new beginning
for tb, mb in [(T_HOPE + 2, 62), (T_HOPE + 30, 66), (T_HOPE + 60, 69)]:
    place_stereo(lay_L, lay_R, bell(mb, dur=5.0), tb, 0.6, wet=0.6, pan=0.5)
commit(lay_L, lay_R, 0.10)
print(f"glockenspiel + bells committed ({i} glints)")


# --- heartbeat: the through-line, now full and audible ---------------------
clear()
def heart():
    n = int(0.26 * SR)
    td = np.arange(n) / SR
    f = 32 + 36 * np.exp(-td * 20)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-td * 13)
    body += 0.5 * np.sin(2 * np.pi * 70 * td) * np.exp(-td * 18)   # midrange punch
    sos = signal.butter(2, 220, "low", fs=SR, output="sos")
    thud = signal.sosfilt(sos, rng.standard_normal(n)) * np.exp(-td * 28)
    thud /= np.max(np.abs(thud)) + 1e-12
    x = body / (np.max(np.abs(body)) + 1e-12) + 0.3 * thud
    x *= 1 - np.exp(-td / 0.004)
    return x / (np.max(np.abs(x)) + 1e-12)

THUMP = heart()

def interval(tm):
    if tm < T_CONF:
        return 1.0
    if tm < T_LOSS:
        return 0.98
    if tm < T_DREAD:
        return 1.18
    if tm < T_SAD - 8:
        u = (tm - T_DREAD) / (T_SAD - 8 - T_DREAD)
        return 1.05 - 0.5 * u
    if tm < T_SAD:
        return None
    if tm < T_HOPE:
        return 1.6
    return 1.0

heart_gain = ramp([(0, 0.7), (T_CONF, 0.6), (T_LOSS, 0.55), (T_DREAD, 0.7),
                   (T_SAD - 10, 1.0), (T_SAD - 2, 0.55), (T_SAD, 0.0),
                   (T_SAD + 6, 0.4), (T_HOPE, 0.0), (T_HOPE + 8, 0.6),
                   (T_END, 0.5)])
tm = 0.6
while tm < T_END - 1:
    iv = interval(tm)
    if iv is None:
        tm = T_SAD + 1.0
        continue
    g = heart_gain[min(N - 1, int(tm * SR))]
    jit = rng.uniform(-0.01, 0.01)
    if T_CONF <= tm < T_LOSS:
        jit += rng.uniform(-0.05, 0.05)
    add_at(lay_L, THUMP, tm + jit, g)
    add_at(lay_R, THUMP, tm + jit, g)
    add_at(lay_L, THUMP, tm + jit + 0.22, g * 0.62)
    add_at(lay_R, THUMP, tm + jit + 0.22, g * 0.62)
    tm += iv
commit(lay_L, lay_R, 0.26)
print("heartbeat committed")


# --- nature: wind throughout, rain in loss/dread, stream + birds in hope ---
clear()
sos_low = signal.butter(2, [120, 900], "bandpass", fs=SR, output="sos")
sos_hiss = signal.butter(2, [2000, 7000], "bandpass", fs=SR, output="sos")
whoosh = signal.sosfilt(sos_low, rng.standard_normal(N))
hiss = signal.sosfilt(sos_hiss, rng.standard_normal(N))
gust = slow_noise(0.18) ** 2.0
wind = whoosh * (0.5 + 0.5 * gust) + hiss * 0.12 * (0.4 + 0.6 * slow_noise(0.06))
wind /= np.max(np.abs(wind)) + 1e-12
wind_gain = ramp([(0, 0.4), (T_LOSS, 0.45), (T_DREAD, 0.6), (T_SAD - 10, 0.7),
                  (T_SAD, 0.35), (T_HOPE, 0.4), (T_END, 0.35)])
wp = slow_noise(0.05)
lay_L[:] = wind * wind_gain * np.cos(wp * np.pi / 2)
lay_R[:] = wind * wind_gain * np.sin(wp * np.pi / 2)
commit(lay_L, lay_R, 0.07)

clear()
sos_rain = signal.butter(2, [1500, 8000], "bandpass", fs=SR, output="sos")
rain = signal.sosfilt(sos_rain, rng.standard_normal(N))
rain *= 0.6 + 0.4 * slow_noise(2.5)
rain /= np.max(np.abs(rain)) + 1e-12
rain_gain = ramp([(0, 0), (T_LOSS - 4, 0), (T_LOSS + 8, 0.8), (T_DREAD, 0.7),
                  (T_DREAD + 40, 0.4), (T_SAD - 4, 0.2), (T_SAD + 6, 0), (T_END, 0)])
rp = slow_noise(0.07)
lay_L[:] = rain * rain_gain * np.cos(rp * np.pi / 2)
lay_R[:] = rain * rain_gain * np.sin(rp * np.pi / 2)
commit(lay_L, lay_R, 0.05)

clear()
sos_st = signal.butter(2, [400, 2400], "bandpass", fs=SR, output="sos")
stream = signal.sosfilt(sos_st, rng.standard_normal(N))
stream *= 0.5 + 0.5 * slow_noise(3.0)
stream /= np.max(np.abs(stream)) + 1e-12
stream_gain = ramp([(0, 0), (T_HOPE - 2, 0), (T_HOPE + 12, 0.7), (T_END - 8, 0.7),
                    (T_END, 0.3)])
sp = slow_noise(0.06)
lay_L[:] = stream * stream_gain * np.cos(sp * np.pi / 2)
lay_R[:] = stream * stream_gain * np.sin(sp * np.pi / 2)

def chirp():
    dur = rng.uniform(0.18, 0.4)
    n = int(dur * SR)
    td = np.arange(n) / SR
    f0 = rng.uniform(2400, 3600)
    f = f0 * (1 + 0.18 * np.sin(2 * np.pi * rng.uniform(14, 22) * td)) * \
        (1 + 0.4 * np.clip(td / dur, 0, 1))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * td / dur) ** 2
    return x / (np.max(np.abs(x)) + 1e-12)

bt = T_HOPE + 6
while bt < T_END - 6:
    pan = rng.uniform(0.2, 0.8)
    g = rng.uniform(0.25, 0.5)
    for j in range(int(rng.integers(1, 4))):
        place_stereo(lay_L, lay_R, chirp(), bt + j * rng.uniform(0.18, 0.35),
                     gain=g, wet=0.5, pan=pan)
    bt += rng.uniform(3.0, 7.0)
commit(lay_L, lay_R, 0.07)
print("nature committed")


# ---------------------------------------------------------------- master

fade(mix_L, fade_in=3.0, fade_out=8.0)
fade(mix_R, fade_in=3.0, fade_out=8.0)

peak = max(np.max(np.abs(mix_L)), np.max(np.abs(mix_R)))
mix_L = mix_L / peak * 0.88
mix_R = mix_R / peak * 0.88

stereo = np.empty((N, 2))
stereo[:, 0] = mix_L
stereo[:, 1] = mix_R
pcm = (stereo * 32767.0).astype(np.int16)

OUT_DIR = "/workspace/music"
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, "lost_v2.wav")
with wave.open(OUT, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())

print(f"\nCreated: {os.path.abspath(OUT)}")
print(f"Duration: {N / SR:.1f} s  |  {SR} Hz stereo, 16-bit PCM")

MP3 = os.path.join(OUT_DIR, "lost_v2.mp3")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", OUT,
                "-vn", "-ar", "44100", "-ac", "2", "-b:a", "192k", MP3],
               check=True)
print(f"Created: {os.path.abspath(MP3)}  (192k mp3)")

print("\nSection map:")
for name, tm in [("LOVE", T_LOVE), ("CONFUSION", T_CONF), ("LOSS", T_LOSS),
                 ("DREAD / ANGST", T_DREAD), ("SADNESS", T_SAD), ("HOPE", T_HOPE)]:
    print(f"  {tm:6.1f} s  {name}")
print(f"  {DURATION:6.1f} s  end")

print("\nPer-section RMS:")
bounds = [T_LOVE, T_CONF, T_LOSS, T_DREAD, T_SAD, T_HOPE, T_END]
names = ["love", "confusion", "loss", "dread/angst", "sadness", "hope"]
for nm, a, b in zip(names, bounds[:-1], bounds[1:]):
    i0, i1 = int(a * SR), int(b * SR)
    r = np.sqrt(np.mean(mix_L[i0:i1] ** 2 + mix_R[i0:i1] ** 2) / 2)
    print(f"  {nm:14s} {r:.3f}")
