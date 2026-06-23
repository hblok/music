"""soundmatch.ui.instrument_search_dialog — streaming cross-instrument ranking UI.

Opens non-modally.  As each instrument is evaluated on the worker thread
results stream in and the table re-sorts itself (best score first).
The user can apply any result at any time — the search keeps running.
"""

from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger(__name__)

from PySide6.QtCore import QObject, QThread, Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from soundmatch.core.search import InstrumentRanking, instrument_search


class _InstrumentSearchWorker(QObject):
    """Runs instrument_search on a background thread, streaming results."""

    result   = Signal(object)   # InstrumentRanking
    progress = Signal(int, int) # (done, total)
    finished = Signal()
    error    = Signal(str)

    def __init__(
        self,
        target: object,
        phrase: object,
        seed: int,
        max_per_instrument: int,
        sr: int,
    ) -> None:
        super().__init__()
        self._target = target
        self._phrase = phrase
        self._seed = seed
        self._max_per = max_per_instrument
        self._sr = sr

    def run(self) -> None:
        try:
            instrument_search(
                self._target,
                self._phrase,
                self._seed,
                max_per_instrument=self._max_per,
                sr=self._sr,
                on_result=lambda r: self.result.emit(r),
                on_progress=lambda done, total: self.progress.emit(done, total),
            )
            self.finished.emit()
        except Exception as exc:
            log.error("instrument search worker error: %s", exc, exc_info=True)
            self.error.emit(str(exc))


class InstrumentSearchDialog(QDialog):
    """Non-modal dialog that streams cross-instrument search results.

    Signals:
        instrumentChosen(instrument_id, params):
            Emitted when the user clicks "Use Selected" on a result row.
    """

    instrumentChosen = Signal(str, object)  # (instrument_id, params dict)

    # Table column indices
    _COL_RANK   = 0
    _COL_SCORE  = 1
    _COL_NAME   = 2
    _COL_FAMILY = 3

    def __init__(
        self,
        target: object,
        phrase: object,
        seed: int,
        sr: int = 44100,
        max_per_instrument: int = 20,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Find Best Instrument")
        self.setWindowFlags(
            self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint
        )
        self.resize(560, 500)
        self.setObjectName("instrument-search-dialog")

        self._results: list[InstrumentRanking] = []   # sorted after each update

        layout = QVBoxLayout(self)

        # ── Status + progress ─────────────────────────────────────────
        self._status = QLabel("Evaluating instruments…")
        self._status.setObjectName("search-status")
        layout.addWidget(self._status)

        self._progress = QProgressBar()
        self._progress.setRange(0, 1)
        self._progress.setValue(0)
        layout.addWidget(self._progress)

        # ── Results table ─────────────────────────────────────────────
        self._table = QTableWidget(0, 4)
        self._table.setObjectName("results-table")
        self._table.setHorizontalHeaderLabels(["#", "Score", "Instrument", "Family"])
        self._table.horizontalHeader().setSectionResizeMode(
            self._COL_NAME, QHeaderView.ResizeMode.Stretch
        )
        self._table.horizontalHeader().setSectionResizeMode(
            self._COL_FAMILY, QHeaderView.ResizeMode.Stretch
        )
        self._table.setColumnWidth(self._COL_RANK, 36)
        self._table.setColumnWidth(self._COL_SCORE, 80)
        self._table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.setSortingEnabled(False)  # we sort manually
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
        self._table.itemDoubleClicked.connect(lambda _: self._on_use())
        layout.addWidget(self._table)

        # ── Buttons ───────────────────────────────────────────────────
        btn_row = QHBoxLayout()

        self._use_btn = QPushButton("Use Selected")
        self._use_btn.setObjectName("use-btn")
        self._use_btn.setEnabled(False)
        self._use_btn.setToolTip("Load the selected instrument into the Patch Editor")
        self._use_btn.clicked.connect(self._on_use)
        btn_row.addWidget(self._use_btn)

        btn_row.addStretch()

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setObjectName("cancel-btn")
        self._cancel_btn.clicked.connect(self._on_cancel)
        btn_row.addWidget(self._cancel_btn)

        layout.addLayout(btn_row)

        # ── Worker + thread ───────────────────────────────────────────
        self._worker = _InstrumentSearchWorker(
            target, phrase, seed, max_per_instrument, sr
        )
        self._thread = QThread(self)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.result.connect(self._on_result)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    # ── Slots (from worker) ───────────────────────────────────────────

    def _on_result(self, ranking: InstrumentRanking) -> None:
        self._results.append(ranking)
        self._results.sort(key=lambda r: r.score)
        self._rebuild_table()

    def _on_progress(self, done: int, total: int) -> None:
        self._progress.setRange(0, total)
        self._progress.setValue(done)
        best = self._results[0] if self._results else None
        if best and done < total:
            self._status.setText(
                f"Searching… {done}/{total}  "
                f"(best so far: {best.instrument_id} = {best.score:.4f})"
            )
        else:
            self._status.setText(f"Searching… {done}/{total}")

    def _on_finished(self) -> None:
        n = len(self._results)
        best = self._results[0] if self._results else None
        if best:
            self._status.setText(
                f"Done — {n} instruments ranked.  "
                f"Best: {best.instrument_id} ({best.family})  score={best.score:.4f}"
            )
        else:
            self._status.setText("Done — no results.")
        self._cancel_btn.setText("Close")

    def _on_error(self, msg: str) -> None:
        self._status.setText(f"Error: {msg}")
        self._cancel_btn.setText("Close")

    # ── Slots (from UI) ───────────────────────────────────────────────

    def _on_selection_changed(self) -> None:
        self._use_btn.setEnabled(bool(self._table.selectedItems()))

    def _on_use(self) -> None:
        row = self._table.currentRow()
        if row < 0 or row >= len(self._results):
            return
        ranking = self._results[row]
        log.info("instrument chosen: %s score=%.4f", ranking.instrument_id, ranking.score)
        self.instrumentChosen.emit(ranking.instrument_id, ranking.params)
        self._status.setText(
            f"Applied: {ranking.instrument_id}  score={ranking.score:.4f}"
        )

    def _on_cancel(self) -> None:
        if self._thread.isRunning():
            self._thread.requestInterruption()
            self._thread.quit()
            self._thread.wait(500)
        self.reject()

    # ── Private ───────────────────────────────────────────────────────

    def _rebuild_table(self) -> None:
        self._table.setRowCount(len(self._results))
        for row, r in enumerate(self._results):
            rank_item = QTableWidgetItem(str(row + 1))
            rank_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )

            score_item = QTableWidgetItem(f"{r.score:.4f}")
            score_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )

            name_item  = QTableWidgetItem(r.instrument_id)
            family_item = QTableWidgetItem(r.family)

            self._table.setItem(row, self._COL_RANK,   rank_item)
            self._table.setItem(row, self._COL_SCORE,  score_item)
            self._table.setItem(row, self._COL_NAME,   name_item)
            self._table.setItem(row, self._COL_FAMILY, family_item)

    def closeEvent(self, event) -> None:
        if self._thread.isRunning():
            self._thread.requestInterruption()
            self._thread.quit()
            self._thread.wait(500)
        super().closeEvent(event)
