# -*- coding: utf-8 -*-
"""Fase 0 tarea 2 (S139/S140): la referencia de paridad conserva negativos y recupera lo perdido.

POR QUE: sin RUTINA ni FALSO_POSITIVO no se puede medir sobre-publicacion, que es la brecha real
(S139). Y el consolidado remoto de Mirova-v1 perdio 17 ALERTA_TERMICA de enero a abril que el
respaldo del 2026-04-08 conserva.

Nota de instrumento (S140): la version del plan probaba la clave (Lascar, MODIS, 2026-03-04 07:15)
sin fijar la fuente, y esa pasada ya existe por el canal OCR; el test habria pasado sin unir el
respaldo. Aca se exige la fila CONS y se comprueba que sin respaldo no esta.
"""
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.referencia_mirova_unificada import (clave,  # noqa: E402
                                                 cargar_referencia_unificada)

LASCAR_CONS = ("Lascar", "MODIS", "2026-03-04 07:15", "CONS")


def test_recupera_las_alertas_perdidas():
    ref = cargar_referencia_unificada()
    por_clave = {clave(a): a for a in ref}
    assert LASCAR_CONS in por_clave
    fila = por_clave[LASCAR_CONS]
    assert fila["tipo"] == "ALERTA_TERMICA"
    assert fila["origen"] == "respaldo_20260408"


def test_control_sin_respaldo_la_alerta_cons_no_esta():
    sin = {clave(a) for a in cargar_referencia_unificada(respaldo_path=None)}
    assert LASCAR_CONS not in sin
    # la misma pasada si existe por OCR: por eso la clave lleva la fuente
    assert ("Lascar", "MODIS", "2026-03-04 07:15", "OCR") in sin


def test_sin_duplicados():
    ref = cargar_referencia_unificada()
    claves = [clave(a) for a in ref]
    assert len(claves) == len(set(claves))


def test_conserva_rutina_y_falso_positivo():
    c = Counter(a["tipo"] for a in cargar_referencia_unificada())
    assert c["RUTINA"] > 10000 and c["FALSO_POSITIVO"] > 100 and c["ALERTA_TERMICA"] > 1000, c
    assert c["ALERTA_TERMICA_OCR"] > 500 and c["FALSO_POSITIVO_OCR"] > 50, c


def test_la_principal_gana_y_el_respaldo_solo_agrega():
    principal = {clave(a): a for a in cargar_referencia_unificada(respaldo_path=None)}
    ref = {clave(a): a for a in cargar_referencia_unificada()}
    assert set(principal) <= set(ref)
    assert all(ref[k] is not None and ref[k]["origen"] == "principal" for k in principal)
    extra = Counter(a["tipo"] for k, a in ref.items() if k not in principal)
    # 17 medidas S140 contra el snapshot. Rango y no igualdad: si Mirova-v1 restaura filas
    # (issue #19) y el auto-audit refresca el snapshot, el numero baja sin que haya defecto.
    assert 1 <= extra["ALERTA_TERMICA"] <= 17, extra


def test_distancia_ocr_recuperada():
    ocr = [a for a in cargar_referencia_unificada() if a["tipo"] == "ALERTA_TERMICA_OCR"]
    sin = [a for a in ocr if a["dist_km"] is None]
    assert len(sin) / len(ocr) < 0.05, f"{len(sin)} de {len(ocr)}"
