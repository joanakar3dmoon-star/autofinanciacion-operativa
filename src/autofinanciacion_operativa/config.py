# Project settings and environment configuration

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    project_name: str = "autofinanciacion-operativa"
    base_dir: Path = BASE_DIR
    data_dir: Path = BASE_DIR / "data"
    logs_dir: Path = BASE_DIR / "logs"
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    alpaca_api_key: str = os.getenv("ALPACA_API_KEY", "")
    alpaca_secret_key: str = os.getenv("ALPACA_SECRET_KEY", "")
    paper_trading: bool = os.getenv("PAPER_TRADING", "true").lower() == "true"
    max_drawdown: float = float(os.getenv("MAX_DRAWDOWN", "0.10"))
    var_limit: float = float(os.getenv("VAR_LIMIT", "0.05"))
    default_symbols: tuple[str, ...] = (
        "AAPL",
        "MSFT",
        "AMZN",
        "SPY",
        "IWM",
    )


settings = Settings()
