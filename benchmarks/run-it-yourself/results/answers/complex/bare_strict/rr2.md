## Prompt → injected context path

**Hook file:** `scripts/hooks/skill_pipeline.py` — this is the file wired into every client's per-prompt hook (Claude Code/Codex `UserPromptSubmit`, Gemini `BeforeAgent`, Copilot `userPromptTransformed`/session, Cursor's hook config), per `.github/hooks/master-repo-auto.json` and the docstring at line 19: *"This hook is mechanism 3. Claude Code's UserPromptSubmit and Antigravity's [PreInvocation]..."*.

**Function that builds the context:** `context_for(prompt, session=None, capturing=True, include_goal=True, mode=None, token_enforced=False)`, defined at line 158. It assembles a list of parts — `CORE` (the standing pipeline), an optional single best-matching `LANES` entry (e.g. security/dependency/orientation advice), an `ORCHESTRATION` line for multi-task prompts, the `standing_goal(...)`, a `token_block(...)` budget, and — only when the machine's mode is `"super"` — the result of `chain_block()` — then joins them with `"\n"`. `main()` (line 810) reads the incoming event, extracts `prompt`/`session` via `find_prompt`/`find_session`, calls `context_for(prompt, session)`, and emits it as `additionalContext`/`hookSpecificOutput.additionalContext` in the shape each client expects.

**File that layers the super-harness chain on top:** `scripts/hooks/super_chain.py`. `context_for` calls `chain_block()` (line 757 in `skill_pipeline.py`), which lazily imports `super_chain` and returns `super_chain.super_block()` — kept in its own module (per its docstring) specifically so base-mode sessions never pay the import cost, and so there is exactly one copy of the ten-pass chain (`PASSES`) shared by every client instead of duplicating it inside the hot-path hook.

## Three most-connected symbols (by cross-file import/reference count, excluding `graphify-out/` and the `build/` mirror)

Computed directly from `grep`-counted distinct files doing `import X` / `from X import`:

1. **`skill_pipeline`** (module) — imported by 19 distinct files (tests, `super_chain.py`, `install_auto_mode.py`, CLI, benchmarks harness, etc.) — defined in `scripts/hooks/skill_pipeline.py` (mirrored for packaging in `master_harness/skill_pipeline.py`).
2. **`auto_mode_harness`** (module) — 9 direct importers, 27 total file references — defined in `scripts/auto_mode_harness.py` (mirrored in `master_harness/auto_mode_harness.py`, which has since diverged from the `scripts/` copy).
3. **`harness_paths`** (module) — 9 direct importers, 20 total file references — defined in `scripts/harness_paths.py` (identical mirror at `master_harness/harness_paths.py`); it centralizes the runtime-state path logic (`.auto-mode/`) used by `skill_pipeline.py`, `auto_mode_harness.py`, and the verify/install scripts.