# Penumbra — design notes (the single-wave form)

Composition document for review before writing `penumbra.py`
(→ `penumbra.wav`; filename follows the title — see question 1).

Inspiration: **Brainchild — Symmetry (C-Mix, 1994)**, per
`../../inspiration/Symmetry_Brainchild.md` — mid-90s Belgian progressive
trance, Bonzai/R&S lineage. As with ungeschrieben, this is a NEW track,
not a cover: we take the *form* (the patient single wave — groove →
creeping tension → weightless breakdown → full-bloom peak → mirrored
dissolve), the *palette era* (909, rolling 16th bass, dark analog
string-pads, chorus/detune/delay width, no supersaws, no sidechain),
and the blueprint's two non-negotiables:

1. **The 16th-note gated lead** — sustained melodic notes chopped into
   a 16th stutter; melody and rhythm in one voice. THE defining element.
2. **Static modal harmony** — i ↔ ♭VII ↔ ♭VI oscillation, drone-oriented,
   implied by the pads; no functional progressions, no chord stabs.

**The story**: penumbra — the half-shadow at the edge of a light. The
gate *is* the concept: the melody flickers light/dark sixteen times a
bar, never fully lit, never fully dark. The filter is how far the
shutter stands open — the whole track is one slow opening. The
breakdown is the one moment the shutter swings wide and the melody
sings *ungated*, free; the peak is full light with the gate now dancing
rather than hiding; then the arc closes symmetrically back into
shadow. The emotional payoff, per the blueprint, "comes not from a
sudden drop but from the *unfiltering* of a melody you've been hearing
in shadow for minutes." Dark-euphoric, nocturnal, melancholic but
propulsive.

- Tempo/key: **140 BPM, C natural minor** (see question 2 — the
  blueprint's literal F minor collides with ungeschrieben's identity).
  Harmony: **Cm ↔ B♭ ↔ A♭** (i–♭VII–♭VI), the blueprint's modal
  oscillation transposed. Bass sits on the C pedal nearly throughout;
  *the pads carry the oscillation* — harmony as light, not as motion.
- Seed: `np.random.default_rng(140)  # the BPM, per lost's precedent`
  (1994 is taken by unsung).
- Length ~6:00–6:15 (~210 bars, bar = 1.714 s) — farlight's lesson:
  the back half earns its minutes.
- Output: `/workspace/music/penumbra.wav` (+ mp3).

## Identity separation (three tracks share this corner of the era)

- **vs ungeschrieben** (F minor, Fm–D♭–E♭, 130, Frankfurt): new key
  (question 2), 140 BPM, and the development engine moves from a
  *sequence* under string reveals to the *gated lead itself* — there is
  no rompler-string reveal here, no spoken word, no toms.
- **vs farlight** (E minor, Em–D–C–D shuttle, 136, bright/happy): same
  scale-degree family (the era's lingua franca) but opposite treatment —
  farlight bounces the shuttle brightly with a major re-light payoff;
  penumbra drones it darkly on a pedal with no re-light, no G-major
  moment. The farlight bell appears here as a *guest counter-voice*
  (question 4), not the centerpiece.
- **vs nachtkind** (reverse cymbals are its seam signature): banned
  here. Seams use snare rolls + reverb swells + crashes + ringing pads.

## How the song doctrine maps onto the single-wave form

1. **The refrain is the gated motif** — 8 bars: a circling 2-bar cell
   ×4, built on the blueprint's hypnotic-modal degrees (1, ♭3, 4, 5,
   ♭7 — in C: C, E♭, F, G, B♭). Cells 1–2 identical (the circling),
   cell 3 lifts and hangs on the ♭7 (the question — no leading tone in
   Aeolian, it hangs rather than leads), cell 4 falls home to C (the
   answer). Identical melody at every statement; the *filter position*
   is the only thing that develops. Fragments in the intro/outro count
   as statements only if all 8 bars play.
2. **Thesis in the first ten seconds — compatible, not deviated.** The
   doctrine asks for the hook "quiet, solo, half-voice" early; the
   blueprint teases the motif filtered/subdued. Same thing: the gated
   motif plays from bar 0 through a nearly-closed filter over the dry
   kick+bass. No withheld-thesis deviation this time — the melody is
   *present in shadow* from the first bar; the reveal is the opening,
   not the arrival.
3. **The development engine is the filter arc** — ungeschrieben's
   printable/checkable mechanism (`CUT_BARS`/`CUT_HZ`, per-onset cutoff,
   cached in buckets), applied to the LEAD: rises monotonically across
   the development sections, freezes through the breakdown, reaches its
   global maximum inside the peak, and descends symmetrically to the
   intro value at the bookend. Printed at every boundary and checked.
4. **Q/A between instruments**: the farlight tubular bell is the
   thinner, brighter answering voice (blueprint §7's counter-lead).
   It answers the refrain's ♭7 hangs — teased once in the development
   (question 4), in full call-and-response at the peak only.
5. **The fusion payoff, mapped**: at the peak — and only there — three
   things co-occur: the filter fully open, the gate dancing at full
   brightness, and the bell answering every hang. Before the peak the
   bell and the open filter never meet.
6. **The one ungated statement** (question 3): in the breakdown the
   kick and bass fall away and the lead sings the refrain ONCE with the
   gate lifted — sustained, reverb-drowned, weightless (blueprint §3:
   "pads and the lead sustain in reverb-heavy space"). The gate snaps
   back with the kick at the peak. One ungated statement in the whole
   track, checked.
7. **The symmetry** (the source's own title, kept as form): layers
   strip in the outro in exact reverse order of their entry, and the
   filter lands where it started. The script records add-order and
   strip-order and checks one is the reverse of the other.
8. **Seams**: snare rolls (doubling 16th→32nd), reverb swells, crashes,
   ringing pad chords, and the composed drop-beat silence before the
   peak. No white-noise risers, no reverse cymbals, no toms.

## New instruments (the recipes this track adds)

1. **The trance gate** — per-16th volume gate baked into the note
   render (tech_noir's baked-gate lesson): step = 107 ms at 140 BPM,
   ~55–60 % duty, raised-cosine ~4 ms edges (no clicks). Straight
   16ths (question 5). Applied to the lead only.
2. **The gated lead voice** — bright, hollow analog/digital hybrid
   (blueprint: square-saw blend, Roland JP/Korg character): square +
   saw mix with warmth-recipe guardrails (`1/k**1.3` roll-off, sine
   body ~0.3, `tanh(0.9)`), width from ±0.3 % detuned copies + the
   nachtkind dotted-8th ping-pong delay — never unison stacks. The
   swept lowpass IS the development (see the arc); it must still read
   bright when open, so the arc tops out ~3.6 kHz rather than the
   usual 2.6 k ceiling — the gate and the roll-off keep it from
   reading harsh.
3. **Juno/JX dark string-pad** — wide, dark, slow ~0.8 s attack;
   the rompler-strings recipe darkened (lower LP, no bow-noise layer,
   slower attack) rather than a new voice from scratch. Long hall,
   wet ≥ 0.5. Carries the i↔♭VII↔♭VI oscillation, 2 bars per chord.

Reused as-is: **the farlight tubular bell** (partials 1/2.0/2.76/5.40,
gains 1.0/0.42/0.26/0.10, rising decays, ±0.0006 detune pairs, mallet
thunk, pitch-scaled ring) as the counter-voice; 909 kick/hats/claps
(lost_v6 kit, dry and mechanical — blueprint wants punchy, slightly
boomy, prominent); rolling 16th mono bass on the C pedal with octave
jumps and passing B♭/A♭ approaches (the warmed lost_v4 recipe); snare
roll (farlight's era marker); crash; big hall on pads/lead/bell, kick
and bass bone dry (the dry-wet contrast rule).

## Structure (~210 bars + tail, bar = 1.714 s)

| bar | t | section | what happens |
|-----|------|---------|--------------|
| 0 | 0:00 | thesis/intro (8) | Dry kick + rolling bass from bar 0 (the engine, per blueprint). THE MOTIF from bar 0, gate on, filter nearly closed — a dark throb with a tune inside it. |
| 8 | 0:14 | groove I (16) | +16th closed hats, +offbeat open hat. Filter stage 1. |
| 24 | 0:41 | groove II (16) | +claps on 2&4, +sparse stab accents. Filter stage 2. |
| 40 | 1:09 | theme (16) | The refrain reads as a *melody* for the first time (filter mid). Statements counted from here. |
| 56 | 1:36 | pads (16) | +the dark pad oscillation (Cm↔B♭↔A♭) — harmony arrives. Filter stage 3. |
| 72 | 2:03 | answer (16) | The bell TEASE: one answered hang per 8 bars (question 4). Filter stage 4. |
| 88 | 2:31 | lift (8) | Ride in, hats double, snare roll, crest, crash → |
| 96 | 2:45 | breakdown (20) | Kick+bass out. Pads swell; the lead sings the refrain ONCE UNGATED, drowned in the hall. Last 4 bars: snare roll + reverb swell; final beat silent. |
| 116 | 3:19 | PEAK I (16) | Full arrangement, gate back, filter FULLY OPEN (global max), bell answers every hang — the fusion. |
| 132 | 3:47 | dip (4) | Mid-drop dip (dune long-drop lesson): claps/ride out, filter eases a stage. |
| 136 | 3:53 | PEAK II (20) | The fullest wave: everything returns + densest bell/lead trades. Loudest section. |
| 156 | 4:27 | ride-out I (16) | Mirror strip begins: bell out, pads recede — filter starts its long descent. |
| 172 | 4:55 | ride-out II (16) | Stabs out, claps out, ride out — reverse of the build order. |
| 188 | 5:22 | outro/bookend (16) | Kick/bass/hats + the motif back at the intro's near-closed filter — the bookend is the filter position AND the tune. Kick stops ~bar 200. |
| 204 | 5:50 | tail (6) | The last gated throb + one pad chord and a single bell note ring out. ~6:00. |

## Verification (per ../VERIFY.md — single-wave variant)

- Section map; seam checklist at every boundary (roll / swell / crash /
  ringing chord / the one composed silence).
- **Refrain statements**: identical-melody 8-bar statements counted
  (theme 2, pads 2, answer 2, breakdown 1 *ungated*, peak I 2, peak II
  2, outro 1 ≈ target ≥ 10). **Exactly one ungated statement**, and it
  is inside the breakdown.
- **The filter arc, printed and checked**: cutoff at each boundary
  (from the automation, not audio): monotone rise intro → lift, frozen
  through the breakdown, global max inside the peaks, monotone descent
  after, |outro − intro| small (the symmetric bookend).
- **The symmetry check**: strip-order == reverse(add-order), printed
  as two lists.
- **Bell discipline**: zero bell before bar 72; ≤ 2 answers in the
  tease; answers every hang in the peaks; bell and fully-open filter
  co-occur only in the peaks (the fusion, presence-checked).
- Per-section RMS: rises through the development stages; breakdown is
  the trough; **PEAK II loudest**; ride-out descends; outro lands near
  intro level. Sub entries bloom, never snap (farlight v2's speaker
  lesson — the peak I entry out of the silent beat gets the eased sub).
- Banned-list audit (by construction, printed): no supersaw, no
  sidechain pump, no white-noise riser, no reverse cymbal, no toms,
  no acid resonance; all pitches diatonic to the chosen natural minor
  (pc-set check).

## Open questions for review

1. **Title**: *Penumbra* (the half-shadow — the gate flickering
   light/dark is the concept made audible; my recommendation), vs
   *Axis* (the mirror line of the symmetric arc — closer to the
   source's own title), vs something else English. Filename follows.
   Answer:

2. **Key**: the blueprint is literally F minor / Fm–E♭–D♭ — which is
   ungeschrieben's exact key and chord set. Options: (a) **C natural
   minor** (Cm–B♭–A♭ — my recommendation: cleanest identity, no
   overlap with any track, dark nocturnal color), (b) F♯ natural minor
   (F♯m–E–D — bass register closest to the blueprint's F1 weight),
   (c) keep literal F minor and accept the collision (era-authentic;
   BPM and instrumentation may separate them enough).
   Answer:

3. **The ungated breakdown statement**: the blueprint hints at it
   ("pads and the lead sustain in reverb-heavy space"); I've promoted
   it to a composed device — the melody heard gated for minutes sings
   free exactly once, then the gate snaps back at the peak. Confirm?
   (It becomes a printed check either way.)
   Answer:

4. **Bell scope**: (a) one tease in the answer section + full
   call-and-response at the peaks (my recommendation — the tease makes
   the peak's duet feel foreshadowed, and gives the outro's single
   ring a referent), vs (b) strictly peak-only, per the blueprint's
   stricter reading (counter-melody enters only at the peak).
   Answer:

5. **Gate pattern**: (a) straight 16ths, ~55–60 % duty (my
   recommendation — the blueprint calls it a 16th stutter, and the
   reviewers' point was that remixes *lost* energy dropping the fast
   gate), vs (b) an accented pattern (e.g. offbeat-weighted duty) for
   more groove at the cost of the relentless flicker.
   Answer:
