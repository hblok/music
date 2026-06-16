# Implementation Plan 2 — Modular Music Framework + Basic GUI

> **Working implementation plan** derived from `music_plan2_modular_framework.md`
> (the design brief). This document is the *how* and *in-what-order*; read the
> design brief for the *why*. It targets an AI (or human) implementer who will
> pick up **one or more phases at a time** and iterate.

## What this plan builds

A reusable, composable Python synthesis framework (the **forge**) extracted
from the existing one-shot generator scripts, **plus a basic desktop GUI** on
top of it for creating, composing, and controlling the musical output.

The forge keeps the existing constraints: **numpy + scipy only** for DSP,
stdlib `wave` for WAV output (no `soundfile`/`pydub`), everything synthesized
from first principles, deterministic seeded rendering, the `commit()` mix-bus
discipline, and the per-section RMS / anti-fatigue lessons baked in as
utilities. The GUI adds new dependencies (PySide6, a PortAudio binding) but the
**engine never imports a GUI or audio-IO module** — that boundary is the single
most important architectural rule here.

## Decisions locked for this plan

These were chosen up front and shape every phase. They are *deliberate
deviations* from the design briefs where noted.

| Decision | Choice | Notes |
|---|---|---|
| **GUI toolkit** | **PySide6 / Qt** | Matches Plan 3's recommendation; scales toward a future tracker. Engine stays GUI-agnostic behind a control facade so the binding is swappable. |
| **Playback model** | **Live callback-driven mixer** | A real audio stream (via `sounddevice`/PortAudio) with a small mixer over **cached buffers**: per-channel gain/mute/solo, seamless section looping, click-free hot-swap when a re-render lands. The mixer is *dumb* — it only mixes ready-made buffers; **all synthesis stays offline-batch**. |
| **GUI scope** | **Basic control panel** | Instrument list + parameter sliders + audition, a simple per-channel step grid, mix weights + mute/solo, render-to-WAV, save/load JSON. Tracker-grade editing (accents/ghost columns, keyboard note entry, automation lanes, order list) is **explicitly deferred to Plan 3**. |
| **Regression bar** | **Listening-approved** | Reproductions of legacy tracks are validated by **ear + RMS/seam reports**, not bit-exact golden files. Faster iteration; the accepted risk is silent DSP/RNG drift, mitigated by the analysis toolkit (Phase 6) and by keeping legacy scripts as the reference renders. |

Consequence of "listening-approved": we adopt **hierarchical seeding from the
start** (no two-step bit-exact → reseed migration). Each track is reproduced
once, in the new RNG architecture, and signed off by ear.

## Hard rules (apply to every phase)

- **Engine ↔ UI boundary:** the UI only edits the document model and reads
  rendered buffers; the engine has zero knowledge of widgets, Qt, or the audio
  device. Anything that violates this is a bug regardless of whether it works.
- **Determinism:** same spec + seed ⇒ identical audio. A saved project must
  re-render identically. Interactive "reroll" only rewrites a stored seed.
- **DSP deps:** engine uses numpy + scipy + stdlib `wave` only. GUI/audio deps
  (PySide6, sounddevice) live *only* in the `ui/` and `playback/` packages.
- **Don't delete legacy scripts.** They are the reference renders and the
  source of truth for every recipe. Deleting any file requires explicit author
  confirmation. The framework is additive.
- **Mix-bus discipline:** layers render *into* a mix bus and free themselves;
  never hold all float64 layers of a long track alive at once.

## Target package layout

```
music/
  forge/                     # the framework (numpy+scipy+wave only)
    core/
      buffer.py              # AudioBuffer (stereo float32/64, sample rate)
      grid.py                # tempo / bar-beat-16th <-> seconds (bar_t)
      rng.py                 # hierarchical seeded RNG contexts
      dsp.py                 # filters, fades, slow_noise, glide_curve, oscs
      reverb.py              # make_reverb_ir + reverb (fftconvolve)
      mixbus.py              # commit-and-free layering, weighted sum
      mastering.py           # shelves, soft limiter, peak normalize, fade
      loopfold.py            # on-grid seamless loop folding
    instruments/
      base.py                # Instrument protocol + per-note render cache
      textures.py            # wind, drone, swell  (full-duration)
      percussion.py          # kick, doum, tek, hat, clap, snare, war_drum, frame_roll
      strings.py             # piano, harp (karplus_strong), cello, pluck, pad_chord
      voices.py              # flute/ney, choir, chant, voice_phrase
      bass.py                # bass_note, psy_bass_note, acid_note
      fx.py                  # zap, riser, crash, intercom, radio_click, explosion
      registry.py            # id -> instrument + param schema (drives the GUI)
    patterns/
      step.py                # 16th-step patterns (accents, ghost probability)
      schedule.py            # bar-indexed schedules, fills/variations
      groove.py              # pattern + instrument + grid -> layer buffer
    arrange/
      section.py             # sections as bar ranges
      curves.py              # piecewise energy/duck/automation curves
      transitions.py         # cuts, crossfades, boundary-aligned risers
      track.py               # Track: orchestrates render into mix bus -> WAV
    spec/
      schema.py              # dataclasses for instruments/patterns/arrangement
      io.py                  # JSON round-trip (load/save project documents)
    analysis/
      loudness.py            # per-section RMS reports, build-headroom checks
      loops.py               # loop-seam + RMS-trend flatness checks
      fatigue.py             # sustained high-frequency / anti-tinnitus lint
    control.py               # GUI-agnostic facade: the API the UI talks to
  playback/                  # PortAudio deps live here, NOT in forge/
    mixer.py                 # callback mixer over cached buffers (gain/mute/solo/loop)
    stream.py                # sounddevice stream lifecycle + transport
    cache.py                 # content-addressed buffer cache (hash of subtree)
  ui/                        # PySide6 deps live here, NOT in forge/
    app.py                   # Qt application entry point
    instrument_panel.py      # list + param sliders + audition
    pattern_panel.py         # simple per-channel step grid
    mixer_panel.py           # weights, mute/solo
    transport.py             # play/stop/loop, render, save/load
  forge/tests/               # pytest
```

The legacy generator scripts (`dune/`, `ambient/`, `trance/`) are untouched and
remain runnable throughout.

## How to pick up work

Phases 1–6 build the engine; 7–9 build playback + GUI; 10 polishes. Within the
engine, **instruments (3), patterns (4), and analysis (6) can proceed in
parallel** once Core (1–2) lands. The GUI track (7–9) can start its Qt shell as
soon as the control facade (`forge/control.py`, stubbed in Phase 1) exists, and
fills in real behavior as engine phases complete. Each phase below lists its
**dependencies**, **work items**, and a concrete **acceptance check**.

---

## Phase 0 — Inventory & reference renders

**Goal:** know exactly what we're extracting, and capture the sound we must not
lose.

**Depends on:** nothing.

**Work items:**
- Render every legacy track and sample set from the existing scripts to WAV;
  store them as `reference/` renders (the listening-approved baseline). Record
  duration, peak, and per-section RMS for each.
- Inventory every helper and recipe across `dune/`, `ambient/`, `trance/`.
  Classify each into a forge layer (core / instrument-family / pattern /
  arrange / analysis). The duplicated helpers — `midi_to_hz`, `fade`,
  `slow_noise`, `make_reverb_ir`, `reverb`, `add_at`, `commit`, `bar_t`,
  `glide_curve` — collapse into one canonical core implementation each.
- For each script, note its RNG usage (seed, draw order) so we understand what
  hierarchical seeding will change.
- Produce `forge/INVENTORY.md`: the recipe → target-module mapping.

**Acceptance:** a checked-in inventory table mapping every `def` in the legacy
scripts to a forge destination, and a `reference/` directory of baseline WAVs +
their RMS/peak stats.

---

## Phase 1 — Core: buffers, grid, RNG, mix bus

**Goal:** the substrate everything renders on.

**Depends on:** Phase 0 inventory.

**Work items:**
- `core/buffer.py`: `AudioBuffer` — stereo numpy array + sample rate; helpers
  for length-in-seconds/samples, peak/RMS, normalize, add-with-gain at a time
  offset (canonical `add_at`).
- `core/grid.py`: tempo + bar/beat/16th ↔ seconds (canonical `bar_t`); the unit
  trackers and patterns schedule against.
- `core/rng.py`: **hierarchical seeded RNG contexts** — a master seed derives
  independent child streams per layer/instrument (via `np.random.SeedSequence`
  `.spawn()`), so components are independently reproducible and reorderable.
  This is the determinism backbone.
- `core/mixbus.py`: `MixBus` — layers render *into* it and are freed
  immediately (canonical `commit`); weighted sums are the balance knobs.
- Stub `forge/control.py` with the facade signatures the GUI will call
  (`list_instruments`, `render_instrument`, `render_pattern`, `render_track`,
  `load_project`, `save_project`) returning `NotImplementedError` — this
  unblocks the GUI shell (Phase 7) early.

**Acceptance:** pytest unit tests for buffer math, grid conversions, RNG
determinism (same seed ⇒ identical draws; spawned children are independent),
and mix-bus weighted-sum + free.

---

## Phase 2 — Core: DSP toolbox, reverb, mastering, loop fold

**Goal:** the shared signal-processing primitives, one canonical copy each.

**Depends on:** Phase 1.

**Work items:**
- `core/dsp.py`: `midi_to_hz`, raised-cosine `fade`, `slow_noise(rate, lo, hi)`
  (sparse normals → smoothed → interp → normalized; supports the `**power` lull
  deepening), `glide_curve`, Butterworth band/low/high-pass wrappers,
  pitch-glide oscillators, the warmth helpers (rolled-off partial sums
  `sin(k·ph)/k**1.3`, sine-body blend, raised-cosine attack) from the trance
  warmth recipe.
- `core/reverb.py`: `make_reverb_ir(seconds, decay, seed)` (dark-tail
  exponential noise, energy-normalized, separate L/R seeds for decorrelation)
  and `reverb(x, ir, wet)` via `scipy.signal.fftconvolve`, tail renormalized.
- `core/mastering.py`: peak normalize to 0.85–0.88, shelves, soft limiter,
  final `fade`, int16 interleave + stdlib `wave` writer.
- `core/loopfold.py`: on-grid seamless loop folding (overlap-add the tail onto
  the head on the bar grid).
- **Validation re-render:** reproduce **one simple legacy track** (e.g. a
  game-state loop or `generate_ambient.py`) using only core helpers + inline
  instrument code, and sign it off by ear against its Phase-0 reference.

**Acceptance:** the chosen track re-renders through core helpers and is
listening-approved against its reference (RMS within a small tolerance; loop
seam clean). DSP units have tests where deterministic (filter shapes, fade
curves, reverb tail energy).

---

## Phase 3 — Instruments

**Goal:** every legacy recipe as a parameterized, documented instrument.

**Depends on:** Phase 2. **Parallelizable** with Phases 4 and 6.

**Work items:**
- `instruments/base.py`: the light **Instrument protocol** — a callable taking
  `(params, rng)` returning either a *one-shot event buffer* (hits/notes, with
  a render **cache keyed on params + pitch**) or a *full-duration texture*
  (taking the time/grid context). Document the contract: what's returned, how
  time and stereo are represented, how params and randomness flow in. Leave DSP
  internals free-form — do **not** force a rigid synth/voice/note model.
- Port recipes into families, each with a documented parameter schema:
  - `textures.py` — **wind** (two-band noise: 120–900 Hz whoosh + 2–7 kHz hiss,
    gusts via `slow_noise`), **drone**, **swell** (detuned dissonant cluster).
  - `percussion.py` — `make_kick`, `make_doum`, `make_tek`, `make_hat`,
    `make_clap`, `make_snare`, `make_war_drum`, `frame_roll`/`make_frame_hit`.
  - `strings.py` — felt **piano** (stretched-inharmonic partials, two detuned
    strings, felt thunk, cached per pitch), **harp** (`karplus_strong`, warm
    pick, `damp≈0.9955`), **cello** (detuned additive saw + bow noise,
    vibrato), `pluck`, `pad_chord`.
  - `voices.py` — **flute/ney** (low harmonics + breath noise, blooming
    vibrato), **choir** (glottal source through vowel formant bandpasses,
    polytonal stacking), **chant**, `voice_phrase`.
  - `bass.py` — `bass_note` (warmth recipe: rolled-off saw + sine sub),
    `psy_bass_note`, `acid_note` (303-style, low-Q resonant blend).
  - `fx.py` — `make_zap`, `riser`, `make_crash`, `intercom`, `radio_click`,
    explosion.
- `instruments/registry.py`: `id → (instrument callable, param schema)`. The
  param schema (name, type, range, default) is what the GUI auto-builds sliders
  from — keep it complete and honest.
- Replace the ad-hoc per-sample audition scripts with a single
  `render_instrument(id, params, seed)` path through the registry.

**Acceptance:** each instrument auditions to a WAV via the registry; key
instruments are listening-approved against the corresponding legacy sample
renders. Per-note cache verified to return identical buffers on repeat calls.

---

## Phase 4 — Patterns & loops

**Goal:** place instrument events on a tempo grid and render loops.

**Depends on:** Phase 2 (grid) + Phase 3 (instruments to place).
**Parallelizable** with Phase 6.

**Work items:**
- `patterns/step.py`: 16th-step patterns — per-step dicts with accents and
  ghost-note probabilities (probability stored as data; "reroll" = rewrite the
  stored seed, preserving determinism).
- `patterns/schedule.py`: bar-indexed schedules; fill/variation hooks; the
  "wander, never build" modulation helpers for game-state loops.
- `patterns/groove.py`: turn `pattern + instrument + grid` into a layer buffer,
  rendering into a mix bus; integrate `core/loopfold.py` for seamless loops.
- Re-express the **game-state loop tracks** through patterns; verify with the
  analysis toolkit (seams + RMS flatness — Phase 6) once available, or RMS by
  hand if running ahead of it.

**Acceptance:** a game-state loop reproduced via patterns is listening-approved,
loops seamlessly (no audible seam), and shows flat RMS trend (no build).

---

## Phase 5 — Arrangement & full track migration

**Goal:** sections, energy curves, transitions, whole-track rendering — and the
remaining story tracks migrated.

**Depends on:** Phases 3 + 4.

**Work items:**
- `arrange/section.py`: sections as bar ranges with per-layer per-section
  schedules.
- `arrange/curves.py`: piecewise energy/duck/automation curves (sidechain
  pumping, aftermath-quieter-than-intro).
- `arrange/transitions.py`: cuts, crossfades, boundary-aligned risers.
- `arrange/track.py`: `Track` — orchestrates rendering of all
  sections/layers into the mix bus, applies mastering, writes WAV.
- Migrate the remaining story tracks (`lost`, the dune narrative tracks, the
  trance tracks). Each reproduced once in the new hierarchical-RNG architecture
  and **listening-approved** against its Phase-0 reference.

**Acceptance:** all legacy tracks reproducible through the framework and signed
off by ear; per-section RMS reports within tolerance of the references.

---

## Phase 6 — Analysis / validation toolkit

**Goal:** encode the loudness/fatigue/loop lessons as utilities, not rules to
remember.

**Depends on:** Phase 1 (buffers). **Parallelizable** with Phases 3–5; feeds
their acceptance checks.

**Work items:**
- `analysis/loudness.py`: per-section RMS reports, build-headroom checks,
  intro-vs-aftermath loudness comparison.
- `analysis/loops.py`: loop-seam discontinuity detection, RMS-trend flatness
  for game loops.
- `analysis/fatigue.py`: sustained high-frequency / anti-tinnitus envelope
  linting.
- A `forge.analysis.report(buffer_or_track)` entry point usable from CLI and
  from the GUI (Phase 9 surfaces it as a panel).

**Acceptance:** running the toolkit on a Phase-0 reference reproduces the
known-good stats; it flags a deliberately-broken render (e.g. a loop with an
injected seam or a building game loop).

---

## Phase 7 — Playback service + Qt shell

**Goal:** real audio out, and an empty-but-running GUI wired to the facade.

**Depends on:** `forge/control.py` facade (stub from Phase 1; real renders as
engine phases land).

**Work items:**
- `playback/cache.py`: content-addressed buffer cache keyed by a hash of the
  relevant project subtree (instrument+params+seed, or pattern+channel). This
  is what makes live audition feel sub-second.
- `playback/mixer.py`: a **dumb callback mixer** over cached buffers —
  per-channel gain, **mute/solo**, seamless section looping, sample-accurate
  position, and **click-free hot-swap** when a fresh re-render replaces a stale
  buffer. No synthesis here.
- `playback/stream.py`: `sounddevice` output stream lifecycle + transport
  (play/stop, loop range, position reporting for the UI cursor). Background
  worker renders so the callback never blocks; play the stale buffer until the
  fresh one swaps in.
- `ui/app.py`: PySide6 application that opens, talks **only** to
  `forge/control.py` and the playback service, and can play a hard-coded test
  buffer end-to-end.

**Acceptance:** the **Phase-0 spike** — edit one instrument param in a minimal
panel → engine re-renders → cache → callback playback swaps in the new buffer,
click-free, in well under a second. This de-risks the whole GUI track; measure
and record edit-to-sound latency.

---

## Phase 8 — Basic control panel

**Goal:** the actual "basic controls over creating, composing, controlling".

**Depends on:** Phases 3, 4, 7. (Mixer/arrange features improve as 5 lands.)

**Work items:**
- `ui/instrument_panel.py`: instrument list (from the registry) + parameter
  **sliders auto-built from the param schema** + an audition key/button +
  per-instrument **seed control** (reroll = rewrite seed).
- `ui/pattern_panel.py`: a **simple per-channel 16th step grid** — toggle steps
  on/off per channel, looped playback with **incremental re-render** on edit
  (only the touched channel re-renders). *(Accents, ghost columns, keyboard
  note entry, order list, automation lanes are out — those are Plan 3.)*
- `ui/mixer_panel.py`: per-channel **mix weight** sliders + **mute/solo**
  (driving the playback mixer live).
- `ui/transport.py`: play/stop/loop, **render-to-WAV**, and save/load (wired in
  Phase 9).

**Acceptance:** from a cold GUI start, a user can pick instruments, tweak their
params and hear it, toggle a few steps per channel, set mix weights / mute /
solo while looping, and render the result to a WAV — no code editing.

---

## Phase 9 — Project lifecycle & declarative spec

**Goal:** projects are data: saveable, loadable, deterministically
re-renderable; the spec round-trips.

**Depends on:** Phase 5 (`Track`) + Phase 8 (GUI to drive it).

**Work items:**
- `spec/schema.py`: dataclasses for instruments-with-params, patterns, channels,
  arrangement, global settings (tempo, key, master chain, seeds). A
  **serialization of the API**, not a second system — arbitrary Python stays
  first-class for anything the spec can't express.
- `spec/io.py`: human-diffable, **versioned** JSON load/save. A saved project
  re-renders **identically** (determinism check on round-trip).
- Wire GUI save/load to the spec; **import at least one existing track** as a
  project document and reproduce it through the GUI — the acceptance test that
  the framework + GUI can express the established material.
- Surface the analysis toolkit (Phase 6) as a read-only **report panel** in the
  GUI (run on instrument / channel / track).

**Acceptance:** save a project → reload → re-render produces identical audio; an
imported legacy track round-trips and is listening-approved; the report panel
shows RMS/seam/fatigue stats in-app.

---

## Phase 10 — Polish & worked example

**Goal:** prove composability and make the thing pleasant.

**Depends on:** Phases 1–9.

**Work items:**
- API docs + a **"build a new track in ~50 lines"** tutorial (imperative use of
  the forge, no GUI).
- A worked example composing a **brand-new short track** purely from framework
  parts — the real proof that the building blocks compose, not just that legacy
  tracks were re-expressed.
- GUI niceties: A/B compare of two parameter states, a render queue indicator,
  crash-safe autosave of the open project.

**Acceptance:** a new short track exists that was authored through the framework
(code and/or GUI) and did not start life as a legacy script; the tutorial runs
top-to-bottom from a clean checkout.

---

## Dependency graph (quick reference)

```
0 ─> 1 ─> 2 ─┬─> 3 ─┐
             ├─> 4 ─┼─> 5 ─┐
             └─> 6 ─┘      │
1 (facade stub) ─> 7 ─> 8 ─┴─> 9 ─> 10
```

- **Engine-only contributors:** take 1→2, then any of 3 / 4 / 6 in parallel,
  converging on 5.
- **GUI contributors:** start 7 against the Phase-1 facade stub as soon as it
  exists; flesh out 8 as instruments/patterns land; finish on 9–10.

## Risks & mitigations

- **Live-mixer real-time plumbing is the highest-risk piece.** It is gated
  behind the Phase 7 spike on purpose — prove the edit→render→cache→swap loop
  before building any real GUI on top. If sub-second swap proves infeasible,
  fall back to render-then-play-buffer (no callback mixer) without touching the
  engine; the boundary makes that swap cheap.
- **Listening-approved regression can hide drift.** Mitigated by keeping legacy
  scripts as living references and by running the Phase-6 analysis toolkit
  (RMS/seam/fatigue) on every reproduction, not just by ear.
- **Over-abstraction fighting the recipes.** The instrument protocol
  standardizes only the *contract* (return type, time/stereo, param+rng flow)
  and leaves DSP free-form. Resist any "universal voice" model.
- **Memory on long tracks.** Enforced by the mix-bus commit-and-free pattern
  and per-note caching from Phase 1 onward, not bolted on later.
