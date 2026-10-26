# -*- coding: utf-8 -*-
"""Batería del evaluador del A/B diurno sobre K (PREREGISTRO.md de esta carpeta, §5 y §6).

POR QUÉ. La regla se escribió antes de ver datos; estas pruebas fijan que el evaluador hace lo que la regla dice en
cada rama (casos a a e del §6.2, el veredicto global del §6.3, la robustez del §6.4) y que cada compuerta de
instrumento (I1 a I6) puede fallar. Se escribieron ANTES del evaluador (salida roja en `probar_salida_roja.txt`) y
las mutaciones de `mutaciones.json` tienen que caer por una aserción de aquí (`mutaciones_salida.txt`).

Escenarios sintéticos: pasadas de MIROVA y records armados a mano, con la publicación ya dada (sin node). Láscar:
noche a las 05:00 UTC, día a las 17:00 UTC (elevación solar positiva todo el año a esa hora).

Correr: python -m pytest -q -p no:cacheprovider experiments/_s163_diurno_k/test_evaluar_diurno_k.py
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
for p in (str(ROOT), str(ROOT / "scripts"), str(AQUI)):
    if p not in sys.path:
        sys.path.insert(0, p)

import clase_mirova as cm  # noqa: E402
import evaluar_diurno_k as ev  # noqa: E402

SHA = "a" * 40
C, B = "ctrl", "diurno"
V375, V750 = "VIIRS375", "VIIRS750"
VOLS = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan", "Copahue", "Llaima",
        "Villarrica", "PuyehueCordonCaulle", "Chaiten"]
VENT = [("WT", "2026-08-01", "2026-08-31")]
P_SUP = {V375: 0.0011, V750: 0.0059}


def t(dia, hora):
    return datetime(2026, 8, dia, hora, 0)


def pas(vol, sensor, instante, estado, vrp=None, fuente="CONS"):
    return cm.PasadaMirova(vol, sensor, instante, estado, vrp, None, fuente, fuente != "CONS", False, (), False)


def rec(vol, b, instante, pub=False, disp=0.0, t1=False, fuente="eruption", sha=SHA, diag=None):
    r = {"vol": vol, "b": b, "dt": instante, "pub": pub, "disp": disp if pub else 0.0, "t1": t1,
         "fuente_hotspot": fuente, "sha": sha, "diag_dia": diag}
    r["es_dia"] = ev.es_dia_vol(vol, instante)
    return r


class Escena:
    """Arma pasadas y records de los dos brazos. Toda pasada nocturna tiene record idéntico en los dos brazos; toda
    pasada diurna tiene record en el brazo diurno (con diag_dia) y ninguno en el control, salvo que se diga."""

    def __init__(self):
        self.pasadas, self.rc, self.rb = [], [], []

    def noche(self, vol, sensor, dia, estado="rutina", vrp=None, pub=False, disp=0.0, pub_b=None, disp_b=None,
              hora=5, fuente="CONS"):
        ins = t(dia, hora)
        self.pasadas.append(pas(vol, sensor, ins, estado, vrp, fuente))
        self.rc.append(rec(vol, sensor, ins, pub, disp))
        self.rb.append(rec(vol, sensor, ins, pub if pub_b is None else pub_b, disp if disp_b is None else disp_b))
        return self

    def dia(self, vol, sensor, dia, estado="rutina", vrp=None, pub_b=False, disp_b=0.3, hora=17, fuente="CONS",
            con_record=True):
        ins = t(dia, hora)
        self.pasadas.append(pas(vol, sensor, ins, estado, vrp, fuente))
        if con_record:
            self.rb.append(rec(vol, sensor, ins, pub_b, disp_b, diag=True))
        return self

    def base(self, sensores=(V375, V750)):
        """Fondo neutro: en cada sensor, 10 negativos nocturnos (el control publica 1: Q_n = 10 %) y 40 negativos
        diurnos sin publicar, en días y volcanes sin alerta."""
        for s in sensores:
            for i in range(10):
                self.noche(VOLS[i % 11], s, 1 + i, pub=(i == 0), disp=0.2)
            for i in range(40):
                self.dia(VOLS[i % 11], s, 1 + (i % 20), hora=17 if i < 20 else 18)
        return self

    def evaluar(self, opcion="e-i", **kw):
        return ev.evaluar(self.pasadas, {C: self.rc, B: self.rb}, C, B, opcion=opcion, p_sup=P_SUP, sha=SHA,
                          ventanas=VENT, **kw)


def publicar_negativos_diurnos(e, s, n):
    k = 0
    for r in e.rb:
        if k < n and r["b"] == s and r["es_dia"] and not r["pub"]:
            r["pub"], r["disp"] = True, 0.3
            k += 1
    return e


# ------------------------------------------------------------------------------------------- reglas puras
@pytest.mark.parametrize("m,opcion,esperado", [
    (dict(p2="GANA", neto=-6, P=0, D=False, publica=True, Qd=0.0, Qn=0.1), "e-i", ("ADOPTAR", "a")),
    (dict(p2="EMPATE", neto=0, P=1, D=True, publica=True, Qd=0.0, Qn=0.1), "e-i", ("ADOPTAR", "b")),
    (dict(p2="EMPATE", neto=0, P=1, D=False, publica=True, Qd=0.0, Qn=0.1), "e-i", ("NO ADOPTAR", "c")),
    (dict(p2="SIN SUSTRATO", neto=-1, P=2, D=True, publica=True, Qd=0.0, Qn=0.1), "e-ii", ("ADOPTAR", "b")),
    (dict(p2="SIN SUSTRATO", neto=0, P=0, D=False, publica=False, Qd=0.0, Qn=0.1), "e-i", ("SIN CAMBIO", "c")),
    (dict(p2="EMPATE", neto=-2, P=0, D=True, publica=True, Qd=0.0, Qn=0.1), "e-i", ("NO ADOPTAR", "c")),
    (dict(p2="BLOQUEA", neto=3, P=0, D=False, publica=True, Qd=0.05, Qn=0.1), "e-i", ("NO ADOPTAR", "d")),
    (dict(p2="PIERDE", neto=30, P=3, D=False, publica=True, Qd=0.05, Qn=0.1), "e-i", ("NO ADOPTAR", "d")),
    (dict(p2="PIERDE", neto=30, P=2, D=True, publica=True, Qd=0.05, Qn=0.1), "e-i", ("ADOPTAR", "e-i")),
    (dict(p2="PIERDE", neto=30, P=2, D=True, publica=True, Qd=0.1, Qn=0.1), "e-i", ("ADOPTAR", "e-i")),
    (dict(p2="PIERDE", neto=30, P=2, D=True, publica=True, Qd=0.11, Qn=0.1), "e-i", ("DECIDE NICOLÁS CON M4", "e-i")),
    (dict(p2="PIERDE", neto=30, P=2, D=True, publica=True, Qd=0.01, Qn=0.1), "e-ii", ("DECIDE NICOLÁS CON M4", "e-ii")),
    (dict(p2="SIN SUSTRATO", neto=2, P=1, D=True, publica=True, Qd=0.2, Qn=0.1), "e-i", ("DECIDE NICOLÁS CON M4", "e-i")),
])
def test_veredicto_sensor_casos_a_a_e(m, opcion, esperado):
    assert ev.veredicto_sensor(m, opcion) == esperado


def test_veredicto_sensor_rechaza_opcion_desconocida():
    with pytest.raises(ValueError):
        ev.veredicto_sensor(dict(p2="PIERDE", neto=3, P=1, D=True, publica=True, Qd=0.0, Qn=0.1), "e-iii")


def test_discrimina_binomial_exacta():
    assert ev.discrimina(1, 10, 0.0) is True          # no publica en negativos y recupera una
    assert ev.discrimina(0, 10, 0.0) is False
    assert ev.discrimina(5, 5, 0.9) is False          # el caso de C0: publica casi todo
    assert ev.discrimina(4, 36, 0.02) is True         # P(Bin(36; 0,02) >= 4) = 0,006
    assert ev.discrimina(2, 36, 0.02) is False        # P(Bin(36; 0,02) >= 2) = 0,16
    assert ev.discrimina(3, 0, 0.0) is False


@pytest.mark.parametrize("comp,r1,sens,esperado", [
    ({"invalido": ["x"], "indecidible": []}, [], {V375: "ADOPTAR", V750: "ADOPTAR"}, "INVÁLIDO POR INSTRUMENTO"),
    ({"invalido": [], "indecidible": ["y"]}, [], {V375: "ADOPTAR", V750: "ADOPTAR"}, "INDECIDIBLE"),
    ({"invalido": [], "indecidible": []}, ["p"], {V375: "ADOPTAR", V750: "ADOPTAR"}, "INVÁLIDO POR INSTRUMENTO"),
    ({"invalido": [], "indecidible": []}, [], {V375: "ADOPTAR", V750: "SIN CAMBIO"}, "ADOPTAR"),
    # V-N7: un ADOPTAR de VIIRS 750 (rama diurna con la Tabla 1, no con el código de MIROVA) no se adopta solo
    ({"invalido": [], "indecidible": []}, [], {V375: "ADOPTAR", V750: "ADOPTAR"}, "DECIDE NICOLÁS"),
    ({"invalido": [], "indecidible": []}, [], {V375: "SIN CAMBIO", V750: "ADOPTAR"}, "DECIDE NICOLÁS"),
    ({"invalido": [], "indecidible": []}, [], {V375: "SIN CAMBIO", V750: "SIN CAMBIO"}, "NO ADOPTAR"),
    ({"invalido": [], "indecidible": []}, [], {V375: "NO ADOPTAR", V750: "SIN CAMBIO"}, "NO ADOPTAR"),
    ({"invalido": [], "indecidible": []}, [], {V375: "ADOPTAR", V750: "NO ADOPTAR"}, "DECIDE NICOLÁS"),
    ({"invalido": [], "indecidible": []}, [], {V375: "DECIDE NICOLÁS CON M4", V750: "ADOPTAR"},
     "DECIDE NICOLÁS CON M4"),
    ({"invalido": [], "indecidible": []}, [], {V375: "NO ADOPTAR", V750: "DECIDE NICOLÁS CON M4"},
     "DECIDE NICOLÁS CON M4"),
])
def test_veredicto_global(comp, r1, sens, esperado):
    assert ev.veredicto_global(comp, r1, sens) == esperado


@pytest.mark.parametrize("principal,variantes,esperado", [
    ("ADOPTAR", {"tabla": "ADOPTAR", "sin_W2": "ADOPTAR", "sin_reflejo": "ADOPTAR"}, "ADOPTAR"),
    ("ADOPTAR", {"tabla": "ADOPTAR", "sin_W2": "NO ADOPTAR", "sin_reflejo": "ADOPTAR"}, "DECIDE NICOLÁS"),
    ("NO ADOPTAR", {"tabla": "ADOPTAR", "sin_W2": "NO ADOPTAR", "sin_reflejo": "NO ADOPTAR"}, "DECIDE NICOLÁS"),
    ("NO ADOPTAR", {"tabla": "NO ADOPTAR", "sin_W2": "NO ADOPTAR", "sin_reflejo": "NO ADOPTAR"}, "NO ADOPTAR"),
    ("DECIDE NICOLÁS CON M4", {"tabla": "ADOPTAR", "sin_W2": "ADOPTAR", "sin_reflejo": "ADOPTAR"},
     "DECIDE NICOLÁS CON M4"),
    ("INVÁLIDO POR INSTRUMENTO", {"tabla": "ADOPTAR", "sin_W2": "ADOPTAR", "sin_reflejo": "ADOPTAR"},
     "INVÁLIDO POR INSTRUMENTO"),
    ("INDECIDIBLE", {"tabla": "ADOPTAR", "sin_W2": "ADOPTAR", "sin_reflejo": "ADOPTAR"}, "INDECIDIBLE"),
])
def test_veredicto_final_robustez(principal, variantes, esperado):
    assert ev.veredicto_final(principal, variantes)[0] == esperado


def test_i6_juicio_de_placebos():
    assert ev.juzgar_i6("GANA", 5, 0) == []
    assert ev.juzgar_i6("SIN SUSTRATO", 4, 0) == []          # menos de 5 bloques: se informa, no falla
    assert ev.juzgar_i6("EMPATE", 5, 0) != []                # con sustrato tiene que ver la mejora
    assert ev.juzgar_i6("GANA", 9, 7) == []                  # dos colas: hasta 10 % por sorteo (V-N3)
    assert ev.juzgar_i6("GANA", 9, 8) != []                  # P(Bin(40; 0,10) >= 8) = 0,042
    assert ev.juzgar_i6("GANA", 9, 7, 4) == []
    assert ev.juzgar_i6("GANA", 9, 7, 5) != []               # V3-4: 5 GANA de 40 ya falla aunque la suma no


def test_i4_cota_binomial():
    # N = 2.500 pasadas diurnas y p_sup = 0,0011: 2 sin record es lo esperable, 8 ya no.
    assert ev.cobertura_diurna_excede(2, 2500, 0.0011) is False
    assert ev.cobertura_diurna_excede(8, 2500, 0.0011) is True
    assert ev.cobertura_diurna_excede(0, 0, 0.0011) is False
    # borde de la cola: P(Bin(50; 0,0011) >= 1) = 0,054 no excede; corrida en uno daría P(X >= 2) = 0,001 y excedería
    assert ev.cobertura_diurna_excede(1, 50, 0.0011) is False


# ------------------------------------------------------------------------------------------- escenarios
def test_escena_neutra_sin_cambio_da_no_adoptar():
    r = Escena().base().evaluar()
    assert r["compuertas"]["invalido"] == [] and r["compuertas"]["indecidible"] == []
    assert r["por_sensor"][V375]["veredicto"] == "SIN CAMBIO"
    assert r["global"] == "NO ADOPTAR"


def test_caso_a_gana_con_alertas_bajo_1mw_en_seis_bloques():
    e = Escena().base()
    for i in range(6):
        e.dia(VOLS[i], V375, 21 + i, estado="alerta", vrp=0.4, pub_b=True)
    r = e.evaluar()
    m = r["por_sensor"][V375]
    assert m["p2"] == "GANA" and m["neto"] == -6
    assert m["P"] == 0 and m["amb_recuperadas"] == 6             # alertas bajo 1 MW no son protegidas
    assert m["veredicto"] == "ADOPTAR" and m["caso"] == "a"
    assert r["global"] == "ADOPTAR"


def test_caso_b_protegida_recuperada_sin_empeorar():
    e = Escena().base()
    e.dia("Lascar", V375, 22, estado="alerta", vrp=3.0, pub_b=True, disp_b=2.5)
    r = e.evaluar()
    m = r["por_sensor"][V375]
    assert m["P"] == 1 and m["P_obs"] == 1 and m["neto"] == 0
    assert (m["veredicto"], m["caso"]) == ("ADOPTAR", "b")


def test_caso_d_publica_negativos_sin_protegidas():
    e = publicar_negativos_diurnos(Escena().base(), V375, 6)
    m = e.evaluar()["por_sensor"][V375]
    assert m["neto"] == 6 and m["P"] == 0
    assert (m["veredicto"], m["caso"]) == ("NO ADOPTAR", "d")


def test_caso_e_i_por_debajo_y_por_encima_de_la_noche():
    # Q_n = 1 de 10 negativos nocturnos (10 %). Con 4 de 40 negativos diurnos, Q_d = 10 %: ADOPTAR (≤). Tres protegidas
    # recuperadas de tres: D cumple (P(Bin(3; 0,1) >= 3) = 0,001).
    def con_protegidas(e):
        for i, v in enumerate(("Lascar", "Isluga", "Villarrica")):
            e.dia(v, V375, 22 + i, estado="alerta", vrp=3.0, pub_b=True, disp_b=2.5)
        return e
    e = con_protegidas(publicar_negativos_diurnos(Escena().base(), V375, 4))
    m = e.evaluar()["por_sensor"][V375]
    assert m["Qn"] == pytest.approx(0.1) and m["Qd"] == pytest.approx(0.1) and m["D"] is True
    assert (m["veredicto"], m["caso"]) == ("ADOPTAR", "e-i")
    e2 = con_protegidas(publicar_negativos_diurnos(Escena().base(), V375, 5))
    r2 = e2.evaluar()
    assert r2["por_sensor"][V375]["veredicto"] == "DECIDE NICOLÁS CON M4"
    assert r2["global"] == "DECIDE NICOLÁS CON M4"
    assert e2.evaluar(opcion="e-ii")["por_sensor"][V375]["veredicto"] == "DECIDE NICOLÁS CON M4"
    # con una sola protegida recuperada y Q_d = 10 %, D no cumple: sin beneficio demostrado
    e3 = publicar_negativos_diurnos(Escena().base(), V375, 4)
    e3.dia("Lascar", V375, 22, estado="alerta", vrp=3.0, pub_b=True, disp_b=2.5)
    m3 = e3.evaluar()["por_sensor"][V375]
    assert m3["D"] is False and (m3["veredicto"], m3["caso"]) == ("NO ADOPTAR", "d")


def test_qn_es_del_control_de_noche_y_no_del_brazo():
    e = Escena().base()
    # el brazo diurno publicaría de noche en otro negativo: I5 lo marca, y Q_n sigue siendo el del control
    e.rb[1]["pub"], e.rb[1]["disp"] = True, 0.2
    r = e.evaluar()
    assert r["por_sensor"][V375]["Qn"] == pytest.approx(0.1)
    assert r["por_sensor"][V375]["neto"] == 0                    # P2 diurno no cuenta la noche
    assert r["compuertas"]["indecidible"] != []


def test_negativo_diurno_mira_solo_el_periodo_diurno():
    e = Escena().base()
    # día 25: alerta NOCTURNA de Láscar en VIIRS 375; su RUTINA del mediodía sigue siendo negativo (periodo aparte)
    e.noche("Lascar", V375, 25, estado="alerta", vrp=0.3, pub=True, disp=0.3)
    e.dia("Lascar", V375, 25, pub_b=True)
    # día 26: FALSO_POSITIVO diurno en Isluga; su RUTINA diurna no es negativo
    e.dia("Isluga", V375, 26, estado="fp", vrp=0.5, hora=16)
    e.dia("Isluga", V375, 26, pub_b=True)
    # día 27: alerta diurna bajo 1 MW en Llaima a las 16; su RUTINA de las 18 no es negativo
    e.dia("Llaima", V375, 27, estado="alerta", vrp=0.4, hora=16)
    e.dia("Llaima", V375, 27, pub_b=True, hora=18)
    m = e.evaluar()["por_sensor"][V375]
    assert m["neg_pub"] == 1 and m["pub_otra"] == 2
    # neto: +1 por Láscar; la alerta de Llaima no la publica ninguno de los dos (el control no mira el día), sin
    # discordancia
    assert m["neto"] == 1


def test_negativo_nocturno_no_mira_el_dia():
    e = Escena().base()
    # Q_n: el negativo nocturno de Láscar del día 1 (publicado por el control) sigue siendo negativo aunque haya una
    # alerta diurna ese mismo día
    e.dia("Lascar", V375, 1, estado="alerta", vrp=0.4, hora=19)
    assert e.evaluar()["por_sensor"][V375]["Qn"] == pytest.approx(0.1)


def test_excluir_una_protegida_no_vuelve_negativas_a_sus_vecinas():
    e = Escena().base()
    e.dia("Lascar", V375, 24, estado="alerta", vrp=3.0, hora=16, pub_b=True, disp_b=2.0)
    e.dia("Lascar", V375, 24, hora=18, pub_b=True)              # RUTINA del mismo día: «otra»
    clave = "Lascar|VIIRS375|2026-08-24 16:00:00"
    m = e.evaluar(excluir_claves={clave})["por_sensor"][V375]
    assert m["neg_pub"] == 0 and m["pub_otra"] == 1 and m["P_obs"] == 0


def test_i4a_vigila_tambien_alertas_bajo_1mw():
    e = Escena().base()
    e.dia("Lascar", V375, 28, estado="alerta", vrp=0.4, con_record=False)
    assert any("I4a" in x for x in e.evaluar()["compuertas"]["invalido"])


def test_i5_records_nocturnos_en_un_solo_brazo():
    e = Escena().base()
    e.rb.append(rec("Copahue", V375, t(9, 6), pub=False))      # una pasada nocturna sin MIROVA que sólo el brazo tiene
    r = e.evaluar()
    assert any("I5" in x and "brazo" in x for x in r["compuertas"]["indecidible"])


def test_angulo_de_reflejo_formula_de_mirova():
    # acimuts opuestos con zenits iguales: el satélite mira justo el reflejo del sol (0°); mismo acimut: 60°
    r = {"sz": 30.0, "sa": 100.0, "soz": 30.0, "soa": 280.0}       # opuestos: reflejo especular exacto, 0°
    assert ev.angulo_reflejo(r) == pytest.approx(0.0, abs=1e-6)
    r = {"sz": 30.0, "sa": 100.0, "soz": 30.0, "soa": 100.0}       # mismo lado: 60°
    assert ev.angulo_reflejo(r) == pytest.approx(60.0, abs=1e-6)
    assert ev.angulo_reflejo({"sz": 30.0, "sa": None, "soz": 30.0, "soa": 100.0}) is None


def test_filtro_de_reflejo_apaga_solo_diurnas_bajo_12_grados():
    recs = [{"es_dia": True, "b": V750, "pub": True, "disp": 0.5, "sz": 30.0, "sa": 100.0, "soz": 30.0, "soa": 280.0},
            {"es_dia": True, "b": V750, "pub": True, "disp": 0.5, "sz": 30.0, "sa": 100.0, "soz": 30.0, "soa": 100.0},
            {"es_dia": False, "b": V750, "pub": True, "disp": 0.5, "sz": 30.0, "sa": 100.0, "soz": 30.0, "soa": 280.0}]
    out = ev.aplicar_filtro_reflejo(recs)
    assert [r["pub"] for r in out] == [False, True, True]
    assert recs[0]["pub"] is True                                  # no toca la entrada


def test_m4_por_ventana():
    e = Escena().base()
    e.dia("Lascar", V375, 22, estado="alerta", vrp=3.0, pub_b=True, disp_b=2.5)
    m = ev.evaluar(e.pasadas, {C: e.rc, B: e.rb}, C, B, opcion="e-i", p_sup=P_SUP, sha=SHA,
                   ventanas=[("Wa", "2026-08-01", "2026-08-15"), ("Wb", "2026-08-16", "2026-08-31")])["por_sensor"][V375]
    assert m["por_ventana"]["Wb"]["P"] == 1 and m["por_ventana"]["Wa"]["P_obs"] == 0
    assert m["P_1mw"] == 1


def test_alerta_minima_cuenta_como_negativo_con_sn():
    # La regla SN la aplica clase_mirova antes (una alerta de 0,05 MW o menos llega como RUTINA). Aquí se verifica
    # que el evaluador pide las pasadas con la regla SN por defecto.
    assert ev.REGLA_MINIMAS == "SN"


def test_control_sintetico_solo_si_el_control_no_tiene_records_diurnos():
    e = Escena().base()
    e.rc.append(rec("Lascar", V375, t(3, 17), pub=False))     # el control trae un record VIIRS diurno
    r = e.evaluar()
    assert any("I2" in x for x in r["compuertas"]["invalido"])
    assert r["global"] == "INVÁLIDO POR INSTRUMENTO"


def test_i1_test1_y_sha():
    e = Escena().base()
    e.rb[0]["t1"] = True
    assert any("I1" in x for x in e.evaluar()["compuertas"]["invalido"])
    e = Escena().base()
    e.rc[0]["fuente_hotspot"] = "test1_roi"
    assert any("I1" in x for x in e.evaluar()["compuertas"]["invalido"])
    e = Escena().base()
    e.rb[3]["sha"] = "b" * 40
    assert any("I1" in x for x in e.evaluar()["compuertas"]["invalido"])
    e = Escena().base()
    lanzo = False
    try:
        ev.evaluar(e.pasadas, {C: e.rc, B: e.rb}, C, B, opcion="e-i", p_sup=P_SUP, sha="a" * 7, ventanas=VENT)
    except ValueError:
        lanzo = True
    assert lanzo, "un sha abreviado tiene que rechazarse (git rev-parse <tag>^{commit}, 40 caracteres)"


def test_i2_la_palanca_tiene_que_actuar():
    e = Escena().base(sensores=(V375,))
    for r in e.rb:
        r["diag_dia"] = None
    assert any("I2" in x for x in e.evaluar()["compuertas"]["invalido"])
    e = Escena().base()
    e.rb[0]["diag_dia"] = True                                 # un record NOCTURNO con umbrales diurnos
    assert any("I2" in x for x in e.evaluar()["compuertas"]["invalido"])


def test_i3_cobertura_nocturna_contra_la_referencia():
    e = Escena().base()
    e.noche("Lascar", V375, 27, estado="alerta", vrp=4.0, pub=True, disp=3.0)
    e.rb.pop()                                                  # al brazo le falta la protegida nocturna
    r = e.evaluar()
    assert any("I3" in x for x in r["compuertas"]["invalido"])


def test_i4_protegida_diurna_sin_record_y_dia_vacio():
    e = Escena().base()
    e.dia("Lascar", V375, 28, estado="alerta", vrp=2.0, con_record=False)
    assert any("I4a" in x for x in e.evaluar()["compuertas"]["invalido"])
    e = Escena().base()
    e.dia("Copahue", V375, 29, con_record=False)
    assert any("I4b" in x for x in e.evaluar()["compuertas"]["invalido"])


def test_i4c_tasa_de_pasadas_diurnas_sin_record():
    e = Escena().base()
    # 40 diurnas por sensor con record; se agregan 3 sin record en días que sí tienen otro record diurno
    for i in range(3):
        e.dia(VOLS[i], V375, 1 + i, hora=19, con_record=False)
    r = e.evaluar()
    assert any("I4c" in x for x in r["compuertas"]["invalido"])
    e = Escena().base()
    e.dia(VOLS[0], V375, 1, hora=19, con_record=False)       # 1 de 41 con p_sup = 0,0011: P = 0,044, falla
    assert any("I4c" in x for x in e.evaluar()["compuertas"]["invalido"])
    e = Escena().base()
    e.dia(VOLS[0], V375, 1, hora=19, con_record=False)
    assert not any("I4c" in x for x in e.evaluar(p_sup_override={V375: 0.05, V750: 0.05})["compuertas"]["invalido"])


def test_i5_noche_distinta_da_indecidible():
    e = Escena().base()
    # rb[2] y rc[2] son la misma pasada nocturna de VIIRS 375: los dos publican, con otra magnitud
    e.rc[2]["pub"], e.rc[2]["disp"] = True, 0.2
    e.rb[2]["pub"], e.rb[2]["disp"] = True, 0.25
    r = e.evaluar()
    assert any("I5" in x for x in r["compuertas"]["indecidible"])
    assert r["global"] == "INDECIDIBLE"
    e = Escena().base()
    e.rb[2]["disp"] = 0.0000001                                  # sin publicar, la magnitud no cuenta
    assert e.evaluar()["compuertas"]["indecidible"] == []


def test_r1_incoherente_con_i5_en_verde_es_invalido():
    assert ev.veredicto_global({"invalido": [], "indecidible": []}, ["Lascar|VIIRS375|..."],
                               {V375: "ADOPTAR", V750: "ADOPTAR"}) == "INVÁLIDO POR INSTRUMENTO"


def test_r1_detecta_protegida_que_el_control_publica_y_el_brazo_no():
    e = Escena().base()
    e.noche("Lascar", V375, 27, estado="alerta", vrp=4.0, pub=True, disp=3.0, pub_b=False)
    e.noche("Isluga", V375, 28, estado="alerta", vrp=2.0, pub=False)   # ninguno la publica: no es pérdida
    r = e.evaluar()
    assert len(r["r1"]) == 1
    assert r["global"] == "INDECIDIBLE"                          # I5 manda: la noche cambió


def test_sensores_mezclados_adoptar_y_no_adoptar():
    e = Escena().base()
    e.dia("Lascar", V375, 22, estado="alerta", vrp=3.0, pub_b=True, disp_b=2.5)
    publicar_negativos_diurnos(e, V750, 6)
    r = e.evaluar()
    assert r["por_sensor"][V375]["veredicto"] == "ADOPTAR"
    assert r["por_sensor"][V750]["veredicto"] == "NO ADOPTAR"
    assert r["global"] == "DECIDE NICOLÁS"


def test_excluir_claves_y_dias_cambia_el_veredicto():
    e = Escena().base()
    e.dia("Lascar", V375, 22, estado="alerta", vrp=3.0, pub_b=True, disp_b=2.5)
    clave = "Lascar|VIIRS375|2026-08-22 17:00:00"
    assert e.evaluar()["global"] == "ADOPTAR"
    assert e.evaluar(excluir_claves={clave})["global"] == "NO ADOPTAR"   # sin la protegida: publica sin beneficio
    r = e.evaluar(excluir_dias={"2026-08-22"})
    assert r["global"] == "NO ADOPTAR"
    assert r["por_sensor"][V375]["veredicto"] == "SIN CAMBIO"   # el record del día excluido sale también


def test_placebo_a_ve_la_mejora_con_sustrato():
    e = publicar_negativos_diurnos(Escena().base(), V375, 12)
    r = e.evaluar()
    i6 = r["i6"][V375]
    assert i6["a"]["bloques"] >= 5 and i6["a"]["resultado"] == "GANA"
    assert i6["c_falsos"] <= 4
    assert r["compuertas"]["indecidible"] == []


def test_p1b_arriba_diurno_cuenta_publicaciones_de_1mw_en_negativos():
    e = Escena().base()
    publicar_negativos_diurnos(e, V375, 2)
    for r in e.rb:
        if r["b"] == V375 and r["es_dia"] and r["pub"]:
            r["disp"] = 1.0                                       # justo 1 MW: ya es clase Bajo
            break
    m = e.evaluar()["por_sensor"][V375]
    assert m["neg_1mw"] == 1


def test_magnitud_brazo_sobre_mirova_en_recuperadas():
    e = Escena().base()
    e.dia("Lascar", V375, 22, estado="alerta", vrp=4.0, pub_b=True, disp_b=2.0)
    e.dia("Isluga", V375, 23, estado="alerta", vrp=1.0, pub_b=True, disp_b=1.0)
    m = e.evaluar()["por_sensor"][V375]
    assert m["razon_mag_mediana"] == pytest.approx(0.75)


def test_i6_cuenta_los_falsos_del_placebo_simetrico():
    # Diez bloques (volcán y día) con negativos diurnos publicados y sin publicar en el mismo bloque: el placebo
    # simétrico tiene de dónde voltear. La cuenta del evaluador tiene que ser la de correr las 40 semillas a mano.
    import evaluador_comun as ec
    e = Escena().base()
    for d in range(1, 11):
        for h, pub in ((14, True), (15, True), (19, False), (20, False)):
            e.dia(VOLS[(d + 3) % 11], V375, d, hora=h, pub_b=pub)
    r = e.evaluar()
    T = r["T"]
    excl = lambda f: not (f["es_dia"] and f["pasada"].sensor_bucket == V375)  # noqa: E731
    a_mano = sum(ec.placebo_p2(T, B, "c", 1.0, sem, excluir=excl)[0] in ("GANA", "PIERDE") for sem in ev.SEMILLAS_C)
    assert r["i6"][V375]["c_falsos"] == a_mano
    assert r["i6"][V375]["a"]["bloques"] >= 5


def test_logs_flags_brazo(tmp_path):
    import json as _json
    raiz = tmp_path / "W"
    for brazo, dia in ((C, False), (B, True)):
        (raiz / brazo).mkdir(parents=True)
        (raiz / brazo / "Lascar.json").write_text('{"records": []}', encoding="utf-8")
        fl = {"PROFILE_NAME": brazo, "DATA_SUBDIR": brazo, "ENABLE_DAYTIME_VIIRS": dia, "ENABLE_DAYTIME_MODIS": False,
              "ENABLE_TEST1_PATH": False, "ENABLE_TESTS_23_PROSE_BRANCH": True, "ENABLE_MODIS_B22_PRIMARY": True}
        (raiz / "logs").mkdir(exist_ok=True)
        (raiz / "logs" / ("%s_Lascar.log" % brazo)).write_text("FLAGS_BRAZO " + _json.dumps(fl) + chr(10), encoding="utf-8")
    assert ev.problemas_de_logs([raiz], (C, B), C) == []
    p = raiz / "logs" / ("%s_Lascar.log" % C)
    p.write_text(p.read_text(encoding="utf-8").replace('"ENABLE_TEST1_PATH": false', '"ENABLE_TEST1_PATH": true'),
                 encoding="utf-8")
    assert any("ENABLE_TEST1_PATH" in x for x in ev.problemas_de_logs([raiz], (C, B), C))
    (raiz / "logs" / ("%s_Lascar.log" % B)).unlink()
    assert any("sin línea FLAGS_BRAZO" in x for x in ev.problemas_de_logs([raiz], (C, B), C))


# ------------------------------------------------------------------------------------------- v3 (verificador v2)
def fila(vol, sensor, instante, tipo="RUTINA", vrp=0.0, fuente="CONS"):
    return {"volcano": vol, "sensor_bucket": sensor, "fecha_utc": instante.strftime("%Y-%m-%d %H:%M:%S"),
            "tipo": tipo, "vrp_mw": vrp, "dist_km": 1.0, "source": fuente}


class Completa:
    """Filas de referencia (no pasadas) y records, para probar evaluar_completo (V-N2): las variantes del §6.4."""
    VENT = [("W2", "2026-06-13", "2026-06-30"), ("W3", "2026-07-20", "2026-07-31")]

    def __init__(self):
        self.filas, self.rc, self.rb = [], [], []
        for i in range(10):                                   # noches y días neutros en W3
            ins_n, ins_d = datetime(2026, 7, 20 + i, 5, 0), datetime(2026, 7, 20 + i, 17, 0)
            vol = VOLS[i % 11]
            for sens in (V375, V750):
                self.filas += [fila(vol, sens, ins_n), fila(vol, sens, ins_d)]
                self.rc.append(rec(vol, sens, ins_n))
                self.rb.append(rec(vol, sens, ins_n))
                self.rb.append(rec(vol, sens, ins_d, diag=True))
        for d in (14, 15):                                    # W2 también tiene pasadas (I2)
            for sens in (V375, V750):
                ins = datetime(2026, 6, d, 17, 0)
                self.filas.append(fila("Isluga", sens, ins))
                self.rb.append(rec("Isluga", sens, ins, diag=True))

    def protegida(self, instante, fuente="CONS", vol="Lascar", sens=V375):
        tipo = "ALERTA_TERMICA" if fuente == "CONS" else "ALERTA_TERMICA_OCR"
        self.filas.append(fila(vol, sens, instante, tipo, 3.0, fuente))
        self.rb.append(rec(vol, sens, instante, pub=True, disp=2.0, diag=True))
        return self

    def correr(self, filas_1_13=()):
        return ev.evaluar_completo(self.filas, {C: self.rc, B: self.rb}, C, B, "e-ii", P_SUP, SHA, self.VENT, (),
                                   filas_1_13)


def test_completo_neutro_y_protegida_de_tabla():
    r = Completa().correr()
    assert r["principal"]["global"] == "NO ADOPTAR" and r["final"] == "NO ADOPTAR"
    r = Completa().protegida(datetime(2026, 7, 25, 18, 0)).correr()
    assert r["principal"]["global"] == "ADOPTAR"
    assert r["variantes"] == {"tabla": "ADOPTAR", "sin_W2": "ADOPTAR", "sin_reflejo": "ADOPTAR",
                              "otra_como_negativo": "ADOPTAR"}
    assert r["final"] == "ADOPTAR"


def test_completo_variante_tabla_saca_al_ocr():
    r = Completa().protegida(datetime(2026, 7, 25, 18, 0), fuente="OCR").correr()
    assert r["principal"]["global"] == "ADOPTAR" and r["variantes"]["tabla"] == "NO ADOPTAR"
    assert r["final"] == "DECIDE NICOLÁS"


def test_completo_variante_sin_w2():
    r = Completa().protegida(datetime(2026, 6, 20, 18, 0)).correr()
    assert r["principal"]["global"] == "ADOPTAR" and r["variantes"]["sin_W2"] == "NO ADOPTAR"
    assert r["variantes"]["tabla"] == "ADOPTAR"


def test_completo_variante_sin_reflejo():
    c = Completa().protegida(datetime(2026, 7, 25, 18, 0))
    f113 = [{"volcano": "Lascar", "sensor_bucket": V375, "fecha_utc": "2026-07-25 18:00:40", "clase": "desproporcionada"},
            {"volcano": "Lascar", "sensor_bucket": V375, "fecha_utc": "2026-07-25 18:00:40", "clase": "consistente"}]
    r = c.correr(f113)
    assert len(r["reflejo"]) == 1 and r["variantes"]["sin_reflejo"] == "NO ADOPTAR"
    assert r["final"] == "DECIDE NICOLÁS"


def test_completo_otra_como_negativo():
    c = Completa().protegida(datetime(2026, 7, 25, 16, 0))
    for h in (17, 18, 19):                                    # RUTINA del mismo periodo: «otra», el brazo publica
        ins = datetime(2026, 7, 25, h, 30)
        c.filas.append(fila("Lascar", V375, ins))
        c.rb.append(rec("Lascar", V375, ins, pub=True, disp=0.3, diag=True))
    r = c.correr()
    assert r["principal"]["global"] == "ADOPTAR"
    assert r["variantes"]["otra_como_negativo"] == "NO ADOPTAR"   # 3 negativos publicados, 1 alerta: D no cumple
    assert r["final"] == "DECIDE NICOLÁS"


def test_completo_informa_minimas_y_reflejo_12():
    r = Completa().protegida(datetime(2026, 7, 25, 18, 0)).correr()
    assert set(r["info"]) == {"minimas_SE", "minimas_original", "minimas_SN_0,04", "con_filtro_reflejo_12"}
    assert r["reflejo12"]["sin_angulos"] == 1                 # los records sintéticos no traen ángulos


def test_p_sup_de_vara():
    v = {V375: {"sin_record_produccion": 0, "pasadas_nocturnas": 2715},
         V750: {"sin_record_produccion": 9, "pasadas_nocturnas": 2650}}
    p = ev.p_sup_de_vara(v)
    assert p[V375] == pytest.approx(0.0011028, abs=1e-6) and p[V750] == pytest.approx(0.0059190, abs=1e-6)


def test_es_dia_con_sol_bajo():
    from pipeline.store import _solar_elevation
    lat, lon = ev.coords()["Lascar"]
    t0 = datetime(2026, 8, 1, 10, 0)
    for m in range(0, 600, 5):                                # primer minuto con el sol entre 1 y 10 grados
        ins = t0 + timedelta(minutes=m)
        if 1 < _solar_elevation(lat, lon, ins) < 10:
            break
    assert ev.es_dia_vol("Lascar", ins) is True
    assert ev.es_dia_vol("Lascar", datetime(2026, 8, 1, 5, 0)) is False


def test_cargar_brazo_dedupe_y_modis_diurno(tmp_path):
    import json as _json
    base = {"distance_class": "summit", "vrp_mw": 0.0, "primary_cluster": None, "anomaly_pixels": [],
            "regimen": {"codigo_sha": SHA}, "sensor_zenith_deg": 10.0, "sensor_azimuth_deg": 20.0,
            "solar_zenith_deg": 40.0, "solar_azimuth_deg": 50.0}
    recs = [dict(base, sensor="VIIRS_SNPP", datetime_utc="2026-07-21 05:00"),
            dict(base, sensor="VIIRS_SNPP", datetime_utc="2026-07-21 05:00"),          # duplicado
            dict(base, sensor="VIIRS_SNPP", datetime_utc="2026-07-21 17:00"),
            dict(base, sensor="MODIS_AQUA", datetime_utc="2026-07-21 18:00"),          # MODIS de día: fuera
            dict(base, sensor="MODIS_AQUA", datetime_utc="2026-07-21 06:00"),
            dict(base, sensor="VIIRS_SNPP", datetime_utc="2026-08-21 05:00")]          # fuera de ventana
    (tmp_path / B).mkdir()
    (tmp_path / B / "Lascar.json").write_text(_json.dumps({"records": recs}), encoding="utf-8")
    import banco_paridad as bp
    out = ev.cargar_brazo([tmp_path], B, [("W3", "2026-07-20", "2026-07-31")], bp.inner_desde_html())
    assert sorted((r["b"], r["dt"].hour, r["es_dia"]) for r in out) == [("MODIS", 6, False), (V375, 5, False),
                                                                         (V375, 17, True)]
    assert all(r["sz"] == 10.0 and r["soa"] == 50.0 and r["sha"] == SHA and r["huella"] for r in out)


def test_i3_no_se_tapa_con_un_record_diurno():
    e = Escena().base()
    ins = t(27, 5)
    e.pasadas.append(pas("Llaima", V375, ins, "alerta", 4.0))   # protegida nocturna sin record en ningún brazo
    e.dia("Llaima", V375, 27)                                   # pero el brazo tiene un record diurno ese día
    assert any("I3" in x for x in e.evaluar()["compuertas"]["invalido"])


def test_huella_nocturna_informa_sin_decidir():
    e = Escena().base()
    for r in e.rc:
        r["huella"] = "x"
    for r in e.rb:
        r["huella"] = "x"
    e.rb[3]["huella"] = "y"
    r = e.evaluar()
    assert len(r["noche_records_distintos_en_otros_campos"]) == 1
    assert r["compuertas"]["indecidible"] == []


def test_huella_ignora_volatiles_y_diagnosticos():
    base = {"sensor": "VIIRS_SNPP", "datetime_utc": "2026-07-21 05:00", "final_hotspot_lat": -23.37}
    h = ev.huella_record(base)
    assert ev.huella_record(dict(base, processed_utc="x", first_processed_utc="y", regimen={"a": 1},
                                 diag_mu_deti=0.1)) == h
    assert ev.huella_record(dict(base, final_hotspot_lat=-23.38)) != h


def test_completo_otra_como_negativo_incluye_falsos_positivos():
    # V3-1: el escenario del verificador v2 (una protegida y publicaciones en pasadas FALSO_POSITIVO diurnas)
    c = Completa().protegida(datetime(2026, 7, 25, 16, 0))
    for h in (17, 18, 19):
        ins = datetime(2026, 7, 26 + (h - 17), h, 30)
        c.filas.append(fila("Isluga", V375, ins, "FALSO_POSITIVO", 0.5))
        c.rb.append(rec("Isluga", V375, ins, pub=True, disp=0.3, diag=True))
    r = c.correr()
    assert r["principal"]["global"] == "ADOPTAR"
    assert r["variantes"]["otra_como_negativo"] == "NO ADOPTAR"
    assert r["final"] == "DECIDE NICOLÁS"


def test_i6_cuenta_los_gana_del_placebo_simetrico():
    # V3-4: el tope propio de GANA necesita que el conteo de GANA sea el de correr las semillas a mano, y que en esta
    # escena pueda ser distinto de cero (25 bloques con negativos publicados y sin publicar).
    import evaluador_comun as ec
    e = Escena().base()
    for d in range(1, 26):
        for h, pub in ((14, True), (15, True), (19, False), (20, False)):
            e.dia(VOLS[(d + 3) % 11], V375, d, hora=h, pub_b=pub)
    r = e.evaluar()
    excl = lambda f: not (f["es_dia"] and f["pasada"].sensor_bucket == V375)  # noqa: E731
    a_mano = sum(ec.placebo_p2(r["T"], B, "c", 1.0, sem, excluir=excl)[0] == "GANA" for sem in ev.SEMILLAS_C)
    assert a_mano >= 1 and r["i6"][V375]["c_gana"] == a_mano


def test_variante_d_no_toca_los_falsos_positivos_nocturnos():
    # Verificador v3.1, V1: la reclasificación de la variante d es sólo diurna. Un FALSO_POSITIVO nocturno que el
    # control publica no puede pasar a negativo nocturno (cambiaría Q_n).
    e = Escena().base()
    e.noche("Isluga", V375, 15, estado="fp", vrp=0.5, pub=True, disp=0.3)   # día sin otras pasadas nocturnas
    r0 = e.evaluar()
    r1 = e.evaluar(otra_como_negativo=True)
    assert r0["por_sensor"][V375]["Qn"] == pytest.approx(0.1)
    assert r1["por_sensor"][V375]["Qn"] == pytest.approx(0.1)


def test_i6_el_tope_de_gana_llega_al_juicio(monkeypatch):
    # Verificador v3.1, V2: con el tope de GANA en 0 y una escena donde el placebo c da al menos un GANA, I6 tiene que
    # fallar; si compuerta_i6 no le pasara los GANA a juzgar_i6, no fallaría.
    e = Escena().base()
    for d in range(1, 26):
        for h, pub in ((14, True), (15, True), (19, False), (20, False)):
            e.dia(VOLS[(d + 3) % 11], V375, d, hora=h, pub_b=pub)
    monkeypatch.setattr(ev, "MAX_GANA_C", 0)
    r = e.evaluar()
    assert r["i6"][V375]["c_gana"] >= 1
    assert any("con GANA" in x for x in r["compuertas"]["indecidible"])
