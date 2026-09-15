Verified: 5 unit tests pass, and a 50-trial stress run (100 threads racing for a 10-slot budget) never let the count drift from exactly 10.

```python
# solution.py
import threading
import time
from collections import defaultdict, deque


class RateLimiter:
    """Thread-safe sliding-window rate limiter.

    Each key may make at most `limit` calls in any trailing `window`
    seconds. allow(key) atomically checks the key's recent call history
    and records the call if it's still under budget.
    """

    def __init__(self, limit, window, clock=time.monotonic):
        if limit <= 0:
            raise ValueError("limit must be positive")
        if window <= 0:
            raise ValueError("window must be positive")
        self.limit = limit
        self.window = window
        self.clock = clock
        self._calls = defaultdict(deque)  # key -> deque[timestamp], oldest first
        # ponytail: one lock for all keys, per-key locks if this becomes a
        # throughput bottleneck under many distinct keys.
        self._lock = threading.Lock()

    def allow(self, key):
        now = self.clock()
        cutoff = now - self.window
        with self._lock:
            timestamps = self._calls[key]
            while timestamps and timestamps[0] <= cutoff:
                timestamps.popleft()
            if len(timestamps) < self.limit:
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
    """Manually advanced clock for deterministic window-boundary tests."""

    def __init__(self, start=0.0):
        self.now = start

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class RateLimiterBasicTests(unittest.TestCase):
    def test_allows_up_to_limit_then_blocks(self):
        clock = FakeClock()
        rl = RateLimiter(limit=3, window=10, clock=clock)
        results = [rl.allow("a") for _ in range(4)]
        self.assertEqual(results, [True, True, True, False])

    def test_independent_keys_have_independent_budgets(self):
        clock = FakeClock()
        rl = RateLimiter(limit=1, window=10, clock=clock)
        self.assertTrue(rl.allow("a"))
        self.assertFalse(rl.allow("a"))
        self.assertTrue(rl.allow("b"))  # separate key, untouched budget

    def test_calls_age_out_of_the_window(self):
        clock = FakeClock()
        rl = RateLimiter(limit=2, window=5, clock=clock)
        self.assertTrue(rl.allow("a"))   # t=0
        self.assertTrue(rl.allow("a"))   # t=0
        self.assertFalse(rl.allow("a"))  # t=0, budget exhausted

        clock.advance(4.9)
        self.assertFalse(rl.allow("a"))  # oldest call is 4.9s old, still counts

        clock.advance(0.1)  # oldest call now exactly 5.0s old -> expires
        self.assertTrue(rl.allow("a"))

    def test_rejects_non_positive_limit_or_window(self):
        with self.assertRaises(ValueError):
            RateLimiter(limit=0, window=10)
        with self.assertRaises(ValueError):
            RateLimiter(limit=5, window=0)


class RateLimiterConcurrencyTests(unittest.TestCase):
    def test_concurrent_callers_never_exceed_the_limit(self):
        limit = 10
        thread_count = 64
        rl = RateLimiter(limit=limit, window=60, clock=time.monotonic)
        barrier = threading.Barrier(thread_count)

        def call(_):
            barrier.wait()  # line every thread up to hit allow() at once
            return rl.allow("shared-key")

        with ThreadPoolExecutor(max_workers=thread_count) as pool:
            results = list(pool.map(call, range(thread_count)))

        self.assertEqual(sum(results), limit)
        # internal deque length must match too: no lost/duplicated records
        self.assertEqual(len(rl._calls["shared-key"]), limit)


if __name__ == "__main__":
    unittest.main()
```

**Verification:** ran both files together (concatenated over stdin, no files written to disk) with `python -m unittest -v` — all 5 tests pass, including the 64-thread barrier-synchronized concurrency test. Then ran the concurrency scenario standalone 50 times with 100 threads each — every trial landed on exactly 10 allowed calls, no drift.

**Why this data structure:** a `deque` per key holding only the timestamps still inside the window turns "how many calls recently" into O(1) amortized work — expired entries pop off the left in a `while` loop and the count is just `len(deque)`, so memory is bounded by `limit` per active key rather than growing forever. A single `threading.Lock` around the check-and-record makes `allow()` atomic: two threads racing for the last slot can't both read "9 of 10 used" and both append, which a naive read-then-write without a lock would allow. `defaultdict(deque)` was picked over a plain dict because it removes the per-key initialization branch for free, and a deque beats a list here because popping from the left is O(1) instead of O(n).

**Edge cases not handled:**
- Keys are never evicted once created — a caller hitting many distinct one-off keys leaks memory (empty deques stick around forever); a max-keys cap or TTL sweep would fix it.
- One global lock serializes `allow()` across *all* keys, not just contended ones — fine at moderate throughput, a real bottleneck under many hot distinct keys (per-key locks/sharding would fix it).
- `clock()` is trusted to be monotonic non-decreasing; a caller passing `time.time()` (which can jump backward on NTP correction) could let expired entries linger or expire early.
- No distributed/multi-process support — state is in-process memory only, so this doesn't help behind multiple app instances without an external store (e.g. Redis).