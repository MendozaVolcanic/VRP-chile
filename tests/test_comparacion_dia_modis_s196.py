# -*- coding: utf-8 -*-
"""S196 (E3 del camino de independencia): la comparación diaria separa la franja diurna de MODIS de la nocturna.

POR QUÉ. Desde #1090 producción procesa MODIS de día y la regla de auditoría deja pasar el día de MODIS después del primer
record diurno, en nuestros records y en las filas de MIROVA. Sin separar, una alerta diurna de MIROVA marcaba la fecha
como «con alerta» y la pasada nocturna de esa fecha dejaba de ser negativo limpio: la cuenta nocturna cambiaba por algo
que pasó de día. Estas pruebas fijan que (1) los números nocturnos no dependen de lo diurno, (2) el día se cuenta aparte
con la vía contra MIROVA y (3) la página lee lo que el script escribe.

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) Si el día se colara en la noche, ¿lo veríamos? El caso de punta a punta pone una
alerta diurna de MIROVA y una noche tranquila en la misma fecha: con el día colado, la noche cae a «sin juicio» y su
negativo limpio desaparece (TN 0 en vez de 1). (2) ¿Puede dar algo distinto de cero? La franja diurna tiene que dar un
acierto protegido de la vía.
"""
import csv
import json
import os
import shutil
import sys
from datetime import datetime, timezone

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, ROOT)

import auto_audit_weekly as aa  # noqa: E402  (el mismo módulo que usan banco_paridad y comparacion_via_k)
import comparacion_via_k as cv  # noqa: E402
import pipeline.profile as prof  # noqa: E402

node = pytest.mark.skipif(shutil.which("node") is None, reason="node no disponible")

NOCHE, DIA = "2027-01-05 03:00", "2027-01-05 18:30"   # Láscar: elevación solar -39° y +63°
CAMPOS_CSV = ["Fecha_Satelite_UTC", "Volcan", "Sensor", "VRP_MW", "Distancia_km", "Tipo_Registro",
              "Clasificacion Mirova", "Ultima_Actualizacion", "Nota_Validacion"]


def _rec(dt, publica):
    base = {"sensor": "MODIS_AQUA", "datetime_utc": dt, "triggered_test1": False, "vrp_vent_mw": 0.0,
            "f5_core_vrp_mw": None, "anomaly_pixels": [], "via_codigo_mirova": True}
    if publica:
        base.update({"distance_class": "summit", "t_max_k": 320.0, "vrp_mw": 2.0,
                     "primary_cluster": {"vrp_mw": 2.0, "centroid_dist_km": 0.7, "n_pixels": 3},
                     "final_hotspot_lat": -23.37, "final_hotspot_lon": -67.73})
    else:
        base.update({"distance_class": None, "t_max_k": 280.0, "vrp_mw": 0.0, "primary_cluster": None})
    return base


def _carpeta(tmp_path, nombre, recs):
    d = tmp_path / nombre
    d.mkdir()
    for vol in cv.bp.VOLS:
        (d / f"{vol}.json").write_text(json.dumps({"records": recs if vol == "Lascar" else []}), encoding="utf-8")
    return d


def _csv(path, filas):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CAMPOS_CSV)
        w.writeheader()
        for dt, tipo, vrp in filas:
            w.writerow({"Fecha_Satelite_UTC": dt + ":00", "Volcan": "Lascar", "Sensor": "MODIS", "VRP_MW": vrp,
                        "Distancia_km": "0.8" if tipo != "RUTINA" else "0.0", "Tipo_Registro": tipo,
                        "Clasificacion Mirova": "", "Ultima_Actualizacion": "2027-01-05 21:00:00",
                        "Nota_Validacion": ""})


@pytest.fixture
def dia_encendido(monkeypatch):
    """Rama diurna de MODIS encendida desde 2027-01-01 en la serie por defecto (la que lee banco_paridad)."""
    monkeypatch.setattr(aa, "_INICIO_DIA_MODIS", {})
    monkeypatch.setattr(prof, "ENABLE_DAYTIME_MODIS", True)
    monkeypatch.setattr(prof, "ENABLE_DAYTIME_VIIRS", False)
    aa.fijar_inicio_dia_modis(datetime(2027, 1, 1, tzinfo=timezone.utc))


def _correr(tmp_path, con_dia):
    sub = tmp_path / ("con_dia" if con_dia else "sin_dia")
    sub.mkdir()
    prod = _carpeta(sub, "prod", [_rec(NOCHE, False)] + ([_rec(DIA, True)] if con_dia else []))
    guardia = _carpeta(sub, "guardia", [_rec(NOCHE, False)])
    cons, ocr = sub / "cons.csv", sub / "ocr.csv"
    _csv(cons, [(NOCHE, "RUTINA", "0.0")] + ([(DIA, "ALERTA_TERMICA", "2.1")] if con_dia else []))
    _csv(ocr, [])
    cache = sub / "cache.json"
    cache.write_text(json.dumps({"meta": {"sha_predicado": cv.sha_predicado_actual()}, "pasadas": []}), encoding="utf-8")
    out = sub / "out.json"
    assert cv.main(["--prod", str(prod), "--guardia-modis", str(guardia), "--guardia-viirs", str(guardia),
                    "--cache-k", str(cache), "--cons", str(cons), "--ocr", str(ocr), "--hoy", "2027-01-10",
                    "--sin-capas-historicas", "--out", str(out)]) == 0
    return json.loads(out.read_text(encoding="utf-8"))


@node
def test_la_noche_no_cambia_con_lo_que_pasa_de_dia(tmp_path, dia_encendido):
    con, sin = _correr(tmp_path, True), _correr(tmp_path, False)
    noct = lambda d: {k: v for k, v in d["resultados"].items() if "|dia|" not in k}  # noqa: E731
    assert noct(con) == noct(sin)
    assert con["noches"] == sin["noches"]
    r = con["resultados"]["tabla|adopcion|MODIS"]
    # La noche tranquila sigue siendo un negativo limpio bien callado pese a la alerta diurna de la misma fecha.
    assert (r["via"]["TN"], r["via"]["FP"], r["k"]["TN"]) == (1, 0, 1)
    (fila,) = con["noches"]["filas"] if con["noches"]["filas"] else [None]
    assert fila is None, "una noche tranquila sin publicación no tiene fila; la pasada diurna no se cuela en la noche"


@node
def test_el_dia_se_cuenta_aparte_contra_mirova(tmp_path, dia_encendido):
    d = _correr(tmp_path, True)
    assert d["meta"]["franjas"]["dia_desde"] == "2027-01-05"
    assert (d["meta"]["franjas"]["via_pasadas_noche"], d["meta"]["franjas"]["via_pasadas_dia"]) == (1, 1)
    r = d["resultados"]["tabla|dia|MODIS"]
    assert (r["n_pasadas"], r["via"]["TP"], r["via"]["FN"], r["via"]["protegidas"]) == (1, 1, 0, 1)
    assert "k" not in r, "de día no hay K: la guardia procesa sólo de noche"
    (fila,) = d["dias"]["filas"]
    f = dict(zip(d["dias"]["campos"], fila))
    assert (f["vol"], f["dia"], f["horas"], f["lab_tabla"], f["prot_tabla"], f["via_pub"]) == \
        ("Lascar", "2027-01-05", ["18:30"], "pos", 1, 1)


@node
def test_sin_dia_no_hay_franja_diurna(tmp_path, dia_encendido):
    d = _correr(tmp_path, False)
    assert d["meta"]["franjas"]["dia_desde"] is None
    assert not any("|dia|" in k for k in d["resultados"])
    assert d["dias"]["filas"] == []


def test_franja_de_pasadas_y_filas_de_referencia():
    coords = cv.bp._coords_por_volcan()
    t = lambda s: datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)  # noqa: E731
    pas = [{"vol": "Lascar", "b": "MODIS", "dt": t(NOCHE)}, {"vol": "Lascar", "b": "MODIS", "dt": t(DIA)},
           {"vol": "Lascar", "b": "VIIRS375", "dt": t(DIA)}]
    assert [p["dt"] for p in cv.pasadas_de_franja(pas, coords, False)] == [t(NOCHE)]
    # De día sólo MODIS: VIIRS sigue de noche en producción (#1090).
    assert [(p["b"], p["dt"]) for p in cv.pasadas_de_franja(pas, coords, True)] == [("MODIS", t(DIA))]
    filas = [{"volcano": "Lascar", "sensor_bucket": b, "fecha_utc": s + ":00"}
             for b, s in (("MODIS", NOCHE), ("MODIS", DIA), ("VIIRS375", DIA))]
    assert [f["fecha_utc"] for f in cv.filas_ref_de_franja(filas, coords, False)] == [NOCHE + ":00"]
    assert [(f["sensor_bucket"], f["fecha_utc"]) for f in cv.filas_ref_de_franja(filas, coords, True)] == \
        [("MODIS", DIA + ":00")]


def test_la_franja_usa_la_regla_de_store():
    """Día = elevación solar > 0 con la fórmula de pipeline/store.py, la misma que frontend/diurno.js."""
    from pipeline.store import _solar_elevation
    lat, lon = cv.bp._coords_por_volcan()["Lascar"]
    for s in (NOCHE, DIA, "2027-01-05 10:40", "2027-01-05 23:30"):
        dt = datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        assert cv.es_dia(lat, lon, dt) == (_solar_elevation(lat, lon, dt) > 0)


def test_la_pagina_lee_la_franja_diurna():
    src = open(os.path.join(ROOT, "frontend", "comparacion_via_k.js"), encoding="utf-8").read()
    assert "|dia|" in src and "d.dias" in src
    for campo in cv.CAMPOS_DIA:
        assert f'"{campo}"' in src, campo
