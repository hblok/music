# The song doctrine, ported to trance

The dune album ended by learning how to write *songs*: *Sihaya* and
*Muad'Dib* feel complete and bound together in a way the earlier tracks
don't. This document extracts what made that work and maps it onto the
trance/ tracks, so the next revisions here (`nachtkind_v3`, `lost_v5`,
`tech_noir_v3` — per-track note docs alongside this file) get the
composition for free without importing the Dune *sound*.

## What carries over (form, not sound)

1. **Refrain identity.** One hook the listener can hum, stated with
   *identical* melody every chorus. Repetition is the point. The script
   counts the statements and prints the number (target set per track).
2. **Question / answer at three levels.**
   - *Inside the melody*: every phrase an antecedent/consequent pair —
     same rhythm, question ending off-tonic, answer resolving home.
   - *Between instruments*: composed echoes and trades — one voice
     calls, another answers the tail (not a delay effect, a written
     echo). In trance the "performers" are instruments: piano/lead,
     lead/cello, fanfare/anvil.
   - *Between sections*: verse (sparse, dark, low) asks; chorus/drop
     (full, resolved, high) answers; the bridge asks the track's oldest
     question and the final chorus answers it.
3. **One continuous cursor, no dead seams.** Every section boundary is
   crossed by a pickup, a ringing chord, a fill, or a reverse cymbal.
   Nothing starts from silence mid-track; the one allowed silence is a
   composed drop-beat before a final chorus.
4. **One progression family per track.** Sections differ by density,
   register, and who carries the tune — never by swapping the harmonic
   language.
5. **Motif development.** Every motif gets stated, varied, and answered.
   No 4-bar drive-by ideas.
6. **Thesis early.** State the hook (quiet, solo, half-voice) in the
   first ten seconds; skip the long DJ/settle-in intro. The outro
   bookends it — the same solo statement closes the track.
7. **The fusion payoff.** The final chorus sounds question and answer
   *together*: the track's counter-theme under the refrain (Sihaya
   chorus 4). This is earned, not default — before the fusion the two
   ideas never fully overlap.
8. **Verification in the script.** Print: hook-statement count,
   per-section RMS with ordering checks (chorus above its pre-chorus,
   final chorus loudest, bridge trough quietest), and a seam checklist
   naming what crosses every boundary. Structure verifiable without
   listening. (Codified as the repo-wide standard in `../VERIFY.md`.)

## What stays behind (no cross-pollination)

- **The Dune palette.** No wind beds, worm rumbles, duduk, ney, chant,
  choir, darbuka, or D Phrygian dominant. Each trance track keeps its
  own established sound: nachtkind's Eye Q kit + gothic piano, lost's
  warm five (lead/pluck/pads/piano/cello), tech_noir's Fiedel machine.
- **Vowel singing / vocals.** These tracks stay instrumental, the
  refrain carried by an instrument (piano, lead, fanfare). The rule was
  suspended ONCE (`unsung`, 2026-07: a sung TTS-hybrid hook, real
  words) and the verdict was a dead end — pitch-perfect but the voice
  sounds strange to the ear. So the rule stands again, dated and
  tested, until someone brings a genuinely new idea for vocal
  naturalness — not just a rerun of the hybrid recipe.
- **Existing genre rules stay load-bearing**: the warmth recipe, the
  Eye Q dry/wet contrast, the 13/16 limp, no acid in lost, dread =
  sadness not horror. The doctrine changes *form*, never timbre.

## How song form maps onto trance

| song | trance |
|------|--------|
| verse | groove section carrying the melodic questions |
| pre-chorus | the build / layering rise |
| chorus | the drop, stating the refrain identically |
| bridge | the breakdown — teardown and rebuild, ending in the drop-silence beat |
| outro bookend | solo hook statement after the machinery stops |

The trance convention "add one element every 16 bars" survives as the
*development engine inside verses* — it stops being the whole form.
Exception: tech_noir is a machine score, not dance music — it takes the
doctrine (Q/A, refrain identity, fusion, seams) *without* the pop form;
see its note doc.

## Roadmap — status

All five tracks are built, each printing the `../VERIFY.md` blocks with
all checks passing:

1. **lost_v6** (`lost_v6.py`, notes `lost_v6_notes.md`) — DONE. One
   refrain, three lights: the Bm–G–D–A loop entered at three rotation
   points, so the *identical* refrain lands bright (D), sad (Bm), or
   resolved — the emotion is the harmony's light, never the tune.
2. **nachtkind_v3** (`nachtkind_v3.py`, notes `nachtkind_v3_notes.md`)
   — DONE. The gothic piano theme as a Q/A refrain hanging on the F#
   leading tone (resolved F#→G across every seam); the piano/lead duet
   earned progressively: alone → composed echoes → the fusion.
3. **tech_noir_v3** (`tech_noir_v3.py`, notes `tech_noir_v3_notes.md`)
   — DONE. The doctrine without the pop form: hollow-ended fanfare
   question vs love-theme answer at *contour* level (the duality lives
   across dimensions — melody vs bassline, harmony trades), the
   interrogation, the fusion over an unmoved pedal, ends cold.
4. **ungeschrieben** (`ungeschrieben.py`, notes
   `ungeschrieben_notes.md`) — DONE. The from-scratch original became
   the **two-reveal form** (1992 proto-trance, blueprint in
   `../../inspiration/Zyon-No_Fate.md`): withheld thesis (the ghost
   foreshadow — a sanctioned doctrine deviation), the filter arc as
   the development engine (printed and checked), rompler strings, one
   spoken-word drop with a documented `VOICE_GAIN` knob.
5. **unsung** (`unsung.py`, notes `ungesungen_notes.md`, probe
   `unsung_probe.py`) — BUILT, but the verdict was **a dead end**: the
   first vocal-song attempt (the hybrid TTS-graft voice, pitch verified
   to 3 cents) passes every check, yet the sung voice sounds strange,
   the spoken bridge drop is awkward, and as an instrumental it offers
   little. Kept for reference; see its notes doc for the lesson.

The doctrine has three proven shapes — **song form** (lost, nachtkind),
**machine score** (tech_noir), **two-reveal** (ungeschrieben) — with
the check variants recorded in `../VERIFY.md`. The vocal song is NOT
yet a proven shape: unsung tried it and stalled. Next candidates: a
second original in a proven shape, or a new shape entirely — note doc
with embedded questions first, as always.

## Classical → trance: the source list (2026-07-03)

A lot of successful instrumental techno/trance borrowed from the
classical canon. We want sources that are **not already worn out by
the dance floor**. Off the table as sources (they are precedents that
prove the move works, nothing more): Barber's *Adagio for Strings*
(Ferry Corsten/Tiësto), Pachelbel's *Canon*, *Für Elise*, *O Fortuna*,
Bach's *Toccata & Fugue*, Albinoni's *Adagio*
(already euro-danced in the 90s), Grieg's *Mountain King*, the
*Moonlight* first movement — plus everything on William Orbit's
*Pieces in a Modern Style* (Barber again, Ravel's *Pavane*, Górecki 3,
Cavalleria rusticana): covered means claimed.

What makes a piece translate: a hummable theme (refrain identity for
free), loop-compatible harmony (ground bass / chaconne / ostinato —
the trance loop 300 years early), modal color, drone/pedal tolerance,
and a formal arc that maps onto one of our proven shapes. As always:
one blueprint doc per piece in `../../inspiration/` (the
Symmetry/No-Fate flow), then a notes doc with open questions, then the
track. We take the *form and theme*, never a sampled recording —
everything stays synthesized.

The candidates:

1. **Satie — Gnossienne No. 1** (1890, solo piano). Modal, hypnotic,
   bar-less; the melody floats free over an oscillating two-chord
   minor accompaniment that is already a trance loop. Almost zero
   dance remixes (the Gymnopédies took the ambient hits). Fit: the
   dirty dream piano carries it; early-dark or dream both work.
   Shape: song form, the accompaniment as the unmoved ground.
2. **Debussy — La cathédrale engloutie** (1910, Préludes I). The
   sunken cathedral rising from the sea and sinking back — continues
   Adrift's ocean thread; parallel-fifth modal swells, bell tolls, one
   huge crest. Essentially never club-remixed. Shape: single-wave
   (penumbra's), with the rise-crest-sink baked into the source.
3. **Purcell — Dido's Lament** (1689). THE ground bass: a repeating
   5-bar descending line with the lament unfolding over it — a
   looping bassline with development on top, i.e. trance form three
   centuries early. Known, but not dance-worn. Note: the ground is
   *chromatic* — would need a sanctioned exception to the diatonic
   rule, agreed in its notes doc. Shape: a new one — "the ground"
   (loop constant, everything above develops).
4. **Holst — Neptune / Venus** (1914–16, The Planets). Actual space
   music: Venus floats, Neptune dissolves into an offstage **wordless
   female choir** fading to nothing — our breath choir's direct
   ancestor, and the "space sounds" answer. Mars is worn; these two
   are not. Shape: texture-led, likely two-reveal or a state piece.
5. **Chopin — Prelude Op. 28 No. 15 "Raindrop"** (1839). One repeated
   pedal note through the entire piece — a pulse/ostinato the beat can
   own — with the dark C♯-minor middle as the composed trough. Media-
   known, barely dance-remixed. Shape: song form with the pedal as the
   seam device everywhere (nothing ever stops).
6. **Rachmaninoff — Vocalise** (1915). A melody *written wordless* —
   the one source whose theme the breath choir could legitimately
   carry without breaking the instrumental rule (no words by design,
   not by omission). The careful path back toward a "vocal" track
   after unsung's dead end. Shape: song form, choir as refrain voice.
7. **Fauré — Pavane** (1887, F♯ minor). Modal melancholic theme over a
   walking pluck pulse; the dreamier, less-claimed sibling of Ravel's
   (Orbit took Ravel's, not this). Shape: song form, dream-era palette.
8. **Bach — "Ich ruf zu dir, Herr Jesu Christ" BWV 639** (chorale
   prelude). A three-voice texture that is already sequencer music:
   steady arpeggiated middle voice, walking bass, long-tone chorale on
   top. The precedent is perfect: Artemyev's synth arrangement carried
   Tarkovsky's *Solaris* (1972) — proto-electronic before Switched-On
   wore off. Shape: the ground/chorale split maps to bass-arp/refrain.
9. **Vivaldi — Winter, RV 297** (1725, The Four Seasons; added on
   review). Honest wear-warning: this is the most-claimed source on
   the list — Max Richter recomposed the whole cycle (2012), Orbit's
   album took *L'inverno* too. The unworn corner is the middle
   **Largo**: a pizzicato rain-ostinato under one long cantabile
   melody — offbeat pluck + refrain, a dream-trance texture as
   written. The famous shivering repeated-chord ostinato of the first
   Allegro comes along as *texture* only (the icy stab/tremolo bed),
   not as the theme everyone has already stormed through. Source key
   is F minor — ungeschrieben's identity — so it transposes; decide in
   its notes doc. Shape: song form; Largo theme as refrain, the
   Allegro shiver as the verses' cold engine.

Recommended first two: **Gnossienne No. 1** (the piano-led early-dark
one) and **La cathédrale engloutie** (the dream one, and the ocean
thread continues). Dido's Lament is the form-nerd wildcard when we
want a new shape rather than a new palette.

## Conventions (unchanged)

Same as `CLAUDE.md` here + `../dune/CLAUDE.md`: standalone scripts,
duplicated helpers, seeded RNG, revisions get a new WAV name — never
overwrite a WAV the user has listened to (e.g. `lost_v4.py` had already
rendered `lost_v5.wav`, so the next revision became `lost_v6.py` →
`lost_v6.wav`). WAVs to `/workspace/music/`, stage in git, no commit
without asking.
