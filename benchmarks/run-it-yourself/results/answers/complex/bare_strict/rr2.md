## The prompt-to-context path

**Hook:** `scripts/hooks/skill_pipeline.py` — this is the `UserPromptSubmit` hook (Claude Code) that also serves Antigravity's `PreInvocation`, Gemini's `BeforeAgent`, Cursor, and Copilot via CLI flags (`--antigravity`, `--cursor`, `--gemini`, `--copilot-session`, `--copilot-transform`).

**Function that builds the context:** `context_for(prompt, session=None, capturing=True, include_goal=True, mode=None, token_enforced=False)`, also in `scripts/hooks/skill_pipeline.py` (line 158). It assembles: the mandatory `CORE` three-layer text, an optional single matched `LANES` entry, `ORCHESTRATION` advice for multi-part prompts, the `standing_goal()` block, a `token_block()` budget, and — only when the machine is in `"super"` mode — the chain block. `main()` calls `context_for` per-client and emits it as `additionalContext`/`additional_context`/`injectSteps` depending on the client shape.

**File that layers the super-harness chain on top:** `scripts/hooks/super_chain.py`. It's imported lazily by `chain_block()` (in `skill_pipeline.py`) only when `harness_mode() == "super"`, so base mode pays nothing for it. It defines the `PASSES` tuple (10 named passes: CAVEMAN, FULL OUTPUT, ANTI-SLOP, PLAN, DESIGN, ARCHITECT, REFACTOR, COMPRESS, REVIEW, VERIFY) and `super_block()`, which `context_for` appends last, after the goal and token budget.

## Three most-connected symbols (by cross-file reference count, excluding `build/`, `__pycache__`, `.git`, `graphify-out/`)

1. **`context_for`** — defined in `scripts/hooks/skill_pipeline.py` (~21 referencing files: per-client hook variants, `harness_goal.py`, `harness_super.py`, `harness_proxy.py`, tests).
2. **`harness_paths`** (module) — defined in `scripts/harness_paths.py` (~20 referencing files). It's the bootstrap module ("where does everything live") that `master_harness/_loader.py` resolves first, before anything else, and nearly every harness/hook imports it for state-directory/seed-path resolution.
3. **`capture`** — defined in `scripts/hooks/skill_pipeline.py` (~15 referencing files: goal-capture logic invoked from `main()`, tested directly by `tests/test_skill_pipeline_hook.py`, and referenced by `harness_goal.py`/`harness_super.py`).