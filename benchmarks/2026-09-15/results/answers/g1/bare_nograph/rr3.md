Three architectural hubs, ranked by call/import fan-in across the repo:

1. **`context_for()`** — `<repo>\scripts\hooks\skill_pipeline.py`
   The base hook-context builder. `harness_goal.py`'s `context_for` wraps it (`skill_pipeline.context_for(...)`), and `harness_super.py`'s `context_for` wraps that in turn — a three-deep delegation chain. Referenced across 15 files (~75 call sites): all harness variants (`auto_mode_harness`, `harness_ab_test`, `harness_goal`, `harness_proxy`, `harness_super`, `harness_wrap`) plus ~9 test files.

2. **`capture()`** — `<repo>\scripts\hooks\skill_pipeline.py`
   The prompt-submit hook entrypoint that sets/updates the standing goal. Same file as above, which overall has the highest module-level fan-in in the repo (26 files import `skill_pipeline`).

3. **`build()`** — `<repo>\scripts\build_atlas_data.py`
   The catalog aggregator: internally fans out to call 12 lane-producer functions (`stage_lanes`, `model_setup_lane`, `catalog_lanes`, `script_lanes`, `skill_lanes`, `agent_lanes`, etc.) and fans back in as the data source used by `build_public_site.py`, `load_catalog_mongo.py`, and ~10 test files (`test_atlas_designs.py`, `test_custom_surfaces.py`, `test_harness_super.py`, etc.).

Runner-up: `harness_paths.py` (13 files import it) supplies the shared `repo_root()`/`skills_dir()` primitives used throughout the harness family, but its per-symbol fan-in is lower than the three above.