"""Tesorería r3dm/titan: pagar costes con ingresos y reinvertir solo lo autorizado.

Sin trading, criptomonedas, transferencias, cargos ni retiradas.
Todas las cantidades representan céntimos EUR.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


def _euros_cents(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} debe ser entero no negativo en céntimos")


@dataclass(frozen=True)
class ProviderBalance:
    """Saldo confirmado por API autenticada, no una cifra de formulario."""
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
        _euros_cents("available_cents", self.available_cents)
        if self.observed_at.tzinfo is None or now.tzinfo is None:
            raise ValueError("fechas con zona horaria obligatorias")
        if self.observed_at > now + timedelta(minutes=1):
            raise ValueError("la observación tiene fecha futura")
        if now - self.observed_at > max_age:
            raise ValueError("saldo desactualizado")


@dataclass(frozen=True)
class OperatingPolicy:
    """Límites aprobados por titular. Por defecto, gasto y reinversión cero."""
    tax_reserve_cents: int = 0
    refund_reserve_cents: int = 0
    unpaid_obligations_cents: int = 0  # facturas ya comprometidas: reserva, no gastar de nuevo
    pending_outbound_cents: int = 0
    minimum_cash_buffer_cents: int = 0
    requested_new_operating_expenses_cents: int = 0  # propuesta de nuevos costes reales
    daily_limit_cents: int = 0
    already_spent_today_cents: int = 0
    single_operation_limit_cents: int = 0
    reinvestment_share_basis_points: int = 0  # elegido por propietario: 0..10000

    def validate(self) -> None:
        for name, value in vars(self).items():
            _euros_cents(name, value)
        if self.reinvestment_share_basis_points > 10000:
            raise ValueError("proporción de reinversión máxima 100 %")


@dataclass(frozen=True)
class SpendingPlan:
    total_verified_available_cents: int
    reserved_cents: int
    usable_after_reserves_cents: int
    titan_reconciled_cash_limit_cents: int
    proposed_operating_expenses_cents: int
    proposed_reinvestment_cents: int
    remaining_unallocated_cents: int
    funds_transferred_cents: int = 0  # este módulo jamás mueve fondos


def plan_reinvestment(
    balances: list[ProviderBalance],
    policy: OperatingPolicy,
    *,
    titan_reconciled_cash_limit_cents: int,
    now: datetime | None = None,
    max_age: timedelta = timedelta(minutes=15),
) -> SpendingPlan:
    """Propone primero cubrir costes y después reinvertir un % del resto.

    El límite TITAN debe proceder de su libro mayor de cobros conciliados y
    egresos reales, NO del balance global de Stripe compartido con otros negocios,
    de un formulario, ni de facturas aún no cobradas. No usar una transferencia
    Stripe→banco simultáneamente en ambos balances; deduplicar previamente.
    Si falta evidencia del libro mayor, pasar 0 (resultado sin gasto).
    No ejecuta pagos: toda transferencia requiere autorización específica aparte.
    """
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None or max_age <= timedelta(0):
        raise ValueError("hora y antigüedad deben ser válidas")
    policy.validate()
    _euros_cents("titan_reconciled_cash_limit_cents", titan_reconciled_cash_limit_cents)
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
    free_provider_cash = max(0, total - reserve)
    usable = min(free_provider_cash, titan_reconciled_cash_limit_cents)
    daily_remaining = max(0, policy.daily_limit_cents - policy.already_spent_today_cents)
    proposed_operating = min(
        usable,
        policy.requested_new_operating_expenses_cents,
        daily_remaining,
        policy.single_operation_limit_cents,
    )
    after_costs = usable - proposed_operating
    reinvestment_target = after_costs * policy.reinvestment_share_basis_points // 10000
    proposed_reinvestment = min(
        reinvestment_target,
        max(0, daily_remaining - proposed_operating),
        policy.single_operation_limit_cents,
    )
    return SpendingPlan(
        total_verified_available_cents=total,
        reserved_cents=reserve,
        usable_after_reserves_cents=usable,
        titan_reconciled_cash_limit_cents=titan_reconciled_cash_limit_cents,
        proposed_operating_expenses_cents=proposed_operating,
        proposed_reinvestment_cents=proposed_reinvestment,
        remaining_unallocated_cents=after_costs - proposed_reinvestment,
    )
