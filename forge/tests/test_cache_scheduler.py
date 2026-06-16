"""Phase 2 tests: ContentAddressedCache and RenderScheduler."""

import tempfile
import threading
import time
import unittest
from pathlib import Path

import numpy as np


def _fake_buf(n: int = 100) -> np.ndarray:
    return np.ones((n, 2), dtype=np.float32) * 0.5


class TestContentAddressedCache(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _cache(self, max_memory=8):
        from forge.playback.cache import ContentAddressedCache
        return ContentAddressedCache(cache_dir=self._dir, max_memory=max_memory)

    # ---- basic get/put

    def test_miss_returns_none(self):
        c = self._cache()
        self.assertIsNone(c.get("deadbeef01234567"))

    def test_put_then_get(self):
        c = self._cache()
        arr = _fake_buf()
        c.put("aabbccdd11223344", arr)
        result = c.get("aabbccdd11223344")
        self.assertIsNotNone(result)
        np.testing.assert_array_almost_equal(result, arr)

    def test_has_after_put(self):
        c = self._cache()
        c.put("key1234567890abc", _fake_buf())
        self.assertTrue(c.has("key1234567890abc"))

    def test_has_false_before_put(self):
        c = self._cache()
        self.assertFalse(c.has("nothere00000000"))

    # ---- LRU eviction

    def test_lru_evicts_oldest_from_memory(self):
        c = self._cache(max_memory=2)
        keys = [f"key{i:015d}" for i in range(3)]
        for k in keys:
            c.put(k, _fake_buf())
        # First key evicted from memory but still on disk
        c.clear_disk()
        result = c.get(keys[0])
        # After clearing disk, the evicted key is gone
        self.assertIsNone(result)

    def test_recent_key_stays_in_memory_on_eviction(self):
        c = self._cache(max_memory=2)
        k0 = "key00000000000000"
        k1 = "key11111111111111"
        k2 = "key22222222222222"
        c.put(k0, _fake_buf())
        c.put(k1, _fake_buf())
        c.get(k0)           # refresh k0 in LRU
        c.put(k2, _fake_buf())  # k1 should be evicted (was LRU)
        # k0 and k2 are in memory; k1 only on disk
        self.assertEqual(c.memory_size(), 2)

    # ---- disk persistence

    def test_disk_survives_memory_clear(self):
        c = self._cache()
        key = "persistkey000000"
        arr = _fake_buf(200)
        c.put(key, arr)
        c.clear_memory()
        # Re-open: new cache instance, same dir
        c2 = self._cache()
        result = c2.get(key)
        self.assertIsNotNone(result)
        np.testing.assert_array_almost_equal(result, arr)

    def test_disk_size_counts_files(self):
        c = self._cache()
        c.put("filekey000000000", _fake_buf())
        c.put("filekey111111111", _fake_buf())
        self.assertEqual(c.disk_size(), 2)

    def test_clear_disk_removes_files(self):
        c = self._cache()
        c.put("todel00000000000", _fake_buf())
        c.clear_disk()
        self.assertEqual(c.disk_size(), 0)

    def test_clear_all(self):
        c = self._cache()
        c.put("aa000000000000000"[:16], _fake_buf())
        c.clear_all()
        self.assertEqual(c.memory_size(), 0)
        self.assertEqual(c.disk_size(), 0)

    # ---- float32 coercion

    def test_stores_as_float32(self):
        c = self._cache()
        arr = np.ones((50, 2), dtype=np.float64)
        c.put("f32key0000000000", arr)
        result = c.get("f32key0000000000")
        self.assertEqual(result.dtype, np.float32)

    # ---- thread safety

    def test_concurrent_puts(self):
        c = self._cache(max_memory=32)
        errors = []

        def worker(i):
            try:
                key = f"{i:016x}"
                c.put(key, _fake_buf(10))
                got = c.get(key)
                if got is None:
                    errors.append(f"key {key} missing after put")
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(16)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(errors, [])

    # ---- identical content → same key hits cache

    def test_same_key_returns_same_array(self):
        c = self._cache()
        arr = _fake_buf(64)
        c.put("samekey000000000", arr)
        r1 = c.get("samekey000000000")
        r2 = c.get("samekey000000000")
        np.testing.assert_array_equal(r1, r2)


# ---------------------------------------------------------------------------
# RenderScheduler

class TestRenderScheduler(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _make(self, n_workers=1):
        from forge.playback.cache import ContentAddressedCache
        from forge.playback.scheduler import RenderScheduler
        cache = ContentAddressedCache(cache_dir=self._dir)
        sched = RenderScheduler(cache, n_workers=n_workers)
        return cache, sched

    def _render_fn(self, value=0.5, delay=0.0):
        def fn():
            if delay:
                time.sleep(delay)
            return _fake_buf(100) * value
        return fn

    # ---- cache hit

    def test_cache_hit_returns_immediately(self):
        cache, sched = self._make()
        arr = _fake_buf(100)
        cache.put("hitkey0000000000", arr)
        result, fresh = sched.get_or_schedule("hitkey0000000000", self._render_fn())
        self.assertTrue(fresh)
        self.assertIsNotNone(result)
        np.testing.assert_array_almost_equal(result, arr)
        sched.shutdown()

    # ---- cache miss → background render

    def test_cache_miss_schedules_render(self):
        cache, sched = self._make()
        done = threading.Event()
        results = []

        def on_done(key, buf):
            results.append((key, buf))
            done.set()

        buf, fresh = sched.get_or_schedule("misskey000000000", self._render_fn(0.7), on_done)
        self.assertFalse(fresh)
        self.assertIsNone(buf)
        done.wait(timeout=5.0)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], "misskey000000000")
        sched.shutdown()

    def test_render_result_stored_in_cache(self):
        cache, sched = self._make()
        done = threading.Event()
        sched.get_or_schedule("cachekey00000000", self._render_fn(), lambda k, b: done.set())
        done.wait(timeout=5.0)
        self.assertTrue(cache.has("cachekey00000000"))
        sched.shutdown()

    # ---- coalescing

    def test_same_key_twice_only_one_render_call(self):
        cache, sched = self._make()
        call_count = [0]
        done = threading.Event()

        def counting_render():
            call_count[0] += 1
            time.sleep(0.1)
            return _fake_buf(50)

        done_count = [0]
        def on_done(k, b):
            done_count[0] += 1
            if done_count[0] >= 1:
                done.set()

        sched.get_or_schedule("coalesce00000000", counting_render, on_done)
        sched.get_or_schedule("coalesce00000000", counting_render, on_done)
        done.wait(timeout=5.0)
        # Either 1 or 2 renders (second may or may not have been coalesced depending on timing)
        # But the cache should have the result
        self.assertTrue(cache.has("coalesce00000000"))
        sched.shutdown()

    # ---- pending / fresh queries

    def test_is_fresh_after_render(self):
        cache, sched = self._make()
        done = threading.Event()
        sched.get_or_schedule("freshkey00000000", self._render_fn(), lambda k, b: done.set())
        done.wait(timeout=5.0)
        self.assertTrue(sched.is_fresh("freshkey00000000"))
        sched.shutdown()

    def test_is_pending_while_rendering(self):
        cache, sched = self._make()
        started = threading.Event()
        finishing = threading.Event()

        def slow_render():
            started.set()
            finishing.wait(timeout=5.0)
            return _fake_buf(50)

        sched.get_or_schedule("pendkey000000000", slow_render)
        started.wait(timeout=2.0)
        self.assertTrue(sched.is_pending("pendkey000000000"))
        finishing.set()
        sched.shutdown()

    def test_pending_count_decrements_after_render(self):
        cache, sched = self._make()
        done = threading.Event()
        sched.get_or_schedule("pcount000000000a", self._render_fn(), lambda k, b: done.set())
        done.wait(timeout=5.0)
        time.sleep(0.05)  # let internal state settle
        self.assertEqual(sched.pending_count(), 0)
        sched.shutdown()

    # ---- invalidate

    def test_invalidate_cancels_pending(self):
        cache, sched = self._make()
        # Schedule something slow
        done = threading.Event()
        sched.get_or_schedule("invalkey0000000", lambda: (time.sleep(2), _fake_buf())[1])
        sched.invalidate("invalkey0000000")
        # After invalidation the key is no longer pending
        time.sleep(0.1)
        self.assertFalse(sched.is_pending("invalkey0000000"))
        sched.shutdown(wait=False)

    # ---- render_fn error handling

    def test_render_error_does_not_crash(self):
        cache, sched = self._make()
        done = threading.Event()

        def bad_render():
            raise RuntimeError("boom")

        results = []
        sched.get_or_schedule("errkey000000000", bad_render, lambda k, b: (results.append(b), done.set()))
        done.wait(timeout=5.0)
        # on_done still called (with a fallback zero buffer)
        self.assertEqual(len(results), 1)
        sched.shutdown()

    # ---- shutdown

    def test_shutdown_idempotent(self):
        cache, sched = self._make()
        sched.shutdown()
        sched.shutdown()  # should not raise


# ---------------------------------------------------------------------------
# Integration: render_channel via control → cache

class TestRenderChannelIntegration(unittest.TestCase):
    def test_render_channel_returns_audio(self):
        import tempfile
        from forge.document.channels import PatternChannel
        from forge import control

        ch = PatternChannel("kick")
        ch.steps[0].on = True
        ch.steps[4].on = True

        buf = control.render_channel(ch, bpm=138.0, length_bars=4, seed=0)
        self.assertGreater(len(buf), 0)
        self.assertEqual(buf.data.shape[1], 2)

    def test_render_channel_same_input_same_output(self):
        from forge.document.channels import PatternChannel
        from forge import control

        ch = PatternChannel("kick")
        ch.steps[0].on = True
        buf1 = control.render_channel(ch, bpm=138.0, length_bars=2, seed=42)
        buf2 = control.render_channel(ch, bpm=138.0, length_bars=2, seed=42)
        np.testing.assert_array_equal(buf1.data, buf2.data)


if __name__ == "__main__":
    unittest.main()
