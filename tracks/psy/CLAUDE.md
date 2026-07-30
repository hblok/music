# CLAUDE.md — psy/ generators

Implementation guide for the old-school **Goa (1995–97)** generators in this
directory. The shared **stack, common architecture, and conventions** live in
`../dune/CLAUDE.md` (numpy+scipy only, stdlib `wave` output, everything
synthesized, seeded RNG, `commit()` mix-bus, per-section RMS checks, the
`add_at`/`glide_curve`/`reverb` helpers). The **big-room master** and the
**song doctrine + VERIFY blocks** live in `../trance/CLAUDE.md`. Read those
first; this file covers only what is specific to the goa work.

## Tracks

- **phototaxis** — `phototaxis_v2.py` (~5:00) → `phototaxis_v2.wav` — the
  directory-opening goa track: an FM "orchestra" + interlocking swarm in
  F# natural minor, 147 BPM, seed 1995. v1 (`phototaxis.py`, kept for
  reference) was the withheld-anthem "Mahadeva" form; v2 is the song-form
  rebuild after the listen verdict. Full design + every amendment in
  `phototaxis_notes.md`.

## The goa freshness contract (why this dir sounds like nothing else here)

Declared per-track in the notes doc; the load-bearing rules:

- **FM/PM is the whole orchestra** — `sin(φc + I(t)·sin(ratio·φc))`, the
  index and ratio the expressive axis (moving inside every note). **Zero
  saw-stacks, zero `iirpeak`** — the entire 303 family is claimed by
  silver_wire / morgenland / flightpath / maschinenherz. Not the navigator's
  ratio-3 decay-index lead dialect either.
- **The swarm is the thesis**: 3 pitched FM voices + a murk shadow run
  SIMULTANEOUS interlocking 16th cells (≤ 2 onsets per 16th step, register
  medians ≥ 7 semitones apart, cells mutate every 8 bars). No other repo
  track has multi-voice counterpoint — every other track is one singer + answers.
- **Moving bassline** (≥ 2 pitches/bar), never static-root K-b-b-b; kick-gap
  contract kept (bass silent on every kick 16th). Loop/chorus waves use a
  **root-relative** bass cell so it follows the harmony, not a static figure.
- **Kit**: goa kick 95→48 Hz in ~35 ms (not the trance 150→45 dive), sparse
  hats (the swarm owns the 16th grid). FX vocabulary = **chatter** (machine-elf
  random-ratio FM blips) + **bubble-rise** (accelerating gurgle arp into a
  boundary); zaps / reverse cymbals / tom fills are claimed elsewhere.
- **The anthem hangs on the FIFTH** (C#), resolves C#→F# only in the final
  statement, with the track's single E# in the one V chord under it (NOT the
  leading-tone hang — that seam is used twice already).

## The FM orchestra (the voice family)

- **gurgle** — the singer: ratio 2, index wobbles 6–9 Hz on held notes, sung
  vibrato, warm LP; held notes ring (0.22 s release).
- **fizz** — the runner: ratio 1 + modulator feedback (DX7 near-saw), short gate.
- **glint** — the bell: non-integer ratio 3.53 (inharmonic), index snaps shut
  in ~80 ms. **A listen-confirmed keeper — do not touch.**
- **murk** — the shadow: ratio 0.5 (modulator below carrier), dark, low gain.
- **pad_bed** (v2) — the warm floor: ratio-1 detuned root+5th+octave, slow
  attack, dark LP, slow-noise evolve, rooted an octave up from the bass.

## Lessons from phototaxis v1 → v2 (the practice this dir now has)

1. **A percussive-only voice family reads "timid / pling pling, no depth."**
   v1 had a sustained bed only in the anthem waves, so the whole groove had
   nothing under the plinks. Fix: a `pad_bed` under EVERY groove wave, a
   fattened bass, boom-sub in the verses too. The plinks (glints) and the
   melodies were keepers — depth is the *floor*, added underneath, not a
   melodic rewrite. (The standing repo rule: a deep/dark/low bed that
   evolves, not a lone flute.)
2. **The withheld "Mahadeva" reveal read as "two separate songs".** A long
   beatless breakdown + an anthem the listener has never heard = no shared
   material across the gap. Fix here was **song form** (the `../trance/idea.md`
   doctrine): thesis early (quiet solo hook ~0:20), choruses restate it
   identically, the BRIDGE keeps a half-time pulse and a half-lit anthem
   across it (max beatless gap check < 3.5 s — the v1 hole was ~33 s), the
   payoff is the fullest restatement, a solo bookend closes. The withheld
   form is not banned, but it needs foreshadow material carried across the
   break or it splits the track in two.
3. **The goa low end overdrives the big-room tanh → "growl".** pad_bed + a
   bass sub-octave pushed sub-120 share to ~0.8 and the loud-section crest
   factor to ~2.5 — the saturator distorted where layers stacked. This is the
   second failure mode of a hot low end (full recipe + the master HP / crest
   guardrail in `../trance/CLAUDE.md`). PRINT per-section crest, not just RMS.

## Conventions

Standalone script, duplicated helpers (copy the function, don't import),
seeded RNG, printed VERIFY blocks (`../VERIFY.md`), WAV + FLAC to
`/workspace/music/`, never commit audio. Revisions get a new file/WAV name
(`_vN`) — never overwrite a WAV the user has listened to. The **`--preview`
knob** (short excerpts through the same placement path, checks on full renders
only) is a keeper pattern — judge material before a full render.
