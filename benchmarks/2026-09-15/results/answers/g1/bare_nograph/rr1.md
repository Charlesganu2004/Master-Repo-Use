Confirmed by cross-checking against the extracted graph in `graphify-out/graph.json` (3,488 nodes / 6,206 edges) — computing degree centrality over code relations (calls, method, inherits, uses, references), excluding pure `contains`/`rationale_for` edges and unresolved external-library nodes:

1. **`run()`** — `tests/test_no_compress_guard.py` (line 24) — degree 50, the shared test-runner helper invoked by nearly every guard test case in that file.
2. **`run()`** — `tests/test_no_prune_guard.py` (line 22) — degree 41, the equivalent helper for the no-prune guard suite.
3. **`Verifier`** — `scripts/verify_auto_mode.py` (line 101) — degree 37, a class whose methods drive ~36 outbound calls orchestrating the auto-mode verification checks.

(Runner-up: `build()` in `scripts/build_atlas_data.py:2502`, degree 27.)