from __future__ import annotations

from autofinanciacion_operativa.agents.portfolio_strategy_agent import PortfolioStrategyAgent
from autofinanciacion_operativa.agents.research_agent import ResearchAgent
from autofinanciacion_operativa.agents.risk_monitoring_agent import RiskMonitoringAgent
from autofinanciacion_operativa.agents.trade_execution_agent import TradeExecutionAgent


def test_research_agent_returns_symbols():
    agent = ResearchAgent(["AAPL", "MSFT"])
    market_data = agent.fetch_market_data()
    assert set(market_data).issuperset({"AAPL", "MSFT"})


def test_portfolio_strategy_agent_weights_total_one():
    agent = PortfolioStrategyAgent()
    weights = agent.optimize_weights(
        [
            {"symbol": "AAPL", "daily_return": 0.02, "momentum": "bullish"},
            {"symbol": "MSFT", "daily_return": 0.01, "momentum": "bullish"},
        ]
    )
    assert abs(sum(weights.values()) - 1.0) < 1e-9


def test_risk_agent_flags_blocked_state():
    agent = RiskMonitoringAgent(max_drawdown=0.10, var_limit=0.05)
    status = agent.evaluate_portfolio([0.01, -0.12, -0.07, 0.02], current_drawdown=0.12)
    assert status["is_blocked"] is True


def test_trade_execution_agent_returns_ready_plan():
    agent = TradeExecutionAgent(paper_trading=True)
    plan = agent.prepare_orders(
        {"AAPL": 0.6, "MSFT": 0.4},
        {"AAPL": 0.5, "MSFT": 0.5},
        {"is_blocked": False, "reasons": []},
    )
    assert plan["status"] == "ready"
    assert len(plan["orders"]) >= 1
