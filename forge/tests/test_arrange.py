"""Phase 5 tests: sections, curves, transitions, track orchestration."""

import unittest
from pathlib import Path
import tempfile

import numpy as np

from forge.arrange.curves import (
    Curve,
    constant,
    fade_in,
    fade_in_out,
    fade_out,
    sidechain_pump,
)
from forge.arrange.section import Section
from forge.arrange.track import Track
from forge.arrange.transitions import crossfade, hard_cut, insert_riser
from forge.core.buffer import AudioBuffer
from forge.core.grid import Grid
from forge.core.rng import RngContext
from forge.patterns.schedule import Schedule


# ---------------------------------------------------------------------------
# Curves

class TestCurve(unittest.TestCase):
    def test_at_anchors(self):
        c = Curve([(0.0, 0.0), (4.0, 1.0)])
        self.assertAlmostEqual(c.at(0.0), 0.0)
        self.assertAlmostEqual(c.at(4.0), 1.0)

    def test_at_midpoint(self):
        c = Curve([(0.0, 0.0), (4.0, 1.0)])
        self.assertAlmostEqual(c.at(2.0), 0.5)

    def test_at_clamps_below(self):
        c = Curve([(2.0, 0.5), (4.0, 1.0)])
        self.assertAlmostEqual(c.at(0.0), 0.5)

    def test_at_clamps_above(self):
        c = Curve([(0.0, 0.0), (4.0, 1.0)])
        self.assertAlmostEqual(c.at(8.0), 1.0)

    def test_sample_length(self):
        c = Curve([(0.0, 0.0), (4.0, 1.0)])
        samples = c.sample(1000, bpm=138.0)
        self.assertEqual(len(samples), 1000)

    def test_sample_monotone_rising(self):
        c = fade_in(4.0)
        samples = c.sample(44100, bpm=138.0)
        self.assertLess(samples[0], samples[-1])

    def test_constant_factory(self):
        c = constant(0.7)
        self.assertAlmostEqual(c.at(0.0), 0.7)
        self.assertAlmostEqual(c.at(0.5), 0.7)
        self.assertAlmostEqual(c.at(1.0), 0.7)

    def test_fade_in_out_holds(self):
        c = fade_in_out(8.0, ramp_bars=2.0)
        self.assertAlmostEqual(c.at(4.0), 1.0)

    def test_sidechain_pump_dips_on_beat(self):
        c = sidechain_pump(4.0, 138.0, depth=0.8)
        # Beat 0 = bar 0; the curve dips there
        self.assertLess(c.at(0.0), 0.5)

    def test_curve_needs_two_points(self):
        with self.assertRaises(ValueError):
            Curve([(0.0, 1.0)])

    def test_sample_values_in_range(self):
        c = fade_in_out(8.0, ramp_bars=2.0)
        s = c.sample(10000, bpm=138.0)
        self.assertGreaterEqual(s.min(), 0.0)
        self.assertLessEqual(s.max(), 1.0 + 1e-9)


# ---------------------------------------------------------------------------
# Transitions

class TestTransitions(unittest.TestCase):
    def _silence(self, n, val=0.0):
        buf = AudioBuffer(n)
        buf.data[:] = val
        return buf

    def test_crossfade_length(self):
        a = AudioBuffer(1000)
        b = AudioBuffer(800)
        out = crossfade(a, b, xf_samples=200)
        self.assertEqual(len(out), 1000 + 800 - 200)

    def test_crossfade_has_signal(self):
        a = AudioBuffer.from_mono(np.ones(1000))
        b = AudioBuffer.from_mono(np.ones(800))
        out = crossfade(a, b, xf_samples=200)
        self.assertGreater(out.peak(), 0)

    def test_hard_cut_length(self):
        a = AudioBuffer(1000)
        b = AudioBuffer(500)
        out = hard_cut(a, b)
        self.assertEqual(len(out), 1500)

    def test_hard_cut_at_sample(self):
        a = AudioBuffer(1000)
        b = AudioBuffer(500)
        out = hard_cut(a, b, cut_sample=400)
        self.assertEqual(len(out), 900)

    def test_insert_riser_modifies_buffer(self):
        n = int(44100 * 4.0)
        buf = AudioBuffer(n)
        rng_ctx = RngContext(42)
        before_peak = buf.peak()
        insert_riser(buf, bar=0, bpm=138.0, rng_ctx=rng_ctx, duration_bars=2.0)
        self.assertGreater(buf.peak(), before_peak)


# ---------------------------------------------------------------------------
# Section

class TestSection(unittest.TestCase):
    def _kick_schedule(self, bpm=138.0, length_bars=2):
        return Schedule.from_pattern_spec({
            "bpm": bpm,
            "length_bars": length_bars,
            "tracks": [
                {"instrument": "kick",
                 "steps": [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]},
            ],
        })

    def test_section_renders(self):
        sec = Section("intro", start_bar=0, length_bars=2)
        sec.add_schedule(self._kick_schedule())
        buf = sec.render(RngContext(42))
        self.assertIsInstance(buf, AudioBuffer)
        self.assertGreater(buf.peak(), 0)

    def test_section_length(self):
        sec = Section("intro", start_bar=0, length_bars=4)
        sec.add_schedule(self._kick_schedule(length_bars=4))
        buf = sec.render(RngContext(42))
        grid = Grid(138.0)
        expected_s = grid.bar * 4
        self.assertAlmostEqual(buf.len_seconds(), expected_s, delta=0.02)

    def test_section_gain(self):
        sec_full = Section("full", start_bar=0, length_bars=2, gain=1.0)
        sec_half = Section("half", start_bar=0, length_bars=2, gain=0.5)
        for sec in (sec_full, sec_half):
            sec.add_schedule(self._kick_schedule())
        buf_full = sec_full.render(RngContext(99))
        buf_half = sec_half.render(RngContext(99))
        self.assertAlmostEqual(buf_half.peak(), buf_full.peak() * 0.5, delta=0.01)

    def test_section_end_bar(self):
        sec = Section("bridge", start_bar=8, length_bars=4)
        self.assertEqual(sec.end_bar, 12)

    def test_section_no_schedule_raises(self):
        sec = Section("empty", start_bar=0, length_bars=2)
        with self.assertRaises(RuntimeError):
            sec.render(RngContext(0))

    def test_section_deterministic(self):
        sec1 = Section("s", start_bar=0, length_bars=2)
        sec2 = Section("s", start_bar=0, length_bars=2)
        for sec in (sec1, sec2):
            sec.add_schedule(self._kick_schedule())
        buf1 = sec1.render(RngContext(7))
        buf2 = sec2.render(RngContext(7))
        np.testing.assert_array_equal(buf1.data, buf2.data)


# ---------------------------------------------------------------------------
# Track

class TestTrack(unittest.TestCase):
    def _minimal_track(self, seed=0):
        bpm = 138.0
        track = Track(bpm, title="test_track")
        sched = Schedule.from_pattern_spec({
            "bpm": bpm,
            "length_bars": 4,
            "tracks": [
                {"instrument": "kick",
                 "steps": [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]},
            ],
        })
        sec = Section("main", start_bar=0, length_bars=4)
        sec.add_schedule(sched)
        track.add_section(sec)
        return track

    def test_render_returns_buffer(self):
        buf = self._minimal_track().render(seed=0)
        self.assertIsInstance(buf, AudioBuffer)
        self.assertGreater(buf.peak(), 0)

    def test_total_bars(self):
        t = self._minimal_track()
        self.assertEqual(t.total_bars(), 4)

    def test_two_sections_sum(self):
        bpm = 138.0
        track = Track(bpm, title="two_sec")
        for name, bar in (("intro", 0), ("drop", 4)):
            sched = Schedule.from_pattern_spec({
                "bpm": bpm,
                "length_bars": 4,
                "tracks": [
                    {"instrument": "kick",
                     "steps": [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]},
                ],
            })
            sec = Section(name, start_bar=bar, length_bars=4)
            sec.add_schedule(sched)
            track.add_section(sec)
        buf = track.render(seed=0)
        grid = Grid(bpm)
        self.assertAlmostEqual(buf.len_seconds(), grid.bar * 8, delta=0.05)

    def test_render_deterministic(self):
        t1 = self._minimal_track()
        t2 = self._minimal_track()
        buf1 = t1.render(seed=42)
        buf2 = t2.render(seed=42)
        np.testing.assert_array_equal(buf1.data, buf2.data)

    def test_master_gain_curve_applied(self):
        from forge.arrange.curves import fade_in
        track = self._minimal_track()
        c = fade_in(4.0)
        track.set_master_gain_curve(c)
        buf = track.render(seed=0)
        # fade-in: first sample should be much quieter than peak
        first_amp = abs(float(buf.data[0, 0]))
        self.assertLess(first_amp, buf.peak() * 0.5)

    def test_invalid_bpm_raises(self):
        with self.assertRaises(ValueError):
            Track(bpm=0.0)

    def test_render_writes_wav(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "test.wav"
            self._minimal_track().render(seed=0, output_path=out_path)
            self.assertTrue(out_path.exists())
            self.assertGreater(out_path.stat().st_size, 1000)


# ---------------------------------------------------------------------------
# control.render_track wiring

class TestControlPhase5(unittest.TestCase):
    def _project(self):
        return {
            "title": "Control Test",
            "bpm": 138.0,
            "seed": 42,
            "sections": [
                {
                    "name": "main",
                    "start_bar": 0,
                    "length_bars": 4,
                    "schedules": [
                        {
                            "tracks": [
                                {"instrument": "kick",
                                 "steps": [1, 0, 0, 0, 1, 0, 0, 0,
                                           1, 0, 0, 0, 1, 0, 0, 0]},
                            ]
                        }
                    ],
                }
            ],
            "fade_out_s": 1.0,
        }

    def test_render_track_returns_buffer(self):
        from forge import control
        buf = control.render_track(self._project())
        self.assertIsInstance(buf, AudioBuffer)
        self.assertGreater(buf.peak(), 0)

    def test_render_track_deterministic(self):
        from forge import control
        p = self._project()
        buf1 = control.render_track(p)
        buf2 = control.render_track(p)
        np.testing.assert_array_equal(buf1.data, buf2.data)

    def test_render_track_with_curve(self):
        from forge import control
        p = self._project()
        p["master_gain_curve"] = [[0, 0.0], [2, 1.0], [4, 1.0]]
        buf = control.render_track(p)
        self.assertIsInstance(buf, AudioBuffer)

    def test_render_track_writes_wav(self):
        from forge import control
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "out.wav"
            control.render_track(self._project(), output_path=str(out))
            self.assertTrue(out.exists())


if __name__ == "__main__":
    unittest.main()
