from __future__ import annotations

import argparse
import json
from pathlib import Path

from dotenv import load_dotenv

from autofinanciacion_operativa.config import settings
from autofinanciacion_operativa.runner import PortfolioAutomationRunner


def _parse_symbols(value: str | None) -> list[str]:
    if not value:
        return list(settings.default_symbols)
    return [symbol.strip().upper() for symbol in value.split(",") if symbol.strip()]


def main() -> None:
    load_dotenv(dotenv_path=Path(".env"), override=False)

    parser = argparse.ArgumentParser(description="Run a single portfolio automation cycle.")
    parser.add_argument("--symbols", type=str, default=",".join(settings.default_symbols), help="Comma-separated tickers")
    parser.add_argument("--current-weights", type=str, default=None, help="Optional current portfolio weights as CSV, e.g. AAPL=0.4,MSFT=0.6")
    parser.add_argument("--paper-trading", action="store_true", default=settings.paper_trading, help="Force paper-trading mode")
    parser.add_argument("--print-json", action="store_true", help="Print the decision payload as JSON")
    args = parser.parse_args()

    symbols = _parse_symbols(args.symbols)
    runner = PortfolioAutomationRunner(symbols=symbols)

    current_weights = None
    if args.current_weights:
        pairs = {}
        for item in args.current_weights.split(","):
            if "=" not in item:
                continue
            symbol, ratio = item.split("=", 1)
            pairs[symbol.strip().upper()] = float(ratio)
        current_weights = pairs

    decision = runner.run_cycle(current_weights=current_weights)
    if args.print_json:
        print(json.dumps(decision, indent=2, default=str))

    print(f"Prepared {len(symbols)} symbols for cycle execution.")
    print(f"Risk blocked: {decision['risk_status'].get('is_blocked', False)}")
    print(f"Execution status: {decision['execution_plan'].get('status', 'unknown')}")


if __name__ == "__main__":
    main()
