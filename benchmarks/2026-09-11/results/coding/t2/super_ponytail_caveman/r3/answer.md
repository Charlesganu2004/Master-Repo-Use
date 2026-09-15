Verify: ran full check inline (no files touched), output `ALL CHECKS PASSED 50` — 500 concurrent threads on one key, exactly `limit=50` won. Goal status: sliding-window `RateLimiter` done, thread-safe, tests incl. concurrent caller done. Nothing left blocked.

Skills applied: master-architect (picked shape before code — single dict+deque, one lock), master-plan (small task, no written plan needed, ladder run inline), verify-before-complete (ran real check, quoted real output above), master-anti-slop / caveman-full (prose cut).

```python
# solution.py
"""Thread-safe sliding-window rate limiter."""
import threading
import time
from collections import deque
from typing import Callable, Dict, Hashable


class RateLimiter:
    """Allow at most `limit` calls per key in the trailing `window` seconds."""

    def __init__(self, limit: int, window: float, clock: Callable[[], float] = time.monotonic):
        if limit <= 0:
            raise ValueError("limit must be positive")
        if window <= 0:
            raise ValueError("window must be positive")
        self.limit = limit
        self.window = window
        self.clock = clock
        self._calls: Dict[Hashable, deque] = {}
        # ponytail: single global lock serializes all keys, add per-key locks if throughput matters
        self._lock = threading.Lock()

    def allow(self, key: Hashable) -> bool:
        """Return True and record `key`'s call if under limit in the window, else False."""
        now = self.clock()
        cutoff = now - self.window
        with self._lock:
            q = self._calls.setdefault(key, deque())
            while q and q[0] <= cutoff:
                q.popleft()
            if len(q) < self.limit:
                q.append(now)
                return True
            return False
```

```python
# test_solution.py
"""Unit tests for RateLimiter."""
import threading

import pytest

from solution import RateLimiter


class FakeClock:
    """Manually-advanced clock for deterministic window tests."""

    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def test_allows_up_to_limit_then_blocks():
    fc = FakeClock()
    rl = RateLimiter(limit=3, window=10, clock=fc)
    assert [rl.allow("a") for _ in range(3)] == [True, True, True]
    assert rl.allow("a") is False


def test_sliding_window_expiry():
    fc = FakeClock()
    rl = RateLimiter(limit=2, window=10, clock=fc)
    assert rl.allow("a") is True   # t=0
    fc.t = 5
    assert rl.allow("a") is True   # t=5, 2 calls in window
    fc.t = 9.999
    assert rl.allow("a") is False  # both prior calls still in window
    fc.t = 10.0
    assert rl.allow("a") is True   # call at t=0 now exactly window-old, expires


def test_keys_are_independent():
    fc = FakeClock()
    rl = RateLimiter(limit=1, window=10, clock=fc)
    assert rl.allow("a") is True
    assert rl.allow("a") is False
    assert rl.allow("b") is True   # separate budget, unaffected by "a"


def test_invalid_constructor_args_raise():
    with pytest.raises(ValueError):
        RateLimiter(limit=0, window=10)
    with pytest.raises(ValueError):
        RateLimiter(limit=5, window=0)


def test_concurrent_callers_respect_limit():
    """500 threads race the same key; exactly `limit` may win, no over/under count."""
    limit = 50
    rl = RateLimiter(limit=limit, window=5)
    results = []
    results_lock = threading.Lock()
    n_threads = 500
    barrier = threading.Barrier(n_threads)

    def worker():
        barrier.wait()  # maximize contention: all threads call allow() near-simultaneously
        allowed = rl.allow("shared-key")
        with results_lock:
            results.append(allowed)

    threads = [threading.Thread(target=worker) for _ in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert sum(results) == limit
    assert len(results) == n_threads


def test_concurrent_callers_different_keys_each_get_own_budget():
    limit = 10
    rl = RateLimiter(limit=limit, window=5)
    n_keys = 20
    calls_per_key = 15
    results = {k: [] for k in range(n_keys)}
    results_lock = threading.Lock()

    def worker(key):
        allowed = rl.allow(key)
        with results_lock:
            results[key].append(allowed)

    threads = [
        threading.Thread(target=worker, args=(k,))
        for k in range(n_keys)
        for _ in range(calls_per_key)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    for k in range(n_keys):
        assert sum(results[k]) == limit
```

Note (3 sentences): deque per key gives O(1) amortized push/pop at both ends, so expiring stale timestamps off the front costs nothing extra beyond what `allow` already pays. A dict maps key to its own deque so unrelated keys never block or count against each other. One `threading.Lock` around the whole read-modify-write (prune, check, append) is what makes it thread-safe — without it, two threads could each read `len(q) < limit` as true before either appends, both getting `True` past the limit.

Edge cases not handled: single global lock serializes all keys under load, so throughput drops if many hot keys contend (upgrade: per-key locks, e.g. `defaultdict` of locks). Keys are never evicted, so a rate limiter tracking unbounded distinct keys leaks memory forever (upgrade: TTL sweep or LRU cap on `_calls`). No max on deque length before pruning, so a caller with a very small `window` and very high call rate holds a growing deque between prunes within the same `window`. Clock going backwards (non-monotonic `clock` passed in) isn't guarded against and could let stale entries survive past their real expiry.