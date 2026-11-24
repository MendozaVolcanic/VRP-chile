# -*- coding: utf-8 -*-
"""S192 (adoptada en S193, A45 aprobado por Nicolás el 2026-11-21): el marcador del cráter separa el relleno bow-tie de VIIRS del dato perdido, y la MIR
de la TIR.

POR QUÉ (el fenómeno primero). Al final del barrido de VIIRS los barridos vecinos se solapan; el satélite descarta a
bordo los detectores del borde de cada barrido (ese suelo ya lo midió el barrido contiguo) y el L1B los entrega con una
bandera de relleno y el bit 256 «Bowtie_Deleted» en quality_flags (UserGuide VIIRS L1B Aug 2021, Tabla C.1). El lector
los deja en NaN, como toda bandera, y el marcador de #1060 los contaba como dato faltante del cráter: el 2026-11-20 los
105 píxeles que contó en 27 pasadas NOAA-21 eran todos bow-tie (probe S192, run 44818788733). Un Missing_EV o un
Cal_Fail sí es hueco. Perder la MIR esconde el foco; perder sólo la TIR puede destapar parte de él (S191): por eso
los huecos se cuentan por banda.

Qué se exige: (1) bow-tie junto al cráter cuenta en px_bowtie_crater y no en los huecos, también con la codificación
de M13 (DN 327678 en un dataset de más de 16 bits); (2) Missing_EV o Cal_Fail cuentan en el hueco de su banda;
(3) el total px_mir_invalido_crater no cambia (continuidad de la serie); (4) nada de lo publicado cambia; (5) sin
quality_flags, px_bowtie_crater es None y el hueco es todo lo no finito (MODIS siempre).

El gránulo es sintético (copia del armado de test_via_dato_faltante_crater_s190.py; no se importa para que pytest no
cargue ese módulo dos veces): temperaturas ilustrativas, no instrumentales.
"""
from __future__ import annotations

import json
import math

import numpy as np
import pytest

from pipeline import mirova_v750_codigo as MV

VOLC = "Villarrica"
V_LAT, V_LON = -39.42, -71.93          # volcanoes.yaml, Villarrica (volcan_por_coordenadas exige igualdad)
INNER_KM = 5.0
SENSOR = {"MODIS": "MODIS_AQUA", "VIIRS750": "VIIRS_NOAA20_750", "VIIRS375": "VIIRS_NOAA20"}
PASO_NATIVO_KM = {"MODIS": 1.0, "VIIRS750": 0.75, "VIIRS375": 0.375}
T_FOCO_K = {"MODIS": 420.0, "VIIRS750": 340.0, "VIIRS375": 340.0}
SF, AO = 0.0002, 0.0
BOWTIE, MISSING_EV, CAL_FAIL = 256, 512, 1024          # bits de la Tabla C.1
DN_FLAG = {BOWTIE: 65533, MISSING_EV: 65532, CAL_FAIL: 65534}   # UserGuide págs. 21 y 23
DN_BOWTIE_M13_REAL = 327678                            # lo que trae M13 en VJ202MOD_NRT v2.1 (probe S192)
VALID_MAX_M13_UINT32 = 327670                          # valid_max de M13 en ese archivo (run 44820394068)
CLAVES_S192 = ("px_bowtie_crater", "px_mir_hueco_crater", "px_tir_hueco_crater")


def _granulo(familia, semilla=190):
    paso = PASO_NATIVO_KM[familia]
    n = 2 * int(round(41.0 / paso)) + 1
    c = n // 2
    rng = np.random.default_rng(semilla)
    fil, col = np.indices((n, n))
    yn = (c - fil) * paso + rng.normal(0, 0.05 * paso, (n, n))
    xe = (col - c) * paso + rng.normal(0, 0.05 * paso, (n, n))
    lat = V_LAT + yn / 111.32
    lon = V_LON + xe / (111.32 * math.cos(math.radians(V_LAT)))
    lat[c, c], lon[c, c] = V_LAT, V_LON
    cfg = MV.FAMILIAS[familia]
    t = 268.0 + rng.normal(0, 0.4, (n, n))
    mir = MV.temperatura_a_radiancia(t, cfg["lam_mir"])
    tir = MV.temperatura_a_radiancia(t - 3.0, cfg["lam_tir"])
    mir[c, c] = MV.temperatura_a_radiancia(T_FOCO_K[familia], cfg["lam_mir"])
    tir[c, c] = MV.temperatura_a_radiancia(300.0, cfg["lam_tir"])
    ang = {"sensor_zenith": np.full((n, n), 20.0), "solar_zenith": np.full((n, n), 120.0),
           "sensor_azimuth": np.full((n, n), -100.0), "solar_azimuth": np.full((n, n), 50.0)}
    b_mir, b_tir = cfg["bandas"]
    return {"rad": {b_mir: mir, b_tir: tir}, "lat": lat, "lon": lon, "ang": ang, "c": c,
            "b_mir": b_mir, "b_tir": b_tir}


def _l1b(tmp_path, gr, marcas, nombre="l1b.nc", con_qf=True, dn_bowtie_mir=None):
    """L1B sintético. marcas = {(banda "mir"|"tir", fila, col): bit}: pone el DN de bandera y el bit en quality_flags.
    dn_bowtie_mir: si se da, la MIR se guarda en uint32 y su bow-tie con ese DN (codificación real de M13)."""
    import h5py
    ruta = tmp_path / nombre
    with h5py.File(ruta, "w") as f:
        obs = f.create_group("observation_data")
        for lado, b in (("mir", gr["b_mir"]), ("tir", gr["b_tir"])):
            ancho = np.uint32 if (lado == "mir" and dn_bowtie_mir is not None) else np.uint16
            dn = np.clip(np.round((gr["rad"][b] - AO) / SF), 0, 65527).astype(ancho)
            qf = np.zeros(dn.shape, np.uint16)
            for (bl, i, j), bit in marcas.items():
                if bl == lado:
                    dn[i, j] = dn_bowtie_mir if (bit == BOWTIE and ancho == np.uint32) else DN_FLAG[bit]
                    qf[i, j] |= bit
            ds = obs.create_dataset(b, data=dn)
            if ancho == np.uint32:
                # #1070: el lector corta en el valid_max de la variable; M13 uint32 de VJ202MOD v2.1 trae 327670.
                ds.attrs["valid_max"] = np.array([VALID_MAX_M13_UINT32], np.uint32)
            ds.attrs["scale_factor"] = np.array([SF], np.float32)
            ds.attrs["add_offset"] = np.array([AO], np.float32)
            if con_qf:
                obs.create_dataset(f"{b}_quality_flags", data=qf)
    return ruta


def _correr(ruta, gr, familia):
    rad = MV.leer_radiancia_l1b(ruta, bandas=(gr["b_mir"], gr["b_tir"]))
    rec = MV.calcular_vrp_granulo(rad, gr["lat"], gr["lon"], gr["ang"], VOLC, V_LAT, V_LON, INNER_KM,
                                  SENSOR[familia], familia=familia)
    assert rec is not None, "el gránulo sintético no dio record (error de armado)"
    return rec, rad


def _d(rec):
    return rec["diag_codigo_mirova"]


def _sin(rec):
    r = json.loads(json.dumps(rec, default=float))
    for k in CLAVES_S192:
        r["diag_codigo_mirova"].pop(k, None)
    return r


def _fila_bowtie(gr, fila):
    n = gr["lat"].shape[1]
    return {(lado, fila, j): BOWTIE for lado in ("mir", "tir") for j in range(n)}


@pytest.mark.parametrize("familia", ("VIIRS750", "VIIRS375"))
def test_fila_bowtie_junto_al_crater_no_es_hueco(tmp_path, familia):
    """Una fila de detectores borrados pasando junto al cráter, como en el borde de un barrido."""
    gr = _granulo(familia)
    d = _d(_correr(_l1b(tmp_path, gr, _fila_bowtie(gr, gr["c"] + 1), "bt.nc"), gr, familia)[0])
    d0 = _d(_correr(_l1b(tmp_path, gr, {}, "sano.nc"), gr, familia)[0])
    assert d.get("px_mir_invalido_crater", 0) > 0                         # (3) el marcador de siempre lo cuenta
    assert d.get("px_bowtie_crater") == d["px_mir_invalido_crater"]      # (1) y todo es bow-tie
    assert (d.get("px_mir_hueco_crater"), d.get("px_tir_hueco_crater")) == (0, 0)
    assert (d0.get("px_bowtie_crater"), d0.get("px_mir_hueco_crater"), d0.get("px_tir_hueco_crater")) == (0, 0, 0)


def test_bowtie_con_la_codificacion_real_de_m13(tmp_path):
    """(1) M13 trae el bow-tie como DN 327678 en un dataset de más de 16 bits; el bit lo reconoce igual."""
    gr = _granulo("VIIRS750")
    d = _d(_correr(_l1b(tmp_path, gr, _fila_bowtie(gr, gr["c"] + 1), dn_bowtie_mir=DN_BOWTIE_M13_REAL),
                   gr, "VIIRS750")[0])
    assert d.get("px_mir_invalido_crater", 0) > 0
    assert d.get("px_bowtie_crater") == d["px_mir_invalido_crater"]
    assert d.get("px_mir_hueco_crater") == 0


@pytest.mark.parametrize("bit,lado,esperado", [(MISSING_EV, "mir", (1, 0)), (CAL_FAIL, "tir", (0, 1)),
                                               (BOWTIE, "mir", (0, 0)), (BOWTIE, "tir", (0, 0))])
@pytest.mark.parametrize("familia", ("VIIRS750", "VIIRS375"))
def test_bandera_en_el_crater_cuenta_en_su_banda(tmp_path, familia, bit, lado, esperado):
    """(2) y (3): un píxel con bandera en el cráter; el total sigue en 1 y el hueco va a su banda (o a bow-tie)."""
    gr = _granulo(familia)
    c = gr["c"]
    d = _d(_correr(_l1b(tmp_path, gr, {(lado, c, c): bit}), gr, familia)[0])
    assert d.get("px_mir_invalido_crater") == 1
    assert (d.get("px_mir_hueco_crater"), d.get("px_tir_hueco_crater")) == esperado
    assert d.get("px_bowtie_crater") == (1 if bit == BOWTIE else 0)


@pytest.mark.parametrize("familia", ("VIIRS750", "VIIRS375"))
def test_lo_publicado_no_cambia(tmp_path, familia):
    """(4) con y sin las máscaras de bow-tie el record es el mismo salvo las claves de diagnóstico nuevas."""
    gr = _granulo(familia)
    rec, rad = _correr(_l1b(tmp_path, gr, _fila_bowtie(gr, gr["c"] + 1)), gr, familia)
    rad = {k: v for k, v in rad.items() if not k.startswith("bowtie_")}
    rec_sin = MV.calcular_vrp_granulo(rad, gr["lat"], gr["lon"], gr["ang"], VOLC, V_LAT, V_LON, INNER_KM,
                                      SENSOR[familia], familia=familia)
    assert _sin(rec) == _sin(rec_sin)


def test_sin_quality_flags_bowtie_sin_dato(tmp_path):
    """(5) sin quality_flags no se puede separar: px_bowtie_crater None y todo lo no finito es hueco."""
    gr = _granulo("VIIRS750")
    c = gr["c"]
    d = _d(_correr(_l1b(tmp_path, gr, {("mir", c, c): BOWTIE}, con_qf=False), gr, "VIIRS750")[0])
    assert "px_bowtie_crater" in d and d["px_bowtie_crater"] is None
    assert d.get("px_mir_hueco_crater") == 1


def test_modis_sin_bowtie():
    """(5) MODIS no descarta a bordo y su lector no trae máscara: None y el hueco es lo no finito."""
    gr = _granulo("MODIS")
    c = gr["c"]
    gr["rad"][gr["b_mir"]][c, c] = np.nan
    rec = MV.calcular_vrp_granulo(gr["rad"], gr["lat"], gr["lon"], gr["ang"], VOLC, V_LAT, V_LON, INNER_KM,
                                  SENSOR["MODIS"], familia="MODIS")
    d = _d(rec)
    assert "px_bowtie_crater" in d and d["px_bowtie_crater"] is None
    assert (d.get("px_mir_hueco_crater"), d.get("px_tir_hueco_crater")) == (1, 0)
