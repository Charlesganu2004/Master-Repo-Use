# Training Plan

This plugin is for paper-first engineering experiments. Do not use any trained model for live trading until the model, data, risk controls, and broker adapter are reviewed.

## Data

1. Use time-ordered data: OHLCV bars, spreads, quotes, news, filings, fundamentals, and macro data where relevant.
2. Track data source, timestamp, symbol universe, survivorship bias, fees, spreads, and missing values.
3. Split by time: train, validation, test, then walk-forward.
4. Never random-shuffle time series when measuring a trading strategy.

## Baselines

1. Buy and hold.
2. Equal-weight portfolio.
3. Moving average crossover.
4. Mean reversion.
5. Cash/no-trade baseline.

## ML, RL, LLM, And QML

| Model type | Use it for | Rule |
| --- | --- | --- |
| ML | Ranking, prediction, regime classification. | Compare against simple baselines. |
| RL | Policy experiments and allocation. | Include costs, slippage, and drawdown penalties. |
| LLM | Research summaries, sentiment extraction, explanations. | Do not let the LLM directly place live orders. |
| QML/quantum | Optimization or QML experiments. | Compare against classical baselines. |

## Acceptance Before Paper Automation

- Backtest includes fees, spread, and slippage.
- Out-of-sample test does not collapse.
- Max drawdown is inside configured limits.
- Trade count is large enough to matter.
- Strategy behavior is explainable.
- Risk gate rejects oversized, disallowed, stale, or repeated trades.

## Acceptance Before Live Adapter

- At least several weeks of paper trading logs.
- Manual review of every failure, rejection, and suspicious order.
- Broker permissions reviewed.
- Kill switch tested.
- Secrets stored outside the repo.
- Human approval token required per live order.
