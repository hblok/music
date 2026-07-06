# music

A programmatic music synthesis toolkit — every sound is generated from code, no samples, no DAW, no MIDI. Three integrated applications (a synthesis framework, an audio analyser, and a patch-matching studio) sit alongside a growing catalogue of procedural tracks and a body of music-theory and sound-engineering reference material. Everything runs in Python with NumPy and SciPy; GUIs use PySide6.

## What's inside

### forge — modular synthesis framework + tracker GUI

The heart of the repo. `forge` is a fully sample-accurate synthesis engine with 27 registered instruments across six families (percussion, bass, strings, voices, textures, FX), a step-pattern sequencer with accent/ghost/probability per step, a section-based arrangement renderer with crossfades and automation curves, and a PySide6 tracker GUI with transport, mixer, A/B compare, breakpoint automation lanes, and project save/load. The UI communicates with the engine exclusively through a single facade module (`forge/control.py`) — no DSP or engine imports leak into the GUI layer.

```bash
python -m forge.ui.main              # launch the tracker GUI
python examples/sleeper_awakens_mini.py  # render a worked example to WAV
python -m unittest discover -s forge/tests -p "test_*.py"  # 674 tests
```

The tracker provides a 16-step grid per channel with per-step accent, ghost, and probability controls; a workshop panel for per-instrument parameter tweaking and auditioning; sections with independent pattern overrides; a mixer dock; an arrangement view for section CRUD; A/B snapshot comparison; and autosave recovery. Projects save as versioned JSON; WAV export renders all channels across all sections with mastering. See [MANUAL.md](MANUAL.md) for the full user manual.

### inspector — audio analysis CLI

A standalone command-line tool that loads any audio file and produces a structured report covering tempo (with per-30-second windows), structural segmentation, per-section timbral features (spectral centroid, bandwidth, rolloff, zero-crossing rate, bass/mid/high ratios), key estimation (Krumhansl-Kessler + Essentia), and optional stem separation via Demucs with per-stem pitch and rhythm transcription. Outputs text reports and matplotlib plots.

```bash
python -m inspector.analyse track.mp3 --plots --separate
```

Inspector has no dependency on forge — it runs on librosa, essentia, matplotlib, and soundfile. Demucs/torch are optional and degrade gracefully when absent.

### soundmatch — sound-match studio GUI

A PySide6 application that helps you match a synthesised instrument patch to a real-world audio reference. You load a reference file, select a region, and the tool measures timbral metrics (via inspector), renders a candidate patch (via forge), and scores the match. A variant sweep lets you audition many parameter combinations at once, and a cross-instrument search explores which forge instrument best fits the target. Sessions save as `.smatch` JSON.

```bash
python -m soundmatch.app             # launch the studio
python -m soundmatch.app ref.mp3     # launch with a reference file
```

### Legacy track generators

Before forge existed, every track was a standalone procedural script — self-contained, no imports, deterministic via seeded RNG. These scripts still render correctly and are kept for bug-fixing and reference. They live under `tracks/` in three collections:

- **dune/** — 19 generative ambient and psy-trance tracks for a Dune RTS game, all in D Phrygian dominant, from desert ambience (`arrakis_winds_v3`, a seamless game loop) through battle psy (`fall_of_arrakeen`, `jihad`) to the album closer `kwisatz_haderach` which fuses the engines of three previous tracks simultaneously. Every track has detailed design notes and the scripts verify their own composition (section RMS ordering, hook counts, seam checks) on every render.
- **trance/** — a catalogue of standalone trance tracks (lost, nachtkind, tech_noir, ungeschrieben, unsung, adrift, farlight, penumbra, eisgang, maschinenherz, silver_wire), each with its own instrument recipes and compositional form. The `instruments/` subdirectory contains a full indexed catalog of every synthesis recipe used across the collection.
- **ambient/** — ambient experiments (lost, persian).
- **house/** — house variants (strike_intro, strike_variants).

### Theory and reference material

- **theory/** — three longform references written from a math/code perspective: a music theory introduction, a programmatic synthesis primer, and a sound engineering guide covering mixing, mastering, and the signal pipeline from oscillators to final WAV.
- **inspiration/** — analysis notes and inspector reports for tracks that inspired the project's sound design.
- **plans/** — design and implementation documents for the forge framework, the tracker GUI, and sound-match studio.

## Repository structure

```
music/
├── forge/                  synthesis framework + tracker GUI
│   ├── core/               AudioBuffer, Grid, RNG, MixBus, DSP, reverb, mastering
│   ├── instruments/        27 instruments in 6 families + registry
│   ├── patterns/           StepPattern, Schedule, render_groove / render_loop
│   ├── arrange/            Section, Curve, Track (full-track renderer)
│   ├── analysis/           loudness reports, loop-seam checks
│   ├── playback/           PlaybackService, PlaybackClock, mixer, cache, scheduler
│   ├── document/           mutable project model + undo/redo (no Qt, no DSP)
│   ├── spec/               ProjectSpec dataclasses, validation, JSON serialize
│   ├── ui/                 PySide6 GUI: MainWindow, transport, panels, editors
│   ├── tools/              collect_stats.py CLI tool
│   └── tests/              674 unittest tests
├── inspector/              audio analysis CLI
│   ├── analyse.py          CLI entry point
│   ├── features.py         librosa + essentia extraction
│   ├── separation.py       demucs stem separation (optional)
│   ├── transcription.py    per-stem pyin/onset transcription
│   ├── metrics.py          Metrics dataclass + characterize()
│   ├── report.py           text report renderer
│   └── plots.py            matplotlib PNG output
├── soundmatch/             sound-match GUI
│   ├── core/               Target, Phrase, candidate, scoring, search, variants
│   ├── ui/                 PySide6 panels (reference, stems, metrics, patch, …)
│   └── tests/              unittest tests (headless + Qt smoke)
├── tracks/                 legacy standalone generator scripts
│   ├── dune/               Dune RTS soundtrack (19 tracks + notes)
│   ├── trance/             trance catalogue + instrument catalog
│   ├── ambient/            ambient experiments
│   └── house/              house variants
├── examples/               forge worked examples
├── theory/                 music theory, synthesis primer, sound engineering
├── inspiration/            reference track analyses
├── plans/                  design and implementation documents
├── reference/              baseline WAV renders + stats.json
├── MANUAL.md               forge tracker user manual
└── CLAUDE.md               development conventions and style guide
```

## Getting started

### Dependencies

```bash
pip install numpy scipy pyside6 sounddevice soundfile
```

For inspector's full feature set (optional):

```bash
pip install librosa essentia demucs torch matplotlib
```

### Quick start

Render a track:

```bash
python examples/sleeper_awakens_mini.py   # writes to out/sleeper_awakens_mini.wav
```

Launch the tracker GUI:

```bash
python -m forge.ui.main                  # opens the forge tracker
python -m forge.ui.main --bpm 138        # with a specific tempo
```

Analyse an audio file:

```bash
python -m inspector.analyse track.mp3 --plots
```

Match a synth patch to a reference:

```bash
python -m soundmatch.app reference.mp3
```

Run the test suite:

```bash
python -m unittest discover -s forge/tests -p "test_*.py"
python -m unittest discover -s soundmatch/tests -p "test_*.py"
```

## Key design principles

**No samples.** Every sound is synthesized from oscillators, noise, and DSP — no external audio assets. This makes the entire catalogue deterministic and regenerable from code alone.

**Seeded randomness.** All randomness flows through `np.random.default_rng` (legacy scripts) or forge's `RngContext` (hierarchical `SeedSequence` with CRC32 key hashing, process-stable across runs). The same script with the same seed always produces the same WAV, bit-for-bit.

**Self-verifying tracks.** Legacy generator scripts print section maps, hook counts, seam checklists, per-section RMS, and form checks (PASS/FAIL) after every render — the composition can be verified without listening.

**Audio spec.** 44100 Hz, stereo, float64 internally, 16-bit PCM on disk. No generated WAV files are committed to git.

**Strict module boundaries.** The forge UI imports only from `forge.control` — never from core, instruments, or DSP. The `forge.document` package has no Qt or DSP imports. Inspector has no forge dependency. Soundmatch delegates audio loading and measurement to inspector and rendering to forge — it owns neither.

## Python style

- Python 3.12, `pathlib` for all paths (never `os.path`), `unittest` for tests (never pytest).
- Import the module, not the name: `import numpy as np` over `from numpy import array`. Exceptions for stdlib patterns (`from dataclasses import dataclass, field`).
- All imports at module top level; lazy imports only for heavy optional dependencies (demucs/torch).
- No copy-pasted blocks — extract a shared helper. Duplication in test fixtures is acceptable; never for assertion logic.

## License

CC0 1.0 Universal — see [LICENSE](LICENSE).
