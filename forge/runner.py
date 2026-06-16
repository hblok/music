"""forge/runner.py — CLI helpers for rendering a ProjectSpec to a WAV file.

Typical usage in an examples script::

    from forge.runner import project_main
    from forge.spec.schema import ProjectSpec

    def build_project() -> ProjectSpec:
        ...

    if __name__ == "__main__":
        project_main(build_project, default_out=Path("out/my_track.wav"))
"""

from __future__ import annotations

import argparse
from pathlib import Path

from forge import control
from forge.core.buffer import AudioBuffer
from forge.spec.schema import ProjectSpec
from forge.spec.serialize import save_project


def render_project(project: ProjectSpec, output_wav: Path) -> AudioBuffer:
    """Render *project* to *output_wav*, saving the spec as a sibling JSON.

    Creates the output directory if it does not exist.  Returns the rendered
    :class:`~forge.core.buffer.AudioBuffer` so callers can inspect or test it.
    """
    output_wav = Path(output_wav)
    output_wav.parent.mkdir(parents=True, exist_ok=True)

    spec_path = output_wav.with_suffix(".json")
    save_project(project, spec_path)
    print(f"Saved spec  → {spec_path}")

    buf = control.render_track(project.to_dict(), output_path=output_wav)
    print(f"Rendered {buf.len_seconds():.1f}s  peak={buf.peak():.4f}  → {output_wav}")
    return buf


def project_main(
    build_fn,
    default_out: Path,
    argv=None,
) -> None:
    """Parse ``--out`` from *argv* and render the project returned by *build_fn*.

    Intended as the ``main()`` body of every example script::

        if __name__ == "__main__":
            project_main(build_project, Path("out/my_track.wav"))
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path(default_out))
    args = parser.parse_args(argv)
    render_project(build_fn(), args.out)
