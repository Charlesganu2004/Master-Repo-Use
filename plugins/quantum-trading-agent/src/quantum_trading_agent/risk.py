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
        side = proposal.side.lower()
        symbol = proposal.symbol.upper()

        if self.limits.kill_switch:
            reasons.append("kill_switch is enabled")

        if self.limits.allowed_symbols and symbol not in self.limits.allowed_symbols:
            reasons.append(f"{symbol} is not in allowed_symbols")

        if side not in {"buy", "sell"}:
            reasons.append("side must be buy or sell")

        if side == "sell" and proposal.quantity < 0 and not self.limits.allow_short_selling:
            reasons.append("short selling is disabled")

        if proposal.quantity <= 0:
            reasons.append("quantity must be positive")

        if proposal.price <= 0:
            reasons.append("price must be positive")

        if proposal.order_value_usd > self.limits.max_order_value_usd:
            reasons.append(
                f"order value {proposal.order_value_usd:.2f} exceeds max_order_value_usd "
                f"{self.limits.max_order_value_usd:.2f}"
            )

        if proposal.asset_type == "option" and not self.limits.allow_options:
            reasons.append("options are disabled")

        if proposal.asset_type == "crypto" and not self.limits.allow_crypto:
            reasons.append("crypto is disabled")

        return RiskDecision(approved=not reasons, reasons=tuple(reasons))
