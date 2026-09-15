Function use regex, enforce order d→h→m→s, each unit optional, appear once max, only digits.

```python
# solution.py
import re

_DURATION_RE = re.compile(r'(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?')


def parse_duration(text):
    """Convert a human duration string (e.g. '1h30m', '45s', '2d4h') into seconds.

    Units must be a subset of d (days), h (hours), m (minutes), s (seconds),
    each appearing at most once and in that order (d, h, m, s). Values must
    be non-negative integers.

    Raises:
        ValueError: if `text` is not a string, is empty/whitespace-only, or
            does not match the expected format.
    """
    if not isinstance(text, str):
        raise ValueError(f"duration must be a string, got {type(text).__name__!r}")

    stripped = text.strip()
    if not stripped:
        raise ValueError("duration string is empty")

    match = _DURATION_RE.fullmatch(stripped)
    if not match or not any(match.groups()):
        raise ValueError(
            f"invalid duration string {text!r}: expected units d, h, m, s "
            "in that order, each at most once, e.g. '1h30m', '45s', '2d4h'"
        )

    days, hours, minutes, seconds = (int(g) if g else 0 for g in match.groups())
    return days * 86400 + hours * 3600 + minutes * 60 + seconds
```

```python
# test_solution.py
import unittest

from solution import parse_duration


class TestParseDurationValid(unittest.TestCase):
    def test_hours_minutes(self):
        self.assertEqual(parse_duration('1h30m'), 5400)

    def test_seconds_only(self):
        self.assertEqual(parse_duration('45s'), 45)

    def test_days_hours(self):
        self.assertEqual(parse_duration('2d4h'), 187200)

    def test_days_only(self):
        self.assertEqual(parse_duration('1d'), 86400)

    def test_minutes_only(self):
        self.assertEqual(parse_duration('90m'), 5400)

    def test_zero_seconds(self):
        self.assertEqual(parse_duration('0s'), 0)

    def test_all_units(self):
        self.assertEqual(parse_duration('1d2h3m4s'), 86400 + 7200 + 180 + 4)

    def test_whitespace_trimmed(self):
        self.assertEqual(parse_duration('  1h  '), 3600)

    def test_leading_zeros(self):
        self.assertEqual(parse_duration('007s'), 7)


class TestParseDurationInvalid(unittest.TestCase):
    def test_empty_string(self):
        with self.assertRaises(ValueError):
            parse_duration('')

    def test_whitespace_only(self):
        with self.assertRaises(ValueError):
            parse_duration('   ')

    def test_missing_unit(self):
        with self.assertRaises(ValueError):
            parse_duration('30')

    def test_unknown_unit(self):
        with self.assertRaises(ValueError):
            parse_duration('5x')

    def test_garbage_text(self):
        with self.assertRaises(ValueError):
            parse_duration('abc')

    def test_duplicate_unit(self):
        with self.assertRaises(ValueError):
            parse_duration('1h1h')

    def test_duplicate_day_unit(self):
        with self.assertRaises(ValueError):
            parse_duration('1d2d3h')

    def test_wrong_order(self):
        with self.assertRaises(ValueError):
            parse_duration('1m1h')

    def test_decimal_value(self):
        with self.assertRaises(ValueError):
            parse_duration('1.5h')

    def test_negative_value(self):
        with self.assertRaises(ValueError):
            parse_duration('-5s')

    def test_internal_whitespace(self):
        with self.assertRaises(ValueError):
            parse_duration('1h 30m')

    def test_non_string_input(self):
        with self.assertRaises(ValueError):
            parse_duration(None)

    def test_error_message_mentions_offending_text(self):
        with self.assertRaisesRegex(ValueError, "5x"):
            parse_duration('5x')


if __name__ == '__main__':
    unittest.main()
```

Ran both, all cases pass (valid strings compute right, malformed raise ValueError with clear message).