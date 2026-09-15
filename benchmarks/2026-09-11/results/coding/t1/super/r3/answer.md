Ran the implementation against 7 valid and 14 malformed cases via `python - <<'EOF'` (no files touched) — all passed, including order violations, duplicate units, decimals, negatives, wrong case, and non-string input, each raising `ValueError` with a clear message.

```python
# solution.py
import re

_PATTERN = re.compile(r'^(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$')


def parse_duration(text):
    """Convert a human duration string (e.g. '1h30m', '45s', '2d4h') to seconds.

    Units are d, h, m, s; each may appear at most once and must appear in
    that order (days, then hours, then minutes, then seconds). Any unit may
    be omitted, but at least one must be present.

    Raises:
        ValueError: if text is not a non-empty string matching that grammar.
    """
    if not isinstance(text, str):
        raise ValueError(f"duration must be a string, got {type(text).__name__}")
    if text == "":
        raise ValueError("duration string is empty")

    match = _PATTERN.match(text)
    if match is None or not any(match.groups()):
        raise ValueError(
            f"invalid duration string {text!r}: expected digits followed by "
            "units d, h, m, s, each used at most once and in that order "
            "(e.g. '1d2h3m4s')"
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
        self.assertEqual(parse_duration("1h30m"), 5400)

    def test_seconds_only(self):
        self.assertEqual(parse_duration("45s"), 45)

    def test_days_hours(self):
        self.assertEqual(parse_duration("2d4h"), 2 * 86400 + 4 * 3600)

    def test_all_units(self):
        self.assertEqual(
            parse_duration("1d2h3m4s"),
            86400 + 2 * 3600 + 3 * 60 + 4,
        )

    def test_single_unit_days(self):
        self.assertEqual(parse_duration("10d"), 10 * 86400)

    def test_zero_value(self):
        self.assertEqual(parse_duration("0s"), 0)

    def test_leading_zero_digits(self):
        self.assertEqual(parse_duration("01h"), 3600)

    def test_large_numbers(self):
        self.assertEqual(parse_duration("100d"), 100 * 86400)


class TestParseDurationMalformed(unittest.TestCase):
    def test_empty_string(self):
        with self.assertRaises(ValueError):
            parse_duration("")

    def test_garbage_text(self):
        with self.assertRaises(ValueError):
            parse_duration("abc")

    def test_wrong_order(self):
        with self.assertRaises(ValueError):
            parse_duration("1h1d")

    def test_wrong_order_minutes_before_hours(self):
        with self.assertRaises(ValueError):
            parse_duration("1m2h")

    def test_duplicate_unit(self):
        with self.assertRaises(ValueError):
            parse_duration("1h2h3m")

    def test_duplicate_unit_same_letter(self):
        with self.assertRaises(ValueError):
            parse_duration("1d2d")

    def test_negative_number(self):
        with self.assertRaises(ValueError):
            parse_duration("-5s")

    def test_decimal_number(self):
        with self.assertRaises(ValueError):
            parse_duration("1.5h")

    def test_whitespace(self):
        with self.assertRaises(ValueError):
            parse_duration(" 1h")

    def test_wrong_case_unit(self):
        with self.assertRaises(ValueError):
            parse_duration("1H")

    def test_unit_without_digits(self):
        with self.assertRaises(ValueError):
            parse_duration("h")

    def test_number_without_unit(self):
        with self.assertRaises(ValueError):
            parse_duration("5")

    def test_unknown_unit(self):
        with self.assertRaises(ValueError):
            parse_duration("5x")

    def test_non_string_input(self):
        with self.assertRaises(ValueError):
            parse_duration(123)

    def test_none_input(self):
        with self.assertRaises(ValueError):
            parse_duration(None)


if __name__ == "__main__":
    unittest.main()
```

Goal status: the standing goal (parse_duration + tests) is fully delivered and verified — nothing left blocked.