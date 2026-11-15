# -*- coding: utf-8 -*-
"""S186 (b.3): la regla de posición del record de la vía es «radiante». Decisión de Nicolás, 2026-11-15: «Formalizar
radiante».

POR QUÉ. En una misma pasada puede haber un píxel débil en el cráter y una fuente más radiante lejos (otra boca, un
flujo, un incendio). El record tiene que ponerse en un solo lugar, y de ese lugar sale la clase (cumbre o lejano) que
decide si el tablero publica. Las tres reglas que se midieron:
  - radiante: centroide del cúmulo 8-conexo que contiene a la alertada más radiante (la que corre);
  - pico: el píxel más radiante solo (da la misma clase que radiante en 3.656 de 3.656 pasadas);
  - cercano: el alertado más cercano al cráter (rescata 9 pasadas de 1.664 en que MIROVA alertó en el cráter, pero
    publica 114 pasadas más en que MIROVA ubicó el calor lejos).
Acuerdo de clase con MIROVA en 2.037 pasadas (2026-03-01 a 2026-11-15, 11 Tier A, tabla sola): radiante 98,7 %,
cercano 93,6 %. Evidencia: D:\\vrp-trabajo\\temporales\\s185_posicion_medida\\INFORME.md y su verificador
(s185_posicion_medida_verif\\NOTAS.txt).

La prueba que ya existía (test_mirova_v750_codigo_s162.py::test_record_suma_todos_los_alertados_y_sin_modo_de_un_pixel)
pone el foco fuerte en el cráter, donde las tres reglas coinciden: no protege la regla. Esta pone el débil en el
cráter y el fuerte lejos, el único caso en que radiante y cercano se separan. Cambiar la regla exige cambiar esta prueba
y, antes, una decisión de Nicolás.

La función es una sola para los tres sensores: process_modis, process_viirs y process_viirs_mod llaman a
calcular_vrp_granulo, que llama a procesar_grilla, que llama a _cumulo_del_mas_radiante.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from pipeline import mirova_v750_codigo as MV  # noqa: E402

CRATER = (33, 33)
LEJOS = (33, 46)          # 13 celdas de 750 m: 9,75 km al este, fuera del radio interior de 5 km
INNER_KM = 5.0


def _escena_debil_en_crater_fuerte_lejos():
    rng = np.random.default_rng(186)
    T15 = 265.0 + rng.normal(0, 0.3, (67, 67))
    T13 = T15 - 3 + rng.normal(0, 0.3, (67, 67))
    T13[CRATER] += 15     # foco débil en el cráter
    T13[LEJOS] += 30      # foco más radiante, lejos
    return MV.temperatura_a_radiancia(T13, MV.LAMBDA_M13), MV.temperatura_a_radiancia(T15, MV.LAMBDA_M15)


def _record(box):
    m13, m15 = _escena_debil_en_crater_fuerte_lejos()
    g = MV.grilla_del_volcan("Lascar")
    rec = MV.procesar_grilla(m13, m15, g, box, 0, 40.0, (33.0, 33.0), INNER_KM, "VIIRS_NOAA20_750")
    mask = MV.detectar_mirova(m13, m15, box, 0, 40.0)
    return rec, mask, m13


def test_control_los_dos_focos_alertan():
    """Sin esto la prueba de abajo no distingue nada: si el foco del cráter no alertara, cualquier regla daría lejos."""
    _, mask, m13 = _record(MV.caja_roi("sens"))
    assert mask[CRATER] and mask[LEJOS]
    assert m13[LEJOS] > m13[CRATER]


def test_posicion_es_la_del_cumulo_mas_radiante_aunque_haya_alerta_en_el_crater():
    rec, mask, _ = _record(MV.caja_roi("sens"))
    pc = rec["primary_cluster"]
    # radiante: el record va al foco lejano (con cercano iría al cráter, a 0 km, y sería summit)
    assert rec["distance_class"] == "far"
    assert pc["centroid_dist_km"] > INNER_KM
    assert abs(pc["centroid_dist_km"] - 13 * 0.75) < 0.5
    assert pc["n_pixels"] == 1
    # el VRP no depende de la regla de posición: es la unión de todos los alertados (D32)
    assert rec["vrp_mw"] == pc["vrp_mw"]
    assert rec["n_anomalous_pixels"] == int(mask.sum()) >= 2


def test_cumulo_del_mas_radiante_elige_el_de_mayor_radiancia_no_el_mas_cercano():
    """La función sola, sin detector: dos cúmulos, el del cráter más grande pero menos radiante."""
    mascara = np.zeros((67, 67), bool)
    m13 = np.ones((67, 67))
    for c in [(33, 33), (33, 34), (34, 33)]:   # cúmulo del cráter: 3 píxeles tibios
        mascara[c] = True
        m13[c] = 2.0
    mascara[LEJOS] = True                       # cúmulo lejano: 1 píxel caliente
    m13[LEJOS] = 5.0
    assert MV._cumulo_del_mas_radiante(mascara, m13) == [LEJOS]
