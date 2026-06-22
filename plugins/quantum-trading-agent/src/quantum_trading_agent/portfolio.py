from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PortfolioResult:
    method: str
    weights: dict[str, float]
    note: str


def optimize_portfolio(expected_returns: dict[str, float]) -> PortfolioResult:
    """Small deterministic optimizer placeholder.

    Replace this with Qiskit, PennyLane, OpenQAOA, or another quantum optimizer
    once your data, baseline, and risk gates work standalone.
    """
    positive = {symbol: max(value, 0.0) for symbol, value in expected_returns.items()}
    total = sum(positive.values())
    if total <= 0:
        equal = 1.0 / max(len(expected_returns), 1)
        weights = {symbol: round(equal, 4) for symbol in expected_returns}
        note = "all expected returns were non-positive; using equal weights"
    else:
        weights = {symbol: round(value / total, 4) for symbol, value in positive.items()}
        note = "positive-return normalized weights; quantum optimizer not yet enabled"

    return PortfolioResult(method="classical-placeholder", weights=weights, note=note)
