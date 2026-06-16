"""Phase 3 tests: instrument base, registry, and representative instruments."""

import unittest

import numpy as np

from forge.core.buffer import AudioBuffer
from forge.core.rng import RngContext
from forge.instruments.base import ParamSchema, RenderCache, _freeze_params, render_cached
from forge.instruments.registry import REGISTRY, get_instrument, list_instruments


# ---------------------------------------------------------------------------
# ParamSchema

class TestParamSchema(unittest.TestCase):
    def test_to_dict_has_required_keys(self):
        p = ParamSchema("freq", "float", 440.0, lo=20.0, hi=20000.0, unit="Hz")
        d = p.to_dict()
        for key in ("name", "kind", "default", "lo", "hi", "label", "unit"):
            self.assertIn(key, d)

    def test_default_label_is_name(self):
        p = ParamSchema("drive", "float", 1.0)
        self.assertEqual(p.label, "drive")

    def test_custom_label(self):
        p = ParamSchema("x", "float", 0.0, label="My Param")
        self.assertEqual(p.label, "My Param")


# ---------------------------------------------------------------------------
# RenderCache

class TestRenderCache(unittest.TestCase):
    def setUp(self):
        self.cache = RenderCache()

    def test_miss_returns_none(self):
        self.assertIsNone(self.cache.get("kick", {"f0": 55.0}))

    def test_store_and_retrieve(self):
        buf = AudioBuffer(100)
        self.cache.put("kick", {"f0": 55.0}, buf)
        self.assertIs(self.cache.get("kick", {"f0": 55.0}), buf)

    def test_different_params_different_entries(self):
        buf1 = AudioBuffer(100)
        buf2 = AudioBuffer(200)
        self.cache.put("kick", {"f0": 55.0}, buf1)
        self.cache.put("kick", {"f0": 60.0}, buf2)
        self.assertIs(self.cache.get("kick", {"f0": 55.0}), buf1)
        self.assertIs(self.cache.get("kick", {"f0": 60.0}), buf2)

    def test_invalidate_one(self):
        self.cache.put("kick", {"f0": 55.0}, AudioBuffer(100))
        self.cache.put("hat", {"open_": False}, AudioBuffer(50))
        self.cache.invalidate("kick")
        self.assertIsNone(self.cache.get("kick", {"f0": 55.0}))
        self.assertIsNotNone(self.cache.get("hat", {"open_": False}))

    def test_invalidate_all(self):
        self.cache.put("kick", {}, AudioBuffer(100))
        self.cache.put("hat", {}, AudioBuffer(50))
        self.cache.invalidate()
        self.assertEqual(len(self.cache), 0)

    def test_freeze_params_deterministic(self):
        a = _freeze_params({"f0": 55.0, "drive": 1.5})
        b = _freeze_params({"drive": 1.5, "f0": 55.0})
        self.assertEqual(a, b)

    def test_render_cached_uses_cache(self):
        call_count = [0]

        def fake_instrument(params, rng, **ctx):
            call_count[0] += 1
            return AudioBuffer(100)

        cache = RenderCache()
        rng = np.random.default_rng(0)
        p = {"f0": 55.0}
        render_cached("fake", fake_instrument, p, rng, cache=cache)
        render_cached("fake", fake_instrument, p, rng, cache=cache)
        self.assertEqual(call_count[0], 1)  # only rendered once

    def test_render_cached_different_params_renders_again(self):
        call_count = [0]

        def fake_instrument(params, rng, **ctx):
            call_count[0] += 1
            return AudioBuffer(100)

        cache = RenderCache()
        rng = np.random.default_rng(0)
        render_cached("fake", fake_instrument, {"f0": 55.0}, rng, cache=cache)
        render_cached("fake", fake_instrument, {"f0": 60.0}, rng, cache=cache)
        self.assertEqual(call_count[0], 2)


# ---------------------------------------------------------------------------
# Registry

class TestRegistry(unittest.TestCase):
    def test_all_families_present(self):
        families = {e["family"] for e in REGISTRY.values()}
        for f in ("texture", "percussion", "strings", "voice", "bass", "fx"):
            self.assertIn(f, families)

    def test_all_entries_have_required_keys(self):
        for iid, entry in REGISTRY.items():
            self.assertIn("fn", entry, f"{iid} missing 'fn'")
            self.assertIn("params", entry, f"{iid} missing 'params'")
            self.assertIn("family", entry, f"{iid} missing 'family'")

    def test_get_instrument_known(self):
        entry = get_instrument("kick")
        self.assertIn("fn", entry)

    def test_get_instrument_unknown_raises(self):
        with self.assertRaises(KeyError):
            get_instrument("nonexistent_instrument_xyz")

    def test_list_instruments_returns_list(self):
        result = list_instruments()
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 5)

    def test_list_instruments_entries_have_params(self):
        for entry in list_instruments():
            self.assertIn("id", entry)
            self.assertIn("family", entry)
            self.assertIn("params", entry)
            self.assertIsInstance(entry["params"], list)


# ---------------------------------------------------------------------------
# Percussion instruments

class TestPercussion(unittest.TestCase):
    def _rng(self):
        return RngContext(42).spawn("test").rng

    def _render(self, iid, params=None):
        entry = get_instrument(iid)
        return entry["fn"](params or {}, self._rng())

    def test_doum_returns_buffer(self):
        buf = self._render("doum")
        self.assertIsInstance(buf, AudioBuffer)
        self.assertGreater(len(buf), 0)
        self.assertGreater(buf.peak(), 0)

    def test_tek_returns_buffer(self):
        self.assertGreater(self._render("tek").peak(), 0)

    def test_tek_ghost_lower_than_normal(self):
        normal = self._render("tek", {"ghost": False})
        ghost = self._render("tek", {"ghost": True})
        self.assertLess(ghost.peak(), normal.peak())

    def test_kick_returns_buffer(self):
        self.assertGreater(self._render("kick").peak(), 0)

    def test_hat_closed(self):
        self.assertGreater(self._render("hat", {"open_": False}).peak(), 0)

    def test_hat_open_longer_than_closed(self):
        closed = self._render("hat", {"open_": False})
        open_ = self._render("hat", {"open_": True})
        self.assertGreater(len(open_), len(closed))

    def test_clap_returns_buffer(self):
        self.assertGreater(self._render("clap").peak(), 0)

    def test_snare_returns_buffer(self):
        self.assertGreater(self._render("snare").peak(), 0)

    def test_war_drum_returns_buffer(self):
        self.assertGreater(self._render("war_drum").peak(), 0)

    def test_frame_hit_returns_buffer(self):
        self.assertGreater(self._render("frame_hit").peak(), 0)


# ---------------------------------------------------------------------------
# Strings

class TestStrings(unittest.TestCase):
    def _rng(self):
        return RngContext(42).spawn("strings").rng

    def test_harp_returns_buffer(self):
        entry = get_instrument("harp")
        buf = entry["fn"]({"midi": 62, "duration": 1.0}, self._rng())
        self.assertGreater(buf.peak(), 0)

    def test_piano_returns_buffer(self):
        entry = get_instrument("piano")
        buf = entry["fn"]({"midi": 62, "duration": 1.0}, self._rng())
        self.assertGreater(buf.peak(), 0)

    def test_cello_returns_buffer(self):
        entry = get_instrument("cello")
        buf = entry["fn"]({"notes": [(62, 1.0)], "lp_cutoff": 1900.0}, self._rng())
        self.assertGreater(buf.peak(), 0)

    def test_pad_stereo(self):
        entry = get_instrument("pad")
        buf = entry["fn"]({"midi_notes": [62, 66, 69], "duration": 2.0}, self._rng())
        self.assertIsInstance(buf, AudioBuffer)


# ---------------------------------------------------------------------------
# Textures

class TestTextures(unittest.TestCase):
    def _rng(self):
        return RngContext(42).spawn("textures").rng

    def _render(self, iid, params):
        entry = get_instrument(iid)
        return entry["fn"](params, self._rng())

    def test_wind_length(self):
        dur = 2.0
        buf = self._render("wind", {"duration": dur})
        self.assertAlmostEqual(buf.len_seconds(), dur, delta=0.1)

    def test_drone_length(self):
        dur = 3.0
        buf = self._render("drone", {"duration": dur})
        self.assertAlmostEqual(buf.len_seconds(), dur, delta=0.1)

    def test_wind_has_signal(self):
        self.assertGreater(self._render("wind", {"duration": 1.0}).peak(), 0)

    def test_drone_has_signal(self):
        self.assertGreater(self._render("drone", {"duration": 1.0}).peak(), 0)


# ---------------------------------------------------------------------------
# Bass

class TestBass(unittest.TestCase):
    def _rng(self):
        return RngContext(42).spawn("bass").rng

    def test_bass_note(self):
        entry = get_instrument("bass")
        buf = entry["fn"]({"midi": 38, "duration": 0.46}, self._rng())
        self.assertGreater(buf.peak(), 0)

    def test_psy_bass(self):
        entry = get_instrument("psy_bass")
        buf = entry["fn"]({"midi": 26, "duration": 0.42}, self._rng())
        self.assertGreater(buf.peak(), 0)

    def test_acid(self):
        entry = get_instrument("acid")
        buf = entry["fn"]({"midi": 38, "cutoff": 800.0, "duration": 0.22}, self._rng())
        self.assertGreater(buf.peak(), 0)


# ---------------------------------------------------------------------------
# FX

class TestFx(unittest.TestCase):
    def _rng(self):
        return RngContext(42).spawn("fx").rng

    def test_zap(self):
        entry = get_instrument("zap")
        buf = entry["fn"]({}, self._rng())
        self.assertGreater(buf.peak(), 0)

    def test_riser_length(self):
        entry = get_instrument("riser")
        dur = 2.0
        buf = entry["fn"]({"duration": dur}, self._rng())
        self.assertAlmostEqual(buf.len_seconds(), dur, delta=0.05)

    def test_explosion(self):
        entry = get_instrument("explosion")
        buf = entry["fn"]({}, self._rng())
        self.assertGreater(buf.peak(), 0)

    def test_heart_has_beats(self):
        entry = get_instrument("heart")
        buf = entry["fn"]({"duration": 5.0, "bpm": 60.0}, self._rng())
        self.assertGreater(buf.peak(), 0)


# ---------------------------------------------------------------------------
# Voices

class TestVoices(unittest.TestCase):
    def _rng(self):
        return RngContext(42).spawn("voices").rng

    def test_voice_phrase(self):
        entry = get_instrument("voice")
        buf = entry["fn"]({"notes": [(62, 1.0), (65, 1.0)]}, self._rng())
        self.assertGreater(buf.peak(), 0)

    def test_lead_phrase(self):
        entry = get_instrument("lead")
        buf = entry["fn"]({"notes": [(62, 0.5), (65, 0.5)]}, self._rng())
        self.assertGreater(buf.peak(), 0)


# ---------------------------------------------------------------------------
# control.py Phase 3 wiring

class TestControlPhase3(unittest.TestCase):
    def test_list_instruments(self):
        from forge import control
        result = control.list_instruments()
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 5)

    def test_render_instrument(self):
        from forge import control
        buf = control.render_instrument("kick", {"f0": 55.0, "duration": 0.3}, seed=0)
        self.assertIsInstance(buf, AudioBuffer)
        self.assertGreater(buf.peak(), 0)

    def test_render_instrument_deterministic(self):
        from forge import control
        buf1 = control.render_instrument("harp", {"midi": 62, "duration": 1.0}, seed=42)
        buf2 = control.render_instrument("harp", {"midi": 62, "duration": 1.0}, seed=42)
        np.testing.assert_array_equal(buf1.data, buf2.data)

    def test_render_instrument_unknown_raises(self):
        from forge import control
        with self.assertRaises(KeyError):
            control.render_instrument("does_not_exist", {})


if __name__ == "__main__":
    unittest.main()
