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
- **Vowel singing.** These tracks stay instrumental. The refrain is
  carried by an instrument (piano, lead, fanfare) — the "voice" work
  continues in the dune songbook, not here.
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

All four tracks are built, each printing the `../VERIFY.md` blocks with
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

The doctrine now has three proven shapes — **song form** (lost,
nachtkind), **machine score** (tech_noir), **two-reveal** (ungeschrieben)
— with their check variants recorded in `../VERIFY.md`. Next candidates:
a second original in a proven shape, or a new shape entirely — note doc
with embedded questions first, as always.

## Conventions (unchanged)

Same as `CLAUDE.md` here + `../dune/CLAUDE.md`: standalone scripts,
duplicated helpers, seeded RNG, revisions get a new WAV name — never
overwrite a WAV the user has listened to (e.g. `lost_v4.py` had already
rendered `lost_v5.wav`, so the next revision became `lost_v6.py` →
`lost_v6.wav`). WAVs to `/workspace/music/`, stage in git, no commit
without asking.
