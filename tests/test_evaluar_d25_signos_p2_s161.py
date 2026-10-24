"""S161, D-45: P2 del A/B de D25 se decide con la prueba de signos por bloque noche-volcán
(experiments/_s157_prereg_d25/ADENDA_SIGNOS_P2.md, quinta adenda, sellada por Nicolás el 2026-10-22).

POR QUE. El verificador de D-42, vuelta 3 (experiments/_s159/instrumentos/verificador_d42/vuelta3/INFORME.md, V42-20),
enumeró los 2^B repartos de signo con la función real y mostró que el intervalo bootstrap de D-34 deja el neto entero
sobre 0 también con 6 noches contra 1: con 7 noches su tasa exacta de falsos es 6,25 % por cola, la calibración de D-42
lo ve y deja P2 INDECIDIBLE, así que 7 noches discordantes todas del mismo lado (el efecto más claro que P2 puede
recibir) quedaban siempre INDECIDIBLE, aunque la prueba exacta de signos dé p = 1/128. Nicolás eligió (D-45): «Sí a
D-45 opción (ii): P2 se decide con la prueba de signos por bloque noche-volcán (exacta hasta 20 noches)».

La regla (adenda §2): el bloque es la noche-volcán; su suma es la suma de los aportes de sus pasadas (+1 error sólo de
D, -1 sólo de K); B cuenta los bloques con alguna discordante, incluidos los de suma 0; bajo el nulo cada bloque cambia
de signo con probabilidad 1/2; una cola por dirección al 5 %; exacto con B <= 20 (2^B repartos), con B >= 21 10.000
sorteos con semilla 162 y valor-p (1 + m) / 10.001; comparación en enteros; GANA, PIERDE, BLOQUEA (neto > 0 sin
llegar) o EMPATE; SIN SUSTRATO con B <= 4; INDECIDIBLE sólo con controles caídos. D-34 y D-42 dejan de decidir y se
informan (§3). El detalle trae lo de §4.

Los números sellados están escritos aquí como literales: la prueba no los lee del evaluador. Los oráculos se escriben
aparte: el exacto ENUMERA los 2^B repartos con bits (no convoluciona, como el evaluador), el de sorteos repite el sorteo
con los literales 162 y 10.000. Lo que fija el oráculo de sorteos además de la semilla: el orden de los bloques
(ordenados por su clave) y la forma del sorteo (np.random.default_rng(162).choice((-1, 1), size=(10000, B))).

Las pruebas fallan primero por ASERCIÓN (S152, S156): preguntan si el campo existe antes de leerlo.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import os
import subprocess
import sys
from datetime import date, timedelta
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest

RAIZ = Path(__file__).parent.parent
DIR = Path(os.environ.get("D25_EVALUADOR_DIR") or (RAIZ / "experiments" / "_s157_prereg_d25"))
sys.path.insert(0, str(DIR))
_spec = importlib.util.spec_from_file_location("evaluar_d25_signos_p2_s161", DIR / "evaluar_d25.py")
X = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(X)

# Los números sellados (ADENDA_SIGNOS_P2.md §2.5 y §2.7), como literales.
SEMILLA_SIGNOS, N_SORTEOS_SIGNOS, MAX_B_EXACTO, MAX_B_SIN_SUSTRATO = 162, 10000, 20, 4
CAMPOS_D45 = ("neto", "B", "bloques_suma_no_nula", "sumas_bloque", "p_gana", "p_pierde", "p_dos_colas",
              "p_gana_fraccion", "p_pierde_fraccion", "p_dos_colas_fraccion", "metodo", "p_minimo",
              "p_minimo_fraccion", "semilla_signos",
              "n_sorteos_signos", "regla")
# Lo que deja de decidir y se informa (§3): D-34 sin calibrar con su intervalo, y D-42 entera.
CAMPOS_INFORMA = ("resultado_sin_calibrar", "ic95", "resultado_d42", "calibrada", "falsos_gana", "falsos_pierde",
                  "falsos_bloquea", "n_sorteos", "semilla_calibracion")


def _contrib(por_noche, vol="Lascar", sensor="VIIRS375"):
    """por_noche: lista de listas de aportes (+1 = error que sólo comete D, -1 = error que sólo comete K). Cada noche es
    un día distinto desde el 2026-08-01 (sirve para más de 31 noches)."""
    out = []
    for n, cs in enumerate(por_noche):
        dia = (date(2026, 8, 1) + timedelta(days=n)).isoformat()
        for j, c in enumerate(cs):
            out.append({"clave": "%s|%s|%s 05:%02d" % (vol, sensor, dia, j), "c": c, "bloque": "%s|%s" % (vol, dia)})
    return out


def _decidir(por_noche, ok_ctrl=True):
    v, det = X.decidir_p2_bloques(_contrib(por_noche), ok_ctrl=ok_ctrl)
    for campo in CAMPOS_D45:
        assert campo in det, "el detalle de P2 no trae %s (ADENDA_SIGNOS_P2.md §4)" % campo
    return v, det


def _sumas_bloque(contrib):
    """Las sumas por bloque en el orden de la clave del bloque (el orden del sorteo)."""
    tot = {}
    for x in contrib:
        tot[x["bloque"]] = tot.get(x["bloque"], 0) + x["c"]
    return [tot[b] for b in sorted(tot)]


def _oraculo_exacto(sumas, neto):
    """ENUMERA los 2^B repartos (un signo por bloque) con bits; devuelve (k_gana, k_pierde, k_dos, 2^B)."""
    B = len(sumas)
    s = np.asarray(sumas, dtype=np.int64)
    le = ge = dos = 0
    for i0 in range(0, 2 ** B, 1 << 16):                  # de a 65.536 repartos
        k = np.arange(i0, min(2 ** B, i0 + (1 << 16)), dtype=np.int64)
        tot = (1 - 2 * ((k[:, None] >> np.arange(B, dtype=np.int64)) & 1)) @ s
        le += int((tot <= neto).sum()); ge += int((tot >= neto).sum()); dos += int((np.abs(tot) >= abs(neto)).sum())
    return le, ge, dos, 2 ** B


def _oraculo_sorteos(sumas, neto):
    """El sorteo de la adenda §2.5 con los literales: 10.000 sorteos de signos por bloque, semilla 162, valor-p con +1."""
    S = np.random.default_rng(SEMILLA_SIGNOS).choice((-1, 1), size=(N_SORTEOS_SIGNOS, len(sumas)))
    tot = S @ np.asarray(sumas, dtype=np.int64)
    m = (int((tot <= neto).sum()), int((tot >= neto).sum()), int((np.abs(tot) >= abs(neto)).sum()))
    return tuple(1 + x for x in m) + (N_SORTEOS_SIGNOS + 1,)


def _frac(det, campo):
    f = det[campo + "_fraccion"]
    assert isinstance(f, (list, tuple)) and len(f) == 2 and all(isinstance(x, int) for x in f), (campo, f)
    return Fraction(f[0], f[1]) if f[1] else None


# ---------------------------------------------------------------- las constantes selladas

def test_las_constantes_de_la_prueba_de_signos_son_las_selladas():
    """§2.5 y §2.7: semilla 162 = SEMILLA + 5, 10.000 sorteos, exacto hasta B = 20, SIN SUSTRATO con B <= 4."""
    for nombre in ("SEMILLA_P2_SIGNOS", "N_SORTEOS_P2_SIGNOS", "MAX_B_EXACTO_P2", "MAX_B_SIN_SUSTRATO_P2"):
        assert hasattr(X, nombre), "falta %s (D-45)" % nombre
    assert X.SEMILLA_P2_SIGNOS == SEMILLA_SIGNOS == X.SEMILLA + 5, X.SEMILLA_P2_SIGNOS
    assert X.N_SORTEOS_P2_SIGNOS == N_SORTEOS_SIGNOS, X.N_SORTEOS_P2_SIGNOS
    assert X.MAX_B_EXACTO_P2 == MAX_B_EXACTO, X.MAX_B_EXACTO_P2
    assert X.MAX_B_SIN_SUSTRATO_P2 == MAX_B_SIN_SUSTRATO, X.MAX_B_SIN_SUSTRATO_P2


# ---------------------------------------------------------------- el caso de V42-20 (§7, tercer punto; mutación 11)

@pytest.mark.parametrize("signo,esperado", [(+1, "PIERDE"), (-1, "GANA")])
def test_siete_noches_del_mismo_lado_deciden_con_p_1_de_128(signo, esperado):
    """V42-20: con 7 noches todas del mismo lado la calibración de D-42 falla (la regla de D-34 tiene 6,25 % por cola
    con B = 7) y dejaba INDECIDIBLE. Con D-45 decide, con p = 1/128 en la cola de su dirección (mutación 11: la
    calibración de D-42 todavía decide). Control de poder: el detalle informa que D-42 habría dado INDECIDIBLE."""
    v, det = _decidir([[signo]] * 7)
    assert v == esperado, (v, det)
    cola, otra = ("p_pierde", "p_gana") if signo > 0 else ("p_gana", "p_pierde")
    assert _frac(det, cola) == Fraction(1, 128) and det[cola] == 1 / 128, det
    assert _frac(det, otra) == Fraction(1, 1), det
    assert (det["neto"], det["B"], det["metodo"]) == (7 * signo, 7, "exacto"), det
    assert det.get("resultado_d42") == "INDECIDIBLE" and det.get("calibrada") is False, \
        "sin poder: D-42 no habría bloqueado este caso: %s" % {k: det.get(k) for k in CAMPOS_INFORMA}


@pytest.mark.parametrize("signo,esperado", [(+1, "BLOQUEA"), (-1, "EMPATE")])
def test_seis_contra_una_con_siete_noches_no_decide(signo, esperado):
    """§7: 6 contra 1 con 7 noches no decide. Neto 5: p = 8/128 = 6,25 % > 5 % (mutación 2, tope al 10 %). La regla de
    D-34 sin calibrar sí lo daba por decidido (V42-20), y se informa."""
    v, det = _decidir([[signo]] * 6 + [[-signo]])
    assert v == esperado, (v, det)
    cola = "p_pierde" if signo > 0 else "p_gana"
    assert _frac(det, cola) == Fraction(8, 128), det
    assert det.get("resultado_sin_calibrar") == ("PIERDE" if signo > 0 else "GANA"), \
        "sin poder: la regla de D-34 no decidía este caso: %s" % det.get("resultado_sin_calibrar")


# ---------------------------------------------------------------- una cola por dirección (mutaciones 1 y 3)

@pytest.mark.parametrize("signo,esperado", [(+1, "PIERDE"), (-1, "GANA")])
def test_cinco_noches_del_mismo_lado_deciden_a_una_cola(signo, esperado):
    """§2.4: a una cola 5 noches del mismo lado dan p = 1/32 = 3,1 % y deciden; a dos colas (p = 1/16) no podrían
    (mutación 1). El valor-p a dos colas se informa al lado y no decide."""
    v, det = _decidir([[signo]] * 5)
    assert v == esperado, (v, det)
    cola = "p_pierde" if signo > 0 else "p_gana"
    assert _frac(det, cola) == Fraction(1, 32), det
    assert _frac(det, "p_dos_colas") == Fraction(2, 32), det


def test_la_cola_de_gana_es_menor_o_igual_y_la_de_pierde_mayor_o_igual():
    """§2.4 (mutación 3): GANA = fracción de repartos con suma <= neto; PIERDE = fracción con suma >= neto. Con el neto
    observado en -5 y bloques [-2, -1, -1, +1, -1, -1] los dos valores-p se calculan aparte por enumeración."""
    por_noche = [[-1, -1], [-1], [-1], [+1], [-1], [-1, +1, -1]]
    c = _contrib(por_noche)
    s = _sumas_bloque(c)
    neto = sum(s)
    k_le, k_ge, k_dos, den = _oraculo_exacto(s, neto)
    v, det = _decidir(por_noche)
    assert det["neto"] == neto == -5, det
    assert _frac(det, "p_gana") == Fraction(k_le, den) and _frac(det, "p_pierde") == Fraction(k_ge, den), (det, k_le, k_ge)
    assert _frac(det, "p_dos_colas") == Fraction(k_dos, den), det
    assert k_le != k_ge, "sin poder: las dos colas coinciden y no distinguen la dirección"


# ---------------------------------------------------------------- SIN SUSTRATO y B (mutaciones 4 y 5)

@pytest.mark.parametrize("signo", [+1, -1])
def test_cuatro_noches_dan_sin_sustrato(signo):
    """§2.7: con B <= 4 P2 da SIN SUSTRATO y no decide ni bloquea (mutación 4 con B <= 3: con 4 noches de +1 saldría
    BLOQUEA y con 4 de -1 EMPATE). Los campos de §4 se informan igual."""
    v, det = _decidir([[signo]] * 4)
    assert v == "SIN SUSTRATO", (v, det)
    assert det["B"] == 4 and _frac(det, "p_minimo") == Fraction(1, 16), det


def test_b_cuenta_los_bloques_de_suma_cero():
    """§2.2 (mutación 5): cuatro noches de -1 y una noche con un error de D y otro de K (suma 0) son B = 5, no 4: P2
    se calcula (EMPATE, p = 2/32) y no queda SIN SUSTRATO."""
    v, det = _decidir([[-1]] * 4 + [[+1, -1]])
    assert det["B"] == 5 and det["bloques_suma_no_nula"] == 4, det
    assert sorted(det["sumas_bloque"]) == [-1, -1, -1, -1, 0], det
    assert _frac(det, "p_gana") == Fraction(2, 32) and _frac(det, "p_minimo") == Fraction(1, 32), det
    assert v == "EMPATE", (v, det)


# ---------------------------------------------------------------- signo por bloque (mutación 6)

def test_el_signo_es_por_bloque_y_no_por_pasada():
    """§2.3 (mutación 6): doce errores sólo de K en una misma noche y cuatro noches de suma 0 son 5 bloques; la noche
    entera cambia de signo junta, así que P(suma <= -12) = 1/2 y P2 da EMPATE. Por pasada (20 monedas) saldría GANA."""
    v, det = _decidir([[-1] * 12, [+1, -1], [+1, -1], [+1, -1], [+1, -1]])
    assert det["neto"] == -12 and det["B"] == 5, det
    assert _frac(det, "p_gana") == Fraction(1, 2), det
    assert v == "EMPATE", (v, det)


# ---------------------------------------------------------------- el método y la semilla (mutaciones 7, 8 y 9)

def _veinte():
    """B = 20 con bloques desiguales y dos de suma 0: 3 + 1 + 0 + ... para que el valor-p no sea simétrico trivial."""
    return [[-1, -1, -1], [-1], [+1, -1], [+1], [-1, -1]] + [[-1]] * 9 + [[+1]] * 4 + [[+1, -1, +1]] + [[-1, +1]]


def _veintiuno():
    """B = 21: una noche de 5 errores de K, 13 de uno de K, 7 de uno de D (neto -11)."""
    return [[-1] * 5] + [[-1]] * 13 + [[+1]] * 7


def test_con_b_20_el_metodo_es_exacto_y_reproduce_la_enumeracion():
    """§2.5 (mutación 7): con B <= 20 se enumeran los 2^B repartos. La prueba exige «exacto» en B = 20 y el valor-p
    k / 2^20 de la enumeración hecha aparte, sin semilla ni sorteos."""
    c = _veinte()
    s = _sumas_bloque(_contrib(c))
    assert len(s) == 20
    k_le, k_ge, k_dos, den = _oraculo_exacto(s, sum(s))
    v, det = _decidir(c)
    assert det["metodo"] == "exacto" and det["B"] == 20, det
    assert (_frac(det, "p_gana"), _frac(det, "p_pierde"), _frac(det, "p_dos_colas")) == (
        Fraction(k_le, den), Fraction(k_ge, den), Fraction(k_dos, den)), det
    assert det["p_gana_fraccion"][1] == 2 ** 20, "el denominador del exacto es 2^B: %s" % det["p_gana_fraccion"]
    assert det["semilla_signos"] is None and det["n_sorteos_signos"] is None, det
    assert _frac(det, "p_minimo") == Fraction(1, 2 ** 20), det


def test_con_b_21_son_10000_sorteos_con_semilla_162_y_el_mas_uno():
    """§2.5 (mutaciones 7, 8 y 9): con B >= 21, 10.000 sorteos de signos por bloque con semilla 162 y valor-p
    (1 + m) / 10.001. Se compara con el sorteo repetido aquí con los literales; el valor-p de GANA cae lejos de 0 y de
    1 (unas 1.000 de 10.000), así que otra semilla, otro número de sorteos o el valor-p sin el +1 dan otra fracción."""
    c = _veintiuno()
    s = _sumas_bloque(_contrib(c))
    assert len(s) == 21
    num_le, num_ge, num_dos, den = _oraculo_sorteos(s, sum(s))
    assert 100 < num_le < 9900, "sin poder: el sorteo no distingue semillas (%d)" % num_le
    v, det = _decidir(c)
    assert det["metodo"] == "sorteos" and det["B"] == 21, det
    assert (det["semilla_signos"], det["n_sorteos_signos"]) == (SEMILLA_SIGNOS, N_SORTEOS_SIGNOS), det
    assert list(det["p_gana_fraccion"]) == [num_le, den], (det["p_gana_fraccion"], num_le)
    assert list(det["p_pierde_fraccion"]) == [num_ge, den], (det["p_pierde_fraccion"], num_ge)
    assert list(det["p_dos_colas_fraccion"]) == [num_dos, den], (det["p_dos_colas_fraccion"], num_dos)
    assert det["p_gana"] == num_le / den, det
    assert _frac(det, "p_minimo") == Fraction(1, N_SORTEOS_SIGNOS + 1), det


def test_el_detalle_dice_la_semilla_y_los_sorteos_que_se_usaron(monkeypatch):
    """Como V42-04 para D-42: la semilla y el número de sorteos del detalle salen de lo que la prueba usó, no de las
    constantes (si no, una llamada con otros números seguiría declarando 162 y 10.000)."""
    assert hasattr(X, "prueba_signos_p2"), "falta prueba_signos_p2 (D-45)"
    original = X.prueba_signos_p2

    def otra(sumas, neto, n_sorteos=None, semilla=None):
        return original(sumas, neto, n_sorteos=50, semilla=7)
    monkeypatch.setattr(X, "prueba_signos_p2", otra)
    v, det = _decidir(_veintiuno())
    assert (det["semilla_signos"], det["n_sorteos_signos"]) == (7, 50), det
    assert det["p_gana_fraccion"][1] == 51, det


def test_un_sorteo_con_una_noche_grande_es_por_bloque():
    """§2.3 con sorteos (mutación 6 en la rama de B >= 21): una noche con doce errores de K y veinte noches de suma 0.
    Por bloque, la suma es ±12 con probabilidad 1/2 cada una: valor-p de GANA cerca de 1/2 y P2 EMPATE."""
    c = [[-1] * 12] + [[+1, -1]] * 20
    s = _sumas_bloque(_contrib(c))
    num_le, num_ge, num_dos, den = _oraculo_sorteos(s, sum(s))
    v, det = _decidir(c)
    assert det["metodo"] == "sorteos" and det["B"] == 21, det
    assert list(det["p_gana_fraccion"]) == [num_le, den], (det["p_gana_fraccion"], num_le)
    assert v == "EMPATE", (v, det)


# ---------------------------------------------------------------- el veredicto (§2.6, mutación 10)

def test_neto_cero_es_empate_y_no_bloquea():
    """§2.6 (mutación 10): BLOQUEA exige neto > 0; con neto 0 y sin llegar, EMPATE."""
    v, det = _decidir([[+1]] * 3 + [[-1]] * 3)
    assert det["neto"] == 0 and det["B"] == 6, det
    assert v == "EMPATE", (v, det)


def test_neto_positivo_sin_llegar_bloquea():
    v, det = _decidir([[+1]] * 6 + [[-1]] * 4)
    assert det["neto"] == 2 and det["B"] == 10, det
    assert _frac(det, "p_pierde") == Fraction(386, 1024), det
    assert v == "BLOQUEA", (v, det)


def test_con_muchas_noches_decide_en_las_dos_direcciones():
    for por_noche, esperado in (([[-1]] * 12, "GANA"), ([[+1]] * 12, "PIERDE")):
        v, det = _decidir(por_noche)
        assert v == esperado, (v, det)


def test_controles_caidos_dejan_indecidible_e_informan():
    """§2.8: con los controles generales caídos P2 sigue INDECIDIBLE (es lo único que lo deja INDECIDIBLE)."""
    v, det = _decidir([[-1]] * 12, ok_ctrl=False)
    assert v == "INDECIDIBLE", (v, det)
    assert det["neto"] == -12 and det["B"] == 12, det


def test_la_regla_que_decide_es_d45():
    v, det = _decidir([[-1]] * 7)
    assert "D-45" in det["regla"], det["regla"]


# ---------------------------------------------------------------- lo que se informa (§3, §4, mutación 12)

def _oraculo_d34(contrib):
    """La regla de D-34 aparte: intervalo al 95 % por bloques (10.000 remuestreos, semilla 157)."""
    cv = np.array([x["c"] for x in contrib], dtype=np.float64)
    W = X.pesos_bloque([x["bloque"] for x in contrib], n_boot=10000, semilla=157)
    s = W @ cv
    lo, hi = float(np.percentile(s, 2.5)), float(np.percentile(s, 97.5))
    neto = int(round(cv.sum()))
    return ("GANA" if hi < 0 else "PIERDE" if lo > 0 else "BLOQUEA" if neto > 0 else "EMPATE"), [lo, hi]


def test_d34_y_d42_se_informan_y_no_deciden():
    """§3 (mutación 12): el resultado de D-34 sin calibrar con su intervalo, y el de D-42 (calibrada o no, falsos GANA,
    PIERDE y BLOQUEA, sorteos y semilla 161), se informan. En 7 noches de +1 D-34 da PIERDE con el intervalo entero
    sobre 0, D-42 lo deja INDECIDIBLE (calibración fallida, 1.000 sorteos con semilla 161) y decide D-45 (PIERDE)."""
    c = _contrib([[+1]] * 7)
    v34, ic = _oraculo_d34(c)
    v, det = X.decidir_p2_bloques(c, ok_ctrl=True)
    for campo in CAMPOS_INFORMA:
        assert campo in det, "el detalle ya no informa %s (§3)" % campo
    assert (det["resultado_sin_calibrar"], det["ic95"]) == (v34, ic) == ("PIERDE", ic), (det, v34, ic)
    assert det["calibrada"] is False and det["resultado_d42"] == "INDECIDIBLE", det
    assert (det["n_sorteos"], det["semilla_calibracion"]) == (1000, 161), det
    assert max(det["falsos_pierde"], det["falsos_gana"]) > 0.05, det
    assert v == "PIERDE", (v, det)


def test_d42_calibrada_informa_el_resultado_de_d34():
    """Con 12 noches de -1 la calibración de D-42 pasa: D-42 habría decidido GANA, igual que D-45."""
    v, det = _decidir([[-1]] * 12)
    assert det.get("calibrada") is True and det.get("resultado_d42") == "GANA", det
    assert det.get("resultado_sin_calibrar") == "GANA" and v == "GANA", det


@pytest.mark.parametrize("por_noche,v34", [([[+1]] * 4, "SIN SUSTRATO"), ([[+1] * 4] * 3, "PIERDE")])
def test_d34_y_d42_conservan_su_propio_minimo(por_noche, v34):
    """LECTURA (README de signos_p2): D-34 y D-42 se informan con su propio mínimo (D-34 §5.6: 5 pasadas y 3 noches),
    para que se vea si el cambio de regla cambia el veredicto (§3). Tres noches de cuatro pasadas son SIN SUSTRATO
    para D-45 (B = 3) pero D-34 da PIERDE y D-42 INDECIDIBLE (la calibración corre)."""
    v, det = _decidir(por_noche)
    assert v == "SIN SUSTRATO", (v, det)
    assert det.get("resultado_sin_calibrar") == v34, det
    if v34 == "SIN SUSTRATO":
        assert det.get("resultado_d42") == "SIN SUSTRATO" and det.get("calibrada") is None, det
    else:
        assert det.get("resultado_d42") == "INDECIDIBLE" and det.get("calibrada") is False, det


def test_las_sumas_de_bloque_son_el_multiconjunto():
    por_noche = [[-1, -1], [+1], [+1, -1], [-1], [-1], [-1, -1, -1]]
    v, det = _decidir(por_noche)
    assert sorted(det["sumas_bloque"]) == [-3, -2, -1, -1, 0, 1], det
    assert det["neto"] == sum(det["sumas_bloque"]) == -6, det
    assert det["bloques_suma_no_nula"] == 5 and det["B"] == 6, det


# ---------------------------------------------------------------- contar, la ventana e imprimir

def _fila(pub, lab, disp=0.0, vrp_ref=None):
    return {"pub": pub, "lab": lab, "disp": disp, "vrp_ref": vrp_ref, "z": 20.0, "plataforma": "NOAA20",
            "pc_lat": None, "pc_lon": None}


def _armar(n_d, n_k):
    """Noches de Láscar en VIIRS 375 con una pasada discordante cada una: en n_d, D publica un negativo limpio que K no
    (error sólo de D, +1); en n_k, D publica una alerta Muy Bajo que K pierde (error sólo de K, -1). Más una pasada
    concordante por noche, que no aporta."""
    T, R = {}, {"K": {}, "D": {}}
    for n in range(n_d + n_k):
        k = "Lascar|VIIRS375|2026-09-%02d 05:10" % (n + 1)
        if n < n_d:
            T[k] = {"control": _fila(False, "neg_limpio"), "brazo": _fila(True, "neg_limpio", 0.3)}
        else:
            T[k] = {"control": _fila(False, "pos", 0.0, 0.3), "brazo": _fila(True, "pos", 0.2, 0.3)}
        R["K"][k], R["D"][k] = {"pc_vrp": 0.0, "dc": "summit"}, {"pc_vrp": 0.3, "dc": "summit"}
        k2 = "Lascar|VIIRS375|2026-09-%02d 06:40" % (n + 1)
        T[k2] = {"control": _fila(True, "neg_limpio", 0.1), "brazo": _fila(True, "neg_limpio", 0.1)}
        R["K"][k2], R["D"][k2] = {"pc_vrp": 0.1, "dc": "summit"}, {"pc_vrp": 0.1, "dc": "summit"}
    prot = {k: {"A": False, "B": False, "alerta_solo_ocr": False} for k in T}
    cfg = {"brazos": ("K", "D"), "solo_tabla": True, "desde": "2026-09-01", "hasta": "2026-09-30"}
    res_ctrl = {"controles_ok": True, "cableado": {"K": True, "D": True}}
    return {("K", "D"): T}, prot, R, cfg, res_ctrl


def _completar(ver):
    out = dict(ver)
    for s in X.SENS:
        out.setdefault("P1|%s" % s, "CUMPLE"); out.setdefault("P1b|%s" % s, "SIN CRUCES")
    return out


def test_contar_publica_el_veredicto_de_d45_y_la_ventana_lo_lee():
    """Como V42-02 para D-42: la regla decide en un solo punto, ver["P2|sensor"] dentro de contar, que es lo que lee
    global_ventana. Siete noches con un error sólo de D: D-45 da PIERDE (p = 1/128), D-42 habría dado INDECIDIBLE, y la
    ventana queda NO CUMPLE (suma de errores)."""
    T, prot, R, cfg, res_ctrl = _armar(7, 0)
    ver, info = X.contar(T, prot, R, cfg, "SN", res_ctrl, None, {"Lascar": 5.0})
    i = info["P2|VIIRS375"]
    assert i.get("resultado_d42") == "INDECIDIBLE", "sin poder: %s" % {k: i.get(k) for k in CAMPOS_INFORMA}
    assert ver["P2|VIIRS375"] == "PIERDE", "contar publica %s" % ver["P2|VIIRS375"]
    assert X.global_ventana(_completar(ver), True)[0] == "NO CUMPLE (suma de errores)"


def test_contar_no_publica_el_resultado_de_d34():
    """Seis noches con error de D y una con error de K: D-34 sin calibrar da PIERDE (V42-20), D-45 BLOQUEA (p = 8/128).
    La ventana queda en DECIDE NICOLAS por P2, no en NO CUMPLE."""
    T, prot, R, cfg, res_ctrl = _armar(6, 1)
    ver, info = X.contar(T, prot, R, cfg, "SN", res_ctrl, None, {"Lascar": 5.0})
    i = info["P2|VIIRS375"]
    assert i.get("resultado_sin_calibrar") == "PIERDE", "sin poder: %s" % i.get("resultado_sin_calibrar")
    assert ver["P2|VIIRS375"] == "BLOQUEA", "contar publica %s" % ver["P2|VIIRS375"]
    estado, mejora, empeora = X.global_ventana(_completar(ver), True)
    assert estado.startswith("DECIDE NICOLAS") and "P2" in estado and empeora, estado


def test_imprimir_muestra_la_regla_nueva_y_lo_que_informa(capsys):
    """El informe de texto dice qué regla decidió (D-45, valores-p, método) y deja a la vista D-34 y D-42."""
    T, prot, R, cfg, res_ctrl = _armar(7, 0)
    ver, info = X.contar(T, prot, R, cfg, "SN", res_ctrl, None, {"Lascar": 5.0})
    capsys.readouterr()
    X.imprimir("SN", ver, info, "estado")
    out = capsys.readouterr().out
    linea = next((l for l in out.splitlines() if l.strip().startswith("P2 VIIRS375")), "")
    assert "D-45" in linea and "PIERDE" in linea, linea
    assert "0.0078" in out and "exacto" in out, out
    assert "D-34" in out and "D-42" in out and "INDECIDIBLE" in out, out


# ---------------------------------------------------------------- punta a punta (el JSON)

E2E_VOLS = ["Lascar", "Villarrica"]
E2E_DESDE, E2E_HASTA = "2026-10-01", "2026-10-12"
REF_V1 = RAIZ / "experiments" / "_s157_prereg_d25" / "_congelado_v1"
BRAZOS = {"K": "_s157_ab_d25_k_control", "G": "_s157_ab_d25_k_gemelo", "D": "_s157_ab_d25_k_on"}
DECLARADO_K = {"ENABLE_TEST1_PATH": False, "ENABLE_TESTS_23_PROSE_BRANCH": True, "ENABLE_MODIS_B22_PRIMARY": True,
               "ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375": False, "ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750": False,
               "VRP_BG_NEIGHBOR_MAX_HALF_PX": 3, "SENSOR_MODIS": False}
DECLARADO = {"K": DECLARADO_K, "G": DECLARADO_K,
             "D": dict(DECLARADO_K, ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375=True, ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750=True)}


def _bucket(s):
    s = s or ""
    return "VIIRS750" if s.startswith("VIIRS") and s.endswith("_750") else "VIIRS375" if s.startswith("VIIRS") else None


@pytest.fixture(scope="module")
def e2e(tmp_path_factory):
    """Brazos desde PRODUCCIÓN (data/mirova_equivalent, K desde el 2026-09-18), nunca desde artefactos del A/B: K' = K;
    D = K con todas las publicaciones de VIIRS 375 apagadas (cúmulo a 0,0 MW), para que P2 tenga discordantes en
    varias noches. Referencia de MIROVA: la congelada de V1. Cobertura: histórico vacío y «producción» = K."""
    tmp = tmp_path_factory.mktemp("e2e_signos")
    K = {}
    for v in E2E_VOLS:
        recs = json.load(open(RAIZ / "data" / "mirova_equivalent" / (v + ".json"), encoding="utf-8"))["records"]
        K[v] = [r for r in recs if E2E_DESDE <= r["datetime_utc"][:10] <= E2E_HASTA and _bucket(r.get("sensor"))]
    D = copy.deepcopy(K)
    apagadas = 0
    for v in E2E_VOLS:
        for r in D[v]:
            pc = r.get("primary_cluster") or {}
            if pc:
                r["diag_bg_vecinos_n_sin_vecinos"] = 0
            if _bucket(r.get("sensor")) == "VIIRS375" and (pc.get("vrp_mw") or 0) > 0:
                pc["vrp_mw"] = 0.0
                apagadas += 1
                if r.get("f5_core_vrp_mw") is not None:
                    r["f5_core_vrp_mw"] = 0.0
    raiz = tmp / "raiz"
    (raiz / "logs").mkdir(parents=True)
    for n, recs in (("K", K), ("G", copy.deepcopy(K)), ("D", D)):
        (raiz / BRAZOS[n]).mkdir()
        for v, rr in recs.items():
            json.dump({"records": rr}, open(raiz / BRAZOS[n] / (v + ".json"), "w", encoding="utf-8"))
            fl = dict(DECLARADO[n], PROFILE_NAME=BRAZOS[n], DATA_SUBDIR=BRAZOS[n])
            (raiz / "logs" / ("%s_%s.log" % (BRAZOS[n], v))).write_text("FLAGS_BRAZO " + json.dumps(fl) + "\n",
                                                                         encoding="utf-8")
    hist, prod = tmp / "cob_hist", tmp / "cob_prod"
    hist.mkdir(); prod.mkdir()
    for v in E2E_VOLS:
        json.dump({"records": [{"datetime_utc": r["datetime_utc"], "sensor": r["sensor"]} for r in K[v]]},
                  open(prod / (v + ".json"), "w", encoding="utf-8"))
    out = tmp / "out.json"
    cmd = [sys.executable, str(DIR / "evaluar_d25.py"), "--ventana", "V1", "--raiz", str(raiz), "--logs",
           str(raiz / "logs"), "--out", str(out), "--tmp", str(tmp / "tmp"), "--vols", ",".join(E2E_VOLS), "--desde",
           E2E_DESDE, "--hasta", E2E_HASTA, "--ref", str(REF_V1), "--cobertura", str(hist), str(prod)]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    assert p.returncode == 0, "el evaluador cayó:\n" + p.stderr[-3000:]
    return json.load(open(out, encoding="utf-8")), p.stdout, apagadas


def test_e2e_el_json_trae_el_detalle_de_d45_y_lo_que_informa(e2e):
    """§4: siempre que P2 se calcule, el detalle del JSON trae neto, B, bloques de suma no nula, sumas de bloque,
    valores-p, método, p mínimo, semilla y sorteos, la regla, y lo de §3 (D-34 con su intervalo, D-42 entera)."""
    res, out, apagadas = e2e
    assert apagadas >= 10, "sin poder: sólo %d publicaciones de K apagadas en D" % apagadas
    assert res["controles_ok"] is True and all(res["cableado"].values()), (res["controles_ok"], res["cableado"])
    for regla in ("original", "SN"):
        for s in ("VIIRS375", "VIIRS750"):
            i = res["por_regla"][regla]["info"]["P2|%s" % s]
            for campo in CAMPOS_D45 + CAMPOS_INFORMA:
                assert campo in i, (regla, s, campo)
            assert "D-45" in i["regla"], i["regla"]
            assert i["neto"] == sum(i["sumas_bloque"]) and i["B"] == len(i["sumas_bloque"]), i
            assert i["bloques_suma_no_nula"] == sum(1 for x in i["sumas_bloque"] if x != 0), i
            assert i["metodo"] == ("exacto" if i["B"] <= MAX_B_EXACTO else "sorteos"), i


def test_e2e_el_veredicto_sale_de_los_valores_p_del_detalle(e2e):
    """El veredicto de cada sensor y regla es el que dan, con §2.6 y §2.7, los campos que el mismo JSON informa (las
    fracciones, en enteros). Y VIIRS 375 tiene sustrato: hay al menos un P2 que se calcula con B >= 5."""
    res, out, apagadas = e2e
    con_sustrato = 0
    for regla in ("original", "SN"):
        for s in ("VIIRS375", "VIIRS750"):
            i = res["por_regla"][regla]["info"]["P2|%s" % s]
            v = res["por_regla"][regla]["veredicto"]["P2|%s" % s]
            for campo in ("B", "neto", "p_gana_fraccion", "p_pierde_fraccion"):
                assert campo in i, (regla, s, campo)
            g, p = i["p_gana_fraccion"], i["p_pierde_fraccion"]
            if i["B"] <= MAX_B_SIN_SUSTRATO:
                esperado = "SIN SUSTRATO"
            elif i["neto"] < 0 and 20 * g[0] <= g[1]:
                esperado = "GANA"
            elif i["neto"] > 0 and 20 * p[0] <= p[1]:
                esperado = "PIERDE"
            else:
                esperado = "BLOQUEA" if i["neto"] > 0 else "EMPATE"
            con_sustrato += i["B"] > MAX_B_SIN_SUSTRATO
            assert v == esperado, (regla, s, v, esperado, i)
    assert con_sustrato >= 2, "sin poder: P2 no se calculó con sustrato en ningún sensor"
    linea = [l for l in out.splitlines() if l.strip().startswith("P2 VIIRS375")]
    assert linea and all("D-45" in l for l in linea), linea
