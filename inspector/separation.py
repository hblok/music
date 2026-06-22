"""
Stem separation for the music inspector.

Uses the demucs Python API (htdemucs model) to split an audio file into
drums / bass / other / vocals stems.  torchaudio.save is broken in this
environment (TorchCodec ImportError), so stems are kept in-memory as
numpy arrays and only written to disk via soundfile if --stems-out is given.

Graceful degradation: if demucs or torch are not installed, separate_stems()
returns None and sets a human-readable reason string.
"""

from __future__ import annotations

import numpy as np
from pathlib import Path
from typing import Optional


def separate_stems(
    path: str,
    offset: float = 0.0,
    end: Optional[float] = None,
    sr: int = 22050,
    stems_out_dir: Optional[str] = None,
) -> tuple[Optional[dict], str]:
    """Separate *path* into demucs stems.

    Parameters
    ----------
    path        : audio file to separate
    offset, end : time range in seconds (already-applied by the caller via
                  librosa.load; we re-load only this range at model.samplerate)
    sr          : analysis sample rate (used when down-mixing stems for transcription)
    stems_out_dir : if given, write each stem as a WAV into this directory

    Returns
    -------
    (stems_dict, reason)
        stems_dict: None on failure; otherwise a dict with keys
            'names'   : list of stem names e.g. ['drums','bass','other','vocals']
            'sr'      : sample rate of raw stereo stems (= model.samplerate, 44100)
            'sr_mono' : analysis sr used for mono down-mixes
            <name>_stereo : (2, N) float32 numpy array at model.samplerate
            <name>_mono   : (N,) float32 numpy array at sr_mono  (for transcription)
        reason: empty string on success, error/skip message on failure
    """
    # ── lazy imports ─────────────────────────────────────────────────────────
    try:
        import torch
        import librosa
        from demucs.pretrained import get_model
        from demucs.apply import apply_model
    except ImportError as exc:
        return None, f"Stem separation unavailable: {exc}"

    try:
        # Load the demucs model (downloads & caches on first use)
        model = get_model("htdemucs")
        model.eval()

        model_sr = model.samplerate  # typically 44100

        # Load file at model sample rate, stereo
        duration = (end - offset) if end is not None else None
        wav, _ = librosa.load(path, sr=model_sr, mono=False, offset=offset, duration=duration)
        # librosa returns (2, N) for stereo or (N,) for mono sources
        if wav.ndim == 1:
            wav = np.stack([wav, wav])

        # Normalise mix (demucs convention)
        mix = torch.tensor(wav, dtype=torch.float32)[None]  # (1, 2, N)
        ref = mix.mean(0)                                    # (2, N)
        mix = (mix - ref.mean()) / (ref.std() + 1e-8)

        with torch.no_grad():
            out = apply_model(model, mix, device="cpu", progress=False)[0]  # (S, 2, N)

        # De-normalise
        out = out * (ref.std() + 1e-8) + ref.mean()

        stem_names: list[str] = list(model.sources)  # ['drums', 'bass', 'other', 'vocals']

        result: dict = {
            "names":   stem_names,
            "sr":      model_sr,
            "sr_mono": sr,
        }

        for i, name in enumerate(stem_names):
            stereo = out[i].numpy()                          # (2, N) float32
            # Down-mix to mono at analysis sr for transcription
            mono_native = stereo.mean(axis=0)               # (N,) at model_sr
            if sr != model_sr:
                mono_resampled = librosa.resample(mono_native, orig_sr=model_sr, target_sr=sr)
            else:
                mono_resampled = mono_native

            result[f"{name}_stereo"] = stereo
            result[f"{name}_mono"]   = mono_resampled.astype(np.float32)

        # Optionally write stems to disk via soundfile
        if stems_out_dir is not None:
            _write_stems(result, stem_names, model_sr, stems_out_dir, path)

        return result, ""

    except Exception as exc:
        return None, f"Stem separation failed: {exc}"


def _write_stems(
    result: dict,
    stem_names: list[str],
    sr: int,
    out_dir: str,
    source_path: str,
) -> None:
    """Write each stem as a stereo WAV using soundfile (NOT torchaudio)."""
    try:
        import soundfile as sf
    except ImportError:
        print("  [warn] soundfile not available — stems not written to disk")
        return

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    stem_base = Path(source_path).stem

    for name in stem_names:
        stereo = result[f"{name}_stereo"]          # (2, N)
        wav_path = out_path / f"{stem_base}_{name}.wav"
        # soundfile expects (N, channels)
        sf.write(str(wav_path), stereo.T, sr, subtype="FLOAT")
        print(f"  Wrote stem: {wav_path}", flush=True)
