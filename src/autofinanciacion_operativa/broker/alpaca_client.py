from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import requests


class AlpacaClient:
    """Small REST wrapper for Alpaca paper-trading interactions."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        base_url: str = "https://paper-api.alpaca.markets",
    ) -> None:
        self.api_key = api_key or os.getenv("ALPACA_API_KEY", "")
        self.secret_key = secret_key or os.getenv("ALPACA_SECRET_KEY", "")
        self.base_url = base_url.rstrip("/")

    def _headers(self) -> Dict[str, str]:
        return {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.secret_key,
            "Content-Type": "application/json",
        }

    def get_account(self) -> Dict[str, Any]:
        response = requests.get(f"{self.base_url}/v2/account", headers=self._headers(), timeout=30)
        response.raise_for_status()
        return response.json()

    def list_positions(self) -> List[Dict[str, Any]]:
        response = requests.get(f"{self.base_url}/v2/positions", headers=self._headers(), timeout=30)
        response.raise_for_status()
        return response.json()

    def submit_order(
        self,
        symbol: str,
        qty: int | float | None = None,
        side: str = "buy",
        type: str = "market",
        time_in_force: str = "day",
    ) -> Dict[str, Any]:
        payload = {
            "symbol": symbol,
            "side": side,
            "type": type,
            "time_in_force": time_in_force,
        }
        if qty is not None:
            payload["qty"] = str(qty)

        response = requests.post(
            f"{self.base_url}/v2/orders",
            headers=self._headers(),
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        response = requests.get(
            f"{self.base_url}/v2/stocks/{symbol}/quotes/latest",
            headers=self._headers(),
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
