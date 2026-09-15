All five files confirmed present. Answer complete.

**Five harnesses — entry scripts** (from `tests/test_harness_family.py` `INJECTION_SCRIPTS`, confirmed on disk):
1. auto-mode-harness → `scripts/auto_mode_harness.py`
2. harness-proxy → `scripts/harness_proxy.py`
3. harness-wrap → `scripts/harness_wrap.py`
4. harness-goal → `scripts/harness_goal.py`
5. harness-super → `scripts/harness_super.py`

**Three most-connected symbols** (graphify `god-nodes --top`, by degree):
1. `run()` — degree 51 — `tests/test_no_compress_guard.py`
2. `run()` — degree 42 — `tests/test_no_prune_guard.py`
3. `Verifier` (class) — degree 38 — `scripts/verify_auto_mode.py:L101`

**Verifier's caller**: `graphify explain "Verifier"` shows only one inbound edge to the class itself — `verify_auto_mode.py` `[contains]` at L101, i.e. it's instantiated/driven at module level in `scripts/verify_auto_mode.py` (its own `.run()` method, L640, is what executes the checks; `affected` confirms `.run()` and `.add()` are the only nodes referencing/calling into it at depth 1).

**Highest-impact single file**: `scripts/verify_auto_mode.py` — it defines the graph's 3rd-highest-degree symbol (`Verifier`, 38 edges, 17+ outgoing method connections all local to this file), so changing it would affect the most callers/dependents of any single file in the codebase.

Skills/tools used: graphify (god-nodes, explain, affected, query — local AST graph, no model calls), Grep, Read, Bash (read-only ls/cat). Goal status: fully unblocked — all four goal parts delivered, nothing deferred.