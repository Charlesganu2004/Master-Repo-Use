"""Hidden checks for task t1, parse_duration. The model never sees these.

Only cases the prompt decides are here. The prompt says units d, h, m, s, each
at most once and in that order, an integer result, and ValueError with a clear
message for malformed input. Whitespace, fractions and a bare number are left
out on purpose: the prompt does not settle them, and scoring an answer on a
choice it was never asked to make would measure luck.

    python hidden_t1.py <directory containing solution.py>

prints one JSON object: passed, total and the failing cases.
"""
import importlib
import json
import sys

VALID = [
    ("1h30m", 5400), ("45s", 45), ("2d4h", 187200), ("1d", 86400),
    ("1d2h3m4s", 93784), ("10m", 600), ("0s", 0), ("100h", 360000),
    ("2h45s", 7245), ("3d15m", 260100),
]
INVALID = ["", "abc", "1x", "h", "1h1h", "30m1h", "-1h", "d1", "1hh", "m30"]


def main() -> None:
    sys.path.insert(0, sys.argv[1])
    results = []
    try:
        parse = importlib.import_module("solution").parse_duration
    except Exception as error:  # the answer did not produce an importable function
        print(json.dumps({"passed": 0, "total": len(VALID) + len(INVALID) + 1,
                          "failures": [f"import: {type(error).__name__}: {error}"]}))
        return
    for text, expected in VALID:
        try:
            got = parse(text)
            ok = got == expected and isinstance(got, int) and not isinstance(got, bool)
            results.append((f"valid {text!r}", ok, f"got {got!r}, expected {expected}"))
        except Exception as error:
            results.append((f"valid {text!r}", False, f"raised {type(error).__name__}: {error}"))
    for text in INVALID:
        try:
            got = parse(text)
            results.append((f"invalid {text!r}", False, f"returned {got!r}"))
        except ValueError as error:
            results.append((f"invalid {text!r}", bool(str(error).strip()), "empty message"))
        except Exception as error:
            results.append((f"invalid {text!r}", False, f"raised {type(error).__name__}, not ValueError"))
    try:
        parse(None)
        results.append(("None is rejected", False, "returned for None"))
    except (ValueError, TypeError):
        results.append(("None is rejected", True, ""))
    except Exception as error:
        results.append(("None is rejected", False, f"raised {type(error).__name__}"))
    failures = [f"{name}: {why}" for name, ok, why in results if not ok]
    print(json.dumps({"passed": sum(ok for _, ok, _ in results), "total": len(results),
                      "failures": failures}))


if __name__ == "__main__":
    main()
