# -*- coding: utf-8 -*-
"""S142 D22: la compuerta `bt > t_bg + bt_sanity_k` dentro del dNTI contextual y de los Tests 2 y 3.

EL FENÓMENO. En un cono nevado, de noche, el píxel con lava sub-píxel puede estar más frío que la
mediana del anillo regional (lleno de valle tibio) y aun así destacar en el índice espectral
contra sus 8 vecinos. La fórmula de los Tests 2 y 3 de Coppola 2016a (p. 7) no tiene condición de
temperatura; la compuerta la heredamos del camino del NTI absoluto (docs/MIROVA_DIVERGENCES.md D22).

QUÉ FIJAN. (1) El default de los tres helpers es la compuerta de hoy. (2) `apply_bt_gate=False`
deja entrar exactamente al píxel que la compuerta rechazaba. (3) Sin compuerta sigue exigiendo BT
finita. (4) El segundo pase no tiene compuerta (corrección S138). (5) Sólo VIIRS 375 la apaga.
"""
import inspect
import json
import re
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from arnes_sintetico_s142 import (CENTRO_V375, N_V375, correr_en_subproceso,  # noqa: E402
                                  entradas_helpers, salidas_helpers)
from pipeline.detection_context import (contextual_dnti_hot_mask,  # noqa: E402
                                        dual_roi_contextual_dnti_hot_mask,
                                        first_pass_tests_2_and_3, second_pass_adjacent)

GOLDEN = json.loads((ROOT / "tests" / "golden_s142" / "apagado.json").read_text(encoding="utf-8"))
CRATER = CENTRO_V375 * N_V375 + CENTRO_V375
VECINO = CRATER + 1


def _src(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def _tokens(src, token):
    """Cuenta el token con frontera de palabra a los DOS lados (A92): un guard por subcadena da
    falso verde cuando el nombre viejo queda dentro del nuevo."""
    return len(re.findall(r"(?<![A-Za-z0-9_])" + re.escape(token) + r"(?![A-Za-z0-9_])", src))


def test_default_y_explicito_true_son_la_compuerta_de_hoy():
    assert salidas_helpers() == GOLDEN["helpers"]
    assert salidas_helpers(apply_bt_gate=True) == GOLDEN["helpers"]


def test_sin_compuerta_el_primer_pase_toma_al_crater_y_al_vecino_tibio():
    hoy = GOLDEN["helpers"]
    sin = salidas_helpers(apply_bt_gate=False)
    assert CRATER not in hoy["first_pass"] and VECINO not in hoy["first_pass"]
    assert CRATER in sin["first_pass"] and VECINO in sin["first_pass"]
    # sólo cambia el conjunto de activos: mu y sigma salen del pool de fondo, que no depende de BT
    for k in ("mu_dnti", "sd_dnti", "mu_deti", "sd_deti", "n_bg_used"):
        assert sin["first_pass_diag"][k] == hoy["first_pass_diag"][k], k
    # y no aparece ningún píxel que no estuviera ya en la escena con la compuerta bajada a -inf
    e = entradas_helpers()
    ref, _ = first_pass_tests_2_and_3(nti=e["nti"], nti_app=e["nti_app"], bt=e["bt"],
                                      roi_mask=e["roi"], dist_km=e["dist"], t_bg=e["t_bg"],
                                      bt_sanity_k=-np.inf, inner_km=5.0, c1_dnti_scene=0.010,
                                      c1_deti_scene=0.010, c2_dnti_scene=10, c2_deti_scene=10)
    assert sin["first_pass"] == np.flatnonzero(ref).tolist()


def _escena_minima():
    """7x7: NTI plano a -0,90 y el centro a -0,85 (dNTI = 0,05 > C1). BT del centro 260 K contra
    t_bg 270 K: la compuerta (273 K) lo rechaza."""
    nti = np.full((7, 7), -0.90)
    nti[3, 3] = -0.85
    bt = np.full((7, 7), 255.0)
    bt[3, 3] = 260.0
    roi = np.ones((7, 7), dtype=bool)
    return nti, bt, roi


def test_dnti_contextual_sin_compuerta_toma_el_centro():
    nti, bt, roi = _escena_minima()
    con = contextual_dnti_hot_mask(nti, bt, roi, 270.0, 0.003, 3.0)
    sin = contextual_dnti_hot_mask(nti, bt, roi, 270.0, 0.003, 3.0, apply_bt_gate=False)
    assert not con.any()
    assert sin[3, 3] and int(sin.sum()) == 1


def test_dual_roi_reenvia_la_compuerta():
    nti, bt, roi = _escena_minima()
    dist = np.zeros((7, 7))
    con = dual_roi_contextual_dnti_hot_mask(nti, bt, roi, dist, 270.0, 0.003, 0.010, 5.0, 3.0)
    sin = dual_roi_contextual_dnti_hot_mask(nti, bt, roi, dist, 270.0, 0.003, 0.010, 5.0, 3.0,
                                            apply_bt_gate=False)
    assert not con.any()
    assert sin[3, 3] and int(sin.sum()) == 1


def test_sin_compuerta_sigue_exigiendo_bt_finita():
    nti, bt, roi = _escena_minima()
    bt[3, 3] = np.nan
    sin = contextual_dnti_hot_mask(nti, bt, roi, 270.0, 0.003, 3.0, apply_bt_gate=False)
    assert not sin[3, 3]


def test_el_primer_pase_sin_compuerta_sigue_exigiendo_bt_finita():
    """Misma garantía en el primer pase: sin compuerta el criterio es BT finita, no 'cualquier BT'.
    Un NaN de BT es un píxel sin dato, no un píxel frío."""
    e = entradas_helpers()
    bt = e["bt"].copy()
    r, c = CENTRO_V375, CENTRO_V375
    bt[r, c] = np.nan
    hot, _ = first_pass_tests_2_and_3(nti=e["nti"], nti_app=e["nti_app"], bt=bt,
                                      roi_mask=e["roi"], dist_km=e["dist"], t_bg=e["t_bg"],
                                      bt_sanity_k=3.0, inner_km=5.0, c1_dnti_scene=0.010,
                                      c1_deti_scene=0.010, c2_dnti_scene=10, c2_deti_scene=10,
                                      apply_bt_gate=False)
    assert not hot[r, c]


def test_el_segundo_pase_no_recibe_temperatura():
    """Corrección S138: el segundo pase no tiene compuerta; por eso rescata lo que ella rechaza."""
    assert "bt" not in inspect.signature(second_pass_adjacent).parameters
    assert "apply_bt_gate" not in inspect.signature(second_pass_adjacent).parameters
