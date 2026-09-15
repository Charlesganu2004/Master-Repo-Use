All 7 tests pass. Final files below.

```python
# solution.py
import threading
import time
from collections import deque
from typing import Callable, Deque, Dict, Hashable


class RateLimiter:
    """Thread-safe sliding-window rate limiter.

    Allows at most `limit` calls per `key` within any trailing `window`
    seconds. Each call's timestamp is recorded per key; a call is
    allowed only if fewer than `limit` timestamps fall within
    (now - window, now].
    """

    def __init__(self, limit: int, window: float, clock: Callable[[], float] = time.monotonic):
        if limit <= 0:
            raise ValueError("limit must be positive")
        if window <= 0:
            raise ValueError("window must be positive")
        self._limit = limit
        self._window = window
        self._clock = clock
        self._lock = threading.Lock()
        self._calls: Dict[Hashable, Deque[float]] = {}

    def allow(self, key: Hashable) -> bool:
        now = self._clock()
        with self._lock:
            timestamps = self._calls.setdefault(key, deque())
            cutoff = now - self._window
            while timestamps and timestamps[0] <= cutoff:
                timestamps.popleft()
            if len(timestamps) < self._limit:
                timestamps.append(now)
                return True
            return False
```

```python
# test_solution.py
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor

from solution import RateLimiter


class FakeClock:
    def __init__(self, start=0.0):
        self.t = start

    def __call__(self):
        return self.t

    def advance(self, dt):
        self.t += dt


class TestRateLimiterBasics(unittest.TestCase):
    def test_allows_up_to_limit_then_blocks(self):
        clock = FakeClock()
        rl = RateLimiter(limit=3, window=10, clock=clock)
        results = [rl.allow("a") for _ in range(5)]
        self.assertEqual(results, [True, True, True, False, False])

    def test_resets_after_window_elapses(self):
        clock = FakeClock()
        rl = RateLimiter(limit=2, window=5, clock=clock)
        self.assertTrue(rl.allow("a"))
        self.assertTrue(rl.allow("a"))
        self.assertFalse(rl.allow("a"))
        clock.advance(5.0001)
        self.assertTrue(rl.allow("a"))

    def test_sliding_not_fixed_bucket(self):
        clock = FakeClock()
        rl = RateLimiter(limit=2, window=10, clock=clock)
        self.assertTrue(rl.allow("a"))    # t=0
        clock.advance(1)
        self.assertTrue(rl.allow("a"))    # t=1, window full: [0, 1]
        clock.advance(1)
        self.assertFalse(rl.allow("a"))   # t=2, still full
        clock.advance(8.0001)
        self.assertTrue(rl.allow("a"))    # t=10.0001, t=0 expired, [1] -> allow

    def test_independent_keys(self):
        clock = FakeClock()
        rl = RateLimiter(limit=1, window=10, clock=clock)
        self.assertTrue(rl.allow("a"))
        self.assertTrue(rl.allow("b"))
        self.assertFalse(rl.allow("a"))
        self.assertFalse(rl.allow("b"))

    def test_invalid_args(self):
        with self.assertRaises(ValueError):
            RateLimiter(limit=0, window=10)
        with self.assertRaises(ValueError):
            RateLimiter(limit=1, window=0)


class TestRateLimiterConcurrency(unittest.TestCase):
    def test_concurrent_callers_enforce_limit_exactly(self):
        limit = 10
        num_threads = 50
        rl = RateLimiter(limit=limit, window=2.0)
        barrier = threading.Barrier(num_threads)

        def worker():
            barrier.wait()
            return rl.allow("shared-key")

        with ThreadPoolExecutor(max_workers=num_threads) as pool:
            results = list(pool.map(lambda _: worker(), range(num_threads)))

        self.assertEqual(sum(results), limit)

    def test_concurrent_distinct_keys_do_not_interfere(self):
        limit = 5
        rl = RateLimiter(limit=limit, window=2.0)

        def worker(key):
            return sum(rl.allow(key) for _ in range(limit + 5))

        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(worker, [f"key-{i}" for i in range(8)]))

        self.assertTrue(all(r == limit for r in results))


if __name__ == "__main__":
    unittest.main()
```

Ran locally: 7/7 pass.

Why deque: per key store timestamps sorted by insertion (already time-ordered), so expiry check only pop from left, O(1) amortized. Single global lock keep design simple and correct, cost acceptable since critical section tiny (deque trim + append). setdefault build dict entry lazily, so memory scale with active key count not preset key space.

Edge case not handled: no eviction of empty/stale key entries, dict grows forever if new keys keep appearing (memory leak over long run). Single global lock also serialize all keys, so throughput bottleneck under many distinct hot keys (per-key lock or sharding would fix). Clock going backward (non-monotonic clock passed in) not guarded, could let stale timestamps linger past their window.