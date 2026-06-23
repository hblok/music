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

from PySide6.QtCore import Qt, QObject, QThread, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QDockWidget,
    QFileDialog,
    QLabel,
    QMainWindow,
    QPlainTextEdit,
    QProgressBar,
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
from soundmatch.core.variants import render_and_score, sweep
from soundmatch.ui.ab_viewer import ABViewer
from soundmatch.ui.instrument_search_dialog import InstrumentSearchDialog
from soundmatch.ui.metrics_panel import MetricsPanel
from soundmatch.ui.patch_editor import PatchEditor
from soundmatch.ui.reference_panel import ReferencePanel
from soundmatch.ui.scorecard_panel import ScorecardPanel
from soundmatch.ui.stems_panel import StemsPanel
from soundmatch.ui.variant_grid import VariantGrid


class _SearchWorker(QObject):
    """Runs coarse_search on a background thread."""

    finished = Signal(object)       # SearchResult
    progress = Signal(int, int)     # (done, total)
    error = Signal(str)

    def __init__(self, target, phrase, instrument_id, params, layers, seed):
        super().__init__()
        self._target = target
        self._phrase = phrase
        self._instrument_id = instrument_id
        self._params = params
        self._layers = layers
        self._seed = seed

    def run(self) -> None:
        from soundmatch.core.search import coarse_search
        try:
            # Throttle: emit at most ~20 progress updates so the event queue
            # doesn't flood before the main thread has time to paint any of them.
            _last_emitted = [-1]
            def _progress(done: int, total: int) -> None:
                step = max(1, total // 20)
                if done - _last_emitted[0] >= step or done >= total:
                    _last_emitted[0] = done
                    self.progress.emit(done, total)
            result = coarse_search(
                self._target, self._phrase,
                self._instrument_id, self._params, self._layers, self._seed,
                on_progress=_progress,
            )
            self.finished.emit(result)
        except Exception as exc:
            log.error("search worker error: %s", exc, exc_info=True)
            self.error.emit(str(exc))


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
        self._ref_path: Path | None = None
        self._target_metrics: Metrics | None = None
        self._phrase: Phrase | None = None
        self._project: MatchProject = MatchProject()
        self._cand_y: np.ndarray | None = None
        self._cand_sr: int = 44100
        self._search_worker: _SearchWorker | None = None
        self._search_thread: QThread | None = None
        # Current time selection in original-file coordinates
        self._sel_start_s: float = 0.0
        self._sel_end_s: float = 10.0

        self.setWindowTitle("Sound-Match Studio")
        self.setObjectName("soundmatch-main-window")
        self.resize(1200, 800)

        # ── Menu bar ──────────────────────────────────────────────
        tools_menu = self.menuBar().addMenu("&Tools")

        export_act = QAction("Export Sound Brief…", self)
        export_act.setToolTip(
            "Analyse the selected region and export a brief for an AI to implement a new instrument"
        )
        export_act.triggered.connect(self._on_export_brief)
        tools_menu.addAction(export_act)

        reload_act = QAction("Reload Instruments", self)
        reload_act.setToolTip("Re-import forge/instruments/ to pick up newly added instrument files")
        reload_act.triggered.connect(self._on_reload_instruments)
        tools_menu.addAction(reload_act)

        tools_menu.addSeparator()

        resynth_act = QAction("Resynthesize Region…", self)
        resynth_act.setToolTip(
            "Reconstruct the selected region from scratch using additive synthesis "
            "and spectrally-shaped noise — no original bytes replayed"
        )
        resynth_act.triggered.connect(self._on_resynthesize)
        tools_menu.addAction(resynth_act)

        # Central placeholder
        central = QWidget()
        central.setObjectName("central-widget")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(4, 4, 4, 4)

        # ── Dock: Reference panel (left) ───────────────────────
        self._reference = ReferencePanel(service)
        self._reference.setObjectName("reference-panel")
        self._reference.fileLoaded.connect(self._on_reference_file_loaded)
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
        self._stems.separateRequested.connect(self._on_separate_requested)
        self._stems.stemsReady.connect(self._on_stems_ready)
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
        self._patch_editor.findInstrumentRequested.connect(self._on_find_instrument_requested)
        self._patch_editor.noteOverride.connect(self._on_note_override)
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
        self._status.addWidget(self._status_label, 1)

        self._progress = QProgressBar()
        self._progress.setObjectName("main-progress")
        self._progress.setRange(0, 0)  # indeterminate by default
        self._progress.setMaximumWidth(180)
        self._progress.setVisible(False)
        self._status.addPermanentWidget(self._progress)

        self.setStatusBar(self._status)

        # Menu
        self._build_menu()

    def _show_progress(self, label: str, total: int = 0) -> None:
        """Show the progress bar. total=0 means indeterminate."""
        self._progress.setRange(0, total)
        self._progress.setValue(0)
        self._progress.setVisible(True)
        self._status_label.setText(label)
        QApplication.processEvents()

    def _hide_progress(self) -> None:
        self._progress.setVisible(False)

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
        self._ref_path = None
        self._target_metrics = None
        self._phrase = None
        self._cand_y = None
        self._reference.clear()
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

        # Restore stems if the stems directory still exists
        if proj.stems_dir and proj.stems_dir.is_dir():
            self._load_stems_from_dir(proj.stems_dir)

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

    def _on_reference_file_loaded(self, path: object) -> None:
        """Keep self._ref_path in sync whenever the reference panel finishes loading."""
        from pathlib import Path as _Path
        self._ref_path = _Path(str(path))
        log.debug("ref_path synced: %s", self._ref_path)

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
        """Handle selection change: propagate to stems and re-characterize."""
        log.debug("selection changed: %.2f–%.2fs", start_s, end_s)
        self._sel_start_s = start_s
        self._sel_end_s = end_s
        self._stems.set_selection(start_s, end_s)
        self._show_progress("Characterizing…")
        self._characterize_target(start_s, end_s, stem="mix")
        self._hide_progress()

    def _on_stem_chosen(self, stem_name: str) -> None:
        """Handle stem choice: re-characterize the selected region of this stem."""
        log.debug("stem chosen: %s (%.2f–%.2fs)", stem_name, self._sel_start_s, self._sel_end_s)
        self._show_progress(f"Characterizing stem '{stem_name}'…")
        self._characterize_target(self._sel_start_s, self._sel_end_s, stem=stem_name)
        self._hide_progress()

    def _on_note_override(self, midi: int) -> None:
        """Apply a root note override to the current phrase and re-render."""
        if self._phrase is None:
            return
        if midi == -1:
            return  # "auto" selected — nothing to do until next re-characterize
        import dataclasses
        from soundmatch.core.phrase import Note
        new_notes = [Note(t=n.t, midi=[midi]) for n in self._phrase.notes]
        self._phrase = dataclasses.replace(self._phrase, notes=new_notes)
        from soundmatch.ui.patch_editor import midi_to_note_name
        log.info("note override: %s (midi=%d)", midi_to_note_name(midi), midi)
        self._on_patch_changed(
            self._patch_editor.instrument_id,
            self._patch_editor.params,
            self._patch_editor.layers,
            self._patch_editor.seed,
        )

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
        self._show_progress("Rendering…")

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
        finally:
            self._hide_progress()

    def _on_sweep_requested(self, axis: str, values: list) -> None:
        """Handle variant sweep request from the grid."""
        if self._target_metrics is None or self._phrase is None:
            self._status_label.setText("No target — characterize first")
            return
        n = len(values)
        log.info("sweep requested: axis=%s values=%s", axis, values)
        self._show_progress(f"Sweeping '{axis}'…", total=n)

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
            for i, r in enumerate(results):
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
                self._progress.setValue(i + 1)
                QApplication.processEvents()

            log.info("sweep done: %d variants on '%s'", len(results), axis)
            self._variant_grid.set_results(results, audio_data=audio_data)
            self._status_label.setText(f"Swept {len(results)} variants on axis '{axis}'")
        except Exception as exc:
            log.error("sweep error: %s", exc, exc_info=True)
            self._status_label.setText(f"Sweep error: {exc}")
        finally:
            self._hide_progress()

    def _on_promote_requested(self, params: dict, layers: list) -> None:
        """Promote a variant's params back to the patch editor."""
        inst_id = self._patch_editor.instrument_id
        seed = self._patch_editor.seed
        self._patch_editor.set_patch(inst_id, params, layers, seed)
        self._status_label.setText("Promoted variant → Patch Editor")

    def _load_stems_from_dir(self, stems_dir: Path) -> None:
        """Load stem .wav files from a directory into the stems panel."""
        import soundfile as sf
        stems: dict = {}
        sr = self._service.sr
        try:
            for wav in sorted(stems_dir.glob("*.wav")):
                audio, file_sr = sf.read(str(wav), dtype="float32", always_2d=False)
                if audio.ndim == 2:
                    audio = audio.mean(axis=1)
                stems[wav.stem] = audio
                sr = file_sr
            if stems:
                log.info("loaded %d stems from %s", len(stems), stems_dir)
                self._stems.set_stems(stems, sr)
            else:
                log.warning("stems dir exists but contains no .wav files: %s", stems_dir)
        except Exception as exc:
            log.error("failed to load stems from %s: %s", stems_dir, exc, exc_info=True)

    def _on_stems_ready(self, stems: object, sr: int) -> None:
        """Save separated stems to disk and record the dir in the project."""
        import soundfile as sf
        stems_dict: dict = stems  # type: ignore[assignment]
        if not stems_dict or self._ref_path is None:
            return
        stems_dir = self._ref_path.parent / f"{self._ref_path.stem}_stems"
        # Already loaded from this directory — don't re-save
        if self._project.stems_dir == stems_dir and stems_dir.is_dir():
            log.debug("stems already on disk at %s, skipping re-save", stems_dir)
            return
        try:
            stems_dir.mkdir(exist_ok=True)
            for name, audio in stems_dict.items():
                out = stems_dir / f"{name}.wav"
                sf.write(str(out), audio, sr)
            self._project.stems_dir = stems_dir
            log.info("stems saved to %s", stems_dir)
            self._status_label.setText(f"Stems saved: {stems_dir.name}/")
        except Exception as exc:
            log.error("failed to save stems: %s", exc, exc_info=True)

    def _on_separate_requested(self) -> None:
        """Handle Separate Stems button: run demucs on the loaded reference."""
        if self._ref_path is None:
            log.warning("separate requested but no reference file is loaded")
            self._status_label.setText("Load a reference file first")
            return
        log.info("separate requested: %s (%.2f–%.2fs)", self._ref_path, self._sel_start_s, self._sel_end_s)
        self._status_label.setText("Separating stems…")
        self._stems.separate(
            str(self._ref_path),
            start_s=self._sel_start_s,
            end_s=self._sel_end_s,
            sr=self._service.sr,
        )

    def _on_suggest_requested(self) -> None:
        """Run coarse param search on a background thread."""
        if self._target_metrics is None or self._phrase is None:
            self._status_label.setText("No target — characterize first")
            return
        if self._search_thread is not None and self._search_thread.isRunning():
            log.debug("search already running")
            return

        log.info("suggest requested: instrument=%s", self._patch_editor.instrument_id)
        # Start in determinate mode (max_iterations default=200) so the bar
        # shows at 0%, not as a solid indeterminate block.
        self._show_progress("Searching…", total=200)

        self._search_worker = _SearchWorker(
            self._target_metrics,
            self._phrase,
            self._patch_editor.instrument_id,
            self._patch_editor.params,
            self._patch_editor.layers,
            self._patch_editor.seed,
        )
        self._search_thread = QThread(self)
        self._search_worker.moveToThread(self._search_thread)
        self._search_thread.started.connect(self._search_worker.run)
        self._search_worker.progress.connect(self._on_search_progress)
        self._search_worker.finished.connect(self._on_search_done)
        self._search_worker.error.connect(self._on_search_error)
        self._search_worker.finished.connect(self._search_thread.quit)
        self._search_worker.error.connect(self._search_thread.quit)
        self._search_thread.finished.connect(self._search_thread.deleteLater)
        self._search_thread.start()

    def _on_search_progress(self, done: int, total: int) -> None:
        if self._progress.maximum() != total:
            self._progress.setRange(0, total)
        self._progress.setValue(done)
        self._status_label.setText(f"Searching… {done}/{total}")

    def _on_search_done(self, result: object) -> None:
        self._hide_progress()
        from soundmatch.core.search import SearchResult
        r: SearchResult = result  # type: ignore[assignment]
        self._patch_editor.set_patch(r.instrument_id, r.best_params, r.best_layers, r.seed)
        log.info("suggest done: agg=%.4f iterations=%d", r.best_score, r.iterations)
        self._status_label.setText(
            f"Suggest: agg={r.best_score:.4f} ({r.iterations} iterations)"
        )

    def _on_search_error(self, msg: str) -> None:
        self._hide_progress()
        log.error("suggest failed: %s", msg)
        self._status_label.setText(f"Search error: {msg}")

    def _on_find_instrument_requested(self) -> None:
        """Open the cross-instrument ranking dialog."""
        if self._target_metrics is None or self._phrase is None:
            self._status_label.setText("No target — characterize first")
            return

        log.info("find instrument requested")
        dialog = InstrumentSearchDialog(
            self._target_metrics,
            self._phrase,
            self._patch_editor.seed,
            sr=self._service.sr,
            parent=self,
        )
        dialog.instrumentChosen.connect(self._on_instrument_found)
        dialog.show()

    def _on_instrument_found(self, instrument_id: str, params: object) -> None:
        """Apply an instrument from the search dialog to the patch editor."""
        layers = self._patch_editor.layers
        seed = self._patch_editor.seed
        log.info("applying found instrument: %s", instrument_id)
        self._patch_editor.set_patch(instrument_id, dict(params), layers, seed)  # type: ignore[arg-type]
        self._status_label.setText(f"Loaded instrument: {instrument_id}")

    def _on_resynthesize(self) -> None:
        """Analyse the selected region and open the Spectral Resynthesis dialog."""
        y, sr = self._reference.audio_data
        if y is None:
            self._status_label.setText("Load a reference file first")
            return

        i0 = max(0, int(self._sel_start_s * sr))
        i1 = min(int(self._sel_end_s * sr), len(y))
        region = y[i0:i1] if i1 > i0 else y

        source_name = self._reference.file_path.stem if self._reference.file_path else "sound"

        from soundmatch.ui.resynth_dialog import ResynthDialog
        dlg = ResynthDialog(region, sr, source_name=source_name, parent=self)
        def _on_resynth_ready(audio: np.ndarray, out_sr: int) -> None:
            self._ab_viewer.set_candidate(audio, out_sr)
            self._status_label.setText("Resynthesis → A/B Viewer")

        dlg.resynthReady.connect(_on_resynth_ready)
        dlg.exec()

    def _on_export_brief(self) -> None:
        """Analyse the selected region and export a synthesis brief + JSON."""
        y, sr = self._reference.audio_data
        if y is None:
            self._status_label.setText("Load a reference file first")
            return

        out_dir = QFileDialog.getExistingDirectory(
            self, "Choose output directory for sound brief", ""
        )
        if not out_dir:
            return

        i0 = max(0, int(self._sel_start_s * sr))
        i1 = min(int(self._sel_end_s * sr), len(y))
        region = y[i0:i1] if i1 > i0 else y

        source_name = self._reference.file_path.stem if self._reference.file_path else "sound"
        chord_midi = (
            self._target_metrics.chord.get("midi", [])
            if self._target_metrics is not None else []
        )

        self._show_progress("Analysing…")
        try:
            from soundmatch.core.extract import (
                ExtractionReport,
                export_brief,
                extract_synthesis_features,
                generate_synthesis_brief,
            )
            from pathlib import Path

            report = extract_synthesis_features(
                region, sr, source_name=source_name, chord_midi=chord_midi,
            )
            json_path, brief_path = export_brief(report, Path(out_dir))
            log.info("exported brief: %s", brief_path)

            brief_text = generate_synthesis_brief(report, include_template=True)
            self._show_brief_preview(brief_text, brief_path)
            self._status_label.setText(f"Brief saved: {brief_path.name}")
        except Exception as exc:
            log.error("export brief failed: %s", exc, exc_info=True)
            self._status_label.setText(f"Export error: {exc}")
        finally:
            self._hide_progress()

    def _show_brief_preview(self, text: str, saved_to=None) -> None:
        """Show a read-only preview of the generated brief."""
        dlg = QDialog(self)
        dlg.setWindowTitle("Sound Synthesis Brief")
        dlg.resize(740, 620)
        layout = QVBoxLayout(dlg)

        if saved_to is not None:
            layout.addWidget(QLabel(f"Saved to: {saved_to}"))

        editor = QPlainTextEdit(dlg)
        editor.setReadOnly(True)
        editor.setPlainText(text)
        editor.setFont(self.font())   # monospace if the app uses one
        layout.addWidget(editor)

        bbox = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        copy_btn = bbox.addButton("Copy to Clipboard", QDialogButtonBox.ButtonRole.ActionRole)
        copy_btn.clicked.connect(
            lambda: QApplication.clipboard().setText(text)
        )
        bbox.rejected.connect(dlg.reject)
        layout.addWidget(bbox)

        dlg.exec()

    def _on_reload_instruments(self) -> None:
        """Re-import forge.instruments.registry so newly added files are visible."""
        try:
            import importlib
            import forge.instruments.registry as reg
            importlib.reload(reg)
            from forge.instruments.registry import REGISTRY
            n = len(REGISTRY)
            log.info("instruments reloaded: %d entries", n)
            self._status_label.setText(f"Instruments reloaded — {n} registered")
        except Exception as exc:
            log.error("reload failed: %s", exc, exc_info=True)
            self._status_label.setText(f"Reload error: {exc}")

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
                # Slice to the selection within stem coordinates
                stem_audio = self._stems.get_stem_audio_for_selection(stem, start_s, end_s)
                if stem_audio is None or len(stem_audio) == 0:
                    stem_audio = y[int(start_s * sr):min(int(end_s * sr), len(y))]
                m = characterize(stem_audio, sr)

            self._target_metrics = m
            self._metrics.set_metrics(m)
            self._scorecard.set_target_metrics(m)
            self._phrase = seed_from_metrics(m, bpm=138.0)

            self._project.start_s = start_s
            self._project.end_s = end_s
            self._project.stem = stem
            self._project.target_metrics = m
            self._project.phrase = self._phrase

            # Show phrase note names in the patch editor
            phrase_midi = list({n for note in self._phrase.notes for n in note.midi})
            self._patch_editor.set_phrase_notes(sorted(phrase_midi))

            log.debug("characterize done: perc=%.1f%% cent=%.0fHz", m.percussive_ratio, m.centroid_hz)
            self._status_label.setText(
                f"Target: perc={m.percussive_ratio:.1f}% cent={m.centroid_hz:.0f}Hz"
            )
        except Exception as exc:
            log.error("characterize error: %s", exc, exc_info=True)
            self._status_label.setText(f"Characterization error: {exc}")

    def _target_y_for_ab(self) -> np.ndarray | None:
        """Get the selected region of the reference audio for the A/B viewer."""
        y, sr = self._reference.audio_data
        if y is None:
            return None
        i0 = int(self._reference._start_s * sr)
        i1 = min(int(self._reference._end_s * sr), len(y))
        return y[i0:i1] if i1 > i0 else y

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
