scripts/harness_paths.py clearly has the widest blast radius (29 affected nodes at depth 2 vs single digits for the others), consistent with it defining path helpers (`repo_root()`, `harness_modules_dir()`, `hooks_dir()`) imported across the harness family.

**Goal restated:** five harnesses' entry scripts; top-3 connected symbols + files; caller of `Verifier`; single highest-impact file.

**Five harnesses (from `tests/test_harness_family.py` `INJECTION_SCRIPTS`, entry = same-named script, ordered least→most reach):**
1. auto-mode-harness — `scripts/auto_mode_harness.py`
2. harness-proxy — `scripts/harness_proxy.py`
3. harness-wrap — `scripts/harness_wrap.py`
4. harness-goal — `scripts/harness_goal.py`
5. harness-super — `scripts/harness_super.py` (calls the other four)

**Three most connected symbols** (graphify `god-nodes --top 8 --json`):
1. `run()` — 51 edges — `tests/test_no_compress_guard.py`
2. `run()` — 42 edges — `tests/test_no_prune_guard.py`
3. `Verifier` (class) — 38 edges — `scripts/verify_auto_mode.py:101`

**Verifier's caller:** `main()` in `scripts/verify_auto_mode.py:707` — `verifier = Verifier(pathlib.Path(args.repo), pathlib.Path(args.home), clients, installed_only=args.installed_only)`, then `verifier.run()`.

**Highest-impact file:** `scripts/harness_paths.py` — `graphify affected` at depth 2 returns 29 dependents (vs. single digits for `verify_auto_mode.py`, `harness_super.py`, `auto_mode_harness.py`), since it supplies the shared path helpers (`repo_root()`, `harness_modules_dir()`, `hooks_dir()`) that the harness scripts and tests import.

Tools used: graphify (`god-nodes`, `explain`, `affected`), Grep/Read for the two lookups graphify's node-matching couldn't disambiguate (harness list, Verifier's exact call site) — no model-backed docs pass, all local. Goal check: all four parts answered, nothing blocked, nothing left outstanding.