GOAL restated: trace prompt→injected-context (hook file + builder function), the file adding the super-harness chain, and the 3 most-connected symbols with their files. This turn answers all parts in full.

**Prompt → injected context**
- Hook file: `scripts/hooks/skill_pipeline.py` — registered as Claude Code's `UserPromptSubmit` hook (confirmed at line 19: "This hook is mechanism 3. Claude Code's UserPromptSubmit and Antigravity's...").
- Builder function: `context_for(prompt, session=...)` at `scripts/hooks/skill_pipeline.py:158`. It's called from `scripts/auto_mode_harness.py:885` (`context_for(prompt, session) if prompt.strip() else CORE`) which then emits `{"hookEventName": "UserPromptSubmit", "additionalContext": context}` (lines 900-901) — this is the actual stdout JSON Claude Code reads to inject context.

**Super-harness chain**
- File: `scripts/super_chain.py` — imported lazily ("only in super mode so base mode pays nothing", line 774) by `auto_mode_harness.py`, via `super_chain.super_block()` (line 780), which is what gets appended as `"## The super harness, on every prompt"` (line 232). `skill_pipeline.py` also pulls `super_chain.EXTRA_SKILLS` when mode is super (line 245).

**Three most-connected symbols (graphify god-nodes, by graph degree)**
1. `run()` — degree 51 — `tests/test_no_compress_guard.py`
2. `run()` — degree 42 — `tests/test_no_prune_guard.py`
3. `Verifier` — degree 38 — `scripts/verify_auto_mode.py`

Nothing blocked; all four requested items (hook file, builder function, super-chain file, top-3 connected symbols+files) resolved with direct source evidence.