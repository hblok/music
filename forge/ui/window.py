"""forge.ui.window — main application window (Plan 3 tracker UI).

The window shows the full tracker interface:
  - Transport bar at the top
  - Horizontal splitter: ArrangementView | TrackerEditor rows | MixerWidget
  - Bottom panel: WorkshopPanel (for selected channel) + ABCompareWidget

The engine is accessed only through forge.control — this module never imports
forge.core, forge.instruments, or any DSP code directly.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal, QObject, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QProgressBar,
    QScrollArea,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from forge.playback.service import PlaybackService
from forge.ui.transport import TransportWidget


class _RenderWorker(QObject):
    """Renders audio in a background thread then signals done."""

    finished = Signal(object)
    error = Signal(str)

    def __init__(self, fn, parent=None):
        super().__init__(parent)
        self._fn = fn

    def run(self):
        try:
            buf = self._fn()
            self.finished.emit(buf)
        except Exception as exc:  # noqa: BLE001
            self.error.emit(str(exc))


class MainWindow(QMainWindow):
    """Forge tracker main window.

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
        self._render_thread: QThread | None = None
        self._current_project: dict | None = None
        self._selected_channel: int = 0
        self._workshop: QWidget | None = None
        self._autosave = None

        self.setWindowTitle("Forge — Tracker")
        self.resize(1200, 700)

        # --- document + render backend ---
        from forge.playback.cache import ContentAddressedCache
        from forge.playback.scheduler import RenderScheduler
        self._cache = ContentAddressedCache(cache_dir=None)
        self._scheduler = RenderScheduler(self._cache)

        self._doc = _make_default_doc()

        # --- menu ---
        self._build_menu(service)

        # --- central widget ---
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(4)

        # Transport
        self._transport = TransportWidget(service, parent=central)
        self._transport.positionChanged.connect(self._on_position)
        self._transport.set_scheduler(self._scheduler)
        root.addWidget(self._transport)

        # Main horizontal splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: arrangement view
        from forge.ui.arrangement import ArrangementView
        self._arrangement = ArrangementView(self._doc)
        self._arrangement.sectionSelected.connect(self._on_section_selected)
        self._arrangement.setMinimumWidth(160)
        splitter.addWidget(self._arrangement)
        splitter.setStretchFactor(0, 0)

        # Centre: scrollable tracker rows
        self._tracker_scroll = QScrollArea()
        self._tracker_scroll.setWidgetResizable(True)
        self._tracker_container = QWidget()
        self._tracker_layout = QVBoxLayout(self._tracker_container)
        self._tracker_layout.setSpacing(2)
        self._tracker_layout.setContentsMargins(2, 2, 2, 2)
        self._tracker_layout.addStretch()
        self._tracker_scroll.setWidget(self._tracker_container)
        splitter.addWidget(self._tracker_scroll)
        splitter.setStretchFactor(1, 1)

        # Right: mixer
        from forge.ui.mixer import MixerWidget
        self._mixer = MixerWidget([], parent=splitter)
        self._mixer.setMinimumWidth(160)
        splitter.addWidget(self._mixer)
        splitter.setStretchFactor(2, 0)

        root.addWidget(splitter, stretch=1)

        # Bottom panel: workshop area + A/B compare
        bottom = QHBoxLayout()
        bottom.setContentsMargins(0, 0, 0, 0)

        self._workshop_area = QWidget()
        self._workshop_area_layout = QVBoxLayout(self._workshop_area)
        self._workshop_area_layout.setContentsMargins(0, 0, 0, 0)
        bottom.addWidget(self._workshop_area, stretch=1)

        from forge.ui.ab_compare import ABCompareWidget
        self._ab_compare = ABCompareWidget(self._doc)
        bottom.addWidget(self._ab_compare, stretch=0)

        root.addLayout(bottom)

        # Progress bar (shown during WAV export)
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setVisible(False)
        root.addWidget(self._progress)

        # --- status bar ---
        self._status = QStatusBar()
        self._status_label = QLabel("Ready")
        self._status.addWidget(self._status_label)
        self.setStatusBar(self._status)

        # --- initial populate ---
        self._rebuild_tracker_rows()
        self._rebuild_mixer_strips()
        self._update_workshop()
        self._start_autosave()

    # ------------------------------------------------------------------
    # Private helpers

    def _build_menu(self, service: PlaybackService) -> None:
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction("&New project", self._on_new)
        file_menu.addAction("&Open Tracker project…", self._on_open_doc)
        file_menu.addAction("&Save Tracker project…", self._on_save_doc)
        file_menu.addSeparator()
        file_menu.addAction("Open &Engine project…", self._on_open)
        file_menu.addAction("Save Engine project…", self._on_save)
        file_menu.addSeparator()
        file_menu.addAction("&Export WAV…", self._on_export_wav)
        file_menu.addSeparator()
        file_menu.addAction("&Quit", QApplication.quit)

        transport_menu = self.menuBar().addMenu("&Transport")
        transport_menu.addAction("&Play", service.play)
        transport_menu.addAction("P&ause", service.pause)
        transport_menu.addAction("&Stop", service.stop)

    def _rebuild_tracker_rows(self) -> None:
        """Recreate TrackerEditor widgets to match current doc PatternChannels."""
        from forge.document.channels import PatternChannel
        from forge.ui.pattern_editor import TrackerEditor

        # Remove old editors (all items except the trailing stretch)
        while self._tracker_layout.count() > 1:
            item = self._tracker_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for idx, ch in enumerate(self._doc.channels):
            if not isinstance(ch, PatternChannel):
                continue
            editor = TrackerEditor(idx, self._doc, parent=self._tracker_container)
            editor.channelChanged.connect(self._on_channel_changed)
            # clicking inside an editor selects that channel for the workshop
            editor.cursorMoved.connect(lambda _step, i=idx: self._select_channel(i))
            self._tracker_layout.insertWidget(
                self._tracker_layout.count() - 1, editor
            )

    def _rebuild_mixer_strips(self) -> None:
        """Sync MixerWidget strips with current doc PatternChannels."""
        from forge.document.channels import PatternChannel
        for name in list(self._mixer._strips.keys()):
            self._mixer.remove_strip(name)
        for ch in self._doc.channels:
            if isinstance(ch, PatternChannel):
                self._mixer.add_strip(ch.instrument_id)

    def _update_workshop(self) -> None:
        """Replace the WorkshopPanel with one for the selected channel."""
        from forge.document.channels import PatternChannel

        # Clear the workshop area
        while self._workshop_area_layout.count():
            item = self._workshop_area_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._workshop = None

        pat_channels = [
            (i, ch) for i, ch in enumerate(self._doc.channels)
            if isinstance(ch, PatternChannel)
        ]
        if not pat_channels:
            return
        idx = min(self._selected_channel, len(pat_channels) - 1)
        real_idx = pat_channels[idx][0]

        from forge.ui.instrument_panel import WorkshopPanel
        workshop = WorkshopPanel(
            real_idx,
            self._doc,
            self._scheduler,
            bpm=self._doc.bpm,
            length_bars=4,
        )
        workshop.auditionReady.connect(self._on_audition_ready)
        self._workshop_area_layout.addWidget(workshop)
        self._workshop = workshop

    def _select_channel(self, idx: int) -> None:
        if idx != self._selected_channel:
            self._selected_channel = idx
            self._update_workshop()

    def _set_doc(self, doc) -> None:
        """Swap in a new ProjectDoc and rebuild all dependent widgets."""
        self._stop_autosave()
        self._selected_channel = 0
        self._doc = doc

        # Rebuild arrangement (it holds a doc reference)
        from forge.ui.arrangement import ArrangementView
        old = self._arrangement
        new_arr = ArrangementView(doc)
        new_arr.sectionSelected.connect(self._on_section_selected)
        new_arr.setMinimumWidth(160)
        splitter = old.parent()
        idx = splitter.indexOf(old)
        splitter.replaceWidget(idx, new_arr)
        old.deleteLater()
        self._arrangement = new_arr

        # Rebuild A/B compare
        from forge.ui.ab_compare import ABCompareWidget
        old_ab = self._ab_compare
        new_ab = ABCompareWidget(doc)
        bottom_layout = old_ab.parent().layout() if old_ab.parent() else None
        if bottom_layout:
            bottom_layout.replaceWidget(old_ab, new_ab)
        old_ab.deleteLater()
        self._ab_compare = new_ab

        self._rebuild_tracker_rows()
        self._rebuild_mixer_strips()
        self._update_workshop()
        self._start_autosave()

    def _start_autosave(self) -> None:
        import tempfile
        from forge.document.autosave import AutoSave
        path = Path(tempfile.gettempdir()) / "forge_autosave.json"
        self._autosave = AutoSave(self._doc, path, interval=10)

    def _stop_autosave(self) -> None:
        if self._autosave is not None:
            self._autosave.stop()
            self._autosave = None

    # ------------------------------------------------------------------
    # Slots

    def _on_position(self, pos_bars: float) -> None:
        self._status_label.setText(f"Position: {self._service.bar_beat_string}")

    def _on_section_selected(self, start_bar: int, length_bars: int) -> None:
        self._transport.set_loop_range(start_bar, start_bar + length_bars)

    def _on_channel_changed(self, channel_idx: int) -> None:
        """Schedule a background re-render when a channel is edited."""
        doc = self._doc
        key = doc.channel_cache_key(channel_idx)
        ch = doc.channel(channel_idx)
        bpm = doc.bpm

        def render_fn():
            from forge import control
            return control.render_channel(ch, bpm, 4)

        def on_done(k, buf):
            arr = buf.data.astype("float32")
            QTimer.singleShot(0, lambda: self._status_label.setText("Render ready"))

        self._scheduler.get_or_schedule(key, render_fn, on_done)

    def _on_audition_ready(self, channel_idx: int, buf) -> None:
        """Load an auditioned buffer into the playback service."""
        from forge.core.buffer import AudioBuffer
        if isinstance(buf, AudioBuffer):
            self._service.load(buf)
        else:
            # numpy array from WorkshopPanel
            ab = AudioBuffer(len(buf), self._service.sr if hasattr(self._service, "sr") else 44100)
            ab._data = buf
            self._service.load(ab)
        self._transport.set_total_bars(4.0)

    def _on_new(self) -> None:
        self._set_doc(_make_default_doc())
        self._status_label.setText("New project")

    def _on_open_doc(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Tracker Project", "", "Tracker Projects (*.json)"
        )
        if not path:
            return
        try:
            from forge.spec.serialize import load_project_doc
            self._set_doc(load_project_doc(path))
            self._status_label.setText(f"Loaded: {path}")
        except Exception as e:  # noqa: BLE001
            self._status_label.setText(f"Load error: {e}")

    def _on_save_doc(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Tracker Project", "", "Tracker Projects (*.json)"
        )
        if not path:
            return
        try:
            from forge.spec.serialize import save_project_doc
            save_project_doc(self._doc, path)
            self._status_label.setText(f"Saved: {path}")
        except Exception as e:  # noqa: BLE001
            self._status_label.setText(f"Save error: {e}")

    def _on_export_wav(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export WAV", "", "WAV files (*.wav)"
        )
        if not path:
            return
        self._progress.setVisible(True)
        self._status_label.setText("Exporting WAV…")

        doc = self._doc

        def do_export():
            from forge import control
            return control.export_wav_from_doc(doc, path)

        self._render_thread = QThread(self)
        self._worker = _RenderWorker(do_export)
        self._worker.moveToThread(self._render_thread)
        self._render_thread.started.connect(self._worker.run)
        self._worker.finished.connect(lambda _: self._on_export_done(path))
        self._worker.error.connect(self._on_render_error)
        self._render_thread.start()

    def _on_export_done(self, path: str) -> None:
        self._progress.setVisible(False)
        self._status_label.setText(f"Exported: {path}")
        if self._render_thread:
            self._render_thread.quit()

    def _on_render_error(self, msg: str) -> None:
        self._progress.setVisible(False)
        self._status_label.setText(f"Error: {msg}")
        if self._render_thread:
            self._render_thread.quit()

    # --- Legacy engine project support ---
    def _on_open(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Engine Project", "", "Forge Projects (*.json)"
        )
        if not path:
            return
        try:
            from forge import control
            self._current_project = control.load_project(path)
            self._status_label.setText(f"Opened engine project: {path}")
        except Exception as e:  # noqa: BLE001
            self._status_label.setText(f"Open error: {e}")

    def _on_save(self) -> None:
        if self._current_project is None:
            self._status_label.setText("No engine project loaded")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Engine Project", "", "Forge Projects (*.json)"
        )
        if not path:
            return
        try:
            from forge import control
            control.save_project(self._current_project, path)
            self._status_label.setText(f"Saved: {path}")
        except Exception as e:  # noqa: BLE001
            self._status_label.setText(f"Save error: {e}")


def _make_default_doc():
    """Return a new ProjectDoc with starter channels."""
    from forge.document.channels import PatternChannel
    from forge.document.model import ProjectDoc
    doc = ProjectDoc(title="Untitled", bpm=138.0, seed=0)
    kick = PatternChannel("kick")
    kick.steps[0].on = True
    kick.steps[4].on = True
    kick.steps[8].on = True
    kick.steps[12].on = True
    doc.add_channel(kick)
    hat = PatternChannel("hat")
    for i in range(0, 16, 2):
        hat.steps[i].on = True
    doc.add_channel(hat)
    doc.add_channel(PatternChannel("bass"))
    doc.add_section("intro", 8)
    doc.add_section("drop", 16)
    return doc
