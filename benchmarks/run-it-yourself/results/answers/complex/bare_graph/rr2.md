This confirms the full chain. Answer:

**Prompt → injected context pipeline**

- **Hook file:** `scripts/hooks/skill_pipeline.py` — the `UserPromptSubmit` hook (invoked via its `main()` at L840).
- **Function that builds the context:** `context_for()` (L158) inside that file. It assembles the core block plus at most one skill lane and fan-out advice, calling `capture()`, `resolve_token_limit()` / `parse_token_command()`, `standing_goal()`, `harness_mode()`, `token_block()`, and `chain_block()`.
- **File that adds the super harness chain on top:** `context_for()` calls `chain_block()` (also in `skill_pipeline.py`, L757), which lazily imports `scripts/hooks/super_chain.py` and appends its `super_block()` output — so the super-mode chain is layered on only when `super_chain` is importable (base mode pays nothing).

**Three most-connected symbols (god nodes)**

1. `run()` — 51 edges — `tests/test_no_compress_guard.py`
2. `run()` — 42 edges — `tests/test_no_prune_guard.py`
3. `Verifier` — 38 edges — `scripts/verify_auto_mode.py`

(Runners-up: `build()` — 28 edges — `scripts/build_atlas_data.py`; `IsolatedPublicSite` — 28 edges — `tests/public_site_fixture.py`.)