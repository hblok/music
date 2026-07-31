# Meridian — design notes (2026-07-30, second tracks/psy/ track)

**Working title *Meridian*** (the high arc / the turning line — warm, a
long journey; alternatives in Q1). Seed **1997** (the late-goa "sunrise"
year, to phototaxis's 1995). The second goa track: it **reuses the
phototaxis engine** (the FM orchestra, the swarm, song form, the
big-room master — all validated and documented in `CLAUDE.md`) and must
earn a distinct identity through a *different compositional thesis*, not
a re-skin.

## THE THESIS — invert phototaxis (the freshness move)

Phototaxis's star was the **swarm**: many short interlocking 16th cells,
the anthem a late guest. Meridian's star is **the long morphing lead** —
ONE continuously-evolving FM voice (the gurgle, promoted and extended)
that snakes and *sings* across long phrases, present as the through-line
from early on. The swarm is **demoted to a shimmering accompaniment
bed** under the lead. Same voices, opposite center of gravity.

The morphing is the psychedelia: the lead's **ratio and index morph
cyclically across bars** (a slow LFO on the FM index, occasional
ratio steps between integer values) — the "liquid, snaking" goa line.
DECLARED DISTINCTION from the navigator dialect (banned) and from
phototaxis's gurgle: this is not a one-way 4→0.8 decay per note, and not
a short wobbled stab — it is a *sustained line that morphs over 8–16
bars*, a journey inside the timbre.

## Emotional target — bittersweet euphoria (the warm lane)

Not phototaxis's kinetic spiral, not dread. **Melancholic-hopeful**:
minor-rooted verses that **lift to a major-tinged chorus** (the goa
"sunrise", but wistful, per the repo warmth rule — warm not squeaky,
sadness not horror). The lead sings a refrain you can hum; the lift is
the euphoria, the minor root is the ache.

## Declared up front (not questions)

- **~145 BPM, 4/4, ~5:00–6:00, E Dorian** (E F# G A B C# D — natural
  minor with a **raised 6th**; the ♮6 and the resulting **IV major** are
  the built-in major-lift, unclaimed in psy — phototaxis is F# natural
  minor, morgenland/water is Phrygian dominant). Key/mode is Q4.
- **Standalone script** `tracks/psy/meridian.py`, conventions per
  `CLAUDE.md` here + `../dune/CLAUDE.md` (dup helpers, seeded rng,
  printed VERIFY, WAV+FLAC to `/workspace/music/`, `_vN` on revision,
  never commit audio, the `--preview` knob).
- **Song form** (the validated shape): thesis early → verses → choruses
  → a BRIDGE that keeps a pulse + a half-lit lead across it → the
  fullest restatement (payoff) → a solo bookend. No long intro; no
  beatless hole (the phototaxis lessons, now directory law).
- **The big-room master with the crest/HP guardrail** (the v2.1 fix is
  now the default): master HP ~30 Hz, watch loud-section crest ≥ 3.2,
  no int16 clip. The pad bed under the whole groove stays.
- **The lead sings** (the standing law): sustained + slow-ish attack +
  vibrato; it carries the refrain. The swarm never carries it.

## The freshness contract (what stays OUT — now incl. phototaxis)

Repo-wide bans hold: **no saw-stack + iirpeak 303** (silver_wire /
morgenland / flightpath / maschinenherz), no navigator ratio-3
decay-index lead, no Phrygian-dominant / duduk / ney / chant / Eastern
palette (the desert), no reverse cymbals / zaps / tom fills / noise
sweeps. **New this track, claimed by phototaxis:** the moth/light frame,
the swarm-as-star role, and the **chatter + bubble-rise** FX vocabulary
— Meridian needs its OWN seam device (Q6). The swarm is here, but as a
bed, and its cells are Meridian's own (Dorian, longer, softer-attack —
a shimmer, not a chatter).

## The new signatures (what "fresh" is BUILT from)

1. **The morphing lead** (the thesis voice): the gurgle with a cyclic
   index LFO (depth ~2, rate a slow fraction of the bar) and staged
   ratio changes across the phrase; sustained, sung, warm — the liquid
   line that is the track.
2. **The major-lift** (E Dorian's IV / ♮6): the chorus tilts major
   without leaving the mode — the bittersweet euphoria, no cheese.
3. **A new seam device** to replace chatter/bubble (Q6): proposal — a
   **tape-flutter** (a slow wow/flutter pitch-warble under a boundary) +
   a **harmonic bloom** (a chord whose FM index blooms open across two
   bars into the downbeat). Composed, not an effect; no noise sweeps.

## Form + verify (implement per phototaxis + these deltas)

Reuse phototaxis's VERIFY blocks (section map/ledger, per-section RMS
orderings, big-room + crest/peak, swarm interlock, bass kick-gap, FM
dialect, seam checklist, no-beatless-gap, hard stop, FLAC). New/changed
checks: **lead-presence** (the morphing lead sounds in ≥ N% of bars —
it's the through-line, not a late guest); **morph is cyclic not
one-way** (index LFO spread printed, net slope ~0 across the track — the
anti-arc rule, applied to the lead); **the major-lift** (chorus contains
the ♮6 / IV-major, verses don't, printed); **swarm is a bed** (its RMS
share sits UNDER the lead's in the choruses — inverted from phototaxis).

## Open questions for review

1. **Name.** *Meridian* (recommended — the high arc, a long warm
   journey, ties to the one-long-line thesis) vs *Solstice* (the
   turning point; bittersweet built in — the longest light also the
   turn toward dark) vs *Ley Line* (the mystic earth-current = the one
   snaking line; very goa, two words). Seed 1997 either way.
   Answer: Meridian is fine.

2. **The thesis.** The long morphing lead as the star (recommended — the
   clean inversion of phototaxis; a genuinely different track from the
   same engine) vs another swarm-led track (safer, but risks
   re-skinning phototaxis) vs a true co-lead (lead + swarm trading the
   star role — richer, harder to keep readable).
   Answer: Long morphing lead.

3. **Emotional target.** Bittersweet / melancholic-euphoric (recommended
   — the warm lane; minor verses, major-lift chorus) vs dark driving
   night-goa (Phrygian, relentless, the swarm as menace — a hard
   contrast to phototaxis's brightness) vs full euphoric "sunrise"
   (major-key hands-in-air — the one emotion the repo hasn't done;
   cheese risk managed by the song form).
   Answer: Let's focus on "full euphoric sunrise". However, mixing in some "night-goa", especially with a heavy beat and baseline should work.

4. **Mode / key.** E Dorian (recommended — the ♮6/IV give the lift from
   inside the mode; unclaimed) vs E natural minor with a borrowed-major
   chorus (a sharper light/dark switch) vs (if Q3 = dark) E Phrygian
   (the ♭2 menace).
   Answer: E Dorian is good

5. **Tempo.** 145 BPM (recommended — the goa pocket, just off
   phototaxis's 147) vs 147 (match) vs 150 (pushier, toward the
   later-90s school).
   Answer: 145

6. **The new seam device.** Tape-flutter + harmonic-bloom (recommended —
   composed, warm, fits the morphing-lead world) vs a single device
   (pick one) vs something else you hear.
   Answer: Tape-flutter & harmonic-bloom - interesting.

7. **The major-lift mechanism.** Dorian IV + ♮6 (recommended — lift from
   inside the mode, subtle) vs a full Picardy-major chorus (a stronger,
   more obvious sunrise) vs stay minor and imply the lift with the
   melody only (purest, softest).
   Answer: Let's go bold: a Picardy-major chorus lift

8. **Carry-over check.** Definitely kept: the pad bed, the big-room
   master + crest guardrail, song form, the FM voice family. Open: keep
   the two foreshadow fragments? keep the exact swarm density (≤ 2
   onsets/16th) or thin it further since it's now a bed? keep the solo
   bookend? Any phototaxis element you specifically want NOT repeated?

Answer: Well, it's OK to carry elements over. As long as the entire song does not feel exactly the same. So, the big-room master and guardrail worked. Song form is fine. FM voice family also OK, but watch for too similar melodies.
Foreshadow fragments: well, doesn't have to be, and if it makes it too similar to the previous track, let's come up with something else.

9. **Inspiration doc first?** Option A (recommended): implement from this
   plan — the engine and the era grammar are understood, the thesis is
   the fresh part and it's specified. Option B: run inspector `--separate`
   on a bittersweet-goa reference first (a Hallucinogen / Etnica-style
   track you drop in) and write an `inspiration/` note — costs a session,
   buys calibration of the morphing-lead shape. (phototaxis went A.)

Answer: the inspiration docs are a seperate effort, and do not have th be intangled with the planning.
However, finding a good Hallucinogen track is a good idea. Let's make a note of that, so we come back to that another day.
