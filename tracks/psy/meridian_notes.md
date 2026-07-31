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

## Implemented (2026-07-31) — `meridian.py` → `meridian.wav` (~5:06)

Built from the answers above; all VERIFY checks pass (0 fail). 145 BPM,
seed 1997. Reuses the phototaxis engine (helpers, pad bed, big-room
master, verify scaffolding); the composition is inverted per the thesis.

**The star = the long morphing lead** (`lead_note`): sustained + sung,
FM index morphs on a slow LFO tied to GLOBAL time (period 6.6 s = 4 bars,
phase-continuous across notes → the liquid snaking line), ratio steps
2→3 on the high euphoric notes. Present in 66% of bars (the through-line,
checked). The swarm (fizz/glint/murk) is demoted to a shimmer BED — in
the choruses the lead sits above every swarm voice (lead 1.0 vs fizz
0.30, checked = the inversion of phototaxis).

**Euphoric sunrise on a heavy engine (Q3).** Verses in E DORIAN over a
heavier/darker kick (102→42, long body + sub tail) and a heavy sub-octave
bass; the choruses bloom to bold Picardy E MAJOR (Q7). Written in
DEGREES so the SAME refrain flips minor→major — the major 3rd (G#)
appears in the choruses and NOWHERE in the verses (checked). The refrain
arcs (rise→peak→descent) and hangs on the 3rd — which itself blooms
G→G#; the final chorus resolves that 3rd down to the root E (a new
cadence, not phototaxis's fifth-hang).

**Seams (Q6, Meridian's own vocabulary):** `harmonic_bloom` (an FM chord
whose index blooms open across 2 bars) into each chorus downbeat;
`tape_flutter` (wow+flutter pitch-warble) swelling across the bridge and
outro seams. Phototaxis's chatter + bubble-rise are NOT reused. Q8: the
foreshadow fragments were dropped (kept distance from phototaxis).

**Master.** The v2.1 growl guardrail carried over — but the growl check
was REFINED: crest alone is a bad proxy (a heavy track sits at crest
~2.9 and is still clean), so the check is now near-ceiling **hot%** (the
direct saturation measure): FINALCH hot 0.24%, no clip. sub-60 share
0.37–0.40 — lower than phototaxis because Meridian is bright by design
(euphoric leads), with the heavy low end present in absolute terms.

Form: OPEN→INTRO→THESIS(0:20)→VERSE1/2→BUILD1→CHORUS1(1:39)→VERSE3→
CHORUS2→VERSE4→BRIDGE(3:12, dark Dorian, half-lit lead, one drop-beat)→
BUILD2→FINALCH(3:52, the payoff)→CHORUSOUT(4:18, resolve)→OUTRO(4:45,
wistful Dorian bookend). Listen verdict pending.

## VERDICT: DEAD END (2026-07-31 listen)

Failed attempt — "nothing to do with goa/psy-trance; more akin to
country/western (Clint Eastwood on his horse with his harmonica)." Kept
for reference (like `../trance/unsung.py`), NOT corrected. The lesson is
the value here — it maps where goa's genre boundary is:

WHY IT LEFT THE GENRE (diagnosis, so the next goa track doesn't repeat it):
- **Picardy MAJOR choruses** were the single biggest wrong turn. Goa is
  MODAL and MINOR/dark. A major key reads pop/folk/country — not trance.
- **A warm, sustained, vibrato "singing" lead playing an arch melody** =
  a harmonica / pedal-steel / folk voice. Goa leads SNAKE and GNARL and
  REPEAT hypnotically; they do not "sing a tune". The `lead_note` (ratio
  2, warm LP 2600, sung vibrato, arch contour) is a harmonica.
- **The song-doctrine "the lead sings a refrain" does NOT transfer to
  goa.** That doctrine is for the trance/song tracks. In goa a hummable
  warm major refrain = a ballad, and a mid-tempo heavy kick under it =
  a Western groove.
- **The "euphoric sunrise" emotional target (Q3)** was the seed: chasing
  euphoric-MAJOR melodicism pulled it out of goa. Goa euphoria — when it
  exists — comes from MODAL uplift + hypnotic layering, never a major-key
  singing melody in a warm timbre.

WHAT THIS CONFIRMS: phototaxis worked because it stayed F# MINOR, MODAL,
SWARM-HYPNOTIC. Goa identity = modal + minor/dark + hypnotic + gnarly-
electronic + repetitive-driving. "Freshness" within goa must keep that
core; invert the COMPOSITION (swarm vs lead), never the genre DNA.
See memory [[feedback_goa_genre_boundary]].
