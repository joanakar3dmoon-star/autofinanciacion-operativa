"""Tests offline: ningún pago simulado habilita entrega."""
import json
import hmac
import hashlib
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from payment_fulfillment import (
    Order, verify_stripe_signature, stripe_paid_evidence,
    verified_bank_credit, release_paid_asset,
)

ORDER = Order("pedido-123456", "titan-seo-00014-eventos", 5900)
SECRET = "whsec_testing_only_not_real"


def signed_event(*, paid=True, livemode=True, amount=5900, product="titan-seo-00014-eventos"):
    event = {"id": "evt_test", "type": "checkout.session.completed", "livemode": livemode,
             "data": {"object": {"object": "checkout.session", "id": "cs_live_mocked_only",
                                 "payment_status": "paid" if paid else "unpaid",
                                 "client_reference_id": ORDER.order_id,
                                 "metadata": {"titan_product_id": product},
                                 "currency": "eur", "amount_total": amount}}}
    body = json.dumps(event).encode()
    when = 1794146400
    signature = hmac.new(SECRET.encode(), str(when).encode() + b"." + body, hashlib.sha256).hexdigest()
    return body, f"t={when},v1={signature}", when


class PaymentsAndDeliveryTest(unittest.TestCase):
    def test_signed_paid_order_can_prepare_delivery_only_after_approval(self):
        body, signature, now = signed_event()
        event = verify_stripe_signature(body, signature, SECRET, now=now)
        evidence = stripe_paid_evidence(event, ORDER)
        permit = release_paid_asset(order=ORDER, evidence=evidence, asset_content="A" * 1300,
                                    asset_approved=True, persisted_payment_verified=True)
        self.assertTrue(permit["release"])
        self.assertEqual(permit["next_action"], "authenticated_private_delivery")

    def test_unsigned_forged_webhook_rejected(self):
        body, _, now = signed_event()
        with self.assertRaises(ValueError):
            verify_stripe_signature(body, f"t={now},v1=not-a-real-hmac", SECRET, now=now)

    def test_stale_signature_rejected(self):
        body, sig, now = signed_event()
        with self.assertRaises(ValueError):
            verify_stripe_signature(body, sig, SECRET, now=now + 400)

    def test_unpaid_and_wrong_amount_rejected(self):
        for kw in ({"paid": False}, {"amount": 1}, {"product": "another-product"}, {"livemode": False}):
            body, sig, now = signed_event(**kw)
            with self.assertRaises(ValueError):
                stripe_paid_evidence(verify_stripe_signature(body, sig, SECRET, now=now), ORDER)

    def test_bizum_requires_confirmed_banking_feed(self):
        with self.assertRaises(ValueError):
            verified_bank_credit(ORDER, provider="bizum", amount_cents=5900, currency="eur",
                                 transaction_id="bank_tx_012345", reference_order_id=ORDER.order_id,
                                 settled=False, provider_api_authenticated=False)
        verified = verified_bank_credit(ORDER, provider="bizum", amount_cents=5900, currency="eur",
                                        transaction_id="bank_tx_012345", reference_order_id=ORDER.order_id,
                                        settled=True, provider_api_authenticated=True)
        with self.assertRaises(ValueError):
            release_paid_asset(order=ORDER, evidence=verified, asset_content="A" * 1300,
                               asset_approved=False, persisted_payment_verified=True)

    def test_payment_not_persisted_never_releases(self):
        body, sig, now = signed_event()
        proof = stripe_paid_evidence(verify_stripe_signature(body, sig, SECRET, now=now), ORDER)
        with self.assertRaises(ValueError):
            release_paid_asset(order=ORDER, evidence=proof, asset_content="A" * 1300,
                               asset_approved=True, persisted_payment_verified=False)

    def test_repeat_does_not_redeliver(self):
        body, sig, now = signed_event()
        proof = stripe_paid_evidence(verify_stripe_signature(body, sig, SECRET, now=now), ORDER)
        result = release_paid_asset(order=ORDER, evidence=proof, asset_content="A" * 1300,
                                    asset_approved=True, persisted_payment_verified=True,
                                    already_delivered=True)
        self.assertFalse(result["release"])

    def test_incomplete_asset_cannot_sell(self):
        body, sig, now = signed_event()
        proof = stripe_paid_evidence(verify_stripe_signature(body, sig, SECRET, now=now), ORDER)
        with self.assertRaises(ValueError):
            release_paid_asset(order=ORDER, evidence=proof, asset_content="x",
                               asset_approved=True, persisted_payment_verified=True)


if __name__ == "__main__":
    unittest.main()
