#!/usr/bin/env python3
"""No Access v2 — the jackhammer (tracks/ebm, 2026-09-08).  Working title Clearance.

v2, from the v1 listen verdict (no_access_notes.md, "v2 amendment"):
  * the ticks are EVENTS, not a carpet — six PIN attempts (eight keys
    typed on 16ths, then an ANSWER: two ticks falling = denied, rising
    = granted), the same sound, a few seconds each instead of 30-40 s;
  * the beat — the silver_wire_v3 recipe: a 55 % sidechain pump on the
    sustained layers (bed, pads, organ, stabs, bass; never the lead or
    the voice) and a sub-boom sine on every kick quarter, an octave
    under the bass root (a declared deviation from the 1993 "no pump,
    no sub-boom" — the user's ear over the blueprint);
  * the spoken slot is a TTS take (edge-tts, cached once in VOICE_DIR/
    tts/, the user's own take in VOICE_DIR/ takes priority) through
    machine(): the denials ring-modulated at the root (the robot), the
    grant dirt-only (intelligible);
  * more organ: the pre-choruses and the outro's fade, besides the break.
Everything else is v1 (below).

v1 (2026-09-06):

140 BPM, C# minor, 160 bars + tail = 4:34, seed 18.  The Backdraft
archetype from ../../inspiration/Apop_Soli_Deo_Gloria.md: the SH-101
gallop as the engine, the drums carrying the 16th energy, the song
standing still over it (harmony every bar or two, the seethe bed under
everything, the refrain declaimed baritone on dark_lead).  Notes:
no_access_notes.md — the plan, then the amendments from the probe
verdicts, which this script follows: NO BARK (the SH-101 tick
counter-sequence and a dark stab in its slots); gallop everywhere the
engine plays; pad and stabs voiced an octave above the refrain; the
deeper bass (the SH-101 sub square 0.6 / 0.85 in the choruses, a longer
kick body, a +2.5 dB low shelf below 90 Hz, the refrain's chest 1.0 -> 1.3);
the low organ throughout the break; a fade ending.  The spoken slot is
instrumental in v1 (VOICE_GAIN 0, Q14): the tick phrase retriggered
stands in for NO ACCESS, plain for ACCESS GRANTED.  For v2 drop
no_access.wav / access_granted.wav (spoken, dry) into VOICE_DIR and set
VOICE_GAIN — the machine chain is wired.

Output: /workspace/music/<NAME>.wav + .flac (44100 Hz stereo 16-bit).
Prints the VERIFY.md blocks; a FAIL never aborts the render.

Listening flags (LISTENING.md; checks are skipped on a partial render):
  --solo lead[,bass]   render only these layers (through the master)
  --mute drums         everything but these
  --slice 40 56        bars [40, 56) only — chorus 1
  --suffix _leadA      output <NAME>_leadA.wav
  --stems              + <NAME>_stems/<layer>.wav (post-reverb, weighted, pre-master)
"""
from __future__ import annotations

import argparse
import asyncio
import pathlib
import subprocess
import sys
import wave

import numpy as np
import soundfile
from scipy import signal

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "instruments"))
import _common                                                            # noqa: E402

_common.set_tempo(140)                          # BEFORE the instrument imports (they bind the grid)
_common.seed(18)
from _common import BAR, BEAT, SR, STEP, midi_to_hz, norm                 # noqa: E402
from dark_lead import dark_lead                                           # noqa: E402
from eps_hit import hit                                                   # noqa: E402
from eps_kick import kick                                                 # noqa: E402
from eps_snare import snare                                               # noqa: E402
from hats import hat                                                      # noqa: E402
from juno import arp, chorus, noise_sweep, organ, pad, stab               # noqa: E402
from machine import machine, retrigger                                    # noqa: E402
from seethe import seethe                                                 # noqa: E402
from sh101_bass import CELLS, note                                        # noqa: E402

# ------------------------------------------------------------- the piece
NAME = "no_access_v2"                                 # bump per iteration (no_access_v2.1 ...)
TOTAL_BARS = 160
END = TOTAL_BARS * BAR + 0.5
N = int(END * SR)
SECTIONS = [("INTRO", 0, 16), ("VERSE 1", 16, 32), ("PRE 1", 32, 40), ("CHORUS 1", 40, 56),
            ("VERSE 2", 56, 72), ("PRE 2", 72, 80), ("CHORUS 2", 80, 96), ("BREAK", 96, 112),
            ("FINAL", 112, 144), ("OUTRO", 144, 160)]

CS3, A2, GS2 = 49, 45, 44
CLUSTER = (56, 61, 62)                                # G#3 C#4 D4: the flat-2 cluster (verses)
CSM, A_, GSM = (64, 68, 73), (64, 69, 73), (63, 68, 71)   # an octave ABOVE the refrain (the 07 lesson)
CSM_LOW = (56, 61, 64)                                # the dark verse stab
ORGAN_I, ORGAN_V = (49, 56, 61), (44, 51, 56)         # open fifths: the break's organ, i then v
HIT_CHORD = (49, 56, 61, 64)
CHORUS_LOOP = (CSM, CSM, A_, GSM, CSM, CSM, A_, CSM)  # i i VI v | i i VI i
PRE_CHORDS = (CSM,) * 4 + (A_,) * 2 + (GSM,) * 2
ROOT = {CSM: CS3, A_: A2, GSM: GS2}
CELL = {**CELLS, "8ths": "x.x.x.x.x.x.x.x.", "answer": "x.x.x.x.7.7.o.5."}
INTERVAL = {"x": 0, "o": 12, "5": 7, "7": 10}

KICK_FIG = {"A": "x...x...x...x...", "B": "x...x...x...x.x.", "C": "x..xx...x...x.x."}
SNARE_P = "....x.......x..."
RUN_P = "............xxxx"
HAT_ACC = (1.0, 0.5, 0.7, 0.5)
OPEN_STEPS = (2, 6, 10, 14)
DARK_STAB_STEPS = (6, 14)
PIN_CELL = "x.xx.x.xx.xx...."                        # eight keys in twelve 16ths; the answer on beat 4
PIN_CODE = (73, 68, 74, 73, 68, 73, 74, 68)           # the same code every time: root / 5th / flat-2
ANSWER = {"denied": ((12, 74), (14, 68)),             # D5 falling to G#4: the tritone, wrong
          "granted": ((0, 68), (2, 73))}              # G#4 rising to C#5: the tonic, on the NEXT downbeat
ATTEMPTS = [(24, "denied", False), (38, "denied", True), (64, "denied", False), (78, "denied", True),
            (103, "denied", True), (111, "granted", True)]     # (bar, answer, spoken)
ORGAN_OF = {CS3: (49, 56, 61), A2: (45, 52, 57), GS2: (44, 51, 56)}   # open fifths per root

NOTE = {"G#2": 44, "A2": 45, "B2": 47, "C#3": 49, "D3": 50, "E3": 52, "F#3": 54, "G#3": 56, "A3": 57}
HOOK = ["C#3 C#3 C#3 - E3 - D3 -", "C#3 - . C#3 - - - -", "E3 - E3 E3 F#3 - E3 -", "G#2 - . G#2 - - - -",
        "C#3 C#3 C#3 - E3 - D3 -", "C#3 - - - . E3 F#3 G#3", "A3 - G#3 - F#3 - E3 -", "C#3 - - - - - . ."]
REFRAINS = [(40, 1.0), (48, 1.0), (80, 1.2), (88, 1.2), (112, 1.3), (120, 1.3), (128, 1.3), (136, 1.3)]
DOUBLES = (128, 136)                                  # the octave-up double: the fusion, final pass only
HITS = (8, 40, 80, 112, 128)
ROLL_BARS = {38, 39, 78, 79, 110, 111}
RISERS, DOWNSWEEPS = (38, 78, 110), (40, 80, 112)
SILENT = (111.75, 112.0)                              # the composed silent beat (bars)
FADE = (156, 160)
KICK_OUT = ((96, 112), (152, 160))

VOICE_GAIN = 1.0                                      # v2: the TTS slot on (0 = instrumental: the answers alone)
VOICE_DIR = pathlib.Path("/workspace/music/vocals/no_access")
VOICE_ID, VOICE_RATE = "en-GB-SoniaNeural", "-10%"    # edge-tts: the calm system voice
VOICE_TEXT = {"no_access": "No access.", "access_granted": "Access granted."}
PUMP_DEPTH, PUMP_TAU, PUMP_FLOOR = 0.55, 0.10, 0.30   # the silver_wire_v3 pump
BOOM_OCTAVE = -12                                     # the sub-boom an octave under the bass root (69/55/52 Hz)


def bar_t(b):
    return b * BAR


def section_of(bar):
    return next(name for name, b0, b1 in SECTIONS if b0 <= bar < b1)


def is_pre(b):
    return 32 <= b < 40 or 72 <= b < 80


def is_chorusy(b):
    return 40 <= b < 56 or 80 <= b < 96 or 112 <= b < 152


def is_versey(b):
    return 8 <= b < 32 or 56 <= b < 72


def chord_at(b):
    return PRE_CHORDS[b % 8] if is_pre(b) else CHORUS_LOOP[b % 8]


def figure_for(b):
    if is_pre(b):
        return "B" if b % 2 else "A"          # no figure C under the offbeat cell (its 16th would land on a bass note)
    return "C" if b % 4 == 3 else ("B" if b % 2 else "A")


def bass_spec(b):
    """-> (cell name, root midi, note kwargs) for bar b."""
    if b in (55, 95, 143):
        return "answer", CS3, {"sub": 0.85}
    if b < 8 or b >= 152:
        return "gallop", CS3, {"cutoff": (1400.0, 250.0), "sub": 0.6}
    if is_pre(b):
        return "offbeat", ROOT[chord_at(b)], {"sub": 0.6}
    if is_chorusy(b):
        return "gallop", ROOT[chord_at(b)], {"sub": 0.85}     # the deeper bass (Q12): the sub square up
    if 96 <= b < 112:
        return "8ths", CS3 if b < 104 else GS2, {"cutoff": (900.0, 250.0), "sub": 0.6}
    return "gallop", CS3, {"sub": 0.6}


def parse(lines):
    """8th-note token lines -> [(start_8th, midi, len_8ths)]."""
    out, prev = [], None
    for b, line in enumerate(lines):
        for i, tok in enumerate(line.split()):
            if tok in NOTE:
                out.append([b * 8 + i, NOTE[tok], 1])
            elif tok == "-":
                assert prev not in (".", None), f"'-' after a rest in bar {b}: {line!r}"
                out[-1][2] += 1
            prev = tok
    return [tuple(e) for e in out]


# ---------------------------------------------------------------- helpers
def fade(x, fin=0.004, fout=0.05):
    y = x.copy()
    ni, no = int(fin * SR), int(fout * SR)
    if ni:
        y[:ni] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(ni) / ni)
    if no:
        y[-no:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(no) / no)
    return y


def make_reverb_ir(seconds, decay, seed):
    r = np.random.default_rng(seed)
    n = int(seconds * SR)
    ir = r.standard_normal(n) * np.exp(-np.arange(n) / SR / decay)
    b, a = signal.butter(2, 4000 / (SR / 2), "low")
    ir = signal.lfilter(b, a, ir)
    return ir / np.sqrt(np.sum(ir ** 2))


IR_L = make_reverb_ir(3.0, 1.0, 7)
IR_R = make_reverb_ir(3.0, 1.0, 11)


def reverb_pair(L, R, wet):
    if wet <= 0.0:
        return L, R
    wL = signal.fftconvolve(L, IR_L)[: len(L)]
    wR = signal.fftconvolve(R, IR_R)[: len(R)]
    for d, w in ((L, wL), (R, wR)):
        w *= (np.max(np.abs(d)) + 1e-12) / (np.max(np.abs(w)) + 1e-12)
    return (1 - wet) * L + wet * wL, (1 - wet) * R + wet * wR


def highpass(x, hz, order=2):
    return signal.sosfilt(signal.butter(order, hz, "high", fs=SR, output="sos"), x)


def lowpass(x, hz, order=2):
    return signal.sosfilt(signal.butter(order, hz, "low", fs=SR, output="sos"), x)


def add_at(buf, x, start_s, gain=1.0):
    i0 = int(start_s * SR)
    if i0 >= len(buf):
        return
    n = min(len(x), len(buf) - i0)
    if n > 0:
        buf[i0:i0 + n] += gain * x[:n]


def place(layer, x, t, gain=1.0, pan=0.0):
    """Constant-power pan of a mono event into a stereo layer pair."""
    a = (pan + 1.0) / 2.0
    add_at(layer[0], x, t, gain * np.cos(a * np.pi / 2))
    add_at(layer[1], x, t, gain * np.sin(a * np.pi / 2))


def place_stereo(layer, dry, t, gain=1.0):
    """The Juno stereo chorus: modulation inverted between the channels."""
    add_at(layer[0], chorus(dry, 1.0, "I", phase=0.0), t, gain)
    add_at(layer[1], chorus(dry, 1.0, "I", phase=np.pi), t, gain)


def tick(midi, steps=0.35):
    """The keypad voice: the SH-101 as a dry square blip; `steps` = its
    length in 16ths (0.35 a key, 1.2 an answer, 3.2 the held grant)."""
    return note(midi, dur=STEP * steps, cutoff=(6000.0, 1500.0), env=0.02, res=4.5, sub=0.0, wave="square")


def take(name):
    """The spoken phrase, mono at SR, silence trimmed: the user's own take
    (VOICE_DIR/<name>.wav) if present, else the TTS cached once in
    VOICE_DIR/tts/ (edge-tts; needs the network the first time).
    Returns (array or None, status)."""
    if VOICE_GAIN <= 0.0:
        return None, "silenced (VOICE_GAIN 0)"
    own, cache = VOICE_DIR / f"{name}.wav", VOICE_DIR / "tts" / f"{name}.wav"
    path, source = (own, "own take") if own.exists() else (cache, "tts " + VOICE_ID)
    if not path.exists():
        try:
            import edge_tts                                   # heavy, optional: lazy on purpose
            cache.parent.mkdir(parents=True, exist_ok=True)
            tmp = cache.with_suffix(".mp3")
            asyncio.run(edge_tts.Communicate(VOICE_TEXT[name], voice=VOICE_ID, rate=VOICE_RATE).save(str(tmp)))
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(tmp), "-ar", str(SR), "-ac", "1",
                            str(cache)], check=True)
            tmp.unlink()
        except Exception as e:                                # no net, no cache: the answers alone
            return None, f"unavailable ({type(e).__name__}) — the tick answer alone"
    x, sr = soundfile.read(str(path))
    x = x.mean(axis=1) if x.ndim > 1 else x
    if sr != SR:
        x = signal.resample(x, int(len(x) * SR / sr))
    x = norm(x)
    loud = np.abs(x) > 0.03
    x = x[int(np.argmax(loud)): len(x) - int(np.argmax(loud[::-1]))]
    return norm(x), source


def kick_quarters():
    """(t, bass root) of every 4-on-the-floor kick, from the tables — roll
    bars excluded (crescendos don't pump).  Drives the pump and the boom."""
    out = []
    for b in range(4, 152):
        if any(b0 <= b < b1 for b0, b1 in KICK_OUT) or b in ROLL_BARS:
            continue
        root = bass_spec(b)[1]
        for beat in range(4):
            out.append((bar_t(b) + beat * BEAT, root))
    return out


def make_sub_boom(f):
    """The silver_wire_v3 boom: a sine with a short pitch drop, sustaining
    the beat (0.40 s), hard release in the last 60 ms.  The kick's low end."""
    n = int(0.40 * SR)                                   # the beat at 140 is 0.429 s
    td = np.arange(n) / SR
    f_curve = f * (1.0 + 0.35 * np.exp(-td * 12.0))
    x = np.sin(2 * np.pi * np.cumsum(f_curve) / SR)
    env = (1 - np.exp(-td / 0.003)) * np.exp(-td * 1.2) * np.clip((0.40 - td) / 0.06, 0, 1)
    return x * env


LAYER_NAMES = ["bed", "pad", "organ", "stab", "ticks", "bass", "boom", "drums", "lead", "double", "hit", "voice", "fx"]
WETS = {"bed": 0.0, "pad": 0.35, "organ": 0.3, "stab": 0.2, "ticks": 0.1, "bass": 0.0, "boom": 0.0, "drums": 0.06,
        "lead": 0.25, "double": 0.35, "hit": 0.3, "voice": 0.15, "fx": 0.3}
WEIGHTS = {"bed": 0.30, "pad": 0.20, "organ": 0.26, "stab": 0.20, "ticks": 0.16, "bass": 0.40, "boom": 0.18, "drums": 0.44,
           "lead": 0.40, "double": 0.16, "hit": 0.28, "voice": 0.30, "fx": 0.14}
PUMPED = {"bed", "pad", "organ", "stab", "bass"}       # the sustained layers breathe on the kick; never the lead/voice

ap = argparse.ArgumentParser(description="No Access — see the docstring")
ap.add_argument("--solo", default="", help="comma-separated layer names to render alone")
ap.add_argument("--mute", default="", help="comma-separated layer names to leave out")
ap.add_argument("--slice", nargs=2, type=int, metavar=("B0", "B1"), help="bars [B0, B1) only")
ap.add_argument("--suffix", default="", help="appended to the output name")
ap.add_argument("--stems", action="store_true", help="also write per-layer stems")
ARGS = ap.parse_args()
SOLO = {x for x in ARGS.solo.split(",") if x}
MUTE = {x for x in ARGS.mute.split(",") if x}
PARTIAL = bool(SOLO or MUTE or ARGS.slice)
for name in SOLO | MUTE:
    assert name in LAYER_NAMES, f"unknown layer {name!r}; layers: {LAYER_NAMES}"


def want(name):
    return name not in MUTE and (not SOLO or name in SOLO)


MIX = [np.zeros(N), np.zeros(N)]
PRE = {}                                              # stems only (memory: 12 layers x 4:34 is 2 GB)


KICKS = kick_quarters()
PUMP = np.ones(N)
_dip_n = int(0.40 * SR)
_dip = PUMP_DEPTH * np.exp(-np.arange(_dip_n) / SR / PUMP_TAU)
for _t, _ in KICKS:
    _i0 = int(_t * SR)
    _i1 = min(N, _i0 + _dip_n)
    PUMP[_i0:_i1] = np.minimum(PUMP[_i0:_i1], 1.0 - _dip[: _i1 - _i0])
np.clip(PUMP, PUMP_FLOOR, 1.0, out=PUMP)


def commit(name, layer):
    """Normalise, pump (the sustained layers), reverb, weight, add to the
    mix; the layer is dropped after."""
    L, R = layer
    pk = max(np.max(np.abs(L)), np.max(np.abs(R)))
    if pk < 1e-9:
        return
    L, R = L / pk, R / pk
    if name in PUMPED:
        L, R = L * PUMP, R * PUMP
    L, R = reverb_pair(L, R, WETS[name])
    MIX[0] += WEIGHTS[name] * L
    MIX[1] += WEIGHTS[name] * R
    if ARGS.stems:
        PRE[name] = (WEIGHTS[name] * L, WEIGHTS[name] * R)


def new_layer():
    return [np.zeros(N), np.zeros(N)]


HOOKS = 0
lead_events = []            # (t, midi, dur, bar)
drum_events = []            # (t, kind)
bass_events = []            # (bar, step, midi, cell)
tick_events = []            # (bar, step, kind: key | denied | granted, dur)
voice_events = []           # (bar, name, mode, source)
boom_count = 0
BED = None

# ------------------------------------------------------------------- bed
if want("bed"):
    BED = seethe(CS3, END, throb=0.4, grit=0.3)
    layer = new_layer()
    place(layer, BED, 0.0)
    commit("bed", layer)

# ------------------------------------------------------------------- pad
if want("pad"):
    layer = new_layer()
    for b in list(range(16, 32, 2)) + list(range(56, 72, 2)):
        place_stereo(layer, pad(CLUSTER, 2 * BAR, depth=0.0, cutoff=600.0), bar_t(b))
    for b in [b for b in range(32, 152) if is_pre(b) or is_chorusy(b)]:
        place_stereo(layer, pad(chord_at(b), BAR, depth=0.0), bar_t(b))
    commit("pad", layer)

# ----------------------------------------------------------------- organ
if want("organ"):
    layer = new_layer()
    for b in [b for b in range(32, 80) if is_pre(b)]:                     # v2: under the pre-choruses
        place_stereo(layer, organ(ORGAN_OF[ROOT[chord_at(b)]], BAR, cutoff=600.0, depth=0.0), bar_t(b), 0.8)
    for b in range(96, 112, 2):
        place_stereo(layer, organ(ORGAN_I if b < 104 else ORGAN_V, 2 * BAR, cutoff=600.0, depth=0.0), bar_t(b))
    for b in range(152, 160, 2):                                            # v2: the fade ends on the organ
        place_stereo(layer, organ(ORGAN_I, 2 * BAR, cutoff=500.0, depth=0.0), bar_t(b), 0.9)
    commit("organ", layer)

# ------------------------------------------------------------------ stab
if want("stab"):
    layer = new_layer()
    for b in range(16, 32):
        for s in DARK_STAB_STEPS:
            place(layer, stab(CSM_LOW, depth=0.0, cutoff=500.0, hpf=1), bar_t(b) + s * STEP, 0.9, pan=0.25)
    for b in range(56, 72):
        for s in DARK_STAB_STEPS:
            place(layer, stab(CSM_LOW, depth=0.0, cutoff=700.0, hpf=1), bar_t(b) + s * STEP, 1.0, pan=0.25)
    for b in [b for b in range(32, 152) if is_pre(b) or is_chorusy(b)]:
        g = 0.8 if b < 72 else 1.0                       # chorus 2 and the final a notch up
        for s in OPEN_STEPS:
            place_stereo(layer, stab(chord_at(b), depth=0.0), bar_t(b) + s * STEP, g)
    commit("stab", layer)

# ----------------------------------------------------------------- ticks
if want("ticks"):
    layer = new_layer()
    keys = [i for i, ch in enumerate(PIN_CELL) if ch == "x"]
    for b, kind, _ in ATTEMPTS:
        for k, s in enumerate(keys):                                       # the code typed
            place(layer, tick(PIN_CODE[k]), bar_t(b) + s * STEP, pan=-0.3)
            tick_events.append((b, s, "key", STEP * 0.35))
        ab = b if kind == "denied" else b + 1                              # granted: after the silent beat
        for i, (s, m) in enumerate(ANSWER[kind]):
            steps = 1.2 if (kind == "denied" or i == 0) else 3.2           # the grant's tonic is held
            place(layer, tick(m, steps), bar_t(ab) + s * STEP, 1.0, pan=-0.3)
            tick_events.append((ab, s, kind, STEP * steps))
    commit("ticks", layer)

# ------------------------------------------------------------------ bass
if want("bass"):
    layer = new_layer()
    for b in range(TOTAL_BARS):
        cell_name, root, kw = bass_spec(b)
        cell = CELL[cell_name]
        onsets = [i for i, ch in enumerate(cell) if ch != "."]
        for j, s in enumerate(onsets):
            gap = (onsets[j + 1] if j + 1 < len(onsets) else onsets[0] + 16) - s
            m = root + INTERVAL[cell[s]]
            place(layer, note(m, dur=gap * STEP * 0.5, **kw), bar_t(b) + s * STEP)
            bass_events.append((b, s, m, cell_name))
    commit("bass", layer)

# ------------------------------------------------------------------ boom
if want("boom"):
    layer = new_layer()
    BOOM = {r: make_sub_boom(midi_to_hz(r + BOOM_OCTAVE)) for r in (CS3, A2, GS2)}
    for t, root in KICKS:
        place(layer, BOOM[root], t)
        boom_count += 1
    commit("boom", layer)

# ----------------------------------------------------------------- drums
KICK, SNARE, CH, OH = kick(decay=6.0), snare(), hat(), hat(open_=True)     # decay 6: a longer body (the deeper bass, Q12)
if want("drums"):
    layer = new_layer()
    for b in range(4, 152):
        kick_out = any(b0 <= b < b1 for b0, b1 in KICK_OUT)
        rolling = b in ROLL_BARS
        if kick_out and not rolling:
            continue
        fig = KICK_FIG[figure_for(b)]
        for s in range(16):
            t = bar_t(b) + s * STEP
            if not kick_out and fig[s] == "x":
                place(layer, KICK, t, 1.0)
                drum_events.append((t, "kick"))
            if b < 8:
                continue                                  # bars 4-8: the kick alone
            if not rolling and SNARE_P[s] == "x":
                place(layer, SNARE, t, 0.9)
                drum_events.append((t, "snare"))
            elif not rolling and is_versey(b) and b % 4 == 3 and RUN_P[s] == "x":
                place(layer, SNARE, t, 0.55)
                drum_events.append((t, "run"))
            if not kick_out:
                if (is_pre(b) or is_chorusy(b)) and s in OPEN_STEPS:
                    place(layer, OH, t, 0.32, pan=0.2)
                    drum_events.append((t, "oh"))
                else:
                    place(layer, CH, t, 0.28 * HAT_ACC[s % 4], pan=0.2)
                    drum_events.append((t, "ch"))
        if rolling:                                       # 8ths, then 16ths -> 32nds, rising
            first = b in (38, 78, 110)
            steps = np.arange(0, 16, 2) if first else np.concatenate([np.arange(0, 8, 1), np.arange(8, 16, 0.5)])
            for i, s in enumerate(steps):
                g = (0.4 + 0.25 * i / len(steps)) if first else (0.65 + 0.35 * i / len(steps))
                t = bar_t(b) + s * STEP
                place(layer, SNARE, t, 0.9 * g)
                drum_events.append((t, "roll"))
    commit("drums", layer)


# ------------------------------------------------------------------ lead
def place_line(layer, lines, bar0, chest, count=True, transpose=0, stereo=False, gain=1.0):
    global HOOKS
    for start, midi, ln in parse(lines):
        t = bar_t(bar0) + start * BEAT / 2
        dur = ln * BEAT / 2 * 0.95
        x = dark_lead(midi + transpose, dur, chest)
        if stereo:
            place_stereo(layer, x, t, gain)
        else:
            place(layer, x, t, gain)
        if count:
            lead_events.append((t, midi, dur, bar0 + start // 8))
    if count:
        HOOKS += 1


if want("lead"):
    layer = new_layer()
    for bar0, chest in REFRAINS:
        place_line(layer, HOOK, bar0, chest)
    commit("lead", layer)
if want("double"):
    layer = new_layer()
    for bar0 in DOUBLES:
        place_line(layer, HOOK, bar0, 0.0, count=False, transpose=12, stereo=True)
    commit("double", layer)

# ------------------------------------------------------------------- hit
if want("hit"):
    layer = new_layer()
    for b in HITS:
        place(layer, hit(HIT_CHORD), bar_t(b), pan=0.3)
    commit("hit", layer)

# ----------------------------------------------------------------- voice
if want("voice"):
    layer = new_layer()
    for b, kind, spoken in ATTEMPTS:
        if not spoken:
            continue
        name = "no_access" if kind == "denied" else "access_granted"
        x, source = take(name)
        t = bar_t(b + 1) + (BEAT if kind == "granted" else 0.0)           # denied: the next downbeat; granted: beat 2
        retrig = b == 103                                                   # the break: the code jams
        if x is not None:
            y = machine(x, ring_hz=midi_to_hz(CS3)) if kind == "denied" else machine(x)   # the robot / the clean grant
            if retrig:
                y = retrigger(y, STEP, 3, head=0.08)
            place(layer, y, t, VOICE_GAIN)
        voice_events.append((b + 1, name, "retrigger" if retrig else "plain", source if x is not None else source))
    commit("voice", layer)

# -------------------------------------------------------------------- fx
if want("fx"):
    layer = new_layer()
    for b in RISERS:
        place(layer, noise_sweep(2 * BAR, 200.0, 6000.0, res=3.0), bar_t(b), 0.8)
    for b in DOWNSWEEPS:
        place(layer, noise_sweep(BAR, 6000.0, 150.0, res=4.0), bar_t(b), 0.6)
    for b in range(128, 144) if want("fx") else ():   # the one Juno sequence: 8th-note down-arp, final pass
        x = arp(chord_at(b), bars=1, octaves=1, pattern="down", rate=2, cutoff=500.0)
        place(layer, x[: int(BAR * SR) + int(0.3 * SR)], bar_t(b), 0.7, pan=0.35)
    commit("fx", layer)

# ------------------------------------------------------------------- mix
for ch in (0, 1):                                     # the minimal 1993 master: HP, two shelves, glue
    MIX[ch] = highpass(MIX[ch], 30)
    MIX[ch] = MIX[ch] + 0.33 * lowpass(MIX[ch], 90)       # +2.5 dB below 90 Hz: the deeper bass (Q12)
    MIX[ch] = MIX[ch] + 0.22 * highpass(MIX[ch], 3000)
pk = max(np.max(np.abs(MIX[0])), np.max(np.abs(MIX[1]))) + 1e-12
for ch in (0, 1):
    MIX[ch] = np.tanh(1.12 * MIX[ch] / pk) / np.tanh(1.12) * 0.92
# the composed silent beat, then the fade (both on the mastered mix)
i0, i1 = int(bar_t(SILENT[0]) * SR), int(bar_t(SILENT[1]) * SR)
edge = int(0.005 * SR)
gate = np.ones(N)
gate[i0:i1] = 0.0
gate[i0 - edge:i0] = np.linspace(1, 0, edge)
gate[i1:i1 + edge] = np.linspace(0, 1, edge)
f0, f1 = int(bar_t(FADE[0]) * SR), int(bar_t(FADE[1]) * SR)
gate[f0:f1] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(f1 - f0) / (f1 - f0))
gate[f1:] = 0.0
for ch in (0, 1):
    MIX[ch] *= gate
i_sl = (int(bar_t(ARGS.slice[0]) * SR), int(bar_t(ARGS.slice[1]) * SR)) if ARGS.slice else (0, N)
OUT = np.stack([fade(MIX[0][i_sl[0]:i_sl[1]], 0.002, 0.03), fade(MIX[1][i_sl[0]:i_sl[1]], 0.002, 0.03)], axis=1)

out_dir = pathlib.Path("/workspace/music")
out_dir.mkdir(parents=True, exist_ok=True)
STEM = NAME + ARGS.suffix


def write_wav(path, x):
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())
    print(f"Wrote {path}  ({len(x) / SR:.1f} s)")


wav_path = out_dir / f"{STEM}.wav"
write_wav(wav_path, OUT)
flac_path = out_dir / f"{STEM}.flac"
soundfile.write(str(flac_path), OUT, SR)
print(f"Wrote {flac_path}")
if ARGS.stems:
    stem_dir = out_dir / f"{STEM}_stems"
    stem_dir.mkdir(exist_ok=True)
    for name, (L, R) in PRE.items():
        write_wav(stem_dir / f"{name}.wav", np.stack([L[i_sl[0]:i_sl[1]], R[i_sl[0]:i_sl[1]]], axis=1))
if PARTIAL:
    print(f"\npartial render (solo {sorted(SOLO) or '-'}, mute {sorted(MUTE) or '-'}, "
          f"slice {ARGS.slice or '-'}): checks skipped — the piece is the full render.")
    sys.exit(0)

# ---------------------------------------------------------------- verify
fails = []


def check(name, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}  {detail}")
    if not ok:
        fails.append(name)


def mmss(t):
    return f"{int(t // 60)}:{t % 60:04.1f}"


def rms_between(t0, t1):
    seg = OUT[int(t0 * SR):int(t1 * SR)]
    return float(np.sqrt(np.mean(seg ** 2)))


def sec_rms(b0, b1):
    return rms_between(bar_t(b0), bar_t(b1))


def sub_share(b0, b1, hz=60.0):
    seg = OUT[int(bar_t(b0) * SR):int(bar_t(b1) * SR)].mean(axis=1)
    X = np.abs(np.fft.rfft(seg)) ** 2
    f = np.fft.rfftfreq(len(seg), 1 / SR)
    return float(X[f < hz].sum() / X.sum())


print("\n=== SECTION MAP ===")
for name, b0, b1 in SECTIONS:
    print(f"  {mmss(bar_t(b0)):>6}  bar {b0:3d}  {name}")
events = [(0, "bed + the riff naked (gallop, dark)"), (4, "kick in"), (8, "slam + hats + hit 1"),
          (24, "PIN attempt 1: eight keys, the falling answer (denied)"), (32, "offbeat bass, chorused stabs, open hats, organ"),
          (38, "PIN attempt 2 + roll + riser"), (39, "denied -> NO ACCESS (the voice)"), (40, "hit; refrain x2, chest 1.0; the downsweep"),
          (55, "the bass turnaround (answer cell)"), (56, "verse 2: stab opens"), (64, "PIN attempt 3 (denied)"),
          (78, "PIN attempt 4 + roll + riser"), (79, "denied -> NO ACCESS"), (80, "hit; refrain x2, chest 1.2"),
          (96, "kick OUT (no pump, no boom): bed, organ i, the riff on dark 8ths"),
          (103, "PIN attempt 5; organ v"), (104, "denied -> NO ACCESS retriggered (the code jams)"), (110, "roll + riser"),
          (111, "PIN attempt 6 (beats 1-3)"), (SILENT[0], "THE SILENT BEAT"),
          (112, "the rising answer (granted) + hit; ACCESS GRANTED on beat 2; final chorus, chest 1.3"),
          (128, "hit; the octave double + the Juno down-arp (the fusion)"),
          (144, "outro: the chorus instrumental"), (152, "drums out (pump and boom stop): bed + riff + organ"),
          (156, "the fade"), (160, "end")]
for b, what in events:
    print(f"  {mmss(bar_t(b)):>6}  bar {b:5.2f}  {what}")
cells = {}
for b, s, m, c in bass_events:
    cells.setdefault(section_of(b), set()).add(c)
print("  bass cells:", "  ".join(f"{n}:{'/'.join(sorted(cells.get(n, ())))}" for n, _, _ in SECTIONS))

print(f"\n=== HOOK COUNT ===\n  full refrain statements: {HOOKS} (target >= 8); the octave double and the riff uncounted")
check("hook count >= 8", HOOKS >= 8)

print("\n=== SEAM CHECKLIST ===")
win = int(0.25 * SR)
bed_rms = [float(np.sqrt(np.mean(BED[i:i + win] ** 2)))
           for i in range(int(0.5 * SR), int(bar_t(FADE[0]) * SR) - win, win)]
print(f"  bed continuous 0.5 s .. bar {FADE[0]} (the fade): min 0.25 s RMS {min(bed_rms):.4f}")
for b0, device in ((16, "the tick-less engine + the cluster pad entering"), (32, "the bass to the offbeat cell + the chorused stab"),
                   (40, "roll + riser + NO ACCESS, then the hit"), (56, "the bass turnaround (answer cell) across the bar"),
                   (72, "the offbeat cell + stabs"), (80, "roll + riser + NO ACCESS, then the hit"),
                   (96, "the organ entering under the last chorus bar's bass turnaround; kick out"),
                   (112, "the silent beat, then ACCESS GRANTED + the hit"), (144, "the refrain out, the engine unbroken"),
                   (152, "drums out; the bed + riff + ticks carry the fade")):
    print(f"  bar {b0:3d}: bed unbroken + {device}")
check("bed unbroken at every seam (up to the fade)", min(bed_rms) > 1e-3)

print("\n=== PER-SECTION RMS (post-master) ===")
R = {name: sec_rms(b0, b1) for name, b0, b1 in SECTIONS}
S = {name: sub_share(b0, b1) for name, b0, b1 in SECTIONS}
S80 = {name: sub_share(b0, b1, 80.0) for name, b0, b1 in SECTIONS}
for name, b0, b1 in SECTIONS:
    print(f"  {name:9s} {R[name]:.3f}   sub-60 share {S[name]:.2f}   sub-80 share {S80[name]:.2f}")
check("intro < verse 1 < chorus 1", R["INTRO"] < R["VERSE 1"] < R["CHORUS 1"])
check("each chorus > its pre-chorus", R["CHORUS 1"] > R["PRE 1"] and R["CHORUS 2"] > R["PRE 2"])
check("chorus 2 >= chorus 1", R["CHORUS 2"] >= R["CHORUS 1"])
check("the break is the trough", R["BREAK"] < R["CHORUS 2"] and R["BREAK"] < R["FINAL"])
check("the final chorus is the loudest", R["FINAL"] == max(R.values()))
check("outro < final", R["OUTRO"] < R["FINAL"])

print("\n=== THE STOMP (from the tables and the drum events) ===")
for fig, p in KICK_FIG.items():
    check(f"figure {fig}: kick on every quarter", all(p[s] == "x" for s in (0, 4, 8, 12)), p)
check("snare on 2 and 4 only", [i for i, c in enumerate(SNARE_P) if c == "x"] == [4, 12])
kicks = sorted(t for t, k in drum_events if k == "kick")
out_hits = [t for t in kicks if any(bar_t(b0) <= t < bar_t(b1) for b0, b1 in KICK_OUT)]
check("no kick in the kick-out sections (break, outro's second half)", not out_hits, f"({len(out_hits)} stray)")
print(f"  drum onsets {len(drum_events)}; first kick bar {kicks[0] / BAR:.2f}; last drum bar {max(t for t, _ in drum_events) / BAR:.2f}")

print("\n=== BASS CELLS ===")
per_bar = {}
for b, s, m, c in bass_events:
    per_bar.setdefault(b, []).append((s, m, c))
ok_count = all(len(v) == sum(1 for ch in CELL[v[0][2]] if ch != ".") for v in per_bar.values())
check("onsets per bar == the declared cell, every bar", ok_count)
check("gate duty 0.5 (each note half its gap)", True, "(by construction: dur = gap * STEP * 0.5)")
clash = [(b, s) for b, v in per_bar.items() if v[0][2] == "offbeat"
         for s, _, _ in v if KICK_FIG[figure_for(b)][s] == "x"]
check("offbeat cell: no bass onset on a kick 16th", not clash, f"{clash[:4]}" if clash else "")
ledger = [(b, per_bar[b][0][1], ROOT[chord_at(b)]) for b in range(40, 152) if is_chorusy(b) and b not in (55, 95, 143)]
bad = [(b, m, r) for b, m, r in ledger if m != r]
print("  chorus root ledger (bar 40-48):", " ".join(f"{m}" for _, m, _ in ledger[:8]), "== chord roots",
      " ".join(f"{r}" for _, _, r in ledger[:8]))
check("chorus root ledger: bass root == chord root every chorus bar", not bad, f"{bad[:3]}" if bad else "")

print("\n=== THE REFRAIN SINGS + DARK (from the HOOK table) ===")
ev = parse(HOOK)
onsets = len(ev)
density = onsets / 128
held = sum(1 for _, _, ln in ev if ln >= 2) / onsets
run = best = 0
for _, _, ln in ev:
    run = run + 1 if ln == 1 else 0
    best = max(best, run)
q_end = [e for e in ev if e[0] < 32][-1]
a_end = ev[-1]
midis = [m for _, m, _ in ev]
steps = [b - a for a, b in zip(midis[:-1], midis[1:]) if b != a]
downs = sum(1 for d in steps if d < 0) / max(1, len(steps))
flat2 = sum(1 for m in midis if m % 12 == 2)
print(f"  onsets {onsets}  density {density:.2f} (0.20-0.50)  held {held:.2f} (>= 0.5)  longest 8th run {best} (<= 4)  {onsets / (8 * BAR):.1f} notes/s")
print(f"  DARK: register {min(midis)}-{max(midis)} (median {int(np.median(midis))}; floor G#2=44, ceiling A3=57)  "
      f"down-steps {downs:.2f} (>= 0.5)  max upward leap {max(steps)} st (<= 5)  flat-2nd onsets {flat2} (>= 2)")
check("density window 0.20-0.50", 0.20 <= density <= 0.50)
check("held fraction >= 0.5", held >= 0.5)
check("run ceiling <= 4", best <= 4)
check("phrase ends held >= a half note", q_end[2] >= 4 and a_end[2] >= 4)
check("Q hangs on a G#, A lands on a C#", q_end[1] % 12 == 8 and a_end[1] % 12 == 1)
check("register G#2..A3", min(midis) >= 44 and max(midis) <= 57)
check("descending contour: down-steps >= 0.5", downs >= 0.5)
check("no soaring leap: max upward <= 5 st", max(steps) <= 5)
check("the flat 2nd colours the refrain", flat2 >= 2)
lowest_pad = min(min(ch) for ch in CHORUS_LOOP + PRE_CHORDS)
check("chorus pad and stabs voiced above the refrain (lowest note > A3)", lowest_pad > 57, f"(midi {lowest_pad})")

print("\n=== TRUNCATION ===")
for k, x, cut in (("kick", KICK, 0.20), ("snare", SNARE, 0.14)):
    sounding = (int(np.max(np.nonzero(np.abs(x) > 1e-3))) + 1) / SR
    check(f"{k} truncated at its cut", sounding <= cut + 0.012, f"(sounding {sounding * 1000:.0f} ms, cut {cut * 1000:.0f} ms)")

print("\n=== BED CHECK (tinnitus rule) ===")
w2 = int(2.0 * SR)
peaks = []
for i in range(0, len(BED) - w2, w2):
    seg = BED[i:i + w2] * np.hanning(w2)
    X = np.abs(np.fft.rfft(seg))
    f = np.fft.rfftfreq(w2, 1 / SR)
    m = f > 20
    peaks.append(float(f[m][np.argmax(X[m])]))
print(f"  strongest peak per 2 s: min {min(peaks):.0f} Hz, max {max(peaks):.0f} Hz over {len(peaks)} windows")
check("bed's strongest peak < 120 Hz in every window", max(peaks) < 120)

print("\n=== THE KEYPAD (ticks as events) ===")
spans = {}
for b, s, kind, dur in tick_events:
    a = next(a for a, _, _ in ATTEMPTS if a <= b <= a + 1)
    t0, t1 = spans.get(a, (1e9, 0))
    t = bar_t(b) + s * STEP
    spans[a] = (min(t0, t), max(t1, t + dur))
total = sum(d for _, _, _, d in tick_events)
kinds = [k for _, k, _ in ATTEMPTS]
print(f"  {len(ATTEMPTS)} attempts ({kinds.count('denied')} denied, {kinds.count('granted')} granted); "
      f"{sum(1 for e in tick_events if e[2] == 'key')} keys; ticks sounding {total:.1f} s of {END:.0f} s")
for a, (t0, t1) in sorted(spans.items()):
    print(f"  bar {a:3d}  {t1 - t0:.2f} s")
check("five denials then one grant", kinds == ["denied"] * 5 + ["granted"])
check("every attempt shorter than 3 s", all(t1 - t0 < 3.0 for t0, t1 in spans.values()))
check("ticks sounding < 20 s in total (a keypad, not a carpet)", total < 20.0)

print("\n=== TWO-VOICE SEPARATION (ticks vs refrain) ===")
tick_ch = sum(1 for b, _, k, _ in tick_events if is_chorusy(b) and b < 144 and k != "granted")
tick_vb = sum(1 for b, _, _, _ in tick_events if is_versey(b) or is_pre(b) or 96 <= b < 112)
lead_ch = sum(1 for _, _, _, b in lead_events if is_chorusy(b) and b < 144)
lead_vb = sum(1 for _, _, _, b in lead_events if not (is_chorusy(b) and b < 144))
print(f"  tick onsets: verses/pre/break {tick_vb}, choruses {tick_ch} (+ the granted answer on bar 112);  "
      f"refrain onsets: choruses {lead_ch}, elsewhere {lead_vb}")
check("ticks never in a chorus (but the grant); refrain never outside one", tick_ch == 0 and lead_vb == 0 and tick_vb > 0 and lead_ch > 0)

print("\n=== THE BEAT (pump + boom) ===")
mean_ch1 = float(np.mean(PUMP[int(bar_t(40) * SR):int(bar_t(56) * SR)]))
mean_br = float(np.mean(PUMP[int(bar_t(96) * SR):int(bar_t(110) * SR)]))
print(f"  pump: depth {PUMP_DEPTH}, floor {PUMP.min():.2f}, {len(KICKS)} ducked beats; mean in chorus 1 {mean_ch1:.2f}, in the break {mean_br:.2f}")
print(f"  boom: {boom_count} hits an octave under the bass root ({', '.join(f'{midi_to_hz(r + BOOM_OCTAVE):.0f}' for r in (CS3, A2, GS2))} Hz)")
check("the pump breathes in the choruses and rests in the break", 0.75 <= mean_ch1 <= 0.95 and mean_br == 1.0)
check("one boom per ducked beat", boom_count == len(KICKS) and boom_count > 0)

print("\n=== THE SLOT ===")
print(f"  VOICE_GAIN {VOICE_GAIN}  voice {VOICE_ID} {VOICE_RATE}  dir {VOICE_DIR}")
for b, name, mode, src in voice_events:
    print(f"  bar {b:3d}  {name:15s} {mode:9s} ({src})")
check("three denials + one grant, in order", [n for _, n, _, _ in voice_events] == ["no_access"] * 3 + ["access_granted"]
      and [b for b, _, _, _ in voice_events] == [39, 79, 104, 112])
voiced = all(src.startswith(("own", "tts")) for _, _, _, src in voice_events)
print(f"  voice status: {'placed in all four slots' if voiced else 'NOT placed — ' + voice_events[0][3]} "
      f"(a missing voice is reported, not failed: the answers carry the slot)")
silent = rms_between(bar_t(SILENT[0]) + 0.02, bar_t(SILENT[1]) - 0.02)
check("the silent beat is silent (< -50 dBFS)", silent < 10 ** (-50 / 20), f"({20 * np.log10(silent + 1e-12):.0f} dBFS)")

print("\n=== THE ENDING (fade) ===")
last_drum = max(t for t, _ in drum_events)
check("no drum onset at/after bar 152", last_drum < bar_t(152), f"(last drum bar {last_drum / BAR:.2f})")
check("no boom after the drums stop", max(t for t, _ in KICKS) < bar_t(152))
tail = [sec_rms(b, b + 1) for b in range(FADE[0], FADE[1])]
print("  per-bar RMS over the fade:", " ".join(f"{r:.3f}" for r in tail))
check("the last 4 bars' RMS descend", all(a > b for a, b in zip(tail, tail[1:])))
last = rms_between(END - 0.1, END)
check("the final 0.1 s < -60 dBFS", last < 1e-3, f"({20 * np.log10(last + 1e-12):.0f} dBFS)")

print("\n=== MASTER GUARDRAILS ===")
tp = float(np.max(np.abs(OUT)))
fin = OUT[int(bar_t(112) * SR):int(bar_t(144) * SR)]
crest = float(np.max(np.abs(fin)) / np.sqrt(np.mean(fin ** 2)))
print(f"  true peak {tp:.3f}   final-chorus crest {crest:.2f}")
check("true peak < 1.0", tp < 1.0)
check("final-chorus crest >= 3.2", crest >= 3.2)
kick_secs = ("VERSE 1", "PRE 1", "CHORUS 1", "VERSE 2", "PRE 2", "CHORUS 2", "FINAL")
check("sub-80 share 0.45-0.75 where the kick plays (C#'s sub square sits at 69 Hz; sub-60 printed above)",
      all(0.45 <= S80[n] <= 0.75 for n in kick_secs), " ".join(f"{n}:{S80[n]:.2f}" for n in kick_secs))
check("FLAC written", flac_path.exists())

print("\nall checks passed" if not fails else f"SOME CHECKS FAILED: {fails}")
