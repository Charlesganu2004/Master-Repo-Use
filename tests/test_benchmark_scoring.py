"""The benchmark's hidden checks have to score right, or every number moves.

These run the two hidden suites against a reference solution that must score
full marks and against deliberately broken ones that must each fail only the
check aimed at them. A hidden suite that passes everything measures nothing.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
HIDDEN = ROOT / "benchmarks" / "2026-09-11" / "hidden"

GOOD_T1 = '''
import re
_R = re.compile(r"(?:(\\d+)d)?(?:(\\d+)h)?(?:(\\d+)m)?(?:(\\d+)s)?")
def parse_duration(text):
    if not isinstance(text, str) or not text:
        raise ValueError("duration must be a non-empty string")
    m = _R.fullmatch(text)
    if not m or not any(m.groups()):
        raise ValueError(f"malformed duration: {text!r}")
    return sum(int(v) * s for v, s in zip(m.groups(), (86400, 3600, 60, 1)) if v)
'''

# Finds units anywhere, so order and repeats slip through.
LOOSE_T1 = '''
import re
def parse_duration(text):
    if not text:
        raise ValueError("empty")
    return sum(int(n) * {"d": 86400, "h": 3600, "m": 60, "s": 1}[u]
               for n, u in re.findall(r"(\\d+)([dhms])", text))
'''

GOOD_T2 = '''
import threading, time
from collections import defaultdict, deque
class RateLimiter:
    def __init__(self, limit, window, clock=time.monotonic):
        self.limit, self.window, self.clock = limit, window, clock
        self.calls = defaultdict(deque)
        self.lock = threading.Lock()
    def allow(self, key):
        with self.lock:
            now = self.clock()
            q = self.calls[key]
            while q and q[0] <= now - self.window:
                q.popleft()
            if len(q) < self.limit:
                q.append(now)
                return True
            return False
'''

# Counts refused calls too, so a refusal extends the block.
COUNTS_DENIED_T2 = GOOD_T2.replace(
    "            if len(q) < self.limit:\n                q.append(now)\n                return True\n            return False",
    "            q.append(now)\n            return len(q) <= self.limit")

# No lock, so concurrent callers race past the limit.
NO_LOCK_T2 = '''
import time
from collections import defaultdict, deque
class RateLimiter:
    def __init__(self, limit, window, clock=time.monotonic):
        self.limit, self.window, self.clock = limit, window, clock
        self.calls = defaultdict(deque)
    def allow(self, key):
        now = self.clock()
        q = self.calls[key]
        while q and q[0] <= now - self.window:
            q.popleft()
        room = len(q) < self.limit
        time.sleep(0.0005)
        if room:
            q.append(now)
            return True
        return False
'''


def score(task: str, solution: str) -> dict:
    with tempfile.TemporaryDirectory(prefix="bench-score-") as tmp:
        work = pathlib.Path(tmp)
        (work / "solution.py").write_text(solution, encoding="utf-8")
        out = subprocess.run([sys.executable, str(HIDDEN / f"hidden_{task}.py"), str(work)],
                             capture_output=True, text=True, timeout=300)
        return json.loads(out.stdout.strip().splitlines()[-1])


class HiddenChecksDiscriminate(unittest.TestCase):
    def test_a_correct_parser_scores_full_marks(self):
        result = score("t1", GOOD_T1)
        self.assertEqual(result["passed"], result["total"], result["failures"])
        self.assertGreaterEqual(result["total"], 20)

    def test_a_parser_that_ignores_order_and_repeats_is_caught(self):
        result = score("t1", LOOSE_T1)
        self.assertLess(result["passed"], result["total"])
        joined = " ".join(result["failures"])
        self.assertIn("'1h1h'", joined)
        self.assertIn("'30m1h'", joined)

    def test_a_missing_function_scores_zero_rather_than_crashing(self):
        result = score("t1", "x = 1\n")
        self.assertEqual(result["passed"], 0)
        self.assertTrue(result["failures"][0].startswith("import:"))

    def test_a_correct_limiter_scores_full_marks(self):
        result = score("t2", GOOD_T2)
        self.assertEqual(result["passed"], result["total"], result["failures"])

    def test_counting_refused_calls_is_caught(self):
        result = score("t2", COUNTS_DENIED_T2)
        self.assertIn("check_denied_not_recorded", " ".join(result["failures"]))

    def test_a_limiter_without_a_lock_is_caught(self):
        result = score("t2", NO_LOCK_T2)
        self.assertIn("check_concurrent_one_key", " ".join(result["failures"]))


if __name__ == "__main__":
    unittest.main()
