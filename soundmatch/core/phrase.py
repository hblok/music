"""soundmatch.core.phrase — Phrase/Note model; seed_from_metrics(); loop length.

A Phrase is the unit of sound matching: a timed sequence of notes that loops.
``seed_from_metrics`` derives a starting phrase from measured target metrics,
converting onsets to note times and chord detections to MIDI pitches.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

log = logging.getLogger(__name__)

import numpy as np

from inspector.metrics import Metrics


@dataclass
class Note:
    """A single note event within a Phrase."""

    t: float          # onset time in seconds (relative to phrase start)
    midi: list[int]   # MIDI note numbers (chord / multi-note)

    def to_dict(self) -> dict[str, Any]:
        return {"t": self.t, "midi": list(self.midi)}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Note:
        return cls(t=d["t"], midi=list(d["midi"]))


@dataclass
class Phrase:
    """A timed sequence of notes that loops to fill the selection length.

    Attributes:
        bpm:       Tempo in BPM.
        length_s:  Loop length in seconds (= selection length).
        notes:     Ordered list of Note events.
        loop:      Whether to loop the phrase to fill the target duration.
    """

    bpm: float
    length_s: float
    notes: list[Note] = field(default_factory=list)
    loop: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "bpm": self.bpm,
            "length_s": self.length_s,
            "notes": [n.to_dict() for n in self.notes],
            "loop": self.loop,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Phrase:
        return cls(
            bpm=d["bpm"],
            length_s=d["length_s"],
            notes=[Note.from_dict(n) for n in d.get("notes", [])],
            loop=d.get("loop", True),
        )


def seed_from_metrics(m: Metrics, bpm: float) -> Phrase:
    """Derive a starting Phrase from target metrics.

    Uses onset times (derived from onset_count and median_ioi) and
    chord detection MIDI notes to seed the phrase.  The loop length
    equals the selection duration derived from onset stats.
    """
    duration = m.median_ioi_s * m.onset_count if m.onset_count > 0 else 1.0
    duration = max(duration, 0.5)

    # Derive note onset times from onset stats
    notes: list[Note] = []
    if m.onset_count > 0 and m.median_ioi_s > 0:
        t = 0.0
        for _ in range(m.onset_count):
            midi_notes = m.chord.get("midi", [61])  # default to C#4
            if not midi_notes:
                midi_notes = [61]
            notes.append(Note(t=t, midi=list(midi_notes)))
            t += m.median_ioi_s
            if t >= duration:
                break
    else:
        # Fallback: a single note
        midi_notes = m.chord.get("midi", [61])
        notes.append(Note(t=0.0, midi=list(midi_notes) if midi_notes else [61]))

    return Phrase(
        bpm=bpm,
        length_s=duration,
        notes=notes,
        loop=True,
    )
