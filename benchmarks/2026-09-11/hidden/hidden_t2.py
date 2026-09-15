"""Hidden checks for task t2, RateLimiter. The model never sees these.

The prompt fixes the interface, RateLimiter(limit, window, clock=time.monotonic)
with allow(key), so every check drives a fake clock and is deterministic. Exact
window boundaries are left out: the prompt says "in the last window seconds"
and does not settle whether a call exactly window seconds old still counts.

    python hidden_t2.py <directory containing solution.py>
"""
import importlib
import json
import sys
import threading


class Clock:
    def __init__(self, start=1000.0):
        self.now = start

    def __call__(self):
        return self.now


def check_basic(RateLimiter):
    c = Clock()
    rl = RateLimiter(3, 10, clock=c)
    got = [rl.allow("a") for _ in range(4)]
    return got == [True, True, True, False], f"four calls gave {got}"


def check_expiry(RateLimiter):
    c = Clock()
    rl = RateLimiter(3, 10, clock=c)
    for _ in range(3):
        rl.allow("a")
    c.now += 10.5
    return rl.allow("a") is True, "a call after the window passed was refused"


def check_sliding_not_fixed(RateLimiter):
    c = Clock(0.0)
    rl = RateLimiter(3, 10, clock=c)
    seen = []
    for t in (0.0, 5.0, 9.0):
        c.now = t
        seen.append(rl.allow("a"))
    c.now = 10.5
    seen.append(rl.allow("a"))      # the t=0 call has left the window
    c.now = 10.6
    seen.append(rl.allow("a"))      # 5, 9 and 10.5 are all inside it
    return seen == [True, True, True, True, False], f"sequence gave {seen}"


def check_denied_not_recorded(RateLimiter):
    c = Clock(0.0)
    rl = RateLimiter(1, 10, clock=c)
    first = rl.allow("a")
    c.now = 1.0
    second = rl.allow("a")
    c.now = 5.0
    third = rl.allow("a")
    c.now = 10.5                     # only the t=0 call ever counted
    fourth = rl.allow("a")
    ok = [first, second, third, fourth] == [True, False, False, True]
    return ok, f"gave {[first, second, third, fourth]}; a refused call must not count"


def check_keys_independent(RateLimiter):
    c = Clock()
    rl = RateLimiter(2, 10, clock=c)
    rl.allow("a"), rl.allow("a")
    return (rl.allow("a") is False and rl.allow("b") is True), "keys share a budget"


def check_returns_bool(RateLimiter):
    rl = RateLimiter(1, 10, clock=Clock())
    a, b = rl.allow("k"), rl.allow("k")
    return (type(a) is bool and type(b) is bool), f"returned {type(a).__name__}, {type(b).__name__}"


def check_concurrent_one_key(RateLimiter):
    for attempt in range(3):
        rl = RateLimiter(100, 1000, clock=Clock())
        allowed = []
        lock = threading.Lock()
        barrier = threading.Barrier(32)

        def worker():
            barrier.wait()
            mine = sum(1 for _ in range(25) if rl.allow("k"))
            with lock:
                allowed.append(mine)

        threads = [threading.Thread(target=worker) for _ in range(32)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(30)
        if sum(allowed) != 100:
            return False, f"800 concurrent calls allowed {sum(allowed)}, expected exactly 100"
    return True, ""


def check_concurrent_two_keys(RateLimiter):
    rl = RateLimiter(50, 1000, clock=Clock())
    counts = {"x": 0, "y": 0}
    lock = threading.Lock()
    barrier = threading.Barrier(16)

    def worker(index):
        barrier.wait()
        for step in range(20):
            key = "x" if (index + step) % 2 else "y"
            if rl.allow(key):
                with lock:
                    counts[key] += 1

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(16)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(30)
    return counts == {"x": 50, "y": 50}, f"allowed {counts}, expected 50 each"


CHECKS = [check_basic, check_expiry, check_sliding_not_fixed, check_denied_not_recorded,
          check_keys_independent, check_returns_bool, check_concurrent_one_key,
          check_concurrent_two_keys]


def main() -> None:
    sys.path.insert(0, sys.argv[1])
    try:
        RateLimiter = importlib.import_module("solution").RateLimiter
    except Exception as error:
        print(json.dumps({"passed": 0, "total": len(CHECKS),
                          "failures": [f"import: {type(error).__name__}: {error}"]}))
        return
    failures, passed = [], 0
    for check in CHECKS:
        try:
            ok, why = check(RateLimiter)
        except Exception as error:
            ok, why = False, f"raised {type(error).__name__}: {error}"
        passed += bool(ok)
        if not ok:
            failures.append(f"{check.__name__}: {why}")
    print(json.dumps({"passed": passed, "total": len(CHECKS), "failures": failures}))


if __name__ == "__main__":
    main()
