"""Pruebas offline del motor de tesorería; nunca se contacta con un banco."""
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wallet import OperatingPolicy, ProviderBalance, plan_reinvestment


NOW = datetime(2026, 11, 8, 12, 0, tzinfo=timezone.utc)


def live(amount: int, provider: str = "stripe") -> ProviderBalance:
    return ProviderBalance(provider=provider, available_cents=amount, observed_at=NOW, livemode=True)


class AutoinversionOperativaTests(unittest.TestCase):
    def plan(self, amount=100_000, titan_limit=100_000, **options):
        policy = OperatingPolicy(**options)
        return plan_reinvestment([live(amount)], policy, titan_reconciled_cash_limit_cents=titan_limit, now=NOW)

    def test_default_zero_spending_and_reinvestment(self):
        p = self.plan()
        self.assertEqual((p.proposed_operating_expenses_cents, p.proposed_reinvestment_cents), (0, 0))
        self.assertEqual(p.funds_transferred_cents, 0)

    def test_paid_expenses_first_then_user_selected_partial_reinvestment(self):
        p = self.plan(requested_new_operating_expenses_cents=20_000,
                      reinvestment_share_basis_points=2500,
                      daily_limit_cents=100_000, single_operation_limit_cents=100_000)
        self.assertEqual(p.proposed_operating_expenses_cents, 20_000)
        self.assertEqual(p.proposed_reinvestment_cents, 20_000)
        self.assertEqual(p.remaining_unallocated_cents, 60_000)

    def test_reserves_not_available_to_spend(self):
        p = self.plan(tax_reserve_cents=40_000,
                      refund_reserve_cents=10_000,
                      unpaid_obligations_cents=15_000,
                      pending_outbound_cents=10_000,
                      minimum_cash_buffer_cents=25_000,
                      requested_new_operating_expenses_cents=10_000,
                      reinvestment_share_basis_points=10000,
                      daily_limit_cents=100_000, single_operation_limit_cents=100_000)
        self.assertEqual(p.usable_after_reserves_cents, 0)
        self.assertEqual(p.proposed_operating_expenses_cents, 0)
        self.assertEqual(p.proposed_reinvestment_cents, 0)

    def test_never_spend_revenue_of_other_business_in_shared_stripe(self):
        p = self.plan(titan_limit=0, requested_new_operating_expenses_cents=5_000,
                      reinvestment_share_basis_points=10000,
                      daily_limit_cents=10_000, single_operation_limit_cents=10_000)
        self.assertEqual((p.proposed_operating_expenses_cents, p.proposed_reinvestment_cents), (0, 0))

    def test_daily_limit_shared_by_expenses_and_reinvestment(self):
        p = self.plan(requested_new_operating_expenses_cents=10_000,
                      reinvestment_share_basis_points=10000,
                      daily_limit_cents=12_000, single_operation_limit_cents=100_000)
        self.assertEqual((p.proposed_operating_expenses_cents, p.proposed_reinvestment_cents), (10_000, 2_000))

    def test_percentage_is_owner_controlled(self):
        p = self.plan(reinvestment_share_basis_points=250,
                      daily_limit_cents=100_000, single_operation_limit_cents=100_000)
        self.assertEqual(p.proposed_reinvestment_cents, 2_500)
        with self.assertRaises(ValueError):
            OperatingPolicy(reinvestment_share_basis_points=10001).validate()

    def test_testmode_or_stale_money_rejected(self):
        with self.assertRaises(ValueError):
            plan_reinvestment([ProviderBalance("stripe", 1000, NOW, False)],
                              OperatingPolicy(), titan_reconciled_cash_limit_cents=1000, now=NOW)
        with self.assertRaises(ValueError):
            plan_reinvestment([ProviderBalance("stripe", 1000, NOW - timedelta(hours=1), True)],
                              OperatingPolicy(), titan_reconciled_cash_limit_cents=1000, now=NOW)

    def test_duplicate_providers_rejected(self):
        with self.assertRaises(ValueError):
            plan_reinvestment([live(1000), live(1000, "STRIPE")],
                              OperatingPolicy(), titan_reconciled_cash_limit_cents=1000, now=NOW)

    def test_negative_balance_and_negative_limits_rejected(self):
        with self.assertRaises(ValueError):
            self.plan(-10)
        with self.assertRaises(ValueError):
            self.plan(titan_limit=-1)
        with self.assertRaises(ValueError):
            self.plan(daily_limit_cents=-1)

    def test_no_unverified_income_and_no_movement(self):
        p = plan_reinvestment([], OperatingPolicy(requested_new_operating_expenses_cents=1000,
                             reinvestment_share_basis_points=10000, daily_limit_cents=10000,
                             single_operation_limit_cents=10000),
                             titan_reconciled_cash_limit_cents=0, now=NOW)
        self.assertEqual(p.total_verified_available_cents, 0)
        self.assertEqual(p.proposed_reinvestment_cents, 0)
        self.assertEqual(p.funds_transferred_cents, 0)


if __name__ == "__main__":
    unittest.main()
