"""Motor de conciliación y entrega. No puede mover dinero ni vender por sí solo.

Backend-only: nunca aceptar un comprobante aportado por el comprador como
prueba de pago. Stripe exige firma de webhook; las entidades externas exigen
movimiento bancario acreditado mediante API del proveedor autorizado.
"""
from __future__ import annotations
import hashlib
import hmac
import json
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class Order:
    order_id: str
    product_id: str
    expected_amount_cents: int
    currency: str = "eur"


@dataclass(frozen=True)
class PaymentEvidence:
    provider: str
    provider_payment_id: str
    order_id: str
    product_id: str
    amount_cents: int
    currency: str
    confirmed: bool
    verified_source: str


def verify_stripe_signature(payload: bytes, signature: str, secret: str,
                            *, now: int | None = None) -> dict:
    """Implementa firma v1 oficial y tolerancia máxima de cinco minutos."""
    if not secret.startswith("whsec_"):
        raise ValueError("falta secreto legítimo del endpoint Stripe")
    entries = {}
    for pair in signature.split(","):
        if "=" not in pair:
            continue
        key, value = pair.split("=", 1)
        entries.setdefault(key, []).append(value)
    try:
        timestamp = int(entries["t"][0])
        signatures = entries["v1"]
    except (ValueError, IndexError, KeyError) as error:
        raise ValueError("cabecera Stripe-Signature inválida") from error
    if abs((int(time.time()) if now is None else now) - timestamp) > 300:
        raise ValueError("evento fuera de tolerancia")
    signed = str(timestamp).encode() + b"." + payload
    expected = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    if not any(hmac.compare_digest(expected, value) for value in signatures):
        raise ValueError("firma Stripe inválida")
    event = json.loads(payload)
    if not isinstance(event, dict):
        raise ValueError("Stripe event no es objeto")
    return event


def stripe_paid_evidence(event: dict, order: Order) -> PaymentEvidence:
    """No basta con 'checkout.session.completed': payment_status ha de ser paid.

    Todos los campos deben pertenecer al checkout ORIGINAL de TITAN,
    persistido previamente en su base de datos. Comparar la session.id con
    la session_id registrada para la orden en producción antes de entregar.
    """
    if event.get("livemode") is not True:
        raise ValueError("el evento no es LIVE")
    if event.get("type") not in ("checkout.session.completed", "checkout.session.async_payment_succeeded"):
        raise ValueError("evento no acredita cobro")
    session = event.get("data", {}).get("object", {})
    if session.get("object") != "checkout.session" or session.get("payment_status") != "paid":
        raise ValueError("la sesión no está pagada")
    metadata = session.get("metadata") or {}
    if session.get("client_reference_id") != order.order_id or metadata.get("titan_product_id") != order.product_id:
        raise ValueError("checkout sin vínculo con el pedido TITAN")
    amount = session.get("amount_total")
    if isinstance(amount, bool) or not isinstance(amount, int) or amount != order.expected_amount_cents:
        raise ValueError("importe no coincide con pedido")
    if session.get("currency", "").lower() != order.currency.lower():
        raise ValueError("moneda incorrecta")
    session_id = session.get("id")
    if not isinstance(session_id, str) or not session_id.startswith("cs_live_"):
        raise ValueError("identificador de checkout LIVE inválido")
    return PaymentEvidence(
        provider="stripe", provider_payment_id=session_id,
        order_id=order.order_id, product_id=order.product_id,
        amount_cents=amount, currency=order.currency, confirmed=True,
        verified_source="stripe_signed_webhook",
    )


def verified_bank_credit(
    order: Order, *, provider: str, amount_cents: int, currency: str,
    transaction_id: str, reference_order_id: str, settled: bool,
    provider_api_authenticated: bool,
) -> PaymentEvidence:
    """Conciliación bancaria de solo lectura. Jamás justificantes o capturas."""
    if provider not in ("bizum", "sepa", "revolut", "wise"):
        raise ValueError("proveedor externo no permitido")
    if not provider_api_authenticated or not settled:
        raise ValueError("el ingreso no está confirmado por el banco/proveedor")
    if reference_order_id != order.order_id:
        raise ValueError("referencia del ingreso no coincide")
    if not transaction_id or len(transaction_id) < 8:
        raise ValueError("no hay identificador de movimiento bancario verificable")
    if isinstance(amount_cents, bool) or not isinstance(amount_cents, int) or amount_cents != order.expected_amount_cents:
        raise ValueError("importe acreditado distinto del pedido")
    if currency.lower() != order.currency.lower():
        raise ValueError("moneda no coincide")
    return PaymentEvidence(
        provider=provider, provider_payment_id=transaction_id,
        order_id=order.order_id, product_id=order.product_id,
        amount_cents=amount_cents, currency=currency, confirmed=True,
        verified_source=f"{provider}_authenticated_bank_feed",
    )


def release_paid_asset(*, order: Order, evidence: PaymentEvidence,
                       asset_content: str, asset_approved: bool,
                       persisted_payment_verified: bool,
                       already_delivered: bool = False) -> dict:
    """Únicamente prepara un permiso interno para que el backend entregue.

    El backend debe bloquear la fila en transacción, confirmar el idempotency
    key en DB, guardar estado y generar un URL firmado/caducable por comprador.
    Nunca devolver aquí el archivo a un cliente sin autenticar.
    """
    if not asset_approved or len(asset_content.strip()) < 1200:
        raise ValueError("producto no aprobado o incompleto")
    if not persisted_payment_verified or not evidence.confirmed:
        raise ValueError("pago real no persistido/verificado")
    if (evidence.order_id, evidence.product_id, evidence.amount_cents) != (
        order.order_id, order.product_id, order.expected_amount_cents
    ):
        raise ValueError("pago ajeno al pedido")
    if evidence.currency.lower() != order.currency.lower():
        raise ValueError("moneda no coincide")
    if evidence.provider not in ("stripe", "bizum", "sepa", "revolut", "wise"):
        raise ValueError("proveedor no autorizado")
    if not evidence.provider_payment_id:
        raise ValueError("referencia del pago vacía")
    if already_delivered:
        return {"release": False, "reason": "already_delivered", "order_id": order.order_id}
    return {
        "release": True,
        "order_id": order.order_id,
        "product_id": order.product_id,
        "payment_provider": evidence.provider,
        "payment_reference": evidence.provider_payment_id,
        "asset_sha256": hashlib.sha256(asset_content.encode()).hexdigest(),
        "next_action": "authenticated_private_delivery",
    }
