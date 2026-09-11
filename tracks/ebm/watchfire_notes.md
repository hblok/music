# Watchfire — design notes (2026-09-11, the first 1999-dialect track)

**The ascent.** A ~4:19 song in the mould of *Empires*' *Saviour* —
the archetype `../../inspiration/VNV_Empires.md` §6 ranks first, and
the only track on that record whose emotional centre is carried
without a voice: *"warm, compassionate synthesizers conveying melody
without vocals."* A vocal band arriving at this repo's constitution on
its own is the whole reason to build it.

This is the directory's **third dialect** and its first track: 1993
dark-electro is `reliquary` / `no_access` / `procession` / `litany`,
and this is 1999. The era move is one knob on the existing kit plus one
voice, both now in place — `instruments/rom.py` and `demo_rom.py`,
rendered 2026-09-11, **verdict pending**. Nothing below survives a bad
verdict on those two, so they are heard first.

**The title.** *Empires* is framed in Roman and imperial imagery, not
liturgy — the blueprint's §5 says titles from Rome, ruin and cycles, not
from the Mass, which also separates this track from `reliquary` and
`procession`. A watchfire is the signal relayed hill to hill: a message
that ascends, is answered, and never rests in one place. One abstract
noun, in the *Kingdom* / *Legion* / *Arclight* manner. Free repo-wide.
Alternatives in Q1.

**Workflow — probe first** (the standing rule): `watchfire_probe.py`
renders the short samples below and prints the inspection the track's
verify block will carry. No track script until they are heard.

## Declared up front (not questions)

- **126 BPM, 4/4, B natural minor, 136 bars ≈ 4:19.** Needs
  `_common.set_tempo(126)` **before importing any instrument module**.
  At 126: beat 0.476 s, bar 1.905 s, 16th 0.119 s.
- **Why 126.** It is below every trance track in this repo (the lowest
  is 130) and inside *Empires*' 76–144 range, while avoiding the two
  club singles at 134 and 139 that §5 puts on the leave list. Momentum
  at 126 has to come from continuity, not from speed — which is the
  correct problem to be solving on this track.
- **Why B minor.** The directory holds A minor, C♯ minor and F♯ minor.
  B2 (midi 47, 123.5 Hz) puts the SH-101 sub square at **61.7 Hz**,
  above the directory's measured-good 55 Hz centre — the first track
  here whose root register is comfortable rather than argued.
- **Script** `tracks/ebm/watchfire.py` → `/workspace/music/watchfire.wav`
  + `.flac`, one `NAME` constant, the `LISTENING.md` flags, imports from
  `instruments/`, checks skipped on a partial render.
- **The 1999 palette**: `rom.strings` and `rom.choir` as the orchestra,
  the SH-101 on its Pro One reading, the EPS kit **with its dirt off**
  (`hold=1`, the lowpass ceilings lifted), one clean orchestral hit, the
  seethe bed. No Juno chorus anywhere.
- **No arp, at all.** The 16th arp is the futurepop signature and it is
  on §5's leave list together with the supersaw lead it usually carries.
  The counter-melody job goes to the **chant** instead — the *Legion*
  take, static and chordal. This is the single biggest departure from
  what an *Empires* track would actually do, and it is deliberate.
- **~4:19, not ~7:00.** Both long tracks on *Empires* drew
  repetitiveness complaints in the reviews, and this directory's own
  last two verdicts said the same thing about its own work.
- **Instrumental, and no spoken slot.** *Saviour* has no vocal for its
  first ninety seconds and this track has none at all.

## The load-bearing decision: the ascent is not an intro

*Saviour* opens with ninety seconds of instrumental ascension before the
song proper. This repo's standing feedback says to skip long intros and
keep one continuous cursor with no dead seams. Both are right, so:

> **The ascent is the refrain's first statement, arriving in pieces.**

Not a pad swell that precedes the song. The refrain's own notes are
present from bar 1 and the melody is assembled in front of the listener:
one sustained tone, then two, then the first phrase, then its answer,
each pass adding one layer and one more note of the line. The kick
enters underneath at bar 8 and the bass at bar 12, so the groove arrives
*during* the assembly rather than after it.

This gives the track an opening unlike anything else in the directory —
`reliquary` opens on a bed, `no_access` on a riff, `procession` on an
808 quote, `litany` on a struck hit — and it satisfies the thesis-early
rule natively, because the thesis is literally what is being built.

## The refrain — the line that ascends

8 bars, 8th-note tokens, over the loop one chord per bar. The 1993
tracks all recite downward in a baritone; **this one rises**, and that
contrast is the point of having a second dialect at all.

```
Bm | B3 -  C#4 D4  -  -   -   -
G  | E4 -  D4  -   B3 -   D4  -
D  | D4 -  F#4 -   A4 -   -   -
Em | G4 -  F#4 E4  -  F#4 -   -
Bm | B3 -  C#4 D4  -  -   -   -
G  | E4 -  D4  -   F#4 -  G4  -
D  | A4 -  -   F#4 -  D4  F#4 -
Em | E4 -  -   -   -  -   -   -      leans on the iv, unresolved
```

MIDI: B3 59, C♯4 61, D4 62, E4 64, F♯4 66, G4 67, A4 69.

26 onsets, density 0.20 (onsets / 16th slots), 1.71 notes/s at 126,
longest 8th run 2, register 59–69, held fraction ~0.5, peak A4 on bar 7.

**The anti-trap mechanism.** A rising line peaking at A4 is, on paper,
the Frankfurt tenor arch that `CLAUDE.md` warns about. Four things
separate it, and they are mechanisms rather than taste:

1. **The carrier is a section, not a lead.** `rom.strings` is a 5-voice
   detuned stack with no vibrato and no chorus. The trap's recipe is a
   chorused, vibrato'd single lead.
2. **Every note is octave-doubled downward** — the line is voiced
   `strings((m - 12, m), dur)`, so the section plays B2–A3 and B3–A4 at
   once and its centre of mass sits an octave below the trance register.
   This is what a ROM string patch does natively.
3. **There is no arp under it.** The trap needs the updown two-octave
   sequence as much as it needs the lead.
4. **There is no ♭VII lift** — see the harmony below.

## Harmony — the loop that never rests

**Bm – G – D – Em**, one chord per bar: i – VI – III – iv.

No A major anywhere. The ♭VII is what makes a progression feel like an
arrival, which reads as uplifting trance regardless of the drums
(`CLAUDE.md`, the trap; `VNV_Empires.md` §5, leave 1). Instead the loop
ends on the **iv**, which leans back into the i and starts again — so
the harmony itself is the momentum, and the track never lands.

**One exception, and it is the whole ending:** the final statement of
the refrain resolves its last bar to **B3**, the tonic. That is the only
resolution in the track, and the verify block checks that it happens
exactly once and last.

Verses sit on a **B pedal** (the EBM tell). Choruses follow the loop bar
by bar (the futurepop tell), and the chorus roots **rise**: B2 47, G2
43, D3 50, E3 52 — the bass climbing through the loop is the ascent in
the low end. Probe 03 checks the G2 sub square at 49 Hz.

## Structure (136 bars ≈ 4:19)

| bars | time | section | what happens |
|---|---|---|---|
| 0–16 | 0:00 | **THE ASCENT** | the refrain assembled: one tone at bar 0, two at 4, the first phrase at 8, its answer at 12. Kick at 8, bass at 12, bed throughout |
| 16–32 | 0:30 | VERSE 1 | the B pedal, the engine, strings low and thin |
| 32–40 | 1:01 | RISE 1 | the bass starts following the loop; the orchestra climbs; open hats |
| 40–56 | 1:16 | CHORUS 1 | the refrain whole ×2, the loop, the chant enters underneath |
| 56–72 | 1:47 | VERSE 2 | the pedal again, one layer denser than verse 1 |
| 72–80 | 2:17 | RISE 2 | as rise 1, a notch up |
| 80–96 | 2:32 | CHORUS 2 | the refrain ×2, the strings an octave up (the registral lift) |
| 96–112 | 3:03 | **THE TROUGH** | kick out; the chant alone over the bed; the refrain stated once, slow, on a single voice |
| 112–136 | 3:33 | **THE FINAL** | the refrain ×3: strings, then + the octave, then + the chant in fusion. The last pass resolves to B |

Hook count: 2 + 2 + 1 + 3 = **8 full statements**, the assembly in the
ascent uncounted. Target **≥ 8**.

The trough keeps a pulse (the phototaxis lesson: a long beatless break
reads as two songs) — the chant is chordal and moves on the bar, and
the bed's throb continues.

## Kit (library calls)

| slot | call | notes |
|---|---|---|
| refrain | `rom.strings((m - 12, m), dur)` | the carrier; octave-doubled by voicing, not by a knob |
| orchestra | `rom.strings(chord, BAR)` via `juno.pad_loop(prog, fn=strings)` | the pad bed under the choruses; an octave up in chorus 2 |
| chant | `rom.choir(chord, BAR, vowel="o")` | octave-doubled, static, chordal — the arp's replacement |
| bass | `sh101_bass.note(m, dur, res=1.8, hold=1, lowpass=None)` | the Pro One reading: less resonance, no decimation |
| cells | `CELLS["stomp"]` verses, `CELLS["rolling"]` choruses | `rolling` (`xoxxxoxxxoxxxoxx`) is the VNV chorus engine and is unused in this directory so far |
| kick | `eps_kick.kick(hold=1, lowpass=None)` | every quarter |
| snare | `eps_snare.snare(hold=1, lowpass=None)` | 2 and 4 — the fastest tell against trance |
| hats | `hats.hat(hold=1)` | 16th carpet with the accent cell; open on the off-8ths in rises and choruses |
| hit | `eps_hit.hit(chord, hold=1, lowpass=None)` | clean, not truncated-13-bit; chorus downbeats |
| bed | `seethe.seethe(47, END, throb=…)` | one continuous cursor, rooted on B |

No `juno` presets as voices, no `kit808`, no `riff`, no `bark`, no
`machine`, no `dark_lead` — the last one is the 1993 refrain voice and
this dialect's refrain is the section.

## The probes (`watchfire_probe.py` → `/workspace/music/ebm/watchfire_probe/`)

| id | what it asks |
|---|---|
| `01a` | **the refrain as a section** — the 8 bars on `rom.strings`, octave-doubled by voicing, over the loop |
| `01b` | the same line **not** octave-doubled — the A/B that proves mechanism 2 against the trap |
| `01c` | the same line on a Juno lead with chorus and vibrato — the trap rendered on purpose, as the thing to hear and reject |
| `02` | **the ascent** — bars 0–16 assembled, one tone to the full phrase, with the kick and bass entering underneath |
| `03` | **the chorus roots** — the bass rising B2 G2 D3 E3 through the loop, against pedalling on B2. The G2 sub square at 49 Hz is the question |
| `04` | **the rolling cell** — `rolling` against `stomp` under the same chorus bar |
| `05` | **the chant as the counter-layer** — the chorus with the chant, then without, then with a 16th arp instead. The argument for leaving the arp out |
| `06` | **the era** — the same 8 groove bars with the kit clean, then with the 1993 dirt back on. If this is inaudible the whole dialect premise is wrong |
| `07` | **the lift** — chorus 1 against chorus 2, the strings an octave up, the harmony unchanged |
| `08` | **the trough** — the chant alone over the bed with the slow refrain, checking it keeps a pulse |
| `09` | **the resolution** — the final pass landing on B against the loop's usual unresolved iv |

## Verify (the track script prints)

The standard set (`../VERIFY.md`) plus, from `VNV_Empires.md` §6 and
this track's own claims:

- **the dirt ledger** — every sampled voice's `hold` printed, asserting
  `hold == 1` and no lowpass ceiling below 8 kHz. The receipt that the
  track has not drifted back into 1993;
- **no ♭VII** — the chord ledger printed, asserting A major appears
  nowhere;
- **the resolution is unique and last** — exactly one refrain statement
  ends on the tonic, and it is the final one;
- **the ascent builds** — distinct pitches sounding per 4-bar block in
  bars 0–16 increases monotonically;
- **the instrumental centre** — the first full refrain statement lands
  inside the first third of the track (bar 45 at this length);
- **no arp layer exists** — a structural assertion, not a measurement;
- **the refrain sings**: density 0.20–0.50, run ceiling ≤ 6, held
  fraction ≥ 0.5, register inside the declared 59–69 plus its octave
  double;
- **the registral lift** — chorus 2's orchestral median pitch at least
  an octave above chorus 1's, with the chord roots unchanged between
  them;
- per-section RMS arc, the trough as the lowest groove section, master
  guardrails, crest ≥ 3.2 in the choruses.

## Open questions for review

1. **Title and seed.** *Watchfire*; alternatives *Ascendant*,
   *Vanguard*, *Zenith*. Seed **1999**; the blueprint also offers 8
   (catalogue mind 008) and 50.
2. **126, or faster.** Recommended 126, for the separation argued
   above. The risk is that "relentless momentum" needs more than this,
   in which case 131 is the next step that still misses every taken
   tempo.
3. **The peak at A4.** Recommended: keep it, with the octave doubling
   doing the work. Probe 01a/01b/01c is exactly this argument, and if
   the doubled version still reads as trance the line drops a third.
4. **Leaving the arp out entirely.** Recommended yes — it is the
   genre's signature and also its trap, and the chant covers the
   counter-melody job. Probe 05 is the check.
5. **The chorus bass rising through the loop**, with G2's sub square at
   49 Hz. Recommended yes; the fallback is pedalling on B under the
   moving chords, as `procession` does.
6. **The trough at 16 bars.** Recommended yes at this length, because
   it keeps a pulse. If it reads as two songs, it goes to 8.
7. **How warm is too warm.** The relative major III is the warmth here.
   The standing goa verdict is that major reads as country; the
   defence is that III inside a minor loop is diatonic and the track
   never cadences on it. Probe 01a decides.
8. **Whether `rom.strings` wants a `lead` sibling** after all — a
   single warm sustained voice rather than the section on one note. The
   module deliberately does not have one yet. Probe 01a answers it.

## Probe amendments (2026-09-11, written and rendered, before any listening)

`watchfire_probe.py` is written and its 11 files are rendered to
`/workspace/music/ebm/watchfire_probe/`; all probe checks pass. It was
written **out of order on request** — every probe in it uses `rom.py`,
whose audition has not been heard, so a bad verdict there rebuilds this
script rather than retuning it. Four things to record:

1. **The chord voicings are inversions, and the root check has to know
   that.** `Bm` is voiced F♯3–B3–D4, `D` is F♯3–A3–D4, `Em` is
   G3–B3–E4. The first version of the anti-♭VII check read the lowest
   note as the root and reported the loop as "F♯ G F♯ G", passing for
   entirely the wrong reason. The roots now come from a declared map,
   and the track script's verify block must do the same. A check that
   passes by accident is worse than no check.
2. **The refrain measures better than the notes claimed.** Held
   fraction is **0.85**, not the ~0.5 estimated above, and the longest
   run of short notes is **1**, not 2. Up-steps 0.58, max upward leap 4
   semitones, max downward 7 (the drop back to restate the petition).
   So the line climbs in steps and never leaps — which is the honest
   answer to "is this the Frankfurt arch?", since an arch leaps.
3. **The octave doubling works, but modestly.** Measured on the line
   alone, energy below 400 Hz goes from 0.43 undoubled to **0.54**
   doubled, and the centroid from 2071 Hz to 1956 Hz. It moves the
   centre of mass in the right direction, but it is not dramatic, and
   probe 01a/01b/01c is where the ear decides whether it is enough.
4. **The era move may be subtler than the premise assumes.** Probe 06
   measures the same four bars clean against 1993's decimation:
   centroid **3068 Hz versus 2812 Hz**, about an 8 % shift. That is a
   real difference but not an obvious one, and the whole 1999 dialect
   rests on it being audible. This probe, with `demo_rom.wav`, is the
   one that can invalidate the plan.

**The chant was buried, and the chant is load-bearing.** A check-audit
the same day found it sitting **14.5 dB** under the mix it plays in, at
gain 0.42. That layer is the entire justification for leaving the arp
out — it is supposed to *be* the counter-melody — so at that level probe
05 could not have answered its own question. Raised to 0.78, which puts
it 9.2 dB down, and re-rendered. The ear still sets the final balance.

**One weak spot in the rising-roots reading** (probe 03): G2's sub
square lands at 49 Hz, under the directory's measured-good 55 Hz
centre. B2, D3 and E3 are all comfortable at 61.7, 73.4 and 82.4 Hz, so
the loop has exactly one soft chord in the low end. The pedal reading
is rendered beside it.

## Next

1. **Listen to `rom.wav` and `demo_rom.wav` first.** Everything here is
   downstream of those two verdicts, probe 06 most of all.
2. Then the probe ladders: `01a → 01b → 01c` (the anti-trap argument),
   `02` (the ascent as an opening), `03`, `04`, `05` (the chant against
   the arp), `06` (the era), `07`, `08`, `09`.
3. Answer the eight questions above, now that the alternatives are
   audible.
4. Only then `watchfire.py`.
