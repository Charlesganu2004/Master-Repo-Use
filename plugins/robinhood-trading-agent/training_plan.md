# Robinhood Trading Agent Training Plan

Use this plan for AI-assisted Robinhood or Robinhood-style trading research.

## Data

- Public market data first.
- Broker data only after credentials and permissions are reviewed.
- Store no credentials in repos.
- Record timestamp, source, asset type, and transformation.

## LLM Use

Use LLMs for:

- News and filing summaries.
- Sentiment extraction.
- Strategy explanation.
- Risk note generation.
- Trade proposal explanations.

Do not use LLMs to directly place orders.

## ML Use

Use ML for:

- Signal classification.
- Volatility regime detection.
- Position sizing suggestions.
- Risk scoring.

Rules:

- Use time-based splits.
- Include costs and slippage.
- Compare to simple baselines.
- Reject strategies with data leakage.

## Day-Trading Setup

1. Use a tiny symbol allowlist.
2. Use paper mode.
3. Add max orders per day.
4. Add cooldown.
5. Add stale quote checks.
6. Add daily loss stop.
7. Require manual approval for every live order.

## Promotion Gates

```text
research notebook
  -> backtest
  -> paper trading
  -> small monitored pilot
  -> live trading with human approval
```

The included plugin stops before live trading.
