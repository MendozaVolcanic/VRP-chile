# -*- coding: utf-8 -*-
"""Tests del conteo S144 de pasadas VIIRS 375 con TIF UTM de MIROVA.

POR QUÉ. El conteo decide sobre qué muestra se mide `keep_peak` con dirección (decisión 1 del traspaso
S144). Un emparejamiento de TIF que aceptara filas vacías, horas de nombre de archivo u otro volcán
inflaría la muestra sin dar error. Estos tests fijan las definiciones de
`experiments/_s144_conteo_tif/README.md`.
"""
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DIR = os.path.join(ROOT, "experiments", "_s144_conteo_tif")
for p in (ROOT, os.path.join(ROOT, "scripts"), DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

import conteo_tif as ct  # noqa: E402

CAB = "captured_at_utc,volcano,sensor,band,acquisition_utc,last_modified_utc,md5,size_bytes,tif_path,kmz_path\n"


def _fila(vol="Villarrica", sensor="VIIRS375", acq="2026-09-15T05:10:00+00:00", size="40000",
          tif="data/tif/Villarrica/x.tif"):
    return f"2026-09-15T06:00:00+00:00,{vol},{sensor},I4,{acq},2026-09-15T05:30:00+00:00,abc,{size},{tif},\n"


def _dt(s):
    return datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)


# ------------------------------------------------------------------ índice
def test_indice_descarta_otro_sensor_vacios_y_sin_adquisicion():
    txt = CAB + _fila() + _fila(sensor="MODIS") + _fila(size="0") + _fila(acq="")
    idx = ct.cargar_indice_tif(txt)
    assert sum(len(v) for v in idx.values()) == 1


def test_indice_mapea_nombre_de_carpeta_mirova_al_del_repo():
    idx = ct.cargar_indice_tif(CAB + _fila(vol="ChillanNevadosde"))
    assert list(idx) == ["NevadosDeChillan"]


def test_inicio_utm_es_la_primera_adquisicion():
    txt = CAB + _fila(acq="2026-09-16T05:00:00+00:00") + _fila(acq="2026-09-14T06:36:10+00:00")
    assert ct.inicio_utm(ct.cargar_indice_tif(txt)) == datetime(2026, 9, 14, 6, 36, 10, tzinfo=timezone.utc)


def test_imagen_repetida_bajo_otra_adquisicion_no_es_propia():
    # MIROVA volvió a servir la imagen de las 05:10 rotulada 05:40: sólo la primera es propia
    txt = (CAB + _fila(acq="2026-09-15T05:10:00+00:00", tif="a.tif").replace(",abc,", ",m1,")
           + _fila(acq="2026-09-15T05:40:00+00:00", tif="b.tif").replace(",abc,", ",m1,")
           + _fila(acq="2026-09-15T05:10:00+00:00", tif="a.tif").replace(",abc,", ",m1,"))
    idx = ct.cargar_indice_tif(txt)
    propias = {f["tif_path"]: f["propia"] for _, f in idx["Villarrica"]}
    assert propias == {"a.tif": True, "b.tif": False}


# ------------------------------------------------------------------ emparejamiento
def test_empareja_dentro_de_tolerancia_y_elige_la_mas_cercana():
    txt = CAB + _fila(acq="2026-09-15T05:10:00+00:00", tif="a.tif") + _fila(acq="2026-09-15T05:03:00+00:00", tif="b.tif")
    idx = ct.cargar_indice_tif(txt)
    fila, dts = ct.emparejar_tif(idx, "Villarrica", _dt("2026-09-15 05:05"))
    assert fila["tif_path"] == "b.tif" and dts == 120


def test_no_empareja_fuera_de_tolerancia():
    idx = ct.cargar_indice_tif(CAB + _fila(acq="2026-09-15T05:10:00+00:00"))
    assert ct.emparejar_tif(idx, "Villarrica", _dt("2026-09-15 05:26")) is None
    assert ct.emparejar_tif(idx, "Villarrica", _dt("2026-09-15 05:25")) is not None


def test_no_empareja_otro_volcan():
    idx = ct.cargar_indice_tif(CAB + _fila(vol="Llaima"))
    assert ct.emparejar_tif(idx, "Villarrica", _dt("2026-09-15 05:10")) is None


# ------------------------------------------------------------------ patrón keep_peak
def _r(src="test1_roi", n=1, fh=(-39.4202, -71.9399), cen=(-39.3977, -71.9587)):
    return {"final_hotspot_source": src, "final_hotspot_lat": fh[0], "final_hotspot_lon": fh[1],
            "primary_cluster": {"n_pixels": n, "centroid_lat": cen[0], "centroid_lon": cen[1]}}


def test_patron_keep_peak_caso_villarrica_real():
    # record Villarrica 2026-09-19 05:06 VIIRS_NOAA20: cúmulo de 1 píxel a ~2,98 km del vent
    assert ct.patron_keep_peak(_r()) is True


def test_patron_exige_test1_roi_un_pixel_y_separacion():
    assert ct.patron_keep_peak(_r(src="ctx_cluster")) is False
    assert ct.patron_keep_peak(_r(n=2)) is False
    assert ct.patron_keep_peak(_r(cen=(-39.4230, -71.9399))) is False   # ~0,31 km
    assert ct.patron_keep_peak(_r(cen=(-39.4260, -71.9399))) is True    # ~0,64 km


def test_patron_sin_cumulo_o_sin_posicion_es_falso():
    r = _r()
    r["primary_cluster"] = None
    assert ct.patron_keep_peak(r) is False
    r = _r()
    r["final_hotspot_lat"] = None
    assert ct.patron_keep_peak(r) is False


# ------------------------------------------------------------------ lectura del TIF
def test_es_utm_375():
    assert ct.es_utm_375("EPSG:32719", (375.0, 375.0)) is True
    assert ct.es_utm_375("EPSG:32718", (374.9, 375.2)) is True
    assert ct.es_utm_375("EPSG:4326", (0.0034, 0.0034)) is False
    assert ct.es_utm_375("EPSG:32719", (1000.0, 1000.0)) is False


# ------------------------------------------------------------------ tabla de cruce
def test_tabla_de_cruce_cuenta_cada_combinacion():
    ps = [{"tif": True, "alerta": True, "patron": True, "pub": 1},
          {"tif": True, "alerta": False, "patron": True, "pub": 0},
          {"tif": False, "alerta": True, "patron": False, "pub": 1}]
    t = ct.tabla_cruce(ps)
    assert t == {"pasadas": 3, "con_tif": 2, "con_alerta": 2, "alerta_y_tif": 1, "patron": 2,
                 "patron_y_tif": 2, "patron_alerta_tif": 1, "publicadas": 2,
                 "patron_publicadas": 1, "patron_publicadas_tif": 1}
