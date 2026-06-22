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

  • LEAD (stem "other") — a bright **synth-brass stab** riff, pitch classes
    G#/B/C# in a LOW register: G#3, B2, C#3 (MIDI 56/47/49). A 5–♭7–root cell
    over the pedal. Timbre: centroid ~2.5 kHz, suppressed fundamental, a
    resonant body formant up at the 5th–6th harmonic — NOT a mellow sax.
  • BASS (stem "bass") — a sustained **G#1 pedal** (MIDI 32, ~52 Hz), the
    dominant pedal under the C#-minor centre.
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
GS3, B2, CS3 = 56, 47, 49            # lead: G#3, B2, C#3
GS1 = 32                             # bass: G#1 pedal (~52 Hz)

# ── Lead: (start_s, midi, dur_s) — synth-brass stabs transcribed from the
#    "other" stem, shifted so the piece starts at t=0 (= second 1.0 of source).
LEAD = [
    (1.62, GS3, 0.17),
    (2.00, B2, 0.20), (2.49, B2, 0.37), (2.87, CS3, 0.42),     # B B C# cell
    (3.50, B2, 0.18),
    (4.18, GS3, 0.20),
    (4.50, B2, 0.20), (4.76, B2, 0.13), (4.89, CS3, 0.21),     # cell again
    (6.52, B2, 0.20), (6.75, B2, 0.17), (6.92, CS3, 0.22), (7.18, CS3, 0.17),
    (8.56, B2, 0.19), (8.83, CS3, 0.14),
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
    ir_L, ir_R = make_stereo_ir_pair(1.3, 0.5, sr=SR, lp_cutoff=5000.0)

    # ── Lead synth-brass stabs (light plate for space) ───────────────────────
    lead_rng = root.spawn("lead")
    for i, (t, midi, dur) in enumerate(LEAD):
        buf = synth_brass({"notes": [(midi, dur)]}, lead_rng.spawn(f"n{i}").rng, sr=SR)
        L, R = reverb_stereo(buf.L, buf.R, ir_L, ir_R, wet=0.15)
        mix.add_at(np.column_stack([L, R]), t, gain=G_LEAD)

    # ── Bass: sustained G#1 pedal, re-struck every half-bar (pedal pulse) ─────
    b_rng = root.spawn("bass")
    t = 0.0
    while t < TOTAL - 0.3:
        bass = bass_note({"midi": GS1, "duration": 1.3, "lp_cutoff": 1100.0,
                          "drive": 0.8, "sub_mix": 0.6},
                         b_rng.spawn(f"b{t:.2f}").rng, sr=SR)
        mix.add_at(bass.L, t, gain=G_BASS)
        t += 2 * BEAT

    # ── Drums: drop at beat 2, run to the end ────────────────────────────────
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
