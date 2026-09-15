Confirmed. Now the direct answer.

**Prompt → injected context trace**

- Hook file: `scripts/hooks/skill_pipeline.py` — registered as the `UserPromptSubmit` hook; it prints `{"hookSpecificOutput": {"additionalContext": ...}}` (line 867/883).
- Function that builds the context: `context_for(prompt, session=None, ...)` at `scripts/hooks/skill_pipeline.py:158` — called at line 869 as `context_for(prompt, session)`, falling back to `CORE` for empty prompts.
- File that adds the super harness chain on top: `scripts/hooks/super_chain.py`. `skill_pipeline.py`'s own `chain_block()` (line 757) lazily `import super_chain` and calls `super_chain.super_block()` (line 761/764) — done only in super mode, "with no imports beyond the standard library," per that file's docstring, so base mode pays nothing.

**Three most-connected symbols (graphify god-nodes --top 3 --json)**

1. `run()` — 51 edges — `tests/test_no_compress_guard.py`
2. `run()` — 42 edges — `tests/test_no_prune_guard.py`
3. `Verifier` — 38 edges — `scripts/verify_auto_mode.py`

GOAL check: both parts of the standing goal are done — hook/function/super-chain file traced, and the three top god-nodes named with their files. Nothing blocked. Left out to fit the 600-token cap: the internals of `context_for`'s skill-selection logic and `super_block()`'s own chain contents — ask if you want those expanded.