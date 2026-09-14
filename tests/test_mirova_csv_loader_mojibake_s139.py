# -*- coding: utf-8 -*-
"""S139: 578 de 846 ALERTA_TERMICA_OCR quedaban sin distancia porque el commit ffc7a97d8b de
Mirova-v1 (2026-06-12) reescribio las notas con codificacion doble: 'dist≈3.33 km' quedo como
'distâ‰ˆ3.33 km'. El regex del loader no lo reconocia y la alerta perdia su posicion."""
import csv
import os

from pipeline.mirova_csv_loader import parse_ocr_distance

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OCR = os.path.join(ROOT, "data", "mirova_reference", "mirova_v1_snapshot", "registro_vrp_ocr.csv")


def test_mojibake_verbatim():
    assert parse_ocr_distance("Estrella en Y=283 (dentro lÃ\xadmite Y=257, distâ‰ˆ3.33 km)") == 3.33


def test_formatos_previos_siguen():
    assert parse_ocr_distance("Grupo píxeles rojos (área=50 px², dist≈12.94 km)") == 12.94
    assert parse_ocr_distance("validado -> 2.5 km") == 2.5
    assert parse_ocr_distance("sin distancia") is None


def test_alertas_ocr_reales_con_distancia():
    """Control de instrumento: sobre el CSV real, la fraccion sin distancia baja de 68 % a menos de 5 %."""
    with open(OCR, encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["Tipo_Registro"] == "ALERTA_TERMICA_OCR"]
    assert len(rows) > 500
    sin = [r for r in rows if parse_ocr_distance(r.get("Nota_Validacion", "")) is None]
    assert len(sin) / len(rows) < 0.05, f"{len(sin)} de {len(rows)} sin distancia"
