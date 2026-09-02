# -*- coding: utf-8 -*-
"""S132 R17 — sello de tiempo de proceso en el record.

POR QUÉ. El record guarda cuándo el SATÉLITE tomó la escena (`datetime_utc`) pero no cuándo
NOSOTROS la procesamos. Sin esa segunda marca, la latencia del NRT —el tiempo entre que el
dato existe y el operador puede verlo— sólo se puede estimar por la fecha de modificación
del archivo, que se pierde en cada `git clone` y en cada deploy.

Es la diferencia entre poder decir «el sistema entrega a las 3,2 h de la pasada» y tener que
adivinarlo. Para un sistema de apoyo a la decisión de alerta, la latencia es parte del
producto: una detección que llega doce horas tarde no sirve igual que una que llega en dos.

Es un campo descriptivo: no entra en detección, ni en magnitud, ni en ninguna compuerta.
"""
import re

import pytest


def test_el_record_lleva_sello_de_proceso(tmp_path, monkeypatch):
    from pipeline import store
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    r = {"datetime_utc": "2026-05-12 03:30", "sensor": "VIIRS_NOAA20", "vrp_mw": 1.0,
         "hotspot_dist_km": 0.4, "product_version": "standard"}
    store.append_record("TestVolcano", r)
    assert "processed_utc" in r
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", r["processed_utc"]), \
        f"formato inesperado: {r['processed_utc']}"


def test_el_sello_es_posterior_a_la_pasada(tmp_path, monkeypatch):
    """Control de cordura: procesar no puede ocurrir antes de observar."""
    from datetime import datetime, timezone

    from pipeline import store
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    r = {"datetime_utc": "2026-05-12 03:30", "sensor": "VIIRS_NOAA20", "vrp_mw": 1.0,
         "hotspot_dist_km": 0.4, "product_version": "standard"}
    store.append_record("TestVolcano", r)
    proc = datetime.strptime(r["processed_utc"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    pasada = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    assert proc > pasada


def test_un_reproceso_actualiza_el_sello(tmp_path, monkeypatch):
    """El sello dice cuándo se produjo ESTA versión del record, no la primera de todas:
    si no, un reproceso dejaría una latencia falsa de meses."""
    from pipeline import store
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    base = dict(datetime_utc="2026-05-12 03:30", sensor="VIIRS_NOAA20", vrp_mw=1.0,
                hotspot_dist_km=0.4, product_version="standard")
    r1 = dict(base); r1["processed_utc"] = "2020-01-01T00:00:00Z"
    store.append_record("TestVolcano", r1)
    assert r1["processed_utc"] != "2020-01-01T00:00:00Z"
