"""Lectura exclusiva del saldo Stripe LIVE. No contiene operaciones de escritura."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from wallet import ProviderBalance


def fetch_stripe_eur_available(*, restricted_key: str | None = None) -> ProviderBalance:
    """GET /v1/balance con clave restringida y alcance de solo lectura.

    Nunca colocar la clave en el repositorio, la aplicación móvil, URLs o logs.
    Esta función no ofrece transferencias, compras ni retiros.
    """
    key = restricted_key if restricted_key is not None else os.getenv("TITAN_STRIPE_RESTRICTED_KEY", "")
    if not key.startswith("rk_live_"):
        raise RuntimeError("falta clave Stripe LIVE restringida y de solo lectura")
    request = Request(
        "https://api.stripe.com/v1/balance",
        headers={"Authorization": f"Bearer {key}", "Accept": "application/json"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=10) as response:
            payload = json.load(response)
    except (HTTPError, URLError, TimeoutError, ValueError):
        raise RuntimeError("no se pudo verificar el saldo real en Stripe") from None

    if not isinstance(payload, dict) or payload.get("livemode") is not True:
        raise RuntimeError("Stripe no ha confirmado modo real")
    available = payload.get("available")
    if not isinstance(available, list):
        raise RuntimeError("respuesta de saldo Stripe incompleta")
    eur_total = 0
    for row in available:
        if not isinstance(row, dict):
            raise RuntimeError("formato de saldo Stripe inesperado")
        if row.get("currency") != "eur":
            continue
        amount = row.get("amount")
        if isinstance(amount, bool) or not isinstance(amount, int) or amount < 0:
            raise RuntimeError("saldo Stripe EUR no válido")
        eur_total += amount
    return ProviderBalance(
        provider="stripe",
        available_cents=eur_total,
        observed_at=datetime.now(timezone.utc),
        livemode=True,
        currency="EUR",
    )
