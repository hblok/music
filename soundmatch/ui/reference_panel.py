"""soundmatch.ui.reference_panel — load + waveform/spectrogram + draggable selection.

Displays a reference audio file as a waveform + spectrogram, with a draggable
time selection that emits ``selectionChanged(start_s, end_s)``.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from forge.playback.service import PlaybackService
from soundmatch.ui.spectrogram import SpectrogramWidget, WaveformWidget


class ReferencePanel(QWidget):
    """Reference audio panel: load, display waveform + spectrogram, select region.

    Signals:
        selectionChanged(start_s, end_s): Emitted when the user changes the
            time selection on the waveform.

    Args:
        service: PlaybackService for auditioning the reference.
        parent:  Optional parent widget.
    """

    selectionChanged = Signal(float, float)

    def __init__(
        self,
        service: PlaybackService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._service = service
        self._y: np.ndarray | None = None
        self._sr: int = 44100
        self._start_s: float = 0.0
        self._end_s: float = 10.0
        self._path: Path | None = None

        self.setObjectName("reference-panel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Top bar: load button + label
        top = QHBoxLayout()
        self._load_btn = QPushButton("Load Reference\u2026")
        self._load_btn.setObjectName("load-reference-btn")
        self._load_btn.clicked.connect(self._on_load)
        top.addWidget(self._load_btn)

        self._file_label = QLabel("No file loaded")
        self._file_label.setObjectName("file-label")
        top.addWidget(self._file_label, stretch=1)
        layout.addLayout(top)

        # Waveform display
        self._waveform = WaveformWidget(self)
        self._waveform.setObjectName("reference-waveform")
        layout.addWidget(self._waveform, stretch=1)

        # Spectrogram display
        self._spectrogram = SpectrogramWidget(self)
        self._spectrogram.setObjectName("reference-spectrogram")
        layout.addWidget(self._spectrogram, stretch=2)

        # Selection controls
        sel_layout = QHBoxLayout()
        self._start_label = QLabel("Start:")
        self._start_spin = QLabel("0.0 s")
        self._end_label = QLabel("End:")
        self._end_spin = QLabel("10.0 s")
        self._apply_btn = QPushButton("Set Selection")
        self._apply_btn.setObjectName("apply-selection-btn")
        self._apply_btn.clicked.connect(self._on_apply_selection)

        sel_layout.addWidget(self._start_label)
        sel_layout.addWidget(self._start_spin)
        sel_layout.addWidget(self._end_label)
        sel_layout.addWidget(self._end_spin)
        sel_layout.addStretch()
        sel_layout.addWidget(self._apply_btn)
        layout.addLayout(sel_layout)

        # Play reference button
        self._play_btn = QPushButton("\u25b6 Play")
        self._play_btn.setObjectName("play-reference-btn")
        self._play_btn.clicked.connect(self._on_play)
        layout.addWidget(self._play_btn)

    def load_audio(self, path: Path, sr: int = 22050) -> None:
        """Load an audio file and display it.

        Parameters
        ----------
        path: Path to the audio file.
        sr  : Target sample rate for analysis.
        """
        from inspector.features import load_audio

        audio = load_audio(str(path), sr=sr)
        self._y = audio["y"]
        self._sr = audio.get("sr", sr)
        self._path = path

        duration = len(self._y) / self._sr
        self._end_s = min(10.0, duration)
        self._start_spin.setText(f"{self._start_s:.1f} s")
        self._end_spin.setText(f"{self._end_s:.1f} s")
        self._file_label.setText(path.name)

        # Display
        self._waveform.set_audio(self._y, self._sr, title="Waveform")
        self._waveform.set_selection(self._start_s, self._end_s)
        self._spectrogram.set_audio(self._y, self._sr, title="Spectrogram")

    def set_selection(self, start_s: float, end_s: float) -> None:
        """Programmatically set the time selection."""
        self._start_s = start_s
        self._end_s = end_s
        self._start_spin.setText(f"{start_s:.1f} s")
        self._end_spin.setText(f"{end_s:.1f} s")
        if self._y is not None:
            self._waveform.set_audio(self._y, self._sr)
            self._waveform.set_selection(start_s, end_s)

    @property
    def audio_data(self) -> tuple[np.ndarray | None, int]:
        """Return (y, sr) tuple of the loaded audio."""
        return self._y, self._sr

    @property
    def file_path(self) -> Path | None:
        """Return the loaded file path."""
        return self._path

    # ------------------------------------------------------------------ slots

    def _on_load(self) -> None:
        path_str, _ = QFileDialog.getOpenFileName(
            self, "Load Reference Audio", "",
            "Audio (*.wav *.mp3 *.flac *.ogg *.m4a);;All (*)",
        )
        if path_str:
            self.load_audio(Path(path_str))

    def _on_apply_selection(self) -> None:
        # For now, emit the current start/end values
        # In a full implementation, these would be spinboxes
        self.selectionChanged.emit(self._start_s, self._end_s)

    def _on_play(self) -> None:
        if self._y is None:
            return
        from forge.core.buffer import AudioBuffer
        buf = AudioBuffer.from_mono(self._y, sr=self._sr)
        self._service.load(buf)
        self._service.play()
