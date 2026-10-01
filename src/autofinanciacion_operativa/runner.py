from __future__ import annotations

from pathlib import Path

from ..agents.portfolio_strategy_agent import PortfolioStrategyAgent
from ..agents.research_agent import ResearchAgent
from ..agents.risk_monitoring_agent import RiskMonitoringAgent
from ..agents.trade_execution_agent import TradeExecutionAgent
from ..config import settings
from ..journal.reflective_journal import ReflectiveJournal


class PortfolioAutomationRunner:
    """Orchestrates the end-to-end trading workflow at a high level."""

    def __init__(self, symbols: list[str] | None = None):
        self.symbols = symbols or list(settings.default_symbols)
        self.research_agent = ResearchAgent(self.symbols)
        self.strategy_agent = PortfolioStrategyAgent()
        self.risk_agent = RiskMonitoringAgent(
            max_drawdown=settings.max_drawdown,
            var_limit=settings.var_limit,
        )
        self.execution_agent = TradeExecutionAgent(paper_trading=settings.paper_trading)
        self.journal = ReflectiveJournal(settings.logs_dir)

    def run_cycle(self, current_weights: dict[str, float] | None = None) -> dict:
        """Run a single research -> allocation -> risk -> execution cycle."""
        market_data = self.research_agent.fetch_market_data()
        signals = self.research_agent.build_signals(market_data)
        target_weights = self.strategy_agent.optimize_weights(signals, current_weights or {})
        current_weights = current_weights or {symbol: 1.0 / len(self.symbols) for symbol in self.symbols}

        daily_returns = [float(signal.daily_return) for signal in signals]
        risk_status = self.risk_agent.evaluate_portfolio(daily_returns, current_drawdown=0.02)
        execution_plan = self.execution_agent.prepare_orders(target_weights, current_weights, risk_status)

        decision = {
            "market_data": market_data,
            "target_weights": target_weights,
            "current_weights": current_weights,
            "risk_status": risk_status,
            "execution_plan": execution_plan,
        }

        self.journal.append_decision(decision)
        return decision


if __name__ == "__main__":
    runner = PortfolioAutomationRunner()
    result = runner.run_cycle()
    print(result)
