from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RiskLimits:
    paper_trading_only: bool
    require_human_approval: bool
    allowed_symbols: tuple[str, ...]
    allowed_asset_types: tuple[str, ...]
    max_order_value_usd: float
    max_position_percent: float
    max_daily_loss_percent: float
    max_orders_per_day: int
    max_intraday_trades_per_symbol: int
    cooldown_seconds: int
    allow_short_selling: bool
    allow_options: bool
    stale_quote_seconds: int
    min_cash_reserve_usd: float
    require_backtest_pass: bool
    min_backtest_trades: int
    max_strategy_drawdown_percent: float
    min_strategy_sharpe: float
    kill_switch: bool


def load_risk_limits(path: str | Path) -> RiskLimits:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return RiskLimits(
        paper_trading_only=bool(data.get("paper_trading_only", True)),
        require_human_approval=bool(data.get("require_human_approval", True)),
        allowed_symbols=tuple(str(item).upper() for item in data.get("allowed_symbols", [])),
        allowed_asset_types=tuple(str(item).lower() for item in data.get("allowed_asset_types", [])),
        max_order_value_usd=float(data.get("max_order_value_usd", 0)),
        max_position_percent=float(data.get("max_position_percent", 0)),
        max_daily_loss_percent=float(data.get("max_daily_loss_percent", 0)),
        max_orders_per_day=int(data.get("max_orders_per_day", 0)),
        max_intraday_trades_per_symbol=int(data.get("max_intraday_trades_per_symbol", 0)),
        cooldown_seconds=int(data.get("cooldown_seconds", 0)),
        allow_short_selling=bool(data.get("allow_short_selling", False)),
        allow_options=bool(data.get("allow_options", False)),
        stale_quote_seconds=int(data.get("stale_quote_seconds", 30)),
        min_cash_reserve_usd=float(data.get("min_cash_reserve_usd", 0)),
        require_backtest_pass=bool(data.get("require_backtest_pass", True)),
        min_backtest_trades=int(data.get("min_backtest_trades", 0)),
        max_strategy_drawdown_percent=float(data.get("max_strategy_drawdown_percent", 0)),
        min_strategy_sharpe=float(data.get("min_strategy_sharpe", 0)),
        kill_switch=bool(data.get("kill_switch", False)),
    )
