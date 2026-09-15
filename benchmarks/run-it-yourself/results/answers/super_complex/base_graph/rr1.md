GOAL restated: name the five harnesses' entry scripts, the three most-connected symbols with defining files, who calls `Verifier`, and which file's change hits the most callers — all in this one turn.

**Five harnesses (entry scripts):**
1. auto-mode-harness — `scripts/auto_mode_harness.py`
2. harness-proxy — `scripts/harness_proxy.py`
3. harness-wrap — `scripts/harness_wrap.py`
4. harness-goal — `scripts/harness_goal.py`
5. harness-super — `scripts/harness_super.py`

**Three most-connected symbols** (graphify `god-nodes`, by graph degree):
1. `run()` — degree 51 — `tests/test_no_compress_guard.py`
2. `run()` — degree 42 — `tests/test_no_prune_guard.py`
3. `Verifier` (class) — degree 38 — `scripts/verify_auto_mode.py:101`

**Caller of `Verifier`:** `main()` in `scripts/verify_auto_mode.py:707` constructs `Verifier(...)` and calls `.run()` on it (line 709).

**Highest-impact file:** `scripts/harness_paths.py` — every harness and the verifier import it for all path/mode resolution, so a change there ripples to the most callers.

Left out: full 68/75-node connection lists graphify truncated (raise `--budget` to see them); not needed to satisfy the GOAL. Nothing else blocked.