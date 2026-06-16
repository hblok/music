"""forge.document.model — mutable project document.

``ProjectDoc`` is the live, editable representation of a tracker project.
All mutations go through a typed edit API that:
  1. Records the (path, old, new) change in a Transaction.
  2. Applies the change to the in-memory state.
  3. Pushes the transaction to the History (undo/redo).
  4. Notifies subscribed observers (UI, scheduler) via callbacks.

This module has no Qt imports and no DSP imports.  It is fully testable
headless and importable from the audio thread safely (read-only access).

Paths used in transactions::

    ("global", field)                          → project-level fields
    ("channels", idx)                          → insert (new=channel) / remove (new=None)
    ("channel", idx, "instrument_id")
    ("channel", idx, "seed")
    ("channel", idx, "params", name)
    ("channel", idx, "step", step_idx, field)
    ("channel", idx, "step", step_idx, "params", name)
    ("channel", idx, "envelope", bp_idx, "bar"|"value")
"""

from __future__ import annotations

import random
from typing import Callable, Any

from forge.document.channels import (
    AnyChannel,
    AutomationChannel,
    Breakpoint,
    PatternChannel,
    StepData,
    TextureChannel,
    channel_from_dict,
)
from forge.document.history import History
from forge.document.transaction import Transaction, channel_content_hash


# ---------------------------------------------------------------------------
# Observer type alias

Observer = Callable[[Transaction], None]


# ---------------------------------------------------------------------------
# ProjectDoc

class ProjectDoc:
    """Mutable project document.

    Args:
        title:  Project title string.
        bpm:    Tempo in BPM.
        sr:     Sample rate (default 44100).
        seed:   Global RNG seed (default 0).
    """

    def __init__(
        self,
        title: str = "Untitled",
        bpm: float = 138.0,
        sr: int = 44100,
        seed: int = 0,
    ) -> None:
        self._title = title
        self._bpm = bpm
        self._sr = sr
        self._seed = seed
        self._normalize = True
        self._target = 0.85
        self._fade_out_s = 2.0

        self._channels: list[AnyChannel] = []
        self._history = History()
        self._observers: list[Observer] = []

    # ---------------------------------------------------------------- observers

    def subscribe(self, callback: Observer) -> None:
        """Subscribe to change notifications.  callback(txn) is called after each edit."""
        self._observers.append(callback)

    def unsubscribe(self, callback: Observer) -> None:
        self._observers = [cb for cb in self._observers if cb is not callback]

    def _notify(self, txn: Transaction) -> None:
        for cb in self._observers:
            cb(txn)

    # ---------------------------------------------------------------- read-only accessors

    @property
    def title(self) -> str:
        return self._title

    @property
    def bpm(self) -> float:
        return self._bpm

    @property
    def sr(self) -> int:
        return self._sr

    @property
    def seed(self) -> int:
        return self._seed

    @property
    def channels(self) -> list[AnyChannel]:
        return list(self._channels)

    def channel(self, idx: int) -> AnyChannel:
        return self._channels[idx]

    def channel_count(self) -> int:
        return len(self._channels)

    @property
    def history(self) -> History:
        return self._history

    # ---------------------------------------------------------------- cache keys

    def channel_cache_key(self, idx: int) -> str:
        """Return the content hash of channel *idx*'s render-relevant data."""
        return channel_content_hash(self._channels[idx].to_dict())

    # ---------------------------------------------------------------- global edits

    def set_global(self, field: str, value: Any, *, coalesce: bool = False) -> None:
        """Set a project-level field (title, bpm, sr, seed, …)."""
        attr = f"_{field}"
        old = getattr(self, attr)
        if old == value:
            return
        txn = Transaction(f"set {field}")
        txn.add_change(("global", field), old, value)
        setattr(self, attr, value)
        self._history.push(txn, coalesce=coalesce)
        self._notify(txn)

    # ---------------------------------------------------------------- channel management

    def add_channel(self, channel: AnyChannel) -> int:
        """Append a channel; returns its new index."""
        idx = len(self._channels)
        txn = Transaction("add channel")
        txn.add_change(("channels", idx), None, channel)
        self._channels.append(channel)
        self._history.push(txn)
        self._notify(txn)
        return idx

    def remove_channel(self, idx: int) -> None:
        """Remove channel at *idx*."""
        old = self._channels[idx]
        txn = Transaction(f"remove channel {idx}")
        txn.add_change(("channels", idx), old, None)
        self._channels.pop(idx)
        self._history.push(txn)
        self._notify(txn)

    # ---------------------------------------------------------------- per-channel edits

    def set_instrument(self, channel_idx: int, instrument_id: str) -> None:
        ch = self._channels[channel_idx]
        if not isinstance(ch, (PatternChannel, TextureChannel)):
            raise TypeError("set_instrument only applies to pattern/texture channels")
        old = ch.instrument_id
        if old == instrument_id:
            return
        txn = Transaction("set instrument")
        txn.add_change(("channel", channel_idx, "instrument_id"), old, instrument_id)
        ch.instrument_id = instrument_id
        self._history.push(txn)
        self._notify(txn)

    def set_param(self, channel_idx: int, param: str, value: Any, *, coalesce: bool = False) -> None:
        """Set a track-level param override for a pattern or texture channel."""
        ch = self._channels[channel_idx]
        old = ch.params.get(param)
        if old == value:
            return
        txn = Transaction(f"set param {param}")
        txn.add_change(("channel", channel_idx, "params", param), old, value)
        ch.params[param] = value
        self._history.push(txn, coalesce=coalesce)
        self._notify(txn)

    def set_seed(self, channel_idx: int, seed: int) -> None:
        ch = self._channels[channel_idx]
        old = ch.seed
        if old == seed:
            return
        txn = Transaction("set seed")
        txn.add_change(("channel", channel_idx, "seed"), old, seed)
        ch.seed = seed
        self._history.push(txn)
        self._notify(txn)

    def reroll(self, channel_idx: int) -> None:
        """Generate a new random seed for channel *channel_idx*."""
        new_seed = random.randint(0, 2 ** 31 - 1)
        self.set_seed(channel_idx, new_seed)

    # ---------------------------------------------------------------- step edits (PatternChannel)

    def set_step(
        self,
        channel_idx: int,
        step_idx: int,
        field: str,
        value: Any,
    ) -> None:
        """Set one field of one step in a PatternChannel.

        field ∈ {on, accent, ghost, probability}
        """
        ch = self._channels[channel_idx]
        if not isinstance(ch, PatternChannel):
            raise TypeError("set_step only applies to PatternChannel")
        step = ch.steps[step_idx]
        old = getattr(step, field)
        if old == value:
            return
        txn = Transaction(f"set step[{step_idx}].{field}")
        txn.add_change(("channel", channel_idx, "step", step_idx, field), old, value)
        setattr(step, field, value)
        self._history.push(txn)
        self._notify(txn)

    def set_step_param(
        self,
        channel_idx: int,
        step_idx: int,
        param: str,
        value: Any,
        *,
        coalesce: bool = False,
    ) -> None:
        """Set a per-step param override."""
        ch = self._channels[channel_idx]
        if not isinstance(ch, PatternChannel):
            raise TypeError("set_step_param only applies to PatternChannel")
        step = ch.steps[step_idx]
        old = step.params.get(param)
        if old == value:
            return
        txn = Transaction(f"set step[{step_idx}].params.{param}")
        txn.add_change(("channel", channel_idx, "step", step_idx, "params", param), old, value)
        step.params[param] = value
        self._history.push(txn, coalesce=coalesce)
        self._notify(txn)

    def toggle_step(self, channel_idx: int, step_idx: int) -> None:
        """Toggle the on/off state of a step."""
        ch = self._channels[channel_idx]
        if not isinstance(ch, PatternChannel):
            raise TypeError("toggle_step only applies to PatternChannel")
        self.set_step(channel_idx, step_idx, "on", not ch.steps[step_idx].on)

    def clear_steps(self, channel_idx: int) -> None:
        """Clear all steps in a PatternChannel (all off)."""
        ch = self._channels[channel_idx]
        if not isinstance(ch, PatternChannel):
            raise TypeError("clear_steps only applies to PatternChannel")
        txn = Transaction("clear steps")
        for i, step in enumerate(ch.steps):
            if step.on or step.accent or step.ghost or step.probability != 1.0 or step.params:
                txn.add_change(
                    ("channel", channel_idx, "step", i, "on"),
                    step.on, False,
                )
                step.on = False
                step.accent = False
                step.ghost = False
                step.probability = 1.0
                step.params = {}
        if not txn.is_empty():
            self._history.push(txn)
            self._notify(txn)

    # ---------------------------------------------------------------- block copy/paste

    def copy_steps(self, channel_idx: int, start: int, end: int) -> list[StepData]:
        """Return a copy of steps[start:end] (exclusive end)."""
        import copy
        ch = self._channels[channel_idx]
        if not isinstance(ch, PatternChannel):
            raise TypeError("copy_steps only applies to PatternChannel")
        return [copy.copy(s) for s in ch.steps[start:end]]

    def paste_steps(self, channel_idx: int, start: int, clipboard: list[StepData]) -> None:
        """Paste *clipboard* steps starting at *start*."""
        import copy
        ch = self._channels[channel_idx]
        if not isinstance(ch, PatternChannel):
            raise TypeError("paste_steps only applies to PatternChannel")
        txn = Transaction("paste steps")
        for offset, new_step in enumerate(clipboard):
            idx = start + offset
            if idx >= ch.n_steps:
                break
            old_step = copy.copy(ch.steps[idx])
            new_copy = copy.copy(new_step)
            txn.add_change(("channel", channel_idx, "step", idx, "__step__"), old_step, new_copy)
            ch.steps[idx] = new_copy
        if not txn.is_empty():
            self._history.push(txn)
            self._notify(txn)

    # ---------------------------------------------------------------- envelope edits (TextureChannel)

    def add_breakpoint(self, channel_idx: int, bar: float, value: float) -> int:
        ch = self._channels[channel_idx]
        if not isinstance(ch, TextureChannel):
            raise TypeError("add_breakpoint only applies to TextureChannel")
        bp = Breakpoint(bar, value)
        idx = len(ch.envelope)
        txn = Transaction("add breakpoint")
        txn.add_change(("channel", channel_idx, "envelope_add", idx), None, bp)
        ch.envelope.append(bp)
        self._history.push(txn)
        self._notify(txn)
        return idx

    def set_breakpoint(self, channel_idx: int, bp_idx: int, bar: float, value: float) -> None:
        ch = self._channels[channel_idx]
        if not isinstance(ch, TextureChannel):
            raise TypeError("set_breakpoint only applies to TextureChannel")
        bp = ch.envelope[bp_idx]
        txn = Transaction("set breakpoint")
        if bp.bar != bar:
            txn.add_change(("channel", channel_idx, "envelope", bp_idx, "bar"), bp.bar, bar)
            bp.bar = bar
        if bp.value != value:
            txn.add_change(("channel", channel_idx, "envelope", bp_idx, "value"), bp.value, value)
            bp.value = value
        if not txn.is_empty():
            self._history.push(txn)
            self._notify(txn)

    # ---------------------------------------------------------------- undo/redo

    def undo(self) -> bool:
        """Undo the last transaction.  Returns True if there was something to undo."""
        rev = self._history.pop_for_undo()
        if rev is None:
            return False
        self._apply_transaction(rev)
        self._notify(rev)
        return True

    def redo(self) -> bool:
        """Redo the last undone transaction.  Returns True if there was something to redo."""
        txn = self._history.pop_for_redo()
        if txn is None:
            return False
        self._apply_transaction(txn)
        self._notify(txn)
        return True

    # ---------------------------------------------------------------- serialization

    def to_dict(self) -> dict:
        return {
            "title": self._title,
            "bpm": self._bpm,
            "sr": self._sr,
            "seed": self._seed,
            "normalize": self._normalize,
            "target": self._target,
            "fade_out_s": self._fade_out_s,
            "channels": [ch.to_dict() for ch in self._channels],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ProjectDoc":
        doc = cls(
            title=str(d.get("title", "Untitled")),
            bpm=float(d.get("bpm", 138.0)),
            sr=int(d.get("sr", 44100)),
            seed=int(d.get("seed", 0)),
        )
        doc._normalize = bool(d.get("normalize", True))
        doc._target = float(d.get("target", 0.85))
        doc._fade_out_s = float(d.get("fade_out_s", 2.0))
        for ch_dict in d.get("channels", []):
            doc._channels.append(channel_from_dict(ch_dict))
        return doc

    # ---------------------------------------------------------------- internal apply

    def _apply_transaction(self, txn: Transaction) -> None:
        """Apply all changes in *txn* to the in-memory state."""
        for change in txn.changes:
            self._apply_change(change.path, change.new_value)

    def _apply_change(self, path: tuple, value: Any) -> None:  # noqa: C901 — dispatch method
        """Route a (path, new_value) change to the correct field."""
        kind = path[0]

        if kind == "global":
            setattr(self, f"_{path[1]}", value)

        elif kind == "channels":
            idx = path[1]
            if value is None:
                # Remove channel at idx
                if 0 <= idx < len(self._channels):
                    self._channels.pop(idx)
            elif idx <= len(self._channels):
                if idx == len(self._channels):
                    self._channels.append(value)
                else:
                    self._channels.insert(idx, value)

        elif kind == "channel":
            idx = path[1]
            ch = self._channels[idx]
            sub = path[2]

            if sub == "instrument_id":
                ch.instrument_id = value  # type: ignore[union-attr]
            elif sub == "seed":
                ch.seed = value  # type: ignore[union-attr]
            elif sub == "params":
                if value is None:
                    ch.params.pop(path[3], None)
                else:
                    ch.params[path[3]] = value

            elif sub == "step":
                step_idx = path[3]
                field = path[4]
                if not isinstance(ch, PatternChannel):
                    return
                step = ch.steps[step_idx]
                if field == "__step__":
                    ch.steps[step_idx] = value
                elif field == "params":
                    if value is None:
                        step.params.pop(path[5], None)
                    else:
                        step.params[path[5]] = value
                else:
                    setattr(step, field, value)

            elif sub == "envelope":
                bp_idx = path[3]
                field = path[4]
                if isinstance(ch, TextureChannel):
                    setattr(ch.envelope[bp_idx], field, value)

            elif sub == "envelope_add":
                bp_idx = path[3]
                if isinstance(ch, TextureChannel):
                    if value is None:
                        if 0 <= bp_idx < len(ch.envelope):
                            ch.envelope.pop(bp_idx)
                    else:
                        ch.envelope.append(value)
