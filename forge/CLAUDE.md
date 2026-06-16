# CLAUDE.md — forge/

Implementation guide for the **forge** modular music synthesis framework.
See `../CLAUDE.md` for repo-level context.

## Architecture in one paragraph

The UI talks **only through `forge.control`** — no UI module imports `core`,
`instruments`, or any DSP code directly. `control.py` is the facade. The
engine (core + instruments + patterns + arrange + analysis + playback) is
UI-free. This one-way boundary is strict: breaking it is a bug.

## Module map

| Module | Role |
|--------|------|
| `core/buffer.py` | `AudioBuffer(n, sr)` — `(N,2)` float64 stereo array; `add_at`, `add_at_pan`, `peak`, `rms`, `section_rms`, `normalize` |
| `core/grid.py` | `Grid(bpm, sr)` — `bar_t(bar, beat)`, `n_samples(bars)`, `step_t` |
| `core/rng.py` | `RngContext(seed).spawn(key)` — hierarchical SeedSequence; keys hashed via `zlib.crc32` (process-stable, unlike `hash()`) |
| `core/mixbus.py` | `MixBus.commit(L, R, weight)` — peak-normalizes before adding; commit-and-free to avoid holding all layers in RAM |
| `core/dsp.py` | `midi_to_hz`, `fade`, `slow_noise`, `lowpass/highpass/bandpass`, `glide_curve`, `sine_phase`, `warm_partials`, `feedback_delay` |
| `core/reverb.py` | `make_reverb_ir`, `reverb`, `reverb_stereo`, `make_stereo_ir_pair` |
| `core/mastering.py` | `master(buf)`, `write_wav(buf, path)`, `soft_limiter`, `high_shelf`, `low_shelf` |
| `core/loopfold.py` | `loop_fold(buf, loop_bars, xf_bars, grid)` — equal-power overlap-add for seamless game loops; `check_seam` |
| `instruments/base.py` | `ParamSchema`, `RenderCache` (MD5-keyed), `render_cached` |
| `instruments/registry.py` | `REGISTRY`, `get_instrument(id)`, `list_instruments()` |
| `instruments/*.py` | 27 instruments: percussion, strings, bass, voice, texture, fx |
| `patterns/step.py` | `Step`, `StepPattern` — per-step dicts with probability/accent/ghost |
| `patterns/schedule.py` | `Schedule(length_bars, bpm)` — bar-indexed pattern list; `add(bar, pattern, every=N)` |
| `patterns/groove.py` | `render_groove(schedule, rng_ctx)` — per-hit deterministic RNG; `render_loop` (wraps + folds); `render_pattern_spec(spec_dict)` |
| `arrange/section.py` | `Section(name, start_bar, length_bars)` — holds Schedules, renders into one buffer |
| `arrange/curves.py` | `Curve([(bar, value)])` — piecewise-linear automation; `fade_in_out`, `sidechain_pump` |
| `arrange/transitions.py` | `crossfade`, `hard_cut`, `insert_riser` |
| `arrange/track.py` | `Track(bpm)` — orchestrates sections, applies mastering, optional WAV write |
| `analysis/loudness.py` | `section_rms_report`, `rms_trend_slope`, `peak_headroom_db`, `intro_vs_aftermath` |
| `analysis/loops.py` | `seam_report`, `rms_flatness_report`, `full_loop_report` |
| `playback/clock.py` | `PlaybackClock` — sample/bar/beat position, thread-safe via GIL |
| `playback/service.py` | `PlaybackService` — single-buffer OR mixer-mode (`with_mixer()`); degrades gracefully without audio |
| `playback/cache.py` | `ContentAddressedCache` — in-memory LRU + on-disk .npy; SHA-256 keyed; thread-safe |
| `playback/scheduler.py` | `RenderScheduler` — ThreadPoolExecutor job queue; coalesces rapid edits; stale-while-fresh pattern |
| `playback/mixer.py` | `CallbackMixer` — N channel slots; gain/mute/solo; seamless loop + hot-swap at loop boundary |
| `document/__init__.py` | `forge.document` package (no Qt, no DSP) — mutable project model |
| `document/channels.py` | `PatternChannel`, `TextureChannel`, `AutomationChannel`, `StepData`, `Breakpoint` |
| `document/transaction.py` | `Transaction`, `FieldChange`, `channel_content_hash` (SHA-256, 16 hex) |
| `document/history.py` | `History` — undo/redo stack; slider-drag coalescing via `push(coalesce=True)` |
| `document/model.py` | `ProjectDoc` — typed edit API (`set_param`, `set_step`, `toggle_step`, `reroll`, `copy_steps`, `paste_steps`); observer callbacks; `channel_cache_key()` |
| `ui/window.py` | `MainWindow` — QMainWindow with transport, render button, File→Open/Save |
| `ui/transport.py` | `TransportWidget` — play/pause/stop/seek slider + bar:beat label |
| `ui/instrument_panel.py` | `InstrumentPanel` — auto-builds sliders/checkboxes from ParamSchema; `WorkshopPanel` — doc-bound with seed control + scheduler-backed audition |
| `ui/mixer.py` | `MixerWidget` — per-layer volume faders + mute buttons |
| `ui/pattern_editor.py` | `PatternEditor` — 16-step toggle grid; `TrackerEditor` — full tracker grid (keyboard, accent/ghost/prob, copy/paste, doc-bound) |
| `ui/project_view.py` | `InstrumentBrowser`, `ProjectTree` |
| `spec/schema.py` | `TrackSpec`, `PatternSpec`, `SectionSpec`, `ProjectSpec` dataclasses |
| `spec/validate.py` | `validate_project`, `validate_pattern` — raise ValueError on bad input |
| `spec/serialize.py` | `save_project(project, path)`, `load_project(path)` — stdlib JSON + pathlib |
| `control.py` | **Facade**: `list_instruments`, `render_instrument`, `render_pattern`, `render_track`, `render_channel`, `load_project`, `save_project` |
| `runner.py` | `render_project(project, path)` — save spec + render WAV + print; `project_main(build_fn, default_out)` — argparse entry point for example scripts |

## Instrument protocol

Every instrument callable has the signature:

```python
def make_kick(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
    sr = ctx.get("sr", 44100)
    ...
```

`params` keys match the instrument's `ParamSchema` list. Missing keys fall
back to schema defaults. Never raise on a missing optional key.

## PatternSpec dict format

```python
{
    "bpm": 138.0,
    "length_bars": 4,
    "n_steps": 16,          # optional, default 16
    "loop": False,          # apply loop_fold after render
    "xf_bars": 2.0,         # loop fold crossfade width
    "tracks": [
        {
            "instrument": "kick",
            "steps": [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0],
            "params": {"f0": 55.0},     # track-level defaults
            "probability": 1.0,
            "bars": [0, 4],             # only these bars (omit = all bars)
            "every": 2,                 # repeat every N bars
        }
    ]
}
```

Steps: `0`/`False`/`None` = silent; `1`/`True` = fire; dict = `{"on": bool,
"params": dict, "probability": float, "accent": bool, "ghost": bool}`.

## ProjectSpec dict format

```python
{
    "title": "My Track",
    "bpm": 138.0,
    "seed": 0,
    "sr": 44100,
    "normalize": True,
    "target": 0.85,
    "fade_out_s": 2.0,
    "sections": [
        {
            "name": "intro",
            "start_bar": 0,
            "length_bars": 8,
            "gain": 1.0,
            "schedules": [ <PatternSpec dict>, ... ]
        }
    ],
    "master_gain_curve": [[0, 0.0], [4, 1.0], [28, 1.0], [32, 0.0]]  # optional
}
```

## RNG rules

- Each `RngContext(seed)` is a root; `.spawn(key)` creates an independent
  child stream.
- Siblings spawned in any order produce identical per-sibling streams (keys
  are CRC32-hashed, so `spawn("a")` and `spawn("b")` on the same parent are
  always independent regardless of call order).
- Per-hit RNG in `render_groove`: `rng_ctx.spawn(f"b{bar}p{pat}s{step}")`.
  This means: reordering bars or patterns does NOT shift other RNG streams.

## Acceptance criteria from the plan

- **Game-state loops**: `full_loop_report(buf, seam_tolerance=0.05,
  max_slope=0.005)["ok"]` must be True.
- **Story tracks**: listening-approved against Phase-0 reference renders.
- **Per-section RMS**: aftermath RMS < intro RMS (the plan's "aftermath
  quieter than intro" rule).

## Tests

```bash
python3 -m unittest discover -s forge/tests -p "test_*.py"
# 555 tests, all green as of Plan 3 Phase 5
```

Tests use `unittest` (not pytest). All tests are in `forge/tests/`.
Qt tests use `QT_QPA_PLATFORM=offscreen` (set at the top of each Qt test
file — no display needed).

New test files added in Plan 3:
- `test_document.py`       — document model, transactions, history (74 tests)
- `test_cache_scheduler.py`— cache + scheduler (25 tests)
- `test_mixer.py`          — callback mixer (24 tests)
- `test_tracker_editor.py` — TrackerEditor + TrackerRow (33 tests)

## Document model (Plan 3 addition)

The `forge.document` package provides a mutable project model used by the
tracker GUI.  Key contracts:

- **No Qt, no DSP** in `forge.document.*` — fully testable headless.
- Every mutation goes through `ProjectDoc`'s typed edit API, which records a
  `Transaction` and pushes it to `History` for undo/redo.
- `doc.channel_cache_key(idx)` returns a SHA-256 hash of the channel's
  render-relevant data; the hash changes when anything that affects audio
  changes and stays the same after pure UI changes.
- `doc.subscribe(callback)` registers an observer called after every edit
  (including undo/redo).  The callback receives the `Transaction`.
- `History.push(txn, coalesce=True)` merges with the previous entry if both
  touch the same paths — used for slider drags.

## Cache / Scheduler / Mixer (Plan 3 addition)

- `ContentAddressedCache` — in-memory LRU + on-disk `.npy` store.
  Keys = `channel_cache_key()`; stored as float32 stereo arrays.
- `RenderScheduler` — wraps a `ThreadPoolExecutor`; `get_or_schedule(key, fn,
  on_done)` returns `(cached_buf, True)` on a hit, `(None, False)` on a miss
  and schedules the render.  `on_done(key, buf)` is called from the worker
  thread — UI code must marshal back to Qt (e.g. `QTimer.singleShot(0, ...)`).
- `CallbackMixer` — multi-channel loop mixer.  `load_channel(name, arr)` queues
  a hot-swap; the swap fires at the next loop boundary.  `mix_offline(n)`
  drives the same logic headless (tests + Phase 0 spike).
- `PlaybackService.with_mixer()` — creates a mixer-mode service; access via
  `svc.mixer`.

## Key design decisions (non-obvious, worth preserving)

- **`zlib.crc32` not `hash()`** in `RngContext.spawn()` — Python's `hash()`
  is randomized per-process since 3.3; CRC32 is stable across runs.
- **`loop_fold` requires `n_loop + n_xf` samples** — render more than
  `length_bars` by cycling the schedule in `render_loop`, not by extending
  the Schedule itself.
- **`_freeze_params` uses MD5 of sorted JSON** — dict key order is
  irrelevant; the same params always hit the same cache entry.
- **`MixBus.commit` peak-normalizes before adding** — prevents one loud
  instrument from stealing all the headroom from quieter ones.
- **`PlaybackService._open_stream` catches all exceptions** — no audio
  device in CI/headless is silent, not a crash.
- **`Section._bpm()` reads from the first Schedule** — sections don't carry
  their own BPM; they inherit it. All sections in a Track must agree on tempo.

## Adding a new instrument

1. Add a function `make_<name>(params, rng, **ctx) -> AudioBuffer` in the
   appropriate `instruments/*.py` file.
2. Add a `<NAME>_PARAMS = [ParamSchema(...), ...]` list.
3. Register it in `instruments/registry.py` under `REGISTRY`.
4. Add at least one test in `forge/tests/test_instruments.py`.
