# -*- coding: utf-8 -*-
# FICHA (SDA, CPLT 372): brazos de medición de D36 punto 1. Sólo lectura; no es detección de producción.
"""Brazos del A/B de umbrales MODIS (D36 punto 6 del catálogo, punto 1 del encargo S190).

POR QUÉ una copia de detectar_mirova y no un flag en pipeline/: no se toca producción para medir (A45). La copia sólo
parametriza los dos números nocturnos que difieren de la Tabla 1 de Coppola et al. 2016a (página 7, leída renderizada
en S190: noche K1 -0,8; C1 0,003 en ROI1 y 0,01 en ROI2; C2 5 y 10). El control que la valida se cancela por
construcción (A110): con los números de la vía, la copia tiene que dar el MISMO record que el módulo de producción
en cada pasada (control_copia_igual). Una copia en línea diverge (A102): por eso el control corre en cada pasada.
Brazos:
  A   la vía de hoy: K1 -0,7 y piso de dNTI fuera de la cumbre (zonas 0 y 1 de la caja) 0,02 (.m de VIIRS 750 l. 177-199)
  B   Tabla 1: K1 -0,8 y piso 0,01
  B1  sólo K1 -0,8 (piso 0,02)
  B2  sólo piso 0,01 (K1 -0,7)
Lo demás (piso 0,003 en la cumbre, ETI 0,01 y 0,003, sigmas 10 y 5, día) queda igual que la vía: ya coincide con la
Tabla 1 de noche, y la vía MODIS no procesa de día en la práctica (S190: 0 records diurnos de vía en los 11 Tier A).
"""
from unittest.mock import patch

import numpy as np

from pipeline import mirova_v750_codigo as MV

BRAZOS = {"A": (-0.7, 0.02), "B": (-0.8, 0.01), "B1": (-0.8, 0.02), "B2": (-0.7, 0.01)}


def detectar_param(m13, m15, box, dayflag, sunglint, devolver_diag=False, lam_mir=MV.LAMBDA_M13,
                   lam_tir=MV.LAMBDA_M15, u_abs_noche=-0.7, n1_noche=0.02):
    """Copia de MV.detectar_mirova con K1 y el piso n1 nocturnos como parámetros (todo lo demás, idéntico)."""
    m13 = np.asarray(m13, float)
    vacio = np.zeros(m13.shape, bool)

    def _salida(mask, d):
        return (mask, d) if devolver_diag else mask

    d = {"motivo": None}
    if not np.isfinite(sunglint) or sunglint < 12:
        d["motivo"] = "sunglint"
        return _salida(vacio, d)
    m15 = np.array(m15, float)
    box = np.array(box, float)
    box[:, [0, -1]] = np.nan
    box[[0, -1], :] = np.nan
    m0 = np.where(box == 0, 1.0, np.nan)
    m1 = np.where(box == 1, 1.0, np.nan)
    m2 = np.where(box == 2, 1.0, np.nan)
    excl = np.isnan(box)
    bt15 = MV.radiancia_a_temperatura(m15, lam_tir)
    with np.errstate(invalid="ignore"):
        frio = bt15 <= 200
    bt15[frio] = np.nan
    m15[frio] = np.nan
    with np.errstate(invalid="ignore", divide="ignore"):
        nti = (m13 - m15) / (m13 + m15)
    if nti.size == 0 or np.isnan(nti).sum() >= np.floor(nti.size / 2):
        d["motivo"] = "escena_invalida"
        return _salida(vacio, d)
    nti_roi = nti.copy()
    nti_roi[excl] = np.nan
    if dayflag == 0:
        u_abs, s1, s2, n1, n2, e1, e2 = u_abs_noche, 10, 5, n1_noche, 0.003, 0.01, 0.003
    else:
        u_abs, s1, s2, n1, n2, e1, e2 = -0.5, 15, 15, 0.02, 0.02, 0.02, 0.02
    with np.errstate(invalid="ignore"):
        absol = nti_roi > u_abs
    p1 = MV._pasada_contextual(nti_roi, bt15, m15, excl, m0, m1, m2, absol, s1, s2, n1, n2, e1, e2, lam_mir=lam_mir)
    ctx1 = p1[0] | p1[1] | p1[2]
    p2 = MV._pasada_contextual(nti_roi, bt15, m15, excl, m0, m1, m2, absol | ctx1, s1, s2, n1, n2, e1, e2,
                               lam_mir=lam_mir)
    mask = ctx1 | absol | p2[0] | p2[1] | p2[2]
    d.update({"pasada1": p1[3], "pasada2": p2[3], "n_abs": int(absol.sum()), "n_p1": int(ctx1.sum()),
              "n_p2": int((p2[0] | p2[1] | p2[2]).sum()), "nti": nti_roi,
              "contrastes": {1: (p1[4], p1[5]), 2: (p2[4], p2[5])}, "box": box})
    return _salida(mask, d)


def _fn(brazo):
    u, n1 = BRAZOS[brazo]

    def f(*a, **k):
        # S197 (rama desechable s197-1106-probe): desde S195/S196 procesar_grilla pasa zona_a, s_a y piso_a; en
        # producción van en None. La copia del .m no los conoce: se exige None y se descartan.
        for kk in ("zona_a", "s_a", "piso_a"):
            if k.pop(kk, None) is not None:
                raise ValueError("brazos.py: %s distinto de None, no es el perfil de producción" % kk)
        return detectar_param(*a, u_abs_noche=u, n1_noche=n1, **k)
    return f


def correr_brazos(rad, lat, lon, ang, nombre, vent_lat, vent_lon, inner_km, sensor, sin_corte_5km=False):
    """Record de la vía por brazo (más «prod»: el módulo sin tocar). sin_corte_5km (punto 3): quita el corte de 5 km
    al centro sólo en esta llamada (patch.dict sobre FAMILIAS["MODIS"])."""
    out = {}
    extra = {"dist_max_centro_km": None} if sin_corte_5km else {}
    with patch.dict(MV.FAMILIAS["MODIS"], extra):
        out["prod"] = MV.calcular_vrp_granulo(rad, lat, lon, ang, nombre, vent_lat, vent_lon, inner_km, sensor,
                                              familia="MODIS")
        for b in BRAZOS:
            with patch.object(MV, "detectar_mirova", _fn(b)):
                out[b] = MV.calcular_vrp_granulo(rad, lat, lon, ang, nombre, vent_lat, vent_lon, inner_km, sensor,
                                                 familia="MODIS")
    return out
