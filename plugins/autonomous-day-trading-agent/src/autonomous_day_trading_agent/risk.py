from __future__ import annotations

from dataclasses import dataclass

from .config import RiskLimits


@dataclass(frozen=True)
class TradeProposal:
    symbol: str
    side: str
    quantity: float
    price: float
    asset_type: str = "stock"
    strategy: str = "manual"
    confidence: float = 0.0
    portfolio_value_usd: float = 10000.0
    cash_available_usd: float = 10000.0
    current_daily_loss_percent: float = 0.0
    orders_today: int = 0
    symbol_trades_today: int = 0

    @property
    def order_value_usd(self) -> float:
        return abs(self.quantity * self.price)


@dataclass(frozen=True)
class RiskDecision:
    approved: bool
    reasons: tuple[str, ...]


class RiskGate:
    def __init__(self, limits: RiskLimits):
        self.limits = limits

    def evaluate(self, proposal: TradeProposal) -> RiskDecision:
        reasons: list[str] = []
        symbol = proposal.symbol.upper()
        side = proposal.side.lower()
        asset_type = proposal.asset_type.lower()

        if self.limits.kill_switch:
            reasons.append("kill_switch is enabled")

        if self.limits.allowed_symbols and symbol not in self.limits.allowed_symbols:
            reasons.append(f"{symbol} is not in allowed_symbols")

        if self.limits.allowed_asset_types and asset_type not in self.limits.allowed_asset_types:
            reasons.append(f"{asset_type} is not in allowed_asset_types")

        if side not in {"buy", "sell"}:
            reasons.append("side must be buy or sell")

        if proposal.quantity <= 0:
            reasons.append("quantity must be positive")

        if proposal.price <= 0:
            reasons.append("price must be positive")

        if proposal.order_value_usd > self.limits.max_order_value_usd:
            reasons.append(
                f"order value {proposal.order_value_usd:.2f} exceeds max_order_value_usd "
                f"{self.limits.max_order_value_usd:.2f}"
            )

        if self.limits.max_position_percent > 0 and proposal.portfolio_value_usd > 0:
            position_percent = proposal.order_value_usd / proposal.portfolio_value_usd * 100
            if position_percent > self.limits.max_position_percent:
                reasons.append(
                    f"order is {position_percent:.2f}% of portfolio, above max_position_percent "
                    f"{self.limits.max_position_percent:.2f}"
                )

        if proposal.cash_available_usd - proposal.order_value_usd < self.limits.min_cash_reserve_usd and side == "buy":
            reasons.append("buy order would violate min_cash_reserve_usd")

        if proposal.current_daily_loss_percent >= self.limits.max_daily_loss_percent:
            reasons.append("current_daily_loss_percent reached max_daily_loss_percent")

        if self.limits.max_orders_per_day > 0 and proposal.orders_today >= self.limits.max_orders_per_day:
            reasons.append("max_orders_per_day has been reached")

        if (
            self.limits.max_intraday_trades_per_symbol > 0
            and proposal.symbol_trades_today >= self.limits.max_intraday_trades_per_symbol
        ):
            reasons.append("max_intraday_trades_per_symbol has been reached")

        if side == "sell" and not self.limits.allow_short_selling and asset_type in {"stock", "etf"}:
            reasons.append("short selling is disabled unless holdings are verified by a broker adapter")

        if asset_type == "option" and not self.limits.allow_options:
            reasons.append("options are disabled")

        return RiskDecision(approved=not reasons, reasons=tuple(reasons))
