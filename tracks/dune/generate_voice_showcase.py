#!/usr/bin/env python3
"""
generate_voice_showcase.py — voice variety showcase for the Dune RTS.

Uses three representative lines to compare voices:
  "Our base is under attack!"   — tests urgency and energy
  "Orders received."            — tests short acknowledgement / character
  "The spice must flow."        — tests gravitas and atmosphere

Two source groups:

  edge-tts  15 curated neural voices — male and female, across GB, US,
            AU, IE, IN, ZA, NG, HK. Needs internet. Async API.
            File naming: <slug>_edge_<tag>.wav
            e.g. base_under_attack_edge_gb_ryan_m.wav

  gTTS      5 English accent variants via the tld parameter (US, AU,
            Indian, Canadian, Irish). Quick comparison baseline.
            File naming: <slug>_gtts_<accent>.wav

Each file gets the standard intercom chain (bandpass + overdrive +
reverb + stereo spread) and OLA pitch/speed adjustment.
Output: /workspace/music/voice/showcase/
"""

import os
import asyncio
import wave
import tempfile
import subprocess
import numpy as np
from scipy import signal

SR = 44100
OUT_DIR = "/workspace/music/voice/showcase"
os.makedirs(OUT_DIR, exist_ok=True)

# ---------------------------------------------------------------- showcase lines
LINES = [
    ("alert", "base_under_attack",   "Our base is under attack!"),
    ("order", "orders_received",     "Orders received."),
    ("atmo",  "the_spice_must_flow", "The spice must flow."),
]

CAT_SETTINGS = {
    "alert": (-3, 1.25),
    "order": (-2, 1.00),
    "atmo":  (-3, 0.95),
}

# ---------------------------------------------------------------- edge-tts voices
# Tag format: <locale>_<name_abbrev>_<m/f>
EDGE_VOICES = [
    # British
    ("en-GB-RyanNeural",               "gb_ryan_m"),
    ("en-GB-ThomasNeural",             "gb_thomas_m"),
    ("en-GB-SoniaNeural",              "gb_sonia_f"),
    # American
    ("en-US-GuyNeural",                "us_guy_m"),
    ("en-US-ChristopherNeural",        "us_christopher_m"),
    ("en-US-BrianNeural",              "us_brian_m"),
    ("en-US-AriaNeural",               "us_aria_f"),
    # Australian
    ("en-AU-WilliamMultilingualNeural","au_william_m"),
    ("en-AU-NatashaNeural",            "au_natasha_f"),
    # Irish
    ("en-IE-ConnorNeural",             "ie_connor_m"),
    ("en-IE-EmilyNeural",              "ie_emily_f"),
    # Indian
    ("en-IN-PrabhatNeural",            "in_prabhat_m"),
    ("en-IN-NeerjaExpressiveNeural",   "in_neerja_f"),
    # South African
    ("en-ZA-LukeNeural",               "za_luke_m"),
    # Nigerian
    ("en-NG-AbeoNeural",               "ng_abeo_m"),
]

# ---------------------------------------------------------------- gTTS accents
GTTS_ACCENTS = [
    ("com",    "us"),       # American
    ("com.au", "au"),       # Australian
    ("co.in",  "in"),       # Indian
    ("ca",     "ca"),       # Canadian
    ("ie",     "ie"),       # Irish
]


# ---------------------------------------------------------------- shared utils

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


def noise_gate(x, thr=0.010):
    env = np.abs(signal.sosfilt(
        signal.butter(1, 80, "low", fs=SR, output="sos"), np.abs(x)))
    gate = np.clip(np.convolve((env > thr).astype(float),
                               np.ones(int(0.005 * SR)), mode="same"), 0, 1)
    return x * gate


def radio_click():
    n = int(0.004 * SR)
    t = np.arange(n) / SR
    click = np.random.default_rng(99).standard_normal(n)
    sos = signal.butter(4, [1200, 8000], "bandpass", fs=SR, output="sos")
    click = signal.sosfilt(sos, click)
    click *= np.exp(-t * 1200) * (1 - np.exp(-t * 8000))
    return click / (np.max(np.abs(click)) + 1e-12)


IR_SHORT = make_ir(0.5, 31)
CLICK    = radio_click()


def intercom(x, cat):
    sos = signal.butter(4, [300, 3400], "bandpass", fs=SR, output="sos")
    x = signal.sosfilt(sos, x)
    x = noise_gate(x)
    drive = 4.5 if cat in ("alert", "status") else 3.0
    x = np.tanh(x * drive) / max(np.tanh(drive), 1e-9)
    if cat == "alert":
        x = np.concatenate([CLICK, np.zeros(int(0.04 * SR)), x])
    x = apply_reverb(x, IR_SHORT, wet=0.38)
    d = int(0.007 * SR)
    R = np.concatenate([np.zeros(d), x[:-d]])
    return x, R


def process_and_save(mono, cat, slug, tag):
    semitones, speed = CAT_SETTINGS[cat]
    processed = time_pitch_adjust(mono, semitones, speed)
    pad = np.concatenate([np.zeros(int(0.15 * SR)),
                          processed,
                          np.zeros(int(0.30 * SR))])
    L, R = intercom(pad, cat)
    ml = min(len(L), len(R))
    save_stereo(os.path.join(OUT_DIR, f"{slug}_{tag}.wav"), L[:ml], R[:ml])


# ---------------------------------------------------------------- edge-tts synthesis

async def edge_synthesise(text, voice, path):
    import edge_tts
    tmp_mp3 = path.replace(".wav", ".mp3")
    comm = edge_tts.Communicate(text, voice=voice)
    await comm.save(tmp_mp3)
    subprocess.run(
        ["ffmpeg", "-y", "-i", tmp_mp3,
         "-ar", str(SR), "-ac", "1", "-sample_fmt", "s16", path],
        capture_output=True, check=True)
    os.remove(tmp_mp3)


async def run_edge(tmpdir):
    import edge_tts
    total = 0
    for voice, tag in EDGE_VOICES:
        print(f"\n  [edge-tts] {tag}  ({voice})")
        for cat, slug, text in LINES:
            tmp = os.path.join(tmpdir, f"{slug}_{tag}.wav")
            try:
                await edge_synthesise(text, voice, tmp)
                mono = load_wav_mono(tmp)
                process_and_save(mono, cat, slug, f"edge_{tag}")
                print(f"    {slug}")
                total += 1
            except Exception as e:
                print(f"    SKIP {slug}: {e}")
    return total


# ---------------------------------------------------------------- gTTS synthesis

def run_gtts(tmpdir):
    from gtts import gTTS
    total = 0
    for tld, accent_tag in GTTS_ACCENTS:
        print(f"\n  [gTTS] tld={tld}  ({accent_tag})")
        for cat, slug, text in LINES:
            tmp_mp3 = os.path.join(tmpdir, f"{slug}_{accent_tag}.mp3")
            tmp_wav = tmp_mp3.replace(".mp3", ".wav")
            try:
                gTTS(text=text, lang="en", tld=tld, slow=False).save(tmp_mp3)
                subprocess.run(
                    ["ffmpeg", "-y", "-i", tmp_mp3,
                     "-ar", str(SR), "-ac", "1", "-sample_fmt", "s16", tmp_wav],
                    capture_output=True, check=True)
                os.remove(tmp_mp3)
                mono = load_wav_mono(tmp_wav)
                process_and_save(mono, cat, slug, f"gtts_{accent_tag}")
                print(f"    {slug}")
                total += 1
            except Exception as e:
                print(f"    SKIP {slug}: {e}")
    return total


# ---------------------------------------------------------------- main

async def main():
    with tempfile.TemporaryDirectory() as tmpdir:
        print("=== edge-tts neural voices ===")
        n_edge = await run_edge(tmpdir)
        print("\n=== gTTS accent variants ===")
        n_gtts = run_gtts(tmpdir)

    total = n_edge + n_gtts
    print(f"\n{total} files written to {OUT_DIR}")
    print("\nNaming: <line>_edge_<locale>_<name>_<m/f>.wav")
    print("        <line>_gtts_<accent>.wav")
    print("\nLines:")
    for _, slug, text in LINES:
        print(f"  {slug:<28} '{text}'")

asyncio.run(main())
