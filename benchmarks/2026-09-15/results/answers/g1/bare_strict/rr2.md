**Three architectural hubs** (by cross-file reference count in the `master_harness` source, excluding `build/` copies and `graphify-out/`):

1. **`load_goal`** — defined in `<repo>\master_harness\skill_pipeline.py`. Called from `harness_goal.py`, `harness_super.py`, and 6 test files (`test_harness_family.py`, `test_goal_session_isolation.py`, `test_harness_super.py`, `test_budget_boundaries.py`, `test_refactor_layer.py`, `test_token_limit_and_super_mode.py`) — ~59 references, the busiest symbol in the tree.

2. **`repo_root`** — defined in `<repo>\master_harness\harness_paths.py`. This is the mode-detection primitive the module's own docstring calls out ("Every harness asks this module and gets a path"); it's called internally by `skills_dir`, `skill_path`, `state_dir`, `block_path`, and `project_dir` in the same file, and re-exported through `resources.py` and `_loader.py` for the rest of the package and tests — ~38 references.

3. **`skills_dir`** — also defined in `harness_paths.py`, built on top of `repo_root`. Consumed by `auto_mode_harness.py`, `harness_computer.py`, `install_auto_mode.py`, `verify_auto_mode.py`, re-exported via `resources.py`, and exercised in `test_install_preservation.py`/`test_package.py` — ~23 references.

Note: `harness_paths.py` supplies two of the three hubs (it's the single most depended-upon module, per its own docstring, to avoid "the same rule written seven times"); `scripts/*.py` are verified byte-identical staged copies of the `master_harness/*.py` originals, so counts were deduplicated to the canonical package files.