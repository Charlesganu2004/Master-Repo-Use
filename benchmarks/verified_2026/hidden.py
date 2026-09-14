"""Deterministic evaluator. Never copied into a model's working directory."""
import ast
import json
import sys
import threading
import unittest


class LedgerChecks(unittest.TestCase):
    factory = None

    def ledger(self):
        return self.factory({"a": 100, "b": 30, "c": 0})

    def op(self, id="x", source="a", target="b", amount=20):
        return {"id": id, "source": source, "target": target, "amount": amount}

    def test_commit(self):
        x = self.ledger()
        self.assertEqual(x.apply([self.op()]), [True])
        self.assertEqual(x.snapshot(), {"a": 80, "b": 50, "c": 0})

    def test_duplicate_batch(self):
        x = self.ledger()
        self.assertEqual(x.apply([self.op(), self.op()]), [True, False])

    def test_replay_after_depletion(self):
        x = self.ledger()
        x.apply([self.op(amount=100)])
        self.assertEqual(x.apply([self.op(amount=100)]), [False])

    def test_conflict_rolls_back_history(self):
        x = self.ledger()
        with self.assertRaises(ValueError):
            x.apply([self.op(), self.op(amount=21)])
        self.assertEqual(x.snapshot()["a"], 100)
        self.assertEqual(x.apply([self.op()]), [True])

    def test_insufficient_rolls_back(self):
        x = self.ledger()
        with self.assertRaises(ValueError):
            x.apply([self.op(), self.op(id="y", amount=90)])
        self.assertEqual(x.snapshot()["a"], 100)
        self.assertEqual(x.apply([self.op()]), [True])

    def test_validation(self):
        bad = [None, {}, {"a": True}, {"": 1}, {"a": -1}, {"a": 1.5}]
        for item in bad:
            if item == {}:
                continue
            with self.subTest(item=item), self.assertRaises(ValueError):
                self.factory(item)
        for change in [{"amount": True}, {"amount": 0}, {"source": "z"},
                       {"target": "a"}, {"id": ""}, {"extra": 2}]:
            x = self.ledger()
            operation = self.op()
            operation.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                x.apply([self.op(id="good"), operation])
            self.assertEqual(x.snapshot()["a"], 100)

    def test_detached(self):
        balances = {"a": 100, "b": 0}
        x = self.factory(balances)
        balances["a"] = 0
        result = x.snapshot()
        result["a"] = 0
        op = self.op()
        original = dict(op)
        x.apply([op])
        self.assertEqual(op, original)
        self.assertEqual(x.snapshot()["a"], 80)

    def test_empty_and_sequential(self):
        x = self.ledger()
        self.assertEqual(x.apply([]), [])
        self.assertEqual(x.apply([self.op(amount=100),
                                 self.op("y", "b", "c", 130)]), [True, True])
        self.assertEqual(x.snapshot(), {"a": 0, "b": 0, "c": 130})


class Clock:
    def __init__(self):
        self.now = 0.0
        self.calls = 0

    def __call__(self):
        self.calls += 1
        return self.now


class LimiterChecks(unittest.TestCase):
    factory = None

    def setUp(self):
        self.clock = Clock()
        self.obj = self.factory({"a": 3, "b": 2}, 10, self.clock)

    def test_atomic_denial(self):
        self.assertIs(self.obj.acquire({"b": 2}), True)
        self.assertIs(self.obj.acquire({"a": 3, "b": 1}), False)
        self.assertIs(self.obj.acquire({"a": 3}), True)
        self.assertEqual(self.clock.calls, 3)

    def test_exact_boundary(self):
        self.obj.acquire({"a": 3})
        self.clock.now = 9.999
        self.assertIs(self.obj.acquire({"a": 1}), False)
        self.clock.now = 10
        self.assertIs(self.obj.acquire({"a": 3}), True)
        self.assertEqual(self.obj.snapshot()["events"]["a"], [[10, 3]])

    def test_all_keys_expire_on_denial(self):
        self.obj.acquire({"a": 3})
        self.clock.now = 9
        self.obj.acquire({"b": 2})
        self.clock.now = 10
        self.assertFalse(self.obj.acquire({"b": 1}))
        self.assertEqual(self.obj.snapshot(),
                         {"last": 10, "events": {"a": [], "b": [[9, 2]]}})

    def test_bad_clock_atomic(self):
        self.obj.acquire({"a": 1})
        state = self.obj.snapshot()
        for value in [-1, float("nan"), float("inf"), True, "1"]:
            self.clock.now = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.obj.acquire({"a": 1})
            self.assertEqual(self.obj.snapshot(), state)

    def test_bad_request_atomic(self):
        state = self.obj.snapshot()
        for request in [{}, None, {"a": True}, {"a": 4}, {"z": 1}, {"a": -1}]:
            with self.subTest(request=request), self.assertRaises(ValueError):
                self.obj.acquire(request)
            self.assertEqual(self.obj.snapshot(), state)

    def test_detached_restore(self):
        state = {"last": 5, "events": {"a": [[1, 2]], "b": []}}
        self.obj.restore(state)
        state["events"]["a"][0][1] = 3
        snapshot = self.obj.snapshot()
        snapshot["events"]["a"].clear()
        self.assertEqual(self.obj.snapshot()["events"]["a"], [[1, 2]])
        self.assertEqual(self.clock.calls, 0)

    def test_restore_invalid_atomic(self):
        self.obj.acquire({"a": 1})
        old = self.obj.snapshot()
        bad = [
            {"last": None, "events": {"a": [[0, 1]], "b": []}},
            {"last": 10, "events": {"a": [[0, 1]], "b": []}},
            {"last": 5, "events": {"a": [[6, 1]], "b": []}},
            {"last": 5, "events": {"a": [[2, 2], [1, 1]], "b": []}},
            {"last": 5, "events": {"a": [[2, 4]], "b": []}},
            {"last": 5, "events": {"a": [[2, True]], "b": []}},
            {"last": 5, "events": {"a": []}},
            {"last": float("nan"), "events": {"a": [], "b": []}},
        ]
        for state in bad:
            with self.subTest(state=state), self.assertRaises(ValueError):
                self.obj.restore(state)
            self.assertEqual(self.obj.snapshot(), old)

    def test_constructor_validation(self):
        for limits, window in [({}, 1), ({"a": True}, 1), ({"": 2}, 1),
                               ({"a": 1}, True), ({"a": 1}, float("inf")),
                               ({"a": 1}, 0)]:
            with self.subTest(limits=limits, window=window), self.assertRaises(ValueError):
                self.factory(limits, window, self.clock)

    def test_concurrent(self):
        obj = self.factory({"a": 25, "b": 25}, 10, self.clock)
        barrier = threading.Barrier(8)
        counts, errors = [], []
        lock = threading.Lock()

        def worker():
            try:
                barrier.wait(timeout=5)
                result = sum(obj.acquire({"a": 1, "b": 1}) for _ in range(10))
                with lock:
                    counts.append(result)
            except BaseException as error:  # noqa: BLE001 - report candidate thread failures
                with lock:
                    errors.append(str(error))

        threads = [threading.Thread(target=worker, daemon=True) for _ in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=8)
        self.assertFalse(any(thread.is_alive() for thread in threads))
        self.assertEqual(errors, [])
        self.assertEqual(sum(counts), 25)


ALLOWED_IMPORTS = {"threading", "collections", "math", "copy", "time",
                   "typing", "numbers", "dataclasses", "unittest", "__future__"}


def validate_source(source):
    """Conservative accidental-side-effect gate, not an adversarial sandbox."""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""]
            if any(name.split(".")[0] not in ALLOWED_IMPORTS for name in names):
                raise ValueError("non-allowlisted import")
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id in {"open", "exec", "eval", "compile", "input", "__import__",
                                    "getattr", "setattr", "delattr", "globals", "locals", "vars"}):
            raise ValueError("unsafe builtin")
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            raise ValueError("dunder attribute access")
    return tree


def evaluate(source, task):
    tree = validate_source(source)
    namespace = {"__name__": "solution"}
    exec(compile(tree, "<candidate>", "exec"), namespace)  # noqa: S102 - bounded candidate evaluator
    cls = LedgerChecks if task == "complex" else LimiterChecks
    factory = namespace["Ledger" if task == "complex" else "Limiter"]
    case = type("CandidateChecks", (cls,), {"factory": staticmethod(factory)})
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(case)
    result = unittest.TestResult()
    suite.run(result)
    failures = [{"test": str(test), "traceback": text}
                for test, text in result.failures + result.errors]
    failed_tests = {getattr(test, "test_case", test).id() for test, _ in result.failures + result.errors}
    return {"passed": result.testsRun - len(failed_tests), "total": result.testsRun,
            "failures": failures, "all_correct": result.wasSuccessful()}


if __name__ == "__main__":
    from pathlib import Path
    try:
        print(json.dumps(evaluate(Path(sys.argv[2]).read_text(encoding="utf-8"), sys.argv[1])))
    except BaseException as error:  # noqa: BLE001 - malformed candidates score zero
        print(json.dumps({"passed": 0, "total": 8 if sys.argv[1] == "complex" else 9,
                          "failures": [str(error)], "all_correct": False}))
