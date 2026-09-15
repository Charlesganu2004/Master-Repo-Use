All 7 tests pass, in-memory, no files touched (`Ran 7 tests in 0.065s / OK`), including both concurrency cases: 500 threads racing on one key cap at exactly the limit, and 400 threads across 4 keys each land exactly at their own limit.

```python
# solution.py
"""Thread-safe sliding-window rate limiter."""
import threading
import time
from collections import defaultdict, deque


class RateLimiter:
    """Sliding-window rate limiter, safe for concurrent use.

    allow(key) returns True and records the call if `key` has had fewer
    than `limit` allowed calls in the trailing `window` seconds (measured
    by `clock`), otherwise returns False without recording anything.
    """

    def __init__(self, limit, window, clock=time.monotonic):
        if limit <= 0:
            raise ValueError("limit must be positive")
        if window <= 0:
            raise ValueError("window must be positive")
        self._limit = limit
        self._window = window
        self._clock = clock
        self._lock = threading.Lock()
        # ponytail: one lock guards every key, so calls for unrelated keys
        # serialize behind each other. Shard into N locks keyed by
        # hash(key) % N if that contention ever shows up in profiling.
        self._calls = defaultdict(deque)

    def allow(self, key):
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
"""Unit tests for RateLimiter."""
import unittest
from concurrent.futures import ThreadPoolExecutor

from solution import RateLimiter


class FakeClock:
    """Manually advanceable clock, so window-sliding is deterministic."""

    def __init__(self, start=0.0):
        self.t = start

    def __call__(self):
        return self.t

    def advance(self, dt):
        self.t += dt


class TestRateLimiterBasics(unittest.TestCase):
    def test_allows_up_to_limit_then_blocks(self):
        rl = RateLimiter(3, 10, clock=FakeClock())
        results = [rl.allow("a") for _ in range(5)]
        self.assertEqual(results, [True, True, True, False, False])

    def test_window_slides_to_admit_new_calls(self):
        clock = FakeClock()
        rl = RateLimiter(2, 5, clock=clock)
        self.assertTrue(rl.allow("k"))
        self.assertTrue(rl.allow("k"))
        self.assertFalse(rl.allow("k"))
        clock.advance(5.0001)  # oldest calls now outside the window
        self.assertTrue(rl.allow("k"))

    def test_partial_expiry_frees_exactly_one_slot(self):
        clock = FakeClock()
        rl = RateLimiter(2, 5, clock=clock)
        rl.allow("k")           # t=0
        clock.advance(3)
        rl.allow("k")           # t=3
        clock.advance(2.0001)   # t=5.0001: first call (t=0) now expired
        self.assertTrue(rl.allow("k"))   # slot freed by expiry
        self.assertFalse(rl.allow("k"))  # but limit (2) reached again

    def test_keys_are_independent(self):
        rl = RateLimiter(1, 10, clock=FakeClock())
        self.assertTrue(rl.allow("a"))
        self.assertFalse(rl.allow("a"))
        self.assertTrue(rl.allow("b"))  # unaffected by key "a"

    def test_invalid_limit_or_window_rejected(self):
        with self.assertRaises(ValueError):
            RateLimiter(0, 10)
        with self.assertRaises(ValueError):
            RateLimiter(5, 0)


class TestRateLimiterConcurrency(unittest.TestCase):
    def test_concurrent_callers_never_exceed_limit(self):
        # Real clock, window wide enough that it can't expire mid-test.
        limit = 10
        rl = RateLimiter(limit, window=100)

        with ThreadPoolExecutor(max_workers=50) as pool:
            results = list(pool.map(lambda _: rl.allow("shared-key"), range(500)))

        self.assertEqual(sum(results), limit)

    def test_concurrent_callers_distinct_keys_each_get_own_limit(self):
        limit = 5
        rl = RateLimiter(limit, window=100)
        keys = [f"key-{i % 4}" for i in range(400)]

        with ThreadPoolExecutor(max_workers=40) as pool:
            results = list(pool.map(rl.allow, keys))

        per_key_allowed = {}
        for key, allowed in zip(keys, results):
            per_key_allowed[key] = per_key_allowed.get(key, 0) + int(allowed)
        for key in set(keys):
            self.assertEqual(per_key_allowed[key], limit)


if __name__ == "__main__":
    unittest.main()
```

**Why a dict of deques.** A deque per key gives O(1) `popleft` for expiring old timestamps and O(1) `append` for new ones, whereas a list would need an O(n) shift on every eviction. Timestamps are appended in monotonically increasing order, so the oldest entry is always at the left end — no sorting or scanning is ever needed to find what expired. Keying by dict also gives each caller an exact, independent window instead of the accuracy-for-memory tradeoff of a fixed-bucket counter, while the deque for any one key never grows past `limit` since expiry runs before the length check.

**Edge cases not handled:** memory for keys is never reclaimed — a key queried once then abandoned keeps its (eventually empty-on-next-check) deque entry in the dict forever, so tracking unboundedly many distinct keys leaks memory; a non-monotonic or backward-jumping clock (e.g. plugging in `time.time` across an NTP correction) can make timestamps look older or newer than they should and isn't guarded against; the single lock serializes `allow()` across *all* keys, so it's a throughput ceiling under many-key concurrent load (flagged inline with a `ponytail:` comment); and every call has a fixed cost of 1 — there's no support for weighted/variable-cost requests or a burst allowance beyond `limit`.

Skills/tools used: `master-plan` (stated the deque-per-key + single-lock design before writing), `verify-before-complete` (ran the real test suite in-memory via stdin and quoted the `OK` output above rather than asserting it passes), ponytail ladder (stdlib `threading.Lock`/`collections.deque`/`concurrent.futures`, no third-party dependency, one `ponytail:` comment marking the single-lock ceiling). No file was created or modified — verification ran as one `python - <<'EOF'` script executed in memory via `exec`+`sys.modules`.