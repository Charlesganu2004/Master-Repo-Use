Goal: parse_duration(text) → int seconds, units d/h/m/s once each in order, ValueError on bad input, plus tests. Verified via python heredoc (no files touched) — all pass cases and malformed cases work as shown above.

```python
# solution.py
import re

_PATTERN = re.compile(r'(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?')


def parse_duration(text):
    """Convert human duration string ('1h30m', '45s', '2d4h') to seconds (int).

    Units d, h, m, s each appear at most once, in that order.
    Raises ValueError on malformed input.
    """
    if not isinstance(text, str):
        raise ValueError(f"duration must be a string, got {type(text).__name__}")

    match = _PATTERN.fullmatch(text)
    if match is None:
        raise ValueError(f"invalid duration string: {text!r}")

    days, hours, minutes, seconds = match.groups()
    if days is hours is minutes is seconds is None:
        raise ValueError(f"invalid duration string: {text!r}")

    total = 0
    if days is not None:
        total += int(days) * 86400
    if hours is not None:
        total += int(hours) * 3600
    if minutes is not None:
        total += int(minutes) * 60
    if seconds is not None:
        total += int(seconds)
    return total
```

```python
# test_solution.py
import unittest
from solution import parse_duration


class TestParseDuration(unittest.TestCase):
    def test_single_units(self):
        self.assertEqual(parse_duration('45s'), 45)
        self.assertEqual(parse_duration('5m'), 300)
        self.assertEqual(parse_duration('2h'), 7200)
        self.assertEqual(parse_duration('1d'), 86400)

    def test_combined_units(self):
        self.assertEqual(parse_duration('1h30m'), 5400)
        self.assertEqual(parse_duration('2d4h'), 187200)
        self.assertEqual(parse_duration('1d2h3m4s'), 93784)

    def test_zero_value(self):
        self.assertEqual(parse_duration('0s'), 0)

    def test_malformed_empty_string(self):
        with self.assertRaises(ValueError):
            parse_duration('')

    def test_malformed_no_unit(self):
        with self.assertRaises(ValueError):
            parse_duration('5')

    def test_malformed_no_number(self):
        with self.assertRaises(ValueError):
            parse_duration('d')

    def test_malformed_wrong_order(self):
        with self.assertRaises(ValueError):
            parse_duration('30m1h')

    def test_malformed_duplicate_unit(self):
        with self.assertRaises(ValueError):
            parse_duration('1h1h')

    def test_malformed_unknown_unit(self):
        with self.assertRaises(ValueError):
            parse_duration('1x')

    def test_malformed_negative_number(self):
        with self.assertRaises(ValueError):
            parse_duration('-5s')

    def test_malformed_decimal(self):
        with self.assertRaises(ValueError):
            parse_duration('5.5h')

    def test_malformed_whitespace(self):
        with self.assertRaises(ValueError):
            parse_duration(' 5s')
        with self.assertRaises(ValueError):
            parse_duration('1h30m ')

    def test_non_string_input(self):
        with self.assertRaises(ValueError):
            parse_duration(45)


if __name__ == '__main__':
    unittest.main()
```

Skipped: no support for float/fractional units, no negative durations, no whitespace tolerance — add if a caller needs them.

Skills/tools named: Bash (ran python heredoc, no files written/read) to verify regex logic before answering, per verify-before-complete. Rest is plain stdlib (`re`, `unittest`) per ponytail ladder — no new deps needed.

GOAL status: fully done, nothing blocked.