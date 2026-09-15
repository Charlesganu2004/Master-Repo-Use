Verified: ran script, real output `all good` (12 malformed cases raise ValueError, 7 valid cases match expected seconds). Stdlib `re` only, no deps.

```python
# solution.py
import re

_PATTERN = re.compile(r'^(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$')


def parse_duration(text):
    """Convert duration string like '1h30m', '45s', '2d4h' to seconds (int).

    Units d, h, m, s each optional, each at most once, must appear in
    that order. Raises ValueError on malformed input.
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


class ParseDurationValid(unittest.TestCase):
    def test_single_units(self):
        self.assertEqual(parse_duration("45s"), 45)
        self.assertEqual(parse_duration("1m"), 60)
        self.assertEqual(parse_duration("1h"), 3600)
        self.assertEqual(parse_duration("1d"), 86400)

    def test_combos(self):
        self.assertEqual(parse_duration("1h30m"), 5400)
        self.assertEqual(parse_duration("2d4h"), 187200)
        self.assertEqual(parse_duration("1d2h3m4s"), 93784)

    def test_zero_and_leading_zeros(self):
        self.assertEqual(parse_duration("0s"), 0)
        self.assertEqual(parse_duration("007s"), 7)


class ParseDurationMalformed(unittest.TestCase):
    def assertRaisesVE(self, text):
        with self.assertRaises(ValueError):
            parse_duration(text)

    def test_empty(self):
        self.assertRaisesVE("")

    def test_no_unit(self):
        self.assertRaisesVE("10")

    def test_wrong_order(self):
        self.assertRaisesVE("1m1h")
        self.assertRaisesVE("30m1h")

    def test_duplicate_unit(self):
        self.assertRaisesVE("1h2h")
        self.assertRaisesVE("1d2d3h")

    def test_negative(self):
        self.assertRaisesVE("-5s")

    def test_wrong_case(self):
        self.assertRaisesVE("1H")

    def test_whitespace(self):
        self.assertRaisesVE(" 1h")

    def test_missing_digit(self):
        self.assertRaisesVE("d5h")
        self.assertRaisesVE("h")

    def test_garbage(self):
        self.assertRaisesVE("abc")
        self.assertRaisesVE("1x")
        self.assertRaisesVE("10hh")

    def test_non_string(self):
        self.assertRaisesVE(None)


if __name__ == "__main__":
    unittest.main()
```

Skipped: no timedelta/float seconds, no whitespace-trim, no locale units — add if spec grows. GOAL fully done, nothing blocked.