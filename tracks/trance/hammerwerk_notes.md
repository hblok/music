# Hammerwerk — design notes (ABANDONED)

**The hoover track.** Working title *Hammerwerk* (the industrial
hammer mill — the German naming line continues; alternatives in Q1).
Seed **1991** — the year "Dominator" dropped. Blueprint:
`../../inspiration/Dominator_Human_Resource.md` (Human Resource,
1991 — early Belgian/Dutch hardcore rave), already analysed and so
far unclaimed by any track.

THE CONCEPT — the fourth station of the machine-voice arc, and the
turn: maschinenherz LEARNED to sing, silver_wire sang SOLO,
morgenland sang an OLD SONG — **hammerwerk stops singing and starts
SHOUTING**. The hoover stab is the machine's fist: snarling,
detuned, mid-heavy, the voice of the 1991 warehouse. Where every
prior track earned warmth, this one earns a LICENSE TO SNARL — a
declared, guard-railed exception to the warmth recipe, like
ungeschrieben's Q 2.2 resonance license (Q7).

## What the blueprint gives (mechanisms, never samples)

- **The hoover** (Alpha Juno "WhatThe?" family): detuned saw + PWM
  cluster, aggressive chorus, the fast pitch-SWOOP attack (the
  vacuum-cleaner dive into each stab), heavy portamento between
  stabs. Mid-heavy 300 Hz–3 kHz. It is bass and lead SIMULTANEOUSLY
  — there is no separate bassline in the source; low end = kick +
  the hoover's low harmonics (+ our big-room boom, see below).
- **The riff = the refrain**: ONE 1-bar motif (2-bar with variation)
  of root-anchored chromatic slides — root, ♭2, ♭3, heavy pitch-bend.
  Harmony is static drone; the "chords" are the cluster's own
  detuning. The song doctrine maps cleanly: the riff's question
  climbs and HANGS on the ♭2; the answer slams back to the root
  (the house mechanism in its angriest dialect).
- **Rave stabs**: sampled-orchestra minor hits with 12-bit sampler
  grit, pitched down, punching offbeats — the between-instruments
  answer to the hoover's call. We synthesize an orchestral-ish burst
  (saw-string stack + noise bow) then BITCRUSH it (12-bit, ~22 kHz
  downsample — the aliasing IS the era).
- **The kit**: 909 four-on-the-floor with saturated midrange knock
  (pre-gabber, not yet square-wave), offbeat 8th closed hats, clap
  on 2 & 4, snare-roll transitions, crash accents. Rigid, no swing,
  deliberately simple — the hoover carries all aggression.
- **Structure** (additive/subtractive, mapped to our song form):
  intro stabs → riff reveal → "verse" (the MC slot — see Q2) →
  breakdown 1 (hoover sustains alone) → drop → breakdown 2 (riser)
  → FINAL PEAK (densest) → strip outro, near-abrupt rave ending.

## What stays ours

- **The song doctrine**: riff stated identically and counted; Q/A at
  melody level (♭2 hang → root slam), instrument level (hoover call,
  stab answer), section level (breakdowns ask, peaks answer); thesis
  early (one naked hoover swoop in the first ten seconds); bookend =
  the last lone stab ringing into the abrupt stop (the tech_noir
  cold-end license, second use).
- **The big-room master** (directory default): pump, sub-boom under
  the kick (solving the source's thin-sub problem the 2026 way),
  high+low shelves, tanh bus limiter, FLAC out. The 1991 aesthetic
  over a modern floor is the point of the fusion.
- **Instrumental rule**: the MC vocal does NOT come along (Q2 decides
  what takes its slot).
- **Banned as ever**: Dune palette (morgenland's darbuka license was
  a one-track sanction, not a precedent), gothic piano, rompler
  strings, TTS singing, other tracks' claimed devices (ladders,
  ice-cracks, tom fills, reverse cymbal as MAIN seam — one riser
  sweep is era-native here and declared).

## Sound-design sketches

- **Hoover patch**: 5–7 saw copies detuned ±0.5–1.5 % + a PWM layer
  (pulse with slow width LFO), summed through a chorus (two 8–14 ms
  modulated delays L/R — instant width, era-correct); the SWOOP =
  pitch starts +7 semitones and falls exponentially over ~90 ms into
  each stab; portamento (glide_curve) between tied stabs; bandpass
  emphasis 300–3000 Hz; drive tanh(≤1.5). The warmth-recipe
  guardrails that STAY even under the license: no parked iirpeak
  scream, rolled partials 1/k^1.15 (not raw 1/k), a 0.2× sine body
  so the low register has weight, commit modest (the snarl is
  spectral, not loud).
- **909-knock kick**: our trance kick + tanh(1.6) saturation and a
  200–400 Hz "knock" bandpass layer; the big-room boom still owns
  the true sub underneath.
- **Rave stab**: Fm/F#m minor cluster (root, ♭3, 5, root+12) of
  fast-attack saw+string burst, 60 ms hold, bitcrushed to 12-bit /
  22 kHz, then pitched DOWN a fourth (resample) for menace.
- **Riser**: single pitch-rising drone + filtered noise into each
  drop (era-native, declared — not nachtkind's reverse cymbal).

## Verify paragraph (implement exactly)

Section map; riff statement count ≥ 8 (1-bar riff, identical map,
printed as a 16-step grid with slides/swoops marked); chromatic
budget check — every riff pitch ∈ {root, root±1, root+3, root−12,
root+12} (the blueprint's root/♭2/♭3 language, NOTHING diatonic
sneaks in); ♭2-hang and root-slam landmark check; stab placement
check — 100 % of stab onsets on offbeats; kick 4/4 duty check;
per-section RMS with orderings (breakdowns are troughs, final peak
is the summit, outro strips); the >120 Hz drop comparison if two
drops emerge; big-room metrics with pinned floors; the bitcrush
verified by construction (print the stab's bit depth / rate).

## Open questions for review

1. **Name.** *Hammerwerk* (recommended — the industrial hammer mill,
   and the track IS hammer blows) vs *Maschinensturm* (the machine-
   breakers' riot — great concept-fit but collides with
   maschinenherz's prefix) vs *Presswerk*. Seed 1991 either way.
   Answer: Reopened (2026-07-10): the German naming line is retired —
   pick an English title instead (candidates: *Foundry*, *Ironworks*,
   *Piledriver*). Final name pending; seed stays 1991.

2. **The MC slot.** The source's rap verses need a replacement:
   (a) RECOMMENDED — the hoover answers ITSELF: low-register growl
   phrases in the "verses" vs high-register scream in the peaks
   (register-jump call/response — the silver_wire device in rave
   dialect, keeps the track fully instrumental); (b) ONE spoken-word
   drop with a `VOICE_GAIN` knob (the ungeschrieben sanctioned
   device — a short German phrase, e.g. "das Hammerwerk", used
   once); (c) nothing — pure machine. (a) and (b) can combine.
   Answer: (2026-07-10) Not (b) — no rap / spoken-word direction at
   all; the MC slot stays voiceless. Between (a) and (c), (a) stands
   as the recommendation: the fully instrumental register
   self-answer.

3. **Key.** F# minor (recommended — the blueprint cites F/F# by
   pressing, and F natural minor is ungeschrieben's claimed
   identity; F# keeps the directory's one-key-per-track cleanliness)
   vs F minor (the more-cited reading).
   Answer:

4. **Tempo.** 126 BPM (recommended — era-authentic, and the
   directory's first dance track below 130; the heaviness lives in
   the slower stomp) vs 135–140 (modernized hard-techno reading,
   closer to eisgang's lane — but then why not just eisgang?).
   Answer:

5. **Lo-fi grit budget.** Bitcrush on the rave stabs only
   (recommended — the era artifact as a spice, the big-room master
   stays clean) vs a whole-bus 12-bit pass (full 1991 authenticity,
   but it fights the validated master chain head-on).
   Answer:

6. **Breakbeat texture.** The blueprint hears a faint era breakbeat
   under some peaks. Skip for v1 (recommended — the four-on-floor
   stomp is the identity; a synthesized break is a whole new
   instrument for a background garnish) vs build it.
   Answer:

7. **The snarl license.** Confirm the declared warmth-recipe
   exception scoped EXACTLY to the hoover: mid-band 300–3000 Hz
   emphasis, tanh ≤ 1.5, chorus detune cluster — with the guardrails
   listed above (no parked resonance, rolled partials, sine body,
   modest commit). Everything else in the track (stabs aside, which
   get the bitcrush license instead) obeys the warmth recipe as
   written.
   Answer:
