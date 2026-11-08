"""Ensayos de la factoría de cuatro propuestas/hora y de la multitarea."""
import json
import sys
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from product_pipeline import START, GOALS, SECTORS, ANGLES, build_four, parse_hour, prepare_hour

class ProductFactoryTests(unittest.TestCase):
    def test_four_per_hour_and_five_task_families(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)
            a=prepare_hour(START, path)
            self.assertEqual(a["new_products"], 4)
            self.assertEqual(a["tasks_created"], 20)
            catalog=json.loads((path/"catalog.json").read_text(encoding="utf-8"))
            self.assertEqual(len(set(p["id"] for p in catalog["products"])),4)
            self.assertEqual(set(p["format"] for p in catalog["products"]),{"landing","seo","redes","emails"})
            queue=json.loads((path/"tasks.json").read_text(encoding="utf-8"))
            self.assertEqual(set(t["family"] for t in queue["tasks"]),
                             {"Buscadores","Ejecutores","Reinversores","Cazadores","Cerradores"})
            self.assertEqual(a["sale_enabled"],False)
    def test_restart_same_hour_is_idempotent(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)
            self.assertEqual(prepare_hour(START,path)["new_products"],4)
            self.assertEqual(prepare_hour(START,path)["new_products"],0)
            self.assertEqual(prepare_hour(START+timedelta(hours=1),path)["new_products"],4)
            catalog=json.loads((path/"catalog.json").read_text(encoding="utf-8"))
            self.assertEqual(len(catalog["products"]),8)
            self.assertEqual(len(set(p["id"] for p in catalog["products"])),8)
    def test_no_unauthorized_prices_payments_or_marketing(self):
        for p in build_four(START,set()):
            self.assertIsNone(p["price_eur"])
            self.assertIsNone(p["checkout_url"])
            self.assertEqual(p["orders"],0)
            self.assertEqual(p["revenue_cents"],0)
            self.assertEqual(p["commercial_state"],"borrador_para_revision")
            self.assertEqual(p["reference_store_url"],"https://r3dmtitan.com/servicios")
            self.assertGreater(len(" ".join(p["sample_content"])),200)
    def test_rotation_generates_unique_products(self):
        seen=set()
        for i in range(min(50,len(SECTORS)*len(GOALS)*len(ANGLES))):
            batch=build_four(START+timedelta(hours=i),seen)
            self.assertEqual(len(batch),4)
            seen.update(p["id"] for p in batch)
        self.assertEqual(len(seen),200)
    def test_bad_hour_rejected(self):
        with self.assertRaises(ValueError):
            parse_hour("2026-11-08T13:05:00+00:00")
        with self.assertRaises(ValueError):
            parse_hour("2026-11-07T23:00:00+00:00")
        with self.assertRaises(ValueError):
            parse_hour("2026-11-08T13:00:00")
    def test_malformed_old_catalog_fails_closed(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)
            (path/"catalog.json").write_text('{"schema":"quasar","products":[]}',encoding="utf-8")
            with self.assertRaises(ValueError):
                prepare_hour(START,path)

if __name__ == "__main__":
    unittest.main()
