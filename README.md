# autofinanciacion-operativa

A modular Python-based framework for a multi-agent automated portfolio and trading workflow.

## Architecture

This project is organized around the core operational flow described in the repository brief:

- Research Agent: fetches market data and transforms it into actionable signals
- Portfolio Strategy Agent: computes target weights and portfolio allocations
- Risk Monitoring Agent: performs drawdown and VaR checks before any trade
- Trade Execution Agent: prepares and validates orders for a broker or paper-trading account
- Reflective Journaling Module: stores decisions and portfolio state as timestamped JSON artifacts

## Repository structure

```text
.
├── README.md
├── .env.example
├── .gitignore
├── requirements.txt
├── pyproject.toml
├── src/
│   └── autofinanciacion_operativa/
│       ├── __init__.py
│       ├── config.py
│       ├── runner.py
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── research_agent.py
│       │   ├── portfolio_strategy_agent.py
│       │   ├── risk_monitoring_agent.py
│       │   └── trade_execution_agent.py
│       └── journal/
│           ├── __init__.py
│           └── reflective_journal.py
├── data/
│   └── .gitkeep
├── logs/
│   └── .gitkeep
├── tests/
│   └── test_agents.py
└── scripts/
    └── .gitkeep
```

## Quick start

1. Create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Copy the environment template:

```bash
cp .env.example .env
```

3. Add your broker and LLM credentials in `.env`.

4. Run a sample cycle:

```bash
python -m autofinanciacion_operativa.runner
```

## Safety and controls

- Default behavior is paper trading only.
- Risk constraints are evaluated before orders are executed.
- API credentials should be restricted to trading permissions only.
- Withdrawal permissions should be disabled for all automated systems.
- The journaling module stores decision context for audit and iterative improvement.

## Why this project matters

This starter structure is designed to support a disciplined, auditable automation workflow for portfolio management while minimizing operational risk. It is intentionally modular so each layer can evolve independently.

## Phase plan

### Phase 1: Environment and tools
- Configure Python environment and API credentials
- Start with paper-trading only

### Phase 2: Pipeline connection
- Connect broker APIs and market data sources
- Validate account/balance and quote fetch flows

### Phase 3: Scheduling and automation
- Trigger jobs at market open and close
- Deploy via cron or cloud task runners

### Phase 4: Audit and scaling
- Review journaling output daily
- Expand capabilities only after stability is validated

## Notes

This repository currently provides a clean starter architecture and intentionally avoids live execution by default. Replace the mock logic with real broker integration and production-grade controls when you are ready to proceed to live deployment.
