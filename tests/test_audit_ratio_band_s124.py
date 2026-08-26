# -*- coding: utf-8 -*-
"""La auditoría debe juzgar la MEDIANA con la banda estricta, no con la floja.

POR QUÉ (S124): `~memory/reference_paridad_mirova_umbrales.md` define DOS bandas
distintas y por una buena razón física:

  - **Una detección individual**: [0,5 – 2,0]. MIROVA declara ±30 % de error en
    el método MIR; si ambos instrumentos tienen ese error, el ratio de una noche
    puntual fluctúa naturalmente entre 0,54 y 1,85.
  - **La mediana de un volcán**: [0,7 – 1,4]. Textual: *"más estricto que
    individual porque mide tendencia central, no outliers puntuales. Mediana
    2.0 = sesgo sistemático, no ruido"*.

`auto_audit_weekly.py` aplicaba la banda floja a la mediana — 4× de ancho donde
el criterio propio pide 2×. Con eso, dos selecciones de cluster que difieren 17 %
(0,71 vs 0,83 global) "pasaban" las dos, y cuatro volcanes sub-reportando 35-50 %
quedaban invisibles.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.auto_audit_weekly import (RATIO_BAND_INDIVIDUAL,  # noqa: E402
                                       RATIO_BAND_MEDIAN,
                                       evaluar_ratio_mediano)


def test_las_dos_bandas_existen_y_la_de_mediana_es_mas_estricta():
    assert RATIO_BAND_MEDIAN == (0.7, 1.4)
    assert RATIO_BAND_INDIVIDUAL == (0.5, 2.0)
    lo_m, hi_m = RATIO_BAND_MEDIAN
    lo_i, hi_i = RATIO_BAND_INDIVIDUAL
    assert lo_i < lo_m and hi_m < hi_i, "la de mediana debe estar contenida"


@pytest.mark.parametrize("ratio,esperado", [
    (1.00, None),      # paridad
    (0.70, None),      # borde inferior inclusive
    (1.40, None),      # borde superior inclusive
    (0.62, "sub"),     # Lascar medido S124 — antes pasaba con la banda floja
    (0.61, "sub"),     # Isluga medido S124
    (0.36, "sub"),     # Llaima medido S124
    (1.57, "sobre"),   # sobre-estimación
    (4.86, "sobre"),   # Villarrica congelada pre-flip
])
def test_veredicto_por_ratio(ratio, esperado):
    v = evaluar_ratio_mediano("Lascar", ratio, n_noches=50)
    if esperado is None:
        assert v is None, f"{ratio} debería estar en banda"
    else:
        assert v is not None and esperado in v.lower()


def test_los_casos_que_la_banda_floja_dejaba_pasar():
    """El corazón del bug: 0,62 y 0,61 pasaban [0,5-2,0] y no debían."""
    for ratio in (0.62, 0.61):
        assert RATIO_BAND_INDIVIDUAL[0] <= ratio <= RATIO_BAND_INDIVIDUAL[1]
        assert evaluar_ratio_mediano("Lascar", ratio, n_noches=50) is not None


def test_n_insuficiente_no_flaggea():
    """Llaima tiene n=2 en la ventana S124: no es concluyente."""
    assert evaluar_ratio_mediano("Llaima", 0.36, n_noches=2) is None


def test_excepcion_fisica_documentada_no_flaggea_por_debajo():
    """Lastarria sub-banda es el cat-b Lazufre conocido (AUDIT_S119 §2.3)."""
    assert evaluar_ratio_mediano("Lastarria", 0.47, n_noches=95) is None
    # pero sobre-estimar SÍ sería nuevo
    assert evaluar_ratio_mediano("Lastarria", 2.5, n_noches=95) is not None


def test_el_flag_referencia_el_hallazgo_para_no_leerse_como_regresion():
    v = evaluar_ratio_mediano("Lascar", 0.62, n_noches=50)
    assert "S124" in v, "el flag debe apuntar al hallazgo documentado"
