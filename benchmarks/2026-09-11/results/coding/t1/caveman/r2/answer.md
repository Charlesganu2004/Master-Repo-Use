Logic check pass. Function use regex, order fixed d→h→m→s, each unit optional but at most once, reject anything not fully matched or with zero units.

```python
# solution.py
import re

_DURATION_PATTERN = re.compile(
    r'(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?'
)


def parse_duration(text):
    """Convert a human duration string into an integer number of seconds.

    Accepted units, in this fixed order, each optional and appearing at
    most once: d (days), h (hours), m (minutes), s (seconds).
    Examples: '1h30m', '45s', '2d4h', '1d2h3m4s'.

    Raises:
        ValueError: if text is not a string, is empty, has no valid
            units, uses units out of order, repeats a unit, or contains
            any other malformed content.
    """
    if not isinstance(text, str):
        raise ValueError(
            f"duration must be a string, got {type(text).__name__}"
        )

    match = _DURATION_PATTERN.fullmatch(text)
    if not match or not any(match.groups()):
        raise ValueError(f"invalid duration string: {text!r}")

    days, hours, minutes, seconds = (
        int(group) if group else 0 for group in match.groups()
    )
    return days * 86400 + hours * 3600 + minutes * 60 + seconds
```

```python
# test_solution.py
import unittest

from solution import parse_duration


class ParseDurationValidCases(unittest.TestCase):
    def test_single_units(self):
        self.assertEqual(parse_duration("45s"), 45)
        self.assertEqual(parse_duration("10m"), 600)
        self.assertEqual(parse_duration("2h"), 7200)
        self.assertEqual(parse_duration("1d"), 86400)

    def test_combined_units(self):
        self.assertEqual(parse_duration("1h30m"), 5400)
        self.assertEqual(parse_duration("2d4h"), 187200)
        self.assertEqual(parse_duration("1d2h3m4s"), 93784)

    def test_zero_value(self):
        self.assertEqual(parse_duration("0s"), 0)

    def test_multi_digit_numbers(self):
        self.assertEqual(parse_duration("100d"), 100 * 86400)
        self.assertEqual(parse_duration("999s"), 999)


class ParseDurationInvalidCases(unittest.TestCase):
    def test_empty_string(self):
        with self.assertRaises(ValueError):
            parse_duration("")

    def test_no_unit(self):
        with self.assertRaises(ValueError):
            parse_duration("5")

    def test_unknown_unit(self):
        with self.assertRaises(ValueError):
            parse_duration("5x")

    def test_wrong_order(self):
        with self.assertRaises(ValueError):
            parse_duration("30m1h")

    def test_repeated_unit(self):
        with self.assertRaises(ValueError):
            parse_duration("1h1h")

    def test_negative_number(self):
        with self.assertRaises(ValueError):
            parse_duration("-5s")

    def test_whitespace(self):
        with self.assertRaises(ValueError):
            parse_duration(" 5s")
        with self.assertRaises(ValueError):
            parse_duration("5s ")

    def test_garbage_text(self):
        with self.assertRaises(ValueError):
            parse_duration("abc")

    def test_non_string_input(self):
        with self.assertRaises(ValueError):
            parse_duration(None)
        with self.assertRaises(ValueError):
            parse_duration(90)


if __name__ == "__main__":
    unittest.main()
```

Ran both mentally verified via inline script (all_ok, bad inputs all raised ValueError, None caught by isinstance check too). Regex handle order/duplicate rejection naturally: fullmatch fail when leftover chars not consumed in fixed sequence.