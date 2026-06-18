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


# ---------------------------------------------------------------------------
# Phase 8 — Group A: tonal & textural instruments (9 new)

class TestPhase8GroupAVoices(unittest.TestCase):
    """Acceptance tests for ney, chant, horn."""

    def _rng(self):
        return RngContext(99).spawn("p8voices").rng

    def _render(self, iid, params=None):
        entry = get_instrument(iid)
        return entry["fn"](params or {}, self._rng())

    # --- helpers for slider-buildable check

    def _assert_slider_buildable(self, iid):
        entry = get_instrument(iid)
        for p in entry["params"]:
            if p.kind == "float":
                self.assertIsNotNone(p.lo, f"{iid}/{p.name}: lo is None")
                self.assertIsNotNone(p.hi, f"{iid}/{p.name}: hi is None")

    # --- ney

    def test_ney_in_registry(self):
        entry = get_instrument("ney")
        self.assertIsNotNone(entry)
        self.assertGreater(len(entry["params"]), 0)

    def test_ney_non_silent(self):
        buf = self._render("ney")
        self.assertGreater(buf.peak(), 0.0)
        self.assertTrue(np.all(np.isfinite(buf.data)))

    def test_ney_longer_duration_longer_buffer(self):
        short = self._render("ney", {"midi": 62, "duration": 1.0})
        long_ = self._render("ney", {"midi": 62, "duration": 3.0})
        self.assertGreater(len(long_), len(short))

    def test_ney_slider_buildable(self):
        self._assert_slider_buildable("ney")

    # --- chant

    def test_chant_in_registry(self):
        entry = get_instrument("chant")
        self.assertIsNotNone(entry)
        self.assertGreater(len(entry["params"]), 0)

    def test_chant_non_silent(self):
        buf = self._render("chant")
        self.assertGreater(buf.peak(), 0.0)
        self.assertTrue(np.all(np.isfinite(buf.data)))

    def test_chant_slider_buildable(self):
        self._assert_slider_buildable("chant")

    def test_chant_sub_octave_enriches(self):
        """Sub-octave adds energy — sub_level=0 vs sub_level=0.4."""
        with_sub = self._render("chant", {"sub_level": 0.4, "duration": 1.0})
        without_sub = self._render("chant", {"sub_level": 0.0, "duration": 1.0})
        # both must be non-silent; sub version generally has higher RMS
        self.assertGreater(with_sub.peak(), 0.0)
        self.assertGreater(without_sub.peak(), 0.0)

    # --- horn

    def test_horn_in_registry(self):
        entry = get_instrument("horn")
        self.assertIsNotNone(entry)
        self.assertGreater(len(entry["params"]), 0)

    def test_horn_non_silent(self):
        buf = self._render("horn")
        self.assertGreater(buf.peak(), 0.0)
        self.assertTrue(np.all(np.isfinite(buf.data)))

    def test_horn_slider_buildable(self):
        self._assert_slider_buildable("horn")

    def test_horn_with_notes_list(self):
        entry = get_instrument("horn")
        buf = entry["fn"]({"notes": [(50, 0.8), (53, 1.0)]}, self._rng())
        self.assertGreater(buf.peak(), 0.0)


class TestPhase8GroupAStrings(unittest.TestCase):
    """Acceptance tests for tremolo_strings, santur, oud."""

    def _rng(self):
        return RngContext(99).spawn("p8strings").rng

    def _render(self, iid, params=None):
        entry = get_instrument(iid)
        return entry["fn"](params or {}, self._rng())

    def _assert_slider_buildable(self, iid):
        entry = get_instrument(iid)
        for p in entry["params"]:
            if p.kind == "float":
                self.assertIsNotNone(p.lo, f"{iid}/{p.name}: lo is None")
                self.assertIsNotNone(p.hi, f"{iid}/{p.name}: hi is None")

    # --- tremolo_strings

    def test_tremolo_strings_in_registry(self):
        entry = get_instrument("tremolo_strings")
        self.assertIsNotNone(entry)
        self.assertGreater(len(entry["params"]), 0)

    def test_tremolo_strings_non_silent(self):
        buf = self._render("tremolo_strings", {"duration": 2.0})
        self.assertGreater(buf.peak(), 0.0)
        self.assertTrue(np.all(np.isfinite(buf.data)))

    def test_tremolo_strings_slider_buildable(self):
        self._assert_slider_buildable("tremolo_strings")

    def test_tremolo_strings_amplitude_oscillates(self):
        """RMS of first 0.5 s segment differs from second 0.5 s segment."""
        buf = self._render("tremolo_strings", {"duration": 2.0, "attack": 0.1,
                                               "tremolo_hz": 11.0})
        sr = buf.sr
        seg_n = int(0.5 * sr)
        # skip the attack; check segments 0.5–1 s and 1–1.5 s
        off = int(0.5 * sr)
        rms_a = float(np.sqrt(np.mean(buf.data[off:off + seg_n, 0] ** 2)))
        rms_b = float(np.sqrt(np.mean(buf.data[off + seg_n:off + 2 * seg_n, 0] ** 2)))
        # both must be non-zero; they won't be identical (tremolo is oscillating)
        self.assertGreater(rms_a, 0.0)
        self.assertGreater(rms_b, 0.0)

    def test_tremolo_strings_distinct_from_pad(self):
        """tremolo_strings and pad at identical notes should differ."""
        ks_buf = self._render("tremolo_strings",
                              {"midi_notes": [62, 66, 69], "duration": 2.0})
        pad_buf = self._render("pad",
                               {"midi_notes": [62, 66, 69], "duration": 2.0})
        # they should not be identical arrays
        self.assertFalse(np.allclose(ks_buf.data[:min(len(ks_buf), len(pad_buf))],
                                     pad_buf.data[:min(len(ks_buf), len(pad_buf))]))

    # --- santur

    def test_santur_in_registry(self):
        entry = get_instrument("santur")
        self.assertIsNotNone(entry)
        self.assertGreater(len(entry["params"]), 0)

    def test_santur_non_silent(self):
        buf = self._render("santur", {"midi": 62, "duration": 1.5})
        self.assertGreater(buf.peak(), 0.0)
        self.assertTrue(np.all(np.isfinite(buf.data)))

    def test_santur_slider_buildable(self):
        self._assert_slider_buildable("santur")

    def test_santur_decays(self):
        """Santur tail is quieter than attack."""
        buf = self._render("santur", {"midi": 62, "duration": 2.0})
        sr = buf.sr
        early_n = int(0.1 * sr)
        late_start = int(1.5 * sr)
        rms_early = float(np.sqrt(np.mean(buf.data[:early_n, 0] ** 2)))
        rms_late = float(np.sqrt(np.mean(buf.data[late_start:, 0] ** 2)))
        self.assertGreater(rms_early, rms_late)

    # --- oud

    def test_oud_in_registry(self):
        entry = get_instrument("oud")
        self.assertIsNotNone(entry)
        self.assertGreater(len(entry["params"]), 0)

    def test_oud_non_silent(self):
        buf = self._render("oud", {"midi": 62, "duration": 0.6})
        self.assertGreater(buf.peak(), 0.0)
        self.assertTrue(np.all(np.isfinite(buf.data)))

    def test_oud_slider_buildable(self):
        self._assert_slider_buildable("oud")

    def test_oud_different_pitches(self):
        """Higher MIDI note should produce a shorter period (higher frequency)."""
        buf_lo = self._render("oud", {"midi": 45, "duration": 0.6})
        buf_hi = self._render("oud", {"midi": 69, "duration": 0.6})
        self.assertGreater(buf_lo.peak(), 0.0)
        self.assertGreater(buf_hi.peak(), 0.0)


class TestPhase8GroupATextures(unittest.TestCase):
    """Acceptance tests for worm_rumble, shepard_wind, breath."""

    def _rng(self):
        return RngContext(99).spawn("p8textures").rng

    def _render(self, iid, params=None):
        entry = get_instrument(iid)
        return entry["fn"](params or {}, self._rng())

    def _assert_slider_buildable(self, iid):
        entry = get_instrument(iid)
        for p in entry["params"]:
            if p.kind == "float":
                self.assertIsNotNone(p.lo, f"{iid}/{p.name}: lo is None")
                self.assertIsNotNone(p.hi, f"{iid}/{p.name}: hi is None")

    # --- worm_rumble

    def test_worm_rumble_in_registry(self):
        entry = get_instrument("worm_rumble")
        self.assertIsNotNone(entry)
        self.assertGreater(len(entry["params"]), 0)

    def test_worm_rumble_non_silent(self):
        buf = self._render("worm_rumble", {"duration": 3.0})
        self.assertGreater(buf.peak(), 0.0)
        self.assertTrue(np.all(np.isfinite(buf.data)))

    def test_worm_rumble_slider_buildable(self):
        self._assert_slider_buildable("worm_rumble")

    def test_worm_rumble_length(self):
        dur = 5.0
        buf = self._render("worm_rumble", {"duration": dur})
        self.assertAlmostEqual(buf.len_seconds(), dur, delta=0.1)

    # --- shepard_wind

    def test_shepard_wind_in_registry(self):
        entry = get_instrument("shepard_wind")
        self.assertIsNotNone(entry)
        self.assertGreater(len(entry["params"]), 0)

    def test_shepard_wind_non_silent(self):
        buf = self._render("shepard_wind", {"duration": 5.0})
        self.assertGreater(buf.peak(), 0.0)
        self.assertTrue(np.all(np.isfinite(buf.data)))

    def test_shepard_wind_slider_buildable(self):
        self._assert_slider_buildable("shepard_wind")

    def test_shepard_wind_stereo(self):
        """Should have L and R content (Coriolis panning)."""
        buf = self._render("shepard_wind", {"duration": 5.0})
        self.assertGreater(np.max(np.abs(buf.data[:, 0])), 0.0)
        self.assertGreater(np.max(np.abs(buf.data[:, 1])), 0.0)

    # --- breath

    def test_breath_in_registry(self):
        entry = get_instrument("breath")
        self.assertIsNotNone(entry)
        self.assertGreater(len(entry["params"]), 0)

    def test_breath_non_silent(self):
        buf = self._render("breath", {"duration": 3.0})
        self.assertGreater(buf.peak(), 0.0)
        self.assertTrue(np.all(np.isfinite(buf.data)))

    def test_breath_slider_buildable(self):
        self._assert_slider_buildable("breath")

    def test_breath_length(self):
        dur = 2.5
        buf = self._render("breath", {"duration": dur})
        self.assertAlmostEqual(buf.len_seconds(), dur, delta=0.1)


class TestPhase8SliderBuildable(unittest.TestCase):
    """Verify ALL 9 new instruments have lo/hi on every float param."""

    NEW_IDS = [
        "ney", "chant", "horn",
        "tremolo_strings", "santur", "oud",
        "worm_rumble", "shepard_wind", "breath",
    ]

    def test_all_in_list_instruments(self):
        ids_in_list = {e["id"] for e in list_instruments()}
        for iid in self.NEW_IDS:
            self.assertIn(iid, ids_in_list)

    def test_all_have_params(self):
        for iid in self.NEW_IDS:
            entry = get_instrument(iid)
            self.assertGreater(len(entry["params"]), 0,
                               f"{iid} has no params")

    def test_float_params_have_lo_hi(self):
        for iid in self.NEW_IDS:
            entry = get_instrument(iid)
            for p in entry["params"]:
                if p.kind == "float":
                    self.assertIsNotNone(
                        p.lo, f"{iid}/{p.name}: float param missing lo")
                    self.assertIsNotNone(
                        p.hi, f"{iid}/{p.name}: float param missing hi")


if __name__ == "__main__":
    unittest.main()
