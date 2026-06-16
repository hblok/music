"""forge.spec.validate — validation for ProjectSpec dicts and dataclasses.

Raises ``ValueError`` with a descriptive message on the first problem found.
All functions accept either a dict or the corresponding dataclass.
"""

from __future__ import annotations

from forge.spec.schema import PatternSpec, ProjectSpec, SectionSpec, TrackSpec


# ---------------------------------------------------------------------------
# Public API

def validate_project(project) -> None:
    """Raise ValueError if *project* (dict or ProjectSpec) is invalid."""
    if isinstance(project, dict):
        project = ProjectSpec.from_dict(project)
    _check_project(project)


def validate_pattern(pattern) -> None:
    """Raise ValueError if *pattern* (dict or PatternSpec) is invalid."""
    if isinstance(pattern, dict):
        pattern = PatternSpec.from_dict(pattern)
    _check_pattern(pattern)


# ---------------------------------------------------------------------------
# Internal checks

def _check_project(p: ProjectSpec) -> None:
    if not p.title:
        raise ValueError("Project title must not be empty")
    if p.bpm <= 0:
        raise ValueError(f"bpm must be positive, got {p.bpm}")
    if not (1 <= p.sr <= 192000):
        raise ValueError(f"sr out of range: {p.sr}")
    if not (0.0 < p.target <= 1.0):
        raise ValueError(f"target out of range (0, 1]: {p.target}")
    if p.fade_out_s < 0:
        raise ValueError(f"fade_out_s must be >= 0, got {p.fade_out_s}")
    for sec in p.sections:
        _check_section(sec, p.bpm)
    if p.master_gain_curve is not None:
        if len(p.master_gain_curve) < 2:
            raise ValueError("master_gain_curve needs at least 2 points")
        for pt in p.master_gain_curve:
            if len(pt) != 2:
                raise ValueError(f"master_gain_curve point must be [bar, value]: {pt}")


def _check_section(s: SectionSpec, bpm: float) -> None:
    if not s.name:
        raise ValueError("Section name must not be empty")
    if s.start_bar < 0:
        raise ValueError(f"Section '{s.name}': start_bar must be >= 0")
    if s.length_bars <= 0:
        raise ValueError(f"Section '{s.name}': length_bars must be positive")
    if not (0.0 < s.gain <= 4.0):
        raise ValueError(f"Section '{s.name}': gain out of range (0, 4]: {s.gain}")
    for pattern in s.schedules:
        _check_pattern(pattern)


def _check_pattern(p: PatternSpec) -> None:
    if p.bpm <= 0:
        raise ValueError(f"Pattern bpm must be positive, got {p.bpm}")
    if p.length_bars <= 0:
        raise ValueError(f"Pattern length_bars must be positive, got {p.length_bars}")
    if p.n_steps < 1:
        raise ValueError(f"n_steps must be >= 1, got {p.n_steps}")
    for track in p.tracks:
        _check_track(track, p.n_steps)


def _check_track(t: TrackSpec, n_steps: int) -> None:
    if not t.instrument:
        raise ValueError("Track instrument must not be empty")
    if not (0.0 <= t.probability <= 1.0):
        raise ValueError(
            f"Track '{t.instrument}': probability out of [0, 1]: {t.probability}"
        )
    if len(t.steps) > n_steps:
        raise ValueError(
            f"Track '{t.instrument}': steps length {len(t.steps)} > n_steps {n_steps}"
        )
