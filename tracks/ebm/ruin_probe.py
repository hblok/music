#!/usr/bin/env python3
"""Ruin — the probes (the hammer, tracks/ebm's fourth track).

Thirteen short samples at 109 BPM of the drone argument, the sub at F#,
the hats question, the chorus roots, the hammer snare, the space, the
petition, the final's kick and — after the toll was rejected — three
candidate openings — each printed with the
inspection the track's verify block will print, heard and checked
BEFORE ruin.py exists.  Notes: ruin_notes.md ("The probes").

The recommendations in the notes are the DEFAULT state here, and every
ladder keeps the alternative next to it, so answering the ten questions
later costs one re-render (the procession_probe.py pattern).

One refinement on the notes: the engine cell is `hammer`
("x.x.x.x.x.x.x.x."), not `CELLS["stomp"]`.  Stomp puts an octave on the
"and" of 4, which would be a pitch event, and this archetype's whole
claim is that the pitch never moves.  The notes are amended to match.

    python3 ruin_probe.py                   # all, to /workspace/music/ebm/ruin_probe/
    python3 ruin_probe.py --only 01a,01b    # a subset
    python3 ruin_probe.py --bpm 100         # another tempo (files suffixed _100)

Raw: mono, no master; the refrain probes carry a 0.25 reverb so the
voice is judged as it will sit.  Seed 2018.  A/B any pair with
    python3 ../../tools/ab.py A.wav B.wav --bpm 109 --bars 2
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

ap = argparse.ArgumentParser(description="Ruin probes — see the docstring")
ap.add_argument("--bpm", type=float, default=109.0)
ap.add_argument("--only", default="", help="comma-separated probe ids, e.g. 01a,04")
ap.add_argument("--out", default="/workspace/music/ebm/ruin_probe")
ARGS = ap.parse_args()
_common.set_tempo(ARGS.bpm)                     # BEFORE the instrument imports (they bind the grid)
_common.seed(2018)                              # the year the record was remastered from the tapes
from _common import BAR, BEAT, SR, STEP, midi_to_hz, norm, place, steps_buffer, write_wav  # noqa: E402
from dark_lead import dark_lead                                           # noqa: E402
from eps_hit import hit                                                   # noqa: E402
from eps_kick import kick                                                 # noqa: E402
from eps_snare import snare                                               # noqa: E402
from hats import hat                                                      # noqa: E402
from juno import noise_sweep, organ, pad                                  # noqa: E402
from seethe import seethe                                                 # noqa: E402
from sh101_bass import CELLS, note                                        # noqa: E402

# ------------------------------------------------------------- the material
FS2, D2, CS2, D3, CS3 = 42, 38, 37, 50, 49          # the roots: F#2 is home
NOTE = {"F#2": 42, "A2": 45, "C#3": 49, "D3": 50, "E3": 52, "F#3": 54, "G3": 55}

# the pads sit ABOVE the refrain's G3 ceiling (the no_access probe-07 lesson)
FSM_HI, D_HI, CSM_HI = (57, 61, 66), (57, 62, 66), (56, 61, 64)
LOOP = [FSM_HI, D_HI, CSM_HI, FSM_HI]               # F#m D C#m F#m: the minor v, never the flat-VII
ROOT_OF = {FSM_HI: FS2, D_HI: D2, CSM_HI: CS2}
HIT_CHORD = (42, 49, 54, 57)                        # F#2 C#3 F#3 A3
ORGAN_LOW = (42, 49, 54)

# the petition (bars 1-4) and its response (bars 5-8) — ruin_notes.md
HOOK = ["F#3 - F#3 F#3 G3 - F#3 -", "E3 - - - . F#3 E3 C#3", "D3 - C#3 D3 E3 - D3 -", "C#3 - - - - - . .",
        "F#3 - F#3 F#3 G3 - F#3 -", "E3 - - - . D3 C#3 D3", "E3 - D3 C#3 A2 - - -", "F#2 - - - - - . ."]
PETITION = HOOK[:4]

# the engine: the pitch NEVER moves; the phrase is in the filter, the gate and the accent
CELL = {**CELLS, "hammer": "x.x.x.x.x.x.x.x.", "walk": "x.x.x.5.x.7.o.o.",
        "half": "x...x...x...x...",                   # the pre-chorus half-time bass
        "hole": "x...x...x......."}                   # its last bar: the bass leaves the hole too
PHRASE = ("hammer",) * 7 + ("walk",)
CUTS = (2200.0, 2200.0, 1500.0, 1500.0, 2800.0, 2800.0, 1700.0, 2400.0)
GATES = (0.50, 0.50, 0.42, 0.42, 0.50, 0.50, 0.35, 0.50)
FLOORS = (0.72, 0.72, 0.72, 0.72, 0.60, 0.60, 0.78, 0.60)
ACCENT = {0: 1.0, 4: 0.92, 8: 1.0, 12: 0.92}          # the quarters lean
INTERVAL = {"x": 0, "o": 12, "5": 7, "7": 10}
SUB_VERSE, SUB_CHORUS = 0.6, 0.85                     # Q2's recommendation
PLATE_CUT = 0.22                                      # Q5: longer than procession's 140 ms — the blow rings
CHEST = (1.0, 1.15, 1.3)                              # chorus 1 / chorus 2 / the final
TOLL_DUR = 0.45                                       # Q6's recommendation, between the hit and a bell
SPACE_CEILING = 24                                    # onsets per verse bar: this track's claim is space

KICK_Q = "x...x...x...x..."                           # every quarter
KICK_8 = "x.x.x.x.x.x.x.x."                           # the final chorus only (Q7)
SNARE_P = "....x.......x..."
HAT_8 = (0, 2, 4, 6, 8, 10, 12, 14)
HAT_16 = tuple(range(16))
HAT_ACC = (1.0, 0.5, 0.7, 0.5)

GAIN = {"kick": 1.0, "snare": 1.15, "hat": 0.16, "bass": 0.75, "bed": 0.45,
        "pad": 0.22, "organ": 0.3, "hit": 0.7, "lead": 0.85}


def mix(buf, x, bar=0, gain=1.0):
    i0 = int(round(bar * BAR * SR))
    n = min(len(x), len(buf) - i0)
    if n > 0:
        buf[i0:i0 + n] += gain * x[:n]


# ---------------------------------------------------------------- parts
def drums(bars, kick_cell=KICK_Q, snare_gain=None, hat_steps=(), plate_cut=PLATE_CUT, kick_out=()):
    """The hammer: kick on every quarter, the slam on 2 and 4, and hats
    only if asked — at 109 the gap between blows is the material."""
    K, S, H = kick(decay=5.0), snare(plate_decay=3.0, cut=plate_cut), hat()
    sg = GAIN["snare"] if snare_gain is None else snare_gain
    buf = steps_buffer(bars)
    for b in range(bars):
        for s in range(16):
            st = b * 16 + s
            if kick_cell[s] == "x" and b not in kick_out:
                place(buf, K, st, GAIN["kick"])
            if SNARE_P[s] == "x":
                place(buf, S, st, sg)
            if s in hat_steps:
                place(buf, H, st, GAIN["hat"] * HAT_ACC[s % 4])
    return buf, {"kick": K, "snare": S}


def bassline(bars, roots, phrase=True, cell_name="hammer", sub=SUB_VERSE, accents=True,
             cycle=True, gate=None, **kw):
    """The engine.  phrase=True walks PHRASE with the filter/gate/accent
    cycle (the counter-measure); phrase=False repeats one cell flat — the
    A/B that is the whole argument of probe 01."""
    buf = steps_buffer(bars)
    for b in range(bars):
        i = b % 8
        cell = CELL[PHRASE[i] if phrase else cell_name]
        root = roots[b % len(roots)] if isinstance(roots, (list, tuple)) else roots
        cutoff = (CUTS[i] if cycle else 2200.0, 250.0)
        g_frac = gate if gate is not None else (GATES[i] if cycle else 0.5)
        floor = FLOORS[i] if accents else 1.0
        onsets = [j for j, ch in enumerate(cell) if ch != "."]
        for j, s in enumerate(onsets):
            gap = (onsets[j + 1] if j + 1 < len(onsets) else onsets[0] + 16) - s
            g = (ACCENT.get(s, floor) if cell[s] == "x" else 1.0) if accents else 1.0
            place(buf, note(root + INTERVAL[cell[s]], dur=gap * STEP * g_frac, sub=sub,
                            cutoff=cutoff, **kw), b * 16 + s, g)
    return buf


def pads(chords, bars_each=1, fn=pad, **kw):
    buf = steps_buffer(len(chords) * bars_each)
    for i, ch in enumerate(chords):
        mix(buf, fn(ch, bars_each * BAR, **kw), i * bars_each)
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


def line_on(lines, bars, chest=1.0, fn=None):
    buf = steps_buffer(bars, tail=1.5)
    for start, midi, ln in parse(lines):
        x = fn(midi, ln * BEAT / 2 * 0.95) if fn else dark_lead(midi, ln * BEAT / 2 * 0.95, chest)
        _common.add_at(buf, x, start * BEAT / 2)
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


def bed(bars, throb=0.35, sub=0.6):
    return seethe(FS2, bars * BAR + 0.5, throb=throb, grit=0.3, sub=sub)


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
        print(f"    {bar * BAR:6.2f}s  bar {bar:5.2f}  {what}")


def root_report(roots):
    for r in (roots if isinstance(roots, (list, tuple)) else [roots]):
        flag = "  <- under the measured-good band (A2 = 55 Hz)" if midi_to_hz(r) / 2 < 50 else ""
        print(f"    root midi {r}: {midi_to_hz(r):.1f} Hz, sub square {midi_to_hz(r) / 2:.1f} Hz{flag}")


def phrase_report():
    """The counter-measure's receipt: nothing moves in pitch, everything
    else does."""
    pitches = {INTERVAL[ch] for c in PHRASE[:7] for ch in CELL[c] if ch != "."}
    states = list(zip(CUTS, GATES, FLOORS))
    print(f"    the phrase: {' '.join(PHRASE)}")
    print(f"    cutoff {CUTS} Hz;  gate {GATES};  accent floor {FLOORS}; quarters lean {ACCENT}")
    check("the pitch never moves in bars 0-6 (root only)", pitches == {0},
          f"(intervals present: {sorted(pitches)})")
    check("bar 7 is the ONLY pitch event: bars 0-6 are all the hammer cell",
          set(PHRASE[:7]) == {"hammer"} and PHRASE[7] == "walk")
    check("and the walk really does leave the root", set(CELL["walk"]) - {".", "x"} != set(),
          f"(intervals {sorted({INTERVAL[c] for c in CELL['walk'] if c != '.'})})")
    runs, run = [], 1
    for a, b in zip(states, states[1:]):
        run = run + 1 if a == b else (runs.append(run) or 1)
    runs.append(run)
    check("no state holds for more than 2 bars (the cycle turns)", max(runs) <= 2, f"(longest {max(runs)} bars)")
    check("at least 4 distinct states over the 8 bars", len(set(states)) >= 4, f"({len(set(states))})")
    check("gate duty <= 0.5 everywhere (the 1993 figure)", max(GATES) <= 0.5, f"(max {max(GATES)})")
    check("the phrase moves 3 parameters, not 1", len({*CUTS}) >= 3 and len({*GATES}) >= 3 and len({*FLOORS}) >= 3)


def refrain_report(lines=HOOK, label="the Q/A pair"):
    ev = parse(lines)
    slots = len(lines) * 16
    onsets = len(ev)
    density = onsets / slots
    held = sum(1 for _, _, ln in ev if ln >= 2) / onsets
    run = best = 0
    for _, _, ln in ev:
        run = run + 1 if ln == 1 else 0
        best = max(best, run)
    midis = [m for _, m, _ in ev]
    steps = [b - a for a, b in zip(midis[:-1], midis[1:]) if b != a]
    downs = sum(1 for d in steps if d < 0) / max(1, len(steps))
    flat2 = sum(1 for m in midis if m % 12 == 7)                  # G natural, the flat 2 of F#
    print(f"    {label}: onsets {onsets}  density {density:.2f} (0.20-0.50)  held {held:.2f} (>= 0.5)  "
          f"longest 8th run {best} (<= 6)  {onsets / (len(lines) * BAR):.1f} notes/s")
    print(f"    DARK: register {min(midis)}-{max(midis)} (median {int(np.median(midis))}; floor F#2=42, ceiling G3=55)"
          f"  down-steps {downs:.2f} (>= 0.5)  max upward leap {max(steps)} st (<= 5)  flat-2nd onsets {flat2}")
    check("density window 0.20-0.50", 0.20 <= density <= 0.50)
    check("held fraction >= 0.5", held >= 0.5)
    check("run ceiling <= 6", best <= 6)
    check("register F#2..G3", min(midis) >= 42 and max(midis) <= 55)
    check("descending contour: down-steps >= 0.5", downs >= 0.5)
    check("no soaring leap: max upward <= 5 st", max(steps) <= 5)
    if lines is HOOK:
        q_end = [e for e in ev if e[0] < 32][-1]
        check("the petition hangs on the 5th (C#), the response lands on the tonic (F#)",
              q_end[1] % 12 == 1 and ev[-1][1] % 12 == 6)
        check("both phrase ends held >= a half note", q_end[2] >= 4 and ev[-1][2] >= 4)
        check("the flat 2nd colours the refrain", flat2 >= 2)


def space_report(kick_cell, hat_steps, cell="hammer", rejected=False):
    """This track's claim is space, so it is measured.  `rejected=True`
    marks a reading the probe renders on purpose as the alternative — for
    those the check is that it really does break the ceiling, otherwise
    the A/B is not an A/B (the procession guitar-carpet pattern)."""
    onsets = kick_cell.count("x") + SNARE_P.count("x") + len(hat_steps) + CELL[cell].count("x")
    print(f"    onsets per bar: kick {kick_cell.count('x')} + slam {SNARE_P.count('x')} + "
          f"hats {len(hat_steps)} + bass {CELL[cell].count('x')} = {onsets} (ceiling {SPACE_CEILING})")
    if rejected:
        check("the rejected reading really is over the ceiling (the A/B is real)", onsets > SPACE_CEILING,
              f"({onsets} > {SPACE_CEILING})")
    else:
        check(f"keeps its space (<= {SPACE_CEILING} onsets/bar)", onsets <= SPACE_CEILING)


def snare_report(hits, snare_gain, plate_cut):
    k, s = hits["kick"], hits["snare"]
    snd = (int(np.max(np.nonzero(np.abs(s) > 1e-3))) + 1) / SR
    blow = np.zeros(max(len(k), len(s)))
    blow[:len(k)] += k
    blow[:len(s)] += snare_gain * s
    total = (int(np.max(np.nonzero(np.abs(blow) > 1e-3))) + 1) / SR
    print(f"    slam: sounding {snd * 1000:.0f} ms (cut {plate_cut * 1000:.0f} ms);  the blow "
          f"{total * 1000:.0f} ms at weight {snare_gain:.2f}, snare/kick peak {np.max(np.abs(s)) / np.max(np.abs(k)):.2f}")
    check("the snare is truncated at its cut", snd <= plate_cut + 0.012)
    check("the blow still reads as one gesture (< 400 ms at 109)", total < 0.40)


def sub_share(x, hz=60.0):
    X = np.abs(np.fft.rfft(x)) ** 2
    f = np.fft.rfftfreq(len(x), 1 / SR)
    return float(X[f < hz].sum() / X.sum())


# ---------------------------------------------------------------- probes
def verse(bars, roots=FS2, hat_steps=(), phrase=True, sub=SUB_VERSE, accents=True, cycle=True,
          kick_cell=KICK_Q, pad_chords=None, **kw):
    x = steps_buffer(bars)
    d, hits = drums(bars, kick_cell=kick_cell, hat_steps=hat_steps)
    mix(x, d)
    mix(x, bassline(bars, roots, phrase=phrase, sub=sub, accents=accents, cycle=cycle, **kw), 0, GAIN["bass"])
    mix(x, bed(bars), 0, GAIN["bed"])
    if pad_chords:
        mix(x, pads(pad_chords, depth=0.0), 0, GAIN["pad"])
    return x, hits


def p01a():
    """The drone: the hammer cell flat on the F# pedal for eight bars — no
    accents, no filter cycle, no gate move.  What the archetype literally
    asks for, and what the v3 verdict warned about."""
    x, _ = verse(8, phrase=False, accents=False, cycle=False)
    print("    the engine as the blueprint states it: one cell, one cutoff, one gate, flat velocities")
    root_report(FS2)
    return x, 8


def p01b():
    """The same eight bars as the PHRASE: the pitch still never moves, but
    the filter, the gate and the accents do.  The A/B against 01a is the
    whole argument of this track."""
    x, _ = verse(8)
    phrase_report()
    root_report(FS2)
    return x, 8


def p01c():
    """The control: the phrase with the PITCH allowed to walk instead.  Is
    the archetype's 'root only' worth keeping, or is this simply better?"""
    x, _ = verse(8, roots=[FS2, FS2, FS2, D2, FS2, FS2, CS2, FS2])
    print("    the pedal walks F#2 F#2 F#2 D2 F#2 F#2 C#2 F#2 — everything else as 01b")
    root_report([FS2, D2, CS2])
    return x, 8


def p02():
    """The sub at F#2: its square lands at 46.3 Hz against the directory's
    measured-good 55 Hz.  Four bars each at 0.85 / 0.6 / 0.4, the last with
    the kick up to carry what the square gives up."""
    x = steps_buffer(12)
    for i, (sub, kick_gain) in enumerate(((0.85, 1.0), (SUB_VERSE, 1.0), (0.4, 1.0))):
        d, _ = drums(4)
        mix(x, d, 4 * i, kick_gain)
        mix(x, bassline(4, FS2, sub=sub), 4 * i, GAIN["bass"])
        seg = x[int(4 * i * BAR * SR): int(4 * (i + 1) * BAR * SR)]
        share = sub_share(seg)
        print(f"    bars {4 * i}-{4 * i + 3}: sub {sub:.2f}  sub-60 share {share:.2f}"
              f"  {'inside' if 0.60 <= share <= 0.70 else 'OUTSIDE'} the master guardrail band 0.60-0.70"
              f"{'  <- the recommended reading' if sub == SUB_VERSE else ''}")
    mix(x, bed(12), 0, GAIN["bed"])
    root_report(FS2)
    return x, 12


def p03():
    """The hats question: the same four verse bars with no hats, then
    8ths, then a 16th carpet.  At 109 a carpet fills exactly the space the
    archetype is made of."""
    x = steps_buffer(12)
    for i, steps in enumerate(((), HAT_8, HAT_16)):
        seg, _ = verse(4, hat_steps=steps)
        mix(x, seg, 4 * i)
        print(f"    bars {4 * i}-{4 * i + 3}: {len(steps)} hats per bar"
              f"{'  <- the recommended reading' if steps is HAT_8 else ''}")
        space_report(KICK_Q, steps, rejected=steps is HAT_16)
    return x, 12


def p04():
    """The chorus roots: following DOWN (F#2 D2 C#2, sub squares 46 / 37 /
    35 Hz), then PEDALLING on F#2 under the same chords, then following UP
    (F#2 D3 C#3)."""
    x = steps_buffer(12)
    readings = (("down", [FS2, D2, CS2, FS2]), ("pedal", FS2), ("up", [FS2, D3, CS3, FS2]))
    for i, (name, roots) in enumerate(readings):
        d, _ = drums(4, hat_steps=HAT_8)
        mix(x, d, 4 * i)
        mix(x, bassline(4, roots, phrase=False, sub=SUB_CHORUS), 4 * i, GAIN["bass"])
        mix(x, pads(LOOP, depth=0.0), 4 * i, GAIN["pad"])
        print(f"    bars {4 * i}-{4 * i + 3}: the {name} reading")
        root_report(roots)
    mix(x, bed(12), 0, GAIN["bed"])
    return x, 12


def p05():
    """The hammer snare: plate cut 140 / 220 / 300 ms at the default
    weight, then the weight ladder 0.90 / 1.15 / 1.40 at the chosen cut.
    Q5 stretches the truncation rule; this is the argument."""
    x = steps_buffer(12)
    for i, (cut, w) in enumerate(((0.14, 1.15), (0.22, 1.15), (0.30, 1.15),
                                  (PLATE_CUT, 0.90), (PLATE_CUT, 1.15), (PLATE_CUT, 1.40))):
        d, hits = drums(2, snare_gain=w, plate_cut=cut)
        mix(x, d, 2 * i)
        mix(x, bassline(2, FS2), 2 * i, GAIN["bass"])
        print(f"    bars {2 * i}-{2 * i + 1}: cut {cut * 1000:.0f} ms, weight {w:.2f}")
        snare_report(hits, w, cut)
    return x, 12


def p06():
    """The space: the full verse with the hats off and no pad — kick, slam,
    pedal, bed.  Is the gap between blows the track, or is it a hole?"""
    x, _ = verse(8)
    space_report(KICK_Q, ())
    timeline((0, "kick every quarter, the slam on 2 and 4, the pedal, nothing else"),
             (4, "the phrase's wide opening (cutoff 2800) and the choked bar 6 ahead"))
    return x, 8


def p07a():
    """THE PETITION: the 4-bar hook on dark_lead over F#m D C#m F#m, chest
    1.0 (chorus 1), the choir hit on the downbeat, the engine on the
    pedal under it."""
    x = steps_buffer(4)
    d, _ = drums(4, hat_steps=HAT_8)
    mix(x, d)
    mix(x, bassline(4, FS2, phrase=False, sub=SUB_CHORUS), 0, GAIN["bass"])
    mix(x, pads(LOOP, depth=0.0), 0, GAIN["pad"])
    mix(x, bed(4), 0, GAIN["bed"])
    place(x, hit(HIT_CHORD, kind="choir", dur=TOLL_DUR), 0, GAIN["hit"])
    mix(x, reverb(line_on(PETITION, 4, CHEST[0])), 0, GAIN["lead"])
    refrain_report(PETITION, "the petition alone")
    return x, 4


def p07b():
    """The full Q/A pair at chest 1.3 — the final chorus's voice, and the
    response landing on the low tonic that doubles the bass."""
    x = steps_buffer(8)
    d, _ = drums(8, hat_steps=HAT_8)
    mix(x, d)
    mix(x, bassline(8, FS2, phrase=False, sub=SUB_CHORUS), 0, GAIN["bass"])
    mix(x, pads(LOOP * 2, depth=0.0), 0, GAIN["pad"])
    mix(x, bed(8), 0, GAIN["bed"])
    for b in (0, 4):
        place(x, hit(HIT_CHORD, kind="choir", dur=TOLL_DUR), b * 16, GAIN["hit"])
    mix(x, reverb(line_on(HOOK, 8, CHEST[2])), 0, GAIN["lead"])
    refrain_report()
    return x, 8


def p08():
    """The toll: the chopped choir hit at 0.25 / 0.45 / 0.80 s under a lone
    kick and the bed.  Does a struck bell need to exist, or is the EPS hit
    already the toll (Q6)?"""
    x = steps_buffer(6)
    for i, dur in enumerate((0.25, 0.45, 0.80)):
        d, _ = drums(2, kick_cell="x...............")
        mix(x, d, 2 * i)
        place(x, hit(HIT_CHORD, kind="choir", dur=dur), 2 * i * 16, GAIN["hit"])
        print(f"    bars {2 * i}-{2 * i + 1}: the hit truncated at {dur * 1000:.0f} ms")
    mix(x, bed(6, throb=0.0), 0, GAIN["bed"])
    mix(x, pads([ORGAN_LOW], bars_each=6, fn=organ, depth=0.0), 0, GAIN["organ"])
    return x, 6


def p09():
    """The final's one energy move: the kick to 8ths (Q7).  Three readings,
    because the first rendering found the problem — 8ths UNDER the 8th-note
    hats puts the bar at 26 onsets, over this track's own space ceiling.
    The third reading is the fix: when the kick takes the 8ths, the hats
    give them up."""
    x = steps_buffer(6)
    readings = ((KICK_Q, HAT_8, "quarters + 8th hats (chorus 1 and 2)", False),
                (KICK_8, HAT_8, "8ths + 8th hats — over the ceiling", True),
                (KICK_8, (), "8ths, hats OUT — the fix", False))
    for i, (cell, hats, label, rejected) in enumerate(readings):
        d, _ = drums(2, kick_cell=cell, hat_steps=hats)
        mix(x, d, 2 * i)
        mix(x, bassline(2, FS2, phrase=False, sub=SUB_CHORUS), 2 * i, GAIN["bass"])
        mix(x, pads(LOOP[:2], depth=0.0), 2 * i, GAIN["pad"])
        print(f"    bars {2 * i}-{2 * i + 1}: {label}")
        space_report(cell, hats, rejected=rejected)
    mix(x, bed(6), 0, GAIN["bed"])
    mix(x, reverb(line_on(PETITION[:2], 6, CHEST[2])), 0, GAIN["lead"])
    return x, 6


def p10():
    """THE OPENING, take two.  The toll was rejected ("not great",
    2026-09-11) and it was the whole of bars 0-8, so this is three
    candidates with nothing decided between them — try something, adjust
    later.  Each is 8 bars and each ends the same way, with the engine
    running, so only the way IN differs.

    a) THE NAKED BLOW: the hammer announces itself.  Kick and slam
       together on beats 1 and 3, nothing else, 1.1 s of silence between
       blows at this tempo.  The bed creeps in at bar 2, the pedal at 4.
       No other track in the directory opens on a bare drum.
    b) THE WAY IN: no_access v3's device, which the ear has already
       passed ("works quite well").  The bed swells from silence, one low
       organ chord, one slow noise swell; the kick lands at bar 4.
    c) NO OPENING: the engine simply starts, full hammer at bar 0.  The
       "skip long intros" rule taken to its limit — and the reading that
       risks repeating the "starts abruptly" verdict."""
    x = steps_buffer(24)
    blow_steps = (0, 8)

    # (a) the naked blow
    K, S = kick(decay=5.0), snare(plate_decay=3.0, cut=PLATE_CUT)
    for b in range(2):
        for st in blow_steps:
            place(x, K, b * 16 + st, GAIN["kick"])
            place(x, S, b * 16 + st, GAIN["snare"])
    ramp = bed(6)
    n = int(2 * BAR * SR)
    ramp[:n] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(n) / n)       # creeping in over bars 2-3
    mix(x, ramp, 2, GAIN["bed"])
    mix(x, bassline(4, FS2), 4, GAIN["bass"])
    d, _ = drums(4)
    mix(x, d, 4)
    mix(x, line_on(PETITION[:2], 4, fn=organ), 6, GAIN["organ"])

    # (b) the way in
    swell = bed(8)
    n = int(2 * BAR * SR)
    swell[:n] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(n) / n)
    mix(x, swell, 8, GAIN["bed"])
    mix(x, organ(ORGAN_LOW, 3 * BAR, depth=0.0), 8, GAIN["organ"] * 0.8)
    mix(x, noise_sweep(3 * BAR, f0=150.0, f1=2500.0, res=2.0), 8, 0.12)
    d, _ = drums(4)
    mix(x, d, 12)
    mix(x, bassline(4, FS2), 12, GAIN["bass"])
    mix(x, line_on(PETITION[:2], 4, fn=organ), 14, GAIN["organ"])

    # (c) no opening
    seg, _ = verse(8, hat_steps=HAT_8)
    mix(x, seg, 16)

    for i, what in enumerate(("a) the naked blow", "b) the way in (no_access v3's device)", "c) no opening at all")):
        print(f"    bars {8 * i}-{8 * i + 7}: {what}")
    lvl = [20 * np.log10(np.sqrt(np.mean(x[int((8 * i) * BAR * SR): int((8 * i + 2) * BAR * SR)] ** 2)) + 1e-12)
           for i in range(3)]
    print(f"    first two bars, RMS dBFS: {[round(v, 1) for v in lvl]}  (the way in should be the quietest)")
    check("the three openings are genuinely different in level", max(lvl) - min(lvl) > 6.0,
          f"({max(lvl) - min(lvl):.1f} dB spread)")
    print("    no eps_hit in any reading: the toll is out of all three")
    return x, 24


PROBES = [("01a", "drone_flat_cell", p01a), ("01b", "drone_as_phrase", p01b),
          ("01c", "phrase_with_moving_pitch", p01c), ("02", "sub_at_fsharp", p02),
          ("03", "hats_none_8ths_16ths", p03), ("04", "chorus_roots", p04),
          ("05", "hammer_snare", p05), ("06", "the_space", p06),
          ("07a", "petition", p07a), ("07b", "petition_and_response", p07b),
          ("08", "the_toll", p08), ("09", "final_kick_to_8ths", p09),
          ("10", "the_opening_take_two", p10)]

if __name__ == "__main__":
    only = {x.strip() for x in ARGS.only.split(",") if x.strip()}
    out_dir = pathlib.Path(ARGS.out)
    suffix = "" if ARGS.bpm == 109.0 else f"_{ARGS.bpm:g}"
    print(f"grid {ARGS.bpm:g} BPM: bar {BAR:.3f} s, 16th {STEP * 1000:.0f} ms;  F#2 = {midi_to_hz(FS2):.1f} Hz, "
          f"sub square {midi_to_hz(FS2) / 2:.1f} Hz (the directory's measured-good centre is 55 Hz)")
    for nn, name, fn in PROBES:
        if only and nn not in only:
            continue
        print(f"\n=== {nn} {name} ===")
        x, bars = fn()
        assert np.all(np.isfinite(x)), name
        stats(x, bars)
        write_wav(out_dir / f"{nn}_{name}{suffix}.wav", x)
    print("\nall probe checks passed" if not FAILS else f"\nSOME PROBE CHECKS FAILED: {FAILS}")
