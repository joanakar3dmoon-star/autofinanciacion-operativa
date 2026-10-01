from __future__ import annotations

from typing import Iterable, List

import numpy as np


class RiskMonitoringAgent:
    """Runs portfolio-level checks for drawdown and market risk exposure."""

    def __init__(self, max_drawdown: float = 0.10, var_limit: float = 0.05):
        self.max_drawdown = max_drawdown
        self.var_limit = var_limit

    def calculate_var(self, daily_returns: Iterable[float]) -> float:
        """Return a simple historical VaR estimate for the 5th percentile."""
        returns = np.asarray(list(daily_returns), dtype=float)
        if returns.size == 0:
            return 0.0
        return float(np.quantile(returns, 0.05))

    def evaluate_portfolio(self, daily_returns: Iterable[float], current_drawdown: float = 0.0) -> dict:
        """Check whether a trade would violate the configured risk constraints."""
        var_value = self.calculate_var(daily_returns)
        drawdown_ok = current_drawdown <= self.max_drawdown
        var_ok = var_value >= -self.var_limit

        return {
            "var_value": var_value,
            "current_drawdown": current_drawdown,
            "max_drawdown": self.max_drawdown,
            "drawdown_ok": drawdown_ok,
            "var_ok": var_ok,
            "is_blocked": not (drawdown_ok and var_ok),
            "reasons": [
                reason
                for reason, ok in {
                    "drawdown_exceeded": not drawdown_ok,
                    "var_exceeded": not var_ok,
                }.items()
                if not ok
            ],
        }
