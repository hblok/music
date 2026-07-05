# Silver Wire v2 — design notes (the melody goes acid)

Amendment to `silver_wire_notes.md` for `silver_wire_v2.py`
(→ **`silver_wire_v2.wav`** — v1's WAV stays untouched, per
convention). Scope: **the 303 melody only.** Everything the listen
test validated is frozen.

## The v1 verdict (2026-07-05)

"Super fun, this works" — the 303 question / low-register answer
device, the bassline, the volume balance, the whole structure are
KEEPERS. The fail: the melody is fun and catchy but **too simple**,
and simplicity has a genre: it reads as funky jazz / pop & rock
(the comparison: "Rocksteady", The Bloody Beetroots) instead of
acid & psy. The hallmark of acid was always the opposite — **long,
complex 303 attacks, extended winding lines** (the reference:
"East Europe" by Beta Frequency; too obscure to find online, so its
qualities are imported from the genre grammar — and see Q4).

## The diagnosis — why v1 reads pop

Look at v1's own printed refrain map: `O=.oo/o=..o/o===` — onset,
breath, pickup, cadence, HOLD. That is *vocal phrasing*: one gesture
per bar, an arch contour, a rest where a singer breathes, a held
note where a line ends, a funk octave-drop lick in bar 7. Onset
density was 47 notes over 128 steps (0.37); the longest unbroken run
of 16ths was 3. A melody built like a chorus vocal will read as pop
no matter how correct the psy floor under it is — the floor was
never the problem.

## The acid grammar — what the new melody is made of

Acid lines are not sung, they RUN. The v2 refrain is rebuilt from
these rules (each one checkable, see Verify):

1. **Near-continuous 16ths.** Rests are punctuation, not breaths:
   rest budget ≤ 12 of 128 steps (v1: 25). Onset density ≥ 0.70
   (v1: 0.37). At least one full 2-bar unbroken run (≥ 32 onsets);
   longest v1 run was 3.
2. **Cell sequencing, not phrase arches.** The line is built from
   3–4-note winding cells (circle the center, chromatic lower
   neighbor, re-attack) SEQUENCED up and down the scale — state,
   restate a step higher, restate again, displace an octave. The
   complexity is structured, not random: the ear tracks the cell,
   not a tune-you-can-hum-first-listen.
3. **Cross-rhythm accents.** The accent map cycles in THREES against
   the 4/4 grid (accent every 3rd 16th) for multi-bar stretches,
   re-phasing at bar 8 boundaries — the acid roll that makes a
   static bar feel like it turns. Accents stay pitch-anchored to
   chord/scale tones.
4. **Slides mid-run.** Slide chains inside the runs (2–3 slid notes
   in a row bending through a turn), not only at phrase ends — the
   303 tie as motion-blur, the within-run legato that keeps a
   percussive stream singing (the eisgang sustain lesson, acid
   dialect).
5. **Chromatic winding, budgeted.** Chromatic lower neighbors are
   free on unaccented 16ths (the acid snake); accented notes and
   run-endpoints stay on A-minor scale/chord tones so the key never
   dissolves (Q2).
6. **Cadences avoided — except the two landmarks.** The line never
   closes bar-by-bar. It winds until the two moments v1 got right,
   which are KEPT verbatim: **the screaming hang on the dominant E**
   (mid-refrain) and **the long held G#→A slide close** (refrain
   end, landing across the barline). Everything between them turns
   from song into wire.

## The size question — 8 bars → 16

"Long complex tunes" is also literal length. The v2 refrain doubles
to **16 bars**: Q = 8 bars winding UP to the E hang (bars 7–8 of Q),
A = 8 bars winding DOWN home to the G#→A close (bars 7–8 of A). Each
half is one continuous attack; the whole statement is one long
breath of machine. Consequences (Q1):

- Statement slots re-map (structure bars UNCHANGED): verse = 1 full
  statement (16 bars, octave down, dark), drop 1 = 2 full + a
  declared Q-half at bars 80–87, chorus 1 = 1, drop 2 = 2 (the
  a-cappella dip plays the first 4 Q bars naked), chorus 2 = 1.
  **Full-statement count target drops 8 → 6** (7 placed); the halves
  and dip fragments stay declared and uncounted.
- The thesis states the first 4 bars of Q (the hook is now a cell +
  its first sequence steps, stated in ten seconds as before); the
  bookend states the last 4 bars of A (ending on the stated A) at
  the thesis filter position. Both halves of the bookend contract
  survive.

## What is FROZEN (the listen test paid for it)

Structure and section bars, the kit and its psy/straight split, the
K-b-b-b bass in both modes, the walking Am–F–G–E laps, the pads, the
low-register answer cells and turnaround loops (upgraded only per
Q3), volumes and commit weights, the anti-arc rule and CUT_PROFILE
mechanics (the per-phrase profile now spans 16 bars — same contract,
same checks), the 303 voice itself (Q 6 / fb 1.3 / tanh 1.5 — the
sound was never the complaint), BPM 142, A minor, seed 303.

## Verify (v2 additions to the v1 block)

All v1 checks stay (RMS ordering, anti-arc spread/slope, K-b-b-b,
statement count at the new ≥ 6 target). The sings-not-plinks check
is joined by the **complexity block**, printed from THEME itself:

- onset density ≥ 0.70 (onsets / 128×2 steps);
- rest budget ≤ 24 of 256 steps;
- longest unbroken 16th run ≥ 32;
- accent cross-rhythm: ≥ 4 consecutive bars where accents fall on a
  3-step cycle;
- slide chains: ≥ 4 places with 2+ consecutive slid notes mid-run;
- tied/slid fraction ≥ 0.25 still (slides carry it now; the two
  landmark holds remain the only long notes);
- landmarks intact: the E hang and the G#→A close present at their
  bars (printed).

## Open questions for review

1. **16-bar refrain** as argued above (with count target 8 → 6), or
   keep 8 bars and put ALL the complexity inside (count target
   stays 8)? Recommended: 16 — "long" was half the feedback, and the
   halves give the thesis/bookend clean quarters to state.
   Answer:

2. **Chromatic budget.** Free chromatic lower neighbors on weak
   16ths, scale tones on accents (recommended — the snake without
   losing A minor)? Or stricter (diatonic runs, chromatics only at
   the two landmark approaches, i.e. barely more than v1)?
   Answer:

3. **The low answers.** Keep the v1 cells exactly (they passed the
   listen test), or let the low register speak the new grammar too —
   its answer cells become 1-bar mini-runs (still never the
   refrain)? Recommended: upgrade — a running lead over v1's sparse
   funk-ish low cells would reopen the genre gap from below.
   Answer:

4. **East Europe.** Not findable online — if there is one specific
   quality of that track you want imported as *technique* (e.g. the
   relentlessness of the runs, a particular winding-down-then-jump
   contour, triplet-feel accent rolls, the way it never breaks for a
   chorus), name it and it gets written into the melody rules.
   Answer:
