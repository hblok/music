"""forge.ui.ab_compare — A/B parameter-state compare widget.

``ABCompareWidget`` snapshots the current ``ProjectDoc`` state as "A" or "B"
and lets the user toggle between them without a render stall.  The snapshot
is a full copy of the doc's ``to_dict()`` serialisation; toggling restores
the doc state from the snapshot via a single transaction.

Usage::

    ab = ABCompareWidget(doc, scheduler, parent=w)
    ab.stateChanged.connect(lambda label: print(f"now on {label}"))
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from forge.document.model import ProjectDoc


class ABCompareWidget(QWidget):
    """Two-state parameter snapshot / toggle widget.

    Args:
        doc:       Live ProjectDoc whose state is snapshotted.
        parent:    Optional parent widget.

    Signals:
        stateChanged(str):  Emitted with "A" or "B" after a toggle.
    """

    stateChanged = Signal(str)

    def __init__(
        self,
        doc: "ProjectDoc",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._doc = doc
        self._snap_a: dict | None = None
        self._snap_b: dict | None = None
        self._current: str = "A"  # which snapshot is live

        self._status = QLabel("No snapshot saved")
        self._snap_a_btn = QPushButton("Snap A")
        self._snap_b_btn = QPushButton("Snap B")
        self._toggle_btn = QPushButton("Toggle A/B")
        self._toggle_btn.setEnabled(False)

        self._snap_a_btn.clicked.connect(lambda: self._snap("A"))
        self._snap_b_btn.clicked.connect(lambda: self._snap("B"))
        self._toggle_btn.clicked.connect(self._toggle)

        btn_row = QHBoxLayout()
        for b in (self._snap_a_btn, self._snap_b_btn, self._toggle_btn):
            btn_row.addWidget(b)

        group = QGroupBox("A/B Compare")
        inner = QVBoxLayout(group)
        inner.setContentsMargins(4, 4, 4, 4)
        inner.addLayout(btn_row)
        inner.addWidget(self._status)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(group)

    # ---------------------------------------------------------------- public

    @property
    def current(self) -> str:
        """Which snapshot is currently loaded: "A" or "B" (or "A" if neither)."""
        return self._current

    def snapshot(self, label: str) -> None:
        """Programmatically take a snapshot without a button click."""
        self._snap(label)

    def has_snap(self, label: str) -> bool:
        """Return True if snapshot *label* ("A" or "B") has been saved."""
        return (self._snap_a if label == "A" else self._snap_b) is not None

    # ---------------------------------------------------------------- private

    def _snap(self, label: str) -> None:
        snap = self._doc.to_dict()
        if label == "A":
            self._snap_a = snap
        else:
            self._snap_b = snap
        self._current = label
        self._update_status()
        if self._snap_a is not None and self._snap_b is not None:
            self._toggle_btn.setEnabled(True)

    def _toggle(self) -> None:
        # Switch to the other snapshot
        other = "B" if self._current == "A" else "A"
        snap = self._snap_b if other == "B" else self._snap_a
        if snap is None:
            return
        self._restore(snap, other)

    def _restore(self, snap: dict, label: str) -> None:
        """Restore *snap* into the live doc (direct attribute replacement)."""
        from forge.document.model import ProjectDoc
        from forge.document.transaction import Transaction

        # Build a replacement doc from the snapshot
        restored = ProjectDoc.from_dict(snap)

        # Apply as a single non-undoable state swap (A/B compare is ephemeral)
        self._doc._channels = restored._channels
        self._doc._sections = restored._sections
        self._doc._title = restored._title
        self._doc._bpm = restored._bpm
        self._doc._seed = restored._seed

        # Notify observers so the UI refreshes
        txn = Transaction(f"A/B restore {label}")
        txn.add_change(("ab_restore",), self._current, label)
        self._doc._notify(txn)

        self._current = label
        self._update_status()
        self.stateChanged.emit(label)

    def _update_status(self) -> None:
        has_a = self._snap_a is not None
        has_b = self._snap_b is not None
        parts = []
        if has_a:
            parts.append(f"A saved")
        if has_b:
            parts.append(f"B saved")
        if not parts:
            self._status.setText("No snapshot saved")
        else:
            self._status.setText(f"{', '.join(parts)} — showing {self._current}")
