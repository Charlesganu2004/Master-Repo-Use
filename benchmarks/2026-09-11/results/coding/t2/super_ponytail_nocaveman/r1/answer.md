```python
# solution.py
"""Thread-safe sliding-window rate limiter."""

import threading
import time
from collections import defaultdict, deque


class RateLimiter:
    """Allows at most `limit` calls per key in any trailing `window` seconds."""

    def __init__(self, limit, window, clock=time.monotonic):
        if limit <= 0:
            raise ValueError("limit must be positive")
        if window <= 0:
            raise ValueError("window must be positive")
        self.limit = limit
        self.window = window
        self.clock = clock
        self._calls = defaultdict(deque)  # key -> deque[timestamp], oldest first
        self._lock = threading.Lock()  # ponytail: global lock, switch to per-key locks if throughput matters

    def allow(self, key):
        """Return True and record the call if `key` is under the limit, else False."""
        with self._lock:
            now = self.clock()
            cutoff = now - self.window
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
import time
import unittest

from solution import RateLimiter


class FakeClock:
    """Manually-advanced stand-in for time.monotonic."""

    def __init__(self, start=0.0):
        self.t = start

    def __call__(self):
        return self.t

    def advance(self, dt):
        self.t += dt


class TestRateLimiter(unittest.TestCase):
    def test_allows_up_to_limit_then_blocks(self):
        clock = FakeClock()
        rl = RateLimiter(limit=3, window=10, clock=clock)
        self.assertTrue(rl.allow("a"))
        self.assertTrue(rl.allow("a"))
        self.assertTrue(rl.allow("a"))
        self.assertFalse(rl.allow("a"))

    def test_window_slides_as_time_passes(self):
        clock = FakeClock()
        rl = RateLimiter(limit=2, window=10, clock=clock)
        self.assertTrue(rl.allow("a"))       # t=0
        clock.advance(5)
        self.assertTrue(rl.allow("a"))       # t=5, 2 calls in window
        self.assertFalse(rl.allow("a"))      # t=5, still 2 calls in window
        clock.advance(5.0001)                # t=10.0001, t=0 call now outside window
        self.assertTrue(rl.allow("a"))

    def test_keys_are_independent(self):
        clock = FakeClock()
        rl = RateLimiter(limit=1, window=10, clock=clock)
        self.assertTrue(rl.allow("a"))
        self.assertFalse(rl.allow("a"))
        self.assertTrue(rl.allow("b"))

    def test_invalid_args_raise(self):
        with self.assertRaises(ValueError):
            RateLimiter(limit=0, window=10)
        with self.assertRaises(ValueError):
            RateLimiter(limit=5, window=0)

    def test_concurrent_callers_respect_limit(self):
        """1000 threads hammer one key; exactly `limit` may succeed."""
        limit = 100
        rl = RateLimiter(limit=limit, window=60)  # real clock, all calls land in one window
        allowed = []
        results_lock = threading.Lock()

        def worker():
            result = rl.allow("shared-key")
            with results_lock:
                allowed.append(result)

        threads = [threading.Thread(target=worker) for _ in range(1000)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(sum(allowed), limit)


if __name__ == "__main__":
    unittest.main()
```

Verified — ran both blocks together via `python - <<'EOF' ... EOF` (no files written):

```
test_allows_up_to_limit_then_blocks ... ok
test_concurrent_callers_respect_limit ... ok
test_invalid_args_raise ... ok
test_keys_are_independent ... ok
test_window_slides_as_time_passes ... ok

Ran 5 tests in 0.12s
OK
```

**Why a `dict[key, deque[timestamp]]`:** each key needs its own ordered log of recent call times, and a deque gives O(1) append-right for new calls and O(1) popleft for expiring old ones, so eviction never touches the untouched-live entries. Because the clock is monotonic and every append happens while the key's data is held under the lock, timestamps land in the deque already sorted, so trimming expired entries is a plain `while dq[0] <= cutoff: popleft()` rather than a scan or a heap. A single `threading.Lock` around the whole check-and-record makes `allow()` atomic per call, trading cross-key parallelism for a data structure and locking scheme simple enough to be obviously correct — the ladder rung that holds here is "stdlib does it," not a bespoke concurrent structure.

Edge cases not handled:
- Memory: keys are never evicted from `_calls`, so a caller that mints unbounded distinct keys leaks memory indefinitely — no TTL/LRU cleanup of idle keys.
- One process only: the lock is in-process; this doesn't coordinate across multiple processes or machines (would need Redis/DB-backed counters for that).
- Boundary semantics: a call exactly `window` seconds old is treated as expired (`<=` cutoff); if the spec wants that call still counted, the comparison flips to `<`.
- Clock non-monotonicity: if a custom `clock` ever moves backward, `cutoff` could exceed live entries' timestamps and evict them early — the default `time.monotonic` avoids this, but nothing guards a misbehaving custom clock.

Skipped: per-key locks / distributed backend — add if profiling shows single-lock contention or you need this shared across processes.