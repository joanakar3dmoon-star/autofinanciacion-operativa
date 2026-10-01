from __future__ import annotations

from typing import Dict, Iterable, Mapping


class PortfolioStrategyAgent:
    """Constructs target portfolio allocations from expected returns and risk signals."""

    def __init__(self, target_return: float = 0.08, risk_tolerance: float = 1.0):
        self.target_return = target_return
        self.risk_tolerance = risk_tolerance

    def optimize_weights(
        self,
        signals: Iterable[Mapping[str, float | str]],
        current_weights: Mapping[str, float] | None = None,
    ) -> Dict[str, float]:
        """Create a simple target-weight allocation based on signal strength."""
        scored: list[tuple[str, float]] = []
        for entry in signals:
            symbol = str(entry.get("symbol", ""))
            if not symbol:
                continue
            daily_return = float(entry.get("daily_return", 0.0))
            momentum = str(entry.get("momentum", "neutral")).lower()
            score = daily_return + (0.05 if momentum == "bullish" else -0.05 if momentum == "bearish" else 0.0)
            scored.append((symbol, score))

        if not scored:
            return {}

        total_score = sum(score for _, score in scored)
        if total_score == 0:
            equal_weight = 1.0 / len(scored)
            return {symbol: equal_weight for symbol, _ in scored}

        weights: Dict[str, float] = {}
        for symbol, score in scored:
            weights[symbol] = max(0.0, score / total_score)

        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {symbol: value / total_weight for symbol, value in weights.items()}

        return weights

    def compare_with_current(
        self,
        target_weights: Mapping[str, float],
        current_weights: Mapping[str, float],
    ) -> Dict[str, float]:
        """Return the delta between target and current weights."""
        universe = sorted(set(target_weights) | set(current_weights))
        return {
            symbol: target_weights.get(symbol, 0.0) - current_weights.get(symbol, 0.0)
            for symbol in universe
        }
