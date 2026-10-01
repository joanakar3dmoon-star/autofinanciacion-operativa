from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Mapping


@dataclass
class ResearchSignal:
    symbol: str
    price: float
    daily_return: float
    momentum: str
    source: str = "yfinance"


class ResearchAgent:
    """Collects and transforms market data into normalized signals."""

    def __init__(self, symbols: Iterable[str] | None = None):
        self.symbols = tuple(symbols or ())

    def fetch_market_data(self) -> Dict[str, Dict[str, Any]]:
        """Return a dictionary of market metrics for the configured symbols."""
        if not self.symbols:
            return {}

        try:
            import yfinance as yf
        except Exception:  # pragma: no cover - optional dependency path
            return {
                symbol: {
                    "price": 0.0,
                    "daily_return": 0.0,
                    "momentum": "unknown",
                    "source": "mock",
                }
                for symbol in self.symbols
            }

        market_data: Dict[str, Dict[str, Any]] = {}
        for symbol in self.symbols:
            ticker = yf.Ticker(symbol)
            history = ticker.history(period="5d", auto_adjust=True)
            if history.empty:
                market_data[symbol] = {
                    "price": 0.0,
                    "daily_return": 0.0,
                    "momentum": "unknown",
                    "source": "mock",
                }
                continue

            close_series = history["Close"]
            latest_price = float(close_series.iloc[-1])
            previous_price = float(close_series.iloc[-2]) if len(close_series) > 1 else latest_price
            daily_return = (latest_price - previous_price) / previous_price if previous_price else 0.0
            momentum = "bullish" if daily_return >= 0 else "bearish"
            market_data[symbol] = {
                "price": latest_price,
                "daily_return": daily_return,
                "momentum": momentum,
                "source": "yfinance",
            }

        return market_data

    def build_signals(self, market_data: Mapping[str, Mapping[str, Any]]) -> list[ResearchSignal]:
        """Normalize market metrics into signal objects."""
        signals: list[ResearchSignal] = []
        for symbol, data in market_data.items():
            signals.append(
                ResearchSignal(
                    symbol=symbol,
                    price=float(data.get("price", 0.0)),
                    daily_return=float(data.get("daily_return", 0.0)),
                    momentum=str(data.get("momentum", "neutral")),
                    source=str(data.get("source", "unknown")),
                )
            )
        return signals
