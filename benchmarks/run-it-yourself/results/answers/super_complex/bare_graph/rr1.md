## Five harnesses (entry scripts)

1. **auto-mode-harness** — `scripts/auto_mode_harness.py`
2. **harness-proxy** — `scripts/harness_proxy.py`
3. **harness-wrap** — `scripts/harness_wrap.py`
4. **harness-goal** — `scripts/harness_goal.py`
5. **harness-super** — `scripts/harness_super.py`

(Confirmed by `HARNESSES` list in `scripts/build_atlas_data.py`, each entry with a `python scripts/<name>.py --check` command; each script also verified to exist on disk.)

## Three most-connected symbols

1. `run()` — 51 edges — `tests/test_no_compress_guard.py:24`
2. `run()` — 42 edges — `tests/test_no_prune_guard.py:22`
3. `Verifier` (class) — 38 edges — `scripts/verify_auto_mode.py:101`

## Verifier's caller

`main()` in `scripts/verify_auto_mode.py` instantiates and calls it:
```python
verifier = Verifier(pathlib.Path(args.repo), pathlib.Path(args.home),
                    clients, installed_only=args.installed_only)
return print_report(verifier.run())
```

## Most-impactful file

`tests/test_no_compress_guard.py` — its `run()` helper is called by 51 separate test functions in that file, making it the single file whose change would ripple to the most callers.