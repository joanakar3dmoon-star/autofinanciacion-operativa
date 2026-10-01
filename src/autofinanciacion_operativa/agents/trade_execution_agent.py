from __future__ import annotations

from typing import Dict, Mapping


class TradeExecutionAgent:
    """Prepares broker orders under the constraints of the risk layer."""

    def __init__(self, paper_trading: bool = True):
        self.paper_trading = paper_trading

    def prepare_orders(
        self,
        target_weights: Mapping[str, float],
        current_weights: Mapping[str, float],
        risk_status: Mapping[str, object],
    ) -> Dict[str, object]:
        """Return order instructions if the strategy is permitted under current guardrails."""
        if risk_status.get("is_blocked", False):
            return {
                "status": "blocked",
                "orders": [],
                "reason": risk_status.get("reasons", ["risk_checks_failed"]),
            }

        orders: list[dict] = []
        for symbol in sorted(set(target_weights) | set(current_weights)):
            target = float(target_weights.get(symbol, 0.0))
            current = float(current_weights.get(symbol, 0.0))
            delta = target - current
            if abs(delta) < 1e-9:
                continue

            side = "buy" if delta > 0 else "sell"
            orders.append(
                {
                    "symbol": symbol,
                    "side": side,
                    "notional_delta": abs(delta),
                    "paper_trade": self.paper_trading,
                }
            )

        return {
            "status": "ready",
            "orders": orders,
            "mode": "paper_trading" if self.paper_trading else "live",
        }
