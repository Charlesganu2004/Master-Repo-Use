Restating the goal: write `parse_duration(text)` parsing `d/h/m/s` (each optional, at most once, strict order) into integer seconds, raising `ValueError` on malformity, with unit tests. This turn delivers the full implementation, tests, and a verification run.

Read/approach: one anchored regex (`^(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$`) enforces unit order, uniqueness, and rejects garbage/extra chars all at once via `fullmatch` — no manual parsing loop needed. Empty match (nothing captured) is the only edge case requiring an explicit check.

```python
# solution.py
import re

_PATTERN = re.compile(r"^(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$")
_SECONDS_PER_UNIT = (86400, 3600, 60, 1)  # d, h, m, s


def parse_duration(text: str) -> int:
    """Convert a duration string like '1h30m', '45s', or '2d4h' into seconds.

    Units are d, h, m, s; each may appear at most once, and only in that
    order. Raises ValueError for empty input, missing/duplicated/out-of-order
    units, non-digit values, or any other malformed text.
    """
    match = _PATTERN.fullmatch(text) if text else None
    if not match or not any(match.groups()):
        raise ValueError(
            f"invalid duration string {text!r}: expected digits followed by "
            "units d, h, m, s in that order, e.g. '1h30m'"
        )

    return sum(
        int(value) * unit_seconds
        for value, unit_seconds in zip(match.groups(), _SECONDS_PER_UNIT)
        if value is not None
    )
```

```python
# test_solution.py
import unittest

from solution import parse_duration


class TestParseDuration(unittest.TestCase):
    def test_single_unit(self):
        self.assertEqual(parse_duration("45s"), 45)
        self.assertEqual(parse_duration("30m"), 30 * 60)
        self.assertEqual(parse_duration("2h"), 2 * 3600)
        self.assertEqual(parse_duration("3d"), 3 * 86400)

    def test_combined_units(self):
        self.assertEqual(parse_duration("1h30m"), 3600 + 30 * 60)
        self.assertEqual(parse_duration("2d4h"), 2 * 86400 + 4 * 3600)
        self.assertEqual(parse_duration("1d2h3m4s"), 86400 + 2 * 3600 + 3 * 60 + 4)

    def test_zero_value(self):
        self.assertEqual(parse_duration("0s"), 0)

    def test_empty_string_raises(self):
        with self.assertRaises(ValueError):
            parse_duration("")

    def test_none_raises(self):
        with self.assertRaises(ValueError):
            parse_duration(None)

    def test_no_units_raises(self):
        with self.assertRaises(ValueError):
            parse_duration("30")

    def test_no_digits_raises(self):
        with self.assertRaises(ValueError):
            parse_duration("h")

    def test_wrong_order_raises(self):
        with self.assertRaises(ValueError):
            parse_duration("30m1h")

    def test_duplicate_unit_raises(self):
        with self.assertRaises(ValueError):
            parse_duration("1h1h")

    def test_garbage_raises(self):
        with self.assertRaises(ValueError):
            parse_duration("abc")

    def test_negative_number_raises(self):
        with self.assertRaises(ValueError):
            parse_duration("-5h")

    def test_extra_characters_raise(self):
        with self.assertRaises(ValueError):
            parse_duration("1h 30m")


if __name__ == "__main__":
    unittest.main()
```

Verification (ran the logic + all 12 test cases inline via `python - <<'EOF'`, no files created):

```
test_combined (__main__.T.test_combined) ... ok
test_dup (__main__.T.test_dup) ... ok
test_empty (__main__.T.test_empty) ... ok
test_extra_chars (__main__.T.test_extra_chars) ... ok
test_garbage (__main__.T.test_garbage) ... ok
test_negative (__main__.T.test_negative) ... ok
test_no_digits (__main__.T.test_no_digits) ... ok
test_no_units (__main__.T.test_no_units) ... ok
test_none (__main__.T.test_none) ... ok
test_single_unit (__main__.T.test_single_unit) ... ok
test_wrong_order (__main__.T.test_wrong_order) ... ok
test_zero (__main__.T.test_zero) ... ok

Ran 12 tests in 0.001s
OK
```

Done: `parse_duration` implemented and verified against valid combos, order/duplicate/garbage/empty/None/negative rejection. Left: nothing — goal fully satisfied this turn. Skipped a custom parser/state machine — regex `fullmatch` covers order+uniqueness+validation in one expression; add a hand-rolled parser only if you need per-unit distinct error messages later.