Logic verified, all cases pass.

```python
# solution.py
import re

_PATTERN = re.compile(r'^(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$')


def parse_duration(text):
    """Convert a duration string like '1h30m', '45s', '2d4h' into seconds.

    Units are d (days), h (hours), m (minutes), s (seconds). Each unit may
    appear at most once, and units must appear in that order (d, h, m, s).
    All present unit values are optional individually, but at least one
    must be present.

    Raises ValueError on malformed input (unknown unit, wrong unit order,
    duplicate unit, missing digits, negative/decimal numbers, empty
    string, or non-string input).
    """
    if not isinstance(text, str):
        raise ValueError(f"duration must be a string, got {type(text).__name__}")

    match = _PATTERN.fullmatch(text)
    if match is None or not any(match.groups()):
        raise ValueError(f"invalid duration string: {text!r}")

    days, hours, minutes, seconds = (int(g) if g else 0 for g in match.groups())
    return days * 86400 + hours * 3600 + minutes * 60 + seconds
```

```python
# test_solution.py
import unittest

from solution import parse_duration


class ParseDurationValidCases(unittest.TestCase):
    def test_hours_minutes(self):
        self.assertEqual(parse_duration("1h30m"), 5400)

    def test_seconds_only(self):
        self.assertEqual(parse_duration("45s"), 45)

    def test_days_hours(self):
        self.assertEqual(parse_duration("2d4h"), 187200)

    def test_single_day(self):
        self.assertEqual(parse_duration("1d"), 86400)

    def test_zero_value(self):
        self.assertEqual(parse_duration("0s"), 0)

    def test_all_units(self):
        self.assertEqual(parse_duration("1d2h3m4s"), 93784)

    def test_multi_digit_numbers(self):
        self.assertEqual(parse_duration("100d"), 8640000)


class ParseDurationMalformedCases(unittest.TestCase):
    def test_empty_string(self):
        with self.assertRaises(ValueError):
            parse_duration("")

    def test_wrong_unit_order(self):
        with self.assertRaises(ValueError):
            parse_duration("30m1h")

    def test_duplicate_unit(self):
        with self.assertRaises(ValueError):
            parse_duration("1h2h")

    def test_unknown_unit(self):
        with self.assertRaises(ValueError):
            parse_duration("1x")

    def test_missing_number(self):
        with self.assertRaises(ValueError):
            parse_duration("h")

    def test_negative_number(self):
        with self.assertRaises(ValueError):
            parse_duration("-5s")

    def test_decimal_number(self):
        with self.assertRaises(ValueError):
            parse_duration("1.5h")

    def test_trailing_garbage(self):
        with self.assertRaises(ValueError):
            parse_duration("1h30mx")

    def test_whitespace_only(self):
        with self.assertRaises(ValueError):
            parse_duration("  ")

    def test_wrong_case_unit(self):
        with self.assertRaises(ValueError):
            parse_duration("1H")

    def test_unit_before_number(self):
        with self.assertRaises(ValueError):
            parse_duration("s1")

    def test_non_string_input(self):
        with self.assertRaises(ValueError):
            parse_duration(90)


if __name__ == "__main__":
    unittest.main()
```

GOAL check: this turn delivers full function + tests, done. Nothing left blocked.