"""soundmatch.core.extract — timbral extraction and AI synthesis brief generator.

Pipeline
--------
1. ``extract_synthesis_features(y, sr)``
       Analyses a mono audio clip and returns an ``ExtractionReport`` with
       envelope, pitch/harmonics, spectral and modulation features.

2. ``generate_synthesis_brief(report)``
       Converts the report to a plain-text prompt you can paste into an AI
       chatbot (Claude, GPT, …).  Includes the full source code of the closest
       existing forge instrument as a template.

3. ``export_brief(report, out_dir)``
       Writes two files to *out_dir*:
           sound_extract.json  — all measurements, machine-readable
           sound_brief.txt     — the AI prompt, human-readable

The two-file output is intentional: the JSON is for tooling/replay; the TXT
is what the user hands to the AI.
"""

from __future__ import annotations

import inspect
import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

log = logging.getLogger(__name__)

_NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def _midi_to_note(midi: int) -> str:
    return f"{_NOTE_NAMES[midi % 12]}{(midi // 12) - 1}"


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class ADSREnvelope:
    attack_ms:   float   # 10% → 90% of peak amplitude
    decay_ms:    float   # peak → sustain level
    sustain_db:  float   # dB relative to peak (negative)
    release_ms:  float   # sustain → noise floor
    peak_db:     float   # absolute peak level in dBFS


@dataclass
class HarmonicProfile:
    fundamental_hz:      float
    fundamental_note:    str              # e.g. "A4"
    harmonic_amps_db:    list[float]      # [0 dB, Δh2, Δh3, …] relative to fundamental
    hnr_db:              float            # harmonic-to-noise ratio


@dataclass
class SpectralProfile:
    centroid_hz:       float
    bandwidth_hz:      float
    rolloff_hz:        float
    tilt_db_per_oct:   float             # spectral tilt (negative = rolls off)
    formant_hz:        list[float]       # up to 4 approximate formant peaks


@dataclass
class ModulationProfile:
    am_rate_hz:     float   # tremolo rate
    am_depth:       float   # 0–1
    fm_rate_hz:     float   # vibrato rate  (0 if not detected)
    fm_depth_cents: float


@dataclass
class ExtractionReport:
    # Source
    source_name:       str
    duration_s:        float
    sr:                int

    # High-level classification
    percussive_ratio:  float   # from inspector HPSS
    is_percussive:     bool
    is_tonal:          bool
    is_noisy:          bool
    onset_count:       int

    # Features
    envelope:          ADSREnvelope
    harmonic:          HarmonicProfile | None
    spectral:          SpectralProfile
    modulation:        ModulationProfile

    # AI guidance
    suggested_approach:  str   # one-line synthesis description
    suggested_template:  str   # forge instrument id to use as template

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


# ── Extraction helpers ────────────────────────────────────────────────────────

def _estimate_adsr(y: np.ndarray, sr: int) -> ADSREnvelope:
    import librosa
    from scipy.ndimage import uniform_filter1d
    from scipy.signal import hilbert

    if len(y) < 256:
        return ADSREnvelope(10.0, 50.0, -12.0, 100.0, -20.0)

    # Hilbert amplitude envelope — frequency-independent and smooth.
    # RMS frames oscillate for low-frequency chirps (partial cycles per frame);
    # |hilbert(y)| tracks the true amplitude modulation directly.
    env = np.abs(hilbert(y.astype(float)))
    # 10 ms smooth kills residual carrier ripple without blurring the attack shape.
    env = uniform_filter1d(env, size=max(4, int(0.01 * sr)))

    global_max = float(env.max())
    peak_db    = float(20 * np.log10(max(global_max, 1e-10)))
    threshold  = 0.1 * global_max

    # Onset: first sample crossing 10% of peak
    onset_idx = int(np.argmax(env >= threshold))

    # Attack endpoint: first sustained downturn within 500 ms of onset.
    # A 25 ms secondary smoothing + 3-consecutive check avoids false early triggers
    # from AM oscillations or minor frame noise while still catching fast attacks.
    window_end = min(len(env), onset_idx + int(0.5 * sr))
    region     = env[onset_idx:window_end]
    smooth2    = uniform_filter1d(region, size=max(4, int(0.025 * sr)))
    grad = np.diff(smooth2)
    peak_rel = int(np.argmax(smooth2))  # fallback = window max
    for i in range(len(grad) - 2):
        if grad[i] <= 0 and grad[i + 1] <= 0 and grad[i + 2] <= 0:
            peak_rel = i
            break
    attack_peak_idx = onset_idx + peak_rel
    attack_ms = float((attack_peak_idx - onset_idx) / sr * 1000)

    # Switch to coarser RMS frames for sustain / decay / release
    hop   = max(64, int(0.005 * sr))    # 5 ms hop
    rms   = librosa.feature.rms(y=y, frame_length=hop * 2, hop_length=hop)[0]
    rms   = np.maximum(rms, 1e-10)
    times = librosa.times_like(rms, sr=sr, hop_length=hop)

    rms_peak_frame = min(len(rms) - 1, attack_peak_idx // hop)
    peak_val = float(rms[rms_peak_frame])

    after   = rms[rms_peak_frame:]
    after_t = times[rms_peak_frame:]
    n_after = len(after)
    mid_s, mid_e = n_after // 3, 2 * n_after // 3
    mid_e = max(mid_s + 1, mid_e)
    sustain_val = float(np.median(after[mid_s:mid_e])) if mid_e <= n_after else float(after[-1])
    sustain_db  = float(20 * np.log10(max(sustain_val, 1e-10) / max(peak_val, 1e-10)))

    decay_thr = max(sustain_val * 1.2, peak_val * 0.02)
    below     = np.where(after <= decay_thr)[0]
    decay_ms  = float((after_t[below[0]] - after_t[0]) * 1000) if len(below) else \
                float((after_t[-1]       - after_t[0]) * 1000) if len(after_t) > 1 else 50.0

    noise_thr = peak_val * 0.02
    voiced    = np.where(after >= noise_thr)[0]
    if len(voiced) > 0:
        rel_start  = int(voiced[-1])
        release_ms = float((after_t[-1] - after_t[rel_start]) * 1000) if len(after_t) > rel_start + 1 else 20.0
    else:
        release_ms = 20.0

    return ADSREnvelope(
        attack_ms  = max(1.0, attack_ms),
        decay_ms   = max(1.0, decay_ms),
        sustain_db = min(0.0, sustain_db),
        release_ms = max(1.0, release_ms),
        peak_db    = peak_db,
    )


def _estimate_pitch(y: np.ndarray, sr: int, chord_midi: list[int]) -> float:
    """Return dominant fundamental Hz.  Uses chord detection first, pyin as fallback."""
    # chord_midi is already computed by inspector from chroma — use it if available
    if chord_midi:
        midi = int(np.median(chord_midi))
        return float(440.0 * 2 ** ((midi - 69) / 12))

    # Fallback: pyin pitch tracking
    try:
        import librosa
        f0_arr, voiced, _ = librosa.pyin(
            y, fmin=librosa.note_to_hz("C2"), fmax=librosa.note_to_hz("C7"), sr=sr,
        )
        valid = f0_arr[voiced & np.isfinite(f0_arr)]
        if len(valid) > 0:
            return float(np.median(valid))
    except Exception as exc:
        log.debug("pyin failed: %s", exc)
    return 0.0


def _estimate_harmonics(y: np.ndarray, sr: int, f0: float) -> HarmonicProfile | None:
    if f0 <= 20 or f0 >= sr / 2 * 0.9:
        return None

    # Nearest MIDI note
    midi = int(round(69 + 12 * np.log2(f0 / 440.0)))
    midi = max(0, min(127, midi))
    note_name = _midi_to_note(midi)

    n_fft = min(len(y), 32768)
    Y     = np.abs(np.fft.rfft(y[:n_fft], n=n_fft))
    freqs = np.fft.rfftfreq(n_fft, 1.0 / sr)

    amps_db: list[float] = []
    harmonic_power = 0.0
    margin_hz = max(15.0, f0 * 0.04)

    for n in range(1, 13):
        target = f0 * n
        if target > sr / 2 * 0.9:
            break
        lo = int((target - margin_hz) / (sr / n_fft))
        hi = int((target + margin_hz) / (sr / n_fft)) + 1
        lo, hi = max(0, lo), min(len(Y), hi)
        if hi <= lo:
            continue
        window = Y[lo:hi]
        harmonic_power += float(np.sum(window ** 2))
        amps_db.append(float(window.max()))

    if not amps_db:
        return None

    fund = amps_db[0]
    amps_rel = [0.0] + [float(20 * np.log10(max(a, 1e-12) / fund)) for a in amps_db[1:]]

    total_power = float(np.sum(Y ** 2))
    noise_power = max(total_power - harmonic_power, 1e-12)
    hnr_db = float(10 * np.log10(harmonic_power / noise_power))

    return HarmonicProfile(
        fundamental_hz   = f0,
        fundamental_note = note_name,
        harmonic_amps_db = amps_rel,
        hnr_db           = hnr_db,
    )


def _estimate_spectral(y: np.ndarray, sr: int) -> SpectralProfile:
    import librosa
    from scipy.signal import find_peaks

    cent  = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))
    bw    = float(np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr)))
    roll  = float(np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr, roll_percent=0.85)))

    # Spectral tilt: linear regression of log-magnitude vs log-frequency
    n_fft = min(len(y), 4096)
    Y     = np.abs(np.fft.rfft(y[:n_fft], n=n_fft))
    freqs = np.fft.rfftfreq(n_fft, 1.0 / sr)
    mask  = (freqs > 80) & (freqs < sr / 2 * 0.9)
    if mask.sum() > 4:
        lf = np.log2(freqs[mask] + 1e-12)
        lY = 20 * np.log10(Y[mask] + 1e-12)
        coeffs = np.polyfit(lf, lY, 1)
        tilt = float(coeffs[0])   # dB per octave
    else:
        tilt = 0.0

    # Formants: peaks in smoothed spectrum below 5 kHz
    try:
        from scipy.ndimage import uniform_filter1d
        smooth = uniform_filter1d(Y, size=max(1, n_fft // 60))
        peaks, _ = find_peaks(smooth, height=smooth.max() * 0.08, distance=n_fft // 30)
        f_peaks  = freqs[peaks]
        mask_f   = (f_peaks > 120) & (f_peaks < 5000)
        formants = sorted(float(f) for f in f_peaks[mask_f])[:4]
    except Exception:
        formants = []

    return SpectralProfile(
        centroid_hz     = cent,
        bandwidth_hz    = bw,
        rolloff_hz      = roll,
        tilt_db_per_oct = tilt,
        formant_hz      = formants,
    )


def _estimate_modulation(y: np.ndarray, sr: int) -> ModulationProfile:
    import librosa

    frame_len = max(128, int(0.02 * sr))
    hop       = max(64, frame_len // 2)
    rms       = librosa.feature.rms(y=y, frame_length=frame_len, hop_length=hop)[0]
    rms_sr    = sr / hop

    am_rate, am_depth = 0.0, 0.0
    if len(rms) >= 16:
        r = rms - rms.mean()
        ac = np.correlate(r, r, mode="full")
        ac = ac[len(ac) // 2:]
        ac /= max(float(ac[0]), 1e-12)
        lo = max(2, int(rms_sr / 12))   # max 12 Hz (musical tremolo tops out here)
        hi = min(len(ac) - 1, int(rms_sr / 2))  # min 2 Hz
        if hi > lo:
            w  = ac[lo:hi]
            pi = int(np.argmax(w)) + lo
            if float(ac[pi]) > 0.25:
                am_rate  = float(rms_sr / pi)
                am_depth = float(ac[pi])

    return ModulationProfile(
        am_rate_hz    = am_rate,
        am_depth      = am_depth,
        fm_rate_hz    = 0.0,     # FM / vibrato detection left for future work
        fm_depth_cents= 0.0,
    )


def _suggest_approach(
    perc: float,
    harmonic: HarmonicProfile | None,
    spectral: SpectralProfile,
    envelope: ADSREnvelope,
) -> tuple[str, str]:
    """Returns (one-line synthesis description, forge template instrument id)."""
    centroid = spectral.centroid_hz
    f0 = harmonic.fundamental_hz if harmonic else 0.0
    hnr = harmonic.hnr_db if harmonic else -99.0

    if perc > 0.65:
        if centroid > 4000:
            return ("Short filtered-noise burst — hi-hat / cymbal character",   "hat")
        elif centroid > 1200:
            return ("Noise + tonal body with fast transient — snare character", "snare")
        else:
            return ("Pitch-falling sine with exponential decay — kick character","kick")

    if hnr > 8 and f0 > 0:
        short = envelope.attack_ms < 30 and (envelope.decay_ms + envelope.release_ms) < 500
        if f0 < 200:
            if centroid < 600:
                return ("Detuned sawtooth + low-pass filter — bass character", "bass")
            else:
                return ("Subtractive synth with resonant LP — bass/mid lead",   "psy_bass")
        elif short:
            return ("Plucked string — fast attack, exponential decay",         "harp")
        elif len(spectral.formant_hz) >= 2:
            return ("Formant-filtered oscillator bank — vocal/reed character", "voice")
        else:
            return ("Sustained pad — slow attack, harmonic oscillators",       "pad")

    if centroid < 400:
        return ("Low drone / rumble — filtered noise or detuned oscillators",  "drone")
    return ("Textural noise layer — bandpass-filtered noise with slow LFO",    "wind")


# ── Public API ────────────────────────────────────────────────────────────────

def extract_synthesis_features(
    y: np.ndarray,
    sr: int,
    *,
    source_name: str = "sound",
    chord_midi: list[int] | None = None,
) -> ExtractionReport:
    """Analyse a mono audio clip and return a full ExtractionReport.

    Parameters
    ----------
    y           : Mono audio signal.
    sr          : Sample rate.
    source_name : Human-readable label used in the brief.
    chord_midi  : MIDI notes already detected by the inspector (passed in to
                  avoid re-computing).  If None, pyin is used as fallback.
    """
    from inspector.metrics import characterize

    log.info("extract: %.2fs at %d Hz — %s", len(y) / sr, sr, source_name)
    y = np.asarray(y, dtype=np.float32)
    if y.ndim > 1:
        y = y.mean(axis=1)

    # Re-use inspector for classification features
    m = characterize(y, sr)
    # percussive_ratio is in percent (0–100); normalize to 0–1 for all comparisons
    perc      = float(m.percussive_ratio) / 100.0
    c_midi    = chord_midi if chord_midi is not None else m.chord.get("midi", [])
    onset_cnt = int(m.onset_count)

    envelope  = _estimate_adsr(y, sr)
    f0        = _estimate_pitch(y, sr, c_midi)
    harmonic  = _estimate_harmonics(y, sr, f0) if f0 > 0 else None
    spectral  = _estimate_spectral(y, sr)
    modulation = _estimate_modulation(y, sr)

    approach, template = _suggest_approach(perc, harmonic, spectral, envelope)

    return ExtractionReport(
        source_name       = source_name,
        duration_s        = float(len(y) / sr),
        sr                = sr,
        percussive_ratio  = perc,          # stored as 0–1
        is_percussive     = perc > 0.60,
        is_tonal          = bool(harmonic and harmonic.hnr_db > 8),
        is_noisy          = perc < 0.30 and (not harmonic or harmonic.hnr_db < 5),
        onset_count       = onset_cnt,
        envelope          = envelope,
        harmonic          = harmonic,
        spectral          = spectral,
        modulation        = modulation,
        suggested_approach = approach,
        suggested_template = template,
    )


def _get_template_source(instrument_id: str) -> str:
    """Return the source code of the forge function for *instrument_id*."""
    try:
        from forge.instruments.registry import REGISTRY
        entry = REGISTRY.get(instrument_id)
        if entry is None:
            return f"# template '{instrument_id}' not found in REGISTRY"
        return inspect.getsource(entry["fn"])
    except Exception as exc:
        return f"# could not retrieve template source: {exc}"


def generate_synthesis_brief(report: ExtractionReport, *, include_template: bool = True) -> str:
    """Return a plain-text AI prompt describing the sound and what to implement."""
    r = report
    h = r.harmonic
    e = r.envelope
    s = r.spectral
    mod = r.modulation

    lines: list[str] = []
    w = lines.append

    w("SOUND SYNTHESIS BRIEF")
    w("=" * 60)
    w(f"Source:    {r.source_name}")
    w(f"Duration:  {r.duration_s:.2f} s   SR: {r.sr} Hz")
    w("")

    # Classification
    kind = ("Percussive" if r.is_percussive
            else "Tonal" if r.is_tonal
            else "Mostly noise / texture")
    w(f"Character: {kind}  (percussive_ratio={r.percussive_ratio * 100:.0f}%)")
    w(f"Onsets:    {r.onset_count}")
    w("")

    # Envelope
    w("ENVELOPE")
    w("-" * 40)
    w(f"  Attack:  {e.attack_ms:.0f} ms")
    w(f"  Decay:   {e.decay_ms:.0f} ms")
    w(f"  Sustain: {e.sustain_db:.0f} dB  (relative to peak)")
    w(f"  Release: {e.release_ms:.0f} ms")
    w(f"  Peak:    {e.peak_db:.1f} dBFS")
    w("")

    # Pitch / harmonics
    w("PITCH & HARMONICS")
    w("-" * 40)
    if h:
        w(f"  Fundamental: {h.fundamental_hz:.1f} Hz  ({h.fundamental_note})")
        w(f"  HNR:         {h.hnr_db:.1f} dB  "
          f"({'highly tonal' if h.hnr_db > 20 else 'somewhat tonal' if h.hnr_db > 8 else 'noisy'})")
        if len(h.harmonic_amps_db) > 1:
            parts = [f"h{i+1} {a:+.0f} dB" for i, a in enumerate(h.harmonic_amps_db)]
            w(f"  Harmonics:   {', '.join(parts[:8])}")
    else:
        w("  No clear fundamental — unpitched or noise-dominated.")
    w("")

    # Spectral
    w("SPECTRAL")
    w("-" * 40)
    brightness = ("very bright" if s.centroid_hz > 4000
                  else "bright" if s.centroid_hz > 2000
                  else "mid-range" if s.centroid_hz > 800
                  else "dark")
    w(f"  Centroid:    {s.centroid_hz:.0f} Hz  ({brightness})")
    w(f"  Bandwidth:   {s.bandwidth_hz:.0f} Hz")
    w(f"  Rolloff:     {s.rolloff_hz:.0f} Hz  (85 %)")
    w(f"  Tilt:        {s.tilt_db_per_oct:+.1f} dB/oct")
    if s.formant_hz:
        w(f"  Formants≈    {', '.join(f'{f:.0f} Hz' for f in s.formant_hz)}")
    w("")

    # Modulation
    w("MODULATION")
    w("-" * 40)
    if mod.am_rate_hz > 0:
        w(f"  Tremolo:  {mod.am_rate_hz:.1f} Hz  depth≈{mod.am_depth:.2f}")
    else:
        w("  No significant amplitude modulation detected.")
    w("")

    # Synthesis recommendation
    w("SUGGESTED SYNTHESIS APPROACH")
    w("-" * 40)
    w(f"  {r.suggested_approach}")
    w("")

    # AI task
    w("TASK FOR THE AI")
    w("=" * 60)
    w("""Implement a new Python forge instrument that reproduces this sound.

Rules:
- The function signature must be:
      def my_instrument(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
- Use ctx.get("sr", 44100) for the sample rate.
- Use ctx.get("duration", <default_s>) for clip length if the sound is a texture.
- Expose tuneable parameters as ParamSchema entries in REGISTRY (see template).
- Return an AudioBuffer(data, sr) where data.shape is (N,) mono or (N, 2) stereo.
- Register in forge/instruments/registry.py:
      from forge.instruments.my_module import my_instrument
      REGISTRY["my_instrument"] = {
          "fn": my_instrument,
          "params": [ParamSchema(name=..., kind="float", default=..., lo=..., hi=...), ...],
          "family": "<percussion|bass|voice|strings|synth|texture|fx>",
      }

Below is the full source of the closest existing instrument as a template.
Study it, then write your own that matches the measurements above.
""")

    if include_template:
        src = _get_template_source(r.suggested_template)
        w(f"TEMPLATE  ({r.suggested_template})")
        w("=" * 60)
        w(src)
        w("")

    return "\n".join(lines)


def export_brief(
    report: ExtractionReport,
    out_dir: Path,
    *,
    include_template: bool = True,
) -> tuple[Path, Path]:
    """Write sound_extract.json and sound_brief.txt to *out_dir*.

    Returns
    -------
    (json_path, brief_path)
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path  = out_dir / "sound_extract.json"
    brief_path = out_dir / "sound_brief.txt"

    json_path.write_text(report.to_json(), encoding="utf-8")
    brief_path.write_text(
        generate_synthesis_brief(report, include_template=include_template),
        encoding="utf-8",
    )

    log.info("exported brief to %s/", out_dir)
    return json_path, brief_path
