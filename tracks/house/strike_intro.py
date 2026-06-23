#!/usr/bin/env python3
"""
strike_intro.py — recreation of the Black Box "Strike It Up" INTRO (1–10 s).

Scope: only the ~9-second intro of the source, not the full track. No vocal and
no piano in this window — it's a bright synth-brass stab riff over a low bass
pedal, with the house beat dropping in.

Transcribed from the demucs-isolated stems of
``Black_Box-Strike_It_Up_Xo3kp5BLF6Q.mp3`` (seconds 1–10) — separating the mix
into stems first is what finally made the analysis reliable (whole-mix pitch
trackers gave four contradictory answers):

  • LEAD (stem "other") — dense **4-note chord stabs** (G# major vamp moving to
    B and C# major), ~38 stabs in a steady 8th/16th-note rhythm. Chord voicings:
    G# [G#3 C5 D#5 G#5], B [B3 D#5 F#5 B5], C# [C#4 F5 G#5 C#6].
    Two layers, matching how it's heard ("brass synth / sax / snare drum"):
      (1) tonal — a *staccato* saw-brass chord (synth_brass perc_decay), and
      (2) a bright noise "snap" at the onset (3-6.5 kHz burst, the snare-like
          chiff). The isolated stem reads ~82% percussive (HPSS) with a body
          that decays to 25% in ~60-100 ms — i.e. punchy stabs, not a sax swell.
          The earlier sustained version read 0.3% percussive and sounded wrong.
    Bass is currently silenced (ENABLE_BASS = False) — focusing on the brass lead.
  • BASS (stem "bass") — a sustained **G#1 pedal** (MIDI 32, ~52 Hz), the
    dominant pedal under the C#-minor centre.  Gated by ENABLE_BASS.
  • 117.5 BPM, dead-straight. Lead enters ~0.6 s after the drop; kick /
    offbeat open hat / backbeat clap drop at ~1 s (second 2 of the source).

Uses the ``synth_brass`` instrument (forge/instruments/synth.py), tuned to
match the isolated lead stem's spectrum.

Output: /workspace/music/house_strike_intro.wav
Run:    python3 -m house.strike_intro      (from /repos/music)
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from forge.core.buffer import AudioBuffer
from forge.core.rng import RngContext
from forge.core.mastering import master
from forge.core.reverb import make_stereo_ir_pair, reverb_stereo
from forge.core.dsp import bandpass

from forge.instruments.synth import synth_brass
from forge.instruments.bass import bass_note
from forge.instruments.percussion import make_kick, make_hat, make_clap

SR = 44100
BPM = 117.5
BEAT = 60.0 / BPM                     # 0.5106 s
TOTAL = 9.4                           # ~9 s intro + short tail

# Notes (concert pitch) from the isolated stems
GS1 = 32                             # bass: G#1 pedal (~52 Hz)

# ── Feature flags ─────────────────────────────────────────────────────────────
ENABLE_BASS  = False    # silenced for now — focusing on the brass lead
ENABLE_DRUMS = True

# ── Chord voicings (MIDI note numbers) ────────────────────────────────────────
CHORDS = {
    "Gs": [56, 72, 75, 80],   # G# major:  G#3 C5  D#5 G#5
    "B":  [59, 75, 78, 83],   # B  major:  B3  D#5 F#5 B5
    "Cs": [61, 77, 80, 85],   # C# major:  C#4 F5  G#5 C#6
}

# ── Stab sequence: (start_s, chord_key) — times are seconds from piece start
#    (= second 1.0 of the source).
STABS = [
    (1.09, "Gs"), (1.34, "Gs"), (1.59, "Gs"), (1.83, "Gs"), (2.07, "Gs"), (2.35, "Gs"),
    (2.48, "B"),  (2.73, "B"),  (2.86, "Cs"), (3.12, "Cs"),
    (3.36, "Gs"), (3.61, "Gs"), (3.75, "Gs"), (3.99, "Gs"), (4.15, "Gs"), (4.38, "Gs"),
    (4.51, "B"),  (4.75, "B"),  (4.88, "Cs"),
    (5.12, "Gs"), (5.39, "Gs"), (5.61, "Gs"), (5.88, "Gs"), (6.12, "Gs"), (6.39, "Gs"),
    (6.53, "B"),  (6.76, "B"),  (6.90, "Cs"), (7.15, "Cs"),
    (7.39, "Gs"), (7.66, "Gs"), (7.80, "Gs"), (8.05, "Gs"), (8.17, "Gs"), (8.42, "Gs"),
    (8.56, "B"),  (8.79, "Cs"), (8.95, "Gs"),
]

# Relative gains (master() peak-normalises afterwards)
G_LEAD = 0.85
G_KICK = 0.95
G_HAT  = 0.30
G_CLAP = 0.38
G_BASS = 0.70

# ── Lead timbre: percussive stab + noise "snare" snap ─────────────────────────
# The isolated lead stem reads ~82% percussive (HPSS): each hit is a *staccato*
# G#-major chord (mid-band decays to 25% in ~60-100 ms) topped by a bright noisy
# attack chiff at 3-6.5 kHz — the "snare drum" layer. Two layers, as heard.
STAB_DUR     = 0.34     # render length per stab; perc_decay shapes the real tail
STAB_ATTACK  = 0.004    # near-instant onset (sharp transient, not a sax swell)
STAB_DECAY   = 0.060    # exp-decay tau — staccato, drives the percussive feel
STAB_LP      = 7500.0   # tone lowpass; with the snap, hits source centroid ~2.5kHz
SNAP_LEVEL   = 0.16     # noise snap level, fraction of the chord's peak
SNAP_LO      = 3000.0   # snap band low edge
SNAP_HI      = 8000.0   # snap band high edge
SNAP_TAU     = 0.050    # snap decay tau (~70 ms to 25%)
REVERB_WET   = 0.03     # keep low — a long tail re-smears the staccato stabs
IR_SECONDS   = 0.30     # short, bright room (not a long dark plate)
IR_DECAY     = 0.6
IR_LP        = 7000.0


def compose(seed: int = 7, drums: bool | None = None, bass: bool | None = None) -> AudioBuffer:
    drums = ENABLE_DRUMS if drums is None else drums
    bass = ENABLE_BASS if bass is None else bass
    root = RngContext(seed)
    mix = AudioBuffer(int(TOTAL * SR), SR)
    # Tight, fairly dry room — the source lead is close-mic'd/dry, and a long
    # plate would smear the staccato snap that defines the sound.
    ir_L, ir_R = make_stereo_ir_pair(IR_SECONDS, IR_DECAY, sr=SR, lp_cutoff=IR_LP)

    # ── Lead: percussive G#-major chord stabs + noise snap (two layers) ──────
    lead_rng = root.spawn("lead")
    tone_gain = G_LEAD / len(next(iter(CHORDS.values()))) ** 0.5   # ~0.42/tone
    snap_env = np.exp(-np.arange(int(STAB_DUR * SR)) / (SNAP_TAU * SR))
    for i, (start_s, chord_key) in enumerate(STABS):
        chord = CHORDS[chord_key]
        stab_rng = lead_rng.spawn(f"stab{i}")

        # Layer 1 — tonal: each chord tone as a staccato (perc-decay) saw stab.
        stab_L = np.zeros(int((STAB_DUR + 0.6) * SR))  # extra tail for reverb
        stab_R = np.zeros(int((STAB_DUR + 0.6) * SR))
        for midi in chord:
            buf = synth_brass(
                {"notes": [(midi, STAB_DUR)], "attack": STAB_ATTACK,
                 "perc_decay": STAB_DECAY, "lp_cutoff": STAB_LP,
                 "bloom": 0.2, "rasp": 0.22},
                stab_rng.spawn(f"t{midi}").rng,
                sr=SR,
            )
            n = min(len(buf.L), len(stab_L))
            stab_L[:n] += buf.L[:n]
            stab_R[:n] += buf.R[:n]

        # Layer 2 — the "snare" snap: a short bright noise burst at the onset,
        # decorrelated L/R for width, scaled to the chord's own peak.
        peak = max(np.max(np.abs(stab_L)), np.max(np.abs(stab_R))) + 1e-12
        ne = len(snap_env)
        for ch, snap_rng in ((stab_L, stab_rng.spawn("snapL").rng),
                             (stab_R, stab_rng.spawn("snapR").rng)):
            nz = bandpass(snap_rng.standard_normal(ne), SNAP_LO, SNAP_HI, sr=SR)
            nz /= np.max(np.abs(nz)) + 1e-12
            ch[:ne] += SNAP_LEVEL * peak * nz * snap_env

        # Tight room reverb on the summed two-layer stab
        L, R = reverb_stereo(stab_L, stab_R, ir_L, ir_R, wet=REVERB_WET)
        mix.add_at(np.column_stack([L, R]), start_s, gain=tone_gain)

    # ── Bass: sustained G#1 pedal, re-struck every half-bar (pedal pulse) ─────
    if bass:
        b_rng = root.spawn("bass")
        t = 0.0
        while t < TOTAL - 0.3:
            bass = bass_note({"midi": GS1, "duration": 1.3, "lp_cutoff": 1100.0,
                              "drive": 0.8, "sub_mix": 0.6},
                             b_rng.spawn(f"b{t:.2f}").rng, sr=SR)
            mix.add_at(bass.L, t, gain=G_BASS)
            t += 2 * BEAT

    # ── Drums: drop at beat 2, run to the end ────────────────────────────────
    if drums:
        k_rng = root.spawn("kick")
        h_rng = root.spawn("hat")
        c_rng = root.spawn("clap")
        kick = make_kick({"f0": 52.0, "f1": 40.0, "duration": 0.5,
                          "drive": 1.6, "sub_level": 0.55}, k_rng.spawn("k").rng, sr=SR)
        clap = make_clap({}, c_rng.spawn("c").rng, sr=SR)

        n_beats = int((TOTAL - 0.4) / BEAT)
        for i in range(2, n_beats):                      # i = global beat index
            bt = i * BEAT
            mix.add_at(kick.L, bt, gain=G_KICK)          # four-on-the-floor
            oh = make_hat({"open_": True, "decay_open": 0.30},
                          h_rng.spawn(f"oh{i}").rng, sr=SR)
            mix.add_at(oh.L, bt + 0.5 * BEAT, gain=G_HAT)  # offbeat open hat
            if (i - 2) % 4 in (1, 3):                     # backbeat clap
                mix.add_at(clap.L, bt, gain=G_CLAP)

    return master(mix, target=0.92, fade_in_s=0.0, fade_out_s=0.5)


def main() -> None:
    out_dir = Path("/workspace/music")
    out_dir.mkdir(parents=True, exist_ok=True)
    print("Composing Strike It Up intro recreation …")

    full = compose(seed=7)
    full_path = out_dir / "house_strike_intro.wav"
    sf.write(str(full_path), full.data, SR, subtype="PCM_24")
    print(f"Written {full_path}  ({len(full.data)/SR:.1f} s, {SR} Hz, 24-bit PCM)")
    print("Section RMS arc:", " ".join(f"{x:.3f}" for x in full.section_rms(9)))

    # Lead-only render — A/B this against the isolated source "other" stem.
    lead = compose(seed=7, drums=False, bass=False)
    lead_path = out_dir / "house_strike_intro_leadonly.wav"
    sf.write(str(lead_path), lead.data, SR, subtype="PCM_24")
    print(f"Written {lead_path}  (lead only)")


if __name__ == "__main__":
    main()
