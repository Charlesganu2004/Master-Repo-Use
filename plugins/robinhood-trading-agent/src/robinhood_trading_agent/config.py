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
    max_daily_loss_percent: float
    max_orders_per_day: int
    cooldown_seconds: int
    allow_short_selling: bool
    allow_options: bool
    stale_quote_seconds: int
    kill_switch: bool


def load_risk_limits(path: str | Path) -> RiskLimits:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return RiskLimits(
        paper_trading_only=bool(data.get("paper_trading_only", True)),
        require_human_approval=bool(data.get("require_human_approval", True)),
        allowed_symbols=tuple(data.get("allowed_symbols", [])),
        allowed_asset_types=tuple(data.get("allowed_asset_types", [])),
        max_order_value_usd=float(data.get("max_order_value_usd", 0)),
        max_daily_loss_percent=float(data.get("max_daily_loss_percent", 0)),
        max_orders_per_day=int(data.get("max_orders_per_day", 0)),
        cooldown_seconds=int(data.get("cooldown_seconds", 0)),
        allow_short_selling=bool(data.get("allow_short_selling", False)),
        allow_options=bool(data.get("allow_options", False)),
        stale_quote_seconds=int(data.get("stale_quote_seconds", 30)),
        kill_switch=bool(data.get("kill_switch", False)),
    )
