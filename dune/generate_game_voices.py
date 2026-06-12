#!/usr/bin/env python3
"""
generate_game_voices.py — Pre-generate all in-game voice lines.

Reads voice_config.json to know which edge-tts voice + effect to use per
faction × role, then synthesises every cue phrase and writes the result
directly into the game's data directory:

  dune_prototype/data/voice/{faction}/{role}/{cue_name}.wav

Run this whenever voice_cues.json gains new cues, or when you want to
switch voice packs (edit voice_config.json, re-run, done).

Output audio key format (matches BootScene + VoiceSystem):
  voice_{faction}_{role}_{cue_name}

Usage:
  cd /repos/dune
  python music/generate_game_voices.py [--dry-run]

Dependencies: edge-tts, ffmpeg on PATH, numpy, scipy.
"""

import os
import sys
import json
import asyncio
import wave
import tempfile
import subprocess
import numpy as np
from scipy import signal

# ---------------------------------------------------------------------------
# Paths

REPO_ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME_DIR     = os.path.join(REPO_ROOT, "dune_prototype")
VOICE_CONFIG = os.path.join(GAME_DIR, "data", "voice_config.json")
VOICE_CUES   = os.path.join(GAME_DIR, "data", "voice_cues.json")
OUT_BASE     = os.path.join(GAME_DIR, "data", "voice")

SR  = 44100
DRY_RUN = "--dry-run" in sys.argv

# ---------------------------------------------------------------------------
# Per-role synthesis settings (pitch shift in semitones, speed multiplier)

ROLE_SETTINGS = {
    "advisor":  {"semitones": -2,  "speed": 1.05},
    "infantry": {"semitones": -2,  "speed": 1.15},
    "heavy":    {"semitones": -3,  "speed": 1.05},
}

# ---------------------------------------------------------------------------
# Phrases for every cue key (advisor cues + ack variants)

PHRASES = {
    # advisor — strategic announcements
    "base_under_attack":               "Our base is under attack!",
    "wormsign":                        "Worm sign. Get off the sand.",
    "enemy_vehicle_approaching_north": "Warning! Enemy vehicle approaching from the north.",
    "enemy_vehicle_approaching_south": "Warning! Enemy vehicle approaching from the south.",
    "enemy_vehicle_approaching_east":  "Warning! Enemy vehicle approaching from the east.",
    "enemy_vehicle_approaching_west":  "Warning! Enemy vehicle approaching from the west.",
    "enemy_unit_approaching":          "Warning! Enemy unit approaching.",
    "structure_destroyed":             "Structure destroyed.",
    "unit_destroyed":                  "Unit destroyed.",
    "harvester_attacked":              "Warning! Harvester under attack!",
    "missile_launched":                "Missile launched!",
    "spice_bloom":                     "Spice bloom.",
    "spice_field_located":             "Spice field located.",
    "construction_complete":           "Construction complete.",
    "production_complete":             "Unit deployed.",
    "harvester_deployed":              "Harvester deployed.",
    "harvester_arrived":               "Harvester arrived.",
    "radar_on":                        "Radar activated.",
    "radar_off":                       "Radar deactivated.",
    "repair_complete":                 "Repair complete.",
    "fremen_deployed":                 "Fremen deployed.",
    "victory":                         "Your mission is complete. Select your next conquest.",
    "defeat":                          "You have failed your mission.",
    # unit acknowledgement variants (used for both infantry and heavy roles)
    "ack_yes_sir":         "Yes, sir.",
    "ack_moving_out":      "Moving out.",
    "ack_orders_received": "Orders received.",
    "ack_affirmative":     "Affirmative.",
}

# ---------------------------------------------------------------------------
# DSP utilities

rng = np.random.default_rng(2342)


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
        x[:ne]  *= np.linspace(0, 1, ne)
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
    tail = signal.fftconvolve(x, ir)[:len(x)]
    tail /= np.max(np.abs(tail)) + 1e-12
    return (1 - wet) * x + wet * tail * (np.max(np.abs(x)) + 1e-12)


def pitch_layer(x, semitones, delay_ms=0, gain=1.0):
    pf = 2 ** (semitones / 12.0)
    s  = signal.resample(x, int(len(x) / pf))
    s  = s[:len(x)] if len(s) >= len(x) else np.pad(s, (0, len(x) - len(s)))
    d  = int(delay_ms * SR / 1000)
    if d > 0:
        s = np.concatenate([np.zeros(d), s[:-d]])
    return s * gain


def noise_gate(x, thr=0.010):
    env = np.abs(signal.sosfilt(
        signal.butter(1, 80, "low", fs=SR, output="sos"), np.abs(x)))
    gate = np.clip(np.convolve(
        (env > thr).astype(float), np.ones(int(0.005 * SR)), mode="same"), 0, 1)
    return x * gate


def radio_click():
    n  = int(0.004 * SR)
    t  = np.arange(n) / SR
    c  = np.random.default_rng(99).standard_normal(n)
    sos = signal.butter(4, [1200, 8000], "bandpass", fs=SR, output="sos")
    c  = signal.sosfilt(sos, c)
    c  *= np.exp(-t * 1200) * (1 - np.exp(-t * 8000))
    return c / (np.max(np.abs(c)) + 1e-12)


IR_ROOM   = make_ir(0.5,  31)
IR_HALL   = make_ir(1.8,  53)
CLICK     = radio_click()


# ---------------------------------------------------------------------------
# Effects  (each returns (L, R) stereo numpy arrays)

def fx_benegesserit(x):
    sub    = pitch_layer(x, -12, gain=0.18)
    chorus = (pitch_layer(x, -0.4, delay_ms=8,  gain=0.28) +
              pitch_layer(x,  0.6, delay_ms=15, gain=0.22) +
              pitch_layer(x, -0.9, delay_ms=23, gain=0.16))
    y = x + sub + chorus
    sos = signal.butter(2, [800, 3000], "bandpass", fs=SR, output="sos")
    y  += signal.sosfilt(sos, y) * 0.30
    y   = apply_reverb(y, IR_ROOM, wet=0.28)
    d   = int(0.005 * SR)
    return y, np.concatenate([np.zeros(d), y[:-d]])


def fx_bitcrush(x):
    crush_sr = 7350
    small = signal.resample(x, max(1, int(len(x) * crush_sr / SR)))
    y     = signal.resample(small, len(x))
    y     = np.round(y * 128.0) / 128.0
    noise = rng.standard_normal(len(y)) * 0.025
    sos   = signal.butter(2, 3000, "low", fs=SR, output="sos")
    noise = signal.sosfilt(sos, noise)
    y    += noise
    sos2  = signal.butter(4, [400, 3000], "bandpass", fs=SR, output="sos")
    y     = signal.sosfilt(sos2, y)
    return y, y.copy()


def fx_ringmod(x):
    n       = len(x)
    carrier = np.sin(2 * np.pi * 72 * np.arange(n) / SR)
    y       = x * carrier
    sos     = signal.butter(2, 3500, "low", fs=SR, output="sos")
    y       = signal.sosfilt(sos, y)
    y       = 0.6 * y + 0.4 * x
    y       = apply_reverb(y, IR_ROOM, wet=0.22)
    d       = int(0.006 * SR)
    return y, np.concatenate([np.zeros(d), y[:-d]])


def fx_intercom(x, is_alert=False):
    sos = signal.butter(4, [300, 3400], "bandpass", fs=SR, output="sos")
    x   = signal.sosfilt(sos, x)
    x   = noise_gate(x)
    drive = 4.5 if is_alert else 3.0
    x   = np.tanh(x * drive) / max(np.tanh(drive), 1e-9)
    if is_alert:
        x = np.concatenate([CLICK, np.zeros(int(0.04 * SR)), x])
    x   = apply_reverb(x, IR_ROOM, wet=0.38)
    d   = int(0.007 * SR)
    return x, np.concatenate([np.zeros(d), x[:-d]])


EFFECT_FNS = {
    "benegesserit": lambda x, alert: fx_benegesserit(x),
    "bitcrush":     lambda x, alert: fx_bitcrush(x),
    "ringmod":      lambda x, alert: fx_ringmod(x),
    "intercom":     lambda x, alert: fx_intercom(x, alert),
}

ALERT_CUES = {
    "base_under_attack", "wormsign", "harvester_attacked", "missile_launched",
    "enemy_vehicle_approaching_north", "enemy_vehicle_approaching_south",
    "enemy_vehicle_approaching_east",  "enemy_vehicle_approaching_west",
    "enemy_unit_approaching",
}


# ---------------------------------------------------------------------------
# TTS

async def edge_to_wav(text, voice, path):
    import edge_tts
    tmp_mp3 = path.replace(".wav", "_tmp.mp3")
    await edge_tts.Communicate(text, voice=voice).save(tmp_mp3)
    subprocess.run(
        ["ffmpeg", "-y", "-i", tmp_mp3,
         "-ar", str(SR), "-ac", "1", "-sample_fmt", "s16", path],
        capture_output=True, check=True)
    os.remove(tmp_mp3)


# ---------------------------------------------------------------------------
# Main

async def main():
    with open(VOICE_CONFIG) as f:
        config = json.load(f)
    with open(VOICE_CUES) as f:
        cues_data = json.load(f)

    # Build the list of (faction, role, cue_name) triples to generate.
    # For variant cues, expand each variant as a separate file.
    targets = []
    for faction, roles in config.items():
        if faction.startswith("_"):
            continue
        for role, voice_cfg in roles.items():
            # Collect all cue names for this role
            cue_names = set()
            for cue_name, cue_def in cues_data["cues"].items():
                if cue_def.get("role") != role:
                    continue
                if "variants" in cue_def:
                    cue_names.update(cue_def["variants"])
                else:
                    cue_names.add(cue_name)
            for cue_name in sorted(cue_names):
                if cue_name not in PHRASES:
                    print(f"  WARN: no phrase for '{cue_name}' — skipping")
                    continue
                targets.append((faction, role, cue_name, voice_cfg))

    total = len(targets)
    print(f"{total} files to generate\n")
    if DRY_RUN:
        for faction, role, cue_name, vcfg in targets:
            out_path = os.path.join(OUT_BASE, faction, role, f"{cue_name}.wav")
            print(f"  {out_path}")
        return

    generated = 0
    with tempfile.TemporaryDirectory() as tmpdir:
        for faction, role, cue_name, voice_cfg in targets:
            out_dir = os.path.join(OUT_BASE, faction, role)
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, f"{cue_name}.wav")

            voice   = _VOICE_IDS[voice_cfg["voice"]]
            effect  = voice_cfg["effect"]
            phrase  = PHRASES[cue_name]
            settings = ROLE_SETTINGS[role]

            tmp_wav = os.path.join(tmpdir, f"{faction}_{role}_{cue_name}.wav")
            try:
                await edge_to_wav(phrase, voice, tmp_wav)
            except Exception as e:
                print(f"  SKIP [{faction}/{role}/{cue_name}]: TTS error — {e}")
                continue

            mono = load_wav_mono(tmp_wav)
            mono = time_pitch_adjust(mono, settings["semitones"], settings["speed"])
            pad  = np.concatenate([
                np.zeros(int(0.12 * SR)),
                mono,
                np.zeros(int(0.25 * SR)),
            ])

            is_alert = cue_name in ALERT_CUES
            fx_fn = EFFECT_FNS.get(effect)
            if fx_fn is None:
                print(f"  WARN: unknown effect '{effect}' — using intercom")
                fx_fn = EFFECT_FNS["intercom"]

            L, R = fx_fn(pad.copy(), is_alert)
            ml   = min(len(L), len(R))
            save_stereo(out_path, L[:ml], R[:ml])
            generated += 1
            print(f"  [{faction}/{role}] {cue_name}.wav")

    print(f"\n{generated}/{total} files written to {OUT_BASE}/")


# ---------------------------------------------------------------------------
# Voice ID map — tag → edge-tts voice ID

_VOICE_IDS = {
    "au_william_m": "en-AU-WilliamMultilingualNeural",
    "au_natasha_f": "en-AU-NatashaNeural",
    "us_aria_f":    "en-US-AriaNeural",
    "us_guy_m":     "en-US-GuyNeural",
    # extras easy to add
    "gb_ryan_m":    "en-GB-RyanNeural",
    "ie_connor_m":  "en-IE-ConnorNeural",
}

asyncio.run(main())
