"""Loader canónico del ground truth MIROVA (CONS ∪ OCR).

Centraliza la carga del CSV scrapeado de mirovaweb.it (repo Mirova-v1),
resolviendo los bugs del loader local detectados por la auditoría S86
(Subagente F, `docs/AUDIT_S86.md`):

- **F-B1**: los audits consumían solo CONS (latest.php) e ignoraban el
  canal OCR, que aporta ~344 ALERTAs únicas → subconteo MIROVA ~45%.
  El universo MIROVA real es CONS ∪ OCR (regla A11).
- **F-B2**: las filas OCR tienen `Distancia_km=0`; la distancia real vive
  en texto libre `Nota_Validacion` con formato `dist≈X.XX km`.
- **F-B4**: variante histórica `Peteroa` (CONS pre-2026-01-16) no migrada
  a `PlanchonPeteroa`.
- **A14**: variantes de nombre por volcán entre CONS y OCR.

El pipeline de detección NRT (`process_*.py`) NO usa este módulo — es
soporte de scripts de auditoría/evaluación. Por eso vive como módulo
independiente sin tocar la lógica de detección (no dispara regla A45).
"""
from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Optional


# === Normalización de nombre de volcán (11 Tier A, regla A14 + F-B4) ===

# Mapea cada variante observada en CONS/OCR al stem canónico del JSON.
# Las claves se comparan en lower-case + strip para robustez.
_VOLCANO_ALIASES = {
    "chaiten": "Chaiten",
    "copahue": "Copahue",
    "isluga": "Isluga",
    "lascar": "Lascar",
    "lastarria": "Lastarria",
    "llaima": "Llaima",
    "nevados de chillan": "NevadosDeChillan",
    "nevadosdechillan": "NevadosDeChillan",
    "planchonpeteroa": "PlanchonPeteroa",
    "planchon-peteroa": "PlanchonPeteroa",
    "peteroa": "PlanchonPeteroa",  # F-B4 variante huérfana histórica
    "puyehue-cordon caulle": "PuyehueCordonCaulle",
    "puyehuecordoncaulle": "PuyehueCordonCaulle",
    "tupungatito": "Tupungatito",
    "villarrica": "Villarrica",
}


def normalize_volcano_name(csv_label: str) -> Optional[str]:
    """Mapea una etiqueta de volcán del CSV al stem canónico del JSON.

    Devuelve None si el volcán no es uno de los 11 Tier A.
    """
    if csv_label is None:
        return None
    return _VOLCANO_ALIASES.get(str(csv_label).strip().lower())


# === Normalización de sensor (CSV → bucket, regla A48) ===

def normalize_sensor(sensor_raw: str) -> str:
    """Mapea el sensor del CSV MIROVA a un bucket canónico.

    Convención del CSV consolidado (= frontend mirovaSensorBucket, confirmada por
    Nicolás autor del scraper Mirova-v1):
    - MODIS → "MODIS"
    - "VIIRS375" (I-band 375m, etiqueta explícita) → "VIIRS375"
    - "VIIRS" (a secas) o "VIIRS750" → "VIIRS750" (M-band 750m)

    S93 fix (regla A48): la versión S86 mapeaba "VIIRS" → "VIIRS375", mandando las
    alertas VIIRS750 (M-band) al cajón equivocado → falso "MIROVA no usa VIIRS750".
    El orden importa: "375" explícito ANTES del genérico "VIIRS".
    """
    s = str(sensor_raw).strip().upper()
    if "MODIS" in s:
        return "MODIS"
    if "375" in s:
        return "VIIRS375"
    if "VIIRS" in s:  # "VIIRS" a secas o "VIIRS750" = M-band 750m
        return "VIIRS750"
    return s


# === Parseo de distancia OCR (F-B2) ===

# S120: el scraper cambió el formato de Nota_Validacion — ahora es
# 'Estrella verde en Y=283 -> 1.49 km (límite 3.0 km, geometría medida)'.
# El regex acepta ambos formatos (dist≈X km histórico y '-> X km' actual).
_OCR_DIST_RE = re.compile(r"(?:dist[≈~=]|->|→)\s*(\d+\.?\d*)\s*km")


def parse_ocr_distance(nota: str) -> Optional[float]:
    """Extrae la distancia en km del texto libre `Nota_Validacion`.

    Formatos reales OCR: 'Grupo píxeles rojos (área=50 px², dist≈12.94 km)'
    (histórico) y 'Estrella verde en Y=283 -> 1.49 km (límite 3.0 km, ...)'
    (scraper 2026-06+). Devuelve None si no hay patrón de distancia.
    """
    if not nota:
        return None
    m = _OCR_DIST_RE.search(str(nota))
    return float(m.group(1)) if m else None


# === Loader CONS ∪ OCR ===

_ALERT_TIPOS = {"ALERTA_TERMICA", "ALERTA_TERMICA_OCR"}


def _read_rows(path, source):
    if path is None or not Path(path).exists():
        return []
    out = []
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            row["_source"] = source
            out.append(row)
    return out


def load_mirova_alertas(
    cons_path=None,
    ocr_path=None,
    volcano: Optional[str] = None,
):
    """Carga las ALERTAs MIROVA del universo CONS ∪ OCR.

    Args:
        cons_path: ruta al registro_vrp_consolidado.csv (CONS / latest.php).
        ocr_path: ruta al registro_vrp_ocr.csv (canal OCR por imagen).
        volcano: si se da, filtra a ese volcán (stem canónico).

    Returns:
        Lista de dicts normalizados, uno por pasada-ALERTA, con campos:
        timestamp, volcano (canónico), sensor_bucket, vrp_mw, dist_km
        (resuelta de Distancia_km o Nota_Validacion), tipo, source (CONS/OCR),
        clasificacion, fecha_utc, fecha_local.

        Dedup por (timestamp, volcano, sensor_bucket): si una pasada está en
        CONS y OCR, se prioriza CONS (canal oficial latest.php).
    """
    raw = _read_rows(cons_path, "CONS") + _read_rows(ocr_path, "OCR")
    by_key = {}
    for row in raw:
        tipo = (row.get("Tipo_Registro") or "").strip()
        if tipo not in _ALERT_TIPOS:
            continue
        vol = normalize_volcano_name(row.get("Volcan"))
        if vol is None:
            continue
        if volcano is not None and vol != volcano:
            continue
        sensor_bucket = normalize_sensor(row.get("Sensor"))
        source = row["_source"]

        # Distancia: CONS usa Distancia_km; OCR la trae en Nota_Validacion.
        # F-B2 completo: las filas OCR traen Distancia_km=0 siempre — ese 0 es
        # "no informado", no "distancia cero". Si la nota no parsea, dist_km
        # queda None; NO heredar el 0.0 de Distancia_km (daría matches espurios
        # al vent en los cruces de auditoría).
        if source == "OCR":
            # S120: el scraper actual SÍ puebla Distancia_km real en algunas
            # filas OCR (geometría medida). Preferirla cuando >0; el 0 sigue
            # siendo "no informado" (F-B2), NUNCA distancia cero.
            try:
                _dk = float(row.get("Distancia_km") or 0.0)
            except (TypeError, ValueError):
                _dk = 0.0
            dist_km = _dk if _dk > 0 else parse_ocr_distance(row.get("Nota_Validacion", ""))
        else:  # CONS
            try:
                dist_km = float(row.get("Distancia_km"))
            except (TypeError, ValueError):
                dist_km = None

        try:
            vrp_mw = float(row.get("VRP_MW") or 0.0)
        except (TypeError, ValueError):
            vrp_mw = 0.0

        rec = {
            "timestamp": row.get("timestamp"),
            "volcano": vol,
            "sensor_bucket": sensor_bucket,
            "vrp_mw": vrp_mw,
            "dist_km": dist_km,
            "tipo": tipo,
            "source": source,
            "clasificacion": (row.get("Clasificacion Mirova") or "").strip(),
            "fecha_utc": row.get("Fecha_Satelite_UTC"),
            "fecha_local": row.get("Fecha_Captura_Chile"),
        }
        key = (rec["timestamp"], vol, sensor_bucket)
        # Dedup: CONS gana sobre OCR para la misma pasada.
        if key in by_key:
            if by_key[key]["source"] == "CONS":
                continue  # ya tenemos el canal oficial
            if source == "CONS":
                by_key[key] = rec  # reemplazar OCR por CONS
            continue
        by_key[key] = rec

    return list(by_key.values())
