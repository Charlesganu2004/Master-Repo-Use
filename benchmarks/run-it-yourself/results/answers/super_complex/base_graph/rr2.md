Found the 5: harness-surface (`scripts/auto_mode_harness.py`), harness-proxy (`scripts/harness_proxy.py`), harness-wrap (`scripts/harness_wrap.py`), harness-goal (`scripts/harness_goal.py`), harness-super (`scripts/harness_super.py`).

**GOAL restated:** name each of 5 harnesses' entry scripts; name 3 most-connected symbols + defining file; name the function calling `Verifier`; state which single file's change hits the most callers. This turn: finished data-gathering via graphify god-nodes/explain + grep confirmation.

**5 harnesses (entry scripts):**
1. harness-surface — `scripts/auto_mode_harness.py`
2. harness-proxy — `scripts/harness_proxy.py`
3. harness-wrap — `scripts/harness_wrap.py`
4. harness-goal — `scripts/harness_goal.py`
5. harness-super — `scripts/harness_super.py`

**3 most-connected symbols (by graph degree):**
1. `run()` — `tests/test_no_compress_guard.py` (degree 51)
2. `run()` — `tests/test_no_prune_guard.py` (degree 42)
3. `Verifier` class — `scripts/verify_auto_mode.py` (degree 38)

**Verifier caller:** `main()` in `scripts/verify_auto_mode.py:680` instantiates and runs it — `verifier = Verifier(...)` at line 707.

**Most-impactful file:** `scripts/verify_auto_mode.py` — it defines the `Verifier` class (38 connections, 3rd-most-connected symbol repo-wide) called from its own `main()`, and is the subject of both guard tests (`test_no_compress_guard`, `test_no_prune_guard`), so changing it would ripple to the most callers/tests.

Done: all four parts answered. Nothing blocked. Left out (ask for detail if wanted): full list of 118 nodes from the truncated harness query, and the other 18 unlisted `Verifier` connections.