# Implementation Plan 3 — Interactive Tracker GUI

> **Working implementation plan** derived from `music_plan3_tracker_gui.md`
> (the design brief). This document is the *how* and *in-what-order*; read the
> design brief for the *why*. It targets an AI (or human) implementer who will
> pick up **one or more phases at a time** and iterate.
>
> **Cost/time/lines estimates** per phase are included (see each phase's
> *Estimate* block and the consolidated table at the end), derived from
> `token_cost.md`, so a planner can decide how much fits in one session.

## Starting point: the forge already exists

Plan 3 does **not** start from the legacy scripts. The forge framework
(Plan 2, `implementation_plan2_modular_framework.md`) is **already built and
green** (~9.4k lines, 390 tests). It gives us, as foundation:

- **Engine** (`forge/core`, `forge/instruments` (27 instruments + registry),
  `forge/patterns`, `forge/arrange`, `forge/analysis`) — UI-free, deterministic,
  numpy+scipy+`wave` only.
- **Facade** (`forge/control.py`) — `list_instruments`, `render_instrument`,
  `render_pattern`, `render_track`, `load_project`, `save_project`.
- **Spec** (`forge/spec/`) — `Track/Pattern/Section/ProjectSpec` dataclasses,
  JSON round-trip, validation.
- **Playback** (`forge/playback/`) — `PlaybackClock` + `PlaybackService`, a
  **single-buffer** sounddevice stream that degrades silently when headless.
- **Basic GUI** (`forge/ui/`) — `MainWindow`, `TransportWidget`,
  `InstrumentPanel` (auto-sliders from `ParamSchema`), `MixerWidget`,
  `PatternEditor` (a **16-step on/off toggle grid**), `InstrumentBrowser`/
  `ProjectTree`.

Plan 3 turns this *basic control panel* into a **tracker**. The work is a
well-bounded delta on top of forge, summarised in "What this plan adds" below.

## What this plan adds (the delta)

| Capability | Forge today | Plan 3 delivers |
|---|---|---|
| **Editing model** | serialization dataclasses only | a mutable **document model** with a transactional edit API, dirty-subtree tracking, and **undo/redo** |
| **Caching** | per-note `RenderCache` (in-process, MD5) | a **persistent, content-addressed cache** + a **background render scheduler** (workers; UI never blocks) |
| **Playback** | plays **one** buffer | a **dumb callback mixer** over many cached channel buffers: per-channel gain/**mute/solo**, seamless section **loop**, **click-free hot-swap** on re-render, sample-accurate cursor |
| **Pattern editing** | 16 on/off toggles | full tracker grid: **keyboard note entry**, **accent** + **probability/ghost** columns with **reroll**, per-step param overrides, **copy/paste blocks** |
| **Arrangement** | none | **order/section list**, per-channel schedules, section-loop-while-editing, mix weights + master chain |
| **Continuous material** | none in UI | **texture channels** (no steps; an **envelope lane**) and **automation lanes** bound to engine control curves |
| **Lifecycle** | save/load current spec | **versioned** tracker spec (textures, automation, order list, per-step data), **WAV export** w/ seamless-loop fold, **import a legacy track** as a project |
| **Polish** | — | tracker keyboard shortcuts, **A/B param compare**, render-queue UI, **crash-safe autosave** |

## Decisions locked for this plan

These were chosen up front and shape every phase. They extend the Plan 2
decisions (PySide6/Qt, live callback mixer over cached buffers, deterministic
seeded re-render, listening-approved regression) — those still hold.

| Decision | Choice | Notes |
|---|---|---|
| **Document model home** | new `forge/document/` package (pure data + transactions, **no Qt, no DSP**) | The UI edits the document; renders still go through `forge.control`. Keeps the engine↔UI boundary intact and the model unit-testable headless. |
| **Cache/scheduler/mixer home** | new modules under `forge/playback/` (`cache.py`, `scheduler.py`, `mixer.py`) | PortAudio stays quarantined here, as in Plan 2. |
| **Background rendering** | **process pool** (`concurrent.futures.ProcessPoolExecutor`), fall back to a thread pool if pickling pain dominates | Renders are CPU-bound numpy; processes dodge the GIL. The scheduler owns invalidation; the mixer only mixes ready buffers. |
| **Tracker UI strategy** | **extend** existing `forge/ui` widgets, don't replace | `PatternEditor` grows columns/keyboard entry; `MixerWidget` feeds the new mixer; new `arrangement.py`/`automation_lane.py` widgets are added. |
| **Spec evolution** | **additive, versioned** (`schema_version`) with a load-time migrator | Old Plan 2 projects must still load. New concepts (texture channels, automation, order list, per-step dicts) are added fields, not a rewrite. |
| **Regression bar** | **listening-approved + analysis toolkit** (unchanged from Plan 2) | The imported-legacy-track acceptance test (Phase 8) is the proof the tracker can express established material. |

## Hard rules (apply to every phase — inherited from Plan 2, restated)

- **Engine ↔ UI boundary is one-way.** UI imports only `forge.control`, the
  `forge.document` model, and `forge.playback`. No UI module imports `core`,
  `instruments`, or DSP. The document model imports **neither** Qt **nor** DSP.
- **Determinism.** Same spec + seed ⇒ identical audio. "Reroll" only rewrites a
  stored seed. A saved project re-renders bit-for-bit identically.
- **Dumb player.** The mixer/scheduler never synthesize; they cache, mix, and
  hot-swap engine-produced buffers. All synthesis stays offline-batch.
- **DSP deps:** engine = numpy + scipy + stdlib `wave`. GUI/audio deps
  (PySide6, sounddevice) live only in `ui/` and `playback/`.
- **Don't delete legacy scripts or files** without explicit author confirmation.
  The tracker is additive; legacy renders remain the reference.
- **Tests are not optional and cost ~as much as impl** (forge was 60/40
  impl/test). Every phase below budgets for tests. Qt tests run under
  `QT_QPA_PLATFORM=offscreen`; the document model and cache/scheduler are tested
  fully headless.

## Target package layout (additions to forge)

```
forge/
  document/                  # NEW — pure data + transactions (no Qt, no DSP)
    model.py                 # ProjectDoc: live editable tree wrapping spec dataclasses
    transaction.py           # Edit transactions; dirty-subtree marking for cache keys
    history.py               # Undo/redo stack over transactions
    channels.py              # Channel kinds: pattern / texture / automation
  playback/
    cache.py                 # NEW — content-addressed buffer cache (hash of subtree)
    scheduler.py             # NEW — background render workers; invalidation; stale-until-fresh
    mixer.py                 # NEW — dumb callback mixer: gain/mute/solo/loop/hot-swap
    service.py               # EXTEND — drive the mixer instead of a single buffer
    clock.py                 # (unchanged)
  ui/
    pattern_editor.py        # EXTEND — tracker grid: keys, accent/prob columns, per-step params, copy/paste
    arrangement.py           # NEW — order/section list + per-channel lanes
    automation_lane.py       # NEW — envelope + automation-curve editor widget
    instrument_panel.py      # EXTEND — seed control + audition-on-key + cache-aware audition
    mixer.py                 # EXTEND — bind faders/mute/solo to playback/mixer.py
    transport.py             # EXTEND — loop range, render-queue indicator
    window.py                # EXTEND — dock the new views; wire document + history
    ab_compare.py            # NEW — A/B parameter-state compare
  control.py                 # EXTEND — render_channel/render_section; cache+scheduler entry points
  spec/
    schema.py                # EXTEND — TextureChannelSpec, AutomationSpec, OrderList; schema_version
    serialize.py             # EXTEND — versioned load + migrator from Plan 2 format
```

Legacy generator scripts (`dune/`, `ambient/`, `trance/`) stay untouched and
runnable throughout.

## How to pick up work

Phases are ordered to **front-load risk** (the real-time plumbing) and to keep
each phase independently demonstrable. Phase 0 is the de-risking spike. Phases
1–3 are the headless foundations (document model, cache/scheduler, mixer) and
have **no Qt** in their critical path — they can be built and fully tested
without a display. Phases 4–7 are the UI build-out and depend on the
foundations. Phases 8–9 are lifecycle + polish.

Each phase lists **Depends on**, **Work items**, an **Acceptance** check, and an
**Estimate** (lines incl. tests / output tokens / size / wall time).

---

## Phase 0 — Tracker spike: prove the edit→render→cache→swap loop

**Goal:** re-validate, on top of forge, the single most important loop with
**no real tracker UI** — and measure edit-to-sound latency before building
anything on it. (Forge's Phase 7 spiked single-buffer playback; this spikes the
**multi-channel cache + hot-swap** path the tracker needs.)

**Depends on:** forge (exists).

**Work items:**
- A throwaway `examples/tracker_spike.py`: a minimal panel with one instrument,
  one looping pattern channel, and one slider bound to a param.
- Wire a *stub* content-addressed cache + a *stub* background render (thread is
  fine here) so a param edit → re-renders one channel → swaps the buffer under a
  looping playback, click-free.
- Instrument it: log/measure **edit-to-sound latency** and confirm the loop
  doesn't drop audio on swap.

**Acceptance:** moving the slider changes the looping sound in well under a
second with no click; latency is measured and written into the plan/PR notes.
This de-risks Phases 2–3; if sub-second swap is infeasible, fall back to
render-then-play (no live mixer) is decided **here**, cheaply.

**Estimate:** ~500 lines · ~5k output tokens · **light** · 5–10 min.

---

## Phase 1 — Document model + transactions + undo/redo

**Goal:** the editing backbone. A mutable project tree the UI mutates *only*
through transactions, yielding undo/redo and precise cache-invalidation keys.

**Depends on:** Phase 0 (informs the model's render-key granularity).

**Work items:**
- `document/model.py`: `ProjectDoc` — a live, editable wrapper over the spec
  dataclasses (instruments+params+seed, channels, sections/order, globals).
  Mutations go through a typed edit API (`set_param`, `set_step`, `add_channel`,
  `move_section`, `reroll`, …). No Qt, no DSP.
- `document/channels.py`: the three channel kinds — **pattern**, **texture**,
  **automation** — as data (texture/automation are stubs here, fleshed out in
  Phase 6).
- `document/transaction.py`: edits as transactions that record the **affected
  subtree** → a stable content hash per channel/section (the cache key in
  Phase 2). Dirty-tracking falls out of this.
- `document/history.py`: undo/redo stack over transactions; coalescing for
  slider drags.
- Emit change notifications (a tiny observer/callback, **not** a Qt signal) so
  the UI and scheduler can subscribe without coupling the model to Qt.

**Acceptance:** headless unit tests: a sequence of edits → undo/redo restores
exact prior state; identical edits produce identical subtree hashes; reroll
changes only the targeted channel's hash. No Qt import in the package.

**Estimate:** ~950 lines · ~9k output tokens · **medium (heavy-ish)** · 15–20 min.

---

## Phase 2 — Persistent content-addressed cache + background scheduler

**Goal:** make audition feel sub-second by never re-rendering what hasn't
changed, and never blocking the UI thread.

**Depends on:** Phase 1 (subtree hashes are the keys).

**Work items:**
- `playback/cache.py`: a **content-addressed** buffer cache keyed by the Phase 1
  subtree hash (instrument+params+pitch+seed, or channel+pattern). In-memory LRU
  layered over an on-disk store (numpy `.npy`) so it **persists across runs**.
  Promote forge's per-note `RenderCache` idea to project granularity.
- `playback/scheduler.py`: a render-job scheduler over a
  `ProcessPoolExecutor`. Jobs are `(cache_key, render_callable)`; results land in
  the cache. **Invalidation** = a changed subtree hash; supersede in-flight jobs
  for the same channel. Expose "is X fresh? else give me the stale buffer."
- `control.py`: add `render_channel(channel, seed)` /
  `render_section(section, seed)` entry points the scheduler calls (pure,
  picklable; route through existing `render_pattern`/`render_track`).
- Coalesce rapid edits (slider drags) into the latest job only.

**Acceptance:** headless tests: identical project subtree ⇒ cache hit (render
fn called once); an edit invalidates exactly the affected key; the scheduler
returns a stale buffer immediately and the fresh one after the worker completes;
disk cache survives a process restart.

**Estimate:** ~800 lines · ~8k output tokens · **medium** · 15–20 min.

---

## Phase 3 — Callback mixer + multi-channel playback *(highest risk)*

**Goal:** replace the single-buffer player with a **dumb callback mixer** over
many cached channel buffers — the real-time heart of the tracker.

**Depends on:** Phase 2 (it mixes cached buffers; scheduler feeds fresh ones).

**Work items:**
- `playback/mixer.py`: a callback mixer holding N channel buffers with
  per-channel **gain**, **mute/solo**, seamless **loop range**, sample-accurate
  position, and **click-free hot-swap** (equal-power crossfade or zero-cross
  swap) when the scheduler lands a fresh buffer. **No allocation in the
  callback; no synthesis.**
- `playback/service.py`: drive the mixer instead of `self._buf`. Keep the
  graceful headless degradation. Transport gains **loop range** and the
  position callback already present.
- Define the mixer↔scheduler handoff: play the **stale** buffer until **fresh**
  swaps in; swaps are lock-free / double-buffered to keep the audio thread real-time.

**Acceptance:** headless offline test of the mix math (sum of channels with
gain/mute/solo equals a reference numpy mix; loop wrap is sample-exact; a
hot-swap mid-buffer introduces no discontinuity above a seam tolerance). On a
machine with audio, the Phase 0 spike now runs through the real mixer.

**Estimate:** ~850 lines · ~8k output tokens · **medium (risk-padded)** · 20–30 min.

---

## Phase 4 — Instrument workshop

**Goal:** the first genuinely useful tracker view — browse/audition instruments
and tweak synthesis params with immediate, cache-backed playback. (Replaces the
ad-hoc audition scripts.)

**Depends on:** Phases 2 + 3. Existing `ui/instrument_panel.py` is the seed.

**Work items:**
- Extend `ui/instrument_panel.py`: instrument list from the registry + sliders
  auto-built from `ParamSchema` (already present) + **audition on a key/button**
  routed through cache+scheduler (so repeats are instant) + **per-instrument
  seed control** (reroll = rewrite seed via a Phase 1 transaction).
- Bind the panel to the `ProjectDoc` so every tweak is a transaction (undoable)
  and produces a cache key.
- Show a tiny "rendering…/cached" indicator fed by the scheduler.

**Acceptance:** from a cold GUI, pick an instrument, drag a param and hear it
in well under a second; re-auditioning an already-heard patch is instant
(cache hit); reroll changes the sound deterministically; undo restores the prior
param. Qt test (offscreen) drives the panel against a fake scheduler.

**Estimate:** ~650 lines · ~6k output tokens · **medium (UI +20%)** · 15–20 min.

---

## Phase 5 — Tracker pattern editor

**Goal:** turn the 16-toggle grid into a real tracker pattern editor.

**Depends on:** Phases 1 (per-step edits), 2–3 (incremental re-render of the
touched channel only). Extends `ui/pattern_editor.py`.

**Work items:**
- **Keyboard-first note entry** (tracker tradition): piano-row key mapping to
  pitches per channel; arrow/Tab navigation; insert/delete/clear.
- **Accent** and **probability/ghost** columns per step, with a per-step or
  per-channel **reroll seed** button (reroll = Phase 1 transaction; determinism
  preserved). These map onto the existing `Step` fields (`accent`, `ghost`,
  `probability`) and the dict-step PatternSpec form.
- **Per-step param overrides** (a popover/expander writing the step's `params`).
- **Copy/paste of pattern blocks** and basic pattern **variations**.
- Incremental re-render: editing a channel re-renders **only that channel**
  (via the Phase 2 key) and hot-swaps it under looped playback.

**Acceptance:** enter a beat by keyboard with accents and a ghosted,
probabilistic step; loop it; edits update the sound per-channel without
re-rendering the others; copy/paste a block; reroll changes only the rolled
steps; everything is undoable. Offscreen Qt test covers entry, columns,
copy/paste, and the emitted PatternSpec.

**Estimate:** ~1,300 lines · ~12k output tokens · **heavy (UI +20%)** · 30–40 min.

---

## Phase 6 — Texture channels & automation lanes

**Goal:** represent the generative concepts trackers lack — continuous textures
and control curves — as first-class editable lanes.

**Depends on:** Phases 1 (channel kinds), 3 (mixing continuous layers under
patterns). Adds `ui/automation_lane.py`; fleshes out `document/channels.py`.

**Work items:**
- **Texture channels**: no step grid — an **envelope lane** (gust/energy/gain
  over bars) driving a full-duration instrument (`wind`, `drone`, `swell`).
  Pre-rendered once per param/envelope change and looped under the patterns.
- **Automation lanes**: bind a lane to an engine **control curve**
  (`arrange/curves.py`: energy/duck/sidechain/master gain) — draw breakpoints,
  edit values, scope to a section.
- `ui/automation_lane.py`: a reusable breakpoint-curve widget used for both
  texture envelopes and automation; writes back through Phase 1 transactions.
- `control.py`/scheduler: render texture channels at envelope granularity and
  cache them like pattern channels.

**Acceptance:** add a wind texture with a hand-drawn gust envelope and hear it
loop under a beat; draw a master-gain/sidechain automation curve and hear it
take effect; both serialize and re-render deterministically; edits are
cached/undoable. Offscreen Qt test of the breakpoint widget.

**Estimate:** ~900 lines · ~9k output tokens · **medium-heavy** · 20–30 min.

---

## Phase 7 — Arrangement view

**Goal:** arrange patterns and textures into sections/tracks and audition a
section on loop while editing it.

**Depends on:** Phases 5 + 6 (channels to arrange), 3 (section-loop playback).
Adds `ui/arrangement.py`; extends `ui/mixer.py`, `ui/transport.py`.

**Work items:**
- `ui/arrangement.py`: an **order/section list** (sections as bar ranges, à la
  `arrange/section.py`) with per-channel schedules per section; add/remove/
  reorder/duplicate sections (all transactions).
- **Section-loop while editing**: transport gains a loop-range bound to the
  selected section; mixer mute/solo apply live.
- Extend `ui/mixer.py`: per-channel **mix weights** + **mute/solo** driving
  `playback/mixer.py`; a simple **master chain** control surfacing
  `core/mastering.py` settings.
- Render-queue indicator in `ui/transport.py` (scheduler depth).

**Acceptance:** build a 2-section arrangement, loop one section while tweaking a
channel, set weights/mute/solo live, and hear the whole track play through with
correct section boundaries; reorder sections and undo. Offscreen Qt test drives
the order list and mixer bindings.

**Estimate:** ~900 lines · ~9k output tokens · **medium-heavy (UI +20%)** · 20–30 min.

---

## Phase 8 — Project lifecycle: versioned spec, export, legacy import

**Goal:** projects are saveable, loadable, deterministically re-renderable, and
the tracker can express **existing** material.

**Depends on:** Phases 5–7 (the full document), and forge `spec/` + `Track`.

**Work items:**
- Extend `spec/schema.py`: add `TextureChannelSpec`, `AutomationSpec`, an
  **order list**, and per-step dict data; add a top-level **`schema_version`**.
- Extend `spec/serialize.py`: **versioned** load with a **migrator** that reads
  Plan 2 projects unchanged (additive fields default sensibly).
- Wire GUI **save/load** to the live `ProjectDoc` (round-trip = identical
  re-render; assert in a test).
- **WAV export** wired in the UI, including **seamless-loop folding**
  (`core/loopfold.py`) for loop projects, plus export of the deterministic
  project JSON.
- **Import a legacy track** (one existing `dune/ambient/trance` track) as a
  tracker project and reproduce it through the GUI — the acceptance test that
  the tracker can express established material.

**Acceptance:** save → reload → re-render is bit-identical; a Plan 2 project
loads via the migrator; one legacy track imports, plays, and exports to WAV,
listening-approved against its reference; export of a loop project is seam-clean
per `analysis/loops.py`.

**Estimate:** ~800 lines · ~8k output tokens · **medium** · 15–20 min.

---

## Phase 9 — Workflow polish

**Goal:** make it pleasant and tracker-fast.

**Depends on:** Phases 4–8.

**Work items:**
- Tracker **keyboard shortcuts** throughout (transport, navigation, step
  toggles, octave shift, copy/paste, undo/redo).
- `ui/ab_compare.py`: **A/B compare** of two parameter states (snapshot via a
  Phase 1 transaction; toggle playback between them).
- **Render-queue UI**: visible scheduler depth / per-channel render status.
- **Crash-safe autosave** of the open `ProjectDoc` (atomic write of the spec on
  a timer / after N transactions; recover on launch).

**Acceptance:** keyboard-only editing of a pattern is possible; A/B toggles two
patches without a render stall; killing the app mid-edit recovers the project on
relaunch. Offscreen Qt test for autosave-recover and A/B snapshotting.

**Estimate:** ~700 lines · ~7k output tokens · **medium** · 15–20 min.

---

## Dependency graph (quick reference)

```
forge (exists)
  └─ 0 spike ─┐
              ▼
   1 document ─> 2 cache/scheduler ─> 3 mixer ─┐
                                                ├─> 4 instrument workshop
   1 ───────────────────────────────────────────> 5 pattern editor
   1,3 ─────────────────────────────────────────> 6 textures/automation
   5,6,3 ───────────────────────────────────────> 7 arrangement
   5,6,7 ───────────────────────────────────────> 8 lifecycle/import
   4..8 ────────────────────────────────────────> 9 polish
```

- **Headless foundations (1–3)** need no display and carry the real-time risk —
  build and test them first.
- **UI build-out (4–7)** can start its panels against the Phase 1 model + a fake
  scheduler as soon as 1–3 land.

---

## Cost / time / lines summary (per `token_cost.md`)

Output-token estimate uses the doc's formula (`lines × 32.5 chars/line ÷ 3.5
chars/token ≈ lines × 9.3`). Lines include tests (forge ran ~60% impl / 40%
test; budgeted in). Sizes use the doc's Light/Medium/Heavy bands. Wall times are
the doc's bands and were measured on **Sonnet 4.6** — see the note below.

| Phase | Lines | Output tokens | Size | Wall time |
|-------|------:|-------------:|------|-----------|
| 0 — Spike | 500 | ~5k | light | 5–10 min |
| 1 — Document model + undo/redo | 950 | ~9k | medium | 15–20 min |
| 2 — Cache + scheduler | 800 | ~8k | medium | 15–20 min |
| 3 — Mixer + multi-channel playback | 850 | ~8k | medium* | 20–30 min |
| 4 — Instrument workshop | 650 | ~6k | medium | 15–20 min |
| 5 — Tracker pattern editor | 1,300 | ~12k | heavy | 30–40 min |
| 6 — Textures & automation lanes | 900 | ~9k | med-heavy | 20–30 min |
| 7 — Arrangement view | 900 | ~9k | med-heavy | 20–30 min |
| 8 — Lifecycle / legacy import | 800 | ~8k | medium | 15–20 min |
| 9 — Workflow polish | 700 | ~7k | medium | 15–20 min |
| **Total** | **8,350** | **~78k** | | **~3.5–4.5 h** |

\* Phase 3 is sized medium but **risk-padded** — it is the real-time piece; the
Phase 0 spike exists to de-risk it.

This is **about one forge-sized project** (~9.4k lines / ~88k tokens), which
`token_cost.md` records took **2 sessions**. Plan accordingly.

### Recommended session packing

**Session 1 — Foundations + first useful view (Phases 0–4).**
- Lines ≈ 3,750 · output ≈ ~36k tokens.
- Front-loads *all* the non-UI risk (document model, cache, scheduler, mixer)
  and ends on the **instrument workshop**, which is independently useful and a
  clean demo/stopping point.
- Well under the ~60k-output ceiling a forge session absorbed, leaving headroom
  for planning, the Phase-0 latency spike, and context growth.

**Session 2 — Tracker UI + lifecycle + polish (Phases 5–9).**
- Lines ≈ 4,600 · output ≈ ~45k tokens.
- The UI-heavy half (pattern editor is the single heaviest phase), finishing on
  arrangement, project import, and polish.
- Mirrors forge's own split (engine-ish first session, UI/integration second).
- A `~8k`-token summary handoff between sessions costs little (per the doc).

**Conservative fallback — 3 sessions** if Qt friction or the real-time mixer
overruns: **S1** = 0–3 (foundations, ~2,600 lines), **S2** = 4–6 (~2,850 lines),
**S3** = 7–9 (~2,400 lines). Each session is then comfortably inside one
context window with room for debugging the real-time/audio parts.

### Caveat on the estimates

`token_cost.md` was measured on **Claude Sonnet 4.6**. Output-token counts here
are model-independent (they count the *code produced*, which is the same lines
regardless of model). What differs on **Opus 4.8** is reasoning overhead and
wall-clock, not the code volume — so the **lines** and **output-token** columns
are the reliable planning anchors; treat **wall time** as indicative. UI phases
carry the doc's **+20%** offscreen-test-setup surcharge (already folded into the
sizes above). Reserve, as the doc advises, one slot (Phase 0) for the spike — it
pays back through a de-risked real-time path in every later phase.

## Risks & mitigations

- **Real-time mixer/hot-swap is the highest-risk piece** (as in Plan 2). Gated
  behind the **Phase 0 spike**: prove sub-second, click-free swap *before*
  building UI on it. If infeasible, fall back to render-then-play-buffer (no live
  mixer) — the engine↔UI boundary makes that swap cheap and touches no engine code.
- **Background-process pickling.** Render callables must be picklable and pure;
  if process pools fight numpy/closures, fall back to a thread pool (renders are
  numpy-heavy but release the GIL in scipy FFT paths). Decide at Phase 2.
- **Spec drift breaking old projects.** Mitigated by `schema_version` + a
  load-time migrator and a round-trip determinism test from Phase 8 onward.
- **Listening-approved regression can hide drift.** Mitigated, as in Plan 2, by
  the `analysis/` toolkit (RMS/seam/fatigue) run on every reproduction and by the
  Phase 8 legacy-import acceptance test.
- **UI scope creep.** Out of scope (per the brief): MIDI hardware, audio
  recording, plugin hosting, full mixing-console — those belong to the Plan 4 DAW.
  The tracker edits *this system's* generative building blocks, nothing more.
```
