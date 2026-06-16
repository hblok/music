# CLAUDE.md — music/ root

This repository contains:
1. **Legacy generator scripts** (`dune/`, `trance/`, `ambient/`) — standalone
   procedural tracks written before the framework existed.
2. **forge** — a modular music synthesis framework extracted from those scripts.
3. **examples/** — worked examples using forge.
4. **plans/** — design documents.
5. **reference/** — reference WAV renders and stats.

## Repository map

```
music/
├── forge/               ← the framework (see forge/CLAUDE.md)
│   ├── core/            instruments, DSP, grid, RNG, mix, reverb, mastering
│   ├── instruments/     27 instruments in 6 families + registry
│   ├── patterns/        StepPattern, Schedule, render_groove / render_loop
│   ├── arrange/         Section, Curve, Track (full-track renderer)
│   ├── analysis/        loudness reports, loop-seam checks
│   ├── playback/        PlaybackService (sounddevice), PlaybackClock
│   ├── ui/              PySide6 GUI: MainWindow, transport, panels, editor
│   ├── spec/            ProjectSpec dataclasses, validation, JSON serialize
│   ├── tools/           collect_stats.py CLI tool
│   ├── tests/           390 unittest tests (all green)
│   └── control.py       GUI-agnostic facade — the ONLY import the UI uses
├── dune/                legacy standalone generators (psy-trance, dune lore)
├── trance/              legacy trance tracks (lost, nachtkind, tech_noir)
├── ambient/             legacy ambient tracks (lost, generate_ambient)
├── examples/            forge worked examples (sleeper_awakens_mini.py)
├── plans/               design/planning documents
└── reference/           reference WAV renders + stats.json
```

## Which path to use for new work

- **New tracks / modifications** → use forge (see `forge/CLAUDE.md`).
- **Bug-fixing a specific legacy script** → edit it directly, keep it
  standalone. Do NOT import forge into legacy scripts — they are self-
  contained by design.
- **Understanding a synthesis recipe** → the legacy CLAUDE.md files in
  `dune/`, `trance/`, and `ambient/` document every technique.

## Running

```bash
# Run all forge tests
python3 -m unittest discover -s forge/tests -p "test_*.py"

# Render a worked example to out/sleeper_awakens_mini.wav
python examples/sleeper_awakens_mini.py

# Launch the Qt GUI
python -m forge.ui.main --bpm 138
```

## Plans

`plans/implementation_plan2_modular_framework.md` is the authoritative
implementation guide for forge. The other plan files (`music_plan*.md`) cover
alternate directions (JS port, tracker GUI, full DAW) that have NOT been
implemented.

## Conventions shared across the whole repo

- **Python 3.12**, numpy + scipy, stdlib `wave`, PySide6 (GUI only).
- `soundfile`/`pydub` are NOT installed.
- **No samples** — everything is synthesized.
- All randomness: seeded `np.random.default_rng` (legacy) or forge's
  `RngContext` (hierarchical SeedSequence, process-stable CRC32 key hashing).
- Output: 44100 Hz, stereo, float64 internally, 16-bit PCM on disk.
- **Do not commit generated WAV files** — they are large and ephemeral.
- Do not delete or `.gitignore` tracked files without asking first.
