"""soundmatch.ui.resynth_dialog — Spectral Resynthesis dialog.

Analyses the supplied audio region, builds a ResynthModel, and renders a
fresh synthesis of the sound.  The synthesised audio never contains original
sample bytes — only the measured spectral/temporal structure is re-created.

The user can send the result directly to the A/B Viewer (resynthReady signal)
or save it as a WAV or model JSON file.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

log = logging.getLogger(__name__)

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


_NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def _hz_to_note(hz: float) -> str:
    if hz <= 0:
        return "—"
    midi = 69 + 12 * np.log2(hz / 440.0)
    name = _NOTE_NAMES[int(round(midi)) % 12]
    octave = int(round(midi)) // 12 - 1
    cents = (midi - round(midi)) * 100
    suffix = f" {cents:+.0f}¢" if abs(cents) > 3 else ""
    return f"{name}{octave}{suffix}"


class ResynthDialog(QDialog):
    """Modal dialog that analyses, resynthesises, and previews a sound region.

    Signals
    -------
    resynthReady(audio: np.ndarray, sr: int)
        Emitted when the user clicks "Send to A/B Viewer".
    """

    resynthReady = Signal(object, int)   # (np.ndarray, sr)

    def __init__(
        self,
        y: np.ndarray,
        sr: int,
        *,
        source_name: str = "sound",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Spectral Resynthesis")
        self.setObjectName("resynth-dialog")
        self.resize(420, 300)

        self._rendered: np.ndarray | None = None
        self._sr = sr
        self._model = None

        layout = QVBoxLayout(self)

        # ── Description ───────────────────────────────────────────────
        desc = QLabel(
            "Analyses the selected region and reconstructs it from scratch "
            "using additive synthesis and/or spectrally-shaped noise.\n"
            "No original sample bytes are stored or replayed."
        )
        desc.setWordWrap(True)
        desc.setObjectName("resynth-desc")
        layout.addWidget(desc)

        # ── Info grid ─────────────────────────────────────────────────
        form = QFormLayout()
        form.setContentsMargins(0, 8, 0, 8)

        self._lbl_approach  = QLabel("—")
        self._lbl_f0        = QLabel("—")
        self._lbl_partials  = QLabel("—")
        self._lbl_hnr       = QLabel("—")
        self._lbl_duration  = QLabel("—")
        self._lbl_status    = QLabel("Analysing…")
        self._lbl_status.setObjectName("resynth-status")

        form.addRow("Approach:",   self._lbl_approach)
        form.addRow("Fundamental:", self._lbl_f0)
        form.addRow("Partials:",   self._lbl_partials)
        form.addRow("HNR:",        self._lbl_hnr)
        form.addRow("Duration:",   self._lbl_duration)
        form.addRow("Status:",     self._lbl_status)
        layout.addLayout(form)

        layout.addStretch()

        # ── Buttons ───────────────────────────────────────────────────
        self._ab_btn = QPushButton("Send to A/B Viewer")
        self._ab_btn.setObjectName("resynth-ab-btn")
        self._ab_btn.setToolTip("Load the resynthesised audio into the A/B Viewer for comparison")
        self._ab_btn.setEnabled(False)
        self._ab_btn.clicked.connect(self._on_send_to_ab)
        layout.addWidget(self._ab_btn)

        bbox = QDialogButtonBox()
        self._save_wav_btn = bbox.addButton(
            "Save WAV…", QDialogButtonBox.ButtonRole.ActionRole
        )
        self._save_wav_btn.setEnabled(False)
        self._save_wav_btn.clicked.connect(self._on_save_wav)

        self._save_model_btn = bbox.addButton(
            "Save Model…", QDialogButtonBox.ButtonRole.ActionRole
        )
        self._save_model_btn.setEnabled(False)
        self._save_model_btn.clicked.connect(self._on_save_model)

        close_btn = bbox.addButton(QDialogButtonBox.StandardButton.Close)
        close_btn.clicked.connect(self.reject)
        layout.addWidget(bbox)

        # ── Run analysis now (synchronous — fast for short clips) ─────
        QApplication.processEvents()
        self._run(y, sr, source_name)

    # ── Analysis + render ─────────────────────────────────────────────

    def _run(self, y: np.ndarray, sr: int, source_name: str) -> None:
        try:
            from soundmatch.core.resynth import analyze, render
            self._lbl_status.setText("Analysing…")
            QApplication.processEvents()

            model = analyze(y, sr, source_name=source_name)
            self._model = model

            self._lbl_status.setText("Rendering…")
            QApplication.processEvents()

            rendered = render(model)
            self._rendered = rendered

            # Update info labels
            self._lbl_approach.setText(model.approach.capitalize())
            if model.source_f0 > 0:
                self._lbl_f0.setText(
                    f"{model.source_f0:.1f} Hz  ({_hz_to_note(model.source_f0)})"
                )
            else:
                self._lbl_f0.setText("— (unpitched)")
            self._lbl_partials.setText(str(len(model.partials)))
            self._lbl_hnr.setText(f"{model.hnr_db:.1f} dB")
            self._lbl_duration.setText(f"{model.duration_s:.2f} s")
            self._lbl_status.setText("Ready")

            self._ab_btn.setEnabled(True)
            self._save_wav_btn.setEnabled(True)
            self._save_model_btn.setEnabled(True)

        except Exception as exc:
            log.error("resynth failed: %s", exc, exc_info=True)
            self._lbl_status.setText(f"Error: {exc}")

    # ── Button slots ──────────────────────────────────────────────────

    def _on_send_to_ab(self) -> None:
        if self._rendered is not None:
            self.resynthReady.emit(self._rendered, self._sr)
            self._lbl_status.setText("Sent to A/B Viewer")

    def _on_save_wav(self) -> None:
        if self._rendered is None:
            return
        path_str, _ = QFileDialog.getSaveFileName(
            self, "Save Resynthesis WAV", "resynth.wav",
            "WAV (*.wav);;All (*)",
        )
        if not path_str:
            return
        try:
            import soundfile as sf
            sf.write(path_str, self._rendered, self._sr)
            self._lbl_status.setText(f"Saved: {Path(path_str).name}")
        except Exception as exc:
            log.error("save wav failed: %s", exc, exc_info=True)
            self._lbl_status.setText(f"Save error: {exc}")

    def _on_save_model(self) -> None:
        if self._model is None:
            return
        path_str, _ = QFileDialog.getSaveFileName(
            self, "Save Resynthesis Model", "resynth_model.json",
            "JSON (*.json);;All (*)",
        )
        if not path_str:
            return
        try:
            from soundmatch.core.resynth import save_model
            save_model(self._model, Path(path_str))
            self._lbl_status.setText(f"Model saved: {Path(path_str).name}")
        except Exception as exc:
            log.error("save model failed: %s", exc, exc_info=True)
            self._lbl_status.setText(f"Save error: {exc}")
