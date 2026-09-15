All checks pass as expected. Here's the implementation and tests:

```python
# solution.py
import re

_PATTERN = re.compile(
    r'^(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$'
)


def parse_duration(text):
    """Convert a human duration string into an integer number of seconds.

    Accepts an optional days, hours, minutes and seconds component, each
    written as digits followed by its unit letter ('d', 'h', 'm', 's').
    Each unit may appear at most once, and the units that are present must
    appear in that order (e.g. '1h30m', '45s', '2d4h', '1d2h3m4s').

    Raises:
        ValueError: if `text` is not a string, is empty, contains an unknown
            unit, repeats a unit, uses units out of order, or is otherwise
            not a valid duration string.
    """
    if not isinstance(text, str):
        raise ValueError(
            f"Duration must be a string, got {type(text).__name__!r}"
        )
    if text == "":
        raise ValueError("Duration string is empty")

    match = _PATTERN.match(text)
    if not match or not any(match.groups()):
        raise ValueError(
            f"Invalid duration string {text!r}: expected units 'd', 'h', "
            "'m', 's' (each optional, each at most once, in that order), "
            "e.g. '1h30m', '45s', '2d4h'"
        )

    days, hours, minutes, seconds = (
        int(group) if group is not None else 0 for group in match.groups()
    )
    return days * 86400 + hours * 3600 + minutes * 60 + seconds
```

```python
# test_solution.py
import unittest

from solution import parse_duration


class TestParseDurationValid(unittest.TestCase):
    def test_examples_from_spec(self):
        self.assertEqual(parse_duration('1h30m'), 5400)
        self.assertEqual(parse_duration('45s'), 45)
        self.assertEqual(parse_duration('2d4h'), 187200)

    def test_single_units(self):
        self.assertEqual(parse_duration('5d'), 5 * 86400)
        self.assertEqual(parse_duration('5h'), 5 * 3600)
        self.assertEqual(parse_duration('5m'), 5 * 60)
        self.assertEqual(parse_duration('5s'), 5)

    def test_all_units_combined(self):
        self.assertEqual(parse_duration('1d2h3m4s'), 86400 + 7200 + 180 + 4)

    def test_zero_value(self):
        self.assertEqual(parse_duration('0s'), 0)
        self.assertEqual(parse_duration('0d0h0m0s'), 0)

    def test_large_numbers(self):
        self.assertEqual(parse_duration('100d'), 100 * 86400)
        self.assertEqual(parse_duration('999h'), 999 * 3600)

    def test_leading_zeros_in_value(self):
        self.assertEqual(parse_duration('01h05m'), 3600 + 300)


class TestParseDurationInvalid(unittest.TestCase):
    def test_empty_string(self):
        with self.assertRaises(ValueError):
            parse_duration('')

    def test_missing_unit(self):
        with self.assertRaises(ValueError):
            parse_duration('30')

    def test_unknown_unit(self):
        with self.assertRaises(ValueError):
            parse_duration('30x')

    def test_units_out_of_order(self):
        with self.assertRaises(ValueError):
            parse_duration('30m1h')
        with self.assertRaises(ValueError):
            parse_duration('1s1d')

    def test_duplicate_unit(self):
        with self.assertRaises(ValueError):
            parse_duration('1h2h')
        with self.assertRaises(ValueError):
            parse_duration('1h30m2h')

    def test_negative_number(self):
        with self.assertRaises(ValueError):
            parse_duration('-5s')

    def test_decimal_number(self):
        with self.assertRaises(ValueError):
            parse_duration('1.5h')

    def test_whitespace(self):
        with self.assertRaises(ValueError):
            parse_duration(' 1h')
        with self.assertRaises(ValueError):
            parse_duration('1h ')

    def test_unit_with_no_digits(self):
        with self.assertRaises(ValueError):
            parse_duration('h')
        with self.assertRaises(ValueError):
            parse_duration('d')

    def test_non_string_input(self):
        with self.assertRaises(ValueError):
            parse_duration(None)
        with self.assertRaises(ValueError):
            parse_duration(100)

    def test_error_message_is_informative(self):
        with self.assertRaisesRegex(ValueError, 'empty'):
            parse_duration('')
        with self.assertRaisesRegex(ValueError, "Invalid duration string"):
            parse_duration('30x')


if __name__ == '__main__':
    unittest.main()
```

Notes on the design:
- The regex `^(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$` enforces the `d, h, m, s` ordering and "at most once" rule structurally — each unit group can only be matched once and only in that position, so `1h2h` or `30m1h` fail to fully match and fall through to the error path.
- An all-empty match (e.g. from an empty string) is explicitly rejected rather than silently returning `0`.
- Non-string input raises `ValueError` (not `TypeError`) per the spec's requirement that malformed input raises `ValueError`.

I ran both the core logic and the full equivalent-test battery locally (`python /tmp/check_solution.py`) — all valid cases compute the expected seconds and all invalid cases raise `ValueError` with a descriptive message, matching what `test_solution.py` asserts. No files were created or modified in your project; the scratch check lived only at `/tmp/check_solution.py`.