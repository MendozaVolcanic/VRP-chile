# -*- coding: utf-8 -*-
"""S194: controles de la partición por áreas del laboratorio (experiments/_s194_areas/particion.py).

POR QUÉ: la partición reparte entre cráter, agua, flanco y resto los alertados que la vía ya guarda. Dos cosas tienen
que valer siempre: (1) un píxel puesto a mano en cada área cae en esa área, con el cráter ganándole al agua (un lago
cratérico es volcánico); (2) la suma de las áreas devuelve el VRP del record (D32), porque la partición sólo reparte.
"""
import importlib.util
import math
from pathlib import Path

import numpy as np
import pytest
import yaml

RAIZ = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("particion_s194", RAIZ / "experiments" / "_s194_areas" / "particion.py")
P = importlib.util.module_from_spec(spec)
spec.loader.exec_module(P)

CONF = yaml.safe_load((RAIZ / "config" / "areas_laboratorio.yaml").read_text(encoding="utf-8"))
VY = {v["name"]: v for v in yaml.safe_load((RAIZ / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}


def _areas(volcan="Villarrica"):
    return P.Areas(volcan, RAIZ, CONF, VY[volcan])


def _punto(a, x_km, y_km):
    """lat, lon de un punto a (x, y) km del cráter, con la misma proyección local de la partición."""
    return a.lat0 + y_km / P.KM_LAT, a.lon0 + x_km / a.kx


def _seco(a, r_km):
    """Un punto a r_km del cráter que no cae en agua (barre rumbos)."""
    for ang in range(0, 360, 5):
        la, lo = _punto(a, r_km * math.sin(math.radians(ang)), r_km * math.cos(math.radians(ang)))
        if a.lago_de(la, lo) is None and not a._cerca_agua(la, lo, 0.5):
            return la, lo
    raise AssertionError("sin punto seco")


def _lago_fuera_del_crater(a):
    for g in sorted(a.lagos, key=lambda L: -L.area_km2()):
        x, y = g.punto_interior(paso=0.2)
        d = math.hypot(x, y)
        if a.inner_km + 1 < d < 24:
            return a.lat0 + y / P.KM_LAT, a.lon0 + x / a.kx, d
    raise AssertionError("sin lago")


def _record(a, pixeles, fam="VIIRS750", t_bk=270.0):
    sensor = {"VIIRS750": "VIIRS_NOAA20_750", "MODIS": "MODIS_AQUA", "VIIRS375": "VIIRS_NOAA20"}[fam]
    lam = P.FAMILIAS[fam]["lam_mir"]
    coef = P.FAMILIAS[fam]["coef"]
    l_hot = sum(P.radiancia_pixel(q["bt_k"], fam) for q in pixeles)
    l_bk = len(pixeles) * float(P.temperatura_a_radiancia(np.array([t_bk]), lam)[0])
    return {"sensor": sensor, "vrp_mw": round(coef * (l_hot - l_bk), 3), "n_anomalous_pixels": len(pixeles),
            "anomaly_pixels": pixeles, "diag_codigo_mirova": {"L_hot": l_hot, "L_bk": l_bk, "dayflag": 0}}


def test_un_pixel_en_cada_area_cae_donde_debe():
    a = _areas()
    lc = _punto(a, 0.0, 1.0)
    lw = _lago_fuera_del_crater(a)
    lf = _seco(a, (a.inner_km + a.flanco_km) / 2)
    lr = _seco(a, a.flanco_km + 6)
    pix = [
        {"lat": lc[0], "lon": lc[1], "dist_km": 1.0, "bt_k": 300.0},
        {"lat": lw[0], "lon": lw[1], "dist_km": round(lw[2], 2), "bt_k": 290.0},
        {"lat": lf[0], "lon": lf[1], "dist_km": (a.inner_km + a.flanco_km) / 2, "bt_k": 285.0},
        {"lat": lr[0], "lon": lr[1], "dist_km": a.flanco_km + 6, "bt_k": 280.0},
    ]
    r = P.repartir(_record(a, pix), a)
    assert [q["area"] for q in r["pix"]] == ["crater", "agua", "flanco", "resto"]
    assert all(r["areas"][k]["n"] == 1 for k in P.AREAS)
    assert r["areas"]["crater"]["max_bt_k"] == 300.0
    assert r["pix"][1]["lago"] is not None


def test_el_crater_le_gana_al_agua():
    a = _areas()
    lw = _lago_fuera_del_crater(a)
    pix = [{"lat": lw[0], "lon": lw[1], "dist_km": a.inner_km - 1.0, "bt_k": 290.0}]
    r = P.repartir(_record(a, pix), a)
    assert r["pix"][0]["area"] == "crater"


def test_una_isla_no_es_agua():
    """Los polígonos JRC traen huecos (islas): un píxel sobre una isla es tierra, no agua."""
    for volcan in CONF["volcanes"]:
        a = _areas(volcan)
        for L in a.lagos:
            for h in L.anillos[1:]:
                isla = P.Lago([h])
                if isla.area_km2() < 0.05:
                    continue
                x, y = isla.punto_interior(paso=0.02)
                la, lo = a.lat0 + y / P.KM_LAT, a.lon0 + x / a.kx
                d = math.hypot(x, y)
                if d <= a.inner_km + 1 or any(o is not L and o.contiene(x, y) for o in a.lagos):
                    continue
                r = P.repartir(_record(a, [{"lat": la, "lon": lo, "dist_km": d, "bt_k": 290.0}]), a)
                assert r["pix"][0]["area"] in ("flanco", "resto"), (volcan, x, y)
                assert a.lago_de(la, lo) is None
                return
    pytest.skip("sin islas de tamaño suficiente")


@pytest.mark.parametrize("fam", ["VIIRS750", "MODIS", "VIIRS375"])
def test_la_suma_de_las_areas_da_el_vrp_del_record(fam):
    a = _areas()
    lc = _punto(a, 0.0, 1.0)
    lr = _seco(a, a.flanco_km + 6)
    pix = [{"lat": lc[0], "lon": lc[1], "dist_km": 1.0, "bt_k": 330.0},
           {"lat": lr[0], "lon": lr[1], "dist_km": a.flanco_km + 6, "bt_k": 295.0}]
    rec = _record(a, pix, fam=fam)
    r = P.repartir(rec, a)
    suma = sum(r["areas"][k]["vrp_mw"] for k in P.AREAS)
    assert r["cierre_ok"]
    assert abs(suma - rec["vrp_mw"]) <= r["tol"]
    assert r["areas"]["crater"]["vrp_mw"] > r["areas"]["resto"]["vrp_mw"] > 0


def test_el_cierre_detecta_un_vrp_que_no_cuadra():
    """Control de que el control puede fallar (A116): un vrp_mw alterado en 10 % no pasa."""
    a = _areas()
    lc = _punto(a, 0.0, 1.0)
    rec = _record(a, [{"lat": lc[0], "lon": lc[1], "dist_km": 1.0, "bt_k": 330.0}])
    rec["vrp_mw"] = round(rec["vrp_mw"] * 1.1, 3)
    assert not P.repartir(rec, a)["cierre_ok"]


def test_borde_a_media_celda():
    a = _areas()
    lc = _punto(a, 0.0, a.inner_km - 0.1)
    r = P.repartir(_record(a, [{"lat": lc[0], "lon": lc[1], "dist_km": a.inner_km - 0.1, "bt_k": 300.0}]), a)
    assert r["pix"][0]["area"] == "crater" and r["pix"][0]["borde"]
    lc = _punto(a, 0.0, 1.0)
    r = P.repartir(_record(a, [{"lat": lc[0], "lon": lc[1], "dist_km": 1.0, "bt_k": 300.0}]), a)
    assert not r["pix"][0]["borde"]


def test_config_cubre_los_diez_tier_a_sin_puyehue():
    vols = set(CONF["volcanes"])
    assert "PuyehueCordonCaulle" not in vols
    assert vols == {"Lascar", "Isluga", "Lastarria", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan", "Copahue",
                    "Llaima", "Villarrica", "Chaiten"}
    assert CONF["precedencia"] == ["crater", "agua", "flanco", "resto"]
    for v, c in CONF["volcanes"].items():
        assert (RAIZ / c["agua"]).exists()
        assert c["radio_flanco_km"] > VY[v]["inner_radius_km"]


def test_nocturna():
    assert P.es_nocturna({"diag_codigo_mirova": {"dayflag": 0}, "solar_zenith_deg": 120})
    assert not P.es_nocturna({"diag_codigo_mirova": {"dayflag": 1}, "solar_zenith_deg": 120})
    assert not P.es_nocturna({"diag_codigo_mirova": {"dayflag": 0}, "solar_zenith_deg": 60})
