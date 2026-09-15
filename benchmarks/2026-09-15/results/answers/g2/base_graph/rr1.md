GOAL: which file defines class Verifier, which function calls it — answering directly.

**File:** `<repo>\scripts\verify_auto_mode.py` (class `Verifier` at line 101).

**Caller:** function `main()` in that same file — line 707: `verifier = Verifier(pathlib.Path(args.repo), pathlib.Path(args.home), clients, installed_only=args.installed_only)`, then `verifier.run()` at line 709.

Confirmed via graphify `explain "Verifier"` (defined scripts/verify_auto_mode.py:L101) plus direct grep for `Verifier(` locating the sole instantiation inside `main()`.

Done: file and calling function both located and verified. Nothing left blocked.