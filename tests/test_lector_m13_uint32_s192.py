# -*- coding: utf-8 -*-
"""S192: los lectores del L1B de VIIRS separan medición de bandera con el valid_max de cada variable, no con una
constante de uint16.

POR QUÉ (el fenómeno primero). M13 (4 µm) es la banda que ve la lava. En VJ202MOD_NRT v2.1 NASA la guarda en uint32,
con más resolución y el mismo techo físico: valid_max 327670, banderas 327677 a 327679, relleno 327680 (probe S192,
run 44820394068). El UserGuide la describe como uint16 con banderas desde 65532. Con el corte fijo `DN >= 65528`, la
vía borraba todo píxel M13 sobre unos 512 K: en una fase efusiva, el píxel del foco, que la interpolación rellenaba
con vecinos fríos. La guardia K leía la temperatura por la LUT (sin ese corte), pero enmascaraba la lista fija
{65532..65535}: en M13 uint32 eso borra valores válidos y deja pasar las banderas reales hasta la LUT.

Qué se exige: (1) un foco M13 uint32 a 600 K llega como radiancia en la vía y como temperatura en K; (2) las banderas
reales de M13 uint32 quedan en NaN en las dos, aunque la LUT tenga algo en esas posiciones; (3) el formato uint16 no
cambia: 65527 es medición, 65528 a 65535 no (con valid_max y sin él); (4) un archivo que no es uint16 y no trae
valid_max no se mide con un corte inventado (error). Los atributos de M13 y M15 son los del archivo real (copiados del
artefacto `m13_atributos.json` del run); las temperaturas del foco son ilustrativas.
"""
from __future__ import annotations

import numpy as np
import pytest

from pipeline import mirova_v750_codigo as MV
from pipeline import process_viirs_mod as PVM

# Atributos reales, VJ202MOD_NRT.A2026324.0448.021.2026324063539.nc (artefacto del run 44820394068)
M13_REAL = {"valid_min": 0, "valid_max": 327670, "_FillValue": 327680, "flag_values": [327677, 327678, 327679],
            "scale_factor": 0.0016174810007214546, "add_offset": 0.0010805600322782993, "lut_largo": 327681}
M15_REAL = {"valid_min": 0, "valid_max": 65527, "_FillValue": 65535, "flag_values": [65532, 65533, 65534],
            "scale_factor": 0.00036626122891902924, "add_offset": 0.004836199805140495, "lut_largo": 65536}
N = 8
T_FOCO_K = 600.0       # ilustrativa: sobre los ~512 K del corte viejo y bajo el techo de 634 K de la guardia


def _dn(L, a):
    return int(round((L - a["add_offset"]) / a["scale_factor"]))


def _l1b(tmp_path, m13_dn, m13_dtype=np.uint32, con_attrs=True, con_lut=False, nombre="l1b.nc", cola_lut=300.0):
    """L1B sintético con M13 (tipo pedido) y M15 uint16 a 268 K. m13_dn: dict {(fila, col): DN}."""
    import h5py
    ruta = tmp_path / nombre
    a13 = M13_REAL if m13_dtype == np.uint32 else M15_REAL | {"scale_factor": 0.008088269, "add_offset": 0.00108056}
    l13 = MV.temperatura_a_radiancia(268.0, MV.LAMBDA_M13)
    l15 = MV.temperatura_a_radiancia(268.0, MV.LAMBDA_M15)
    d13 = np.full((N, N), _dn(l13, a13), m13_dtype)
    for (i, j), v in m13_dn.items():
        d13[i, j] = v
    d15 = np.full((N, N), _dn(l15, M15_REAL), np.uint16)
    with h5py.File(ruta, "w") as f:
        obs = f.create_group("observation_data")
        for b, d, a in (("M13", d13, a13), ("M15", d15, M15_REAL)):
            ds = obs.create_dataset(b, data=d)
            ds.attrs["scale_factor"] = np.array([a["scale_factor"]], np.float32)
            ds.attrs["add_offset"] = np.array([a["add_offset"]], np.float32)
            if con_attrs:
                for k in ("valid_min", "valid_max", "_FillValue"):
                    ds.attrs[k] = np.array([a[k]], d.dtype)
                ds.attrs["flag_values"] = np.array(a["flag_values"], d.dtype)
            if con_lut:
                # LUT de BT ilustrativa, monótona en el rango válido; fuera de él (donde caen las banderas) un valor
                # plausible, para que la prueba no dependa de lo que la LUT real tenga ahí.
                n = a["lut_largo"] if (b == "M15" or m13_dtype == np.uint32) else 65536
                lut = np.full(n, cola_lut, np.float32)
                lam = MV.LAMBDA_M13 if b == "M13" else MV.LAMBDA_M15
                idx = np.arange(a["valid_max"] + 1)
                L = np.clip(idx * a["scale_factor"] + a["add_offset"], 1e-6, None)
                lut[: a["valid_max"] + 1] = MV.radiancia_a_temperatura(L, lam)
                obs.create_dataset(f"{b}_brightness_temperature_lut", data=lut)
    return ruta


# ------------------------------------------------------------------------------------------ (1) foco caliente
def test_via_foco_m13_uint32_sobre_65528_llega_como_radiancia(tmp_path):
    L = MV.temperatura_a_radiancia(T_FOCO_K, MV.LAMBDA_M13)
    dn = _dn(L, M13_REAL)
    assert 65528 <= dn <= M13_REAL["valid_max"]          # control: el caso cae donde el corte viejo cortaba
    rad = MV.leer_radiancia_l1b(_l1b(tmp_path, {(3, 3): dn}))
    assert np.isfinite(rad["M13"][3, 3])
    assert rad["M13"][3, 3] == pytest.approx(L, abs=M13_REAL["scale_factor"])
    assert MV.radiancia_a_temperatura(rad["M13"][3, 3], MV.LAMBDA_M13) == pytest.approx(T_FOCO_K, abs=0.1)


def test_guardia_k_foco_m13_uint32_y_dn_65532_son_medicion(tmp_path):
    L = MV.temperatura_a_radiancia(T_FOCO_K, MV.LAMBDA_M13)
    ruta = _l1b(tmp_path, {(3, 3): _dn(L, M13_REAL), (4, 4): 65532}, con_lut=True)
    bt = PVM.read_viirs_mod_l1b(ruta)["M13"]
    assert bt[3, 3] == pytest.approx(T_FOCO_K, abs=0.1)
    assert np.isfinite(bt[4, 4])                         # 65532 es un valor válido en M13 uint32 (~512 K)


# ------------------------------------------------------------------------------------------ (2) banderas reales
@pytest.mark.parametrize("dn", [327671, 327677, 327678, 327679, 327680])
def test_banderas_m13_uint32_quedan_nan_en_la_via_y_en_k(tmp_path, dn):
    ruta = _l1b(tmp_path, {(3, 3): dn, (2, 2): M13_REAL["valid_max"]}, con_lut=True)
    rad = MV.leer_radiancia_l1b(ruta)
    bt = PVM.read_viirs_mod_l1b(ruta)["M13"]
    assert np.isnan(rad["M13"][3, 3]) and np.isnan(bt[3, 3])
    assert np.isfinite(rad["M13"][2, 2])                 # el valid_max mismo es medición


# ------------------------------------------------------------------------------------------ (3) uint16 sin cambio
@pytest.mark.parametrize("con_attrs", [True, False])
def test_uint16_igual_que_antes(tmp_path, con_attrs):
    dns = {(1, j): v for j, v in enumerate([65527, 65528, 65531, 65532, 65533, 65534, 65535])}
    ruta = _l1b(tmp_path, dns, m13_dtype=np.uint16, con_attrs=con_attrs)
    m13 = MV.leer_radiancia_l1b(ruta)["M13"][1, :7]
    assert np.isfinite(m13[0]) and np.isnan(m13[1:]).all()


def test_guardia_k_uint16_banderas_nan(tmp_path):
    # el DN válido es uno intermedio: en M13 uint16 el 65527 está sobre el techo de 634 K de la guardia, que lo descarta
    dns = {(1, j): v for j, v in enumerate([30000, 65532, 65533, 65534, 65535])}
    bt = PVM.read_viirs_mod_l1b(_l1b(tmp_path, dns, m13_dtype=np.uint16, con_lut=True))["M13"][1, :5]
    assert np.isfinite(bt[0]) and np.isnan(bt[1:]).all()


# ------------------------------------------------------------------------------------------ (4) sin base
def test_uint32_sin_valid_max_no_se_mide_con_un_corte_inventado(tmp_path):
    ruta = _l1b(tmp_path, {}, con_attrs=False)
    with pytest.raises(ValueError, match="valid_max"):
        MV.leer_radiancia_l1b(ruta)
