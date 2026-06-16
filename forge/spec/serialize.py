"""forge.spec.serialize — JSON-safe serialization and deserialization.

load_project / save_project are the canonical entry points.  They use stdlib
json and pathlib.Path so there are no extra dependencies.
"""

from __future__ import annotations

import json
from pathlib import Path

from forge.spec.schema import ProjectSpec
from forge.spec.validate import validate_project


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
