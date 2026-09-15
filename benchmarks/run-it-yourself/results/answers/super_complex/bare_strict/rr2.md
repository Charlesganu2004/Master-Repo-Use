## Five harnesses and their entry scripts

1. **Surface harness** — `scripts/auto_mode_harness.py` (`if __name__ == "__main__"` → `main()`)
2. **Proxy harness** — `scripts/harness_proxy.py`
3. **Wrap harness** — `scripts/harness_wrap.py`
4. **Goal harness** — `scripts/harness_goal.py`
5. **Computer harness** — `scripts/harness_computer.py`

Each is mirrored (built/packaged copy) under `master_harness/<same name>.py` and dispatched via `master_harness/cli.py`/`master_harness/_loader.py`'s `HARNESSES` dict. A sixth file, `scripts/harness_super.py`, is the meta-harness that imports and calls these five rather than reimplementing them (its own docstring: "installs the surfaces, serves the proxy, wraps a command, carries the standing goal and routes computer control, by CALLING the four[/five] rather than reimplementing any of them").

## Three most-connected symbols

1. **`repo_root()`** — defined in `scripts/harness_paths.py` (mirrored in `master_harness/harness_paths.py`). Nearly every other function in that same module calls it first to resolve the checkout root (14 internal call sites), plus external callers in `master_harness/_loader.py` and `tests/test_package.py`.
2. **`hooks_dir()`** — defined in `scripts/harness_paths.py`. Called ~16 times from `install_auto_mode.py` and `verify_auto_mode.py` (both the `scripts/` and `master_harness/` copies) to locate hook scripts.
3. **`skills_dir()`** — defined in `scripts/harness_paths.py`. Called from `auto_mode_harness.py`, `harness_computer.py`, `install_auto_mode.py`, and `verify_auto_mode.py` to locate the skills source directory.

All three live in the same file, `scripts/harness_paths.py`, which is imported by roughly 20 files across `scripts/`, `master_harness/`, and `tests/`.

## `Verifier` caller

`class Verifier` is defined in `scripts/verify_auto_mode.py` (mirrored in `master_harness/verify_auto_mode.py`). It is instantiated and invoked by `main()` in that same file (`scripts/verify_auto_mode.py:707`, `verifier = Verifier(...); return print_report(verifier.run())`), which is the function run when the `verify` harness alias executes.

## Highest-impact file

If changed, **`scripts/harness_paths.py`** (and its packaged mirror `master_harness/harness_paths.py`) would affect the most callers, since it is the single module every harness, installer, and verifier imports to resolve paths like the repo root, skills directory, and hooks directory.