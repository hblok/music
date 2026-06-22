"""soundmatch.ui.ab_viewer — stacked spectrograms + synced, looped A/B playback.

Displays target (A) on top and candidate (B) below using the shared
``SpectrogramWidget``.  Toggle playback between A and B with looped
audition.  Export the montage as PNG.

Inspired by ``forge.ui.ab_compare.ABCompareWidget`` but compares *audio*,
not document parameters.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from forge.playback.service import PlaybackService
from soundmatch.ui.spectrogram import SpectrogramWidget, draw_spectrogram

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.figure import Figure


class ABViewer(QWidget):
    """Stacked spectrograms for target (A) and candidate (B) with
    synced, looped toggle playback.

    Signals:
        montageExported(path): Emitted after a montage PNG is saved.

    Args:
        service: PlaybackService for audition.
        parent:  Optional parent widget.
    """

    montageExported = Signal(str)

    def __init__(
        self,
        service: PlaybackService | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._service = service
        self._target_y: np.ndarray | None = None
        self._target_sr: int = 44100
        self._cand_y: np.ndarray | None = None
        self._cand_sr: int = 44100
        self._current: str = "A"  # which side is playing

        self.setObjectName("ab-viewer")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # ── Spectrograms ──────────────────────────────────────────
        self._target_spec = SpectrogramWidget(self)
        self._target_spec.setObjectName("ab-target-spectrogram")
        self._target_spec.setMinimumHeight(100)

        self._cand_spec = SpectrogramWidget(self)
        self._cand_spec.setObjectName("ab-candidate-spectrogram")
        self._cand_spec.setMinimumHeight(100)

        layout.addWidget(QLabel("A — Target"))
        layout.addWidget(self._target_spec, stretch=1)
        layout.addWidget(QLabel("B — Candidate"))
        layout.addWidget(self._cand_spec, stretch=1)

        # ── Playback controls ─────────────────────────────────────
        ctrl_row = QHBoxLayout()
        self._play_a_btn = QPushButton("▶ A (Target)")
        self._play_a_btn.setObjectName("ab-play-a")
        self._play_a_btn.setEnabled(False)
        self._play_a_btn.clicked.connect(self._on_play_a)
        ctrl_row.addWidget(self._play_a_btn)

        self._play_b_btn = QPushButton("▶ B (Candidate)")
        self._play_b_btn.setObjectName("ab-play-b")
        self._play_b_btn.setEnabled(False)
        self._play_b_btn.clicked.connect(self._on_play_b)
        ctrl_row.addWidget(self._play_b_btn)

        self._stop_btn = QPushButton("■ Stop")
        self._stop_btn.setObjectName("ab-stop")
        self._stop_btn.clicked.connect(self._on_stop)
        ctrl_row.addWidget(self._stop_btn)

        self._loop_cb = QPushButton("Loop")
        self._loop_cb.setObjectName("ab-loop")
        self._loop_cb.setCheckable(True)
        self._loop_cb.setChecked(True)
        ctrl_row.addWidget(self._loop_cb)

        layout.addLayout(ctrl_row)

        # ── Export ─────────────────────────────────────────────────
        export_row = QHBoxLayout()
        self._export_btn = QPushButton("Export Montage PNG…")
        self._export_btn.setObjectName("ab-export-png")
        self._export_btn.setEnabled(False)
        self._export_btn.clicked.connect(self._on_export_montage)
        export_row.addWidget(self._export_btn)

        self._status = QLabel("")
        self._status.setObjectName("ab-status")
        export_row.addWidget(self._status, stretch=1)
        layout.addLayout(export_row)

    # ── Public API ──────────────────────────────────────────────────

    def set_target(self, y: np.ndarray, sr: int) -> None:
        """Set the target (A) audio and display its spectrogram."""
        self._target_y = y
        self._target_sr = sr
        self._target_spec.set_audio(y, sr, title="A — Target")
        self._play_a_btn.setEnabled(True)
        self._update_export_state()

    def set_candidate(self, y: np.ndarray, sr: int) -> None:
        """Set the candidate (B) audio and display its spectrogram."""
        self._cand_y = y
        self._cand_sr = sr
        self._cand_spec.set_audio(y, sr, title="B — Candidate")
        self._play_b_btn.setEnabled(True)
        self._update_export_state()

    def clear(self) -> None:
        """Clear both spectrograms and audio data."""
        self._target_y = None
        self._cand_y = None
        self._target_spec.clear()
        self._cand_spec.clear()
        self._play_a_btn.setEnabled(False)
        self._play_b_btn.setEnabled(False)
        self._export_btn.setEnabled(False)
        self._status.setText("")

    @property
    def current(self) -> str:
        """Which side is currently playing: 'A' or 'B'."""
        return self._current

    def export_montage(self, path: Path) -> None:
        """Export a side-by-side montage PNG to *path*.

        The montage shows target (top) and candidate (bottom) spectrograms
        in a single figure, suitable for reports.
        """
        fig, axes = plt.subplots(2, 1, figsize=(8, 4), tight_layout=True)
        if self._target_y is not None:
            draw_spectrogram(axes[0], self._target_y, self._target_sr, title="A — Target")
        else:
            axes[0].set_visible(False)
        if self._cand_y is not None:
            draw_spectrogram(axes[1], self._cand_y, self._cand_sr, title="B — Candidate")
        else:
            axes[1].set_visible(False)
        fig.savefig(str(path), dpi=150)
        plt.close(fig)
        self.montageExported.emit(str(path))

    # ── Private ─────────────────────────────────────────────────────

    def _on_play_a(self) -> None:
        """Play the target (A) audio, looped if toggle is checked."""
        if self._target_y is None or self._service is None:
            return
        from forge.core.buffer import AudioBuffer
        buf = AudioBuffer.from_mono(self._target_y, sr=self._target_sr)
        self._service.load(buf)
        self._service.play(loop=self._loop_cb.isChecked())
        self._current = "A"
        self._status.setText("Playing A (Target)")

    def _on_play_b(self) -> None:
        """Play the candidate (B) audio, looped if toggle is checked."""
        if self._cand_y is None or self._service is None:
            return
        from forge.core.buffer import AudioBuffer
        buf = AudioBuffer.from_mono(self._cand_y, sr=self._cand_sr)
        self._service.load(buf)
        self._service.play(loop=self._loop_cb.isChecked())
        self._current = "B"
        self._status.setText("Playing B (Candidate)")

    def _on_stop(self) -> None:
        """Stop playback."""
        if self._service is not None:
            self._service.stop()
        self._status.setText("Stopped")

    def _on_export_montage(self) -> None:
        """Prompt for save path and export the montage."""
        from PySide6.QtWidgets import QFileDialog
        path_str, _ = QFileDialog.getSaveFileName(
            self, "Export Montage PNG", "ab_montage.png",
            "PNG (*.png);;All (*)",
        )
        if path_str:
            self.export_montage(Path(path_str))

    def _update_export_state(self) -> None:
        """Enable export button when both A and B are set."""
        self._export_btn.setEnabled(
            self._target_y is not None and self._cand_y is not None,
        )
