# -*- coding: utf-8 -*-
"""Tarea 0.2 del loop (S150/S151): que es una "alerta protegida" en el criterio de victoria.

POR QUE: el criterio de Nicolas (2026-10-13) protege toda alerta que MIROVA clasifique de "Bajo" para
arriba. La columna `Clasificacion Mirova` del CSV NO la escribe MIROVA: la calcula el scraper desde el
VRP (Mirova-v1 `volcanes.py:63`), y cambio de escala en el tiempo (17 "Bajo" de menos de 1 MW en
enero; S139 H110). El unico campo que si viene de MIROVA es `Nivel_Anomalia_MIROVA` (banner de la
imagen, desde V30). Estos tests fijan la definicion operativa (VRP de la pasada >= 1 MW, recalculado,
nunca leido de la columna) y la comprueban contra el banner de MIROVA como control.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.clase_mirova import (UMBRAL_PROTEGIDA_MW, alerta_protegida,  # noqa: E402
                                  clase_por_vrp, filas_con_banner)


def test_umbral_es_1_mw():
    assert UMBRAL_PROTEGIDA_MW == 1.0


def test_la_clase_sale_del_vrp_no_de_la_columna():
    # Caso real de enero: Villarrica VIIRS375 2026-01-14 05:48, 0,07 MW, columna "Bajo".
    fila = {"tipo": "ALERTA_TERMICA", "vrp_mw": 0.07, "clasificacion": "Bajo"}
    assert clase_por_vrp(0.07) == "Muy Bajo"
    assert not alerta_protegida(fila)


def test_borde_y_tipos():
    assert alerta_protegida({"tipo": "ALERTA_TERMICA", "vrp_mw": 1.0})
    assert alerta_protegida({"tipo": "ALERTA_TERMICA_OCR", "vrp_mw": 5.18})
    assert not alerta_protegida({"tipo": "ALERTA_TERMICA", "vrp_mw": 0.99})
    assert not alerta_protegida({"tipo": "FALSO_POSITIVO", "vrp_mw": 30.0})
    assert not alerta_protegida({"tipo": "RUTINA", "vrp_mw": 0.0})
    assert not alerta_protegida({"tipo": "ALERTA_TERMICA", "vrp_mw": None})


def test_control_coincide_con_el_banner_de_mirova():
    # Control: sobre las pasadas con banner, la clase recalculada separa VERY_LOW de LOW sin error.
    filas = filas_con_banner()
    low = [f for f in filas if f["banner"] == "LOW"]
    very_low = [f for f in filas if f["banner"] == "VERY_LOW"]
    assert len(low) >= 10 and len(very_low) >= 50, (len(low), len(very_low))
    assert all(f["vrp_mw"] >= UMBRAL_PROTEGIDA_MW for f in low)
    assert all(f["vrp_mw"] < UMBRAL_PROTEGIDA_MW for f in very_low)


def test_control_negativo_un_umbral_equivocado_falla_contra_el_banner():
    # El control puede fallar: con un corte de 0,5 MW, parte del VERY_LOW quedaria "protegido".
    very_low = [f for f in filas_con_banner() if f["banner"] == "VERY_LOW"]
    assert any(f["vrp_mw"] >= 0.5 for f in very_low)
