from __future__ import annotations

from dataclasses import asdict

from .risk import TradeProposal


def build_crypto_order_dry_run(proposal: TradeProposal) -> dict:
    """Return a dry-run request shape for a Robinhood Crypto order.

    This function intentionally does not sign or submit requests. Implement signing
    and network calls only after reviewing the current official Robinhood Crypto API
    docs and adding audit logs, idempotency, and human approval.
    """
    if proposal.asset_type != "crypto":
        raise ValueError("Robinhood Crypto dry-run route only accepts asset_type=crypto")

    return {
        "dry_run": True,
        "route": "robinhood_crypto",
        "proposal": asdict(proposal),
        "implementation_note": (
            "Add current Robinhood Crypto API signing and order endpoint handling here; "
            "do not store credentials in the repo."
        ),
    }
