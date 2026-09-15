Confirmed: five harnesses, each with its entry script.

## Five harnesses and entry scripts (from `designs/atlas-data.json` → `harnesses[]`, verified against `INJECTION_SCRIPTS` in `tests/test_harness_family.py`)

1. **auto-mode-harness** → `scripts/auto_mode_harness.py`
2. **harness-proxy** → `scripts/harness_proxy.py`
3. **harness-wrap** → `scripts/harness_wrap.py`
4. **harness-goal** → `scripts/harness_goal.py`
5. **harness-super** → `scripts/harness_super.py`

## Three most connected symbols (graphify `god-nodes --top`, by degree)

1. `run()` — degree 51 — `tests/test_no_compress_guard.py`
2. `run()` — degree 42 — `tests/test_no_prune_guard.py`
3. `Verifier` — degree 38 — `scripts/verify_auto_mode.py:101`

## Verifier caller

`Verifier` is instantiated and driven by **`main()`** in `scripts/verify_auto_mode.py` (line 707: `verifier = Verifier(...)`, then `verifier.run()`; `main()` is defined at line 680 and invoked from `if __name__ == "__main__":` at line 712).

## Highest-blast-radius file

`scripts/build_atlas_data.py` (containing `build()`, degree 28, plus `script_lanes()`/`lane()`/`pick()` all in the top-connected set) would affect the most callers if changed, since it generates the shared `designs/atlas-data.json` that the harness list, the god-node rankings, and most test suites all read from.

**GOAL status:** all parts of the standing GOAL are answered above (5 harnesses + entries, top-3 symbols + files, Verifier's caller, highest-impact file). Nothing blocked. Left out due to the 600-token cap: the other ~15 god-node symbols beyond the top 3, and full call chains for `run()` in the two guard tests.