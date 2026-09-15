GOAL: name 3 most-connected symbols + defining file, repo `Master-Repo-Use`. This turn: ran `graphify god-nodes --json` + `explain` on root, got answer.

Three architectural hubs:
1. `run()` (51 edges) — `tests/test_no_compress_guard.py:24`
2. `run()` (42 edges) — `tests/test_no_prune_guard.py:22`
3. `Verifier` (38 edges) — `scripts/verify_auto_mode.py:101`

Done: goal answered from repo root graph. Left: nothing pending; ask if you want next-ranked hubs (`build()` in scripts/build_atlas_data.py, 28 edges; `IsolatedPublicSite` in tests/public_site_fixture, 28 edges).