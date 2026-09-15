All 14 tests pass.

```python
# solution.py
import re

_PATTERN = re.compile(r'^(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$')


def parse_duration(text):
    """Convert duration string ('1h30m', '45s', '2d4h') to seconds (int).

    Units: d, h, m, s. Each unit at most once, in that order (d,h,m,s).
    Raise ValueError on malformed input.
    """
    if not isinstance(text, str):
        raise ValueError(f"duration must be a string, got {type(text).__name__}")
    if text == "":
        raise ValueError("duration string is empty")

    match = _PATTERN.match(text)
    if not match or not any(match.groups()):
        raise ValueError(f"invalid duration string: {text!r}")

    days, hours, minutes, seconds = (int(g) if g else 0 for g in match.groups())
    return days * 86400 + hours * 3600 + minutes * 60 + seconds
```

```python
# test_solution.py
import unittest
from solution import parse_duration


class TestParseDuration(unittest.TestCase):
    def test_hours_minutes(self):
        self.assertEqual(parse_duration('1h30m'), 5400)

    def test_seconds_only(self):
        self.assertEqual(parse_duration('45s'), 45)

    def test_days_hours(self):
        self.assertEqual(parse_duration('2d4h'), 2 * 86400 + 4 * 3600)

    def test_all_units(self):
        self.assertEqual(parse_duration('1d2h3m4s'), 1 * 86400 + 2 * 3600 + 3 * 60 + 4)

    def test_zero_value(self):
        self.assertEqual(parse_duration('0s'), 0)

    def test_single_day(self):
        self.assertEqual(parse_duration('1d'), 86400)

    def test_empty_string(self):
        with self.assertRaises(ValueError):
            parse_duration('')

    def test_no_unit(self):
        with self.assertRaises(ValueError):
            parse_duration('100')

    def test_bad_unit_letter(self):
        with self.assertRaises(ValueError):
            parse_duration('5x')

    def test_wrong_order(self):
        with self.assertRaises(ValueError):
            parse_duration('30m1h')

    def test_duplicate_unit(self):
        with self.assertRaises(ValueError):
            parse_duration('1h2h')

    def test_negative_number(self):
        with self.assertRaises(ValueError):
            parse_duration('-5h')

    def test_non_string_input(self):
        with self.assertRaises(ValueError):
            parse_duration(None)

    def test_whitespace(self):
        with self.assertRaises(ValueError):
            parse_duration(' 1h')


if __name__ == '__main__':
    unittest.main()
```

Regex fix order (d,h,m,s) natural way to enforce sequence, uniqueness. Ran tests inline (Bash, no files written) — 14/14 pass.