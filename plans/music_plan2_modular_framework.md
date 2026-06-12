# Plan 2 — Modular Music Generation Framework

> **Standalone briefing document.** This plan is self-contained: it describes
> the existing system in conceptual terms and everything an implementing
> agent needs. It does not depend on any other plan being completed first.

## Background (context for the implementing agent)

The source system is a set of **standalone Python scripts (numpy + scipy),
one per track**, that procedurally synthesize a themed album of ambient,
action, and psy-trance music plus game-state loops for an RTS. Everything
is synthesized from first principles — no audio samples. Each script
follows the same internal shape:

1. Constants (sample rate 44.1 kHz, duration, time vector, one seeded RNG).
2. A copied set of helper functions (pitch conversion, fades, smoothed
   random control signals, reverb IR construction + FFT convolution,
   bounds-safe event placement). Helpers are **deliberately duplicated
   between scripts** so each script is standalone.
3. One section per instrument layer (wind, drone, plucked strings via
   Karplus-Strong, darbuka/war-drum kits, duduk/ney-like melodic voices,
   303-style acid, kick stacks, chants, explosions…), each producing a
   normalized stereo pair.
4. A final weighted mix, mastering (peak normalization, sometimes shelves
   and a soft limiter), optional seamless-loop folding, 16-bit WAV output.

The scripts embody a large library of hard-won **synthesis recipes and
arrangement lessons** (documented in the project's docs): anti-tinnitus
envelope rules, loudness/RMS balancing across sections, loop-folding on
the bar grid, "no builds in game-state loops", sidechain pumping, etc.
There are also separate scripts that render individual instrument *samples*
to WAV for auditioning. All music shares one key (D) and mode family
(Phrygian dominant), which is a palette convention, not a code constraint.

The pain point: the system is **one-shot** — each track is a monolithic
script; reuse happens by copy-paste; changing a sound means editing code
and re-rendering a whole track.

## Goal / Scope

Refactor the system into a **reusable, composable Python framework** with
three tiers of building blocks and a clean API:

1. **Sample/instrument generators** — parameterized synthesizers that
   render single hits, notes, or sustained textures (a darbuka stroke at a
   given brightness, an oud pluck at a pitch, ten seconds of gusting wind).
2. **Loop/pattern builders** — step sequencers, bar-grid schedulers,
   groove assemblers that place instrument events on a tempo grid and
   render loops (including on-grid seamless loop folding).
3. **Track assemblers** — section/arrangement machinery: layer schedules,
   energy curves, mix weights, mastering chains, whole-track rendering.

Plus the cross-cutting goals: **determinism is preserved** (same spec +
seed ⇒ same audio), **existing tracks are reproduced** through the new
framework as the proof of correctness, and the API is pleasant to use both
imperatively (Python code) and declaratively (a track described as data).

Out of scope: any GUI, real-time playback, JavaScript. (But see
"Dependencies / Assumptions" for integration points other efforts may use.)

## Key Challenges

- **Refactoring without changing the sound.** The existing tracks are
  approved by ear; a refactor that subtly shifts a filter design or RNG
  consumption order changes the audio. Strategy: golden-file regression —
  before refactoring, render every track and key instrument from the
  legacy scripts as references; after migration, require either
  bit-identical output or explicitly reviewed, listening-approved diffs.
  Bit-identical is *achievable* here (same numpy, same algorithms) and
  should be the default bar for pure mechanical extraction.
- **RNG architecture.** Today one RNG per script feeds everything in
  source order; any reordering changes every downstream random draw. The
  framework needs **hierarchical seeding** (a master seed deriving
  independent child streams per layer/instrument, e.g. via seed
  sequences) so components are independently reproducible and reorderable.
  This *will* break bit-parity with legacy scripts — so migrate each track
  in two steps: (1) extract code with identical RNG order (bit-exact
  check), (2) switch to hierarchical seeds (listening check).
- **Right level of abstraction.** The recipes vary wildly (event-based
  percussion, continuous textures, per-note cached synthesis, whole-track
  control curves). Over-abstracting into a rigid "synth/voice/note" model
  will fight the material. The framework should standardize the *contracts*
  (what a generator returns, how time and stereo are represented, how
  randomness and parameters flow in) and leave DSP internals free-form.
- **Performance and memory.** Long tracks with many float64 layers exhaust
  memory if all layers stay alive; the legacy scripts learned to commit
  each layer into a mix bus immediately. The framework must build this in
  (a mix-bus object layers render *into*), plus per-note render caching
  for repeated pitches/strokes.
- **Loudness conventions.** Peak-normalized layers hide RMS imbalance;
  several legacy lessons exist about section-RMS verification, build
  headroom, aftermath-quieter-than-intro. Encode these as framework-level
  *analysis/validation utilities* (per-section RMS reports, flatness
  checks for loops, anti-tinnitus envelope linting) rather than as rules
  the user must remember.

## Proposed Architecture / Approach

A layered library (working name: the **forge**):

- **Core layer.** Audio buffer type (stereo float, sample rate),
  time/grid model (seconds + bar/beat grid with tempo), hierarchical
  seeded RNG contexts, the DSP toolbox (filters, envelopes,
  smoothed-random control signals, reverb IRs + convolution, pitch-glide
  oscillators, loop folding, fades), and the **mix bus** (commit-and-free
  layering, weighted sums, mastering chain: shelves, limiter,
  normalization).
- **Instrument layer.** A light protocol: an instrument is a callable
  taking (params, rng) and returning either a one-shot event buffer (hits,
  notes — with caching keyed on the params) or a full-duration texture
  (wind, drone — taking the time context). Port each legacy recipe as one
  instrument with documented parameters. Group into families: textures,
  percussion, strings, voices/winds, bass/acid, FX/events.
- **Pattern layer.** Step patterns (per-16th dictionaries with accents and
  ghost-note probabilities), bar-indexed schedules, fill/variation hooks,
  and groove renderers that turn pattern + instrument + grid into a layer.
  Includes the on-grid seamless loop fold and the "wander, never build"
  modulation helpers for game-state loops.
- **Arrangement layer.** Sections as bar ranges, per-layer per-section
  schedules, piecewise energy/duck curves, transitions (cuts, crossfades,
  risers ending on boundaries), and a `Track` object that orchestrates
  rendering into the mix bus and writes output.
- **Declarative spec (thin, on top).** A data representation
  (dict/JSON-able) for instruments-with-params, patterns, and arrangements
  — enough to describe a track as data and round-trip it. Keep it a
  *serialization of the API*, not a second system; arbitrary Python remains
  first-class for anything the spec can't express.
- **Validation toolkit.** Golden-file comparison (exact and perceptual),
  per-section RMS reports, loop-seam checks, RMS-trend flatness for loops,
  anti-tinnitus checks for sustained high-frequency content.

Migration approach: **strangler pattern.** The framework grows by
extracting one capability at a time from the legacy scripts; each legacy
track is re-expressed through the framework and verified against its
golden render; legacy scripts are kept until their replacement is verified
(do not delete them without the author's confirmation).

## Milestones / Phases

- **Phase 0 — Golden references & inventory.** Render and checksum all
  legacy tracks and sample sets. Inventory every helper and recipe across
  the scripts; classify into the four layers above; note RNG usage per
  script.
- **Phase 1 — Core layer.** Buffers, grid, RNG contexts, DSP toolbox, mix
  bus, mastering. Unit tests + a re-render of one simple legacy track
  using core helpers only, bit-identical to its golden file.
- **Phase 2 — Instruments.** Extract all instrument recipes with
  parameter documentation and per-instrument audition rendering (replacing
  the ad-hoc sample scripts). Each instrument validated against legacy
  output where extractable.
- **Phase 3 — Patterns & loops.** Step sequencing, schedules, groove
  assembly, loop folding. Re-express the game-state loop tracks; verify
  seams and RMS flatness with the validation toolkit.
- **Phase 4 — Arrangement & full migration.** Sections, energy curves,
  transitions; migrate the remaining story tracks. All tracks reproducible
  through the framework (bit-exact where mechanical, listening-approved
  where RNG re-architecture changed draws).
- **Phase 5 — Declarative spec & polish.** Data-driven track descriptions
  for at least two tracks end-to-end; API documentation with a "build a
  new track in 50 lines" tutorial; a worked example composing a *new*
  short track purely from framework parts (the real proof of
  composability).

## Dependencies / Assumptions

- Python with numpy + scipy remains the platform; no new heavyweight
  dependencies are required (pure-Python/numpy framework). Test tooling
  (pytest) may be added.
- The legacy scripts and their docs are available as the source of truth
  for recipes and conventions; golden WAVs can be rendered locally.
- Determinism (seed ⇒ identical audio) is a hard requirement of the
  framework, not a nice-to-have.
- Keep legacy scripts in place until migrations are verified; deleting
  files requires explicit author confirmation.
- Optional integration points (do not depend on them): an interactive GUI
  could later drive the pattern/arrangement layers; a JavaScript port
  could later consume the declarative track spec as its input format.
  Designing clean layer boundaries and a serializable spec keeps both
  doors open at near-zero extra cost.
