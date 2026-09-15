GOAL restated: name the 3 most-connected symbols (hubs) and defining file in Master-Repo-Use. This turn: ran `graphify god-nodes --top 3` + `explain` on each — done, nothing blocked.

Top 3 hubs (by graph degree):
1. `run()` (test runner) — degree 51 — `tests/test_no_compress_guard.py` L24
2. `run()` (test runner) — degree 42 — `tests/test_no_prune_guard.py` L22
3. `Verifier` (class) — degree 38 — `scripts/verify_auto_mode.py` L101

Left out to fit 400-token cap: per-connection call lists (51/42/38 edges each), community labels (blank in graph). Ask for those or a `graphify path A B` between any pair if needed.