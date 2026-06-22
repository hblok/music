"""Sound-Match test fixtures — paths and reference numbers.

The Strike It Up reference numbers are from the worked session measuring the
isolated ``other`` stem (1–10 s) of ``Black_Box-Strike_It_Up_Xo3kp5BLF6Q.mp3``.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).resolve().parent / "data"
FIXTURE_WAV = DATA_DIR / "strike_lead_synthetic.wav"

# Source mp3 (may not exist in CI — tests skip if absent)
SOURCE_MP3 = Path("/workspace/music/Black_Box-Strike_It_Up_Xo3kp5BLF6Q.mp3")

# ---------------------------------------------------------------------------
# Known reference values from the worked session
# ---------------------------------------------------------------------------

REF_PERCUSSIVE_RATIO = 82.0      # %
REF_CENTROID_HZ = 2542.0
REF_BAND_BALANCE = {
    "80-300": 18.0,
    "300-800": 30.0,
    "800-2500": 41.0,
    "2500-9000": 7.0,
}
REF_ONSET_COUNT = 36
REF_MEDIAN_IOI_S = 0.238

# Chord: G# major with sub-octave
REF_CHORD_PITCH_CLASSES = ["G#", "D#", "C"]
REF_CHORD_SUB_OCTAVE = True

# ---------------------------------------------------------------------------
# Tolerances for regression contract
# ---------------------------------------------------------------------------

TOL_PERC = 3.0           # ±3 %
TOL_CENTROID = 150.0     # ±150 Hz
TOL_BAND = 4.0           # ±4 pts per band
TOL_ONSET_COUNT = 2      # ±2 onsets


# ---------------------------------------------------------------------------
# Synthetic fixture generator
# ---------------------------------------------------------------------------

def generate_synthetic_fixture(sr: int = 44100, seed: int = 42) -> np.ndarray:
    """Generate a short synthetic signal mimicking the percussive brass lead.

    This avoids needing the actual mp3 or demucs for tests.  The signal has:
      - percussive stabs (high percussive ratio ~80%+)
      - strong mid-band energy
      - multiple onsets
      - very short decays so HPSS reads it as percussive
    """
    rng = np.random.default_rng(seed)
    duration = 2.0  # short clip
    n = int(duration * sr)
    y = np.zeros(n, dtype=np.float64)

    # Create percussive stabs — very short (20-40ms) with fast decay
    stab_count = 16
    ioi = duration / stab_count
    for i in range(stab_count):
        t_start = i * ioi
        s0 = int(t_start * sr)
        stab_len = int(0.04 * sr)  # 40ms staccato stab
        if s0 + stab_len > n:
            break
        # Very fast decay (tau=15ms) so HPSS classifies as percussive
        t = np.arange(stab_len) / sr
        # Mid-band tonal component with very fast decay
        freq = 800.0
        stab = 0.4 * np.sin(2 * np.pi * freq * t) * np.exp(-t / 0.015)
        stab += 0.2 * np.sin(2 * np.pi * 2.5 * freq * t) * np.exp(-t / 0.012)
        # Strong noise snap (the percussive attack layer)
        noise = 0.8 * rng.standard_normal(stab_len) * np.exp(-t / 0.015)
        from scipy.signal import butter, sosfilt
        sos = butter(4, [3000 / (sr / 2), 8000 / (sr / 2)], btype="band", output="sos")
        noise = sosfilt(sos, noise)
        # Also add a broadband transient click at onset
        click_len = min(int(0.005 * sr), stab_len)
        click = 1.2 * rng.standard_normal(click_len)
        y[s0:s0 + stab_len] += stab + noise
        y[s0:s0 + click_len] += click

    # Normalize
    peak = np.max(np.abs(y))
    if peak > 1e-12:
        y /= peak
    return y.astype(np.float64)


def ensure_fixture(sr: int = 44100) -> np.ndarray:
    """Return the fixture audio array, generating and caching if needed."""
    if FIXTURE_WAV.exists():
        y, sr_out = sf.read(str(FIXTURE_WAV), dtype="float64")
        if sr_out != sr and sr_out > 0:
            import librosa
            y = librosa.resample(y, orig_sr=sr_out, target_sr=sr)
        return y
    y = generate_synthetic_fixture(sr=sr)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    sf.write(str(FIXTURE_WAV), y, sr, subtype="FLOAT")
    return y