I have everything needed to answer precisely.

## How a prompt becomes injected context

- **Hook file:** `scripts/hooks/skill_pipeline.py` (a UserPromptSubmit hook — its `main()` prints `{"hookSpecificOutput": {"additionalContext": ...}}`).
- **Function that builds the context:** `context_for(prompt, session=None, ...)` at `scripts/hooks/skill_pipeline.py:158`. It assembles the injected block in order: `CORE` text, an optional single best-matching skill "lane," an `ORCHESTRATION` note for large/multi-task prompts, the standing goal (`standing_goal()`), a token-limit block (`token_block()`), and finally — only in super mode — the chain block.
- **File that adds the super harness chain on top:** `scripts/hooks/super_chain.py`. Inside `context_for`, when `(mode or harness_mode()) == "super"`, it calls `chain_block()` (`skill_pipeline.py:757`), which lazily imports `super_chain` and returns `super_chain.super_block()` (defined in `scripts/hooks/super_chain.py:84`), appending that block last so base mode never pays the cost of loading it.

## Three most connected symbols (god nodes)

1. `run()` — 51 edges
2. `run()` — 42 edges (a second, distinct `run()` symbol elsewhere in the repo)
3. `Verifier` — 38 edges

(Runner-up: `build()` with 28 edges, tied with `IsolatedPublicSite`.)

Note: `graphify god-nodes` reports only the symbol name, edge count, and rank — it doesn't include each node's defining file in that output, and the two `run()` entries aren't disambiguated by path in the CLI result. To name the exact source file for each of these three, they'd need to be looked up individually (e.g. `graphify explain "run"` / `graphify explain "Verifier"` per candidate, or a grep for `def run(` / `class Verifier`), since multiple same-named `run()` functions exist across the repo (e.g. under `scripts/`, `master_harness/`, and test/benchmark harness files).