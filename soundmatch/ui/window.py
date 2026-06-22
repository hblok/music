"""soundmatch.ui.window — MainWindow for Sound-Match Studio.

Docks the reference, stems, metrics, patch editor, scorecard, variant grid,
and A/B viewer panels.  Owns a PlaybackService.  Wires panel signals together:
selection change → re-characterize, stem chosen → set target stem +
re-characterize, patch change → render candidate + score, sweep → variant
grid, promote → patch editor.

File menu: New / Open / Save MatchProject (.smatch JSON).
"""

from __future__ import annotations

import logging
import json
from pathlib import Path
from typing import Any

import numpy as np

log = logging.getLogger(__name__)

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
from inspector.metrics import Metrics, characterize
from soundmatch.core.candidate import render_phrase
from soundmatch.core.phrase import Phrase, seed_from_metrics
from soundmatch.core.project import MatchProject
from soundmatch.core.scoring import Scorecard, diff
from soundmatch.core.target import Target
from soundmatch.core.variants import render_and_score, sweep
from soundmatch.ui.ab_viewer import ABViewer
from soundmatch.ui.metrics_panel import MetricsPanel
from soundmatch.ui.patch_editor import PatchEditor
from soundmatch.ui.reference_panel import ReferencePanel
from soundmatch.ui.scorecard_panel import ScorecardPanel
from soundmatch.ui.stems_panel import StemsPanel
from soundmatch.ui.variant_grid import VariantGrid


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
        self._target_metrics: Metrics | None = None
        self._phrase: Phrase | None = None
        self._project: MatchProject = MatchProject()
        self._cand_y: np.ndarray | None = None
        self._cand_sr: int = 44100

        self.setWindowTitle("Sound-Match Studio")
        self.setObjectName("soundmatch-main-window")
        self.resize(1200, 800)

        # Central placeholder
        central = QWidget()
        central.setObjectName("central-widget")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(4, 4, 4, 4)

        # ── Dock: Reference panel (left) ───────────────────────
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

        # ── Dock: Stems panel (left, tabbed with reference) ───
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
        self.tabifyDockWidget(ref_dock, stems_dock)

        # ── Dock: Metrics panel (right) ───────────────────────
        self._metrics = MetricsPanel()
        self._metrics.setObjectName("metrics-panel")
        metrics_dock = QDockWidget("Metrics", self)
        metrics_dock.setObjectName("metrics-dock")
        metrics_dock.setWidget(self._metrics)
        metrics_dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea,
        )
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, metrics_dock)

        # ── Dock: Patch editor (right, tabbed with metrics) ───
        self._patch_editor = PatchEditor()
        self._patch_editor.setObjectName("patch-editor")
        self._patch_editor.patchChanged.connect(self._on_patch_changed)
        self._patch_editor.suggestRequested.connect(self._on_suggest_requested)
        patch_dock = QDockWidget("Patch Editor", self)
        patch_dock.setObjectName("patch-editor-dock")
        patch_dock.setWidget(self._patch_editor)
        patch_dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea,
        )
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, patch_dock)
        self.tabifyDockWidget(metrics_dock, patch_dock)

        # ── Dock: Scorecard panel (right, tabbed with metrics) ─
        self._scorecard = ScorecardPanel(service)
        self._scorecard.setObjectName("scorecard-panel")
        scorecard_dock = QDockWidget("Scorecard", self)
        scorecard_dock.setObjectName("scorecard-dock")
        scorecard_dock.setWidget(self._scorecard)
        scorecard_dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea,
        )
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, scorecard_dock)
        self.tabifyDockWidget(patch_dock, scorecard_dock)

        # ── Dock: Variant grid (bottom) ────────────────────────
        self._variant_grid = VariantGrid(service=service)
        self._variant_grid.setObjectName("variant-grid")
        self._variant_grid.sweepRequested.connect(self._on_sweep_requested)
        self._variant_grid.promoteRequested.connect(self._on_promote_requested)
        variant_dock = QDockWidget("Variants", self)
        variant_dock.setObjectName("variant-dock")
        variant_dock.setWidget(self._variant_grid)
        variant_dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, variant_dock)

        # ── Dock: A/B viewer (bottom, tabbed with variants) ───
        self._ab_viewer = ABViewer(service)
        self._ab_viewer.setObjectName("ab-viewer")
        ab_dock = QDockWidget("A/B Viewer", self)
        ab_dock.setObjectName("ab-dock")
        ab_dock.setWidget(self._ab_viewer)
        ab_dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, ab_dock)

        # Tabify A/B viewer with variant grid
        self.tabifyDockWidget(variant_dock, ab_dock)

        # Raise the primary tabs so they're visible on startup
        ref_dock.raise_()
        metrics_dock.raise_()

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
        file_menu.addAction("&New", self._on_new_project)
        file_menu.addAction("&Open…", self._on_open_project)
        file_menu.addAction("&Save…", self._on_save_project)
        file_menu.addAction("Save &As…", self._on_save_project_as)
        file_menu.addSeparator()
        file_menu.addAction("&Open Reference…", self._on_open_reference)
        file_menu.addSeparator()

        export_menu = file_menu.addMenu("E&xport")
        export_menu.addAction("Patch Snippet…", self._on_export_snippet)
        export_menu.addAction("Markdown Report…", self._on_export_markdown)
        export_menu.addAction("Montage PNG…", self._on_export_montage)

        file_menu.addSeparator()
        file_menu.addAction("&Quit", QApplication.quit)

    # ── File menu slots ────────────────────────────────────────────

    def _on_new_project(self) -> None:
        """Reset the project and all panels."""
        self._project = MatchProject()
        self._target = None
        self._ref_path = None
        self._target_metrics = None
        self._phrase = None
        self._cand_y = None
        self._reference._y = None
        self._reference._sr = 44100
        self._reference._waveform.clear()
        self._reference._spectrogram.clear()
        self._stems.set_stems({}, sr=44100)
        self._metrics.clear()
        self._scorecard.clear()
        self._ab_viewer.clear()
        self._variant_grid.set_results([])
        self._status_label.setText("New project")

    def _on_open_project(self) -> None:
        """Open a saved MatchProject (.smatch JSON)."""
        path_str, _ = QFileDialog.getOpenFileName(
            self, "Open Project", "",
            "Sound-Match Project (*.smatch);;JSON (*.json);;All (*)",
        )
        if not path_str:
            return
        p = Path(path_str)
        try:
            proj = MatchProject.load(p)
        except Exception as exc:
            self._status_label.setText(f"Open error: {exc}")
            return

        self._project = proj

        # Restore UI state from project
        if proj.reference_path and proj.reference_path.exists():
            self._ref_path = proj.reference_path
            self._reference.load_audio(proj.reference_path)
            self._status_label.setText(f"Loading: {proj.reference_path.name}…")
        else:
            self._status_label.setText(f"Project opened (reference not found)")

        if proj.target_metrics is not None:
            self._target_metrics = proj.target_metrics
            self._metrics.set_metrics(proj.target_metrics)
            self._scorecard.set_target_metrics(proj.target_metrics)

        if proj.phrase is not None:
            self._phrase = proj.phrase

        # Restore patch editor state
        if proj.instrument_id:
            self._patch_editor.set_patch(
                proj.instrument_id, proj.params, proj.layers, proj.seed,
            )

    def _on_save_project(self) -> None:
        """Save the project (prompt for path if not yet saved)."""
        if self._project.reference_path == Path("."):
            self._on_save_project_as()
        else:
            self._save_project_to(self._project.reference_path.parent / "project.smatch")

    def _on_save_project_as(self) -> None:
        """Save the project to a new path."""
        path_str, _ = QFileDialog.getSaveFileName(
            self, "Save Project", "project.smatch",
            "Sound-Match Project (*.smatch);;JSON (*.json);;All (*)",
        )
        if path_str:
            self._save_project_to(Path(path_str))

    def _save_project_to(self, p: Path) -> None:
        """Persist the current session into a MatchProject and save."""
        proj = self._project
        if self._ref_path is not None:
            proj.reference_path = self._ref_path
        if self._target_metrics is not None:
            proj.target_metrics = self._target_metrics
        if self._phrase is not None:
            proj.phrase = self._phrase
        proj.instrument_id = self._patch_editor.instrument_id
        proj.params = dict(self._patch_editor.params)
        proj.layers = list(self._patch_editor.layers)
        proj.seed = self._patch_editor.seed
        try:
            proj.update_sha()
        except Exception:
            pass
        proj.save(p)
        self._status_label.setText(f"Saved: {p.name}")

    # ── Export slots ────────────────────────────────────────────────

    def _on_export_snippet(self) -> None:
        """Export a runnable Python patch snippet."""
        if self._phrase is None:
            self._status_label.setText("No phrase — render a candidate first")
            return
        path_str, _ = QFileDialog.getSaveFileName(
            self, "Export Patch Snippet", "matched_snippet.py",
            "Python (*.py);;All (*)",
        )
        if not path_str:
            return
        from soundmatch.core.exporters import export_snippet
        export_snippet(
            self._phrase,
            self._patch_editor.instrument_id,
            self._patch_editor.params,
            self._patch_editor.layers,
            self._patch_editor.seed,
            Path(path_str),
        )
        self._status_label.setText(f"Snippet exported: {Path(path_str).name}")

    def _on_export_markdown(self) -> None:
        """Export a markdown characterization report."""
        if self._target_metrics is None:
            self._status_label.setText("No target — characterize first")
            return
        path_str, _ = QFileDialog.getSaveFileName(
            self, "Export Markdown Report", "report.md",
            "Markdown (*.md);;All (*)",
        )
        if not path_str:
            return
        from soundmatch.core.exporters import export_markdown
        scorecard_dict = None
        if self._scorecard.scorecard is not None:
            scorecard_dict = self._scorecard.scorecard.to_dict()
        export_markdown(
            self._target_metrics,
            cand_metrics=None,
            scorecard_dict=scorecard_dict,
            reference=str(self._ref_path) if self._ref_path else "",
            instrument_id=self._patch_editor.instrument_id,
            path=Path(path_str),
        )
        self._status_label.setText(f"Report exported: {Path(path_str).name}")

    def _on_export_montage(self) -> None:
        """Export a montage PNG via the A/B viewer."""
        if self._cand_y is None:
            self._status_label.setText("No candidate — render first")
            return
        path_str, _ = QFileDialog.getSaveFileName(
            self, "Export Montage PNG", "ab_montage.png",
            "PNG (*.png);;All (*)",
        )
        if not path_str:
            return
        from soundmatch.core.exporters import export_montage_png
        target_y = self._target_y_for_ab()
        if target_y is not None:
            export_montage_png(
                target_y, 44100,
                self._cand_y, self._cand_sr,
                Path(path_str),
            )
            self._status_label.setText(f"Montage exported: {Path(path_str).name}")

    # ── Panel signal slots ──────────────────────────────────────────

    def _on_open_reference(self) -> None:
        path_str, _ = QFileDialog.getOpenFileName(
            self, "Open Reference Audio", "",
            "Audio (*.wav *.mp3 *.flac *.ogg *.m4a);;All (*)",
        )
        if path_str:
            self._ref_path = Path(path_str)
            self._reference.load_audio(self._ref_path)
            self._status_label.setText(f"Loading: {self._ref_path.name}…")

    def _on_selection_changed(self, start_s: float, end_s: float) -> None:
        """Handle selection change: characterize the selected region."""
        log.debug("selection changed: %.2f–%.2fs", start_s, end_s)
        self._status_label.setText("Characterizing…")
        QApplication.processEvents()
        self._characterize_target(start_s, end_s, stem="mix")

    def _on_stem_chosen(self, stem_name: str) -> None:
        """Handle stem choice: re-characterize with the chosen stem."""
        start_s = 0.0
        end_s = 10.0
        y, sr = self._reference.audio_data
        if y is not None:
            end_s = len(y) / sr
        log.debug("stem chosen: %s", stem_name)
        self._status_label.setText(f"Characterizing stem '{stem_name}'…")
        QApplication.processEvents()
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
        log.debug("patch changed: %s seed=%d", instrument_id, seed)
        self._status_label.setText("Rendering…")
        QApplication.processEvents()

        if self._phrase is None:
            self._phrase = seed_from_metrics(self._target_metrics, bpm=138.0)

        try:
            buf = render_phrase(self._phrase, instrument_id, params, layers, seed)
            cand_y = buf.data.mean(axis=1) if buf.data.ndim == 2 else buf.data
            cand_y = np.ascontiguousarray(cand_y)
            cand_metrics = characterize(cand_y, buf.sr)
            sc = diff(self._target_metrics, cand_metrics)
            self._scorecard.set_scorecard(sc, cand_y=cand_y, cand_sr=buf.sr)

            self._cand_y = cand_y
            self._cand_sr = buf.sr
            self._ab_viewer.set_candidate(cand_y, buf.sr)
            target_y = self._target_y_for_ab()
            if target_y is not None:
                self._ab_viewer.set_target(target_y, 44100)

            agg = sc.aggregate()
            worst = sc.worst()
            log.debug("render done: agg=%.4f worst=%s", agg, worst)
            self._status_label.setText(f"Candidate: agg={agg:.4f} worst={worst}")
        except Exception as exc:
            log.error("render error: %s", exc, exc_info=True)
            self._status_label.setText(f"Render error: {exc}")

    def _on_sweep_requested(self, axis: str, values: list) -> None:
        """Handle variant sweep request from the grid."""
        if self._target_metrics is None or self._phrase is None:
            self._status_label.setText("No target — characterize first")
            return
        log.debug("sweep requested: axis=%s values=%s", axis, values)
        self._status_label.setText(f"Sweeping '{axis}'…")
        QApplication.processEvents()

        try:
            specs = sweep(self._patch_editor.params, axis, values)
            results = render_and_score(
                self._phrase,
                self._patch_editor.instrument_id,
                self._patch_editor.params,
                specs,
                self._target_metrics,
                layers=self._patch_editor.layers,
                seed=self._patch_editor.seed,
            )

            audio_data: list[tuple[np.ndarray, int]] = []
            for r in results:
                merged = dict(self._patch_editor.params)
                merged.update(r.spec.param_overrides)
                buf = render_phrase(
                    self._phrase,
                    self._patch_editor.instrument_id,
                    merged,
                    self._patch_editor.layers,
                    self._patch_editor.seed,
                )
                y = buf.data.mean(axis=1) if buf.data.ndim == 2 else buf.data
                audio_data.append((y, buf.sr))

            log.debug("sweep done: %d variants on '%s'", len(results), axis)
            self._variant_grid.set_results(results, audio_data=audio_data)
            self._status_label.setText(f"Swept {len(results)} variants on axis '{axis}'")
        except Exception as exc:
            log.error("sweep error: %s", exc, exc_info=True)
            self._status_label.setText(f"Sweep error: {exc}")

    def _on_promote_requested(self, params: dict, layers: list) -> None:
        """Promote a variant's params back to the patch editor."""
        inst_id = self._patch_editor.instrument_id
        seed = self._patch_editor.seed
        self._patch_editor.set_patch(inst_id, params, layers, seed)
        self._status_label.setText("Promoted variant → Patch Editor")

    def _on_suggest_requested(self) -> None:
        """Run a coarse param search and apply the best result."""
        if self._target_metrics is None or self._phrase is None:
            self._status_label.setText("No target — characterize first")
            return

        log.debug("suggest requested")
        from soundmatch.core.search import coarse_search
        self._status_label.setText("Searching…")
        QApplication.processEvents()

        try:
            result = coarse_search(
                self._target_metrics,
                self._phrase,
                self._patch_editor.instrument_id,
                self._patch_editor.params,
                self._patch_editor.layers,
                self._patch_editor.seed,
            )
            self._patch_editor.set_patch(
                result.instrument_id,
                result.best_params,
                result.best_layers,
                result.seed,
            )
            log.debug("suggest done: agg=%.4f iterations=%d", result.best_score, result.iterations)
            self._status_label.setText(
                f"Suggest: agg={result.best_score:.4f} ({result.iterations} iterations)"
            )
        except Exception as exc:
            log.error("suggest error: %s", exc, exc_info=True)
            self._status_label.setText(f"Search error: {exc}")

    def _characterize_target(self, start_s: float, end_s: float, stem: str = "other") -> None:
        """Characterize the target and update the metrics panel."""
        y, sr = self._reference.audio_data
        if y is None:
            return

        log.debug("characterize: %.2f–%.2fs stem=%s", start_s, end_s, stem)
        try:
            if stem == "mix":
                i0 = int(start_s * sr)
                i1 = min(int(end_s * sr), len(y))
                m = characterize(y[i0:i1], sr)
            else:
                stem_audio = self._stems.get_stem_audio(stem)
                m = characterize(stem_audio if stem_audio is not None else y, sr)

            self._target_metrics = m
            self._metrics.set_metrics(m)
            self._scorecard.set_target_metrics(m)
            self._phrase = seed_from_metrics(m, bpm=138.0)

            self._project.start_s = start_s
            self._project.end_s = end_s
            self._project.stem = stem
            self._project.target_metrics = m
            self._project.phrase = self._phrase

            log.debug("characterize done: perc=%.1f%% cent=%.0fHz", m.percussive_ratio, m.centroid_hz)
            self._status_label.setText(
                f"Target: perc={m.percussive_ratio:.1f}% cent={m.centroid_hz:.0f}Hz"
            )
        except Exception as exc:
            log.error("characterize error: %s", exc, exc_info=True)
            self._status_label.setText(f"Characterization error: {exc}")

    def _target_y_for_ab(self) -> np.ndarray | None:
        """Get the target audio for the A/B viewer."""
        y, sr = self._reference.audio_data
        return y

    # ── Public properties ──────────────────────────────────────────

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

    @property
    def variant_grid(self) -> VariantGrid:
        return self._variant_grid

    @property
    def ab_viewer(self) -> ABViewer:
        return self._ab_viewer
