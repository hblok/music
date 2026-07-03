#!/usr/bin/env python3
"""
unsung.py — "Unsung" (~5:28, 132 BPM, A natural minor).
The first VOCAL song in the trance tracks (design notes:
ungesungen_notes.md; probe: unsung_probe.py — the hybrid treatment won,
median 3 cents pitch error). Era blueprint: Jam & Spoon-school Frankfurt
vocal trance, 1993/94 — real sung female vocal over the classic groove,
melancholic-warm, NOT 2000s uplifting (no supersaws, no sidechain).

THE STORY — the companion piece to Ungeschrieben. That track said the
future is unwritten; this one is the song that was always there and never
had a voice — the trance tracks themselves, instrumental by doctrine
until now, finally singing. The lyric is the whole story, mantra-like:

    "So long unsung — until tonight."

Four syllables rising to hang off-tonic on E (the question), four falling
home to A (the answer). The Q/A pair IS the lyric's grammar.

THE VOICE (the headline recipe) — the C7 hybrid: for each melody note the
edge-tts consonant onset (and coda) is grafted onto a synth vowel that
holds the target pitch perfectly — real intelligibility, synth control.
Our own vibrato (5.7 Hz, blooming), light sampler chain (6 kHz lowpass,
gentle tanh), near-dry. The script re-measures the f0 of every rendered
note and prints target vs measured in cents — the singing is verifiable
without listening.

THE FORM — song form (the proven lost/nachtkind shape), rule 6 fully
honored (the inversion of ungeschrieben's withheld thesis): the track
OPENS with the naked voice, a cappella over one pad swell, and the same
solo statement closes it. The duet is earned: in choruses 1–2 the voice
and the warm lead only TRADE (composed echoes entering as each vocal tail
ends — near-zero overlap, printed); at chorus 3 the lead's countermelody
finally sounds UNDER the sung refrain — the fusion.

  0:00  THESIS      the hook a cappella — one voice, near-dry, one dark
                    pad swelling under its tail.
  0:15  intro       kick, hats, then the rolling bass on the A pedal.
  0:44  verse 1     sparse and dark: low pluck questions, lead answers
                    fragments — trading, never overlapping.
  1:13  pre-chorus  the bass filter sweeps up, hats double, clap roll,
                    sung pickup across the barline →
  1:27  CHORUS 1    the drop: harmonic movement arrives (Am–F–C–G in the
                    bass at last), the hook SUNG 2x, lead echoing each tail.
  1:56  verse 2     groove holds (no teardown); the stab layer doubles.
  2:25  pre-chorus  as before, hotter →
  2:40  CHORUS 2    hook 2x; pads join; the echoes grow into a
                    half-countermelody (still only trading).
  3:09  bridge      teardown, harmony avoiding the tonic (F/G pads); the
                    SPOKEN thesis line alone over the pad (a fragment,
                    uncounted); rebuild; the composed silent beat with a
                    lone sung pickup hanging in it →
  3:53  CHORUS 3    the fusion: hook 3x with detuned double and octave
                    shimmer, the full countermelody UNDER the voice at
                    last. Loudest section.
  4:36  ride-out    peel in reverse: countermelody out, stabs thin,
                    claps out, the bass filters down.
  5:05  BOOKEND     kick stops; the hook a cappella once more over the
                    pad's last swell. Ring out.

THE KNOBS:
  VOICE_MODE = "sung"          the full vocal song (default)
             = "spoken"        no singing — the lead carries the refrain,
                               the voice contributes the spoken line only
             = "instrumental"  no voice at all; the lead carries the
                               refrain (the track must survive its singer)
  VOICE_GAIN = 1.0             scales all voice material; 0.0 is treated
                               as "instrumental"
Syllables are rendered once via edge-tts (en-US-AriaNeural) and cached to
/workspace/music/samples/unsung/ — cache-first, no network after the
first run. If TTS and cache are both unavailable the script degrades to
"instrumental" and says so.

BANNED: supersaws, sidechain pumping, reverse cymbals (nachtkind's), and
the other tracks' signatures (piano centerpiece, resonant sequence,
rompler strings, 13/16).

Everything else synthesized (numpy + scipy).
Output: /workspace/music/unsung.wav + unsung.mp3 (192k).
"""

import asyncio
import os
import subprocess
import wave
import numpy as np
from scipy import signal

SR = 44100
DURATION = 328.0
N = int(SR * DURATION)
t = np.arange(N) / SR

rng = np.random.default_rng(1994)     # the year the Frankfurt vocal broke

BPM = 132.0
BEAT = 60.0 / BPM
BAR = BEAT * 4
STEP = BEAT / 4
GRID0 = 0.5

# ------------------------------------------------------------- THE KNOBS
VOICE_MODE = "sung"                   # "sung" | "spoken" | "instrumental"
VOICE_GAIN = 1.0                      # 0.0 = fully instrumental
VOICE_ID = "en-US-AriaNeural"         # edge-tts neural voice (female)
CACHE_DIR = "/workspace/music/samples/unsung"

if VOICE_GAIN <= 0:
    VOICE_MODE = "instrumental"


def bar_t(b, beat=0.0):
    return GRID0 + b * BAR + beat * BEAT


# ----------------------------------------------------- section boundaries (bars)
B_INTRO = 8       # thesis is bars 0-8: the a cappella hook
B_V1 = 24         # verse 1: pluck questions, lead answer fragments
B_PRE1 = 40       # pre-chorus: the sweep
B_CH1 = 48        # CHORUS 1: the hook sung, lead tail-echoes
B_V2 = 64         # verse 2: groove holds, stabs double
B_PRE2 = 80
B_CH2 = 88        # CHORUS 2: + pads, half-countermelody
B_BR = 104        # bridge: teardown off the tonic; the spoken line
B_CH3 = 128       # CHORUS 3: the fusion (after the silent beat)
B_RIDE = 152      # ride-out: peel in reverse
B_BOOK = 168      # kick stops; the a cappella bookend
B_END = 180


def section_of(b):
    for name, b0 in [("book", B_BOOK), ("ride", B_RIDE), ("ch3", B_CH3),
                     ("bridge", B_BR), ("ch2", B_CH2), ("pre2", B_PRE2),
                     ("v2", B_V2), ("ch1", B_CH1), ("pre1", B_PRE1),
                     ("v1", B_V1), ("intro", B_INTRO)]:
        if b >= b0:
            return name
    return "thesis"


def silent_beat(b, beat):
    # THE composed silence: the last beat before the fusion, with only
    # the sung pickup hanging in it.
    return b == B_CH3 - 1 and beat >= 3.0


# ---------------------------------------------------------------- helpers

def midi_to_hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def fade(x, fade_in=0.3, fade_out=6.0):
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


def add_at(buf, x, start_s, gain=1.0):
    i0 = int(start_s * SR)
    end = min(len(buf), i0 + len(x))
    if end > i0:
        buf[i0:end] += x[: end - i0] * gain


def place_pan(layL, layR, clip, t0, gain, pan):
    add_at(layL, clip, t0, gain * np.cos(pan * np.pi / 2))
    add_at(layR, clip, t0, gain * np.sin(pan * np.pi / 2))


def glide_curve(notes, n, tau=0.05):
    f_target = np.zeros(n)
    edge = 0.0
    for m, d in notes:
        a, b = int(edge * SR), min(n, int((edge + d) * SR))
        f_target[a:b] = midi_to_hz(m)
        edge += d
    i_end = min(n - 1, int(edge * SR))
    f_target[i_end:] = f_target[i_end - 1]
    alpha = 1.0 - np.exp(-1.0 / (tau * SR))
    return signal.lfilter([alpha], [1.0, -(1.0 - alpha)],
                          f_target, zi=[f_target[0] * (1 - alpha)])[0]


IR_L = make_reverb_ir(4.5, 2.2, 7)
IR_R = make_reverb_ir(4.5, 2.2, 11)

mix_L = np.zeros(N)
mix_R = np.zeros(N)


def commit(layer_L, layer_R, weight, env=None):
    global mix_L, mix_R
    peak = max(np.max(np.abs(layer_L)), np.max(np.abs(layer_R)), 1e-12)
    s = weight / peak
    if env is None:
        mix_L += layer_L * s
        mix_R += layer_R * s
    else:
        mix_L += layer_L * env * s
        mix_R += layer_R * env * s


lay_L = np.zeros(N)
lay_R = np.zeros(N)


def clear():
    lay_L[:] = 0.0
    lay_R[:] = 0.0


# ------------------------------------------------------------- material
# A natural minor. One progression family everywhere: i-VI-III-VII =
# Am-F-C-G, one chord per bar, the 4-bar loop the hook was written over.
# Verses sit on the A pedal (hypnotic); the harmonic movement arrives with
# the choruses — the drop is where the loop starts turning.

ROOTS = [45, 41, 48, 43]                       # A2 F2 C3 G2
CHORDS = [(45, 57, 60, 64), (41, 53, 57, 60),  # Am  F
          (48, 55, 60, 64), (43, 55, 59, 62)]  # C   G
STABS_V = [(57, 60, 64), (53, 57, 60), (55, 60, 64), (55, 59, 62)]

# THE HOOK — "So long unsung — until tonight." (syllable, midi, beats);
# 16 beats = 4 bars, aligned to the Am-F-C-G loop. Q rises to hang on E4
# over F (off-tonic); A falls home to A3. "sung" and "night" land across
# barlines — this track's own seam device. Identical every statement.
HOOK = [("so", 57, 1.0), ("long", 60, 1.0), ("un", 62, 1.0), ("sung", 64, 5.0),
        ("un", 64, 1.0), ("til", 62, 1.0), ("to", 60, 1.0), ("night", 57, 3.0)]
HOOK_BEATS = 16.0
LYRIC = "So long unsung. Until tonight."      # the spoken bridge line

# Per-syllable graft plan (onset/coda seconds of TTS consonant; vowel
# formants, female range; "night" is a diphthong a->i morphed over the note).
SYL = {
    "so":    dict(onset=0.12, coda=0.00, v1=(450, 900),  v2=None),
    "long":  dict(onset=0.10, coda=0.12, v1=(600, 950),  v2=None),
    "un":    dict(onset=0.00, coda=0.10, v1=(650, 1250), v2=None),
    "sung":  dict(onset=0.10, coda=0.14, v1=(650, 1250), v2=None),
    "til":   dict(onset=0.10, coda=0.10, v1=(420, 2100), v2=None),
    "to":    dict(onset=0.10, coda=0.00, v1=(380, 850),  v2=None),
    "night": dict(onset=0.10, coda=0.10, v1=(750, 1350), v2=(350, 2300)),
}

# THE COUNTERMELODY — the lead's material, grown across the choruses.
# Chorus 1: the tail echo only. Chorus 2: the first half. Chorus 3: the
# full 8-bar line UNDER the voice. Octave-up register (A4-G5) so the two
# never fight for the same band. Mostly chord tones, moving where the
# hook holds and holding where it moves.
ECHO_TAIL = [(76, 1), (74, 1), (72, 1), (69, 3)]         # "until tonight," echoed
CM = [(76, 3), (74, 1), (72, 2), (74, 2), (76, 2), (79, 2), (74, 3), (71, 1),
      (72, 3), (74, 1), (77, 2), (76, 2), (76, 2), (72, 2), (74, 2), (71, 2)]
CM_HALF = CM[:8]                                          # bars 1-4

# Verse questions (low, dark — the pluck) and the lead's fragment answers.
# The answer lands on C (III), not home: verses ask, choruses answer.
VQ1 = [(45, 1.5), (48, 1.0), (50, 1.5)]                   # hangs on D
VQ2 = [(45, 1.5), (48, 1.0), (52, 1.5)]                   # hangs on E
VA = [(64, 1), (62, 1), (60, 2)]

HOOK_STMTS = []                     # bars of full hook statements (verified)
VOICE_SPANS = []                    # (t0, t1) of refrain activity
COUNTER_SPANS = []                  # (t0, t1) of echo/countermelody activity


# ----------------------------------------------------- the vocal engine
# The hybrid recipe, proven by unsung_probe.py: TTS consonant onset/coda
# grafted onto a synth vowel holding the target pitch (median 3 cents).

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
    Two base renders (+0 / +60 Hz) keep the resample ratio small, so the
    formant shift stays inaudible."""
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
    x = x.copy()
    k = min(fade_n, len(x))
    x[:k] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(k) / k)
    end = min(len(buf), i0 + len(x))
    if end > i0:
        buf[i0:end] += x[: end - i0]


XF = int(0.025 * SR)


def hybrid_note(text, midi, beats):
    """One sung note: TTS onset/coda grafted onto the pitch-held vowel.
    Returns (audio, measured_f0_of_the_held_vowel)."""
    f_t = midi_to_hz(midi)
    p = SYL[text]
    dur = beats * BEAT * (0.92 if beats <= 1 else 0.97)
    tts = get_syllable(text, f_t)
    note = np.zeros(int((dur + 0.35) * SR))
    pos = 0
    if p["onset"] > 0:
        on = tts[: int(p["onset"] * SR)].copy()
        on[-XF:] *= np.linspace(1, 0, XF)
        note[: len(on)] += on
        pos = max(0, len(on) - XF)
    vow = vowel_note(f_t, dur - pos / SR, p["v1"], p["v2"])
    xfade_place(note, vow * 0.9, pos, XF)
    if p["coda"] > 0:
        co = tts[-int(p["coda"] * SR):].copy()
        co[:XF] *= np.linspace(0, 1, XF)
        k2 = int(0.02 * SR)
        co[-k2:] *= np.linspace(1, 0, k2)
        i0 = int(dur * SR) - len(co) // 3
        note[i0:i0 + len(co)] += co * 0.8 * np.max(np.abs(vow))
    vs = int((pos / SR + 0.10) * SR)
    ve = int(min(dur - 0.05, pos / SR + 0.40) * SR)
    f_m = estimate_f0(note[vs:max(ve, vs + int(0.1 * SR))])
    return note, f_m


def build_hook():
    """The canonical sung hook (mono) + per-note pitch measurements.
    Built once — the refrain is IDENTICAL at every statement."""
    n = int((HOOK_BEATS * BEAT + 1.2) * SR)
    out = np.zeros(n)
    meas = []
    edge = 0.0
    for text, midi, beats in HOOK:
        note, f_m = hybrid_note(text, midi, beats)
        xfade_place(out, note, int(edge * SR), int(0.005 * SR))
        meas.append((text, midi_to_hz(midi), f_m))
        edge += beats * BEAT
    # the light sampler chain: gentle tanh, 6 kHz lowpass, rumble cut
    out = np.tanh(0.9 * out / (np.max(np.abs(out)) + 1e-12))
    out = signal.sosfilt(signal.butter(2, 6000, "low", fs=SR, output="sos"), out)
    out = signal.sosfilt(signal.butter(2, 120, "high", fs=SR, output="sos"), out)
    return out / (np.max(np.abs(out)) + 1e-12), meas


def detune(x, r):
    idx = np.arange(0, len(x) - 1, r)
    return x[idx.astype(int)]


def get_spoken():
    """The full lyric spoken (the bridge fragment) — ungeschrieben's
    sampler treatment: pitch-down resample, 6 kHz lowpass."""
    path = os.path.join(CACHE_DIR, "spoken_line.wav")
    if not os.path.exists(path):
        import edge_tts
        os.makedirs(CACHE_DIR, exist_ok=True)
        tmp = path + ".mp3"

        async def go():
            await edge_tts.Communicate(LYRIC, voice=VOICE_ID).save(tmp)

        asyncio.run(go())
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp,
                        "-ar", str(SR), "-ac", "1", path], check=True)
        os.remove(tmp)
    with wave.open(path, "rb") as w:
        v = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(float)
    v /= np.max(np.abs(v)) + 1e-12
    idx = np.arange(0, len(v) - 1, 0.94)
    v = v[idx.astype(int)]
    v = signal.sosfilt(signal.butter(2, 6000, "low", fs=SR, output="sos"), v)
    v = signal.sosfilt(signal.butter(2, 120, "high", fs=SR, output="sos"), v)
    return v / (np.max(np.abs(v)) + 1e-12)


# Resolve the voice up front (the lead layer depends on the mode).
PITCH_MEAS = None
HOOK_V = PICKUP = SPOKEN = None
if VOICE_MODE in ("sung", "spoken"):
    try:
        if VOICE_MODE == "sung":
            HOOK_V, PITCH_MEAS = build_hook()
            PICKUP, _ = hybrid_note("so", 57, 0.9)   # the seam-device syllable
        SPOKEN = get_spoken()
    except Exception as e:                           # no net, no cache
        VOICE_MODE = "instrumental"
        print(f"voice unavailable ({type(e).__name__}) — degrading to instrumental")
print(f"VOICE_MODE={VOICE_MODE}  VOICE_GAIN={VOICE_GAIN}")


# ---------------------------------------------------------------- drums
# 909 school (the lost_v6/nachtkind kit recipes — punchy, not sub-heavy).

def make_kick():
    n = int(0.26 * SR)
    td = np.arange(n) / SR
    f_curve = 48.0 + 102.0 * np.exp(-td * 50.0)
    body = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    sos_c = signal.butter(2, [1500, 6000], "bandpass", fs=SR, output="sos")
    click = signal.sosfilt(sos_c, rng.standard_normal(n)) * np.exp(-td * 500)
    click /= np.max(np.abs(click)) + 1e-12
    env = (1 - np.exp(-td / 0.001)) * np.exp(-td * 10.0)
    x = (body + 0.30 * click) * env
    return x / (np.max(np.abs(x)) + 1e-12)


def make_hat(open_=False):
    n = int((0.12 if open_ else 0.045) * SR)
    td = np.arange(n) / SR
    sos_h = signal.butter(4, 7000, "high", fs=SR, output="sos")
    x = signal.sosfilt(sos_h, rng.standard_normal(n))
    x *= np.exp(-td * (28 if open_ else 110))
    return x / (np.max(np.abs(x)) + 1e-12)


def make_clap():
    n = int(0.30 * SR)
    td = np.arange(n) / SR
    sos_c = signal.butter(2, [900, 4500], "bandpass", fs=SR, output="sos")
    x = np.zeros(n)
    for i, dmp in [(0, 120.0), (1, 120.0), (2, 120.0), (3, 26.0)]:
        i0 = int(i * 0.011 * SR)
        seg = signal.sosfilt(sos_c, rng.standard_normal(n - i0))
        x[i0:] += seg * np.exp(-td[: n - i0] * dmp)
    return x / (np.max(np.abs(x)) + 1e-12)


def make_crash():
    n = int(2.0 * SR)
    td = np.arange(n) / SR
    sos_c = signal.butter(2, 5000, "high", fs=SR, output="sos")
    x = signal.sosfilt(sos_c, rng.standard_normal(n)) * np.exp(-td * 2.2)
    x *= 1 - np.exp(-td / 0.002)
    return x / (np.max(np.abs(x)) + 1e-12)


KICK = make_kick()
CHAT = make_hat()
OHAT = make_hat(open_=True)
CLAP = make_clap()
CRASH = make_crash()


def kick_gain(b):
    if b >= B_BOOK:
        return 0.0
    if B_BR + 8 <= b < B_BR + 12:
        return 0.0                                   # the bridge floor
    if B_BR + 12 <= b < B_BR + 16:
        return 0.7                                   # the kick walks back in
    s = section_of(b)
    return {"intro": 0.9, "v1": 0.95, "pre1": 1.0, "ch1": 1.0, "v2": 0.95,
            "pre2": 1.0, "ch2": 1.0, "bridge": 0.85, "ch3": 1.0,
            "ride": 0.95}.get(s, 0.0)


clear()
for b in range(B_END):
    g = kick_gain(b)
    if g <= 0:
        continue
    if B_BR <= b < B_BR + 8:
        g *= 1.0 - 0.06 * (b - B_BR)                 # teardown fade
    for beat in range(4):
        if silent_beat(b, beat):
            continue
        add_at(lay_L, KICK, bar_t(b, beat), g)
        add_at(lay_R, KICK, bar_t(b, beat), g)
commit(lay_L, lay_R, 0.33)
print("kick committed")

# closed 16th hats (skipping the open slot) + offbeat open hat
clear()
CH_GAINS = [0.50, 0.25, 0.0, 0.30]
for b in range(B_BOOK):
    if b < 10 or (B_BR + 6 <= b < B_BR + 16):
        continue
    s = section_of(b)
    g = {"intro": 0.7, "bridge": 0.6}.get(s, 1.0)
    if s in ("pre1", "pre2"):
        g = 1.1                                      # hats double under the sweep
    for beat in range(4):
        for sx in range(4):
            if CH_GAINS[sx] == 0.0 or silent_beat(b, beat + sx * 0.25):
                continue
            add_at(lay_L, CHAT, bar_t(b, beat + sx * 0.25), g * CH_GAINS[sx] * 0.9)
            add_at(lay_R, CHAT, bar_t(b, beat + sx * 0.25), g * CH_GAINS[sx])
        if 12 <= b and s not in ("bridge",) and b < B_RIDE + 8:
            if silent_beat(b, beat + 0.5):
                continue
            add_at(lay_L, OHAT, bar_t(b, beat + 0.5), g)
            add_at(lay_R, OHAT, bar_t(b, beat + 0.5), g * 0.85)
commit(lay_L, lay_R, 0.08)
print("hats committed")

# claps on 2 & 4, plus the roll fills into the choruses
clear()
for b in range(B_END):
    if not (16 <= b < B_BR or B_CH3 <= b < B_RIDE + 4):
        continue
    for beat in (1, 3):
        if silent_beat(b, beat):
            continue
        p = 0.42 if beat == 1 else 0.58
        place_pan(lay_L, lay_R, CLAP, bar_t(b, beat), 1.0, p)


def clap_roll(b, last_beat=4.0):
    i = 0
    while i * 0.5 < last_beat:
        g = 0.35 + 0.65 * (i * 0.5) / 4.0
        place_pan(lay_L, lay_R, CLAP, bar_t(b, i * 0.5), g, 0.5)
        i += 1


clap_roll(B_CH1 - 1)
clap_roll(B_CH2 - 1)
clap_roll(B_CH3 - 1, last_beat=3.0)                  # the roll INTO the silence
commit(lay_L, lay_R, 0.10)
print("claps committed")

# crashes mark the section changes (NO reverse cymbals)
clear()
for b, g in [(B_INTRO, 0.4), (B_CH1, 1.0), (B_V2, 0.4), (B_CH2, 1.0),
             (B_BR, 0.5), (B_CH3, 1.0), (B_RIDE, 0.6), (B_BOOK, 0.5)]:
    place_pan(lay_L, lay_R, CRASH, bar_t(b), g, 0.5)
commit(lay_L, lay_R, 0.05)
print("crashes committed")


# ---------------------------------------------------------------- bass
# Rolling 16th mono bass, warmed recipe. Verses: the hypnotic A pedal.
# Pre-choruses and choruses: the roots start MOVING (Am-F-C-G) — the
# harmonic movement arrives with the drop. The pre-chorus rise is the
# bass filter sweeping up (the era's riser).

bass_cache = {}


def bass_note(midi, cutoff, dur=STEP * 0.92):
    key = (midi, int(cutoff // 60))
    if key in bass_cache:
        return bass_cache[key]
    f = midi_to_hz(midi)
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    for k in range(1, min(24, int(3000 / f)) + 1):
        x += np.sin(2 * np.pi * k * f * td) / k ** 1.3
    y = signal.sosfilt(signal.butter(2, cutoff, "low", fs=SR, output="sos"), x)
    bpk, apk = signal.iirpeak(cutoff, Q=1.2, fs=SR)
    y = y + 0.3 * signal.lfilter(bpk, apk, y)
    y += 0.4 * np.sin(2 * np.pi * (f / 2) * td)
    y = np.tanh(0.9 * y)
    y *= (1 - np.exp(-td / 0.004)) * np.clip((dur - td) / 0.02, 0, 1)
    bass_cache[key] = y / (np.max(np.abs(y)) + 1e-12)
    return bass_cache[key]


def bass_root(b):
    s = section_of(b)
    if s in ("pre1", "ch1", "pre2", "ch2", "ch3", "ride"):
        return ROOTS[b % 4]                          # loop-aligned everywhere
    if s == "bridge":
        if b < B_BR + 8:
            return ROOTS[b % 4]
        if b < B_BR + 16:
            return 41                                # off the tonic: F
        return 41 if b < B_BR + 20 else 43           # F -> G, the walk home
    return 45                                        # the A pedal


def bass_cut(b):
    s = section_of(b)
    if s in ("pre1", "pre2"):                        # the sweep, per bar
        b0 = B_PRE1 if s == "pre1" else B_PRE2
        return 420 + (720 - 420) * (b - b0) / 8.0
    if s == "bridge":
        return 260
    if s == "ride":
        return 480 - (480 - 300) * (b - B_RIDE) / 16.0
    return {"intro": 360, "v1": 400, "ch1": 560, "v2": 430,
            "ch2": 580, "ch3": 620}.get(s, 360)


clear()
for b in range(16, B_BOOK):
    if B_BR + 8 <= b < B_BR + 14:
        continue                                     # the bridge floor
    root = bass_root(b)
    cut = bass_cut(b)
    for step in range(16):
        if silent_beat(b, step * 0.25):
            continue
        midi = root + (12 if step in (6, 14) else 0)
        g = 0.85 if step % 2 == 0 else 0.72
        if step in (6, 14):
            g = 0.9
        x = bass_note(midi, cut)
        add_at(lay_L, x, bar_t(b, step * 0.25), g)
        add_at(lay_R, x, bar_t(b, step * 0.25), g)
commit(lay_L, lay_R, 0.28)
print(f"bass committed ({len(bass_cache)} cached)")


# ---------------------------------------------------------------- stabs
# The dark gated offbeat chord stab (nachtkind recipe, re-voiced to the
# Am-F-C-G loop) — the 16-bar development engine inside the verses:
# verse 1 sparse, verse 2 doubled, full in the choruses.

def make_stab(midis):
    dur = STEP * 1.6
    n = int(dur * SR)
    td = np.arange(n) / SR
    x = np.zeros(n)
    for m in midis:
        f = midi_to_hz(m)
        for k in range(1, min(12, int(2500 / f)) + 1):
            x += np.sin(2 * np.pi * k * f * td + rng.uniform(0, 2 * np.pi)) / k
    sos_s = signal.butter(2, 900, "low", fs=SR, output="sos")
    x = signal.sosfilt(sos_s, x)
    x *= (1 - np.exp(-td / 0.002)) * np.clip((dur - td) / 0.05, 0, 1)
    return x / (np.max(np.abs(x)) + 1e-12)


STAB = [make_stab(v) for v in STABS_V]

clear()
for b in range(B_END):
    s = section_of(b)
    if s in ("v1", "pre1"):
        beats, g = (1.5, 3.5), 0.7                   # sparse: two per bar
    elif s in ("v2", "pre2"):
        beats, g = (0.5, 1.5, 2.5, 3.5), 0.85        # doubled
    elif s in ("ch1", "ch2", "ch3"):
        beats, g = (0.5, 1.5, 2.5, 3.5), 1.0
    elif s == "ride" and b < B_RIDE + 8:
        beats, g = (1.5, 3.5), 0.6                   # thinning out
    else:
        continue
    st = STAB[b % 4]
    for beat in beats:
        if silent_beat(b, beat):
            continue
        p = 0.35 if beat < 2 else 0.65
        place_pan(lay_L, lay_R, st, bar_t(b, beat), g, p)
lay_L = reverb(lay_L, IR_L, wet=0.30)
lay_R = reverb(lay_R, IR_R, wet=0.30)
commit(lay_L, lay_R, 0.10)
print("stabs committed")


# ---------------------------------------------------------------- leads
# The warm detuned analog lead (full warmth recipe) — the voice's duet
# partner. And the dark low pluck that asks the verse questions.

def lead_phrase(notes, cutoff=2600):
    total = sum(d for _, d in notes) * BEAT
    n = int((total + 2.5) * SR)
    tt = np.arange(n) / SR
    f_curve = glide_curve([(m, d * BEAT) for m, d in notes], n, tau=0.06)
    vib = 1.0 + 0.003 * np.sin(2 * np.pi * 5.0 * tt) * np.clip(tt / 1.8, 0, 1)
    K = max(3, int(7000 / np.max(f_curve)))

    def reed(det):
        ph = 2 * np.pi * np.cumsum(f_curve * det * vib) / SR
        v = np.zeros(n)
        for k in range(1, K + 1):
            v += np.sin(k * ph) / k ** 1.3
        return v

    base = reed(1.0)
    body = np.sin(2 * np.pi * np.cumsum(f_curve * vib) / SR)
    vL = base + reed(0.9965) + 0.30 * body
    vR = base + reed(1.0038) + 0.30 * body
    env = np.minimum(np.clip(tt / 0.35, 0, 1),
                     np.clip((total + 0.6 - tt) / 1.4, 0, 1))
    sos_w = signal.butter(2, cutoff, "low", fs=SR, output="sos")
    vL = np.tanh(0.8 * signal.sosfilt(sos_w, vL * env))
    vR = np.tanh(0.8 * signal.sosfilt(sos_w, vR * env))
    peak = max(np.max(np.abs(vL)), np.max(np.abs(vR)), 1e-12)
    return vL / peak, vR / peak


DELAY = 0.75 * BEAT                                  # dotted 8th


def place_lead(LR, t0, gain, notes=None, counter=True):
    L, R = LR
    add_at(lay_L, L, t0, gain)
    add_at(lay_R, R, t0, gain)
    add_at(lay_L, R, t0 + DELAY, gain * 0.28)        # ping-pong echoes
    add_at(lay_R, L, t0 + DELAY, gain * 0.28)
    add_at(lay_L, L, t0 + 2 * DELAY, gain * 0.13)
    add_at(lay_R, R, t0 + 2 * DELAY, gain * 0.13)
    if notes is not None and counter:
        COUNTER_SPANS.append((t0, t0 + sum(d for _, d in notes) * BEAT))


# verse questions (own quiet layer — dark, low, filtered down)
clear()
for b0, vq in [(B_V1, VQ1), (B_V1 + 8, VQ1), (B_V2, VQ2), (B_V2 + 8, VQ2)]:
    L, R = lead_phrase(vq, cutoff=900)
    add_at(lay_L, L, bar_t(b0), 1.0)
    add_at(lay_R, R, bar_t(b0), 1.0)
lay_L = reverb(lay_L, IR_L, wet=0.35)
lay_R = reverb(lay_R, IR_R, wet=0.35)
commit(lay_L, lay_R, 0.12)
print("verse questions committed")

# the answer lead: verse fragments; chorus echoes growing into the
# countermelody; in instrumental/spoken mode it also carries the refrain
clear()
LEAD_VA = lead_phrase(VA)
LEAD_ECHO = lead_phrase(ECHO_TAIL)
LEAD_CMH = lead_phrase(CM_HALF)
LEAD_CM = lead_phrase(CM)
LEAD_HOOK = lead_phrase([(m + 12, d) for _, m, d in HOOK])   # shimmer / carrier

# verse answer fragments — trading with the questions
for b0 in (B_V1 + 4, B_V1 + 12, B_V2 + 4, B_V2 + 12):
    place_lead(LEAD_VA, bar_t(b0), 0.6, notes=VA, counter=False)

# chorus 1: the tail echo, entering as each vocal statement ends
for b0 in (B_CH1 + 4, B_CH1 + 12):
    place_lead(LEAD_ECHO, bar_t(b0), 0.8, notes=ECHO_TAIL)
# chorus 2: the half-countermelody — still only trading
for b0 in (B_CH2 + 4, B_CH2 + 12):
    place_lead(LEAD_CMH, bar_t(b0), 0.85, notes=CM_HALF)
# chorus 3: THE FUSION — the full countermelody under every statement
for b0 in (B_CH3, B_CH3 + 8, B_CH3 + 16):
    place_lead(LEAD_CM, bar_t(b0), 0.9, notes=CM)

if VOICE_MODE == "sung":
    # the octave shimmer doubling the sung refrain in the fusion
    for b0 in (B_CH3, B_CH3 + 8, B_CH3 + 16):
        place_lead(LEAD_HOOK, bar_t(b0), 0.30, counter=False)
else:
    # the lead carries the refrain — the track survives its singer
    def hook_stmt_lead(b0, gain=1.0):
        place_lead(LEAD_HOOK, bar_t(b0), gain, counter=False)
        VOICE_SPANS.append((bar_t(b0), bar_t(b0) + HOOK_BEATS * BEAT))
        HOOK_STMTS.append(b0)

    hook_stmt_lead(0, 0.9)
    for b0 in (B_CH1, B_CH1 + 8, B_CH2, B_CH2 + 8,
               B_CH3, B_CH3 + 8, B_CH3 + 16):
        hook_stmt_lead(b0)
    hook_stmt_lead(B_BOOK + 2, 0.8)

lay_L = reverb(lay_L, IR_L, wet=0.45)
lay_R = reverb(lay_R, IR_R, wet=0.45)
commit(lay_L, lay_R, 0.22)
print("lead committed")


# ---------------------------------------------------------------- pads
# The dark sine pad: the thesis/bookend swell, the chorus warmth (from
# chorus 2 — development), and the bridge bed AVOIDING THE TONIC (F/G).

def pad_chord(chord, dur, attack=2.0, release=2.5):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    L = np.zeros(n)
    R = np.zeros(n)
    for m in chord:
        f = midi_to_hz(m)
        amp = 0.8 + 0.2 * np.sin(2 * np.pi * rng.uniform(0.02, 0.06) * tt +
                                 rng.uniform(0, 6))
        for det, gL, gR in [(0.9993, 1.0, 0.65), (1.0007, 0.65, 1.0)]:
            ph = 2 * np.pi * f * det * tt + rng.uniform(0, 6)
            v = (np.sin(ph) + 0.30 * np.sin(2 * ph)) * amp
            L += gL * v
            R += gR * v
    env = np.minimum(np.clip(tt / attack, 0, 1) ** 1.5,
                     np.clip((dur - tt) / release, 0, 1))
    sos = signal.butter(2, 750, "low", fs=SR, output="sos")
    L = signal.sosfilt(sos, L * env)
    R = signal.sosfilt(sos, R * env)
    peak = max(np.max(np.abs(L)), np.max(np.abs(R)), 1e-12)
    return L / peak, R / peak


clear()
# the thesis swell, under the a cappella tail
pL, pR = pad_chord(CHORDS[0], 6 * BAR, attack=3.0, release=3.0)
add_at(lay_L, pL, bar_t(1.5), 0.9)
add_at(lay_R, pR, bar_t(1.5), 0.9)
# choruses 2-3: per-bar loop pads (development: chorus 1 has none)
for b in range(B_CH2, B_BR):
    pL, pR = pad_chord(CHORDS[b % 4], BAR + 0.8, attack=0.5, release=1.0)
    add_at(lay_L, pL, bar_t(b), 0.5)
    add_at(lay_R, pR, bar_t(b), 0.5)
for b in range(B_CH3, B_RIDE):
    pL, pR = pad_chord(CHORDS[b % 4], BAR + 0.8, attack=0.5, release=1.0)
    add_at(lay_L, pL, bar_t(b), 0.55)
    add_at(lay_R, pR, bar_t(b), 0.55)
# the bridge bed, off the tonic: F and G only — resolution waits for ch3
for b in range(B_BR, B_CH3 - 1, 2):
    ch = CHORDS[1] if (b - B_BR) % 4 < 2 else CHORDS[3]
    pL, pR = pad_chord(ch, 2 * BAR + 1.5)
    add_at(lay_L, pL, bar_t(b), 0.95)
    add_at(lay_R, pR, bar_t(b), 0.95)
# ride-out and the bookend's last swell
for b in range(B_RIDE + 4, B_BOOK, 2):
    pL, pR = pad_chord(CHORDS[b % 4], 2 * BAR + 1.5)
    add_at(lay_L, pL, bar_t(b), 0.6)
    add_at(lay_R, pR, bar_t(b), 0.6)
pL, pR = pad_chord(CHORDS[0], 8 * BAR, attack=3.5, release=5.0)
add_at(lay_L, pL, bar_t(B_BOOK), 0.85)
add_at(lay_R, pR, bar_t(B_BOOK), 0.85)
lay_L = reverb(lay_L, IR_L, wet=0.5)
lay_R = reverb(lay_R, IR_R, wet=0.5)
commit(lay_L, lay_R, 0.13)
print("pads committed")


# ---------------------------------------------------------------- voice
# The sung refrain — identical audio every statement (the doctrine made
# literal). Near-dry (wet 0.18), center; the choruses add a detuned
# double (+-0.3 %) for width; the fusion adds both plus the shimmer.

def place_hook_sung(b0, double=False, gain=1.0):
    t0 = bar_t(b0)
    add_at(lay_L, HOOK_V, t0, gain)
    add_at(lay_R, HOOK_V, t0, gain)
    if double:
        for r, pan in [(0.997, 0.38), (1.003, 0.62)]:
            d = detune(HOOK_V, r)
            add_at(lay_L, d, t0, 0.30 * gain * np.cos(pan * np.pi / 2))
            add_at(lay_R, d, t0, 0.30 * gain * np.sin(pan * np.pi / 2))
    VOICE_SPANS.append((t0, t0 + HOOK_BEATS * BEAT))
    HOOK_STMTS.append(b0)


if VOICE_MODE == "sung":
    clear()
    place_hook_sung(0)                               # THE THESIS
    for b0 in (B_CH1, B_CH1 + 8, B_CH2, B_CH2 + 8):
        place_hook_sung(b0, double=True)
    for b0 in (B_CH3, B_CH3 + 8, B_CH3 + 16):        # the fusion
        place_hook_sung(b0, double=True)
    place_hook_sung(B_BOOK + 2, gain=0.9)            # THE BOOKEND
    # the pickup syllable across the seams — and hanging in the silence
    for b, beat in [(B_CH1 - 1, 3.0), (B_CH2 - 1, 3.0), (B_CH3 - 1, 3.2)]:
        add_at(lay_L, PICKUP, bar_t(b, beat), 0.8)
        add_at(lay_R, PICKUP, bar_t(b, beat), 0.8)
    lay_L = reverb(lay_L, IR_L, wet=0.18)
    lay_R = reverb(lay_R, IR_R, wet=0.18)
    commit(lay_L, lay_R, 0.30 * VOICE_GAIN)
    print("voice committed (sung)")

if VOICE_MODE in ("sung", "spoken") and SPOKEN is not None:
    # the bridge: the thesis line SPOKEN, alone over the off-tonic pad —
    # the oldest question asked plainly (a fragment, uncounted)
    clear()
    t0 = bar_t(B_BR + 9)
    add_at(lay_L, SPOKEN, t0, 1.0)
    add_at(lay_R, SPOKEN, t0, 1.0)
    for i, g in [(1, 0.30), (2, 0.14)]:              # tempo-synced delay tail
        add_at(lay_L, SPOKEN, t0 + i * DELAY, g if i % 2 else g * 0.6)
        add_at(lay_R, SPOKEN, t0 + i * DELAY, g * 0.6 if i % 2 else g)
    commit(lay_L, lay_R, 0.32 * VOICE_GAIN)   # a sample drop sits ON TOP
    print("spoken line committed (bridge)")


# ------------------------------------------------------------------ air

sos_air = signal.butter(4, [150, 1100], "bandpass", fs=SR, output="sos")
air = signal.sosfilt(sos_air, rng.standard_normal(N))
air /= np.max(np.abs(air))
air_env = slow_noise(0.05, 0.4, 1.0)
edge = np.minimum(np.clip((bar_t(B_V1) - t) / 12.0, 0, 1) +
                  np.clip((t - bar_t(B_RIDE)) / 20.0, 0, 1), 1.0)
commit(air * air_env * edge, air * air_env[::-1] * edge, 0.04)
print("air committed")


# ---------------------------------------------------------------- master
# Era master: peak-normalized with headroom. No loudness compression.

fade(mix_L, fade_in=0.3, fade_out=6.0)
fade(mix_R, fade_in=0.3, fade_out=6.0)

peak = max(np.max(np.abs(mix_L)), np.max(np.abs(mix_R)))
mix_L = mix_L / peak * 0.87
mix_R = mix_R / peak * 0.87

stereo = np.empty((N, 2))
stereo[:, 0] = mix_L
stereo[:, 1] = mix_R
pcm = (stereo * 32767.0).astype(np.int16)

OUT_DIR = "/workspace/music"
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, "unsung.wav")
with wave.open(OUT, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())

print(f"\nCreated: {os.path.abspath(OUT)}")
print(f"Duration: {N / SR:.1f} s  |  {SR} Hz stereo, 16-bit PCM  |  "
      f"{BPM:.0f} BPM, A natural minor (Am-F-C-G)")

MP3 = os.path.join(OUT_DIR, "unsung.mp3")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", OUT,
                "-vn", "-ar", "44100", "-ac", "2", "-b:a", "192k", MP3],
               check=True)
print(f"Created: {os.path.abspath(MP3)}  (192k mp3)")

# ---------------------------------------------------------------- verify form
# Song-form set (../VERIFY.md) + this track's own vocal checks.

print("\nSection map:")
SECTIONS = [("THESIS (a cappella)", 0), ("intro groove", B_INTRO),
            ("verse 1", B_V1), ("pre-chorus 1", B_PRE1), ("CHORUS 1", B_CH1),
            ("verse 2", B_V2), ("pre-chorus 2", B_PRE2), ("CHORUS 2", B_CH2),
            ("bridge", B_BR), ("CHORUS 3 (the fusion)", B_CH3),
            ("ride-out", B_RIDE), ("BOOKEND", B_BOOK)]
for name, b in SECTIONS:
    print(f"  {bar_t(b):6.1f} s  bar {b:3d}  {name}")
print(f"  {bar_t(B_BOOK):6.1f} s  bar {B_BOOK}  kick stops")
print(f"  {DURATION:6.1f} s  end")

carrier = "sung" if VOICE_MODE == "sung" else "lead-carried"
print(f"\nHook statements ({carrier}): {len(HOOK_STMTS)} at bars {HOOK_STMTS} "
      f"(target >= 9; the bridge's spoken line is a fragment, uncounted)")

if PITCH_MEAS is not None:
    print("\nVocal pitch (the rendered refrain, target vs measured):")
    errs = []
    for text, ft, fm in PITCH_MEAS:
        cents = 1200 * np.log2(fm / ft) if fm > 0 else float("nan")
        errs.append(abs(cents))
        print(f"  {text:6s} target {ft:6.1f} Hz  measured {fm:6.1f} Hz  {cents:+5.0f} cents")
    med_err, max_err = np.median(errs), np.max(errs)
    print(f"  median |err| {med_err:.0f} cents, max {max_err:.0f} cents")

print("\nSeam checklist (what crosses every boundary):")
for b, dev in [(B_INTRO, "the hook's last note + hall tail ring over the first kicks"),
               (B_V1, "unbroken groove; the stab layer enters on the downbeat"),
               (B_PRE1, "the bass filter sweep begins; hats double"),
               (B_CH1, "clap roll + crash; the sung pickup crosses the barline"),
               (B_V2, "groove holds — no teardown; the echo's delay tail rings across"),
               (B_PRE2, "the sweep again, hotter"),
               (B_CH2, "clap roll + crash; the sung pickup crosses the barline"),
               (B_BR, "chorus 2's last vocal tail + crash ring into the teardown"),
               (B_CH3, "THE COMPOSED SILENT BEAT, one sung pickup hanging in it; crash"),
               (B_RIDE, "crash; the countermelody's last note + pads ring across"),
               (B_BOOK, "kick stops mid-ring; the pad swells under the final a cappella hook")]:
    print(f"  bar {b:3d} ({bar_t(b):5.1f} s): {dev}")


def rms_between(b0, b1):
    i0 = int(bar_t(b0) * SR)
    i1 = int(bar_t(b1) * SR) if b1 is not None else N
    return np.sqrt(np.mean(mix_L[i0:i1] ** 2 + mix_R[i0:i1] ** 2) / 2)


print("\nPer-section RMS:")
R = {}
for (name, b0), (_, b1) in zip(SECTIONS, SECTIONS[1:] + [("end", None)]):
    R[name] = rms_between(b0, b1)
    print(f"  {name:24s} {R[name]:.3f}")

# duet separation: overlap of refrain vs echo/countermelody activity
mask_v = np.zeros(int(DURATION * 100), dtype=bool)
mask_c = np.zeros_like(mask_v)
for spans, mask in [(VOICE_SPANS, mask_v), (COUNTER_SPANS, mask_c)]:
    for t0, t1 in spans:
        mask[int(t0 * 100):int(t1 * 100)] = True


def overlap_in(b0, b1):
    i0, i1 = int(bar_t(b0) * 100), int(bar_t(b1) * 100)
    v = mask_v[i0:i1]
    return (v & mask_c[i0:i1]).sum() / max(v.sum(), 1)


OV = {name: overlap_in(b0, b1) for name, b0, b1 in
      [("chorus 1", B_CH1, B_V2), ("chorus 2", B_CH2, B_BR),
       ("chorus 3", B_CH3, B_RIDE)]}
print("\nDuet separation (refrain/countermelody overlap ratio):")
for name, r in OV.items():
    print(f"  {name}: {r:.2f}")

checks = [
    ("thesis < verse 1 < chorus 1",
     R["THESIS (a cappella)"] < R["verse 1"] < R["CHORUS 1"]),
    ("chorus 1 > pre-chorus 1", R["CHORUS 1"] > R["pre-chorus 1"]),
    ("chorus 2 > pre-chorus 2", R["CHORUS 2"] > R["pre-chorus 2"]),
    ("chorus 2 >= chorus 1", R["CHORUS 2"] >= R["CHORUS 1"]),
    ("chorus 3 is the loudest section",
     R["CHORUS 3 (the fusion)"] == max(R.values())),
    ("the bridge is the trough",
     R["bridge"] < min(R["CHORUS 2"], R["CHORUS 3 (the fusion)"])),
    ("the bookend settles back near the thesis",
     R["BOOKEND"] < R["verse 1"]),
    ("hook count >= 9", len(HOOK_STMTS) >= 9),
    ("choruses 1-2 trade (overlap < 0.10)",
     OV["chorus 1"] < 0.10 and OV["chorus 2"] < 0.10),
    ("chorus 3 is the fusion (overlap > 0.40)", OV["chorus 3"] > 0.40),
]
if PITCH_MEAS is not None:
    checks.append(("vocal pitch: median <= 35 cents, max <= 60",
                   med_err <= 35 and max_err <= 60))

print("\nForm checks:")
ok = True
for name, passed in checks:
    print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
    ok &= passed
print("banned by construction: supersaw / sidechain / reverse cymbal / "
      "piano centerpiece / resonant sequence / rompler strings")
print("all checks passed" if ok else "SOME CHECKS FAILED")
