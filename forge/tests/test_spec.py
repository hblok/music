"""Phase 9 tests: spec schema, validation, serialization, and control wiring."""

import json
import tempfile
import unittest
from pathlib import Path

from forge.spec.schema import PatternSpec, ProjectSpec, SectionSpec, TrackSpec
from forge.spec.validate import validate_pattern, validate_project


# ---------------------------------------------------------------------------
# TrackSpec

class TestTrackSpec(unittest.TestCase):
    def test_roundtrip(self):
        t = TrackSpec(
            instrument="kick",
            steps=[1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
            params={"f0": 55.0},
            probability=0.9,
        )
        d = t.to_dict()
        t2 = TrackSpec.from_dict(d)
        self.assertEqual(t2.instrument, "kick")
        self.assertAlmostEqual(t2.probability, 0.9)
        self.assertEqual(t2.steps, t.steps)

    def test_bars_key_preserved(self):
        t = TrackSpec("hat", bars=[0, 4])
        d = t.to_dict()
        t2 = TrackSpec.from_dict(d)
        self.assertEqual(t2.bars, [0, 4])

    def test_every_key_preserved(self):
        t = TrackSpec("clap", every=2)
        d = t.to_dict()
        t2 = TrackSpec.from_dict(d)
        self.assertEqual(t2.every, 2)


# ---------------------------------------------------------------------------
# PatternSpec

class TestPatternSpec(unittest.TestCase):
    def test_roundtrip(self):
        p = PatternSpec(
            bpm=138.0,
            length_bars=4,
            tracks=[TrackSpec("kick", [1, 0, 0, 0] * 4)],
            loop=True,
        )
        d = p.to_dict()
        p2 = PatternSpec.from_dict(d)
        self.assertAlmostEqual(p2.bpm, 138.0)
        self.assertEqual(p2.length_bars, 4)
        self.assertTrue(p2.loop)
        self.assertEqual(len(p2.tracks), 1)

    def test_defaults(self):
        p = PatternSpec(bpm=120.0, length_bars=2)
        self.assertEqual(p.n_steps, 16)
        self.assertFalse(p.loop)
        self.assertAlmostEqual(p.xf_bars, 2.0)


# ---------------------------------------------------------------------------
# SectionSpec

class TestSectionSpec(unittest.TestCase):
    def test_roundtrip(self):
        sec = SectionSpec(
            name="intro",
            start_bar=0,
            length_bars=8,
            gain=0.8,
            schedules=[PatternSpec(bpm=138.0, length_bars=8)],
        )
        d = sec.to_dict()
        sec2 = SectionSpec.from_dict(d)
        self.assertEqual(sec2.name, "intro")
        self.assertEqual(sec2.start_bar, 0)
        self.assertAlmostEqual(sec2.gain, 0.8)
        self.assertEqual(len(sec2.schedules), 1)


# ---------------------------------------------------------------------------
# ProjectSpec

class TestProjectSpec(unittest.TestCase):
    def _minimal(self):
        return ProjectSpec(
            title="Test",
            bpm=138.0,
            sections=[
                SectionSpec(
                    name="main",
                    start_bar=0,
                    length_bars=4,
                    schedules=[
                        PatternSpec(
                            bpm=138.0,
                            length_bars=4,
                            tracks=[TrackSpec("kick", [1, 0] * 8)],
                        )
                    ],
                )
            ],
        )

    def test_roundtrip(self):
        p = self._minimal()
        d = p.to_dict()
        p2 = ProjectSpec.from_dict(d)
        self.assertEqual(p2.title, "Test")
        self.assertAlmostEqual(p2.bpm, 138.0)
        self.assertEqual(len(p2.sections), 1)

    def test_master_gain_curve_roundtrip(self):
        p = self._minimal()
        p.master_gain_curve = [[0, 0.0], [4, 1.0]]
        d = p.to_dict()
        p2 = ProjectSpec.from_dict(d)
        self.assertIsNotNone(p2.master_gain_curve)
        self.assertEqual(len(p2.master_gain_curve), 2)


# ---------------------------------------------------------------------------
# Validation

class TestValidation(unittest.TestCase):
    def _valid_project(self):
        return ProjectSpec(
            title="Valid",
            bpm=138.0,
            sections=[
                SectionSpec("main", 0, 4,
                    schedules=[PatternSpec(138.0, 4,
                        tracks=[TrackSpec("kick", [1, 0] * 8)])])
            ],
        )

    def test_valid_project_ok(self):
        validate_project(self._valid_project())

    def test_empty_title_raises(self):
        p = self._valid_project()
        p.title = ""
        with self.assertRaises(ValueError):
            validate_project(p)

    def test_negative_bpm_raises(self):
        p = self._valid_project()
        p.bpm = -1.0
        with self.assertRaises(ValueError):
            validate_project(p)

    def test_zero_length_bars_raises(self):
        p = self._valid_project()
        p.sections[0].length_bars = 0
        with self.assertRaises(ValueError):
            validate_project(p)

    def test_invalid_probability_raises(self):
        p = self._valid_project()
        p.sections[0].schedules[0].tracks[0].probability = 1.5
        with self.assertRaises(ValueError):
            validate_project(p)

    def test_invalid_target_raises(self):
        p = self._valid_project()
        p.target = 0.0
        with self.assertRaises(ValueError):
            validate_project(p)

    def test_validate_from_dict(self):
        d = self._valid_project().to_dict()
        validate_project(d)

    def test_validate_pattern_ok(self):
        p = PatternSpec(138.0, 4, tracks=[TrackSpec("kick", [1, 0] * 8)])
        validate_pattern(p)

    def test_validate_pattern_zero_n_steps_raises(self):
        p = PatternSpec(138.0, 4, n_steps=0)
        with self.assertRaises(ValueError):
            validate_pattern(p)


# ---------------------------------------------------------------------------
# Serialization

class TestSerialization(unittest.TestCase):
    def _minimal_project(self):
        return ProjectSpec(
            title="Serialize Test",
            bpm=138.0,
            sections=[
                SectionSpec("main", 0, 4,
                    schedules=[PatternSpec(138.0, 4,
                        tracks=[TrackSpec("kick", [1, 0] * 8)])])
            ],
        )

    def test_save_and_load(self):
        from forge.spec.serialize import load_project, save_project
        p = self._minimal_project()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "project.json"
            save_project(p, path)
            self.assertTrue(path.exists())
            p2 = load_project(path)
            self.assertEqual(p2.title, p.title)
            self.assertAlmostEqual(p2.bpm, p.bpm)

    def test_save_creates_parent_dirs(self):
        from forge.spec.serialize import save_project
        p = self._minimal_project()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "subdir" / "deep" / "project.json"
            save_project(p, path)
            self.assertTrue(path.exists())

    def test_load_invalid_json_raises(self):
        from forge.spec.serialize import load_project
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "bad.json"
            path.write_text("not json")
            with self.assertRaises(json.JSONDecodeError):
                load_project(path)

    def test_load_missing_file_raises(self):
        from forge.spec.serialize import load_project
        with self.assertRaises(FileNotFoundError):
            load_project(Path("/nonexistent/project.json"))

    def test_save_and_load_dict(self):
        from forge.spec.serialize import load_project_dict, save_project
        p = self._minimal_project()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "project.json"
            save_project(p.to_dict(), path)
            d = load_project_dict(path)
            self.assertIsInstance(d, dict)
            self.assertEqual(d["title"], p.title)


# ---------------------------------------------------------------------------
# control.load_project / save_project wiring

class TestControlPhase9(unittest.TestCase):
    def _project_dict(self):
        return {
            "title": "Control Test",
            "bpm": 138.0,
            "seed": 0,
            "sections": [
                {
                    "name": "main",
                    "start_bar": 0,
                    "length_bars": 4,
                    "schedules": [
                        {
                            "bpm": 138.0,
                            "length_bars": 4,
                            "tracks": [
                                {"instrument": "kick",
                                 "steps": [1, 0, 0, 0, 1, 0, 0, 0,
                                           1, 0, 0, 0, 1, 0, 0, 0]},
                            ],
                        }
                    ],
                }
            ],
        }

    def test_save_and_load_roundtrip(self):
        from forge import control
        p = self._project_dict()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "project.json"
            control.save_project(p, path)
            loaded = control.load_project(path)
            self.assertEqual(loaded["title"], "Control Test")
            self.assertAlmostEqual(loaded["bpm"], 138.0)

    def test_load_and_render(self):
        from forge import control
        p = self._project_dict()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "project.json"
            control.save_project(p, path)
            loaded = control.load_project(path)
            buf = control.render_track(loaded)
            self.assertGreater(buf.peak(), 0)

    def test_load_missing_raises(self):
        from forge import control
        with self.assertRaises(FileNotFoundError):
            control.load_project(Path("/does/not/exist.json"))


if __name__ == "__main__":
    unittest.main()
