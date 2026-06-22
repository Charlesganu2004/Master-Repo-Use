from __future__ import annotations

import os
from dataclasses import asdict, dataclass

from .config import RiskLimits
from .risk import RiskDecision, TradeProposal


@dataclass(frozen=True)
class OrderResult:
    status: str
    mode: str
    proposal: dict
    risk: dict
    message: str


class PaperBroker:
    def submit(self, proposal: TradeProposal, decision: RiskDecision) -> OrderResult:
        if not decision.approved:
            return OrderResult(
                status="rejected",
                mode="paper",
                proposal=asdict(proposal),
                risk=asdict(decision),
                message="risk gate rejected the proposal",
            )

        return OrderResult(
            status="accepted",
            mode="paper",
            proposal=asdict(proposal),
            risk=asdict(decision),
            message="paper order accepted; no live trade was placed",
        )


class LiveBrokerBlocked:
    def submit(
        self,
        proposal: TradeProposal,
        decision: RiskDecision,
        limits: RiskLimits,
        approval_token: str | None,
    ) -> OrderResult:
        live_env_enabled = os.getenv("ALLOW_LIVE_TRADING", "").lower() == "true"
        live_requested = not limits.paper_trading_only
        approved_by_human = bool(approval_token)

        if not (live_env_enabled and live_requested and approved_by_human and decision.approved):
            return OrderResult(
                status="blocked",
                mode="live",
                proposal=asdict(proposal),
                risk=asdict(decision),
                message="live trading blocked; paper mode is the default and required gates are not satisfied",
            )

        return OrderResult(
            status="blocked",
            mode="live",
            proposal=asdict(proposal),
            risk=asdict(decision),
            message="live broker adapter is intentionally not implemented in this starter scaffold",
        )
