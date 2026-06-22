"""
Per-stem transcription for the music inspector.

  transcribe_stem(y, sr, kind, time_offset) -> dict

  kind in {'bass', 'other', 'vocals'} → pyin pitch tracking → note events
  kind == 'drums'                      → onset / rhythm analysis

Each function returns a plain dict; no numpy arrays leak out.

Graceful degradation mirrors features.analyse_essentia: all failures are
caught and an 'error' key is included so the report can still render.
"""

from __future__ import annotations

import numpy as np
import librosa
from typing import Optional

# Note names (chromatic, starting from C)
_NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Silence threshold (RMS): stems below this are considered empty
_SILENCE_RMS = 1e-3

# Minimum note event duration to keep (seconds)
_MIN_NOTE_DUR = 0.06

# pyin frame / hop parameters for transcription
_PYIN_FRAME  = 2048
_PYIN_HOP    = 256

# Frequency ranges per stem kind
_FMIN = {
    "bass":   librosa.note_to_hz("E1"),   # ~41 Hz
    "other":  librosa.note_to_hz("A2"),   # ~110 Hz
    "vocals": librosa.note_to_hz("B2"),   # ~123 Hz
}
_FMAX = {
    "bass":   librosa.note_to_hz("G4"),   # ~392 Hz  (a touch above 400)
    "other":  librosa.note_to_hz("G6"),   # ~1568 Hz (a touch below 1600)
    "vocals": librosa.note_to_hz("C6"),   # ~1047 Hz (a touch above 1000)
}


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def transcribe_stem(
    y: np.ndarray,
    sr: int,
    kind: str,
    time_offset: float = 0.0,
) -> dict:
    """Transcribe a single mono stem.

    Parameters
    ----------
    y           : mono float32 audio at sr
    sr          : sample rate
    kind        : 'drums', 'bass', 'other', or 'vocals'
    time_offset : absolute start time (seconds) — added to all timestamps

    Returns
    -------
    dict with keys depending on kind:
        silent  : True/False
        kind    : stem name
        (if silent) → only 'silent', 'kind', 'rms'
        (drums)     → onset/rhythm keys
        (melodic)   → note_events, pitch_classes, centroid_hz, ...
    """
    rms = float(np.sqrt(np.mean(y ** 2))) if len(y) > 0 else 0.0
    base = {"kind": kind, "rms": rms}

    if rms < _SILENCE_RMS:
        base["silent"] = True
        return base

    base["silent"] = False

    try:
        if kind == "drums":
            return {**base, **_transcribe_drums(y, sr, time_offset)}
        else:
            return {**base, **_transcribe_melodic(y, sr, kind, time_offset)}
    except Exception as exc:
        base["error"] = str(exc)
        return base


# ---------------------------------------------------------------------------
# Drum / rhythm analysis
# ---------------------------------------------------------------------------

def _transcribe_drums(y: np.ndarray, sr: int, time_offset: float) -> dict:
    """Onset detection + tempo for the drums stem."""
    onset_times = librosa.onset.onset_detect(y=y, sr=sr, units="time")
    onset_times_abs = (onset_times + time_offset).tolist()

    n_onsets    = len(onset_times)
    duration    = float(len(y) / sr)
    onsets_per_sec = float(n_onsets / max(duration, 1e-3))

    # Median inter-onset interval
    if n_onsets >= 2:
        ioi = float(np.median(np.diff(onset_times)))
    else:
        ioi = None

    # Beat tracking
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=_PYIN_HOP)
    try:
        tempo_est, _ = librosa.beat.beat_track(
            onset_envelope=onset_env, sr=sr, hop_length=_PYIN_HOP
        )
        tempo_est = float(tempo_est) if np.ndim(tempo_est) == 0 else float(tempo_est[0])
    except Exception:
        tempo_est = None

    return {
        "n_onsets":       n_onsets,
        "onsets_per_sec": onsets_per_sec,
        "median_ioi_s":   ioi,
        "tempo_bpm":      tempo_est,
        "onset_times":    onset_times_abs,
    }


# ---------------------------------------------------------------------------
# Melodic / harmonic transcription (pyin)
# ---------------------------------------------------------------------------

def _transcribe_melodic(
    y: np.ndarray,
    sr: int,
    kind: str,
    time_offset: float,
) -> dict:
    """pyin pitch tracking → note events + pitch-class histogram for melodic stems."""
    fmin = _FMIN.get(kind, librosa.note_to_hz("C2"))
    fmax = _FMAX.get(kind, librosa.note_to_hz("C7"))

    f0, voiced_flag, voiced_prob = librosa.pyin(
        y,
        fmin=fmin,
        fmax=fmax,
        sr=sr,
        frame_length=_PYIN_FRAME,
        hop_length=_PYIN_HOP,
    )

    times = librosa.times_like(f0, sr=sr, hop_length=_PYIN_HOP)

    # Convert voiced f0 frames to rounded MIDI numbers
    safe_f0 = np.where((voiced_flag) & (~np.isnan(f0)) & (f0 > 0), f0, np.nan)
    midi_raw = np.where(
        ~np.isnan(safe_f0),
        np.round(69.0 + 12.0 * np.log2(safe_f0 / 440.0)),
        np.nan,
    )

    # ── Build note events from runs of identical MIDI values ─────────────────
    note_events = _midi_to_events(times, midi_raw, time_offset, _MIN_NOTE_DUR)

    # ── Pitch-class histogram (duration-weighted) ─────────────────────────────
    pc_histogram = _pitch_class_histogram(midi_raw, times)

    # ── Spectral centroid ─────────────────────────────────────────────────────
    centroid = float(librosa.feature.spectral_centroid(y=y, sr=sr).mean())

    # ── Voiced frame ratio ────────────────────────────────────────────────────
    voiced_ratio = float(np.sum(voiced_flag) / max(len(voiced_flag), 1))

    return {
        "note_events":    note_events,
        "n_events":       len(note_events),
        "pitch_classes":  pc_histogram,
        "centroid_hz":    centroid,
        "voiced_ratio":   voiced_ratio,
    }


def _midi_to_events(
    times: np.ndarray,
    midi: np.ndarray,
    time_offset: float,
    min_dur: float,
) -> list[dict]:
    """Walk frame-level MIDI array and group runs of same pitch into events."""
    events: list[dict] = []
    n = len(midi)
    i = 0
    while i < n:
        m = midi[i]
        if np.isnan(m):
            i += 1
            continue
        # Find end of this run
        j = i + 1
        while j < n and not np.isnan(midi[j]) and midi[j] == m:
            j += 1
        t_start = float(times[i]) + time_offset
        t_end   = float(times[j - 1]) + time_offset
        dur     = t_end - t_start
        if dur >= min_dur:
            midi_int = int(m)
            note_name = f"{_NOTES[midi_int % 12]}{midi_int // 12 - 1}"
            events.append({
                "t_start":   round(t_start, 3),
                "duration":  round(dur,     3),
                "midi":      midi_int,
                "note":      note_name,
            })
        i = j
    return events


def _pitch_class_histogram(
    midi: np.ndarray,
    times: np.ndarray,
) -> list[dict]:
    """Duration-weighted pitch-class histogram, sorted by weight descending."""
    # Estimate frame duration from times array
    if len(times) >= 2:
        frame_dur = float(times[1] - times[0])
    else:
        frame_dur = _PYIN_HOP / 22050.0

    counts = np.zeros(12, dtype=float)
    for m, t in zip(midi, times):
        if not np.isnan(m):
            counts[int(m) % 12] += frame_dur

    total = counts.sum()
    if total < 1e-9:
        return []

    counts /= total
    result = [
        {"note": _NOTES[i], "weight": round(float(counts[i]), 4)}
        for i in range(12)
        if counts[i] > 0.0
    ]
    result.sort(key=lambda x: -x["weight"])
    return result
