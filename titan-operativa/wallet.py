"""Planificador de autoinversión del negocio TITAN. No transfiere fondos."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True)
class ProviderBalance:
    """Saldo disponible confirmado por un proveedor autorizado."""
    provider: str
    available_cents: int
    observed_at: datetime
    livemode: bool
    currency: str = "EUR"

    def validate(self, now: datetime, max_age: timedelta) -> None:
        if not self.provider or not self.provider.strip():
            raise ValueError("proveedor sin identificar")
        if self.currency.upper() != "EUR":
            raise ValueError("solo se consolidan EUR")
        if not self.livemode:
            raise ValueError("el saldo procede de pruebas, no de dinero real")
        if isinstance(self.available_cents, bool) or not isinstance(self.available_cents, int) or self.available_cents < 0:
            raise ValueError("saldo disponible no válido")
        if self.observed_at.tzinfo is None or now.tzinfo is None:
            raise ValueError("fechas UTC con zona horaria obligatorias")
        if self.observed_at > now + timedelta(minutes=1):
            raise ValueError("la observación tiene fecha futura")
        if now - self.observed_at > max_age:
            raise ValueError("saldo desactualizado")


@dataclass(frozen=True)
class OperatingPolicy:
    """Las cantidades son céntimos de euro, jamás floats."""
    tax_reserve_cents: int = 0
    refund_reserve_cents: int = 0
    unpaid_obligations_cents: int = 0
    pending_outbound_cents: int = 0
    minimum_cash_buffer_cents: int = 0
    daily_limit_cents: int = 0
    already_spent_today_cents: int = 0
    single_operation_limit_cents: int = 0
    reinvestment_share_basis_points: int = 0  # 10000 = 100 %

    def validate(self) -> None:
        for name, value in vars(self).items():
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} debe ser un entero no negativo")
        if self.reinvestment_share_basis_points > 10000:
            raise ValueError("proporción máxima 100 %")


@dataclass(frozen=True)
class SpendingPlan:
    total_verified_available_cents: int
    reserved_cents: int
    usable_after_reserves_cents: int
    maximum_proposed_reinvestment_cents: int
    funds_transferred_cents: int = 0  # Este módulo nunca mueve dinero


def plan_reinvestment(
    balances: list[ProviderBalance],
    policy: OperatingPolicy,
    *,
    now: datetime | None = None,
    max_age: timedelta = timedelta(minutes=15),
) -> SpendingPlan:
    """Plan conservador: ninguna estimación de ingresos, solo saldos LIVE recientes.

    No llamar con saldos recibidos desde formularios: los adaptadores de proveedores
    deben obtenerlos por canal autenticado. Si falta uno, se excluye por completo.
    Los movimientos entre proveedores aún pendientes se descuentan en policy.
    """
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None or max_age <= timedelta(0):
        raise ValueError("hora y antigüedad deben ser válidas")
    policy.validate()
    seen: set[str] = set()
    total = 0
    for balance in balances:
        balance.validate(now, max_age)
        provider = balance.provider.lower().strip()
        if provider in seen:
            raise ValueError(f"proveedor duplicado: {provider}")
        seen.add(provider)
        total += balance.available_cents

    reserve = (
        policy.tax_reserve_cents
        + policy.refund_reserve_cents
        + policy.unpaid_obligations_cents
        + policy.pending_outbound_cents
        + policy.minimum_cash_buffer_cents
    )
    usable = max(0, total - reserve)
    allocated = usable * policy.reinvestment_share_basis_points // 10000
    daily_remaining = max(0, policy.daily_limit_cents - policy.already_spent_today_cents)
    proposal = min(allocated, daily_remaining, policy.single_operation_limit_cents)
    return SpendingPlan(
        total_verified_available_cents=total,
        reserved_cents=reserve,
        usable_after_reserves_cents=usable,
        maximum_proposed_reinvestment_cents=proposal,
    )
