## Prompt → injected context

**Hook file:** `scripts/hooks/skill_pipeline.py` — this is the `UserPromptSubmit`/`PreInvocation`/`userPromptTransformed` handler wired into Claude Code, Antigravity, Cursor, Gemini, and Copilot (see `main()`, lines 810‑888, which branches on `--antigravity`/`--cursor`/`--gemini`/`--copilot-*` flags and prints each client's expected JSON shape).

**Function that builds the context:** `context_for(prompt, session=None, capturing=True, include_goal=True, mode=None, token_enforced=False)` (lines 158‑222). It assembles the injected string by concatenating, in order:
- `CORE` — the mandatory 3‑layer pipeline text (caveman/full‑output/anti‑slop → plan/design → capabilities/agents/refactor/re‑apply/verify)
- the single best‑matching `LANES` regex entry (security, UI, refactor, etc.)
- `ORCHESTRATION` advice on long/multi‑task prompts
- `standing_goal(...)` if a goal is captured/set
- `token_block(...)` if a `/token limit` is active
- `chain_block()` **only if** `harness_mode() == "super"`

**File that adds the super‑harness chain:** `scripts/hooks/super_chain.py`. `context_for` calls its own local helper `chain_block()` (lines 757‑764), which lazily `import super_chain` and returns `super_chain.super_block()`. That function formats the `PASSES` tuple (CAVEMAN, FULL OUTPUT, ANTI‑SLOP, PLAN, DESIGN, ARCHITECT, REFACTOR, COMPRESS, REVIEW, VERIFY) into the `SUPER_BLOCK` template and appends it after the goal/token blocks — kept in its own module specifically so base‑mode sessions never pay the import cost.

## Three most-connected symbols

Ranked by actual `import` statements found via grep across `scripts/`, `master_harness/`, and `tests/` (not graphify):

1. **`skill_pipeline`** — module defined in `scripts/hooks/skill_pipeline.py` — imported by 18 files (`auto_mode_harness.py`, `build_atlas_data.py`, `harness_ab_test.py`, `harness_goal.py`, `harness_proxy.py`, `harness_super.py`, `harness_wrap.py`, and their `master_harness/` mirrors, plus 6 test files). It's the shared context/goal/token/mode engine every harness entry point depends on.
2. **`harness_paths`** — module defined in `scripts/harness_paths.py` — imported by 11 files (`auto_mode_harness.py`, `harness_computer.py`, `install_auto_mode.py`, `verify_auto_mode.py`, `skill_pipeline.py` itself, mirrors, and `tests/test_package.py`). Supplies `state_dir()`, `seed_path()`, `repo_root()` etc. used for all cross-client path resolution.
3. **`harness_super`** — module defined in `scripts/harness_super.py` — imported by 9 files (`build_atlas_data.py`, `harness_ab_test.py`, `harness_proxy.py`, `harness_wrap.py`, mirrors, and 3 test files). Re-exports the super chain and mode switch for the install/serve/route commands.