# -*- coding: utf-8 -*-
"""S175 (hallazgo 253 de docs/AUDIT_S175.md): decisión 3 de S174 en el lector de la retrospectiva.

POR QUÉ. Con la vía «código MIROVA» encendida, cuando la vía no puede correr en un gránulo (volcán sin grilla de MIROVA
o sin MxD03) el procesador escribe K con la marca en texto (`via_codigo_mirova`: "sin_grilla" o "sin_mxd03"). Eso es
lo que producción habría publicado esa noche: K. Nicolás aprobó el 2026-11-05 («Sí, a todo», punto 3 del bloque S174,
VPR940b-04): esos records se tratan como K y se listan como aviso. El lector hacía lo contrario: los sacaba de la
evaluación (`via_sin_marca:<marca>`) y C-via quedaba en rojo con uno solo.

LO QUE NO CAMBIA. Un record de la vía SIN la marca (clave ausente) o con una marca que la decisión no nombra
("geo_distinta") sigue siendo C-via en rojo: esa es la primera pregunta del instrumento (si la vía no corriera, C-via
lo ve). Y si TODAS las pasadas son caídas a K, la vía no corrió: C-via en rojo.
"""
import importlib.util
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "_s172_retro_paquete"
_RUTA = Path(os.environ.get("LEER_RETRO_MODULO") or EXP / "leer_retro.py")
_spec = importlib.util.spec_from_file_location("leer_retro_caida_bajo_prueba", _RUTA)
L = importlib.util.module_from_spec(_spec)
sys.modules["leer_retro_caida_bajo_prueba"] = L
_spec.loader.exec_module(L)


def _rec(dts, summit, vrp, via=None, sensor="MODIS_AQUA"):
    r = {"datetime_utc": dts, "sensor": sensor, "sensor_zenith_deg": 25.0,
         "distance_class": "summit" if summit else None, "vrp_mw": vrp,
         "primary_cluster": {"vrp_mw": vrp, "centroid_dist_km": 1.0, "n_pixels": 1} if vrp else None,
         "hotspot_dist_km": 1.0 if vrp else None,
         "anomaly_pixels": [{"dist_km": 0.8, "lat": 0, "lon": 0, "vrp_mw": vrp, "bt_k": 300}] if vrp else []}
    if via is not None:
        r["via_codigo_mirova"] = via
    return r


def pred(casos):
    out = []
    for r, _inner in casos:
        pc = (r or {}).get("primary_cluster") or {}
        v = float(pc.get("vrp_mw") or 0.0)
        out.append((1 if (r or {}).get("distance_class") == "summit" and v > 0 else 0, v))
    return out


def _par(dts, marca, summit=1, vrp=0.4, vol="Lascar"):
    key = (vol, "MODIS_AQUA", dts)
    return key, _rec(dts, summit, vrp, via=marca), _rec(dts, summit, vrp)


def _armar(marcas):
    via, k = {}, {}
    for i, m in enumerate(marcas):
        key, rv, rk = _par(f"2026-02-{i + 1:02d} 05:00", m)
        via[key], k[key] = rv, rk
    return L.armar_pasadas(via, k)


@pytest.mark.parametrize("marca", ["sin_grilla", "sin_mxd03"])
def test_la_caida_a_k_de_la_via_es_evaluable_como_k_y_se_lista(marca):
    fs = _armar([True, marca])
    caida = [f for f in fs if f["via_marca"] == marca][0]
    assert caida["estado"] == "ok" and caida["via_caida_k"] == marca
    c = L.c_via(fs, "F26-M")
    assert c["estado"] == "OK" and c["sin_marca"] == 0
    assert c["caidas_a_k"] == 1 and c["aviso"] and marca in c["aviso"]


@pytest.mark.parametrize("marca", [None, "geo_distinta", False])
def test_control_la_via_sin_marca_o_con_otra_marca_sigue_en_rojo(marca):
    fs = _armar([True, marca])
    otra = [f for f in fs if f["via_marca"] is not True][0]
    assert otra["estado"] == "via_sin_marca:" + str(marca)
    assert L.c_via(fs, "F26-M")["estado"].startswith("ROJO")


def test_si_todas_las_pasadas_caen_a_k_la_via_no_corrio():
    fs = _armar(["sin_grilla", "sin_mxd03", "sin_grilla"])
    assert L.c_via(fs, "F26-M")["estado"].startswith("ROJO")
    assert L.c_via(fs, "R25")["estado"].startswith("ROJO")


def test_los_brazos_de_la_via_publican_lo_que_publica_el_record_de_k():
    """«Se tratan como K»: los tres brazos de posición de la vía toman el record tal cual (K no tiene posiciones de la
    vía), y publican lo mismo que K en esa pasada."""
    fs = _armar([True, "sin_grilla"])
    L.tabla_publica(L.Reglas(), fs, pred)
    caida = [f for f in fs if f["via_marca"] == "sin_grilla"][0]
    assert caida["_evaluable"] is True
    for b in L.BRAZOS:
        assert caida["_t"][b] == caida["_t"]["K"] == {"pub": 1, "mag": 0.4}, b


def test_k_de_disco_con_marca_de_caida_es_k_con_aviso():
    """VPR940b-04: un record de K de disco escrito por un perfil con la vía encendida que cayó a K es K (c_k_puro
    sigue OK), pero se lista. La marca True sigue en rojo (VPR940-02)."""
    key, rv, rk = _par("2026-02-10 05:00", True)
    rk["via_codigo_mirova"] = "sin_grilla"
    fs = L.armar_pasadas({key: rv}, {key: rk})
    c = L.c_k_puro(fs)
    assert c["estado"] == "OK" and c["caidas_a_k"] == [("Lascar", "MODIS_AQUA", "2026-02-10 05:00", "sin_grilla")]
    rk["via_codigo_mirova"] = True
    assert L.c_k_puro(L.armar_pasadas({key: rv}, {key: rk}))["estado"].startswith("ROJO")
