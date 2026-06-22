"""soundmatch.core.target — load audio, select region, pick stem → Metrics.

Uses ``inspector.features.load_audio`` and ``inspector.separation.separate_stems``
for loading and separation; ``inspector.metrics.characterize`` for measurement.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np

from inspector.metrics import Metrics, characterize


class Target:
    """A reference audio target: file path + time region + stem choice.

    Attributes:
        path:    Path to the source audio file.
        start_s: Start of the selection in seconds.
        end_s:   End of the selection in seconds.
        stem:    Stem name (e.g. ``"other"``); ``"mix"`` means no separation.
        metrics: Measured characteristics (populated after ``characterize()``).
        y:       Audio samples (mono, at analysis SR).
        sr:      Analysis sample rate.
    """

    def __init__(
        self,
        path: Path,
        start_s: float,
        end_s: float,
        stem: str = "other",
        y: Optional[np.ndarray] = None,
        sr: int = 22050,
        metrics: Optional[Metrics] = None,
    ) -> None:
        self.path = path
        self.start_s = start_s
        self.end_s = end_s
        self.stem = stem
        self.y = y
        self.sr = sr
        self.metrics = metrics

    @classmethod
    def from_file(
        cls,
        path: Path,
        start_s: float,
        end_s: float,
        stem: str = "other",
        sr: int = 22050,
    ) -> Target:
        """Load audio, optionally separate stems, and characterize.

        If ``stem != "mix"``, runs demucs separation on the selected region
        and uses the chosen stem.  Gracefully degrades if demucs is absent.
        """
        from inspector.features import load_audio

        audio = load_audio(str(path), sr=sr, offset=start_s, end=end_s)
        y: np.ndarray = audio["y"]

        if stem != "mix":
            y = cls._extract_stem(y, str(path), start_s, end_s, stem, sr)

        metrics = characterize(y, sr)
        return cls(
            path=path,
            start_s=start_s,
            end_s=end_s,
            stem=stem,
            y=y,
            sr=sr,
            metrics=metrics,
        )

    @staticmethod
    def _extract_stem(
        mix_y: np.ndarray,
        path: str,
        start_s: float,
        end_s: Optional[float],
        stem: str,
        sr: int,
    ) -> np.ndarray:
        """Attempt demucs stem extraction; fall back to the mix on failure."""
        from inspector.separation import separate_stems
        result, reason = separate_stems(
            path, offset=start_s, end=end_s, sr=sr,
        )
        if result is not None and stem in result.get("names", []):
            mono_key = f"{stem}_mono"
            if mono_key in result:
                return result[mono_key].copy()
        # Graceful degradation: return the mix as-is
        return mix_y

    def to_dict(self) -> dict:
        """Serialize for project save."""
        return {
            "path": str(self.path),
            "start_s": self.start_s,
            "end_s": self.end_s,
            "stem": self.stem,
            "sr": self.sr,
            "metrics": self.metrics.to_dict() if self.metrics else None,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Target:
        """Deserialize from project load."""
        metrics = Metrics.from_dict(d["metrics"]) if d.get("metrics") else None
        return cls(
            path=Path(d["path"]),
            start_s=d["start_s"],
            end_s=d["end_s"],
            stem=d.get("stem", "other"),
            sr=d.get("sr", 22050),
            metrics=metrics,
        )
