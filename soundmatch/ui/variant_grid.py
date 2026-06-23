"""soundmatch.ui.variant_grid — axis/macro sweep → scored, auditionable cards.

Declare an axis (param or macro) + values, run ``variants.render_and_score``,
and display a grid of cards.  Each card shows a spectrogram thumbnail, key
metrics, the aggregate score, and a loop-play button.  "Promote" sends the
card's params back to the Patch Editor.
"""

from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger(__name__)

import numpy as np

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from forge.playback.service import PlaybackService
from soundmatch.ui.spectrogram import SpectrogramWidget


class _VariantCard(QWidget):
    """A single variant result card: thumbnail + metrics + score + actions.

    Signals:
        promoteRequested(params, layers): Emitted when "Promote" is clicked.
    """

    promoteRequested = Signal(dict, list)

    def __init__(
        self,
        name: str,
        score: float,
        metrics_summary: str,
        y: np.ndarray | None = None,
        sr: int = 44100,
        params: dict | None = None,
        layers: list | None = None,
        service: PlaybackService | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._y = y
        self._sr = sr
        self._params = params or {}
        self._layers = layers or []
        self._service = service

        self.setObjectName(f"variant-card-{name}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Name + score header
        header = QHBoxLayout()
        name_label = QLabel(name)
        name_label.setObjectName("variant-name")
        name_label.setStyleSheet("font-weight: bold;")
        header.addWidget(name_label)
        score_label = QLabel(f"Score: {score:.4f}")
        score_label.setObjectName("variant-score")
        if score < 0.2:
            score_label.setStyleSheet("color: green; font-weight: bold;")
        elif score < 0.5:
            score_label.setStyleSheet("color: orange; font-weight: bold;")
        else:
            score_label.setStyleSheet("color: red; font-weight: bold;")
        header.addWidget(score_label)
        header.addStretch()
        layout.addLayout(header)

        # Spectrogram thumbnail
        self._spec = SpectrogramWidget(self)
        self._spec.setObjectName("variant-spectrogram")
        self._spec.setFixedHeight(80)
        if y is not None:
            self._spec.set_audio(y, sr, title=name)
        layout.addWidget(self._spec)

        # Metrics summary
        metrics_label = QLabel(metrics_summary)
        metrics_label.setObjectName("variant-metrics")
        metrics_label.setWordWrap(True)
        layout.addWidget(metrics_label)

        # Action buttons
        btn_row = QHBoxLayout()
        play_btn = QPushButton("▶")
        play_btn.setObjectName("variant-play-btn")
        play_btn.setFixedWidth(30)
        play_btn.clicked.connect(self._on_play)
        btn_row.addWidget(play_btn)

        promote_btn = QPushButton("Promote")
        promote_btn.setObjectName("variant-promote-btn")
        promote_btn.clicked.connect(self._on_promote)
        btn_row.addWidget(promote_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

    def _on_play(self) -> None:
        if self._y is None or self._service is None:
            return
        from forge.core.buffer import AudioBuffer
        buf = AudioBuffer.from_mono(self._y, sr=self._sr)
        self._service.load(buf)
        self._service.play()

    def _on_promote(self) -> None:
        self.promoteRequested.emit(self._params, self._layers)


class VariantGrid(QWidget):
    """Variant grid: declare an axis + values → render_and_score → cards.

    Signals:
        promoteRequested(params, layers):
            Emitted when a card's "Promote" button is clicked.
            The Patch Editor should absorb these params.

    Args:
        service: PlaybackService for auditioning variants.
        parent:  Optional parent widget.
    """

    promoteRequested = Signal(dict, list)

    def __init__(
        self,
        service: PlaybackService | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._service = service
        self._cards: list[_VariantCard] = []

        self.setObjectName("variant-grid")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # ── Axis selection ────────────────────────────────────────────
        axis_row = QHBoxLayout()
        axis_row.addWidget(QLabel("Axis:"))
        self._axis_combo = QComboBox()
        self._axis_combo.setObjectName("axis-combo")
        self._axis_combo.setEditable(True)
        self._axis_combo.addItems(["snare", "staccato", "body"])
        # Add instrument params from the current instrument
        self._axis_combo.addItems([
            "perc_decay", "drive", "formant_hz", "detune",
            "n_voices", "hp_cutoff", "attack", "release",
            "bloom", "f0", "tone", "decay",
        ])
        axis_row.addWidget(self._axis_combo, stretch=1)
        layout.addLayout(axis_row)

        # ── Values input ──────────────────────────────────────────────
        vals_row = QHBoxLayout()
        vals_row.addWidget(QLabel("Values (comma-sep):"))
        self._values_edit = QLineEdit()
        self._values_edit.setObjectName("values-edit")
        self._values_edit.setPlaceholderText("e.g. 0.0, 0.1, 0.2, 0.3")
        vals_row.addWidget(self._values_edit, stretch=1)
        layout.addLayout(vals_row)

        # ── Sweep button ──────────────────────────────────────────────
        sweep_row = QHBoxLayout()
        self._sweep_btn = QPushButton("Sweep")
        self._sweep_btn.setObjectName("sweep-btn")
        self._sweep_btn.clicked.connect(self._on_sweep)
        sweep_row.addWidget(self._sweep_btn)
        self._count_label = QLabel("0 variants")
        self._count_label.setObjectName("variant-count-label")
        sweep_row.addWidget(self._count_label)
        sweep_row.addStretch()
        layout.addLayout(sweep_row)

        # ── Card grid (scrollable) ────────────────────────────────────
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setObjectName("variant-scroll")
        self._grid_container = QWidget()
        self._grid_layout = QGridLayout(self._grid_container)
        self._grid_layout.setContentsMargins(4, 4, 4, 4)
        self._scroll.setWidget(self._grid_container)
        layout.addWidget(self._scroll, stretch=1)

    # ── Public API ───────────────────────────────────────────────────

    def set_results(
        self,
        results: list[Any],
        audio_data: list[tuple[np.ndarray, int]] | None = None,
    ) -> None:
        """Populate the grid from render_and_score results.

        Parameters
        ----------
        results     : List of VariantResult objects (from render_and_score).
        audio_data  : Optional list of (y, sr) for each result.
        """
        # Clear existing cards
        self._clear_cards()

        cols = 3
        for i, result in enumerate(results):
            y, sr = (44100, 44100)  # defaults
            if audio_data and i < len(audio_data):
                y, sr = audio_data[i]

            from soundmatch.core.variants import VariantResult
            if isinstance(result, VariantResult):
                name = result.spec.name
                score = result.aggregate
                m = result.metrics
                summary = (
                    f"perc={m.percussive_ratio:.1f}% "
                    f"cent={m.centroid_hz:.0f}Hz "
                    f"onsets={m.onset_count}"
                )
                params = result.spec.param_overrides
                layers = []
            else:
                # Stub/dict result for testing
                name = getattr(result, "name", f"V{i}")
                score = getattr(result, "aggregate", 1.0)
                summary = getattr(result, "summary", "")
                params = getattr(result, "params", {})
                layers = getattr(result, "layers", [])

            card = _VariantCard(
                name=name,
                score=score,
                metrics_summary=summary,
                y=y if isinstance(y, np.ndarray) else None,
                sr=sr if isinstance(sr, int) else 44100,
                params=params,
                layers=layers,
                service=self._service,
                parent=self._grid_container,
            )
            card.promoteRequested.connect(self._on_card_promote)
            self._cards.append(card)
            row = i // cols
            col = i % cols
            self._grid_layout.addWidget(card, row, col)

        self._count_label.setText(f"{len(results)} variants")

    def _clear_cards(self) -> None:
        for card in self._cards:
            self._grid_layout.removeWidget(card)
            card.deleteLater()
        self._cards.clear()

    # ── Slots ─────────────────────────────────────────────────────────

    def _on_sweep(self) -> None:
        """Emit a signal requesting a sweep (handled by MainWindow)."""
        axis = self._axis_combo.currentText()
        vals_text = self._values_edit.text().strip()
        if not vals_text:
            self._count_label.setText("Enter values first")
            return
        try:
            values = [float(v.strip()) for v in vals_text.split(",") if v.strip()]
        except ValueError:
            self._count_label.setText("Invalid values — use comma-separated numbers")
            return
        if not values:
            self._count_label.setText("Enter values first")
            return
        self.sweepRequested.emit(axis, values)

    def _on_card_promote(self, params: dict, layers: list) -> None:
        self.promoteRequested.emit(params, layers)

    # New signal for sweep
    sweepRequested = Signal(str, list)  # (axis, values)
