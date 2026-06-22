"""soundmatch.ui.metrics_panel — render the Metrics battery as numbers + plots.

Displays target Metrics as:
  - A numbers grid (percussive %, centroid Hz, onset count, etc.)
  - A band-balance bar plot
  - An onset table
"""

from __future__ import annotations

from typing import Any

import numpy as np

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QGridLayout,
    QVBoxLayout,
    QWidget,
)

from inspector.metrics import Metrics

import matplotlib
matplotlib.use("Agg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class MetricsPanel(QWidget):
    """Panel displaying target Metrics as numbers + band-balance bar plot.

    Args:
        parent: Optional parent widget.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._metrics: Metrics | None = None

        self.setObjectName("metrics-panel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Header
        self._header = QLabel("Target Metrics")
        self._header.setObjectName("metrics-header")
        layout.addWidget(self._header)

        # Numbers grid
        self._grid = QGridLayout()
        self._grid.setContentsMargins(2, 2, 2, 2)
        self._grid.setSpacing(4)

        self._perc_label = QLabel("Percussive %:")
        self._perc_value = QLabel("—")
        self._cent_label = QLabel("Centroid Hz:")
        self._cent_value = QLabel("—")
        self._onset_label = QLabel("Onset Count:")
        self._onset_value = QLabel("—")
        self._density_label = QLabel("Onset Density:")
        self._density_value = QLabel("—")
        self._ioi_label = QLabel("Median IOI (s):")
        self._ioi_value = QLabel("—")
        self._chord_label = QLabel("Chord:")
        self._chord_value = QLabel("—")

        row = 0
        for label, value in [
            (self._perc_label, self._perc_value),
            (self._cent_label, self._cent_value),
            (self._onset_label, self._onset_value),
            (self._density_label, self._density_value),
            (self._ioi_label, self._ioi_value),
            (self._chord_label, self._chord_value),
        ]:
            self._grid.addWidget(label, row, 0)
            self._grid.addWidget(value, row, 1)
            row += 1

        layout.addLayout(self._grid)

        # Band balance bar plot
        self._band_fig = Figure(figsize=(4, 1.5), dpi=100, tight_layout=True)
        self._band_canvas = FigureCanvas(self._band_fig)
        self._band_ax = self._band_fig.add_subplot(111)
        self._band_ax.set_visible(False)
        self._band_canvas.setMinimumHeight(60)
        layout.addWidget(self._band_canvas)

        # Decay table
        self._decay_group = QGroupBox("Band Decay (ms)")
        self._decay_layout = QVBoxLayout(self._decay_group)
        self._decay_label = QLabel("—")
        self._decay_layout.addWidget(self._decay_label)
        layout.addWidget(self._decay_group)

    def set_metrics(self, metrics: Metrics) -> None:
        """Update the display with new Metrics.

        Parameters
        ----------
        metrics: The Metrics to display.
        """
        self._metrics = metrics

        # Numbers
        self._perc_value.setText(f"{metrics.percussive_ratio:.1f}")
        self._cent_value.setText(f"{metrics.centroid_hz:.0f}")
        self._onset_value.setText(str(metrics.onset_count))
        self._density_value.setText(f"{metrics.onset_density:.1f} /s")
        self._ioi_value.setText(f"{metrics.median_ioi_s:.3f}")
        chord_pc = ", ".join(metrics.chord.get("pitch_classes", []))
        sub = " (sub-oct)" if metrics.chord.get("sub_octave") else ""
        self._chord_value.setText(f"{chord_pc}{sub}" if chord_pc else "—")

        # Band balance bar plot
        self._band_ax.clear()
        self._band_ax.set_visible(True)
        if metrics.band_balance:
            bands = list(metrics.band_balance.keys())
            values = [metrics.band_balance[b] for b in bands]
            colors = ["#3498db", "#2ecc71", "#e74c3c", "#f39c12"][:len(bands)]
            self._band_ax.bar(bands, values, color=colors, edgecolor="white", linewidth=0.5)
            self._band_ax.set_ylabel("%")
            self._band_ax.set_title("Band Balance", fontsize=9)
        self._band_canvas.draw()

        # Decay
        if metrics.band_decay_ms:
            lines = [f"{k}: {v:.1f} ms" for k, v in metrics.band_decay_ms.items()]
            self._decay_label.setText("\n".join(lines))
        else:
            self._decay_label.setText("—")

    def clear(self) -> None:
        """Clear the display."""
        self._metrics = None
        for v in (self._perc_value, self._cent_value, self._onset_value,
                  self._density_value, self._ioi_value, self._chord_value):
            v.setText("—")
        self._band_ax.clear()
        self._band_ax.set_visible(False)
        self._band_canvas.draw()
        self._decay_label.setText("—")

    @property
    def metrics(self) -> Metrics | None:
        """Return the currently displayed Metrics, if any."""
        return self._metrics
