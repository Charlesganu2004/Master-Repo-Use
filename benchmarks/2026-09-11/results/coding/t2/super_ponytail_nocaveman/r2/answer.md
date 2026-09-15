Verified via `python - <<'EOF'` (stdin heredoc, no files written) — 5/5 tests pass, including the concurrency test with 200 threads on a shared key.

```python
# solution.py
"""Thread-safe sliding-window rate limiter."""

import threading
import time
from collections import deque
from typing import Callable, Dict, Hashable


class RateLimiter:
    """Allows up to `limit` calls per key in any trailing `window` seconds.

    Each key holds a deque of the timestamps of its allowed calls, oldest
    first. allow() evicts everything older than `window`, then admits the
    call if what's left is under `limit`.
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
        self._calls: Dict[Hashable, deque] = {}
        # ponytail: one global lock serializes all keys, not just contending
        # ones. Fine up to moderate throughput; shard into N locks keyed by
        # hash(key) % N if a hot key set starts to bottleneck.
        self._lock = threading.Lock()

    def allow(self, key: Hashable) -> bool:
        now = self._clock()
        cutoff = now - self._window
        with self._lock:
            q = self._calls.setdefault(key, deque())
            while q and q[0] <= cutoff:
                q.popleft()
            if len(q) < self._limit:
                q.append(now)
                return True
            return False
```

```python
# test_solution.py
"""Unit tests for RateLimiter."""

import threading
import time
import unittest

from solution import RateLimiter


class FakeClock:
    """Manually advanceable clock so window-edge behavior is deterministic."""

    def __init__(self, start: float = 0.0) -> None:
        self.t = start

    def __call__(self) -> float:
        return self.t

    def advance(self, dt: float) -> None:
        self.t += dt


class RateLimiterTest(unittest.TestCase):
    def test_allows_up_to_limit_then_blocks(self):
        clock = FakeClock()
        rl = RateLimiter(limit=3, window=10, clock=clock)
        results = [rl.allow("a") for _ in range(5)]
        self.assertEqual(results, [True, True, True, False, False])

    def test_window_slides_and_frees_capacity(self):
        clock = FakeClock()
        rl = RateLimiter(limit=2, window=10, clock=clock)
        self.assertTrue(rl.allow("a"))       # t=0
        clock.advance(4)
        self.assertTrue(rl.allow("a"))       # t=4, 2 calls in window
        self.assertFalse(rl.allow("a"))      # t=4, limit hit
        clock.advance(6.001)                 # t=10.001, t=0 call now expires
        self.assertTrue(rl.allow("a"))       # only the t=4 call still counts
        self.assertFalse(rl.allow("a"))

    def test_keys_are_independent(self):
        clock = FakeClock()
        rl = RateLimiter(limit=1, window=10, clock=clock)
        self.assertTrue(rl.allow("a"))
        self.assertFalse(rl.allow("a"))
        self.assertTrue(rl.allow("b"))

    def test_rejects_invalid_limit_or_window(self):
        with self.assertRaises(ValueError):
            RateLimiter(limit=0, window=1)
        with self.assertRaises(ValueError):
            RateLimiter(limit=1, window=0)

    def test_concurrent_callers_never_exceed_limit(self):
        """200 threads hit the same key at once; a Barrier lines them up to
        maximize contention. Exactly `limit` must win — proving the lock
        actually serializes read-evict-append instead of letting two threads
        both read len(q) < limit before either appends."""
        limit = 10
        n_threads = 200
        rl = RateLimiter(limit=limit, window=60, clock=time.monotonic)
        start_gate = threading.Barrier(n_threads)
        results = [None] * n_threads

        def worker(i):
            start_gate.wait()
            results[i] = rl.allow("shared-key")

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(sum(1 for r in results if r), limit)
        self.assertEqual(sum(1 for r in results if not r), n_threads - limit)


if __name__ == "__main__":
    unittest.main()
```

**Why a deque per key:** the window only ever moves forward, so timestamps are evicted strictly oldest-first — a deque gives O(1) popleft/append, unlike a list (O(n) pops from the front) or a sorted structure that would be overkill for data that's already time-ordered by construction. Storing one deque per key (rather than one global structure) keeps keys independent without needing to filter by key on every check. A single `threading.Lock` around the whole read-evict-append sequence is the smallest thing that's actually correct — anything finer-grained (per-key locks, atomics) is optimizing a bottleneck that hasn't been shown to exist yet.

**Edge cases not handled:**
- Unbounded memory: entries for a key are never dropped until that key calls `allow()` again, so a key that's called once and never again keeps its (tiny, single-item) deque forever — no TTL/cleanup sweep for abandoned keys.
- No fairness/ordering guarantee across threads — the Barrier test proves the *count* is correct, not *which* callers win when arrival order is genuinely simultaneous.
- `clock()` is trusted to be non-decreasing; a clock that jumps backward (e.g. swapping in `time.time()` across a system clock adjustment) could let an evicted-too-early or evicted-too-late window slip through. `time.monotonic` (the default) doesn't have this problem.

Skipped: per-key lock sharding — add if profiling shows the global lock is the bottleneck. Skipped: TTL cleanup for idle keys — add if key cardinality is unbounded/attacker-controlled.