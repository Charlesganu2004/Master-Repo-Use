All checks pass. Here's the implementation and tests.

```python
# solution.py
import re

# order enforced: d, h, m, s — each optional, each at most once
_PATTERN = re.compile(r'(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?')


def parse_duration(text):
    """Convert a duration string like '1h30m', '45s', '2d4h' into seconds.

    Units d, h, m, s each appear at most once, in that order.
    Raises ValueError for anything else.
    """
    if not isinstance(text, str):
        raise ValueError(f"duration must be a string, got {type(text).__name__}")

    match = _PATTERN.fullmatch(text)
    if not match or not any(match.groups()):
        raise ValueError(f"invalid duration string: {text!r}")

    days, hours, minutes, seconds = (int(p) if p else 0 for p in match.groups())
    return days * 86400 + hours * 3600 + minutes * 60 + seconds
```

```python
# test_solution.py
import unittest
from solution import parse_duration


class ParseDurationTests(unittest.TestCase):
    def test_valid_combinations(self):
        self.assertEqual(parse_duration("1h30m"), 5400)
        self.assertEqual(parse_duration("45s"), 45)
        self.assertEqual(parse_duration("2d4h"), 187200)
        self.assertEqual(parse_duration("1d"), 86400)
        self.assertEqual(parse_duration("0s"), 0)
        self.assertEqual(parse_duration("007h"), 25200)  # leading zeros ok

    def test_rejects_wrong_order(self):
        with self.assertRaises(ValueError):
            parse_duration("30m1h")

    def test_rejects_duplicate_unit(self):
        with self.assertRaises(ValueError):
            parse_duration("1h2h")

    def test_rejects_unknown_unit(self):
        with self.assertRaises(ValueError):
            parse_duration("1x")
        with self.assertRaises(ValueError):
            parse_duration("1D")  # case sensitive

    def test_rejects_empty_and_junk(self):
        with self.assertRaises(ValueError):
            parse_duration("")
        with self.assertRaises(ValueError):
            parse_duration("abc")
        with self.assertRaises(ValueError):
            parse_duration(" ")
        with self.assertRaises(ValueError):
            parse_duration("1h 30m")

    def test_rejects_negative(self):
        with self.assertRaises(ValueError):
            parse_duration("-1h")

    def test_rejects_non_string(self):
        with self.assertRaises(ValueError):
            parse_duration(None)
        with self.assertRaises(ValueError):
            parse_duration(5)


if __name__ == "__main__":
    unittest.main()
```

Ran both through Python locally — all pass. Skipped fractional/negative unit support and locale-specific parsing since none were requested; add if a future format needs them.