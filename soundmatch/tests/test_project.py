"""Tests for soundmatch.core.project — MatchProject save/load round-trip."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from inspector.metrics import Metrics
from soundmatch.core.phrase import Note, Phrase
from soundmatch.core.project import MatchProject
from soundmatch.core.variants import VariantSpec


def _sample_project() -> MatchProject:
    """Build a sample MatchProject for testing."""
    m = Metrics(
        percussive_ratio=82.0,
        centroid_hz=2542.0,
        band_balance={"80-300": 18.0, "300-800": 30.0, "800-2500": 41.0, "2500-9000": 7.0},
        onset_count=36,
        onset_density=4.5,
        median_ioi_s=0.238,
        peaks=[(800.0, -3.0)],
        chord={"pitch_classes": ["G#"], "midi": [68], "sub_octave": True},
        band_decay_ms={"200-1500": 30.0, "3500-9000": 15.0},
    )
    p = Phrase(
        bpm=125,
        length_s=8.0,
        notes=[Note(t=0.0, midi=[68, 72, 75]), Note(t=0.238, midi=[68, 72, 75])],
        loop=True,
    )
    return MatchProject(
        reference_path=Path("/some/audio.mp3"),
        reference_sha="abcd1234",
        start_s=1.0,
        end_s=10.0,
        stem="other",
        target_metrics=m,
        phrase=p,
        instrument_id="synth_brass",
        params={"drive": 2.0, "rasp": 0.18},
        layers=[("hat", {"f0": 8000.0, "decay": 0.05})],
        seed=42,
        variant_specs=[VariantSpec("A", {"drive": 1.0}), VariantSpec("B", {"drive": 3.0})],
    )


class TestMatchProjectRoundTrip(unittest.TestCase):
    """Test save/load produces an equivalent project."""

    def test_roundtrip_via_json(self):
        proj = _sample_project()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.smatch"
            proj.save(path)
            proj2 = MatchProject.load(path)
            self.assertEqual(proj2.reference_path, proj.reference_path)
            self.assertEqual(proj2.reference_sha, proj.reference_sha)
            self.assertEqual(proj2.start_s, proj.start_s)
            self.assertEqual(proj2.end_s, proj.end_s)
            self.assertEqual(proj2.stem, proj.stem)
            self.assertAlmostEqual(proj2.target_metrics.percussive_ratio,
                                   proj.target_metrics.percussive_ratio, places=1)
            self.assertEqual(proj2.instrument_id, proj.instrument_id)
            self.assertEqual(proj2.seed, proj.seed)
            self.assertEqual(len(proj2.variant_specs), len(proj.variant_specs))

    def test_roundtrip_preserves_layers(self):
        proj = _sample_project()
        d = proj.to_dict()
        proj2 = MatchProject.from_dict(d)
        self.assertEqual(len(proj2.layers), 1)
        self.assertEqual(proj2.layers[0][0], "hat")

    def test_roundtrip_preserves_phrase(self):
        proj = _sample_project()
        d = proj.to_dict()
        proj2 = MatchProject.from_dict(d)
        self.assertEqual(proj2.phrase.bpm, proj.phrase.bpm)
        self.assertEqual(len(proj2.phrase.notes), len(proj.phrase.notes))

    def test_roundtrip_preserves_variant_specs(self):
        proj = _sample_project()
        d = proj.to_dict()
        proj2 = MatchProject.from_dict(d)
        self.assertEqual(len(proj2.variant_specs), 2)
        self.assertEqual(proj2.variant_specs[0].name, "A")
        self.assertEqual(proj2.variant_specs[1].param_overrides["drive"], 3.0)


class TestMatchProjectDefaults(unittest.TestCase):
    """Test default values and edge cases."""

    def test_empty_project(self):
        proj = MatchProject()
        self.assertEqual(proj.stem, "other")
        self.assertEqual(proj.seed, 42)
        self.assertIsNone(proj.target_metrics)
        self.assertIsNone(proj.phrase)
        self.assertIsNone(proj.best_variant)

    def test_save_load_empty(self):
        proj = MatchProject()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "empty.smatch"
            proj.save(path)
            proj2 = MatchProject.load(path)
            self.assertIsNone(proj2.target_metrics)
            self.assertIsNone(proj2.phrase)


class TestMatchProjectSHA(unittest.TestCase):
    """Test SHA-256 computation."""

    def test_update_sha_on_existing_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "test.wav"
            p.write_text("hello", encoding="utf-8")
            proj = MatchProject(reference_path=p)
            proj.update_sha()
            self.assertGreater(len(proj.reference_sha), 0)

    def test_no_sha_on_missing_file(self):
        proj = MatchProject(reference_path=Path("/nonexistent/file.wav"))
        proj.update_sha()
        self.assertEqual(proj.reference_sha, "")


class TestMatchProjectJSON(unittest.TestCase):
    """Test that the saved file is valid JSON."""

    def test_valid_json_output(self):
        proj = _sample_project()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.smatch"
            proj.save(path)
            text = path.read_text(encoding="utf-8")
            data = json.loads(text)
            self.assertIn("reference_path", data)
            self.assertIn("target_metrics", data)
            self.assertIn("phrase", data)
            self.assertIn("variant_specs", data)


if __name__ == "__main__":
    unittest.main()
