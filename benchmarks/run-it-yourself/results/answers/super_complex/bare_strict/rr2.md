## The five harnesses (entry scripts)

1. **Surface harness** (1st) — `scripts/auto_mode_harness.py`
2. **Proxy harness** (2nd) — `scripts/harness_proxy.py`
3. **Wrap harness** (3rd) — `scripts/harness_wrap.py`
4. **Goal harness** (4th) — `scripts/harness_goal.py`
5. **Super harness** (5th, chains the other four) — `scripts/harness_super.py`

(`scripts/harness_computer.py` is explicitly *not* a harness — its own docstring says "This is a capability router, not another model harness.")

## Three most-connected symbols

Measured by number of distinct files calling each symbol across `scripts/` and `tests/`:

1. **`context_for`** — defined in `scripts/hooks/skill_pipeline.py` (line 158) — referenced from ~15 files (every harness entry script plus most tests); it builds the injected pipeline block each harness prepends to a prompt.
2. **`load_goal`** — defined in `scripts/hooks/skill_pipeline.py` (line 337) — referenced from ~9 files (goal/super/proxy/wrap harnesses and tests); reads the persisted standing-goal state.
3. **`set_goal`** — defined in `scripts/hooks/skill_pipeline.py` (line 413) — referenced from ~7 files; the mutator every "set the goal" entry point (hook, `/goal`, harness_goal CLI) funnels through.

## `Verifier` caller

`class Verifier` is defined in `scripts/verify_auto_mode.py` (line 101). It is instantiated and driven by **`main()`** in that same file (`verifier = Verifier(...); return print_report(verifier.run())`, line 707).

## Highest-impact single file

**`scripts/hooks/skill_pipeline.py`** would affect the most callers if changed, since it defines `context_for`, `load_goal`, and `set_goal` — the three functions every one of the five harnesses (and most of the test suite) calls to build and manage the injected prompt/goal state.