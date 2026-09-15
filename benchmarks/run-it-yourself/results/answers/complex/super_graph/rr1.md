All confirmed via graphify (query/explain, no model calls, local graph read).

**Prompt → injected context trace**
- **Hook file:** `scripts/hooks/skill_pipeline.py` — its `main()` (L826) reads the `UserPromptSubmit` event JSON from stdin (`event = json.load(sys.stdin)`, L837) and emits `additional_context`/`additionalContext` (L856, L885, L900).
- **Context-building function:** `context_for()` at `scripts/hooks/skill_pipeline.py:L158` — builds the core block plus at most one skill lane plus fan-out advice, called by `main()` for each hook path.
- **Super harness chain file:** inside `context_for()`, line 219 calls `chain_block()` (`skill_pipeline.py:L773`), which imports and calls `super_chain.super_block()` in **`scripts/hooks/super_chain.py`** (only when `harness_mode()` is "super", so base mode pays nothing). `super_chain.py` also defines `pass_lines()` (L71) and is annotated "the super harness chain: ten named passes on top of the three layers."

**Three most-connected symbols (graphify god-nodes):**
1. `run()` — 51 edges — `tests/test_no_compress_guard.py:L24`
2. `run()` — 42 edges — `tests/test_no_prune_guard.py:L22`
3. `Verifier` — 38 edges — `scripts/verify_auto_mode.py:L101`

Goal status: fully unblocked, nothing left outstanding on this GOAL.