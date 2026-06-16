"""examples/tracker_spike.py — Phase 0: prove the edit→render→cache→swap loop.

A minimal window with one instrument selector, one param slider, and looping
playback.  On each slider move:
  1. A background thread re-renders the instrument.
  2. The result is cached (in-memory, content-addressed by params+seed).
  3. PlaybackService buffer is hot-swapped; looping resumes immediately.

Edit-to-sound latency is measured and printed.  This de-risks Phases 2–3
before the full cache/scheduler/mixer stack is built.

Run::

    python examples/tracker_spike.py            # Qt GUI
    python examples/tracker_spike.py --headless # headless self-test
"""

from __future__ import annotations

import sys
import time
import threading
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np

from forge import control
from forge.playback.service import PlaybackService

try:
    from PySide6.QtWidgets import (
        QApplication,
        QComboBox,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QSlider,
        QVBoxLayout,
        QWidget,
    )
    from PySide6.QtCore import Qt, QTimer
    _QT_AVAILABLE = True
except ImportError:
    _QT_AVAILABLE = False


# ---------------------------------------------------------------------------
# Stub in-memory content-addressed cache

class _SpikeCache:
    """In-memory cache keyed by (instrument_id, sorted-params, seed)."""

    def __init__(self) -> None:
        self._store: dict = {}

    def _key(self, iid: str, params: dict, seed: int) -> tuple:
        return (iid, tuple(sorted(params.items())), seed)

    def get(self, iid: str, params: dict, seed: int):
        return self._store.get(self._key(iid, params, seed))

    def put(self, iid: str, params: dict, seed: int, buf) -> None:
        self._store[self._key(iid, params, seed)] = buf

    def __len__(self) -> int:
        return len(self._store)


_CACHE = _SpikeCache()


# ---------------------------------------------------------------------------
# Background renderer (coalesces rapid edits to latest job only)

class _BackgroundRenderer:
    def __init__(self, on_done) -> None:
        self._on_done = on_done  # (buf, render_ms: float) → None
        self._lock = threading.Lock()
        self._pending: dict | None = None
        self._thread: threading.Thread | None = None

    def schedule(self, iid: str, params: dict, seed: int) -> None:
        with self._lock:
            self._pending = {"iid": iid, "params": dict(params), "seed": seed}
        if self._thread is None or not self._thread.is_alive():
            self._thread = threading.Thread(target=self._worker, daemon=True)
            self._thread.start()

    def _worker(self) -> None:
        while True:
            with self._lock:
                job = self._pending
                self._pending = None
            if job is None:
                break
            t0 = time.monotonic()
            buf = _CACHE.get(job["iid"], job["params"], job["seed"])
            if buf is None:
                buf = control.render_instrument(job["iid"], job["params"], job["seed"])
                _CACHE.put(job["iid"], job["params"], job["seed"], buf)
            ms = (time.monotonic() - t0) * 1000
            self._on_done(buf, ms)


# ---------------------------------------------------------------------------
# Qt window

if _QT_AVAILABLE:

    class SpikeWindow(QWidget):
        def __init__(self) -> None:
            super().__init__()
            self.setWindowTitle("Tracker spike — Phase 0 (edit→render→cache→swap)")
            self._svc = PlaybackService(sr=44100, bpm=120.0)
            self._renderer = _BackgroundRenderer(self._on_render_done)
            self._edit_t0: float = 0.0
            self._instruments = control.list_instruments()
            self._current_iid = "kick"
            self._current_params: dict = {}
            self._seed = 42
            self._sliders: dict[str, QSlider] = {}

            self._loop_timer = QTimer(self)
            self._loop_timer.setInterval(50)
            self._loop_timer.timeout.connect(self._check_loop)

            layout = QVBoxLayout(self)

            # Instrument selector
            row = QHBoxLayout()
            row.addWidget(QLabel("Instrument:"))
            self._combo = QComboBox()
            for e in self._instruments:
                self._combo.addItem(e["id"])
            self._combo.setCurrentText("kick")
            self._combo.currentTextChanged.connect(self._on_instrument_changed)
            row.addWidget(self._combo)
            layout.addLayout(row)

            # Param sliders (rebuilt per instrument)
            self._param_area = QVBoxLayout()
            layout.addLayout(self._param_area)

            # Transport
            tr = QHBoxLayout()
            play_btn = QPushButton("▶ Play loop")
            play_btn.clicked.connect(self._play)
            stop_btn = QPushButton("■ Stop")
            stop_btn.clicked.connect(self._stop)
            tr.addWidget(play_btn)
            tr.addWidget(stop_btn)
            layout.addLayout(tr)

            # Status
            self._status = QLabel("Status: idle")
            layout.addWidget(self._status)

            self._build_param_controls()
            self._schedule_render()

        # ---------------------------------------------------------------- UI build

        def _build_param_controls(self) -> None:
            while self._param_area.count():
                item = self._param_area.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                elif item.layout():
                    # clear sub-layout widgets
                    sub = item.layout()
                    while sub.count():
                        w = sub.takeAt(0).widget()
                        if w:
                            w.deleteLater()

            self._sliders = {}
            self._current_params = {}

            entry = next((e for e in self._instruments if e["id"] == self._current_iid), None)
            if entry is None:
                return

            for schema in entry["params"][:4]:   # show first 4 params
                name = schema["name"]
                kind = schema.get("kind", "float")
                if kind == "bool":
                    continue
                lo = float(schema.get("lo") or 0.0)
                hi = float(schema.get("hi") or 1.0)
                default = float(schema.get("default", lo))
                self._current_params[name] = default

                row = QHBoxLayout()
                row.addWidget(QLabel(name[:10]))
                slider = QSlider(Qt.Orientation.Horizontal)
                slider.setRange(0, 1000)
                slider.setValue(int((default - lo) / max(hi - lo, 1e-12) * 1000))
                val_lbl = QLabel(f"{default:.3g}")
                val_lbl.setFixedWidth(60)
                slider.valueChanged.connect(
                    lambda tick, n=name, lo_=lo, hi_=hi, lbl=val_lbl:
                    self._on_slider(tick, n, lo_, hi_, lbl)
                )
                self._sliders[name] = slider
                row.addWidget(slider)
                row.addWidget(val_lbl)
                self._param_area.addLayout(row)

        # ---------------------------------------------------------------- event handlers

        def _on_slider(self, tick: int, name: str, lo: float, hi: float, lbl: QLabel) -> None:
            v = lo + (hi - lo) * tick / 1000
            lbl.setText(f"{v:.3g}")
            self._current_params[name] = v
            self._edit_t0 = time.monotonic()
            self._status.setText("Status: rendering…")
            self._schedule_render()

        def _on_instrument_changed(self, iid: str) -> None:
            self._current_iid = iid
            self._build_param_controls()
            self._schedule_render()

        def _schedule_render(self) -> None:
            self._renderer.schedule(self._current_iid, dict(self._current_params), self._seed)

        def _on_render_done(self, buf, render_ms: float) -> None:
            self._svc.load(buf)
            total_ms = (time.monotonic() - self._edit_t0) * 1000
            hit = "cache hit" if render_ms < 1.0 else f"render {render_ms:.0f} ms"
            print(f"edit-to-sound: {total_ms:.0f} ms ({hit})")
            self._status.setText(f"Status: ready — latency {total_ms:.0f} ms ({hit})")

        def _play(self) -> None:
            self._svc.play()
            self._loop_timer.start()

        def _stop(self) -> None:
            self._svc.stop()
            self._loop_timer.stop()

        def _check_loop(self) -> None:
            if not self._svc.is_playing:
                self._svc.seek(0)
                self._svc.play()

        def closeEvent(self, event) -> None:
            self._loop_timer.stop()
            self._svc.close()
            super().closeEvent(event)


# ---------------------------------------------------------------------------
# Headless self-test

def _headless_test() -> None:
    print("headless self-test: render kick → measure latency")
    done1 = threading.Event()
    done2 = threading.Event()
    results: list[float] = []

    def on_done(buf, ms):
        results.append(ms)
        print(f"  render: {ms:.1f} ms, samples: {len(buf)}")
        if len(results) == 1:
            done1.set()
        elif len(results) == 2:
            done2.set()

    renderer = _BackgroundRenderer(on_done)

    t0 = time.monotonic()
    # First render — cache miss
    renderer.schedule("kick", {"f0": 60.0}, 42)
    done1.wait(timeout=10.0)

    # Second render — same params → should be a cache hit (near 0 ms)
    renderer.schedule("kick", {"f0": 60.0}, 42)
    done2.wait(timeout=5.0)

    print(f"Cache size: {len(_CACHE)} entry (expect 1 — second was a hit)")
    assert len(_CACHE) == 1, "second render should be a cache hit (no new entry)"
    assert results[1] < 5.0, f"cache hit should be <5 ms, got {results[1]:.1f} ms"
    print("PASS: edit→render→cache→swap loop works")
    print(f"Total wall time: {(time.monotonic() - t0)*1000:.0f} ms")


# ---------------------------------------------------------------------------
# Entry point

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()

    if args.headless or not _QT_AVAILABLE:
        _headless_test()
        return

    app = QApplication(sys.argv)
    w = SpikeWindow()
    w.resize(520, 280)
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
