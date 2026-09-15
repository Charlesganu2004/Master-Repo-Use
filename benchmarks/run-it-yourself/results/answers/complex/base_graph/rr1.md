GOAL: trace prompt→injected-context path + name top-3 connected symbols. This turn answers both; nothing blocked.

**Prompt → injected context:**
- Hook file: `scripts/hooks/skill_pipeline.py`
- Context-building function: `context_for()` (L158) — assembles the injected block; `chain_block()` (L757) composes the final chain output appended to context.
- Super-harness-chain file: `scripts/hooks/super_chain.py`, via `super_block()` (L84), which builds the "ten named passes on top of the three layers" block that `skill_pipeline.py` layers on.

**Top 3 most-connected symbols (from `graphify god-nodes --top 3 --json`):**
1. `run()` — 51 edges — `tests/test_no_compress_guard.py`
2. `run()` — 42 edges — `tests/test_no_prune_guard.py`
3. `Verifier` — 38 edges — `scripts/verify_auto_mode.py`

(Note: `scripts/hooks/skill_pipeline.py` itself also has degree 38, tied with `Verifier` but ranked 4th by the tool.)

Done: both GOAL parts answered with evidence from graphify. Left out: full 18+ remaining contains-edges list for skill_pipeline.py (truncated by budget) — ask for `graphify explain "scripts/hooks/skill_pipeline.py" --budget 100` to see the rest.