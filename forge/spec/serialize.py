"""forge.spec.serialize — JSON-safe serialization and deserialization.

Two families of functions:
  Plan 2 / engine format  →  save_project / load_project / load_project_dict
  Plan 3 / tracker format →  save_project_doc / load_project_doc

A migrator converts Plan 2 dicts to the Plan 3 format so old project files
continue to load.  ``migrate_project_dict`` is idempotent on Plan 3 dicts.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from forge.spec.schema import ProjectSpec
from forge.spec.validate import validate_project

if TYPE_CHECKING:
    from forge.document.model import ProjectDoc


# ---------------------------------------------------------------------------
# Plan 2 / engine format

def save_project(project: "ProjectSpec | dict", path: Path) -> None:
    """Serialize *project* to *path* (creates parent directories).

    Args:
        project: ProjectSpec dataclass or equivalent dict.
        path:    Output JSON file path.
    """
    if isinstance(project, dict):
        d = project
    else:
        d = project.to_dict()

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(d, fh, indent=2, ensure_ascii=False)


def load_project(path: Path) -> ProjectSpec:
    """Deserialize and validate a project JSON file.

    Args:
        path: JSON file path.

    Returns:
        Validated ProjectSpec dataclass.

    Raises:
        FileNotFoundError: if *path* does not exist.
        json.JSONDecodeError: if the file is not valid JSON.
        ValueError: if the project fails schema validation.
        KeyError: if a required key is missing.
    """
    path = Path(path)
    with path.open("r", encoding="utf-8") as fh:
        d = json.load(fh)

    project = ProjectSpec.from_dict(d)
    validate_project(project)
    return project


def load_project_dict(path: Path) -> dict:
    """Load and validate a project JSON file, returning the raw dict.

    Useful for passing directly to ``control.render_track``.
    """
    return load_project(path).to_dict()


# ---------------------------------------------------------------------------
# Plan 3 / tracker document format

def save_project_doc(doc: "ProjectDoc", path: Path) -> None:
    """Serialize a ``ProjectDoc`` to *path* in the tracker JSON format.

    The file is atomic (written to a temp file then renamed) so a crash
    during write never leaves a corrupt file.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp.json")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(doc.to_dict(), fh, indent=2, ensure_ascii=False)
    tmp.replace(path)


def load_project_doc(path: Path) -> "ProjectDoc":
    """Load a ``ProjectDoc`` from *path*.

    Handles both Plan 3 (tracker) format and Plan 2 (engine) format.  Plan 2
    files are migrated automatically: pattern channels are extracted from
    section schedules and a section order list is created.

    Raises:
        FileNotFoundError: if *path* does not exist.
        json.JSONDecodeError: if the file is not valid JSON.
        KeyError: if a required field is missing after migration.
    """
    from forge.document.model import ProjectDoc
    path = Path(path)
    with path.open("r", encoding="utf-8") as fh:
        d = json.load(fh)
    d = migrate_project_dict(d)
    return ProjectDoc.from_dict(d)


# ---------------------------------------------------------------------------
# Migrator

def migrate_project_dict(d: dict) -> dict:
    """Convert a project dict to schema_version 3.0 (idempotent on 3.x dicts).

    Plan 2 dicts have ``sections[].schedules[].tracks[]`` but no ``channels``
    key.  This function promotes each unique instrument to a ``PatternChannel``
    entry and creates a flat ``sections`` order list.
    """
    if d.get("schema_version", "").startswith("3"):
        return d
    if "channels" in d and "schema_version" not in d:
        d = dict(d)
        d["schema_version"] = "3.0"
        return d

    # Plan 2 → Plan 3 promotion
    channels: list[dict] = []
    sections_out: list[dict] = []
    seen: dict[str, int] = {}  # instrument_id → channel index

    for sec in d.get("sections", []):
        sections_out.append({
            "name": str(sec.get("name", "section")),
            "length_bars": int(sec.get("length_bars", 8)),
        })
        for sched in sec.get("schedules", []):
            for track in sched.get("tracks", []):
                iid = str(track.get("instrument", "kick"))
                if iid not in seen:
                    seen[iid] = len(channels)
                    steps_raw = track.get("steps", [0] * 16)
                    steps = [_step_to_doc_dict(v) for v in steps_raw]
                    channels.append({
                        "kind": "pattern",
                        "instrument_id": iid,
                        "n_steps": len(steps),
                        "steps": steps,
                        "params": dict(track.get("params", {})),
                        "seed": 0,
                    })

    result: dict = {
        "schema_version": "3.0",
        "title": str(d.get("title", "Imported")),
        "bpm": float(d.get("bpm", 138.0)),
        "sr": int(d.get("sr", 44100)),
        "seed": int(d.get("seed", 0)),
        "normalize": bool(d.get("normalize", True)),
        "target": float(d.get("target", 0.85)),
        "fade_out_s": float(d.get("fade_out_s", 2.0)),
        "channels": channels,
        "sections": sections_out,
    }
    if "master_gain_curve" in d:
        result["master_gain_curve"] = d["master_gain_curve"]
    return result


def _step_to_doc_dict(v) -> dict:
    """Convert a compact step value to the ProjectDoc dict form."""
    if v is None or v == 0 or v is False:
        return {"on": False}
    if v == 1 or v is True:
        return {"on": True}
    if isinstance(v, dict):
        out: dict = {"on": bool(v.get("on", True))}
        for key in ("accent", "ghost", "probability", "params"):
            if key in v:
                out[key] = v[key]
        return out
    return {"on": bool(v)}
