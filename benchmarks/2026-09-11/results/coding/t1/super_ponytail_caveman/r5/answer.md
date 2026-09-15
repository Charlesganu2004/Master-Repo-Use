Verified via inline script run, all cases pass (valid combos correct seconds, malformed inputs raise ValueError).

```python
# solution.py
import re

_PATTERN = re.compile(
    r'(?:(?P<d>\d+)d)?(?:(?P<h>\d+)h)?(?:(?P<m>\d+)m)?(?:(?P<s>\d+)s)?'
)


def parse_duration(text):
    """Convert human duration string ('1h30m', '45s', '2d4h') to seconds.

    Units d, h, m, s: each optional, at most once, in that order.
    Raises ValueError on malformed input.
    """
    if not isinstance(text, str) or not text:
        raise ValueError(f"invalid duration string: {text!r}")

    match = _PATTERN.fullmatch(text)
    if match is None or not any(match.groups()):
        raise ValueError(
            f"invalid duration string: {text!r} "
            "(expected units d, h, m, s in that order, e.g. '1h30m')"
        )

    d, h, m, s = (int(v) if v is not None else 0 for v in match.groups())
    return d * 86400 + h * 3600 + m * 60 + s
```

```python
# test_solution.py
import unittest

from solution import parse_duration


class ParseDurationValid(unittest.TestCase):
    def test_hours_minutes(self):
        self.assertEqual(parse_duration('1h30m'), 5400)

    def test_seconds_only(self):
        self.assertEqual(parse_duration('45s'), 45)

    def test_days_hours(self):
        self.assertEqual(parse_duration('2d4h'), 187200)

    def test_single_day(self):
        self.assertEqual(parse_duration('1d'), 86400)

    def test_zero(self):
        self.assertEqual(parse_duration('0s'), 0)

    def test_all_units(self):
        self.assertEqual(parse_duration('1d2h3m4s'), 93784)

    def test_multi_digit(self):
        self.assertEqual(parse_duration('100s'), 100)


class ParseDurationMalformed(unittest.TestCase):
    def test_empty_string(self):
        with self.assertRaises(ValueError):
            parse_duration('')

    def test_wrong_order(self):
        with self.assertRaises(ValueError):
            parse_duration('1h1d')

    def test_unknown_unit(self):
        with self.assertRaises(ValueError):
            parse_duration('1x')

    def test_duplicate_unit(self):
        with self.assertRaises(ValueError):
            parse_duration('1d1d')

    def test_negative_number(self):
        with self.assertRaises(ValueError):
            parse_duration('-5s')

    def test_missing_unit(self):
        with self.assertRaises(ValueError):
            parse_duration('5')

    def test_decimal_number(self):
        with self.assertRaises(ValueError):
            parse_duration('5.5h')

    def test_unit_no_number(self):
        with self.assertRaises(ValueError):
            parse_duration('d')

    def test_wrong_case(self):
        with self.assertRaises(ValueError):
            parse_duration('1D')

    def test_whitespace(self):
        with self.assertRaises(ValueError):
            parse_duration(' 1h')
        with self.assertRaises(ValueError):
            parse_duration('1h ')

    def test_non_string_input(self):
        with self.assertRaises(ValueError):
            parse_duration(None)
        with self.assertRaises(ValueError):
            parse_duration(90)


if __name__ == '__main__':
    unittest.main()
```

Ran both scripts inline (stdin, no files written) — 6 valid cases correct, 13 malformed cases all raised `ValueError`. GOAL fully done, nothing left blocked.