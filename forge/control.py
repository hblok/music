"""forge.control — GUI-agnostic facade for the forge engine.

The UI talks exclusively through this module.  Engine internals (synthesis,
DSP, file I/O) are never imported by the UI directly.

All methods raise NotImplementedError until the corresponding engine phase
is complete.  This lets the Qt shell (Phase 7) be wired and tested against
stub responses before real synthesis lands.

Completed stubs are filled in phase-by-phase:
  Phase 3 → list_instruments, render_instrument
  Phase 4 → render_pattern
  Phase 5 → render_track
  Phase 9 → load_project, save_project
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Instrument queries

def list_instruments() -> list[dict]:
    """Return the registry of available instruments.

    Each entry: ``{"id": str, "family": str, "params": list[ParamSchema]}``.
    """
    from forge.instruments.registry import list_instruments as _list
    return _list()


def render_instrument(
    instrument_id: str,
    params: dict[str, Any],
    seed: int = 0,
) -> "forge.core.buffer.AudioBuffer":  # type: ignore[name-defined]
    """Render a single instrument hit/note/texture to an AudioBuffer.

    Args:
        instrument_id: Registry key (e.g. ``"kick"``, ``"wind"``).
        params:        Parameter dict; keys match the instrument's param schema.
        seed:          RNG seed for this render.
    """
    from forge.instruments.registry import get_instrument
    from forge.core.rng import RngContext
    entry = get_instrument(instrument_id)
    rng = RngContext(seed).spawn(instrument_id).rng
    return entry["fn"](params, rng)


# ---------------------------------------------------------------------------
# Pattern queries

def render_pattern(
    pattern: dict[str, Any],
    seed: int = 0,
) -> "forge.core.buffer.AudioBuffer":  # type: ignore[name-defined]
    """Render a step pattern to an AudioBuffer.

    Args:
        pattern: Pattern document (see forge.spec.schema.PatternSpec).
        seed:    RNG seed.
    """
    from forge.patterns.groove import render_pattern_spec
    return render_pattern_spec(pattern, seed=seed)


# ---------------------------------------------------------------------------
# Track / project queries

def render_track(
    project: dict[str, Any],
    output_path: Path | None = None,
) -> "forge.core.buffer.AudioBuffer":  # type: ignore[name-defined]
    """Render a complete project to an AudioBuffer (and optionally to WAV).

    ProjectSpec format::

        {
            "title": "My Track",
            "bpm": 138.0,
            "seed": 0,
            "sections": [
                {
                    "name": "intro",
                    "start_bar": 0,
                    "length_bars": 8,
                    "gain": 1.0,
                    "schedules": [ <PatternSpec>, ... ]
                }
            ],
            "master_gain_curve": [[bar, value], ...],  # optional
            "normalize": true,
            "fade_out_s": 2.0
        }

    Args:
        project:     Project document.
        output_path: If given, the rendered WAV is also written here.
    """
    from forge.arrange.section import Section
    from forge.arrange.track import Track
    from forge.patterns.schedule import Schedule

    bpm = float(project["bpm"])
    seed = int(project.get("seed", 0))
    title = str(project.get("title", "track"))
    sr = int(project.get("sr", 44100))

    track = Track(bpm, title=title, sr=sr)

    for sec_spec in project.get("sections", []):
        sec = Section(
            name=str(sec_spec["name"]),
            start_bar=int(sec_spec["start_bar"]),
            length_bars=int(sec_spec["length_bars"]),
            gain=float(sec_spec.get("gain", 1.0)),
        )
        for sched_spec in sec_spec.get("schedules", []):
            sched_spec = dict(sched_spec)
            if "bpm" not in sched_spec:
                sched_spec["bpm"] = bpm
            if "length_bars" not in sched_spec:
                sched_spec["length_bars"] = sec.length_bars
            sec.add_schedule(Schedule.from_pattern_spec(sched_spec))
        track.add_section(sec)

    if "master_gain_curve" in project:
        from forge.arrange.curves import Curve
        track.set_master_gain_curve(Curve(project["master_gain_curve"]))

    return track.render(
        seed=seed,
        normalize=bool(project.get("normalize", True)),
        target=float(project.get("target", 0.85)),
        fade_out_s=float(project.get("fade_out_s", 2.0)),
        output_path=Path(output_path) if output_path is not None else None,
    )


def load_project(path: Path) -> dict[str, Any]:
    """Load a project document from a JSON file.

    Returns the parsed and validated project dict (see forge.spec.schema).
    Raises FileNotFoundError, json.JSONDecodeError, or ValueError on bad input.
    """
    from forge.spec.serialize import load_project_dict
    return load_project_dict(Path(path))


def save_project(project: dict[str, Any], path: Path) -> None:
    """Serialize a project document to a JSON file."""
    from forge.spec.serialize import save_project as _save
    _save(project, Path(path))
