# Procession — design notes (2026-09-11, the third tracks/ebm/ track)

**The slam.** A ~3:56 song in the mould of *Soli Deo Gloria*'s *Ashes
to Ashes '93* — the record's **slam** archetype and the last of the
three (`../../inspiration/Apop_Soli_Deo_Gloria.md` §3, §6): 122 BPM, A
minor, kick and snare hitting like one instrument, the SH-101 in gated
8ths on a pedal, "the whole thing short and relentless". The blueprint
calls it "the most classic archetype on the record and the safest
single target".

**This is the song `reliquary` bookends.** Part 1 states a hook, ends
open on the V (E), and says a later song quotes that hook as its
refrain — that is what a Part 1 is *for* (`reliquary_notes.md` Q4, Q8;
`no_access_notes.md` head). So the refrain here is not new material:
it is Reliquary's dark hook, same notes, same key, moved from an
interlude's Juno lead onto the stomp. Seed **1991** (the *Ashes to
Ashes* single). Working title **Procession** — the reliquary carried,
hammering, through the streets; alternatives in Q1.

**Workflow — probe first** (the standing rule, `no_access_probe.py` is
the pattern): nothing here is rendered as a track until it has been
heard small. `procession_probe.py` renders ~9 short samples (4–8 bars
at 122) and prints the inspection the track's verify block will print;
every probe is tied to a numbered question below. The track script is
written only after the probe verdicts.

## Declared up front (not questions)

- **122 BPM, 4/4, 120 bars + tail ≈ 3:56, A natural minor.** 122 is the
  library's default grid — no `set_tempo` call, unlike no_access. Short
  on purpose: the last two verdicts were both about *dragging*, and the
  source slam is 4:18 with a fraction of this one's arrangement.
- **Script** `tracks/ebm/procession.py` → `/workspace/music/procession.wav`
  + `.flac`, one `NAME` constant, the `LISTENING.md` flags (`--solo`,
  `--mute`, `--slice`, `--suffix`, `--stems`), imports from
  `instruments/`, checks skipped on a partial render. Everything else
  per `no_access_v3.py`.
- **The refrain is Reliquary's hook** (below) — the quote is literal,
  on `dark_lead`, in A minor. The song's own new material is the
  engine, the verse device and the pre-chorus.
- **Register.** Bass root A2 (45, 110 Hz, the sub square at 55 Hz — the
  directory's measured-good centre). The chorus roots F and E would sit
  at F2 (41, 87 Hz, sub at **43.7 Hz**) and E2 (40, 82 Hz, sub at
  **41.2 Hz**), both under the band where the sub square stops being
  body and starts eating headroom — so the chorus either takes F3/E3
  (53/52) or keeps the bass on A under the moving chords. Probe 2
  settles it. The refrain lives A2–B♭3 (45–58), exactly as Reliquary
  v3.3 plays it.
- **The 1993 palette**: SH-101 bass, EPS kick / slam snare / hats, the
  Juno pad and offbeat stab, one EPS hit, the seethe bed, `dark_lead`
  as the refrain, the 808 kit for the bookend frame only. **No bark**
  (dead, 2026-09-06), no strings, no arp wall, no supersaw.
- **The engine is a PHRASE, not a cell** — the v3 lesson
  (`no_access_notes.md` §v3), built in from bar 1 rather than patched
  in later: an 8-bar shape, 16th accents, a filter cycle, and a pedal
  that answers. At 122 with gated 8ths the risk of drone is *higher*
  than it was at 140, not lower.
- **Instrumental.** The spoken slot is open (Q6); TTS through
  `machine.py` is allowed in this directory for a short machine phrase,
  a user take takes priority, and `VOICE_GAIN = 0` must render a
  complete track without it.
- **One continuous cursor**: the seethe bed runs unbroken from the
  first bar to the fade; every seam is crossed by it plus one named
  device. The break is **8 bars and keeps a pulse** (the phototaxis
  lesson: a long beatless break reads as two songs).

## The refrain — Reliquary's hook, returned

Verbatim from `reliquary_v2.py` (the dark rewrite, the kept v3.3
render), 8 bars, 8th-note tokens, A minor:

```
A3 -  A3 A3 Bb3 -  A3 -      | recitation on A3, the b2 (Bb3) as neighbour
G3 -  -  -  .   A3 G3 F3     |
E3 -  F3 E3 D3  -  E3 -      |
E3 -  -  -  -   -  .  .      | Q hangs on the low E (the 5th)
A3 -  A3 A3 Bb3 -  A3 -      |
G3 -  -  -  .   F3 E3 F3     |
G3 -  F3 E3 C3  -  -  -      |
A2 -  -  -  -   -  .  .      | A lands on the LOW tonic, doubling the bass
```

29 onsets, density 0.23, 1.8 notes/s at 122, held fraction 0.52,
longest 8th run 3, register 45–58, down-steps 0.65, max upward leap 5
semitones, two ♭2 onsets — it passes every sung-grammar and dark check
in `VERIFY.md` as written, recomputed at this tempo. What changes here:

- **the carrier**: `dark_lead(chest=...)`, the promoted 1993 refrain
  voice, not the Juno lead Part 1 used;
- **the chest arc**: 1.0 in chorus 1, 1.15 in chorus 2, 1.3 in the
  final (the no_access ladder);
- **the octave double** on the last chorus pass only (the fusion);
- **the tag** (`A3 G3 E3`, Reliquary's 2-bar tag) becomes the
  pre-chorus answer rather than an ending.

Harmony under it is Reliquary's own loop — **Am F Em Am** per bar (the
minor v, never the ♭VII lift: the Frankfurt trap, `CLAUDE.md`). The
verses sit on a tonic pedal (the EBM tell), the choruses follow the
loop bar by bar.

## Structure (120 bars ≈ 3:56, 8- and 16-bar blocks)

| bars | section | what enters |
|---|---|---|
| 0–8 | **PART 1 QUOTE** | the 808 kit + the Juno arp cell from Reliquary, alone; the bed under it; the kick lands at bar 4 |
| 8–24 | VERSE 1 | the stomp phrase + kick/slam/hats; the verse device (Q3); pad on the pedal |
| 24–32 | PRE 1 | the bass to half-time or offbeat; the tag answers; one EPS hit at 31 |
| 32–48 | CHORUS 1 | the refrain ×2, chest 1.0; chorused offbeat stabs; the Am F Em Am loop |
| 48–64 | VERSE 2 | as verse 1, the device opened up |
| 64–72 | PRE 2 | as pre 1, a notch up |
| 72–88 | CHORUS 2 | the refrain ×2, chest 1.15 |
| 88–96 | BREAK (8) | drums out, the 808 keeps the pulse, organ/pad, the spoken slot if it exists |
| 96–112 | FINAL | the refrain ×2, chest 1.3, + the octave double |
| 112–120 | OUTRO | the arp cell returns and **resolves to A** — the answer Part 1 withheld; fade |

The bookend is inside one track (the blueprint's device compressed):
the opening 8 bars and the closing 8 are the same idea, and the second
one resolves. The eventual *Reliquary (Part 2)* then restates it at
album scale.

## The engine (the bass)

Gated 8ths on a pedal is the archetype — `CELLS["stomp"]`
(`x.x.x.x.x.x.x.o.`, the octave on the & of 4). Built as a phrase from
the start:

| bar of 8 | cell | why |
|---|---|---|
| 0–2 | `stomp` | the pedal |
| 3 | `stomp` + the 5th on 12 | the first answer |
| 4–5 | `stomp` | |
| 6 | `riff` (`x..x..x...x.5...`) | the DAF/Nitzer syncopation as the phrase's question |
| 7 | a walk: 5 → ♭7 → octave into the next phrase | the turnaround (v3's `walk`) |

Plus: 16th accents (quarters lean, the rest sit back at ~0.78), a
4-bar filter-open cycle, `sub` 0.6 in verses / 0.85 in choruses, gate
duty 0.5, and the root following Am F Em Am in the choruses. **The
verse pedal answers** (A → F or A → E in the last two bars of each 8)
rather than sitting on A for sixteen.

## Kit (library calls)

| slot | call | notes |
|---|---|---|
| bass | `sh101_bass.note(m, dur, cutoff=(open, 250), res=2.5, sub=…)` | the phrase above |
| kick | `eps_kick.kick(decay=6.0)` | every quarter; the longer body from no_access |
| snare | `eps_snare.snare()` | 2 and 4, loud — at 122 the snare *is* the aggression |
| hats | `hats.hat()` / `hat(open_=True)` | closed 16ths quiet in verses, open on the & in choruses |
| pad | `juno.pad(chord, BAR, depth=0.0)` | thin voicings above the refrain |
| stab | `juno.stab(chord, depth=0.0)` | chorused, offbeat — the Juno goth colour |
| arp | `juno.arp(chord, bars=1, pattern="down", octaves=1)` | the bookend quote only, at Reliquary's cutoffs |
| 808 | `kit808.kick/snare/hat/…` | the bookend frame only (the *Arp (808 Edit)* lesson) |
| hit | `eps_hit.hit(chord)` | chorus downbeats and the break's edge |
| bed | `seethe.seethe(45, END, throb=…)` | one continuous cursor |
| refrain | `dark_lead.dark_lead(m, dur, chest)` | the quote |
| slot | `machine.machine(x, …)` + `retrigger` | only if Q6 says yes |

## The probes (`procession_probe.py` → `/workspace/music/ebm/procession_probe/`)

1. **the slam** — kick + snare + hats, 4 bars, three snare weights: do
   the two read as one instrument at 122? (Q2)
2. **the engine** — the stomp cell ×8 bars vs the 8-bar phrase, same
   mix: is the phrase enough, and does the F/E root hold below A2? (Q2)
3. **the verse device**, 8 bars each, the three candidates in Q3.
4. **the quote** — the refrain on `dark_lead` over Am F Em Am at 122,
   chest 1.0 and 1.3: does Part 1's hook survive as a chorus? (Q4)
5. **the bookend** — the 808 + arp cell, 8 bars, open (E) then resolved
   (A): does it read as the same idea as Reliquary? (Q5)
6. **the beat** — dry 1993 vs sub-boom + a light pump (0.30, not the
   0.55 of no_access): how much of the modern low end survives at 122?
   (Q7)
7. **the pre-chorus** — three lifts: the snare roll (reads jackhammer?),
   the bass to half-time, a held hit + the tag. (Q8)
8. **the colour** — `hit(kind="orch")` vs `kind="choir"` on a chorus
   downbeat. (Q9)
9. **the slot** — one machine phrase, if Q6 names one.

## Verify (the track script prints)

The standard set (`../VERIFY.md`: section map, hook count ≥ 8, seam
checklist, per-section RMS with the arc, truncation, the bed's tinnitus
check, master guardrails) plus, specific to this track:

- **the quote check**: the refrain's note list is byte-identical to
  `reliquary_v2.py`'s `HOOK` (the bookend's whole point);
- **the bookend match**: the outro's arp note list restates the intro's,
  and its last chord is A where the intro's is E;
- **the phrase check** (from v3): ≥ 4 distinct bass cells over the
  verses and choruses, the pedal moves, accents printed;
- **bass gate duty ≤ 0.5** (stricter than futurepop — this bass stomps);
- **the slam check**: a snare on 2 and 4 in every non-break bar, kick on
  every quarter, and their onsets within 1 ms of each other where they
  coincide;
- **two-voice separation**: the verse device never plays in a chorus,
  the refrain never outside one;
- **the break keeps a pulse**: no window longer than 2 s without an
  onset anywhere in 88–96.

## Open questions for review

1. **Title.** *Procession* recommended (the reliquary carried; keeps
   Reliquary's frame, English, one word). Alternatives: *Vigil*,
   *Anvil*, *Threshold*, *The Nail*, *Ashes* (the source's own, maybe
   too on the nose).
2. **The slam's weight.** The blueprint says kick and snare hit "like
   one instrument" — probe 1 sets the snare weight. Recommended: the
   snare *louder* than no_access's 0.9 and the hats quieter, so 122
   hits harder than 140 did.
3. **The verse device** (the bark's slot, now empty). Candidates:
   (a) **the guitar** — `riff.py`'s palm-muted chug as a texture stab,
   the library's one unused instrument and its declared one-track
   exception ("Norwegian 1993, the metal scene next door");
   (b) **the arp cell** as a counter-sequence, quoting Part 1 twice
   over (hook *and* cell), the no_access tick solution transplanted;
   (c) a low `dark_lead` mutter on the pedal.
   Recommended: (a) — it is the one colour this directory has never
   used, and it is exactly what a 1993 slam had.
4. **The refrain quote: literal or developed?** Recommended literal in
   choruses 1 and 2, developed in the final (the last phrase extended,
   the octave double) — a quote that never changes is a rerun.
5. **The bookend inside the track.** Recommended: open the song with
   the arp cell over the 808 (8 bars) and close with it resolved to A.
   Or keep the 808 out entirely and let the song start on the engine?
6. **The spoken slot.** Leave it empty (recommended: the guitar and the
   engine carry the verses, and the last track spent its slot well), or
   one short machine phrase in the break? If yes, name the phrase.
7. **The beat.** no_access v2/v3 deviated from the 1993 "no pump, no
   sub-boom" and you liked it. Recommended here: **the boom yes, the
   pump halved** (0.30) — at 122 a deep pump is audibly modern, while
   the boom is what made the bass land. Or dry 1993, or the full v3
   treatment?
8. **The pre-chorus lift.** A snare roll is the no_access device and
   may read as the wrong archetype at this tempo. Recommended: the bass
   drops to half-time under a held hit, the tag answers on top.
9. **The chorus hit**: orchestral stack or choir? Recommended choir —
   the liturgical frame, and it separates this track from no_access's
   orchestral hit.
10. **Length.** 120 bars (3:56) recommended. 136 bars (4:27) buys a
    third verse or a longer break; the slam archetype argues against
    it.
