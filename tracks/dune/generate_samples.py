#!/usr/bin/env python3
"""
generate_samples.py — a listening glossary for the Dune music generators.

Produces short (~5 s) isolated samples of every instrument, tone, effect and
musical concept used in generate_ambient.py / generate_arrakis.py /
generate_base_attack.py, so the building blocks can be heard one at a time
and compared. Each recipe is copied verbatim from the track generators
(scripts here are standalone by convention — they execute on import, so
sharing code means copying it).

File naming: <category>_<nn>_<descriptive_name>.wav
  tone_       raw synthesis building blocks
  noise_      unshaped noise colors
  filter_     the same noise through different filters
  wind_       the assembled wind from the Dune tracks
  effect_     reverb, explosions, rumbles, drones
  instrument_ darbuka, oud, duduk-voice, klaxon, pads
  scale_      hear the difference between the two scales used
  rhythm_     the maqsum darbuka pattern

Output: /workspace/music/samples/*.wav + README.txt describing each file.
"""

import os
import wave
import numpy as np
from scipy import signal

SR = 44100
OUT_DIR = "/workspace/music/samples"
os.makedirs(OUT_DIR, exist_ok=True)

rng = np.random.default_rng(10191)

manifest = []   # (filename, description) for README.txt


# ---------------------------------------------------------------- plumbing

def midi_to_hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def save(name, desc, L, R=None):
    """Peak-normalize, de-click edges, write 16-bit stereo WAV."""
    if R is None:
        R = L
    L, R = np.asarray(L, float).copy(), np.asarray(R, float).copy()
    ne = int(0.03 * SR)                       # 30 ms edge fades, no clicks
    for x in (L, R):
        x[:ne] *= np.linspace(0, 1, ne)
        x[-ne:] *= np.linspace(1, 0, ne)
    peak = max(np.max(np.abs(L)), np.max(np.abs(R)), 1e-12)
    L, R = L / peak * 0.85, R / peak * 0.85
    pcm = np.empty((len(L), 2))
    pcm[:, 0], pcm[:, 1] = L, R
    pcm = (pcm * 32767.0).astype(np.int16)
    path = os.path.join(OUT_DIR, name)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    manifest.append((name, desc))
    print(f"  {name}")


def tsec(dur):
    return np.arange(int(dur * SR)) / SR


def place(buf, x, at_s, gain=1.0):
    i0 = int(at_s * SR)
    end = min(len(buf), i0 + len(x))
    buf[i0:end] += x[: end - i0] * gain


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


IR = make_reverb_ir(4.0, 1.6, 7)


def karplus_strong(freq, dur, damp=0.992):
    n = int(dur * SR)
    period = max(2, int(SR / freq))
    buf = rng.uniform(-1, 1, period)
    buf = np.convolve(buf, np.ones(3) / 3, mode="same")
    out = np.empty(n)
    prev = buf.copy()
    i = 0
    while i < n:
        m = min(period, n - i)
        out[i:i + m] = prev[:m]
        prev = damp * 0.5 * (prev + np.roll(prev, 1))
        i += m
    return out


def oud_pluck(midi, dur=1.2):
    f = midi_to_hz(midi)
    p = karplus_strong(f, dur) + 0.6 * karplus_strong(f * 1.004, dur)
    return p / (np.max(np.abs(p)) + 1e-12)


print("Generating samples...")

# ================================================================ TONES

# 1. pure sine — the atom of all our synthesis
tt = tsec(5.0)
f = midi_to_hz(62)                                       # D4
save("tone_01_sine_pure.wav",
     "A pure sine wave on D4 (293.7 Hz). One single frequency, nothing else "
     "— the simplest possible sound, and the atom every other sample here "
     "is built from.",
     np.sin(2 * np.pi * f * tt))

# 2. harmonics stacked -> brassy/sawtooth (the rejected 'trombone' tone)
sawish = sum(np.sin(2 * np.pi * f * k * tt) / k for k in range(1, 9))
save("tone_02_harmonics_brassy_saw.wav",
     "The same D4 with 8 harmonics stacked (each k-th harmonic at 1/k "
     "volume) — a sawtooth-like, brassy buzz. THIS is the 'trombone' tone "
     "that was cut from Base Under Attack v1.",
     sawish)

# 3. detuning -> beating
beat = np.sin(2 * np.pi * f * tt) + np.sin(2 * np.pi * (f + 1.0) * tt)
save("tone_03_detune_beating.wav",
     "Two sines 1 Hz apart. They drift in and out of phase, making the "
     "volume pulse once per second: 'beating'. Slowed way down, this is "
     "what makes the drones feel alive.",
     beat)

# 4. pitch glide (the cumsum trick)
tt4 = tsec(5.0)
f_curve = 440.0 * (110.0 / 440.0) ** (tt4 / 5.0)         # 440 -> 110 Hz
glide = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
save("tone_04_pitch_glide_down.wav",
     "A sine sliding smoothly from 440 Hz down to 110 Hz. Pitch glides like "
     "this (sped up and deepened) are the core of the kick drums, worm "
     "rumbles and explosion cores.",
     glide)

# ================================================================ NOISE

white = rng.standard_normal(int(5.0 * SR))
save("noise_01_white.wav",
     "White noise: every frequency at equal energy. Harsh hiss on its own — "
     "but it is the raw material for wind, sand, drum slaps and reverb.",
     white)

brown = np.cumsum(rng.standard_normal(int(5.0 * SR)))
brown -= np.linspace(brown[0], brown[-1], len(brown))
save("noise_02_brown_rumbly.wav",
     "Brown noise (white noise accumulated step by step): energy piles up "
     "at low frequencies, so it rumbles instead of hissing. The body of "
     "every explosion starts as brown noise.",
     brown)

# ================================================================ FILTERS

sos = signal.butter(4, 500, "low", fs=SR, output="sos")
save("filter_01_lowpass_500hz.wav",
     "The same white noise through a lowpass filter at 500 Hz: everything "
     "above 500 Hz is removed. 'Lowpass = keep the lows.' Distant or huge "
     "things are always lowpassed.",
     signal.sosfilt(sos, white))

sos = signal.butter(4, [120, 900], "bandpass", fs=SR, output="sos")
save("filter_02_bandpass_120_900_whoosh.wav",
     "White noise through a bandpass keeping only 120-900 Hz: the WHOOSH "
     "band. This exact filter makes the body of the desert wind.",
     signal.sosfilt(sos, white))

sos = signal.butter(4, [2000, 7000], "bandpass", fs=SR, output="sos")
save("filter_03_bandpass_2k_7k_hiss.wav",
     "White noise keeping only 2000-7000 Hz: the HISS band — bright and "
     "sandy. This is the 'sand carried on the wind' layer.",
     signal.sosfilt(sos, white))

# ================================================================ WIND

dur = 8.0
n = int(dur * SR)
twind = tsec(dur)
raw = rng.standard_normal(n)
sos_w = signal.butter(4, [120, 900], "bandpass", fs=SR, output="sos")
sos_h = signal.butter(4, [2000, 7000], "bandpass", fs=SR, output="sos")
whoosh = signal.sosfilt(sos_w, raw)
whoosh /= np.max(np.abs(whoosh))
hiss = signal.sosfilt(sos_h, raw)
hiss /= np.max(np.abs(hiss))
# two gust swells in 8 seconds
gust = (0.5 - 0.5 * np.cos(2 * np.pi * twind / 4.0)) ** 2.2
wind = (whoosh + 0.3 * hiss) * (0.15 + 0.85 * gust)
pan_c = 0.5 + 0.3 * np.sin(2 * np.pi * twind / 8.0)
save("wind_01_gusting_desert.wav",
     "Everything assembled: whoosh band + hiss band, volume driven by a "
     "slow 'gust' envelope (note the lulls go almost silent), drifting "
     "between the speakers. This is the Arrakis wind.",
     wind * np.cos(pan_c * np.pi / 2), wind * np.sin(pan_c * np.pi / 2))

# ================================================================ EFFECTS

# reverb demo: identical pluck, dry then wet
demo = np.zeros(int(6.0 * SR))
pl = oud_pluck(62, 1.5)
place(demo, pl, 0.5)
wet_part = np.zeros_like(demo)
place(wet_part, pl, 3.0)
wet_part = reverb(wet_part, IR, wet=0.75)
save("effect_01_reverb_dry_then_wet.wav",
     "The SAME oud pluck twice: first bone-dry (sounds close), then through "
     "75% convolution reverb (sounds far away in a huge space). Reverb = "
     "distance. The arrakis 'distant calls' use exactly this wet setting.",
     demo + wet_part)

# explosion
dur = 6.0
n = int(dur * SR)
tb = tsec(dur)
brown_e = np.cumsum(rng.standard_normal(n))
brown_e -= np.linspace(brown_e[0], brown_e[-1], n)
brown_e /= np.max(np.abs(brown_e)) + 1e-12
env = (1 - np.exp(-tb / 0.08)) * np.exp(-tb / 1.8)
sos_b = signal.butter(4, 150, "low", fs=SR, output="sos")
body = signal.sosfilt(sos_b, brown_e * env)
fsub = 22.0 + 38.0 * np.exp(-tb * 1.6)
core = np.sin(2 * np.pi * np.cumsum(fsub) / SR) * env
save("effect_02_explosion_deep_slow.wav",
     "One explosion: brown noise lowpassed below 150 Hz + a sub-sine "
     "falling 60->22 Hz. The attack takes 80 ms instead of being instant — "
     "that slow swell is why it sounds deep and heavy, not harsh.",
     reverb(body * 0.7 + core * 0.6, IR, wet=0.4))

# worm rumble
dur = 6.0
tb = tsec(dur)
n = len(tb)
f_curve = 27.0 + 28.0 * np.exp(-tb * 2.2)
env = np.exp(-tb * 1.1) * (1 - np.exp(-tb * 30))
thump = env * np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
sos_gr = signal.butter(4, 90, "low", fs=SR, output="sos")
shake = signal.sosfilt(sos_gr, rng.standard_normal(n)) * env * 0.6
save("effect_03_worm_rumble_subsonic.wav",
     "The Shai-Hulud rumble: a sine falling 55->27 Hz plus ground-shake "
     "noise below 90 Hz. Mostly subsonic — on small speakers you barely "
     "hear it; on a subwoofer you FEEL it.",
     thump + shake)

# drone
tt5 = tsec(8.0)
f_D1 = midi_to_hz(26)
drone = (np.sin(2 * np.pi * f_D1 * tt5) +
         0.55 * np.sin(2 * np.pi * f_D1 * 2 * tt5 + 0.4) +
         0.30 * np.sin(2 * np.pi * f_D1 * 3 * tt5) +
         0.30 * np.sin(2 * np.pi * f_D1 * 3.003 * tt5))
save("effect_04_drone_deep_D1.wav",
     "The planetary drone under every Dune track: D1 (36.7 Hz) plus its "
     "2nd and 3rd harmonics — and a second copy of the 3rd harmonic "
     "detuned 0.3%, so the pair beats slowly (hear tone_03).",
     drone)

# ================================================================ INSTRUMENTS

def make_doum():
    n = int(0.30 * SR)
    td = tsec(0.30)
    f_curve = 55.0 + 35.0 * np.exp(-td * 28.0)
    body = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    ring = 0.25 * np.sin(2 * np.pi * 190.0 * td) * np.exp(-td * 35)
    env = np.exp(-td * 14.0) * (1 - np.exp(-td * 600))
    return (body + ring) * env


def make_tek(ghost=False):
    n = int(0.09 * SR)
    td = tsec(0.09)
    sos_h2 = signal.butter(4, [2500, 9000], "bandpass", fs=SR, output="sos")
    slap = signal.sosfilt(sos_h2, rng.standard_normal(n))
    ping = 0.4 * np.sin(2 * np.pi * 640.0 * td)
    env = np.exp(-td * (90.0 if ghost else 55.0))
    x = (slap / (np.max(np.abs(slap)) + 1e-12) + ping) * env
    return x * (0.35 if ghost else 1.0)


DOUM, TEK, KA = make_doum(), make_tek(), make_tek(ghost=True)

buf = np.zeros(int(5.0 * SR))
for k in range(4):
    place(buf, DOUM, 0.5 + k * 1.1)
save("instrument_01_darbuka_doum.wav",
     "DOUM — the deep center-stroke of a darbuka (Middle Eastern goblet "
     "drum): a pitch-drop thump with a short skin 'ring'. The heartbeat of "
     "the maqsum rhythm.",
     buf)

buf = np.zeros(int(5.0 * SR))
for k in range(4):
    place(buf, TEK, 0.5 + k * 1.1)
save("instrument_02_darbuka_tek.wav",
     "TEK — the sharp rim slap of the darbuka: a bright noise crack with a "
     "640 Hz ping. The 'answer' to the doum's 'call'.",
     buf)

buf = np.zeros(int(5.0 * SR))
for k in range(6):
    place(buf, KA, 0.5 + k * 0.7)
save("instrument_03_darbuka_ka_ghost.wav",
     "KA — a quiet, quickly-damped ghost tek played between the main "
     "strokes. Almost inaudible alone, but it gives the rhythm its rolling "
     "drive.",
     buf)

buf = np.zeros(int(5.0 * SR))
nk = int(0.35 * SR)
tk = tsec(0.35)
fk = 36.0 + 60.0 * np.exp(-tk * 16.0)
SUB = np.sin(2 * np.pi * np.cumsum(fk) / SR) * np.exp(-tk * 10) * (1 - np.exp(-tk * 400))
for k in range(4):
    place(buf, SUB, 0.5 + k * 1.1)
save("instrument_04_subkick.wav",
     "Sub-kick: a sine dropping 96->36 Hz with a soft attack — no click at "
     "all. Layered under every doum to add chest-weight the small drum "
     "can't produce.",
     buf)

buf = np.zeros(int(6.0 * SR))
for k, m in enumerate([50, 53, 54, 57]):                 # D3 F3 F#3 A3
    place(buf, oud_pluck(m, 1.4), 0.5 + k * 1.3)
save("instrument_05_oud_plucks.wav",
     "Oud — the Middle Eastern lute, synthesized with Karplus-Strong "
     "(a burst of noise recycled through a delay = a vibrating string). "
     "Each note is two strings slightly detuned, like the oud's real "
     "double courses. Four single notes.",
     buf)

# duduk-like voice: two-note call with portamento + vibrato
dur = 6.0
n = int(dur * SR)
tv = tsec(dur)
f_target = np.full(n, midi_to_hz(69))                    # A4...
f_target[int(2.5 * SR):] = midi_to_hz(62)                # ...sliding to D4
alpha = 1.0 - np.exp(-1.0 / (0.09 * SR))
f_curve = signal.lfilter([alpha], [1.0, -(1.0 - alpha)], f_target,
                         zi=[f_target[0] * (1 - alpha)])[0]
vib = 1.0 + 0.006 * np.sin(2 * np.pi * 5.2 * tv) * np.clip(tv / 1.2, 0, 1)
phase = 2 * np.pi * np.cumsum(f_curve * vib) / SR
env = np.minimum(np.clip(tv / 1.2, 0, 1), np.clip((dur - tv) / 1.5, 0, 1))
voice = env * (np.sin(phase) + 0.40 * np.sin(2 * phase) +
               0.18 * np.sin(3 * phase) + 0.07 * np.sin(4 * phase))
sos_v = signal.butter(2, 2200, "low", fs=SR, output="sos")
voice = signal.sosfilt(sos_v, voice)
save("instrument_06_duduk_voice_call.wav",
     "The 'distant call' voice from Arrakis Winds, up close: a dark reedy "
     "tone (like an Armenian duduk) sliding from A down to D — hear the "
     "smooth slide (portamento) and the slow wobble that blooms after the "
     "start (vibrato). In the track it is drowned in reverb.",
     reverb(voice, IR, wet=0.35))

# klaxon
buf = np.zeros(int(5.0 * SR))
nb = int(0.12 * SR)
tb2 = tsec(0.12)
beep_env = np.minimum(np.clip(tb2 / 0.008, 0, 1), np.clip((0.12 - tb2) / 0.02, 0, 1))
for k in range(6):
    fq = 740.0 if k % 2 == 0 else 988.0
    beep = beep_env * (np.sin(2 * np.pi * fq * tb2) +
                       0.35 * np.sin(2 * np.pi * 2 * fq * tb2))
    place(buf, beep, 0.5 + k * 0.24)
save("instrument_07_klaxon_alarm.wav",
     "The base-attack klaxon: six fast 120 ms beeps alternating between "
     "two tones, almost dry. Fast + dry = urgent alarm; slow + reverbed "
     "(the v1 mistake) = horror movie.",
     reverb(buf, IR, wet=0.25))

# pad chord
tt6 = tsec(8.0)
pad = np.zeros(len(tt6))
padR = np.zeros(len(tt6))
for vi, m in enumerate([50, 57, 60, 64, 69]):            # Dm9
    fq = midi_to_hz(m)
    lfo = 0.65 + 0.35 * np.sin(2 * np.pi * (0.05 + 0.03 * vi) * tt6 + vi)
    det = 1.0 + 0.0007 * (vi - 2)
    pad += lfo * (np.sin(2 * np.pi * fq * det * tt6) +
                  0.5 * np.sin(2 * np.pi * fq * det * 1.002 * tt6))
    padR += lfo * (np.sin(2 * np.pi * fq / det * tt6 + 0.7) +
                   0.5 * np.sin(2 * np.pi * fq / det * 0.998 * tt6))
save("instrument_08_pad_chord_dm9.wav",
     "A synth pad: five detuned sine voices holding one chord (Dm9), each "
     "voice slowly swelling and fading on its own cycle so the texture "
     "never stands still. The whole first ambient track is four of these "
     "crossfaded.",
     pad, padR)

# ================================================================ SCALES

def scale_demo(midis):
    buf = np.zeros(int((len(midis) * 0.6 + 1.5) * SR))
    for k, m in enumerate(midis):
        place(buf, oud_pluck(m, 1.2), 0.4 + k * 0.6)
    return buf

save("scale_01_minor_pentatonic_D.wav",
     "D minor pentatonic, ascending (D F G A C D): five notes, no "
     "half-steps — smooth, safe, calm. The scale of the first ambient "
     "track's plucks.",
     scale_demo([50, 53, 55, 57, 60, 62]))

save("scale_02_phrygian_dominant_D.wav",
     "D Phrygian dominant, ascending (D Eb F# G A Bb C D). Listen to the "
     "second note: only a half-step above the first — that crunch, plus "
     "the wide jump to F#, is the instantly-'desert' sound. The scale of "
     "both Dune tracks.",
     scale_demo([50, 51, 54, 55, 57, 58, 60, 62]))

# ================================================================ RHYTHM

BPM = 128.0
STEP = 60.0 / BPM / 4.0
PATTERN = {0: "D", 2: "T", 6: "T", 8: "D", 12: "T"}
bars = 4
buf = np.zeros(int((bars * 16 * STEP + 1.0) * SR))
bufR = buf.copy()
for bar_i in range(bars):
    for step_i in range(16):
        st = 0.2 + (bar_i * 16 + step_i) * STEP
        s = PATTERN.get(step_i)
        if s == "D":
            place(buf, DOUM, st)
            place(bufR, DOUM, st)
            place(buf, SUB, st, 0.8)
            place(bufR, SUB, st, 0.8)
        elif s == "T":
            p = 0.35 if step_i in (2, 12) else 0.65
            place(buf, TEK, st, np.cos(p * np.pi / 2))
            place(bufR, TEK, st, np.sin(p * np.pi / 2))
        elif step_i % 2 == 1 and rng.random() < 0.3:
            place(buf, KA, st, 0.6)
            place(bufR, KA, st, 0.5)
save("rhythm_01_maqsum_128bpm.wav",
     "Four bars of maqsum at 128 BPM — one of the most common Arabic "
     "rhythms: DOUM tek . tek DOUM . tek . — built only from the three "
     "darbuka strokes (samples 01-03) plus the sub-kick. This is the "
     "groove of Base Under Attack v2.",
     buf, bufR)

# ================================================================ README

lines = ["Dune music — listening glossary",
         "=" * 60,
         "Each file isolates ONE sound or concept from the track",
         "generators in /repos/dune/music. Listen in order within each",
         "category; later samples build on earlier ones.", ""]
for name, desc in manifest:
    lines.append(name)
    lines.append("    " + desc)
    lines.append("")
readme_path = os.path.join(OUT_DIR, "README.txt")
with open(readme_path, "w") as fh:
    fh.write("\n".join(lines))

print(f"\n{len(manifest)} samples + README.txt written to {OUT_DIR}")
