#!/usr/bin/env python3
"""Clearance — the probes.

Short samples at 147 BPM of the engine, the drum figures, the bed, the
refrain and the vocal-slot treatment, each printed with the inspection
the track's verify block will print — heard and checked BEFORE
clearance.py exists.  Notes: clearance_notes.md, "The probes" (which
probe decides which open question).

    python3 clearance_probe.py                 # all, to /workspace/music/ebm/clearance_probe/
    python3 clearance_probe.py --only 01,02    # a subset
    python3 clearance_probe.py --bpm 140       # the same set a notch slower (files suffixed _140)

Raw: mono, no master; the refrain probes carry a 0.25 reverb so the
voice is judged as it will sit.  Seed 18.  A/B any pair with
    python3 ../../tools/ab.py A.wav B.wav --bpm 147 --bars 2
"""
from __future__ import annotations

import argparse
import pathlib
import sys

import numpy as np
import soundfile
from scipy import signal

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "instruments"))
import _common                                                            # noqa: E402

ap = argparse.ArgumentParser(description="Clearance probes — see the docstring")
ap.add_argument("--bpm", type=float, default=147.0)
ap.add_argument("--only", default="", help="comma-separated probe numbers, e.g. 01,07")
ap.add_argument("--out", default="/workspace/music/ebm/clearance_probe")
ARGS = ap.parse_args()
_common.set_tempo(ARGS.bpm)                     # BEFORE the instrument imports (they bind the grid)
_common.seed(18)
from _common import BAR, BEAT, SR, STEP, midi_to_hz, norm, place, steps_buffer, write_wav  # noqa: E402
from bark import bark, chant                                              # noqa: E402
from dark_lead import dark_lead                                           # noqa: E402
from eps_hit import hit                                                   # noqa: E402
from eps_kick import kick                                                 # noqa: E402
from eps_snare import snare                                               # noqa: E402
from hats import hat                                                      # noqa: E402
from juno import noise_sweep, pad, stab                                   # noqa: E402
from machine import machine, retrigger                                    # noqa: E402
from seethe import seethe                                                 # noqa: E402
from sh101_bass import CELLS, render_cell                                 # noqa: E402

# ------------------------------------------------------------- the material
CS3, A2, GS2 = 49, 45, 44
CSM, A_, GSM = (56, 61, 64), (57, 61, 64), (56, 59, 63)      # C#m, A, G#m — close voicings, shared tones
CLUSTER = (56, 61, 62)                                        # G#3 C#4 D4: the flat-2 cluster (verses)
HIT_CHORD = (49, 56, 61, 64)
CHORUS_LOOP = [CSM, CSM, A_, GSM, CSM, CSM, A_, CSM]          # i i VI v | i i VI i
ROOT = {CSM: CS3, A_: A2, GSM: GS2}

KICK_FIG = {"A": "x...x...x...x...", "B": "x...x...x...x.x.", "C": "x..xx...x...x.x."}
SNARE_P = "....x.......x..."
RUN_P = "............xxxx"                                    # the machine-gun on beat 4, bars 4n+3
HAT_ACC = (1.0, 0.5, 0.7, 0.5)
OPEN_STEPS = (2, 6, 10, 14)

NOTE = {"G#2": 44, "A2": 45, "B2": 47, "C#3": 49, "D3": 50, "E3": 52, "F#3": 54, "G#3": 56, "A3": 57}
HOOK = ["C#3 C#3 C#3 - E3 - D3 -", "C#3 - . C#3 - - - -", "E3 - E3 E3 F#3 - E3 -", "G#2 - . G#2 - - - -",
        "C#3 C#3 C#3 - E3 - D3 -", "C#3 - - - . E3 F#3 G#3", "A3 - G#3 - F#3 - E3 -", "C#3 - - - - - . ."]

GAIN = {"kick": 1.0, "snare": 0.9, "ch": 0.28, "oh": 0.32, "bass": 0.75, "bed": 0.45, "pad": 0.22,
        "stab": 0.25, "hit": 0.7, "bark": 0.5, "lead": 0.6, "voice": 0.7, "riser": 0.3}


def figure_for(b):
    return "C" if b % 4 == 3 else ("B" if b % 2 else "A")


def mix(buf, x, bar=0, gain=1.0):
    i0 = int(round(bar * BAR * SR))
    n = min(len(x), len(buf) - i0)
    if n > 0:
        buf[i0:i0 + n] += gain * x[:n]


# ---------------------------------------------------------------- parts
def drums(bars, kick_kw=None, figures=True, runs=True, open_from=None, roll_into=None):
    """Kick / slam / hats for `bars` bars; the 2-bar roll (8ths -> 16ths ->
    32nds) replaces the backbeat in the two bars before `roll_into`."""
    K, S, CH, OH = kick(**(kick_kw or {})), snare(), hat(), hat(open_=True)
    buf = steps_buffer(bars)
    for b in range(bars):
        fig = KICK_FIG[figure_for(b) if figures else "A"]
        rolling = roll_into is not None and roll_into - 2 <= b < roll_into
        for s in range(16):
            st = b * 16 + s
            if fig[s] == "x":
                place(buf, K, st, GAIN["kick"])
            if not rolling and SNARE_P[s] == "x":
                place(buf, S, st, GAIN["snare"])
            elif not rolling and runs and b % 4 == 3 and RUN_P[s] == "x":
                place(buf, S, st, 0.6 * GAIN["snare"])
            if open_from is not None and b >= open_from and s in OPEN_STEPS:
                place(buf, OH, st, GAIN["oh"])
            else:
                place(buf, CH, st, GAIN["ch"] * HAT_ACC[s % 4])
        if rolling:
            first = b == roll_into - 2
            steps = np.arange(0, 16, 2) if first else np.concatenate([np.arange(0, 8, 1), np.arange(8, 16, 0.5)])
            for i, s in enumerate(steps):
                g = (0.4 + 0.25 * i / len(steps)) if first else (0.65 + 0.35 * i / len(steps))
                place(buf, S, b * 16 + s, g * GAIN["snare"])
    return buf, {"kick": K, "snare": S, "ch": CH, "oh": OH}


def bassline(bars, cell, roots, **kw):
    """`roots`: one midi or one per bar; the cell rendered bar by bar."""
    roots = [roots] * bars if isinstance(roots, int) else roots
    buf = steps_buffer(bars)
    for b, r in enumerate(roots):
        mix(buf, render_cell(cell, root=r, bars=1, **kw), b)
    return buf


def pads(chords, bars_each=1, **kw):
    buf = steps_buffer(len(chords) * bars_each)
    for i, ch in enumerate(chords):
        mix(buf, pad(ch, bars_each * BAR, depth=0.0, **kw), i * bars_each)
    return buf


def stabs(chords):
    buf = steps_buffer(len(chords))
    for b, ch in enumerate(chords):
        x = stab(ch)
        for s in OPEN_STEPS:
            place(buf, x, b * 16 + s)
    return buf


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


def refrain(chest=0.8):
    buf = steps_buffer(8, tail=1.5)
    for start, midi, ln in parse(HOOK):
        _common.add_at(buf, dark_lead(midi, ln * BEAT / 2 * 0.95, chest), start * BEAT / 2)
    return buf


def reverb(x, wet=0.25, seconds=2.5, decay=1.0):
    r = np.random.default_rng(7)
    n = int(seconds * SR)
    ir = r.standard_normal(n) * np.exp(-np.arange(n) / SR / decay)
    ir = signal.sosfilt(signal.butter(2, 4000, "low", fs=SR, output="sos"), ir)
    ir /= np.sqrt(np.sum(ir ** 2))
    w = signal.fftconvolve(x, ir)[: len(x)]
    w *= (np.max(np.abs(x)) + 1e-12) / (np.max(np.abs(w)) + 1e-12)
    return (1 - wet) * x + wet * w


def bed(bars, throb=0.4):
    return seethe(CS3, bars * BAR + 0.5, throb=throb, grit=0.3)


def sparse_barks(bars, every=2):
    buf = steps_buffer(bars)
    for i, b in enumerate(range(0, bars, every)):
        x = bark(CS3, dur=0.25, vowel="u" if i % 2 == 0 else "a", onset="d" if i % 2 == 0 else "k", fall=4.0)
        place(buf, x, b * 16)
    return buf


def stand_in_voice(seconds=1.2):
    """The demucs vocal stem in /workspace/music/vocaltest/ — a real voice
    to prove the chain on.  Never in the track.  None if absent."""
    path = pathlib.Path("/workspace/music/vocaltest/00_source.wav")
    if not path.exists():
        return None
    x, sr = soundfile.read(str(path))
    x = x.mean(axis=1) if x.ndim > 1 else x
    if sr != SR:
        x = signal.resample(x, int(len(x) * SR / sr))
    n, hop = int(seconds * SR), int(0.1 * SR)
    rms = [np.sqrt(np.mean(x[i:i + n] ** 2)) for i in range(0, len(x) - n, hop)]
    i0 = int(np.argmax(rms)) * hop
    y = x[i0:i0 + n]
    fade = int(0.02 * SR)
    y[:fade] *= np.linspace(0, 1, fade)
    y[-fade:] *= np.linspace(1, 0, fade)
    return norm(y)


# ----------------------------------------------------------- inspection
FAILS = []


def check(name, ok, detail=""):
    print(f"    [{'PASS' if ok else 'FAIL'}] {name}  {detail}")
    if not ok:
        FAILS.append(name)


def stats(x, bars):
    y = norm(x)
    rms = float(np.sqrt(np.mean(y ** 2)))
    X = np.abs(np.fft.rfft(y)) ** 2
    f = np.fft.rfftfreq(len(y), 1 / SR)
    print(f"    {len(y) / SR:.1f} s ({bars} bars)  RMS {20 * np.log10(rms):.1f} dBFS  crest {1 / rms:.1f}  "
          f"sub-60 share {X[f < 60].sum() / X.sum():.2f}")


def bass_report(cell, name, gate_frac=0.5):
    onsets = [i for i, ch in enumerate(cell) if ch != "."]
    gaps = [b - a for a, b in zip(onsets, onsets[1:] + [onsets[0] + 16])]
    kick_steps = [i for i, ch in enumerate(KICK_FIG["A"]) if ch == "x"]
    print(f"    bass cell {name}: {cell}  onsets/bar {len(onsets)}  shortest note {min(gaps) * STEP * gate_frac * 1000:.0f} ms"
          f"  gate duty {gate_frac:.2f} (each note {gate_frac:g} of its gap)")
    check("gate duty <= 0.5", gate_frac <= 0.5)
    if name == "offbeat":
        check("offbeat: bass never on a kick 16th", not any(cell[s] != "." for s in kick_steps))


def drums_report(hits, cuts):
    for fig, p in KICK_FIG.items():
        check(f"figure {fig}: kick on every quarter", all(p[s] == "x" for s in (0, 4, 8, 12)), p)
    check("snare on 2 and 4 only", [i for i, c in enumerate(SNARE_P) if c == "x"] == [4, 12])
    for k in ("kick", "snare"):
        x = hits[k]
        sounding = (int(np.max(np.nonzero(np.abs(x) > 1e-3))) + 1) / SR
        check(f"{k} truncated at its cut", sounding <= cuts[k] + 0.012, f"(sounding {sounding * 1000:.0f} ms, cut {cuts[k] * 1000:.0f} ms)")


def refrain_report():
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
    print(f"    onsets {onsets}  density {density:.2f} (0.20-0.50)  held {held:.2f} (>= 0.5)  longest 8th run {best} (<= 4)"
          f"  {onsets / (8 * BAR):.1f} notes/s")
    print(f"    DARK: register {min(midis)}-{max(midis)} (median {int(np.median(midis))}; floor G#2=44, ceiling A3=57)"
          f"  down-steps {downs:.2f} (>= 0.5)  max upward leap {max(steps)} st (<= 5)  flat-2nd onsets {flat2} (>= 2)")
    check("density window 0.20-0.50", 0.20 <= density <= 0.50)
    check("held fraction >= 0.5", held >= 0.5)
    check("run ceiling <= 4", best <= 4)
    check("phrase ends held >= a half note", q_end[2] >= 4 and a_end[2] >= 4)
    check("Q hangs on a G#, A lands on a C#", q_end[1] % 12 == 8 and a_end[1] % 12 == 1)
    check("register G#2..A3", min(midis) >= 44 and max(midis) <= 57)
    check("descending contour: down-steps >= 0.5", downs >= 0.5)
    check("no soaring leap: max upward <= 5 st", max(steps) <= 5)
    check("the flat 2nd colours the refrain", flat2 >= 2)


def bed_report(x):
    w2 = int(2.0 * SR)
    peaks = []
    for i in range(0, len(x) - w2, w2):
        seg = x[i:i + w2] * np.hanning(w2)
        X = np.abs(np.fft.rfft(seg))
        f = np.fft.rfftfreq(w2, 1 / SR)
        m = f > 20
        peaks.append(float(f[m][np.argmax(X[m])]))
    check("bed's strongest peak < 120 Hz in every 2 s window", max(peaks) < 120, f"(max {max(peaks):.0f} Hz)")


def timeline(*events):
    for bar, what in events:
        print(f"    {bar * BAR:6.2f}s  bar {bar:2d}  {what}")


# ---------------------------------------------------------------- probes
def engine(bars, cell, root, kick_kw=None, open_from=None, roll_into=None, runs=True):
    d, hits = drums(bars, kick_kw=kick_kw, open_from=open_from, roll_into=roll_into, runs=runs)
    b = bassline(bars, CELLS[cell], root)
    buf = d + GAIN["bass"] * b[: len(d)]
    return buf, hits


def p01():
    x, _ = engine(4, "gallop", CS3)
    bass_report(CELLS["gallop"], "gallop")
    return x, 4


def p02():
    x, _ = engine(4, "stomp", CS3)
    bass_report(CELLS["stomp"], "stomp")
    return x, 4


def p03():
    x, _ = engine(4, "gallop", A2)
    print(f"    root A2: sub square at {midi_to_hz(A2) / 2:.0f} Hz (C#3's sits at {midi_to_hz(CS3) / 2:.0f} Hz)")
    return x, 4


def p04(kick_kw=None):
    d, hits = drums(8, kick_kw=kick_kw, open_from=4, roll_into=8)
    mix(d, noise_sweep(2 * BAR, 200.0, 6000.0, res=3.0), 6, GAIN["riser"])
    timeline((0, "figures A/B/C, closed 16ths"), (3, "snare run on beat 4"), (4, "open hats on the off-8ths"),
             (6, "the roll (8ths -> 16ths -> 32nds) + the riser"))
    drums_report(hits, {"kick": (kick_kw or {}).get("cut", 0.20), "snare": 0.14})
    return d, 8


def p05():
    return p04({"drive": 2.6, "cut": 0.12})


def p06():
    x, _ = engine(8, "gallop", CS3, runs=False)
    the_bed = bed(8)
    mix(x, the_bed, 0, GAIN["bed"])
    mix(x, pads([CLUSTER] * 4, bars_each=2, cutoff=600.0), 0, GAIN["pad"])
    mix(x, sparse_barks(8), 0, GAIN["bark"])
    timeline((0, "engine (gallop) + bed (throb 0.4) + the flat-2 cluster pad"), (0, "barks UH / KAH every 2 bars"))
    bed_report(the_bed)
    return x, 8


def p07():
    x, _ = engine(8, "rolling", [ROOT[c] for c in CHORUS_LOOP], open_from=0, runs=False)
    mix(x, bed(8), 0, GAIN["bed"] * 0.7)
    mix(x, pads(CHORUS_LOOP), 0, GAIN["pad"])
    mix(x, stabs(CHORUS_LOOP), 0, GAIN["stab"])
    place(x, hit(HIT_CHORD), 0, GAIN["hit"])
    mix(x, reverb(refrain(chest=0.8)), 0, GAIN["lead"])
    timeline((0, "hit; rolling bass on the roots C#3 C#3 A2 G#2 | C#3 C#3 A2 C#3; pad i i VI v | i i VI i; stabs"),
             (0, "the refrain Q (bars 0-3), A (bars 4-7), chest 0.8"))
    bass_report(CELLS["rolling"], "rolling")
    refrain_report()
    return x, 8


def p08():
    return reverb(refrain(chest=0.8)), 8


def p09():
    v = stand_in_voice()
    if v is None:
        print("    no stand-in voice at /workspace/music/vocaltest/00_source.wav — probe skipped")
        return None, 0
    x, _ = engine(4, "stomp", CS3, runs=False)
    root_hz = midi_to_hz(CS3)
    variants = [("band + dirt", machine(v)), (f"+ ring mod at the root ({root_hz:.0f} Hz)", machine(v, ring_hz=root_hz)),
                ("+ retrigger x3 on 16ths", retrigger(machine(v, ring_hz=root_hz), STEP, 3))]
    for b, (label, y) in enumerate(variants):
        mix(x, y, b, GAIN["voice"])
        print(f"    {b * BAR:6.2f}s  bar {b:2d}  voice: {label}  ({len(y) / SR:.2f} s)")
    check("each variant fits inside its bar", all(len(y) / SR < BAR for _, y in variants))
    return x, 4


def p10():
    x = steps_buffer(8)
    mix(x, bed(8, throb=0.6), 0, GAIN["bed"] * 1.2)
    mix(x, pads([CLUSTER] * 4, bars_each=2, cutoff=500.0), 0, GAIN["pad"])
    mix(x, bassline(8, "x.x.x.x.x.x.x.x.", CS3, cutoff=(900.0, 250.0)), 0, GAIN["bass"] * 0.8)
    mix(x, chant("x...........l...", root=CS3, vowels="ou", bars=8, onset="d", fall=4.0), 0, GAIN["bark"] * 0.8)
    stutter = retrigger(bark(CS3, dur=0.3, vowel="a", vowel2="e", onset="k"), STEP, 3)
    place(x, stutter, 4 * 16, GAIN["bark"])
    timeline((0, "kick out: bed (throb 0.6) + cluster + the riff on dark 8ths + low barks"),
             (4, "the retrigger event (a bark stands in for NO ACCESS)"))
    bass_report("x.x.x.x.x.x.x.x.", "8ths dark")
    return x, 8


PROBES = [("01", "engine_gallop_cs3", p01), ("02", "engine_stomp_cs3", p02), ("03", "engine_gallop_a2", p03),
          ("04", "drums_jackhammer", p04), ("05", "drums_jackhammer_shortkick", p05), ("06", "brood_verse", p06),
          ("07", "refrain_chorus", p07), ("08", "refrain_solo", p08), ("09", "machine_voice", p09),
          ("10", "break_riff", p10)]

if __name__ == "__main__":
    only = {x.strip() for x in ARGS.only.split(",") if x.strip()}
    out_dir = pathlib.Path(ARGS.out)
    suffix = "" if ARGS.bpm == 147.0 else f"_{ARGS.bpm:g}"
    print(f"grid {ARGS.bpm:g} BPM: bar {BAR:.3f} s, 16th {STEP * 1000:.0f} ms;  C#3 = {midi_to_hz(CS3):.1f} Hz")
    for nn, name, fn in PROBES:
        if only and nn not in only:
            continue
        print(f"\n=== {nn} {name} ===")
        x, bars = fn()
        if x is None:
            continue
        assert np.all(np.isfinite(x)), name
        stats(x, bars)
        write_wav(out_dir / f"{nn}_{name}{suffix}.wav", x)
    print("\nall probe checks passed" if not FAILS else f"\nSOME PROBE CHECKS FAILED: {FAILS}")
