Based on the source files (not graphify-out):

**Prompt → injected context pipeline**

- **Hook file:** `scripts/hooks/skill_pipeline.py` — the `UserPromptSubmit` hook (also serving Cursor/Copilot/Gemini/Antigravity variants) that Claude Code invokes on every prompt.
- **Function that builds the context:** `context_for(prompt, session=None, ...)` (defined at line 158 of that file). It assembles `CORE` (the three-layer standing pipeline text), picks at most one matching `LANES` entry, adds orchestration advice for multi-part prompts, appends the `standing_goal(...)` block, appends a `token_block(...)` if a limit is set, and — only when the harness is in super mode — appends `chain_block()`. `main()` calls `context_for(prompt, session)` directly and emits it as `hookSpecificOutput.additionalContext` (or the client-specific equivalent key).

**Super-harness chain file**

- **`scripts/hooks/super_chain.py`** — defines `super_block()` (and `PASSES`/`SUPER_BLOCK`). `context_for`'s `chain_block()` helper imports this module lazily and calls `super_chain.super_block()`, appending its text after everything else *only* when `harness_mode() == "super"` — literally layering the ten-pass chain "on top of" the base three-layer context. (`scripts/harness_super.py` and `master_harness/harness_super.py` merely re-export/wrap this same module for the CLI; the chain itself is authored in `super_chain.py`.)

**Three most-connected symbols** (by distinct-file reference count under `scripts/`, `master_harness/`, and `tests/`, excluding the generated `build/lib/` copy and `graphify-out/`):

1. **`context_for`** — defined independently at three composition levels: `scripts/hooks/skill_pipeline.py` (base), `scripts/harness_goal.py` (adds the goal block), `scripts/harness_super.py` (adds the chain). Referenced/called from ~21 files (hooks, CLI wrappers, harness_ab_test.py, and a dozen tests).
2. **`harness_paths`** (module) — defined in `scripts/harness_paths.py`, providing `state_dir()`, `seed_path()`, `skills_dir()`, `hooks_dir()`, etc. Imported by ~20 files across the hooks, install/verify scripts, and tests as the shared path-resolution utility.
3. **`load_goal`** — defined in `scripts/hooks/skill_pipeline.py`; read by `harness_goal.py`, `harness_super.py`, the CLI, and 6+ tests (~12 files) as the single source of standing-goal state.