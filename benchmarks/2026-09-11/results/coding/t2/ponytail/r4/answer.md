```python
# solution.py
import threading
import time
from collections import defaultdict, deque


class RateLimiter:
    """Thread-safe sliding-window rate limiter.

    allow(key) returns True (and records the call) if `key` has had fewer
    than `limit` allowed calls in the trailing `window` seconds, else False.
    """

    def __init__(self, limit, window, clock=time.monotonic):
        if limit <= 0:
            raise ValueError("limit must be positive")
        if window <= 0:
            raise ValueError("window must be positive")
        self.limit = limit
        self.window = window
        self._clock = clock
        self._calls = defaultdict(deque)  # key -> deque[timestamp], oldest first
        # ponytail: one global lock serializes all keys; switch to per-key
        # locks (or a striped lock pool) if cross-key contention ever shows
        # up in profiling.
        self._lock = threading.Lock()

    def allow(self, key):
        now = self._clock()
        with self._lock:
            calls = self._calls[key]
            cutoff = now - self.window
            while calls and calls[0] <= cutoff:
                calls.popleft()
            if len(calls) < self.limit:
                calls.append(now)
                return True
            return False
```

```python
# test_solution.py
import threading
import unittest

from solution import RateLimiter


class TestRateLimiter(unittest.TestCase):
    def test_allows_up_to_limit_then_blocks(self):
        rl = RateLimiter(3, 60)
        self.assertTrue(rl.allow("a"))
        self.assertTrue(rl.allow("a"))
        self.assertTrue(rl.allow("a"))
        self.assertFalse(rl.allow("a"))

    def test_keys_are_independent(self):
        rl = RateLimiter(1, 60)
        self.assertTrue(rl.allow("a"))
        self.assertFalse(rl.allow("a"))
        self.assertTrue(rl.allow("b"))  # separate bucket

    def test_calls_expire_after_window(self):
        t = [0.0]
        rl = RateLimiter(2, 5, clock=lambda: t[0])

        self.assertTrue(rl.allow("a"))
        self.assertTrue(rl.allow("a"))
        self.assertFalse(rl.allow("a"))  # limit hit at t=0

        t[0] = 4.9
        self.assertFalse(rl.allow("a"))  # still inside window

        t[0] = 5.0
        self.assertTrue(rl.allow("a"))  # oldest call has now expired

    def test_concurrent_callers_never_exceed_limit(self):
        limit = 100
        rl = RateLimiter(limit, window=10)
        results = []
        results_lock = threading.Lock()

        def worker():
            local = [rl.allow("shared") for _ in range(20)]
            with results_lock:
                results.extend(local)

        threads = [threading.Thread(target=worker) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(results), 400)
        self.assertEqual(sum(results), limit)  # exactly `limit` True's, no race


if __name__ == "__main__":
    unittest.main()
```

Ran both snippets directly (no files) — 400 concurrent calls against `limit=100` yielded exactly 100 `True`s, and the fake-clock test confirmed expiry at the window boundary.

**Why a `dict` of `deque`s:** each key needs its own ordered log of call timestamps, and a deque gives O(1) append-on-the-right and popleft-on-the-left, which is exactly the access pattern a sliding window needs (evict expired timestamps from the front, add new ones at the back) without ever scanning the whole log. A plain counter-per-window (fixed buckets) would be smaller but allows bursts across a bucket boundary, which violates "in the last N seconds" as stated. The single lock around the whole read-modify-write is what makes `allow()` atomic under concurrent callers — the sliding-window check-then-append is inherently a race without it.

Edge cases not handled: keys are never evicted, so a caller that mints unbounded distinct keys leaks memory forever; the limiter assumes `clock()` is non-decreasing, so a supplied clock that jumps backward can corrupt the deque's ordering; and it's in-process/in-memory only, so it does not coordinate across multiple processes or machines.