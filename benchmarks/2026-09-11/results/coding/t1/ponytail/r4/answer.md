All cases behave as expected. Here's the implementation and tests.

```python
# solution.py
import re

_PATTERN = re.compile(r'^(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$')
_MULTIPLIERS = (86400, 3600, 60, 1)  # seconds per unit, matching group order d,h,m,s


def parse_duration(text):
    """Convert a duration string like '1h30m', '45s', '2d4h' into seconds.

    Units d, h, m, s are each optional but, if present, must appear at
    most once and in that order (d before h before m before s).
    Raises ValueError on any other format.
    """
    if not isinstance(text, str):
        raise ValueError(f"Duration must be a string, got {type(text).__name__}")

    match = _PATTERN.match(text)
    groups = match.groups() if match else None
    if not match or all(g is None for g in groups):
        raise ValueError(f"Invalid duration string: {text!r}")

    return sum(int(g) * mult for g, mult in zip(groups, _MULTIPLIERS) if g is not None)
```

```python
# test_solution.py
import unittest

from solution import parse_duration


class ParseDurationTests(unittest.TestCase):
    def test_single_units(self):
        self.assertEqual(parse_duration('45s'), 45)
        self.assertEqual(parse_duration('30m'), 1800)
        self.assertEqual(parse_duration('2h'), 7200)
        self.assertEqual(parse_duration('3d'), 259200)

    def test_combined_units(self):
        self.assertEqual(parse_duration('1h30m'), 5400)
        self.assertEqual(parse_duration('2d4h'), 187200)
        self.assertEqual(parse_duration('1d2h3m4s'), 93784)

    def test_zero_value(self):
        self.assertEqual(parse_duration('0s'), 0)

    def test_malformed_raises_value_error(self):
        bad_inputs = [
            '',            # empty
            'abc',         # no digits/units
            '30',          # missing unit
            '30m1h',       # wrong order
            '1h1h',        # repeated unit
            '1.5h',        # non-integer
            '-5s',         # negative
            '5x',          # unknown unit
            '1h30ms',      # trailing garbage
            '1D',          # wrong case
            '  ',          # whitespace only
        ]
        for text in bad_inputs:
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_non_string_raises_value_error(self):
        for value in (None, 5, 3.5):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_duration(value)


if __name__ == '__main__':
    unittest.main()
```

Ran both against Python 3.11 — all pass. skipped: uppercase units (`1H`) and whitespace tolerance, add if a caller needs them.