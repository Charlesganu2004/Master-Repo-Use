All 5 harness entry scripts confirmed via designs/atlas-data.json.

**5 harnesses — entry scripts:**
1. Surface harness → `scripts/auto_mode_harness.py`
2. Proxy harness → `scripts/harness_proxy.py`
3. Wrapper harness → `scripts/harness_wrap.py`
4. Goal harness → `scripts/harness_goal.py`
5. Super harness → `scripts/harness_super.py` (calls the other four rather than reimplementing them)

**3 most-connected symbols (graphify god-nodes, by degree):**
1. `run()` — degree 51 — `tests/test_no_compress_guard.py`
2. `run()` — degree 42 — `tests/test_no_prune_guard.py`
3. `Verifier` (class) — degree 38 — `scripts/verify_auto_mode.py:101`

**Verifier's caller:** `main()` in `scripts/verify_auto_mode.py` instantiates it — `verifier = Verifier(...)` at line 707 (edge confirmed: `main() --calls--> Verifier`).

**Highest-impact file:** `tests/test_no_compress_guard.py` — its `run()` is the single most-connected symbol in the graph (degree 51), so changing it would ripple to the most callers/dependents repo-wide.

Tools used: graphify (god-nodes, query, explain — local graph, no model calls) per S1/Layer1; Grep/ls for the two narrow lookups graphify's budget truncated (harness file list, Verifier() call site) rather than re-querying repeatedly. Goal check: all four parts answered, none blocked. Nothing left outstanding on this goal for the current turn.