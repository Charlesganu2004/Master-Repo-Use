I have everything needed.

**Prompt → injected context flow**

- Hook file: `scripts/hooks/skill_pipeline.py`
- Function that builds the injected context: `context_for()` (defined at L158 in that file). It calls `chain_block()` (L757) to assemble the block content.
- The user's live prompt is fed in via `last_user_text()` in `scripts/harness_proxy.py` (L74), called from that file's `inject()` (L155/159) — this is "the newest user turn, which is what the pipeline scores its lanes against."
- Super harness chain addition: `scripts/hooks/super_chain.py` — `chain_block()` imports/invokes it only in super mode ("The super chain, imported only in super mode so base mode pays nothing"), layering the ten-pass super-harness chain on top of the base injected context built by `context_for()`.

Flow: `harness_proxy.py:inject()` → `last_user_text()` (grabs newest prompt) → `skill_pipeline.py:context_for()` (builds base context) → `chain_block()` → conditionally pulls in `super_chain.py` when super mode is active.

**Three most connected symbols (god nodes)**

1. `run()` — 51 edges — `tests/test_no_compress_guard.py`
2. `run()` — 42 edges — `tests/test_no_prune_guard.py`
3. `Verifier` — 38 edges — `scripts/verify_auto_mode.py`

(Runners-up: `build()` in `scripts/build_atlas_data.py`, 28 edges; `IsolatedPublicSite` in `tests/public_site_fixture.py`, 28 edges.)