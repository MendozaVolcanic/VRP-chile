# -*- coding: utf-8 -*-
"""Tarea 0.2 del loop (S150/S151): que es una "alerta protegida" en el criterio de victoria.

POR QUE: el criterio de Nicolas (2026-10-13) protege toda alerta que MIROVA clasifique de "Bajo" para
arriba. La columna `Clasificacion Mirova` del CSV NO la escribe MIROVA: la calcula el scraper desde el
VRP (Mirova-v1 `volcanes.py:63`), y cambio de escala en el tiempo (17 "Bajo" de menos de 1 MW en
enero; S139 H110). El unico campo que si viene de MIROVA es `Nivel_Anomalia_MIROVA` (banner de la
imagen, desde V30). Estos tests fijan la definicion operativa (VRP de la pasada >= 1 MW, recalculado,
nunca leido de la columna) y la comprueban contra el banner de MIROVA como control, llamando a la
funcion real (verificador de #780: la version anterior de los controles no la llamaba).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.clase_mirova import (UMBRAL_PROTEGIDA_MW, alerta_protegida,  # noqa: E402
                                  clase_por_vrp, filas_con_banner,
                                  pasadas_protegidas)


def test_umbral_es_1_mw():
    assert UMBRAL_PROTEGIDA_MW == 1.0


def test_la_clase_sale_del_vrp_no_de_la_columna():
    # Caso real de enero: Villarrica VIIRS375 2026-01-14 05:48, 0,07 MW, columna "Bajo".
    fila = {"tipo": "ALERTA_TERMICA", "vrp_mw": 0.07, "clasificacion": "Bajo"}
    assert clase_por_vrp(0.07) == "Muy Bajo"
    assert not alerta_protegida(fila)
    # Y al reves: una columna "Muy Bajo" no protege de la proteccion a 1,5 MW.
    assert alerta_protegida({"tipo": "ALERTA_TERMICA", "vrp_mw": 1.5, "clasificacion": "Muy Bajo"})


def test_borde_y_tipos():
    assert alerta_protegida({"tipo": "ALERTA_TERMICA", "vrp_mw": 1.0})
    assert alerta_protegida({"tipo": "ALERTA_TERMICA_OCR", "vrp_mw": 5.18})
    assert not alerta_protegida({"tipo": "ALERTA_TERMICA", "vrp_mw": 0.99})
    assert not alerta_protegida({"tipo": "FALSO_POSITIVO", "vrp_mw": 30.0})
    assert not alerta_protegida({"tipo": "RUTINA", "vrp_mw": 0.0})
    assert not alerta_protegida({"tipo": "ALERTA_TERMICA", "vrp_mw": None})


def test_lectura_b_incluye_falso_positivo_y_nunca_rutina():
    assert alerta_protegida({"tipo": "FALSO_POSITIVO", "vrp_mw": 30.0}, lectura="B")
    assert alerta_protegida({"tipo": "FALSO_POSITIVO_OCR", "vrp_mw": 2.27}, lectura="B")
    assert not alerta_protegida({"tipo": "FALSO_POSITIVO", "vrp_mw": 0.5}, lectura="B")
    assert not alerta_protegida({"tipo": "RUTINA", "vrp_mw": 0.0}, lectura="B")


def _como_alerta(f):
    # El banner trae tambien filas FALSO_POSITIVO_OCR; para comparar el CORTE de intensidad se evalua
    # cada pasada con banner como si fuera alerta.
    return {"tipo": "ALERTA_TERMICA_OCR", "vrp_mw": f["vrp_mw"]}


def _separa(umbral):
    filas = filas_con_banner()
    low = [f for f in filas if f["banner"] == "LOW"]
    very_low = [f for f in filas if f["banner"] == "VERY_LOW"]
    assert len(low) >= 10 and len(very_low) >= 50, (len(low), len(very_low))
    return (all(alerta_protegida(_como_alerta(f), umbral) for f in low)
            and not any(alerta_protegida(_como_alerta(f), umbral) for f in very_low))


def test_control_la_funcion_coincide_con_el_banner():
    assert _separa(UMBRAL_PROTEGIDA_MW)


def test_control_negativo_umbral_equivocado_falla():
    assert not _separa(0.5)
    assert not _separa(1.01)


def test_conteo_por_pasada_junta_consolidado_y_ocr():
    fila = {"volcano": "Lascar", "sensor_bucket": "MODIS", "fecha_utc": "2026-03-04 07:15:00",
            "tipo": "ALERTA_TERMICA", "vrp_mw": 3.0}
    gemela = {**fila, "tipo": "ALERTA_TERMICA_OCR", "fecha_utc": "2026-03-04 07:15:30"}
    assert len(pasadas_protegidas([fila, gemela])) == 1
