from __future__ import annotations

from dataclasses import dataclass

from .config import RiskLimits


@dataclass(frozen=True)
class TradeProposal:
    symbol: str
    side: str
    quantity: float
    price: float
    asset_type: str

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

        if side == "sell" and not self.limits.allow_short_selling and asset_type in {"stock", "etf"}:
            reasons.append("short selling is disabled unless holdings are verified by a broker adapter")

        if asset_type == "option" and not self.limits.allow_options:
            reasons.append("options are disabled")

        return RiskDecision(approved=not reasons, reasons=tuple(reasons))
