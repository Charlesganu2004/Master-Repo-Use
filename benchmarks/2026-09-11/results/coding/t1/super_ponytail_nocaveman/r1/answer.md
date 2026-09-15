All 13 tests pass (verified by running the suite above, no files created). Regex enforces d→h→m→s ordering, at-most-once units, and digit-only values in one line via optional groups; malformed input raises `ValueError`.

Skills applied: master-plan (traced the regex/edge-case shape before coding), master-design-taste N/A (no UI), ponytail ladder (stdlib `re`/`unittest`, no new deps, one-line pattern does the ordering/uniqueness validation instead of hand-rolled parsing), verify-before-complete (ran the real suite, quoted output above), master-review (checked empty string, case sensitivity, whitespace, non-string, duplicate/out-of-order units as adversarial cases).

Goal check: GOAL was exactly this function + tests — fully delivered, nothing deferred.

```python
# solution.py
import re

_PATTERN = re.compile(r'^(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$')


def parse_duration(text: str) -> int:
    """Convert a duration string like '1h30m', '45s', '2d4h' into seconds.

    Units are d, h, m, s; each may appear at most once, and only in that
    order (days before hours before minutes before seconds).

    Raises:
        ValueError: if text is not a well-formed duration string.
    """
    if not isinstance(text, str) or not text:
        raise ValueError(f"invalid duration: {text!r}")

    match = _PATTERN.match(text)
    if not match or not any(match.groups()):
        raise ValueError(f"invalid duration: {text!r}")

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
        self.assertEqual(parse_duration('30m'), 1800)
        self.assertEqual(parse_duration('2h'), 7200)
        self.assertEqual(parse_duration('3d'), 259200)

    def test_combined_units(self):
        self.assertEqual(parse_duration('1h30m'), 5400)
        self.assertEqual(parse_duration('2d4h'), 187200)
        self.assertEqual(parse_duration('1d2h3m4s'), 93784)

    def test_zero_and_leading_zero_values(self):
        self.assertEqual(parse_duration('0s'), 0)
        self.assertEqual(parse_duration('01h'), 3600)

    def test_empty_string(self):
        with self.assertRaises(ValueError):
            parse_duration('')

    def test_unknown_unit(self):
        with self.assertRaises(ValueError):
            parse_duration('1x')

    def test_wrong_order(self):
        with self.assertRaises(ValueError):
            parse_duration('30m1h')

    def test_duplicate_unit(self):
        with self.assertRaises(ValueError):
            parse_duration('1h1h')

    def test_missing_digits(self):
        with self.assertRaises(ValueError):
            parse_duration('h')

    def test_trailing_garbage(self):
        with self.assertRaises(ValueError):
            parse_duration('1d2h3m4s5x')

    def test_wrong_case(self):
        with self.assertRaises(ValueError):
            parse_duration('1H')

    def test_whitespace(self):
        with self.assertRaises(ValueError):
            parse_duration(' 1h')

    def test_non_integer_or_negative(self):
        with self.assertRaises(ValueError):
            parse_duration('1.5h')
        with self.assertRaises(ValueError):
            parse_duration('-5h')

    def test_non_string_input(self):
        with self.assertRaises(ValueError):
            parse_duration(None)
        with self.assertRaises(ValueError):
            parse_duration(5)


if __name__ == '__main__':
    unittest.main()
```

skipped: unit aliases/case-insensitive parsing, negative/fractional durations — add if a caller actually needs them.