"""S160, D-42: calibración de P2 del A/B de D25 y candados de V34-03 (experiments/_s157_prereg_d25/ADENDA_CALIBRACION_P2.md).

POR QUE. La regla de P2 de D-34 (ADENDA_GEMELO.md §5) decide con un intervalo al 95 % por bloques noche-volcán, pero
sin calibrar. El verificador con contexto limpio de D-34 (experiments/_s159/instrumentos/verificador_d34/INFORME.md,
V34-01) midió que con pocas noches decide en falso muy por encima del 5 %: con 3 noches discordantes de signo común por
noche, 24,8 % de los nulos; el mecanismo es que con B noches del mismo lado (probabilidad 2^(1-B)) ningún remuestreo de
bloques puede cruzar 0. Nicolás selló el 2026-10-22 (D-42): «Sí a D-42 opción (a): calibra P2 como M en una cuarta
adenda sellada, con los candados de V34-03 y V29-01 y verificador limpio antes del tag.»

La regla nueva (adenda §2): se sortea el signo de cada BLOQUE noche-volcán entero (1.000 sorteos, semilla 161 =
SEMILLA + 4), a cada sorteo se le aplica la misma regla de D-34 (intervalo con pesos_bloque, 10.000 remuestreos,
semilla 157), y si los falsos GANA o los falsos PIERDE pasan del 5 % (50 de 1.000, cada cola por separado), P2 de ese
sensor queda INDECIDIBLE, informando al lado el resultado sin calibrar. BLOQUEA no se calibra: se informa su fracción.

Más los candados de V34-03 que caen sobre P2 y el comparador: semilla y remuestreos del intervalo, nivel del 95 %, borde
de PIERDE, tope del 5 % de d′ en la comparación e INDECIDIBLE por d′ sólo cuando d da MEJORA. Y el estrato informativo
del hallazgo 203 (NOTA_ESTRATO_203.md, 5f986a209), que se cuenta y no decide.

Las pruebas fallan primero por ASERCIÓN (S152, S156), por eso preguntan antes si el nombre existe.

S161 (D-45, experiments/_s157_prereg_d25/ADENDA_SIGNOS_P2.md): P2 se decide con la prueba de signos por bloque y
D-42 deja de decidir y se informa (§3). Las pruebas de aquí que sólo miraban la DECISIÓN de D-42 se re-apuntaron al
campo que ahora la informa (`resultado_d42`) y fijan aparte lo que decide D-45; la lista, una por una, en
experiments/_s159/instrumentos/signos_p2/README.md. Las que miran la calibración misma (semilla, sorteos, oráculo,
tope en el campo `calibrada`) no cambian: siguen vigilando lo que se informa.
"""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import numpy as np
import pytest

RAIZ = Path(__file__).parent.parent
DIR = Path(os.environ.get("D25_EVALUADOR_DIR") or (RAIZ / "experiments" / "_s157_prereg_d25"))
sys.path.insert(0, str(DIR))
_spec = importlib.util.spec_from_file_location("evaluar_d25_calib_p2_s160", DIR / "evaluar_d25.py")
X = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(X)

# Los números sellados, escritos aquí como literales a propósito: la prueba no los lee del evaluador.
SEMILLA_INTERVALO, N_REMUESTREOS = 157, 10000            # ADENDA_GEMELO.md §5.3
SEMILLA_CALIB, N_SORTEOS, TOPE_POR_COLA = 161, 1000, 50  # ADENDA_CALIBRACION_P2.md §2.3 y §2.4 (50 de 1.000)
E750 = "VIIRS750|z<=40"
CAMPOS_CALIB = ("calibrada", "falsos_gana", "falsos_pierde", "falsos_bloquea", "n_sorteos", "semilla_calibracion",
                "resultado_sin_calibrar")


def _tiene(nombre):
    assert hasattr(X, nombre), "falta %s (D-42)" % nombre


def _contrib(por_noche, vol="Lascar", sensor="VIIRS375", mes="09"):
    """por_noche: lista de listas de contribuciones (+1 = error que sólo comete D, -1 = error que sólo comete K)."""
    out = []
    for n, cs in enumerate(por_noche):
        for j, c in enumerate(cs):
            out.append({"clave": "%s|%s|2026-%s-%02d 05:%02d" % (vol, sensor, mes, n + 1, j), "c": c,
                        "bloque": "%s|2026-%s-%02d" % (vol, mes, n + 1)})
    return out


# Mezcla de 15 noches de tamaños distintos y signos mezclados (27 pasadas, neto -9): intervalo [-19, 1], EMPATE. Con
# percentiles 5 y 95 da [-17, -1] (GANA) y con 1.000 remuestreos [-18, 2]: los dos números se distinguen aquí.
MEZCLA = [[-1, -1, +1], [-1], [+1, +1], [-1, -1], [-1], [+1], [-1, -1, -1], [+1, -1], [-1], [-1, +1, -1], [+1],
          [-1, -1], [+1, +1, -1], [-1], [-1]]


def _oraculo(contrib):
    """La calibración de la adenda §2 escrita aparte, con los números sellados como literales: signo sorteado por
    bloque (un +1 o -1 por noche-volcán, aplicado a todas sus pasadas), la regla de D-34 sobre cada sorteo."""
    c = np.array([x["c"] for x in contrib], dtype=np.float64)
    bl = [x["bloque"] for x in contrib]
    uniq = sorted(set(bl))
    idx = np.array([uniq.index(b) for b in bl])
    W = X.pesos_bloque(bl, n_boot=N_REMUESTREOS, semilla=SEMILLA_INTERVALO).astype(np.float64)
    rng = np.random.default_rng(SEMILLA_CALIB)
    n = {"GANA": 0, "PIERDE": 0, "BLOQUEA": 0, "EMPATE": 0}
    for _ in range(N_SORTEOS):
        cc = c * rng.choice((-1.0, 1.0), size=len(uniq))[idx]
        s = W @ cc
        lo, hi = np.percentile(s, 2.5), np.percentile(s, 97.5)
        n["GANA" if hi < 0 else "PIERDE" if lo > 0 else "BLOQUEA" if round(cc.sum()) > 0 else "EMPATE"] += 1
    return n


def _calibracion_forzada(monkeypatch, f_gana, f_pierde, f_bloquea=0.0):
    """La calibración de P2 devuelve las tasas pedidas: prueba qué hace la regla en el borde sin depender de una semilla."""
    _tiene("calibrar_p2")
    monkeypatch.setattr(X, "calibrar_p2", lambda *a, **k: (f_gana, f_pierde, f_bloquea, N_SORTEOS, SEMILLA_CALIB))


# ---------------------------------------------------------------- la calibración (adenda §2)

def test_los_numeros_de_la_calibracion_son_los_sellados():
    _tiene("SEMILLA_CALIB_P2")
    _tiene("N_CALIB_P2")
    assert X.SEMILLA_CALIB_P2 == SEMILLA_CALIB == X.SEMILLA + 4, "semilla de la calibración de P2 %s" % X.SEMILLA_CALIB_P2
    assert X.N_CALIB_P2 == N_SORTEOS, "sorteos de la calibración de P2 %s" % X.N_CALIB_P2
    assert round(X.MAX_FALSOS_CALIB * N_SORTEOS) == TOPE_POR_COLA


def test_la_calibracion_reproduce_el_oraculo_con_los_numeros_sellados():
    """Fija semilla, número de sorteos, sorteo por bloque y la regla aplicada a cada sorteo a la vez: el detalle de P2
    trae las mismas tres fracciones que el oráculo escrito aparte con los literales de la adenda."""
    _tiene("calibrar_p2")
    c = _contrib(MEZCLA)
    n = _oraculo(c)
    v, det = X.decidir_p2_bloques(c, ok_ctrl=True)
    for campo in CAMPOS_CALIB:
        assert campo in det, "el detalle de P2 no trae %s (adenda §2.7)" % campo
    assert det["n_sorteos"] == N_SORTEOS and det["semilla_calibracion"] == SEMILLA_CALIB, det
    assert (det["falsos_gana"], det["falsos_pierde"], det["falsos_bloquea"]) == (
        n["GANA"] / N_SORTEOS, n["PIERDE"] / N_SORTEOS, n["BLOQUEA"] / N_SORTEOS), (det, n)
    # poder de la prueba: el oráculo no da cero en las colas (si diera cero, una mutación del sorteo podría no verse)
    assert n["GANA"] > 0 and n["PIERDE"] > 0 and n["BLOQUEA"] > 0, n


def test_el_sorteo_es_por_bloque_y_no_por_pasada():
    """Tres noches de cuatro pasadas, todas con error sólo de D: sin calibrar, PIERDE. Con el signo sorteado por noche,
    las tres caen del mismo lado en 1 de cada 4 sorteos (12,5 % por cola): la calibración falla y queda INDECIDIBLE.
    Sorteando por pasada, una noche casi nunca queda entera de un lado y la regla saldría «calibrada» (S156: V34-01).
    S161 (D-45, ADENDA_SIGNOS_P2.md §3 y §5): D-42 dejó de decidir y se informa en `resultado_d42`; esta prueba se
    re-apuntó a ese campo y fija aparte lo que decide D-45. Con 3 noches D-45 da SIN SUSTRATO (B <= 4)."""
    _tiene("calibrar_p2")
    v, det = X.decidir_p2_bloques(_contrib([[+1] * 4] * 3), ok_ctrl=True)
    assert det.get("resultado_sin_calibrar") == "PIERDE", det
    # S161: preguntar antes de comparar, para que un falso que deja de informarse (None) falle por aserción y no por
    # TypeError (mutación s12c de experiments/_s159/instrumentos/signos_p2/mutar_signos_p2.py)
    assert det.get("falsos_gana") is not None and det.get("falsos_pierde") is not None, det
    assert det["falsos_gana"] > 0.10 and det["falsos_pierde"] > 0.10, det
    assert det["calibrada"] is False, det
    assert det.get("resultado_d42") == "INDECIDIBLE", det
    assert v == "SIN SUSTRATO", (v, det)


@pytest.mark.parametrize("f_gana,f_pierde,calibrada", [
    (0.05, 0.05, True),      # en el tope: 50 de 1.000 por cola es calibrada
    (0.051, 0.0, False),     # una sola cola pasada basta
    (0.0, 0.051, False),     # la otra cola sola también basta
    (0.06, 0.0, False),      # tope del 5 %, no del 10 %
    (0.0, 0.08, False),
])
def test_el_tope_es_5_por_ciento_en_cada_cola(monkeypatch, f_gana, f_pierde, calibrada):
    """S161 (D-45, ADENDA_SIGNOS_P2.md §3 y §5): D-42 dejó de decidir y se informa en `resultado_d42`; esta prueba se
    re-apuntó a ese campo y fija aparte lo que decide D-45. Con 12 noches de -1 D-45 da GANA (p = 1/4096),
    calibre o no D-42."""
    _calibracion_forzada(monkeypatch, f_gana, f_pierde)
    v, det = X.decidir_p2_bloques(_contrib([[-1]] * 12), ok_ctrl=True)
    assert det.get("resultado_sin_calibrar") == "GANA", det
    assert det["calibrada"] is calibrada, det
    assert det.get("resultado_d42") == ("GANA" if calibrada else "INDECIDIBLE"), det
    assert v == "GANA", (v, det)


@pytest.mark.parametrize("por_noche,sin_calibrar", [
    ([[-1]] * 12, "GANA"),
    ([[+1]] * 12, "PIERDE"),
    ([[+1]] * 6 + [[-1]] * 4, "BLOQUEA"),
    ([[+1]] * 4 + [[-1]] * 6, "EMPATE"),
])
def test_si_la_calibracion_falla_queda_indecidible_sea_cual_sea_el_resultado(monkeypatch, por_noche, sin_calibrar):
    """Adenda §2.5: «P2 de ese sensor queda INDECIDIBLE, sea cual sea su resultado sin calibrar, que se informa al lado».
    Un PIERDE sin calibrar tampoco cuenta.
    S161 (D-45, ADENDA_SIGNOS_P2.md §3 y §5): D-42 dejó de decidir y se informa en `resultado_d42`; esta prueba se
    re-apuntó a ese campo y fija aparte lo que decide D-45. En estos cuatro conjuntos D-45 da lo mismo que D-34
    sin calibrar
    (12 noches: p = 1/4096; 6 contra 4 con neto 2: p de PIERDE 386/1024, BLOQUEA; 4 contra 6: EMPATE)."""
    _calibracion_forzada(monkeypatch, 0.5, 0.5)
    v, det = X.decidir_p2_bloques(_contrib(por_noche), ok_ctrl=True)
    assert det.get("resultado_sin_calibrar") == sin_calibrar, det
    assert det.get("resultado_d42") == "INDECIDIBLE", det
    assert v == sin_calibrar, (v, det)
    assert det["calibrada"] is False


def test_bloquea_no_se_calibra_y_su_fraccion_se_informa(monkeypatch):
    """Adenda §2.6: con la calibración OK, BLOQUEA sigue como está aunque bajo el nulo bloquee en muchos sorteos."""
    _calibracion_forzada(monkeypatch, 0.0, 0.0, f_bloquea=0.9)
    v, det = X.decidir_p2_bloques(_contrib([[+1]] * 6 + [[-1]] * 4), ok_ctrl=True)
    assert v == "BLOQUEA", (v, det)
    assert det.get("resultado_d42") == "BLOQUEA", det          # S161: lo que D-42 habría dado se informa (D-45 §3)
    assert det["falsos_bloquea"] == 0.9 and det["calibrada"] is True, det


def test_sin_sustrato_y_controles_caidos_no_se_calibran_pero_informan():
    """Adenda §2: la calibración va después del SIN SUSTRATO y sólo con los controles OK; §2.7: se informa siempre."""
    _tiene("calibrar_p2")
    for c, ok, esperado in ((_contrib([[+1]] * 4), True, "SIN SUSTRATO"), (_contrib([[-1]] * 12), False, "INDECIDIBLE")):
        v, det = X.decidir_p2_bloques(c, ok_ctrl=ok)
        assert v == esperado, (v, det)
        for campo in CAMPOS_CALIB:
            assert campo in det, "sin %s en el detalle cuando P2 da %s" % (campo, esperado)
        assert det["calibrada"] is None and det["falsos_gana"] is None, det
        assert det["n_sorteos"] is None and det["semilla_calibracion"] is None, "sin calibración no hubo sorteos: %s" % det
        assert det["resultado_sin_calibrar"] == esperado, det


def test_el_detalle_dice_los_sorteos_y_la_semilla_que_la_calibracion_uso(monkeypatch):
    """V42-04 (verificador de D-42): n_sorteos y semilla_calibracion tienen que salir de lo que calibrar_p2 usó, no de
    las constantes; si no, una llamada con otros números seguiría declarando 1.000 y 161 (A116)."""
    _tiene("calibrar_p2")
    original = X.calibrar_p2

    def otra(c, bloques, W, n_rep=None, semilla=None):
        return original(c, bloques, W, n_rep=20, semilla=7)
    monkeypatch.setattr(X, "calibrar_p2", otra)
    v, det = X.decidir_p2_bloques(_contrib(MEZCLA), ok_ctrl=True)
    assert (det["n_sorteos"], det["semilla_calibracion"]) == (20, 7), det


def _armar_p2_tres_noches():
    """Tres noches de Láscar en VIIRS 375 con cuatro pasadas cada una en que D publica un negativo limpio y K no: doce
    errores sólo de D. Sin calibrar es PIERDE (todas las noches del mismo lado); calibrada, las tres noches caen del
    mismo lado en 1 de cada 4 sorteos y la calibración falla: INDECIDIBLE."""
    def fila(pub, lab, disp=0.0):
        return {"pub": pub, "lab": lab, "disp": disp, "vrp_ref": None, "z": 20.0, "plataforma": "NOAA20",
                "pc_lat": None, "pc_lon": None}
    T, R = {}, {"K": {}, "D": {}}
    for n in range(3):
        for j in range(4):
            k = "Lascar|VIIRS375|2026-09-%02d 05:%02d" % (n + 1, 10 * j)
            T[k] = {"control": fila(False, "neg_limpio"), "brazo": fila(True, "neg_limpio", 0.3)}
            R["K"][k], R["D"][k] = {"pc_vrp": 0.0, "dc": "summit"}, {"pc_vrp": 0.3, "dc": "summit"}
    prot = {k: {"A": False, "B": False, "alerta_solo_ocr": False} for k in T}
    cfg = {"brazos": ("K", "D"), "solo_tabla": True, "desde": "2026-09-01", "hasta": "2026-09-30"}
    res_ctrl = {"controles_ok": True, "cableado": {"K": True, "D": True}}
    return {("K", "D"): T}, prot, R, cfg, res_ctrl


def test_contar_publica_el_veredicto_calibrado_y_no_el_sin_calibrar():
    """V42-02 (verificador de D-42, su m07): la calibración decide en un solo punto, el valor que contar escribe en
    ver["P2|sensor"], que es lo que lee global_ventana. Si contar escribiera el resultado sin calibrar, D-42 quedaría
    sin efecto; esta prueba lo mira en contar y en la ventana, no en decidir_p2_bloques aislada.
    S161 (D-45, ADENDA_SIGNOS_P2.md §3 y §5): D-42 dejó de decidir y se informa en `resultado_d42`; esta prueba se
    re-apuntó a ese campo y fija aparte lo que decide D-45. Con 3 noches D-45 da SIN SUSTRATO, así que contar
    publica SIN SUSTRATO (no el INDECIDIBLE de D-42) y la ventana no queda INDECIDIBLE por P2. El candado de V42-02 para
    la regla nueva (contar publica D-45 y no D-34 ni D-42) está en tests/test_evaluar_d25_signos_p2_s161.py."""
    _tiene("calibrar_p2")
    T, prot, R, cfg, res_ctrl = _armar_p2_tres_noches()
    ver, info = X.contar(T, prot, R, cfg, "SN", res_ctrl, None, {"Lascar": 5.0})
    i = info["P2|VIIRS375"]
    assert i.get("resultado_sin_calibrar") == "PIERDE" and i.get("calibrada") is False, "sin poder: %s" % i
    assert i.get("resultado_d42") == "INDECIDIBLE", i
    assert ver["P2|VIIRS375"] == "SIN SUSTRATO", "contar publica %s" % ver["P2|VIIRS375"]
    estado = X.global_ventana(_completar(ver), True)[0]
    assert not estado.startswith("INDECIDIBLE"), estado


def test_con_muchas_noches_la_calibracion_pasa_y_decide():
    """Control de poder: un efecto repartido en 12 noches sigue decidiendo (la calibración no lo apaga)."""
    _tiene("calibrar_p2")
    for por_noche, esperado in (([[-1]] * 12, "GANA"), ([[+1]] * 12, "PIERDE")):
        v, det = X.decidir_p2_bloques(_contrib(por_noche), ok_ctrl=True)
        assert det.get("calibrada") is True, det
        assert det.get("resultado_d42") == esperado, det     # S161: D-42 informa (D-45 §3)
        assert v == esperado, (v, det)


def test_global_ventana_con_p2_indecidible():
    """Adenda §2.5: como hoy con un M INDECIDIBLE, la ventana queda INDECIDIBLE, salvo un VETADO de P1, que manda antes."""
    _tiene("calibrar_p2")
    ver = {"P1|VIIRS375": "CUMPLE", "P1|VIIRS750": "CUMPLE", "P2|VIIRS375": "INDECIDIBLE", "P2|VIIRS750": "EMPATE",
           "P1b|VIIRS375": "SIN CRUCES", "P1b|VIIRS750": "SIN CRUCES"}
    for nom, modo in X.ESTRATOS:
        ver["M|%s" % nom] = "MEJORA" if nom == E750 else "NEUTRO"
    assert X.global_ventana(ver, True)[0] == "INDECIDIBLE"
    assert X.global_ventana(dict(ver, **{"P1|VIIRS750": "VETADO"}), True)[0].startswith("NO CUMPLE (veto)")


def test_lectura_pendiente_p2_indecidible_en_un_sensor_y_pierde_calibrado_en_el_otro():
    """NO es regla sellada: documenta lo que hace hoy global_ventana, sin cambio (PIERDE se mira antes que INDECIDIBLE,
    H2 de ADENDA_CALIBRACION.md §4). La adenda D-42 §2.5 dice «Como hoy con un M INDECIDIBLE» y también «salvo un
    VETADO de P1»; en este caso cruzado las dos frases no dicen lo mismo. Pregunta abierta para Nicolás (README de
    experiments/_s159/instrumentos/calib_p2/)."""
    _tiene("calibrar_p2")
    ver = {"P1|VIIRS375": "CUMPLE", "P1|VIIRS750": "CUMPLE", "P2|VIIRS375": "INDECIDIBLE", "P2|VIIRS750": "PIERDE",
           "P1b|VIIRS375": "SIN CRUCES", "P1b|VIIRS750": "SIN CRUCES"}
    for nom, modo in X.ESTRATOS:
        ver["M|%s" % nom] = "NEUTRO"
    assert X.global_ventana(ver, True)[0] == "NO CUMPLE (suma de errores)"


# ---------------------------------------------------------------- V34-03: el intervalo de P2

def test_el_intervalo_de_p2_usa_la_semilla_y_los_remuestreos_sellados(monkeypatch):
    """V34-03 (m05, m06): toda matriz de pesos que arma P2 sale de 10.000 remuestreos con la semilla 157 (la de M)."""
    _tiene("calibrar_p2")
    llamadas = []
    original = X.pesos_bloque

    def espia(bloques, n_boot=X.N_BOOT, semilla=X.SEMILLA):
        llamadas.append((n_boot, semilla))
        return original(bloques, n_boot, semilla)
    monkeypatch.setattr(X, "pesos_bloque", espia)
    X.decidir_p2_bloques(_contrib(MEZCLA), ok_ctrl=True)
    assert llamadas, "P2 no armó ninguna matriz de pesos por bloques"
    assert set(llamadas) == {(N_REMUESTREOS, SEMILLA_INTERVALO)}, llamadas


def test_el_intervalo_de_p2_es_el_95_por_ciento_exacto():
    """V34-03 (m05, m06, m15): el ic95 informado es el par de percentiles 2,5 y 97,5 de las sumas con los pesos
    sellados, calculado aquí aparte. Con percentiles 5 y 95 este conjunto da [-17, -1]; con 1.000 remuestreos, [-18, 2]."""
    c = _contrib(MEZCLA)
    cv = np.array([x["c"] for x in c], dtype=np.float64)
    W = X.pesos_bloque([x["bloque"] for x in c], n_boot=N_REMUESTREOS, semilla=SEMILLA_INTERVALO)
    s = W @ cv
    v, det = X.decidir_p2_bloques(c, ok_ctrl=True)
    assert det["ic95"] == [float(np.percentile(s, 2.5)), float(np.percentile(s, 97.5))] == [-19.0, 1.0], det
    assert det.get("resultado_sin_calibrar", v) == "EMPATE", det


@pytest.mark.parametrize("lado", ["PIERDE", "GANA"])
def test_los_bordes_del_intervalo_son_estrictos(lado):
    """V34-03 (m08) y D-34 §5.4: PIERDE exige el intervalo ENTERO sobre 0 (lo > 0), GANA entero bajo 0 (hi < 0). Un
    intervalo que toca 0 no decide; con el neto en contra de D, BLOQUEA."""
    _tiene("regla_p2")
    if lado == "PIERDE":
        sumas = np.array([0.0] * 300 + [3.0] * 9700)       # percentil 2,5 = 0 exacto
        v, lo, hi = X.regla_p2(sumas, 3)
        assert lo == 0.0 and v == "BLOQUEA", (v, lo, hi)
    else:
        sumas = np.array([-3.0] * 9700 + [0.0] * 300)      # percentil 97,5 = 0 exacto
        v, lo, hi = X.regla_p2(sumas, -3)
        assert hi == 0.0 and v == "EMPATE", (v, lo, hi)


# ---------------------------------------------------------------- V34-03: el comparador de M (D-30, D-32)

def _pares(razon, vols=("Lascar", "Isluga", "Tupungatito"), noches=12, por_noche=2, ruido=0.3, semilla=1):
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


def _mitad_de_camino():
    P = _pares(0.6)
    for p in P:
        p["d"] = p["k"] * (p["m"] / p["k"]) ** 0.5
    return P


def _calib_dprima_forzada(monkeypatch, f_mej, f_emp):
    original = X.calibrar_simetrico

    def falsa(d, W, bloques, n_rep=X.N_CALIB, semilla=X.SEMILLA + 2):
        if semilla == X.SEMILLA + 3:
            return f_mej, f_emp, True
        return original(d, W, bloques, n_rep=n_rep, semilla=semilla)
    monkeypatch.setattr(X, "calibrar_simetrico", falsa)


@pytest.mark.parametrize("f_mej,esperado", [(0.05, "MEJORA"), (0.051, "INDECIDIBLE"), (0.06, "INDECIDIBLE"),
                                            (0.09, "INDECIDIBLE")])
def test_el_tope_de_la_calibracion_de_dprima_es_el_5_por_ciento(monkeypatch, f_mej, esperado):
    """V34-03 (m16): la prueba de D-32 fija la constante, no la comparación. Aquí la comparación misma, en el borde."""
    _calib_dprima_forzada(monkeypatch, f_mej, 0.0)
    ver, info = X.evaluar_m({E750: _mitad_de_camino()}, ok_ctrl=True, modo_calib="simetrica")
    assert info["M|%s" % E750]["regla"] == "MEJORA", "sin poder: d no da MEJORA"
    assert ver["M|%s" % E750] == esperado, (f_mej, ver["M|%s" % E750])


def test_dprima_mal_calibrada_no_toca_un_estrato_donde_d_no_da_mejora(monkeypatch):
    """V34-03 (m22): ADENDA_PLACEBO.md §5.1 punto 1 manda INDECIDIBLE sólo «si d da MEJORA». Con D = K, d es NEUTRO y el
    estrato sigue NEUTRO aunque la calibración de d′ falle."""
    _calib_dprima_forzada(monkeypatch, 0.5, 0.5)
    ver, info = X.evaluar_m({E750: _pares(0.6)}, ok_ctrl=True, modo_calib="simetrica")
    i = info["M|%s" % E750]
    assert i["regla"] == "NEUTRO" and i.get("calibrada_dprima") is False, i
    assert ver["M|%s" % E750] == "NEUTRO", ver["M|%s" % E750]


# ---------------------------------------------------------------- estrato informativo del hallazgo 203

def _fila(pub, lab, disp=0.0, vrp_ref=None):
    return {"pub": pub, "lab": lab, "disp": disp, "vrp_ref": vrp_ref, "z": 20.0, "plataforma": "NOAA20",
            "pc_lat": None, "pc_lon": None}


def _armar_203(pc_vrp_k):
    """Seis noches de Isluga en VIIRS 750: cuatro alertas Muy Bajo que D publica y K no (D recupera), dos negativos
    limpios que D publica y K no (D enciende), y una pasada por noche que los dos publican igual. En las seis primeras
    el cúmulo de cumbre de K vale `pc_vrp_k` (0,0 las mete al estrato 203; 0,3 las deja fuera sin tocar la tabla)."""
    T, R = {}, {"K": {}, "D": {}}
    for n in range(6):
        k = "Isluga|VIIRS750|2026-09-%02d 05:10" % (n + 1)
        lab = "pos" if n < 4 else "neg_limpio"
        T[k] = {"control": _fila(False, lab, 0.0, 0.3 if lab == "pos" else None), "brazo": _fila(True, lab, 0.2, 0.3 if lab == "pos" else None)}
        R["K"][k] = {"pc_vrp": pc_vrp_k, "dc": "summit"}
        R["D"][k] = {"pc_vrp": 0.2, "dc": "summit"}
        k2 = "Isluga|VIIRS750|2026-09-%02d 06:40" % (n + 1)
        T[k2] = {"control": _fila(True, "neg_limpio", 0.1), "brazo": _fila(True, "neg_limpio", 0.1)}
        R["K"][k2], R["D"][k2] = {"pc_vrp": 0.1, "dc": "summit"}, {"pc_vrp": 0.1, "dc": "summit"}
    prot = {k: {"A": False, "B": False, "alerta_solo_ocr": False} for k in T}
    cfg = {"brazos": ("K", "D"), "solo_tabla": True, "desde": "2026-09-01", "hasta": "2026-09-30"}
    res_ctrl = {"controles_ok": True, "cableado": {"K": True, "D": True}}
    return {("K", "D"): T}, prot, R, cfg, res_ctrl


def test_el_estrato_203_se_cuenta():
    """Control positivo sintético (NOTA_ESTRATO_203.md, «Qué se informa»): las seis pasadas con cumbre de K en 0,0 MW
    entran a la tabla con su clase, y los totales dan 4 que D recupera, 2 que enciende y 0 sin cambio."""
    T, prot, R, cfg, res_ctrl = _armar_203(0.0)
    ver, info = X.contar(T, prot, R, cfg, "SN", res_ctrl, None, {"Isluga": 5.0})
    assert "estrato_203" in info, "contar no informa el estrato del hallazgo 203"
    e = info["estrato_203"]
    assert e["n"] == 6 and len(e["pasadas"]) == 6, e
    assert (e["recupera_D"], e["enciende_D"], e["no_cambia"]) == (4, 2, 0), e
    x = next(p for p in e["pasadas"] if p["hora"] == "2026-09-05 05:10")
    assert x == {"volcan": "Isluga", "hora": "2026-09-05 05:10", "clase_mirova": "negativo limpio", "vrp_mirova": None,
                 "publica_K": False, "publica_D": True, "pc_vrp_mw_K": 0.0, "pc_vrp_mw_D": 0.2, "error_p2_de": "D"}, x
    assert next(p for p in e["pasadas"] if p["hora"] == "2026-09-01 05:10")["error_p2_de"] == "K"


def test_el_estrato_203_no_decide():
    """El mismo conjunto con la cumbre de K en 0,3 MW queda fuera del estrato, y todos los veredictos son idénticos:
    la pertenencia al estrato 203 no entra a P1, P1b, P2 ni M (y global_ventana sólo lee `ver`)."""
    def correr(pc_vrp_k):
        T, prot, R, cfg, res_ctrl = _armar_203(pc_vrp_k)
        return X.contar(T, prot, R, cfg, "SN", res_ctrl, None, {"Isluga": 5.0})
    a, b = correr(0.0), correr(0.3)
    assert "estrato_203" in a[1] and a[1]["estrato_203"]["n"] == 6, "sin poder: el estrato no se contó"
    assert b[1]["estrato_203"]["n"] == 0, b[1]["estrato_203"]
    assert a[0] == b[0], "el estrato 203 cambió un veredicto: %s contra %s" % (a[0], b[0])
    assert not any("203" in k for k in a[0]), a[0]
    assert X.global_ventana(_completar(a[0]), True) == X.global_ventana(_completar(b[0]), True)


def _completar(ver):
    out = dict(ver)
    for s in X.SENS:
        out.setdefault("P1|%s" % s, "CUMPLE"); out.setdefault("P1b|%s" % s, "SIN CRUCES")
    return out


def test_el_estrato_203_es_solo_viirs_750_y_solo_cumbre():
    """VIIRS 375 no entra; un cúmulo de K en 0,0 con distance_class far no es de cumbre; uno ausente con summit sí."""
    T, prot, R, cfg, res_ctrl = _armar_203(0.0)
    TKD = T[("K", "D")]
    k375 = "Isluga|VIIRS375|2026-09-01 05:20"
    TKD[k375] = {"control": _fila(False, "neg_limpio"), "brazo": _fila(True, "neg_limpio", 0.2)}
    R["K"][k375], R["D"][k375] = {"pc_vrp": 0.0, "dc": "summit"}, {"pc_vrp": 0.2, "dc": "summit"}
    prot[k375] = {"A": False, "B": False, "alerta_solo_ocr": False}
    R["K"]["Isluga|VIIRS750|2026-09-01 05:10"] = {"pc_vrp": 0.0, "dc": "far"}
    R["K"]["Isluga|VIIRS750|2026-09-02 05:10"] = {"pc_vrp": None, "dc": "summit"}
    ver, info = X.contar(T, prot, R, cfg, "SN", res_ctrl, None, {"Isluga": 5.0})
    assert "estrato_203" in info, "contar no informa el estrato del hallazgo 203"
    horas = sorted(p["hora"] for p in info["estrato_203"]["pasadas"])
    assert "2026-09-01 05:10" not in horas and "2026-09-02 05:10" in horas and len(horas) == 5, horas
