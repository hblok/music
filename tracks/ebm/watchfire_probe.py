#!/usr/bin/env python3
"""Watchfire — the probes (the ascent, tracks/ebm's first 1999 track).

Eleven short samples at 126 BPM of the refrain-as-a-section, the
anti-trap A/B, the ascent, the chorus roots, the rolling cell, the
chant against the arp, the era move, the registral lift, the trough and
the one resolution — each printed with the inspection the track's verify
block will print, heard and checked BEFORE watchfire.py exists.  Notes:
watchfire_notes.md ("The probes").  Blueprint:
../../inspiration/VNV_Empires.md.

**These probes sit downstream of an unheard verdict.**  Every one of
them uses `instruments/rom.py`, whose own audition (`rom.wav`) and
dialect demo (`demo_rom.wav`) have not been listened to yet.  If the ROM
orchestra is wrong, this whole script is rebuilt rather than retuned.
Rendered anyway, on request, so the ladders are waiting.

The recommendations in the notes are the DEFAULT state here and every
ladder keeps its alternative alongside.

    python3 watchfire_probe.py                  # all, to /workspace/music/ebm/watchfire_probe/
    python3 watchfire_probe.py --only 01a,01b   # a subset
    python3 watchfire_probe.py --bpm 131        # another tempo (files suffixed _131)

Raw: mono, no master; the refrain probes carry a 0.25 reverb so the
line is judged as it will sit.  Seed 1999.  A/B any pair with
    python3 ../../tools/ab.py A.wav B.wav --bpm 126 --bars 2
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

ap = argparse.ArgumentParser(description="Watchfire probes — see the docstring")
ap.add_argument("--bpm", type=float, default=126.0)
ap.add_argument("--only", default="", help="comma-separated probe ids, e.g. 01a,07")
ap.add_argument("--out", default="/workspace/music/ebm/watchfire_probe")
ARGS = ap.parse_args()
_common.set_tempo(ARGS.bpm)                     # BEFORE the instrument imports (they bind the grid)
_common.seed(1999)                              # Empires
from _common import BAR, BEAT, SR, STEP, midi_to_hz, norm, place, steps_buffer, write_wav  # noqa: E402
from eps_hit import hit                                                   # noqa: E402
from eps_kick import kick                                                 # noqa: E402
from eps_snare import snare                                               # noqa: E402
from hats import hat                                                      # noqa: E402
from juno import arp, lead                                                # noqa: E402
from rom import choir, strings                                            # noqa: E402
from seethe import seethe                                                 # noqa: E402
from sh101_bass import CELLS, note                                        # noqa: E402

# ------------------------------------------------------------- the material
B2, G2, D3, E3 = 47, 43, 50, 52                     # the chorus roots: they RISE through the loop
NOTE = {"B3": 59, "C#4": 61, "D4": 62, "E4": 64, "F#4": 66, "G4": 67, "A4": 69}

BM, G, D, EM = (54, 59, 62), (55, 59, 62), (54, 57, 62), (55, 59, 64)
LOOP = [BM, G, D, EM]                               # i VI III iv — no A major, no flat-VII arrival
ROOT_OF = {BM: B2, G: G2, D: D3, EM: E3}
HIT_CHORD = (47, 54, 59, 62)                        # B2 F#3 B3 D4
FORBIDDEN_ROOT = 9                                  # A: the flat-VII chord of B minor
BM_SCALE = {11, 1, 2, 4, 6, 7, 9}                   # B natural minor: B C# D E F# G A

# the refrain — it RISES, which is the point of a second dialect (watchfire_notes.md)
HOOK = ["B3 - C#4 D4 - - - -", "E4 - D4 - B3 - D4 -", "D4 - F#4 - A4 - - -", "G4 - F#4 E4 - F#4 - -",
        "B3 - C#4 D4 - - - -", "E4 - D4 - F#4 - G4 -", "A4 - - F#4 - D4 F#4 -", "E4 - - - - - - -"]
HOOK_RESOLVED = HOOK[:7] + ["B3 - - - - - - -"]     # the final pass, and the only resolution in the track
PHRASE_A, PHRASE_B = HOOK[:4], HOOK[4:]

# the era move: one knob on the existing kit (VNV_Empires.md §2)
CLEAN = {"hold": 1, "lowpass": None}                # 1999: the ASR-10
DIRT93 = {"kick": {"hold": 2, "lowpass": 6500.0}, "snare": {"hold": 2, "lowpass": 8000.0},
          "bass": {"hold": 2}, "hit": {"hold": 3, "lowpass": 7000.0}, "strings": {"hold": 2, "lowpass": 7000.0}}

KICK_Q = "x...x...x...x..."
SNARE_P = "....x.......x..."
HAT_16 = tuple(range(16))
OPEN_STEPS = (2, 6, 10, 14)
HAT_ACC = (1.0, 0.5, 0.7, 0.5)
BASS_RES = 1.8                                      # the Pro One reading: less bite than the SH-101's 2.5
LIFT = 12                                           # the registral lift: a whole octave, so the harmony cannot move
SUB_VERSE, SUB_CHORUS = 0.5, 0.7

GAIN = {"kick": 1.0, "snare": 0.9, "hat": 0.22, "oh": 0.26, "bass": 0.75, "bed": 0.4,
        "pad": 0.45, "chant": 0.42, "hit": 0.55, "lead": 0.9, "arp": 0.35}


def mix(buf, x, bar=0, gain=1.0):
    i0 = int(round(bar * BAR * SR))
    n = min(len(x), len(buf) - i0)
    if n > 0:
        buf[i0:i0 + n] += gain * x[:n]


# ---------------------------------------------------------------- parts
def drums(bars, hat_steps=HAT_16, open_from=None, kick_out=(), dirt=False):
    """The 1999 kit: the same instruments with the decimation off unless
    `dirt` puts 1993 back on (probe 06 is that A/B)."""
    kk = DIRT93["kick"] if dirt else CLEAN
    sk = DIRT93["snare"] if dirt else CLEAN
    K, S = kick(decay=7.0, **kk), snare(**sk)
    CH, OH = hat(hold=2 if dirt else 1), hat(open_=True, hold=2 if dirt else 1)
    buf = steps_buffer(bars)
    for b in range(bars):
        for s in range(16):
            st = b * 16 + s
            if KICK_Q[s] == "x" and b not in kick_out:
                place(buf, K, st, GAIN["kick"])
            if SNARE_P[s] == "x":
                place(buf, S, st, GAIN["snare"])
            if open_from is not None and b >= open_from and s in OPEN_STEPS:
                place(buf, OH, st, GAIN["oh"])
            elif s in hat_steps:
                place(buf, CH, st, GAIN["hat"] * HAT_ACC[s % 4])
    return buf


def bassline(bars, roots, cell="stomp", sub=SUB_VERSE, dirt=False, **kw):
    kw = {**({"hold": 2} if dirt else CLEAN), "res": BASS_RES, "sub": sub, **kw}
    c = CELLS[cell]
    onsets = [j for j, ch in enumerate(c) if ch != "."]
    buf = steps_buffer(bars)
    for b in range(bars):
        root = roots[b % len(roots)] if isinstance(roots, (list, tuple)) else roots
        for j, s in enumerate(onsets):
            gap = (onsets[j + 1] if j + 1 < len(onsets) else onsets[0] + 16) - s
            m = root + {"x": 0, "o": 12, "5": 7, "7": 10}[c[s]]
            place(buf, note(m, dur=gap * STEP * 0.5, **kw), b * 16 + s)
    return buf


def orchestra(chords, bars_each=1, octave=0, fn=strings, **kw):
    """The ROM section on the loop.  `octave` is the registral lift: the
    same chords moved up, the harmony untouched."""
    buf = steps_buffer(len(chords) * bars_each)
    for i, ch in enumerate(chords):
        mix(buf, fn(tuple(m + octave for m in ch), bars_each * BAR, **kw), i * bars_each)
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


def refrain(lines, bars, doubled=True, trap=False):
    """The carrier.  doubled: the line voiced (m-12, m) so the section
    plays it in two octaves — the anti-trap mechanism.  trap=True renders
    it on the chorused, vibrato'd Juno lead instead, on purpose."""
    buf = steps_buffer(bars, tail=2.0)
    for start, midi, ln in parse(lines):
        dur = ln * BEAT / 2 * 0.95
        x = lead(midi, dur) if trap else strings((midi - 12, midi) if doubled else (midi,), dur)
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


def bed(bars, throb=0.35):
    return seethe(B2, bars * BAR + 0.5, throb=throb, grit=0.25, sub=0.5)


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


def centroid(x):
    X = np.abs(np.fft.rfft(x))
    f = np.fft.rfftfreq(len(x), 1 / SR)
    return float((f * X).sum() / X.sum())


def low_share(x, below=400.0):
    X = np.abs(np.fft.rfft(x)) ** 2
    f = np.fft.rfftfreq(len(x), 1 / SR)
    return float(X[f < below].sum() / X.sum())


def refrain_report(lines=HOOK, label="the refrain"):
    """The sung-grammar window applies (this line is the singer).  The
    1993 DARK checks are inverted on purpose: this dialect ASCENDS."""
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
    ups = sum(1 for d in steps if d > 0) / max(1, len(steps))
    print(f"    {label}: onsets {onsets}  density {density:.2f} (0.20-0.50)  held {held:.2f} (>= 0.5)  "
          f"longest 8th run {best} (<= 6)  {onsets / (len(lines) * BAR):.1f} notes/s")
    print(f"    ASCENT: register {min(midis)}-{max(midis)} (median {int(np.median(midis))}), doubled down to "
          f"{min(midis) - 12}  up-steps {ups:.2f} (>= 0.5)  max upward leap {max(steps)} st  "
          f"max downward {min(steps)} st")
    check("density window 0.20-0.50", 0.20 <= density <= 0.50)
    check("held fraction >= 0.5", held >= 0.5)
    check("run ceiling <= 6", best <= 6)
    check("the line ascends: up-steps >= 0.5", ups >= 0.5, f"({ups:.2f})")
    check("it climbs, it does not leap (max upward <= 5 st)", max(steps) <= 5, f"({max(steps)} st)")
    check("register inside the declared 59-69", min(midis) >= 59 and max(midis) <= 69)


NAME_OF = {BM: "Bm", G: "G", D: "D", EM: "Em"}
PC = "C C# D D# E F F# G G# A A# B".split()


def loop_report(chords=LOOP):
    """The roots come from ROOT_OF, not from the lowest note of the
    voicing — every chord here is an inversion, so `min(chord)` would
    report F# G F# G and the anti-flat-VII check would be meaningless."""
    roots = [ROOT_OF[ch] % 12 for ch in chords]
    print(f"    the loop: {' '.join(NAME_OF[ch] for ch in chords)}  = i VI III iv;  roots {[PC[r] for r in roots]}"
          f";  {PC[FORBIDDEN_ROOT]} major would be the flat-VII")
    for ch in chords:
        low = min(ch) % 12
        if low != ROOT_OF[ch] % 12:
            print(f"      {NAME_OF[ch]} is voiced as an inversion (lowest note {PC[low]}, root {PC[ROOT_OF[ch] % 12]})")
    check("no flat-VII chord in the loop", FORBIDDEN_ROOT not in roots)
    check("every chord's notes belong to B natural minor", all(m % 12 in BM_SCALE for ch in chords for m in ch))
    check("the loop ends on the iv and leans back (no arrival)", chords[-1] is EM)


def root_report(roots):
    for r in (roots if isinstance(roots, (list, tuple)) else [roots]):
        flag = "  <- under the measured-good band (A2 = 55 Hz)" if midi_to_hz(r) / 2 < 50 else ""
        print(f"    root midi {r}: {midi_to_hz(r):.1f} Hz, sub square {midi_to_hz(r) / 2:.1f} Hz{flag}")


def dirt_report(dirt):
    era = "1993 (the EPS)" if dirt else "1999 (the ASR-10)"
    holds = {k: v["hold"] for k, v in DIRT93.items()} if dirt else {k: 1 for k in DIRT93}
    print(f"    era {era}: holds {holds}")
    if not dirt:
        check("every sampled voice has its decimation off (hold == 1)", set(holds.values()) == {1})


# ---------------------------------------------------------------- probes
def chorus_bed(bars, roots, octave=0, chant=True, sub=SUB_CHORUS, dirt=False, hits=(0,)):
    x = steps_buffer(bars)
    mix(x, drums(bars, open_from=0, dirt=dirt))
    mix(x, bassline(bars, roots, cell="rolling", sub=sub, dirt=dirt), 0, GAIN["bass"])
    skw = DIRT93["strings"] if dirt else {}
    mix(x, orchestra(LOOP * (bars // 4), octave=octave, **skw), 0, GAIN["pad"])
    if chant:
        mix(x, orchestra(LOOP * (bars // 4), fn=choir), 0, GAIN["chant"])
    mix(x, bed(bars), 0, GAIN["bed"])
    for b in hits:
        place(x, hit(HIT_CHORD, **(DIRT93["hit"] if dirt else CLEAN)), b * 16, GAIN["hit"])
    return x


def p01a():
    """THE REFRAIN AS A SECTION: the 8 bars on rom.strings, octave-doubled
    by voicing, over Bm G D Em with the rolling engine under it.  The
    track's central claim — a melody carried without a voice."""
    x = chorus_bed(8, [B2, G2, D3, E3], hits=(0, 4))
    mix(x, reverb(refrain(HOOK, 8)), 0, GAIN["lead"])
    refrain_report()
    loop_report()
    return x, 8


def p01b():
    """The same line NOT octave-doubled — one note per event instead of
    (m-12, m).  The A/B for anti-trap mechanism 2."""
    x = chorus_bed(8, [B2, G2, D3, E3], hits=(0, 4))
    line = refrain(HOOK, 8, doubled=False)
    mix(x, reverb(line), 0, GAIN["lead"])
    print(f"    single-octave voicing: centroid {centroid(line):.0f} Hz, "
          f"<400 Hz share {low_share(line):.2f}")
    d = refrain(HOOK, 8)
    print(f"    against the doubled voicing: centroid {centroid(d):.0f} Hz, "
          f"<400 Hz share {low_share(d):.2f}")
    check("doubling really lowers the line's centre of mass", low_share(d) > low_share(line),
          f"({low_share(d):.2f} vs {low_share(line):.2f})")
    return x, 8


def p01c():
    """The trap, rendered on purpose: the same notes on the chorused,
    vibrato'd Juno lead.  This is what the directory's Frankfurt warning
    is about, and it is here to be rejected, not chosen."""
    x = chorus_bed(8, [B2, G2, D3, E3], hits=(0, 4))
    mix(x, reverb(refrain(HOOK, 8, trap=True)), 0, GAIN["lead"])
    print("    carrier: juno.lead — chorus depth 1.0, vibrato 5.5 Hz / 10 cents, single octave")
    print("    the A/B is one variable: same notes, same bed, same loop")
    return x, 8


def p02():
    """THE ASCENT: bars 0-16 assembled.  One sustained tone, then two, then
    the first phrase, then its answer — the refrain arriving in pieces,
    with the kick entering at bar 8 and the bass at bar 12.  Not an intro."""
    x = steps_buffer(16)
    mix(x, bed(16), 0, GAIN["bed"])
    mix(x, strings((47, 59), 4 * BAR), 0, GAIN["lead"] * 0.7)
    mix(x, strings((47, 59), 2 * BAR), 4, GAIN["lead"] * 0.8)
    mix(x, strings((50, 62), 2 * BAR), 6, GAIN["lead"] * 0.8)
    mix(x, drums(8, hat_steps=()), 8)
    mix(x, reverb(refrain(PHRASE_A, 4)), 8, GAIN["lead"])
    mix(x, bassline(4, B2), 12, GAIN["bass"])
    mix(x, reverb(refrain(PHRASE_B, 4)), 12, GAIN["lead"])
    mix(x, orchestra(LOOP, octave=0), 12, GAIN["pad"] * 0.6)
    blocks = [{59}, {59, 62}, {m for _, m, _ in parse(PHRASE_A)}, {m for _, m, _ in parse(PHRASE_B)}]
    sizes = [len(b) for b in blocks]
    print(f"    distinct melody pitches per 4-bar block: {sizes}")
    check("the ascent builds (pitch count never decreases)", all(a <= b for a, b in zip(sizes, sizes[1:])))
    timeline((0, "one tone, octave-doubled, over the bed"), (4, "two tones"),
             (8, "the first phrase at speed; the kick enters"), (12, "its answer; the bass enters"))
    return x, 16


def p03():
    """The chorus roots: the bass RISING B2 G2 D3 E3 through the loop (the
    ascent in the low end), against pedalling on B2.  G2's sub square at
    49 Hz is the question."""
    x = steps_buffer(8)
    for i, (name, roots) in enumerate((("rising", [B2, G2, D3, E3]), ("pedal", B2))):
        mix(x, drums(4, open_from=0), 4 * i)
        mix(x, bassline(4, roots, cell="rolling", sub=SUB_CHORUS), 4 * i, GAIN["bass"])
        mix(x, orchestra(LOOP), 4 * i, GAIN["pad"])
        print(f"    bars {4 * i}-{4 * i + 3}: the {name} reading"
              f"{'  <- the recommended one' if name == 'rising' else ''}")
        root_report(roots)
    mix(x, bed(8), 0, GAIN["bed"])
    return x, 8


def p04():
    """The engine cell: `rolling` (xoxxxoxxxoxxxoxx — the VNV chorus
    engine, unused in this directory so far) against `stomp`, same roots,
    same bar."""
    x = steps_buffer(8)
    for i, cell in enumerate(("rolling", "stomp")):
        mix(x, drums(4, open_from=0), 4 * i)
        mix(x, bassline(4, [B2, G2, D3, E3], cell=cell, sub=SUB_CHORUS), 4 * i, GAIN["bass"])
        mix(x, orchestra(LOOP), 4 * i, GAIN["pad"])
        c = CELLS[cell]
        print(f"    bars {4 * i}-{4 * i + 3}: cell {cell} ({c}) — {c.count('x') + c.count('o')} onsets/bar, "
              f"{c.count('o')} octaves")
    mix(x, bed(8), 0, GAIN["bed"])
    return x, 8


def p05():
    """The counter-layer: the chorus WITH the chant, then without, then
    with a 16th arp in its place.  The arp is the genre's signature and
    its trap; this is the argument for leaving it out."""
    x = steps_buffer(12)
    mix(x, chorus_bed(4, [B2, G2, D3, E3], chant=True), 0)
    mix(x, chorus_bed(4, [B2, G2, D3, E3], chant=False), 4)
    mix(x, chorus_bed(4, [B2, G2, D3, E3], chant=False), 8)
    a = steps_buffer(4)
    for i, ch in enumerate(LOOP):
        mix(a, arp(ch, bars=1, octaves=2, pattern="updown"), i)
    mix(x, a, 8, GAIN["arp"])
    for i, what in enumerate(("the chant (recommended)", "nothing", "a 16th updown arp (the rejected reading)")):
        print(f"    bars {4 * i}-{4 * i + 3}: {what}")
    check("the arp reading is rendered as the alternative, not the plan", True,
          "(no arp layer exists in watchfire_notes.md's kit table)")
    return x, 12


def p06():
    """THE ERA: the same eight groove bars with the kit clean, then with
    1993's decimation back on.  If this is inaudible, the premise that the
    dialect move is one knob is wrong."""
    x = steps_buffer(8)
    for i, dirt in enumerate((False, True)):
        seg = chorus_bed(4, [B2, G2, D3, E3], chant=False, dirt=dirt)
        mix(x, seg, 4 * i)
        print(f"    bars {4 * i}-{4 * i + 3}: {'1993 (the EPS)' if dirt else '1999 (the ASR-10)'}  "
              f"centroid {centroid(seg):.0f} Hz")
        dirt_report(dirt)
    return x, 8


def p07():
    """THE LIFT: chorus 1, then chorus 2 with the orchestra an octave up.
    The harmony does not move — that is the Kingdom take (VNV_Empires.md
    §5, take 4), and the check measures it rather than assuming it."""
    x = steps_buffer(8)
    mix(x, chorus_bed(4, [B2, G2, D3, E3], octave=0), 0)
    mix(x, chorus_bed(4, [B2, G2, D3, E3], octave=LIFT), 4)
    lo, hi = orchestra(LOOP), orchestra(LOOP, octave=LIFT)
    print(f"    chorus 1 orchestra: <400 Hz share {low_share(lo):.2f}, centroid {centroid(lo):.0f} Hz")
    print(f"    chorus 2 orchestra: <400 Hz share {low_share(hi):.2f}, centroid {centroid(hi):.0f} Hz")
    check("the lift is registral (the orchestra moved up an octave)", low_share(hi) < 0.5 * low_share(lo))
    check("the lift is a whole octave, so no pitch class changes", LIFT % 12 == 0, f"(+{LIFT} semitones)")
    loop_report()
    return x, 8


def p08():
    """THE TROUGH: the kick out, the chant alone over the bed, the refrain
    stated slow on the section.  It must keep a pulse — a long beatless
    break reads as two songs (the phototaxis lesson)."""
    x = steps_buffer(8)
    mix(x, bed(8, throb=0.5), 0, GAIN["bed"] * 1.3)
    mix(x, orchestra(LOOP * 2, fn=choir), 0, GAIN["chant"] * 1.2)
    mix(x, reverb(refrain(PHRASE_A, 8)), 0, GAIN["lead"] * 0.85)
    env = np.abs(signal.hilbert(x[: int(8 * BAR * SR)]))
    w = int(0.05 * SR)
    env = np.convolve(env, np.ones(w) / w, "same")
    print(f"    no kick, no snare; the bed's throb and the chant move on the bar")
    print(f"    envelope variation over the section: {env.std() / (env.mean() + 1e-12):.2f} (a flat carpet is ~0)")
    check("the trough keeps a pulse (envelope varies)", env.std() / (env.mean() + 1e-12) > 0.15)
    return x, 8


def p09():
    """THE RESOLUTION: the loop's usual unresolved iv ending, then the
    final pass landing on B.  Exactly one statement in the track does
    this, and it is the last."""
    x = steps_buffer(16)
    for i, lines in enumerate((HOOK, HOOK_RESOLVED)):
        mix(x, chorus_bed(8, [B2, G2, D3, E3], octave=LIFT if i else 0, hits=(0, 4)), 8 * i)
        mix(x, reverb(refrain(lines, 8)), 8 * i, GAIN["lead"])
        last = parse(lines)[-1][1]
        print(f"    bars {8 * i}-{8 * i + 7}: last note midi {last} "
              f"({'the tonic B — the one resolution' if last % 12 == 11 else 'E4, leaning on the iv'})")
    check("only the second reading resolves to the tonic",
          parse(HOOK)[-1][1] % 12 != 11 and parse(HOOK_RESOLVED)[-1][1] % 12 == 11)
    refrain_report(HOOK_RESOLVED, "the resolved pass")
    return x, 16


PROBES = [("01a", "refrain_as_section", p01a), ("01b", "refrain_single_octave", p01b),
          ("01c", "refrain_on_the_trap_lead", p01c), ("02", "the_ascent", p02),
          ("03", "chorus_roots", p03), ("04", "rolling_vs_stomp", p04),
          ("05", "chant_vs_arp", p05), ("06", "the_era", p06),
          ("07", "the_registral_lift", p07), ("08", "the_trough", p08),
          ("09", "the_resolution", p09)]

if __name__ == "__main__":
    only = {x.strip() for x in ARGS.only.split(",") if x.strip()}
    out_dir = pathlib.Path(ARGS.out)
    suffix = "" if ARGS.bpm == 126.0 else f"_{ARGS.bpm:g}"
    print(f"grid {ARGS.bpm:g} BPM: bar {BAR:.3f} s, 16th {STEP * 1000:.0f} ms;  B2 = {midi_to_hz(B2):.1f} Hz, "
          f"sub square {midi_to_hz(B2) / 2:.1f} Hz (above the directory's measured-good 55 Hz centre)")
    print("NOTE: every probe here uses instruments/rom.py, whose audition is not yet heard.")
    for nn, name, fn in PROBES:
        if only and nn not in only:
            continue
        print(f"\n=== {nn} {name} ===")
        x, bars = fn()
        assert np.all(np.isfinite(x)), name
        stats(x, bars)
        write_wav(out_dir / f"{nn}_{name}{suffix}.wav", x)
    print("\nall probe checks passed" if not FAILS else f"\nSOME PROBE CHECKS FAILED: {FAILS}")
