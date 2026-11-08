"""Pruebas sin banco ni pagos de los ocho bots empresariales de TITAN."""
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wallet import OperatingPolicy, ProviderBalance
from bots_reinversion import ServiceRecord, VerifiedCost, execute_operational_bots

NOW = datetime(2026, 11, 8, 12, 0, tzinfo=timezone.utc)
POLICY = OperatingPolicy(
    requested_new_operating_expenses_cents=10000,
    reinvestment_share_basis_points=3000,
    daily_limit_cents=80000,
    single_operation_limit_cents=80000,
)


def run(services=None, costs=None, titan_limit=80000, policy=POLICY):
    return execute_operational_bots(
        balances=[ProviderBalance("stripe", 100000, NOW, True)],
        titan_reconciled_cash_limit_cents=titan_limit,
        policy=policy,
        services=services or [],
        costs=costs or [],
        now=NOW,
    )


class BotsTITANTests(unittest.TestCase):
    def test_eight_original_bots_are_preserved(self):
        report = run()
        self.assertEqual(set(report), {
            "Analista", "Presupuesto", "SEO", "Campañas",
            "Conversión", "Fideliza", "Control", "Escala"
        })

    def test_costs_first_and_partial_reinvestment(self):
        report = run()
        budget = report["Presupuesto"]
        self.assertEqual(budget["costes_operativos_propuestos_centimos"], 10000)
        self.assertEqual(budget["autoinversion_propuesta_centimos"], 21000)
        self.assertEqual(budget["sin_asignar_centimos"], 49000)
        self.assertFalse(budget["autorizacion_de_gasto"])
        self.assertEqual(report["Campañas"]["gastos_realizados_centimos"], 0)

    def test_organic_work_is_generated_as_draft(self):
        report = run(services=[ServiceRecord("landing", "Textos de página web", 4900)])
        self.assertEqual(report["SEO"]["activos"][0]["estado"], "borrador_no_publicado")
        self.assertIn("Textos de página web", report["Conversión"]["activos"][0]["texto_borrador"])
        self.assertEqual(report["Fideliza"]["destinatarios_contactados"], 0)

    def test_scaling_requires_real_earnings_and_owner_budget(self):
        service = ServiceRecord("seo", "Cinco artículos SEO", 5900, 3, 17700, 2000)
        self.assertEqual(run(services=[service])["Escala"]["prioridad_servicio"], "seo")
        self.assertIsNone(run(services=[service], titan_limit=0)["Escala"]["prioridad_servicio"])

    def test_control_flags_negative_margins_and_unapproved_costs(self):
        report = run(
            services=[ServiceRecord("x", "Oferta", 3000, 1, 3000, 4000)],
            costs=[VerifiedCost("factura-X", "herramienta", 2500, False)],
        )
        self.assertEqual(len(report["Control"]["alertas"]), 2)
        self.assertEqual(report["Analista"]["servicios"]["x"]["margen_centimos"], -1000)

    def test_duplicate_service_rejected(self):
        with self.assertRaises(ValueError):
            run(services=[ServiceRecord("x", "A", 100), ServiceRecord("x", "B", 200)])


if __name__ == "__main__":
    unittest.main()
