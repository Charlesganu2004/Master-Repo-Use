These are genuine, legitimate cross-file hubs (confirmed by inspecting their actual edges — `IsolatedPublicSite` is imported and used as a setup fixture by six separate test modules; `TradeProposal` is the shared data object referenced by every module in its plugin). Based on cross-file connectivity in the repo's dependency graph (`graphify-out/graph.json`), the three architectural hubs are:

1. **`IsolatedPublicSite`** — defined in `benchmarks/2026-09-15/tests/public_site_fixture.py`. A test fixture class imported/used by 6 different test files (`test_atlas_designs.py`, `test_build_version.py`, `test_public_allowlist.py`, `test_public_context_exclusion.py`, `test_public_site_privacy.py`, `build_pages_preview.py`).

2. **`TradeProposal`** — defined in `benchmarks/2026-09-15/plugins/robinhood-trading-agent/src/robinhood_trading_agent/risk.py`. The shared trade-order data object referenced across `broker.py`, `cli.py`, and `robinhood_crypto.py` in that plugin.

3. **`TradeProposal`** — defined in `benchmarks/2026-09-15/plugins/autonomous-day-trading-agent/src/autonomous_day_trading_agent/risk.py`. Same pattern as above (paired closely with its sibling `RiskGate` class in the same file), wired through that plugin's `broker.py`/`cli.py`/`strategy.py`.

(Note: paths are relative to the `benchmarks/2026-09-15` snapshot inside the repo; a near-identical `TradeProposal`/`RiskGate` pair also exists in the `quantum-trading-agent` plugin, just slightly less connected.)