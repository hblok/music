# Ruin — design notes (2026-09-11, the fourth tracks/ebm/ track)

**The hammer.** A ~3:58 song in the mould of *Soli Deo Gloria*'s
*Spiritual Reality* — the record's **hammer** archetype and the last
of the three (`../../inspiration/Apop_Soli_Deo_Gloria.md` §3, §6):
~109 BPM, F♯ minor, "hammering beat and mechanical bassline" in the
manner of Project Pitchfork, Groth's "musings about his own faith and
mortality". The blueprint's own summary is the whole design brief:
**"the weight comes from the tempo, not density."**

With `procession` in flight this closes the set — slam (122),
jackhammer (140), hammer (109) — and it is the only one of the three
that has to be carried by *space*. Every verdict this directory has
collected so far was about something dragging; at 109 the drag risk is
structural, not incidental, so the counter-measures are declared up
front rather than patched in later.

**The title: Ruin** (answered 2026-09-11). The working title was
*Litany* — a prayer of repeated petitions with a fixed response, which
is exactly what a mechanical 8th-note bass that never leaves the root
*is* — but it collided with `../dune/generate_litany_against_fear.py`.
*Ruin* keeps the register: English, one word, and what a hammer leaves
behind. The petition/response vocabulary below is unchanged; it names
the refrain's two halves, not the track.

**Workflow — probe first** (the standing rule): nothing is rendered as
a track until it has been heard small. `ruin_probe.py` renders ~11
short samples at 109 and prints the inspection the track's verify block
will print; every probe is tied to a numbered question below. The track
script is written only after the probe verdicts.

## Declared up front (not questions)

- **109 BPM, 4/4, F♯ natural minor, 104 bars + a 4-bar tail ≈ 3:58.**
  109 needs `_common.set_tempo(109)` **before importing any instrument
  module** (they bind the grid at import and it asserts otherwise) —
  the `no_access_probe.py` import order. At 109: beat 0.550 s, bar
  2.202 s, 16th 0.1376 s.
- **F♯ minor** is the detected key for *Spiritual Reality* and it is
  free here — the directory holds A minor (`reliquary`, `procession`)
  and C♯ minor (`no_access`). 109 is free repo-wide; the nearest
  neighbours are 104 (`night_pursuit`) and 112 (`kanly`).
- **Script** `tracks/ebm/ruin.py` → `/workspace/music/ruin.wav`
  + `.flac`, one `NAME` constant, the `LISTENING.md` flags (`--solo`,
  `--mute`, `--slice`, `--suffix`, `--stems`), imports from
  `instruments/`, checks skipped on a partial render. Everything else
  per `no_access_v3.py` / the procession script.
- **No new instruments.** The whole track is library calls (the kit
  table below). This is the cheapest of the three archetypes to build
  and that is part of why it is next.
- **The 1993 palette**: SH-101 bass, EPS kick / slam snare / hats, the
  Juno pad and organ, the chopped choir hit, the seethe bed,
  `dark_lead` as the refrain. **No bark** (dead, 2026-09-06), no
  strings, no arp wall, no supersaw, no 808 (that kit is the
  interlude/bookend frame and `procession` owns the device).
- **The refrain is new material** — unlike `procession`, which quotes
  Reliquary's hook. Ruin is not part of the Part 1 / Part 2 pair;
  it is a standalone song in a third key.
- **One continuous cursor**: the seethe bed runs unbroken from bar 0 to
  the tail; every seam is crossed by it plus one named device. The
  break is **8 bars and keeps a pulse** (the phototaxis lesson).
- **Instrumental.** No spoken slot (Q8) — `VOICE_GAIN` does not exist
  in this script.

## The counter-measure to 109 (the load-bearing decision)

The archetype says "a mechanical 8th-note bass that never leaves the
root". The v3 verdict says a repeated cell drones. Both are right, and
the resolution is the thing that makes this track its own:

> **The pitch stays on the root. The phrase happens in the filter, the
> gate and the accent.**

That is what a real SH-101 hammer is — the sequencer holds one note
and the hands are on the cutoff. So the verse engine gets an 8-bar
shape built from *four* moving parameters and zero moving pitches
(§"The engine"), and the choruses are where pitch is finally allowed to
move (the roots follow the chords — the Apop chorus tell). The pedal
released after 24 bars of refusal is the track's one harmonic event.

Second counter-measure: **the hook comes around often.** The petition
is 4 bars (8.8 s), not 8, so a 16-bar chorus holds four statements and
the track carries ≥ 12 against `procession`'s 8. A slow song that
repeats its hook twice as often is not slower; it is heavier.

Third: **verse 2 is half the length of verse 1** (8 bars, not 16). The
song gets impatient. Declared, not accidental.

## The refrain — the petition and the response

8-bar Q/A pair in F♯ minor, 8th-note tokens, baritone, on `dark_lead`.
Bars 1–4 are **the petition**, bars 5–8 **the response**; the petition
is the hook unit and what the hook counter counts.

```
F#3 -  F#3 F#3 G3 -  F#3 -     | recitation on the tonic, the b2 (G3) as neighbour
E3  -  -   -   .  F#3 E3 C#3   | the fall
D3  -  C#3 D3  E3 -  D3  -     | the b6 (D3) turning
C#3 -  -   -   -  -  .   .     | the petition hangs on the 5th — the question
F#3 -  F#3 F#3 G3 -  F#3 -     | the petition restated verbatim
E3  -  -   -   .  D3 C#3 D3    |
E3  -  D3  C#3 A2 -  -   -     |
F#2 -  -   -   -  -  .   .     | the response lands on the LOW tonic, doubling the bass
```

MIDI: F♯2 42, A2 45, C♯3 49, D3 50, E3 52, F♯3 54, G3 55.

29 onsets, density 0.23 (onsets / 16th slots), 1.65 notes/s at 109,
longest 8th run 3, register 42–55 (F♯2–G3, a 13-semitone baritone
span), two ♭2 onsets, down-steps dominant, max upward leap 5
semitones — the same shape that passed every sung-grammar and dark
check on `reliquary` v3.3 and `procession`, recomputed at this tempo.
The 1.65 notes/s is below the 2–4 "sings" band on purpose: this is the
slow track and the note *values* are long, which is what the band
actually measures.

- **the carrier**: `dark_lead(chest=…)`, the promoted 1993 refrain
  voice;
- **the chest arc**: 1.0 in chorus 1, 1.15 in chorus 2, 1.3 in the
  final (the no_access ladder);
- **the octave double** on the final chorus only (the fusion);
- **the organ states the petition alone** in the break — the
  "instrumental statement fills the sample slot" rule, and it is why
  there is no spoken slot.

**Harmony**: **F♯m – D – C♯m – F♯m**, one chord per bar, under the
petition and again under the response. The minor v (C♯m), never the
♭VII lift — the Frankfurt trap, `CLAUDE.md`. Verses sit on the F♯
pedal (the EBM tell); choruses follow the loop bar by bar.

## Structure (104 bars + 4-bar tail ≈ 3:58)

| bars | time | section | what enters |
|---|---|---|---|
| 0–8 | 0:00 | **THE OPENING** (device undecided, probe `10`) | the toll is rejected; three candidates render as (a) the naked blow, (b) the way in, (c) no opening. All three land the kick by bar 4 and quote the petition on the organ from bar 6 (thesis, uncounted) |
| 8–24 | 0:17 | VERSE 1 (16) | the pedal engine + kick every beat + the slam on 2 and 4; no hats for the first 8 (Q3); pad on the pedal from bar 16 |
| 24–32 | 0:52 | PRE 1 (8) | the organ enters; the bass to half-time; the hole on beat 4 of bar 31 |
| 32–48 | 1:10 | CHORUS 1 (16) | the petition ×4, chest 1.0; the roots move F♯–D–C♯–F♯; choir hit on each downbeat of 8 |
| 48–56 | 1:45 | VERSE 2 (8) | the pedal returns, the engine one notch open |
| 56–64 | 2:03 | PRE 2 (8) | as pre 1, plus the hit held |
| 64–80 | 2:20 | CHORUS 2 (16) | the petition ×4, chest 1.15; organ doubling the refrain an octave down |
| 80–88 | 2:56 | BREAK (8) | kick and snare out; the bed keeps the pulse; the organ states the petition alone; the toll returns |
| 88–104 | 3:13 | FINAL (16) | the petition ×4, chest 1.3, + the octave double; the kick to 8ths (Q7) |
| 104–108 | 3:49 | TAIL (4) | hard stop on the downbeat of 104; the bed and the last hit ring out and decay (Q9) |

Hook count: 4 + 4 + 4 = **12 petitions**, plus the break's organ
statement (13) and the intro quote (uncounted). Target **≥ 12**.

## The engine (the bass)

`CELLS["stomp"]` (`x.x.x.x.x.x.x.o.`) on an F♯2 pedal — but built as
an 8-bar phrase from bar 1, with the movement in everything except the
pitch:

| bar of 8 | cutoff (open) | gate | accent floor | what the ear hears |
|---|---|---|---|---|
| 0–1 | 2200 | 0.50 | 0.72 | the statement |
| 2–3 | 1500 | 0.42 | 0.72 | closing — the notes shorten, tension |
| 4–5 | 2800 | 0.50 | 0.60 | the widest opening, the accents bite |
| 6 | 1700 | 0.35 | 0.78 | choked: the petition's own "-" bar |
| 7 | 2400 → walk | 0.50 | 0.60 | the turnaround: 5th → ♭7 → octave into the next 8 |

Plus: quarters lean and the rest sit back (the accent floor above),
`sub` per section (Q2), gate duty ≤ 0.5 everywhere, and the **only**
pitch events in a verse are the bar-7 walk. In the choruses the root
follows F♯–D–C♯–F♯; the chorus register question is the same one
`procession` answered — F♯2 42 (sub square 46.3 Hz), D2 38 (36.7 Hz)
and C♯2 37 (34.6 Hz) are all below the directory's measured-good
55 Hz centre, so the chorus either takes D3/C♯3 (50/49) or pedals on
F♯2 under the moving chords. Probe 04 settles it.

## Kit (library calls)

| slot | call | notes |
|---|---|---|
| bass | `sh101_bass.note(m, dur, cutoff=(open, 250), res=2.5, sub=…)` | the phrase above; `render_cell` for the flat A/B |
| kick | `eps_kick.kick(decay=6.0, drive=…)` | every quarter; at 109 there is room for a longer body than procession's |
| snare | `eps_snare.snare(plate=…, cut=…)` | 2 and 4, **the hammer** — the one dialect where the snare is allowed to ring (Q5) |
| hats | `hats.hat()` | 8ths, quiet, and absent from the first 8 bars of verse 1 (Q3) — no 16th carpet at this tempo |
| pad | `juno.pad(chord, BAR, depth=0.0)` | thin voicings, above the refrain in choruses (the probe-07 lesson) |
| organ | `juno.organ(chord, dur)` | the liturgical colour: pre-choruses, the chorus-2 doubling, the break's solo statement |
| hit | `eps_hit.hit(chord, kind="choir", dur=…)` | the toll (longer `dur`) and the chorus downbeats |
| bed | `seethe.seethe(42, END, throb=…)` | one continuous cursor, rooted on F♯ |
| refrain | `dark_lead.dark_lead(m, dur, chest)` | the petition and the response |

No `kit808`, no `riff`, no `bark`, no `machine`.

## The probes (`ruin_probe.py` → `/workspace/music/ebm/ruin_probe/`)

~11 samples, 6–24 s, mono, no master; the refrain probes carry a 0.25
reverb so the voice is judged as it will sit. Seed per Q1, `--bpm` to
move the grid, `--only` for a subset.

| id | what it asks |
|---|---|
| `01a` | **the drone** — the stomp cell flat on the F♯ pedal, 8 bars, no accents, no cycle, no gate move. The thing the design is defending against |
| `01b` | **the same 8 bars as the phrase table above** — the A/B that proves the filter/gate/accent phrase is enough to save a never-moving pitch |
| `01c` | the phrase with the **pitch** allowed to move instead (a walking pedal) — the control: is the archetype's "root only" actually worth keeping? |
| `02` | **the sub at F♯** — the pedal at `sub` 0.85 / 0.6 / 0.4, the last with the kick up. 46.3 Hz versus the directory's 55 Hz centre |
| `03` | **the hats question** — the same 8 verse bars with no hats / 8ths / 16ths |
| `04` | **the chorus roots**, 12 bars — following down (F♯2 D2 C♯2), pedalling on F♯2, and following up (F♯2 D3 C♯3) |
| `05` | **the hammer snare** — the same kick under plate cut 140 / 220 / 300 ms, then a weight ladder 0.90 / 1.15 / 1.40 |
| `06` | **the space** — the full verse groove with hats off and pad off: kick, slam, pedal. Is the gap between blows the track, or a hole? |
| `07a` | **THE PETITION** — the 4-bar hook on `dark_lead` over F♯m D C♯m F♯m, chest 1.0, choir hit on the downbeat |
| `07b` | the full 8-bar Q/A (petition + response), chest 1.3 — the final chorus's voice |
| `08` | **the toll** — the chopped choir hit at `dur` 0.25 / 0.45 / 0.80 s under a lone kick. Does a struck bell need to exist, or is the EPS hit the toll? (Q6) |
| `09` | **the final's kick to 8ths** — the same chorus bars with quarters, then 8ths (Q7) |
| `10` | **the opening, take two** — the naked blow / the way in / no opening at all, 8 bars each, after the toll was rejected |

Ladders to listen in: `01a` → `01b` → `01c`, the three levels inside
`02`, `03`, `05` and `08`, the three root choices inside `04`.

## Verify (the track script prints)

The standard set (`../VERIFY.md`: section map, hook count, seam
checklist, per-section RMS with the arc, the bed's tinnitus check,
truncation, master guardrails) plus, specific to this track:

- **the pedal check**: the set of bass pitches in every verse is
  exactly `{F♯2}` plus the bar-7 walk notes — printed per section, so
  "root only" is verified and not just intended;
- **the phrase check**: the printed cutoff / gate / accent table per
  8-bar block, and an assertion that no two consecutive bars share all
  three (the anti-drone receipt);
- **gate duty ≤ 0.5** per cell (the stricter 1993 figure);
- **the chorus root ledger**: bass root per bar == chord root per bar;
- **the space check**: onsets per bar in verse sections below a
  declared ceiling — this track's claim is space, so it is measured;
- **the petition count ≥ 12**, full 4-bar statements on any
  instrument (the break's organ counts, the intro quote does not);
- **the voice**: refrain median pitch inside F♯2–G3, density
  0.20–0.50, longest run ≤ 6, held fraction ≥ 0.5;
- **the sub-60 share** per section at F♯ (the 46.3 Hz question), and
  crest ≥ 3.2 in the choruses.

## Open questions for review

1. **Title and seed.** *Litany* (the form names the mechanism) —
   **but it collides**: `../dune/generate_litany_against_fear.py`
   already exists, so one of the alternatives probably has to win:
   *Vigil*, *Toll*, *Threnody*, *Mortal Coil*.
   Answer: Tile: Ruin

2. **The sub at F♯2 (46.3 Hz).** Recommended: `sub` 0.6 in verses and
   0.85 in choruses, with the kick carrying the weight the sub gives
   up — but probe 02 decides, and a bad answer means the key moves to
   G♯ minor rather than the register moving up.
   Answer: yes

3. **Hats.** Recommended: 8ths only, and none at all for the first 8
   bars of verse 1. A 16th carpet at 109 fills exactly the space the
   archetype is made of.
   Answer: yes

4. **Verse 2 at 8 bars** instead of 16. Recommended yes — the
   anti-drag measure, and the asymmetry is audible as intent.
   Answer :yes

5. **The snare's size.** Recommended: plate cut 220 ms, longer than
   `procession`'s 140 — the hammer is the one dialect where the blow
   is allowed a tail. This is a declared stretch of the truncation
   rule; argue it or keep 140.
   Answer: yes

6. **The toll device.** Recommended: **no new instrument** — the
   chopped choir hit at a long `dur` under a lone kick is the toll. If
   probe 08 says it reads as a stab and not a bell, the fallback is a
   detuned `eps_kick` at 55 Hz doubling it, still no new module.
   Answer: No - the toll was not great.
   
   **Take two (2026-09-11): "no ideas right now — let's just try
   something and adjust later."** Probe `10` renders three candidate
   openings with nothing decided between them, each 8 bars ending with
   the engine running, so only the way in differs: **(a) the naked
   blow** — kick and slam together on beats 1 and 3, nothing else, 1.1 s
   of silence between blows, the bed creeping in at bar 2 and the pedal
   at 4; **(b) the way in** — no_access v3's device, which the ear has
   already passed, the bed swelling from silence under one low organ
   chord and a slow noise sweep, kick at bar 4; **(c) no opening at
   all** — the engine simply starts, the "skip long intros" rule taken
   to its limit, and the reading that risks repeating the "starts
   abruptly" verdict. Measured first two bars: **-10.4 / -24.1 / -5.7
   dBFS**, an 18.4 dB spread, so they are genuinely three different
   proposals and not three mixes of one. No `eps_hit` in any of them.

7. **The kick to 8ths in the final chorus.** Recommended yes, final
   only — at this tempo it is the one energy move available that adds
   no density.
   Answer: unsure

8. **The spoken slot.** Recommended **no**. `no_access` has it, the
   break here is better served by the organ stating the petition
   alone, and this is the track where silence between blows is the
   material.
   Answer: no

9. **The ending.** Recommended: hard stop on the downbeat of bar 104
   plus a 4-bar decay tail. `no_access` faded and `procession` fades;
   the hammer should stop.
   Answer: hard stop.

10. **Anything that should be borrowed from `procession`'s probe
    verdicts** once those are heard — in particular the accent floor
    and the filter-cycle widths, which were re-tuned there the same
    day. If the probes land before this one is written, its defaults
    inherit from them.
    Answer: no

## Probe amendments (2026-09-11, written and rendered, before any listening)

`ruin_probe.py` is written and its 13 files are rendered to
`/workspace/music/ebm/ruin_probe/`; all probe checks pass. The
recommendations above are the probe's DEFAULT state and every ladder
keeps its alternative, so answering the ten questions later costs one
re-render. Three things changed on the way, and the plan changes with
them:

1. **The engine cell is `hammer` (`x.x.x.x.x.x.x.x.`), not
   `CELLS["stomp"]`.** Stomp puts an octave on the "and" of 4, which is
   a pitch event — and this track's entire claim is that the pitch never
   moves. The verify block's pedal check now reads exactly: bars 0–6 of
   every phrase contain interval 0 and nothing else, with bar 7's walk
   as the only pitch event in a verse.
2. **Q7's answer is conditional: when the kick takes the 8ths, the hats
   give them up.** The first rendering failed the space check — kick 8 +
   slam 2 + hats 8 + bass 8 is 26 onsets against this track's ceiling of
   24. Probe 09 now renders three readings (quarters with hats at 22,
   8ths with hats at 26 and over, 8ths without hats at 18). The fix is
   musically the obvious one and it is now the recommendation.
3. **The anti-drone check was measuring the wrong thing.** The filter,
   gate and accent cycle turns every *two* bars by design, so a
   per-bar "nothing repeats" assertion was always going to fail. It now
   checks that no state holds longer than 2 bars and that at least 4
   distinct states appear across the 8.

**Measured, supporting Q2** (probe 02, the sub at F♯2 whose square lands
at 46.2 Hz):

| sub | sub-60 share | against the guardrail band 0.60–0.70 |
|---|---|---|
| 0.85 | 0.71 | just over |
| **0.60** | **0.65** | **inside — the recommendation holds** |
| 0.40 | 0.60 | at the floor |

The low root is affordable after all: at `sub` 0.6 the track sits mid-band
without the kick having to compensate. The ear still decides whether
46 Hz has body or just weight.

**The space, measured** (probe 03 and 06): a verse bar runs 14 onsets
with no hats and 22 with 8ths, against `procession`'s 30. The 16th
carpet reaches 30 and is rendered as the rejected reading, so the A/B
is real rather than assumed.

## Built (2026-09-12) — `ruin.py` → `/workspace/music/ruin.wav`

104 bars + a 4-bar decay, 3:58, all checks pass. Every answered
question is followed as given. **Four things were chosen without an
answer**, each a single constant at the top of the script so changing
one is a grep and a re-render:

| constant | chosen | why, and the fallback |
|---|---|---|
| `OPENING` | `"blow"` | the naked blow is the only candidate that belongs to this archetype alone, and the only opening in the directory that is a bare drum. `"way_in"` and `"none"` are wired |
| the verse pedal | both readings, as development | you liked `01b` and `01c` equally, so verse 1 refuses to move at all and verse 2 gives in once, answering A2–B2 in its last two bars. The refusal is the idea; giving in is the development |
| `CHORUS_ROOTS` | `"up"` | `"down"` puts D2 and C♯2 sub squares at 37 and 35 Hz, far under the measured-good 55. `"pedal"` is `procession`'s answer and would waste the one harmonic event this track has |
| `KICK_8THS` | `True` | Q7 was "unsure"; the probe found it fits only if the hats give up their eighths, so they do. Set `False` to drop it |

Two flaws the verify block caught, both in the arc:

1. **The pre-choruses were louder than the choruses they lead into**
   (0.211 against 0.196) with a 0.76 sub-60 share, outside the master
   guardrail band. The half-time bass was running at the chorus sub of
   0.85, so the *build* was heavier than the *arrival*. A pre builds by
   removing rhythm, not by adding weight: `SUB_PRE` is now 0.45.
2. **`VERIFY.md`'s standard check 2 was missing.** "Chorus > its
   pre-chorus — the drop actually lands" is in the standard set and this
   script did not have it, which is precisely why flaw 1 could pass.
   Added, along with a sub-60 guardrail check.

Arc now: verse 1 0.155 → pre 1 0.184 → chorus 1 0.196 → final 0.214,
**+2.0 dB verse to chorus**, −8.2 dB into the break. Twelve petitions,
busiest bar 22 onsets against the ceiling of 24, the slam truncated at
its declared 220 ms.

One consequence of `CHORUS_ROOTS = "up"` worth hearing for: the
choruses carry *less* low end than the verses (sub-60 0.46 against
0.58), because the roots climb to D3 and C♯3. That is the price of
letting the pitch move at all.

## Next

1. **Listen to the probes** — the ladders are `01a → 01b → 01c`, the
   three levels inside `02`, `03`, `05` and `08`, the three roots inside
   `04`, and the three kick readings inside `09`.

   drone-as-phrase is good, phrase with moving pitch is als good.

2. Answer the ten questions above, now that the alternatives are audible.
3. Only then `ruin.py`.


## 2026-09-16 — the listen verdict, and the hook is not new

**Verdict on `ruin.wav` (with Watchfire and the Procession probes, heard
together): "not bad, but flat, boring, and similar."** Three things
found on reading the three scripts against `no_access_v3.py`, the one
track that "works quite well":

1. **The hook is Reliquary's hook transposed to F♯.** Bar for bar:
   `A3 - A3 A3 Bb3 - A3 -` became `F#3 - F#3 F#3 G3 - F#3 -`, the held
   ♭7 + three-note tail in bar 2 likewise, the response likewise. The
   "Declared up front" claim that the refrain is new material was wrong;
   Procession quotes Reliquary on purpose, so two of the three new tracks
   sing the same tune.

2. **Every seam device that made No Access work was declared out of this
   track.** Kick figures, snare runs, the roll + riser, the downsweep,
   the silent beat — `EBM_1990s.md` §6/§9's kit. Ruin has one hole
   before each chorus and a hit. The purity was the flatness.

3. **Nothing varies inside a section.** Six statements of the hook are
   identical (the chest knob aside); the per-bar filter cycle was
   measured "subtle" on the procession probes. The state / vary / answer
   rule was not applied.
   

What changed today, and nothing else (one song at a time): the seam
devices moved into the library (`instruments/devices.py`, all of them
already passed by ear inside No Access v3), and `ruin_probe.py` grew
probes 11–13. `ruin.py` is untouched.

### Three hook candidates (probes 11a/b/c solo, 12a/b/c in the chorus)

All three pass every refrain check (density 0.20, held 0.54, register
F♯2–G3, descending, no leap over a 5th, two ♭2 onsets, Q hangs on C♯,
A lands on F♯). They differ in *grammar*, which is the thing the control
shares with Reliquary:

| | grammar | what it is |
|---|---|---|
| **control** (`11`) | hammered repeats on the beat, held ♭7 | Reliquary transposed — the built track |
| **A, the off-beat** (`11a`) | every note enters on the "and", off the kick; the phrase-end tone alone lands on the beat | the petition CLIMBS A2 → B2 → C♯3 → D3 → G3 before hanging on C♯; the response climbs the same way and falls through to F♯2. The one contour Reliquary never has (it starts at the top) |
| **B, the litany** (`11b`) | one tone held across beats 1–2, a falling tail on 3–4, every bar | recitation: the fewest gestures, the most vocal, the liturgical reading |
| **C, the hammer** (`11c`) | pairs of repeated 8ths (short-short-long), silence between the pairs | the voice strikes like the drum; the space claim carried into the melody |

`11` is the 04c format (solo, wet, chest 1.0 — the one the Procession
verdict loved); `12` is the same eight bars in chorus 1's context. A/B
any candidate against the control:
`python3 ../../tools/ab.py 11_hook_control_solo.wav 11a_hook_offbeat_solo.wav --bpm 109 --bars 4`.

### The seams (probe 13)

Eight bars in this track's context: kick figure B on bar 1, the snare
run on the last beat of bar 3 (the hats yield that beat), the two-bar
roll + riser with the bass to half-time, then the chorus landing with
the hit, the downsweep and the petition. Measured: the figure-B bar 23
onsets, the run bar 24 — the fills touch the ceiling and do not pass
it, so the space claim survives them.

### Questions 11–14

11. **The hook.** Control / A / B / C — from `11` first, then `12` for
    the one(s) that survive. Recommended **A**: it is the only candidate
    whose contour is not Reliquary's, and the off-beat entry is the one
    syncopation in the whole directory. "None — keep the control and
    find the identity elsewhere" is a valid answer.
    Answer: B - litany - clearly the most fitting.

12. **The seams.** Yes to the kit as probe 13 plays it (figure B every
    4th bar, the run on bars 4n+3, roll + riser into each chorus, the
    hit + downsweep on the chorus downbeat), or name the ones to drop.
    Recommended: all of it; it is what No Access has and this does not.
    Answer: Yes

13. **Developing the hook.** The built track states it six times
    unchanged. Next round, shall the second statement in each chorus be
    a *varied* one (the response altered, or the organ answering the
    petition in the gap, or the octave double entering early) — probed
    on the winning candidate, not guessed? Yes/no; the how is the probe.
    Answer: Yes, varied.

14. **Verse 2's engine.** The `riff` cell (`x..x..x...x.5...`, the DAF
    syncopation, unused by any track) instead of the hammer for verse
    2's eight bars — the verse's one identity move, and the archetype's
    "pitch stays put" claim holds (root and 5th only). Probe it next
    round, after the hook is chosen? Yes/no.
    Answer: Yes.

Still open from the built track's docstring: `OPENING` (probe 10),
whether the verse pedal moves (01b/01c), `KICK_8THS` (09). Those wait
for the same listen.

Answer: The opening - let's split the probes for that, because it not clear which is which.

### Round two (2026-09-16, the answers to 11–14 in): probes 10a/b/c, 14a/b/c, 15a/b

Answers: **B, the litany** ("clearly the most fitting"); the seam kit,
yes; the second statement varied, yes; the riff cell for verse 2, yes —
both of those said "probe it", so this round renders them, and the
opening is re-rendered as three files because the combined probe 10
made it unclear which was which. `ruin.py` is still untouched;
`ruin_v2.py` is written after questions 15–17.

| probe | what |
|---|---|
| `10a` / `10b` / `10c` | the opening, one candidate per file: the naked blow / the way in / no opening. Same renderings as before, split |
| `14a` **the litany form** | a whole 16-bar chorus: statement 1 = P1 + the response; statement 2 = a **second petition** (opens on the ♭2 G3, leans on it again in bar 3) + the **same response**. A litany's petitions change and its response is the constant — over the track: P1 A, P2 A, P1 A, P2 A, P3 A … |
| `14b` **the organ answers** | statement 2 = the litany unchanged, but the low organ answers from below (E2 D2 C♯2, then A1 G♯1 F♯1) while the voice holds each phrase-end tone — call and response made literal, a second voice in the gap |
| `14c` **the double early** | statement 2 = the litany + its octave-up dark_lead double at 0.35 (the built track's final-only device brought forward) — the voice thickens, the notes do not change |
| `15a` / `15b` | verse 2 (six bars on the pedal, then A2 and B2) on the **hammer** as built, then on the **riff** cell `x..x..x...x.5...`: five onsets a bar against eight (18 per bar against 22), beat 2 left to the slam alone, the 5th landing with the slam on 4. Both keep the pitch-stays-put claim |

P2 passes every refrain check with the response (density 0.20, held
0.54, down-steps 0.64, three ♭2 onsets).

### Questions 15–17

15. **The opening** (`10a` / `10b` / `10c`). Recommended **10a, the
    naked blow** — the only opening in the directory that is a bare
    drum, and the archetype's own gesture. `10b` is No Access's device
    reused; `10c` risks "starts abruptly".
    Answer: b

16. **How the second statement varies** (`14a` / `14b` / `14c`, or a
    combination — a and b stack; c stacks with either). Recommended
    **14a**, the litany form, because it is what the word means and it
    gives the track a *third* petition for the final; **14b on top of
    it** if the organ answer reads as a voice and not as clutter.
    Answer: c_varied_double

17. **Verse 2's engine** (`15a` hammer / `15b` riff). Recommended
    **15b** — the verse's one identity move, more space not less, and
    the syncopation this directory otherwise lacks. If it reads as a
    different song, verse 2 stays on the hammer and the riff is dropped.
    Answer: a - hammer

Then `ruin_v2.py`: the litany as the refrain (P1/P2 per Q16), the seam
kit at every verse→chorus and into the final, the opening per Q15,
verse 2 per Q17. Still standing from the build unless you say
otherwise: verse 1 refuses to move and verse 2 gives in (01b + 01c as
development), `CHORUS_ROOTS = "up"`, `KICK_8THS = True` with the hats
out, the hard stop.

## Built v2 (2026-09-16) — `ruin_v2.py` → `/workspace/music/ruin_v2.wav`

Answers to 15–17: **10b the way in; 14c the double early; 15a the
hammer for verse 2.** With 11–14 (the litany; the seam kit; varied;
riff-probed-and-declined), v2 is exactly:

- **the litany** as the refrain — 13 petition statements, chest 1.0 /
  1.15 / 1.3 as before; the verify block now checks bars 1–3 and 5–7
  open on a held tone and that bar 1's rhythm is not Reliquary's
  (`[0, 4, 6, 7]` against `[0, 2, 3, 4, 6]`)
- **the seam kit** — figure B on 14 bars (4n+1 of the verses and
  choruses), the run on 18 bars (4n+3, the hats yield beat 4), the
  two-bar roll + riser into 32 / 64 / 88, the holes at 31.75 / 63.75
  measured 10.2 / 7.6 dB deep, one true silent beat at 87.75 (−240
  dBFS, bed included), a downsweep on every chorus entry. The roll bars
  are the declared exception to the space ceiling; every other bar
  measures ≤ 24 (busiest 24)
- **the double on statement 2** of each chorus and on both statements
  of the final, at 0.35
- **the way in** — the bed swells over two bars under the low organ i
  and the noise sweep; the kick at bar 4; the organ quote at 6. The bed
  cursor check starts after the swell
- verse 2 on the hammer, giving in A2–B2 in its last two bars, as v1
- the break now has the organ actually under the petition (v1 said so
  and did not do it)

Arc: verse 1 0.153 → pre 1 0.182 → chorus 1 0.197 → final 0.210;
**+2.2 dB verse to chorus, +0.7 dB pre to chorus** (the roll makes the
pre heavier; it still lands), −7.8 dB into the break. All checks pass.

Kept for the verdict: `ruin.wav` (v1) is untouched, so the A/B is the
two full renders, or slices of both — `--slice 24 48` is pre 1 + chorus
1, where every change but the way in is audible at once.

## Built v3 (2026-09-18) — `ruin_v3.py` → `/workspace/music/ruin_v3.wav`

Verdict on v2: *"not bad at all. However, the main problem is the bass
line (stem). The SH-101 bass is just too timid. It reads like a 1980s
commodore game, as opposed to a heavy bold EBM goth track."* v3 changes
the bass and nothing else — the arrangement, the litany, the seam kit,
the way in, the doubles and the master are v2's.

### The fork, not an edit

`instruments/sh101_bass_ruin.py` is a **fork** of the library module.
`sh101_bass.py` is imported by reliquary, no_access, watchfire and the
procession probes, every one of which has a verdict attached to a
render, so editing it risks changing what a judged track sounds like
when re-rendered. (It *was* edited first, and reverted — the fork rule is
now written down in `instruments/README.md`.) The fork overrides `note()`
alone, imports `CELLS` and `svf_lowpass` from the original, and asserts
in its audition that its defaults are bit-identical, so it is a superset.
Two new knobs, both TODO.md §6's deferred "second oscillator":
`detune` (unison spread in cents) and `sub_wave` ('square' | 'sine').

### Four theories that measured DOWN (recorded so they are not re-run)

Probe 16 was a cumulative ladder built on "the note has no midrange":

1. **The EPS dirt is not the 8-bit read** at this register — `hold=1` and
   `hold=2` measure identically (crest 2.96, centroid ~130 Hz). The note
   is lowpassed long before the decimation has anything to alias. This
   was my first suspect and it is simply wrong.
2. **The filter floor does nothing** — 800 / 1500 / 2500 Hz all give the
   same spectrum, because a `1/k**1.1` saw at 92.5 Hz has almost no
   harmonic energy for the filter to pass in the first place.
3. **A parallel band-passed distorted "grind" layer** only cost crest
   (1.36 → 2.18) and moved the 200–800 Hz share by a rounding error.
4. **The sub-120 share is ~0.85 even with `sub=0.0`** — at F♯2 the
   *fundamental* (92.5 Hz) is itself under 120 Hz, so that share was
   never a fault to fix. This killed the whole "it is all rumble"
   framing, including my own earlier push to *raise* the sub.

And one measurement that killed the simplest reading of all: in a v2
verse **the bass stem runs 6.9 dB LOUDER than the drums** (−18.4 against
−25.3 dBFS), so "timid" was never a level problem.

Spectral share did not predict the verdict. Probe 17 therefore stopped
arguing from numbers and rendered five readings that differ audibly.

### The five readings (probes 17a–17e), and what v3 ships

| probe | reading | measured |
|---|---|---|
| `17a` | the control (v2) | stem crest 2.96, in-context sub-60 0.60 |
| `17b` | **dense** — unison 18 c, sine sub 0.8, drive 2.0, dirt off, gate cycle ×1.3 | crest 2.96 → 1.96, **+2 dB RMS at the same peak**: a wall, not a blip |
| `17c` | **square** — square oscillator, sub back to 0.35, floor 900 Hz | triples the 800 Hz–3 kHz share, but sub-60 collapses to 0.04 — hollow, Nitzer/DAF, gives up the low end |
| `17d` | **octave** — dense + a quiet copy an octave up, floor 1400 Hz, gain 0.30 | sub-60 **0.60 → 0.49** while the bass gets louder: the size moves into the midrange, where small speakers live |
| `17e` | **wide** — the octave copy panned | a declared deviation (§9 says bass mono-centre): bigger on headphones, thinner on a club system |

**v3 ships `17d`**, as `BASS_READING = "octave"` — one word switches to
any of the five, so the verdict costs a re-render and no edit. The gate
stretch (0.50 → 0.65) is a declared deviation from the 1993 "gate ≤ 0.5"
figure, argued on the grounds that the gap is exactly what made it a
blip.

### Two things tuned alongside the bass (both forced, both measured)

The denser bass broke two of v2's checks, which is why they moved:

1. **The composed holes filled in.** At gate ×1.3 the note on step 8 of
   the `hole` cell rang past beat 4 and the hole measured under 6 dB
   deep. The stretch now applies to the ENGINE cells only (`hammer`,
   `walk`); the pre-chorus half-time cells keep v2's 0.5. Holes back to
   12.5 / 9.5 dB.
2. **The chorus stopped clearing its verse.** The denser bass lifted the
   verses +2.8 dB but the choruses only +1.7 (the chorus sub clamps at
   1.0, and its roots climb to D3/C♯3 where there is less low end to
   gain), so the arc fell to +1.5/+1.3. `SECTION_GAIN` sits the verses
   back one more notch: 0.84/0.86 → 0.78/0.80. Arc restored to
   **+2.0 / +1.8 dB**.

All checks pass. Arc: verse 1 0.202 → pre 1 0.229 → chorus 1 0.239 →
final 0.248, −10.6 dB into the break. v1 and v2 are kept, so the A/B is
three renders; `--solo bass,bassoct --slice 16 24` is the stem the
verdict was about.
