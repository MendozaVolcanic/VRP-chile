"""S159, D-34: P2 del A/B de D25 con intervalo por bloques noche-volcán (experiments/_s157_prereg_d25/ADENDA_GEMELO.md).

POR QUE. En V1 los tres brazos corren en el mismo job, en serie sobre la misma CPU, y el gemelo K' salió copia bit a bit
de K (0 de 4.610 pasadas distintas; experiments/_s159/gemelo_d25/INFORME.md en s159-pruebas, d5b6839b2). Con ese
«ruido» en 0, P2 decidía GANA o PIERDE con una sola pasada neta. Pero el ruido que importa no es el de la máquina sino
el de muestreo: si D publica mejor que K en general o sólo en estas noches. Nicolás selló el 2026-10-21 (D-34):
«si, has lo que nos entregue mayor informacion o la mejor metodologia para lograr nuestro trabajo, tenemos tokens
tiempo y podemos probarlo todo». La regla: diferencia neta de errores de P2 sobre las pasadas discordantes, con un
intervalo al 95 % por bloques noche-volcán (la maquinaria y la semilla de M, D-27).

Signo (el de la definición de P2 del pre-registro, §5: P2 cuenta ERRORES): neto = errores de D menos errores de K.
Positivo es malo para D. Una alerta bajo 1 MW que D publica y K no RESTA (D comete un error menos); una publicación de
D en un negativo limpio que K no tiene SUMA.

Las pruebas fallan primero por ASERCIÓN (S152), por eso preguntan antes si la función existe.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
DIR = Path(os.environ.get("D25_EVALUADOR_DIR") or (RAIZ / "experiments" / "_s157_prereg_d25"))
sys.path.insert(0, str(DIR))
_spec = importlib.util.spec_from_file_location("evaluar_d25_p2_s159", DIR / "evaluar_d25.py")
X = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(X)


def _contrib(por_noche, vol="Lascar", sensor="VIIRS375", mes="09"):
    """por_noche: lista de listas de contribuciones (+1 = error que sólo comete D, -1 = error que sólo comete K)."""
    out = []
    for n, cs in enumerate(por_noche):
        for j, c in enumerate(cs):
            clave = "%s|%s|2026-%s-%02d 05:%02d" % (vol, sensor, mes, n + 1, j)
            out.append({"clave": clave, "c": c, "bloque": "%s|2026-%s-%02d" % (vol, mes, n + 1)})
    return out


def _tiene(nombre):
    assert hasattr(X, nombre), "falta %s (D-34)" % nombre


# ---------------------------------------------------------------- la regla (D-34 §3)

def test_d_que_gana_en_muchas_noches_da_gana():
    _tiene("decidir_p2_bloques")
    v, det = X.decidir_p2_bloques(_contrib([[-1]] * 12), ok_ctrl=True)
    assert v == "GANA", (v, det)
    assert det["neto"] == -12 and det["ic95"][1] < 0


def test_d_que_gana_todo_en_una_sola_noche_da_empate():
    """Doce pasadas de una misma noche: es una noche, no doce pruebas independientes. Con 12 el bootstrap por pasada da
    GANA ([-18, -4]) y el de bloques EMPATE ([-36, 0]); con 8 los dos caían en 0 por ser sumas discretas y la prueba no
    distinguía la mutación «bootstrap por pasada» (medido en la primera corrida de mutar_comparador.py de D-34)."""
    _tiene("decidir_p2_bloques")
    c = _contrib([[-1] * 12, [+1, -1], [+1, -1], [+1, -1], [+1, -1]])
    v, det = X.decidir_p2_bloques(c, ok_ctrl=True)
    assert det["neto"] == -12, det
    assert v == "EMPATE", (v, det)


def test_neto_en_contra_chico_bloquea_sin_dar_pierde():
    _tiene("decidir_p2_bloques")
    v, det = X.decidir_p2_bloques(_contrib([[+1]] * 6 + [[-1]] * 4), ok_ctrl=True)
    assert det["neto"] == 2, det
    assert v == "BLOQUEA", (v, det)
    assert det["ic95"][0] <= 0 <= det["ic95"][1]


def test_neto_en_contra_grande_y_repartido_da_pierde():
    _tiene("decidir_p2_bloques")
    v, det = X.decidir_p2_bloques(_contrib([[+1]] * 12), ok_ctrl=True)
    assert v == "PIERDE", (v, det)


@pytest.mark.parametrize("por_noche", [[[+1]] * 4, [[+1, +1, +1], [+1, +1, +1]]])
def test_sin_sustrato_con_menos_de_5_pasadas_o_3_noches(por_noche):
    _tiene("decidir_p2_bloques")
    v, det = X.decidir_p2_bloques(_contrib(por_noche), ok_ctrl=True)
    assert v == "SIN SUSTRATO", (v, det)


def test_controles_caidos_dejan_indecidible():
    _tiene("decidir_p2_bloques")
    v, _ = X.decidir_p2_bloques(_contrib([[-1]] * 12), ok_ctrl=False)
    assert v == "INDECIDIBLE"


# ---------------------------------------------------------------- contar: el signo, la lista y lo informativo

def _fila(pub, lab, disp=0.0, vrp_ref=None):
    return {"pub": pub, "lab": lab, "disp": disp, "vrp_ref": vrp_ref, "z": 20.0, "plataforma": "NOAA20",
            "pc_lat": None, "pc_lon": None}


def _armar():
    """Seis noches de Láscar en VIIRS 375 (septiembre, V2 decide desde abril): en cinco, D publica una alerta Muy Bajo
    que K pierde (D comete un error menos); en una, D publica un negativo limpio que K no (un error más). Más una pasada
    concordante en cada noche que no puede entrar a la lista."""
    T, R = {}, {"K": {}, "D": {}}
    for n in range(6):
        k = "Lascar|VIIRS375|2026-09-%02d 05:10" % (n + 1)
        if n < 5:
            T[k] = {"control": _fila(False, "pos", 0.0, 0.3), "brazo": _fila(True, "pos", 0.2, 0.3)}
            R["K"][k], R["D"][k] = {"pc_vrp": 0.0}, {"pc_vrp": 0.2}
        else:
            T[k] = {"control": _fila(False, "neg_limpio"), "brazo": _fila(True, "neg_limpio", 0.4)}
            R["K"][k], R["D"][k] = {"pc_vrp": 0.0}, {"pc_vrp": 0.4}
        k2 = "Lascar|VIIRS375|2026-09-%02d 06:40" % (n + 1)
        T[k2] = {"control": _fila(True, "neg_limpio", 0.1), "brazo": _fila(True, "neg_limpio", 0.1)}
        R["K"][k2], R["D"][k2] = {"pc_vrp": 0.1}, {"pc_vrp": 0.1}
    prot = {k: {"A": False, "B": False, "alerta_solo_ocr": False} for k in T}
    cfg = {"brazos": ("K", "D"), "solo_tabla": True, "desde": "2026-09-01", "hasta": "2026-09-30"}
    res_ctrl = {"controles_ok": True, "cableado": {"K": True, "D": True}}
    return {("K", "D"): T}, prot, R, cfg, res_ctrl


def test_contar_usa_el_signo_de_errores_y_trae_la_lista():
    _tiene("decidir_p2_bloques")
    T, prot, R, cfg, res_ctrl = _armar()
    ver, info = X.contar(T, prot, R, cfg, "SN", res_ctrl, None, {"Lascar": 5.0})
    i = info["P2|VIIRS375"]
    assert "neto" in i, "contar no usa la regla de D-34"
    assert i["neto"] == -5 + 1, "signo: neto = errores de D menos errores de K: %s" % i["neto"]
    lista = i["discordantes"]
    assert len(lista) == 6, "la lista trae %d pasadas, son 6 las discordantes" % len(lista)
    assert all("06:40" not in x["hora"] for x in lista), "una pasada concordante entró a la lista"
    x = next(x for x in lista if x["hora"] == "2026-09-06 05:10")
    assert x == {"volcan": "Lascar", "sensor": "VIIRS375", "hora": "2026-09-06 05:10", "publica_K": False,
                 "publica_D": True, "clase_mirova": "neg_limpio", "vrp_mirova": None, "pc_vrp_mw_K": 0.0,
                 "pc_vrp_mw_D": 0.4, "error_de": "D", "contribucion": 1}, x
    assert ver["P2|VIIRS375"] in ("GANA", "EMPATE", "BLOQUEA", "PIERDE")


def test_contar_informa_las_reglas_a_y_b_sin_decidir():
    """D-34: el JSON trae lo que habrían dado la regla del gemelo (a) y la de D-33 (b), para ver si la elección de
    regla cambia el veredicto. No deciden."""
    _tiene("decidir_p2_bloques")
    T, prot, R, cfg, res_ctrl = _armar()
    ver, info = X.contar(T, prot, R, cfg, "SN", res_ctrl, None, {"Lascar": 5.0})
    i = info["P2|VIIRS375"]
    assert "regla_a_gemelo" in i and "regla_b_d33" in i, "no se informan las reglas a y b"
    # sin gemelo ni ruido de V1: ruido 0; suma K 5, suma D 1 -> (a) GANA; neto 4 pasadas -> (b) también GANA
    assert i["regla_a_gemelo"] == "GANA", i["regla_a_gemelo"]
    assert i["regla_b_d33"] == "GANA", i["regla_b_d33"]
    # con margen de 1 o 2 la (b) queda pendiente de diagnóstico
    assert X.regla_b_d33("PIERDE", 2) == "PENDIENTE DE DIAGNOSTICO POR PASADA (PIERDE por 2)"
    assert X.regla_b_d33("GANA", 3) == "GANA"
    assert X.regla_b_d33("EMPATE", 1) == "EMPATE"


# ---------------------------------------------------------------- la ventana y combinar

def _ver(p2_375="EMPATE", m750="MEJORA"):
    ver = {"P1|VIIRS375": "CUMPLE", "P1|VIIRS750": "CUMPLE", "P2|VIIRS375": p2_375, "P2|VIIRS750": "EMPATE",
           "P1b|VIIRS375": "SIN CRUCES", "P1b|VIIRS750": "SIN CRUCES"}
    for nom, modo in X.ESTRATOS:
        ver["M|%s" % nom] = m750 if nom == "VIIRS750|z<=40" else "NEUTRO"
    return ver


def test_p2_que_bloquea_no_deja_cumplir(tmp_path):
    _tiene("decidir_p2_bloques")
    estado, mejora, empeora = X.global_ventana(_ver("BLOQUEA"), True)
    assert estado.startswith("DECIDE NICOLAS") and "P2" in estado, estado
    assert empeora, "un P2 que bloquea tiene que marcar la ventana como bloqueada"
    a, b = tmp_path / "v1.json", tmp_path / "v2.json"
    a.write_text(json.dumps({"ventana": "V1", "estado": estado, "mejora": mejora, "empeora": empeora}), encoding="utf-8")
    b.write_text(json.dumps({"ventana": "V2", "estado": "MEJORA", "mejora": True, "empeora": False}), encoding="utf-8")
    assert X.combinar([str(a), str(b)]) != "CUMPLE"


def test_p2_sin_sustrato_no_bloquea():
    _tiene("decidir_p2_bloques")
    estado, mejora, empeora = X.global_ventana(_ver("SIN SUSTRATO"), True)
    assert estado == "MEJORA" and mejora and not empeora, estado
