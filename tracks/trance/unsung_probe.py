#!/usr/bin/env python3
"""
unsung_probe.py — Stage 1 of the "Unsung" plan (ungesungen_notes.md,
question 2: probe first). Renders ONE hook line three ways over a bare
Am-F-C-G pad, back to back in a single WAV, so the sung-voice treatment
can be chosen by listening before the full track is built:

  variant A — pure TTS+OLA singing: the edge-tts syllable is pitch-shifted
              to the target note by plain resample (nearest of two base
              renders keeps ratios small) and OLA time-stretched onto the
              melody grid. The TTS prosody's pitch drift survives inside
              each syllable — speech bent into tune.
  variant B — HYBRID (the C7 recipe): the TTS consonant onset (and coda,
              for consonant-final syllables) grafted onto a synth vowel
              that holds the target pitch perfectly — real intelligibility,
              synth control. This is the recommended treatment.
  variant C — sihaya-style vowel engine alone (the control): no TTS at
              all, pure synth vowels — pitch-perfect but reads as an
              invented language.

The hook: "So long unsung — until tonight."  (4+4 syllables, Q/A)
Melody (A natural minor): Q rises A3-C4-D4 to hang on E4; A falls
E4-D4-C4 home to A3. 132 BPM, one chord per bar Am-F-C-G.

Voice: en-US-AriaNeural (English female, per the notes' answers).
Syllable renders are cached to /workspace/music/samples/unsung/ —
cache-first, no network needed after the first run.

Output: /workspace/music/unsung_probe.wav (+ mp3). Throwaway name — not
a track. Prints a per-note pitch table (target vs measured, cents) for
variants A and B.
"""

import asyncio
import os
import subprocess
import wave
import numpy as np
from scipy import signal

SR = 44100
BPM = 132.0
BEAT = 60.0 / BPM
BAR = BEAT * 4

VOICE_ID = "en-US-AriaNeural"
CACHE_DIR = "/workspace/music/samples/unsung"

# The hook: (syllable, midi, dur_beats). 16 beats = 4 bars.
# Q: so-long-un-SUNG (hangs on E4, off-tonic); A: un-til-to-NIGHT (home to A3).
HOOK = [("so", 57, 1.0), ("long", 60, 1.0), ("un", 62, 1.0), ("sung", 64, 5.0),
        ("un", 64, 1.0), ("til", 62, 1.0), ("to", 60, 1.0), ("night", 57, 3.0)]

# Per-syllable graft plan for the hybrid: (onset_s, coda_s, vowel f1/f2 —
# female-range formants; "night" is a diphthong a->i, morphed over the note).
SYL = {
    "so":    dict(onset=0.12, coda=0.00, v1=(450, 900),  v2=None),
    "long":  dict(onset=0.10, coda=0.12, v1=(600, 950),  v2=None),
    "un":    dict(onset=0.00, coda=0.10, v1=(650, 1250), v2=None),
    "sung":  dict(onset=0.10, coda=0.14, v1=(650, 1250), v2=None),
    "til":   dict(onset=0.10, coda=0.10, v1=(420, 2100), v2=None),
    "to":    dict(onset=0.10, coda=0.00, v1=(380, 850),  v2=None),
    "night": dict(onset=0.10, coda=0.10, v1=(750, 1350), v2=(350, 2300)),
}


def midi_to_hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


# ------------------------------------------------------------ TTS + cache

def tts_syllable(text, pitch_off):
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, f"{text}_{pitch_off:+d}.wav")
    if not os.path.exists(path):
        import edge_tts
        tmp = path + ".mp3"
        kw = {"pitch": f"{pitch_off:+d}Hz"} if pitch_off else {}

        async def go():
            await edge_tts.Communicate(text, voice=VOICE_ID, **kw).save(tmp)

        asyncio.run(go())
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp,
                        "-ar", str(SR), "-ac", "1", path], check=True)
        os.remove(tmp)
    with wave.open(path, "rb") as w:
        v = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(float)
    return v / (np.max(np.abs(v)) + 1e-12)


def trim(x, thresh_db=-40):
    env = np.abs(signal.hilbert(x))
    k = int(0.005 * SR)
    env = np.convolve(env, np.ones(k) / k, mode="same")
    th = 10 ** (thresh_db / 20) * np.max(env)
    idx = np.where(env > th)[0]
    return x[idx[0]:idx[-1] + 1] if len(idx) else x


def estimate_f0(x, lo=120, hi=520):
    k = int(0.09 * SR)
    if len(x) < k + 1:
        return 0.0
    e = np.convolve(x ** 2, np.ones(k), mode="valid")
    i0 = int(np.argmax(e))
    seg = x[i0:i0 + k] * np.hanning(k)
    ac = signal.correlate(seg, seg, mode="full")[k - 1:]
    lag_lo, lag_hi = int(SR / hi), int(SR / lo)
    lag = lag_lo + int(np.argmax(ac[lag_lo:lag_hi]))
    return SR / lag


def get_syllable(text, target_hz):
    """Trimmed TTS syllable, resampled so its measured f0 hits target_hz.
    Two base renders (+0 / +60 Hz) keep the resample ratio small (< ~6 %),
    so the formant shift stays inaudible."""
    best = None
    for off in (0, 60):
        x = trim(tts_syllable(text, off))
        f0 = estimate_f0(x)
        if f0 <= 0:
            continue
        r = target_hz / f0
        if best is None or abs(np.log(r)) < abs(np.log(best[1])):
            best = (x, r)
    x, r = best
    idx = np.arange(0, len(x) - 1, r)
    return x[idx.astype(int)]


# ---------------------------------------------------------------- OLA

def ola_stretch(x, factor, frame=1024, hop=256):
    """Duration x factor, pitch unchanged. Hann frames re-laid at hop*factor."""
    if abs(factor - 1.0) < 1e-3:
        return x.copy()
    win = np.hanning(frame)
    n_out = int(len(x) * factor) + frame
    out = np.zeros(n_out)
    norm = np.zeros(n_out)
    pos = 0.0
    while pos + frame < len(x):
        i, o = int(pos), int(pos * factor)
        out[o:o + frame] += x[i:i + frame] * win
        norm[o:o + frame] += win
        pos += hop
    out /= np.maximum(norm, 1e-3)
    return out[: int(len(x) * factor)]


# ------------------------------------------------- the synth vowel voice
# sihaya-lite female: rolled-off harmonic source with blooming vibrato,
# two formant peaks (Q=8, f2 at 0.7), a lowpassed chest layer so the
# fundamental survives, 8 % breath.

def vowel_note(f_hz, dur, v1, v2=None, vib_depth=0.008):
    n = int((dur + 0.30) * SR)
    tt = np.arange(n) / SR
    bloom = np.clip(tt / 0.5, 0, 1)
    f = f_hz * (1.0 + vib_depth * np.sin(2 * np.pi * 5.7 * tt) * bloom)
    ph = 2 * np.pi * np.cumsum(f) / SR
    src = np.zeros(n)
    for k in range(1, max(3, int(4800 / f_hz)) + 1):
        src += np.sin(k * ph) / k ** 1.2
    src /= np.max(np.abs(src)) + 1e-12

    def formant(sig, ff):
        f1, f2 = ff
        b1, a1 = signal.iirpeak(f1, Q=8, fs=SR)
        b2, a2 = signal.iirpeak(f2, Q=8, fs=SR)
        y = signal.lfilter(b1, a1, sig) + 0.7 * signal.lfilter(b2, a2, sig)
        return y / (np.sqrt(np.mean(y ** 2)) + 1e-12)

    y = formant(src, v1)
    if v2 is not None:                       # diphthong: morph across the note
        y2 = formant(src, v2)
        m = np.clip((tt - 0.35 * dur) / (0.55 * dur), 0, 1)
        y = (1 - m) * y + m * y2
    chest = signal.sosfilt(signal.butter(2, 750, "low", fs=SR, output="sos"), src)
    chest /= np.sqrt(np.mean(chest ** 2)) + 1e-12
    breath = signal.sosfilt(signal.butter(2, [2000, 5000], "bandpass", fs=SR, output="sos"),
                            np.random.default_rng(3).standard_normal(n))
    breath /= np.sqrt(np.mean(breath ** 2)) + 1e-12
    y = y + 0.55 * chest + 0.08 * breath
    env = np.minimum(np.clip(tt / 0.04, 0, 1),
                     np.clip((dur + 0.12 - tt) / 0.18, 0, 1))
    y = signal.sosfilt(signal.butter(2, 4800, "low", fs=SR, output="sos"), y * env)
    return y / (np.max(np.abs(y)) + 1e-12)


def xfade_place(buf, x, i0, fade_n):
    """Add x into buf at i0 with a raised-cosine fade-in of fade_n samples."""
    x = x.copy()
    k = min(fade_n, len(x))
    x[:k] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(k) / k)
    end = min(len(buf), i0 + len(x))
    if end > i0:
        buf[i0:end] += x[: end - i0]


# ----------------------------------------------------- the three builders

def build_hook_tts_ola():
    """Variant A: pure TTS+OLA. Whole syllable pitch-shifted, then OLA
    onto the grid. Prosody drift survives inside the note."""
    n = int((16 * BEAT + 1.0) * SR)
    out = np.zeros(n)
    meas = []
    edge = 0.0
    for text, midi, beats in HOOK:
        f_t = midi_to_hz(midi)
        x = get_syllable(text, f_t)
        want = min(beats * BEAT * 0.92, 1.4)         # cap the stretch
        x = ola_stretch(x, want / (len(x) / SR))
        k = int(0.02 * SR)
        x[-k:] *= np.linspace(1, 0, k)
        xfade_place(out, x, int(edge * SR), int(0.008 * SR))
        meas.append((text, f_t, estimate_f0(x)))
        edge += beats * BEAT
    return out / (np.max(np.abs(out)) + 1e-12), meas


def build_hook_hybrid():
    """Variant B: TTS onset/coda grafted onto the pitch-perfect synth vowel."""
    n = int((16 * BEAT + 1.0) * SR)
    out = np.zeros(n)
    meas = []
    edge = 0.0
    XF = int(0.025 * SR)
    for text, midi, beats in HOOK:
        f_t = midi_to_hz(midi)
        p = SYL[text]
        dur = beats * BEAT * (0.92 if beats <= 1 else 0.97)
        tts = get_syllable(text, f_t)
        note = np.zeros(int((dur + 0.35) * SR))
        pos = 0
        if p["onset"] > 0:                            # consonant onset graft
            on = tts[: int(p["onset"] * SR)].copy()
            on[-XF:] *= np.linspace(1, 0, XF)
            note[: len(on)] += on
            pos = max(0, len(on) - XF)
        vow = vowel_note(f_t, dur - pos / SR, p["v1"], p["v2"])
        xfade_place(note, vow * 0.9, pos, XF)
        if p["coda"] > 0:                             # consonant coda graft
            co = tts[-int(p["coda"] * SR):].copy()
            co[:XF] *= np.linspace(0, 1, XF)
            co[-int(0.02 * SR):] *= np.linspace(1, 0, int(0.02 * SR))
            i0 = int(dur * SR) - len(co) // 3
            note[i0:i0 + len(co)] += co * 0.8 * np.max(np.abs(vow))
        vs = int((pos / SR + 0.10) * SR)
        ve = int(min(dur - 0.05, pos / SR + 0.40) * SR)
        meas.append((text, f_t, estimate_f0(note[vs:max(ve, vs + int(0.1 * SR))])))
        xfade_place(out, note, int(edge * SR), int(0.005 * SR))
        edge += beats * BEAT
    return out / (np.max(np.abs(out)) + 1e-12), meas


def build_hook_vowels():
    """Variant C (control): the vowel engine alone, no TTS."""
    n = int((16 * BEAT + 1.0) * SR)
    out = np.zeros(n)
    edge = 0.0
    for text, midi, beats in HOOK:
        p = SYL[text]
        dur = beats * BEAT * 0.95
        vow = vowel_note(midi_to_hz(midi), dur, p["v1"], p["v2"])
        xfade_place(out, vow, int(edge * SR), int(0.01 * SR))
        edge += beats * BEAT
    return out / (np.max(np.abs(out)) + 1e-12)


# ------------------------------------------------------------ bare pad bed

def make_reverb_ir(seconds, decay, seed):
    r = np.random.default_rng(seed)
    n = int(seconds * SR)
    ir = r.standard_normal(n) * np.exp(-np.arange(n) / SR / decay)
    ir = signal.sosfilt(signal.butter(2, 4000, "low", fs=SR, output="sos"), ir)
    return ir / np.sqrt(np.sum(ir ** 2))


def pad_chord(midis, dur):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    rng = np.random.default_rng(sum(midis))
    x = np.zeros(n)
    for m in midis:
        f = midi_to_hz(m)
        for det in (0.9993, 1.0007):
            ph = 2 * np.pi * f * det * tt + rng.uniform(0, 6)
            x += np.sin(ph) + 0.3 * np.sin(2 * ph)
    env = np.minimum(np.clip(tt / 0.8, 0, 1), np.clip((dur - tt) / 0.9, 0, 1))
    x = signal.sosfilt(signal.butter(2, 900, "low", fs=SR, output="sos"), x * env)
    return x / (np.max(np.abs(x)) + 1e-12)


CHORDS = [(45, 57, 60, 64), (41, 53, 57, 60), (48, 55, 60, 64), (43, 55, 59, 62)]

SEG = 6 * BAR                                # 4 hook bars + 2 gap bars
N = int(3 * SEG * SR + 2 * SR)
mix = np.zeros(N)
IR = make_reverb_ir(3.5, 1.6, 7)

for v in range(3):
    t0 = v * SEG
    for b in range(5):
        i0 = int((t0 + b * BAR) * SR)
        c = pad_chord(CHORDS[b % 4], BAR + 0.6)
        mix[i0:i0 + len(c)] += 0.22 * c[: max(0, N - i0)][: len(mix[i0:i0 + len(c)])]

print("building variant A (pure TTS+OLA) ...")
hookA, measA = build_hook_tts_ola()
print("building variant B (hybrid — TTS graft on synth vowel) ...")
hookB, measB = build_hook_hybrid()
print("building variant C (vowel engine control) ...")
hookC = build_hook_vowels()

for v, h in enumerate([hookA, hookB, hookC]):
    hv = h + 0.22 * signal.fftconvolve(h, IR)[: len(h)] / (np.max(np.abs(h)) + 1e-12)
    i0 = int(v * SEG * SR)
    mix[i0:i0 + len(hv)] += 0.85 * hv[: N - i0]

mix /= np.max(np.abs(mix)) + 1e-12
mix *= 0.85
k = int(1.5 * SR)
mix[-k:] *= np.linspace(1, 0, k)

OUT = "/workspace/music/unsung_probe.wav"
os.makedirs("/workspace/music", exist_ok=True)
pcm = (np.column_stack([mix, mix]) * 32767).astype(np.int16)
with wave.open(OUT, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print(f"\nCreated: {OUT}  ({N / SR:.1f} s)")
MP3 = OUT.replace(".wav", ".mp3")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", OUT,
                "-b:a", "192k", MP3], check=True)
print(f"Created: {MP3}")

print(f"\nLayout: 0.0 s variant A (TTS+OLA) | {SEG:.1f} s variant B (hybrid) | "
      f"{2 * SEG:.1f} s variant C (vowel control)")


def table(name, meas):
    print(f"\n{name} — per-note pitch (target vs measured):")
    errs = []
    for text, ft, fm in meas:
        cents = 1200 * np.log2(fm / ft) if fm > 0 else float("nan")
        errs.append(abs(cents))
        print(f"  {text:6s} target {ft:6.1f} Hz  measured {fm:6.1f} Hz  {cents:+6.0f} cents")
    print(f"  median |err| {np.median(errs):.0f} cents, max {np.max(errs):.0f} cents")


table("variant A (TTS+OLA)", measA)
table("variant B (hybrid)", measB)
