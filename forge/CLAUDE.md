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
| `playback/service.py` | `PlaybackService` — sounddevice OutputStream; gracefully degrades if no audio device |
| `ui/window.py` | `MainWindow` — QMainWindow with transport, render button, File→Open/Save |
| `ui/transport.py` | `TransportWidget` — play/pause/stop/seek slider + bar:beat label |
| `ui/instrument_panel.py` | `InstrumentPanel` — auto-builds sliders/checkboxes from ParamSchema |
| `ui/mixer.py` | `MixerWidget` — per-layer volume faders + mute buttons |
| `ui/pattern_editor.py` | `PatternEditor` — 16-step button grid, emits PatternSpec dict |
| `ui/project_view.py` | `InstrumentBrowser`, `ProjectTree` |
| `spec/schema.py` | `TrackSpec`, `PatternSpec`, `SectionSpec`, `ProjectSpec` dataclasses |
| `spec/validate.py` | `validate_project`, `validate_pattern` — raise ValueError on bad input |
| `spec/serialize.py` | `save_project(project, path)`, `load_project(path)` — stdlib JSON + pathlib |
| `control.py` | **Facade**: `list_instruments`, `render_instrument`, `render_pattern`, `render_track`, `load_project`, `save_project` |

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
# 390 tests, all green as of Phase 10
```

Tests use `unittest` (not pytest). All tests are in `forge/tests/`.
Qt tests use `QT_QPA_PLATFORM=offscreen` (set at the top of each Qt test
file — no display needed).

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
