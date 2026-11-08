"""Bot SEO/Conversión de TITAN: genera borradores con el catálogo público REAL.

El origen es fijo, de solo lectura. No recibe contactos ni números bancarios.
No crea pedidos, no publica y no puede cobrar ni transferir dinero.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

CATALOG_URL = "https://r3dmtitan.com/api/public/catalogo-titan"
EXPECTED_SCHEMA = "titan-products-v1"
EXPECTED_BUSINESS = "r3dm-titan-marketing"
MAX_BYTES = 128 * 1024


class DenyRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RuntimeError("redirección no permitida desde el catálogo TITAN")


def fetch_public_catalog() -> dict:
    request = Request(
        CATALOG_URL,
        headers={"Accept": "application/json", "User-Agent": "r3dm-titan-organic-bot/1.0"},
        method="GET",
    )
    opener = build_opener(DenyRedirects)
    try:
        with opener.open(request, timeout=12) as response:
            if "application/json" not in response.headers.get("Content-Type", ""):
                raise ValueError("el endpoint no devuelve JSON")
            data = response.read(MAX_BYTES + 1)
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError("no se pudo consultar el catálogo TITAN (no se generaron productos)") from exc
    if len(data) > MAX_BYTES:
        raise ValueError("catálogo demasiado grande")
    return validate_catalog(json.loads(data.decode("utf-8")))


def validate_catalog(catalog: object) -> dict:
    if not isinstance(catalog, dict):
        raise ValueError("catálogo no es un objeto")
    if catalog.get("schema") != EXPECTED_SCHEMA or catalog.get("business_id") != EXPECTED_BUSINESS:
        raise ValueError("identidad del negocio o esquema incorrectos")
    if catalog.get("website") != "https://r3dmtitan.com/servicios":
        raise ValueError("enlace comercial inesperado")
    raw = catalog.get("products")
    if not isinstance(raw, list) or not 1 <= len(raw) <= 150:
        raise ValueError("catálogo sin productos válidos")
    products = []
    seen = set()
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("producto inválido")
        product_id = item.get("id")
        title = item.get("titulo")
        description = item.get("descripcion")
        amount = item.get("precio_eur")
        if not isinstance(product_id, str) or not re.fullmatch(r"[a-z0-9_-]{1,60}", product_id):
            raise ValueError("ID producto incorrecto")
        if product_id in seen:
            raise ValueError("producto duplicado")
        if not isinstance(title, str) or not 1 <= len(title.strip()) <= 140:
            raise ValueError("nombre producto incorrecto")
        if not isinstance(description, str) or len(description) > 1000:
            raise ValueError("descripción producto incorrecta")
        if isinstance(amount, bool) or not isinstance(amount, (int, float)) or amount < 0 or amount > 1_000_000:
            raise ValueError("precio no válido")
        if round(amount * 100) != amount * 100:
            raise ValueError("precio contiene fracciones de céntimo")
        seen.add(product_id)
        products.append({
            "id": product_id, "titulo": title.strip(),
            "descripcion": description.strip(), "precio_centimos": int(round(amount * 100)),
        })
    return {"website": catalog["website"], "products": products}


def generate_organic_drafts(validated_catalog: dict) -> dict:
    """Cada borrador tiene evidencia (id/precio/catálogo) y no declara ingresos."""
    products = validated_catalog["products"]
    drafts = []
    for item in products:
        title = item["titulo"]
        desc = item["descripcion"]
        drafts.append({
            "service_id": item["id"],
            "source": CATALOG_URL,
            "title": f"{title} | r3dm/titan"[:70],
            "meta_description": (f"{desc} Servicios digitales profesionales de r3dm/titan.").strip()[:160],
            "organic_post": (
                f"r3dm/titan · {title}. {desc} "
                f"Precio publicado: {item['precio_centimos'] / 100:.2f} €. "
                "Detalles y contratación: https://r3dmtitan.com/servicios"
            ),
            "status": "borrador_sin_publicar",
            "messages_sent": 0,
            "campaign_cost_cents": 0,
        })
    return {
        "schema": "titan-organic-drafts-v1",
        "business_id": EXPECTED_BUSINESS,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "verified_source": CATALOG_URL,
        "product_count": len(products),
        "drafts": drafts,
        "orders_created": 0,
        "revenue_claimed_cents": 0,
    }


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("Uso: python catalog_worker.py /ruta/borradores-titan.json", file=sys.stderr)
        return 2
    output = Path(argv[0])
    catalog = fetch_public_catalog()
    report = generate_organic_drafts(catalog)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"TITAN: {report['product_count']} servicios publicados → borradores preparados, sin envíos ni gastos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
