GOAL: name 3 most connected symbols (hubs) + defining file, in Master-Repo-Use — served now via `graphify god-nodes --json` + `explain` on each id.

Three architectural hubs:
1. `run()` — 51 edges — `tests/test_no_compress_guard.py:L24`
2. `run()` — 42 edges — `tests/test_no_prune_guard.py:L22`
3. `Verifier` — 38 edges — `scripts/verify_auto_mode.py:L101`

Done: goal answered directly from local graph query (no model calls, no files touched). Left out: full connection lists (each had ~18-31 more edges beyond the shown sample) — ask if you want them.