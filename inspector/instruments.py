"""
Instrument analysis module for music inspector.

Pipeline per section (capped at 30 s for expensive steps):
  1. HPSS  — harmonic / percussive energy split
  2. pYIN  — F0 tracking on harmonic component (pitch range, vibrato, note duration)
  3. Onset profiling on percussive component (low/high split, regularity)

Global:
  4. Maqam / scale comparison from aggregate pitch-class histogram
  5. Heuristic instrument identification (Arabic/Persian trance context)
"""

from __future__ import annotations

import warnings
import numpy as np
import librosa

# ---------------------------------------------------------------------------
# Maqam / scale templates  (pitch classes from root, 12-TET approximations)
# ---------------------------------------------------------------------------

_MAQAM_TEMPLATES: dict[str, list[int]] = {
    "Phrygian Dominant / Maqam Hijaz / Dastgah Homayoun": [0, 1, 4, 5, 7, 8, 10],
    "Double Harmonic / Maqam Hijaz Kar":                  [0, 1, 4, 5, 7, 8, 11],
    "Phrygian / Maqam Kurd":                              [0, 1, 3, 5, 7, 8, 10],
    "Maqam Bayati / Dastgah Shur (approx.)":              [0, 1, 3, 5, 7, 8, 10],
    "Natural Minor / Maqam Nahawand":                     [0, 2, 3, 5, 7, 8, 10],
    "Dorian / Maqam Rast (approx.)":                      [0, 2, 3, 5, 7, 9, 10],
    "Maqam Saba (approx.)":                               [0, 2, 3, 5, 7, 8, 10],
    "Major / Dastgah Mahoor":                             [0, 2, 4, 5, 7, 9, 11],
    "Harmonic Minor":                                     [0, 2, 3, 5, 7, 8, 11],
}

_SAMPLE_CAP = 30   # seconds per section for HPSS + pYIN
_PITCH_HOP  = 2048  # hop for pYIN (speed trade-off)
_STFT_HOP   = 512


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def analyse_instruments(audio: dict, boundaries_sec: list[float]) -> dict:
    """
    Run full instrument analysis. Returns a dict suitable for report/plots.
    """
    y, sr = audio["y"], audio["sr"]

    section_results: list[dict] = []
    all_f0_classes: list[float] = []   # for global pitch-class histogram

    for i in range(len(boundaries_sec) - 1):
        t0 = boundaries_sec[i]
        t1 = boundaries_sec[i + 1]
        s0 = int(t0 * sr)
        s1 = int(t1 * sr)
        seg = y[s0:s1]

        if len(seg) < int(sr * 0.5):
            continue

        # Cap at _SAMPLE_CAP seconds for expensive operations
        cap = int(_SAMPLE_CAP * sr)
        sample = seg[:cap]

        hpss_data   = _hpss_section(sample, sr)
        pitch_data  = _pitch_section(hpss_data["y_harm"], sr)
        perc_data   = _percussion_section(hpss_data["y_perc"], sr)

        # Collect F0 values for global maqam comparison
        if pitch_data and pitch_data.get("f0_values_hz"):
            all_f0_classes.extend(pitch_data["f0_values_hz"])

        section_results.append({
            "idx":       i + 1,
            "t_start":   t0,
            "t_end":     t1,
            "duration":  t1 - t0,
            "hpss":      hpss_data,
            "pitch":     pitch_data,
            "percussion": perc_data,
        })

    maqam  = _compare_maqam(all_f0_classes)
    instr  = _estimate_instruments(section_results, maqam)

    return {
        "sections":        section_results,
        "maqam_matches":   maqam,
        "estimates":       instr,
    }


# ---------------------------------------------------------------------------
# HPSS
# ---------------------------------------------------------------------------

def _hpss_section(y: np.ndarray, sr: int) -> dict:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        y_harm, y_perc = librosa.effects.hpss(y, margin=2.0)

    e_total = float(np.mean(y ** 2)) + 1e-10
    e_harm  = float(np.mean(y_harm ** 2))
    e_perc  = float(np.mean(y_perc ** 2))

    # Spectral flatness of harmonic component: near-0 = tonal, near-1 = noisy
    S_h      = np.abs(librosa.stft(y_harm, hop_length=_STFT_HOP))
    flatness = float(librosa.feature.spectral_flatness(S=S_h).mean())

    return {
        "y_harm":       y_harm,
        "y_perc":       y_perc,
        "harm_ratio":   e_harm  / e_total,
        "perc_ratio":   e_perc  / e_total,
        "flatness":     flatness,
    }


# ---------------------------------------------------------------------------
# Pitch tracking (pYIN)
# ---------------------------------------------------------------------------

def _pitch_section(y_harm: np.ndarray, sr: int) -> dict | None:
    if len(y_harm) < _PITCH_HOP * 4:
        return None

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            f0, voiced_flag, _ = librosa.pyin(
                y_harm,
                fmin=librosa.note_to_hz("C2"),   # ~65 Hz
                fmax=librosa.note_to_hz("C7"),   # ~2093 Hz
                hop_length=_PITCH_HOP,
                fill_na=np.nan,
            )
    except Exception:
        return None

    voiced = f0[voiced_flag & ~np.isnan(f0)]
    if len(voiced) < 8:
        return {"voiced_ratio": 0.0, "f0_median_hz": None, "f0_values_hz": []}

    voiced_ratio  = float(voiced_flag.sum() / max(len(voiced_flag), 1))
    f0_median     = float(np.median(voiced))
    f0_low        = float(np.percentile(voiced, 5))
    f0_high       = float(np.percentile(voiced, 95))

    # Vibrato: local pitch deviation in semitones
    st = 12.0 * np.log2(voiced / (f0_median + 1e-10) + 1e-10)
    win = max(2, int(0.4 * sr / _PITCH_HOP))   # ~0.4 s window
    local_stds = [float(np.std(st[j : j + win]))
                  for j in range(0, len(st) - win, win // 2)]
    vibrato_depth = float(np.percentile(local_stds, 75)) if local_stds else 0.0
    vibrato       = vibrato_depth > 0.25   # >0.25 semitone oscillation

    # Median note duration: frames between pitch jumps >0.5 semitone
    jumps = np.where(np.abs(np.diff(st)) > 0.5)[0]
    if len(jumps) > 1:
        median_note_dur = float(np.median(np.diff(jumps)) * _PITCH_HOP / sr)
    else:
        median_note_dur = float(len(voiced) * _PITCH_HOP / sr)

    return {
        "voiced_ratio":         voiced_ratio,
        "f0_median_hz":         f0_median,
        "f0_median_note":       librosa.hz_to_note(f0_median),
        "f0_low_hz":            f0_low,
        "f0_high_hz":           f0_high,
        "f0_low_note":          librosa.hz_to_note(f0_low),
        "f0_high_note":         librosa.hz_to_note(f0_high),
        "vibrato":              vibrato,
        "vibrato_depth_st":     vibrato_depth,
        "median_note_dur_s":    median_note_dur,
        "f0_values_hz":         voiced.tolist(),
    }


# ---------------------------------------------------------------------------
# Percussion onset profiling
# ---------------------------------------------------------------------------

def _percussion_section(y_perc: np.ndarray, sr: int) -> dict:
    S_p      = np.abs(librosa.stft(y_perc, hop_length=_STFT_HOP))
    freqs    = librosa.fft_frequencies(sr=sr)
    low_mask = freqs < 300
    high_mask= freqs > 1200

    onset_env    = librosa.onset.onset_strength(
        S=librosa.power_to_db(S_p ** 2), sr=sr, hop_length=_STFT_HOP
    )
    onset_frames = librosa.onset.onset_detect(
        onset_envelope=onset_env, sr=sr, hop_length=_STFT_HOP
    )

    if len(onset_frames) < 2:
        return {
            "onset_count":    int(len(onset_frames)),
            "low_ratio":      0.5,
            "high_ratio":     0.5,
            "regularity":     0.0,
            "mean_ioi_s":     None,
        }

    onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=_STFT_HOP)
    ioi         = np.diff(onset_times)

    # Regularity: 1 = perfectly metronomic, 0 = random
    regularity = float(1.0 - min(1.0, np.std(ioi) / (np.mean(ioi) + 1e-10)))

    # Low vs high energy at each onset frame
    low_vals, high_vals = [], []
    for fr in onset_frames:
        fr = min(fr, S_p.shape[1] - 1)
        col   = S_p[:, fr]
        total = col.sum() + 1e-10
        low_vals.append(float(col[low_mask].sum() / total))
        high_vals.append(float(col[high_mask].sum() / total))

    return {
        "onset_count":  int(len(onset_frames)),
        "low_ratio":    float(np.mean(low_vals)),
        "high_ratio":   float(np.mean(high_vals)),
        "regularity":   regularity,
        "mean_ioi_s":   float(np.mean(ioi)),
        "ioi_std_s":    float(np.std(ioi)),
    }


# ---------------------------------------------------------------------------
# Maqam / scale comparison
# ---------------------------------------------------------------------------

def _compare_maqam(f0_values_hz: list[float]) -> list[dict]:
    """
    Build a 12-bin pitch-class histogram from all voiced F0 values,
    then correlate against each maqam template.
    Root is C (pitch class 0).
    """
    if not f0_values_hz:
        return []

    arr = np.array(f0_values_hz)
    arr = arr[arr > 0]
    if len(arr) < 10:
        return []

    # Convert Hz → pitch class (semitones mod 12, relative to C=0)
    # C4 = MIDI 60, pitch class 0
    midi   = 12.0 * np.log2(arr / 440.0) + 69.0
    pc     = np.round(midi).astype(int) % 12

    hist = np.bincount(pc, minlength=12).astype(float)
    hist_norm = hist / (np.linalg.norm(hist) + 1e-10)

    results: list[dict] = []
    for name, degrees in _MAQAM_TEMPLATES.items():
        template = np.zeros(12)
        for d in degrees:
            template[int(round(d)) % 12] = 1.0
        t_norm = template / (np.linalg.norm(template) + 1e-10)
        sim    = float(np.dot(hist_norm, t_norm))
        results.append({"name": name, "score": sim})

    return sorted(results, key=lambda x: -x["score"])


# ---------------------------------------------------------------------------
# Heuristic instrument identification
# ---------------------------------------------------------------------------

def _estimate_instruments(sections: list[dict], maqam_matches: list[dict]) -> list[dict]:
    """
    Combine HPSS, pitch, and percussion data into instrument estimates
    with confidence labels, tuned for Arabic/Persian trance context.
    """
    pitch_secs = [s["pitch"] for s in sections
                  if s.get("pitch") and s["pitch"] and s["pitch"].get("f0_median_hz")]
    perc_secs  = [s["percussion"] for s in sections if s.get("percussion")]
    hpss_secs  = [s["hpss"] for s in sections if s.get("hpss")]

    avg_harm      = np.mean([h["harm_ratio"]  for h in hpss_secs]) if hpss_secs else 0.5
    avg_perc      = np.mean([h["perc_ratio"]  for h in hpss_secs]) if hpss_secs else 0.5
    avg_flatness  = np.mean([h["flatness"]    for h in hpss_secs]) if hpss_secs else 0.5

    estimates: list[dict] = []

    # ── Melodic instruments ────────────────────────────────────────────────

    if pitch_secs:
        f0_meds    = [p["f0_median_hz"]       for p in pitch_secs]
        voiced_rs  = [p["voiced_ratio"]        for p in pitch_secs]
        note_durs  = [p["median_note_dur_s"]   for p in pitch_secs]
        vib_count  = sum(1 for p in pitch_secs if p.get("vibrato"))
        vib_depths = [p["vibrato_depth_st"]    for p in pitch_secs]
        all_low    = min(p["f0_low_hz"]  for p in pitch_secs)
        all_high   = max(p["f0_high_hz"] for p in pitch_secs)

        avg_voiced    = float(np.mean(voiced_rs))
        avg_dur       = float(np.mean(note_durs))
        avg_vib_depth = float(np.mean(vib_depths))
        vib_frac      = vib_count / max(len(pitch_secs), 1)
        melody_midpoint = float(np.median(f0_meds))

        # Ney (Persian/Arabic end-blown flute)
        # Breathy (moderate flatness on harmonic), range F3–D6, sustained, vibrato common
        ney_conf = _conf(
            avg_flatness    > 0.08,   # breathy
            300 < melody_midpoint < 1200,
            avg_dur         > 0.4,
            vib_frac        > 0.2,
            avg_voiced      > 0.25,
        )
        estimates.append(_est("Ney (Persian flute)", "melodic", ney_conf,
            f"range {librosa.hz_to_note(all_low)}–{librosa.hz_to_note(all_high)}, "
            f"vibrato depth {avg_vib_depth:.2f} st, "
            f"avg note dur {avg_dur:.2f} s, "
            f"breathy (flatness {avg_flatness:.3f})"
        ))

        # Oud (Arabic/Turkish lute)
        # Plucked (short notes), lower range E2–E5, minimal vibrato
        oud_conf = _conf(
            avg_dur         < 0.6,
            all_low         < 350,
            avg_flatness    < 0.15,   # relatively tonal attack
            vib_frac        < 0.3,
        )
        estimates.append(_est("Oud (Arabic lute)", "melodic", oud_conf,
            f"plucked style (avg note {avg_dur:.2f} s), "
            f"low reach {librosa.hz_to_note(all_low)}, "
            f"voiced {avg_voiced*100:.0f}% of time"
        ))

        # Qanun (plucked zither)
        # Bright, metallic, plucked, mid-high range C3–C6
        qanun_conf = _conf(
            avg_dur         < 0.5,
            avg_flatness    < 0.12,
            melody_midpoint > 300,
            all_high        > 700,
        )
        estimates.append(_est("Qanun (zither)", "melodic", qanun_conf,
            f"plucked (avg {avg_dur:.2f} s/note), "
            f"midpoint {librosa.hz_to_note(melody_midpoint)}, high reach {librosa.hz_to_note(all_high)}"
        ))

        # Synthesizer lead / synth melody
        # Sustained, low flatness (very tonal), any range, often little vibrato or with LFO-vibrato
        synth_lead_conf = _conf(
            avg_dur         > 0.5,
            avg_flatness    < 0.06,   # very tonal / sine-like
            avg_harm        > 0.55,
        )
        estimates.append(_est("Synthesizer lead", "melodic", synth_lead_conf,
            f"very tonal (flatness {avg_flatness:.3f}), "
            f"sustained ({avg_dur:.2f} s/note), "
            f"harmonic content {avg_harm*100:.0f}%"
        ))

    # Synthesizer pad (always present in trance; identified by high harm ratio + sustained)
    pad_conf = _conf(
        avg_harm        > 0.50,
        avg_flatness    < 0.10,
    )
    estimates.append(_est("Synthesizer pad", "harmonic", pad_conf,
        f"harmonic energy {avg_harm*100:.0f}%, "
        f"spectral flatness {avg_flatness:.3f} (lower = more tonal)"
    ))

    # ── Percussion instruments ─────────────────────────────────────────────

    if perc_secs:
        avg_low_ratio  = float(np.mean([p["low_ratio"]    for p in perc_secs]))
        avg_high_ratio = float(np.mean([p["high_ratio"]   for p in perc_secs]))
        avg_reg        = float(np.mean([p["regularity"]   for p in perc_secs]))
        mean_iois      = [p["mean_ioi_s"] for p in perc_secs if p.get("mean_ioi_s")]
        avg_ioi        = float(np.mean(mean_iois)) if mean_iois else 0.2

        # Darbuka / Doumbek (Arabic goblet drum)
        # Mix of low "doum" and high "tak" onsets; moderate regularity (can be human)
        darb_conf = _conf(
            avg_perc        > 0.25,
            avg_low_ratio   > 0.25,
            avg_high_ratio  > 0.20,
        )
        estimates.append(_est("Darbuka / Doumbek", "percussion", darb_conf,
            f"low onset ratio {avg_low_ratio*100:.0f}% (doum), "
            f"high ratio {avg_high_ratio*100:.0f}% (tak), "
            f"regularity {avg_reg:.2f}"
        ))

        # Electronic kick drum
        # Very low onsets, high regularity (machine quantised)
        kick_conf = _conf(
            avg_perc        > 0.25,
            avg_low_ratio   > 0.35,
            avg_reg         > 0.70,
        )
        estimates.append(_est("Electronic kick drum", "percussion", kick_conf,
            f"low onsets {avg_low_ratio*100:.0f}%, "
            f"regularity {avg_reg:.2f} ({'metronomic' if avg_reg > 0.8 else 'slightly loose'}), "
            f"mean IOI {avg_ioi:.3f} s"
        ))

        # Hi-hat / cymbal (electronic or riq)
        hihat_conf = _conf(
            avg_high_ratio  > 0.30,
            avg_perc        > 0.20,
        )
        estimates.append(_est("Hi-hat / cymbal (or Riq)", "percussion", hihat_conf,
            f"high-freq onsets {avg_high_ratio*100:.0f}%, "
            f"regularity {avg_reg:.2f}"
        ))

        # Riq (Arabic tambourine) — similar to hi-hat but with jingles + frame drum
        riq_conf = _conf(
            avg_high_ratio  > 0.25,
            avg_low_ratio   > 0.15,
            avg_reg         < 0.85,   # human feel, not perfectly quantised
        )
        estimates.append(_est("Riq (Arabic tambourine)", "percussion", riq_conf,
            f"mixed low/high onsets, human feel (regularity {avg_reg:.2f})"
        ))

        # Bass synth / sub-bass pad
        bass_conf = _conf(
            avg_harm        > 0.40,
            avg_perc        < 0.50,
        )
        estimates.append(_est("Bass synthesizer / sub-bass", "bass", bass_conf,
            f"sustained low-end harmonic content, "
            f"harmonic ratio {avg_harm*100:.0f}%"
        ))

    # Sort by confidence within each family, then by family order
    family_order = {"melodic": 0, "harmonic": 1, "bass": 2, "percussion": 3}
    conf_order   = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    estimates.sort(key=lambda e: (family_order.get(e["family"], 9),
                                  conf_order.get(e["confidence"], 9)))
    return estimates


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _conf(*conditions: bool) -> str:
    """Map number of True conditions to HIGH / MEDIUM / LOW confidence."""
    n = sum(conditions)
    t = len(conditions)
    ratio = n / max(t, 1)
    if ratio >= 0.65:
        return "HIGH"
    if ratio >= 0.40:
        return "MEDIUM"
    return "LOW"


def _est(name: str, family: str, confidence: str, evidence: str) -> dict:
    return {
        "name":       name,
        "family":     family,
        "confidence": confidence,
        "evidence":   evidence,
    }
