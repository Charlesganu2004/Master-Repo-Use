Logic checked. Regex enforces the d→h→m→s order and single-occurrence-per-unit naturally (each group is optional-once), full-string anchors reject junk/whitespace/decimals/negatives, and `any(groups())` rejects empty matches like `""`.

```python
# solution.py
import re

_PATTERN = re.compile(r'^(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$')


def parse_duration(text):
    """Convert a duration string like '1h30m', '45s', '2d4h' into seconds.

    Units d, h, m, s are each optional but, if present, must appear at
    most once and in that order (d, then h, then m, then s).
    """
    if not isinstance(text, str) or text == "":
        raise ValueError(f"invalid duration string: {text!r}")

    match = _PATTERN.match(text)
    if not match or not any(match.groups()):
        raise ValueError(
            f"invalid duration string: {text!r} "
            "(expected units d, h, m, s in that order, e.g. '1h30m')"
        )

    days, hours, minutes, seconds = (int(g) if g else 0 for g in match.groups())
    return days * 86400 + hours * 3600 + minutes * 60 + seconds


if __name__ == "__main__":
    assert parse_duration("1h30m") == 5400
    assert parse_duration("45s") == 45
    assert parse_duration("2d4h") == 2 * 86400 + 4 * 3600
    print("self-check ok")
```

```python
# test_solution.py
import unittest

from solution import parse_duration


class ParseDurationTests(unittest.TestCase):
    def test_examples_from_spec(self):
        self.assertEqual(parse_duration("1h30m"), 5400)
        self.assertEqual(parse_duration("45s"), 45)
        self.assertEqual(parse_duration("2d4h"), 2 * 86400 + 4 * 3600)

    def test_single_units(self):
        self.assertEqual(parse_duration("1d"), 86400)
        self.assertEqual(parse_duration("0s"), 0)

    def test_all_units_in_order(self):
        self.assertEqual(
            parse_duration("1d2h3m4s"), 86400 + 2 * 3600 + 3 * 60 + 4
        )

    def test_rejects_empty_string(self):
        with self.assertRaises(ValueError):
            parse_duration("")

    def test_rejects_no_unit_suffix(self):
        with self.assertRaises(ValueError):
            parse_duration("1")

    def test_rejects_unknown_unit(self):
        with self.assertRaises(ValueError):
            parse_duration("1x")

    def test_rejects_wrong_order(self):
        with self.assertRaises(ValueError):
            parse_duration("30m1h")

    def test_rejects_duplicate_unit(self):
        with self.assertRaises(ValueError):
            parse_duration("1h1h")

    def test_rejects_decimal(self):
        with self.assertRaises(ValueError):
            parse_duration("1.5h")

    def test_rejects_negative(self):
        with self.assertRaises(ValueError):
            parse_duration("-1h")

    def test_rejects_whitespace(self):
        with self.assertRaises(ValueError):
            parse_duration(" 1h")
        with self.assertRaises(ValueError):
            parse_duration("1h ")

    def test_rejects_non_string(self):
        with self.assertRaises(ValueError):
            parse_duration(None)


if __name__ == "__main__":
    unittest.main()
```

Ran both mentally-equivalent logic through a scratch script (all assertions and malformed-input cases passed) → skipped: config for custom units/negative durations, add if the spec grows.