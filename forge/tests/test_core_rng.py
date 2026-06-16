"""Tests for forge.core.rng.RngContext."""

import unittest

import numpy as np

from forge.core.rng import RngContext, _key_to_int


class TestKeyToInt(unittest.TestCase):
    def test_deterministic(self):
        """Same string → same integer, always (no hash randomization)."""
        self.assertEqual(_key_to_int("kick"), _key_to_int("kick"))
        self.assertEqual(_key_to_int("piano"), _key_to_int("piano"))

    def test_different_keys_differ(self):
        self.assertNotEqual(_key_to_int("kick"), _key_to_int("piano"))
        self.assertNotEqual(_key_to_int("a"), _key_to_int("b"))

    def test_returns_uint32_range(self):
        for key in ("", "x", "midi_to_hz", "forge/core/rng"):
            v = _key_to_int(key)
            self.assertGreaterEqual(v, 0)
            self.assertLess(v, 2**32)


class TestRngContextDeterminism(unittest.TestCase):
    def test_same_seed_same_draws(self):
        ctx1 = RngContext(42)
        ctx2 = RngContext(42)
        a = ctx1.rng.standard_normal(100)
        b = ctx2.rng.standard_normal(100)
        np.testing.assert_array_equal(a, b)

    def test_different_seed_different_draws(self):
        ctx1 = RngContext(42)
        ctx2 = RngContext(43)
        a = ctx1.rng.standard_normal(100)
        b = ctx2.rng.standard_normal(100)
        self.assertFalse(np.array_equal(a, b))

    def test_seed_property(self):
        ctx = RngContext(99)
        self.assertEqual(ctx.seed, 99)


class TestRngContextSpawn(unittest.TestCase):
    def test_child_deterministic(self):
        """spawn with the same key always produces the same child stream."""
        a = RngContext(42).spawn("kick").rng.standard_normal(50)
        b = RngContext(42).spawn("kick").rng.standard_normal(50)
        np.testing.assert_array_equal(a, b)

    def test_children_independent_from_each_other(self):
        ctx = RngContext(42)
        kick_a = ctx.spawn("kick").rng.standard_normal(50)
        piano_a = ctx.spawn("piano").rng.standard_normal(50)
        self.assertFalse(np.array_equal(kick_a, piano_a))

    def test_child_independent_from_parent(self):
        """Spawning a child does not affect the parent's own generator stream."""
        ctx1 = RngContext(42)
        _ = ctx1.spawn("something")
        a = ctx1.rng.standard_normal(50)

        ctx2 = RngContext(42)
        b = ctx2.rng.standard_normal(50)

        np.testing.assert_array_equal(a, b)

    def test_grandchild(self):
        """Multi-level spawning is deterministic."""
        a = RngContext(42).spawn("layer1").spawn("sublayer").rng.standard_normal(20)
        b = RngContext(42).spawn("layer1").spawn("sublayer").rng.standard_normal(20)
        np.testing.assert_array_equal(a, b)

    def test_sibling_order_independence(self):
        """Spawning siblings in different orders gives the same per-sibling stream."""
        ctx1 = RngContext(42)
        kick_first = ctx1.spawn("kick").rng.standard_normal(30)
        piano_first = ctx1.spawn("piano").rng.standard_normal(30)

        ctx2 = RngContext(42)
        piano_second = ctx2.spawn("piano").rng.standard_normal(30)
        kick_second = ctx2.spawn("kick").rng.standard_normal(30)

        np.testing.assert_array_equal(kick_first, kick_second)
        np.testing.assert_array_equal(piano_first, piano_second)

    def test_same_key_twice_returns_independent_same_seed_contexts(self):
        """Spawning with the same key twice gives two equally-seeded but separate objects."""
        ctx = RngContext(42)
        c1 = ctx.spawn("layer")
        c2 = ctx.spawn("layer")
        # They produce the same sequence from their own rng
        a = c1.rng.standard_normal(20)
        b = c2.rng.standard_normal(20)
        np.testing.assert_array_equal(a, b)
        # But they are separate objects
        self.assertIsNot(c1, c2)


class TestRngContextFresh(unittest.TestCase):
    def test_fresh_reproduces_same_stream(self):
        ctx = RngContext(42)
        _ = ctx.rng.standard_normal(10)  # consume some draws
        refreshed = ctx.fresh()
        # fresh returns a NEW context with the same seed path
        a = refreshed.rng.standard_normal(50)
        b = RngContext(42).rng.standard_normal(50)
        np.testing.assert_array_equal(a, b)


class TestRngContextIrSeeds(unittest.TestCase):
    """Verify the IR-seed pattern used in all legacy scripts maps naturally."""

    def test_ir_seeds_independent(self):
        """IR L and IR R seeds must be independent."""
        ctx = RngContext(1965)  # arrakis seed
        ir_L = ctx.spawn("ir_L").rng.standard_normal(100)
        ir_R = ctx.spawn("ir_R").rng.standard_normal(100)
        self.assertFalse(np.array_equal(ir_L, ir_R))

    def test_ir_deterministic_across_contexts(self):
        ir_L_1 = RngContext(1965).spawn("ir_L").rng.standard_normal(100)
        ir_L_2 = RngContext(1965).spawn("ir_L").rng.standard_normal(100)
        np.testing.assert_array_equal(ir_L_1, ir_L_2)


if __name__ == "__main__":
    unittest.main()
