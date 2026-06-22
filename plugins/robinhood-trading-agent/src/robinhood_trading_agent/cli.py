from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from .broker import CommunityRobinhoodLiveBlocked, PaperBroker, RobinhoodCryptoLiveBlocked
from .config import load_risk_limits
from .risk import RiskGate, TradeProposal
from .robinhood_crypto import build_crypto_order_dry_run


def _print_json(payload: object) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def _proposal_from_args(args: argparse.Namespace) -> TradeProposal:
    return TradeProposal(
        symbol=args.symbol.upper(),
        side=args.side.lower(),
        quantity=float(args.quantity),
        price=float(args.price),
        asset_type=args.asset_type.lower(),
    )


def smoke_test(args: argparse.Namespace) -> int:
    limits = load_risk_limits(args.risk)
    proposal = TradeProposal("BTC-USD", "buy", 0.001, 65000.0, "crypto")
    decision = RiskGate(limits).evaluate(proposal)
    result = PaperBroker().submit(proposal, decision)
    _print_json(asdict(result))
    return 0 if result.status == "accepted" else 2


def propose(args: argparse.Namespace) -> int:
    limits = load_risk_limits(args.risk)
    proposal = _proposal_from_args(args)
    decision = RiskGate(limits).evaluate(proposal)
    _print_json({"proposal": asdict(proposal), "risk": asdict(decision)})
    return 0 if decision.approved else 2


def paper_order(args: argparse.Namespace) -> int:
    limits = load_risk_limits(args.risk)
    proposal = _proposal_from_args(args)
    decision = RiskGate(limits).evaluate(proposal)
    result = PaperBroker().submit(proposal, decision)
    _print_json(asdict(result))
    return 0 if result.status == "accepted" else 2


def crypto_dry_run(args: argparse.Namespace) -> int:
    proposal = _proposal_from_args(args)
    _print_json(build_crypto_order_dry_run(proposal))
    return 0


def live_order(args: argparse.Namespace) -> int:
    limits = load_risk_limits(args.risk)
    proposal = _proposal_from_args(args)
    decision = RiskGate(limits).evaluate(proposal)

    if args.route == "community-robinhood":
        result = CommunityRobinhoodLiveBlocked().submit(proposal, decision)
    else:
        result = RobinhoodCryptoLiveBlocked().submit(proposal, decision, limits, args.approval_token)

    _print_json(asdict(result))
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Robinhood trading agent starter CLI")
    sub = parser.add_subparsers(required=True)

    smoke = sub.add_parser("smoke-test", help="Run a paper-mode smoke test")
    smoke.add_argument("--risk", required=True)
    smoke.set_defaults(func=smoke_test)

    for name, handler, help_text in [
        ("propose", propose, "Evaluate a trade proposal"),
        ("paper-order", paper_order, "Submit a paper order"),
        ("crypto-dry-run", crypto_dry_run, "Build a Robinhood Crypto dry-run request shape"),
        ("live-order", live_order, "Attempt live route; blocked by default"),
    ]:
        cmd = sub.add_parser(name, help=help_text)
        if name != "crypto-dry-run":
            cmd.add_argument("--risk", required=True)
        cmd.add_argument("--symbol", required=True)
        cmd.add_argument("--side", choices=["buy", "sell"], required=True)
        cmd.add_argument("--quantity", type=float, required=True)
        cmd.add_argument("--price", type=float, required=True)
        cmd.add_argument("--asset-type", choices=["crypto", "stock", "etf", "option"], required=True)
        if name == "live-order":
            cmd.add_argument("--approval-token", default=None)
            cmd.add_argument("--route", choices=["robinhood-crypto", "community-robinhood"], default="robinhood-crypto")
        cmd.set_defaults(func=handler)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
