"""inspector.metrics — shared metric battery for Sound-Match Studio.

Pure functions over ``(y: np.ndarray, sr: int)``, plus a ``Metrics`` dataclass
bundling them and a single ``characterize()`` entry point.  These formalize
the ad-hoc snippets from the worked session and ensure both the existing
inspector CLI report and the Sound-Match tool measure identically.

No Qt imports; headless and unit-testable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

_NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


# ---------------------------------------------------------------------------
# Metric functions
# ---------------------------------------------------------------------------

def percussive_ratio(y: np.ndarray, sr: int, margin: float = 3.0) -> float:
    """Percentage of percussive energy via HPSS (0–100)."""
    import librosa
    H, P = librosa.effects.hpss(y, margin=margin)
    total = np.sum(H ** 2) + np.sum(P ** 2)
    if total < 1e-12:
        return 0.0
    return float(100.0 * np.sum(P ** 2) / total)


def centroid_hz(y: np.ndarray, sr: int) -> float:
    """Spectral centroid in Hz (mean over frames)."""
    import librosa
    cent = librosa.feature.spectral_centroid(y=y, sr=sr)
    return float(cent[0].mean())


def band_balance(
    y: np.ndarray,
    sr: int,
    edges: tuple[int, ...] = (80, 300, 800, 2500, 9000),
) -> dict[str, float]:
    """Per-band energy as a percentage of total (80–9000 Hz).

    Returns dict mapping ``"80-300"`` etc. → float percentage.
    """
    sp = np.abs(np.fft.rfft(y * np.hanning(len(y))))
    f = np.fft.rfftfreq(len(y), 1.0 / sr)

    def _band_energy(lo: float, hi: float) -> float:
        return float(np.sum(sp[(f >= lo) & (f < hi)] ** 2))

    total = _band_energy(edges[0], edges[-1]) + 1e-12
    result: dict[str, float] = {}
    for i in range(len(edges) - 1):
        label = f"{edges[i]}-{edges[i + 1]}"
        result[label] = round(float(100.0 * _band_energy(edges[i], edges[i + 1]) / total), 1)
    return result


def onset_stats(
    y: np.ndarray,
    sr: int,
    hop: int = 256,
    delta: float = 0.12,
    wait: int = 3,
) -> dict[str, Any]:
    """Onset detection stats: count, density (events/sec), median IOI (s)."""
    import librosa
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    onsets = librosa.onset.onset_detect(
        onset_envelope=onset_env, sr=sr, hop_length=hop,
        delta=delta, wait=wait,
    )
    onset_times = librosa.frames_to_time(onsets, sr=sr, hop_length=hop)
    count = int(len(onset_times))
    duration = float(len(y) / sr)
    density = float(count / duration) if duration > 0 else 0.0

    if count >= 2:
        iois = np.diff(onset_times)
        median_ioi = float(np.median(iois))
    else:
        median_ioi = 0.0

    return {
        "onset_count": count,
        "onset_density": density,
        "median_ioi_s": median_ioi,
    }


def fft_peaks(
    y: np.ndarray,
    sr: int,
    fmax: float = 3000.0,
    floor_db: float = -18.0,
) -> list[tuple[float, float]]:
    """Dominant FFT peaks as ``(freq_hz, relative_db)`` sorted by energy desc.

    Only peaks below *fmax* and above *floor_db* (relative to max) are kept.
    """
    sp = np.abs(np.fft.rfft(y * np.hanning(len(y))))
    f = np.fft.rfftfreq(len(y), 1.0 / sr)
    sp_db = 20.0 * np.log10(sp + 1e-12)
    max_db = sp_db.max()

    # Mask to frequency range
    mask = f <= fmax
    sp_db_masked = sp_db[mask]
    f_masked = f[mask]

    # Find local maxima
    peaks: list[tuple[float, float]] = []
    for i in range(1, len(sp_db_masked) - 1):
        if sp_db_masked[i] > sp_db_masked[i - 1] and sp_db_masked[i] > sp_db_masked[i + 1]:
            rel_db = sp_db_masked[i] - max_db
            if rel_db >= floor_db:
                peaks.append((float(f_masked[i]), float(rel_db)))

    # Sort by energy (highest first)
    peaks.sort(key=lambda p: -p[1])
    return peaks[:20]  # cap at 20 peaks


def detect_chord(y: np.ndarray, sr: int) -> dict[str, Any]:
    """Detect chord from spectral peaks → pitch classes + MIDI incl. sub-octave.

    Returns dict with:
      - ``pitch_classes``: list of note name strings
      - ``midi``: list of MIDI note numbers
      - ``sub_octave``: bool indicating a strong tone below the chord root
    """
    peaks = fft_peaks(y, sr, fmax=4000.0, floor_db=-24.0)
    if not peaks:
        return {"pitch_classes": [], "midi": [], "sub_octave": False}

    # Convert peak frequencies to MIDI notes
    midi_notes: list[int] = []
    for freq_hz, _rel_db in peaks:
        if freq_hz < 20.0:
            continue
        midi = int(round(12.0 * np.log2(freq_hz / 440.0) + 69.0))
        midi = max(0, min(127, midi))
        midi_notes.append(midi)

    if not midi_notes:
        return {"pitch_classes": [], "midi": [], "sub_octave": False}

    # Unique pitch classes (sorted by occurrence count)
    pc_count: dict[str, int] = {}
    for m in midi_notes:
        pc = _NOTES[m % 12]
        pc_count[pc] = pc_count.get(pc, 0) + 1

    pitch_classes = sorted(pc_count, key=lambda n: -pc_count[n])[:6]

    # Sub-octave detection: a strong peak an octave below the lowest chord tone
    midi_set = set(midi_notes)
    min_midi = min(midi_notes)
    sub_octave = (min_midi - 12) in midi_set

    return {
        "pitch_classes": pitch_classes,
        "midi": sorted(set(midi_notes)),
        "sub_octave": sub_octave,
    }


def band_decay_ms(
    y: np.ndarray,
    sr: int,
    bands: tuple[tuple[float, float], ...] = ((200, 1500), (3500, 9000)),
) -> dict[str, float]:
    """Per-band time to 25 % of peak energy (in ms).

    Uses amplitude envelope via lowpass of |signal| in each band.
    """
    result: dict[str, float] = {}
    for lo, hi in bands:
        label = f"{int(lo)}-{int(hi)}"
        # Bandpass filter
        from scipy.signal import butter, sosfilt
        nyq = sr / 2.0
        lo_n = max(lo / nyq, 0.001)
        hi_n = min(hi / nyq, 0.999)
        if lo_n >= hi_n:
            result[label] = 0.0
            continue
        sos = butter(4, [lo_n, hi_n], btype="band", output="sos")
        filtered = sosfilt(sos, y)
        # Amplitude envelope
        env = np.abs(filtered)
        # Smooth
        from scipy.signal import medfilt
        if len(env) > 3:
            env = medfilt(env, kernel_size=3)
        peak_val = np.max(env)
        if peak_val < 1e-12:
            result[label] = 0.0
            continue
        threshold = 0.25 * peak_val
        # Find first sample above peak
        above = np.where(env >= threshold)[0]
        if len(above) == 0:
            result[label] = 0.0
            continue
        peak_idx = above[-1] if len(above) > 0 else 0
        # Find time from peak to first sample below threshold after peak
        after_peak = env[peak_idx:]
        below = np.where(after_peak < threshold)[0]
        if len(below) == 0:
            result[label] = float(len(after_peak) / sr * 1000.0)
        else:
            decay_samples = below[0]
            result[label] = float(decay_samples / sr * 1000.0)
    return result


# ---------------------------------------------------------------------------
# Metrics dataclass
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Metrics:
    """Immutable bundle of all measured audio characteristics."""

    percussive_ratio: float           # % (HPSS)
    centroid_hz: float
    band_balance: dict[str, float]    # "80-300", "300-800", "800-2500", "2.5-9k" → %
    onset_count: int
    onset_density: float              # events/sec
    median_ioi_s: float
    peaks: list[tuple[float, float]]  # (freq_hz, rel_db), low→high energy desc
    chord: dict[str, Any]             # {"pitch_classes": [...], "midi": [...], "sub_octave": bool}
    band_decay_ms: dict[str, float]   # per-band time to 25% of peak

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict for project save."""
        return {
            "percussive_ratio": self.percussive_ratio,
            "centroid_hz": self.centroid_hz,
            "band_balance": dict(self.band_balance),
            "onset_count": self.onset_count,
            "onset_density": self.onset_density,
            "median_ioi_s": self.median_ioi_s,
            "peaks": self.peaks,
            "chord": self.chord,
            "band_decay_ms": dict(self.band_decay_ms),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Metrics:
        """Deserialize from a plain dict (project load)."""
        return cls(
            percussive_ratio=d.get("percussive_ratio", 0.0),
            centroid_hz=d.get("centroid_hz", 0.0),
            band_balance=d.get("band_balance", {}),
            onset_count=d.get("onset_count", 0),
            onset_density=d.get("onset_density", 0.0),
            median_ioi_s=d.get("median_ioi_s", 0.0),
            peaks=d.get("peaks", []),
            chord=d.get("chord", {}),
            band_decay_ms=d.get("band_decay_ms", {}),
        )


def characterize(y: np.ndarray, sr: int) -> Metrics:
    """The single entry point: measure everything and return a Metrics bundle."""
    perc = percussive_ratio(y, sr)
    cent = centroid_hz(y, sr)
    bands = band_balance(y, sr)
    onsets = onset_stats(y, sr)
    pks = fft_peaks(y, sr)
    ch = detect_chord(y, sr)
    decay = band_decay_ms(y, sr)

    return Metrics(
        percussive_ratio=perc,
        centroid_hz=cent,
        band_balance=bands,
        onset_count=onsets["onset_count"],
        onset_density=onsets["onset_density"],
        median_ioi_s=onsets["median_ioi_s"],
        peaks=pks,
        chord=ch,
        band_decay_ms=decay,
    )
