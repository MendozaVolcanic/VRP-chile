# -*- coding: utf-8 -*-
"""Batería del evaluador del A/B diurno sobre la vía (S190, experiments/_s190_diurno/ADENDA_VIA.md §3 a §5).

POR QUÉ. La adenda V (sellada) cambia ocho puntos del evaluador de S163 y su regla de decisión: MODIS entra, el
marcador de I2 es el dayflag de la vía, la tabla dayflag contra elevación se informa, un record diurno sin ángulos hace
fallar I2, el reflejo se cuenta (M7), las publicaciones en pasadas que MIROVA no lista frenan el ADOPTAR (M8), la
magnitud también (M5), el veredicto se lee sin Chillán (R-CH) y sin W7 (R-W7), y hay un veredicto por flag sin la
cláusula de VIIRS 750 de S163. Cada prueba fija una de esas ramas con un escenario sintético que cambia el veredicto
si la rama se rompe; las mutaciones de experiments/_s190_diurno/mutaciones.json tienen que caer por una aserción de
aquí (salida en experiments/_s190_diurno/mutaciones_salida.txt).

Escenarios: pasadas de MIROVA y records armados a mano, con la publicación ya dada (sin node, salvo la prueba de la
carga). Noche a las 05:00 UTC y día a las 16 a 18 UTC (elevación solar positiva en agosto en los 11 Tier A).
Ventanas sintéticas: W2 del 1 al 20 de agosto y W7 del 21 al 31.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import pytest

os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
ROOT = Path(__file__).resolve().parents[1]
AQUI = ROOT / "experiments" / "_s190_diurno"
for p in (str(ROOT), str(ROOT / "scripts"), str(ROOT / "experiments" / "_s163_diurno_k"), str(AQUI)):
    if p not in sys.path:
        sys.path.insert(0, p)

import clase_mirova as cm  # noqa: E402
import evaluar_diurno_via as ev  # noqa: E402

SHA = "a" * 40
C, B = "ctrl", "diurno"
MOD, V375, V750 = "MODIS", "VIIRS375", "VIIRS750"
SENS = (MOD, V375, V750)
VOLS = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan", "Copahue", "Llaima",
        "Villarrica", "PuyehueCordonCaulle", "Chaiten"]
VOLS_SIN_CH = [v for v in VOLS if v != "NevadosDeChillan"]
VENT = [("W2", "2026-08-01", "2026-08-20"), ("W7", "2026-08-21", "2026-08-31")]
P_SUP = {MOD: 0.0432, V375: 0.0266, V750: 0.0011}
AD, NO, SC, DE, DM4 = ev.ADOPTAR, ev.NO_ADOPTAR, ev.SIN_CAMBIO, ev.DECIDE, ev.DECIDE_M4
FM, FV = ev.FLAG_MODIS, ev.FLAG_VIIRS


def t(dia, hora, minuto=0):
    return datetime(2026, 8, dia, hora, minuto)


def pas(vol, sensor, instante, estado, vrp=None, fuente="CONS"):
    return cm.PasadaMirova(vol, sensor, instante, estado, vrp, None, fuente, fuente != "CONS", False, (), False)


def rec(vol, b, instante, pub=False, disp=0.0, sha=SHA, dayflag=None, via=True, motivo=None, soz="auto"):
    es_dia = ev.ek.es_dia_vol(vol, instante)
    return {"vol": vol, "b": b, "dt": instante, "pub": pub, "disp": disp if pub else 0.0, "t1": False,
            "fuente_hotspot": "codigo_mirova", "sha": sha, "via": via, "es_dia": es_dia,
            "dayflag": (1 if es_dia else 0) if dayflag is None else dayflag, "motivo": motivo,
            "soz": (50.0 if es_dia else 120.0) if soz == "auto" else soz}


class Escena:
    """Toda pasada nocturna tiene record idéntico en los dos brazos; toda pasada diurna tiene record en el brazo
    diurno (vía, dayflag 1, con ángulos) y ninguno en el control, salvo que se diga."""

    def __init__(self):
        self.pasadas, self.rc, self.rb = [], [], []

    def noche(self, vol, sensor, dia, estado="rutina", vrp=None, pub=False, disp=0.0, pub_b=None, hora=5):
        ins = t(dia, hora)
        self.pasadas.append(pas(vol, sensor, ins, estado, vrp))
        self.rc.append(rec(vol, sensor, ins, pub, disp))
        self.rb.append(rec(vol, sensor, ins, pub if pub_b is None else pub_b, disp))
        return self

    def dia(self, vol, sensor, dia, estado="rutina", vrp=None, pub_b=False, disp_b=0.3, hora=17, minuto=0,
            fuente="CONS", con_record=True, **kw):
        ins = t(dia, hora, minuto)
        self.pasadas.append(pas(vol, sensor, ins, estado, vrp, fuente))
        if con_record:
            self.rb.append(rec(vol, sensor, ins, pub_b, disp_b, **kw))
        return self

    def extra_brazo(self, vol, sensor, dia, hora, minuto, disp):
        """Una publicación diurna del brazo en una pasada que MIROVA no lista (M8)."""
        self.rb.append(rec(vol, sensor, t(dia, hora, minuto), True, disp))
        return self

    def base(self, sensores=SENS):
        """Fondo neutro por sensor: 10 negativos nocturnos (el control publica 1) y 40 negativos diurnos sin publicar,
        todos en W2, sin Chillán (así sacar Chillán no cambia el fondo)."""
        for s in sensores:
            for i in range(10):
                self.noche(VOLS_SIN_CH[i % 10], s, 1 + i, pub=(i == 0), disp=0.2)
            for i in range(40):
                self.dia(VOLS_SIN_CH[i % 10], s, 1 + (i % 20), hora=17 if i < 20 else 18)
        return self

    def evaluar(self, **kw):
        return ev.evaluar(self.pasadas, {C: self.rc, B: self.rb}, C, B, p_sup=P_SUP, sha=SHA, ventanas=VENT, **kw)


def publicar_negativos(e, s, n, vol=None):
    k = 0
    for r in e.rb:
        if k < n and r["b"] == s and r["es_dia"] and not r["pub"] and (vol is None or r["vol"] == vol):
            r["pub"], r["disp"] = True, 0.3
            k += 1
    assert k == n
    return e


def sensor(r, s):
    assert s in r["por_sensor"], "el sensor %s no se evaluó" % s
    return r["por_sensor"][s]


def limpio(r):
    return not r["compuertas"]["invalido"] and not r["compuertas"]["indecidible"] and not r["r1"]


# ------------------------------------------------------------------------------------------- reglas puras (§4)
@pytest.mark.parametrize("base,sch,sw7,m5,m8,esperado", [
    (AD, AD, AD, (0, None), 0, AD),
    (AD, NO, AD, (0, None), 0, DM4),          # R-CH
    (AD, SC, AD, (0, None), 0, AD),           # R-CH sólo con NO ADOPTAR sin Chillán
    (NO, NO, NO, (0, None), 0, DM4),          # R-W7 tal como está escrito: también con el base en NO ADOPTAR
    (AD, AD, NO, (0, None), 0, DM4),          # R-W7
    (AD, AD, SC, (0, None), 0, AD),
    (AD, AD, AD, (5, 2.5), 0, DE),            # M5 con 5 pares fuera de 0,5 a 2
    (AD, AD, AD, (5, 0.49), 0, DE),
    (AD, AD, AD, (5, 2.0), 0, AD),            # borde incluido
    (AD, AD, AD, (5, 0.5), 0, AD),
    (AD, AD, AD, (4, 9.0), 0, AD),            # con menos de 5 pares sólo se informa
    (NO, NO, AD, (6, 9.0), 0, NO),            # M5 sólo impide ADOPTAR
    (AD, AD, AD, (0, None), 5, DM4),          # M8
    (AD, AD, AD, (0, None), 4, AD),
    (SC, SC, SC, (0, None), 9, SC),           # M8 sólo impide ADOPTAR
    (AD, AD, AD, (5, 3.0), 5, DM4),           # M5 y M8 a la vez: manda CON M4
])
def test_aplicar_modificadores(base, sch, sw7, m5, m8, esperado):
    assert ev.aplicar_modificadores(base, sch, sw7, m5, m8)[0] == esperado


@pytest.mark.parametrize("v375,v750,esperado", [
    (AD, AD, AD), (AD, SC, AD), (SC, AD, AD),          # sin la cláusula de VIIRS 750 de S163
    (AD, NO, DE), (NO, AD, DE),
    (NO, SC, NO), (SC, SC, NO), (NO, NO, NO),
    (DM4, AD, DM4), (DE, AD, DE), (DE, DM4, DM4),
])
def test_veredicto_viirs(v375, v750, esperado):
    assert ev.veredicto_viirs(v375, v750) == esperado


def test_veredicto_flags_compuertas_y_modis():
    ps = {MOD: {"veredicto": AD}, V375: {"veredicto": SC}, V750: {"veredicto": AD}}
    vacio = {"invalido": [], "indecidible": []}
    assert ev.veredicto_flags(vacio, [], ps) == {FM: AD, FV: AD}
    assert ev.veredicto_flags({"invalido": ["x"], "indecidible": []}, [], ps) == {FM: ev.INVALIDO, FV: ev.INVALIDO}
    assert ev.veredicto_flags({"invalido": [], "indecidible": ["y"]}, [], ps) == {FM: ev.INDECIDIBLE,
                                                                                  FV: ev.INDECIDIBLE}
    assert ev.veredicto_flags(vacio, ["una"], ps) == {FM: ev.INVALIDO, FV: ev.INVALIDO}
    assert ev.veredicto_flags(vacio, [], dict(ps, MODIS={"veredicto": NO}))[FM] == NO
    sin_modis = {k: v for k, v in ps.items() if k != MOD}
    assert ev.veredicto_flags(vacio, [], sin_modis)[FM] == ev.INVALIDO


def test_veredicto_final_por_flag():
    pr = {FM: AD, FV: NO}
    f = ev.veredicto_final_flags(pr, {"tabla": {FM: AD, FV: NO}, "sin_W2": {FM: NO, FV: NO}})
    assert f[FM][0] == DE and f[FV][0] == NO


def test_opcion_e_sellada_es_e_ii():
    assert ev.OPCION_E == "e-ii"


# ------------------------------------------------------------------------------------------- escenas
def test_base_limpia_y_sin_publicar():
    r = Escena().base().evaluar()
    assert limpio(r), r["compuertas"]
    assert r["flags"] == {FM: SC, FV: NO}
    assert all(sensor(r, s)["P_obs"] == 0 for s in SENS)


def test_modis_entra_a_la_regla_y_adopta_con_protegidas_recuperadas():
    e = Escena().base()
    e.dia("Lascar", MOD, 3, "alerta", 3.0, pub_b=True, disp_b=3.0, hora=16)
    e.dia("Lastarria", MOD, 4, "alerta", 2.0, pub_b=True, disp_b=2.0, hora=16)
    r = e.evaluar()
    assert limpio(r), r["compuertas"]
    m = sensor(r, MOD)
    assert (m["P"], m["P_obs"], m["base"], m["veredicto"]) == (2, 2, AD, AD)
    assert r["flags"][FM] == AD


def test_modis_negativos_publicados_pesan_en_el_neto():
    """El control sintético de día tiene que cubrir MODIS: si no, los negativos que el brazo publica no entran al neto."""
    e = Escena().base()
    e.dia("Lascar", MOD, 3, "alerta", 3.0, pub_b=True, disp_b=3.0, hora=16)
    e.dia("Lastarria", MOD, 4, "alerta", 2.0, pub_b=True, disp_b=2.0, hora=16)
    publicar_negativos(e, MOD, 3, vol="Isluga")
    r = e.evaluar()
    m = sensor(r, MOD)
    assert m["neto"] == 3 and m["neg_pub"] == 3
    assert m["base"] == DM4 and r["flags"][FM] == DM4


def test_r_ch_beneficio_solo_de_chillan_pasa_a_decide_con_m4():
    e = Escena().base()
    e.dia("NevadosDeChillan", V375, 3, "alerta", 2.0, pub_b=True, disp_b=2.0, hora=16)
    e.dia("NevadosDeChillan", V375, 4, "alerta", 2.0, pub_b=True, disp_b=2.0, hora=16)
    e.dia("Lascar", V375, 5, "alerta", 0.5, pub_b=True, disp_b=0.5, hora=16)
    publicar_negativos(e, V375, 1, vol="Lastarria")
    r = e.evaluar()
    assert limpio(r), r["compuertas"]
    m = sensor(r, V375)
    assert (m["base"], m["sin_chillan"]) == (AD, NO)
    assert m["veredicto"] == DM4 and r["flags"][FV] == DM4


def test_r_ch_no_actua_si_el_beneficio_no_es_de_chillan():
    e = Escena().base()
    e.dia("Copahue", V375, 3, "alerta", 2.0, pub_b=True, disp_b=2.0, hora=16)
    e.dia("Copahue", V375, 4, "alerta", 2.0, pub_b=True, disp_b=2.0, hora=16)
    e.dia("Lascar", V375, 5, "alerta", 0.5, pub_b=True, disp_b=0.5, hora=16)
    publicar_negativos(e, V375, 1, vol="Lastarria")
    r = e.evaluar()
    m = sensor(r, V375)
    assert (m["base"], m["sin_chillan"], m["veredicto"]) == (AD, AD, AD)
    assert r["flags"][FV] == AD


def test_r_w7_beneficio_solo_de_w7_pasa_a_decide_con_m4():
    e = Escena().base()
    e.dia("Lascar", V375, 22, "alerta", 2.0, pub_b=True, disp_b=2.0, hora=16)
    e.dia("Lascar", V375, 23, "alerta", 2.0, pub_b=True, disp_b=2.0, hora=16)
    e.dia("Lastarria", V375, 5, "alerta", 0.5, pub_b=True, disp_b=0.5, hora=16)
    publicar_negativos(e, V375, 1, vol="Isluga")
    r = e.evaluar()
    assert limpio(r), r["compuertas"]
    m = sensor(r, V375)
    assert (m["base"], m["sin_W7"]) == (AD, NO)
    assert m["veredicto"] == DM4 and r["flags"][FV] == DM4


def test_r_w7_tal_como_esta_escrito_con_un_brazo_malo_en_todas_las_ventanas():
    """Lectura literal del §4: «no cambia el veredicto salvo que sin W7 salga NO ADOPTAR». Un brazo que publica sin
    discriminar en W2 sale NO ADOPTAR con y sin W7, y por R-W7 queda DECIDE NICOLÁS CON M4, no NO ADOPTAR. Se deja
    fijado y se informa a Nicolás (no es un ADOPTAR, así que no viola el control del brazo ruidoso)."""
    e = Escena().base()
    publicar_negativos(e, V750, 30)
    r = e.evaluar()
    m = sensor(r, V750)
    assert (m["base"], m["sin_W7"], m["veredicto"]) == (NO, NO, DM4)


def test_m8_cinco_publicaciones_de_1_mw_sin_fila_de_mirova_impiden_adoptar():
    e = Escena().base()
    e.dia("Lascar", V750, 3, "alerta", 2.0, pub_b=True, disp_b=2.0, hora=16)
    e.dia("Lastarria", V750, 4, "alerta", 2.0, pub_b=True, disp_b=2.0, hora=16)
    for i in range(5):
        e.extra_brazo(VOLS_SIN_CH[i], V750, 6 + i, 15, 30, 1.5)
    r = e.evaluar()
    assert limpio(r), r["compuertas"]
    m = sensor(r, V750)
    assert m["M8"]["n_1mw"] == 5 and len(m["M8"]["lista"]) == 5
    assert (m["base"], m["veredicto"]) == (AD, DM4)
    assert r["flags"][FV] == DM4


def test_m8_cuatro_no_bastan_y_lo_bajo_1_mw_no_cuenta():
    e = Escena().base()
    e.dia("Lascar", V750, 3, "alerta", 2.0, pub_b=True, disp_b=2.0, hora=16)
    e.dia("Lastarria", V750, 4, "alerta", 2.0, pub_b=True, disp_b=2.0, hora=16)
    for i in range(4):
        e.extra_brazo(VOLS_SIN_CH[i], V750, 6 + i, 15, 30, 1.5)
    e.extra_brazo("Copahue", V750, 12, 15, 30, 0.9)
    r = e.evaluar()
    m = sensor(r, V750)
    assert m["M8"]["n_1mw"] == 4 and len(m["M8"]["lista"]) == 5
    assert m["veredicto"] == AD and r["flags"][FV] == AD


def test_m8_no_cuenta_publicaciones_en_pasadas_que_mirova_lista():
    e = Escena().base()
    publicar_negativos(e, V750, 6)
    m8 = ev.publicaciones_sin_fila(e.pasadas, e.rb)
    assert m8[V750]["lista"] == [] and m8[V750]["n_1mw"] == 0


def test_m5_magnitud_fuera_de_rango_con_cinco_pares_impide_adoptar():
    e = Escena().base()
    for i in range(5):
        e.dia(VOLS_SIN_CH[i], V375, 3 + i, "alerta", 2.0, pub_b=True, disp_b=6.0, hora=16)
    r = e.evaluar()
    m = sensor(r, V375)
    assert m["M5"][0] == 5 and m["M5"][1] == pytest.approx(3.0)
    assert (m["base"], m["veredicto"]) == (AD, DE)
    assert r["flags"][FV] == DE


def test_m5_con_cuatro_pares_se_informa():
    e = Escena().base()
    for i in range(4):
        e.dia(VOLS_SIN_CH[i], V375, 3 + i, "alerta", 2.0, pub_b=True, disp_b=6.0, hora=16)
    r = e.evaluar()
    m = sensor(r, V375)
    assert m["M5"][0] == 4 and m["veredicto"] == AD


# ------------------------------------------------------------------------------------------- compuertas
def test_i2_marcador_es_el_dayflag_de_la_via():
    """Un brazo cuyos records diurnos MODIS llegan con dayflag 0 no ejerció la rama diurna del .m: I2 falla."""
    e = Escena().base()
    for r in e.rb:
        if r["b"] == MOD and r["es_dia"]:
            r["dayflag"] = 0
    r = e.evaluar()
    assert any(x.startswith("I2 W2 MODIS") for x in r["compuertas"]["invalido"]), r["compuertas"]
    assert r["flags"] == {FM: ev.INVALIDO, FV: ev.INVALIDO}


def test_i2_no_mira_el_marcador_viejo_de_k():
    """Los records de la vía no traen diag_umbrales_diurnos; con dayflag 1 I2 pasa."""
    e = Escena().base()
    assert all("diag_dia" not in r for r in e.rb)
    assert not any(x.startswith("I2") for x in e.evaluar()["compuertas"]["invalido"])


def test_i2_control_con_records_diurnos_invalida():
    e = Escena().base()
    e.rc.append(rec("Lascar", MOD, t(2, 17, 30)))
    r = e.evaluar()
    assert any(x.startswith("I2: el control") for x in r["compuertas"]["invalido"])
    assert r["flags"][FM] == ev.INVALIDO


def test_i2_record_diurno_de_la_via_sin_angulos_invalida():
    e = Escena().base()
    e.rb.append(rec("Lascar", V375, t(2, 17, 30), soz=None))
    r = e.evaluar()
    assert any("sin solar_zenith_deg" in x for x in r["compuertas"]["invalido"]), r["compuertas"]
    assert r["flags"][FV] == ev.INVALIDO


def test_i2_record_diurno_de_k_sin_angulos_no_es_de_la_via():
    e = Escena().base()
    e.rb.append(rec("Lascar", V375, t(2, 17, 30), soz=None, via="sin_grilla"))
    assert not any("sin solar_zenith_deg" in x for x in e.evaluar()["compuertas"]["invalido"])


def test_tabla_dayflag_contra_elevacion_informa_el_crepusculo():
    e = Escena().base(sensores=(MOD,))
    e.rc.append(rec("Lascar", MOD, t(25, 5), dayflag=1))
    e.rb.append(rec("Lascar", MOD, t(25, 5), dayflag=1))
    tab = ev.tabla_dayflag({C: e.rc, B: e.rb})
    assert tab["%s|MODIS|noche|dayflag=1" % C] == 1 and tab["%s|MODIS|noche|dayflag=1" % B] == 1
    assert tab["%s|MODIS|dia|dayflag=1" % B] == 40


def test_i1_flags_de_la_via_y_del_dia_por_brazo():
    def fl(diurno):
        d = {"PROFILE_NAME": B if diurno else C, "DATA_SUBDIR": B if diurno else C, "ENABLE_TEST1_PATH": False,
             "ENABLE_TESTS_23_PROSE_BRANCH": True, "ENABLE_MODIS_B22_PRIMARY": True, "ENABLE_DAYTIME_VIIRS": diurno,
             "ENABLE_DAYTIME_MODIS": diurno}
        d.update({k: True for k in ev.FLAGS_VIA})
        return d
    assert ev.problemas_flags(fl(False), C, C, "x") == []
    assert ev.problemas_flags(fl(True), B, C, "x") == []
    assert any("ENABLE_DAYTIME_MODIS" in x for x in ev.problemas_flags(dict(fl(True), ENABLE_DAYTIME_MODIS=False), B, C,
                                                                       "x"))
    assert any("ENABLE_DAYTIME_MODIS" in x for x in ev.problemas_flags(dict(fl(False), ENABLE_DAYTIME_MODIS=True), C,
                                                                       C, "x"))
    for k in ev.FLAGS_VIA:
        assert any(k in x for x in ev.problemas_flags(dict(fl(True), **{k: False}), B, C, "x")), k
    assert ev.problemas_flags(None, B, C, "x") == ["I1a x: sin línea FLAGS_BRAZO"]


def test_i1_sha_distinto_invalida():
    e = Escena().base()
    e.rb[0]["sha"] = "b" * 40
    r = e.evaluar()
    assert any(x.startswith("I1 ") for x in r["compuertas"]["invalido"])
    with pytest.raises(ValueError):
        ev.evaluar(e.pasadas, {C: e.rc, B: e.rb}, C, B, p_sup=P_SUP, sha=SHA[:12], ventanas=VENT)


def test_i4_cubre_modis():
    e = Escena().base()
    e.dia("Lascar", MOD, 3, "alerta", 3.0, hora=16, con_record=False)
    quitados = 0
    for r in list(e.rb):
        if quitados < 10 and r["b"] == MOD and r["es_dia"]:
            e.rb.remove(r)
            quitados += 1
    r = e.evaluar()
    inv = r["compuertas"]["invalido"]
    assert any(x.startswith("I4a Lascar|MODIS") for x in inv), inv
    assert any(x.startswith("I4c MODIS") for x in inv), inv
    assert r["cobertura_diurna"].get(MOD, {}).get("pasadas_diurnas") == 41


def test_i5_noche_distinta_es_indecidible():
    e = Escena().base()
    for r in e.rb:
        if r["b"] == MOD and not r["es_dia"] and not r["pub"]:
            r["pub"], r["disp"] = True, 0.4
            break
    r = e.evaluar()
    assert any(x.startswith("I5") for x in r["compuertas"]["indecidible"])
    assert r["flags"] == {FM: ev.INDECIDIBLE, FV: ev.INDECIDIBLE}


# ------------------------------------------------------------------------------------------- M6 y M7
def test_m6_diurnos_que_cayeron_a_k_no_entran_a_la_regla():
    e = Escena().base()
    e.dia("Lascar", MOD, 3, "alerta", 3.0, pub_b=True, disp_b=3.0, hora=16, via="sin_mxd03")
    e.dia("Lastarria", MOD, 4, "alerta", 2.0, pub_b=True, disp_b=2.0, hora=16, via="sin_grilla")
    r = e.evaluar()
    assert limpio(r), r["compuertas"]
    assert len(r["M6_diurnos_de_K"]) == 2 and len(r["M6_pasadas_fuera_de_la_regla"]) == 2
    m = sensor(r, MOD)
    assert (m["P_obs"], m["P"]) == (0, 0)
    assert r["flags"][FM] == SC


def test_m7_cuenta_el_reflejo_y_la_sospecha():
    e = Escena().base()
    r = e.evaluar()
    assert r["M7_sospecha"] is True
    for x in e.rb:
        if x["b"] == V750 and x["es_dia"]:
            x["motivo"] = "sunglint"
            break
    e.rb.append(rec("Lascar", MOD, t(2, 17, 40), motivo="sunglint"))
    r = e.evaluar()
    assert r["M7_reflejo"][B].get(V750) == {"dia": 1, "noche": 0}
    assert r["M7_reflejo"][B].get(MOD, {}).get("dia") == 1
    assert r["M7_sospecha"] is False


def test_m7_lee_motivo_vacio_del_record():
    lig = ev.record_ligero({"via_codigo_mirova": True, "diag_codigo_mirova": {"motivo_vacio": "sunglint", "dayflag": 1},
                            "solar_zenith_deg": 40.0}, "Lascar", MOD, t(2, 17), True)
    assert (lig["motivo"], lig["dayflag"], lig["soz"], lig["via"]) == ("sunglint", 1, 40.0, True)


# ------------------------------------------------------------------------------------------- carga y pasadas
def test_pasadas_de_conserva_el_dia_de_modis(monkeypatch):
    p_dia = pas("Lascar", MOD, t(3, 17), "rutina")
    p_noche = pas("Lascar", MOD, t(3, 5), "rutina")
    p_fuera = pas("Lascar", MOD, datetime(2026, 9, 3, 17), "rutina")
    monkeypatch.setattr(ev.cm, "resumir_pasadas", lambda filas, **kw: [p_dia, p_noche, p_fuera])
    assert ev.pasadas_de([], "union", VENT) == [p_dia, p_noche]


def test_cargar_brazo_conserva_modis_de_dia_y_lee_la_via(tmp_path):
    base = {"vrp_mw": 0.0, "primary_cluster": None, "distance_class": None, "anomaly_pixels": [],
            "via_codigo_mirova": True, "regimen": {"codigo_sha": SHA}, "triggered_test1": False}
    recs = [dict(base, sensor="MODIS_AQUA", datetime_utc="2026-08-03 17:00", solar_zenith_deg=50.0,
                 diag_codigo_mirova={"dayflag": 1, "motivo_vacio": "sunglint"}),
            dict(base, sensor="MODIS_AQUA", datetime_utc="2026-08-03 05:00", solar_zenith_deg=120.0,
                 diag_codigo_mirova={"dayflag": 0, "motivo_vacio": None}),
            dict(base, sensor="VIIRS_NOAA20_750", datetime_utc="2026-08-03 17:10", solar_zenith_deg=50.0,
                 diag_codigo_mirova={"dayflag": 1, "motivo_vacio": None})]
    (tmp_path / B).mkdir()
    (tmp_path / B / "Lascar.json").write_text(json.dumps({"records": recs}), encoding="utf-8")
    out = ev.cargar_brazo([str(tmp_path)], B, VENT, {v: 5.0 for v in VOLS})
    got = sorted((r["b"], r["es_dia"], r["dayflag"], r["motivo"], r["pub"]) for r in out)
    assert got == [(MOD, False, 0, None, False), (MOD, True, 1, "sunglint", False), (V750, True, 1, None, False)]


def test_main_se_niega_con_referencia_distinta_o_dias_malos(tmp_path):
    import sustrato_k as sk
    ref = tmp_path / "ref"
    ref.mkdir()
    for n in sk.ARCHIVOS_REF:
        (ref / n).write_text("x", encoding="utf-8")
    sus = tmp_path / "sus.json"
    sus.write_text(json.dumps({"sha256": {n: "0" * 64 for n in sk.ARCHIVOS_REF}}), encoding="utf-8")
    assert ev.main(["--raiz", str(tmp_path), "--ref", str(ref), "--sustrato", str(sus), "--sha-codigo", SHA]) == 3
    sus.write_text(json.dumps({"sha256": {n: ev.ek.sha256(ref / n) for n in sk.ARCHIVOS_REF}}), encoding="utf-8")
    exc = tmp_path / "exc.json"
    exc.write_text(json.dumps({"excluir_dias": ["2026-12-01"]}), encoding="utf-8")
    assert ev.main(["--raiz", str(tmp_path), "--ref", str(ref), "--sustrato", str(sus), "--sha-codigo", SHA,
                    "--excluidos", str(exc)]) == 4


def test_vara_de_los_tres_sensores_en_el_sustrato_sellado():
    """El sustrato de la adenda trae la vara de I4 (c) de los tres sensores y el evaluador la convierte con la misma
    cota de Clopper-Pearson que S163."""
    sus = json.loads((AQUI / "sustrato_via.json").read_text(encoding="utf-8"))
    ps = ev.p_sup_de_vara(sus["vara_cobertura_nocturna_produccion"])
    assert set(ps) == set(SENS)
    for s in SENS:
        assert ps[s] == pytest.approx(sus["vara_cobertura_nocturna_produccion"][s]["p_sup"])
        assert 0 < ps[s] < 0.1
