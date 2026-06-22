# Phase 1 — Headless Core (no Qt)

## Remaining Core Modules
- [ ] Fix candidate.py (remove stub AudioBuffer, fix RngContext.spawn usage)
- [ ] Create core/scoring.py (Scorecard dataclass, diff(), aggregate, worst)
- [ ] Create core/variants.py (VariantSpec, sweep(), render_and_score())
- [ ] Create core/project.py (MatchProject dataclass, save/load JSON)

## Phase 1 Tests
- [ ] Create tests/test_target.py
- [ ] Create tests/test_phrase.py
- [ ] Create tests/test_candidate.py
- [ ] Create tests/test_scoring.py
- [ ] Create tests/test_variants.py
- [ ] Create tests/test_project.py

## Phase 1 Acceptance
- [ ] All tests green: `python -m unittest discover soundmatch/tests`
- [ ] Commit: `soundmatch: headless core (target/phrase/candidate/scoring/variants/project) + tests`

# Phase 2 — Read-only inspector GUI
- [ ] app.py, ui/window.py, ui/reference_panel.py, ui/stems_panel.py, ui/metrics_panel.py, ui/spectrogram.py
- [ ] test_ui_smoke.py
- [ ] Commit: `soundmatch: read-only GUI (reference + stems + metrics panels)`

# Phase 3 — Patch Editor + Match Scorecard
- [ ] ui/patch_editor.py, ui/scorecard_panel.py
- [ ] Commit: `soundmatch: patch editor + match scorecard`

# Phase 4 — Variant Grid
- [ ] ui/variant_grid.py
- [ ] Commit: `soundmatch: variant grid`

# Phase 5 — A/B Viewer, project save/load, exporters
- [ ] ui/ab_viewer.py, wire project.py into window.py, exporters
- [ ] Commit: `soundmatch: A/B viewer + project save/load + exporters`

# Phase 6 (stretch) — Assisted matching
- [ ] core/search.py + button in patch_editor.py
- [ ] Commit: `soundmatch: assisted matching (coarse param search)`

# Final
- [ ] Push all commits to GitHub
