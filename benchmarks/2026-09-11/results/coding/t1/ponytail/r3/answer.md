Logic verified. Regex enforces d→h→m→s order, each unit at most once, rejects empty/garbage/whitespace/negatives/floats.

```python
# solution.py
import re

_PATTERN = re.compile(r'(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?')


def parse_duration(text):
    """Convert a duration string like '1h30m', '45s', '2d4h' into seconds.

    Units are d, h, m, s; each may appear at most once and must appear in
    that order. Raises ValueError for malformed input.
    """
    if not isinstance(text, str) or not text:
        raise ValueError(f"invalid duration string: {text!r}")

    match = _PATTERN.fullmatch(text)
    if not match or not any(match.groups()):
        raise ValueError(f"invalid duration string: {text!r}")

    days, hours, minutes, seconds = (int(g) if g else 0 for g in match.groups())
    return days * 86400 + hours * 3600 + minutes * 60 + seconds
```

```python
# test_solution.py
import unittest

from solution import parse_duration


class ParseDurationTests(unittest.TestCase):
    def test_single_units(self):
        self.assertEqual(parse_duration('45s'), 45)
        self.assertEqual(parse_duration('5m'), 300)
        self.assertEqual(parse_duration('2h'), 7200)
        self.assertEqual(parse_duration('1d'), 86400)

    def test_combined_units(self):
        self.assertEqual(parse_duration('1h30m'), 5400)
        self.assertEqual(parse_duration('2d4h'), 187200)
        self.assertEqual(parse_duration('1d2h3m4s'), 93784)

    def test_zero(self):
        self.assertEqual(parse_duration('0s'), 0)

    def test_malformed_raises(self):
        for bad in ['', 'abc', '30m1h', '1h1h', '10x', '1.5h',
                    ' 1h', '1h ', 'h', '1', '-1h']:
            with self.assertRaises(ValueError):
                parse_duration(bad)


if __name__ == '__main__':
    unittest.main()
```

`skipped: whitespace-tolerant parsing / float units, add if inputs come from users who type them that way.`