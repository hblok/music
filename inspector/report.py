"""Text report renderer for music inspector results."""

from __future__ import annotations
import numpy as np
from . import features as feat_mod


_WIDTH = 77


def render(results: dict) -> str:
    audio     = results["audio"]
    tempo     = results["tempo"]
    harmony   = results["harmony"]
    structure = results["structure"]
    timbre    = results["timbre"]

    lines: list[str] = []

    def rule(title: str = ""):
        if title:
            pad = _WIDTH - len(title) - 4
            lines.append(f"{'─' * 2} {title} {'─' * pad}")
        else:
            lines.append("─" * _WIDTH)

    def bar(value: float, width: int = 22, max_val: float = 1.0) -> str:
        filled = max(0, min(width, int(round(value / max(max_val, 1e-10) * width))))
        return "█" * filled + "░" * (width - filled)

    # ── Header ───────────────────────────────────────────────────────────────
    lines.append("=" * _WIDTH)
    lines.append("  MUSIC INSPECTOR REPORT")
    lines.append("=" * _WIDTH)
    lines.append(f"  File:      {audio['path']}")
    lines.append(f"  Duration:  {_fmt(audio['duration'])}  ({audio['duration']:.0f} s)")
    lines.append(f"  Analysed:  {audio['sr']} Hz, mono")

    # ── Tempo & Rhythm ────────────────────────────────────────────────────────
    lines.append("")
    rule("TEMPO & RHYTHM")

    bpm_lib = tempo["bpm"]
    bpm_es  = tempo.get("bpm_essentia")
    bpm_conf = tempo.get("bpm_confidence")
    lines.append(f"  BPM (librosa):    {bpm_lib:.2f}")
    if bpm_es is not None:
        lines.append(f"  BPM (essentia):   {bpm_es:.2f}   [confidence {bpm_conf:.2f}]")

    std = tempo["bpm_std"]
    if std < 2:
        stab = "HIGH"
    elif std < 6:
        stab = "MODERATE"
    else:
        stab = "LOW  (free tempo or significant tempo changes)"
    lines.append(f"  Tempo stability:  {stab}  (σ = {std:.1f} BPM across 30 s windows)")
    lines.append(f"  Total beats:      {tempo['beat_count']}")

    tot = tempo["tempo_over_time"]
    if tot:
        lines.append("")
        lines.append("  Tempo over time (30-second windows):")
        for i, w in enumerate(tot):
            t0_str = _fmt(w["t_start"])
            t1_str = _fmt(w["t_start"] + 30)
            lines.append(f"    {t0_str} – {t1_str}   {w['bpm']:.1f} BPM")
            if i >= 59:  # cap at 60 rows (30 min shown, then ellipsis)
                remaining = len(tot) - 60
                if remaining > 0:
                    lines.append(f"    … ({remaining} more windows)")
                break

    # ── Key & Harmony ─────────────────────────────────────────────────────────
    lines.append("")
    rule("KEY & HARMONY")

    key_l, mode_l, corr_l = harmony["key"], harmony["mode"], harmony["key_corr"]
    lines.append(f"  Key (librosa):    {key_l} {mode_l}   [correlation {corr_l:.2f}]")

    key_es   = harmony.get("key_essentia")
    mode_es  = harmony.get("mode_essentia")
    str_es   = harmony.get("key_strength_essentia")
    if key_es:
        lines.append(f"  Key (essentia):   {key_es} {mode_es}   [strength {str_es:.2f}]")

    lines.append("")
    lines.append("  Chroma profile (relative to strongest note):")
    for note, val in harmony["top_notes"]:
        lines.append(f"    {note:>3}  {bar(val, 24, 1.0)}  {val:.2f}")

    cot = harmony.get("chroma_over_time", [])
    if cot:
        lines.append("")
        lines.append("  Dominant note per minute:")
        row = "    "
        for w in cot:
            item = f"{_fmt(w['t_start'])}:{w['dominant_note']:>3}   "
            if len(row) + len(item) > _WIDTH - 2:
                lines.append(row.rstrip())
                row = "    " + item
            else:
                row += item
        if row.strip():
            lines.append(row.rstrip())

    # ── Structure ─────────────────────────────────────────────────────────────
    lines.append("")
    rule("STRUCTURE")
    lines.append(f"  {structure['n_sections']} sections detected")
    lines.append("")
    lines.append(f"  {'§':>3}  {'Start':>7}   {'End':>7}  {'Dur':>7}   {'RMS':>7}   "
                 f"{'Centroid':>8}   {'Density':>9}   Label")
    lines.append(f"  {'─'*3}  {'─'*7}   {'─'*7}  {'─'*7}   {'─'*7}   "
                 f"{'─'*8}   {'─'*9}   {'─'*14}")

    if timbre:
        rms_vals    = [s["rms_db"]     for s in timbre]
        onset_vals  = [s["onset_rate"] for s in timbre]
        rms_mean    = float(np.mean(rms_vals))
        rms_std     = float(np.std(rms_vals))
        onset_mean  = float(np.mean(onset_vals))
    else:
        rms_mean = rms_std = onset_mean = 0.0

    for sec in timbre:
        label = feat_mod.label_section(sec, rms_mean, rms_std, onset_mean)
        t0 = _fmt(sec["t_start"])
        t1 = _fmt(sec["t_end"])
        d  = _fmt(sec["duration"])
        lines.append(
            f"  {sec['idx']:>3}  {t0:>7}   {t1:>7}  {d:>7}   "
            f"{sec['rms_db']:>6.1f} dB   "
            f"{sec['centroid_hz']:>6.0f} Hz   "
            f"{sec['onset_rate']:>5.1f} ev/s   "
            f"{label}"
        )

    # ── Timbral summary ───────────────────────────────────────────────────────
    lines.append("")
    rule("TIMBRAL SUMMARY")

    if timbre:
        avg_c  = float(np.mean([s["centroid_hz"] for s in timbre]))
        avg_b  = float(np.mean([s["bass_ratio"]  for s in timbre]))
        avg_m  = float(np.mean([s["mid_ratio"]   for s in timbre]))
        avg_h  = float(np.mean([s["high_ratio"]  for s in timbre]))
        avg_o  = float(np.mean([s["onset_rate"]  for s in timbre]))
        rms_min = min(rms_vals)
        rms_max = max(rms_vals)

        lines.append(f"  Avg spectral centroid:  {avg_c:.0f} Hz")
        lines.append(f"  Frequency balance:")
        lines.append(f"    Bass   (<250 Hz):    {bar(avg_b)}  {avg_b*100:.1f}%")
        lines.append(f"    Mids   (250–4k Hz):  {bar(avg_m)}  {avg_m*100:.1f}%")
        lines.append(f"    Highs  (>4k Hz):     {bar(avg_h)}  {avg_h*100:.1f}%")
        lines.append(f"  Avg onset density:      {avg_o:.1f} events/sec")
        lines.append(f"  RMS range:              {rms_min:.1f} dB  →  {rms_max:.1f} dB")

    # ── Instrument hints ──────────────────────────────────────────────────────
    lines.append("")
    rule("INSTRUMENT HINTS")

    for hint in feat_mod.get_instrument_hints(timbre):
        lines.append(f"  • {hint}")

    # ── Instrument analysis ───────────────────────────────────────────────────
    instr_data = results.get("instruments")
    if instr_data:
        lines.append("")
        rule("INSTRUMENT ANALYSIS")

        # HPSS per section
        isecs = instr_data.get("sections", [])
        if isecs:
            lines.append("  Harmonic / Percussive split per section:")
            lines.append(f"  {'§':>3}  {'Harmonic':>10}  {'Percussive':>11}  "
                         f"{'Flatness':>9}  Pitch centre   Vibrato  Note dur")
            lines.append(f"  {'─'*3}  {'─'*10}  {'─'*11}  {'─'*9}  {'─'*13}   {'─'*7}  {'─'*8}")
            for s in isecs:
                h = s["hpss"]
                p = s["pitch"]
                pitch_str = f"{p['f0_median_note']:>5}" if p and p.get("f0_median_note") else "  n/a"
                vib_str   = ("yes" if p and p.get("vibrato") else "no ") if p else " - "
                dur_str   = f"{p['median_note_dur_s']:.2f} s" if p and p.get("median_note_dur_s") else "  n/a"
                lines.append(
                    f"  {s['idx']:>3}  "
                    f"{h['harm_ratio']*100:>8.1f}%  "
                    f"{h['perc_ratio']*100:>9.1f}%  "
                    f"{h['flatness']:>9.4f}  "
                    f"{pitch_str:>13}   "
                    f"{vib_str:>7}  "
                    f"{dur_str}"
                )

        # Maqam comparison
        maqam = instr_data.get("maqam_matches", [])
        if maqam:
            lines.append("")
            lines.append("  Scale / Maqam comparison (cosine similarity to pitch-class histogram):")
            for m in maqam[:5]:
                score_bar = bar(m["score"], 18, 1.0)
                lines.append(f"    {score_bar}  {m['score']:.3f}  {m['name']}")

        # Instrument estimates
        estimates = instr_data.get("estimates", [])
        if estimates:
            lines.append("")
            lines.append("  Instrument estimates:")
            lines.append("")
            prev_family = None
            for e in estimates:
                if e["family"] != prev_family:
                    family_label = {
                        "melodic":    "MELODIC",
                        "harmonic":   "HARMONIC / PADS",
                        "bass":       "BASS",
                        "percussion": "PERCUSSION",
                    }.get(e["family"], e["family"].upper())
                    lines.append(f"    [{family_label}]")
                    prev_family = e["family"]
                conf_marker = {"HIGH": "●●●", "MEDIUM": "●●○", "LOW": "●○○"}.get(e["confidence"], "?")
                lines.append(f"      {conf_marker} {e['confidence']:<7}  {e['name']}")
                lines.append(f"               {e['evidence']}")

    lines.append("")
    lines.append("=" * _WIDTH)
    return "\n".join(lines)


def _fmt(seconds: float) -> str:
    """Format seconds as H:MM:SS or M:SS."""
    s = int(round(seconds))
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    if h:
        return f"{h}:{m:02d}:{sec:02d}"
    return f"{m}:{sec:02d}"
