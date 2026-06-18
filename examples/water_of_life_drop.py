"""examples/water_of_life_drop.py — dune track → Forge tracker project.

Converts the **DROP 1 ("the agony")** groove of
``dune/generate_water_of_life.py`` into a loadable Forge tracker project
(schema 3.0).  Run this to (re)generate ``water_of_life_drop.json``, which
can be opened in the Forge GUI (File → Open Tracker Project) and played.

Why the drop and not the whole track: the Forge document→playback path
renders every PatternChannel as a *single 16-step pattern looped across the
whole length* — it does not yet honour per-section step variation, texture
channels, automation/gain curves, or loop-fold (see
``plans/forge_play_dune_tracks.md``).  DROP 1 is the one part of
water_of_life that *is* a repeating 16-step psy-trance groove built from
instruments that all already exist in the Forge registry, so it round-trips
faithfully.  The melodic drift (acid cutoff sweep, bass cadence walk, octave
flicks) and every non-rhythmic layer (wind, drone, strings, duduk, ney,
chant, zaps, risers, war drums) are intentionally out of scope here and are
catalogued in the plan doc.

Source groove (water_of_life.py, bars 64–95, 140 BPM, D Phrygian dominant):

  kick      4-on-the-floor                       (150→45 Hz trance kick)
  psy_bass  K-b-b-b rolling bass on D2            (the three 16ths per beat)
  acid      RIFF_DARK 303 line                    (cutoff ~900, mid-sweep)
  hat open  offbeat 8ths
  hat closed 16th ghosts
  doum/tek  maqsum darbuka {0:D,2:T,6:T,8:D,12:T}

Mapping notes / deliberate approximations (full list in the plan doc):
  * Per-step velocity (bass .8/.7/.95, darbuka level) collapses to
    on/accent/ghost — the tracker has no continuous per-step gain.
  * Acid cutoff is fixed at the mid-sweep value; the original sweeps it
    over each 16-bar phrase.
  * Stereo placement / Haas / reverb sends are dropped (mono per channel).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from forge.document.channels import PatternChannel, StepData  # noqa: E402
from forge.document.model import ProjectDoc  # noqa: E402
from forge.spec.serialize import save_project_doc  # noqa: E402

BPM = 140.0
SEED = 140  # the tempo is the seed — from generate_water_of_life.py
N_STEPS = 16


def _steps(on_steps: dict[int, dict] | set[int], n: int = N_STEPS) -> list[StepData]:
    """Build a 16-slot step list.

    ``on_steps`` may be a set of indices (plain on) or a dict mapping an
    index to a kwargs dict for ``StepData`` (params/accent/ghost).
    """
    out = [StepData(on=False) for _ in range(n)]
    if isinstance(on_steps, set):
        for i in on_steps:
            out[i] = StepData(on=True)
    else:
        for i, kw in on_steps.items():
            out[i] = StepData(on=True, **kw)
    return out


def build_doc() -> ProjectDoc:
    doc = ProjectDoc(title="Water of Life — Drop 1 (the agony)",
                     bpm=BPM, sr=44100, seed=SEED)

    # --- kick: four to the floor (trance kick: 150→45 Hz, tight) ----------
    doc.add_channel(PatternChannel(
        instrument_id="kick",
        steps=_steps({0, 4, 8, 12}),
        params={"f0": 150.0, "f1": 45.0, "duration": 0.30,
                "drive": 1.2, "sub_level": 0.3, "attack": 0.001},
    ))

    # --- psy bass: K-b-b-b rolling D2 (the 3 sixteenths after each kick) ---
    doc.add_channel(PatternChannel(
        instrument_id="psy_bass",
        steps=_steps({1, 2, 3, 5, 6, 7, 9, 10, 11, 13, 14, 15}),
        params={"midi": 38, "duration": 0.10},  # D2, tight gate
    ))

    # --- acid: RIFF_DARK (50=D3 root; accents brighten the 303 filter) ----
    riff_dark = {
        0:  {"params": {"midi": 50, "accent": True}},
        2:  {"params": {"midi": 50}},
        4:  {"params": {"midi": 50}},
        5:  {"params": {"midi": 62, "accent": True}},
        7:  {"params": {"midi": 50}},
        8:  {"params": {"midi": 51}},
        10: {"params": {"midi": 50}},
        12: {"params": {"midi": 54, "accent": True}},
        14: {"params": {"midi": 48}},
        15: {"params": {"midi": 50}},
    }
    doc.add_channel(PatternChannel(
        instrument_id="acid",
        steps=_steps(riff_dark),
        params={"cutoff": 900.0, "duration": 0.12,
                "resonance_q": 1.4, "drive": 2.0},
    ))

    # --- hats: offbeat open 8ths -----------------------------------------
    doc.add_channel(PatternChannel(
        instrument_id="hat",
        steps=_steps({2, 6, 10, 14}),
        params={"open_": True},
    ))
    # --- hats: closed 16th ghosts (odd steps) ----------------------------
    doc.add_channel(PatternChannel(
        instrument_id="hat",
        steps=_steps({i: {"ghost": True} for i in (1, 3, 5, 7, 9, 11, 13, 15)}),
        params={"open_": False},
    ))

    # --- darbuka: maqsum {0:D, 2:T, 6:T, 8:D, 12:T} ----------------------
    doc.add_channel(PatternChannel(
        instrument_id="doum",
        steps=_steps({0, 8}),
        params={"f0": 90.0, "f1": 55.0, "duration": 0.30},
    ))
    doc.add_channel(PatternChannel(
        instrument_id="tek",
        steps=_steps({2, 6, 12}),
        params={"duration": 0.12},
    ))

    # One section: the drop, looped. (Playback loops the single pattern.)
    doc.add_section("drop — the agony", length_bars=16)
    return doc


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path,
                    default=Path(__file__).parent / "water_of_life_drop.json",
                    help="tracker project JSON output path")
    ap.add_argument("--wav", type=Path, default=None,
                    help="also render a WAV here (via control.export_wav_from_doc)")
    args = ap.parse_args()

    doc = build_doc()
    save_project_doc(doc, args.out)
    print(f"Wrote tracker project: {args.out}  "
          f"({doc.channel_count()} channels, {len(doc.sections)} section)")

    if args.wav is not None:
        from forge import control
        buf = control.export_wav_from_doc(doc, args.wav)
        print(f"Rendered WAV: {args.wav}  "
              f"({buf.data.shape[0] / doc.sr:.1f}s, peak {buf.peak():.3f})")


if __name__ == "__main__":
    main()
