"""forge.ui.arrangement — section order list and per-channel lane layout.

ArrangementView shows the project's sections as a vertical list of named bar
ranges.  Buttons allow adding, removing, renaming, reordering, and duplicating
sections.  All mutations go through the ``ProjectDoc`` transactional API so
they are undoable.

A section can be "selected" for section-loop playback (the transport highlights
it; the mixer plays only its bar range on repeat).

Usage::

    view = ArrangementView(doc, parent=w)
    view.sectionSelected.connect(on_section_selected)   # (start_bar, length_bars)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from forge.document.model import ProjectDoc


# ---------------------------------------------------------------------------
# Section item display

def _section_label(sec: dict) -> str:
    return f"{sec['name']}  ({sec['length_bars']} bars)"


# ---------------------------------------------------------------------------
# ArrangementView

class ArrangementView(QWidget):
    """Order/section list with add/remove/rename/reorder/duplicate.

    Args:
        doc:    Live ProjectDoc.
        parent: Optional parent widget.

    Signals:
        sectionSelected(int, int):  Emitted when the user clicks a section.
                                    Args: (start_bar, length_bars).
    """

    sectionSelected = Signal(int, int)  # start_bar, length_bars

    def __init__(
        self,
        doc: "ProjectDoc",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._doc = doc
        self._applying = False

        # --- list widget ---
        self._list = QListWidget()
        self._list.currentRowChanged.connect(self._on_row_changed)

        # --- buttons ---
        add_btn = QPushButton("+ Add")
        add_btn.setFixedWidth(56)
        add_btn.clicked.connect(self._on_add)

        remove_btn = QPushButton("✕")
        remove_btn.setFixedWidth(32)
        remove_btn.clicked.connect(self._on_remove)

        rename_btn = QPushButton("✎")
        rename_btn.setFixedWidth(32)
        rename_btn.clicked.connect(self._on_rename)

        up_btn = QPushButton("▲")
        up_btn.setFixedWidth(32)
        up_btn.clicked.connect(self._on_move_up)

        down_btn = QPushButton("▼")
        down_btn.setFixedWidth(32)
        down_btn.clicked.connect(self._on_move_down)

        dup_btn = QPushButton("⎘")
        dup_btn.setFixedWidth(32)
        dup_btn.setToolTip("Duplicate section")
        dup_btn.clicked.connect(self._on_duplicate)

        # --- length spin ---
        self._len_spin = QSpinBox()
        self._len_spin.setRange(1, 512)
        self._len_spin.setValue(8)
        self._len_spin.setPrefix("bars: ")
        self._len_spin.setFixedWidth(90)
        self._len_spin.valueChanged.connect(self._on_length_changed)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(2)
        for w in (add_btn, remove_btn, rename_btn, up_btn, down_btn, dup_btn):
            btn_row.addWidget(w)
        btn_row.addStretch()
        btn_row.addWidget(self._len_spin)

        group = QGroupBox("Sections")
        inner = QVBoxLayout(group)
        inner.setContentsMargins(4, 4, 4, 4)
        inner.addWidget(self._list)
        inner.addLayout(btn_row)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(group)

        doc.subscribe(self._on_doc_changed)
        self._refresh()

    # ---------------------------------------------------------------- public

    @property
    def selected_row(self) -> int:
        return self._list.currentRow()

    # ---------------------------------------------------------------- private refresh

    def _refresh(self) -> None:
        self._applying = True
        try:
            row = self._list.currentRow()
            self._list.clear()
            for sec in self._doc.sections:
                self._list.addItem(QListWidgetItem(_section_label(sec)))
            if 0 <= row < self._list.count():
                self._list.setCurrentRow(row)
        finally:
            self._applying = False

    def _on_doc_changed(self, txn) -> None:
        # Refresh whenever sections change (path starts with "sections" or "section")
        if any(c.path[0] in ("sections", "section", "section_move") for c in txn.changes):
            self._refresh()

    # ---------------------------------------------------------------- slot handlers

    def _on_row_changed(self, row: int) -> None:
        if self._applying or row < 0:
            return
        secs = self._doc.sections
        if not secs:
            return
        # Update len spin
        self._applying = True
        try:
            self._len_spin.setValue(secs[row]["length_bars"])
        finally:
            self._applying = False
        # Compute start_bar
        start_bar = sum(s["length_bars"] for s in secs[:row])
        self.sectionSelected.emit(start_bar, secs[row]["length_bars"])

    def _on_add(self) -> None:
        name, ok = QInputDialog.getText(self, "Add Section", "Section name:")
        if ok and name.strip():
            self._doc.add_section(name.strip(), self._len_spin.value())

    def _on_remove(self) -> None:
        row = self._list.currentRow()
        if row < 0:
            return
        self._doc.remove_section(row)

    def _on_rename(self) -> None:
        row = self._list.currentRow()
        if row < 0:
            return
        old = self._doc.sections[row]["name"]
        name, ok = QInputDialog.getText(self, "Rename Section", "New name:", text=old)
        if ok and name.strip():
            self._doc.rename_section(row, name.strip())

    def _on_move_up(self) -> None:
        row = self._list.currentRow()
        if row > 0:
            self._doc.move_section(row, row - 1)
            self._list.setCurrentRow(row - 1)

    def _on_move_down(self) -> None:
        row = self._list.currentRow()
        if row >= 0 and row < self._list.count() - 1:
            self._doc.move_section(row, row + 1)
            self._list.setCurrentRow(row + 1)

    def _on_duplicate(self) -> None:
        row = self._list.currentRow()
        if row < 0:
            return
        sec = self._doc.sections[row]
        self._doc.add_section(sec["name"] + " copy", sec["length_bars"])

    def _on_length_changed(self, value: int) -> None:
        if self._applying:
            return
        row = self._list.currentRow()
        if row >= 0:
            self._doc.set_section_length(row, value)
