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

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from forge.runner import project_main
from forge.spec.schema import PatternSpec, ProjectSpec, SectionSpec, TrackSpec


def build_project() -> ProjectSpec:
    """Build the ProjectSpec for the mini Sleeper Awakens track."""
    bpm = 145.0

    kick_track = TrackSpec(
        instrument="kick",
        steps=[1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
        params={"f0": 55.0, "duration": 0.35},
    )
    bass_track = TrackSpec(
        instrument="psy_bass",
        steps=[1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        params={"midi": 26, "duration": 0.42},
    )
    hat_track = TrackSpec(
        instrument="hat",
        steps=[1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
        params={"open_": False},
        probability=0.9,
    )
    acid_track = TrackSpec(
        instrument="acid",
        steps=[0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0],
        params={"midi": 38, "cutoff": 600.0, "duration": 0.22},
        bars=list(range(4, 12)),
    )
    wind_track = TrackSpec(
        instrument="wind",
        steps=[1] + [0] * 15,
        params={"duration": 1.5},
    )

    intro = SectionSpec("intro", start_bar=0, length_bars=4,
                        schedules=[PatternSpec(bpm=bpm, length_bars=4,
                                              tracks=[kick_track, bass_track, hat_track])],
                        gain=0.7)
    drop = SectionSpec("drop", start_bar=4, length_bars=8,
                       schedules=[PatternSpec(bpm=bpm, length_bars=8,
                                             tracks=[kick_track, bass_track, hat_track, acid_track])])
    outro = SectionSpec("outro", start_bar=12, length_bars=4,
                        schedules=[PatternSpec(bpm=bpm, length_bars=4,
                                              tracks=[kick_track, bass_track])],
                        gain=0.6)
    wind_sec = SectionSpec("wind", start_bar=0, length_bars=16,
                           schedules=[PatternSpec(bpm=bpm, length_bars=16,
                                                 tracks=[wind_track])],
                           gain=0.3)

    return ProjectSpec(
        title="Sleeper Awakens Mini",
        bpm=bpm,
        seed=145,
        sections=[intro, drop, outro, wind_sec],
        master_gain_curve=[[0, 0.0], [2, 1.0], [14, 1.0], [16, 0.0]],
        fade_out_s=2.0,
    )


if __name__ == "__main__":
    project_main(build_project, Path("out/sleeper_awakens_mini.wav"))
