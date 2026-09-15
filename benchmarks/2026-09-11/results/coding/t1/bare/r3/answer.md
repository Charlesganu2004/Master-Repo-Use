All 18 tests pass. Here's the implementation and its tests.

```python
# solution.py
"""Parse human-readable duration strings into a number of seconds."""

import re

# Units must appear in the order d, h, m, s, each at most once.
_PATTERN = re.compile(
    r'^(?:(?P<days>\d+)d)?(?:(?P<hours>\d+)h)?(?:(?P<minutes>\d+)m)?(?:(?P<seconds>\d+)s)?$'
)


def parse_duration(text):
    """Convert a human duration string into an integer number of seconds.

    Accepts strings built from the units d (days), h (hours), m (minutes),
    and s (seconds). Each unit may appear at most once, and any units that
    are present must appear in the order d, h, m, s (though any subset of
    them may be omitted), e.g. '1h30m', '45s', '2d4h', '1d2h3m4s'.

    Args:
        text: The duration string to parse.

    Returns:
        The total duration in seconds, as an int.

    Raises:
        ValueError: If ``text`` is not a string, is empty/blank, contains no
            recognized units, has units out of order, repeats a unit,
            contains a negative or non-integer value, or otherwise doesn't
            match the expected format.
    """
    if not isinstance(text, str):
        raise ValueError(f"Duration must be a string, got {type(text).__name__!r}")

    stripped = text.strip()
    if not stripped:
        raise ValueError("Duration string is empty")

    match = _PATTERN.fullmatch(stripped)
    if match is None or not any(match.groups()):
        raise ValueError(
            f"Invalid duration string {text!r}: expected units d, h, m, s "
            "(each at most once, in that order), e.g. '1h30m'"
        )

    days, hours, minutes, seconds = (int(g) if g else 0 for g in match.groups())
    return days * 86400 + hours * 3600 + minutes * 60 + seconds
```

```python
# test_solution.py
import unittest

from solution import parse_duration


class ParseDurationTests(unittest.TestCase):
    def test_hours_minutes(self):
        self.assertEqual(parse_duration('1h30m'), 5400)

    def test_seconds_only(self):
        self.assertEqual(parse_duration('45s'), 45)

    def test_days_hours(self):
        self.assertEqual(parse_duration('2d4h'), 2 * 86400 + 4 * 3600)

    def test_all_units(self):
        self.assertEqual(parse_duration('1d2h3m4s'), 86400 + 2 * 3600 + 3 * 60 + 4)

    def test_zero_value(self):
        self.assertEqual(parse_duration('0s'), 0)

    def test_single_unit_each(self):
        self.assertEqual(parse_duration('5d'), 5 * 86400)
        self.assertEqual(parse_duration('5h'), 5 * 3600)
        self.assertEqual(parse_duration('5m'), 5 * 60)
        self.assertEqual(parse_duration('5s'), 5)

    def test_whitespace_trimmed(self):
        self.assertEqual(parse_duration('  1h  '), 3600)

    def test_empty_string_raises(self):
        with self.assertRaises(ValueError):
            parse_duration('')

    def test_garbage_raises(self):
        with self.assertRaises(ValueError):
            parse_duration('abc')

    def test_wrong_order_raises(self):
        with self.assertRaises(ValueError):
            parse_duration('30m1h')

    def test_duplicate_unit_raises(self):
        with self.assertRaises(ValueError):
            parse_duration('1h1h')

    def test_uppercase_unit_raises(self):
        with self.assertRaises(ValueError):
            parse_duration('1H')

    def test_negative_raises(self):
        with self.assertRaises(ValueError):
            parse_duration('-5s')

    def test_decimal_raises(self):
        with self.assertRaises(ValueError):
            parse_duration('1.5h')

    def test_trailing_garbage_raises(self):
        with self.assertRaises(ValueError):
            parse_duration('1h30mx')

    def test_missing_number_raises(self):
        with self.assertRaises(ValueError):
            parse_duration('h30m')

    def test_unknown_unit_raises(self):
        with self.assertRaises(ValueError):
            parse_duration('1w')

    def test_non_string_raises(self):
        with self.assertRaises(ValueError):
            parse_duration(90)


if __name__ == '__main__':
    unittest.main()
```

Notes on behavior:
- Units must appear in `d, h, m, s` order; any subset can be omitted (e.g. `'45s'`, `'2d4h'` are fine), but a present unit can't repeat and can't appear out of order.
- Input is `str.strip()`-ed, so incidental leading/trailing whitespace is tolerated, but an empty/blank string raises.
- Non-string input, decimals, negative numbers, unknown unit letters, and trailing garbage after a valid unit all raise `ValueError` with a descriptive message.

I ran the test suite locally (`python -m unittest`, 18 tests) and all pass.