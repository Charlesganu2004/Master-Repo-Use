Confirmed: `main()` in scripts/verify_auto_mode.py instantiates and calls `Verifier`.

## Five harnesses — entry scripts
1. **auto-mode-harness** → `scripts/auto_mode_harness.py`
2. **harness-proxy** → `scripts/harness_proxy.py`
3. **harness-wrap** → `scripts/harness_wrap.py`
4. **harness-goal** → `scripts/harness_goal.py`
5. **harness-super** → `scripts/harness_super.py` (calls the other four, listed last by design)

(Source: `tests/test_harness_family.py` L38-45, `INJECTION_SCRIPTS` dict, cross-checked against `designs/atlas-data.json`.)

## Three most-connected symbols (by graph degree)
1. `run()` — `tests/test_no_compress_guard.py` (degree 51)
2. `run()` — `tests/test_no_prune_guard.py` (degree 42)
3. `Verifier` class — `scripts/verify_auto_mode.py` L101 (degree 38)

## Verifier's caller
`main()` in `scripts/verify_auto_mode.py` (L707-708) constructs `Verifier(...)` and calls `verifier.run()`. (A second call site exists only in test scaffolding: `tests/test_install_preservation.py` L122.)

## Highest-impact file
`scripts/harness_paths.py` would affect the most callers if changed: its path-resolution functions (`repo_root()`, `hooks_dir()`, `harness_modules_dir()`) are called from every hook-registration function in `install_auto_mode.py` and are the shared dependency underpinning all five harnesses' file layout.

**Done:** all four parts of the goal answered from the graph. **Left:** nothing outstanding.