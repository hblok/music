"""soundmatch.ui.reference_panel — load + waveform/spectrogram + draggable selection.

Displays a reference audio file as a waveform + spectrogram, with a draggable
time selection that emits ``selectionChanged(start_s, end_s)``.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

import numpy as np

log = logging.getLogger(__name__)

from PySide6.QtCore import QObject, QThread, Signal
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


class _AudioLoader(QObject):
    """Worker: loads audio and computes display data off the main thread."""

    # y_full, sr, y_display, duration_s, S_db, hop
    finished = Signal(object, int, object, float, object, int)
    error = Signal(str)

    def __init__(self, path: str, sr: int) -> None:
        super().__init__()
        self._path = path
        self._sr = sr

    def run(self) -> None:
        t0 = time.perf_counter()
        try:
            from inspector.features import load_audio
            import librosa

            log.debug("load starting: %s", self._path)
            audio = load_audio(self._path, sr=self._sr)
            y = audio["y"]
            sr_out = int(audio.get("sr", self._sr))
            duration_s = float(len(y) / sr_out)
            log.debug("load audio done: %.1fs, %d samples (%.2fs)", duration_s, len(y), time.perf_counter() - t0)

            y_display = self._peak_downsample(y, target=2000)
            log.debug("waveform downsampled to %d pts (%.2fs)", len(y_display), time.perf_counter() - t0)

            hop = 4096
            S = librosa.feature.melspectrogram(y=y, sr=sr_out, n_mels=128, hop_length=hop)
            S_db = librosa.power_to_db(S, ref=np.max)
            log.debug("spectrogram computed %s (%.2fs)", S_db.shape, time.perf_counter() - t0)

            self.finished.emit(y, sr_out, y_display, duration_s, S_db, hop)
            log.debug("finished signal emitted (%.2fs)", time.perf_counter() - t0)
        except Exception as exc:
            log.error("load error: %s", exc, exc_info=True)
            self.error.emit(str(exc))

    @staticmethod
    def _peak_downsample(y: np.ndarray, target: int) -> np.ndarray:
        if len(y) <= target:
            return y
        block = len(y) // target
        trimmed = y[: block * target].reshape(target, block)
        idx = np.argmax(np.abs(trimmed), axis=1)
        return trimmed[np.arange(target), idx]


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
    fileLoaded = Signal(object)  # Path — emitted when audio finishes loading

    def __init__(
        self,
        service: PlaybackService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._service = service
        self._target_sr: int = service.sr
        self._y: np.ndarray | None = None
        self._sr: int = self._target_sr
        self._start_s: float = 0.0
        self._end_s: float = 10.0
        self._path: Path | None = None
        self._y_display: np.ndarray | None = None  # downsampled display copy
        self._duration_s: float = 0.0
        self._load_thread: QThread | None = None
        self._load_worker: _AudioLoader | None = None

        self.setObjectName("reference-panel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Top bar: load button + label
        top = QHBoxLayout()
        self._load_btn = QPushButton("Load Reference…")
        self._load_btn.setObjectName("load-reference-btn")
        self._load_btn.clicked.connect(self._on_load)
        top.addWidget(self._load_btn)

        self._file_label = QLabel("No file loaded")
        self._file_label.setObjectName("file-label")
        top.addWidget(self._file_label, stretch=1)
        layout.addLayout(top)

        # Waveform display (drag to select a region)
        self._waveform = WaveformWidget(self)
        self._waveform.setObjectName("reference-waveform")
        self._waveform.selectionChanged.connect(self._on_waveform_selection)
        layout.addWidget(self._waveform, stretch=1)

        # Spectrogram display
        self._spectrogram = SpectrogramWidget(self)
        self._spectrogram.setObjectName("reference-spectrogram")
        layout.addWidget(self._spectrogram, stretch=2)

        # Selection readout + re-characterize button
        sel_layout = QHBoxLayout()
        self._start_label = QLabel("Sel:")
        self._start_spin = QLabel("0.00 s")
        self._start_spin.setObjectName("sel-start-label")
        sep_label = QLabel("–")
        self._end_spin = QLabel("10.00 s")
        self._end_spin.setObjectName("sel-end-label")
        self._apply_btn = QPushButton("Re-characterize")
        self._apply_btn.setObjectName("apply-selection-btn")
        self._apply_btn.setToolTip("Re-run target characterization on the current selection")
        self._apply_btn.clicked.connect(self._on_apply_selection)

        sel_layout.addWidget(self._start_label)
        sel_layout.addWidget(self._start_spin)
        sel_layout.addWidget(sep_label)
        sel_layout.addWidget(self._end_spin)
        sel_layout.addStretch()
        sel_layout.addWidget(self._apply_btn)
        layout.addLayout(sel_layout)

        # Play reference button
        self._play_btn = QPushButton("▶ Play")
        self._play_btn.setObjectName("play-reference-btn")
        self._play_btn.clicked.connect(self._on_play)
        layout.addWidget(self._play_btn)

    def load_audio(self, path: Path, sr: int | None = None) -> None:
        """Load an audio file in the background and display it when ready.

        Parameters
        ----------
        path: Path to the audio file.
        sr  : Target sample rate (defaults to the service sample rate).
        """
        target_sr = sr if sr is not None else self._target_sr
        self._path = path
        self._file_label.setText(f"Loading {path.name}…")
        self._load_btn.setEnabled(False)

        # Cancel any in-progress load
        if self._load_thread is not None and self._load_thread.isRunning():
            self._load_thread.quit()
            self._load_thread.wait()

        worker = _AudioLoader(str(path), target_sr)
        thread = QThread(self)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.finished.connect(self._on_audio_loaded)
        worker.error.connect(self._on_load_error)
        worker.finished.connect(thread.quit)
        worker.error.connect(thread.quit)
        thread.finished.connect(thread.deleteLater)

        # Keep strong Python references so neither gets GC'd before the thread runs
        self._load_worker = worker
        self._load_thread = thread
        thread.start()

    def clear(self) -> None:
        """Reset the panel to its initial (no file loaded) state."""
        self._y = None
        self._y_display = None
        self._duration_s = 0.0
        self._sr = self._target_sr
        self._start_s = 0.0
        self._end_s = 10.0
        self._path = None
        self._file_label.setText("No file loaded")
        self._start_spin.setText("0.0 s")
        self._end_spin.setText("10.0 s")
        self._waveform.clear()
        self._spectrogram.clear()

    def set_selection(self, start_s: float, end_s: float) -> None:
        """Programmatically set the time selection."""
        self._start_s = start_s
        self._end_s = end_s
        self._start_spin.setText(f"{start_s:.2f} s")
        self._end_spin.setText(f"{end_s:.2f} s")
        if self._y_display is not None:
            self._waveform.set_audio(self._y_display, self._sr, duration_s=self._duration_s)
            self._waveform.set_selection(start_s, end_s)

    def _on_waveform_selection(self, start_s: float, end_s: float) -> None:
        """Called when the user finishes a drag selection on the waveform."""
        self._start_s = start_s
        self._end_s = end_s
        self._start_spin.setText(f"{start_s:.2f} s")
        self._end_spin.setText(f"{end_s:.2f} s")
        log.debug("waveform drag selection: %.2f–%.2fs", start_s, end_s)
        self.selectionChanged.emit(start_s, end_s)

    @property
    def audio_data(self) -> tuple[np.ndarray | None, int]:
        """Return (y, sr) tuple of the loaded audio."""
        return self._y, self._sr

    @property
    def file_path(self) -> Path | None:
        """Return the loaded file path."""
        return self._path

    # ------------------------------------------------------------------ slots

    def _on_audio_loaded(
        self,
        y: object,
        sr: int,
        y_display: object,
        duration_s: float,
        S_db: object,
        hop: int,
    ) -> None:
        """Called on the main thread when background load + display computation finish."""
        t0 = time.perf_counter()
        log.debug("_on_audio_loaded: main thread, sr=%d, duration=%.1fs", sr, duration_s)

        self._y = np.asarray(y)
        self._y_display = np.asarray(y_display)
        self._duration_s = duration_s
        self._sr = sr
        self._end_s = min(10.0, duration_s)
        self._start_spin.setText(f"{self._start_s:.2f} s")
        self._end_spin.setText(f"{self._end_s:.2f} s")

        if self._path is not None:
            self._file_label.setText(self._path.name)
        log.debug("labels updated (%.2fs)", time.perf_counter() - t0)

        self._waveform.set_audio(np.asarray(y_display), sr, duration_s=duration_s, title="Waveform")
        log.debug("waveform drawn (%.2fs)", time.perf_counter() - t0)

        self._waveform.set_selection(self._start_s, self._end_s)
        log.debug("selection drawn (%.2fs)", time.perf_counter() - t0)

        self._spectrogram.set_spectrogram_data(np.asarray(S_db), sr, hop, title="Spectrogram")
        log.debug("spectrogram drawn (%.2fs)", time.perf_counter() - t0)

        self._load_btn.setEnabled(True)
        log.info("audio ready: %s (%.2fs total)", self._path.name if self._path else "?", time.perf_counter() - t0)
        if self._path is not None:
            self.fileLoaded.emit(self._path)

    def _on_load_error(self, msg: str) -> None:
        log.error("audio load failed: %s", msg)
        self._file_label.setText(f"Error: {msg}")
        self._load_btn.setEnabled(True)

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
        i0 = int(self._start_s * self._sr)
        i1 = min(int(self._end_s * self._sr), len(self._y))
        region = self._y[i0:i1] if i1 > i0 else self._y
        log.debug("play reference: %.2f–%.2fs (%d samples)", self._start_s, self._end_s, len(region))
        buf = AudioBuffer.from_mono(region, sr=self._sr)
        self._service.load(buf)
        self._service.play()
