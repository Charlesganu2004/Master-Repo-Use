from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from .broker import LiveBrokerBlocked, PaperBroker
from .config import load_risk_limits
from .risk import RiskGate, TradeProposal
from .strategy import equal_weight_allocation, load_bars, moving_average_signal, simple_backtest


def _print_json(payload: object) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def _proposal_from_args(args: argparse.Namespace) -> TradeProposal:
    return TradeProposal(
        symbol=args.symbol.upper(),
        side=args.side.lower(),
        quantity=float(args.quantity),
        price=float(args.price),
        asset_type=args.asset_type.lower(),
        strategy=getattr(args, "strategy", "manual"),
        confidence=float(getattr(args, "confidence", 0.0)),
        portfolio_value_usd=float(getattr(args, "portfolio_value", 10000.0)),
        cash_available_usd=float(getattr(args, "cash_available", 10000.0)),
        current_daily_loss_percent=float(getattr(args, "daily_loss", 0.0)),
        orders_today=int(getattr(args, "orders_today", 0)),
        symbol_trades_today=int(getattr(args, "symbol_trades_today", 0)),
    )


def smoke_test(args: argparse.Namespace) -> int:
    limits = load_risk_limits(args.risk)
    proposal = TradeProposal(symbol="SPY", side="buy", quantity=1, price=400.0, asset_type="etf")
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


def live_order(args: argparse.Namespace) -> int:
    limits = load_risk_limits(args.risk)
    proposal = _proposal_from_args(args)
    decision = RiskGate(limits).evaluate(proposal)
    result = LiveBrokerBlocked().submit(proposal, decision, limits, args.approval_token)
    _print_json(asdict(result))
    return 2


def strategy_signal(args: argparse.Namespace) -> int:
    limits = load_risk_limits(args.risk)
    bars = load_bars(args.bars)
    signal = moving_average_signal(
        bars=bars,
        symbol=args.symbol,
        quantity=args.quantity,
        asset_type=args.asset_type,
        fast_window=args.fast_window,
        slow_window=args.slow_window,
    )

    payload: dict[str, object] = {"signal": asdict(signal)}
    if signal.side != "hold":
        proposal = TradeProposal(
            symbol=signal.symbol,
            side=signal.side,
            quantity=signal.quantity,
            price=signal.price,
            asset_type=signal.asset_type,
            strategy=signal.strategy,
            confidence=signal.confidence,
        )
        decision = RiskGate(limits).evaluate(proposal)
        payload["proposal"] = asdict(proposal)
        payload["risk"] = asdict(decision)
        _print_json(payload)
        return 0 if decision.approved else 2

    payload["risk"] = {"approved": False, "reasons": ["signal was hold; no order proposed"]}
    _print_json(payload)
    return 0


def backtest(args: argparse.Namespace) -> int:
    bars = load_bars(args.bars)
    result = simple_backtest(
        bars=bars,
        symbol=args.symbol,
        fast_window=args.fast_window,
        slow_window=args.slow_window,
        fee_bps=args.fee_bps,
    )
    _print_json(asdict(result))
    return 0


def invest_plan(args: argparse.Namespace) -> int:
    limits = load_risk_limits(args.risk)
    plan = equal_weight_allocation(args.capital, args.symbols.split(","))
    risk_gate = RiskGate(limits)
    proposals = []
    for order in plan.orders:
        price = float(args.assumed_price)
        quantity = float(order["target_value_usd"]) / price
        proposal = TradeProposal(
            symbol=str(order["symbol"]),
            side="buy",
            quantity=quantity,
            price=price,
            asset_type=args.asset_type,
            strategy="equal_weight_invest_plan",
            confidence=0.0,
            portfolio_value_usd=max(args.portfolio_value, args.capital),
            cash_available_usd=args.capital,
        )
        decision = risk_gate.evaluate(proposal)
        proposals.append({"proposal": asdict(proposal), "risk": asdict(decision)})

    _print_json({"plan": asdict(plan), "proposals": proposals})
    return 0 if all(item["risk"]["approved"] for item in proposals) else 2


def _add_trade_args(cmd: argparse.ArgumentParser) -> None:
    cmd.add_argument("--risk", required=True, help="Path to risk_limits JSON")
    cmd.add_argument("--symbol", required=True)
    cmd.add_argument("--side", choices=["buy", "sell"], required=True)
    cmd.add_argument("--quantity", type=float, required=True)
    cmd.add_argument("--price", type=float, required=True)
    cmd.add_argument("--asset-type", choices=["stock", "etf", "crypto", "option"], default="stock")
    cmd.add_argument("--strategy", default="manual")
    cmd.add_argument("--confidence", type=float, default=0.0)
    cmd.add_argument("--portfolio-value", type=float, default=10000.0)
    cmd.add_argument("--cash-available", type=float, default=10000.0)
    cmd.add_argument("--daily-loss", type=float, default=0.0)
    cmd.add_argument("--orders-today", type=int, default=0)
    cmd.add_argument("--symbol-trades-today", type=int, default=0)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Autonomous day-trading agent starter CLI")
    sub = parser.add_subparsers(required=True)

    smoke = sub.add_parser("smoke-test", help="Run a paper-mode smoke test")
    smoke.add_argument("--risk", required=True)
    smoke.set_defaults(func=smoke_test)

    for name, handler, help_text in [
        ("propose", propose, "Evaluate a proposed trade"),
        ("paper-order", paper_order, "Submit a paper order"),
        ("live-order", live_order, "Attempt a live route; blocked by default"),
    ]:
        cmd = sub.add_parser(name, help=help_text)
        _add_trade_args(cmd)
        if name == "live-order":
            cmd.add_argument("--approval-token", default=None)
        cmd.set_defaults(func=handler)

    signal = sub.add_parser("strategy-signal", help="Generate an SMA crossover signal from CSV bars")
    signal.add_argument("--risk", required=True)
    signal.add_argument("--bars", required=True)
    signal.add_argument("--symbol", required=True)
    signal.add_argument("--quantity", type=float, required=True)
    signal.add_argument("--asset-type", choices=["stock", "etf", "crypto"], default="stock")
    signal.add_argument("--fast-window", type=int, default=5)
    signal.add_argument("--slow-window", type=int, default=20)
    signal.set_defaults(func=strategy_signal)

    bt = sub.add_parser("backtest", help="Run a toy SMA backtest from CSV bars")
    bt.add_argument("--bars", required=True)
    bt.add_argument("--symbol", required=True)
    bt.add_argument("--fast-window", type=int, default=5)
    bt.add_argument("--slow-window", type=int, default=20)
    bt.add_argument("--fee-bps", type=float, default=1.0)
    bt.set_defaults(func=backtest)

    invest = sub.add_parser("invest-plan", help="Create an equal-weight investment allocation proposal")
    invest.add_argument("--risk", required=True)
    invest.add_argument("--capital", type=float, required=True)
    invest.add_argument("--symbols", required=True, help="Comma-separated symbols")
    invest.add_argument("--asset-type", choices=["stock", "etf", "crypto"], default="etf")
    invest.add_argument("--assumed-price", type=float, default=100.0)
    invest.add_argument("--portfolio-value", type=float, default=10000.0)
    invest.set_defaults(func=invest_plan)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
