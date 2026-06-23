#!/usr/bin/env python3
"""strike_variants.py — render a spread of lead-tone variants for A/B picking.

The locked recreation (``strike_intro.py``) matches the isolated source lead on
gross stats (≈82 % percussive, centroid ≈2.5 kHz). But a body-spectrum
comparison showed the tone was still off: the source brass has a *full chord
root* (80–300 Hz ≈ 18–20 % of energy) and strong upper-mid presence
(800–2500 Hz ≈ 41 %), whereas the first recreation suppressed the fundamental
(≈3 %) and piled energy into a ~700 Hz honk (300–800 Hz ≈ 65 %).

This module fixes the body (lower highpass, smaller body formant, stronger
presence formant) and then sweeps the two axes that matter by ear:

  • SNARE-NESS — the noise "snap" level / brightness at the onset
  • STACCATO   — the percussive decay time of the tonal stab

Each variant is rendered **lead-only** so it can be A/B'd directly against
``strike_stems/..._other.wav``. Measurements (percussive %, centroid, 4-band
balance) are printed next to the source target.

Output: /workspace/music/variants/strike_<name>.wav  (+ printed table)
Run:    python3 -m house.strike_variants      (from /repos/music)
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from forge.core.dsp import bandpass
from forge.instruments.synth import synth_brass

from house.strike_intro import CHORDS, STABS, SR, TOTAL

OUT_DIR = Path("/workspace/music/variants")
SOURCE_STEM = "/workspace/music/strike_stems/Black_Box-Strike_It_Up_Xo3kp5BLF6Q_other.wav"

# Source lead reference (measured): percussive %, centroid Hz, 4-band balance.
SRC_PERC, SRC_CENT = 82.0, 2542.0
SRC_BANDS = np.array([18.0, 30.0, 41.0, 7.0])   # 80-300 / 300-800 / 800-2500 / 2.5-9k


@dataclass
class Variant:
    name: str
    blurb: str
    # synth_brass body params
    hp_cutoff: float = 110.0
    formant_mix: float = 0.2
    formant2_hz: float = 1750.0
    formant2_mix: float = 1.4
    rolloff: float = 0.6
    drive: float = 2.0
    lp_cutoff: float = 9000.0
    rasp: float = 0.18
    # envelope
    stab_dur: float = 0.34
    attack: float = 0.004
    perc_decay: float = 0.060
    # noise snap ("snare")
    snap_level: float = 0.16
    snap_lo: float = 3000.0
    snap_hi: float = 8000.0
    snap_tau: float = 0.050
    sub_octave: float = 0.0   # >0 adds a tone an octave below the chord root at this gain
    extras: dict = field(default_factory=dict)


# ── The variant set ───────────────────────────────────────────────────────────
VARIANTS = [
    Variant("A_balanced",
            "Corrected body, balanced snap — the recommended new baseline."),
    Variant("B_more_snare",
            "Louder, brighter noise snap — pushes toward 'snare drum'.",
            snap_level=0.30, snap_hi=9500, perc_decay=0.050),
    Variant("C_more_sax",
            "Quiet snap + longer decay — smoother, more 'sax/brass' sustain.",
            snap_level=0.06, perc_decay=0.110, stab_dur=0.42),
    Variant("D_snappy_punch",
            "Very short decay, tight snap — maximum staccato punch.",
            perc_decay=0.040, snap_level=0.18, snap_tau=0.040),
    Variant("E_fuller_darker",
            "Fuller root, darker top — heavier, rounder brass stab.",
            hp_cutoff=60, lp_cutoff=6500, formant_mix=0.35, rolloff=0.7,
            snap_level=0.12, snap_hi=6500),
    Variant("F_brighter_edgy",
            "Brighter & grittier — saw edge + airy snap for a sharper attack.",
            rolloff=0.55, lp_cutoff=11000, drive=3.0, snap_level=0.22,
            snap_hi=10000),
    Variant("G_full_root",
            "Adds a sub-octave (G#2 ~104 Hz) + low highpass — matches the "
            "source's strong root weight (the missing low end).",
            hp_cutoff=45, rasp=0.10, sub_octave=0.5, formant_mix=0.25,
            snap_level=0.14, snap_hi=7500),
]


def render_lead(v: Variant, seed: int = 7) -> np.ndarray:
    """Render the full STAB sequence (lead only, stereo) for one variant."""
    rng = np.random.default_rng(seed)
    n_total = int(TOTAL * SR)
    L = np.zeros(n_total)
    R = np.zeros(n_total)
    snap_env = np.exp(-np.arange(int(v.stab_dur * SR)) / (v.snap_tau * SR))
    n_chord = len(next(iter(CHORDS.values())))
    tone_gain = 0.85 / n_chord ** 0.5
    for start_s, chord_key in STABS:
        chord = list(CHORDS[chord_key])
        gains = [1.0] * len(chord)
        if v.sub_octave > 0.0:
            chord.append(min(chord) - 12)   # octave below the chord root
            gains.append(v.sub_octave)
        nlen = int((v.stab_dur + 0.4) * SR)
        sL = np.zeros(nlen)
        sR = np.zeros(nlen)
        for midi, g in zip(chord, gains):
            buf = synth_brass(
                {"notes": [(midi, v.stab_dur)], "attack": v.attack,
                 "perc_decay": v.perc_decay, "hp_cutoff": v.hp_cutoff,
                 "formant_mix": v.formant_mix, "formant2_hz": v.formant2_hz,
                 "formant2_mix": v.formant2_mix, "rolloff": v.rolloff,
                 "drive": v.drive, "lp_cutoff": v.lp_cutoff, "bloom": 0.2,
                 "rasp": v.rasp, **v.extras},
                rng, sr=SR)
            n = min(len(buf.L), nlen)
            sL[:n] += g * buf.L[:n]
            sR[:n] += g * buf.R[:n]
        peak = max(np.max(np.abs(sL)), np.max(np.abs(sR))) + 1e-12
        ne = len(snap_env)
        for ch in (sL, sR):
            nz = bandpass(rng.standard_normal(ne), v.snap_lo, v.snap_hi, sr=SR)
            nz /= np.max(np.abs(nz)) + 1e-12
            ch[:ne] += v.snap_level * peak * nz * snap_env
        a = int(start_s * SR)
        n = min(nlen, n_total - a)
        L[a:a + n] += tone_gain * sL[:n]
        R[a:a + n] += tone_gain * sR[:n]
    peak = max(np.max(np.abs(L)), np.max(np.abs(R))) + 1e-12
    return np.column_stack([L / peak, R / peak])


def measure(stereo: np.ndarray) -> tuple[float, float, np.ndarray]:
    import librosa
    y = stereo.mean(axis=1)
    H, P = librosa.effects.hpss(y, margin=3.0)
    perc = 100 * np.sum(P ** 2) / (np.sum(H ** 2) + np.sum(P ** 2))
    cent = float(librosa.feature.spectral_centroid(y=y, sr=SR)[0].mean())
    sp = np.abs(np.fft.rfft(y * np.hanning(len(y))))
    f = np.fft.rfftfreq(len(y), 1 / SR)

    def be(lo, hi):
        return np.sum(sp[(f >= lo) & (f < hi)] ** 2)

    tot = be(80, 9000) + 1e-12
    bands = np.array([100 * be(80, 300) / tot, 100 * be(300, 800) / tot,
                      100 * be(800, 2500) / tot, 100 * be(2500, 9000) / tot])
    return perc, cent, bands


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Rendering {len(VARIANTS)} lead-only variants to {OUT_DIR}\n")
    hdr = f"{'variant':16s} {'perc%':>6s} {'cent':>6s}  {'bands 80-300/300-800/800-2500/2.5-9k':38s}"
    print(hdr)
    print(f"{'SOURCE (target)':16s} {SRC_PERC:6.1f} {SRC_CENT:6.0f}  "
          + " ".join(f"{x:8.1f}" for x in SRC_BANDS))
    print("-" * len(hdr))
    for v in VARIANTS:
        stereo = render_lead(v)
        out = OUT_DIR / f"strike_{v.name}.wav"
        sf.write(str(out), stereo, SR, subtype="PCM_24")
        perc, cent, bands = measure(stereo)
        print(f"{v.name:16s} {perc:6.1f} {cent:6.0f}  "
              + " ".join(f"{x:8.1f}" for x in bands) + f"   {v.blurb}")


if __name__ == "__main__":
    main()
