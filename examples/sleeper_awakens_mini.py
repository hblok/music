"""examples/sleeper_awakens_mini.py — short forge-framework recreation.

A 16-bar psy-trance loop in the style of generate_sleeper_awakens.py,
expressed entirely through the forge framework.

Renders to ``out/sleeper_awakens_mini.wav`` when run directly.

Run::

    python examples/sleeper_awakens_mini.py
    # or with a custom output path:
    python examples/sleeper_awakens_mini.py --out /tmp/mini.wav
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add the repo root to the path so we can import forge without installing it.
sys.path.insert(0, str(Path(__file__).parent.parent))

from forge import control
from forge.arrange.curves import fade_in_out, sidechain_pump
from forge.arrange.section import Section
from forge.arrange.track import Track
from forge.patterns.schedule import Schedule
from forge.spec.schema import PatternSpec, ProjectSpec, SectionSpec, TrackSpec
from forge.spec.serialize import save_project


def build_project(output_wav: Path | None = None) -> ProjectSpec:
    """Build the ProjectSpec for the mini Sleeper Awakens track."""
    bpm = 145.0  # original seed = 145 BPM

    # -- Kick pattern: four-on-the-floor
    kick_track = TrackSpec(
        instrument="kick",
        steps=[1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
        params={"f0": 55.0, "duration": 0.35},
    )
    # -- Psy-bass: on beat 1 of each bar
    bass_track = TrackSpec(
        instrument="psy_bass",
        steps=[1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        params={"midi": 26, "duration": 0.42},
    )
    # -- Hi-hat: straight 8ths
    hat_track = TrackSpec(
        instrument="hat",
        steps=[1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
        params={"open_": False},
        probability=0.9,
    )
    # -- Acid line: syncopated, only in the drop (bars 4–12)
    acid_track = TrackSpec(
        instrument="acid",
        steps=[0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0],
        params={"midi": 38, "cutoff": 600.0, "duration": 0.22},
        bars=list(range(4, 12)),
    )
    # -- Wind texture: full track (added every bar)
    wind_track = TrackSpec(
        instrument="wind",
        steps=[1] + [0] * 15,
        params={"duration": 1.5},
    )

    # Intro section (bars 0–3): kick + bass + hat only
    intro_pattern = PatternSpec(
        bpm=bpm,
        length_bars=4,
        tracks=[kick_track, bass_track, hat_track],
    )
    intro = SectionSpec("intro", start_bar=0, length_bars=4,
                         schedules=[intro_pattern], gain=0.7)

    # Drop section (bars 4–11): full band
    drop_pattern = PatternSpec(
        bpm=bpm,
        length_bars=8,
        tracks=[kick_track, bass_track, hat_track, acid_track],
    )
    drop = SectionSpec("drop", start_bar=4, length_bars=8,
                        schedules=[drop_pattern])

    # Outro section (bars 12–15): kick + bass only
    outro_pattern = PatternSpec(
        bpm=bpm,
        length_bars=4,
        tracks=[kick_track, bass_track],
    )
    outro = SectionSpec("outro", start_bar=12, length_bars=4,
                         schedules=[outro_pattern], gain=0.6)

    # Wind texture spans the whole 16 bars
    wind_pattern = PatternSpec(
        bpm=bpm,
        length_bars=16,
        tracks=[wind_track],
    )
    wind_sec = SectionSpec("wind", start_bar=0, length_bars=16,
                            schedules=[wind_pattern], gain=0.3)

    return ProjectSpec(
        title="Sleeper Awakens Mini",
        bpm=bpm,
        seed=145,
        sections=[intro, drop, outro, wind_sec],
        master_gain_curve=[[0, 0.0], [2, 1.0], [14, 1.0], [16, 0.0]],
        fade_out_s=2.0,
    )


def render(output_wav: Path) -> None:
    project = build_project(output_wav)

    # Save the project spec alongside the WAV
    spec_path = output_wav.with_suffix(".json")
    save_project(project, spec_path)
    print(f"Saved project spec → {spec_path}")

    # Render via control facade
    buf = control.render_track(project.to_dict(), output_path=output_wav)
    print(f"Rendered {buf.len_seconds():.1f}s  peak={buf.peak():.4f}  → {output_wav}")


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path,
                        default=Path("out/sleeper_awakens_mini.wav"))
    args = parser.parse_args(argv)
    render(args.out)


if __name__ == "__main__":
    main()
