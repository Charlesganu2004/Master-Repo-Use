GOAL restated: five harnesses' entry scripts, top-3 connected symbols with files, Verifier's caller, and the single highest-impact file — via graphify (local, no model). This turn completes it in full.

**Five harnesses (entry scripts, from `tests/test_harness_family.py::INJECTION_SCRIPTS`):**
1. auto-mode-harness → `scripts/auto_mode_harness.py`
2. harness-proxy → `scripts/harness_proxy.py`
3. harness-wrap → `scripts/harness_wrap.py`
4. harness-goal → `scripts/harness_goal.py`
5. harness-super → `scripts/harness_super.py` (calls the other four)

**Three most connected symbols** (graphify `god-nodes`):
1. `run()` — `tests/test_no_compress_guard.py:L24` — 51 edges
2. `run()` — `tests/test_no_prune_guard.py:L22` — 42 edges
3. `Verifier` — `scripts/verify_auto_mode.py:L101` — 38 edges

**Verifier's caller:** `main()` in `scripts/verify_auto_mode.py` (L707-708) — builds `Verifier(...)` then calls `verifier.run()`.

**Highest-impact file:** `scripts/harness_paths.py` — `graphify affected --depth 2` shows 29 downstream nodes (23 calls, 6 imports), more than any other harness-family file (harness_super.py: 4, verify_auto_mode.py: 6, auto_mode_harness.py: 7), because every harness imports its path-resolution logic — changing it would ripple into all five.

Tools used: `graphify` (god-nodes, explain, affected) exclusively — local AST graph, no model calls, no files created/modified. Word count ~230, within the 450-word/600-token budget.

Done: all four GOAL parts delivered and cross-checked against graph output. Left out: nothing — full scope answered.