All tests pass. Move `import time` to top in final version (test ran fine, just cleanup for delivery).

```python
# solution.py
"""Thread-safe sliding-window rate limiter."""

import threading
import time
from collections import defaultdict, deque
from typing import Callable, Deque, Dict, Hashable


class RateLimiter:
    """Allows at most `limit` calls per key in any trailing `window` seconds.

    Sliding-window-log algorithm: for each key, keep deque of timestamps of
    its recently allowed calls. Each call drops timestamps older than
    `window` seconds, then admits only if fewer than `limit` remain.
    """

    def __init__(
        self,
        limit: int,
        window: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if limit <= 0:
            raise ValueError("limit must be positive")
        if window <= 0:
            raise ValueError("window must be positive")
        self._limit = limit
        self._window = window
        self._clock = clock
        self._lock = threading.Lock()
        self._calls: Dict[Hashable, Deque[float]] = defaultdict(deque)

    def allow(self, key: Hashable) -> bool:
        now = self._clock()
        cutoff = now - self._window
        with self._lock:
            timestamps = self._calls[key]
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
import time
import unittest
from concurrent.futures import ThreadPoolExecutor

from solution import RateLimiter


class FakeClock:
    """Manually-advanced clock for deterministic window-boundary tests."""

    def __init__(self, start: float = 0.0) -> None:
        self._now = start

    def __call__(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += seconds


class RateLimiterBasicTests(unittest.TestCase):
    def test_allows_up_to_limit_then_denies(self):
        clock = FakeClock()
        rl = RateLimiter(limit=3, window=10, clock=clock)
        results = [rl.allow("a") for _ in range(5)]
        self.assertEqual(results, [True, True, True, False, False])

    def test_calls_expire_after_window(self):
        clock = FakeClock()
        rl = RateLimiter(limit=2, window=10, clock=clock)
        self.assertTrue(rl.allow("a"))
        self.assertTrue(rl.allow("a"))
        self.assertFalse(rl.allow("a"))

        clock.advance(10.001)  # push both earlier calls out of the window
        self.assertTrue(rl.allow("a"))
        self.assertTrue(rl.allow("a"))
        self.assertFalse(rl.allow("a"))

    def test_partial_expiry_slides_window(self):
        clock = FakeClock()
        rl = RateLimiter(limit=2, window=10, clock=clock)
        self.assertTrue(rl.allow("a"))   # t=0
        clock.advance(6)
        self.assertTrue(rl.allow("a"))   # t=6, both in window -> full
        self.assertFalse(rl.allow("a"))  # t=6, still full
        clock.advance(4.001)             # t=10.001, t=0 call expires
        self.assertTrue(rl.allow("a"))   # only t=6 call counts -> allowed
        self.assertFalse(rl.allow("a"))  # now two calls in window again

    def test_keys_are_independent(self):
        clock = FakeClock()
        rl = RateLimiter(limit=1, window=10, clock=clock)
        self.assertTrue(rl.allow("a"))
        self.assertFalse(rl.allow("a"))
        self.assertTrue(rl.allow("b"))  # separate key, own budget

    def test_rejects_bad_config(self):
        with self.assertRaises(ValueError):
            RateLimiter(limit=0, window=1)
        with self.assertRaises(ValueError):
            RateLimiter(limit=1, window=0)


class RateLimiterConcurrencyTests(unittest.TestCase):
    def test_concurrent_callers_never_exceed_limit(self):
        limit = 10
        thread_count = 50
        rl = RateLimiter(limit=limit, window=5.0, clock=time.monotonic)
        barrier = threading.Barrier(thread_count)

        def call():
            barrier.wait()  # line every thread up, hit allow() at once
            return rl.allow("shared-key")

        with ThreadPoolExecutor(max_workers=thread_count) as pool:
            results = list(pool.map(lambda _: call(), range(thread_count)))

        self.assertEqual(results.count(True), limit)
        self.assertEqual(results.count(False), thread_count - limit)


if __name__ == "__main__":
    unittest.main()
```

Ran both files (`python -m unittest test_solution -v`): 6 tests, all pass.

Why deque per key: sliding-window-log gives exact correctness (no fixed-bucket burst-at-boundary error like fixed-window counters), and deque gives O(1) append/popleft so expiry sweep costs only the number of stale entries, not full history. One global `Lock` around read-modify-write of a key's deque keeps `allow` atomic under concurrent callers without per-key lock bookkeeping. `clock` injection decouples tests from wall-clock timing, keeping window-boundary tests deterministic.

Edge cases not handled:
- Memory: deque for a key never gets removed from `_calls`, even once empty — unbounded key cardinality leaks memory forever.
- Throughput: single global lock serializes all keys, not just contended ones — bad under many hot, unrelated keys.
- Clock: assumes non-decreasing clock; a clock that jumps backward corrupts the sort order the popleft-based expiry relies on.
- No `TypeError`/hashability check on `key` beyond what `dict` itself raises.