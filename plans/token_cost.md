# Token cost estimate — forge implementation (Phases 0-10) + Plan 3 (Phases 0-5)

Reference numbers for planning future full-plan implementation sessions.
Measured from the actual forge build: 11 phases, 9,441 lines, 390 tests,
completed in 2 sessions using Claude Sonnet 4.6 at high effort.

Plan 3 (Phases 0–5) added ~3,100 lines and 165 tests in one session.

## Phase-by-phase breakdown

| Phase | Lines | Output tokens | Size | Description |
|-------|------:|-------------:|------|-------------|
| 0 | 505 | ~5k | light | Inventory, INVENTORY.md, collect_stats tool |
| 1 | 1,103 | ~10k | heavy | Core: buffer, grid, RNG, mixbus, control stub |
| 2 | 1,192 | ~11k | heavy | DSP toolbox, reverb, mastering, loopfold |
| 3 | 1,941 | ~18k | heavy | 27 instruments + registry *(heaviest single phase)* |
| 4 | 786 | ~7k | medium | Patterns: StepPattern, Schedule, render_groove/loop |
| 5 | 865 | ~8k | medium | Arrange: Section, Curve, transitions, Track |
| 6 | 438 | ~4k | light | Analysis: loudness reports, loop-seam checks |
| 7 | 755 | ~7k | medium | Playback service (sounddevice) + Qt window skeleton |
| 8 | 702 | ~7k | medium | UI panels: instrument sliders, mixer, pattern editor |
| 9 | 626 | ~6k | medium | Spec: schema dataclasses, validation, JSON serialize |
| 10 | 528 | ~5k | light | Worked example, project browser, save/load wiring |
| **Total** | **9,441** | **~88k** | | |

*Output token estimate: lines × 32.5 chars/line ÷ 3.5 chars/token.*

## Session breakdown

**Session 1 — Planning + Phases 0-2**
- Output tokens (code): ~26k
- Also included: planning doc questions, 2 prior design docs read
- Outcome: hit 200k context limit → auto-summarised, summary handoff

**Session 2 — Phases 3-10**
- Output tokens (code): ~62k
- Started from summary context (~8k tokens)
- Context compressed once mid-session (after Phase 6)
- Outcome: completed all 8 remaining phases in one session

**Total across both sessions**
- Code output: ~88k tokens
- Input consumed (estimate 4× output): ~350k tokens
- Grand total context budget: ~440k tokens across 2 sessions

## Phase size categories

| Size | Lines | Output tokens | Context consumed | Wall time |
|------|------:|-------------:|----------------:|----------:|
| Light | 400–600 | ~4–8k | ~30–40k | 5–10 min |
| Medium | 700–900 | ~7–12k | ~50–80k | 10–20 min |
| Heavy | 1,100–2,000 | ~10–25k | ~100–150k | 20–40 min |

## Planning a 5-hour window

A 5-hour session at high effort on Sonnet 4.6 consumes roughly 400–600k
total tokens (input + output combined).  Practical capacity:

- **8-12 medium phases**, or
- **4-6 heavy phases**, or
- **mixed**: 2 heavy + 6 medium + 2 light ≈ the whole forge project

**Rules of thumb:**

1. Always reserve one slot for a Phase 0 inventory/skeleton — it pays back
   in every subsequent phase through clear naming and structure.
2. Phase 3 (27 instruments) was the single most expensive at ~18k output
   tokens. Splitting by instrument family (percussion / strings / bass /
   voice / fx) would give five medium phases instead of one heavy one.
3. Test code costs roughly the same as implementation code. The forge split
   was 60% impl / 40% tests (5,505 / 3,512 lines). Budget for it.
4. UI phases (Qt widgets) are medium-sized but require a test strategy
   (offscreen platform); add ~20% extra budget for setup friction.
5. A summary handoff between sessions costs ~1,000–2,000 input tokens to
   establish context. The summary itself takes ~8k tokens. Net cost is low;
   plan a break between heavy and light halves of a large project.

## Codebase at completion (forge Plan 2)

| Metric | Value |
|--------|-------|
| Python source files | 68 |
| Total lines | 9,155 |
| Implementation lines | 5,505 (60%) |
| Test lines | 3,512 (40%) — 390 tests |
| Total characters | ~307k |
| Instrument families | 6 |
| Instruments registered | 27 |
| Control facade methods live | 6 / 6 |

## Plan 3 tracker GUI — Phase 0-5 actual costs

Completed in one session (Claude Sonnet 4.6, high effort).

| Phase | Lines | Output tokens | Size | Description |
|-------|------:|-------------:|------|-------------|
| 0 | ~310 | ~3k | light | Tracker spike (examples/tracker_spike.py); latency: 853ms miss / 0ms hit |
| 1 | ~600 | ~6k | medium | `forge/document/`: channels, transaction, history, model (74 tests) |
| 2 | ~420 | ~4k | medium | `playback/cache.py` + `playback/scheduler.py` + control.render_channel (25 tests) |
| 3 | ~330 | ~3k | medium | `playback/mixer.py` + service.with_mixer() (24 tests) |
| 4 | ~450 | ~4k | medium | `WorkshopPanel` in instrument_panel.py (9 tests) |
| 5 | ~940 | ~9k | heavy | `TrackerEditor` + `TrackerRow` in pattern_editor.py (33 tests) |
| **Total** | **~3,050** | **~29k** | | 165 new tests; 555 total |

**Actual vs plan estimates:**
- Plan estimated ~3,750 lines for Phases 0–4; actual ~2,110 (more concise).
- Phase 5 (heavy) at ~940 lines matched the plan estimate well.
- Total output ~29k vs plan's ~36k estimate — implementations were tighter.
- Wall time: approximately 45–60 minutes for all 6 phases.

**Latency spike measurement (Phase 0, kick drum, Sonnet 4.6 environment):**
- Cache miss (first render): ~853 ms
- Cache hit (same params): ~0 ms
- Sub-second swap confirmed — Phase 0 spike accepted, no fallback needed.
