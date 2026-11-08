"""Ocho bots OPERATIVOS de TITAN: tareas reales sin especulación ni gasto.

Ejecutan cálculos y preparan activos digitales; no cobran, publican ni mueven fondos.
La integración productiva debe alimentar estas funciones solo con registros verificados
y persistir los resultados como trabajos, sin declararlos ventas.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from wallet import OperatingPolicy, ProviderBalance, plan_reinvestment


@dataclass(frozen=True)
class ServiceRecord:
    """Datos del catálogo y resultados económicos conciliados de TITAN."""
    service_id: str
    public_name: str
    price_cents: int
    paid_orders: int = 0
    collected_cents: int = 0
    incurred_costs_cents: int = 0

    def validate(self) -> None:
        if not self.service_id.strip() or not self.public_name.strip():
            raise ValueError("servicio sin nombre e identificador")
        for key in ("price_cents", "paid_orders", "collected_cents", "incurred_costs_cents"):
            value = getattr(self, key)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{key} no válido")


@dataclass(frozen=True)
class VerifiedCost:
    """Costes reales del negocio, obtenidos del libro mayor."""
    reference: str
    category: str
    cents: int
    approved: bool

    def validate(self) -> None:
        if not self.reference.strip() or not self.category.strip():
            raise ValueError("gasto sin referencia")
        if isinstance(self.cents, bool) or not isinstance(self.cents, int) or self.cents < 0:
            raise ValueError("importe de gasto no válido")


def execute_operational_bots(
    *,
    balances: list[ProviderBalance],
    titan_reconciled_cash_limit_cents: int,
    policy: OperatingPolicy,
    services: list[ServiceRecord],
    costs: list[VerifiedCost],
    business_url: str = "https://r3dmtitan.com/servicios",
    now: datetime | None = None,
) -> dict[str, Any]:
    """Ejecución efectiva y determinista. Contiene exactamente ocho resultados.

    Analista: márgenes conciliados. Presupuesto: límites. SEO y Conversión:
    borradores concretos listos para revisión. Campañas: solo planificación.
    Fideliza: texto genérico reutilizable, nunca envía a clientes.
    Control: alertas sobre costes y márgenes. Escala: decidir con evidencia.
    """
    now = now or datetime.now(timezone.utc)
    if not business_url.startswith("https://"):
        raise ValueError("solo enlaces HTTPS")
    ids: set[str] = set()
    for service in services:
        service.validate()
        if service.service_id in ids:
            raise ValueError("servicio duplicado")
        ids.add(service.service_id)
    refs: set[str] = set()
    for item in costs:
        item.validate()
        if item.reference in refs:
            raise ValueError("gasto duplicado")
        refs.add(item.reference)

    budget = plan_reinvestment(
        balances, policy, now=now,
        titan_reconciled_cash_limit_cents=titan_reconciled_cash_limit_cents,
    )
    margins = {
        s.service_id: {
            "servicio": s.public_name,
            "pedidos_pagados": s.paid_orders,
            "ingresos_cobrados_centimos": s.collected_cents,
            "costes_registrados_centimos": s.incurred_costs_cents,
            "margen_centimos": s.collected_cents - s.incurred_costs_cents,
        }
        for s in services
    }
    seo = [
        {
            "servicio": s.service_id,
            "titulo_seo_borrador": f"{s.public_name} | r3dm/titan"[:65],
            "descripcion_meta_borrador": f"Servicios digitales: {s.public_name}. Información y contratación online en r3dm/titan."[:155],
            "enlace_destino": business_url,
            "estado": "borrador_no_publicado",
        }
        for s in services
    ]
    conversion = [
        {
            "servicio": s.service_id,
            "texto_borrador": f"{s.public_name} — {s.price_cents / 100:.2f} €.",
            "llamada_a_accion": f"Consultar el servicio: {business_url}",
            "estado": "borrador_no_publicado",
        }
        for s in services
    ]
    alerts = [
        f"Gasto sin aprobación: {c.reference}"
        for c in costs if not c.approved
    ] + [
        f"Servicio con margen negativo: {s.service_id}"
        for s in services if s.collected_cents - s.incurred_costs_cents < 0
    ]
    profitable = [
        s for s in services if s.paid_orders >= 2 and
        s.collected_cents > s.incurred_costs_cents > -1
    ]
    profitable.sort(key=lambda s: s.collected_cents - s.incurred_costs_cents, reverse=True)
    return {
        "Analista": {
            "estado": "calculado",
            "servicios": margins,
            "ventas_inventadas": 0,
        },
        "Presupuesto": {
            "estado": "calculado",
            "disponible_titan_centimos": budget.usable_after_reserves_cents,
            "costes_operativos_propuestos_centimos": budget.proposed_operating_expenses_cents,
            "autoinversion_propuesta_centimos": budget.proposed_reinvestment_cents,
            "sin_asignar_centimos": budget.remaining_unallocated_cents,
            "porcentaje_elegido": policy.reinvestment_share_basis_points / 100,
            "autorizacion_de_gasto": False,
        },
        "SEO": {"estado": "borradores_generados", "activos": seo},
        "Campañas": {
            "estado": "pendiente_aprobacion",
            "presupuesto_maximo_propuesto_centimos": budget.proposed_reinvestment_cents,
            "campanas_publicadas": 0,
            "gastos_realizados_centimos": 0,
        },
        "Conversión": {"estado": "borradores_generados", "activos": conversion},
        "Fideliza": {
            "estado": "plantilla_generada",
            "texto_borrador": "Gracias por confiar en r3dm/titan. ¿Cómo ha resultado el servicio recibido? Estamos disponibles para cualquier revisión.",
            "destinatarios_contactados": 0,
        },
        "Control": {
            "estado": "revisado",
            "alertas": alerts,
            "gastos_aprobados_cobrados_centimos": sum(c.cents for c in costs if c.approved),
            "pagos_realizados_centimos": 0,
        },
        "Escala": {
            "estado": "propuesta" if profitable and budget.proposed_reinvestment_cents else "sin_evidencia_suficiente",
            "prioridad_servicio": profitable[0].service_id if profitable and budget.proposed_reinvestment_cents else None,
            "fondos_movidos_centimos": 0,
        },
    }
