"""
Music Inspector — CLI entry point.

Usage:
    python -m inspector.analyse <file> [options]

Options:
    --plots          Save PNG plots alongside the report
    --out FILE       Write text report to FILE (also printed to stdout)
    --sr INT         Analysis sample rate in Hz (default: 22050)
    --sections N     Force N structural sections (default: auto ~1 per 3 min)

Example:
    python -m inspector.analyse /path/to/track.mp3 --plots --out report.txt
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from . import features, report, plots


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyse an audio file for musical structure, harmony, timbre, and rhythm.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("file",             help="Audio file (MP3, WAV, FLAC, OGG, …)")
    parser.add_argument("--plots",          action="store_true", help="Save PNG plots")
    parser.add_argument("--out",            metavar="FILE",      help="Write report to FILE")
    parser.add_argument("--sr",             type=int, default=22050, metavar="HZ",
                        help="Analysis sample rate (default 22050)")
    parser.add_argument("--sections",       type=int, default=None, metavar="N",
                        help="Force N sections (default: auto)")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        sys.exit(f"Error: file not found: {path}")

    t_start = time.perf_counter()

    # ── Load ──────────────────────────────────────────────────────────────────
    print(f"\nLoading  {path.name}", flush=True)
    audio = features.load_audio(str(path), sr=args.sr)
    print(f"         {audio['duration']:.0f} s at {audio['sr']} Hz mono", flush=True)

    # ── Librosa analyses (all use the same in-memory audio) ───────────────────
    _step("Tempo & rhythm      (librosa)")
    tempo_data = features.analyse_tempo(audio)

    _step("Structural sections (librosa)")
    structure_data = features.analyse_structure(audio, k=args.sections)
    print(f"         {structure_data['n_sections']} sections", flush=True)

    _step("Timbre per section  (librosa)")
    timbre_data = features.analyse_timbre(audio, structure_data["boundaries_sec"])

    _step("Key & harmony       (librosa)")
    harmony_data = features.analyse_harmony(audio)

    # ── Essentia (single extra load at 44100 Hz for key + BPM) ───────────────
    _step("Key + BPM           (essentia @ 44100 Hz)")
    es_data = features.analyse_essentia(str(path))

    # Merge essentia results into the relevant dicts
    tempo_data["bpm_essentia"]   = es_data["bpm_essentia"]
    tempo_data["bpm_confidence"] = es_data["bpm_confidence"]
    harmony_data["key_essentia"]          = es_data["key_essentia"]
    harmony_data["mode_essentia"]         = es_data["mode_essentia"]
    harmony_data["key_strength_essentia"] = es_data["key_strength_essentia"]

    # ── Render ────────────────────────────────────────────────────────────────
    results = {
        "path":      str(path),
        "audio":     audio,
        "tempo":     tempo_data,
        "harmony":   harmony_data,
        "structure": structure_data,
        "timbre":    timbre_data,
    }

    text = report.render(results)
    print("\n" + text, flush=True)

    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"\nReport written to {args.out}", flush=True)

    if args.plots:
        out_dir = path.parent / (path.stem + "_inspector")
        out_dir.mkdir(exist_ok=True)
        _step(f"Generating plots  → {out_dir}/")
        saved = plots.save_all(results, out_dir)
        for p in saved:
            print(f"  {p}", flush=True)

    elapsed = time.perf_counter() - t_start
    print(f"\nDone in {elapsed:.1f} s", flush=True)


def _step(msg: str) -> None:
    print(f"\n▶ {msg}", flush=True)


if __name__ == "__main__":
    main()
