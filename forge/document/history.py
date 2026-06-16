"""forge.document.history — undo/redo stack over transactions.

The undo stack holds original transactions; pop_for_undo returns the reversed
transaction (to re-apply as an undo).  The redo stack holds the original
transactions so pop_for_redo can re-apply them forward.

Coalescing: consecutive slider-drag transactions that touch the exact same
set of paths are merged so that a single undo step undoes the entire drag.

No Qt, no DSP imports here.
"""

from __future__ import annotations

from collections import deque

from forge.document.transaction import Transaction


class History:
    """Undo/redo stack.

    Args:
        max_depth: maximum number of undo steps retained.
    """

    MAX_DEPTH: int = 200

    def __init__(self, max_depth: int = MAX_DEPTH) -> None:
        self._undo: deque[Transaction] = deque(maxlen=max_depth)
        self._redo: deque[Transaction] = deque(maxlen=max_depth)

    # ---------------------------------------------------------------- queries

    def can_undo(self) -> bool:
        return bool(self._undo)

    def can_redo(self) -> bool:
        return bool(self._redo)

    def undo_description(self) -> str:
        return self._undo[-1].description if self._undo else ""

    def redo_description(self) -> str:
        return self._redo[-1].description if self._redo else ""

    # ---------------------------------------------------------------- mutation

    def push(self, txn: Transaction, *, coalesce: bool = False) -> None:
        """Record a transaction.

        Args:
            txn:       The transaction to push.
            coalesce:  If True, attempt to merge with the last undo entry when
                       they touch the same paths (slider-drag coalescing).
                       The merged entry retains the earliest old_value so
                       a single undo reverts the entire drag.
        """
        if txn.is_empty():
            return

        if coalesce and self._undo:
            last = self._undo[-1]
            last_paths = {c.path for c in last.changes}
            new_paths = {c.path for c in txn.changes}
            if last_paths == new_paths:
                # Merge: keep old_values from last, take new_values from txn
                from forge.document.transaction import FieldChange
                merged = Transaction(txn.description)
                last_by_path = {c.path: c for c in last.changes}
                for ch in txn.changes:
                    old = last_by_path[ch.path].old_value
                    merged.add_change(ch.path, old, ch.new_value)
                self._undo[-1] = merged
                self._redo.clear()
                return

        self._undo.append(txn)
        self._redo.clear()

    def pop_for_undo(self) -> Transaction | None:
        """Return the reversed transaction to apply (undoes the last push).

        Also pushes the original to the redo stack.
        """
        if not self._undo:
            return None
        txn = self._undo.pop()
        self._redo.append(txn)
        return txn.reversed()

    def pop_for_redo(self) -> Transaction | None:
        """Return the original transaction to re-apply.

        Also pushes the original back to the undo stack.
        """
        if not self._redo:
            return None
        txn = self._redo.pop()
        self._undo.append(txn)
        return txn

    def clear(self) -> None:
        self._undo.clear()
        self._redo.clear()

    def __len__(self) -> int:
        return len(self._undo)
