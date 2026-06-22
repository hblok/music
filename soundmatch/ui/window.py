"""soundmatch.ui.window — MainWindow for Sound-Match Studio.

Docks the reference, stems, metrics, patch editor, and scorecard panels.
Owns a PlaybackService.  Wires panel signals together: selection change →
re-characterize, stem chosen → set target stem + re-characterize, patch
change → render candidate + score.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QDockWidget,
    QFileDialog,
    QLabel,
    QMainWindow,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from forge.playback.service import PlaybackService
from inspector.metrics import characterize
from soundmatch.core.candidate import render_phrase
from soundmatch.core.phrase import Phrase, seed_from_metrics
from soundmatch.core.scoring import diff
from soundmatch.core.target import Target
from soundmatch.ui.metrics_panel import MetricsPanel
from soundmatch.ui.patch_editor import PatchEditor
from soundmatch.ui.reference_panel import ReferencePanel
from soundmatch.ui.scorecard_panel import ScorecardPanel
from soundmatch.ui.stems_panel import StemsPanel


class MainWindow(QMainWindow):
    """Sound-Match Studio main window.

    Args:
        service: PlaybackService (injected for testing / sharing).
        parent:  Optional parent widget.
    """

    def __init__(
        self,
        service: PlaybackService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._service = service
        self._target: Target | None = None
        self._ref_path: Path | None = None
        self._target_metrics = None
        self._phrase: Phrase | None = None

        self.setWindowTitle("Sound-Match Studio")
        self.setObjectName("soundmatch-main-window")
        self.resize(1100, 700)

        # Central placeholder
        central = QWidget()
        central.setObjectName("central-widget")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(4, 4, 4, 4)

        # Reference panel (dock left)
        self._reference = ReferencePanel(service)
        self._reference.setObjectName("reference-panel")
        self._reference.selectionChanged.connect(self._on_selection_changed)
        ref_dock = QDockWidget("Reference", self)
        ref_dock.setObjectName("reference-dock")
        ref_dock.setWidget(self._reference)
        ref_dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea,
        )
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, ref_dock)

        # Stems panel (dock left, below reference)
        self._stems = StemsPanel(service)
        self._stems.setObjectName("stems-panel")
        self._stems.targetChosen.connect(self._on_stem_chosen)
        stems_dock = QDockWidget("Stems", self)
        stems_dock.setObjectName("stems-dock")
        stems_dock.setWidget(self._stems)
        stems_dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea,
        )
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, stems_dock)

        # Metrics panel (dock right)
        self._metrics = MetricsPanel()
        self._metrics.setObjectName("metrics-panel")
        metrics_dock = QDockWidget("Metrics", self)
        metrics_dock.setObjectName("metrics-dock")
        metrics_dock.setWidget(self._metrics)
        metrics_dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea,
        )
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, metrics_dock)

        # Patch editor (dock right, below metrics)
        self._patch_editor = PatchEditor()
        self._patch_editor.setObjectName("patch-editor")
        self._patch_editor.patchChanged.connect(self._on_patch_changed)
        patch_dock = QDockWidget("Patch Editor", self)
        patch_dock.setObjectName("patch-editor-dock")
        patch_dock.setWidget(self._patch_editor)
        patch_dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea,
        )
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, patch_dock)

        # Scorecard panel (dock right, below patch editor)
        self._scorecard = ScorecardPanel(service)
        self._scorecard.setObjectName("scorecard-panel")
        scorecard_dock = QDockWidget("Scorecard", self)
        scorecard_dock.setObjectName("scorecard-dock")
        scorecard_dock.setWidget(self._scorecard)
        scorecard_dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea,
        )
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, scorecard_dock)

        # Status bar
        self._status = QStatusBar()
        self._status_label = QLabel("Ready")
        self._status_label.setObjectName("status-label")
        self._status.addWidget(self._status_label)
        self.setStatusBar(self._status)

        # Menu
        self._build_menu()

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction("&Open Reference\u2026", self._on_open_reference)
        file_menu.addSeparator()
        file_menu.addAction("&Quit", QApplication.quit)

    # ------------------------------------------------------------------ slots

    def _on_open_reference(self) -> None:
        path_str, _ = QFileDialog.getOpenFileName(
            self, "Open Reference Audio", "",
            "Audio (*.wav *.mp3 *.flac *.ogg *.m4a);;All (*)",
        )
        if path_str:
            self._ref_path = Path(path_str)
            self._reference.load_audio(self._ref_path)
            self._status_label.setText(f"Loaded: {self._ref_path.name}")

    def _on_selection_changed(self, start_s: float, end_s: float) -> None:
        """Handle selection change: characterize the selected region."""
        self._characterize_target(start_s, end_s, stem="mix")

    def _on_stem_chosen(self, stem_name: str) -> None:
        """Handle stem choice: re-characterize with the chosen stem."""
        start_s = 0.0
        end_s = 10.0
        # Get current selection from reference panel
        y, sr = self._reference.audio_data
        if y is not None:
            start_s = 0.0
            end_s = len(y) / sr
        self._characterize_target(start_s, end_s, stem=stem_name)

    def _on_patch_changed(
        self,
        instrument_id: str,
        params: dict[str, Any],
        layers: list[tuple[str, dict[str, Any]]],
        seed: int,
    ) -> None:
        """Handle patch change: render candidate, characterize, score."""
        if self._target_metrics is None:
            self._status_label.setText("No target — load and select reference first")
            return

        if self._phrase is None:
            # Seed a phrase from the target metrics
            self._phrase = seed_from_metrics(self._target_metrics, bpm=138.0)

        try:
            buf = render_phrase(
                self._phrase, instrument_id, params, layers, seed,
            )
            # Convert to mono for characterization
            cand_y = buf.data.mean(axis=1) if buf.data.ndim == 2 else buf.data
            cand_y = np.ascontiguousarray(cand_y)
            cand_metrics = characterize(cand_y, buf.sr)
            sc = diff(self._target_metrics, cand_metrics)
            self._scorecard.set_scorecard(sc, cand_y=cand_y, cand_sr=buf.sr)
            agg = sc.aggregate()
            worst = sc.worst()
            self._status_label.setText(
                f"Candidate: agg={agg:.4f} worst={worst}"
            )
        except Exception as exc:
            self._status_label.setText(f"Render error: {exc}")

    def _characterize_target(self, start_s: float, end_s: float, stem: str = "other") -> None:
        """Characterize the target and update the metrics panel."""
        y, sr = self._reference.audio_data
        if y is None:
            return

        # Create target and measure
        try:
            # Use the loaded audio directly for characterization
            # (no separation needed if stem="mix")
            if stem == "mix":
                # Extract region
                i0 = int(start_s * sr)
                i1 = min(int(end_s * sr), len(y))
                region = y[i0:i1]
                m = characterize(region, sr)
            else:
                # Try to get stem audio from stems panel
                stem_audio = self._stems.get_stem_audio(stem)
                if stem_audio is not None:
                    m = characterize(stem_audio, sr)
                else:
                    m = characterize(y, sr)

            self._target_metrics = m
            self._metrics.set_metrics(m)
            self._scorecard.set_target_metrics(m)

            # Seed a phrase from the target metrics
            self._phrase = seed_from_metrics(m, bpm=138.0)

            self._status_label.setText(
                f"Target: perc={m.percussive_ratio:.1f}% cent={m.centroid_hz:.0f}Hz"
            )
        except Exception as exc:
            self._status_label.setText(f"Characterization error: {exc}")

    @property
    def reference_panel(self) -> ReferencePanel:
        return self._reference

    @property
    def stems_panel(self) -> StemsPanel:
        return self._stems

    @property
    def metrics_panel(self) -> MetricsPanel:
        return self._metrics

    @property
    def patch_editor(self) -> PatchEditor:
        return self._patch_editor

    @property
    def scorecard_panel(self) -> ScorecardPanel:
        return self._scorecard
