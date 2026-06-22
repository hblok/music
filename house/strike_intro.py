#!/usr/bin/env python3
"""
strike_intro.py — "Strike Intro" (≈20 s house cut)

A programmatic house track built from the Black Box – "Strike It Up" intro
analysed in ``inspiration/black_box/intro_report.md``:

  • The hook is the three-note alto-sax riff — G#4, A#4, B4 (MIDI 68/70/71),
    the root, ♭3 and the passing tone of the G# minor / C# minor centre.
  • 117.5 BPM, dead-straight house grid (the source locks σ=0).
  • Harmony parks on a C# minor chord over a G# bass pedal (C#m/G#), the
    static tonic area the intro circles before its drop.

Arrangement (9 bars ≈ 18.4 s + reverb tail):

  bar 0  (0.0 s)   Solo sax: held G#4 (3 beats) → A#4. Big plate, no drums.
  bar 1  (2.0 s)   The riff enters (G# A# G# B A# G# A#); a reverse cymbal
                   and riser build toward the drop.
  bar 2  (4.1 s)   DROP — 4-on-the-floor kick, offbeat open hat, backbeat
                   clap, offbeat house bass. The sax hook loops.
  bars 3–7         Full groove, hook looping with small variation.
  bar 8  (16.3 s)  Land on a held G#4; one last kick on the downbeat of bar 9,
                   then the plate rings out cold.

Uses the new ``sax`` instrument (forge/instruments/reed.py).

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
from forge.core.grid import Grid
from forge.core.rng import RngContext
from forge.core.mastering import master
from forge.core.reverb import make_stereo_ir_pair, reverb_stereo

from forge.instruments.reed import sax_phrase
from forge.instruments.strings import pad_chord
from forge.instruments.bass import bass_note
from forge.instruments.percussion import make_kick, make_hat, make_clap
from forge.instruments.fx import rev_cymbal, riser

SR = 44100
BPM = 117.5
GRID = Grid(BPM, SR)
BEAT = 60.0 / BPM                     # 0.5106 s
TOTAL = 20.0                          # hard cap

# Notes (concert pitch) from the intro analysis
G4S, A4S, B4 = 68, 70, 71            # G#4, A#4, B4
# C#m/G# bed
PAD_CHORD = [49, 52, 56]             # C#3, E3, G#3  (C# minor triad)
BASS_MIDI = 44                       # G#2 pedal
SUB_MIDI = 32                        # G#1 weight on downbeats

# ── Relative gains (master() peak-normalises afterwards) ──────────────────────
G_SAX   = 0.90
G_PAD   = 0.16
G_KICK  = 0.95
G_HAT   = 0.34
G_CLAP  = 0.42
G_BASS  = 0.55
G_SUB   = 0.30
G_BUILD = 0.30


def _beats(seq: list[tuple[int, float]]) -> list[tuple[int, float]]:
    """Convert (midi, beats) → (midi, seconds)."""
    return [(m, b * BEAT) for m, b in seq]


# The looping riff (one bar): G# A# G# B A# G# A#(held) — tongued eighths + a
# quarter, leaving a sax "breath" at the bar's tail.
HOOK = _beats([(G4S, 0.5), (A4S, 0.5), (G4S, 0.5), (B4, 0.5),
               (A4S, 0.5), (G4S, 0.5), (A4S, 1.0)])
# A variation used on alternate bars (ends on the B passing tone).
HOOK_VAR = _beats([(G4S, 0.5), (A4S, 0.5), (G4S, 0.5), (A4S, 0.5),
                   (G4S, 0.5), (B4, 0.5), (A4S, 1.0)])
# Intro statement: long held G#4, then up to A#4.
INTRO_PHRASE = _beats([(G4S, 3.0), (A4S, 1.0)])
# Closing statement: held G#4.
OUTRO_PHRASE = _beats([(G4S, 4.0)])

# Rounded alto for the riff (centroid ~1.5 kHz, matching the source's groove
# sections); the exposed intro/outro held notes use the DARK_SAX voicing below
# (centroid ~1.25 kHz) to mirror the soft, dark held note in §1 of the source.
SAX_PARAMS = {
    "lp_cutoff": 3800.0, "reed": 1.4, "bright": 0.95,
    "formant_hz": 1050.0, "formant_mix": 0.55,
    "breath_level": 0.05, "chiff": 0.14,
    "vibrato_depth": 0.006, "vibrato_rate": 5.4, "vibrato_bloom": 0.9,
}
DARK_SAX = {"lp_cutoff": 2600.0, "reed": 1.2, "bright": 1.05,
            "formant_hz": 950.0, "formant_mix": 0.5}


def render_sax(notes, rng, **over) -> AudioBuffer:
    p = dict(SAX_PARAMS, notes=notes)
    p.update(over)
    return sax_phrase(p, rng, sr=SR)


def compose(seed: int = 7) -> AudioBuffer:
    root = RngContext(seed)
    mix = AudioBuffer(int(TOTAL * SR), SR)

    # Plate reverb for the sax (lush, the intro's defining space).
    ir_L, ir_R = make_stereo_ir_pair(2.0, 0.7, sr=SR, lp_cutoff=4500.0)

    def place_sax(notes, bar, rng, gain=G_SAX, wet=0.28, **over):
        dry = render_sax(notes, rng.rng, **over).L      # mono
        L, R = reverb_stereo(dry, dry, ir_L, ir_R, wet=wet)
        mix.add_at(np.column_stack([L, R]), GRID.bar_t(bar), gain=gain)

    sax_rng = root.spawn("sax")

    # bar 0 — solo intro (dark voicing, extra reverb, slow vibrato bloom)
    place_sax(INTRO_PHRASE, 0, sax_rng.spawn("intro"),
              gain=G_SAX, wet=0.38, vibrato_bloom=1.4, **DARK_SAX)

    # bar 1 — riff enters, still no drums
    place_sax(HOOK, 1, sax_rng.spawn("b1"), wet=0.30)

    # bars 2..7 — hook loops over the groove, alternating the variation
    for bar in range(2, 8):
        hook = HOOK if bar % 2 == 0 else HOOK_VAR
        place_sax(hook, bar, sax_rng.spawn(f"b{bar}"), wet=0.24)

    # bar 8 — land on a held G#4 (dark voicing, like the intro)
    place_sax(OUTRO_PHRASE, 8, sax_rng.spawn("outro"),
              gain=G_SAX * 0.95, wet=0.32, **DARK_SAX)

    # ── Pad: C#m/G# bed, swelling in under the intro, sustaining the groove ──
    pad_rng = root.spawn("pad")
    intro_pad = pad_chord(
        {"midi_notes": PAD_CHORD, "duration": 4.4, "attack": 2.2,
         "release": 1.6, "lp_cutoff": 1700.0}, pad_rng.spawn("intro").rng, sr=SR)
    mix.add_at(intro_pad.data, GRID.bar_t(0), gain=G_PAD * 0.8)
    groove_pad = pad_chord(
        {"midi_notes": PAD_CHORD, "duration": 14.5, "attack": 0.8,
         "release": 2.5, "lp_cutoff": 2000.0}, pad_rng.spawn("groove").rng, sr=SR)
    mix.add_at(groove_pad.data, GRID.bar_t(2), gain=G_PAD)

    # ── Build into the drop (end of bar 1 → downbeat of bar 2) ───────────────
    fx_rng = root.spawn("fx")
    rise = riser({"duration": 2.0, "f_start": 200.0, "f_end": 3500.0,
                  "noise_level": 0.6}, fx_rng.spawn("riser").rng, sr=SR)
    mix.add_at(rise.data if rise.data.ndim > 1 else rise.L,
               GRID.bar_t(2) - 2.0, gain=G_BUILD)
    cym = rev_cymbal({"duration": 1.6, "hp_cutoff": 5000.0},
                     fx_rng.spawn("cym").rng, sr=SR)
    mix.add_at(cym.data if cym.data.ndim > 1 else cym.L,
               GRID.bar_t(2) - 1.6, gain=G_BUILD * 0.9)

    # ── Drums + bass: the groove (bars 2..7) plus a final downbeat on bar 8 ──
    k_rng = root.spawn("kick")
    h_rng = root.spawn("hat")
    c_rng = root.spawn("clap")
    b_rng = root.spawn("bass")

    kick = make_kick({"f0": 52.0, "f1": 40.0, "duration": 0.5,
                      "drive": 1.6, "sub_level": 0.55}, k_rng.spawn("k").rng, sr=SR)
    clap = make_clap({}, c_rng.spawn("c").rng, sr=SR)

    for bar in range(2, 8):
        for beat in range(4):
            t = GRID.bar_t(bar, beat)
            # 4-on-the-floor kick
            mix.add_at(kick.L, t, gain=G_KICK)
            # offbeat open hat (the "and")
            oh = make_hat({"open_": True, "decay_open": 0.32},
                          h_rng.spawn(f"oh{bar}_{beat}").rng, sr=SR)
            mix.add_at(oh.L, t + 0.5 * BEAT, gain=G_HAT)
            # backbeat clap on beats 2 & 4
            if beat in (1, 3):
                mix.add_at(clap.L, t, gain=G_CLAP)
            # offbeat house bass bounce on G#2; soft sub on the downbeat
            bass = bass_note({"midi": BASS_MIDI, "duration": 0.34,
                              "lp_cutoff": 1500.0, "drive": 0.9, "sub_mix": 0.35},
                             b_rng.spawn(f"bs{bar}_{beat}").rng, sr=SR)
            mix.add_at(bass.L, t + 0.5 * BEAT, gain=G_BASS)
            if beat == 0:
                sub = bass_note({"midi": SUB_MIDI, "duration": 0.5,
                                 "lp_cutoff": 900.0, "drive": 0.7, "sub_mix": 0.6},
                                b_rng.spawn(f"sub{bar}").rng, sr=SR)
                mix.add_at(sub.L, t, gain=G_SUB)

    # Final "button": one kick on the bar-8 downbeat, then let it ring out cold.
    mix.add_at(kick.L, GRID.bar_t(8), gain=G_KICK)
    mix.add_at(clap.L, GRID.bar_t(8), gain=G_CLAP * 0.8)

    return master(mix, target=0.92, fade_in_s=0.0, fade_out_s=1.4)


def main() -> None:
    out_path = Path("/workspace/music/house_strike_intro.wav")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    print("Composing house_strike_intro …")
    mix = compose(seed=7)
    sf.write(str(out_path), mix.data, SR, subtype="PCM_24")
    dur = len(mix.data) / SR
    print(f"Written {out_path}  ({dur:.1f} s, {SR} Hz, 24-bit PCM)")
    rms = mix.section_rms(10)
    print("Section RMS arc:", " ".join(f"{x:.3f}" for x in rms))


if __name__ == "__main__":
    main()
