# Training Plan

This plan is for training and evaluating ML, RL, QML, and LLM-assisted trading workflows. It is research-first and paper-trading-first.

## Data Setup

1. Pick a market universe: symbols, asset classes, dates, and market hours.
2. Gather data: OHLCV, fundamentals, filings, news, macro data, sentiment, and corporate actions.
3. Clean data: adjust prices, remove duplicates, align time zones, handle missing values.
4. Split by time: train, validation, test, and walk-forward windows.
5. Never random-shuffle time series for trading evaluation.
6. Record data version, source, timestamp, and transformations.

## Feature Setup

Feature families:

- Returns and log returns.
- Moving averages and momentum.
- Volatility and realized range.
- Volume and liquidity.
- Regime indicators.
- Sentiment and event features.
- Portfolio exposure and risk state.
- Quantum features or embeddings only after classical features work.

## Model Types

Classical baselines:

- Buy and hold.
- Equal weight.
- Moving average crossover.
- Mean variance optimization.
- Logistic regression or random forest.

ML:

- Gradient boosting.
- Random forests.
- Time-series models.
- Neural networks only after baselines.

RL:

- Use a paper environment.
- Include transaction cost, slippage, spread, and drawdown penalty.
- Limit action space.
- Evaluate out of sample.

QML / Quantum:

- Start with small circuits and simulators.
- Compare with classical models.
- Use Qiskit Finance, Qiskit Optimization, PennyLane, TensorFlow Quantum, or TorchQuantum.
- Log quantum backend, shot count, seed, and cost.

LLM:

- Use for research summaries, sentiment extraction, scenario explanations, and risk explanations.
- Do not use LLM output as an order by itself.
- Convert LLM output into structured signals, then pass through deterministic checks.
- Ground with RAG and cite sources.

## Evaluation

Track:

- Total return.
- Sharpe and Sortino.
- Max drawdown.
- Calmar ratio.
- Hit rate.
- Profit factor.
- Turnover.
- Exposure.
- Tail risk.
- Slippage sensitivity.
- Stability across regimes.

Reject strategies that:

- Only work in one time window.
- Fail after costs.
- Require unrealistic liquidity.
- Have unbounded position size.
- Depend on future data.
- Cannot explain risk.

## Promotion Gates

```text
notebook experiment
  -> reproducible script
  -> backtest
  -> walk-forward test
  -> paper trading
  -> manual review
  -> limited live pilot
  -> monitored production
```

Live trading is outside the default scaffold.
