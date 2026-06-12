# Plan 3 — Interactive Tracker GUI

> **Standalone briefing document.** This plan is self-contained: it describes
> the existing system in conceptual terms and everything an implementing
> agent needs. It does not depend on any other plan being completed first
> (it can sit on a modular framework if one exists, or carve out its own
> engine layer if not — see Dependencies / Assumptions).

## Background (context for the implementing agent)

The source system procedurally synthesizes a themed album of ambient,
action, and psy-trance tracks plus RTS game-state loops, **entirely in
Python (numpy + scipy)** — no audio samples, no DAW. Instruments (wind
textures, drones, Karplus-Strong plucked strings, darbuka/war-drum kits,
duduk/ney-like melodic voices, 303-style acid lines, kick stacks, chants,
explosion FX) are synthesized from parameterized recipes; rhythmic
material lives on a bar/16th-step grid; tracks are assembled as scheduled,
weighted layers and rendered offline to 44.1 kHz stereo WAV. Rendering is
deterministic (seeded RNG). The album shares one key (D) and mode family
(Phrygian dominant).

The workflow today is **one-shot**: edit a Python script, run it, render a
whole track (seconds to a minute of compute), listen, repeat. There is no
way to audition a single instrument tweak in context, mute/solo layers,
nudge a pattern, or rearrange sections without a code-edit-rerender cycle.

## Goal / Scope

Build a **desktop GUI in the spirit of a classic music tracker**
(FastTracker II / Renoise lineage: pattern grid, instrument list,
order/arrangement list, keyboard-first) that turns the one-shot pipeline
into an **iterative, audible, real-time-feeling workflow**:

- Browse and **audition instruments** (the synthesized "samples") and tweak
  their synthesis parameters with immediate playback.
- Edit **patterns**: place notes/strokes on a step grid per instrument
  channel, with accents, ghost probability, and per-step parameters.
- Arrange patterns and continuous texture layers into **sections/tracks**;
  mute/solo channels; adjust mix weights and sends; loop a section while
  editing it.
- **Render** the result to WAV (and export the underlying deterministic
  project description), preserving the existing quality bar — the GUI
  must drive the *same* synthesis code that produces the final renders,
  not a lo-fi preview engine.

Out of scope: MIDI hardware input, recording external audio, plugin
hosting, full mixing-console features (those belong to a separate DAW
effort). The tracker edits *this system's* generative building blocks.

## Key Challenges

- **Offline synthesis vs interactive playback.** The synthesis is
  offline-batch by design (whole-buffer numpy DSP), and some sounds are
  expensive (convolution reverb, per-note filter sweeps). A tracker needs
  sub-second feedback. The answer is **aggressive caching + incremental
  re-rendering**, not rewriting the DSP for real time:
  - Cache rendered note/hit buffers keyed by (instrument, params, pitch) —
    the legacy system already does this inside scripts; promote it to a
    persistent, content-addressed cache.
  - Render at *pattern* granularity: a pattern edit re-renders one
    pattern's affected channel, not the track. Mix cached channel buffers
    on playback.
  - Pre-render continuous textures (wind, drone) once per parameter change
    and loop them under the patterns.
  - Use background worker processes for rendering so the UI never blocks;
    play the stale buffer until the fresh one swaps in.
- **Real-time audio output from Python.** Playback (not synthesis) must be
  a proper callback-driven stream (e.g. via a PortAudio binding) with a
  small mixer: per-channel gain/mute/solo, seamless looping, and
  sample-accurate pattern chaining. Keep the player dumb — it only mixes
  ready-made buffers.
- **Mapping generative concepts onto tracker idioms.** Classic trackers
  assume discrete notes; this system also has continuous control curves
  (energy/duck curves, gust envelopes, slowly wandering gains) and
  probabilistic events (ghost-note probability, randomized fills). The UI
  needs: texture channels (no steps; an envelope lane instead),
  probability as a per-step property with a "reroll seed" button, and an
  automation-lane concept for the control curves. Getting these idioms
  right is the core design problem; prototype them early.
- **Determinism in an interactive world.** Every project must serialize to
  a deterministic description (instruments + params + patterns + seeds +
  arrangement) so a saved project re-renders identically. Interactive
  randomness ("reroll") just rewrites a stored seed.
- **Project file format.** Human-diffable (JSON/TOML-like), versioned,
  and importable/exportable so projects live in git alongside the code.
  Undo/redo should fall out of treating edits as transactions on this
  document model.

## Proposed Architecture / Approach

Strict separation into four components:

1. **Engine (no UI).** The synthesis layer: instrument renderers, pattern
   renderers, texture renderers, arrangement/mix logic, plus the
   persistent render cache and a render-job scheduler (background process
   pool, invalidation by content hash of the relevant project subtree).
   If a modular generation framework already exists, the engine *is* that
   framework plus the cache/scheduler; if not, extract the minimum needed
   instrument/pattern/mix capabilities from the existing scripts into an
   engine package as part of this plan (a smaller, GUI-driven subset of a
   full framework refactor).
2. **Document model.** The project description: instrument definitions
   (recipe id + parameter values + seed), pattern data (steps, accents,
   probabilities, per-step params), channels (pattern channels and texture
   channels), arrangement (order list / section list with per-channel
   schedules and mix weights), and global settings (tempo, key, master
   chain). All edits go through a transactional API → undo/redo, dirty
   tracking for cache invalidation, serialization.
3. **Playback service.** Callback-based audio output with a lightweight
   mixer over cached buffers: transport (play/stop/loop range),
   mute/solo, click-free buffer hot-swap when a re-render lands,
   pattern-accurate position reporting for the UI cursor.
4. **UI.** Desktop GUI — recommended: **Qt (PySide6)** for a native,
   keyboard-first tracker feel (a locally-served web UI is the fallback
   option if Qt iteration proves slow). Views: instrument list +
   parameter editor (sliders/knobs bound to recipe params, audition key),
   pattern editor (step grid, keyboard note entry, accent/probability
   columns), arrangement view (order list of patterns per channel +
   texture/automation lanes), mixer strip (weights, mute/solo), and a
   render/export panel. Keyboard navigation as the primary input, in
   tracker tradition.

The architecture rule that keeps this honest: **the UI never synthesizes
and the engine never knows about widgets.** Everything the UI does is an
edit to the document model; everything audible is a cached engine render.

## Milestones / Phases

- **Phase 0 — Spike the feedback loop.** Prove the core loop end-to-end
  with no real UI: document model stub → engine render of one instrument
  + one pattern → cache → callback playback with live parameter tweaking
  from a minimal panel. Measure edit-to-sound latency; this de-risks the
  whole plan.
- **Phase 1 — Instrument workshop.** Instrument list, parameter editor,
  audition playback, per-instrument seed control, persistent render
  cache. Already independently useful (replaces the ad-hoc
  sample-audition scripts).
- **Phase 2 — Pattern editor.** Step grid with keyboard entry, accents,
  ghost probability + reroll, per-channel mute/solo, looped pattern
  playback with incremental re-render on edit.
- **Phase 3 — Arrangement & textures.** Order/section list, texture
  channels with envelope lanes, automation lanes for control curves,
  section-loop playback, mix weights and master chain.
- **Phase 4 — Project lifecycle.** Save/load (versioned format), undo/redo,
  WAV export (including seamless-loop folding for loop projects),
  import of at least one existing track recreated as a project — the
  acceptance test that the GUI can express the established material.
- **Phase 5 — Workflow polish.** Tracker keyboard shortcuts, copy/paste of
  pattern blocks, pattern variations, A/B comparison of parameter states,
  render-queue UI, crash-safe autosave.

## Dependencies / Assumptions

- Python remains the synthesis platform; new dependencies are acceptable
  for the GUI/audio-IO layers (e.g. PySide6, a PortAudio binding such as
  sounddevice). The target is a desktop environment with working audio
  output.
- A modular generation framework is an **optional** foundation: if
  present, the engine builds on it; if absent, this plan extracts its own
  engine subset from the existing generator scripts (which are available
  as the source of truth for all synthesis recipes). Either way the
  GUI ships.
- Deterministic re-rendering from a saved project is a hard requirement.
- Existing generator scripts are left untouched and working; the GUI is
  additive. File deletions require explicit author confirmation.
- Single-user, local tool; no collaboration, networking, or packaging-for
  -distribution requirements.
- Optional integration point (do not depend on it): the project document
  format could later serve as an interchange format for a JavaScript/game
  runtime or a fuller DAW; keep it clean and versioned but don't design
  for hypothetical consumers beyond that.
