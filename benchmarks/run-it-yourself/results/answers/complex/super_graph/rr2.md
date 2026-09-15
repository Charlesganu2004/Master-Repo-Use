All findings confirmed via graphify + Grep/Read (read-only, evidence quoted).

**Hook → context chain**
- Hook file: `scripts/hooks/skill_pipeline.py` — this is "mechanism 3" (line 19: "This hook is mechanism 3. Claude Code's UserPromptSubmit and Antigravity's..."), invoked on `UserPromptSubmit` (confirmed at line 884: `"hookEventName": "UserPromptSubmit"`).
- Function that builds the injected context: `context_for(prompt, session=None, capturing=True, include_goal=True, mode=None, token_enforced=False)`, defined at `scripts/hooks/skill_pipeline.py:158`. Its docstring states the mechanism directly: "The core, plus at most one lane, plus fan-out advice... `mode` overrides the machine's configured mode for one call; **the super harness passes "base" and appends the chain itself, after the goal.**" It's called at the JSON-emit sites (lines 846, 869) as `context_for(prompt, session)`, defaulting to `CORE` (defined line 92) when the prompt is empty.
- File that adds the super harness chain on top: `scripts/hooks/super_chain.py`. Its own header explains the split (lines 5-10): `harness_wrap` "imports every other harness... fine for a command and wrong for a per-prompt hook: skill_pipeline runs on every prompt of every client... So the definition lives here, beside the hook, with no imports beyond the [stdlib]." It defines `SUPER_BLOCK` (line 60, the "SUPER HARNESS. The chain above is the floor..." text seen in this very prompt), built by `pass_lines()` (line 71) and assembled by `super_block()` (line 84).

**Three most-connected symbols (graphify god-nodes --top)**
1. `run()` — degree 51 — `tests/test_no_compress_guard_run.py` (id `tests_test_no_compress_guard_run`)
2. `run()` — degree 42 — `tests/test_no_prune_guard_run.py`
3. `Verifier` — degree 38 — `scripts/verify_auto_mode.py`

GOAL check: all four parts (hook file, context-building function, super-chain file, top-3 connected symbols+files) are done — none blocked. Tools used: graphify (god-nodes query), Grep, Read — no files modified. Left out to fit the 600-token cap: the 4th/5th god-nodes (`build()` in scripts/build_atlas_data.py, `IsolatedPublicSite` in tests/public_site_fixture.py) and the full `context_for` lane-matching logic (lines 202+) — ask if you want either.