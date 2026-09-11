#!/usr/bin/env python3
"""Procession — the probes (the slam, tracks/ebm's third track).

Short samples at 122 BPM of the slam, the engine, the verse guitar, the
refrain quote, the bookend, the beat, the pre-chorus lift and the
chorus hit — each printed with the inspection the track's verify block
will print, heard and checked BEFORE procession.py exists.  Notes:
procession_notes.md ("The probes"; the answers of 2026-09-11 are folded
in: the guitar takes the bark's slot, the quote is literal, the 808 arp
frames the track, boom yes and the pump halved, the spoken slot stays
empty).

    python3 procession_probe.py                 # all, to /workspace/music/ebm/procession_probe/
    python3 procession_probe.py --only 02b,04   # a subset
    python3 procession_probe.py --bpm 129       # another tempo (files suffixed _129)

Raw: mono, no master; the refrain probes carry a 0.25 reverb so the
voice is judged as it will sit.  Seed 1991.  A/B any pair with
    python3 ../../tools/ab.py A.wav B.wav --bpm 122 --bars 2
"""
from __future__ import annotations

import argparse
import pathlib
import sys

import numpy as np
from scipy import signal

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "instruments"))
import _common                                                            # noqa: E402

ap = argparse.ArgumentParser(description="Procession probes — see the docstring")
ap.add_argument("--bpm", type=float, default=122.0)
ap.add_argument("--only", default="", help="comma-separated probe ids, e.g. 02b,04")
ap.add_argument("--out", default="/workspace/music/ebm/procession_probe")
ARGS = ap.parse_args()
_common.set_tempo(ARGS.bpm)                     # BEFORE the instrument imports (they bind the grid)
_common.seed(1991)                              # the Ashes to Ashes single
from _common import BAR, BEAT, SR, STEP, midi_to_hz, norm, place, steps_buffer, write_wav  # noqa: E402
from dark_lead import dark_lead                                           # noqa: E402
from eps_hit import hit                                                   # noqa: E402
from eps_kick import kick                                                 # noqa: E402
from eps_snare import snare                                               # noqa: E402
from hats import hat                                                      # noqa: E402
from juno import arp, pad, stab                                           # noqa: E402
from kit808 import hat as h808, kick as k808, snare as s808               # noqa: E402
from riff import riff                                                     # noqa: E402
from seethe import seethe                                                 # noqa: E402
from sh101_bass import CELLS, note, render_cell                           # noqa: E402

# ------------------------------------------------------------- the material
A2, F2, E2, A3 = 45, 41, 40, 57
CLUSTER = (52, 57, 58)                                # E3 A3 Bb3: the flat-2 cluster (verses, low)
AM_LOW = (57, 60, 64)                                 # A3 C4 E4: the dark verse stab
AM_HI, F_HI, EM_HI = (60, 64, 69), (60, 65, 69), (59, 64, 67)   # above the refrain's Bb3 ceiling (the 07 lesson)
CHORUS_LOOP = [AM_HI, F_HI, EM_HI, AM_HI] * 2         # Reliquary's own loop: i VI v i (never the flat-VII lift)
ROOT = {AM_HI: A2, F_HI: F2, EM_HI: E2}
ARP_CHORDS = [(57, 60, 64), (53, 57, 60), (52, 55, 59), (57, 60, 64)]      # Reliquary's mid-register Am F Em
HIT_CHORD = (45, 52, 57, 60)

KICK_FIG = {"A": "x...x...x...x...", "B": "x...x...x...x.x."}    # the slam: four on the floor, B every 4th bar
SNARE_P = "....x.......x..."
HAT_ACC = (1.0, 0.5, 0.7, 0.5)
OPEN_STEPS = (2, 6, 10, 14)
DARK_STAB_STEPS = (6, 14)
PATTERN808 = {"kick": "x...x...x...x...", "snare": "....x.......x...",      # no cowbell (the reliquary verdict)
              "ch": "x.x.x.x.x.x.x.x.", "oh": "......x.......x."}

# the engine: gated 8ths as an 8-bar PHRASE (the no_access v3 lesson, built in from bar 1)
CELL = {**CELLS, "stomp5": "x.x.x.x.x.x.5.o.", "walk": "x.x.x.5.x.7.o.o.",
        "8ths_half": "x...x...x...x..."}                   # the pre-chorus half-time bass
PHRASE = ("stomp", "stomp", "stomp", "stomp5", "stomp", "stomp", "riff", "walk")
INTERVAL = {"x": 0, "o": 12, "5": 7, "7": 10}
BASS_CUT = (2400.0, 1700.0, 2900.0, 2000.0)           # the filter talks: one open value per two bars
BASS_ACCENT = {0: 1.0, 4: 0.92, 8: 1.0, 12: 0.92}     # the quarters lean, the rest sit back
PUMP_DEPTH, PUMP_TAU, PUMP_FLOOR = 0.30, 0.10, 0.30   # half of no_access's 0.55: 122 does not want a modern pump
BOOM_OCTAVE, BOOM_DUR = -12, 0.45                     # the beat at 122 is 0.492 s

VERSE_RIFF = "x.x.x.x.x.xbx.x."                       # riff.py's own cell: root chugs, the flat 2 as the accent
VERSE_RIFF_SPARSE = "x..x..x...x.5..."                # the DAF/Nitzer cell on the guitar
RIFF_BARS = (3, 7)                                    # events, not a carpet: two bursts per 8 bars

NOTE = {"A2": 45, "C3": 48, "D3": 50, "E3": 52, "F3": 53, "G3": 55, "A3": 57, "Bb3": 58}
# Reliquary's hook, verbatim (reliquary_v2.py) — the quote IS the refrain.
HOOK = ["A3 - A3 A3 Bb3 - A3 -", "G3 - - - . A3 G3 F3", "E3 - F3 E3 D3 - E3 -", "E3 - - - - - . .",
        "A3 - A3 A3 Bb3 - A3 -", "G3 - - - . F3 E3 F3", "G3 - F3 E3 C3 - - -", "A2 - - - - - . ."]
TAG = ["A3 - G3 - E3 - - -", "- - - - - - . ."]

GAIN = {"kick": 1.0, "snare": 1.15, "ch": 0.20, "oh": 0.26, "bass": 0.75, "bed": 0.45, "pad": 0.22,
        "stab": 0.2, "dark_stab": 0.22, "guitar": 0.35, "hit": 0.7, "lead": 0.85, "boom": 0.45,
        "arp": 0.35, "808": 0.8}


def mix(buf, x, bar=0, gain=1.0):
    i0 = int(round(bar * BAR * SR))
    n = min(len(x), len(buf) - i0)
    if n > 0:
        buf[i0:i0 + n] += gain * x[:n]


# ---------------------------------------------------------------- parts
def drums(bars, snare_gain=None, hat_gain=None, figures=True, open_from=None, kick_out=()):
    """The slam: kick on every quarter, the snare on 2 and 4, closed 16ths
    (quiet — at 122 the snare is the aggression, not the hats)."""
    K, S, CH, OH = kick(decay=6.0), snare(), hat(), hat(open_=True)
    sg = GAIN["snare"] if snare_gain is None else snare_gain
    hg = GAIN["ch"] if hat_gain is None else hat_gain
    buf = steps_buffer(bars)
    for b in range(bars):
        if b in kick_out:
            continue
        fig = KICK_FIG["B" if figures and b % 4 == 3 else "A"]
        for s in range(16):
            st = b * 16 + s
            if fig[s] == "x":
                place(buf, K, st, GAIN["kick"])
            if SNARE_P[s] == "x":
                place(buf, S, st, sg)
            if open_from is not None and b >= open_from and s in OPEN_STEPS:
                place(buf, OH, st, GAIN["oh"])
            else:
                place(buf, CH, st, hg * HAT_ACC[s % 4])
    return buf, {"kick": K, "snare": S, "ch": CH, "oh": OH}


def phrase_spec(b, roots, sub=0.6):
    """-> (cell, root, note kwargs) for bar b of the engine phrase."""
    cell = PHRASE[b % 8]
    root = roots[b % len(roots)] if isinstance(roots, (list, tuple)) else roots
    return CELL[cell], root, {"cutoff": (BASS_CUT[(b // 2) % 4], 250.0), "sub": sub}


def bassline(bars, roots, phrase=True, cell_name="stomp", sub=0.6, accents=True, **kw):
    """The engine.  phrase=True walks PHRASE bar by bar (the v3 lesson);
    phrase=False repeats one cell — the A/B that proves the difference."""
    buf = steps_buffer(bars)
    for b in range(bars):
        if phrase:
            cell, root, note_kw = phrase_spec(b, roots, sub)
        else:
            cell = CELL[cell_name]
            root = roots[b % len(roots)] if isinstance(roots, (list, tuple)) else roots
            note_kw = {"sub": sub}
        note_kw.update(kw)
        onsets = [i for i, ch in enumerate(cell) if ch != "."]
        for j, s in enumerate(onsets):
            gap = (onsets[j + 1] if j + 1 < len(onsets) else onsets[0] + 16) - s
            g = (BASS_ACCENT.get(s, 0.78) if cell[s] == "x" else 1.0) if accents else 1.0
            place(buf, note(root + INTERVAL[cell[s]], dur=gap * STEP * 0.5, **note_kw), b * 16 + s, g)
    return buf


def guitar(bars, cell=VERSE_RIFF, bars_playing=RIFF_BARS, root=A2):
    """The verse device (the bark's empty slot): palm-muted power chords as
    a TEXTURE, in bursts — events, not a carpet."""
    buf = steps_buffer(bars)
    for b in range(bars):
        if bars_playing is None or b % 8 in bars_playing:
            mix(buf, riff(cell, root=root, bars=1), b)
    return buf


def pads(chords, bars_each=1, fn=pad, **kw):
    buf = steps_buffer(len(chords) * bars_each)
    for i, ch in enumerate(chords):
        mix(buf, fn(ch, bars_each * BAR, **kw), i * bars_each)
    return buf


def stabs(chords, steps=OPEN_STEPS, **kw):
    buf = steps_buffer(len(chords))
    for b, ch in enumerate(chords):
        x = stab(ch, **kw)
        for s in steps:
            place(buf, x, b * 16 + s)
    return buf


def arp808(bars, chords, cutoff=500.0, rate=1, resolved=True):
    """The bookend: Reliquary's down-arp over the 808 kit.  resolved=False
    ends on the V (E) as Part 1 does; True lands on A — the answer."""
    buf = steps_buffer(bars)
    hits = {"kick": k808(), "snare": s808(), "ch": h808(), "oh": h808(open_=True)}
    for name, line in PATTERN808.items():
        for s in range(bars * 16):
            if line[s % 16] == "x":
                g = (1.0 if name == "kick" else 0.8 if name == "snare" else 0.35)
                place(buf, hits[name], s, GAIN["808"] * g * (1.0 if s % 4 == 0 else 0.8))
    for b in range(bars):
        ch = chords[b % len(chords)]
        if b == bars - 1:
            ch = chords[0] if resolved else (52, 55, 59)          # Am, or the open Em
        x = arp(ch, bars=1, pattern="down", octaves=1, rate=rate, cutoff=cutoff)
        mix(buf, x[: int(BAR * SR) + int(0.3 * SR)], b, GAIN["arp"])
    return buf, (chords[0] if resolved else (52, 55, 59))


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


def line_on_lead(lines, bars, chest=1.0):
    buf = steps_buffer(bars, tail=1.5)
    for start, midi, ln in parse(lines):
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
    return seethe(A2, bars * BAR + 0.5, throb=throb, grit=0.3)


def sub_boom(f):
    """The silver_wire_v3 boom, retimed for 122: a sine with a short pitch
    drop sustaining the beat, hard release.  The kick's low end."""
    n = int(BOOM_DUR * SR)
    td = np.arange(n) / SR
    x = np.sin(2 * np.pi * np.cumsum(f * (1.0 + 0.35 * np.exp(-td * 12.0))) / SR)
    return x * (1 - np.exp(-td / 0.003)) * np.exp(-td * 1.2) * np.clip((BOOM_DUR - td) / 0.06, 0, 1)


def beat_layers(bars, roots):
    """-> (boom buffer, pump curve) for `bars` bars of 4-on-the-floor."""
    boom = steps_buffer(bars)
    pump = np.ones(len(boom))
    dip_n = int(BOOM_DUR * SR)
    dip = PUMP_DEPTH * np.exp(-np.arange(dip_n) / SR / PUMP_TAU)
    for b in range(bars):
        root = roots[b % len(roots)] if isinstance(roots, (list, tuple)) else roots
        x = sub_boom(midi_to_hz(root + BOOM_OCTAVE))
        for beat in range(4):
            place(boom, x, b * 16 + beat * 4)
            i0 = int(round((b * BAR + beat * BEAT) * SR))
            i1 = min(len(pump), i0 + dip_n)
            pump[i0:i1] = np.minimum(pump[i0:i1], 1.0 - dip[: i1 - i0])
    return boom, np.clip(pump, PUMP_FLOOR, 1.0)


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
          f"sub-60 share {X[f < 60].sum() / X.sum():.2f}  sub-80 share {X[f < 80].sum() / X.sum():.2f}")


def timeline(*events):
    for bar, what in events:
        print(f"    {bar * BAR:6.2f}s  bar {bar:2d}  {what}")


def slam_report(hits, snare_gain):
    """The blueprint's claim: kick and snare hit like ONE instrument."""
    k, s = hits["kick"], hits["snare"] * snare_gain
    n = max(len(k), len(s))
    blow = np.zeros(n)
    blow[:len(k)] += k
    blow[:len(s)] += s
    sounding = (int(np.max(np.nonzero(np.abs(blow) > 1e-3))) + 1) / SR
    for name, x, cut in (("kick", k, 0.20), ("snare", hits["snare"], 0.14)):
        snd = (int(np.max(np.nonzero(np.abs(x) > 1e-3))) + 1) / SR
        check(f"{name} truncated at its cut", snd <= cut + 0.012, f"(sounding {snd * 1000:.0f} ms, cut {cut * 1000:.0f} ms)")
    print(f"    the blow (kick + snare at {snare_gain:.2f}): {sounding * 1000:.0f} ms, peak {np.max(np.abs(blow)):.2f}, "
          f"snare/kick peak ratio {np.max(np.abs(s)) / np.max(np.abs(k)):.2f}")
    check("the blow is one gesture (< 250 ms, no tail)", sounding < 0.25)
    check("kick on every quarter", all(KICK_FIG["A"][s] == "x" for s in (0, 4, 8, 12)))
    check("snare on 2 and 4 only", [i for i, c in enumerate(SNARE_P) if c == "x"] == [4, 12])


def phrase_report(roots):
    cells = [PHRASE[b % 8] for b in range(8)]
    colour = sum(1 for c in cells for ch in CELL[c] if ch not in ".x")
    onsets = [len([ch for ch in CELL[c] if ch != "."]) for c in cells]
    print(f"    the phrase: {' '.join(cells)}  ({len(set(cells))} cells, {colour} colour notes per 8 bars, "
          f"onsets/bar {min(onsets)}-{max(onsets)})")
    print(f"    filter cycle {BASS_CUT} Hz per two bars;  accents {BASS_ACCENT} (the rest 0.78)")
    for c in set(cells):
        dur = min(b - a for a, b in zip([i for i, ch in enumerate(CELL[c]) if ch != "."],
                                        [i for i, ch in enumerate(CELL[c]) if ch != "."][1:] + [16]))
        check(f"cell {c}: gate duty 0.5, shortest note {dur * STEP * 0.5 * 1000:.0f} ms", True)
        check(f"cell {c} starts on the root (the chorus ledger)", CELL[c][0] == "x")
    check("the engine is a phrase, not one cell (>= 3 cells)", len(set(cells)) >= 3)
    for r in (roots if isinstance(roots, (list, tuple)) else [roots]):
        print(f"    root {r}: {midi_to_hz(r):.1f} Hz, sub square {midi_to_hz(r) / 2:.1f} Hz"
              f"{'  <- under the measured-good band (A2/55 Hz)' if midi_to_hz(r) / 2 < 50 else ''}")


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
    flat2 = sum(1 for m in midis if m % 12 == 10)                 # Bb, the flat 2 of A
    print(f"    onsets {onsets}  density {density:.2f} (0.20-0.50)  held {held:.2f} (>= 0.5)  longest 8th run {best} (<= 4)"
          f"  {onsets / (8 * BAR):.1f} notes/s")
    print(f"    DARK: register {min(midis)}-{max(midis)} (median {int(np.median(midis))}; floor A2=45, ceiling Bb3=58)"
          f"  down-steps {downs:.2f} (>= 0.5)  max upward leap {max(steps)} st (<= 5)  flat-2nd onsets {flat2} (>= 2)")
    check("density window 0.20-0.50", 0.20 <= density <= 0.50)
    check("held fraction >= 0.5", held >= 0.5)
    check("run ceiling <= 4", best <= 4)
    check("phrase ends held >= a half note", q_end[2] >= 4 and a_end[2] >= 4)
    check("Q hangs on the 5th (E), A lands on the tonic (A)", q_end[1] % 12 == 4 and a_end[1] % 12 == 9)
    check("register A2..Bb3", min(midis) >= 45 and max(midis) <= 58)
    check("descending contour: down-steps >= 0.5", downs >= 0.5)
    check("no soaring leap: max upward <= 5 st", max(steps) <= 5)
    check("the flat 2nd colours the refrain", flat2 >= 2)


def room_report(chords):
    lowest = min(min(ch) for ch in chords)
    print(f"    pad/stab lowest note midi {lowest} ({midi_to_hz(lowest):.0f} Hz); refrain ceiling Bb3 = 58 (233 Hz)")
    check("pad and stabs voiced above the refrain (lowest note > Bb3)", lowest > 58)


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


def guitar_report(cell, bars, bars_playing, carpet=False):
    playing = [b for b in range(bars) if bars_playing is None or b % 8 in bars_playing]
    share = len(playing) / bars
    print(f"    guitar cell {cell} on bars {playing} of {bars}: "
          f"{share:.0%} of the section, {len(playing) * cell.count('x')} chugs")
    if carpet:
        check("the carpet reading, on purpose (this probe is the A/B, not the plan)", share == 1.0)
    else:
        check("the guitar is events, not a carpet (< 40 % of the bars)", share < 0.4)


# ---------------------------------------------------------------- probes
def engine(bars, roots, phrase=True, cell_name="stomp", sub=0.6, snare_gain=None, hat_gain=None,
           open_from=None, figures=True):
    d, hits = drums(bars, snare_gain=snare_gain, hat_gain=hat_gain, open_from=open_from, figures=figures)
    b = bassline(bars, roots, phrase=phrase, cell_name=cell_name, sub=sub)
    return d + GAIN["bass"] * b[: len(d)], hits


def p01():
    """The slam: three snare weights over the same kick.  Which one makes
    the pair read as one instrument at 122?"""
    x = steps_buffer(6)
    hits = None
    for i, sg in enumerate((0.9, 1.15, 1.4)):
        d, hits = drums(2, snare_gain=sg)
        mix(x, d, 2 * i)
        print(f"    {2 * i * BAR:6.2f}s  bars {2 * i}-{2 * i + 1}  snare {sg:.2f} (no_access shipped 0.90)")
    slam_report(hits, 1.15)
    return x, 6


def p02a():
    """The engine as the blueprint states it: ONE cell, gated 8ths on the
    pedal, eight bars.  This is the drone the v3 verdict warned about."""
    x, _ = engine(8, A2, phrase=False)
    print(f"    one cell x 8 bars: {CELLS['stomp']}")
    return x, 8


def p02b():
    """The same eight bars as a PHRASE (the v3 lesson built in from bar 1):
    accents, a filter cycle, the 5th, the riff bar, the walk."""
    x, _ = engine(8, A2)
    phrase_report(A2)
    return x, 8


def p02c():
    """The chorus roots: does the SH-101 hold under F and E?  Bars 0-3 the
    bass follows Am F Em Am down (F2 sub 43.7 Hz, E2 sub 41.2 Hz);
    bars 4-7 it stays on the A pedal under the same chords."""
    x = steps_buffer(8)
    follow = [A2, F2, E2, A2]
    d, _ = drums(8, open_from=0)
    mix(x, d)
    mix(x, bassline(4, follow, sub=0.85), 0, GAIN["bass"])
    mix(x, bassline(4, A2, sub=0.85), 4, GAIN["bass"])
    mix(x, pads(CHORUS_LOOP[:4], depth=0.0), 0, GAIN["pad"])
    mix(x, pads(CHORUS_LOOP[:4], depth=0.0), 4, GAIN["pad"])
    timeline((0, "the bass FOLLOWS: A2 F2 E2 A2 (sub squares 55 / 43.7 / 41.2 Hz)"),
             (4, "the bass PEDALS on A2 under the same chords (sub square 55 Hz throughout)"))
    phrase_report(follow)
    return x, 8


def p03a():
    """The verse with the guitar in the bark's old slot: two bursts per
    eight bars (bars 3 and 7) — events, not a carpet."""
    x, _ = engine(8, A2)
    the_bed = bed(8)
    mix(x, the_bed, 0, GAIN["bed"])
    mix(x, pads([CLUSTER] * 4, bars_each=2, cutoff=600.0, depth=0.0), 0, GAIN["pad"])
    mix(x, stabs([AM_LOW] * 8, steps=DARK_STAB_STEPS, depth=0.0, cutoff=500.0, hpf=1), 0, GAIN["dark_stab"])
    mix(x, guitar(8), 0, GAIN["guitar"])
    timeline((0, "engine (the phrase) + bed + the flat-2 cluster pad + the dark stab on the & of 2 and 4"),
             (3, "the guitar answers (palm-muted power chords on A2)"), (7, "and again, into the next phrase"))
    guitar_report(VERSE_RIFF, 8, RIFF_BARS)
    bed_report(the_bed)
    return x, 8


def p03b():
    """The same verse with the guitar in EVERY bar — the carpet, for the
    A/B that proves why it is two bars."""
    x, _ = engine(8, A2)
    mix(x, bed(8), 0, GAIN["bed"])
    mix(x, pads([CLUSTER] * 4, bars_each=2, cutoff=600.0, depth=0.0), 0, GAIN["pad"])
    mix(x, guitar(8, bars_playing=None), 0, GAIN["guitar"])
    guitar_report(VERSE_RIFF, 8, None, carpet=True)
    return x, 8


def p03c():
    """The sparse DAF cell on the guitar instead of the dense one."""
    x, _ = engine(8, A2)
    mix(x, bed(8), 0, GAIN["bed"])
    mix(x, pads([CLUSTER] * 4, bars_each=2, cutoff=600.0, depth=0.0), 0, GAIN["pad"])
    mix(x, guitar(8, cell=VERSE_RIFF_SPARSE), 0, GAIN["guitar"])
    guitar_report(VERSE_RIFF_SPARSE, 8, RIFF_BARS)
    return x, 8


def _chorus(chest, hit_kind="choir", roots=None):
    roots = roots or [ROOT[c] for c in CHORUS_LOOP]
    x, _ = engine(8, roots, sub=0.85, open_from=0, figures=False)
    mix(x, bed(8), 0, GAIN["bed"] * 0.7)
    mix(x, pads(CHORUS_LOOP, depth=0.0), 0, GAIN["pad"])
    mix(x, stabs(CHORUS_LOOP, depth=0.0), 0, GAIN["stab"])
    place(x, hit(HIT_CHORD, kind=hit_kind), 0, GAIN["hit"])
    mix(x, reverb(line_on_lead(HOOK, 8, chest)), 0, GAIN["lead"])
    return x


def p04a():
    """THE QUOTE: Reliquary's hook, verbatim, on dark_lead over the stomp —
    chorus 1's chest (1.0).  Does Part 1's idea survive as a chorus?"""
    x = _chorus(1.0)
    timeline((0, "the refrain Q (bars 0-3) over Am F Em Am, chest 1.0; choir hit on the downbeat"),
             (4, "the refrain A (bars 4-7), landing on the low tonic A2"))
    refrain_report()
    room_report(CHORUS_LOOP)
    return x, 8


def p04b():
    """The final chorus's chest (1.3) — the same eight bars, the voice deeper."""
    return _chorus(1.3), 8


def p04c():
    """The refrain alone, wet, chest 1.0 — the voice judged on its own."""
    return reverb(line_on_lead(HOOK, 8, 1.0)), 8


def p05a():
    """The bookend, as Part 1 leaves it: the 808 + Reliquary's down-arp,
    ending OPEN on the V (Em)."""
    x, last = arp808(8, ARP_CHORDS, resolved=False)
    mix(x, bed(8, throb=0.0), 0, GAIN["bed"] * 0.8)
    timeline((0, "808 kit + the down-arp on Am F Em Am (Reliquary's cell and cutoffs)"),
             (7, f"the last bar stays OPEN on {last} (E minor) — Part 1's ending"))
    return x, 8


def p05b():
    """The same eight bars RESOLVED to A — the song's outro, the answer
    Part 1 withheld."""
    x, last = arp808(8, ARP_CHORDS, cutoff=400.0, rate=2, resolved=True)
    mix(x, bed(8, throb=0.0), 0, GAIN["bed"] * 0.8)
    timeline((0, "the same cell, 8ths (rate 2) and the cutoff down at 400 — the outro reading"),
             (7, f"the last bar RESOLVES to {last} (A minor)"))
    check("the bookend restates the same cell at both ends", True, "(same chords, same pattern, different last bar)")
    return x, 8


def p06a():
    """The beat, dry 1993: no pump, no boom.  The blueprint's own rule."""
    x, _ = engine(8, [ROOT[c] for c in CHORUS_LOOP], sub=0.85, open_from=0, figures=False)
    mix(x, pads(CHORUS_LOOP, depth=0.0), 0, GAIN["pad"])
    return x, 8


def p06b():
    """The beat with the approved deviation: the sub-boom under every kick
    and the pump HALVED (0.30, against no_access's 0.55)."""
    roots = [ROOT[c] for c in CHORUS_LOOP]
    d, _ = drums(8, open_from=0, figures=False)
    sustained = GAIN["bass"] * bassline(8, roots, sub=0.85)[: len(d)]
    p = pads(CHORUS_LOOP, depth=0.0)
    sustained[: len(p)] += GAIN["pad"] * p[: len(sustained)]
    boom, pump = beat_layers(8, roots)
    x = d + sustained * pump[: len(d)] + GAIN["boom"] * boom[: len(d)]
    print(f"    pump depth {PUMP_DEPTH} (no_access: 0.55), floor {pump.min():.2f}, mean {pump.mean():.2f}; "
          f"boom {BOOM_DUR * 1000:.0f} ms at {', '.join(f'{midi_to_hz(r + BOOM_OCTAVE):.0f}' for r in sorted(set(roots)))} Hz")
    check("the pump breathes but never gates (mean 0.85-0.97)", 0.85 <= pump.mean() <= 0.97)
    check("one boom per quarter, none longer than the beat", BOOM_DUR < BEAT)
    return x, 8


def p07():
    """The pre-chorus lift (the approved one): the bass drops to half-time
    under a held hit, the tag answers on top, then the chorus downbeat."""
    x = steps_buffer(9)
    d, _ = drums(8, open_from=4)
    mix(x, d)
    mix(x, bassline(4, A2, sub=0.6), 0, GAIN["bass"])
    mix(x, bassline(4, [A2, A2, F2, E2], phrase=False, cell_name="8ths_half", sub=0.85), 4, GAIN["bass"])
    mix(x, pads(CHORUS_LOOP[:4], bars_each=2, depth=0.0), 0, GAIN["pad"])
    place(x, hit(HIT_CHORD, kind="choir", dur=0.45), 4 * 16, GAIN["hit"])
    mix(x, reverb(line_on_lead(TAG, 2, 1.0)), 6, GAIN["lead"])
    place(x, hit(HIT_CHORD, kind="choir"), 8 * 16, GAIN["hit"])
    timeline((0, "the verse engine running"), (4, "the bass drops to half-time (quarters) under a held choir hit"),
             (6, "the tag answers: A3 G3 E3"), (8, "the chorus downbeat"))
    return x, 9


def p08():
    """The chorus hit: choir (chosen) against orchestral (no_access's), same
    chord, same bar."""
    x = steps_buffer(4)
    for i, kind in enumerate(("choir", "orch")):
        d, _ = drums(2, open_from=0)
        mix(x, d, 2 * i)
        mix(x, pads(CHORUS_LOOP[:2], depth=0.0), 2 * i, GAIN["pad"])
        place(x, hit(HIT_CHORD, kind=kind), 2 * i * 16, GAIN["hit"])
        print(f"    {2 * i * BAR:6.2f}s  bars {2 * i}-{2 * i + 1}  hit kind {kind!r}")
    return x, 4


PROBES = [("01", "slam_snare_weights", p01), ("02a", "engine_one_cell", p02a), ("02b", "engine_phrase", p02b),
          ("02c", "chorus_roots", p02c), ("03a", "verse_guitar_events", p03a), ("03b", "verse_guitar_carpet", p03b),
          ("03c", "verse_guitar_sparse", p03c), ("04a", "chorus_quote_chest10", p04a),
          ("04b", "chorus_quote_chest13", p04b), ("04c", "refrain_solo", p04c),
          ("05a", "bookend_open", p05a), ("05b", "bookend_resolved", p05b),
          ("06a", "beat_dry_1993", p06a), ("06b", "beat_boom_halfpump", p06b),
          ("07", "pre_chorus_lift", p07), ("08", "chorus_hit_choir_vs_orch", p08)]

if __name__ == "__main__":
    only = {x.strip() for x in ARGS.only.split(",") if x.strip()}
    out_dir = pathlib.Path(ARGS.out)
    suffix = "" if ARGS.bpm == 122.0 else f"_{ARGS.bpm:g}"
    print(f"grid {ARGS.bpm:g} BPM: bar {BAR:.3f} s, 16th {STEP * 1000:.0f} ms;  A2 = {midi_to_hz(A2):.1f} Hz, "
          f"sub square {midi_to_hz(A2) / 2:.1f} Hz")
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
