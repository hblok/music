# Phototaxis — design notes (2026-07-17, first tracks/psy/ track)

**The goa track — the swarm and the lamp.** Working title *Phototaxis*
(the biology of moths spiralling into light; alternatives in Q1 —
English titles per the 2026-07-10 rule). Seed **1995** — goa's golden
year (*Twisted*, *Trust in Trance*). This opens a NEW directory:
`tracks/psy/` — old-school goa (1995–97 school), deliberately separate
from `tracks/trance/` and from the dune psy engine.

THE CONCEPT — phototaxis is movement toward light. The track is built
from a SWARM of short interlocking FM voices (the moths) circling a
groove, and ONE anthem melody withheld until deep in the track (the
lamp). Form is the HYBRID agreed 2026-07-17: groove-first waves are the
spine — the loop is the identity, development is layers entering,
morphing and leaving — plus one withheld melodic reveal (the
two-reveal instinct at minimal dose; the classic goa "Mahadeva moment":
the true theme arrives late and re-frames everything before it).

**The genre claim**: 1995–97 goa is NOT the German/modern psy that
maschinenherz claimed (X-Dream school) and NOT the dune album's
Juno-Reactor tribal fusion. Its fingerprints: FM/PM timbres that MOVE
inside every note (the gurgle, the fizz), three-plus simultaneous
melodic layers interlocking across registers, moving basslines, static
harmonic ground with rare modal shifts, storyboard arrangements in
waves. The multi-voice counterpoint is the big unclaimed prize — every
track in this repo so far is one singer plus answers; goa is a
*colony*.

## Declared up front (not questions)

- **147 BPM, 4/4, ~7:30, F# natural minor** (key in Q2; 147 splits the
  difference of the era and stays off maschinenherz's 145).
- **Standalone script** `tracks/psy/phototaxis.py`, conventions per
  `../dune/CLAUDE.md` (duplicate helpers, no imports from other
  tracks, seeded rng, `commit()` bus, printed verify, WAV to
  `/workspace/music/`, FLAC encode, `_vN` on revision, never commit
  audio).
- **Groove-first entry** (the no-long-intro rule): kick and bass
  groove within the first 8 bars; FX-only open ≤ 4 bars.
- **Instrumental throughout** — no TTS, no spoken drop
  (ungeschrieben's license stays unused here; vocal-shaped slots are
  filled instrumentally per the 2026-07-10 rule). The "voice" of this
  track is the machine-elf chatter texture (see kit), synthesized, not
  speech.
- **The anti-arc rule holds** (directory law by now): no track-long
  cutoff ramp. Development = wave ledger (layers in/out), register,
  and the reveal. Per-voice timbre motion lives INSIDE notes (FM index
  envelopes), not across the track.
- **The big-room master** (validated default): sidechain pump — never
  on the anthem voice — sub-boom layer, master shelves, tanh bus
  limiter, wider pads; drop sub-60 share target 0.6–0.7.
- **The anthem voice sings** (the eisgang verdict, standing law):
  sustain + slow-ish attack + vibrato for the reveal melody. The swarm
  voices are short/percussive by design — they are TEXTURE-melody, the
  groove's own 16th layer, never the refrain carrier.

## THE FRESHNESS CONTRACT (the point of this track — banned lifts)

Per source, what is CLAIMED and stays out of this script:

- **dune/the_navigator**: the ratio-3 / index-4→0.8 decaying nasal FM
  lead recipe, its ratio-1 crystalline ping-pong arp, Hijaz Kar, the
  choir-formant pad, tabla tarang. FM as a *technique* is free — that
  exact dialect is not (see the FM orchestra: our ratios, our index
  behavior, different on purpose).
- **dune/water_of_life + sleeper_awakens**: D Phrygian dominant, the
  duduk/ney/chant/darbuka palette, the dune acid (Q 11) — the whole
  desert. Nothing eastern-instrument-shaped here.
- **maschinenherz**: the psy kit as a set (trance kick 150→45 dive,
  psy clap, psy zap, the K-b-b-b static-root bass with .8/.7/.95
  gains), the Vivaldi W1/W2/W4a/W8a mechanisms, the ported love-phrase
  voice.
- **silver_wire / morgenland / flightpath**: the ENTIRE 303 family —
  saw-core and square-core, iirpeak acid scream, CUT_PROFILE, accent
  cycles, the anchor system, the relay. **Hard rule: no saw-stack +
  iirpeak voice anywhere in this track** — the swarm is FM/PM only.
  Phrygian dominant / Hijaz is morgenland's.
- **eisgang**: W3/W5, circle-of-fifths walking, run-and-plant bass,
  the tick pair. **nachtkind**: reverse cymbal, gothic piano, the
  hang-on-the-leading-tone seam (used twice already — this track ends
  phrases differently, see the anthem). **ungeschrieben**: the filter
  arc, rompler strings, 909 tom fills. **tech_noir**: cold-end
  license not used; we end by subtraction (goa-true).

What "fresh" is BUILT from instead: the FM orchestra, the swarm
counterpoint, the moving bassline, the wave form. Each below.

## The FM orchestra (the new voice family)

All melodic sound is two/three-operator phase modulation —
`sin(φc + I(t)·sin(φm))` — and the psychedelia is that **I(t) and the
ratio are the expressive axis**, per note, always moving (the goa
answer to the 303's bright→dark sweep — same job, different physics).
Four voices, one family, distinct registers:

- **The gurgle** (anthem + wave lead, mid register): 2-op, ratio 2,
  index WOBBLED at 6–9 Hz (depth ~1.5) on held notes — the liquid
  goa warble; slow raised-cosine attack ~0.1 s, sung vibrato blooming
  after 0.3 s, warm (post-LP ~2400, `tanh(0.9)`). This is the singer.
  DECLARED DISTINCTION from the navigator lead: integer ratio 2 (not
  3), index *oscillates* (not a one-way decay), sustain voice (not a
  stab).
- **The fizz** (upper-mid runner): 2-op ratio 1 with **modulator
  feedback** (the DX7 trick — feedback FM approaches a saw without
  being one), index 2.5→1.2 per note, short gate ~0.8 — the fizzy
  goa 16th-cell voice. This is the closest legal thing to acid and it
  is not a 303.
- **The glint** (top register): ratio **3.53** (non-integer =
  inharmonic bell/metal partials), high index snapped shut fast
  (4→0 in ~80 ms) — glassy pings for the off-cells, hard-panned,
  sparse.
- **The murk** (low-mid): ratio 0.5 (modulator below carrier — hollow,
  sub-octave shadow), small index ~0.8, dark LP 1200 — doubles swarm
  cells a 12th below at low gain, the depth layer.

Plus the bed: a **deep evolving drone** for the breakdown only —
low, dark, slow-evolving per the standing drone rule (no beating
mid-frequency tone, pulses to true zero, anti-tinnitus).

## The swarm (the counterpoint engine — the track's thesis)

3–4 voices run SIMULTANEOUS one-bar 16th cells, interlocking by
construction: cells are built in code from complementary step masks —
where the fizz sounds, the glint rests; the murk shadows the fizz;
total swarm onsets per 16th step ≤ 2 (the anti-mud budget). Registers
separated ≥ 7 semitones between voice medians. Pitch material:
F# natural-minor cells circling the root and fifth — cells VARY per
wave (state / vary / answer, the standing development rule — a cell
that enters never just loops till it dies; it mutates every 8 bars or
hands off to another voice).

The swarm is the groove-first identity: it IS the hypnotic loop, it
develops by voice entries/exits and cell mutation (the wave ledger),
and it never carries the anthem. Two anthem FRAGMENTS (≤ 2 bars,
disguised as cells) hide in waves 3 and 5 — the foreshadow, counted
and printed.

## The moving bassline (the anti-K-b-b-b)

Kick-gap contract KEPT (bass silent on every kick 16th — that's
physics, and the printed duty check stays), but everything else moves:
per-bar bass cells with **≥ 2 distinct pitches per bar** (root/♭7/5
walks, octave dips — the Astral Projection gait), cell chosen per
wave, gains varying with the cell — never the fixed static-root
.8/.7/.95 roll. Voice: clean saw-free — a 2-op ratio-1 FM bass, low
index 0.6 (adds bite without a filter), LP 300, short gate. The bass
is a MELODIC participant of the swarm, lowest voice, not a pedal.

## The kit (goa, not psy-kit, not 909-dry)

- **Goa kick**: tight and clicky — 95→48 Hz in ~35 ms (fast knee),
  short body ~120 ms, distinct from the trance kick's long 150→45
  dive. 4/4 throughout the waves.
- **Hats**: offbeat open (goa law) + a SPARSE closed pattern (steps
  vary per wave — never the full 16th carpet; the swarm owns the 16th
  grid, the flightpath lesson).
- **Snare/clap**: a short noise-burst snare on 2 & 4, thin and dry
  (not the psy clap, not the 80s gate).
- **The chatter** (this track's FX signature — the machine elves):
  bursts of tiny high FM blips with random ratios/indices, 3–6 per
  burst, panned wide, at phrase punctuation and in the breakdown —
  replaces zaps (claimed) and reverse cymbals (claimed).
- **The bubble-rise** (this track's seam device): an accelerating
  rising arpeggio of short gurgle blips over the last 2 bars before a
  wave boundary — the composed riser; no noise sweeps.

## Form: waves + the withheld anthem

The WAVE LEDGER is the structure — printed, one row per 8/16-bar
wave: which voices are in, which cell each plays, bass cell, kit
state. Tension moves by addition AND subtraction (a wave that removes
the bass hits harder than one that adds a hat). Sketch:

open (chatter, drone breath, ≤ 4 bars) → W1 kick+bass cell A →
W2 +fizz cell → W3 +glint, murk shadows (foreshadow 1 hidden) →
W4 mutation, bass cell B → **W5 full swarm = drop 1** (foreshadow 2)
→ W6 subtraction dip (bass out 8 bars, swarm suspended) →
**THE POOL** (breakdown ~16 bars: beatless, the deep drone, chatter,
glint sparse — the psychedelic trough) → bubble-rise build (kick roll
last 4) → **W7 THE REVEAL = drop 2**: the anthem on the gurgle, full
groove, swarm thinned to two voices under it → W8 anthem + full swarm
FUSED (the payoff: the colony sings the counterpoint UNDER the lamp)
→ W9 subtraction series (anthem out last — the lamp outlasts the
moths) → exit: kick+bass alone 8 bars, one last chatter, stop.

THE ANTHEM: 8 bars, stated ≥ 3 times after the reveal, never before
(fragments aside). Its phrases end UP-CONTOUR with the final note
HELD on the fifth (C#) over the i ground — the hanging-fifth device,
NOT the leading-tone hang (nachtkind/maschinenherz's, twice used);
only the final statement resolves the held C# down to F#, and the one
borrowed colour of the track — E# inside a single V chord — sounds
under exactly that resolution. Harmony elsewhere: static F# ground in
the waves (goa-true); the anthem waves walk **i–VI–VII–v**
(F#m–D–E–C#m) — the minor v is the modal, floaty, era-true choice (no
track claims it; ungeschrieben's i–VI–VII never had it).

## Verify paragraph (implement exactly)

Section map; **the wave ledger printed** (per wave: bar span, voices
in/out, cell ids, bass cell, kit state); per-section RMS post-master
with orderings (drop 2 ≥ drop 1 above 120 Hz; the pool is the global
trough; exit < drops; hard stop ≤ 200 ms after last onset). Big-room
metrics with pinned floors (drop sub-60 share 0.6–0.7, pump
floor/beats). SWARM block: per-16th-step simultaneous-onset histogram
(≤ 2 everywhere, printed); voice register medians with pairwise gaps
≥ 7 semitones; cell mutation count ≥ 1 per 8 bars per active voice;
interlock ratio (share of sounding steps covered by exactly one voice)
printed with an agreed floor ≥ 0.6. ANTHEM block: first full statement
bar printed and > 55 % into the track; statements after reveal ≥ 3;
foreshadow fragments exactly 2, each ≤ 2 bars, bars printed; final
statement's C#→F# resolution and the single E# occurrence asserted.
BASS block: kick-gap duty check (zero bass onsets on kick 16ths);
distinct pitches per bar ≥ 2 (histogram printed); ≥ 3 distinct bass
cells used. FM DIALECT block: per-voice (ratio, index range, attack)
table printed; zero saw-stack/iirpeak calls (declaration); at least
one non-integer-ratio voice active in every wave with the glint.
Anti-arc: no monotone cutoff/index trend across statements (spread and
slope printed, ~zero). Seam block: bubble-rise count = wave-boundary
count in the drops' half; zero reverse cymbals / tom fills / zaps
(declaration). Drone rule: breakdown bed spectral centroid < 400 Hz,
amplitude reaches true zero each cycle. FLAC written next to the WAV.

## Open questions for review

1. **Name.** *Phototaxis* (recommended — the concept is the form: the
   swarm spirals, the reveal is the light; fresh, one word, no genre
   cliché) vs *Machine Elves* (the McKenna image — very goa, ties the
   chatter FX to the title, but jokier) vs *Heliotrope* (the plant
   that turns to the sun — prettier, less kinetic). Seed 1995 either
   way.
   Answer: Phototaxis

2. **Key.** F# minor (recommended — unclaimed anywhere in tracks/,
   sits between maschinenherz's Em and silver_wire's Am so the swarm
   registers clear both; goa lived around E/F#) vs E minor (era-truest
   but maschinenherz's) vs C# minor (unclaimed, darker, pushes the
   fizz very high).
   Answer: F# minor

3. **Inspiration doc first?** Option A (recommended): implement from
   this plan now — the era grammar above is well understood, and the
   freshness contract is the hard part, already settled. Option B:
   first run inspector (`--separate`) on one classic goa reference
   (e.g. an Astral Projection or Hallucinogen track you drop in) and
   write `inspiration/` notes before implementation — costs a session,
   buys era-calibration of cell shapes and kit weights. You said
   "come back to that"; this is the come-back point if wanted.
   Answer: Option A - let's go.

4. **Swarm size.** 3 pitched voices + murk shadow (recommended — the
   anti-mud budget is provable and the mix stays readable at 147) vs
   full 4 independent voices (denser, era-max, riskier mud; the ≤ 2
   simultaneous-onset budget gets tight).
   Answer: 3 pitched + murk

5. **Anthem harmony.** The i–VI–VII–v loop above (recommended) vs
   keeping even the anthem waves on the static F# ground with the
   melody implying the changes (more hypnotic, purer goa — but the
   reveal lands softer without the ground shifting under it).
   Answer: Let's try the i–VI–VII–v loop
   Extra note here: It would bee good to develop a way to quickly output an example of this, so it's easier to judge before we create everything. Let's make a note of that, and see if we can develop an app or just part of the process which comes before the full generation.

6. **Era cheese level.** The chatter + bubble-rise as designed
   (recommended — signature but tasteful) vs adding one loud
   90s-style FX drop moment (a big pitch-dive "laser fall" before
   drop 2 — period-authentic, undeniably fun, risks kitsch).
   Answer: chatter + bubble-rise

7. **Directory boilerplate.** Add a short `tracks/psy/CLAUDE.md`
   (pointing at `../dune/CLAUDE.md` conventions + this freshness
   contract) now, or only after the first track ships and the
   directory has actual practice to document (recommended: after —
   one track is not a convention yet)?
   Answer: Let's wait.
