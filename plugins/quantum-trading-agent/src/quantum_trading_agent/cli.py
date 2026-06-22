from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from .broker import LiveBrokerBlocked, PaperBroker
from .config import load_risk_limits
from .portfolio import optimize_portfolio
from .risk import RiskGate, TradeProposal


def _proposal_from_args(args: argparse.Namespace) -> TradeProposal:
    return TradeProposal(
        symbol=args.symbol.upper(),
        side=args.side.lower(),
        quantity=float(args.quantity),
        price=float(args.price),
        asset_type=args.asset_type,
    )


def _print_json(payload: object) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def smoke_test(args: argparse.Namespace) -> int:
    limits = load_risk_limits(args.risk)
    proposal = TradeProposal(symbol="MSFT", side="buy", quantity=1, price=100)
    decision = RiskGate(limits).evaluate(proposal)
    result = PaperBroker().submit(proposal, decision)
    _print_json(asdict(result))
    return 0


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


def live_order(args: argparse.Namespace) -> int:
    limits = load_risk_limits(args.risk)
    proposal = _proposal_from_args(args)
    decision = RiskGate(limits).evaluate(proposal)
    result = LiveBrokerBlocked().submit(proposal, decision, limits, args.approval_token)
    _print_json(asdict(result))
    return 2


def optimize_demo(_: argparse.Namespace) -> int:
    result = optimize_portfolio({"MSFT": 0.08, "AAPL": 0.06, "SPY": 0.04, "QQQ": 0.07})
    _print_json(asdict(result))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Quantum trading agent starter CLI")
    sub = parser.add_subparsers(required=True)

    smoke = sub.add_parser("smoke-test", help="Run a paper-mode smoke test")
    smoke.add_argument("--risk", required=True, help="Path to risk_limits JSON")
    smoke.set_defaults(func=smoke_test)

    for name, handler, help_text in [
        ("propose", propose, "Evaluate a proposed trade"),
        ("paper-order", paper_order, "Submit a paper order"),
        ("live-order", live_order, "Attempt a live order; blocked by default"),
    ]:
        cmd = sub.add_parser(name, help=help_text)
        cmd.add_argument("--risk", required=True, help="Path to risk_limits JSON")
        cmd.add_argument("--symbol", required=True)
        cmd.add_argument("--side", choices=["buy", "sell"], required=True)
        cmd.add_argument("--quantity", type=float, required=True)
        cmd.add_argument("--price", type=float, required=True)
        cmd.add_argument("--asset-type", default="stock", choices=["stock", "option", "crypto"])
        if name == "live-order":
            cmd.add_argument("--approval-token", default=None)
        cmd.set_defaults(func=handler)

    opt = sub.add_parser("optimize-demo", help="Run a small portfolio optimization demo")
    opt.set_defaults(func=optimize_demo)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
