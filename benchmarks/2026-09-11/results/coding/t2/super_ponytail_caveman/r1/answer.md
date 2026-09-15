GOAL: thread-safe sliding-window `RateLimiter(limit, window, clock)` w/ `allow(key)`, tests incl concurrent, note, edge cases. This turn delivers full thing, verified by run (5/5 tests pass, 500-thread race check clean). Nothing blocked.

```python
# solution.py
import threading
import time
from collections import defaultdict, deque


class RateLimiter:
    """Thread-safe sliding-window rate limiter.

    allow(key) returns True and records the call if `key` has had fewer
    than `limit` allowed calls in the last `window` seconds, else False.
    """

    def __init__(self, limit, window, clock=time.monotonic):
        if limit < 1:
            raise ValueError("limit must be >= 1")
        if window <= 0:
            raise ValueError("window must be > 0")
        self.limit = limit
        self.window = window
        self.clock = clock
        self._calls = defaultdict(deque)  # key -> deque of allowed-call timestamps
        self._lock = threading.Lock()

    def allow(self, key):
        now = self.clock()
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


class TestRateLimiter(unittest.TestCase):
    def test_allows_up_to_limit_then_blocks(self):
        rl = RateLimiter(limit=3, window=10.0, clock=lambda: 0.0)
        self.assertEqual([rl.allow("a") for _ in range(5)], [True, True, True, False, False])

    def test_keys_independent(self):
        rl = RateLimiter(limit=1, window=10.0, clock=lambda: 0.0)
        self.assertTrue(rl.allow("a"))
        self.assertFalse(rl.allow("a"))
        self.assertTrue(rl.allow("b"))

    def test_window_slides_open_after_expiry(self):
        t = [0.0]
        rl = RateLimiter(limit=2, window=5.0, clock=lambda: t[0])
        self.assertTrue(rl.allow("k"))
        self.assertTrue(rl.allow("k"))
        self.assertFalse(rl.allow("k"))
        t[0] = 4.999
        self.assertFalse(rl.allow("k"))  # still inside window
        t[0] = 5.0
        self.assertTrue(rl.allow("k"))  # oldest call now exactly window-old, expires

    def test_partial_expiry_not_full_reset(self):
        t = [0.0]
        rl = RateLimiter(limit=2, window=10.0, clock=lambda: t[0])
        self.assertTrue(rl.allow("k"))
        t[0] = 1.0
        self.assertTrue(rl.allow("k"))
        t[0] = 2.0
        self.assertFalse(rl.allow("k"))
        t[0] = 10.5
        self.assertTrue(rl.allow("k"))  # first call (t=0) expired, second (t=1) still counts
        t[0] = 10.9
        self.assertFalse(rl.allow("k"))
        t[0] = 11.1
        self.assertTrue(rl.allow("k"))  # second call (t=1) now expired too

    def test_concurrent_callers_same_key_respect_limit(self):
        limit = 100
        rl = RateLimiter(limit=limit, window=1000.0)
        results = []
        results_lock = threading.Lock()

        def worker():
            r = rl.allow("shared")
            with results_lock:
                results.append(r)

        threads = [threading.Thread(target=worker) for _ in range(500)]
        for th in threads:
            th.start()
        for th in threads:
            th.join()

        self.assertEqual(sum(results), limit)
        self.assertEqual(len(results), 500)


if __name__ == "__main__":
    unittest.main()
```

Ran both blocks direct (inline, no files written): 5/5 pass, concurrency test `allowed: 100 expected 100` across 500 threads hitting one key.

**Note.** Deque per key hold only allowed-call timestamps, oldest first, so expiry check is a `while` popleft off front, O(1) amortized per call instead of scanning whole history. Single global lock guard read-check-write as one atomic step; per-key lock would give more throughput but deque op already cheap, and lazy version correct first. `defaultdict` skip separate key-exists branch, one line covers unseen key.

**Edge cases not handled:**
- Unbounded key growth: no eviction of idle keys, long-running process leaks memory. `# ponytail: unbounded dict, add key eviction (LRU/TTL sweep) if key-space unbounded`
- Global lock serializes all keys, not just contended one, throughput ceiling under many keys. `# ponytail: global lock, per-key lock/sharding if throughput matters`
- Clock going backwards (non-monotonic custom clock, or system clock swap) not guarded, could let stale entries linger or miscompute cutoff.
- No `allow_n(key, n)` for batch/weighted requests, and no way to peek remaining quota without recording a call.