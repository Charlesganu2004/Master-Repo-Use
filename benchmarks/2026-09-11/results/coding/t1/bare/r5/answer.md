All 14 tests pass. Here's the implementation and tests.

```python
# solution.py
"""Parse human-readable duration strings like '1h30m' into seconds."""

import re

_DURATION_RE = re.compile(r'^(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$')


def parse_duration(text):
    """Convert a human duration string into an integer number of seconds.

    Accepted units are d (days), h (hours), m (minutes) and s (seconds).
    Each unit may appear at most once, and units that are present must
    appear in the order d, h, m, s (e.g. '1h30m', '45s', '2d4h1m3s').

    Raises:
        ValueError: if `text` is not a string, is empty, uses an unknown
            unit, repeats a unit, presents units out of order, or is
            otherwise malformed (e.g. missing digits, decimal or
            negative numbers, stray whitespace).
    """
    if not isinstance(text, str):
        raise ValueError(
            f"duration must be a string, got {type(text).__name__!r}"
        )
    if text == "":
        raise ValueError("duration string is empty")

    match = _DURATION_RE.match(text)
    if not match or not any(match.groups()):
        raise ValueError(
            f"invalid duration string {text!r}: expected units d, h, m, s, "
            "each used at most once and in that order, e.g. '1h30m'"
        )

    days, hours, minutes, seconds = (
        int(group) if group else 0 for group in match.groups()
    )
    return days * 86400 + hours * 3600 + minutes * 60 + seconds
```

```python
# test_solution.py
import unittest

from solution import parse_duration


class ParseDurationTests(unittest.TestCase):
    def test_single_units(self):
        self.assertEqual(parse_duration("45s"), 45)
        self.assertEqual(parse_duration("5m"), 300)
        self.assertEqual(parse_duration("3h"), 10800)
        self.assertEqual(parse_duration("2d"), 172800)

    def test_combined_units(self):
        self.assertEqual(parse_duration("1h30m"), 5400)
        self.assertEqual(parse_duration("2d4h"), 187200)
        self.assertEqual(parse_duration("1d2h3m4s"), 93784)

    def test_zero_value(self):
        self.assertEqual(parse_duration("0s"), 0)

    def test_large_numbers(self):
        self.assertEqual(parse_duration("100d"), 100 * 86400)

    def test_empty_string_raises(self):
        with self.assertRaises(ValueError):
            parse_duration("")

    def test_unknown_unit_raises(self):
        with self.assertRaises(ValueError):
            parse_duration("1x")

    def test_wrong_order_raises(self):
        with self.assertRaises(ValueError):
            parse_duration("30m1h")

    def test_duplicate_unit_raises(self):
        with self.assertRaises(ValueError):
            parse_duration("1h1h")

    def test_decimal_number_raises(self):
        with self.assertRaises(ValueError):
            parse_duration("1.5h")

    def test_negative_number_raises(self):
        with self.assertRaises(ValueError):
            parse_duration("-5s")

    def test_missing_number_raises(self):
        with self.assertRaises(ValueError):
            parse_duration("h")

    def test_missing_unit_raises(self):
        with self.assertRaises(ValueError):
            parse_duration("100")

    def test_whitespace_raises(self):
        with self.assertRaises(ValueError):
            parse_duration(" 1h")
        with self.assertRaises(ValueError):
            parse_duration("1h ")

    def test_non_string_raises(self):
        with self.assertRaises(ValueError):
            parse_duration(5)
        with self.assertRaises(ValueError):
            parse_duration(None)


if __name__ == "__main__":
    unittest.main()
```

Notes on the design:
- A single anchored regex `^(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$` enforces both "each unit at most once" and "units in d, h, m, s order" simultaneously — if units are out of order or duplicated, the pattern can't consume the whole string and the match fails.
- `\d+` requires plain unsigned integers, so decimals (`1.5h`) and negatives (`-5s`) are rejected automatically.
- The `any(match.groups())` check catches the case where the whole string matched but contributed no unit (i.e., empty string, already handled explicitly above for a clearer message).
- I verified this with `python -m unittest`-style execution (14/14 tests passing) piped via stdin rather than writing files to disk, per your instructions.