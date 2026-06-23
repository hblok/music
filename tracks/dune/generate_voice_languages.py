#!/usr/bin/env python3
"""
generate_voice_languages.py — explore non-English voice timbres for the
Dune RTS voice lines.

Four language strategies, each producing a different vocal quality:

  de  German  — English text fed to German TTS. Harder consonants, clipped
                vowels, authoritative. Good for enemy faction.
  fi  Finnish — English text fed to Finnish TTS. Unusually flat prosody,
                almost mechanical. Strange but intelligible.
  ja  Japanese— English pronunciation written in Katakana (the Japanese
                alphabet used specifically for foreign words), fed to
                Japanese TTS. The voice is distinctly Japanese but the
                words are phonetically English.
  ar  Arabic  — English pronunciation written in Arabic script
                (transliteration), fed to Arabic TTS. Arabic vocal timbre
                with English-ish words — very fitting for Dune's Fremen-
                inspired universe.

Each line gets two outputs:
  _<lang>_raw      — language voice + OLA pitch/speed, no FX
  _<lang>_intercom — same + the standard intercom chain

No existing files are overwritten. All output goes to /workspace/music/voice/
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

rng = np.random.default_rng(2342)

# ---------------------------------------------------------------- per-line text
# For de/fi: use plain English — the TTS reads it with its own accent.
# For ja: Katakana phonetic transcription of each English phrase.
# For ar: Arabic-script phonetic transcription (same sounds, Arabic letters).

LINES = {
    "base_under_attack": {
        "cat": "alert",
        "de":  "Our base is under attack!",
        "fi":  "Our base is under attack!",
        "ja":  "アワー ベース イズ アンダー アタック！",
        "ar":  "آور بيس إز أندر أتاك!",
    },
    "enemy_approaching": {
        "cat": "alert",
        "de":  "Enemy units approaching!",
        "fi":  "Enemy units approaching!",
        "ja":  "エネミー ユニッツ アプローチング！",
        "ar":  "إينيمي يونيتس أبروتشينج!",
    },
    "harvester_attacked": {
        "cat": "alert",
        "de":  "Harvester under attack!",
        "fi":  "Harvester under attack!",
        "ja":  "ハーベスター アンダー アタック！",
        "ar":  "هارفيستر أندر أتاك!",
    },
    "take_evasive_action": {
        "cat": "alert",
        "de":  "Take evasive action!",
        "fi":  "Take evasive action!",
        "ja":  "テイク イヴェイシブ アクション！",
        "ar":  "تيك إيفيسيف أكشن!",
    },
    "unit_lost": {
        "cat": "status",
        "de":  "Unit lost.",
        "fi":  "Unit lost.",
        "ja":  "ユニット ロスト。",
        "ar":  "يونيت لوست.",
    },
    "building_destroyed": {
        "cat": "status",
        "de":  "Building destroyed.",
        "fi":  "Building destroyed.",
        "ja":  "ビルディング ディストロイド。",
        "ar":  "بيلدينج ديستروييد.",
    },
    "low_power": {
        "cat": "status",
        "de":  "Low power.",
        "fi":  "Low power.",
        "ja":  "ロウ パワー。",
        "ar":  "لو باور.",
    },
    "spice_depleted": {
        "cat": "status",
        "de":  "Spice depleted.",
        "fi":  "Spice depleted.",
        "ja":  "スパイス ディプリーテッド。",
        "ar":  "سبايس ديبليتد.",
    },
    "construction_complete": {
        "cat": "build",
        "de":  "Construction complete.",
        "fi":  "Construction complete.",
        "ja":  "コンストラクション コンプリート。",
        "ar":  "كونستراكشن كومبليت.",
    },
    "place_structure": {
        "cat": "build",
        "de":  "Place your structure.",
        "fi":  "Place your structure.",
        "ja":  "プレイス ユア ストラクチャー。",
        "ar":  "بليس يور ستراكشر.",
    },
    "not_enough_credits": {
        "cat": "build",
        "de":  "Not enough credits.",
        "fi":  "Not enough credits.",
        "ja":  "ノット イナフ クレジッツ。",
        "ar":  "نوت إنف كريديتس.",
    },
    "yes_sir": {
        "cat": "order",
        "de":  "Yes, sir.",
        "fi":  "Yes, sir.",
        "ja":  "イエス サー。",
        "ar":  "يس سير.",
    },
    "moving_out": {
        "cat": "order",
        "de":  "Moving out.",
        "fi":  "Moving out.",
        "ja":  "ムービング アウト。",
        "ar":  "موفينج أوت.",
    },
    "orders_received": {
        "cat": "order",
        "de":  "Orders received.",
        "fi":  "Orders received.",
        "ja":  "オーダーズ リシーブド。",
        "ar":  "أوردرز ريسيفد.",
    },
    "worm_sign": {
        "cat": "atmo",
        "de":  "Worm sign. Get off the sand.",
        "fi":  "Worm sign. Get off the sand.",
        "ja":  "ワーム サイン。ゲット オフ ザ サンド。",
        "ar":  "وورم سايين. جيت أوف ذا ساند.",
    },
    "the_spice_must_flow": {
        "cat": "atmo",
        "de":  "The spice must flow.",
        "fi":  "The spice must flow.",
        "ja":  "ザ スパイス マスト フロウ。",
        "ar":  "ذا سبايس مست فلو.",
    },
}

LANGS = {
    "de": "de",     # German
    "fi": "fi",     # Finnish
    "ja": "ja",     # Japanese
    "ar": "ar",     # Arabic
}

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
    L, R = np.clip(L / peak * 0.88, -1, 1), np.clip(R / peak * 0.88, -1, 1)
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
    w = np.hanning(win)
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


def reverb(x, ir, wet):
    tail = signal.fftconvolve(x, ir)[: len(x)]
    tail /= np.max(np.abs(tail)) + 1e-12
    return (1 - wet) * x + wet * tail * (np.max(np.abs(x)) + 1e-12)


def noise_gate(x, thr=0.010):
    env = np.abs(signal.sosfilt(
        signal.butter(1, 80, "low", fs=SR, output="sos"), np.abs(x)))
    gate = np.clip(np.convolve((env > thr).astype(float),
                               np.ones(int(0.005 * SR)), mode="same"), 0, 1)
    return x * gate


IR_SHORT  = make_ir(0.5, 31)
IR_MEDIUM = make_ir(1.2, 53)


def radio_click():
    n = int(0.004 * SR)
    t = np.arange(n) / SR
    click = np.random.default_rng(99).standard_normal(n)
    sos = signal.butter(4, [1200, 8000], "bandpass", fs=SR, output="sos")
    click = signal.sosfilt(sos, click)
    click *= np.exp(-t * 1200) * (1 - np.exp(-t * 8000))
    return click / (np.max(np.abs(click)) + 1e-12)


CLICK = radio_click()


def intercom(x, cat):
    sos = signal.butter(4, [300, 3400], "bandpass", fs=SR, output="sos")
    x = signal.sosfilt(sos, x)
    x = noise_gate(x)
    drive = 4.5 if cat in ("alert", "status") else 3.0
    x = np.tanh(x * drive) / max(np.tanh(drive), 1e-9)
    if cat == "alert":
        x = np.concatenate([CLICK, np.zeros(int(0.04 * SR)), x])
    x = reverb(x, IR_SHORT, wet=0.38)
    d = int(0.007 * SR)
    return x, np.concatenate([np.zeros(d), x[:-d]])


# ---------------------------------------------------------------- TTS

def gtts_to_wav(text, lang_code, tmp_wav):
    from gtts import gTTS
    tmp_mp3 = tmp_wav.replace(".wav", ".mp3")
    gTTS(text=text, lang=lang_code, slow=False).save(tmp_mp3)
    subprocess.run(
        ["ffmpeg", "-y", "-i", tmp_mp3,
         "-ar", str(SR), "-ac", "1", "-sample_fmt", "s16", tmp_wav],
        capture_output=True, check=True)
    os.remove(tmp_mp3)


# ---------------------------------------------------------------- main

count = 0
with tempfile.TemporaryDirectory() as tmpdir:
    for slug, data in LINES.items():
        cat = data["cat"]
        semitones, speed = CAT_SETTINGS[cat]
        for lang_code in LANGS:
            text = data[lang_code]
            print(f"  [{lang_code}/{cat}] {text[:50]}")
            tmp = os.path.join(tmpdir, f"{slug}_{lang_code}.wav")
            try:
                gtts_to_wav(text, lang_code, tmp)
            except Exception as e:
                print(f"    SKIP ({e})")
                continue

            mono = load_wav_mono(tmp)
            mono = time_pitch_adjust(mono, semitones, speed)
            pad  = np.concatenate([np.zeros(int(0.15 * SR)),
                                    mono,
                                    np.zeros(int(0.35 * SR))])

            # raw (pitched/sped, no FX)
            save_stereo(
                os.path.join(OUT_DIR, f"{cat}_{slug}_{lang_code}_raw.wav"),
                pad)
            count += 1

            # intercom
            iL, iR = intercom(pad.copy(), cat)
            ml = min(len(iL), len(iR))
            save_stereo(
                os.path.join(OUT_DIR, f"{cat}_{slug}_{lang_code}_intercom.wav"),
                iL[:ml], iR[:ml])
            count += 1

print(f"\n{count} files written to {OUT_DIR}")
print("Languages: de (German), fi (Finnish), ja (Japanese katakana),",
      "ar (Arabic phonetic)")
print("Flavours per line: _raw, _intercom")
