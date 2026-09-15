All checks pass — deque-per-key sliding-window log, one global lock, exactly `limit` winners out of 100 racing threads.

```python
# solution.py
import time
import threading
from collections import deque, defaultdict


class RateLimiter:
    """Thread-safe sliding-window rate limiter.

    allow(key) returns True and records the call if `key` has had fewer
    than `limit` allowed calls within the trailing `window` seconds;
    otherwise returns False.
    """

    def __init__(self, limit, window, clock=time.monotonic):
        if limit <= 0:
            raise ValueError("limit must be positive")
        if window <= 0:
            raise ValueError("window must be positive")
        self.limit = limit
        self.window = window
        self.clock = clock
        self._calls = defaultdict(deque)  # key -> deque of allowed-call timestamps, oldest first
        # ponytail: single global lock serializes all keys; switch to per-key
        # locks (or a striped lock) if cross-key contention ever shows up in profiling
        self._lock = threading.Lock()

    def allow(self, key):
        now = self.clock()
        with self._lock:
            q = self._calls[key]
            cutoff = now - self.window
            while q and q[0] <= cutoff:
                q.popleft()
            if len(q) < self.limit:
                q.append(now)
                return True
            return False
```

```python
# test_solution.py
import threading
import unittest

from solution import RateLimiter


class FakeClock:
    """Deterministic, manually-advanced clock for tests."""

    def __init__(self, start=0.0):
        self._t = start

    def __call__(self):
        return self._t

    def advance(self, dt):
        self._t += dt


class RateLimiterTests(unittest.TestCase):
    def test_allows_up_to_limit_then_blocks(self):
        clock = FakeClock()
        rl = RateLimiter(limit=3, window=10, clock=clock)
        results = [rl.allow("a") for _ in range(5)]
        self.assertEqual(results, [True, True, True, False, False])

    def test_window_slides_to_allow_more_calls(self):
        clock = FakeClock()
        rl = RateLimiter(limit=2, window=10, clock=clock)
        self.assertTrue(rl.allow("a"))
        clock.advance(5)
        self.assertTrue(rl.allow("a"))
        self.assertFalse(rl.allow("a"))  # 2 calls already within the last 10s
        clock.advance(5.001)  # first call is now just outside the window
        self.assertTrue(rl.allow("a"))

    def test_keys_are_independent(self):
        clock = FakeClock()
        rl = RateLimiter(limit=1, window=10, clock=clock)
        self.assertTrue(rl.allow("a"))
        self.assertFalse(rl.allow("a"))
        self.assertTrue(rl.allow("b"))

    def test_concurrent_callers_never_exceed_limit(self):
        clock = FakeClock()  # frozen clock: every thread races inside the same window
        rl = RateLimiter(limit=10, window=10, clock=clock)
        n_threads = 100
        results = [None] * n_threads
        barrier = threading.Barrier(n_threads)

        def worker(i):
            barrier.wait()  # release all threads at once to maximize contention
            results[i] = rl.allow("shared-key")

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(sum(1 for r in results if r), 10)


if __name__ == "__main__":
    unittest.main()
```

**Note on the data structure:** A deque of allowed-call timestamps per key gives an exact sliding-window log — no bucket-rounding error like fixed-window counters have — while `popleft()` and `append()` are both O(1), so trimming expired entries and recording a new call stay cheap. A single `threading.Lock` around the read-evict-write sequence is what actually makes it thread-safe: without it, two threads could both read `len(q) < limit` as true and both append, letting the count exceed `limit`. `defaultdict(deque)` was picked over a plain dict because it avoids a manual "key present?" branch for the common case of a first-time caller.

**Skipped:** per-key locking (single global lock is fine until profiling shows cross-key contention).

Edge cases not handled:
- Unbounded memory growth — a key's (now-empty) deque is never removed from `_calls`, so a huge number of distinct one-shot keys leaks memory forever.
- Only thread-safe within one process — doesn't coordinate across processes/machines (no shared store like Redis).
- Assumes `clock` is monotonic non-decreasing; a clock that jumps backward (e.g. wall-clock NTP correction) can let stale calls linger past the intended window.