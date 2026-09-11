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

Written and rendered 2026-09-11, after the answers below; re-rendered
the same day with the measured recommendations applied (the section
after the verify block — so the files carry the recommended state, and
the ladders keep the alternatives). 18 samples, 6–24 s each, mono, no master; the
refrain probes carry a 0.25 reverb so the voice is judged as it will
sit. Seed 1991, `--bpm` to move the grid, `--only` for a subset. All
probe checks pass.

| id | what it asks |
|---|---|
| `01` | **the slam** — the same kick under snare weights 0.90 / 1.15 / 1.40. Which makes the pair one blow? (printed: the blow is 200 ms, no tail) |
| `02a` | **the engine as the blueprint states it** — one cell, gated 8ths, eight bars, flat (no accents, no cycle). The drone the v3 verdict warned about |
| `02b` | **the same eight bars as a phrase with the no_access v3 knobs** — 4 cells, 12 colour notes, accent floor 0.78, cycle 2400 / 1700 / 2900 / 2000 Hz. The middle of the ladder |
| `02c` | **the chorus roots**, 12 bars — the bass following A2 F2 E2 A2 *down* (sub squares 55 / 43.7 / 41.2 Hz), then *pedalling* on A2 under the same chords, then following *up* A2 F3 E3 A2 (subs 55 / 87 / 82 Hz) |
| `02d` | **the phrase turned up — now the default in every other probe**: accent floor 0.6 and the wider cycle 2800 / 1300 / 3400 / 1700 Hz |
| `03a` | **the verse guitar as events** — two bursts per eight bars (bars 3 and 7), the bark's old slot; gain 0.75 |
| `03b` | the same guitar **as a carpet**, every bar — the A/B that proves why it is two |
| `03c` | the **sparse** DAF cell on the guitar instead of the dense one |
| `03d` | **the guitar's level** — the same 4-bar verse three times, the burst on bar 3 at 0.45 / 0.75 / 1.10 |
| `04a` | **THE QUOTE** — Reliquary's hook verbatim on `dark_lead` over Am F Em Am with the bass pedalling A2 (sub 0.6, the boom and the pump under it), chest 0.8 (chorus 1), the choir hit at 0.35 s |
| `04b` | the same, chest 1.3 (the final chorus's voice) |
| `04c` | the refrain alone, wet, chest 0.8 — the voice judged on its own |
| `05a` | **the bookend as Part 1 leaves it** — 808 (Reliquary's decay 0.2, the kick tuned to A1 = 55 Hz) + the down-arp, the bed's sub at 0.3, ending open on Em |
| `05b` | the same cell **resolved to A**, 8ths, cutoff down: the outro reading |
| `06a` | **the beat, dry 1993** — the pedal with the sub square at 0.85, no pump, no boom |
| `06b` | **the beat with the deviation** — the pedal with the sub square down to 0.6, the boom's sine carrying 55 Hz under every kick, the pump halved to 0.30 (mean 0.94, floor 0.70) |
| `07` | **the pre-chorus lift** — the bass to half-time under a held choir hit, the tag answering, **the hole** (beat 4 of the last pre bar: no drum, no bass — 17.5 dB down), then two bars of the chorus landing (engine on the pedal + boom, stabs, hit, the refrain's first bars) |
| `08` | **the chorus hit** — choir at 0.35 s against orchestral at 0.25 s (each as it would ship), same chord, same bar |

Listen in ladders: `02a` → `02b` → `02d`, `03a`/`03b`/`03c` and the
three levels inside `03d`, `05a`/`05b`, `06a`/`06b`, the three weights
inside `01` and the three root choices inside `02c`.

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

## Probe measurements and recommendations (2026-09-11, before any listening)

No ears were involved: this is what the inspector (demucs stems + pyin)
and a per-bar band analysis say about the 18 files, and what the
numbers recommend. **The listen verdicts overrule every line below.**
Scripts: the probe's own prints, plus `metrics.py` / `solo.py` /
`remeasure.py` in the session scratchpad (not kept).

### What the numbers found

1. **The engine phrase is real but subtle; the drums swallow most of
   it.** Bass alone, per-bar spectral centroid: the flat cell moves
   1 % across eight bars, the v3 phrase 20 %, the bold phrase 28 %.
   Quarters-vs-offbeat accent: 0.0 / +1.2 / +2.9 dB. In the full mix
   the v3 phrase shows as a 1.4 dB per-bar RMS spread against 0.6 dB
   flat, and a centroid std of 84 Hz against 22 — measurable, small.
   At 122 with gated 8ths there is no phrase that makes the bass
   *interesting on its own*; it can only stop being a drone.
2. **The chorus roots.** Bass alone, `sub` 0.85: following *down* to
   F2/E2 lifts the sub-50 Hz band +6–7 dB while the 60–250 Hz body
   stays put, so body-minus-sub collapses from +6.2 dB (A2) to 0.0 (F)
   and −1.5 (E) — rumble, not bass. Following *up* to F3/E3 does the
   opposite (body-minus-sub +20 / +18 dB: bright and thin, and a leap
   of a 6th). The pedal holds +6 dB everywhere. The demucs bass stem
   transcribes the SH-101 at **A1** (55 Hz) throughout — the sub
   square, not the saw, is the pitch the tracker takes as the bass.
3. **The guitar at the probe's first gain (0.35) was buried**: −20 dB
   under the engine whole-bar, −10 dB in its own 400–1500 Hz band,
   and the separated "other" stem sat 11 dB under the bass. At 0.75
   the burst is −3.3 dB in that band and +2.7 dB in 1.5–5 kHz — a
   texture that is heard; at 1.10 it is level with the engine (a
   second lead, wrong). The sparse cell is 3 dB quieter again with
   half the chugs. Files 03a–c were re-rendered at 0.75 before anyone
   listened; 03d holds the ladder.
4. **The quote holds its room** — voice band (180–520 Hz) +6.5 dB
   above the pad/stab band, pads' lowest note 247 Hz over the
   refrain's 233 Hz ceiling, the grammar checks all pass — **but the
   stem transcribes the refrain at the chest octave**: pyin on the
   "other" stem reads A2 / B♭2 / E3 for the hook, not A3 / B♭3 / E3.
   At chest 1.0 the octave-below layer is at least as loud as the
   voice, and its A2 (110 Hz) is the bass's nominal root.
5. **The bookend reads.** High-passed chroma of the last bar: 05a
   B / E / G (E minor, open), 05b E / C / A (A minor, resolved); the
   arp owns 200–1500 Hz by +8 dB while the 808 owns the rest. The
   intro is the sub-heaviest probe (sub-60 share 0.67–0.69): the 808
   kick at 48 Hz and the bed's sub sit in the same octave.
6. **The beat deviation is small on a pedal.** The boom (0.45) in the
   30–70 Hz band measures −13.2 dB, the bass's own sub square in that
   band −13.1 dB — the same thing twice; net +0.7 dB. The 0.30 pump is
   −0.5 dB on average, −3.1 dB at its floor, below 0.9 for 22 % of the
   time. Both are subtle by design; neither is the no_access feel.
7. **The pre-chorus lifts by about 0.7 dB twice** (verse → pre → the
   chorus landing), the tag reads +2.4–3 dB in the voice band, and the
   half-time bass drops *motion*, not level. A change of gear, not a
   climb.
8. **Choir vs orchestral hit are near-identical by numbers** (centroid
   2390 vs 2470 Hz, −20 dB at 200 vs 220 ms); the choir is 2–3 dB
   softer between 1 and 8 kHz.
9. **The slam weights**: the kick band is constant, the snare body
   climbs −30.8 / −28.5 / −27.4 dB and the wires with it; at 1.40 the
   snare owns the file's peak (crest 4.8 → 5.8) — headroom the master
   pays for. The blow is 200 ms with no tail at every weight.

### Recommendations (what the track script should do, pending the ear)

- **Chorus bass: the A2 pedal** under Am F Em Am (02c's middle
  third). The motion comes from the walk and riff bars, the pad and
  the stabs following the loop, and the refrain landing on A2. Never
  F2/E2 on this instrument; F3/E3 only if the ear wants one leap as a
  one-time colour in the final chorus.
- **Build with the bold phrase knobs** (02d: accent floor 0.6, cycle
  2800 / 1300 / 3400 / 1700) unless 02d sounds like the bass pumping
  on its own — then 02b's. Either way, accept that the interest at 122
  lives in the events around the engine, not in it.
- **Guitar at 0.75**, dense cell, bars 3 and 7 of every verse 8 (03a).
  Verse 2 may add a third burst (bar 5) as "the device opened up".
- **Chest arc 0.8 → 1.0 → 1.3**, not 1.0 → 1.15 → 1.3: chorus 1 at
  Reliquary v2's own chest so the top voice owns the pitch, then the
  voice deepens across the song. Keep the `sub` square out of the way
  of the chest: see the next point.
- **Beat: keep the 0.30 pump, keep the boom, and drop the chorus
  `sub` from 0.85 to 0.6** so the boom's clean sine carries 55 Hz
  instead of doubling the square (whose odd harmonics at 165 / 275 Hz
  sit under the refrain's chest). Verify prints sub-80 share; expect
  it inside no_access's 0.45–0.75 window.
- **Snare 1.15** everywhere, the hats at 0.20; 1.40 only if 1.15
  sounds polite. The master's crest is the reason, not taste.
- **Pre-chorus: keep the device and add one composed hole** — the
  drums out on beat 4 of the last pre-chorus bar (one beat, not
  silence: the bed and the tag's last note carry it), so the chorus
  downbeat slams *into* something. The no_access silent beat, scaled
  to the slam. Verify: the hole is ≥ 6 dB under the surrounding beats.
- **Choir hit as planned**, `dur` 0.35 rather than 0.25 so it reads as
  a voice; if the ear cannot tell 08's halves apart, the frame decides
  and the choice stays choir.
- **Intro: cap the sub.** Under the bookend run the bed with `sub`
  lowered (or the 808 kick's `decay` shorter) so the intro's sub-60
  share prints ≤ 0.6; the verify block should check it.

### Applied to the probe script (same day) — what changed on the way

All of the above is now the probe script's default state and every
file was re-rendered (nothing had been listened to). Three things
moved while applying:

- **The intro sub check was wrong-headed.** With the bed's sub at 0.3
  the intro still measured 0.67: the 808 kick alone is 0.8 sub-60 by
  nature (a 48 Hz sine), the bed sits 20 dB under it. So: the kick
  takes Reliquary's own `decay=0.2` (1.05 s sounding instead of 2.3)
  and is **tuned to A1 = 55 Hz** (the default 48 Hz sits a
  quarter-tone under G — the earlier chroma read G / F♯ for a reason);
  the probe checks the kick's length, and the track's verify will
  compare the intro's 30–70 Hz *level* to the chorus's, not a share.
- **The hole takes the bass out too.** Drums only measured 4.9 dB
  down (the half-time quarter on beat 4 filled it); with the bass's
  last-bar cell `x...x...x.......` it is 17.5 dB down and the bed, pad
  and the tag's last note carry it.
- **02b keeps the v3 knobs explicitly** so the engine ladder stays
  flat → v3 → bold while bold is the default everywhere else.

### Plan changes these imply

`bass_spec`: chorus root A2 always (the ledger check becomes "bass root
== A2 in every chorus bar; the pad follows the loop"), `sub` 0.6 in
the choruses, the bold accent/cycle knobs; `REFRAINS` chest (0.8,
0.8, 1.0, 1.0, 1.3, 1.3); `GAIN["guitar"]` 0.75; a `HOLE` constant
(bars 31.75–32, 71.75–72, 95.75–96: drums *and* bass out, the bass's
last pre bar on the hole cell); the choir hit's `dur` 0.35; the 808
kick `decay=0.2, f0=55.0` in the bookends; an intro level check (30–70
Hz within 1 dB of chorus 1). Everything else stands.

## Next

Listen — the ladders in the probe table — and write the verdicts under
"Probe measurements" as answers. Then `procession.py`, not before.
