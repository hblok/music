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

Written and rendered 2026-09-11, after the answers below. 16 samples,
6–18 s each, mono, no master; the refrain probes carry a 0.25 reverb so
the voice is judged as it will sit. Seed 1991, `--bpm` to move the
grid, `--only` for a subset. All probe checks pass.

| id | what it asks |
|---|---|
| `01` | **the slam** — the same kick under snare weights 0.90 / 1.15 / 1.40. Which makes the pair one blow? (printed: the blow is 200 ms, no tail) |
| `02a` | **the engine as the blueprint states it** — one cell, gated 8ths, eight bars. The drone the v3 verdict warned about |
| `02b` | **the same eight bars as a phrase** — 4 cells, 12 colour notes, the filter cycle, the accents. The A/B against 02a is the whole argument |
| `02c` | **the chorus roots** — four bars with the bass following A2 F2 E2 A2 (sub squares 55 / 43.7 / 41.2 Hz), four with it pedalling on A2 under the same chords |
| `03a` | **the verse guitar as events** — two bursts per eight bars (bars 3 and 7), the bark's old slot |
| `03b` | the same guitar **as a carpet**, every bar — the A/B that proves why it is two |
| `03c` | the **sparse** DAF cell on the guitar instead of the dense one |
| `04a` | **THE QUOTE** — Reliquary's hook verbatim on `dark_lead` over Am F Em Am, chest 1.0, choir hit on the downbeat |
| `04b` | the same, chest 1.3 (the final chorus's voice) |
| `04c` | the refrain alone, wet — the voice judged on its own |
| `05a` | **the bookend as Part 1 leaves it** — 808 + the down-arp, ending open on Em |
| `05b` | the same cell **resolved to A**, 8ths, cutoff down: the outro reading |
| `06a` | **the beat, dry 1993** — no pump, no boom |
| `06b` | **the beat with the deviation** — the sub-boom under every kick, the pump halved to 0.30 (mean 0.94, floor 0.70) |
| `07` | **the pre-chorus lift** — the bass to half-time under a held choir hit, the tag answering, then the chorus downbeat |
| `08` | **the chorus hit** — choir against orchestral, same chord, same bar |

Listen in pairs: `02a`/`02b`, `03a`/`03b`/`03c`, `05a`/`05b`,
`06a`/`06b`, and the two halves inside `01` and `02c`.

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
  every quarter, and the summed blow shorter than 250 ms;
- **two-voice separation**: the guitar never plays in a chorus, the
  refrain never outside one;
- **the break keeps a pulse**: no window longer than 2 s without an
  onset anywhere in 88–96.

## Open questions for review

**Answered 2026-09-11: yes to every recommendation.** The probe script
is built on these answers.

1. **Title.** *Procession* recommended (the reliquary carried; keeps
   Reliquary's frame, English, one word). Alternatives: *Vigil*,
   *Anvil*, *Threshold*, *The Nail*, *Ashes*.
   **Answer: Procession.**
2. **The slam's weight.** Recommended: the snare *louder* than
   no_access's 0.9 and the hats quieter, so 122 hits harder than 140.
   **Answer: yes** — probe `01` renders 0.90 / 1.15 / 1.40; 1.15 is the
   provisional default in the probe's gain table, the ear settles it.
3. **The verse device** (the bark's slot). Recommended (a) **the
   guitar** — `riff.py`'s palm-muted chug as a texture stab, the
   library's one unused instrument and its declared one-track
   exception.
   **Answer: yes, the guitar.** As events, not a carpet: two bursts per
   eight bars (`03a`), with `03b` kept as the negative control.
4. **The refrain quote: literal or developed?** Recommended literal in
   choruses 1 and 2, developed in the final.
   **Answer: yes** — literal, chest 1.0 → 1.15 → 1.3, the octave double
   and the extended last phrase only on the final pass.
5. **The bookend inside the track.** Recommended: open on the arp cell
   over the 808 (8 bars), close with it resolved to A.
   **Answer: yes** (`05a` / `05b`).
6. **The spoken slot.** Recommended: leave it empty.
   **Answer: yes, empty** — no probe, no `VOICE_GAIN`, no TTS in this
   track.
7. **The beat.** Recommended: the boom yes, the pump **halved** (0.30).
   **Answer: yes** (`06b` against the dry `06a`).
8. **The pre-chorus lift.** Recommended: the bass drops to half-time
   under a held hit, the tag answers on top — no snare roll (that is
   no_access's device and the wrong archetype here).
   **Answer: yes** (`07`).
9. **The chorus hit**: recommended **choir** — the liturgical frame,
   and it separates this track from no_access's orchestral hit.
   **Answer: yes, choir** (`08` keeps the A/B).
10. **Length.** Recommended 120 bars (3:56).
    **Answer: yes, 120 bars.**

## Next

Listen to the probes, then the verdicts go here and the track script
`procession.py` is written from them — not before.
