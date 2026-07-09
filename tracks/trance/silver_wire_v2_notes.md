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
   Answer: Yes, 16 bars. The point is to extend the tune.

2. **Chromatic budget.** Free chromatic lower neighbors on weak
   16ths, scale tones on accents (recommended — the snake without
   losing A minor)? Or stricter (diatonic runs, chromatics only at
   the two landmark approaches, i.e. barely more than v1)?
   Answer: Free chromatics.

3. **The low answers.** Keep the v1 cells exactly (they passed the
   listen test), or let the low register speak the new grammar too —
   its answer cells become 1-bar mini-runs (still never the
   refrain)? Recommended: upgrade — a running lead over v1's sparse
   funk-ish low cells would reopen the genre gap from below.
   Answer: The low answer should follow the questions, thus, also needs the new grammar. 

4. **East Europe.** Not findable online — if there is one specific
   quality of that track you want imported as *technique* (e.g. the
   relentlessness of the runs, a particular winding-down-then-jump
   contour, triplet-feel accent rolls, the way it never breaks for a
   chorus), name it and it gets written into the melody rules.
   Answer: Right, it has a relentlessness run, and 303 tune used as an instrument, where the tune is inspired by Eastern folk music and song. Now, we don't need to emulate that right now, it was just an example. And, we can dig up the track so we can analyse it later. Although, all I have is a wave file, so that will have to be a project for later.


## v3 amendment (2026-07-09) — the big-room master

Listen feedback on v2: the acid grammar is CONFIRMED GREAT — melody,
composition, instruments all FROZEN. The fail is the sound: flat,
"like an atari recording", against modern big-room weight. v3 is a
MIX-ONLY revision: not one note, bar, pattern or commit-order
changes. The moves are the verified fall_of_arrakeen v2 master chain
(dune/CLAUDE.md), plus one width knob:

1. **Sidechain pump**: precomputed curve, 55 % duck at every
   4-on-the-floor kick, `1 − 0.55·exp(−t/0.10)`, floor 0.30, applied
   as `env=` to bass and pads. Roll bars don't pump. In the drops
   this deepens the K-b-b-b swell (the fall_of_arrakeen-verified
   "deeper, not muddier" effect on the same bass pattern).
2. **Sub-boom layer**: pure sine at the bass root (A1/F1/G1/E1 —
   already the boom register), ON every 4-on-the-floor kick,
   sustaining the beat, hard release in the last 60 ms, its own
   commit weight — MODEST at 0.14 (this bass already carries 55 Hz
   sub duty; the boom only fills the kick 16th). Follows
   `bass_root(b)`; scaled by `kick_gain(b)`. Inside the drops it
   completes the sub: boom on the kick 16th, `sub_note` on the three
   after — a continuous low-register line with the K-b-b-b contract
   intact (the boom is the KICK's low end, not a bass onset).
3. **Master shelves + bus limiter**: high `+0.22·butter(2,3000,hi)`,
   low `+0.34·butter(2,95,lo)`, then
   `tanh(1.35·mix/peak)/tanh(1.35)·0.88`. DECLARED DEVIATION from
   the fall chain: NO deep 55 Hz shelf — this bass lives at
   41–55 Hz; the compound shelf measured a 0.73–0.79 sub-60 share
   of drop RMS (v2 baseline: 0.60–0.62), burying the mids/top.
4. **Pad width**: detune ±0.07 % → ±0.12 %, cross-gain 0.65 → 0.40;
   pad commit 0.13 → 0.16 gives back the pump's average cut (~0.88)
   so the pads still differentiate drop 2 and the choruses (the
   drop2 > drop1 RMS check was marginal by construction in v2:
   0.191 vs 0.190).
5. **FLAC**: the compressed deliverable is lossless flac, not 192k
   mp3 (user request, 2026-07-09; applies to all future scripts).

Declared NON-moves: the 303 is NOT pumped and gets NO delay throw —
the running line's grammar (density 0.90, the slide chains) must not
smear; it stays bone dry and center, the world pumps around it. The
air layer keeps its band.

Verify (v3 additions): print per-section sub-60 Hz and >3.5 kHz RMS
shares and the pump floor/dip count; check both drops carry the sub
(share >= 0.55) and the lit top octave (hf share >= 0.04) —
thresholds pinned just under observed values, regression guards.

DECLARED CHECK CHANGE (the one v2 check that is redefined, not
weakened): "drop 2 > drop 1" is now compared on the >120 Hz band.
The two drops share one identical kick/bass/boom floor by design
(same kit split, same kick gain, same K-b-b-b contract), so total
RMS only ever measured the added voices — and the v3 boom + low
shelf turned total RMS into a sub meter (the sub floor, identical
in both drops, swamps the average; measured: the v2 master orders
the >120 Hz band the same way, 0.121 vs 0.113). Above 120 Hz, where
the pads / octave double / full percussion live, drop 2 out-sings
drop 1 with real margin (0.143 vs 0.131). All other v2 checks
unchanged and must still pass.
