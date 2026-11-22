# -*- coding: utf-8 -*-
"""Pruebas del evaluador pre-registrado de la zona A del laboratorio (S194, paso 2 del plan S190).

POR QUÉ. El evaluador se escribió antes de tener datos del laboratorio. Para creerle a su veredicto hay que mostrar,
con datos sintéticos de verdad conocida, que (A116) puede dar CUMPLE, NO CUMPLE, SIN PODER e INVALIDO; que (A110) su
control con las fechas NHI corridas 15 días cae a nulo sobre datos sin señal y salta con una señal estacional; y que
una mutación del criterio la atrapa una aserción (`experiments/_s194_lab_zona_a/mutar.py` corre este archivo contra
copias mutadas, sin las pruebas de sello, que atraparían todo por construcción).

`EVALUAR_LAB_PATH` apunta a la copia que se prueba; por defecto, el evaluador del repo.
"""
import hashlib
import importlib.util
import os
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
RUTA_REPO = ROOT / "experiments" / "_s194_lab_zona_a" / "evaluar.py"
RUTA = Path(os.environ.get("EVALUAR_LAB_PATH", str(RUTA_REPO)))


def _cargar(ruta, nombre):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


E = _cargar(RUTA, "evaluar_lab_zona_a_s194")

BASE = date(2026, 3, 1)
ANCLA = (-39.42, -71.93, 5.0)
ANCLAS = {v: ANCLA for v in E.VOLCANES_ZONA_A}


def _pas(vol, d, pub, sensor="VIIRS_NOAA20", hh=5, inval=False, lat=None, lon=None):
    return {"vol": vol, "sensor": sensor, "dt": datetime(d.year, d.month, d.day, hh, 0, tzinfo=timezone.utc),
            "pub": pub, "invalida": inval, "lat": lat, "lon": lon}


def _pos(modo, rng):
    if modo == "fija":
        return ANCLA[0] + 0.001, ANCLA[1]
    r, th = ANCLA[2] * np.sqrt(rng.random()), 2 * np.pi * rng.random()
    return ANCLA[0] + r * np.cos(th) / 111.32, ANCLA[1] + r * np.sin(th) / (111.32 * np.cos(np.radians(ANCLA[0])))


def construir(clases, alertas, nubes=None, modo_pos="fija", semilla=0):
    """clases[vol] y alertas[vol]: listas por noche i (día BASE + i). Una pasada por perfil y noche; la escena NHI
    del día D es de la noche D. Devuelve (noches, nhi)."""
    rng = np.random.default_rng(semilla)
    lab, prod, nhi = [], [], {}
    for vol, cl in clases.items():
        nhi[vol] = []
        for i, c in enumerate(cl):
            d = BASE + timedelta(days=i)
            la, lo = _pos(modo_pos, rng)
            pl, pp = c in ("S", "A"), c in ("A", "P")
            lab.append(_pas(vol, d, pl, lat=la if pl else None, lon=lo if pl else None))
            prod.append(_pas(vol, d, pp, lat=la if pp else None, lon=lo if pp else None))
            if alertas[vol][i] is not None:
                nhi[vol].append({"fecha": d.isoformat(), "alerta": alertas[vol][i], "sensor": "Sentinel-2",
                                 "cloud_cover": 5.0 if nubes is None else nubes[vol][i]})
    return E.clasificar_noches(lab, prod), nhi


def aleatorio(n_noches, p_s, p_alerta_s, p_alerta_n, semilla, vols=E.VOLCANES_NHI):
    rng = np.random.default_rng(semilla)
    clases, alertas = {}, {}
    for vol in vols:
        cl = ["S" if rng.random() < p_s else "N" for _ in range(n_noches)]
        clases[vol] = cl
        alertas[vol] = [bool(rng.random() < (p_alerta_s if c == "S" else p_alerta_n)) for c in cl]
    return clases, alertas


def mezcla(con_senal, semilla, n_noches=150, p_nulo=0.3):
    """`con_senal` volcanes con exceso fuerte, el resto sin señal (misma tasa NHI `p_nulo` en S y N; con 0 el nulo es
    exacto y ningún volcán sin señal puede dar exceso por azar, para las pruebas de borde)."""
    a, b = aleatorio(n_noches, 1 / 3, 0.8, 0.2, semilla, vols=E.VOLCANES_NHI[:con_senal])
    c, d = aleatorio(n_noches, 1 / 3, p_nulo, p_nulo, semilla + 1, vols=E.VOLCANES_NHI[con_senal:])
    a.update(c)
    b.update(d)
    return a, b


# ----------------------------------------------------------------------------------------------- sello
def test_sello_valores_de_nicolas():
    """D5 (2026-11-17) y las definiciones del PREREGISTRO: cambiar uno de estos exige un pre-registro nuevo."""
    assert (E.ALFA, E.MIN_VOLCANES_CUMPLE, E.N_MIN_NOCHES, E.TASA_OBJETIVO) == (0.05, 4, 10, 0.30)
    assert E.DESPLAZAMIENTOS_CONTROL == (15, -15) and E.MAX_VOLCANES_SIG_CONTROL == 1
    assert E.VENTANA_INICIO == "2026-02-15" and E.VENTANA_CALIBRACION_INICIO == "2026-03-01"
    assert len(E.VOLCANES_NHI) == 9 and "PuyehueCordonCaulle" not in E.VOLCANES_NHI
    assert "Lastarria" not in E.VOLCANES_NHI and "Lastarria" in E.VOLCANES_ZONA_A
    assert E.ORDEN_PAREO_DIAS == (0, 1, -1) and E.CORTES_NUBE == (20.0, 50.0)
    assert (E.RADIO_PERSIST_KM, E.NOCHES_PREVIAS, E.N_MIN_EXTRAS) == (1.0, 3, 10)
    assert (E.N_PERMUTACIONES, E.N_SORTEOS_PERSIST, E.SEMILLA) == (10000, 2000, 194)
    assert E.GRILLA_S == (5.0, 4.5, 4.0, 3.5, 3.0, 2.5, 2.0, 1.5, 1.0) and E.N_MIN_NEG_SENSOR == 30
    assert (E.TOL_PAREO_S, E.MAX_FRAC_COBERTURA_DESIGUAL) == (120, 0.05)
    assert E.UNIDAD_TASA == "pasada"


def test_sello_hash_del_evaluador_en_el_preregistro():
    """El pre-registro declara el sha256 del evaluador (LF). Editar el evaluador sin re-sellar cae aquí."""
    txt = (RUTA_REPO.parent / "PREREGISTRO.md").read_text(encoding="utf-8")
    m = re.search(r"sha256 del evaluador \(fin de línea LF\): `([0-9a-f]{64})`", txt)
    assert m, "el PREREGISTRO.md no declara el sha256 del evaluador"
    h = hashlib.sha256(RUTA_REPO.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    assert h == m.group(1), "evaluar.py cambió después del sello: %s != %s" % (h, m.group(1))


def test_sello_grilla_parte_del_s2_de_produccion():
    """El primer brazo del barrido es producción: el s2 nocturno leído del .m portado (helper del guard S147)."""
    g = _cargar(ROOT / "tests" / "test_guard_laboratorio_no_mas_ciego_s147.py", "guard_s147_para_s194")
    assert E.GRILLA_S[0] == g._s2_nocturno_del_detector()
    assert all(s < E.GRILLA_S[0] for s in E.GRILLA_S[1:])


# ----------------------------------------------------------------------------------------------- noches
def test_clases_de_noche_y_cobertura():
    v = "Villarrica"
    d = [BASE + timedelta(days=i) for i in range(7)]
    lab = [_pas(v, d[0], True), _pas(v, d[1], False), _pas(v, d[2], True), _pas(v, d[3], False),
           _pas(v, d[4], True),                                   # sin par en producción: cobertura desigual
           _pas(v, d[5], True, inval=True),                       # inválida sólo en el laboratorio: desigual
           _pas(v, d[6], True, inval=True)]                       # inválida en los dos: no observada
    prod = [_pas(v, d[0], False), _pas(v, d[1], False), _pas(v, d[2], True), _pas(v, d[3], True),
            _pas(v, d[5], False), _pas(v, d[6], False, inval=True)]
    n = E.clasificar_noches(lab, prod)
    cl = [n[(v, x.isoformat())]["clase"] for x in d]
    assert cl == ["S", "N", "A", "P", None, None, None]
    assert [n[(v, x.isoformat())]["cobertura_igual"] for x in d] == [True, True, True, True, False, False, True]


def test_identidad_laboratorio_igual_a_produccion_no_da_noches_s_ni_p():
    v = "Lascar"
    pas = [_pas(v, BASE + timedelta(days=i), i % 3 == 0) for i in range(30)]
    n = E.clasificar_noches(pas, [dict(p) for p in pas])
    assert {i["clase"] for i in n.values()} == {"A", "N"}


def test_pasada_invalida_no_publica_aunque_tenga_pub():
    v = "Lascar"
    lab = [_pas(v, BASE, True, inval=True), _pas(v, BASE, False, sensor="MODIS_AQUA", hh=6)]
    prod = [_pas(v, BASE, False, inval=True), _pas(v, BASE, False, sensor="MODIS_AQUA", hh=6)]
    assert E.clasificar_noches(lab, prod)[(v, BASE.isoformat())]["clase"] == "N"


# ----------------------------------------------------------------------------------------------- pareo NHI
def test_pareo_prefiere_d_luego_d_mas_1_luego_d_menos_1():
    def nv(clases):
        return {(BASE + timedelta(days=k)).isoformat(): {"clase": c} for k, c in clases.items()}
    esc = [{"fecha": (BASE + timedelta(days=5)).isoformat(), "alerta": True, "cloud_cover": 1.0}]
    assert list(E.parear_nhi(esc, nv({4: "N", 5: "S", 6: "N"}))) == [(BASE + timedelta(days=5)).isoformat()]
    assert list(E.parear_nhi(esc, nv({4: "N", 6: "S"}))) == [(BASE + timedelta(days=6)).isoformat()]
    assert list(E.parear_nhi(esc, nv({4: "S"}))) == [(BASE + timedelta(days=4)).isoformat()]
    assert E.parear_nhi(esc, nv({3: "S", 7: "S"})) == {}
    # una noche A consume la escena: no salta a la noche S vecina
    assert E.parear_nhi(esc, nv({5: "A", 6: "S"})) == {}


def test_pareo_respeta_ventana_y_desplazamiento():
    nv = {"2026-03-16": {"clase": "S"}, "2026-03-01": {"clase": "N"}}
    esc = [{"fecha": "2026-03-01", "alerta": True, "cloud_cover": 1.0},
           {"fecha": "2026-02-10", "alerta": True, "cloud_cover": 1.0}]
    assert set(E.parear_nhi(esc, nv)) == {"2026-03-01"}
    assert set(E.parear_nhi(esc, nv, desplazamiento_dias=15)) == {"2026-03-16"}


def test_varias_escenas_en_una_noche_alerta_es_alguna_y_nube_la_menor():
    nv = {"2026-03-05": {"clase": "S"}}
    esc = [{"fecha": "2026-03-05", "alerta": False, "cloud_cover": 60.0},
           {"fecha": "2026-03-05", "alerta": True, "cloud_cover": 12.0}]
    u = E.parear_nhi(esc, nv)["2026-03-05"]
    assert u["alerta"] is True and u["nube"] == 12.0


# ----------------------------------------------------------------------------------------------- permutación
def test_permutacion_estratificada_neutraliza_la_nube():
    """Nubes que apagan a la vez nuestra noche (N) y la alerta NHI fabrican un exceso. Estratificar lo quita."""
    rng = np.random.default_rng(7)
    u = {}
    for i in range(200):
        if i % 2:   # despejado: S o N al azar, NHI independiente de la clase
            u[str(i)] = {"clase": "S" if rng.random() < 0.5 else "N", "alerta": bool(rng.random() < 0.5), "nube": 5.0}
        else:       # nublado: no vemos nada (N) y NHI tampoco
            u[str(i)] = {"clase": "N", "alerta": False, "nube": 80.0}
    estrat = E.prueba_permutacion(u, n_perm=4000)
    plano = E.prueba_permutacion({k: dict(x, nube=5.0) for k, x in u.items()}, n_perm=4000)
    assert plano["p"] < 0.01, plano
    assert estrat["p"] > 0.2, estrat


def test_permutacion_signo_y_p():
    u = {str(i): {"clase": "S" if i < 20 else "N", "alerta": i < 18 or (i >= 20 and i % 5 == 0), "nube": 5.0}
         for i in range(100)}
    r = E.prueba_permutacion(u, n_perm=2000)
    assert r["exceso"] > 0.6 and r["p"] < 0.001
    inv = E.prueba_permutacion({k: dict(x, alerta=not x["alerta"]) for k, x in u.items()}, n_perm=2000)
    assert inv["exceso"] < 0 and inv["p"] > 0.99


def test_voto_sin_poder_por_cualquiera_de_los_dos_grupos():
    assert E.voto_volcan({"n_S": 9, "n_N": 50, "exceso": 0.9, "p": 0.0001}) == E.SIN_PODER
    assert E.voto_volcan({"n_S": 30, "n_N": 9, "exceso": 0.9, "p": 0.0001}) == E.SIN_PODER
    assert E.voto_volcan({"n_S": 10, "n_N": 10, "exceso": 0.9, "p": 0.0001}) == "exceso"
    assert E.voto_volcan({"n_S": 10, "n_N": 10, "exceso": 0.9, "p": 0.05}) == "sin exceso"


# ----------------------------------------------------------------------------------------------- veredictos
@pytest.fixture(scope="module")
def cumple():
    noches, nhi = construir(*mezcla(9, 11))
    return E.veredicto(noches, nhi, ANCLAS)


def test_puede_dar_cumple(cumple):
    assert cumple["veredicto"] == E.CUMPLE, cumple["motivos"]
    assert cumple["control"]["nulo"] and cumple["persistencia"]["supera"]


def test_control_cae_a_nulo_sin_senal_en_el_desplazamiento(cumple):
    """Con señal sólo en la noche misma, las fechas corridas 15 días no la ven (A110)."""
    for dd in ("15", "-15"):
        assert cumple["control"]["desplazamientos"][dd]["n_volcanes_exceso"] <= 1


def test_sin_senal_da_no_cumple_y_control_nulo():
    noches, nhi = construir(*mezcla(0, 21))
    r = E.veredicto(noches, nhi, ANCLAS)
    assert r["veredicto"] == E.NO_CUMPLE and r["control"]["nulo"]
    assert len(r["volcanes_con_exceso"]) <= 1


def test_tres_de_nueve_no_cumple_cuatro_si():
    r3 = E.veredicto(*construir(*mezcla(3, 31, p_nulo=0.0)), ANCLAS)
    r4 = E.veredicto(*construir(*mezcla(4, 31, p_nulo=0.0)), ANCLAS)
    assert sorted(r3["volcanes_con_exceso"]) == sorted(E.VOLCANES_NHI[:3]) and r3["veredicto"] == E.NO_CUMPLE
    assert sorted(r4["volcanes_con_exceso"]) == sorted(E.VOLCANES_NHI[:4]) and r4["veredicto"] == E.CUMPLE


def test_exceso_nhi_sin_persistencia_no_cumple():
    noches, nhi = construir(*mezcla(9, 11), modo_pos="azar")
    r = E.veredicto(noches, nhi, ANCLAS)
    assert not r["persistencia"]["supera"] and r["veredicto"] == E.NO_CUMPLE


def test_sin_poder_con_nueve_noches_s_y_vota_con_diez():
    def caso(n_s):
        clases, alertas = {}, {}
        for vol in E.VOLCANES_NHI:
            cl = ["N"] * 60
            for k in range(n_s):
                cl[2 + 6 * k] = "S"
                cl[3 + 6 * k] = "S"   # pares de noches S consecutivas: persistencia
            clases[vol] = cl
            alertas[vol] = [c == "S" or i % 10 == 0 for i, c in enumerate(cl)]
        return E.veredicto(*construir(clases, alertas), ANCLAS)
    r9, r10 = caso(4), caso(5)    # 8 y 10 noches S por volcán
    assert r9["veredicto"] == E.SIN_PODER and r9["volcanes_con_poder"] == []
    assert len(r10["volcanes_con_poder"]) == 9 and r10["veredicto"] == E.CUMPLE


def test_senal_estacional_hace_saltar_el_control():
    """Una estación de 60 días en que suben a la vez las noches S y la alerta NHI: el exceso aparece, pero las
    fechas corridas 15 días lo siguen viendo, así que el veredicto es INVALIDO y no CUMPLE."""
    rng = np.random.default_rng(5)
    clases, alertas = {}, {}
    for vol in E.VOLCANES_NHI:
        est = [60 <= i < 120 for i in range(180)]
        clases[vol] = ["S" if rng.random() < (0.7 if e else 0.1) else "N" for e in est]
        alertas[vol] = [bool(rng.random() < (0.7 if e else 0.1)) for e in est]
    r = E.veredicto(*construir(clases, alertas), ANCLAS)
    assert len(r["volcanes_con_exceso"]) >= 4
    assert not r["control"]["nulo"] and r["veredicto"] == E.INVALIDO


def test_cobertura_desigual_invalida():
    clases, alertas = mezcla(9, 11)
    noches, nhi = construir(clases, alertas)
    v = E.VOLCANES_NHI[0]
    for k in sorted(k for k in noches if k[0] == v)[:10]:      # 10 de 150 noches (6,7 %) sin par
        noches[k] = dict(noches[k], cobertura_igual=False, clase=None)
    r = E.veredicto(noches, nhi, ANCLAS)
    assert r["veredicto"] == E.INVALIDO and r["cobertura"][v]["desiguales"] == 10


def test_persistencia_fija_supera_y_azar_no():
    clases, alertas = mezcla(9, 11)
    fija = E.persistencia(construir(clases, alertas)[0], ANCLAS)
    azar = E.persistencia(construir(clases, alertas, modo_pos="azar")[0], ANCLAS)
    assert fija["supera"] and fija["frac_obs"] > 0.5
    assert not azar["supera"] and azar["p"] > 0.05


def test_persistencia_temporal_informativa_no_vota(cumple):
    """Con la posición fija, la recurrencia temporal no se distingue de la espacial: p alto, y aun así CUMPLE."""
    t = cumple["persistencia_temporal_informativa"]
    assert t["n_extras"] == cumple["persistencia"]["n_extras"] and t["p"] > 0.05
    assert cumple["veredicto"] == E.CUMPLE


# ----------------------------------------------------------------------------------------------- calibración
def _tasas(por_s, n=1000, por_s_noche=None):
    out = {s: {sen: (round(r * n), n) for sen in E.SENSORES} for s, r in por_s.items()}
    for s in out:
        out[s]["NOCHE"] = (round((por_s_noche or por_s)[s] * n), n)
    return out


def test_elige_el_menor_s_que_cumple_con_30_exacto():
    t = _tasas({5.0: .01, 4.5: .05, 4.0: .10, 3.5: .20, 3.0: .30, 2.5: .301, 2.0: .5, 1.5: .7, 1.0: .9})
    assert E.elegir_valor(t) == {"estado": "ELEGIDO", "valor": 3.0, "detalle": "menor s de la grilla que cumple"}


def test_un_sensor_sobre_la_tasa_basta_para_rechazar():
    t = _tasas({5.0: .01, 4.5: .05, 4.0: .10, 3.5: .20, 3.0: .25, 2.5: .28, 2.0: .29, 1.5: .29, 1.0: .29})
    t[3.0]["VIIRS750"] = (310, 1000)
    for s in (2.5, 2.0, 1.5, 1.0):
        t[s]["VIIRS750"] = (400, 1000)
    assert E.elegir_valor(t)["valor"] == 3.5


def test_calibracion_sin_valor_sin_poder_invalido_y_piso():
    base = {5.0: .01, 4.5: .05, 4.0: .10, 3.5: .20, 3.0: .25, 2.5: .26, 2.0: .27, 1.5: .28, 1.0: .29}
    sobre = {s: 0.31 + 0.01 * i for i, s in enumerate(E.GRILLA_S)}      # producción ya sobre 30 %
    assert E.elegir_valor(_tasas(sobre))["estado"] == "SIN VALOR"
    assert E.elegir_valor(_tasas(base, n=29))["estado"] == E.SIN_PODER
    assert E.elegir_valor(_tasas({**base, 3.0: .19}))["estado"] == E.INVALIDO   # no monótona
    t = _tasas(base)
    del t[2.0]
    assert E.elegir_valor(t)["estado"] == E.INVALIDO
    piso = E.elegir_valor(_tasas(base))
    assert piso["valor"] == 1.0 and "piso de la grilla" in piso["detalle"]


def test_identidad_barrido_plano_no_da_extension():
    """Si todos los brazos fueran producción (s no tiene efecto), la tasa es plana y la regla baja hasta el piso:
    el estado lo dice («piso de la grilla») para que nadie lea eso como una calibración."""
    r = E.elegir_valor(_tasas({s: 0.02 for s in E.GRILLA_S}))
    assert r["valor"] == 1.0 and "piso" in r["detalle"]


def test_unidad_sellada_es_la_pasada_y_la_noche_queda_disponible():
    """D5 aprobó la tasa por pasada. La unidad noche (pregunta 1 del PR) elige otro valor con los mismos brazos."""
    pasada = {5.0: .01, 4.5: .02, 4.0: .05, 3.5: .10, 3.0: .20, 2.5: .30, 2.0: .40, 1.5: .5, 1.0: .6}
    noche = {5.0: .03, 4.5: .08, 4.0: .20, 3.5: .30, 3.0: .45, 2.5: .60, 2.0: .80, 1.5: .9, 1.0: .95}
    t = _tasas(pasada, por_s_noche=noche)
    assert E.elegir_valor(t)["valor"] == 2.5
    assert E.elegir_valor(t, unidad="noche")["valor"] == 3.5
    assert E.elegir_valor(t, unidad="pasada")["valor"] == 2.5


def test_control_del_barrido_exige_que_s5_sea_produccion():
    base = {s: 0.01 * (i + 1) for i, s in enumerate(E.GRILLA_S)}
    t = _tasas(base)
    assert E.control_barrido(t, dict(t[5.0]))
    otra = dict(t[5.0], VIIRS375=(t[5.0]["VIIRS375"][0] + 1, t[5.0]["VIIRS375"][1]))
    assert not E.control_barrido(t, otra)


# ----------------------------------------------------------------------------------------------- poder
def test_tabla_de_poder():
    assert E.minimo_detectable(10, 80, 0.35) == 7
    assert E.minimo_detectable(10, 80, 0.07) == 4
    assert E.minimo_detectable(40, 80, 0.15) == 12
    assert round(E.prob_al_menos(4, 9, 0.05), 5) == 0.00064
    assert round(E.prob_al_menos(2, 9, 0.05), 4) == 0.0712
