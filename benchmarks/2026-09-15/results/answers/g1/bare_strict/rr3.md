Based on directly grepping the source (not graphify-out), ranking symbols by how many distinct files reference them:

1. **`context_for`** — defined in `scripts/hooks/skill_pipeline.py`. This is the busiest hub: it builds the per-prompt context block and is called from every harness entry point (`harness_goal.py`, `harness_wrap.py`, `harness_super.py`, `harness_proxy.py`, `harness_computer.py`, `harness_ab_test.py`, `auto_mode_harness.py`) plus ~8 test files — 15 distinct callers total.

2. **`skills_dir`** (alongside its sibling path helpers like `repo_root`) — defined in `scripts/harness_paths.py`. This module is the explicit "single source of truth for where everything lives" per its own docstring, re-exported through `master_harness/resources.py` and pulled into `auto_mode_harness.py`, `verify_auto_mode.py`, `install_auto_mode.py`, and `harness_computer.py` — 8 distinct callers.

3. **`resolve`/`build_bundle`** — defined in `scripts/auto_mode_harness.py`. Imported wholesale as `surface` by `harness_super.py` (`import auto_mode_harness as surface`) and referenced by `harness_wrap.py`, `harness_proxy.py`, and `scripts/hooks/skill_pipeline.py` to select and install skill bundles — the module itself is cited in 23 files repo-wide.

All three sit in the `scripts/` (and `scripts/hooks/`) layer that `master_harness/_loader.py` bootstraps at import time, confirming these three files are the structural core the rest of the harness (CLI, hooks, tests) is wired around.