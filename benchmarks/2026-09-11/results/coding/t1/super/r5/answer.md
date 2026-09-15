Ran the implementation and edge cases directly in Python (see output above) before writing this — all valid cases compute the right totals and every malformed case raises `ValueError` with a specific message.

```python
# solution.py
import re

_PATTERN = re.compile(
    r'^(?:(?P<days>\d+)d)?'
    r'(?:(?P<hours>\d+)h)?'
    r'(?:(?P<minutes>\d+)m)?'
    r'(?:(?P<seconds>\d+)s)?$'
)


def parse_duration(text):
    """Convert a human duration string like '1h30m', '45s', '2d4h' into seconds.

    Units are d, h, m, s. Each unit may appear at most once, and units that
    appear must be in that order (days, then hours, then minutes, then
    seconds). Raises ValueError for anything else: empty string, unknown
    units, duplicated units, out-of-order units, negative numbers, or
    non-string input.
    """
    if not isinstance(text, str):
        raise ValueError(f"duration must be a string, got {type(text).__name__}")
    if text == "":
        raise ValueError("duration string is empty")

    match = _PATTERN.fullmatch(text)
    if match is None or not any(match.groups()):
        raise ValueError(
            f"invalid duration string {text!r}: expected units d, h, m, s, "
            "each used at most once and in that order (e.g. '1h30m')"
        )

    days, hours, minutes, seconds = (int(g) if g else 0 for g in match.groups())
    return days * 86400 + hours * 3600 + minutes * 60 + seconds
```

```python
# test_solution.py
import unittest

from solution import parse_duration


class TestParseDurationValid(unittest.TestCase):
    def test_hours_and_minutes(self):
        self.assertEqual(parse_duration("1h30m"), 5400)

    def test_seconds_only(self):
        self.assertEqual(parse_duration("45s"), 45)

    def test_days_and_hours(self):
        self.assertEqual(parse_duration("2d4h"), 187200)

    def test_all_four_units(self):
        self.assertEqual(parse_duration("1d2h3m4s"), 93784)

    def test_single_unit_zero(self):
        self.assertEqual(parse_duration("0s"), 0)

    def test_days_only(self):
        self.assertEqual(parse_duration("10d"), 864000)

    def test_multi_digit_values(self):
        self.assertEqual(parse_duration("100m"), 6000)


class TestParseDurationMalformed(unittest.TestCase):
    def test_empty_string(self):
        with self.assertRaises(ValueError):
            parse_duration("")

    def test_garbage_text(self):
        with self.assertRaises(ValueError):
            parse_duration("abc")

    def test_unknown_unit(self):
        with self.assertRaises(ValueError):
            parse_duration("1x")

    def test_wrong_order(self):
        with self.assertRaises(ValueError):
            parse_duration("1h1d")

    def test_duplicate_unit(self):
        with self.assertRaises(ValueError):
            parse_duration("1h1h")

    def test_negative_number(self):
        with self.assertRaises(ValueError):
            parse_duration("-5h")

    def test_number_without_unit(self):
        with self.assertRaises(ValueError):
            parse_duration("5")

    def test_whitespace_only(self):
        with self.assertRaises(ValueError):
            parse_duration(" ")

    def test_uppercase_unit(self):
        with self.assertRaises(ValueError):
            parse_duration("1H")

    def test_trailing_digits_no_unit(self):
        with self.assertRaises(ValueError):
            parse_duration("1h30")

    def test_repeated_full_pattern(self):
        with self.assertRaises(ValueError):
            parse_duration("1d1h1m1s1d")

    def test_non_string_input(self):
        with self.assertRaises(ValueError):
            parse_duration(123)

    def test_none_input(self):
        with self.assertRaises(ValueError):
            parse_duration(None)


if __name__ == "__main__":
    unittest.main()
```

Approach: one fullmatch regex with four optional groups in the fixed order d/h/m/s, each `\d+`. Order and no-duplication fall out of the regex shape itself rather than separate checks; empty/all-groups-empty is rejected explicitly so `""` doesn't slip through as "zero seconds."

Skills applied: `master-plan` (worked the regex-shape decision before coding), `verify-before-complete` (ran the function and 13 malformed cases live in Python before writing this, output pasted above), `master-anti-slop`/`master-full-output` (no placeholders, both files complete).