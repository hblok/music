# Implementation Plan — Sound-Match Studio

> **Handoff document for an implementing agent.** This is the build plan for the
> design in [`inspector_gui_plan1_sound_match_studio.md`](inspector_gui_plan1_sound_match_studio.md).
> Read that first for *why*; this document is *how*: package layout, module
> APIs, tests, and a phase-by-phase sequence with one commit minimum per phase.
> The motivating worked example (Black Box — "Strike It Up" lead) and its
> measured numbers are reused throughout as test fixtures.

---

## Locked decisions (from the project owner)

| Question | Decision |
|---|---|
| UI toolkit | **PySide6** — matches the Forge app. *(Owner said "PyQt like the Forge app"; the Forge app is actually PySide6, so we use PySide6 for consistency and reuse. Do not introduce PyQt5/6.)* |
| Scope of sound | **Phrases and loops**, not just single shots. The selection/phrase is the unit; playback loops. |
| Coupling | **Standalone.** Do **not** wire into the Tracker GUI (Plan 3) or DAW (Plan 4) yet. Clean export only. |
| Code reuse | **Reuse forge + inspector** aggressively (instruments, registry, `ParamSchema`, `PlaybackService`, `InstrumentPanel`, core DSP, demucs separation). |
| Tests | **Unit tests required**, `unittest` style, mirroring `forge/tests/`. Run under `QT_QPA_PLATFORM=offscreen` for any widget tests. |
| Filesystem | **`pathlib` only** — no `os.path`. |
| Duplication | **DRY.** The metric battery, the candidate-render path, and the variant engine are each *one* module reused everywhere. |
| Commits | **≥ 1 commit per phase**, each phase green (tests pass) before committing. |

---

## Conventions (match the existing codebase)

- `from __future__ import annotations` at the top of every module; full type hints.
- Tests are `unittest.TestCase` subclasses in `<pkg>/tests/test_*.py`; no pytest-only features.
- Audio IO via **`soundfile`** only. **Never call `torchaudio.save`** (broken in this
  container — see `inspector/CLAUDE.md`); demucs runs on **CPU**; stems are
  `drums/bass/other/vocals`; separation gracefully degrades if torch/demucs absent.
- Synthesis is deterministic: thread a seed via `forge.core.rng.RngContext` /
  `numpy.random.default_rng(seed)`. Every render records its seed.
- Instruments are discovered through `forge.instruments.registry` (`REGISTRY`,
  `get_instrument`, `list_instruments`) and their `ParamSchema` lists — never
  hard-code an instrument or its params in the UI.
- Keep **all DSP/analysis headless** in `core/` (no Qt imports) so it is unit-
  testable without a display; `ui/` is thin and delegates to `core/`.
- Commit message subject per phase below; keep the repo's existing trailer
  convention (Co-Authored-By / session line) as already used in `git log`.

---

## Package layout (new, standalone at repo root)

```
soundmatch/
├── __init__.py
├── app.py                     # PySide6 entry point: python -m soundmatch.app [--sr] [FILE]
├── core/                      # headless — NO Qt imports; the testable heart
│   ├── __init__.py
│   ├── target.py              # Target: load + select region + pick stem → Metrics
│   ├── phrase.py              # Phrase/Note model; seed_from_metrics(); loop length
│   ├── candidate.py           # render_phrase(): the ONE patch-render path (DRY)
│   ├── scoring.py             # diff(Metrics, Metrics) → Scorecard + aggregate distance
│   ├── variants.py            # sweep() + render_and_score(): the variant engine (DRY)
│   └── project.py             # MatchProject dataclass; save/load JSON via pathlib
├── ui/                        # PySide6 widgets — thin, delegate to core
│   ├── __init__.py
│   ├── window.py              # MainWindow: docks the panels, owns PlaybackService
│   ├── reference_panel.py     # load + waveform/spectrogram + draggable selection
│   ├── stems_panel.py         # separate (async) + per-stem audition/solo + "set target"
│   ├── metrics_panel.py       # render the Metrics battery as numbers + plots
│   ├── patch_editor.py        # wraps forge InstrumentPanel + a layer list
│   ├── scorecard_panel.py     # target vs candidate Δ table + aggregate
│   ├── variant_grid.py        # axis/macro sweep → scored, auditionable cards
│   ├── ab_viewer.py           # stacked spectrograms + synced/looped A/B playback
│   └── spectrogram.py         # shared spectrogram widget (matplotlib FigureCanvas)
└── tests/
    ├── __init__.py
    ├── fixtures.py            # paths + the Strike It Up reference numbers
    ├── test_metrics.py
    ├── test_target.py
    ├── test_phrase.py
    ├── test_candidate.py
    ├── test_scoring.py
    ├── test_variants.py
    ├── test_project.py
    └── test_ui_smoke.py       # offscreen construct-without-crash checks
```

**The keystone (DRY): the metric battery lives in `inspector/metrics.py`** — a new
*shared* module so both the existing inspector CLI report *and* this tool measure
identically (the design doc's "target and candidate measured by the same code").
`soundmatch.core.target` and `soundmatch.core.candidate` both call it; numbers can
never diverge.

---

## Shared metric battery — `inspector/metrics.py` (built in Phase 0)

Pure functions over `(y: np.ndarray, sr: int)`, plus a `Metrics` dataclass bundling
them and a single `characterize()` entry point. These formalize the ad-hoc snippets
from the worked session.

```python
@dataclass(frozen=True)
class Metrics:
    percussive_ratio: float          # % (HPSS)
    centroid_hz: float
    band_balance: dict[str, float]   # "80-300","300-800","800-2500","2.5-9k" → %
    onset_count: int
    onset_density: float             # events/sec
    median_ioi_s: float
    peaks: list[tuple[float, float]] # (freq_hz, rel_db), low→high energy desc
    chord: dict                      # {"pitch_classes": [...], "midi": [...], "sub_octave": bool}
    band_decay_ms: dict[str, float]  # per-band time to 25% of peak

def percussive_ratio(y, sr, margin: float = 3.0) -> float          # librosa.effects.hpss
def centroid_hz(y, sr) -> float
def band_balance(y, sr, edges=(80,300,800,2500,9000)) -> dict[str,float]
def onset_stats(y, sr, hop=256, delta=0.12, wait=3) -> dict
def fft_peaks(y, sr, fmax=3000.0, floor_db=-18.0) -> list[tuple[float,float]]
def detect_chord(y, sr) -> dict        # peaks → pitch classes + MIDI incl. sub-octave
def band_decay_ms(y, sr, bands=((200,1500),(3500,9000))) -> dict[str,float]
def characterize(y, sr) -> Metrics     # calls all of the above — the single entry point
```

`Metrics.to_dict()` / `from_dict()` for project serialization.

---

## Phases

### Phase 0 — Shared metric battery
**Goal:** the foundation both CLI and GUI share. No Qt, no app yet.
**Files:** `inspector/metrics.py`; `soundmatch/__init__.py`, `soundmatch/tests/__init__.py`,
`soundmatch/tests/fixtures.py`, `soundmatch/tests/test_metrics.py`.
**Fixtures:** isolate the Strike It Up lead once (`inspector.separation` on
`Black_Box-Strike_It_Up_Xo3kp5BLF6Q.mp3`, 1–10 s, `other` stem) and commit a
small WAV under `soundmatch/tests/data/` (or compute on the fly if demucs present;
skip-if-absent otherwise). `fixtures.py` records the known targets:
`percussive_ratio≈82`, `centroid≈2542 Hz`, `band_balance≈{80-300:18, 300-800:30,
800-2500:41, 2.5-9k:7}`, `onset_count≈36`, `median_ioi≈0.238 s`, chord G# major
with a sub-octave.
**Tests:** assert each metric on the fixture within tolerance (e.g. ±3 % perc,
±150 Hz centroid, ±4 pts per band, onset count ±2). These tolerances are the
regression contract for the whole tool.
**Acceptance:** `python -m unittest soundmatch.tests.test_metrics` green.
**Commit:** `soundmatch: shared metric battery (inspector/metrics.py) + tests`.

### Phase 1 — Headless core (no Qt)
**Goal:** load→characterize→render-candidate→score→sweep→save, all headless.
**Files & APIs:**
- `core/target.py` — `Target.from_file(path: Path, start_s, end_s, stem="other")`
  using `inspector.features.load_audio` + `inspector.separation.separate_stems`
  (region-limited, like `--start/--end`); `.metrics -> Metrics` via
  `inspector.metrics.characterize`.
- `core/phrase.py` — `Note(t: float, midi: list[int])`, `Phrase(bpm, length_s,
  notes, loop=True)`, `seed_from_metrics(m: Metrics, bpm) -> Phrase` (onsets →
  note times, `detect_chord` → MIDI). Loop length = selection length (phrases/loops req).
- `core/candidate.py` — **the one render path**:
  `render_phrase(phrase, instrument_id, params, layers, seed, sr) -> AudioBuffer`.
  `layers` is a list of `(instrument_id, params)` summed (the two-layer
  tonal+snap decomposition). Used by candidate, scorecard, and variants — never
  re-implemented.
- `core/scoring.py` — `Scorecard` (per-metric target/candidate/Δ) and
  `diff(target: Metrics, cand: Metrics, weights=None) -> Scorecard`;
  `Scorecard.aggregate -> float` (weighted normalized distance);
  `Scorecard.worst() -> str` (metric to chase next).
- `core/variants.py` — `VariantSpec(name, param_overrides)`,
  `sweep(base_params, axis, values) -> list[VariantSpec]` (axis = a param name or
  a named macro: `"snare"`,`"staccato"`,`"body"`), and
  `render_and_score(phrase, instrument_id, specs, target, seed, sr) -> list[VariantResult]`
  reusing `render_phrase` + `characterize` + `diff`. **Port `house/strike_variants.py`
  to call this engine** (delete its duplicated render/measure once equivalent).
- `core/project.py` — `MatchProject` dataclass (reference path+sha, selection,
  stem, cached target metrics, phrase, instrument_id, params, layers, seed,
  variants, score); `save(p: Path)`, `load(p: Path) -> MatchProject` (JSON via
  `pathlib.Path.write_text`/`read_text`).
**Tests:** `test_target` (region+stem metrics match Phase 0 fixture),
`test_phrase` (onset→note mapping, loop length), `test_candidate`
(determinism: same seed → identical buffer; layers sum), `test_scoring`
(diff math, aggregate monotonic, worst() picks the right band),
`test_variants` (sweep cardinality, scores sorted, a known-good spec wins),
`test_project` (round-trip save/load equality).
**Acceptance:** `python -m unittest discover soundmatch/tests` green; a headless
script reproduces the `G_full_root` result (~84 % perc) from the worked example.
**Commit:** `soundmatch: headless core (target/phrase/candidate/scoring/variants/project) + tests`.

### Phase 2 — Read-only inspector GUI
**Goal:** a usable visual front-end to the analysis — load, select, separate, see metrics.
**Files:** `app.py`, `ui/window.py`, `ui/reference_panel.py`, `ui/stems_panel.py`,
`ui/metrics_panel.py`, `ui/spectrogram.py`.
- `app.py` mirrors `forge/ui/main.py` (Fusion light palette, `QApplication`,
  `MainWindow`); owns a `forge.playback.service.PlaybackService` for audition.
- `ui/spectrogram.py` — **shared** matplotlib `FigureCanvasQTAgg` widget; factor
  the spectrogram drawing out of `inspector/plots.py` into a helper both use (no
  copy/paste). Reused by metrics_panel and ab_viewer.
- `reference_panel.py` — waveform + spectrogram + draggable selection emitting
  `selectionChanged(start_s, end_s)`.
- `stems_panel.py` — "Separate" runs `separate_stems` on a `QThread`/worker
  (it's the only slow op, ~10 s/clip) with a progress indicator; per-stem rows
  with audition (via PlaybackService), solo, and `targetChosen(stem)`; disabled
  with a clear message if demucs/torch missing.
- `metrics_panel.py` — renders `Target.metrics` as a numbers grid + band-balance
  bar plot + onset table.
**Tests:** `test_ui_smoke` constructs each widget under
`QT_QPA_PLATFORM=offscreen` and feeds a tiny synthetic buffer; assert no
exceptions and that `selectionChanged`/`targetChosen` signals fire.
**Acceptance:** launch, load the mp3, select 1–10 s, separate, audition `other`,
see ~82 % percussive in the panel.
**Commit:** `soundmatch: read-only GUI (reference + stems + metrics panels)`.

### Phase 3 — Patch Editor + Match Scorecard
**Goal:** match a sound inside the tool.
**Files:** `ui/patch_editor.py`, `ui/scorecard_panel.py`.
- `patch_editor.py` — instrument dropdown from `list_instruments()` grouped by
  family; **reuse `forge.ui.instrument_panel.InstrumentPanel`** for the auto-built
  sliders (it already maps `ParamSchema`); add a **layer list** (add/remove a
  second instrument+params for the tonal+snap split) and a seed field; debounced
  `patchChanged(instrument_id, params, layers, seed)`.
- `scorecard_panel.py` — on patch change, call `render_phrase` + `characterize` +
  `diff`; show target/candidate/Δ per metric and the aggregate; color
  `Scorecard.worst()`. Audition the candidate (looped) via PlaybackService.
**Tests:** extend `test_ui_smoke` (editor builds sliders for a sample
instrument; scorecard computes a diff from two synthetic metrics).
**Acceptance:** dial `synth_brass` toward the target and watch the aggregate drop;
candidate audio loops against the target.
**Commit:** `soundmatch: patch editor + match scorecard`.

### Phase 4 — Variant Grid
**Goal:** sweep and compare, the `strike_variants` workflow made interactive.
**Files:** `ui/variant_grid.py`.
- Declare an axis (param or macro) + values → `variants.render_and_score` →
  grid of cards (spectrogram thumb via the shared widget, key metrics, score,
  loop-play). "Promote" sends a card's params back to the Patch Editor.
**Tests:** smoke test the grid builds N cards from a stub result list.
**Acceptance:** reproduce the 7-variant spread; `G_full_root` shows the best score.
**Commit:** `soundmatch: variant grid`.

### Phase 5 — A/B Viewer, project save/load, exporters
**Goal:** close the loop and make results portable.
**Files:** `ui/ab_viewer.py`; wire `core/project.py` into `window.py`; add exporters.
- `ab_viewer.py` — stacked spectrograms (target on top, candidate below; reuse
  the shared widget) + synced, **looped** toggle playback (learn the toggle UX
  from `forge.ui.ab_compare.ABCompareWidget`, but this compares *audio*, not
  doc params). Export the montage PNG (as produced by hand this session).
- Exporters (in `core/`, reused headless): runnable patch snippet (in the spirit
  of `house/strike_intro.py`), the stems, the montage, and a markdown
  characterization (like `inspiration/black_box/intro_report.md`).
- File menu: New/Open/Save MatchProject (`.smatch` JSON).
**Tests:** `test_project` round-trip already covers the model; add an exporter
test (snippet is importable / runs; markdown contains the metric numbers).
**Acceptance:** save a project, reopen it, every number re-derives identically;
exported snippet renders the matched phrase.
**Commit:** `soundmatch: A/B viewer + project save/load + exporters`.

### Phase 6 — (stretch) Assisted matching
**Goal:** a "Suggest" button proposing a starting patch.
**Files:** `core/search.py` + a button in `patch_editor.py`.
- Coarse param search (the manual `itertools.product` sweep) minimizing
  `Scorecard.aggregate`; reuses `render_phrase`/`characterize`/`diff`; runs on a
  worker thread; proposes params the user then refines by ear. One-click
  pitch/onset seeding into the Phrase.
**Tests:** `test_search` — on a synthetic target the search reduces aggregate
distance below a threshold within a bounded iteration count.
**Acceptance:** "Suggest" lands within audible range of the target on the worked example.
**Commit:** `soundmatch: assisted matching (coarse param search)`.

---

## Dependencies & risks

- **PySide6** (already used by Forge), **librosa/essentia/soundfile/matplotlib**
  (inspector), **demucs/torch** (optional; degrade gracefully). No new heavy deps;
  spectrograms use matplotlib's Qt backend rather than adding pyqtgraph.
- **Slow op:** demucs separation (~10 s/clip on CPU) — always off the UI thread
  with progress; cache stems per (file, region) so re-runs are instant.
- **Determinism:** all renders seeded; the project file is the single source of
  truth so reopening reproduces every metric (no stale cached numbers).
- **DRY guard:** if you find yourself measuring a metric or rendering a patch in
  more than one place, stop and route it through `inspector.metrics.characterize`
  or `core.candidate.render_phrase`. The worked-session pain was exactly this
  duplication; the plan exists to remove it.

## Definition of done (per phase and overall)

- Each phase ends green: `python -m unittest discover soundmatch/tests` (and the
  Phase 0 inspector metric tests) pass, then commit.
- Overall: a user can open the Strike It Up mp3, isolate the `other` stem,
  characterize it, build a `synth_brass` two-layer patch, sweep variants, A/B it
  against the source, score the match, and export a runnable snippet + report —
  all inside one PySide6 app, with no copy-pasted metric or render code.
