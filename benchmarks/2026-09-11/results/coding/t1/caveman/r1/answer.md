Logic verified, all edge cases pass.

```python
# solution.py
import re

_PATTERN = re.compile(r'^(\d+d)?(\d+h)?(\d+m)?(\d+s)?$')
_MULTIPLIERS = {'d': 86400, 'h': 3600, 'm': 60, 's': 1}


def parse_duration(text):
    """Convert human duration string ('1h30m', '45s', '2d4h') to seconds (int).

    Units d, h, m, s each optional, each at most once, must appear in that
    order (d before h before m before s). No whitespace, no negative numbers,
    no unknown units. Raises ValueError on malformed input.
    """
    if not isinstance(text, str) or text == "":
        raise ValueError(f"invalid duration: {text!r} (expected non-empty string)")

    match = _PATTERN.match(text)
    if not match or not any(match.groups()):
        raise ValueError(
            f"invalid duration: {text!r} "
            "(expected units d,h,m,s each at most once, in that order, e.g. '1h30m')"
        )

    total_seconds = 0
    for group in match.groups():
        if group:
            value, unit = int(group[:-1]), group[-1]
            total_seconds += value * _MULTIPLIERS[unit]
    return total_seconds
```

```python
# test_solution.py
import unittest

from solution import parse_duration


class TestParseDuration(unittest.TestCase):
    def test_single_units(self):
        self.assertEqual(parse_duration('45s'), 45)
        self.assertEqual(parse_duration('1m'), 60)
        self.assertEqual(parse_duration('1h'), 3600)
        self.assertEqual(parse_duration('1d'), 86400)

    def test_combined_units(self):
        self.assertEqual(parse_duration('1h30m'), 5400)
        self.assertEqual(parse_duration('2d4h'), 187200)
        self.assertEqual(parse_duration('1d2h3m4s'), 93784)

    def test_zero_value(self):
        self.assertEqual(parse_duration('0s'), 0)

    def test_multi_digit_values(self):
        self.assertEqual(parse_duration('100d'), 100 * 86400)

    def test_empty_string_raises(self):
        with self.assertRaises(ValueError):
            parse_duration('')

    def test_unknown_unit_raises(self):
        with self.assertRaises(ValueError):
            parse_duration('30x')

    def test_duplicate_unit_raises(self):
        with self.assertRaises(ValueError):
            parse_duration('1h1h')

    def test_wrong_order_raises(self):
        with self.assertRaises(ValueError):
            parse_duration('1m1h')

    def test_missing_number_raises(self):
        with self.assertRaises(ValueError):
            parse_duration('h30m')

    def test_whitespace_raises(self):
        with self.assertRaises(ValueError):
            parse_duration(' 1h')
        with self.assertRaises(ValueError):
            parse_duration('1h ')

    def test_negative_number_raises(self):
        with self.assertRaises(ValueError):
            parse_duration('-5s')

    def test_non_string_raises(self):
        with self.assertRaises(ValueError):
            parse_duration(None)
        with self.assertRaises(ValueError):
            parse_duration(45)


if __name__ == '__main__':
    unittest.main()
```

Ran tests, all pass.