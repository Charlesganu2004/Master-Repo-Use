All 16 tests pass. Here's the implementation and tests:

```python
# solution.py
import re

_PATTERN = re.compile(r'^(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$')


def parse_duration(text):
    """Convert a human-readable duration string into a number of seconds.

    The string is made of an optional number of days, hours, minutes and
    seconds, each written as digits followed by its unit letter (d, h, m,
    s). Units that are present must appear at most once and in that
    order, e.g. '1d2h3m4s', '1h30m', '2d4h', '45s'. Surrounding
    whitespace is ignored.

    Raises:
        ValueError: if `text` is not a string, is empty/whitespace-only,
            uses an unknown unit or non-integer value, repeats a unit,
            or lists units out of order.
    """
    if not isinstance(text, str):
        raise ValueError(f"duration must be a string, got {type(text).__name__}")

    stripped = text.strip()
    if not stripped:
        raise ValueError("duration string is empty")

    match = _PATTERN.match(stripped)
    if not match or not any(match.groups()):
        raise ValueError(
            f"invalid duration {text!r}: expected digits followed by "
            "d/h/m/s units in that order, e.g. '1h30m'"
        )

    days, hours, minutes, seconds = (int(g) if g else 0 for g in match.groups())
    return days * 86400 + hours * 3600 + minutes * 60 + seconds
```

```python
# test_solution.py
import unittest

from solution import parse_duration


class TestParseDuration(unittest.TestCase):
    def test_single_units(self):
        self.assertEqual(parse_duration('45s'), 45)
        self.assertEqual(parse_duration('10m'), 600)
        self.assertEqual(parse_duration('3h'), 10800)
        self.assertEqual(parse_duration('2d'), 172800)

    def test_combined_units(self):
        self.assertEqual(parse_duration('1h30m'), 5400)
        self.assertEqual(parse_duration('2d4h'), 187200)
        self.assertEqual(parse_duration('1d2h3m4s'), 93784)

    def test_zero_values(self):
        self.assertEqual(parse_duration('0s'), 0)
        self.assertEqual(parse_duration('0d0h0m0s'), 0)

    def test_whitespace_is_stripped(self):
        self.assertEqual(parse_duration('  1h30m  '), 5400)

    def test_empty_string_raises(self):
        with self.assertRaises(ValueError):
            parse_duration('')
        with self.assertRaises(ValueError):
            parse_duration('   ')

    def test_wrong_unit_order_raises(self):
        with self.assertRaises(ValueError):
            parse_duration('30m1h')

    def test_duplicate_unit_raises(self):
        with self.assertRaises(ValueError):
            parse_duration('1h1h')

    def test_unknown_unit_raises(self):
        with self.assertRaises(ValueError):
            parse_duration('1x')

    def test_non_integer_value_raises(self):
        with self.assertRaises(ValueError):
            parse_duration('1.5h')

    def test_no_unit_raises(self):
        with self.assertRaises(ValueError):
            parse_duration('5')

    def test_missing_number_raises(self):
        with self.assertRaises(ValueError):
            parse_duration('h')
        with self.assertRaises(ValueError):
            parse_duration('d5')

    def test_garbage_input_raises(self):
        with self.assertRaises(ValueError):
            parse_duration('abc')

    def test_wrong_case_raises(self):
        with self.assertRaises(ValueError):
            parse_duration('1H30M')

    def test_negative_number_raises(self):
        with self.assertRaises(ValueError):
            parse_duration('-5s')

    def test_trailing_garbage_raises(self):
        with self.assertRaises(ValueError):
            parse_duration('5d3h2m1s6')

    def test_non_string_input_raises(self):
        with self.assertRaises(ValueError):
            parse_duration(None)
        with self.assertRaises(ValueError):
            parse_duration(123)


if __name__ == '__main__':
    unittest.main()
```

Notes on design:
- A single regex `^(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$` enforces both "each unit at most once" and "in d, h, m, s order" simultaneously — if units are out of order or repeated, the leftover characters can't match the anchored `$`, so the whole match fails.
- Empty/whitespace-only input, unknown units, decimal or negative numbers, and non-string input all raise `ValueError` with a descriptive message.
- I verified the implementation with a 16-case `unittest` run (all passing) via a piped Python heredoc — no files were created or modified in the process, per your instructions.