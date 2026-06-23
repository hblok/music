#!/usr/bin/env python3
"""
generate_voice_final.py — full 16-line generation for the 4 chosen voices,
each with the 3 best effects.

Voices:
  au_william_m  en-AU-WilliamMultilingualNeural
  au_natasha_f  en-AU-NatashaNeural
  us_aria_f     en-US-AriaNeural
  us_guy_m      en-US-GuyNeural

Effects:
  _benegesserit  sub-harmonic + chorus shimmer + formant boost
  _bitcrush      sample-rate + bit-depth crush + noise floor
  _ringmod       72 Hz ring modulation, metallic timbre

Output naming: {cat}_{slug}_{voice_tag}_{effect}.wav
Output dir:    /workspace/music/voice/final/
"""

import os
import asyncio
import wave
import tempfile
import subprocess
import numpy as np
from scipy import signal

SR     = 44100
OUT_DIR = "/workspace/music/voice/final"
os.makedirs(OUT_DIR, exist_ok=True)

rng = np.random.default_rng(2342)

LINES = [
    ("alert",  "base_under_attack",    "Our base is under attack!"),
    ("alert",  "enemy_approaching",    "Enemy units approaching!"),
    ("alert",  "harvester_attacked",   "Harvester under attack!"),
    ("alert",  "take_evasive_action",  "Take evasive action!"),
    ("status", "unit_lost",            "Unit lost."),
    ("status", "building_destroyed",   "Building destroyed."),
    ("status", "low_power",            "Low power."),
    ("status", "spice_depleted",       "Spice depleted."),
    ("build",  "construction_complete","Construction complete."),
    ("build",  "place_structure",      "Place your structure."),
    ("build",  "not_enough_credits",   "Not enough credits."),
    ("order",  "yes_sir",              "Yes, sir."),
    ("order",  "moving_out",           "Moving out."),
    ("order",  "orders_received",      "Orders received."),
    ("atmo",   "worm_sign",            "Worm sign. Get off the sand."),
    ("atmo",   "the_spice_must_flow",  "The spice must flow."),
]

VOICES = [
    ("en-AU-WilliamMultilingualNeural", "au_william_m"),
    ("en-AU-NatashaNeural",             "au_natasha_f"),
    ("en-US-AriaNeural",                "us_aria_f"),
    ("en-US-GuyNeural",                 "us_guy_m"),
]

CAT_SETTINGS = {
    "alert":  (-3, 1.25),
    "status": (-2, 1.10),
    "build":  (-2, 1.05),
    "order":  (-2, 1.00),
    "atmo":   (-3, 0.95),
}


# ---------------------------------------------------------------- utils

def load_wav_mono(path):
    with wave.open(path, "rb") as w:
        ch, sw, fr = w.getnchannels(), w.getsampwidth(), w.getframerate()
        raw = w.readframes(w.getnframes())
    dtype = {1: np.int8, 2: np.int16, 4: np.int32}[sw]
    pcm = np.frombuffer(raw, dtype=dtype).astype(np.float32)
    if ch == 2:
        pcm = pcm.reshape(-1, 2).mean(axis=1)
    pcm /= np.iinfo(dtype).max
    if fr != SR:
        pcm = signal.resample(pcm, int(len(pcm) * SR / fr))
    return pcm


def save_stereo(path, L, R=None):
    if R is None:
        R = L
    L, R = L.copy(), R.copy()
    ne = min(int(0.015 * SR), len(L) // 4)
    for x in (L, R):
        x[:ne] *= np.linspace(0, 1, ne)
        x[-ne:] *= np.linspace(1, 0, ne)
    peak = max(np.max(np.abs(L)), np.max(np.abs(R)), 1e-9)
    L = np.clip(L / peak * 0.88, -1, 1)
    R = np.clip(R / peak * 0.88, -1, 1)
    pcm = np.empty((len(L), 2))
    pcm[:, 0], pcm[:, 1] = L, R
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((pcm * 32767).astype(np.int16).tobytes())


def ola_stretch(x, factor, win=1024, hop=256):
    hop_out = max(1, int(hop * factor))
    n_out   = max(1, int(len(x) * factor))
    out  = np.zeros(n_out + win)
    norm = np.zeros(n_out + win)
    w    = np.hanning(win)
    pi = po = 0
    while pi + win <= len(x):
        out [po:po + win] += x[pi:pi + win] * w
        norm[po:po + win] += w
        pi += hop; po += hop_out
    return (out / np.where(norm > 1e-8, norm, 1.0))[:n_out]


def time_pitch_adjust(x, semitones, speed):
    pf = 2 ** (semitones / 12.0)
    return ola_stretch(signal.resample(x, int(len(x) / pf)), pf / speed)


def make_ir(decay_s, seed):
    r = np.random.default_rng(seed)
    n = int(decay_s * SR)
    ir = r.standard_normal(n) * np.exp(-np.arange(n) / SR / (decay_s / 4))
    sos = signal.butter(2, 4000, "low", fs=SR, output="sos")
    ir = signal.sosfilt(sos, ir)
    return ir / np.sqrt(np.sum(ir ** 2) + 1e-12)


def apply_reverb(x, ir, wet):
    tail = signal.fftconvolve(x, ir)[: len(x)]
    tail /= np.max(np.abs(tail)) + 1e-12
    return (1 - wet) * x + wet * tail * (np.max(np.abs(x)) + 1e-12)


def pitch_layer(x, semitones, delay_ms=0, gain=1.0):
    pf = 2 ** (semitones / 12.0)
    s = signal.resample(x, int(len(x) / pf))
    s = s[:len(x)] if len(s) >= len(x) else np.pad(s, (0, len(x) - len(s)))
    d = int(delay_ms * SR / 1000)
    if d > 0:
        s = np.concatenate([np.zeros(d), s[:-d]])
    return s * gain


IR_ROOM  = make_ir(0.5, 31)
IR_HALL  = make_ir(1.8, 53)


# ---------------------------------------------------------------- effects

def fx_benegesserit(x):
    sub    = pitch_layer(x, -12, gain=0.18)
    chorus = (pitch_layer(x, -0.4, delay_ms=8,  gain=0.28) +
              pitch_layer(x,  0.6, delay_ms=15, gain=0.22) +
              pitch_layer(x, -0.9, delay_ms=23, gain=0.16))
    y = x + sub + chorus
    sos = signal.butter(2, [800, 3000], "bandpass", fs=SR, output="sos")
    y += signal.sosfilt(sos, y) * 0.30
    y = apply_reverb(y, IR_ROOM, wet=0.28)
    d = int(0.005 * SR)
    return y, np.concatenate([np.zeros(d), y[:-d]])


def fx_bitcrush(x):
    crush_sr = 7350
    small = signal.resample(x, max(1, int(len(x) * crush_sr / SR)))
    y = signal.resample(small, len(x))
    y = np.round(y * 128.0) / 128.0
    noise = rng.standard_normal(len(y)) * 0.025
    sos = signal.butter(2, 3000, "low", fs=SR, output="sos")
    noise = signal.sosfilt(sos, noise)
    y += noise
    sos2 = signal.butter(4, [400, 3000], "bandpass", fs=SR, output="sos")
    y = signal.sosfilt(sos2, y)
    return y, y.copy()


def fx_ringmod(x):
    n = len(x)
    carrier = np.sin(2 * np.pi * 72 * np.arange(n) / SR)
    y = x * carrier
    sos = signal.butter(2, 3500, "low", fs=SR, output="sos")
    y = signal.sosfilt(sos, y)
    y = 0.6 * y + 0.4 * x
    y = apply_reverb(y, IR_ROOM, wet=0.22)
    d = int(0.006 * SR)
    return y, np.concatenate([np.zeros(d), y[:-d]])


EFFECTS = [
    ("benegesserit", fx_benegesserit),
    ("bitcrush",     fx_bitcrush),
    ("ringmod",      fx_ringmod),
]


# ---------------------------------------------------------------- TTS

async def edge_to_wav(text, voice, path):
    import edge_tts
    tmp_mp3 = path.replace(".wav", ".mp3")
    await edge_tts.Communicate(text, voice=voice).save(tmp_mp3)
    subprocess.run(
        ["ffmpeg", "-y", "-i", tmp_mp3,
         "-ar", str(SR), "-ac", "1", "-sample_fmt", "s16", path],
        capture_output=True, check=True)
    os.remove(tmp_mp3)


# ---------------------------------------------------------------- main

async def main():
    total = 0
    with tempfile.TemporaryDirectory() as tmpdir:
        for voice_id, voice_tag in VOICES:
            print(f"\n[{voice_tag}]  {voice_id}")
            for cat, slug, text in LINES:
                semitones, speed = CAT_SETTINGS[cat]
                tmp = os.path.join(tmpdir, f"{slug}_{voice_tag}.wav")
                await edge_to_wav(text, voice_id, tmp)
                mono = load_wav_mono(tmp)
                mono = time_pitch_adjust(mono, semitones, speed)
                pad  = np.concatenate([np.zeros(int(0.15 * SR)),
                                        mono,
                                        np.zeros(int(0.30 * SR))])
                for fx_name, fx_fn in EFFECTS:
                    L, R = fx_fn(pad.copy())
                    ml   = min(len(L), len(R))
                    out  = os.path.join(OUT_DIR,
                               f"{cat}_{slug}_{voice_tag}_{fx_name}.wav")
                    save_stereo(out, L[:ml], R[:ml])
                    total += 1
                print(f"  {slug}")

    print(f"\n{total} files written to {OUT_DIR}")
    print(f"  {len(VOICES)} voices × {len(LINES)} lines × {len(EFFECTS)} effects")

asyncio.run(main())
