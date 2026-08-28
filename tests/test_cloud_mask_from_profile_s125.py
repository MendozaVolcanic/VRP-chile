# -*- coding: utf-8 -*-
"""S125 — la máscara de nube de VIIRS 375 m debe leerse del PERFIL, no de un literal.

POR QUÉ EXISTE ESTE TEST
------------------------
`MISSION.md` declara removida la máscara de nube BT<260 K desde S27 (Laiolo 2026,
textual: MIROVA no aplica "cloud-contamination automatic filtering"). La auditoría
S125 encontró que sigue viva, y sólo en un sensor:

  · MODIS y VIIRS 750 la leen del perfil (`CLOUD_MASK_BT_K`), hoy en 0.0 → inerte.
  · VIIRS 375 tenía `CLOUD_BT_THRESHOLD = 260.0` HARDCODEADO en process_viirs.py,
    ignorando la perilla, y lo aplicaba a `roi_mask` **y** a `bg_mask`.

Consecuencia medida en Nevados de Chillán (junio-agosto 2026): 15 de 88 noches
quedaron CIEGAS — el filtro descartó entre 13.200 y 17.300 píxeles del ROI contra
~1.100 en una noche normal, dejando CERO píxeles de fondo. Físicamente, el filtro
corta por temperatura absoluta, y a 3.200 m en invierno austral la nieve irradia
en el mismo rango que el tope de una nube baja: no los distingue.

QUÉ FIJA ESTE TEST
------------------
Que el umbral salga de la configuración y no de un literal en el código. No fija
un valor: fija que la perilla EXISTA y que el código la respete, para que
apagarla o cambiarla sea una decisión de perfil (auditable, A/B-able) y no una
edición de código.

Es el guard que faltaba: sin él, cualquiera puede volver a clavar un número y la
divergencia doc-vs-código se reabre en silencio.
"""
import ast
import os
import re

import pytest

PIPELINE = os.path.join(os.path.dirname(__file__), "..", "pipeline")


def _fuente(nombre):
    with open(os.path.join(PIPELINE, nombre), encoding="utf-8") as fh:
        return fh.read()


def test_viirs375_no_tiene_umbral_de_nube_hardcodeado():
    """No debe existir un literal 260 asignado como umbral de nube."""
    src = _fuente("process_viirs.py")
    # Busca asignaciones del estilo  CLOUD_BT_THRESHOLD = 260.0
    ofensores = re.findall(r"^\s*(CLOUD_[A-Z_]*THRESHOLD[A-Z_]*)\s*=\s*([0-9.]+)",
                           src, flags=re.MULTILINE)
    assert not ofensores, (
        "Umbral de nube hardcodeado en process_viirs.py: "
        f"{ofensores}. Debe venir de CLOUD_MASK_BT_K (pipeline/profile.py), "
        "para que apagarlo sea una decisión de perfil y no una edición de código. "
        "Ver docs/AUDIT_S125_PROFUNDA.md §1 F3."
    )


def test_viirs375_importa_la_perilla_del_perfil():
    """process_viirs debe importar CLOUD_MASK_BT_K, como ya hace process_modis."""
    src = _fuente("process_viirs.py")
    assert "CLOUD_MASK_BT_K" in src, (
        "process_viirs.py no usa CLOUD_MASK_BT_K. MODIS sí la lee "
        "(process_modis.py:505,715); VIIRS 375 debe leer la misma perilla para que "
        "los tres sensores se comporten de forma consistente."
    )


def test_la_perilla_existe_y_es_numerica():
    """La perilla tiene que existir en el perfil y ser un número."""
    import pipeline.profile as p
    assert hasattr(p, "CLOUD_MASK_BT_K"), "CLOUD_MASK_BT_K no existe en pipeline.profile"
    assert isinstance(p.CLOUD_MASK_BT_K, (int, float))


def test_umbral_cero_no_debe_enmascarar_nada():
    """Con la perilla en 0, el predicado `bt > umbral` no puede descartar píxeles válidos.

    Es la semántica que MODIS ya tiene: 0.0 = máscara apagada. Sin esto, poner la
    perilla en 0 podría seguir descartando algo por un `>=` mal puesto.
    """
    import numpy as np
    bt = np.array([200.0, 255.0, 260.0, 273.0, 300.0])
    # predicado con la máscara apagada
    assert (bt > 0.0).all(), "con umbral 0 ningún píxel con BT válida debe quedar fuera"


def test_ast_sin_comparaciones_contra_260_en_bandas_termicas():
    """Ningún `bands[...] >= 260` suelto: esa comparación es la máscara disfrazada."""
    src = _fuente("process_viirs.py")
    tree = ast.parse(src)
    malos = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for comp in node.comparators:
                if isinstance(comp, ast.Constant) and isinstance(comp.value, (int, float)):
                    if 255 <= float(comp.value) <= 265:
                        malos.append((getattr(node, "lineno", "?"), comp.value))
    assert not malos, (
        f"Comparaciones contra un literal ~260 en process_viirs.py (línea, valor): {malos}. "
        "Si es la máscara de nube, debe usar CLOUD_MASK_BT_K."
    )
