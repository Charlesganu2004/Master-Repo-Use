from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Bar:
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class StrategySignal:
    symbol: str
    side: str
    quantity: float
    price: float
    asset_type: str
    strategy: str
    confidence: float
    reason: str


@dataclass(frozen=True)
class BacktestResult:
    symbol: str
    strategy: str
    trades: int
    total_return_percent: float
    max_drawdown_percent: float
    win_rate_percent: float
    note: str


@dataclass(frozen=True)
class AllocationPlan:
    capital_usd: float
    weights: dict[str, float]
    orders: list[dict[str, float | str]]
    note: str


def load_bars(path: str | Path) -> list[Bar]:
    bars: list[Bar] = []
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"timestamp", "open", "high", "low", "close", "volume"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"bars CSV is missing columns: {', '.join(sorted(missing))}")

        for row in reader:
            bars.append(
                Bar(
                    timestamp=row["timestamp"],
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row["volume"]),
                )
            )
    return bars


def _sma(values: list[float], window: int) -> float:
    if window <= 0:
        raise ValueError("window must be positive")
    if len(values) < window:
        raise ValueError("not enough values for moving average window")
    return sum(values[-window:]) / window


def moving_average_signal(
    bars: list[Bar],
    symbol: str,
    quantity: float,
    asset_type: str = "stock",
    fast_window: int = 5,
    slow_window: int = 20,
) -> StrategySignal:
    if len(bars) < slow_window + 1:
        raise ValueError("not enough bars for signal; provide at least slow_window + 1 rows")

    closes = [bar.close for bar in bars]
    fast_now = _sma(closes, fast_window)
    slow_now = _sma(closes, slow_window)
    fast_prev = _sma(closes[:-1], fast_window)
    slow_prev = _sma(closes[:-1], slow_window)
    price = closes[-1]

    if fast_now > slow_now and fast_prev <= slow_prev:
        side = "buy"
        confidence = min((fast_now - slow_now) / max(price, 1.0) * 10, 1.0)
        reason = "fast moving average crossed above slow moving average"
    elif fast_now < slow_now and fast_prev >= slow_prev:
        side = "sell"
        confidence = min((slow_now - fast_now) / max(price, 1.0) * 10, 1.0)
        reason = "fast moving average crossed below slow moving average"
    else:
        side = "hold"
        confidence = 0.0
        reason = "no moving average crossover"

    return StrategySignal(
        symbol=symbol.upper(),
        side=side,
        quantity=quantity,
        price=round(price, 4),
        asset_type=asset_type.lower(),
        strategy=f"sma_{fast_window}_{slow_window}",
        confidence=round(confidence, 4),
        reason=reason,
    )


def simple_backtest(
    bars: list[Bar],
    symbol: str,
    fast_window: int = 5,
    slow_window: int = 20,
    fee_bps: float = 1.0,
) -> BacktestResult:
    if len(bars) < slow_window + 2:
        raise ValueError("not enough bars for backtest")

    cash = 10000.0
    shares = 0.0
    entry_price = 0.0
    wins = 0
    trades = 0
    peak_equity = cash
    max_drawdown = 0.0

    for index in range(slow_window + 1, len(bars)):
        window = bars[: index + 1]
        signal = moving_average_signal(window, symbol, quantity=1, fast_window=fast_window, slow_window=slow_window)
        price = window[-1].close
        fee = price * fee_bps / 10000

        if signal.side == "buy" and shares == 0:
            shares = (cash - fee) / price
            cash = 0.0
            entry_price = price
            trades += 1
        elif signal.side == "sell" and shares > 0:
            cash = shares * price - fee
            if price > entry_price:
                wins += 1
            shares = 0.0
            trades += 1

        equity = cash + shares * price
        peak_equity = max(peak_equity, equity)
        if peak_equity > 0:
            drawdown = (peak_equity - equity) / peak_equity * 100
            max_drawdown = max(max_drawdown, drawdown)

    final_equity = cash + shares * bars[-1].close
    total_return = (final_equity - 10000.0) / 10000.0 * 100
    win_rate = wins / max(trades // 2, 1) * 100 if trades else 0.0
    note = "toy backtest; replace with production backtesting before real trading"

    return BacktestResult(
        symbol=symbol.upper(),
        strategy=f"sma_{fast_window}_{slow_window}",
        trades=trades,
        total_return_percent=round(total_return, 4),
        max_drawdown_percent=round(max_drawdown, 4),
        win_rate_percent=round(min(win_rate, 100.0), 4),
        note=note,
    )


def equal_weight_allocation(capital_usd: float, symbols: list[str]) -> AllocationPlan:
    clean_symbols = [symbol.strip().upper() for symbol in symbols if symbol.strip()]
    if not clean_symbols:
        raise ValueError("at least one symbol is required")
    weight = 1.0 / len(clean_symbols)
    orders = [
        {"symbol": symbol, "side": "buy", "target_value_usd": round(capital_usd * weight, 2)}
        for symbol in clean_symbols
    ]
    weights = {symbol: round(weight, 4) for symbol in clean_symbols}
    return AllocationPlan(
        capital_usd=round(capital_usd, 2),
        weights=weights,
        orders=orders,
        note="equal-weight allocation proposal; not financial advice",
    )
