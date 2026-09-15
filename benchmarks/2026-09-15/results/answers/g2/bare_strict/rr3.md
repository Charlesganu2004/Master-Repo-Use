Confirmed from source directly.

**File:** `<repo>\scripts\verify_auto_mode.py`
- `class Verifier:` is defined at line 101.
- It is instantiated and called by `main()` (same file), at line 707: `verifier = Verifier(pathlib.Path(args.repo), pathlib.Path(args.home), ...)`, followed by `verifier.run()`.

Note: `tests\test_install_preservation.py` also instantiates `verifier_module.Verifier(...)`, but the primary caller in the source is `main()` in `scripts\verify_auto_mode.py`.