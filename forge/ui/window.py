"""forge.ui.window — main application window.

The window has:
  - Menu bar (File, Transport)
  - Transport widget (play/pause/stop/seek)
  - "Render" button that calls control.render_instrument with a test patch
  - Status bar showing playback position

The engine is accessed only through forge.control — this module never imports
forge.core, forge.instruments, or any DSP code directly.
"""

from __future__ import annotations

import threading

from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from forge.playback.service import PlaybackService
from forge.ui.transport import TransportWidget


class _RenderWorker(QObject):
    """Renders audio in a background thread then signals done."""

    finished = Signal(object)   # AudioBuffer
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
    """Forge main window skeleton.

    Args:
        service: PlaybackService (injected so it can be shared / mocked in tests).
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

        self.setWindowTitle("Forge — Modular Music")
        self.resize(640, 200)

        # --- central widget ---
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self._transport = TransportWidget(service, parent=central)
        self._transport.positionChanged.connect(self._on_position)

        self._render_btn = QPushButton("Render (kick test)")
        self._render_btn.clicked.connect(self._on_render)

        self._progress = QProgressBar()
        self._progress.setRange(0, 0)   # indeterminate
        self._progress.setVisible(False)

        layout.addWidget(self._transport)
        layout.addWidget(self._render_btn)
        layout.addWidget(self._progress)

        # --- menu bar ---
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction("&Open project…", self._on_open)
        file_menu.addAction("&Save project…", self._on_save)
        file_menu.addSeparator()
        file_menu.addAction("&Quit", QApplication.quit)

        self._current_project: dict | None = None

        transport_menu = self.menuBar().addMenu("&Transport")
        transport_menu.addAction("&Play", service.play)
        transport_menu.addAction("P&ause", service.pause)
        transport_menu.addAction("&Stop", service.stop)

        # --- status bar ---
        self._status = QStatusBar()
        self._status_label = QLabel("Ready")
        self._status.addWidget(self._status_label)
        self.setStatusBar(self._status)

    # ------------------------------------------------------------------
    # Slots

    def _on_position(self, pos_bars: float) -> None:
        self._status_label.setText(f"Position: {self._service.bar_beat_string}")

    def _on_render(self) -> None:
        if self._render_thread is not None and self._render_thread.isRunning():
            return

        self._render_btn.setEnabled(False)
        self._progress.setVisible(True)
        self._status_label.setText("Rendering…")

        def do_render():
            from forge import control
            return control.render_instrument("kick", {"f0": 55.0, "duration": 0.3}, seed=0)

        self._render_thread = QThread(self)
        self._worker = _RenderWorker(do_render)
        self._worker.moveToThread(self._render_thread)
        self._render_thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_render_done)
        self._worker.error.connect(self._on_render_error)
        self._render_thread.start()

    def _on_render_done(self, buf) -> None:
        self._service.load(buf)
        self._transport.set_total_bars(4.0)
        self._render_btn.setEnabled(True)
        self._progress.setVisible(False)
        self._status_label.setText("Render complete — press Play")
        self._render_thread.quit()

    def _on_render_error(self, msg: str) -> None:
        self._render_btn.setEnabled(True)
        self._progress.setVisible(False)
        self._status_label.setText(f"Render error: {msg}")
        self._render_thread.quit()

    def _on_open(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Project", "", "Forge Projects (*.json)"
        )
        if not path:
            return
        try:
            from forge import control
            self._current_project = control.load_project(path)
            self._status_label.setText(f"Opened: {path}")
        except Exception as e:  # noqa: BLE001
            self._status_label.setText(f"Open error: {e}")

    def _on_save(self) -> None:
        if self._current_project is None:
            self._status_label.setText("No project loaded — render something first")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Project", "", "Forge Projects (*.json)"
        )
        if not path:
            return
        try:
            from forge import control
            control.save_project(self._current_project, path)
            self._status_label.setText(f"Saved: {path}")
        except Exception as e:  # noqa: BLE001
            self._status_label.setText(f"Save error: {e}")
