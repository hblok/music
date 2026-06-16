"""Phase 4 tests: step patterns, schedules, groove rendering."""

import unittest

import numpy as np

from forge.core.buffer import AudioBuffer
from forge.core.grid import Grid
from forge.core.loopfold import check_seam
from forge.core.rng import RngContext
from forge.patterns.groove import render_groove, render_loop, render_pattern_spec
from forge.patterns.schedule import Schedule
from forge.patterns.step import Step, StepPattern


# ---------------------------------------------------------------------------
# Step / StepPattern

class TestStep(unittest.TestCase):
    def test_step_defaults(self):
        s = Step("kick")
        self.assertEqual(s.instrument_id, "kick")
        self.assertAlmostEqual(s.probability, 1.0)
        self.assertFalse(s.accent)
        self.assertFalse(s.ghost)

    def test_pattern_hits_empty(self):
        p = StepPattern("kick")
        self.assertEqual(p.hits(), [])

    def test_pattern_set_and_hits(self):
        p = StepPattern("kick")
        p.set(0).set(4).set(8).set(12)
        hits = p.hits()
        self.assertEqual([i for i, _ in hits], [0, 4, 8, 12])

    def test_pattern_clear(self):
        p = StepPattern("kick")
        p.set(0)
        p.clear(0)
        self.assertEqual(p.hits(), [])

    def test_pattern_params_merged(self):
        p = StepPattern("kick", default_params={"f0": 55.0})
        p.set(0, params={"drive": 2.0})
        _, step = p.hits()[0]
        self.assertAlmostEqual(step.params["f0"], 55.0)
        self.assertAlmostEqual(step.params["drive"], 2.0)

    def test_from_track_dict_simple(self):
        track = {
            "instrument": "kick",
            "steps": [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
        }
        p = StepPattern.from_track_dict(track)
        self.assertEqual(len(p.hits()), 4)
        self.assertEqual([i for i, _ in p.hits()], [0, 4, 8, 12])

    def test_from_track_dict_rich(self):
        track = {
            "instrument": "tek",
            "steps": [
                {"on": True, "accent": True},
                None,
                {"on": True, "ghost": True, "probability": 0.5},
            ] + [0] * 13,
        }
        p = StepPattern.from_track_dict(track)
        hits = dict(p.hits())
        self.assertTrue(hits[0].accent)
        self.assertTrue(hits[2].ghost)
        self.assertAlmostEqual(hits[2].probability, 0.5)

    def test_from_track_dict_on_false(self):
        track = {
            "instrument": "hat",
            "steps": [{"on": False}] + [0] * 15,
        }
        p = StepPattern.from_track_dict(track)
        self.assertEqual(p.hits(), [])


# ---------------------------------------------------------------------------
# Schedule

class TestSchedule(unittest.TestCase):
    def _kick_pattern(self):
        p = StepPattern("kick")
        p.set(0).set(4).set(8).set(12)
        return p

    def test_add_pattern(self):
        sched = Schedule(4, bpm=138.0)
        sched.add(0, self._kick_pattern())
        self.assertEqual(len(sched.get_patterns(0)), 1)
        self.assertEqual(len(sched.get_patterns(1)), 0)

    def test_add_every(self):
        sched = Schedule(8, bpm=138.0)
        sched.add(0, self._kick_pattern(), every=2)
        for b in (0, 2, 4, 6):
            self.assertEqual(len(sched.get_patterns(b)), 1)
        for b in (1, 3, 5, 7):
            self.assertEqual(len(sched.get_patterns(b)), 0)

    def test_add_all(self):
        sched = Schedule(4, bpm=138.0)
        sched.add_all(self._kick_pattern())
        for b in range(4):
            self.assertEqual(len(sched.get_patterns(b)), 1)

    def test_bars_with_patterns(self):
        sched = Schedule(4, bpm=138.0)
        sched.add(0, self._kick_pattern())
        sched.add(2, self._kick_pattern())
        self.assertEqual(sched.bars_with_patterns(), [0, 2])

    def test_from_pattern_spec_basic(self):
        spec = {
            "bpm": 138.0,
            "length_bars": 4,
            "tracks": [
                {"instrument": "kick",
                 "steps": [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]},
            ],
        }
        sched = Schedule.from_pattern_spec(spec)
        self.assertEqual(sched.length_bars, 4)
        self.assertAlmostEqual(sched.bpm, 138.0)
        # kick is add_all → present on every bar
        for b in range(4):
            self.assertEqual(len(sched.get_patterns(b)), 1)

    def test_from_pattern_spec_bars_key(self):
        spec = {
            "bpm": 138.0,
            "length_bars": 8,
            "tracks": [
                {"instrument": "clap",
                 "bars": [0, 4],
                 "steps": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0]},
            ],
        }
        sched = Schedule.from_pattern_spec(spec)
        self.assertEqual(len(sched.get_patterns(0)), 1)
        self.assertEqual(len(sched.get_patterns(4)), 1)
        self.assertEqual(len(sched.get_patterns(2)), 0)

    def test_invalid_bpm_raises(self):
        with self.assertRaises(ValueError):
            Schedule(4, bpm=0.0)

    def test_invalid_length_bars_raises(self):
        with self.assertRaises(ValueError):
            Schedule(0, bpm=138.0)


# ---------------------------------------------------------------------------
# Groove rendering

class TestRenderGroove(unittest.TestCase):
    def _rng(self, seed=42):
        return RngContext(seed)

    def _kick_spec(self, length_bars=2):
        return {
            "bpm": 138.0,
            "length_bars": length_bars,
            "tracks": [
                {"instrument": "kick",
                 "steps": [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]},
            ],
        }

    def test_returns_audio_buffer(self):
        sched = Schedule.from_pattern_spec(self._kick_spec())
        buf = render_groove(sched, self._rng())
        self.assertIsInstance(buf, AudioBuffer)

    def test_has_signal(self):
        sched = Schedule.from_pattern_spec(self._kick_spec())
        buf = render_groove(sched, self._rng())
        self.assertGreater(buf.peak(), 0)

    def test_length_matches_bars(self):
        spec = self._kick_spec(length_bars=4)
        sched = Schedule.from_pattern_spec(spec)
        buf = render_groove(sched, self._rng())
        grid = Grid(sched.bpm)
        expected_s = grid.bar * sched.length_bars
        self.assertAlmostEqual(buf.len_seconds(), expected_s, delta=0.01)

    def test_deterministic(self):
        spec = self._kick_spec()
        sched = Schedule.from_pattern_spec(spec)
        buf1 = render_groove(sched, RngContext(7))
        buf2 = render_groove(sched, RngContext(7))
        np.testing.assert_array_equal(buf1.data, buf2.data)

    def test_different_seeds_differ(self):
        spec = {
            "bpm": 138.0,
            "length_bars": 2,
            "tracks": [
                {"instrument": "tek",
                 "steps": [1] * 16,
                 "probability": 0.5},
            ],
        }
        sched = Schedule.from_pattern_spec(spec)
        buf1 = render_groove(sched, RngContext(1))
        buf2 = render_groove(sched, RngContext(2))
        self.assertFalse(np.array_equal(buf1.data, buf2.data))

    def test_multi_instrument_renders(self):
        spec = {
            "bpm": 138.0,
            "length_bars": 1,
            "tracks": [
                {"instrument": "kick",
                 "steps": [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]},
                {"instrument": "hat",
                 "steps": [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0],
                 "params": {"open_": False}},
            ],
        }
        sched = Schedule.from_pattern_spec(spec)
        buf = render_groove(sched, self._rng())
        self.assertGreater(buf.peak(), 0)

    def test_probability_zero_silences(self):
        spec = {
            "bpm": 138.0,
            "length_bars": 1,
            "tracks": [
                {"instrument": "kick",
                 "steps": [1] * 16,
                 "probability": 0.0},
            ],
        }
        sched = Schedule.from_pattern_spec(spec)
        buf = render_groove(sched, self._rng())
        self.assertAlmostEqual(buf.peak(), 0.0)

    def test_probability_one_always_fires(self):
        spec = self._kick_spec(length_bars=1)
        sched = Schedule.from_pattern_spec(spec)
        buf = render_groove(sched, self._rng())
        self.assertGreater(buf.peak(), 0)


# ---------------------------------------------------------------------------
# Loop rendering

class TestRenderLoop(unittest.TestCase):
    def test_render_loop_returns_buffer(self):
        spec = {
            "bpm": 138.0,
            "length_bars": 4,
            "tracks": [
                {"instrument": "kick",
                 "steps": [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]},
            ],
        }
        sched = Schedule.from_pattern_spec(spec)
        buf = render_loop(sched, RngContext(42))
        self.assertIsInstance(buf, AudioBuffer)
        self.assertGreater(buf.peak(), 0)

    def test_render_loop_seam_ok(self):
        # Kick pattern: many equal beats; after loop_fold the end-of-buffer
        # amplitude converges via the XF crossfade so the seam is below 0.5.
        spec = {
            "bpm": 138.0,
            "length_bars": 4,
            "tracks": [
                {"instrument": "kick",
                 "steps": [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]},
            ],
        }
        sched = Schedule.from_pattern_spec(spec)
        buf = render_loop(sched, RngContext(42), xf_bars=2.0)
        seam = check_seam(buf)
        # kick decays quickly so start/end are both near-zero after the XF
        self.assertLess(seam["discontinuity"], 0.5)


# ---------------------------------------------------------------------------
# render_pattern_spec (top-level, used by control)

class TestRenderPatternSpec(unittest.TestCase):
    def test_basic_spec(self):
        spec = {
            "bpm": 138.0,
            "length_bars": 2,
            "tracks": [
                {"instrument": "kick",
                 "steps": [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]},
            ],
        }
        buf = render_pattern_spec(spec, seed=0)
        self.assertIsInstance(buf, AudioBuffer)
        self.assertGreater(buf.peak(), 0)

    def test_loop_flag(self):
        spec = {
            "bpm": 138.0,
            "length_bars": 4,
            "loop": True,
            "xf_bars": 1.0,
            "tracks": [
                {"instrument": "kick",
                 "steps": [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]},
            ],
        }
        buf = render_pattern_spec(spec, seed=0)
        self.assertIsInstance(buf, AudioBuffer)

    def test_deterministic(self):
        spec = {
            "bpm": 138.0,
            "length_bars": 2,
            "tracks": [
                {"instrument": "kick",
                 "steps": [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
                 "probability": 0.7},
            ],
        }
        buf1 = render_pattern_spec(spec, seed=99)
        buf2 = render_pattern_spec(spec, seed=99)
        np.testing.assert_array_equal(buf1.data, buf2.data)


# ---------------------------------------------------------------------------
# control.render_pattern wiring

class TestControlPhase4(unittest.TestCase):
    def test_render_pattern_returns_buffer(self):
        from forge import control
        spec = {
            "bpm": 138.0,
            "length_bars": 2,
            "tracks": [
                {"instrument": "kick",
                 "steps": [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]},
            ],
        }
        buf = control.render_pattern(spec, seed=0)
        self.assertIsInstance(buf, AudioBuffer)
        self.assertGreater(buf.peak(), 0)

    def test_render_pattern_deterministic(self):
        from forge import control
        spec = {
            "bpm": 138.0,
            "length_bars": 2,
            "tracks": [
                {"instrument": "hat",
                 "steps": [1] * 16,
                 "params": {"open_": False}},
            ],
        }
        buf1 = control.render_pattern(spec, seed=7)
        buf2 = control.render_pattern(spec, seed=7)
        np.testing.assert_array_equal(buf1.data, buf2.data)

    def test_render_pattern_unknown_instrument_raises(self):
        from forge import control
        spec = {
            "bpm": 138.0,
            "length_bars": 1,
            "tracks": [
                {"instrument": "no_such_instrument",
                 "steps": [1] + [0] * 15},
            ],
        }
        with self.assertRaises(KeyError):
            control.render_pattern(spec, seed=0)


if __name__ == "__main__":
    unittest.main()
