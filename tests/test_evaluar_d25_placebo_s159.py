"""S159, tarea I2: el evaluador del A/B de D25 (experiments/_s157_prereg_d25/evaluar_d25.py).

POR QUE. (1) El evaluador dejaba por defecto la calibración original de M y decía que la simétrica «requiere el
sello», pero el sello existe: ADENDA_CALIBRACION.md, l. 3 a 8 (D-27, Nicolás, 2026-10-20) dice que rige la simétrica
con la opción A y que «El evaluador corre con `--calibracion simetrica`» (VB-2 de AUDIT_S158_R2). Un despacho que
olvidara el argumento evaluaba con una regla ya reemplazada. (2) La segunda ronda midió que un brazo placebo que sólo
multiplica la magnitud de K por 1,2 da MEJORA bajo la calibración simétrica (R2-8): como K queda bajo MIROVA (razón
~0,67 en VIIRS 375), cualquier ganancia acerca. (3) Con el placebo como COMPUERTA, D25 salía INVALIDO haga lo que
haga; Nicolás selló el 2026-10-21 (D-28, ADENDA_PLACEBO.md, commit 2629f5a16) el placebo como COMPARADOR: MEJORA sólo
si D queda más cerca de MIROVA que K×ĝ, con ĝ la mediana de D/K del estrato (en log10). Estas pruebas son los
controles del §3 de esa adenda: (i) D = K×1,2 y D = K×0,8 no pueden dar MEJORA (d′ idénticamente 0); (ii) el brazo a
mitad de camino hacia MIROVA sigue dando MEJORA con al menos dos volcanes; (iii) K×0,8 sigue dando EMPEORA por d;
(iv) si d da MEJORA y d′ no, el estrato queda NEUTRO con la nota de la adenda; (v) la compuerta ya no vuelve
INVALIDO ningún veredicto.

Las pruebas que comprueban el comparador fallan primero por ASERCIÓN (S152: una prueba que cae por KeyError o
AttributeError no cuenta), por eso cada una pregunta antes si el dato existe.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

import numpy as np
import pytest

RAIZ = Path(__file__).parent.parent
# D25_EVALUADOR_DIR sólo lo usa el corredor de mutaciones (experiments/_s159/instrumentos/mutar_comparador.py),
# que deja una copia mutada del evaluador en otra carpeta de experiments/.
DIR = Path(os.environ.get("D25_EVALUADOR_DIR") or (RAIZ / "experiments" / "_s157_prereg_d25"))
sys.path.insert(0, str(DIR))
_spec = importlib.util.spec_from_file_location("evaluar_d25_s159", DIR / "evaluar_d25.py")
X = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(X)

E750 = "VIIRS750|z<=40"
NOTA_D28 = "sube en promedio, no en los pares correctos"


def _pares(razon, vols=("Lascar", "Isluga", "Tupungatito"), noches=12, por_noche=2, ruido=0.03, semilla=1):
    """Pares de un estrato: K = razon × MIROVA con ruido lognormal; el brazo D igual a K (nulo)."""
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


def _con_ganancia(P, g):
    return [dict(p, d=p["k"] * g) for p in P]


def _ver_completo(m_estado):
    ver = {"P1|VIIRS375": "CUMPLE", "P1|VIIRS750": "CUMPLE", "P2|VIIRS375": "EMPATE", "P2|VIIRS750": "EMPATE",
           "P1b|VIIRS375": "SIN CRUCES", "P1b|VIIRS750": "SIN CRUCES"}
    for nom, modo in X.ESTRATOS:
        ver["M|%s" % nom] = m_estado.get(nom, "NEUTRO")
    return ver


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


def test_la_adenda_del_comparador_esta_sellada():
    texto = (DIR / "ADENDA_PLACEBO.md").read_text(encoding="utf-8")
    assert "SELLADA por Nicolás el 2026-10-21 (D-28)" in texto
    assert "Placebo como comparador y no como compuerta" in texto


# ---------------------------------------------------------------- D-28 §3 (i): un placebo no puede dar MEJORA

@pytest.mark.parametrize("razon,g", [(0.6, 1.2), (1.6, 0.8)])
def test_placebo_como_brazo_no_puede_dar_mejora(razon, g):
    """K bajo MIROVA con D = K×1,2 (o K sobre MIROVA con D = K×0,8): sin comparador la regla sellada lo aprueba;
    con el comparador d′ es idénticamente 0 y el estrato no puede dar MEJORA."""
    P = _con_ganancia(_pares(razon, ruido=0.3), g)
    ver, info = X.evaluar_m({E750: P}, ok_ctrl=True, modo_calib="simetrica")
    assert ver["M|%s" % E750] != "MEJORA", "un placebo K x %s dio MEJORA: el comparador no actúa" % g
    i = info["M|%s" % E750]
    assert i["regla"] == "MEJORA", "la prueba no tiene poder: sin comparador la regla sobre d no aprobaba el placebo"
    assert "dprima_max_abs" in i, "el evaluador no informa d′"
    assert i["dprima_max_abs"] == 0.0, "d′ no es idénticamente 0 para una ganancia uniforme: %r" % i["dprima_max_abs"]
    assert i["regla_dprima"] == "NEUTRO"


# ---------------------------------------------------------------- D-28 §3 (ii): el control positivo sigue pasando

def test_mitad_de_camino_sigue_dando_mejora_con_dos_volcanes():
    """El brazo que lleva cada par a mitad de camino hacia MIROVA (en log) corrige más a los pares más lejos: no es una
    ganancia uniforme, y con dispersión real de K tiene que seguir dando MEJORA con al menos dos volcanes."""
    P = _pares(0.6, ruido=0.3)
    for p in P:
        p["d"] = p["k"] * (p["m"] / p["k"]) ** 0.5
    ver, info = X.evaluar_m({E750: P}, ok_ctrl=True, modo_calib="simetrica")
    i = info["M|%s" % E750]
    assert "regla_dprima" in i, "el comparador no se calculó"
    assert ver["M|%s" % E750] == "MEJORA", "el control positivo dejó de pasar: %s, d′ %s, nota %s" % (
        ver["M|%s" % E750], i["regla_dprima"], i["nota"])
    assert i["volcanes_con_d_negativa"] >= X.MIN_VOLCANES_MEJORA
    assert i["volcanes_con_dprima_negativa"] >= X.MIN_VOLCANES_MEJORA
    assert i["calibrada_dprima"]


# ---------------------------------------------------------------- D-28 §3 (iii): EMPEORA sigue sobre d

def test_k_por_08_sigue_dando_empeora_por_d():
    """K bajo MIROVA y D = K×0,8: d empeora; d′ es 0. EMPEORA se juzga sobre d (sello §2.4)."""
    P = _con_ganancia(_pares(0.6, ruido=0.3), 0.8)
    ver, info = X.evaluar_m({E750: P}, ok_ctrl=True, modo_calib="simetrica")
    i = info["M|%s" % E750]
    assert "regla_dprima" in i, "el comparador no se calculó"
    assert i["regla_dprima"] != "EMPEORA"          # d′ = 0: el comparador no ve el empeoramiento
    assert ver["M|%s" % E750] == "EMPEORA", "K x 0,8 dejó de dar EMPEORA: %s" % ver["M|%s" % E750]


# ---------------------------------------------------------------- D-28 §3 (iv): d MEJORA y d′ no -> NEUTRO con nota

def test_d_mejora_y_dprima_no_queda_neutro_con_la_nota():
    P = _con_ganancia(_pares(0.6, ruido=0.3), 1.2)
    ver, info = X.evaluar_m({E750: P}, ok_ctrl=True, modo_calib="simetrica")
    assert ver["M|%s" % E750] == "NEUTRO", ver["M|%s" % E750]
    assert NOTA_D28 in info["M|%s" % E750]["nota"], info["M|%s" % E750]["nota"]


def test_el_comparador_no_toca_un_estrato_que_solo_informa():
    """El §2 de D-28 rige para los estratos que deciden o bloquean; uno que informa sigue dando la regla sobre d."""
    P = _con_ganancia(_pares(0.6, vols=("Lastarria", "Villarrica", "Chaiten"), ruido=0.3), 1.2)
    ver, info = X.evaluar_m({"VIIRS375|kernel|z<=40": P}, ok_ctrl=True, modo_calib="simetrica")
    assert ver["M|VIIRS375|kernel|z<=40"] == info["M|VIIRS375|kernel|z<=40"]["regla"] == "MEJORA"


# ---------------------------------------------------------------- D-28 §3 (v): la compuerta se retiró

def test_la_compuerta_ya_no_invalida_y_el_placebo_se_sigue_informando():
    P = _pares(0.6, ruido=0.3)                     # D = K: el nulo
    ver, info = X.evaluar_m({E750: P}, ok_ctrl=True, modo_calib="simetrica")
    assert not any(str(v).startswith("INVALIDO") for v in ver.values()), "la compuerta sigue viva: %s" % ver
    estado, _, _ = X.global_ventana(dict(_ver_completo({}), **ver), True)
    assert not estado.startswith("INVALIDO"), estado
    # se sigue informando lo que la regla da sobre K×1,2 y K×0,8 sin comparador, y ĝ
    pl = info["M_placebo"][E750]
    assert pl["1.2"] == "MEJORA" and pl["0.8"] == "EMPEORA", pl
    assert "g_hat_factor" in info["M|%s" % E750], "no se informa ĝ"
    assert info["M|%s" % E750]["g_hat_factor"] == pytest.approx(1.0)


def test_global_ventana_no_tiene_compuerta():
    """Aunque llegue una marca de placebo vieja en el veredicto, la ventana no queda INVALIDO."""
    ver = _ver_completo({E750: "MEJORA"})
    ver["PLACEBO"] = "INVALIDO: placebo x1.2 da MEJORA en VIIRS750|z<=40"
    estado, mejora, _ = X.global_ventana(ver, True)
    assert estado == "MEJORA" and mejora, estado


def test_combinar_no_da_cumple_con_una_ventana_invalida(tmp_path):
    """Un JSON viejo (de antes de D-28) con una ventana INVALIDO sigue sin poder dar CUMPLE."""
    a, b = tmp_path / "v1.json", tmp_path / "v2.json"
    a.write_text(json.dumps({"ventana": "V1", "estado": "INVALIDO POR INSTRUMENTO (x) | sin el placebo: MEJORA",
                             "mejora": False, "empeora": False}), encoding="utf-8")
    b.write_text(json.dumps({"ventana": "V2", "estado": "MEJORA", "mejora": True, "empeora": False}), encoding="utf-8")
    assert X.combinar([str(a), str(b)]).startswith("INVALIDO POR INSTRUMENTO")


# ---------------------------------------------------------------- D-28 §2 y §3: cómo se calcula ĝ

def test_g_hat_por_estrato_y_por_volcan():
    """ĝ es uno por estrato (mediana de log10(D/K)) y se informa por volcán (no decide)."""
    P = _pares(0.6, ruido=0.3)
    gan = {"Lascar": 2.0, "Isluga": 1.5, "Tupungatito": 2.5}
    for p in P:
        p["d"] = p["k"] * gan[p["clave"].split("|")[0]]
    _, info = X.evaluar_m({E750: P}, ok_ctrl=True, modo_calib="simetrica")
    i = info["M|%s" % E750]
    assert "g_hat_por_volcan" in i, "no se informa ĝ por volcán"
    for v, g in gan.items():
        assert i["g_hat_por_volcan"][v]["factor"] == pytest.approx(g)
    assert i["g_hat_factor"] == pytest.approx(2.0)      # la mediana de las tres ganancias, una por par


def test_g_hat_se_recalcula_en_cada_replica():
    """§3: ĝ se recalcula en cada réplica del bootstrap con los mismos pesos por bloque; su intervalo no es un punto
    cuando D/K varía entre bloques."""
    P = _pares(0.6, ruido=0.3)
    rng = np.random.default_rng(3)
    for p in P:
        p["d"] = p["k"] * float(10 ** rng.normal(0.1, 0.1))
    _, info = X.evaluar_m({E750: P}, ok_ctrl=True, modo_calib="simetrica")
    i = info["M|%s" % E750]
    assert "g_hat_ic95" in i, "no se informa el intervalo de ĝ"
    lo, hi = i["g_hat_ic95"]
    assert lo < i["g_hat_log"] < hi


def test_medianas_por_fila_coinciden_con_medianas_ponderadas():
    assert hasattr(X, "medianas_ponderadas_filas"), "falta la mediana ponderada por fila (d′ cambia en cada réplica)"
    rng = np.random.default_rng(11)
    d = rng.normal(size=37)
    W = X.pesos_bloque([i // 3 for i in range(37)], n_boot=500, semilla=5)
    filas = np.repeat(d[None, :], 500, axis=0)
    assert np.array_equal(X.medianas_ponderadas_filas(filas, W), X.medianas_ponderadas(d, W))


# ---------------------------------------------------------------- D-30 (respuestas de Nicolás, 2026-10-21) y guardas
# ADENDA_PLACEBO.md §5. Cita textual de Nicolás: «Acepto tus recomendaciones para las cinco preguntas de la adenda D-28:
# INDECIDIBLE si falla la calibración de d′, sólo la cola de mejora en esa calibración, la lectura del caso sellada como
# el brazo a mitad de camino, el comparador apagado con --calibracion sellada, y los tres detalles numéricos.»
# Las guardas de opción A y calibración de d′ responden a H3 del verificador con contexto limpio
# (experiments/_s159/instrumentos/verificador_comparador/INFORME.md): tres mutaciones que ninguna prueba atrapaba.

def _mitad_de_camino():
    P = _pares(0.6, ruido=0.3)
    for p in P:
        p["d"] = p["k"] * (p["m"] / p["k"]) ** 0.5
    return P


def _calibracion_de_dprima_forzada(monkeypatch, f_mej, f_emp):
    """La calibración de d′ (y sólo ésa, la de semilla SEMILLA + 3) devuelve las tasas que se le pidan; la de d no se
    toca. Así se prueba qué hace la regla cuando la calibración de d′ falla sin depender de una semilla en el borde."""
    original = X.calibrar_simetrico

    def falsa(d, W, bloques, n_rep=X.N_CALIB, semilla=X.SEMILLA + 2):
        if semilla == X.SEMILLA + 3:
            return f_mej, f_emp, True
        return original(d, W, bloques, n_rep=n_rep, semilla=semilla)
    monkeypatch.setattr(X, "calibrar_simetrico", falsa)


def test_si_d_mejora_y_la_calibracion_de_dprima_falla_queda_indecidible(monkeypatch):
    """D-30, respuesta 1: si la calibración de d′ falla, no se sabe si hay MEJORA; como en D-27, el estrato no decide."""
    _calibracion_de_dprima_forzada(monkeypatch, f_mej=0.5, f_emp=0.0)
    ver, info = X.evaluar_m({E750: _mitad_de_camino()}, ok_ctrl=True, modo_calib="simetrica")
    assert ver["M|%s" % E750] == "INDECIDIBLE", "falla la calibración de d′ y el estrato da %s" % ver["M|%s" % E750]
    assert info["M|%s" % E750]["regla"] == "MEJORA", "sin poder: d no daba MEJORA"
    assert info["M|%s" % E750]["calibrada_dprima"] is False


def test_la_calibracion_de_dprima_solo_mira_la_cola_de_mejora(monkeypatch):
    """D-30, respuesta 2: d′ sólo se usa para MEJORA, así que la cola EMPEORA de su calibración no decide."""
    _calibracion_de_dprima_forzada(monkeypatch, f_mej=0.0, f_emp=0.5)
    ver, info = X.evaluar_m({E750: _mitad_de_camino()}, ok_ctrl=True, modo_calib="simetrica")
    assert "calibrada_dprima" in info["M|%s" % E750], "el comparador no se calculó"
    assert ver["M|%s" % E750] == "MEJORA", "la cola EMPEORA de d′ apagó la MEJORA: %s" % ver["M|%s" % E750]
    assert info["M|%s" % E750]["calibrada_dprima"] is True


def test_la_opcion_a_se_aplica_sobre_dprima_y_no_sobre_d():
    """Guarda (H3): Láscar va derecho a MIROVA (d′ negativa en todos sus pares) e Isluga y Tupungatito reciben
    exactamente la ganancia ĝ (d′ = 0). d da MEJORA en los tres volcanes y d′ da MEJORA en el intervalo, pero d′ es
    negativa en un solo volcán: la opción A sobre d′ tiene que dejarlo NEUTRO."""
    # 48 pares de Láscar contra 8 de cada otro: con 18 contra 6 el intervalo de d′ toca 0 y la prueba no tendría poder
    lascar = _pares(0.6, vols=("Lascar",), noches=24, ruido=0.3, semilla=2)
    otros = _pares(0.6, vols=("Isluga", "Tupungatito"), noches=4, ruido=0.3, semilla=3)
    c = float(np.median([np.log10(p["m"] / p["k"]) for p in lascar]))
    for p in lascar:
        p["d"] = p["m"]
    for p in otros:
        p["d"] = p["k"] * 10 ** c
    ver, info = X.evaluar_m({E750: lascar + otros}, ok_ctrl=True, modo_calib="simetrica")
    i = info["M|%s" % E750]
    assert "regla_dprima" in i, "el comparador no se calculó"
    assert i["regla"] == "MEJORA" and i["volcanes_con_d_negativa"] == 3, "sin poder: d no da MEJORA en los tres"
    assert i["regla_dprima"] == "MEJORA" and i["calibrada_dprima"], "sin poder: d′ no da MEJORA en el intervalo"
    assert i["volcanes_con_dprima_negativa"] == 1, "la opción A de d′ no cuenta con d′: %s" % i["volcanes_con_dprima_negativa"]
    assert ver["M|%s" % E750] == "NEUTRO", "MEJORA de d′ sostenida por un volcán: %s" % ver["M|%s" % E750]


def test_la_calibracion_de_dprima_usa_la_semilla_y_las_repeticiones_selladas():
    """D-32 (ADENDA_PLACEBO.md §5.3), cita textual de Nicolás: «Sí: sube las repeticiones de la calibración de d′ (por
    ejemplo a 1.000) y sella esa semilla y ese número antes del tag, para que una sola semilla no decida V2 VIIRS 750.»
    Con 200, la semilla fija dejaba V2 VIIRS 750 z<=40 en 11 falsos de 200 contra un tope de 10 (H2 del verificador)."""
    assert hasattr(X, "N_CALIB_DPRIMA"), "el número de repeticiones de la calibración de d′ no es una constante"
    assert X.N_CALIB_DPRIMA == 1000, "repeticiones de d′ %s, sellado 1.000 (D-32)" % X.N_CALIB_DPRIMA
    assert X.SEMILLA_CALIB_DPRIMA == 160 == X.SEMILLA + 3, "semilla de d′ %s, sellada 160 (D-32)" % X.SEMILLA_CALIB_DPRIMA
    assert round(X.MAX_FALSOS_CALIB * X.N_CALIB_DPRIMA) == 50, "el tope por cola no es el 5 % de 1.000"


def test_un_veredicto_con_la_calibracion_sellada_no_vale_para_decidir(tmp_path):
    """D-30, respuesta 4: con --calibracion sellada el comparador no se aplica, así que ese veredicto no vale para
    decidir y el JSON lo dice; combinar lo arrastra."""
    assert hasattr(X, "validez_calibracion"), "falta la marca de validez del veredicto"
    assert X.validez_calibracion("sellada")["vale_para_decidir"] is False
    assert X.validez_calibracion("simetrica")["vale_para_decidir"] is True
    a, b = tmp_path / "v1.json", tmp_path / "v2.json"
    for f, v in ((a, "V1"), (b, "V2")):
        f.write_text(json.dumps(dict({"ventana": v, "estado": "MEJORA", "mejora": True, "empeora": False},
                                     **X.validez_calibracion("sellada"))), encoding="utf-8")
    final = X.combinar([str(a), str(b)])
    assert "NO VALE PARA DECIDIR" in final, final
