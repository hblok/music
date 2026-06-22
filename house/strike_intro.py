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


def compose(seed: int = 7) -> AudioBuffer:
    root = RngContext(seed)
    mix = AudioBuffer(int(TOTAL * SR), SR)
    ir_L, ir_R = make_stereo_ir_pair(2.6, 0.9, sr=SR, lp_cutoff=3200.0)

    # ── Lead: dense 4-note chord stabs (deep dark reverb plate) ─────────────
    lead_rng = root.spawn("lead")
    for i, (start_s, chord_key) in enumerate(STABS):
        chord = CHORDS[chord_key]
        # Compute per-stab duration — longer overlapping tails blur into a wash
        if i + 1 < len(STABS):
            next_start = STABS[i + 1][0]
            dur = min(max(0.9 * (next_start - start_s), 0.32), 0.5)
        else:
            dur = 0.4

        # Per-stab attack variation: all tones in the chord share one attack
        # time so the chord stays tight, but different stabs swell differently.
        stab_rng = lead_rng.spawn(f"stab{i}")
        att = float(stab_rng.rng.uniform(0.05, 0.15))

        # Render each chord tone separately then sum
        stab_L = np.zeros(int((dur + 0.8) * SR))  # extra tail for reverb
        stab_R = np.zeros(int((dur + 0.8) * SR))
        tone_gain = G_LEAD / len(chord) ** 0.5     # ~0.425 per tone (4 tones)
        for midi in chord:
            buf = synth_brass(
                {"notes": [(midi, dur)], "attack": att, "lp_cutoff": 6000.0},
                stab_rng.spawn(f"t{midi}").rng,
                sr=SR,
            )
            n = min(len(buf.L), len(stab_L))
            stab_L[:n] += buf.L[:n]
            stab_R[:n] += buf.R[:n]

        # Deep dark plate reverb on the summed chord
        L, R = reverb_stereo(stab_L, stab_R, ir_L, ir_R, wet=0.40)
        mix.add_at(np.column_stack([L, R]), start_s, gain=tone_gain)

    # ── Bass: sustained G#1 pedal, re-struck every half-bar (pedal pulse) ─────
    if ENABLE_BASS:
        b_rng = root.spawn("bass")
        t = 0.0
        while t < TOTAL - 0.3:
            bass = bass_note({"midi": GS1, "duration": 1.3, "lp_cutoff": 1100.0,
                              "drive": 0.8, "sub_mix": 0.6},
                             b_rng.spawn(f"b{t:.2f}").rng, sr=SR)
            mix.add_at(bass.L, t, gain=G_BASS)
            t += 2 * BEAT

    # ── Drums: drop at beat 2, run to the end ────────────────────────────────
    if ENABLE_DRUMS:
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
    out_path = Path("/workspace/music/house_strike_intro.wav")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    print("Composing Strike It Up intro recreation …")
    mix = compose(seed=7)
    sf.write(str(out_path), mix.data, SR, subtype="PCM_24")
    dur = len(mix.data) / SR
    print(f"Written {out_path}  ({dur:.1f} s, {SR} Hz, 24-bit PCM)")
    rms = mix.section_rms(9)
    print("Section RMS arc:", " ".join(f"{x:.3f}" for x in rms))


if __name__ == "__main__":
    main()
