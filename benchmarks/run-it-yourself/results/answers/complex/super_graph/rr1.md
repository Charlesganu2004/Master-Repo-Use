GOAL restated: trace prompt→injected-context path (hook file, context-building function, super-harness-chain file) and name the 3 most-connected symbols with their defining files. This turn delivers both parts.

**Injected-context path**
- Hook file: `scripts/hooks/skill_pipeline.py` (this is the `UserPromptSubmit` hook; its own docstring says "This hook is mechanism 3. Claude Code's UserPromptSubmit and Antigravity's...").
- Context-building function: `context_for(prompt: str, session: str | None = None, ...)` at line 158 of that file — called from `main()` (line 810), output as `hookSpecificOutput.additionalContext` for `UserPromptSubmit` (lines 867-885).
- Super-harness-chain file: `scripts/hooks/super_chain.py`, added on top via `chain_block()` (skill_pipeline.py line 757), which lazily `import super_chain` and returns `super_chain.super_block()` — "imported only in super mode so base mode pays nothing." `super_chain.py` defines `SUPER_BLOCK`, `pass_lines()`, and `super_block()` (lines 60-84), and its header comment states it "lives here, beside the hook" so base-mode sessions don't pay the cost of importing every harness.

**Three most-connected symbols (graphify god-nodes, by graph degree)**
1. `run()` — degree 51 — defined in `tests/test_no_compress_guard.py`
2. `run()` — degree 42 — defined in `tests/test_no_prune_guard.py`
3. `Verifier` — degree 38 — defined in `scripts/verify_auto_mode.py`

Tools used: graphify (`god-nodes --json`, `explain`) for the connectivity ranking; Grep/Bash for the hook/context/chain trace since graphify's `query` truncated at the 400-token budget before reaching those specific symbols.

Status: both GOAL parts complete, nothing blocked. Left out at the 600-token ceiling: node counts/degree for ranks 4-5 (`build()` deg 28, `IsolatedPublicSite` deg 28) and the full `context_for()` body — ask for either by name if wanted.