```python
# solution.py
"""Parse simple human-readable duration strings into whole seconds."""

import re

_DURATION_RE = re.compile(
    r"^(?:(?P<days>\d+)d)?(?:(?P<hours>\d+)h)?(?:(?P<minutes>\d+)m)?(?:(?P<seconds>\d+)s)?$"
)
_UNIT_SECONDS = {"days": 86400, "hours": 3600, "minutes": 60, "seconds": 1}


def parse_duration(text):
    """Convert a duration string like '1h30m', '45s', '2d4h' into seconds.

    Units d (days), h (hours), m (minutes), s (seconds) may each appear at
    most once, and must appear in that order (d, h, m, s). Raises
    ValueError for anything that doesn't fit that shape.
    """
    if not isinstance(text, str):
        raise ValueError(f"duration must be a string, got {type(text).__name__}")

    match = _DURATION_RE.fullmatch(text)
    if not match or not any(match.groups()):
        raise ValueError(
            f"invalid duration string {text!r}: expected units d/h/m/s, each "
            "used at most once and in that order, e.g. '1h30m', '2d4h', '45s'"
        )

    return sum(
        int(value) * _UNIT_SECONDS[unit]
        for unit, value in match.groupdict().items()
        if value is not None
    )
```

```python
# test_solution.py
import unittest

from solution import parse_duration


class ParseDurationValidCases(unittest.TestCase):
    def test_hours_and_minutes(self):
        self.assertEqual(parse_duration("1h30m"), 5400)

    def test_seconds_only(self):
        self.assertEqual(parse_duration("45s"), 45)

    def test_days_and_hours(self):
        self.assertEqual(parse_duration("2d4h"), 2 * 86400 + 4 * 3600)

    def test_all_units(self):
        self.assertEqual(
            parse_duration("1d2h3m4s"), 86400 + 2 * 3600 + 3 * 60 + 4
        )

    def test_single_units(self):
        self.assertEqual(parse_duration("5d"), 5 * 86400)
        self.assertEqual(parse_duration("5h"), 5 * 3600)
        self.assertEqual(parse_duration("5m"), 5 * 60)
        self.assertEqual(parse_duration("5s"), 5)

    def test_zero_value(self):
        self.assertEqual(parse_duration("0s"), 0)

    def test_multi_digit_values(self):
        self.assertEqual(parse_duration("100d"), 100 * 86400)


class ParseDurationMalformedCases(unittest.TestCase):
    def test_empty_string(self):
        with self.assertRaises(ValueError):
            parse_duration("")

    def test_wrong_unit_order(self):
        with self.assertRaises(ValueError):
            parse_duration("30m1h")

    def test_unknown_unit(self):
        with self.assertRaises(ValueError):
            parse_duration("10x")

    def test_duplicate_unit(self):
        with self.assertRaises(ValueError):
            parse_duration("1h2h")

    def test_missing_unit_letter(self):
        with self.assertRaises(ValueError):
            parse_duration("100")

    def test_negative_number(self):
        with self.assertRaises(ValueError):
            parse_duration("-5s")

    def test_whitespace(self):
        with self.assertRaises(ValueError):
            parse_duration(" 1h")
        with self.assertRaises(ValueError):
            parse_duration("1h ")

    def test_uppercase_unit(self):
        with self.assertRaises(ValueError):
            parse_duration("1H")

    def test_letter_only(self):
        with self.assertRaises(ValueError):
            parse_duration("h")

    def test_non_string_input(self):
        with self.assertRaises(ValueError):
            parse_duration(5)
        with self.assertRaises(ValueError):
            parse_duration(None)

    def test_error_message_mentions_the_bad_input(self):
        with self.assertRaisesRegex(ValueError, "30m1h"):
            parse_duration("30m1h")


if __name__ == "__main__":
    unittest.main()
```

Ran both files in the scratchpad with `python -m unittest test_solution -v`: 18/18 passed.

One regex (`re.fullmatch`, stdlib) does validation and parsing in one pass — ordering, duplicates, unknown units, and negative/garbage values all fall out of the pattern itself, no manual state machine needed → skipped: locale/whitespace tolerance, fractional units; add if a spec calls for them.

Skills applied: master-plan (read the shape before coding — one regex covers ordering+dedup+validation), master-full-output (both files complete, no elisions), verify-before-complete (ran the real test suite, quoted the 18/18 OK output above), master-anti-slop (no filler, no invented extra API surface).