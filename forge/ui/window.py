"""forge.ui.window — main application window (Plan 3 tracker UI).

The window shows the full tracker interface:
  - Transport bar at the top
  - Step-pattern timeline (bird's-eye arrangement view)
  - Horizontal splitter: Sections panel | TrackerEditor rows | MixerWidget
  - Bottom panel: WorkshopPanel (for selected channel) + ABCompareWidget

The engine is accessed only through forge.control — this module never imports
forge.core, forge.instruments, or any DSP code directly.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal, QObject, QTimer
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QProgressBar,
    QPushButton,
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
        self._selected_channel: int = 0
        self._active_section: int | None = None
        self._tracker_editors: list = []
        self._workshop: QWidget | None = None
        self._autosave = None

        self.setWindowTitle("Forge — Tracker")
        self.resize(1200, 750)

        # --- document + render backend ---
        from forge.playback.cache import ContentAddressedCache
        from forge.playback.scheduler import RenderScheduler
        self._cache = ContentAddressedCache(cache_dir=None)
        self._scheduler = RenderScheduler(self._cache)

        self._doc = _make_default_doc()
        self._doc.subscribe(self._on_doc_channel_changed)

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

        # Timeline (bird's-eye step pattern view)
        from forge.ui.timeline import TimelineWidget
        self._timeline = TimelineWidget(self._doc)
        self._timeline.sectionClicked.connect(self._on_timeline_section_clicked)
        root.addWidget(self._timeline)

        # Main horizontal splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter = splitter

        # Left: arrangement / sections view
        from forge.ui.arrangement import ArrangementView
        self._arrangement = ArrangementView(self._doc)
        self._arrangement.sectionSelected.connect(self._on_section_selected)
        self._arrangement.setMinimumWidth(160)
        splitter.addWidget(self._arrangement)
        splitter.setStretchFactor(0, 0)

        # Centre: channel toolbar + scrollable tracker rows
        tracker_panel = QWidget()
        tracker_vbox = QVBoxLayout(tracker_panel)
        tracker_vbox.setContentsMargins(0, 0, 0, 0)
        tracker_vbox.setSpacing(2)

        # Channel management toolbar
        ch_bar = QHBoxLayout()
        ch_bar.setContentsMargins(2, 2, 2, 2)
        add_ch_btn = QPushButton("+ Channel")
        add_ch_btn.setFixedHeight(24)
        add_ch_btn.clicked.connect(self._on_add_channel)
        rem_ch_btn = QPushButton("− Channel")
        rem_ch_btn.setFixedHeight(24)
        rem_ch_btn.clicked.connect(self._on_remove_channel)
        ch_bar.addWidget(add_ch_btn)
        ch_bar.addWidget(rem_ch_btn)
        ch_bar.addStretch()
        tracker_vbox.addLayout(ch_bar)

        self._tracker_scroll = QScrollArea()
        self._tracker_scroll.setWidgetResizable(True)
        self._tracker_container = QWidget()
        self._tracker_layout = QVBoxLayout(self._tracker_container)
        self._tracker_layout.setSpacing(2)
        self._tracker_layout.setContentsMargins(2, 2, 2, 2)
        self._tracker_layout.addStretch()
        self._tracker_scroll.setWidget(self._tracker_container)
        tracker_vbox.addWidget(self._tracker_scroll, stretch=1)

        splitter.addWidget(tracker_panel)
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

        # --- global keyboard shortcuts ---
        QShortcut(QKeySequence("Ctrl+Z"), self).activated.connect(self._doc.undo)
        QShortcut(QKeySequence("Ctrl+Y"), self).activated.connect(self._doc.redo)
        QShortcut(QKeySequence("Ctrl+Shift+Z"), self).activated.connect(self._doc.redo)

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

        # Unsubscribe old editors from doc before deleting them
        while self._tracker_layout.count() > 1:
            item = self._tracker_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._tracker_editors = []
        for idx, ch in enumerate(self._doc.channels):
            if not isinstance(ch, PatternChannel):
                continue
            editor = TrackerEditor(idx, self._doc, parent=self._tracker_container)
            editor.channelChanged.connect(self._on_channel_changed)
            editor.cursorMoved.connect(lambda _step, i=idx: self._select_channel(i))
            if self._active_section is not None:
                editor.set_section(self._active_section)
            self._tracker_layout.insertWidget(
                self._tracker_layout.count() - 1, editor
            )
            self._tracker_editors.append(editor)

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

    def _set_active_section(self, section_idx: int | None) -> None:
        """Switch all TrackerEditors to show/edit a specific section's pattern."""
        self._active_section = section_idx
        for editor in self._tracker_editors:
            editor.set_section(section_idx)
        self._timeline.set_active_section(section_idx)

    def _set_doc(self, doc) -> None:
        """Swap in a new ProjectDoc and rebuild all dependent widgets."""
        self._stop_autosave()
        # Unsubscribe from old doc
        self._doc.unsubscribe(self._on_doc_channel_changed)

        self._selected_channel = 0
        self._active_section = None
        self._tracker_editors = []
        self._doc = doc
        doc.subscribe(self._on_doc_channel_changed)

        # Update global Ctrl+Z / Ctrl+Y shortcuts to the new doc
        # (shortcuts are already bound to lambda; replace with new doc reference)
        for sc in self.findChildren(QShortcut):
            sc.deleteLater()
        QShortcut(QKeySequence("Ctrl+Z"), self).activated.connect(doc.undo)
        QShortcut(QKeySequence("Ctrl+Y"), self).activated.connect(doc.redo)
        QShortcut(QKeySequence("Ctrl+Shift+Z"), self).activated.connect(doc.redo)

        # Rebuild arrangement (it holds a doc reference)
        from forge.ui.arrangement import ArrangementView
        old_arr = self._arrangement
        new_arr = ArrangementView(doc)
        new_arr.sectionSelected.connect(self._on_section_selected)
        new_arr.setMinimumWidth(160)
        idx = self._splitter.indexOf(old_arr)
        self._splitter.replaceWidget(idx, new_arr)
        old_arr.deleteLater()
        self._arrangement = new_arr

        # Rebuild A/B compare
        from forge.ui.ab_compare import ABCompareWidget
        old_ab = self._ab_compare
        new_ab = ABCompareWidget(doc)
        layout = old_ab.parent().layout() if old_ab.parent() else None
        if layout:
            layout.replaceWidget(old_ab, new_ab)
        old_ab.deleteLater()
        self._ab_compare = new_ab

        # Swap timeline doc
        self._timeline.set_doc(doc)

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
    # Doc change observer (channel add/remove)

    def _on_doc_channel_changed(self, txn) -> None:
        """Rebuild channel rows and mixer when channels are added or removed."""
        if any(c.path[0] == "channels" for c in txn.changes):
            self._rebuild_tracker_rows()
            self._rebuild_mixer_strips()
            self._update_workshop()

    # ------------------------------------------------------------------
    # Channel management

    def _on_add_channel(self) -> None:
        from PySide6.QtWidgets import QInputDialog
        from forge import control
        instruments = [e["id"] for e in control.list_instruments()]
        iid, ok = QInputDialog.getItem(
            self, "Add Channel", "Choose instrument:", instruments, 0, False
        )
        if ok and iid:
            from forge.document.channels import PatternChannel
            self._doc.add_channel(PatternChannel(iid))

    def _on_remove_channel(self) -> None:
        from forge.document.channels import PatternChannel
        pat_channels = [
            (i, ch) for i, ch in enumerate(self._doc.channels)
            if isinstance(ch, PatternChannel)
        ]
        if not pat_channels:
            return
        sel = min(self._selected_channel, len(pat_channels) - 1)
        real_idx = pat_channels[sel][0]
        self._doc.remove_channel(real_idx)
        self._selected_channel = max(0, sel - 1)

    # ------------------------------------------------------------------
    # Slots

    def _on_position(self, pos_bars: float) -> None:
        self._status_label.setText(f"Position: {self._service.bar_beat_string}")

    def _on_section_selected(self, start_bar: int, length_bars: int) -> None:
        self._transport.set_loop_range(start_bar, start_bar + length_bars)
        # Derive section index from the arrangement view's current row
        sec_idx = self._arrangement.selected_row
        if sec_idx >= 0:
            self._set_active_section(sec_idx)

    def _on_timeline_section_clicked(self, section_idx: int) -> None:
        """Timeline click: select section in both editors and arrangement list."""
        self._set_active_section(section_idx)
        self._arrangement._list.setCurrentRow(section_idx)

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
            QTimer.singleShot(0, lambda: self._status_label.setText("Render ready"))

        self._scheduler.get_or_schedule(key, render_fn, on_done)

    def _on_audition_ready(self, channel_idx: int, buf) -> None:
        """Load an auditioned buffer into the playback service."""
        from forge.core.buffer import AudioBuffer
        if isinstance(buf, AudioBuffer):
            self._service.load(buf)
        else:
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
