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
   listening.

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

## Roadmap

Note docs in this directory, in suggested build order:

1. **`lost_v5_notes.md`** — the emotional journey retold as a song:
   one refrain re-lit by the harmony (bright D / sad B / resolved D).
   Closest to done already (the cohesion trinity is in place).
2. **`nachtkind_v3_notes.md`** — the gothic piano theme becomes a true
   refrain; piano/lead call-and-response replacing the stacked duet
   until the fusion earns it.
3. **`tech_noir_v3_notes.md`** — the experiment: how much song doctrine
   fits a 13/16 machine score (answer: Q/A + fusion + seams; no
   verse/chorus).

Later, once the retrofits prove the port: an **original song-form
trance track** designed from bar 0 as a song (refrain written before
the groove) rather than retrofitted — genre open (Frankfurt anthem or
uplifting), decide after hearing the three revisions.

## Conventions (unchanged)

Same as `CLAUDE.md` here + `../dune/CLAUDE.md`: standalone scripts,
duplicated helpers, seeded RNG, revisions get a new WAV name — never
overwrite a WAV the user has listened to (note: `lost_v4.py` already
renders `lost_v5.wav`, so the *lost_v5 script* renders `lost_v6.wav`).
WAVs to `/workspace/music/`, stage in git, no commit without asking.
