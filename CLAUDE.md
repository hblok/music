# CLAUDE.md — music/ root

This repository contains three main applications and a collection of legacy
generator scripts:

1. **forge** — modular music synthesis framework + PySide6 tracker GUI.
   See `forge/CLAUDE.md` for full detail.
2. **inspector** — standalone CLI audio analysis tool (librosa, essentia,
   demucs stem separation).  See `inspector/CLAUDE.md`.
3. **soundmatch** — PySide6 GUI that matches a synthesised patch to a
   real-world audio reference using inspector metrics + forge instruments.
   See `soundmatch/CLAUDE.md`.
4. **Legacy generator scripts** (`dune/`, `trance/`, `ambient/`) — standalone
   procedural tracks written before forge existed.

## Repository map

```
music/
├── forge/               ← synthesis framework + tracker GUI (forge/CLAUDE.md)
│   ├── core/            AudioBuffer, Grid, RNG, MixBus, DSP, reverb, mastering
│   ├── instruments/     27 instruments in 6 families + registry
│   ├── patterns/        StepPattern, Schedule, render_groove / render_loop
│   ├── arrange/         Section, Curve, Track (full-track renderer)
│   ├── analysis/        loudness reports, loop-seam checks
│   ├── playback/        PlaybackService (sounddevice), PlaybackClock, mixer
│   ├── document/        Mutable project model + undo/redo (no Qt, no DSP)
│   ├── ui/              PySide6 GUI: MainWindow, transport, panels, editor
│   ├── spec/            ProjectSpec dataclasses, validation, JSON serialize
│   ├── tools/           collect_stats.py CLI tool
│   ├── tests/           674 unittest tests (all green)
│   └── control.py       GUI-agnostic facade — the ONLY import the UI uses
├── inspector/           ← audio analysis CLI (inspector/CLAUDE.md)
│   ├── analyse.py       CLI entry point
│   ├── features.py      librosa + essentia extraction
│   ├── separation.py    demucs stem separation (optional, degrades gracefully)
│   ├── transcription.py per-stem pyin/onset transcription
│   ├── metrics.py       Metrics dataclass + characterize()
│   ├── report.py        text report renderer
│   └── plots.py         matplotlib PNG output
├── soundmatch/          ← sound-match GUI (soundmatch/CLAUDE.md)
│   ├── app.py           entry point
│   ├── core/            Target, Phrase, candidate, scoring, search, variants
│   ├── ui/              PySide6 panels (reference, stems, metrics, patch, ...)
│   └── tests/           unittest tests (headless + Qt smoke)
├── dune/                legacy standalone generators (psy-trance, dune lore)
├── trance/              legacy trance tracks (lost, nachtkind, tech_noir)
├── ambient/             legacy ambient tracks (lost, generate_ambient)
├── examples/            forge worked examples (sleeper_awakens_mini.py)
├── plans/               design/planning documents
└── reference/           reference WAV renders + stats.json
```

## Which path to use for new work

- **New tracks / modifications** → use forge (see `forge/CLAUDE.md`).
- **Analysing an audio reference** → use inspector CLI (see `inspector/CLAUDE.md`).
- **Matching a synth patch to audio** → use soundmatch (see `soundmatch/CLAUDE.md`).
- **Bug-fixing a specific legacy script** → edit it directly, keep it
  standalone. Do NOT import forge into legacy scripts — they are
  self-contained by design.
- **Understanding a synthesis recipe** → the CLAUDE.md files in
  `dune/`, `trance/`, and `ambient/` document every technique.

## Running

```bash
# Run forge tests
python3 -m unittest discover -s forge/tests -p "test_*.py"

# Run soundmatch tests
python3 -m unittest discover -s soundmatch/tests -p "test_*.py"

# Render a worked example to out/sleeper_awakens_mini.wav
python examples/sleeper_awakens_mini.py

# Launch the forge tracker GUI
python -m forge.ui.main --bpm 138

# Launch Sound-Match Studio
python -m soundmatch.app

# Run the inspector CLI
python3 -m inspector.analyse <file.mp3> [--plots] [--separate]
```

## Plans

`plans/implementation_plan2_modular_framework.md` — forge (complete).
`plans/implementation_plan3_tracker_gui.md` — tracker GUI (**all 10 phases
  complete**). Phases 0–5: `forge/document/` (mutable project model + undo/redo),
  cache, scheduler, mixer, WorkshopPanel, TrackerEditor. Phases 6–9 add:
  `BreakpointCurveWidget` / `TextureLane` / `AutomationLane` (Phase 6),
  `ArrangementView` + mixer binding (Phase 7), versioned save/load + WAV export
  + Plan 2 migrator (Phase 8), `AutoSave` + `ABCompareWidget` (Phase 9).
  119 new tests in phases 6–9; 674 total.

## Conventions shared across the whole repo

- **Python 3.12**, numpy + scipy, stdlib `wave`, PySide6 (GUI only). `soundfile` and `pydub` are also available.
- **No samples** — everything is synthesized.
- All randomness: seeded `np.random.default_rng` (legacy) or forge's
  `RngContext` (hierarchical SeedSequence, process-stable CRC32 key hashing).
- Output: 44100 Hz, stereo, float64 internally, 16-bit PCM on disk.
- **Do not commit generated WAV files** — they are large and ephemeral.
- Do not delete or `.gitignore` tracked files without asking first.

## Cross-track workflow & composition doctrine

Applies to every track directory (`dune/`, `trance/`, `ambient/`, `tracks/*`) —
genre-specific rules live in each directory's own `CLAUDE.md`; read that
first, this is only the cross-cutting part.

- **Probe before you build.** For a new track: (1) a notes doc with open
  questions, (2) a probe script rendering short (4-8 bar) samples of the
  instruments/drum figures/bed/refrain with a printed PASS/FAIL per
  question, (3) listen verdicts, (4) only then the full track script.
- **One song at a time.** Never build or revise several tracks in the same
  session/batch — it converges everything on the same skeleton. Ideas for
  other tracks go into their notes/TODO, not code.
- **Develop motifs, don't drop them.** One continuous performance cursor
  across the whole arrangement (bridge seams with pickups/ringing chords,
  no dead air); a good motif is stated, varied, made to answer itself, and
  brought back later — not stated once and abandoned after 4 bars. Skip
  long atmospheric intros.
- **Events, not carpets.** A distinctive small sound (ticks, blips, a
  motif) is a short EVENT with a musical answer — never a continuous
  30-40s texture; repeated as wallpaper it loses its character and starts
  to annoy.
- **Refrain/melody voices need sustain.** Never hand the tune to a
  percussive/decaying voice — it reads as a toy ("xylophone"). Percussive
  attacks are for groove and texture, not the lead.
- **Background beds stay low and irregular.** A constant drone/wind/pad
  layer: hard low-pass near the fundamental (no exposed mid tone),
  irregular multi-rate movement (never a fixed-rate beat/LFO — reads as a
  repetitive alarm), and low gain (a felt floor, not a heard wall).
- **Output: FLAC, not mp3**, for the compressed deliverable (WAV stays
  primary).
- **TTS singing/performing is a dead end** — tried multiple times, always
  rejected on naturalness. A short spoken TTS phrase for a sample/interlude
  slot (e.g. `tracks/ebm`'s `machine.py` chain) is fine; don't retry TTS
  *singing* without a genuinely new idea.

## Python style guide

These rules apply everywhere in this repo:

- **Paths**: use `pathlib` — `import pathlib` and `pathlib.Path(...)`.
  Never `os.path`.
- **Tests**: use `unittest` — `import unittest` and subclass
  `unittest.TestCase`.  Never pytest.
- **Imports at module top**: do not place imports inside functions or
  methods unless absolutely required (e.g. lazy-loading a heavy optional
  dependency like demucs/torch).
- **Import the module, not the name**: prefer `import pathlib` over
  `from pathlib import Path`; prefer `import numpy as np` over
  `from numpy import array`.  Exceptions: `from __future__ import
  annotations` and `from dataclasses import dataclass, field` (stdlib
  patterns where the module-level form is awkward and universally accepted).
- **No copy-pasted blocks**: if the same logic appears in two places,
  extract a shared helper.  Duplication in tests is acceptable only for
  fixture setup; never for assertion logic.
