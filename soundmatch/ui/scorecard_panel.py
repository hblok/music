"""soundmatch.ui.scorecard_panel — target vs candidate Δ table + aggregate.

On patch change, calls ``render_phrase`` + ``characterize`` + ``diff`` to
compute a Scorecard comparing the candidate against the target.  Displays
per-metric target/candidate/Δ values and the aggregate distance.  Highlights
the worst metric (the one to chase next).  Provides an audition button for
the candidate audio (looped via PlaybackService).
"""

from __future__ import annotations

from typing import Any

import numpy as np

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from forge.playback.service import PlaybackService


class ScorecardPanel(QWidget):
    """Scorecard panel: target vs candidate comparison.

    Signals:
        candidateRendered(y, sr): Emitted when a candidate is rendered
            and characterized.  Carries the mono audio and sample rate.

    Args:
        service: PlaybackService for auditioning the candidate.
        parent:  Optional parent widget.
    """

    candidateRendered = Signal(np.ndarray, int)

    def __init__(
        self,
        service: PlaybackService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._service = service
        self._target_metrics = None
        self._scorecard = None
        self._cand_y: np.ndarray | None = None
        self._cand_sr: int = 44100

        self.setObjectName("scorecard-panel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Title
        title = QLabel("Scorecard")
        title.setObjectName("scorecard-title")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)

        # Aggregate display
        agg_row = QHBoxLayout()
        agg_row.addWidget(QLabel("Aggregate Distance:"))
        self._agg_label = QLabel("—")
        self._agg_label.setObjectName("aggregate-label")
        self._agg_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        agg_row.addWidget(self._agg_label)
        agg_row.addStretch()
        layout.addLayout(agg_row)

        # Worst metric
        worst_row = QHBoxLayout()
        worst_row.addWidget(QLabel("Worst Metric:"))
        self._worst_label = QLabel("—")
        self._worst_label.setObjectName("worst-label")
        self._worst_label.setStyleSheet("color: red; font-weight: bold;")
        worst_row.addWidget(self._worst_label)
        worst_row.addStretch()
        layout.addLayout(worst_row)

        # Delta table
        self._table = QTableWidget(0, 4)
        self._table.setObjectName("scorecard-table")
        self._table.setHorizontalHeaderLabels(["Metric", "Target", "Candidate", "Δ"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self._table)

        # Audition button
        self._play_btn = QPushButton("▶ Play Candidate")
        self._play_btn.setObjectName("play-candidate-btn")
        self._play_btn.setEnabled(False)
        self._play_btn.clicked.connect(self._on_play)
        layout.addWidget(self._play_btn)

    # ── Public API ───────────────────────────────────────────────────

    def set_target_metrics(self, metrics: Any) -> None:
        """Set the target Metrics for comparison."""
        self._target_metrics = metrics

    def set_scorecard(self, scorecard: Any, cand_y: np.ndarray | None = None, cand_sr: int = 44100) -> None:
        """Set a pre-computed Scorecard and optional candidate audio."""
        self._scorecard = scorecard
        self._cand_y = cand_y
        self._cand_sr = cand_sr
        self._play_btn.setEnabled(cand_y is not None)
        self._update_display()

    @property
    def scorecard(self):
        return self._scorecard

    # ── Internal ─────────────────────────────────────────────────────

    def _update_display(self) -> None:
        """Refresh the table and labels from the current scorecard."""
        if self._scorecard is None:
            self._agg_label.setText("—")
            self._worst_label.setText("—")
            self._table.setRowCount(0)
            return

        # Aggregate
        agg = self._scorecard.aggregate()
        self._agg_label.setText(f"{agg:.4f}")
        if agg < 0.2:
            self._agg_label.setStyleSheet("font-weight: bold; font-size: 14px; color: green;")
        elif agg < 0.5:
            self._agg_label.setStyleSheet("font-weight: bold; font-size: 14px; color: orange;")
        else:
            self._agg_label.setStyleSheet("font-weight: bold; font-size: 14px; color: red;")

        # Worst metric
        worst = self._scorecard.worst()
        self._worst_label.setText(worst)

        # Table rows
        rows = self._build_rows()
        self._table.setRowCount(len(rows))
        for r, (name, target_val, cand_val, delta, is_worst) in enumerate(rows):
            items = [
                QTableWidgetItem(name),
                QTableWidgetItem(f"{target_val:.3g}"),
                QTableWidgetItem(f"{cand_val:.3g}"),
                QTableWidgetItem(f"{delta:.3g}"),
            ]
            for c, item in enumerate(items):
                if is_worst:
                    item.setForeground(Qt.GlobalColor.red)
                    item.setFont(item.font())  # ensure font is set
                self._table.setItem(r, c, item)

        self._table.resizeColumnsToContents()

    def _build_rows(self) -> list[tuple[str, float, float, float, bool]]:
        """Build table rows from the scorecard.

        Returns list of (metric_name, target, candidate, delta, is_worst).
        """
        if self._scorecard is None:
            return []

        worst_name = self._scorecard.worst()
        rows: list[tuple[str, float, float, float, bool]] = []

        # Scalar metrics
        for name in ("percussive_ratio", "centroid_hz", "onset_count",
                      "onset_density", "median_ioi_s"):
            md = getattr(self._scorecard, name)
            is_worst = (name == worst_name)
            rows.append((name, md.target, md.candidate, md.delta, is_worst))

        # band_balance
        if self._scorecard.band_balance:
            for band, md in sorted(self._scorecard.band_balance.items()):
                is_worst = ("band_balance" == worst_name)
                rows.append((f"bb:{band}", md.target, md.candidate, md.delta, is_worst))

        # band_decay_ms
        if self._scorecard.band_decay_ms:
            for band, md in sorted(self._scorecard.band_decay_ms.items()):
                is_worst = ("band_decay_ms" == worst_name)
                rows.append((f"bd:{band}", md.target, md.candidate, md.delta, is_worst))

        return rows

    def _on_play(self) -> None:
        """Play the candidate audio via PlaybackService."""
        if self._cand_y is None:
            return
        from forge.core.buffer import AudioBuffer
        buf = AudioBuffer.from_mono(self._cand_y, sr=self._cand_sr)
        self._service.load(buf)
        self._service.play()

    def clear(self) -> None:
        """Clear all scorecard data."""
        self._target_metrics = None
        self._scorecard = None
        self._cand_y = None
        self._cand_sr = 44100
        self._play_btn.setEnabled(False)
        self._update_display()
