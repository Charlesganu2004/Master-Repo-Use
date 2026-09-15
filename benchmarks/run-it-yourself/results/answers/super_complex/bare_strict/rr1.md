All five confirmed as standalone entry points with `if __name__ == "__main__"` guards.

**The five harnesses and their entry scripts** (from source docstrings, all in `scripts/`, mirrored in `master_harness/`):

1. **Surface harness** — `scripts/auto_mode_harness.py` (installs the pipeline via hooks on Claude Code, Codex, Gemini CLI, Cursor, etc.)
2. **Proxy harness** — `scripts/harness_proxy.py` (OpenAI/Ollama-compatible proxy injecting the pipeline into every request)
3. **Wrapper harness** — `scripts/harness_wrap.py` (wraps any CLI with no hook mechanism)
4. **Goal harness** — `scripts/harness_goal.py` (surface harness plus a standing goal that survives the turn)
5. **Super harness** — `scripts/harness_super.py` (calls the other four, adding a longer 10-pass chain)

(`harness_computer.py` and `harness_paths.py` are explicitly *not* harnesses — the former self-describes as "a capability router, not another model harness," the latter is a shared path-resolution utility all harnesses call into.)

**Three most-connected symbols:**
- `run` — defined in `tests/test_no_compress_guard.py` (helper invoked 67 times in that file)
- `run` — defined in `tests/test_no_prune_guard.py` (helper invoked 46 times in that file)
- `Verifier` — class defined in `scripts/verify_auto_mode.py` (a large class whose many methods — `add`, `passed`, `failed`, `warned`, `skipped`, `_read_text`, `_read_json`, etc. — call each other internally, and which is also referenced by `tests/test_verify_auto_mode.py` and `tests/test_install_preservation.py`)

**Verifier's caller:** In `scripts/verify_auto_mode.py`, function **`main`** builds `verifier = Verifier(...)` and calls `verifier.run()` (line ~707).

**Single highest-impact file:** `scripts/verify_auto_mode.py` — it defines the densely-interconnected `Verifier` class (dozens of internal call edges) and is imported/exercised by two separate test files, so a change there ripples to the most callers of any file in the repo.