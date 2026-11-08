"""Tests del trabajador orgánico: catálogo REAL requiere esquema e identidad válidos."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog_worker import validate_catalog, generate_organic_drafts


SAMPLE = {
    "schema": "titan-products-v1",
    "business_id": "r3dm-titan-marketing",
    "website": "https://r3dmtitan.com/servicios",
    "independent_owner": True,
    "external_checkout_enabled": False,
    "products": [
        {
            "id": "landing",
            "titulo": "Textos de página web completa",
            "descripcion": "Redacción de textos para la web de un negocio.",
            "precio_eur": 49,
        },
        {
            "id": "seo",
            "titulo": "Pack SEO: 5 artículos",
            "descripcion": "Cinco artículos para un blog.",
            "precio_eur": 59,
        },
    ],
}


class CatalogOrganicWorkerTests(unittest.TestCase):
    def test_real_catalog_generates_concrete_unpublished_drafts(self):
        result = generate_organic_drafts(validate_catalog(SAMPLE))
        self.assertEqual(result["product_count"], 2)
        self.assertEqual(result["orders_created"], 0)
        self.assertEqual(result["revenue_claimed_cents"], 0)
        self.assertEqual(result["drafts"][0]["service_id"], "landing")
        self.assertIn("49.00 €", result["drafts"][0]["organic_post"])
        self.assertEqual(result["drafts"][0]["status"], "borrador_sin_publicar")
        self.assertEqual(result["drafts"][0]["campaign_cost_cents"], 0)

    def test_unknown_business_blocked(self):
        mutated = {**SAMPLE, "business_id": "r3dm-quasar"}
        with self.assertRaises(ValueError):
            validate_catalog(mutated)

    def test_spoofed_checkout_url_blocked(self):
        mutated = {**SAMPLE, "website": "https://example.com/steal"}
        with self.assertRaises(ValueError):
            validate_catalog(mutated)

    def test_invalid_or_duplicate_products_blocked(self):
        with self.assertRaises(ValueError):
            validate_catalog({**SAMPLE, "products": [SAMPLE["products"][0]] * 2})
        with self.assertRaises(ValueError):
            validate_catalog({**SAMPLE, "products": [{**SAMPLE["products"][0], "precio_eur": -1}]})

    def test_one_cent_price_is_accepted(self):
        catalog = {**SAMPLE, "products": [{**SAMPLE["products"][0], "precio_eur": 0.29}]}
        result = validate_catalog(catalog)
        self.assertEqual(result["products"][0]["precio_centimos"], 29)


if __name__ == "__main__":
    unittest.main()
