All 21 tests pass. Here's the implementation and tests (I ran them in a scratch temp directory, not the project — nothing was created/modified in the repo).

```python
# solution.py
import re


_UNIT_ORDER = "dhms"
_UNIT_SECONDS = {"d": 86400, "h": 3600, "m": 60, "s": 1}
_TOKEN_RE = re.compile(r"(\d+)([dhms])")


def parse_duration(text):
    """Convert a human duration string like '1h30m' into an integer number
    of seconds.

    Supported units, each optional but appearing at most once and in this
    order, are:
        d - days
        h - hours
        m - minutes
        s - seconds

    Examples:
        parse_duration("1h30m") -> 5400
        parse_duration("45s")   -> 45
        parse_duration("2d4h")  -> 187200

    Raises:
        ValueError: if `text` is not a well-formed duration string.
    """
    if not isinstance(text, str):
        raise ValueError(f"duration must be a string, got {type(text).__name__!r}")

    stripped = text.strip()
    if not stripped:
        raise ValueError("duration string is empty")

    total_seconds = 0
    seen_units = set()
    last_unit_index = -1
    pos = 0
    matched_any = False

    for match in _TOKEN_RE.finditer(stripped):
        if match.start() != pos:
            bad = stripped[pos:match.start()]
            raise ValueError(
                f"invalid duration {text!r}: unexpected text {bad!r} "
                f"at position {pos}"
            )

        value_str, unit = match.groups()

        if unit in seen_units:
            raise ValueError(
                f"invalid duration {text!r}: unit '{unit}' repeated"
            )

        unit_index = _UNIT_ORDER.index(unit)
        if unit_index <= last_unit_index:
            raise ValueError(
                f"invalid duration {text!r}: units must appear in the "
                f"order d, h, m, s"
            )

        seen_units.add(unit)
        last_unit_index = unit_index
        total_seconds += int(value_str) * _UNIT_SECONDS[unit]
        pos = match.end()
        matched_any = True

    if not matched_any or pos != len(stripped):
        raise ValueError(
            f"invalid duration {text!r}: expected a format like "
            f"'1h30m', '45s' or '2d4h'"
        )

    return total_seconds
```

```python
# test_solution.py
import unittest

from solution import parse_duration


class TestParseDuration(unittest.TestCase):
    def test_hours_and_minutes(self):
        self.assertEqual(parse_duration("1h30m"), 5400)

    def test_seconds_only(self):
        self.assertEqual(parse_duration("45s"), 45)

    def test_days_and_hours(self):
        self.assertEqual(parse_duration("2d4h"), 187200)

    def test_days_only(self):
        self.assertEqual(parse_duration("1d"), 86400)

    def test_zero(self):
        self.assertEqual(parse_duration("0s"), 0)

    def test_all_units(self):
        self.assertEqual(parse_duration("1d2h3m4s"), 86400 + 7200 + 180 + 4)

    def test_multi_digit_values(self):
        self.assertEqual(parse_duration("100s"), 100)

    def test_surrounding_whitespace_is_stripped(self):
        self.assertEqual(parse_duration("  2d4h  "), 187200)

    def test_empty_string_raises(self):
        with self.assertRaises(ValueError):
            parse_duration("")

    def test_whitespace_only_raises(self):
        with self.assertRaises(ValueError):
            parse_duration("   ")

    def test_missing_unit_raises(self):
        with self.assertRaises(ValueError):
            parse_duration("30")

    def test_missing_number_raises(self):
        with self.assertRaises(ValueError):
            parse_duration("h")

    def test_unknown_unit_raises(self):
        with self.assertRaises(ValueError):
            parse_duration("5x")

    def test_duplicate_unit_raises(self):
        with self.assertRaises(ValueError):
            parse_duration("1h2h")

    def test_out_of_order_units_raise(self):
        with self.assertRaises(ValueError):
            parse_duration("30m1h")

    def test_negative_number_raises(self):
        with self.assertRaises(ValueError):
            parse_duration("-5s")

    def test_decimal_number_raises(self):
        with self.assertRaises(ValueError):
            parse_duration("1.5h")

    def test_trailing_garbage_raises(self):
        with self.assertRaises(ValueError):
            parse_duration("1h30mx")

    def test_internal_garbage_raises(self):
        with self.assertRaises(ValueError):
            parse_duration("1h,30m")

    def test_non_string_raises(self):
        with self.assertRaises(ValueError):
            parse_duration(None)

    def test_error_message_is_descriptive(self):
        with self.assertRaises(ValueError) as ctx:
            parse_duration("1h2h")
        self.assertIn("repeated", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
```

Notes on the design:
- Uses a single regex `(\d+)([dhms])` and walks matches left to right, tracking the byte offset (`pos`) so any character not consumed by a valid `<number><unit>` token (garbage in the middle, at the end, decimals, negative signs, wrong-case units, etc.) triggers a `ValueError`.
- Enforces strict `d < h < m < s` ordering and rejects a repeated unit, each with its own clear message.
- Leading/trailing whitespace is trimmed, but internal whitespace or punctuation is treated as malformed.
- `0s`-style zero durations and multi-digit values work as plain integers.