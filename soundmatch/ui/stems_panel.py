"""soundmatch.ui.stems_panel — separate (async) + per-stem audition/solo + "set target".

Runs demucs separation on a QThread with a progress indicator.  Per-stem rows
show a waveform thumbnail and a compact spectrogram.  All rows respect the
current time selection: playback plays only the selected region, and
characterization uses the correct slice in stem-relative coordinates.
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
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from forge.playback.service import PlaybackService
from soundmatch.ui.spectrogram import SpectrogramWidget, WaveformWidget

log = logging.getLogger(__name__)

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
        self.start_s = start_s      # public so StemsPanel reads it on done
        self._end_s = end_s
        self._sr = sr

    def run(self) -> None:
        t0 = time.perf_counter()
        log.debug("separation starting: %s offset=%.1fs", self._path, self.start_s)
        try:
            from inspector.separation import separate_stems
            result, reason = separate_stems(
                self._path, offset=self.start_s, end=self._end_s, sr=self._sr,
            )
            if result is not None:
                log.debug("separation done: stems=%s (%.2fs)",
                          result.get("names", []), time.perf_counter() - t0)
                self.finished.emit(result)
            else:
                log.warning("separation returned no results: %s", reason)
                self.error.emit(reason or "Separation returned no results")
        except Exception as exc:
            log.error("separation error: %s", exc, exc_info=True)
            self.error.emit(str(exc))


class StemRow(QWidget):
    """One stem: buttons + waveform thumbnail + compact spectrogram.

    Signals:
        targetChosen(stem_name): emitted when "Set Target" is clicked.
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
        # Playback region in samples (defaults to full stem)
        n = len(mono_audio) if mono_audio is not None else 0
        self._play_i0: int = 0
        self._play_i1: int = n

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 4, 2)
        layout.setSpacing(1)

        # ── Button row ────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        self._name_label = QLabel(f"<b>{stem_name}</b>")
        self._name_label.setMinimumWidth(60)
        btn_row.addWidget(self._name_label)

        self._play_btn = QPushButton("▶")
        self._play_btn.setMaximumWidth(36)
        self._play_btn.clicked.connect(self._on_play)
        self._play_btn.setEnabled(mono_audio is not None)
        btn_row.addWidget(self._play_btn)
        btn_row.addStretch()

        self._target_btn = QPushButton("Set Target")
        self._target_btn.setObjectName(f"target-btn-{stem_name}")
        self._target_btn.clicked.connect(self._on_set_target)
        self._target_btn.setEnabled(mono_audio is not None)
        btn_row.addWidget(self._target_btn)
        layout.addLayout(btn_row)

        # ── Waveform thumbnail ────────────────────────────────────────
        self._waveform = WaveformWidget(self)
        self._waveform.setMinimumHeight(28)
        self._waveform.setMaximumHeight(40)
        if mono_audio is not None:
            # Downsample for display only
            y_disp, dur = self._downsample_for_display(mono_audio, sr)
            self._waveform.set_audio(y_disp, sr, duration_s=dur)
        layout.addWidget(self._waveform)

        # ── Spectrogram ───────────────────────────────────────────────
        self._spectrogram = SpectrogramWidget(self)
        self._spectrogram.setMinimumHeight(60)
        self._spectrogram.setMaximumHeight(90)
        layout.addWidget(self._spectrogram)

    # ── Public API ────────────────────────────────────────────────────

    def set_spectrogram(self, S_db: np.ndarray, sr: int, hop: int) -> None:
        self._spectrogram.set_spectrogram_data(S_db, sr, hop, title=None)

    def update_selection(self, eff_start_s: float, eff_end_s: float) -> None:
        """Set playback slice in stem-relative time coordinates."""
        if self._mono is None:
            return
        self._play_i0 = max(0, int(eff_start_s * self._sr))
        self._play_i1 = min(int(eff_end_s * self._sr), len(self._mono))
        self._waveform.set_selection(eff_start_s, eff_end_s)

    # ── Private ───────────────────────────────────────────────────────

    @staticmethod
    def _downsample_for_display(y: np.ndarray, sr: int, target: int = 1000) -> tuple[np.ndarray, float]:
        dur = len(y) / sr
        if len(y) <= target:
            return y, dur
        block = len(y) // target
        trimmed = y[:block * target].reshape(target, block)
        idx = np.argmax(np.abs(trimmed), axis=1)
        return trimmed[np.arange(target), idx], dur

    def _on_play(self) -> None:
        if self._mono is None:
            return
        from forge.core.buffer import AudioBuffer
        i0, i1 = self._play_i0, self._play_i1
        region = self._mono[i0:i1] if i1 > i0 else self._mono
        log.debug("play stem '%s': samples %d–%d (%.2fs)",
                  self._stem_name, i0, i1, len(region) / self._sr)
        buf = AudioBuffer.from_mono(region, sr=self._sr)
        self._service.load(buf)
        self._service.play()

    def _on_set_target(self) -> None:
        log.debug("set target stem: %s", self._stem_name)
        self.targetChosen.emit(self._stem_name)


class StemsPanel(QWidget):
    """Stem separation panel: run demucs, display per-stem rows.

    Time selection propagation:
        ``set_selection(start_s, end_s)`` tells the panel which region of the
        original file is selected.  Stem audio may be:
          - Full-file (loaded from disk): offset = 0
          - Already sliced (from demucs): offset = the start_s passed to separate()
        The effective playback/characterise slice is computed via
        ``get_stem_audio_for_selection()`` which converts selection times to
        stem-relative sample indices.

    Signals:
        separateRequested: user clicked "Separate Stems".
        targetChosen(stem_name): user chose a stem as the target.
        stemsReady(stems, sr): emitted after stems are loaded/separated.
    """

    separateRequested = Signal()
    targetChosen = Signal(str)
    stemsReady = Signal(object, int)

    def __init__(self, service: PlaybackService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._service = service
        self._stems: dict[str, np.ndarray] = {}
        self._sr: int = 44100
        self._stem_offset_s: float = 0.0   # time in original file where stem audio starts
        self._sel_start_s: float = 0.0     # current selection (original-file coords)
        self._sel_end_s: float = float("inf")
        self._thread: QThread | None = None
        self._worker: _SeparationWorker | None = None

        self.setObjectName("stems-panel")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(4, 4, 4, 4)

        self._header = QLabel("Stem Separation")
        self._header.setObjectName("stems-header")
        outer.addWidget(self._header)

        self._sep_btn = QPushButton("Separate Stems")
        self._sep_btn.setObjectName("separate-btn")
        self._sep_btn.clicked.connect(self._on_separate)
        outer.addWidget(self._sep_btn)

        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setVisible(False)
        self._progress.setObjectName("sep-progress")
        outer.addWidget(self._progress)

        self._status = QLabel("No stems separated")
        self._status.setObjectName("sep-status")
        outer.addWidget(self._status)

        # Scrollable row area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("stems-scroll")
        self._rows_container = QWidget()
        self._rows_layout = QVBoxLayout(self._rows_container)
        self._rows_layout.setContentsMargins(0, 0, 0, 0)
        self._rows_layout.addStretch()
        scroll.setWidget(self._rows_container)
        outer.addWidget(scroll, stretch=1)

        if not _DEMUCS_AVAILABLE:
            self._sep_btn.setEnabled(False)
            self._status.setText(
                "demucs/torch not installed — stem separation unavailable.\n"
                "You can still load a pre-separated stem WAV directly."
            )

    # ── Public API ────────────────────────────────────────────────────

    def separate(
        self, path: str,
        start_s: float = 0.0,
        end_s: float | None = None,
        sr: int = 44100,
    ) -> None:
        """Run demucs separation in a background thread."""
        if not _DEMUCS_AVAILABLE:
            log.warning("separate() called but demucs is not available")
            return
        if self._thread is not None and self._thread.isRunning():
            log.debug("separation already running, ignoring request")
            return

        log.info("starting stem separation: %s start=%.1fs", path, start_s)
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
        """Directly set stem audio data (e.g. from pre-separated files on disk).

        Stems loaded from disk are full-length files, so offset is 0.
        """
        log.debug("set_stems: %d stems at sr=%d", len(stems), sr)
        self._stems = stems
        self._sr = sr
        self._stem_offset_s = 0.0   # full-file stems start at t=0
        self._rebuild_rows()
        self._status.setText(f"{len(stems)} stems loaded")
        self.stemsReady.emit(stems, sr)

    def set_selection(self, start_s: float, end_s: float) -> None:
        """Propagate a new time selection to all stem rows."""
        self._sel_start_s = start_s
        self._sel_end_s = end_s
        eff_start, eff_end = self._effective_selection()
        for i in range(self._rows_layout.count()):
            item = self._rows_layout.itemAt(i)
            if item and isinstance(item.widget(), StemRow):
                item.widget().update_selection(eff_start, eff_end)

    def get_stem_audio(self, stem_name: str) -> np.ndarray | None:
        """Return the full stem audio array (backward-compat helper)."""
        return self._stems.get(stem_name)

    def get_stem_audio_for_selection(
        self, stem_name: str, start_s: float, end_s: float
    ) -> np.ndarray | None:
        """Return stem audio sliced to [start_s, end_s] in original-file coordinates.

        Correctly handles both full-file stems (offset=0) and already-sliced
        demucs stems (offset = the start_s passed to separate()).
        """
        audio = self._stems.get(stem_name)
        if audio is None:
            return None
        eff_start, eff_end = self._effective_selection(start_s, end_s)
        i0 = max(0, int(eff_start * self._sr))
        i1 = min(int(eff_end * self._sr), len(audio))
        if i1 <= i0:
            return audio   # fallback
        return audio[i0:i1]

    # ── Private ───────────────────────────────────────────────────────

    def _effective_selection(
        self,
        start_s: float | None = None,
        end_s: float | None = None,
    ) -> tuple[float, float]:
        """Convert original-file selection to stem-relative coordinates."""
        s = start_s if start_s is not None else self._sel_start_s
        e = end_s if end_s is not None else self._sel_end_s
        eff_start = max(0.0, s - self._stem_offset_s)
        eff_end = e - self._stem_offset_s
        return eff_start, eff_end

    def _on_separate(self) -> None:
        log.debug("separate button clicked")
        self.separateRequested.emit()

    def _on_separation_done(self, result: dict) -> None:
        self._progress.setVisible(False)
        self._sep_btn.setEnabled(True)

        # Stems from demucs start at the offset used during separation
        if self._worker is not None:
            self._stem_offset_s = self._worker.start_s
        else:
            self._stem_offset_s = 0.0

        stems: dict[str, np.ndarray] = {}
        for name in result.get("names", []):
            mono_key = f"{name}_mono"
            if mono_key in result:
                stems[name] = result[mono_key]

        log.info("separation done: %d stems (offset=%.1fs)", len(stems), self._stem_offset_s)
        self._stems = stems
        self._rebuild_rows()
        self._status.setText(f"Separated {len(stems)} stems")
        self.stemsReady.emit(stems, self._sr)

    def _on_separation_error(self, msg: str) -> None:
        log.error("separation failed: %s", msg)
        self._progress.setVisible(False)
        self._sep_btn.setEnabled(True)
        self._status.setText(f"Separation error: {msg}")

    def _rebuild_rows(self) -> None:
        # Remove all existing rows (keep trailing stretch)
        while self._rows_layout.count() > 1:
            item = self._rows_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        eff_start, eff_end = self._effective_selection()

        for name, mono in self._stems.items():
            row = StemRow(name, mono, self._sr, self._service, self._rows_container)
            row.update_selection(eff_start, eff_end)
            row.targetChosen.connect(self.targetChosen.emit)

            # Compute spectrogram synchronously — short clips, ~50 ms each
            if mono is not None and len(mono) > 0:
                try:
                    import librosa
                    hop = 2048
                    S = librosa.feature.melspectrogram(
                        y=mono.astype(np.float32),
                        sr=self._sr, n_mels=64, hop_length=hop,
                    )
                    S_db = librosa.power_to_db(S, ref=np.max)
                    row.set_spectrogram(S_db, self._sr, hop)
                except Exception as exc:
                    log.debug("stem spectrogram failed (%s): %s", name, exc)

            # Insert before the trailing stretch
            self._rows_layout.insertWidget(self._rows_layout.count() - 1, row)
