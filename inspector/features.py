"""
Audio feature extraction for the music inspector.

All public functions take either an `audio` dict (from load_audio) or a file path,
and return plain dicts / lists of dicts — no numpy arrays leak out.
"""

from __future__ import annotations

import numpy as np
import librosa
from typing import Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# Krumhansl-Kessler tonal hierarchy profiles (normalised)
_KK_MAJOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
_KK_MINOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
_KK_MAJOR = _KK_MAJOR / _KK_MAJOR.sum()
_KK_MINOR = _KK_MINOR / _KK_MINOR.sum()

# Hop lengths for different analysis resolutions
_HOP_FINE   = 512    # tempo, onsets, per-section spectra
_HOP_COARSE = 4096   # structure, chromagram over whole track


# ---------------------------------------------------------------------------
# Audio loading
# ---------------------------------------------------------------------------

def load_audio(path: str, sr: int = 22050) -> dict:
    """Load and resample to mono at `sr` Hz. Returns audio dict."""
    y, sr_out = librosa.load(path, sr=sr, mono=True)
    return {
        "path": path,
        "y": y,
        "sr": sr_out,
        "duration": float(len(y) / sr_out),
    }


# ---------------------------------------------------------------------------
# Tempo & rhythm  (librosa)
# ---------------------------------------------------------------------------

def analyse_tempo(audio: dict) -> dict:
    """BPM, beat tracking, per-30s tempo windows."""
    y, sr = audio["y"], audio["sr"]

    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=_HOP_FINE)

    # Global BPM
    global_bpm = float(librosa.feature.tempo(
        onset_envelope=onset_env, sr=sr, hop_length=_HOP_FINE
    )[0])

    # Beat grid
    _, beat_frames = librosa.beat.beat_track(
        onset_envelope=onset_env, sr=sr, hop_length=_HOP_FINE, bpm=global_bpm
    )
    beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=_HOP_FINE)

    # Tempo in 30-second windows
    window_frames = max(1, int(30.0 * sr / _HOP_FINE))
    tempo_over_time: list[dict] = []
    t = 0.0
    i = 0
    while i < len(onset_env):
        chunk = onset_env[i : i + window_frames]
        w_bpm = float(librosa.feature.tempo(
            onset_envelope=chunk, sr=sr, hop_length=_HOP_FINE
        )[0])
        tempo_over_time.append({"t_start": t, "bpm": w_bpm})
        i += window_frames
        t += 30.0

    bpms = [w["bpm"] for w in tempo_over_time]

    return {
        "bpm": global_bpm,
        "bpm_std": float(np.std(bpms)) if bpms else 0.0,
        "beat_count": int(len(beat_times)),
        "beat_times": beat_times.tolist(),
        "tempo_over_time": tempo_over_time,
        # essentia fields populated later by analyse_essentia()
        "bpm_essentia": None,
        "bpm_confidence": None,
    }


# ---------------------------------------------------------------------------
# Key, harmony, chroma  (librosa)
# ---------------------------------------------------------------------------

def analyse_harmony(audio: dict) -> dict:
    """Key via Krumhansl-Kessler, chroma profile, dominant note per minute."""
    y, sr = audio["y"], audio["sr"]

    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=_HOP_COARSE)
    chroma_mean = chroma.mean(axis=1)

    key, mode, corr = _kk_key(chroma_mean)

    # Rank notes by mean chroma energy
    chroma_norm = chroma_mean / (chroma_mean.max() + 1e-10)
    ranked = sorted(range(12), key=lambda i: -chroma_norm[i])
    top_notes = [(_NOTES[i], float(chroma_norm[i])) for i in ranked]

    # Dominant note per minute
    frames_per_min = max(1, int(60.0 * sr / _HOP_COARSE))
    chroma_over_time: list[dict] = []
    t = 0.0
    for i in range(0, chroma.shape[1], frames_per_min):
        chunk = chroma[:, i : i + frames_per_min]
        dominant = _NOTES[int(chunk.mean(axis=1).argmax())]
        chroma_over_time.append({"t_start": t, "dominant_note": dominant})
        t += 60.0

    return {
        "key": key,
        "mode": mode,
        "key_corr": float(corr),
        "chroma_mean": chroma_mean.tolist(),
        "top_notes": top_notes,
        "chroma_over_time": chroma_over_time,
        # essentia fields populated later
        "key_essentia": None,
        "mode_essentia": None,
        "key_strength_essentia": None,
    }


def _kk_key(chroma_mean: np.ndarray) -> tuple[str, str, float]:
    """Krumhansl-Kessler key estimation from 12-dim chroma vector."""
    cn = chroma_mean / (chroma_mean.sum() + 1e-10)
    best_key, best_mode, best_corr = "C", "major", -np.inf
    for i in range(12):
        for profile, mode in [(_KK_MAJOR, "major"), (_KK_MINOR, "minor")]:
            corr = float(np.corrcoef(cn, np.roll(profile, i))[0, 1])
            if corr > best_corr:
                best_corr, best_key, best_mode = corr, _NOTES[i], mode
    return best_key, best_mode, best_corr


# ---------------------------------------------------------------------------
# Structure segmentation
# ---------------------------------------------------------------------------

def analyse_structure(audio: dict, k: Optional[int] = None) -> dict:
    """Segment the track into sections via agglomerative clustering on MFCCs + chroma."""
    y, sr = audio["y"], audio["sr"]

    mfcc   = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, hop_length=_HOP_COARSE)
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=_HOP_COARSE)
    feat   = np.vstack([
        librosa.util.normalize(mfcc,   axis=1),
        librosa.util.normalize(chroma, axis=1),
    ])

    n_frames = feat.shape[1]
    if k is None:
        # ~1 section per 3 minutes, clamped [5, 20]
        k = max(5, min(20, int(audio["duration"] / 180)))
    k = min(k, n_frames - 1)

    bounds = librosa.segment.agglomerative(feat, k=k)
    bounds = np.unique(np.concatenate([[0], bounds, [n_frames]]))
    bounds_sec = librosa.frames_to_time(bounds, sr=sr, hop_length=_HOP_COARSE).tolist()

    return {
        "n_sections": len(bounds) - 1,
        "boundaries_frames": bounds.tolist(),
        "boundaries_sec": bounds_sec,
    }


# ---------------------------------------------------------------------------
# Per-section timbre
# ---------------------------------------------------------------------------

def analyse_timbre(audio: dict, boundaries_sec: list[float]) -> list[dict]:
    """Spectral features for each section defined by boundaries_sec."""
    y, sr = audio["y"], audio["sr"]
    sections: list[dict] = []

    freqs = librosa.fft_frequencies(sr=sr)
    bass_mask = freqs < 250
    mid_mask  = (freqs >= 250) & (freqs < 4000)
    high_mask = freqs >= 4000

    for i in range(len(boundaries_sec) - 1):
        t0 = boundaries_sec[i]
        t1 = boundaries_sec[i + 1]
        s0 = int(t0 * sr)
        s1 = int(t1 * sr)
        seg = y[s0:s1]

        if len(seg) < int(sr * 0.5):
            continue

        rms    = float(np.sqrt(np.mean(seg ** 2)))
        rms_db = float(20 * np.log10(rms + 1e-10))

        S     = np.abs(librosa.stft(seg, hop_length=_HOP_FINE))
        total = S.sum() + 1e-10

        centroid  = float(librosa.feature.spectral_centroid(S=S, sr=sr).mean())
        bandwidth = float(librosa.feature.spectral_bandwidth(S=S, sr=sr).mean())
        rolloff   = float(librosa.feature.spectral_rolloff(S=S, sr=sr, roll_percent=0.85).mean())
        zcr       = float(librosa.feature.zero_crossing_rate(seg, hop_length=_HOP_FINE).mean())

        bass_ratio = float(S[bass_mask, :].sum() / total)
        mid_ratio  = float(S[mid_mask,  :].sum() / total)
        high_ratio = float(S[high_mask, :].sum() / total)

        # Onset density
        onset_env = librosa.onset.onset_strength(S=librosa.power_to_db(S ** 2), sr=sr, hop_length=_HOP_FINE)
        n_onsets  = len(librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, hop_length=_HOP_FINE))
        onset_rate = float(n_onsets / max(t1 - t0, 0.001))

        sections.append({
            "idx":        i + 1,
            "t_start":    t0,
            "t_end":      t1,
            "duration":   t1 - t0,
            "rms_db":     rms_db,
            "centroid_hz":  centroid,
            "bandwidth_hz": bandwidth,
            "rolloff_hz":   rolloff,
            "zcr":          zcr,
            "bass_ratio":   bass_ratio,
            "mid_ratio":    mid_ratio,
            "high_ratio":   high_ratio,
            "onset_rate":   onset_rate,
        })

    return sections


# ---------------------------------------------------------------------------
# Essentia analysis  (key + BPM in a single audio load at 44100 Hz)
# ---------------------------------------------------------------------------

def analyse_essentia(path: str) -> dict:
    """Run essentia KeyExtractor + RhythmExtractor2013 from one 44100 Hz load.

    Returns a dict that is merged into tempo_data and harmony_data by the caller.
    If essentia fails, all values are None so the report can still render.
    """
    result: dict = {
        "bpm_essentia": None, "bpm_confidence": None,
        "key_essentia": None, "mode_essentia": None, "key_strength_essentia": None,
    }
    try:
        import essentia.standard as es  # noqa: PLC0415

        loader = es.MonoLoader(filename=str(path), sampleRate=44100)
        audio  = loader()

        key_ext = es.KeyExtractor()
        key, scale, strength = key_ext(audio)
        result["key_essentia"]          = str(key)
        result["mode_essentia"]         = str(scale)
        result["key_strength_essentia"] = float(strength)

        rx = es.RhythmExtractor2013(method="multifeature")
        bpm, _beats, confidence, _, _ = rx(audio)
        result["bpm_essentia"]   = float(bpm)
        result["bpm_confidence"] = float(confidence)

        del audio
    except Exception:
        pass

    return result


# ---------------------------------------------------------------------------
# Heuristic section labels and instrument hints
# ---------------------------------------------------------------------------

def label_section(sec: dict, rms_mean: float, rms_std: float, onset_mean: float) -> str:
    rms   = sec["rms_db"]
    onset = sec["onset_rate"]
    quiet = rms   < rms_mean   - 0.5 * rms_std
    loud  = rms   > rms_mean   + 0.5 * rms_std
    dense = onset > onset_mean * 1.3
    sparse = onset < onset_mean * 0.7

    if quiet and sparse:
        return "INTRO / OUTRO"
    if quiet:
        return "BREAK"
    if loud and dense:
        return "DROP / PEAK"
    if loud and sparse:
        return "BREAKDOWN"
    if dense:
        return "BUILD"
    return "MAIN"


def get_instrument_hints(sections: list[dict]) -> list[str]:
    if not sections:
        return ["(no sections analysed)"]

    avg_c = np.mean([s["centroid_hz"] for s in sections])
    avg_b = np.mean([s["bass_ratio"]  for s in sections])
    avg_z = np.mean([s["zcr"]         for s in sections])
    avg_o = np.mean([s["onset_rate"]  for s in sections])

    hints: list[str] = []

    if avg_b > 0.30:
        hints.append(f"Heavy sub-bass / kick ({avg_b*100:.0f}% energy below 250 Hz)")
    elif avg_b > 0.18:
        hints.append(f"Moderate bass content ({avg_b*100:.0f}% below 250 Hz)")
    else:
        hints.append(f"Thin low end ({avg_b*100:.0f}% below 250 Hz) — minimal kick/bass")

    if avg_c < 1200:
        hints.append(f"Dark tonal character (centroid {avg_c:.0f} Hz) — heavy low/mid emphasis")
    elif avg_c < 2500:
        hints.append(f"Balanced spectrum (centroid {avg_c:.0f} Hz) — mids dominant")
    else:
        hints.append(f"Bright / airy character (centroid {avg_c:.0f} Hz) — prominent hi-hats or bright leads")

    if avg_z > 0.12:
        hints.append(f"High zero-crossing rate ({avg_z:.3f}) — strong cymbal / snare / noise content")
    elif avg_z > 0.06:
        hints.append(f"Moderate percussive texture (ZCR {avg_z:.3f})")

    if avg_o > 10:
        hints.append(f"Very dense texture ({avg_o:.1f} events/sec) — fast arpeggios or complex percussion")
    elif avg_o > 5:
        hints.append(f"Active arrangement ({avg_o:.1f} events/sec) — regular percussion or sequencing")
    elif avg_o > 2:
        hints.append(f"Moderate event density ({avg_o:.1f} events/sec)")
    else:
        hints.append(f"Sparse / ambient texture ({avg_o:.1f} events/sec) — pads, drones, slow melodies")

    return hints
