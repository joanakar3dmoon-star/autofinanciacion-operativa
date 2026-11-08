"""r3dm/titan: factoría comercial de cuatro fichas de producto por hora.

Genera cuatro propuestas de packs de marketing para la parte pública y
reparte multitareas a los bots. Sin datos ficticios, costes, envíos o cobros.
Un producto no pasa a "comprable" hasta integrar Checkout y fulfillment real.
"""
from __future__ import annotations
import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

SECTORS = [
    ("peluquerias", "Peluquerías y barberías", "reservas y presentación de servicios", "solicitar cita"),
    ("talleres", "Talleres mecánicos", "solicitudes de presupuesto y citas", "consultar reparación"),
    ("fisioterapia", "Clínicas de fisioterapia", "información de servicios y citas", "solicitar información"),
    ("restaurantes", "Restaurantes y cafeterías", "cartas y consultas de reservas", "consultar disponibilidad"),
    ("gimnasios", "Gimnasios y entrenadores", "información de programas y consultas", "conocer los programas"),
    ("comercios", "Comercios y tiendas locales", "catálogos y consultas comerciales", "consultar catálogo"),
    ("instaladores", "Fontaneros y electricistas", "solicitudes de presupuesto", "pedir presupuesto"),
    ("inmobiliarias", "Inmobiliarias", "información de inmuebles y visitas", "pedir información"),
    ("academias", "Academias de formación", "información de cursos y plazas", "consultar los cursos"),
    ("veterinarios", "Clínicas veterinarias", "presentación de servicios y citas", "solicitar cita"),
    ("alojamientos", "Alojamientos rurales", "consultas de estancia y servicios", "consultar estancia"),
    ("mantenimiento", "Empresas de limpieza y mantenimiento", "solicitudes de presupuesto", "pedir presupuesto"),
    ("fotografia", "Fotografía profesional", "presentación de portfolio y reservas", "consultar un proyecto"),
    ("artesania", "Artesanía y tiendas online", "colecciones y encargos", "consultar disponibilidad"),
    ("eventos", "Organización de eventos", "solicitudes de proyecto y disponibilidad", "solicitar propuesta"),
    ("jardineria", "Floristerías y jardinería", "encargos y servicios por temporada", "consultar un encargo"),
    ("panaderias", "Panaderías y pastelerías", "pedidos especiales y horarios", "consultar un pedido"),
    ("arquitectura", "Arquitectura e interiorismo", "portfolio y solicitudes de proyecto", "pedir una consulta"),
    ("turismo", "Actividades culturales y turismo", "programas y reservas de actividades", "consultar actividades"),
    ("informaticos", "Reparación de dispositivos", "diagnóstico y presupuesto", "consultar reparación"),
]
GOALS = [
    "simplificar la primera consulta", "presentar claramente los servicios",
    "dar confianza sin testimonios inventados", "explicar el proceso de contratación",
    "facilitar presupuestos y reservas", "atender dudas frecuentes",
    "dar visibilidad a una especialidad", "reducir la fricción desde el móvil",
]
ANGLES = [
    "práctico", "cercano", "directo", "detallado", "profesional", "didáctico",
    "minimalista", "orientado a preguntas", "enfocado en claridad", "local sin datos inventados",
    "para primera visita", "para clientes recurrentes",
]
FORMATS = [
    ("landing", "Pack de textos para página web", "Portada, servicios, preguntas frecuentes y llamadas a la acción"),
    ("seo", "Pack de 5 planes de contenidos SEO", "Cinco títulos, búsquedas de intención y guiones estructurados"),
    ("redes", "Pack de publicaciones para redes", "Calendario adaptable y 12 ejemplos de publicaciones"),
    ("emails", "Pack de emails comerciales", "Siete mensajes editables de bienvenida y seguimiento autorizado"),
]
SCHEMA = "titan-marketing-catalog-v1"
MAX_CATALOG = 1200
BASE_URL = "https://r3dmtitan.com/servicios"
START = datetime(2026, 11, 8, tzinfo=timezone.utc)

def parse_hour(value: str) -> datetime:
    hour = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if hour.tzinfo is None:
        raise ValueError("hora UTC con zona horaria obligatoria")
    hour = hour.astimezone(timezone.utc)
    if hour.minute or hour.second or hour.microsecond:
        raise ValueError("la hora se indica sin minutos ni segundos")
    if hour < START:
        raise ValueError("fecha fuera de la campaña")
    return hour

def _preview(format_id: str, sector: str, theme: str, action: str, goal: str, angle: str) -> list[str]:
    premise = f"Para {sector.lower()}: {goal}. Enfoque {angle}."
    if format_id == "landing":
        return [
            f"Portada propuesta: «{sector}: descubre nuestros servicios y da el siguiente paso con información clara».",
            f"Introducción: «Te explicamos qué opciones ofrecemos, cómo funciona el proceso y cómo {action}, sin compromiso ni promesas exageradas».",
            f"Servicios: bloque específico para {theme}; incluir alcance, condiciones y datos auténticos del comercio antes de publicar.",
            f"Preguntas frecuentes: «¿Qué incluye el servicio?», «¿Cómo se solicita?», «¿Qué datos necesitamos?» y «¿Cuándo respondemos?»; responder con la información del cliente.",
            f"Botón principal: «{action.capitalize()}». {premise}",
        ]
    if format_id == "seo":
        return [
            f"Guion 1: «Cómo elegir servicios de {sector.lower()}»; audiencia, preguntas y criterios reales.",
            f"Guion 2: «Qué preguntar antes de {action}»; listas de comprobación sin datos inventados.",
            f"Guion 3: «Proceso de {theme} paso a paso»; confirmación de la información empresarial.",
            f"Guion 4: «Dudas frecuentes sobre {theme}»; estructura H2 y H3 para resolver consultas.",
            f"Guion 5: «Guía para comparar opciones de {sector.lower()}»; transparencia sin ataques a competidores.",
        ]
    if format_id == "redes":
        return [
            f"Post 1 — Presentación: «¿Buscas información sobre {theme}? Conoce las opciones y cómo contactar».",
            f"Post 2 — Pregunta útil: «¿Qué necesitas saber antes de {action}? Aquí van los primeros pasos».",
            f"Post 3 — Transparencia: «Esto es lo que incluye el servicio y lo que conviene preguntar antes de decidir».",
            f"Calendario: 12 posts reutilizables, alternando información, preguntas, explicación del proceso y contacto; imágenes y horarios reales pendientes de completar.",
            f"CTA adaptable: «{action.capitalize()}». {premise}",
        ]
    if format_id == "emails":
        return [
            "Email 1 — Bienvenida a quien haya solicitado información: agradecer y explicar próximos pasos.",
            f"Email 2 — Oferta clara: explicar {theme} y cuándo conviene {action}.",
            "Email 3 — Preguntas frecuentes y objeciones: alcance, entrega y condiciones verificables.",
            "Email 4 — Ejemplo orientativo sin resultados fabricados ni supuestos clientes.",
            "Email 5 — Recordatorio moderado para contactos con consentimiento y opción de baja.",
            "Email 6 — Respuesta a una consulta pendiente, nunca envío masivo no solicitado.",
            f"Email 7 — Cierre cordial: ofrecer {action} y canal de atención. {premise}",
        ]
    raise ValueError("familia de producto desconocida")

def build_four(hour: datetime, existing_ids: set[str]) -> list[dict]:
    slot = int((hour - START).total_seconds() // 3600)
    combinations = len(SECTORS) * len(GOALS) * len(ANGLES)
    if slot >= combinations:
        raise ValueError("Variantes sectoriales agotadas: ampliar contenido de calidad antes de repetir productos")
    sector_slug, sector, theme, action = SECTORS[slot % len(SECTORS)]
    goal = GOALS[(slot // len(SECTORS)) % len(GOALS)]
    angle = ANGLES[(slot // (len(SECTORS) * len(GOALS))) % len(ANGLES)]
    result = []
    for fmt, label, content in FORMATS:
        key = f"titan-{fmt}-{slot:05d}-{sector_slug}"
        if key in existing_ids:
            continue
        preview = _preview(fmt, sector, theme, action, goal, angle)
        if len(preview) < 5 or len(" ".join(preview)) < 200:
            raise ValueError("contenido insuficiente; no generar producto vacío")
        result.append({
            "id": key, "created_hour_utc": hour.isoformat(), "format": fmt,
            "title": f"{label} · {sector} · {goal}",
            "sector": sector, "target": theme, "objective": goal,
            "tone": angle, "description": content,
            "sample_content": preview,
            "quality_gate": "texto_base_revisar_y_adaptar_a_cliente",
            "commercial_state": "borrador_para_revision",
            "price_eur": None, "checkout_url": None,
            "fulfillment_status": "requiere_pago_verificado_y_produccion",
            "reference_store_url": BASE_URL,
            "claims_verified": False,
            "orders": 0, "revenue_cents": 0,
        })
    return result

def _load(path: Path) -> dict:
    if not path.exists():
        return {"schema": SCHEMA, "brand": "r3dm/titan", "products": [], "generated_hours": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != SCHEMA or not isinstance(data.get("products"), list):
        raise ValueError("catálogo anterior incompatible; no sobrescribir")
    return data

def prepare_hour(hour: datetime, root: Path) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    catalog_path = root / "catalog.json"
    data = _load(catalog_path)
    ids = {p["id"] for p in data["products"]}
    created = build_four(hour, ids)
    if created:
        data["products"] = (created + data["products"])[:MAX_CATALOG]
        data["generated_hours"] = ([hour.isoformat()] + data.get("generated_hours", []))[:MAX_CATALOG // 4]
    queue = []
    for product in created:
        queue.extend([
            {"product_id": product["id"], "family": "Buscadores", "task": "Segmentar sector y necesidad", "status": "done"},
            {"product_id": product["id"], "family": "Ejecutores", "task": "Producir estructura y muestras", "status": "done"},
            {"product_id": product["id"], "family": "Reinversores", "task": "Controlar presupuesto y no gastar", "status": "done"},
            {"product_id": product["id"], "family": "Cazadores", "task": "Revisar calidad y preparar publicación orgánica", "status": "review_required"},
            {"product_id": product["id"], "family": "Cerradores", "task": "Conectar precio aprobado, Checkout y entrega posterior al pago", "status": "integration_blocked"},
        ])
    # La cola contiene solo la última tanda; ningún dato personal ni secreto.
    (root / "tasks.json").write_text(
        json.dumps({"hour_utc": hour.isoformat(), "new_products": len(created), "tasks": queue},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    catalog_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"new_products": len(created), "products_in_public_preview_catalog": len(data["products"]),
            "tasks_created": len(queue), "hour": hour.isoformat(), "sale_enabled": False}

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hour", required=True)
    parser.add_argument("--root", default="titan-operativa/tienda")
    args = parser.parse_args()
    report = prepare_hour(parse_hour(args.hour), Path(args.root))
    print(json.dumps(report, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
