**Goal (restated):** trace prompt→injected-context (hook file, context-building function, super-harness-chain file) + name the 3 most-connected symbols and their files. This turn answers all of it.
**Tools used:** graphify (query/god-nodes/explain, local AST graph, no model calls) for retrieval; Bash grep/sed and Read to quote exact lines as evidence.

**Prompt → injected context**
- **Hook file:** `scripts/hooks/skill_pipeline.py`. Its own docstring says so: "*This hook is mechanism 3. Claude Code's UserPromptSubmit and Antigravity's…*" (L19). `main()` (L826) is the entrypoint; e.g. L856: `print(json.dumps({"additional_context": context_for(find_prompt(event), session)}))`.
- **Function that builds the context:** `context_for(prompt, session=None, capturing=True, include_goal=True, mode=None, token_enforced=False)` at `skill_pipeline.py:158`. It assembles: the core layers, the best-matching lane, an orchestration note, the standing goal, the token-limit block, and then (L218-221):
```python
if (mode or harness_mode()) == "super":
    chain = chain_block()
    if chain:
        parts.append(chain)
```
- **File that adds the super-harness chain on top:** `scripts/hooks/super_chain.py`. `chain_block()` (`skill_pipeline.py:773`) lazily imports it — "*imported only in super mode so base mode pays nothing*" — and returns `super_chain.super_block()` (`super_chain.py:84`).

**Three most-connected symbols** (`graphify god-nodes --top 5`, ranked by edge degree):
1. `run()` — `tests/test_no_compress_guard.py:24` (51 edges)
2. `run()` — `tests/test_no_prune_guard.py:22` (42 edges)
3. `Verifier` — `scripts/verify_auto_mode.py:101` (38 edges)

Caveat worth flagging (Layer-3 review): #1 and #2 are two *different* functions that happen to share the name `run()`, each local to its own guard test file — not one shared, widely-imported symbol. So "most connected" here reflects two structurally busy test files rather than a single hub. `Verifier` (`scripts/verify_auto_mode.py`) is the first genuinely cross-referenced class-level symbol.

**Status:** Both parts of the standing goal are answered and complete this turn — nothing blocked. Goal stays standing (not lifted); say "goal clear" to lift it.