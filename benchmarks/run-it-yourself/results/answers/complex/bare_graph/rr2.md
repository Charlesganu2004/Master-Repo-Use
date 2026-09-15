## Prompt → injected context

**Hook file:** `scripts/hooks/skill_pipeline.py` — this is Claude Code's `UserPromptSubmit` hook (per its own docstring: "This hook is mechanism 3. Claude Code's UserPromptSubmit and Antigravity's...").

**Function that builds the context:** `context_for(prompt, session=None, capturing=True, include_goal=True, mode=None, token_enforced=False)` (line 158). It assembles the core context plus at most one topic "lane" (chosen by number of matched terms, not declaration order) plus fan-out advice for large prompts, plus the standing goal (unless `include_goal=False`). The hook calls it near the bottom (`additionalContext = context_for(prompt, session)`) and emits it via `hookEventName: "UserPromptSubmit"` / `additionalContext` in the JSON response.

**File adding the super harness chain on top:** `super_chain.py`, pulled in by `chain_block()` (line 773) inside `skill_pipeline.py`:
```python
def chain_block() -> str:
    """The super chain, imported only in super mode so base mode pays nothing."""
    import super_chain
    return super_chain.super_block()
```
`context_for` is called with `mode="base"` in super mode, and `chain_block()` appends the ten-pass super chain block afterward — kept as a lazy import so non-super runs never pay for it.

## Three most-connected symbols (god nodes)

| Rank | Symbol | Degree | Defined in |
|---|---|---|---|
| 1 | `run()` | 51 edges | `tests/test_no_compress_guard.py` |
| 2 | `run()` | 42 edges | `tests/test_no_prune_guard.py` |
| 3 | `Verifier` | 38 edges | `scripts/verify_auto_mode.py` |