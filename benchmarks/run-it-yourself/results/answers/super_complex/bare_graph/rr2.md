## Answer

**Five harnesses and their entry scripts** (from `tests/test_harness_family.py`):
1. `auto-mode-harness` → `scripts/auto_mode_harness.py`
2. `harness-proxy` → `scripts/harness_proxy.py`
3. `harness-wrap` → `scripts/harness_wrap.py`
4. `harness-goal` → `scripts/harness_goal.py`
5. `harness-super` → `scripts/harness_super.py`

**Three most connected symbols** (graphify `god-nodes`, by degree):
1. `run()` — degree 51 — `tests/test_no_compress_guard.py`
2. `run()` — degree 42 — `tests/test_no_prune_guard.py`
3. `Verifier` (class) — degree 38 — `scripts/verify_auto_mode.py` (line 101)

**Function calling `Verifier`:** `main()` in `scripts/verify_auto_mode.py` (line 680) — it constructs `Verifier(...)` at line 707 and calls `verifier.run()`.

**Highest-impact file:** `scripts/harness_paths.py` — it defines the shared path/module-resolution logic imported directly by `auto_mode_harness.py`, `harness_computer.py`, `install_auto_mode.py`, and `verify_auto_mode.py`, and via those, transitively reached by roughly 20 downstream callers/functions across the harness family — more than any other single file in the graph.