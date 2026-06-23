#!/usr/bin/env python3
"""
generate_voice_fx.py — experimental voice effects for the Dune RTS.

Regenerates the base gTTS speech (same pipeline as generate_voice_samples.py)
and applies 7 distinct effect chains, each named with its own suffix.
No existing files are overwritten.

Effects:
  _benegesserit  The Voice: sub-harmonic layer + chorus shimmer + formant
                 boost — sounds like the speaker occupies multiple registers
                 simultaneously. Authoritative, slightly supernatural.
  _megaphone     Outdoor field address: 500-2500 Hz hard-clip + AM carrier
                 buzz. Harsh and blaring.
  _sardaukar     Brutal military transmission: ultra-narrow band, extreme
                 drive, tight gate, opening static burst.
  _chorus        Ghostly shimmer: three detuned+delayed copies + wet reverb.
                 Good for spice/atmospheric lines.
  _bitcrush      Degraded/damaged comms: sample-rate + bit-depth reduction
                 + noise floor. Like a signal breaking up.
  _ringmod       Alien/mechanical: signal multiplied by 72 Hz carrier sine.
                 Classic sci-fi metallic texture.
  _whisper       Conspiratorial: fundamentals stripped, breathiness added.
                 For intel reports or ominous atmosphere.

Output: /workspace/music/voice/<category>_<slug>_<effect>.wav
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

CAT_SETTINGS = {
    "alert":  (-3, 1.25),
    "status": (-2, 1.10),
    "build":  (-2, 1.05),
    "order":  (-2, 1.00),
    "atmo":   (-3, 0.95),
}


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
    L, R = np.clip(L / peak * 0.88, -1, 1), np.clip(R / peak * 0.88, -1, 1)
    pcm = np.empty((len(L), 2))
    pcm[:, 0], pcm[:, 1] = L, R
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((pcm * 32767).astype(np.int16).tobytes())


def ola_stretch(x, stretch_factor, win_size=1024, hop=256):
    hop_out = max(1, int(hop * stretch_factor))
    n_out   = max(1, int(len(x) * stretch_factor))
    out = np.zeros(n_out + win_size)
    norm= np.zeros(n_out + win_size)
    win = np.hanning(win_size)
    pi, po = 0, 0
    while pi + win_size <= len(x):
        out [po:po + win_size] += x[pi:pi + win_size] * win
        norm[po:po + win_size] += win
        pi += hop; po += hop_out
    return (out / np.where(norm > 1e-8, norm, 1.0))[:n_out]


def time_pitch_adjust(x, semitones, speed_factor):
    pf = 2 ** (semitones / 12.0)
    stretched = signal.resample(x, int(len(x) / pf))
    return ola_stretch(stretched, pf / speed_factor)


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
    """Pitch-shifted + delayed copy of x, same length."""
    pf = 2 ** (semitones / 12.0)
    shifted = signal.resample(x, int(len(x) / pf))
    shifted = shifted[:len(x)] if len(shifted) >= len(x) \
              else np.pad(shifted, (0, len(x) - len(shifted)))
    d = int(delay_ms * SR / 1000)
    if d > 0:
        shifted = np.concatenate([np.zeros(d), shifted[:-d]])
    return shifted * gain


IR_ROOM   = make_ir(0.5, 31)
IR_HALL   = make_ir(1.8, 53)


def noise_gate(x, threshold=0.010):
    env = np.abs(signal.sosfilt(
        signal.butter(1, 80, "low", fs=SR, output="sos"), np.abs(x)))
    gate = np.clip(np.convolve((env > threshold).astype(float),
                               np.ones(int(0.005 * SR)), mode="same"), 0, 1)
    return x * gate


# ================================================================ EFFECTS

def fx_benegesserit(x):
    """
    The Voice: sub-harmonic + three detuned chorus copies + formant boost.
    Sounds like the speaker resonates in multiple registers at once.
    """
    sub = pitch_layer(x, -12, gain=0.18)                   # octave below

    chorus = (pitch_layer(x, -0.4, delay_ms=8,  gain=0.28) +
              pitch_layer(x,  0.6, delay_ms=15, gain=0.22) +
              pitch_layer(x, -0.9, delay_ms=23, gain=0.16))

    y = x + sub + chorus
    # boost vowel resonances 800-3000 Hz for that full, commanding presence
    sos = signal.butter(2, [800, 3000], "bandpass", fs=SR, output="sos")
    y += signal.sosfilt(sos, y) * 0.30
    y = apply_reverb(y, IR_ROOM, wet=0.28)
    # slight stereo spread via small L/R delay
    d = int(0.005 * SR)
    return y, np.concatenate([np.zeros(d), y[:-d]])


def fx_megaphone(x):
    """
    Outdoor field megaphone: 500-2500 Hz, hard clip, AM carrier buzz.
    """
    sos = signal.butter(4, [500, 2500], "bandpass", fs=SR, output="sos")
    y = signal.sosfilt(sos, x)
    y = np.clip(y * 10, -1, 1)                              # hard clip
    # AM carrier at 120 Hz: the buzzing transformer inside the horn
    carrier = 1.0 + 0.07 * np.sin(2 * np.pi * 120 * np.arange(len(y)) / SR)
    y *= carrier
    # narrow resonant peak in the horn
    sos2 = signal.butter(2, [900, 1800], "bandpass", fs=SR, output="sos")
    y += signal.sosfilt(sos2, y) * 0.25
    return y, y


def fx_sardaukar(x):
    """
    Brutal Sardaukar military transmission: ultra-narrow band, extreme
    drive, tight noise gate, opening burst of static.
    """
    # Very narrow radio band — colder and harsher than intercom
    sos = signal.butter(6, [600, 2200], "bandpass", fs=SR, output="sos")
    y = signal.sosfilt(sos, x)
    y = noise_gate(y, threshold=0.018)
    # extreme tanh drive — smashes dynamics flat
    y = np.tanh(y * 12) / np.tanh(12)
    # opening static burst (20 ms)
    burst_n = int(0.02 * SR)
    burst = rng.standard_normal(burst_n) * 0.4
    sos_b = signal.butter(4, [1000, 6000], "bandpass", fs=SR, output="sos")
    burst = signal.sosfilt(sos_b, burst)
    burst *= np.linspace(1, 0, burst_n) ** 2
    gap = int(0.03 * SR)
    y = np.concatenate([burst, np.zeros(gap), y])
    # completely dry — no reverb, in your face
    return y, y


def fx_chorus(x):
    """
    Ghostly shimmer: five detuned+delayed copies, lush wet reverb.
    Good for spice-trance or supernatural atmosphere lines.
    """
    layers = (pitch_layer(x,  0.0, delay_ms=0,  gain=1.00) +
              pitch_layer(x, -0.5, delay_ms=11, gain=0.55) +
              pitch_layer(x,  0.7, delay_ms=17, gain=0.50) +
              pitch_layer(x, -1.1, delay_ms=27, gain=0.35) +
              pitch_layer(x,  1.4, delay_ms=34, gain=0.30))
    y = apply_reverb(layers, IR_HALL, wet=0.55)
    d = int(0.009 * SR)
    return y, np.concatenate([np.zeros(d), y[:-d]])


def fx_bitcrush(x):
    """
    Degraded / damaged comms: sample-rate crush + bit reduction + noise floor.
    Sounds like a transmission breaking up or archival recording.
    """
    # Sample-rate crush: downsample to 7350 Hz (SR/6) and back
    crush_sr = 7350
    ratio = crush_sr / SR
    small = signal.resample(x, max(1, int(len(x) * ratio)))
    y = signal.resample(small, len(x))
    # Bit-depth crush to ~8 effective bits
    levels = 128.0
    y = np.round(y * levels) / levels
    # Noise floor that would exist on a degraded signal
    noise_floor = rng.standard_normal(len(y)) * 0.025
    sos = signal.butter(2, 3000, "low", fs=SR, output="sos")
    noise_floor = signal.sosfilt(sos, noise_floor)
    y = y + noise_floor
    # narrow bandpass to simulate old equipment
    sos2 = signal.butter(4, [400, 3000], "bandpass", fs=SR, output="sos")
    y = signal.sosfilt(sos2, y)
    return y, y


def fx_ringmod(x):
    """
    Ring modulation at 72 Hz: multiplies signal by a sine carrier.
    Creates a metallic, alien timbre — classic sci-fi.
    At low carrier frequencies the speech stays intelligible but sounds
    decidedly non-human.
    """
    n = len(x)
    carrier = np.sin(2 * np.pi * 72 * np.arange(n) / SR)
    y = x * carrier
    # light lowpass to tame the upper sidebands
    sos = signal.butter(2, 3500, "low", fs=SR, output="sos")
    y = signal.sosfilt(sos, y)
    # mix with a little dry so speech stays intelligible
    y = 0.6 * y + 0.4 * x
    y = apply_reverb(y, IR_ROOM, wet=0.22)
    d = int(0.006 * SR)
    return y, np.concatenate([np.zeros(d), y[:-d]])


def fx_whisper(x):
    """
    Conspiratorial whisper: strip the voiced fundamentals, keep the
    fricatives, add breath texture. Eerie for Intel / Bene Gesserit asides.
    """
    # Keep only high frequencies (consonants, sibilance)
    sos_hp = signal.butter(4, 1800, "high", fs=SR, output="sos")
    sibilance = signal.sosfilt(sos_hp, x) * 1.8
    # Generate shaped breath noise that follows the amplitude envelope
    env = np.abs(signal.sosfilt(
        signal.butter(1, 15, "low", fs=SR, output="sos"), np.abs(x)))
    breath_noise = rng.standard_normal(len(x))
    sos_bp = signal.butter(4, [800, 5000], "bandpass", fs=SR, output="sos")
    breath = signal.sosfilt(sos_bp, breath_noise) * env * 2.5
    y = sibilance + breath
    y = apply_reverb(y, IR_ROOM, wet=0.20)
    # binaural-ish: whisper right in the ear, slight L/R offset
    d = int(0.003 * SR)
    L = y
    R = np.concatenate([np.zeros(d), y[:-d]])
    return L * 0.85, R * 0.85


EFFECTS = [
    ("benegesserit", fx_benegesserit),
    ("megaphone",    fx_megaphone),
    ("sardaukar",    fx_sardaukar),
    ("chorus",       fx_chorus),
    ("bitcrush",     fx_bitcrush),
    ("ringmod",      fx_ringmod),
    ("whisper",      fx_whisper),
]


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

count = 0
with tempfile.TemporaryDirectory() as tmpdir:
    for cat, slug, text in LINES:
        semitones, speed = CAT_SETTINGS[cat]
        tmp = os.path.join(tmpdir, f"{slug}.wav")
        gtts_to_wav(text, tmp)
        mono = load_wav_mono(tmp)
        mono = time_pitch_adjust(mono, semitones, speed)
        pad = np.concatenate([np.zeros(int(0.15 * SR)),
                               mono,
                               np.zeros(int(0.35 * SR))])

        for fx_name, fx_fn in EFFECTS:
            out = os.path.join(OUT_DIR, f"{cat}_{slug}_{fx_name}.wav")
            L, R = fx_fn(pad.copy())
            # match length (some effects prepend bursts/delays)
            ml = min(len(L), len(R))
            save_stereo(out, L[:ml], R[:ml])
            count += 1

        print(f"  [{cat}] {text}")

print(f"\n{count} files written to {OUT_DIR}")
print("Effects: " + ", ".join(f"_{e}" for e, _ in EFFECTS))
