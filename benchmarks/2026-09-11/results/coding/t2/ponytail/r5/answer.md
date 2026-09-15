All 4 tests pass, including the concurrency one (50 threads hammering one key, exactly 5 get through).

```python
# solution.py
import threading
import time
from collections import defaultdict, deque


class RateLimiter:
    """Thread-safe sliding-window rate limiter.

    Each key may make at most `limit` calls in any trailing `window`
    seconds. allow(key) atomically checks the window and records the
    call if it's allowed.
    """

    def __init__(self, limit: int, window: float, clock=time.monotonic):
        if limit <= 0 or window <= 0:
            raise ValueError("limit and window must be positive")
        self.limit = limit
        self.window = window
        self._clock = clock
        self._calls = defaultdict(deque)  # key -> deque[timestamp], oldest first
        self._lock = threading.Lock()  # ponytail: global lock, switch to per-key locks if contention across many keys becomes a bottleneck

    def allow(self, key) -> bool:
        now = self._clock()
        cutoff = now - self.window
        with self._lock:
            dq = self._calls[key]
            while dq and dq[0] <= cutoff:
                dq.popleft()
            if len(dq) < self.limit:
                dq.append(now)
                return True
            return False
```

```python
# test_solution.py
import threading
import unittest

from solution import RateLimiter


class FakeClock:
    def __init__(self, start=0.0):
        self.t = start

    def __call__(self):
        return self.t

    def advance(self, dt):
        self.t += dt


class RateLimiterTest(unittest.TestCase):
    def test_allows_up_to_limit(self):
        clock = FakeClock()
        rl = RateLimiter(limit=3, window=10, clock=clock)
        self.assertTrue(rl.allow("a"))
        self.assertTrue(rl.allow("a"))
        self.assertTrue(rl.allow("a"))
        self.assertFalse(rl.allow("a"))

    def test_window_slides(self):
        clock = FakeClock()
        rl = RateLimiter(limit=2, window=10, clock=clock)
        self.assertTrue(rl.allow("a"))
        clock.advance(5)
        self.assertTrue(rl.allow("a"))
        self.assertFalse(rl.allow("a"))  # still 2 calls within last 10s
        clock.advance(5.001)  # call at t=0 now outside window
        self.assertTrue(rl.allow("a"))

    def test_keys_are_independent(self):
        clock = FakeClock()
        rl = RateLimiter(limit=1, window=10, clock=clock)
        self.assertTrue(rl.allow("a"))
        self.assertTrue(rl.allow("b"))
        self.assertFalse(rl.allow("a"))
        self.assertFalse(rl.allow("b"))

    def test_concurrent_callers_never_exceed_limit(self):
        clock = FakeClock()  # frozen clock: everyone races at the same instant
        rl = RateLimiter(limit=5, window=10, clock=clock)
        results = []
        results_lock = threading.Lock()

        def worker():
            r = rl.allow("shared")
            with results_lock:
                results.append(r)

        threads = [threading.Thread(target=worker) for _ in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(sum(results), 5)


if __name__ == "__main__":
    unittest.main()
```

A `deque` per key gives O(1) eviction from the front since timestamps are inserted in increasing order, so expired entries are always a contiguous prefix — no need to scan or sort. A single `threading.Lock` around the check-and-append makes the read-modify-write atomic, which is the only way to avoid the classic race where two threads both see `count < limit` and both get admitted. `defaultdict(deque)` avoids a separate "create bucket for new key" branch.

Skipped: memory reclamation for keys that go idle forever (deques for dead keys sit empty in the dict) — add an occasional sweep or an LRU cap if key cardinality is unbounded. Also skipped: per-key locking (single global lock serializes unrelated keys) — add if profiling shows contention across many hot keys.