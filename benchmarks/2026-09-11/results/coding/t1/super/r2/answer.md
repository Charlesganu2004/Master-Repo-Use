Verified: 14 unit tests pass (`Ran 14 tests in 0.001s / OK`), plus a manual check of 7 valid strings and 15 malformed-input cases, all matching expected behavior.

Skills applied: master-plan (designed the parsing approach — regex-driven contiguous match with order/duplicate tracking — before writing code), master-full-output (complete implementation and full test file, no elisions), master-anti-slop (no filler, descriptive error messages instead of generic ones), verify-before-complete (ran the actual test suite via PowerShell/python, quoted the real output above), master-review (checked empty string, non-string input, missing unit, missing number, wrong order, duplicates, trailing/internal garbage, and non-integer values as the error paths).

```python
# solution.py
import re

_UNIT_SECONDS = {"d": 86400, "h": 3600, "m": 60, "s": 1}
_UNIT_ORDER = "dhms"
_UNIT_PATTERN = re.compile(r"(\d+)([dhms])")


def parse_duration(text):
    """Convert a human duration string like '1h30m' into an integer number of seconds.

    Units are d (days), h (hours), m (minutes), s (seconds). Each unit may
    appear at most once, and units that are present must appear in the order
    d, h, m, s (e.g. '2d4h' is valid, '4h2d' is not).

    Raises:
        ValueError: if text is not a string, is empty, contains an unknown
            unit, repeats a unit, presents units out of order, or contains
            any other malformed content (missing number, missing unit,
            stray characters, non-integer numbers, etc).
    """
    if not isinstance(text, str):
        raise ValueError(f"duration must be a string, got {type(text).__name__}")
    if text == "":
        raise ValueError("duration string is empty")

    pos = 0
    seen_units = []
    total_seconds = 0

    for match in _UNIT_PATTERN.finditer(text):
        if match.start() != pos:
            raise ValueError(
                f"invalid duration {text!r}: unexpected characters at position {pos}"
            )

        number_str, unit = match.groups()

        if unit in seen_units:
            raise ValueError(
                f"invalid duration {text!r}: unit {unit!r} appears more than once"
            )
        if seen_units and _UNIT_ORDER.index(unit) < _UNIT_ORDER.index(seen_units[-1]):
            raise ValueError(
                f"invalid duration {text!r}: units must appear in order d, h, m, s"
            )

        seen_units.append(unit)
        total_seconds += int(number_str) * _UNIT_SECONDS[unit]
        pos = match.end()

    if pos != len(text):
        raise ValueError(
            f"invalid duration {text!r}: unexpected characters at position {pos}"
        )
    if not seen_units:
        raise ValueError(f"invalid duration {text!r}: no valid unit found")

    return total_seconds
```

```python
# test_solution.py
import unittest

from solution import parse_duration


class TestParseDuration(unittest.TestCase):
    def test_single_units(self):
        self.assertEqual(parse_duration("45s"), 45)
        self.assertEqual(parse_duration("10m"), 600)
        self.assertEqual(parse_duration("3h"), 10800)
        self.assertEqual(parse_duration("2d"), 172800)

    def test_combined_units(self):
        self.assertEqual(parse_duration("1h30m"), 5400)
        self.assertEqual(parse_duration("2d4h"), 187200)
        self.assertEqual(parse_duration("2d4h30m15s"), 189015)
        self.assertEqual(parse_duration("1d1s"), 86401)

    def test_zero_values(self):
        self.assertEqual(parse_duration("0s"), 0)
        self.assertEqual(parse_duration("0d0h0m0s"), 0)

    def test_leading_zeros(self):
        self.assertEqual(parse_duration("007h"), 25200)

    def test_empty_string(self):
        with self.assertRaises(ValueError):
            parse_duration("")

    def test_non_string_input(self):
        with self.assertRaises(ValueError):
            parse_duration(None)
        with self.assertRaises(ValueError):
            parse_duration(90)

    def test_missing_unit(self):
        with self.assertRaises(ValueError):
            parse_duration("100")

    def test_missing_number(self):
        with self.assertRaises(ValueError):
            parse_duration("h")
        with self.assertRaises(ValueError):
            parse_duration("30mh")

    def test_unknown_unit(self):
        with self.assertRaises(ValueError):
            parse_duration("1x")
        with self.assertRaises(ValueError):
            parse_duration("1y2h")

    def test_wrong_order(self):
        with self.assertRaises(ValueError):
            parse_duration("30m1h")
        with self.assertRaises(ValueError):
            parse_duration("1s1d")

    def test_duplicate_unit(self):
        with self.assertRaises(ValueError):
            parse_duration("1h2h")
        with self.assertRaises(ValueError):
            parse_duration("1d1h1m1s1d")

    def test_trailing_garbage(self):
        with self.assertRaises(ValueError):
            parse_duration("1h5")
        with self.assertRaises(ValueError):
            parse_duration("1h ")

    def test_internal_garbage(self):
        with self.assertRaises(ValueError):
            parse_duration("1 h30m")
        with self.assertRaises(ValueError):
            parse_duration("1h,30m")

    def test_non_integer_values(self):
        with self.assertRaises(ValueError):
            parse_duration("1.5h")
        with self.assertRaises(ValueError):
            parse_duration("-5h")


if __name__ == "__main__":
    unittest.main()
```

GOAL status: fully done, nothing left blocked. `parse_duration` handles d/h/m/s in strict order, each at most once, returns an int, and raises `ValueError` with a specific message for every malformed case tried (empty, non-string, missing number, missing unit, unknown unit, out-of-order units, duplicate units, trailing/internal garbage, non-integer/negative values). Both code blocks were executed together — all 14 tests pass.