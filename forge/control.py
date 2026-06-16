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

    Args:
        project:     Project document (see forge.spec.schema.ProjectSpec).
        output_path: If given, the rendered WAV is also written here.
    """
    raise NotImplementedError("render_track: Phase 5 not yet implemented")


def load_project(path: Path) -> dict[str, Any]:
    """Load a project document from a JSON file.

    Returns the parsed project dict (see forge.spec.schema).
    """
    raise NotImplementedError("load_project: Phase 9 not yet implemented")


def save_project(project: dict[str, Any], path: Path) -> None:
    """Serialize a project document to a JSON file."""
    raise NotImplementedError("save_project: Phase 9 not yet implemented")
