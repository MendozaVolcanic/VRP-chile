# -*- coding: utf-8 -*-
"""Pruebas del evaluador pre-registrado del control diurno de VIIRS (S195).

POR QUÉ. El evaluador se sella antes de medir. Para creerle hay que mostrar, con datos sintéticos de verdad conocida,
que (A116) puede dar CUMPLE, NO CUMPLE, SIN PODER e INVALIDO; que (A110) una regla que no distingue el calor volcánico
de la mancha solar no pasa; y que una mutación del criterio la atrapa una aserción
(`experiments/_s195_viirs_dia_control/mutar.py` corre este archivo contra copias mutadas, sin las pruebas de sello).

`EVALUAR_VDIA_PATH` apunta a la copia que se prueba; por defecto, el evaluador del repo.
"""
import hashlib
import importlib.util
import math
import os
import re
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RUTA_REPO = ROOT / "experiments" / "_s195_viirs_dia_control" / "evaluar.py"
RUTA = Path(os.environ.get("EVALUAR_VDIA_PATH", str(RUTA_REPO)))


def _cargar(ruta, nombre):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


E = _cargar(RUTA, "evaluar_viirs_dia_control_s195")

VOL = "Lascar"
INNER = {VOL: 5.0}
T0 = datetime(2026, 4, 1, 18, 0)
CRATER, FLANCO = (60, 60), (80, 80)


def _rec(dt, celdas, b="VIIRS375", es_dia=True, pub=True, disp=2.0, lat=None, lon=None, vol=VOL, sensor=None):
    return {"vol": vol, "b": b, "sensor": sensor or ("VIIRS_NOAA20" if b == "VIIRS375" else "VIIRS_NOAA20_750"),
            "dt": dt, "es_dia": es_dia, "pub": pub, "disp": disp, "lat": lat, "lon": lon,
            "celdas": [(c[0], c[1], c[2] if len(c) > 2 else 300.0) for c in celdas]}


def _pas(dt, estado="rutina", vrp=None, dist=None, fuente="CONS", b="VIIRS375", vol=VOL):
    return {"vol": vol, "b": b, "dt": dt, "estado": estado, "vrp_mw": vrp, "dist_km": dist, "fuente": fuente,
            "es_dia": True}


def escenario(n_dias=20, celda_artefacto=FLANCO, celdas_noche=(CRATER,), quitar_noches=(), noches_brazo_distintas=False,
              sin_record_de=(), r_pubs=0, artefacto_cada=2):
    """Un volcán, una ventana de `n_dias` desde el 2026-04-01. Cada día una publicación P en el cráter (la tabla de
    MIROVA alertó 3 MW a 0,5 km) y, cada `artefacto_cada` días, una publicación A en `celda_artefacto` (la tabla dice
    RUTINA). Una noche por día y grilla con `celdas_noche` alertadas desde 30 días antes."""
    ventanas = (("T", "2026-04-01", (date(2026, 4, 1) + timedelta(days=n_dias - 1)).isoformat()),)
    noches = []
    for i in range(-E.DIAS_HISTORIA, n_dias):
        d = datetime(2026, 4, 1, 5, 0) + timedelta(days=i)
        if i in quitar_noches:
            continue
        for b in E.SENSORES_VIIRS:
            noches.append(_rec(d + timedelta(minutes=10 * (b == "VIIRS750")), list(celdas_noche), b=b, es_dia=False,
                               pub=False, disp=0.0))
    dia, pasadas = [], []
    for i in range(n_dias):
        t = T0 + timedelta(days=i)
        dia.append(_rec(t, [CRATER + (320.0,)], disp=3.0))
        pasadas.append(_pas(t, "alerta", 3.0, 0.5))
        if i % artefacto_cada == 0:
            ta = t + timedelta(minutes=30)
            dia.append(_rec(ta, [tuple(celda_artefacto) + (310.0,)], disp=2.0))
            pasadas.append(_pas(ta, "rutina", 0.0, None))
        if i < r_pubs:
            tr = t + timedelta(minutes=50)
            dia.append(_rec(tr, [tuple(celda_artefacto) + (310.0,)], disp=2.0))   # MIROVA sin la pasada, cumbre cerca
    dia = [r for r in dia if r["dt"] not in sin_record_de]
    brazo_noches = [dict(r, celdas=[(1, 1, 300.0)]) for r in noches] if noches_brazo_distintas else noches
    return E.evaluar_fase(dia + brazo_noches, noches, pasadas, {}, {}, INNER, ventanas, [VOL])


# ----------------------------------------------------------------------------------------------- sello
def test_sello_valores():
    """Los valores del PREREGISTRO.md: cambiar uno exige un pre-registro nuevo."""
    assert (E.DIAS_HISTORIA, E.VECINDAD, E.UMBRAL_MW, E.TOL_S, E.DIAS_SWIR, E.HORAS_MIROVA_VECINA) == (
        30, 1, 1.0, 120, 3, 12)
    assert (E.N_MIN_A, E.N_MIN_P, E.QUITAR_A, E.MAX_P_PERDIDAS, E.MAX_R_PERDIDAS) == (6, 5, (2, 3), 0, (1, 3))
    assert E.ALFA_REGLA == {"R1": 0.04, "R2": 0.01} and E.ORDEN_REGLAS == ("R1", "R2")
    assert abs(sum(E.ALFA_REGLA.values()) - 0.05) < 1e-12
    assert (E.MIN_FRAC_DIAS_HISTORIA, E.MAX_FRAC_SIN_CELDAS, E.MAX_FRAC_MIROVA_SIN_RECORD, E.MIN_ACUERDO_NOCHE) == (
        0.90, 0.01, 0.05, 0.95)
    assert E.BRAZO == "_s190_ab_diurno_via_on" and E.FECHA_MIN_VEREDICTO == "2027-03-07"
    assert E.VENTANAS_VEREDICTO == (("V1", "2026-04-01", "2026-06-12"), ("V2", "2026-07-01", "2026-07-19"),
                                    ("V3", "2026-08-01", "2026-08-12"), ("V4", "2026-09-21", "2026-09-30"),
                                    ("V5", "2026-11-23", "2027-02-28"))
    assert E.PASO_M == {"VIIRS375": 375, "VIIRS750": 750} and (E.n_grilla("VIIRS375"), E.n_grilla("VIIRS750")) == (134, 67)


def test_sello_hash_del_evaluador_en_el_preregistro():
    """El pre-registro declara el sha256 del evaluador (LF). Editar el evaluador sin re-sellar cae aquí."""
    txt = (RUTA_REPO.parent / "PREREGISTRO.md").read_text(encoding="utf-8")
    m = re.search(r"sha256 del evaluador \(fin de línea LF\): `([0-9a-f]{64})`", txt)
    assert m, "el PREREGISTRO.md no declara el sha256 del evaluador"
    h = hashlib.sha256(RUTA_REPO.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    assert h == m.group(1), "evaluar.py cambió después del sello: %s != %s" % (h, m.group(1))


def test_sello_ventanas_de_veredicto_no_tocan_las_de_desarrollo():
    """Los datos que deciden no se miraron: ninguna fecha de veredicto cae en W2 a W7, y V5 empieza después del sello."""
    def dias(ws):
        out = set()
        for _, a, b in ws:
            d = date.fromisoformat(a)
            while d <= date.fromisoformat(b):
                out.add(d)
                d += timedelta(days=1)
        return out
    assert not dias(E.VENTANAS_VEREDICTO) & dias(E.VENTANAS_DESARROLLO)
    assert date.fromisoformat(E.VENTANAS_VEREDICTO[-1][1]) > date(2026, 11, 22)
    assert min(dias(E.VENTANAS_VEREDICTO)) >= date(2026, 4, 1)          # A119: VIIRS por pasada desde abril


def test_sello_chillan_caja_nhi_corregida():
    """Re-sello S196 (2026-11-23, decisión de Nicolás «Corregir y re-sellar»): NHI-v1 corrigió el centro de Nevados de
    Chillán (PR #1 de NHI-v1, merge 55461a4fa6d2; cajas en el commit 4d24515abe1e) y su caja ahora contiene el punto del
    volcán de volcanoes.yaml, así que su serie SWIR puede respaldar o desmentir publicaciones de Chillán. Antes del
    re-sello (cajas en 09c45707e9a6) el centro estaba a 61 km, junto a Antuco, y la caja no era usable."""
    # Texto anterior (sello S195, conservado por A113):
    #   def test_sello_chillan_sin_respaldo_nhi():
    #       """NHI-v1 (commit fijado) centra Nevados de Chillán a 61 km del volcán: su serie no puede respaldar nada."""
    #       cajas = E.cargar_cajas()
    #       assert cajas["NevadosDeChillan"]["usable"] is False
    cajas = E.cargar_cajas()
    assert cajas["NevadosDeChillan"]["usable"] is True
    assert cajas["NevadosDeChillan"]["dist_centro_yaml_km"] < 1.0
    assert all(cajas[v]["usable"] for v in ("Lascar", "Villarrica", "Isluga", "Tupungatito", "PuyehueCordonCaulle"))
    assert "Lastarria" not in cajas


def test_veredicto_no_se_mide_antes_de_la_fecha():
    assert not E.puede_medir_veredicto("2027-03-06") and E.puede_medir_veredicto("2027-03-07")
    assert not E.puede_medir_veredicto("2026-11-22")


# ----------------------------------------------------------------------------------------------- la regla
def test_historia_vecindad_de_una_celda():
    h = {(61, 61)}
    assert E.con_historia((60, 60), h) and not E.con_historia((62, 62), {(60, 60)})
    assert E.con_historia((60, 62), {(60, 61)}) and not E.con_historia((60, 63), {(60, 61)})


def test_historia_estrictamente_previa_y_de_30_dias():
    t = datetime(2026, 5, 1, 18, 0)
    noches = [_rec(t - timedelta(days=29, hours=12), [CRATER], es_dia=False),
              _rec(t - timedelta(days=31), [FLANCO], es_dia=False),
              _rec(t + timedelta(hours=11), [(70, 70)], es_dia=False)]
    idx = E.indexar_noches(noches)
    assert E.celdas_historia(idx, VOL, "VIIRS375", t) == {CRATER}


def test_historia_por_volcan_y_por_grilla_y_solo_de_noche():
    t = datetime(2026, 5, 1, 18, 0)
    recs = [_rec(t - timedelta(days=1), [CRATER], b="VIIRS750", es_dia=False),
            _rec(t - timedelta(days=1), [CRATER], es_dia=False, vol="Villarrica"),
            _rec(t - timedelta(days=1), [CRATER], es_dia=True)]
    idx = E.indexar_noches(recs)
    assert E.celdas_historia(idx, VOL, "VIIRS375", t) == set()
    assert E.celdas_historia(idx, VOL, "VIIRS750", t) == {CRATER}


def test_r1_cualquier_celda_r2_la_radiante():
    """Cráter con historia y una celda de ladera más caliente sin historia: R1 conserva, R2 no (la posición publicada
    sale de la radiante)."""
    r = _rec(T0, [CRATER + (300.0,), FLANCO + (330.0,)])
    h = {CRATER}
    assert E.conserva("R1", r, h) and not E.conserva("R2", r, h)
    r2 = _rec(T0, [CRATER + (330.0,), FLANCO + (300.0,)])
    assert E.conserva("R1", r2, h) and E.conserva("R2", r2, h)
    assert not E.conserva("R1", _rec(T0, [FLANCO]), h)


def test_radiante_desempata_por_fila_y_columna():
    assert E.radiante([(5, 5, 300.0), (4, 9, 300.0), (6, 1, 299.0)])[:2] == (4, 9)


def test_sin_celdas_se_conserva():
    assert E.conserva("R1", _rec(T0, []), set()) and E.conserva("R2", _rec(T0, []), set())


# ----------------------------------------------------------------------------------------------- etiquetas
CAJA = {"lat": -23.37, "lon": -67.73, "buffer_km": 3.0, "usable": True}


def test_etiquetas_con_mirova():
    r = _rec(T0, [CRATER], disp=2.0)
    assert E.etiquetar(r, _pas(T0, "alerta", 1.0, 5.0), 5.0, None, None) == "P"
    assert E.etiquetar(r, _pas(T0, "alerta", 0.99, 1.0), 5.0, None, None) == "O"
    assert E.etiquetar(r, _pas(T0, "alerta", 3.0, 5.01), 5.0, None, None) == "O"
    assert E.etiquetar(r, _pas(T0, "alerta", 3.0, 1.0, fuente="OCR"), 5.0, None, None) == "O"
    assert E.etiquetar(r, _pas(T0, "sin_geometria"), 5.0, None, None) == "O"
    assert E.etiquetar(r, _pas(T0, "rutina", 0.0), 5.0, None, None) == "A"
    assert E.etiquetar(r, _pas(T0, "fp", 4.0, 12.0), 5.0, None, None) == "A"
    assert E.etiquetar(r, None, 5.0, None, None) == "A"
    assert E.etiquetar(dict(r, disp=0.99), _pas(T0, "rutina"), 5.0, None, None) == "menor"


def test_etiqueta_r_por_swir_en_su_caja_y_a_tres_dias():
    r = _rec(T0, [CRATER], lat=-23.37, lon=-67.73)
    esc = lambda dd, al=True: [{"fecha": (T0.date() + timedelta(days=dd)).isoformat(), "alerta": al}]
    assert E.etiquetar(r, _pas(T0), 5.0, CAJA, esc(3)) == "R"
    assert E.etiquetar(r, _pas(T0), 5.0, CAJA, esc(-3)) == "R"
    assert E.etiquetar(r, _pas(T0), 5.0, CAJA, esc(4)) == "A"
    assert E.etiquetar(r, _pas(T0), 5.0, CAJA, esc(0, False)) == "A"
    assert E.etiquetar(r, _pas(T0), 5.0, dict(CAJA, usable=False), esc(0)) == "A"
    fuera = dict(r, lat=-23.37 - 3.2 / 111.0)                          # 3,2 km al sur: fuera de la caja de 3 km
    assert E.etiquetar(fuera, _pas(T0), 5.0, CAJA, esc(0)) == "A"


def test_etiqueta_r_por_cumbre_de_mirova_solo_si_mirova_no_tiene_la_pasada():
    r = _rec(T0, [CRATER])
    assert E.etiquetar(r, None, 5.0, None, None, cumbre_cerca=True) == "R"
    assert E.etiquetar(r, _pas(T0, "rutina"), 5.0, None, None, cumbre_cerca=True) == "A"


def test_cumbre_alertada_cerca():
    ps = [_pas(T0 + timedelta(hours=11), "alerta", 1.0, 5.0, b="MODIS")]
    assert E.cumbre_alertada_cerca(ps, T0, 5.0)
    assert not E.cumbre_alertada_cerca([dict(ps[0], dt=T0 + timedelta(hours=13))], T0, 5.0)
    assert not E.cumbre_alertada_cerca([dict(ps[0], fuente="OCR")], T0, 5.0)
    assert not E.cumbre_alertada_cerca([dict(ps[0], vrp_mw=0.9)], T0, 5.0)
    assert not E.cumbre_alertada_cerca([dict(ps[0], dist_km=5.5)], T0, 5.0)


def test_pareo_con_mirova_a_120_s_y_mismo_sensor():
    idx = E.indexar_pasadas([_pas(T0 + timedelta(seconds=121)), _pas(T0, b="VIIRS750")])
    assert E.pasada_de(idx, _rec(T0, [CRATER])) is None
    idx = E.indexar_pasadas([_pas(T0 + timedelta(seconds=120), "rutina"), _pas(T0 - timedelta(seconds=30), "alerta")])
    assert E.pasada_de(idx, _rec(T0, [CRATER]))["estado"] == "alerta"


# ----------------------------------------------------------------------------------------------- criterio
def test_p_hiper():
    assert abs(E.p_hiper(13, 6, 4, 4) - 15 / 715) < 1e-12
    assert abs(E.p_hiper(11, 6, 4, 4) - 15 / 330) < 1e-12
    assert E.p_hiper(10, 5, 0, 0) == 1.0
    assert abs(E.p_hiper(10, 5, 3, 1) - (1 - math.comb(5, 3) / math.comb(10, 3))) < 1e-12


def _regla(n_p, n_a, n_r, q_p, q_a, q_r, alfa=0.04):
    et = ["P"] * n_p + ["A"] * n_a + ["R"] * n_r
    co = [False] * q_p + [True] * (n_p - q_p) + [False] * q_a + [True] * (n_a - q_a) + [False] * q_r + [True] * (n_r - q_r)
    return E.evaluar_regla(et, co, alfa)


def test_criterio_bordes():
    assert _regla(20, 6, 0, 0, 4, 0)["estado"] == E.CUMPLE                  # 4 de 6 = 2/3 exacto
    assert _regla(20, 6, 0, 0, 3, 0)["estado"] == E.NO_CUMPLE
    assert _regla(20, 6, 0, 1, 6, 0)["estado"] == E.NO_CUMPLE              # una protegida perdida
    assert _regla(20, 6, 3, 0, 6, 1)["estado"] == E.CUMPLE                  # 1 de 3 con respaldo = 1/3 exacto
    assert _regla(20, 6, 3, 0, 6, 2)["estado"] == E.NO_CUMPLE
    assert _regla(20, 6, 4, 0, 6, 2)["estado"] == E.NO_CUMPLE              # 2 de 4 pasa de 1/3
    r = _regla(5, 6, 0, 0, 4, 0)                                            # p = 15/330 = 0,045
    assert r["estado"] == E.NO_CUMPLE and r["p"] > 0.04
    assert _regla(5, 6, 0, 0, 4, 0, alfa=0.05)["estado"] == E.CUMPLE


def test_universo_del_nulo_es_p_a_r_o():
    """Crítica 4: suprimir lo que MIROVA alertó de otra forma (O) entra al nulo; lo menor que 1 MW, no."""
    et = ["P"] * 5 + ["A"] * 6 + ["O"] * 50 + ["menor"] * 50
    co = [True] * 5 + [False] * 6 + [True] * 50 + [False] * 50
    r = E.evaluar_regla(et, co, 0.04)
    assert r["universo"] == 61 and r["k"] == 6 and abs(r["p"] - 1 / math.comb(61, 6)) < 1e-15
    co_o = [True] * 5 + [False] * 6 + [False] * 50 + [False] * 50
    r = E.evaluar_regla(et, co_o, 0.04)
    assert r["k"] == 56 and r["p"] > 0.04 and r["estado"] == E.NO_CUMPLE


def test_p_estratificado():
    """Informativo (crítica 2): estrato 1 todo A (la supresión al azar quita lo mismo); estrato 2 con 2 A de 10."""
    et = ["A"] * 4 + ["A"] * 2 + ["P"] * 8
    co = [False] * 4 + [False] * 2 + [True] * 8
    es = [("CC", "VIIRS375")] * 4 + [("Lascar", "VIIRS375")] * 10
    assert abs(E.p_estratificado(et, co, es) - 1 / 45) < 1e-12
    assert abs(E.evaluar_regla(et, co, 0.04)["p"] - 1 / math.comb(14, 6)) < 1e-15
    assert E.p_estratificado(["P", "A"], [True, True], [("x", "y")] * 2) == 1.0


def test_r0_referencia_por_volcan():
    assert not E.conserva("R0", _rec(T0, [FLANCO]), set()) and E.conserva("R0", _rec(T0, [FLANCO]), {(1, 1)})


def test_a_desmentible():
    r = _rec(T0, [CRATER], lat=-23.37, lon=-67.73)
    esc = [{"fecha": T0.date().isoformat(), "alerta": False}]
    assert E.a_desmentible(r, CAJA, esc)
    assert not E.a_desmentible(r, CAJA, [{"fecha": T0.date().isoformat(), "alerta": None}])
    assert not E.a_desmentible(r, dict(CAJA, usable=False), esc)
    assert not E.a_desmentible(dict(r, lat=-23.5), CAJA, esc)


def _vd(n_a, n_p, c1, c2, prob=()):
    et = ["A"] * n_a + ["P"] * n_p
    return E.veredicto(et, {"R1": c1, "R2": c2}, prob)


def test_veredicto_orden_y_eleccion():
    bien = [False] * 8 + [True] * 20
    mal = [True] * 8 + [True] * 20
    inv = _vd(8, 20, bien, bien, ["I2: x"])
    assert inv["veredicto"] == E.INVALIDO and "por_regla" not in inv and "n" not in inv   # crítica 5: sin métricas
    assert _vd(5, 20, [False] * 5 + [True] * 20, [False] * 5 + [True] * 20)["veredicto"] == E.SIN_PODER
    assert _vd(8, 4, [False] * 8 + [True] * 4, [False] * 8 + [True] * 4)["veredicto"] == E.SIN_PODER
    r = _vd(8, 20, bien, bien)
    assert r["veredicto"] == E.CUMPLE and r["regla"] == "R1"
    r = _vd(8, 20, mal, bien)
    assert r["veredicto"] == E.CUMPLE and r["regla"] == "R2"
    assert _vd(8, 20, mal, mal)["veredicto"] == E.NO_CUMPLE
    # alfa sellado de R1 (0,04): 4 de 6 artefactos con 5 protegidas da p = 15/330 = 0,045, no alcanza
    justo = [False] * 4 + [True] * 2 + [True] * 5
    r = _vd(6, 5, justo, justo)
    assert r["veredicto"] == E.NO_CUMPLE and abs(r["por_regla"]["R1"]["p"] - 15 / 330) < 1e-12


# ----------------------------------------------------------------------------------------------- de punta a punta
def test_puede_dar_cumple():
    v, det = escenario()
    assert v["veredicto"] == E.CUMPLE and v["regla"] == "R1", v
    assert v["n"] == {"P": 20, "A": 10} and v["por_regla"]["R1"]["quitadas"] == {"A": 10}
    assert v["sin_voto"]["R0"]["quitadas"] == {} and "R0" not in v["por_regla"]
    assert v["por_regla"]["R1"]["informativo"]["A_no_desmentibles"] == {"n": 10, "quitadas": 10}


def test_nulo_artefacto_en_celdas_con_historia_no_cumple():
    """A110: si la mancha diurna cae donde también hay calor nocturno, la regla no la distingue y no pasa."""
    v, _ = escenario(celda_artefacto=(61, 61))
    assert v["veredicto"] == E.NO_CUMPLE and v["por_regla"]["R1"]["quitadas"] == {}


def test_nulo_historia_sin_relacion_no_cumple():
    """Historia nocturna en otro lugar (ni cráter ni ladera): la regla suprime todo y pierde las protegidas."""
    v, _ = escenario(celdas_noche=((20, 20),))
    assert v["veredicto"] == E.NO_CUMPLE and v["por_regla"]["R1"]["quitadas"]["P"] == 20


def test_mancha_diurna_recurrente_en_la_misma_celda_se_suprime():
    """La mancha solar vuelve todos los días al mismo lugar: las publicaciones diurnas no cuentan como historia."""
    v, _ = escenario(artefacto_cada=1)
    assert v["por_regla"]["R1"]["quitadas"] == {"A": 20} and v["veredicto"] == E.CUMPLE


def test_sin_poder():
    v, _ = escenario(n_dias=10, artefacto_cada=2)          # 5 artefactos, 10 protegidas
    assert v["veredicto"] == E.SIN_PODER and v["n"] == {"P": 10, "A": 5}
    v, _ = escenario(n_dias=12, artefacto_cada=2)          # 6 artefactos
    assert v["veredicto"] == E.CUMPLE


def test_r_con_respaldo_de_mirova_vecina_se_conserva_si_hay_historia():
    """Una publicación en una pasada que MIROVA no tiene, con la cumbre alertada por la tabla a ±12 h, es R; en el
    cráter tiene historia nocturna y la regla la conserva."""
    det = escenario(celda_artefacto=CRATER, r_pubs=5)[1]
    sin_fila = [d for d in det if d["dt"].endswith(":50")]
    assert len(sin_fila) == 5 and {d["etiqueta"] for d in sin_fila} == {"R"} and all(d["R1"] for d in sin_fila)


def test_invalido_por_historia_incompleta():
    v, _ = escenario(quitar_noches=tuple(range(-5, 0)))   # 5 de 50 días sin noche: 90 % justo pasa
    assert v["veredicto"] == E.CUMPLE
    v, _ = escenario(quitar_noches=tuple(range(-6, 0)))   # 6 de 50: 88 %
    assert v["veredicto"] == E.INVALIDO and any(p.startswith("I2") for p in v["problemas_instrumento"])


def test_invalido_por_pasadas_de_mirova_sin_record():
    v, _ = escenario(sin_record_de=(T0, T0 + timedelta(days=1)))         # 2 de 30 pasadas de la tabla: 6,7 %
    assert v["veredicto"] == E.INVALIDO and any(p.startswith("I3") for p in v["problemas_instrumento"])
    v, _ = escenario(sin_record_de=(T0,))                                  # 1 de 30: 3,3 %
    assert not any(p.startswith("I3") for p in v["problemas_instrumento"])


def test_invalido_si_las_noches_del_brazo_no_son_las_de_produccion():
    v, _ = escenario(noches_brazo_distintas=True)
    assert v["veredicto"] == E.INVALIDO and any(p.startswith("I4") for p in v["problemas_instrumento"])


def test_invalido_por_publicaciones_sin_celdas():
    ventanas = (("T", "2026-04-01", "2026-04-20"),)
    noches = [_rec(datetime(2026, 4, 1, 5) + timedelta(days=i, minutes=10 * k), [CRATER], b=b, es_dia=False, pub=False)
              for i in range(-30, 20) for k, b in enumerate(E.SENSORES_VIIRS)]
    dia = [_rec(T0 + timedelta(days=i), [CRATER]) for i in range(19)] + [_rec(T0 + timedelta(days=19), [])]
    v = E.evaluar_fase(dia + noches, noches, [], {}, {}, INNER, ventanas, [VOL])[0]
    assert any(p.startswith("I1") for p in v["problemas_instrumento"])


def test_erupcion_nueva_pierde_solo_lo_anterior_a_su_primera_noche():
    """Costo declarado: el día de una erupción que empieza de día no tiene historia; desde la noche siguiente sí."""
    t = datetime(2026, 5, 1, 18, 0)
    noches = [_rec(t + timedelta(hours=11), [CRATER], es_dia=False)]
    idx = E.indexar_noches(noches)
    assert not E.conserva("R1", _rec(t, [CRATER]), E.celdas_historia(idx, VOL, "VIIRS375", t))
    t2 = t + timedelta(days=1)
    assert E.conserva("R1", _rec(t2, [CRATER]), E.celdas_historia(idx, VOL, "VIIRS375", t2))
