# CLAUDE.md — inspector/

Standalone audio analysis tool. No dependency on forge — runs entirely on
librosa, essentia, matplotlib, and soundfile.

## Usage

```bash
# From /repos/music/
python3 -m inspector.analyse <file.mp3> [--plots] [--out report.txt] [--sections N]

# Flags
--plots        Save 3 PNG plots alongside the report (overview, structure, harmony)
--out FILE     Write text report to FILE (also printed to stdout)
--sr HZ        Analysis sample rate (default 22050; lower = faster but coarser)
--sections N   Force N structural sections (default: auto, ~1 per 3 minutes)
--interval S   Chroma sampling interval in seconds (default: auto from duration,
               targets ~30 data points, clamped [1, 60] s; sub-second allowed)
--start S      Start time in seconds (default: 0)
--end S        End time in seconds (default: EOF); use with --start to zoom in
--separate     Run demucs stem separation + per-stem transcription.
  (--stems)    Splits audio into drums/bass/other/vocals; analyses each stem
               independently: pyin note tracking for melodic stems, onset/
               rhythm analysis for drums. Adds a STEM SEPARATION section to
               the report. Gracefully degrades to a warning if demucs/torch
               are not installed.
--stems-out DIR  Write the four separated stems as WAV files into DIR.
               Only active when --separate is also set. Uses soundfile
               (NOT torchaudio — torchaudio.save is broken in this env).
```

## File map

```
inspector/
├── analyse.py        CLI entry point — orchestrates the pipeline
├── features.py       All extraction functions (librosa + essentia)
├── separation.py     Stem separation via demucs Python API (htdemucs model)
├── transcription.py  Per-stem pyin/onset transcription
├── report.py         Text report renderer
├── plots.py          Matplotlib PNG output (overview, structure, harmony)
└── __init__.py
```

## Analysis pipeline

1. **Load** — librosa at 22050 Hz mono (kept in memory throughout)
2. **Tempo** — librosa `onset_strength` → `beat_track`; per-30s BPM windows
3. **Structure** — MFCC + chroma (hop=4096) → agglomerative segmentation
4. **Timbre** — per-section STFT: centroid, bandwidth, rolloff, ZCR, bass/mid/high ratios, onset rate
5. **Harmony** — Krumhansl-Kessler key from chroma; dominant note per minute
6. **Essentia** — single 44100 Hz load: `KeyExtractor` + `RhythmExtractor2013`; result merged into tempo/harmony dicts
7. **Stem separation** *(optional, `--separate`)* — demucs `htdemucs` model via Python API; splits only the analysed time slice (respects `--start`/`--end`); runs on CPU; a 9-second clip takes ~10 s; a full 3.5-min track is minutes. Stems are kept in-memory; optionally written to disk with `--stems-out DIR`.
8. **Per-stem transcription** *(optional, `--separate`)* — melodic stems (`bass`, `other`, `vocals`) use pyin → note events + pitch-class histogram + centroid; `drums` stem uses onset detect + beat_track → count, onsets/sec, median inter-onset interval, tempo estimate. Silent stems (RMS < 1e-3) are skipped.

Peak memory for a 1-hour file: ~950 MB (317 MB @ 22050 + 635 MB @ 44100 for the essentia pass).
Analysis time: ~3–4 minutes for a 70-minute MP3 on a single core.

## Stem separation notes

- **torchaudio.save is broken** in this container (raises `ImportError: TorchCodec is required`). Never shell out to `python -m demucs` or call `torchaudio.save`. The separation module uses the demucs Python API directly and writes WAVs with `soundfile` only.
- `torch.cuda.is_available()` is False here — all separation runs on CPU.
- The model (`htdemucs`) downloads on first use (~30 s) and then caches.
- Graceful degradation: if demucs or torch are missing, `separate_stems()` returns `None` and prints a clear warning; the rest of the pipeline is unaffected.
- `model.sources == ['drums', 'bass', 'other', 'vocals']` — vocals is often silent on instrumental tracks.

## Known quirks

- **BPM doubling**: `librosa.feature.tempo` can return 2× the true value for tracks
  with a strong half-time feel. Check the per-30s window table to find the stable value.
- **Key confidence on non-Western scales**: Persian, Arabic, and other modal scales
  use intervals not in the 12-TET chromatic grid, so KK correlation and essentia
  key strength will be low. Treat the output as "closest Western approximation."
- **Large §N segments**: if one structural section spans 15+ minutes, the features
  are too stable for the segmenter to split it. Re-run with `--sections 25` or `--sections 30`.
- **Tempo-over-time table cap**: the report displays at most 60 rows (30 min).
  The full list is in the results dict if you need it programmatically.

## Workflow: saving results

When running the inspector for a track and saving the output, write **two files**:

1. `<name>.md` — the raw `--out` report (full machine output)
2. `<name>_report.md` — a human analysis summary written by Claude after reading the output

The summary should cover: key (prefer essentia if high confidence), BPM and stability,
dominant-note timeline patterns (what harmonically changes and when), instrument hints,
and any quirks or surprises in the data. Write it as prose/bullets, not a re-paste of
the raw numbers.

## Output files (when --plots)

Saved to `<input_stem>_inspector/` next to the audio file:

| File | Contents |
|---|---|
| `overview.png` | Waveform + RMS energy + BPM over time; section boundaries in orange |
| `structure.png` | Mel spectrogram + per-section RMS bar chart + centroid line |
| `harmony.png` | Chromagram (CQT) + mean chroma profile bar chart |

## Extending

- Add a new analysis step in `features.py` as a standalone function returning a dict.
- Merge the result dict in `analyse.py` and pass it into `results`.
- Add a rendering block in `report.py` and optionally a plot in `plots.py`.
- The `results` dict passed to `report.render()` and `plots.save_all()` is the
  single source of truth — everything flows through it.
