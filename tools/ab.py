#!/usr/bin/env python3
"""ab.py — build an ABAB comparison file from two renders.

Same timeline, alternating source: chunk 1 from A, chunk 2 from B,
chunk 3 from A ... so the difference lands every `--bars` bars instead
of you switching files.  Levels are RMS-matched (B to A) unless
--no-match; 5 ms crossfades at the switches.

    python3 tools/ab.py A.wav B.wav                # 2-bar chunks at 122 BPM
    python3 tools/ab.py A.wav B.wav --bars 4 --bpm 147 --out /tmp/ab.wav
"""
from __future__ import annotations

import argparse
import pathlib
import wave

import numpy as np


def read(path):
    with wave.open(str(path), "rb") as w:
        sr, ch, n = w.getframerate(), w.getnchannels(), w.getnframes()
        x = np.frombuffer(w.readframes(n), dtype=np.int16).reshape(-1, ch) / 32768.0
    if ch == 1:
        x = np.repeat(x, 2, axis=1)
    return sr, x


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--bars", type=float, default=2.0, help="chunk length in bars (default 2)")
    ap.add_argument("--bpm", type=float, default=122.0)
    ap.add_argument("--out", help="default: <A>_AB_<B>.wav next to A")
    ap.add_argument("--no-match", action="store_true", help="keep the files' own levels")
    args = ap.parse_args()

    sr, a = read(args.a)
    sr_b, b = read(args.b)
    assert sr == sr_b, f"sample rates differ: {sr} vs {sr_b}"
    n = min(len(a), len(b))
    a, b = a[:n], b[:n]
    if not args.no_match:
        b *= (np.sqrt(np.mean(a ** 2)) + 1e-12) / (np.sqrt(np.mean(b ** 2)) + 1e-12)
    chunk = int(args.bars * 4 * 60.0 / args.bpm * sr)
    xf = int(0.005 * sr)
    ramp = np.linspace(0, 1, xf)[:, None]
    out = np.empty_like(a)
    print(f"chunk {args.bars:g} bars = {chunk / sr:.2f} s at {args.bpm:g} BPM; {n / sr:.1f} s total")
    for i, i0 in enumerate(range(0, n, chunk)):
        src, name = (a, "A") if i % 2 == 0 else (b, "B")
        i1 = min(n, i0 + chunk)
        if i1 - i0 <= xf:                                # a trailing sliver: A keeps it
            out[i0:i1] = a[i0:i1]
            break
        out[i0:i1] = src[i0:i1]
        if i0 and i1 - i0 > xf:                          # crossfade the switch
            prev = a if name == "B" else b
            out[i0:i0 + xf] = prev[i0:i0 + xf] * (1 - ramp) + src[i0:i0 + xf] * ramp
        print(f"  {i0 / sr:6.2f}s  {name}")
    peak = np.max(np.abs(out)) + 1e-12
    if peak > 0.95:
        out *= 0.95 / peak
    path = pathlib.Path(args.out) if args.out else pathlib.Path(args.a).with_name(
        f"{pathlib.Path(args.a).stem}_AB_{pathlib.Path(args.b).stem}.wav")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes())
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
