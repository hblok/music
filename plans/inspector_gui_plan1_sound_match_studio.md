# Plan — Sound-Match Studio (Inspector GUI)

> **Standalone briefing document.** Self-contained: it describes the existing
> pieces in conceptual terms and everything an implementing agent needs. It does
> not depend on the Tracker GUI (Plan 3) or DAW (Plan 4) — it is a *sibling*
> tool with a different purpose. Where those plans are about **composing** new
> material, this tool is about **reverse-engineering an existing sound** and
> rebuilding it with the procedural synth engine. It can reuse their UI
> primitives (`forge/ui/`) if present, or stand alone on the inspector +
> instrument backends.

---

## Background (context for the implementing agent)

Two mature backends already exist in this repo:

1. **`inspector/`** — a standalone audio-analysis CLI (librosa + essentia +
   demucs). `python3 -m inspector.analyse <file> [--start S --end S]
   [--separate --stems-out DIR] [--plots]` produces tempo/key/structure/timbre/
   harmony, optional **demucs stem separation** (drums/bass/other/vocals) with
   per-stem pitch & rhythm transcription, and PNG plots. See `inspector/CLAUDE.md`.

2. **`forge/`** — a procedural synthesis engine (numpy/scipy, no samples).
   Instruments are parameterized recipes registered in
   `forge/instruments/registry.py`; each exposes a `ParamSchema` list (type,
   range, label, unit) that **the GUI can auto-build sliders from**. Rendering
   is deterministic (seeded RNG). There is already a partial UI layer in
   `forge/ui/` (`ab_compare.py`, `instrument_panel.py`, `mixer.py`, `window.py`, …).

This plan was written immediately after a **manual sound-matching session**:
recreating the lead stab in the first 9 s of Black Box — "Strike It Up". That
session *is* the spec — it exercised, by hand, exactly the loop this tool should
make first-class. The pain was that every step (separate, measure, render a
synth patch, compare, tweak, re-render, sweep variants, plot) was an ad-hoc
shell/Python snippet. The tool turns that into an interactive workstation.

### The worked example (the loop, concretely)

The Strike It Up lead was reverse-engineered like this — each numbered step maps
to a panel below:

1. **Isolate**: demucs on seconds 1–10 → the `other` stem held the lead alone.
   (Whole-mix pitch tracking had given four contradictory answers; the stem made
   analysis reliable. *Stem isolation is the enabler — it must be step one.*)
2. **Characterize the target** with a handful of metrics:
   - HPSS harmonic/percussive split → **82 % percussive** (the key insight: it's
     a *staccato* stab, not a sustained sax — the first recreation read 0.3 %).
   - Spectral centroid → **2542 Hz**.
   - Onset detection → **36 hits**, median IOI 0.238 s ≈ straight 8th notes.
   - FFT peak picking on a stab body → **G# major chord** (207 Hz≈G#3, 520≈C5,
     620≈D#5), plus a strong ~100 Hz **sub-octave** (G#2).
   - 4-band energy balance (80–300 / 300–800 / 800–2500 / 2.5–9 k) →
     **18 / 30 / 41 / 7 %** (revealed the body had a full root + upper-mid
     presence the recreation lacked).
   - Per-band onset-envelope decay → mid-band decays to 25 % in ~60–100 ms;
     a separate **bright 3–8 kHz noise "snap"** at the attack (the "snare" layer).
3. **Resynthesize**: pick `synth_brass`, set params, render, *measure the same
   metrics*, and diff against the target. Added a `perc_decay` envelope mode and
   a noise-snap layer to close the gap.
4. **Variant-explore**: sweep the perceptually meaningful axes (snare-ness,
   staccato, body fullness) → render a spread → compare side-by-side. Final
   `G_full_root` variant: **84 % percussive, 2596 Hz, root 15 %** vs target
   82 / 2542 / 18.
5. **A/B**: waveform + spectrogram montage, source on top, recreation below.

Artifacts from that session that the tool generalizes:
`house/strike_intro.py` (the recreation), `house/strike_variants.py` (the
variant explorer — a hand-rolled prototype of the Variant Grid panel),
`inspiration/black_box/intro_report.md` (the target characterization).

---

## Goal / Scope

Build a **desktop GUI — "Sound-Match Studio"** — that turns reference-sound
reverse-engineering into an interactive loop:

> **Load a reference → isolate the part → characterize it → rebuild it with a
> forge instrument → score the match → iterate / sweep variants → export.**

In scope:

- Reference loading + waveform/spectrogram display with a **time-range
  selection** (zoom to the bars that matter).
- **Stem separation** (demucs) with per-stem audition, solo, and "use this stem
  as the target."
- A **Target Characterization** panel: the metric battery above, computed on the
  selected stem/region, presented as numbers + plots.
- A **Patch Editor**: pick a forge instrument, auto-built parameter sliders
  (from `ParamSchema`), live re-render of the matched phrase.
- A **Match Scorecard**: render the patch, compute the *same* metrics, show a
  side-by-side diff and a single aggregate distance.
- A **Variant Grid**: declare an axis (1–2 params or a named macro), render N
  variants, audition/compare/score them in a grid; promote a winner.
- An **A/B Viewer**: synced playback + stacked spectrograms (reference vs
  candidate), with the montage exportable as PNG.
- A **Match Project** file capturing reference, region, target metrics, instrument
  id, params, and variants — reproducible and re-openable.

Out of scope (defer / belongs to other plans): multi-track arrangement, MIDI
input, recording, full mixing (Plans 3/4). This tool produces *one well-matched
instrument patch / short phrase*, which those tools then consume.

Non-goals: automatic perfect inversion. The tool is an **assistant for a human
ear** — metrics guide, they don't decide. Keep humans in the loop with audition
and A/B everywhere.

---

## Core concepts captured from the session

These are the reusable ideas the GUI must encode (each became a metric or panel):

| Concept | What it is | Where it lives in the tool |
|---|---|---|
| **Stem isolation first** | Whole-mix analysis lies; isolate the part before characterizing | Stems panel, "set as target" |
| **Percussive ratio (HPSS)** | harmonic vs percussive energy — distinguishes a *stab* from a *sustain* | Target metrics + scorecard |
| **Spectral centroid** | overall brightness | metrics + scorecard |
| **Band balance** | energy in 80–300 / 300–800 / 800–2500 / 2.5–9 k — catches "thin root / honky mid / no presence" | metrics + scorecard (bar diff) |
| **Onset rhythm** | count, density, median IOI → grid placement | metrics; seeds the phrase |
| **FFT chord/peak picking** | the actual notes/voicing incl. sub-octaves | metrics; seeds the notes |
| **Per-band decay envelope** | how fast each band decays → envelope shape, layered transients | metrics; informs `perc_decay`, snap |
| **Two-layer decomposition** | tonal body + noise/transient "snap" | patch editor (layer list) |
| **Patch matching loop** | render → measure same metrics → diff | scorecard |
| **Variant explorer** | sweep an axis, render a spread, compare | Variant Grid |
| **Visual A/B** | stacked spectrograms + synced playback | A/B Viewer |

---

## Architecture

```
                ┌──────────────────────── Sound-Match Studio (GUI) ───────────────────────┐
                │  Reference  │  Stems  │  Target Metrics  │  Patch Editor  │  Variant Grid │
                │  + selection│  panel  │  + plots         │  + A/B viewer  │  + scorecard  │
                └───────┬─────────┬───────────┬────────────────────┬───────────────────────┘
                        │         │           │                    │
            ┌───────────▼───┐ ┌───▼─────┐ ┌───▼──────────┐  ┌──────▼───────────────┐
            │ inspector/    │ │ demucs  │ │ analysis_    │  │ forge/instruments/   │
            │ features.py   │ │ (separa-│ │ metrics.py   │  │ registry.py          │
            │ transcription │ │ tion.py)│ │ (NEW shared) │  │  → ParamSchema → UI  │
            └───────────────┘ └─────────┘ └──────────────┘  │ forge/core (render)  │
                                                             └──────────────────────┘
```

- **Analysis backend** = the existing `inspector` modules. Factor the metric
  functions used this session into a shared `inspector/analysis_metrics.py`
  (percussive ratio, centroid, band balance, onset stats, FFT peaks, per-band
  decay) so *both* the CLI report and the GUI scorecard call the same code and
  numbers never disagree. **This is the keystone:** target and candidate must be
  measured by identical functions.
- **Synthesis backend** = `forge` instruments via `registry.py`. The GUI never
  hard-codes a patch; it reads `ParamSchema` to build controls and calls the
  registered render fn. New instrument *capabilities* discovered while matching
  (e.g. `synth_brass`'s `perc_decay`, the noise-snap layer) are contributed back
  to the instrument, not the GUI.
- **GUI layer** = reuse `forge/ui/` primitives where they fit (`ab_compare.py`
  is literally an A/B comparator; `instrument_panel.py` already renders
  ParamSchema sliders). Add the panels unique to matching (Stems, Target
  Metrics, Variant Grid, Scorecard).

---

## UI layout / panels

1. **Reference panel** — load audio; waveform + spectrogram; draggable
   **time-range selection** (mirrors `--start/--end`); transport. Selection is
   the unit everything downstream operates on.
2. **Stems panel** — "Separate" (demucs on the selection only — a 9 s clip is
   ~10 s on CPU). Four stem rows (drums/bass/other/vocals) with solo/mute,
   mini-waveform, RMS, and a **"Set as target"** button. Silent stems greyed.
3. **Target Metrics panel** — runs the metric battery on the target
   stem+selection: percussive %, centroid, band-balance bars, onset table
   (count/density/IOI), detected chord/peaks (with octave), per-band decay
   sparklines, two-layer hint. "Seed phrase from this" button → fills the patch
   editor's note/rhythm grid from onsets + detected pitches.
4. **Patch Editor** — instrument dropdown (from registry, grouped by family);
   auto-built sliders; a **layer list** (e.g. tonal stab + noise snap) so
   multi-layer sounds are explicit; live re-render of the matched phrase on edit
   (debounced). Seedable RNG field for determinism.
5. **Match Scorecard** — renders the patch over the same phrase, computes the
   identical metrics, shows **target vs candidate vs Δ** per metric and a single
   weighted aggregate distance. Color the worst-offending band/metric so the
   user knows what to chase next (this session: "root too thin / honk too high").
6. **Variant Grid** — declare a sweep: pick 1–2 params (or a named macro like
   *snare-ness*, *staccato*, *body fullness*) and a range/list → render N
   variants → grid of cards each with spectrogram thumb, key metrics, score,
   play button. Promote one to the Patch Editor. (Generalizes
   `house/strike_variants.py`.)
7. **A/B Viewer** — synced/toggled playback of target vs candidate; stacked
   spectrograms (source on top); export montage PNG (as produced manually this
   session).

---

## Data model — the "Match Project"

A single JSON/TOML file, reproducible end to end:

```
match_project:
  reference: { path, sha, sr }
  selection: { start_s, end_s }
  target:    { stem: "other", metrics: {...cached...} }
  phrase:    { bpm, grid, notes: [(t, [midi...])...] }   # from onset+pitch seeding
  patch:     { instrument_id, params: {...}, layers: [...], seed }
  variants:  [ { name, axis, params_override, score } ... ]
  score:     { per_metric: {...}, aggregate: float }
```

Opening a project re-derives every number from the same code → no stale results.
Export targets: the patch as a runnable snippet (like `house/strike_intro.py`),
the stems, the A/B montage, and a markdown characterization (like
`inspiration/.../intro_report.md`).

---

## Implementation phases (start small, each independently useful)

- **Phase 0 — Shared metrics module.** Extract `inspector/analysis_metrics.py`
  (percussive ratio, centroid, band balance, onset stats, FFT peaks, per-band
  decay) from the snippets used this session; unit-test against the Strike It Up
  numbers as fixtures (82 % perc, 2542 Hz, bands 18/30/41/7). *No GUI yet — this
  is the foundation both CLI and GUI share.*
- **Phase 1 — Read-only inspector GUI.** Reference panel + Stems panel + Target
  Metrics panel. Load, select a range, separate, audition stems, see the metric
  battery + plots. Already valuable as a visual front-end to the CLI.
- **Phase 2 — Patch Editor + Scorecard.** Registry-driven sliders, live render,
  same-metrics diff. The first time you can *match* inside the tool.
- **Phase 3 — Variant Grid.** Param/macro sweeps with scored, auditionable cards.
- **Phase 4 — A/B Viewer + Project save/load + exporters.** Synced playback,
  spectrogram montage export, runnable-snippet + markdown-report export.
- **Phase 5 (stretch) — Assisted matching.** A "suggest" button that does a
  coarse param search minimizing the aggregate metric distance (the manual
  `itertools.product` sweep from this session), proposing a starting patch the
  user then refines by ear. Optionally pitch/onset seeding becomes one click.

---

## Reuse / what already exists

- `inspector/separation.py`, `transcription.py`, `features.py` — analysis +
  demucs (note: **torchaudio.save is broken here — write WAVs via soundfile**;
  CPU only; `htdemucs` sources = drums/bass/other/vocals).
- `forge/instruments/registry.py` + `ParamSchema` — auto-slider source of truth.
- `forge/ui/ab_compare.py`, `instrument_panel.py`, `window.py` — UI primitives.
- `house/strike_variants.py` — working prototype of the Variant Grid logic
  (Variant dataclass, render-lead, measure → table).
- `house/strike_intro.py` — example of the export target (runnable patch snippet).

## Tech stack options (decide at Phase 1)

- **PySide/PyQt + pyqtgraph** — fast native plotting, good for live spectrograms;
  matches a desktop tool; likely what `forge/ui/` already leans on (verify).
- **Web (FastAPI + React/Canvas)** — shareable, but audio/DSP round-trips and
  spectrogram rendering are heavier. Prefer native unless sharing is a goal.
- Keep all DSP in Python (numpy/scipy/librosa) on a worker thread; the UI only
  orchestrates and plots. Renders are fast (a 9 s phrase is sub-second);
  separation is the only slow op (~10 s) → run async with a progress bar.

## Dependencies / assumptions

- Reuses the live `inspector` and `forge` packages; if `forge/ui` conventions
  conflict, prefer aligning with them over inventing new ones.
- demucs/torch present (graceful deg: Stems panel disabled with a clear message
  if not — mirrors the CLI's existing fallback).
- Determinism: every render carries a seed; the project file is the source of
  truth so results are reproducible across sessions.

## Open questions (for the user, before Phase 1)

- Native (Qt) vs web — driven by whether sharing matched patches matters.
- Should the tool target **single-shot instruments** only, or also short
  **phrases/loops** (the Strike It Up case is really a 9 s phrase)? Plan assumes
  phrase-capable from the start (selection-based), which is strictly more useful.
- How tightly to couple with Plans 3/4: export a patch they import, or embed this
  as a "match" mode inside the larger DAW later? (Plan assumes standalone first,
  clean export second.)
