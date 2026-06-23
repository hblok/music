# CLAUDE.md — soundmatch/

**Sound-Match Studio** — a PySide6 GUI tool that helps match a synthesised
instrument patch to a real-world audio reference.

See `../CLAUDE.md` for repo-level context and Python style rules.

## Purpose in one paragraph

The user selects a region from a reference audio file (and optionally a
separated stem), the tool measures timbral metrics, renders a candidate patch
from a forge instrument, and scores how well it matches.  A variant sweep lets
the user audition many parameter combinations at once.  Sessions are saved as
`.smatch` JSON files.

## Architecture

```
soundmatch/
├── app.py           Entry point: parse args, build QApplication, open MainWindow
├── core/
│   ├── target.py    Target — load audio, select region, pick stem → Metrics
│   ├── phrase.py    Phrase / Note — timed note sequence; seed_from_metrics()
│   ├── candidate.py render_phrase() — THE single shared render path (never duplicated)
│   ├── scoring.py   Scorecard, diff() — per-metric distance + aggregate
│   ├── search.py    coarse_search(), instrument_search() — grid search over params
│   ├── variants.py  VariantSpec, sweep(), render_and_score() — variant engine
│   ├── resynth.py   Spectral resynthesis (tonal + noise model) from analysis
│   ├── project.py   MatchProject dataclass — full session state; save/load JSON
│   └── exporters.py export_snippet / export_markdown / export_montage_png (headless)
├── ui/
│   ├── window.py    MainWindow — docks panels, owns PlaybackService, File menu
│   ├── reference_panel.py  Waveform + region selection
│   ├── stems_panel.py      Stem selector (mix / drums / bass / other / vocals)
│   ├── metrics_panel.py    Target Metrics display
│   ├── patch_editor.py     Instrument + params sliders
│   ├── scorecard_panel.py  Scorecard table (per-metric deltas)
│   ├── variant_grid.py     Sweep grid — N×M card layout
│   ├── spectrogram.py      Shared spectrogram widget
│   ├── ab_viewer.py        A/B compare widget
│   ├── instrument_search_dialog.py  Cross-instrument search UI
│   └── resynth_dialog.py   Resynthesis export dialog
└── tests/
    ├── fixtures.py          Shared test helpers (tiny audio arrays)
    ├── test_candidate.py
    ├── test_metrics.py
    ├── test_phrase.py
    ├── test_project.py
    ├── test_scoring.py
    ├── test_search.py
    ├── test_target.py
    ├── test_ui_smoke.py     Qt smoke tests (QT_QPA_PLATFORM=offscreen)
    └── test_variants.py
```

## Key data flows

1. **Load reference** → `target.Target.load()` → `inspector.metrics.characterize()` → `Metrics`
2. **Set patch** → `candidate.render_phrase(phrase, instrument_id, params, layers, seed)` → `AudioBuffer`
3. **Score** → `scoring.diff(target_metrics, candidate_metrics)` → `Scorecard`
4. **Sweep** → `variants.sweep(phrase, base_params, axis, values)` → list of `VariantResult`
5. **Save** → `project.MatchProject.save(path)` (JSON via `pathlib`)

## Dependencies

- **forge** — `render_phrase` uses forge instruments and `AudioBuffer`.
  `PlaybackService` is forge's playback engine.
- **inspector** — `inspector.metrics.characterize()` measures a raw audio
  array; `inspector.features.load_audio()` loads files.  soundmatch never
  calls inspector's CLI.
- soundmatch does **not** own audio loading or timbral measurement — it
  delegates everything to inspector.

## Running

```bash
# From /repos/music/
python -m soundmatch.app
python -m soundmatch.app reference.mp3

# Tests
python3 -m unittest discover -s soundmatch/tests -p "test_*.py"
# Qt tests require: QT_QPA_PLATFORM=offscreen (set at top of test_ui_smoke.py)
```

## Key invariants

- `core/` has **no Qt imports** — all core modules are headless and testable.
- `candidate.render_phrase` is the **only** place that calls forge to
  render audio.  Never duplicate this logic in UI or variant code.
- `MatchProject.save/load` uses `pathlib.Path.write_text` / `read_text` with
  explicit `encoding="utf-8"`.  No `open()` calls.

## Style

Follow the repo-level Python style guide in `../CLAUDE.md`.
