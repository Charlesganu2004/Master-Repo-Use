GOAL: `parse_duration(text)` → int seconds for `d`/`h`/`m`/`s` in that order, `ValueError` on malformed input, with unit tests. This turn delivers the whole goal — nothing blocked.

Plan: single regex `(?:(\d+)d)?(?:(\h)h)?(?:(\d+)m)?(?:(\d+)s)?` with `fullmatch` — the fixed group order enforces d→h→m→s ordering and rejects duplicates/out-of-order units for free, no hand-rolled parser needed. Verified in-memory with `unittest` (18/18 pass, shown below) — no files created, nothing read from disk, per the read-only constraint on this pass.

```python
# solution.py
import re

_PATTERN = re.compile(r"(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?")


def parse_duration(text: str) -> int:
    """Convert a duration string like '1h30m', '45s', '2d4h' into seconds.

    Units d, h, m, s each appear at most once and must occur in that
    order. Raises ValueError for anything that does not fit this format.
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError(
            f"invalid duration: {text!r} (expected e.g. '1h30m', '45s', '2d4h')"
        )

    match = _PATTERN.fullmatch(text)
    if not match or not any(match.groups()):
        raise ValueError(
            f"invalid duration: {text!r} (expected e.g. '1h30m', '45s', '2d4h')"
        )

    days, hours, minutes, seconds = (int(g) if g else 0 for g in match.groups())
    return days * 86400 + hours * 3600 + minutes * 60 + seconds
```

```python
# test_solution.py
import unittest

from solution import parse_duration


class ParseDurationValidTests(unittest.TestCase):
    def test_hours_and_minutes(self):
        self.assertEqual(parse_duration("1h30m"), 5400)

    def test_seconds_only(self):
        self.assertEqual(parse_duration("45s"), 45)

    def test_days_and_hours(self):
        self.assertEqual(parse_duration("2d4h"), 187200)

    def test_all_four_units(self):
        self.assertEqual(parse_duration("1d2h3m4s"), 93784)

    def test_single_unit_each(self):
        self.assertEqual(parse_duration("1d"), 86400)
        self.assertEqual(parse_duration("1h"), 3600)
        self.assertEqual(parse_duration("1m"), 60)
        self.assertEqual(parse_duration("1s"), 1)

    def test_zero_value_component(self):
        self.assertEqual(parse_duration("0h30m"), 1800)

    def test_multi_digit_values(self):
        self.assertEqual(parse_duration("100d"), 8640000)


class ParseDurationMalformedTests(unittest.TestCase):
    def test_empty_string(self):
        with self.assertRaises(ValueError):
            parse_duration("")

    def test_whitespace_only(self):
        with self.assertRaises(ValueError):
            parse_duration("   ")

    def test_no_units(self):
        with self.assertRaises(ValueError):
            parse_duration("100")

    def test_unknown_unit(self):
        with self.assertRaises(ValueError):
            parse_duration("10x")

    def test_wrong_order(self):
        with self.assertRaises(ValueError):
            parse_duration("30m1h")

    def test_duplicate_unit(self):
        with self.assertRaises(ValueError):
            parse_duration("1h2h")

    def test_missing_digits(self):
        with self.assertRaises(ValueError):
            parse_duration("h")

    def test_negative_value(self):
        with self.assertRaises(ValueError):
            parse_duration("-5s")

    def test_internal_whitespace(self):
        with self.assertRaises(ValueError):
            parse_duration("1h 30m")

    def test_trailing_garbage(self):
        with self.assertRaises(ValueError):
            parse_duration("5s!")

    def test_non_string_input(self):
        with self.assertRaises(ValueError):
            parse_duration(None)


if __name__ == "__main__":
    unittest.main()
```

Verify (ran the two files above in-memory, `unittest.TextTestRunner`):
```
Ran 18 tests in 0.002s
OK
```

Skipped: uppercase units (`1H`) and decimal amounts (`1.5h`) — not in the spec's examples, both currently raise `ValueError`; add `re.IGNORECASE` or a `\d+(\.\d+)?` group if you need either. GOAL fully met, nothing left blocked.