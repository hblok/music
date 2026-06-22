"""soundmatch.ui.stems_panel — separate (async) + per-stem audition/solo + "set target".

Runs demucs separation on a QThread with a progress indicator.  Per-stem rows
allow audition (via PlaybackService), solo, and choosing a stem as the target.
Disabled with a clear message if demucs/torch are absent.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

import numpy as np

from PySide6.QtCore import QThread, Signal, QObject
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from forge.playback.service import PlaybackService

log = logging.getLogger(__name__)

# Check if demucs is available at import time
_DEMUCS_AVAILABLE = False
try:
    import torch  # noqa: F401
    import demucs  # noqa: F401
    _DEMUCS_AVAILABLE = True
except ImportError:
    pass


class _SeparationWorker(QObject):
    """Worker that runs demucs separation in a background thread."""

    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, path: str, start_s: float, end_s: float | None, sr: int):
        super().__init__()
        self._path = path
        self._start_s = start_s
        self._end_s = end_s
        self._sr = sr

    def run(self) -> None:
        t0 = time.perf_counter()
        log.debug("separation starting: %s offset=%.1fs", self._path, self._start_s)
        try:
            from inspector.separation import separate_stems
            result, reason = separate_stems(
                self._path, offset=self._start_s, end=self._end_s, sr=self._sr,
            )
            if result is not None:
                names = result.get("names", [])
                log.debug("separation done: stems=%s (%.2fs)", names, time.perf_counter() - t0)
                self.finished.emit(result)
            else:
                log.warning("separation returned no results: %s", reason)
                self.error.emit(reason or "Separation returned no results")
        except Exception as exc:
            log.error("separation error: %s", exc, exc_info=True)
            self.error.emit(str(exc))


class StemRow(QWidget):
    """A single stem row: name label + play button + "Set Target" button.

    Signals:
        targetChosen(stem_name): Emitted when "Set Target" is clicked.
    """

    targetChosen = Signal(str)

    def __init__(
        self,
        stem_name: str,
        mono_audio: np.ndarray | None,
        sr: int,
        service: PlaybackService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._stem_name = stem_name
        self._mono = mono_audio
        self._sr = sr
        self._service = service

        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)

        self._name_label = QLabel(stem_name)
        self._name_label.setMinimumWidth(80)
        layout.addWidget(self._name_label)

        self._play_btn = QPushButton("▶")
        self._play_btn.setMaximumWidth(40)
        self._play_btn.clicked.connect(self._on_play)
        self._play_btn.setEnabled(mono_audio is not None)
        layout.addWidget(self._play_btn)

        layout.addStretch()

        self._target_btn = QPushButton("Set Target")
        self._target_btn.setObjectName(f"target-btn-{stem_name}")
        self._target_btn.clicked.connect(self._on_set_target)
        self._target_btn.setEnabled(mono_audio is not None)
        layout.addWidget(self._target_btn)

    def _on_play(self) -> None:
        if self._mono is None:
            return
        from forge.core.buffer import AudioBuffer
        log.debug("playing stem: %s", self._stem_name)
        buf = AudioBuffer.from_mono(self._mono, sr=self._sr)
        self._service.load(buf)
        self._service.play()

    def _on_set_target(self) -> None:
        log.debug("set target stem: %s", self._stem_name)
        self.targetChosen.emit(self._stem_name)


class StemsPanel(QWidget):
    """Stem separation panel: run demucs, display per-stem rows.

    Signals:
        separateRequested: Emitted when the user clicks "Separate Stems".
            The window handles this (it holds the reference path).
        targetChosen(stem_name): Emitted when a stem is chosen as the target.
    """

    separateRequested = Signal()
    targetChosen = Signal(str)

    def __init__(
        self,
        service: PlaybackService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._service = service
        self._stems: dict[str, np.ndarray] = {}
        self._sr: int = 44100
        self._thread: QThread | None = None
        self._worker: _SeparationWorker | None = None

        self.setObjectName("stems-panel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self._header = QLabel("Stem Separation")
        self._header.setObjectName("stems-header")
        layout.addWidget(self._header)

        self._sep_btn = QPushButton("Separate Stems")
        self._sep_btn.setObjectName("separate-btn")
        self._sep_btn.clicked.connect(self._on_separate)
        layout.addWidget(self._sep_btn)

        self._progress = QProgressBar()
        self._progress.setRange(0, 0)  # indeterminate
        self._progress.setVisible(False)
        self._progress.setObjectName("sep-progress")
        layout.addWidget(self._progress)

        self._status = QLabel("No stems separated")
        self._status.setObjectName("sep-status")
        layout.addWidget(self._status)

        self._rows_layout = QVBoxLayout()
        layout.addLayout(self._rows_layout)

        if not _DEMUCS_AVAILABLE:
            self._sep_btn.setEnabled(False)
            self._status.setText(
                "demucs/torch not installed — stem separation unavailable.\n"
                "You can still load a pre-separated stem WAV directly."
            )

    def separate(self, path: str, start_s: float = 0.0, end_s: float | None = None, sr: int = 44100) -> None:
        """Run demucs separation in a background thread."""
        if not _DEMUCS_AVAILABLE:
            log.warning("separate() called but demucs is not available")
            return
        if self._thread is not None and self._thread.isRunning():
            log.debug("separation already running, ignoring request")
            return

        log.info("starting stem separation: %s", path)
        self._sr = sr
        self._sep_btn.setEnabled(False)
        self._progress.setVisible(True)
        self._status.setText("Separating stems… (~10 s/clip on CPU)")

        self._worker = _SeparationWorker(path, start_s, end_s, sr)
        self._thread = QThread(self)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_separation_done)
        self._worker.error.connect(self._on_separation_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def set_stems(self, stems: dict[str, np.ndarray], sr: int) -> None:
        """Directly set stem audio data (e.g. from pre-separated files)."""
        log.debug("set_stems: %d stems at sr=%d", len(stems), sr)
        self._stems = stems
        self._sr = sr
        self._rebuild_rows()
        self._status.setText(f"{len(stems)} stems loaded")

    def get_stem_audio(self, stem_name: str) -> np.ndarray | None:
        """Return the mono audio for a specific stem, or None."""
        return self._stems.get(stem_name)

    # ------------------------------------------------------------------ slots

    def _on_separate(self) -> None:
        log.debug("separate button clicked")
        self.separateRequested.emit()

    def _on_separation_done(self, result: dict) -> None:
        self._progress.setVisible(False)
        self._sep_btn.setEnabled(True)

        stems: dict[str, np.ndarray] = {}
        for name in result.get("names", []):
            mono_key = f"{name}_mono"
            if mono_key in result:
                stems[name] = result[mono_key]

        log.info("separation done: %d stems", len(stems))
        self._stems = stems
        self._rebuild_rows()
        self._status.setText(f"Separated {len(stems)} stems")

    def _on_separation_error(self, msg: str) -> None:
        log.error("separation failed: %s", msg)
        self._progress.setVisible(False)
        self._sep_btn.setEnabled(True)
        self._status.setText(f"Separation error: {msg}")

    def _rebuild_rows(self) -> None:
        while self._rows_layout.count():
            item = self._rows_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for name, mono in self._stems.items():
            row = StemRow(name, mono, self._sr, self._service)
            row.targetChosen.connect(self.targetChosen.emit)
            self._rows_layout.addWidget(row)
