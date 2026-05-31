"""S87 Bloque 2 — TDD para pipeline/mirova_csv_loader.py.

Loader canónico CONS∪OCR del ground truth MIROVA. Resuelve los bugs del
loader local detectados por la auditoría S86 (Subagente F):
- F-B1: OCR (344 ALERTAs únicas) no consumido → subconteo MIROVA ~45%.
- F-B2: OCR Distancia_km=0; distancia real en Nota_Validacion (dist≈X km).
- F-B4: variante huérfana 'Peteroa' → 'PlanchonPeteroa'.
- A14: variantes de nombre por volcán.

Cada test captura una intención de comportamiento del loader.
"""
from __future__ import annotations

import textwrap

from pipeline.mirova_csv_loader import (
    normalize_volcano_name,
    normalize_sensor,
    parse_ocr_distance,
    load_mirova_alertas,
)


# === normalize_volcano_name (A14 + F-B4) ===

def test_normalize_peteroa_huerfano_a_planchonpeteroa():
    """F-B4: variante histórica 'Peteroa' (pre-2026-01-16) → PlanchonPeteroa."""
    assert normalize_volcano_name("Peteroa") == "PlanchonPeteroa"


def test_normalize_planchonpeteroa_sin_guion():
    assert normalize_volcano_name("PlanchonPeteroa") == "PlanchonPeteroa"


def test_normalize_puyehue_con_guion_y_espacio():
    """CONS usa 'Puyehue-Cordon Caulle' (guión + espacio)."""
    assert normalize_volcano_name("Puyehue-Cordon Caulle") == "PuyehueCordonCaulle"


def test_normalize_nevados_con_espacios():
    assert normalize_volcano_name("Nevados de Chillan") == "NevadosDeChillan"


def test_normalize_nombre_no_tier_a_devuelve_none():
    """Un volcán fuera de los 11 Tier A no se mapea (devuelve None)."""
    assert normalize_volcano_name("Calbuco") is None


# === normalize_sensor (mapeo CSV → bucket, regla A48) ===

def test_normalize_sensor_modis():
    assert normalize_sensor("MODIS") == "MODIS"


def test_normalize_sensor_viirs_sin_sufijo_es_750():
    """CSV 'VIIRS' (sin sufijo) = M-band 750m (convención MIROVA canónica).

    S93 fix: el test original (S86) asumía 'VIIRS' = I-band 375m, contradiciendo
    el frontend (mirovaSensorBucket: 'VIIRS' → VIIRS750) y la realidad del CSV
    (etiquetas: 'MODIS', 'VIIRS375' explícito I-band, 'VIIRS' = M-band 750m).
    El bug mandaba las 158 alertas VIIRS750 Tier A al cajón VIIRS375 (→ "MIROVA
    no usa VIIRS750", falso). Confirmado por Nicolás (autor scraper Mirova-v1)."""
    assert normalize_sensor("VIIRS") == "VIIRS750"


def test_normalize_sensor_viirs375_explicito():
    assert normalize_sensor("VIIRS375") == "VIIRS375"


def test_normalize_sensor_viirs750_es_mband():
    assert normalize_sensor("VIIRS750") == "VIIRS750"


# === parse_ocr_distance (F-B2) ===

def test_parse_ocr_distance_formato_estandar():
    """Formato real OCR: 'dist≈12.94 km' en texto libre."""
    nota = "Grupo píxeles rojos Y=269 (área=50 px², dist≈12.94 km)"
    assert parse_ocr_distance(nota) == 12.94


def test_parse_ocr_distance_valor_cero():
    nota = "Estrella en Y=238 (dentro límite, dist≈0.00 km)"
    assert parse_ocr_distance(nota) == 0.0


def test_parse_ocr_distance_sin_distancia_devuelve_none():
    assert parse_ocr_distance("nota sin distancia") is None


def test_parse_ocr_distance_nota_vacia_devuelve_none():
    assert parse_ocr_distance("") is None


# === load_mirova_alertas (F-B1 CONS∪OCR + dedup) ===

def _write_csvs(tmp_path):
    """Crea CSVs sintéticos CONS + OCR para tests del loader."""
    cons = tmp_path / "cons.csv"
    ocr = tmp_path / "ocr.csv"
    cons.write_text(textwrap.dedent("""\
        timestamp,Fecha_Satelite_UTC,Fecha_Captura_Chile,Volcan,Sensor,VRP_MW,Distancia_km,Tipo_Registro,Clasificacion Mirova,Nota_Validacion
        1000,2026-02-01 05:00:00,2026-02-01 01:00:00,Lascar,MODIS,2.5,1.2,ALERTA_TERMICA,Bajo,
        1001,2026-02-01 06:00:00,2026-02-01 02:00:00,Llaima,MODIS,0.0,0.0,RUTINA,NULO,
        1002,2026-02-02 05:00:00,2026-02-02 01:00:00,Peteroa,VIIRS,1.1,0.6,ALERTA_TERMICA,Bajo,
        """), encoding="utf-8")
    ocr.write_text(textwrap.dedent("""\
        timestamp,Fecha_Satelite_UTC,Fecha_Captura_Chile,Volcan,Sensor,VRP_MW,Distancia_km,Tipo_Registro,Clasificacion Mirova,Nota_Validacion
        2000,2026-02-03 06:00:00,2026-02-03 02:00:00,Puyehue-Cordon Caulle,VIIRS375,0.32,0.0,ALERTA_TERMICA_OCR,Bajo,"Grupo rojos (dist≈12.94 km)"
        1000,2026-02-01 05:00:00,2026-02-01 01:00:00,Lascar,MODIS,2.5,0.0,ALERTA_TERMICA_OCR,Bajo,"Estrella (dist≈1.30 km)"
        """), encoding="utf-8")
    return cons, ocr


def test_load_descarta_rutina(tmp_path):
    """RUTINA no es ALERTA → no entra al universo."""
    cons, ocr = _write_csvs(tmp_path)
    rows = load_mirova_alertas(cons_path=cons, ocr_path=ocr)
    assert all(r["tipo"] != "RUTINA" for r in rows)
    assert not any(r["volcano"] == "Llaima" for r in rows)


def test_load_incluye_ocr_unico(tmp_path):
    """F-B1: una ALERTA solo-OCR (PCC) debe estar presente."""
    cons, ocr = _write_csvs(tmp_path)
    rows = load_mirova_alertas(cons_path=cons, ocr_path=ocr)
    pcc = [r for r in rows if r["volcano"] == "PuyehueCordonCaulle"]
    assert len(pcc) == 1
    assert pcc[0]["source"] == "OCR"


def test_load_distancia_ocr_parseada_de_nota(tmp_path):
    """F-B2: la distancia OCR sale de Nota_Validacion, no de Distancia_km=0."""
    cons, ocr = _write_csvs(tmp_path)
    rows = load_mirova_alertas(cons_path=cons, ocr_path=ocr)
    pcc = next(r for r in rows if r["volcano"] == "PuyehueCordonCaulle")
    assert pcc["dist_km"] == 12.94


def test_load_normaliza_peteroa(tmp_path):
    """F-B4: 'Peteroa' del CONS se mapea a PlanchonPeteroa."""
    cons, ocr = _write_csvs(tmp_path)
    rows = load_mirova_alertas(cons_path=cons, ocr_path=ocr)
    assert any(r["volcano"] == "PlanchonPeteroa" for r in rows)


def test_load_dedup_cons_ocr_mismo_pasada(tmp_path):
    """Lascar MODIS 2026-02-01 está en CONS y OCR (mismo timestamp,vol,sensor).
    Debe quedar 1 sola fila (dedup), priorizando CONS (canal oficial)."""
    cons, ocr = _write_csvs(tmp_path)
    rows = load_mirova_alertas(cons_path=cons, ocr_path=ocr)
    lascar = [r for r in rows if r["volcano"] == "Lascar"]
    assert len(lascar) == 1
    assert lascar[0]["source"] == "CONS"


def test_load_filtra_por_volcano(tmp_path):
    """El filtro volcano= devuelve solo ese volcán (normalizado)."""
    cons, ocr = _write_csvs(tmp_path)
    rows = load_mirova_alertas(cons_path=cons, ocr_path=ocr, volcano="PlanchonPeteroa")
    assert len(rows) == 1
    assert rows[0]["volcano"] == "PlanchonPeteroa"


def test_load_sensor_bucket_normalizado(tmp_path):
    """Cada fila trae sensor_bucket normalizado."""
    cons, ocr = _write_csvs(tmp_path)
    rows = load_mirova_alertas(cons_path=cons, ocr_path=ocr)
    pcc = next(r for r in rows if r["volcano"] == "PuyehueCordonCaulle")
    assert pcc["sensor_bucket"] == "VIIRS375"


def test_load_ocr_sin_distancia_es_none(tmp_path):
    """F-B2 completo: OCR sin patrón de distancia en la nota → dist_km None.

    Las filas OCR traen Distancia_km=0 siempre; ese 0 es 'no informado', no
    'distancia cero'. Si la nota no parsea, dist_km debe quedar None — NO
    heredar el 0.0 de Distancia_km, que daría matches espurios al vent.
    """
    cons = tmp_path / "cons.csv"
    ocr = tmp_path / "ocr.csv"
    cons.write_text(
        "timestamp,Fecha_Satelite_UTC,Fecha_Captura_Chile,Volcan,Sensor,VRP_MW,"
        "Distancia_km,Tipo_Registro,Clasificacion Mirova,Nota_Validacion\n",
        encoding="utf-8",
    )
    ocr.write_text(
        "timestamp,Fecha_Satelite_UTC,Fecha_Captura_Chile,Volcan,Sensor,VRP_MW,"
        "Distancia_km,Tipo_Registro,Clasificacion Mirova,Nota_Validacion\n"
        '3000,2026-02-03 06:00:00,2026-02-03 02:00:00,Lascar,VIIRS375,0.4,0.0,'
        'ALERTA_TERMICA_OCR,Bajo,"Pixel rojo sin distancia reportada"\n',
        encoding="utf-8",
    )
    rows = load_mirova_alertas(cons_path=cons, ocr_path=ocr)
    assert len(rows) == 1
    assert rows[0]["dist_km"] is None


def test_load_cons_usa_distancia_km(tmp_path):
    """CONS sí usa Distancia_km como fuente de distancia (no la nota)."""
    cons, ocr = _write_csvs(tmp_path)
    rows = load_mirova_alertas(cons_path=cons, ocr_path=ocr)
    lascar = next(r for r in rows if r["volcano"] == "Lascar")  # CONS gana dedup
    assert lascar["dist_km"] == 1.2
