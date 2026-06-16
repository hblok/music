"""forge.document.transaction — edit transactions and content hashing.

A Transaction records one logical edit as a list of (path, old, new) changes.
Paths are tuples that the ProjectDoc's ``_apply_change`` can route to the
right field.

Content hashing: ``channel_content_hash(data_dict)`` produces a stable 16-hex-
char string from the render-relevant fields of a channel.  This is the cache
key used by forge.playback.cache / forge.playback.scheduler.

No Qt, no DSP imports here.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class FieldChange:
    """One field mutation within a transaction."""

    path: tuple
    old_value: Any
    new_value: Any


class Transaction:
    """A set of related field changes representing one logical user action."""

    def __init__(self, description: str = "") -> None:
        self.description = description
        self.changes: list[FieldChange] = []

    def add_change(self, path: tuple, old_value: Any, new_value: Any) -> None:
        self.changes.append(FieldChange(path, old_value, new_value))

    def is_empty(self) -> bool:
        return not self.changes

    def affected_channel_indices(self) -> set[int]:
        """Return the set of channel indices touched by this transaction."""
        result: set[int] = set()
        for ch in self.changes:
            if len(ch.path) >= 2 and ch.path[0] in ("channel", "channels"):
                idx = ch.path[1]
                if isinstance(idx, int):
                    result.add(idx)
        return result

    def reversed(self) -> "Transaction":
        """Return a new transaction that undoes this one."""
        t = Transaction(f"undo: {self.description}")
        for ch in reversed(self.changes):
            t.add_change(ch.path, ch.new_value, ch.old_value)
        return t

    def __repr__(self) -> str:
        return f"Transaction({self.description!r}, {len(self.changes)} changes)"


# ---------------------------------------------------------------------------
# Content hashing

def channel_content_hash(channel_data: dict) -> str:
    """Return a stable 16-hex-char hash of channel render-relevant data.

    The hash changes when anything that would produce different audio changes
    (instrument, params, steps, seed, envelope …).  It does NOT change for
    purely presentational fields.

    Args:
        channel_data: the dict returned by ``AnyChannel.to_dict()``.

    Returns:
        16-character lowercase hex string.
    """
    serialized = json.dumps(channel_data, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()[:16]
