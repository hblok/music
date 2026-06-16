"""collect_stats — scan a directory of WAV files and write a stats JSON.

Usage:
    python -m forge.tools.collect_stats <wav_dir> <output_json>

For each WAV found it records: duration, sample rate, channel count, peak
amplitude, overall RMS, and per-section RMS (8 equal sections).  The JSON
is written to <output_json> and is the machine-readable companion to the
listening-approved baseline in reference/.
"""

import json
import sys
import wave
from pathlib import Path

import numpy as np


def wav_stats(path: Path) -> dict:
    """Return a stats dict for a single WAV file."""
    with wave.open(str(path), "rb") as wf:
        sr = wf.getframerate()
        n_channels = wf.getnchannels()
        n_frames = wf.getnframes()
        sampwidth = wf.getsampwidth()
        raw = wf.readframes(n_frames)

    if sampwidth == 2:
        dtype, scale = np.int16, 32768.0
    elif sampwidth == 4:
        dtype, scale = np.int32, 2147483648.0
    else:
        raise ValueError(f"Unsupported sample width {sampwidth} in {path}")

    data = np.frombuffer(raw, dtype=dtype).reshape(-1, n_channels).astype(np.float64)
    data /= scale

    duration = n_frames / sr
    peak = float(np.max(np.abs(data)))
    rms = float(np.sqrt(np.mean(data ** 2)))

    n_sections = 8
    section_size = len(data) // n_sections
    section_rms = []
    for i in range(n_sections):
        chunk = data[i * section_size : (i + 1) * section_size]
        section_rms.append(float(np.sqrt(np.mean(chunk ** 2))))

    return {
        "duration": round(duration, 3),
        "sr": sr,
        "n_channels": n_channels,
        "peak": round(peak, 6),
        "rms": round(rms, 6),
        "section_rms": [round(x, 6) for x in section_rms],
    }


def collect(wav_dir: Path, output_json: Path) -> dict:
    """Scan *wav_dir* for .wav files, compute stats, write *output_json*."""
    wav_dir = Path(wav_dir)
    output_json = Path(output_json)

    wavs = sorted(wav_dir.glob("*.wav"))
    if not wavs:
        print(f"No .wav files found in {wav_dir}", file=sys.stderr)

    stats: dict = {}
    for wav in wavs:
        try:
            stats[wav.name] = wav_stats(wav)
            print(f"  {wav.name}: {stats[wav.name]['duration']:.1f}s  "
                  f"peak={stats[wav.name]['peak']:.4f}  "
                  f"rms={stats[wav.name]['rms']:.4f}")
        except Exception as exc:
            print(f"  ERROR {wav.name}: {exc}", file=sys.stderr)

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(stats, indent=2))
    print(f"\nWrote {len(stats)} entries to {output_json}")
    return stats


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python -m forge.tools.collect_stats <wav_dir> <output_json>")
        sys.exit(1)
    collect(Path(sys.argv[1]), Path(sys.argv[2]))


if __name__ == "__main__":
    main()
