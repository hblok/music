# Morgenland — design notes (2026-07-09)

**The 303 goes east.** Working title *Morgenland* (the old German word
for the Orient — the naming line of nachtkind / ungeschrieben /
eisgang / maschinenherz continues). Seed **1001** (the Nights).

The concept, third station of the machine-voice arc: maschinenherz was
a machine heart LEARNING to sing; silver_wire was the machine singing
SOLO, its own acid grammar; **morgenland is the machine singing an OLD
song** — the wire channels a folk melody centuries older than any
circuit, in a mode no 303 was ever meant to speak.

This is the user's parked project made concrete: the silver_wire Q4
answer named a 303 tune "inspired by Eastern folk music and song"
(Beta Frequency's *East Europe*, WAV to be dug up later) as the
direction worth importing. We don't wait for the WAV — the genre
grammar route worked for silver_wire v2 — but the door stays open
(Q7).

## Declared borrows (all four, on the table from bar one)

1. **The acid melody grammar** (silver_wire_v2, CONFIRMED GREAT):
   cell-built winding runs, near-continuous 16ths, every-3rd-16th
   accent rolls phase-locked per half, mid-run slide chains, the
   anti-arc CUT_PROFILE contract, register-jump low answers. FROZEN
   as recipe; the notes and the mode are new.
2. **The psy engine** (maschinenherz): trance kick, K-b-b-b bass
   contract (duty-checked), offbeat hats, psy clap, zaps, kit split
   if drops go straighter. The 303 voice recipe (Q 6 / fb 1.3 /
   tanh 1.5, silver_wire's notch).
3. **The big-room master** (validated 2026-07-09, now directory
   default): pump / sub-boom / shelves / tanh limiter, per the
   CLAUDE.md doctrine section — with its calibration guardrails.
4. **The Persian trance analysis**
   (`../../inspiration/Persian_Trance_LdGhQaBCbcE_inspector/`): the
   modal blueprint. Maqam Hijaz / Dastgah Homayoun ≈ **C Phrygian
   dominant: C–D♭–E–F–G–A♭–B♭**; C pedal ~95 % of runtime with
   excursions to ♭2 and G; bass-heavy (44 % < 250 Hz), dark centroid,
   little air — a spectral profile our big-room master already lands.

## Declared sanction — the mode

`idea.md` bans **D Phrygian dominant** as Dune palette. Morgenland
runs **C** Phrygian dominant, arrives at it via the Persian analysis
(not via Dune), and touches NONE of the Dune instruments — the ban
list stays fully in force: no duduk, no ney, no darbuka, no chant,
no wind beds. The Eastern color enters through the MELODY AND MODE
ONLY. (The analysis heard darbuka and synth-ney in the source; we
take neither — the kit stays psy, the singer stays the wire.)

## The mechanisms

- **The color interval**: the augmented second D♭–E is the mode's
  signature. The refrain must CROSS it — the "hijaz crossing" is a
  counted, checked metric (like silver_wire's slide chains). Accents
  snap to C-hijaz scale tones; free chromatics stay on weak 16ths.
- **The landmark lineage**: the question hangs on **D♭** (the ♭2 —
  maximum lean against the C pedal; nachtkind hung on F#,
  maschinenherz on D#, silver_wire on E). The answer resolves
  **D♭→C across the barline** — which is the Phrygian cadence,
  ♭II→i: the house seam mechanism turns out to be the oldest cadence
  in the book. The close: a long held D♭→C slide (the G#→A close
  transposed into the mode).
- **Ornament vocabulary — the NEW melody-rule ingredient** (this is
  what "folk song" adds beyond silver_wire): Eastern melisma spoken
  in 303 dialect. Three ornaments, each mapped to a machine gesture:
  *grace flick* (32nd lower-neighbor double-hit before a landing),
  *mordent turn* (note–upper–note as three 32nds at phrase heads),
  *melisma chain* (slide chains bending through 3+ pitches — the
  portamento the mode sings with). Ornaments are counted and
  checked per statement.
- **Harmony**: verses and drops sit on the C pedal (authentic to the
  source AND to psy). Choruses make the mode's only walk — the lap
  drawn from the source's own excursions: **C–D♭–G–C** (home, the
  lean, the fifth, home; the D♭ bar is the question bar). Pads voice
  OPEN FIFTHS + color tones, not full triads — maqam music doesn't
  think in triads, and the open fifth lets the melody's E♮/A♭ paint
  the color (Q3).
- **The second voice** (Q2): a **santur/qanun-flavored pluck** —
  hammered-string character: detuned string pair, fast double-strike
  attack (the hammer bounce), bright but round, tremolo rolls on
  held tones. NOT on the Dune ban list, and the concept wants it:
  the machine sings the old song, the old instrument answers. It
  takes the low-answer slots (the silver_wire Q/A device) and the
  break; it NEVER carries the refrain alone.
- **Shape**: song form, the proven two-drop arc (thesis → engine →
  verse → build → DROP 1 → chorus → break/trough → build → DROP 2 →
  chorus → outro → bookend). Drops 48+ bars, EVOLVING with mini-dips
  (the long-drop lesson). Thesis: the wire alone states the first
  hijaz phrase over a bare C drone; bookend answers it, the final
  D♭→C stated by wire and santur in octaves — the fusion's last word.

## Verify paragraph (implement exactly)

All silver_wire_v2 blocks (section map, refrain statement count ≥ 6,
identical-map complexity metrics: onset density ≥ 0.70, longest run
≥ 32, accent 3-cycle streak ≥ 4, slide chains ≥ 4, tied/slid ≥ 0.25)
PLUS the mode blocks: (a) mode compliance — 100 % of accented onsets
in C hijaz (printed count); (b) hijaz crossings — the refrain crosses
D♭↔E ≥ 4 times per 16 bars (printed); (c) ornament census — ≥ 6
grace flicks, ≥ 4 mordents, ≥ 4 melisma chains per full statement
(printed per type); (d) landmark checks — the D♭ hang (bar 8) and
the held D♭→C close (bar 16) present; (e) K-b-b-b duty check; (f)
big-room metrics with pinned floors (sub share, hf share, pump
stats) per the master doctrine. Seam checklist at every boundary;
per-section RMS with the staircase/trough/summit orderings.

## Open questions for review

1. **Tempo.** 142 BPM (the wire's continuity — morgenland as the
   next station of the same machine) vs ~100 BPM (the source set's
   true tempo — a slower, heavier groove, halftime feel, would be
   this directory's first non-fast track). Recommended: **142** —
   the concept is the WIRE going east, not us making a Persian set;
   the source lends its mode, not its clock.
   Answer:

2. **The santur answer voice.** Build it (the machine + the old
   instrument, Q/A trades, never the refrain) vs solo wire again
   (silver_wire purity, the mode is the only news). Recommended:
   **build it** — the ornament grammar will read twice as clearly
   answered by a hammered string, and the track needs its own
   identity beside silver_wire.
   Answer:

3. **Pad harmony.** Open fifths + color tones (maqam-authentic,
   melody paints the mode) vs full triads (C major tonic per hijaz —
   warmer but more Western). Recommended: **open fifths**; the E♮
   belongs to the melody, not the bed.
   Answer:

4. **The doum/tak gesture.** The source's darbuka doum/tak split
   could be SUGGESTED inside the psy kit as a kick/rim-tick ghost
   pattern (declared as gesture, no darbuka samples, no swing) — or
   skipped entirely (kit stays pure psy). Recommended: **skip** for
   v1; the mode carries the east, the kit carries the machine. Keep
   as a v2 knob if the groove reads too western.
   Answer:

5. **Drop harmony discipline.** Both drops full-pedal (authentic,
   maximum machine) vs drop 2 walking the C–D♭–G–C lap under the
   fusion (the maschinenherz move: the summit drop earns the walk).
   Recommended: **drop 2 walks** — the D♭ bars under the held D♭
   landmarks give the fusion its lean.
   Answer:

6. **Name + seed.** *Morgenland*, seed 1001. Alternatives:
   *Ostwind*, *Karawane*, *Seidenstrasse*. 
   Answer:

7. **The East Europe WAV.** Proceed now on genre grammar + the
   Persian modal blueprint (recommended — silver_wire v2 proved the
   constructed route); when you dig up the WAV, it gets the
   inspector `--separate` treatment and its contours feed a future
   revision or a sibling track.
   Answer:
