Confirmed — GOAL fully traced this turn.

**Prompt → injected context chain:**
- Hook file: `scripts/hooks/skill_pipeline.py`
- Function that builds the injected context: `context_for()` (defined L158) — builds "the core, plus at most one lane, plus fan-out advice," reading the standing goal and token limit.
- File that adds the super harness chain on top: `scripts/hooks/skill_pipeline.py` itself contains `chain_block()` (L773), which imports `super_chain` (same dir) and calls `super_chain.super_block()` — appended after the goal block when in super mode. Entry point is `scripts/harness_proxy.py`, whose `inject()` (L155) calls `CONTEXT(text, session)`; in super mode `use_super_context()` (L108) swaps `CONTEXT` to `harness_super.context_for(...)`, so `harness_super.py` is the file layering the super chain over the base pipeline's `context_for`.

**Top 3 most connected symbols (by graph degree):**
1. `run()` — degree 51 — `tests/test_no_compress_guard_run.py` (actually `tests_test_no_compress_guard_run` id → file `tests/test_no_compress_guard.py`, function `run`)
2. `run()` — degree 42 — `tests/test_no_prune_guard.py`
3. `Verifier` — degree 38 — `scripts/verify_auto_mode.py`

Not lifted: goal stays standing per master-goal rules until you say "goal clear."