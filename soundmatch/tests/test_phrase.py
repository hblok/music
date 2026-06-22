"""Tests for soundmatch.core.phrase."""
from __future__ import annotations

import unittest

from inspector.metrics import Metrics
from soundmatch.core.phrase import Note, Phrase, seed_from_metrics


class TestNote(unittest.TestCase):
    """Test Note dataclass."""

    def test_to_dict(self):
        n = Note(t=0.5, midi=[60, 64])
        d = n.to_dict()
        self.assertEqual(d["t"], 0.5)
        self.assertEqual(d["midi"], [60, 64])

    def test_from_dict(self):
        d = {"t": 1.0, "midi": [72]}
        n = Note.from_dict(d)
        self.assertEqual(n.t, 1.0)
        self.assertEqual(n.midi, [72])

    def test_roundtrip(self):
        n = Note(t=0.25, midi=[61, 65, 68])
        n2 = Note.from_dict(n.to_dict())
        self.assertEqual(n2.t, n.t)
        self.assertEqual(n2.midi, n.midi)


class TestPhrase(unittest.TestCase):
    """Test Phrase dataclass."""

    def test_to_dict(self):
        notes = [Note(t=0.0, midi=[60]), Note(t=0.5, midi=[64])]
        p = Phrase(bpm=120, length_s=2.0, notes=notes, loop=True)
        d = p.to_dict()
        self.assertEqual(d["bpm"], 120)
        self.assertEqual(d["length_s"], 2.0)
        self.assertEqual(len(d["notes"]), 2)
        self.assertTrue(d["loop"])

    def test_from_dict(self):
        d = {"bpm": 130, "length_s": 1.5, "notes": [{"t": 0.0, "midi": [60]}], "loop": False}
        p = Phrase.from_dict(d)
        self.assertEqual(p.bpm, 130)
        self.assertEqual(p.length_s, 1.5)
        self.assertEqual(len(p.notes), 1)
        self.assertFalse(p.loop)

    def test_roundtrip(self):
        notes = [Note(t=0.0, midi=[61]), Note(t=0.238, midi=[68])]
        p = Phrase(bpm=125, length_s=8.0, notes=notes)
        p2 = Phrase.from_dict(p.to_dict())
        self.assertEqual(p2.bpm, p.bpm)
        self.assertEqual(p2.length_s, p.length_s)
        self.assertEqual(len(p2.notes), len(p.notes))
        self.assertEqual(p2.notes[0].t, p.notes[0].t)

    def test_default_loop(self):
        p = Phrase(bpm=120, length_s=2.0)
        self.assertTrue(p.loop)


class TestSeedFromMetrics(unittest.TestCase):
    """Test seed_from_metrics derives a phrase from target metrics."""

    def test_produces_phrase(self):
        m = Metrics(
            percussive_ratio=82.0,
            centroid_hz=2542.0,
            band_balance={"80-300": 18, "300-800": 30, "800-2500": 41, "2500-9000": 7},
            onset_count=8,
            onset_density=4.0,
            median_ioi_s=0.238,
            peaks=[(800.0, -3.0)],
            chord={"pitch_classes": ["G#"], "midi": [68, 72, 75], "sub_octave": True},
            band_decay_ms={"200-1500": 30.0, "3500-9000": 15.0},
        )
        p = seed_from_metrics(m, bpm=125)
        self.assertIsInstance(p, Phrase)
        self.assertEqual(p.bpm, 125)
        self.assertGreater(len(p.notes), 0)
        self.assertTrue(p.loop)

    def test_onset_to_note_mapping(self):
        m = Metrics(
            percussive_ratio=50.0,
            centroid_hz=1000.0,
            band_balance={"80-300": 25, "300-800": 25, "800-2500": 25, "2500-9000": 25},
            onset_count=4,
            onset_density=2.0,
            median_ioi_s=0.5,
            peaks=[],
            chord={"pitch_classes": ["C"], "midi": [60], "sub_octave": False},
            band_decay_ms={},
        )
        p = seed_from_metrics(m, bpm=120)
        self.assertEqual(len(p.notes), 4)
        # Notes should be spaced by median_ioi_s
        for i in range(1, len(p.notes)):
            self.assertAlmostEqual(p.notes[i].t, p.notes[i-1].t + 0.5, places=2)

    def test_loop_length_matches_duration(self):
        m = Metrics(
            percussive_ratio=50.0,
            centroid_hz=1000.0,
            band_balance={"80-300": 25, "300-800": 25, "800-2500": 25, "2500-9000": 25},
            onset_count=3,
            onset_density=1.5,
            median_ioi_s=0.33,
            peaks=[],
            chord={"pitch_classes": [], "midi": [61], "sub_octave": False},
            band_decay_ms={},
        )
        p = seed_from_metrics(m, bpm=120)
        expected_dur = 0.33 * 3
        self.assertAlmostEqual(p.length_s, expected_dur, places=1)

    def test_zero_onsets_fallback(self):
        m = Metrics(
            percussive_ratio=0.0,
            centroid_hz=0.0,
            band_balance={},
            onset_count=0,
            onset_density=0.0,
            median_ioi_s=0.0,
            peaks=[],
            chord={"pitch_classes": [], "midi": [61], "sub_octave": False},
            band_decay_ms={},
        )
        p = seed_from_metrics(m, bpm=120)
        self.assertGreaterEqual(len(p.notes), 1)


if __name__ == "__main__":
    unittest.main()
