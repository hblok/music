# Eisgang — design notes (the circle form)

Composition document for review before writing `eisgang.py`
(→ `eisgang.wav`; filename follows the title — see question 1).

Inspiration: **one motif, not a piece** — W3 "Stamping feet" from
Vivaldi's Winter (`../../inspiration/Winter_Vivaldi.md`, mvt I mark C).
This is NOT a Vivaldi track and must not sound like one: no theme is
lifted, no other Winter motif is used (the drawer stays shut — see
"What we take" below). What W3 gives us is three *behaviors*:

1. a two-bar cell that alternates **hammer** (one pitch, driving
   repetition) and **oscillation** (two pitches, a wide interval);
2. a bass that **bounces octaves, then plants** — motion, landing,
   *rest* — instead of rolling continuously;
3. harmony that **travels the circle of fifths and still loops** —
   a groove that moves without ever leaving home ground.

**The story**: Eisgang — the moment the frozen river breaks and the ice
starts moving. Keep moving or freeze. The harmony can never sit still
(it walks the circle), the bass runs and plants like feet on ice, and
the one time everything stops moving — the bridge — is the coldest
moment of the track. Movement as survival; arrival (the full circle,
home to Fm) as the payoff.

- Tempo/key: **138 BPM, F minor**. Yes, F minor again — per review:
  a scale is not an identity, melodies are. What must NOT repeat is
  the groove, and it doesn't (see the freshness contract). One
  borrowed color: the **E♮ of the V chord** (C major) at the far side
  of the circle — this track's single non-diatonic note, the pull
  that swings the loop home (nachtkind's F♯ move, different function).
- Harmony — **one progression family: the diatonic circle of fifths**,
  walked at two depths:
  - **half circle** (verses): `Fm – B♭m – E♭ – A♭` and jump home. The
    near side. A perfectly normal 4-chord minor trance loop.
  - **full circle** (choruses): `Fm – B♭m – E♭ – A♭ – D♭ – Gø – C – (Fm)`.
    The far side (D♭–Gø–C) exists ONLY in choruses: completing the
    journey IS the chorus.
  - One chord per **2 bars** (one hammer bar + one oscillation bar
    each), so half circle = 8-bar loop, full circle = 16-bar cycle.
- Seed: `np.random.default_rng(1725)  # Op. 8 published`.
- Length ~5:20–5:50. Output `/workspace/music/eisgang.wav` (+ mp3).

## The freshness contract (why this can't sound like the last three)

The review's concern: beats and basslines have converged. Explicitly:

| | previous tracks | eisgang |
|---|---|---|
| bass pattern | rolling 16ths, continuous, root+octave on a pedal | **run-and-plant**: 2 beats octave-bounce → quarter-note LANDING on the *next* root → **rest** (a real hole; kick shows through) |
| bass root | static pedal per section | **walks every 2 bars** (the circle) |
| bass sound | the warmed saw mono-synth family | **percussive thud-bass**: sine body + soft knock attack, short — a foot, not an engine (see recipes) |
| kick | four-on-floor throughout | four-on-floor base + **the stamp**: a kick double on beat 4& closing every 2-bar cell (and doubled harder into choruses) |
| hats/perc | continuous 16th closed-hat machine grid | **no 16th hat carpet.** Offbeat open hat only, plus the **tick pair**: percussion that performs the cell — hammer bars tick ONE rim center, oscillation bars alternate TWO rims L/R |
| groove DNA | one-bar loops, additive layers | **two-bar breathing**: everything (bass, kick, ticks, stabs) phrases in hammer/oscillation pairs |

Verification makes the bass claim falsifiable: the script prints **bass
duty cycle** (fraction of 16th slots sounding). The old rolling bass
measures ≈1.0; eisgang must print **≤ 0.6** or the design has failed.

## The refrain: the skyline

W3's mechanism (not its pitches): during grooves, a cold stab **hammers
ONE pitch per chord** (the hammer bars). Across a cycle those pitches
spell a line — the refrain, present from bar 1 but in augmentation, one
stone per 2 bars. The chorus reveals it: the lead sings the same
pitches as a connected legato glide line over the full circle.

Proposed skyline (one pitch per chord, ours not Vivaldi's):

```
half circle:   C   D♭   B♭   C      (over Fm  B♭m  E♭  A♭)
far side:      A♭  B♭   G           (over D♭  Gø   C)
```

A sighing zigzag — step up, third down — that lands hanging on **G over
the V chord**, resolved only by the cycle restarting on C-over-Fm. So
the refrain's own last interval is the seam across every chorus
boundary (doctrine rule 3 satisfied by construction). The verses only
ever know the first four notes; **the verses ask a half-question for
minutes before the chorus finishes the sentence.** Q/A, refrain
identity, and the thesis-early rule all kept — but the thesis hides in
plain sight as augmentation instead of a solo statement. Oscillation
bars answer each hammer bar by rocking hammer-pitch ↔ chord root below
(the interval changes as the harmony walks — variety for free).

## Rule breaks, declared (per review: allowed, 90s style intact)

1. **The static pedal is gone.** Every blueprint so far praised
   "static, hypnotic, drone-oriented" harmony; this track's identity is
   the opposite — harmony that *walks* — while remaining one family and
   fully loopable. Still era-true: functional circle sequences are all
   over 90s Eurodance/trance B-sides; nobody built the whole track on
   one. Now we do.
2. **The rolling mono bass is banned from this script.** (Duty-cycle
   check above.)
3. **The hat carpet is banned from this script.** The tick pair + open
   hat carry the top end.
4. **A functional dominant (V major, E♮)** enters a trance/ track for
   the first time — once per full circle, chorus-only.

Not broken: 4/4 909 base (this is still a stomper, not breakbeat), the
warmth recipe (cold ≠ harsh — all voices through the standard knobs),
no supersaws / no sidechain pump / no acid, seams at every boundary,
RMS discipline, everything synthesized, seeded, standalone script.

## New instruments (the recipes this track adds)

1. **Thud-bass (the feet)** — percussive, warm, short: sine fundamental
   + one octave partial, a soft 150–800 Hz "knock" transient (no saw
   stack at all — this bass is closer to a tom than a synth), fast
   raised-cosine decay ~180 ms on the bounces, ~350 ms on the plants.
   Bounces at root/root−12; the plant lands on the NEXT chord's root —
   the bass arrives before the harmony does (a written pickup, every
   2 bars).
2. **The hammer stab (the cold)** — the W3-behavior voice: a gated
   pluck, hollow pulse-wave core (new timbre family for trance/ — the
   saw leads belong to the other tracks) + sine body, lowpass ~2 kHz,
   16th retrigger with a per-16th gain cell so it *chatters* rather
   than carpets. Dry-ish (wet ≤ 0.25): the cold thing is close to the
   face; the hall is for the warm thing.
3. **The skyline lead (the warm)** — chorus-only: warm hollow-pulse
   legato with portamento glide between skyline notes, octave double in
   the final chorus, long dark hall (the Eye Q dry/wet contrast:
   drums+stab dry, lead+pad wet).
4. **Tick pair** — two short rim/woodblock clicks (bandpassed noise +
   tiny pitch thump, ~2.5 kHz and ~1.8 kHz), hard-panned L/R. Hammer
   bar: one tick, center-ish, steady 8ths. Oscillation bar: the two
   trade 8ths L/R. The groove's DNA audible in the percussion alone.
5. **The stamp** — beat-4& kick double: same 909 kick sample, second
   hit −2 dB and slightly shortened, closing every 2-bar cell. In
   choruses the stamp gains a low tom layered under it (the boot).

Reused: 909 kick/clap/open-hat/crash family, dark breakdown pad, tom
fills as seam devices (three max, per ungeschrieben's discipline).

## Structure (~168 bars @ 138 BPM, bar ≈ 1.74 s, ~4:53 + tail)

| bar | t | section | what happens |
|-----|------|---------|--------------|
| 0 | 0:00 | intro (8) | The naked cell: thud-bass run-and-plant on Fm + kick + stamp, tick pair enters bar 5. Skyline note 1 (C) hammered from bar 1 — the thesis, in augmentation, no announcement. |
| 8 | 0:14 | verse 1 (16) | Half circle ×2. Stab chatters the half-skyline (C D♭ B♭ C); oscillation bars answer. +open hat at 8, +claps at 2&4 on the second lap. |
| 24 | 0:42 | crossing 1 (8) | First attempt at the far side: the harmony walks past A♭ into D♭ and **Gø — and breaks off** (bar 31: everything but kick and one tick drops for 2 beats, tom fill) → |
| 32 | 0:56 | **CHORUS 1** (16) | Full circle ×1: the lead sings the whole skyline for the first time, bass runs all 8 stations, stamps doubled, E♮ appears at bar 44 and pulls the loop home. Last lead note (G) hangs across the barline → |
| 48 | 1:23 | verse 2 (16) | Resolution lands on verse 1's C-over-Fm. Back to the near side; tick pair now answers the stab's tail (composed echo, not delay). |
| 64 | 1:51 | crossing 2 (8) | Second crossing, further: reaches C but refuses to resolve — hangs on the V (first time the E♮ is *held*), crash → |
| 72 | 2:05 | **CHORUS 2** (16) | Full circle, lead + octave shimmer, the boot-tom under the stamps. |
| 88 | 2:33 | the freeze (16) | THE STOP — the track's coldest idea: harmony halts **on Gø** (the chord the verses never reach), all motion stops: no kick, no bass, no ticks. Only the pad (Gø voicing) and the stab hammering the half-skyline *pianissimo*, half-time. Movement was survival; this is what stopping sounds like. One heartbeat-slow thud-bass plant every 4 bars keeps the pulse barely alive. |
| 104 | 3:01 | the thaw (8) | Bass resumes bouncing (still on G), ticks wake L then R, kick returns bar 108, the harmony finally moves Gø→C with a long tom fill riser → |
| 112 | 3:15 | **FINAL CHORUS** (32) | Full circle ×2, the fusion: lead in octaves AND the stab hammering under it (the augmented and real refrain sounding together — first and only time), all stamps, loudest section. Second lap adds a high tick descant answering the lead. |
| 144 | 4:11 | ride-out (16) | Peel in reverse: lead → stab returns to solo hammering, claps out, open hat out, half circle only. |
| 160 | 4:39 | outro (8) | The intro's naked cell again, Fm only; ticks stop; the last event is one full run-and-plant landing on a low F **with the final stamp under it** — one boot, then nothing. Ends cold. |

## Verification (per ../VERIFY.md — the circle variant)

- Section map, seam checklist (every boundary crossed by: hanging G,
  pickup plant, tom fill, crash, or the held V).
- **The harmonic odometer**: circle position printed at every section
  boundary; checks — verses never exceed station 4 (A♭), Gø occurs
  ONLY in crossings/choruses/freeze, every chorus completes exactly
  8 stations returning to Fm, the freeze sits on station 6.
- **Skyline count**: full 7-note statements — chorus 1: 1, chorus 2: 1,
  final: 2+2 (lead + stab fusion), total ≥ 4 sung + continuous
  augmented presence in every groove bar (printed as hammer-bar
  coverage %).
- **Bass duty cycle ≤ 0.6** (the anti-rolling-bass check) + bass rest
  count per bar ≥ 1 in every groove bar.
- **Cell integrity**: printed map proving hammer/oscillation
  alternation holds in every groove section (and is suspended in the
  freeze).
- Per-section RMS: intro < verse 1 < chorus 1; freeze is the global
  trough; final chorus loudest; outro lands ≈ intro.
- Banned-list audit: no 16th hat carpet, no continuous bass (by the
  duty check), no supersaw, no sidechain, no acid Q.

## What we take from Winter — and what stays in the drawer

Taken: **W3's behaviors only** (hammer/oscillation cell, run-and-plant
octave bass, circle-of-fifths travel). Not taken: the shiver stack, the
Largo theme and rain texture, the cascades, the storm, all of it — and
none of Vivaldi's actual pitches; the skyline is ours. If the final
chorus bass ever needs one more gear, W2's zigzag contour
(root–oct–oct–5th) is pre-approved as the only permitted extra borrow —
one line in the drawer, nothing else.

## Open questions for review

1. **Title**: *Eisgang* (German — the breakup and run of river ice;
   fits the story, the era scene, and the nachtkind/ungeschrieben
   naming line; my recommendation), vs *Stampfwerk* ("stamping works",
   more machine), vs English *Icerun*. Filename follows the answer.
   Answer: Eisgang is fine.

2. **The V-major question**: the far side's `Gø – C(E♮) – Fm` is a
   functional dominant cadence — the "coming home" pull is the whole
   chorus payoff (my recommendation). Alternative: stay strictly
   Aeolian with Cm (v), which is more era-orthodox but makes arrival
   flat — the circle would loop rather than *resolve*. Confirm the E♮.
   Answer: Let's try "the far side" (we can afford to break with the era style)

3. **Skyline pitches**: confirm the proposed line
   (C D♭ B♭ C | A♭ B♭ G→) or push it darker (start on A♭, dip below the
   root somewhere)? Register: stab hammers around C5–C6, lead sings an
   octave below the stab or unison? (I'd put the lead at the stab's
   octave-below for warmth, octave-up double only in the final chorus.)
   Answer: Yes, let's keep it warm and lighter (so the proposed line)

4. **How hard do the drums break from the house style?** As specced:
   no 16th hat carpet + tick pair + beat-4& stamp (my recommendation —
   clearly different, still a 4/4 stomper). Bolder option: in
   oscillation bars the kick also drops beat 3 (a limp — every second
   bar stumbles). Riskier for dance flow; tech_noir already owns
   "limp" as identity. Say yes only if the stamp alone proves too tame.
   Answer: Yes, let's do 4/4. We still want it dancable.

5. **The freeze on Gø** (bridge): 16 bars of near-silence on the
   coldest chord, pulse reduced to one plant per 4 bars — confirm this
   is the trough we want, or should the freeze sit on the held V (C,
   E♮ exposed) instead, making the thaw a pure dominant resolution?
   Gø is colder (my rec); C is more functional.
   Answer: Ok, let's try C -  more functional.

6. **Retrograde walk** (optional development, cheap to add): in the
   ride-out, the bass walks the circle BACKWARDS one lap (fourths —
   walking home the way you came). Cute mirror of the story, or too
   clever? I lean *skip* — the ride-out peeling is enough.
   Answer: Interesting. I think it could be worth the experiment. And if it's only one the ride-out, we can afford to experiment more.

7. **Tempo**: 138 (my rec — a stomper should push harder than
   ungeschrieben's 130; nachtkind holds 139 but shares nothing else)
   vs 132–134 (roomier for the tick pair)?
   Answer: Yes, 138 bpm sounds good. A hard techno trance track.
