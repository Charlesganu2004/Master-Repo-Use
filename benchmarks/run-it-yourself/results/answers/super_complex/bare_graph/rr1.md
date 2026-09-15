All five data points confirmed. Now I have everything needed.

## The five harnesses and their entry scripts

| Harness | Entry script |
|---|---|
| Surface harness | `scripts/auto_mode_harness.py` |
| Proxy harness | `scripts/harness_proxy.py` |
| Wrapper harness | `scripts/harness_wrap.py` |
| Goal harness | `scripts/harness_goal.py` |
| Super harness | `scripts/harness_super.py` (calls the other four rather than reimplementing them) |

## Three most connected symbols (by graph degree)

1. `run()` — degree 51 — defined in `tests/test_no_compress_guard.py`
2. `run()` — degree 42 — defined in `tests/test_no_prune_guard.py`
3. `Verifier` — degree 38 — defined in `scripts/verify_auto_mode.py:101`

## Function calling `Verifier`

`main()` in `scripts/verify_auto_mode.py:680` constructs/drives the `Verifier` class (which itself dispatches to its own methods like `.run()`, `.add()`, `._check_home_client()`, etc.).

## Highest-impact file

`scripts/verify_auto_mode.py` — it defines `Verifier`, the third-most-connected symbol in the whole graph (38 connections, almost entirely internal check methods it owns), so a change there would ripple through the most callers/checks of any single file.