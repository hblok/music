#!/usr/bin/env python3
"""
generate_voice_samples.py — Dune RTS voice line generator.

All lines use gTTS (en-gb female, natural human voice). Each clip is then
post-processed with independent pitch-shift and time-stretch:

  THE TRICK — pitch lower + speak faster simultaneously:
    1. Resample to 1/pitch_factor length  →  pitch drops, audio gets LONGER
    2. OLA time-compress back to target   →  duration restored, pitch stays low
  OLA (Overlap-Add): chops audio into overlapping Hann-windowed frames and
  reassembles at a different hop distance — changes duration without touching
  frequency content. Same principle as every DAW's time-stretch tool.

  Alerts:  -3 semitones, 1.25x faster  — urgent, clipped, authoritative
  Status:  -2 semitones, 1.10x faster  — matter-of-fact
  Build:   -2 semitones, 1.05x faster  — clear, brisk
  Order:   -2 semitones, 1.00x         — calm, human
  Atmo:    -3 semitones, 0.95x slower  — slow, weighty

Post-processing flavours:
  _intercom : 300-3400 Hz bandpass + tanh overdrive + noise gate + radio
              click (alerts only) + short room reverb
  _distant  : same bandpass + heavy reverb + stereo spread

Output: /workspace/music/voice/<category>_<slug>_<flavour>.wav
"""

import os
import wave
import tempfile
import subprocess
import numpy as np
from scipy import signal

SR = 44100
OUT_DIR = "/workspace/music/voice"
os.makedirs(OUT_DIR, exist_ok=True)

# ---------------------------------------------------------------- voice lines
# Format: (category, slug, text)
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

# Per-category pitch and speed settings
CAT_SETTINGS = {
    #           semitones  speed_factor
    "alert":   (-3,        1.25),
    "status":  (-2,        1.10),
    "build":   (-2,        1.05),
    "order":   (-2,        1.00),
    "atmo":    (-3,        0.95),
}


# ---------------------------------------------------------------- helpers

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


def save_stereo(path, L, R):
    ne = min(int(0.015 * SR), len(L) // 4)
    for x in (L, R):
        x[:ne] *= np.linspace(0, 1, ne)
        x[-ne:] *= np.linspace(1, 0, ne)
    peak = max(np.max(np.abs(L)), np.max(np.abs(R)), 1e-9)
    L, R = np.clip(L / peak * 0.88, -1, 1), np.clip(R / peak * 0.88, -1, 1)
    pcm = np.empty((len(L), 2))
    pcm[:, 0], pcm[:, 1] = L, R
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((pcm * 32767).astype(np.int16).tobytes())


def ola_stretch(x, stretch_factor, win_size=1024, hop=256):
    """
    OLA time-stretch. stretch_factor < 1 = shorter (faster), > 1 = longer.
    Pitch is NOT affected — only duration changes.
    """
    hop_out = max(1, int(hop * stretch_factor))
    n_out = max(1, int(len(x) * stretch_factor))
    out  = np.zeros(n_out + win_size)
    norm = np.zeros(n_out + win_size)
    win  = np.hanning(win_size)
    pos_in = pos_out = 0
    while pos_in + win_size <= len(x):
        out [pos_out:pos_out + win_size] += x[pos_in:pos_in + win_size] * win
        norm[pos_out:pos_out + win_size] += win
        pos_in  += hop
        pos_out += hop_out
    norm = np.where(norm > 1e-8, norm, 1.0)
    return (out / norm)[:n_out]


def time_pitch_adjust(x, semitones, speed_factor):
    """
    Lower pitch by `semitones` (negative = lower) AND change speed
    independently using the resample + OLA trick.

      Step 1: resample to 1/pitch_factor length
              → pitch drops, audio becomes longer (1/pitch_factor × original)
      Step 2: OLA-compress to target_duration = original / speed_factor
              → duration restored to desired length, pitch stays shifted
    """
    pitch_factor = 2 ** (semitones / 12.0)          # e.g. 0.841 for -3 st

    # Step 1: resample — stretches duration, lowers pitch
    stretched = signal.resample(x, int(len(x) / pitch_factor))

    # Step 2: OLA compress/expand so final duration = original / speed_factor
    # stretched length is len(x)/pitch_factor; target is len(x)/speed_factor
    ola_factor = pitch_factor / speed_factor          # < 1 means compress
    result = ola_stretch(stretched, ola_factor)

    return result


def make_reverb_ir(decay_s, seed):
    rng = np.random.default_rng(seed)
    n = int(decay_s * SR)
    ir = rng.standard_normal(n) * np.exp(-np.arange(n) / SR / (decay_s / 4))
    sos = signal.butter(2, 4000, "low", fs=SR, output="sos")
    ir = signal.sosfilt(sos, ir)
    return ir / np.sqrt(np.sum(ir ** 2) + 1e-12)


def apply_reverb(x, ir, wet):
    tail = signal.fftconvolve(x, ir)[: len(x)]
    tail /= np.max(np.abs(tail)) + 1e-12
    return (1 - wet) * x + wet * tail * (np.max(np.abs(x)) + 1e-12)


IR_SHORT  = make_reverb_ir(0.5, 31)
IR_MEDIUM = make_reverb_ir(1.2, 53)
IR_LONG   = make_reverb_ir(2.5, 37)


def radio_click():
    n = int(0.004 * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(99)
    click = rng.standard_normal(n)
    sos = signal.butter(4, [1200, 8000], "bandpass", fs=SR, output="sos")
    click = signal.sosfilt(sos, click)
    click *= np.exp(-t * 1200) * (1 - np.exp(-t * 8000))
    click /= np.max(np.abs(click)) + 1e-12
    return click


def noise_gate(x, threshold=0.010):
    env = np.abs(signal.sosfilt(
        signal.butter(1, 80, "low", fs=SR, output="sos"), np.abs(x)))
    hold = int(0.005 * SR)
    gate = np.clip(np.convolve((env > threshold).astype(float),
                               np.ones(hold), mode="same"), 0, 1)
    return x * gate


CLICK = radio_click()

def intercom(mono, cat):
    sos = signal.butter(4, [300, 3400], "bandpass", fs=SR, output="sos")
    x = signal.sosfilt(sos, mono)
    x = noise_gate(x)
    drive = 4.5 if cat in ("alert", "status") else 3.0
    x = np.tanh(x * drive) / max(np.tanh(drive), 1e-9)
    if cat == "alert":
        gap = int(0.04 * SR)
        x = np.concatenate([CLICK, np.zeros(gap), x])
    x = apply_reverb(x, IR_SHORT, wet=0.38)
    # small stereo spread: 7 ms offset between ears — adds space without echo
    delay = int(0.007 * SR)
    L = x.copy()
    R = np.concatenate([np.zeros(delay), x[:-delay]])
    return L, R


def distant(mono):
    sos = signal.butter(4, [300, 3400], "bandpass", fs=SR, output="sos")
    x = signal.sosfilt(sos, mono)
    x = noise_gate(x)
    x = apply_reverb(x, IR_MEDIUM, wet=0.48)
    shift = int(0.012 * SR)
    L = x.copy()
    R = np.concatenate([np.zeros(shift), x[:-shift]])
    return L * 0.78, R * 0.78


# ---------------------------------------------------------------- TTS

def gtts_to_wav(text, tmp_wav):
    from gtts import gTTS
    tmp_mp3 = tmp_wav.replace(".wav", ".mp3")
    gTTS(text=text, lang="en", tld="co.uk", slow=False).save(tmp_mp3)
    subprocess.run(
        ["ffmpeg", "-y", "-i", tmp_mp3,
         "-ar", str(SR), "-ac", "1", "-sample_fmt", "s16", tmp_wav],
        capture_output=True, check=True)
    os.remove(tmp_mp3)


# ---------------------------------------------------------------- main

with tempfile.TemporaryDirectory() as tmpdir:
    for cat, slug, text in LINES:
        semitones, speed = CAT_SETTINGS[cat]
        print(f"  [{cat}] {text}  ({semitones:+d} st, {speed:.2f}x)")
        tmp = os.path.join(tmpdir, f"{slug}.wav")
        gtts_to_wav(text, tmp)
        mono = load_wav_mono(tmp)

        # independent pitch + speed adjustment
        processed = time_pitch_adjust(mono, semitones, speed)

        pad_pre  = int(0.15 * SR)
        pad_post = int(0.30 * SR)
        padded = np.concatenate([np.zeros(pad_pre), processed, np.zeros(pad_post)])

        iL, iR = intercom(padded.copy(), cat)
        save_stereo(os.path.join(OUT_DIR, f"{cat}_{slug}_intercom.wav"), iL, iR)

        dL, dR = distant(padded.copy())
        save_stereo(os.path.join(OUT_DIR, f"{cat}_{slug}_distant.wav"), dL, dR)

print(f"\n{len(LINES) * 2} files written to {OUT_DIR}")
