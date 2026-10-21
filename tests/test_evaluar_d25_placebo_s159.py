"""S159, tarea I2: el evaluador del A/B de D25 (experiments/_s157_prereg_d25/evaluar_d25.py).

POR QUE. (1) El evaluador dejaba por defecto la calibración original de M y decía que la simétrica «requiere el
sello», pero el sello existe: ADENDA_CALIBRACION.md, l. 3 a 8 (D-27, Nicolás, 2026-10-20) dice que rige la simétrica
con la opción A y que «El evaluador corre con `--calibracion simetrica`» (VB-2 de AUDIT_S158_R2). Un despacho que
olvidara el argumento evaluaba con una regla ya reemplazada. (2) La segunda ronda midió que un brazo placebo que sólo
multiplica la magnitud de K por 1,2 da MEJORA bajo la calibración simétrica (R2-8): como K queda bajo MIROVA (razón
~0,67 en VIIRS 375), cualquier ganancia acerca. Una métrica que aprueba un placebo no distingue un mecanismo fiel de
una ganancia cualquiera, así que el evaluador corre la misma decisión sobre K×1,2 y K×0,8 antes de dar veredicto y,
si alguna da MEJORA en un estrato que decide, el veredicto queda INVALIDO POR INSTRUMENTO.
La regla de decisión sellada no se toca: el placebo es un control del instrumento, no un criterio nuevo.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

RAIZ = Path(__file__).parent.parent
DIR = RAIZ / "experiments" / "_s157_prereg_d25"
sys.path.insert(0, str(DIR))
_spec = importlib.util.spec_from_file_location("evaluar_d25_s159", DIR / "evaluar_d25.py")
X = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(X)


def _pares(razon, vols=("Lascar", "Isluga", "Tupungatito"), noches=12, por_noche=2, ruido=0.03, semilla=1):
    """Pares de un estrato: K = razon × MIROVA con ruido lognormal chico; el brazo D igual a K (nulo)."""
    rng = np.random.default_rng(semilla)
    P = []
    for v in vols:
        for n in range(noches):
            for j in range(por_noche):
                m = float(10 ** rng.uniform(-1, 0.5))
                k = m * razon * float(10 ** rng.normal(0, ruido))
                P.append({"k": k, "d": k, "m": m, "clave": "%s|VIIRS750|2026-09-%02d 05:%02d" % (v, n + 1, j),
                          "bloque": "%s|2026-09-%02d" % (v, n + 1)})
    return P


# ---------------------------------------------------------------- (a) el valor por defecto es el del sello

def test_el_sello_vigente_declara_la_simetrica():
    lineas = (DIR / "ADENDA_CALIBRACION.md").read_text(encoding="utf-8").splitlines()
    sello = " ".join(lineas[2:8])          # l. 3 a 8
    assert "SELLADA por Nicolás" in sello and "D-27" in sello
    assert "--calibracion simetrica" in sello


def test_el_defecto_del_evaluador_es_el_del_sello():
    assert X.CALIB_MODO == "simetrica"
    fuente = (DIR / "evaluar_d25.py").read_text(encoding="utf-8")
    assert "requiere el sello de Nicolás" not in fuente, "el evaluador sigue diciendo que la simétrica no está sellada"


# ---------------------------------------------------------------- (b) placebo obligatorio

def test_placebo_de_ganancia_invalida_cuando_K_queda_bajo_mirova():
    """K a 0,6 de MIROVA en tres volcanes: K×1,2 se acerca y la regla sellada lo aprueba. El instrumento no sirve."""
    P = _pares(0.6)
    ver, info = X.evaluar_m({"VIIRS750|z<=40": P}, ok_ctrl=True, modo_calib="simetrica")
    assert ver["M|VIIRS750|z<=40"] == "NEUTRO"          # el brazo es igual a K: sin efecto propio
    assert info["M_placebo"].get("VIIRS750|z<=40", {}).get("1.2") == "MEJORA", "el placebo no probó K x 1,2"
    assert ver["PLACEBO"].startswith("INVALIDO"), ver["PLACEBO"]
    assert "1.2" in ver["PLACEBO"] and "VIIRS750|z<=40" in ver["PLACEBO"]


def test_placebo_hacia_abajo_invalida_cuando_K_queda_sobre_mirova():
    P = _pares(1.6)
    ver, info = X.evaluar_m({"VIIRS750|z<=40": P}, ok_ctrl=True, modo_calib="simetrica")
    assert info["M_placebo"]["VIIRS750|z<=40"].get("0.8") == "MEJORA", "el placebo no probó K x 0,8"
    assert ver["PLACEBO"].startswith("INVALIDO") and "0.8" in ver["PLACEBO"]


def test_placebo_no_invalida_cuando_K_calza_con_mirova():
    """Control: si K ya calza, una ganancia de 1,2 o 0,8 aleja y la regla no la aprueba; el instrumento sirve."""
    P = _pares(1.0)
    ver, info = X.evaluar_m({"VIIRS750|z<=40": P}, ok_ctrl=True, modo_calib="simetrica")
    assert set(info["M_placebo"]["VIIRS750|z<=40"].values()) <= {"EMPEORA", "NEUTRO", "INDECIDIBLE"}
    assert ver["PLACEBO"] == "OK"


def test_placebo_en_estrato_que_solo_informa_no_invalida():
    P = _pares(0.6, vols=("Lastarria", "Villarrica", "Chaiten"))
    ver, _ = X.evaluar_m({"VIIRS375|kernel|z<=40": P}, ok_ctrl=True, modo_calib="simetrica")
    assert ver["PLACEBO"] == "OK"


def test_placebo_se_mide_aunque_fallen_los_controles():
    """El placebo prueba la métrica, no la corrida: con controles caídos se informa igual."""
    ver, info = X.evaluar_m({"VIIRS750|z<=40": _pares(0.6)}, ok_ctrl=False, modo_calib="simetrica")
    assert ver["M|VIIRS750|z<=40"] == "INDECIDIBLE"
    assert ver["PLACEBO"].startswith("INVALIDO")


def test_evaluar_m_no_cambia_la_decision_del_brazo():
    """La extracción de evaluar_m no puede mover la decisión: un brazo que lleva K a mitad de camino hacia MIROVA."""
    P = _pares(0.6)
    for p in P:
        p["d"] = p["k"] * (p["m"] / p["k"]) ** 0.5
    ver, info = X.evaluar_m({"VIIRS750|z<=40": P}, ok_ctrl=True, modo_calib="simetrica")
    assert ver["M|VIIRS750|z<=40"] == "MEJORA"
    assert info["M|VIIRS750|z<=40"]["volcanes_con_d_negativa"] == 3


def test_veredicto_de_la_ventana_queda_invalido_con_el_motivo():
    ver = {"P1|VIIRS375": "CUMPLE", "P1|VIIRS750": "CUMPLE", "P2|VIIRS375": "EMPATE", "P2|VIIRS750": "EMPATE",
           "P1b|VIIRS375": "SIN CRUCES", "P1b|VIIRS750": "SIN CRUCES"}
    for nom, modo in X.ESTRATOS:
        ver["M|%s" % nom] = "MEJORA" if nom == "VIIRS750|z<=40" else "NEUTRO"
    ver["PLACEBO"] = "OK"
    estado, mejora, _ = X.global_ventana(ver, True)
    assert estado == "MEJORA" and mejora
    ver["PLACEBO"] = "INVALIDO: placebo x1.2 da MEJORA en VIIRS750|z<=40"
    estado, mejora, empeora = X.global_ventana(ver, True)
    assert estado.startswith("INVALIDO POR INSTRUMENTO"), estado
    assert "x1.2" in estado and "sin el placebo: MEJORA" in estado
    assert not mejora and not empeora
    assert X.peor([estado, "NO CUMPLE (veto)", "MEJORA"]) == estado


def test_combinar_no_da_cumple_con_una_ventana_invalida(tmp_path):
    a, b = tmp_path / "v1.json", tmp_path / "v2.json"
    a.write_text(json.dumps({"ventana": "V1", "estado": "INVALIDO POR INSTRUMENTO (x) | sin el placebo: MEJORA",
                             "mejora": False, "empeora": False}), encoding="utf-8")
    b.write_text(json.dumps({"ventana": "V2", "estado": "MEJORA", "mejora": True, "empeora": False}), encoding="utf-8")
    assert X.combinar([str(a), str(b)]).startswith("INVALIDO POR INSTRUMENTO")
