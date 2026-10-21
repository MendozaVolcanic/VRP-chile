"""S159, tarea A: el tope de cordura de pipeline/store.py en VIIRS 375 (AUDIT_S158_R2, R2-7, confirmado por VB v08).

POR QUE. El tope (50.000 MW) descarta magnitudes inverosímiles mirando la CAUSA: si la temperatura de brillo pasa el
límite físico del sensor (500 K) es saturación y se anula; si es plausible, la magnitud puede ser real (el récord de
MIROVA es ~70 GW, sobre el tope) y se conserva con `vrp_exceeds_sanity_cap`. Pero en append_record el tope corre
ANTES de copiar `t_max_i04_k` a `t_max_k`, y los records de VIIRS 375 sólo traen `t_max_i04_k`: el tope ve
t_max_k = None, lo trata como «no se puede juzgar» y ANULA. Es decir: en VIIRS 375, la erupción más grande imaginable
se publicaría como cero, indistinguible de una noche tranquila. Hoy no ha pasado (0 de 74.811 records tocados).

Este archivo NO arregla store.py (A45: tag defensivo y el sí de Nicolás). Deja la prueba del comportamiento correcto
marcada xfail(strict=True): la suite sigue verde mientras el defecto exista, y se pone roja el día que alguien lo
arregle sin quitar la marca. Los dos controles (VIIRS 750 con la misma magnitud, VIIRS 375 a 600 K) pasan hoy y
prueban que append_record sí corre el tope (si no lo corriera, el caso de 600 K tampoco se anularía).
"""
from __future__ import annotations

import json

import pytest

import pipeline.store as store


def _rec(sensor, clave_t, t, minuto):
    return {"datetime_utc": "2026-10-15T05:%02d:00Z" % minuto, "sensor": sensor, "granule": "x", "vrp_mw": 60000.0,
            clave_t: t, "t_bg_k": 270.0, "n_anomalous_pixels": 5, "distance_class": "summit",
            "final_hotspot_dist_km": 0.5, "final_hotspot_lat": -36.86, "final_hotspot_lon": -71.38,
            "primary_cluster": {"n_pixels": 5, "vrp_mw": 60000.0, "centroid_lat": -36.86, "centroid_lon": -71.38,
                                "centroid_dist_km": 0.5}}


def _guardar_y_leer(monkeypatch, tmp_path, r):
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)      # nunca data/ del repo
    store.append_record("Prueba", r, volcano_lat=-36.86, volcano_lon=-71.38, inner_radius_km=5)
    recs = json.loads((tmp_path / "Prueba.json").read_text(encoding="utf-8"))["records"]
    return [x for x in recs if x["datetime_utc"] == r["datetime_utc"] and x["sensor"] == r["sensor"]][0]


@pytest.mark.xfail(strict=True, reason=(
    "R2-7 (AUDIT_S158_R2): store.append_record aplica el tope de cordura antes de normalizar t_max_i04_k a "
    "t_max_k; en VIIRS 375 el tope ve t_max_k=None y anula una magnitud con temperatura plausible. Arreglo propuesto "
    "en experiments/_s159/instrumentos/NOTAS.md (requiere tag y el sí de Nicolás, A45). Al arreglarlo, quitar esta marca."))
def test_v375_magnitud_enorme_con_temperatura_plausible_se_conserva(monkeypatch, tmp_path):
    o = _guardar_y_leer(monkeypatch, tmp_path, _rec("VIIRS_SNPP", "t_max_i04_k", 420.0, 10))
    assert o["primary_cluster"]["vrp_mw"] == 60000.0, "el tope anuló una magnitud con BT de 420 K"
    assert o.get("vrp_exceeds_sanity_cap") is True


def test_control_v750_misma_magnitud_y_temperatura_se_conserva(monkeypatch, tmp_path):
    o = _guardar_y_leer(monkeypatch, tmp_path, _rec("VIIRS_SNPP_750", "t_max_k", 420.0, 20))
    assert o["primary_cluster"]["vrp_mw"] == 60000.0
    assert o.get("vrp_exceeds_sanity_cap") is True


def test_control_v375_temperatura_imposible_se_anula(monkeypatch, tmp_path):
    o = _guardar_y_leer(monkeypatch, tmp_path, _rec("VIIRS_SNPP", "t_max_i04_k", 600.0, 30))
    assert o["primary_cluster"]["vrp_mw"] == 0.0
    assert o.get("diag_pc_rejected_sanity_cap_mw") == 60000.0
