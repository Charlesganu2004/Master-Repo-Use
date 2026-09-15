**Five harnesses (entry scripts, from `tests/test_harness_family.py::INJECTION_SCRIPTS`):**
1. auto-mode-harness → `scripts/auto_mode_harness.py`
2. harness-proxy → `scripts/harness_proxy.py`
3. harness-wrap → `scripts/harness_wrap.py`
4. harness-goal → `scripts/harness_goal.py`
5. harness-super → `scripts/harness_super.py` (calls the other four)

**Three most connected symbols** (verified by reading each file, counting call sites — no graph tool used):
1. `run()` in `tests/test_no_compress_guard.py:24` — a local helper invoked ~67 times by the test methods in that file.
2. `run()` in `tests/test_no_prune_guard.py:22` — invoked ~46 times by that file's tests.
3. `Verifier` class in `scripts/verify_auto_mode.py:101` — a large class whose ~10+ methods (`add`, `passed`, `failed`, `warned`, `skipped`, `_read_text`, `_read_json`, `_check_instruction`, `_canonical_skills`, `_check_skill_tree`, …) call each other constantly, giving it the highest internal edge count of any class in the repo.

**Verifier's caller:** `main()` in the same file, `scripts/verify_auto_mode.py:707` (`verifier = Verifier(...)`, then `verifier.run()`).

**Highest-impact file:** `scripts/harness_paths.py` — its `repo_root()` is called directly by 15 other functions in that same module (`skills_dir`, `block_path`, `state_dir`, `hook_command`, `harness_command`, `describe`, etc.), and the module itself is imported by most of the harness scripts and tests (`auto_mode_harness.py`, `harness_goal.py`, `harness_super.py`, `harness_computer.py`, `skill_pipeline.py`, `install_auto_mode.py`, `verify_auto_mode.py`), so changing it would ripple to the most callers of any file in the repository.