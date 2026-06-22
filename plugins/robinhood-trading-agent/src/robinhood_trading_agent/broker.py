from __future__ import annotations

import os
from dataclasses import asdict, dataclass

from .config import RiskLimits
from .risk import RiskDecision, TradeProposal


@dataclass(frozen=True)
class OrderResult:
    status: str
    mode: str
    route: str
    proposal: dict
    risk: dict
    message: str


class PaperBroker:
    def submit(self, proposal: TradeProposal, decision: RiskDecision) -> OrderResult:
        if not decision.approved:
            return OrderResult(
                status="rejected",
                mode="paper",
                route="paper",
                proposal=asdict(proposal),
                risk=asdict(decision),
                message="risk gate rejected the proposal",
            )

        return OrderResult(
            status="accepted",
            mode="paper",
            route="paper",
            proposal=asdict(proposal),
            risk=asdict(decision),
            message="paper order accepted; no live Robinhood trade was placed",
        )


class RobinhoodCryptoLiveBlocked:
    def submit(
        self,
        proposal: TradeProposal,
        decision: RiskDecision,
        limits: RiskLimits,
        approval_token: str | None,
    ) -> OrderResult:
        allowed_env = os.getenv("ALLOW_LIVE_TRADING", "").lower() == "true"
        live_requested = not limits.paper_trading_only
        approval_present = bool(approval_token)

        if not (allowed_env and live_requested and approval_present and decision.approved):
            return OrderResult(
                status="blocked",
                mode="live",
                route="robinhood_crypto",
                proposal=asdict(proposal),
                risk=asdict(decision),
                message="live Robinhood Crypto order blocked; required gates are not satisfied",
            )

        return OrderResult(
            status="blocked",
            mode="live",
            route="robinhood_crypto",
            proposal=asdict(proposal),
            risk=asdict(decision),
            message="network order submission is intentionally not implemented in this scaffold",
        )


class CommunityRobinhoodLiveBlocked:
    def submit(self, proposal: TradeProposal, decision: RiskDecision) -> OrderResult:
        return OrderResult(
            status="blocked",
            mode="live",
            route="community_robinhood",
            proposal=asdict(proposal),
            risk=asdict(decision),
            message="community Robinhood stocks/options route is blocked in this scaffold",
        )
