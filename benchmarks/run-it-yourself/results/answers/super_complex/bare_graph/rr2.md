Confirmed: `main()` in scripts/verify_auto_mode.py instantiates and calls `Verifier`.

## Five harnesses and entry scripts
1. **auto-mode-harness** → `scripts/auto_mode_harness.py`
2. **harness-proxy** → `scripts/harness_proxy.py`
3. **harness-wrap** → `scripts/harness_wrap.py`
4. **harness-goal** → `scripts/harness_goal.py`
5. **harness-super** → `scripts/harness_super.py`

## Three most connected symbols (by graph degree)
1. `run()` — degree 51 — `tests/test_no_compress_guard.py`
2. `run()` — degree 42 — `tests/test_no_prune_guard.py`
3. `Verifier` (class) — degree 38 — `scripts/verify_auto_mode.py`

## Verifier's caller
`main()` in `scripts/verify_auto_mode.py` constructs `Verifier(...)` and calls `verifier.run()`.

## Highest-impact single file
`scripts/verify_auto_mode.py` — it defines the highest-degree non-test symbol (`Verifier`, degree 38) and is the module most tests and tooling reach into to validate every harness's installed state; changing it would ripple to the most callers.