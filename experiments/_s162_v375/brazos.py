# -*- coding: utf-8 -*-
"""S162 V375-C: los brazos de ROI del código de MIROVA en VIIRS 375 (dónde rigen los umbrales de cumbre).

POR QUÉ. En el código de VIIRS 750 de MIROVA (`MIROVA_VIIRS750_hotspot_detection.m`, port validado contra Octave en
`experiments/_s158_audit_r2/oraculo/mirova_v750_r2.py`, «ORA») la matriz BOX tiene tres valores, pero las regiones 0 y
1 usan los MISMOS umbrales de escena (10 sigma y mínimos 0,02 / 0,01 de noche; ORA.detectar, m0 y m1 con s1, n1, e1):
sólo la región 2 (la caja de cumbre, 5 sigma y 0,003) es distinta. Por eso un brazo de ROI queda definido entero por
el conjunto de celdas con BOX = 2, y la media y la desviación del contraste salen de toda la escena en todos los brazos.
El port de S159 (`experiments/_s159/portes/`) midió que en VIIRS 375 la caja de cumbre del mismo tamaño en metros que la
de 750 (±2.625 m, 14 x 14 celdas) deja sin ver las alertas débiles de MIROVA en Cordón Caulle (lacolito a 5 a 8 km) y
Tupungatito (cráter a 4,79 km al NW del centro del TIF), y que con toda la ROI1 en umbrales de cumbre las recupera
(P-4). El `.m` dice que las ROI se ajustan por volcán. Estos brazos miden cuál reproduce a MIROVA (A115).

Brazos (PREREGISTRO_C.md §2). Centro M = punto de referencia de MIROVA (X0, Y0, centro del TIF UTM); centro C = cráter
de volcanoes.yaml (vent_lat, vent_lon) proyectado a la grilla:
  M14       caja de cumbre ±2.625 m alrededor de M (14 x 14): la «física» del port de S159, brazo de referencia
  M13, M21  13 x 13 y 21 x 21 celdas centradas en la celda más cercana a M
  C13, C14, C21  lo mismo alrededor del cráter
  PIX7      7 x 7 celdas alrededor de M (la «pixel» del port de S159; descriptivo)
  SENS      ±7.875 m alrededor de M en umbrales de cumbre (la «sensible» de S159, N-3 en 750)
  CIRC      las celdas a inner_radius_km o menos del cráter (el círculo del tablero como caja sensible)
  SENS_PT   SENS sólo en Cordón Caulle y Tupungatito, M14 en los demás
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ / "experiments/_s159/portes"))
import mirova_port as MP  # noqa: E402

ORA = MP.ORA
BRAZOS = ("M14", "M13", "M21", "C13", "C14", "C21", "PIX7", "SENS", "CIRC", "SENS_PT")
REFERENCIA = "M14"
VOLCANES_SENS_PT = ("PuyehueCordonCaulle", "Tupungatito")
EQUIV_S159 = {"M14": "fisica", "PIX7": "pixel", "SENS": "sensible"}   # brazos que el port de S159 ya corrió


def crater_xy(g, vent_lat, vent_lon):
    from pyproj import Transformer
    t = Transformer.from_crs("EPSG:4326", f"EPSG:{g['epsg']}", always_xy=True)
    x, y = t.transform(vent_lon, vent_lat)
    return float(x), float(y)


def _cuadrado_celdas(g, X, Y, xc, yc, n):
    """n x n celdas centradas en la celda más cercana a (xc, yc); n impar."""
    assert n % 2 == 1
    i0 = int(np.argmin(np.abs(Y[:, 0] - yc)))
    j0 = int(np.argmin(np.abs(X[0, :] - xc)))
    h = (n - 1) // 2
    m = np.zeros(X.shape, bool)
    m[max(i0 - h, 0):i0 + h + 1, max(j0 - h, 0):j0 + h + 1] = True
    return m


def _cuadrado_metros(X, Y, xc, yc, half_m):
    return (np.abs(X - xc) <= half_m) & (np.abs(Y - yc) <= half_m)


def roi2(g, brazo, X0, Y0, xc, yc, inner_km, volcan):
    """Máscara de las celdas con umbrales de cumbre (BOX = 2) del brazo."""
    X, Y = MP.centros(g)
    if brazo == "SENS_PT":
        brazo = "SENS" if volcan in VOLCANES_SENS_PT else "M14"
    if brazo == "M14":
        return _cuadrado_metros(X, Y, X0, Y0, MP.HALF_ROI2_M)
    if brazo == "C14":
        return _cuadrado_metros(X, Y, xc, yc, MP.HALF_ROI2_M)
    if brazo == "SENS":
        return _cuadrado_metros(X, Y, X0, Y0, MP.HALF_ROI1_M)
    if brazo == "CIRC":
        return np.hypot(X - xc, Y - yc) <= inner_km * 1000.0
    if brazo == "PIX7":
        return _cuadrado_celdas(g, X, Y, X0, Y0, 7)
    centro = {"M": (X0, Y0), "C": (xc, yc)}[brazo[0]]
    return _cuadrado_celdas(g, X, Y, centro[0], centro[1], int(brazo[1:]))


def caja(g, brazo, X0, Y0, xc, yc, inner_km, volcan):
    """BOX del .m: 1 en la ROI1 física de S159 (±7.875 m alrededor de M), 0 fuera, 2 en la ROI2 del brazo. Las regiones
    0 y 1 tienen los mismos umbrales (ver el docstring del módulo); se conserva la forma de S159 para que M14, PIX7 y
    SENS den la BOX idéntica a la de mirova_port.caja (control en probar_brazos.py)."""
    X, Y = MP.centros(g)
    b = np.zeros((g["n"], g["n"]))
    b[_cuadrado_metros(X, Y, X0, Y0, MP.HALF_ROI1_M)] = 1
    b[roi2(g, brazo, X0, Y0, xc, yc, inner_km, volcan)] = 2
    return b


def correr_box(mir, tir, g, box, X0, Y0, dayflag, sunglint, cfg, semillas=0, modo=""):
    """mirova_port.correr con la BOX dada (en vez de armarla por modo). Mismas salidas, mismas distancias a (X0, Y0)."""
    mask, _lista, d = MP.detectar(mir, tir, box, dayflag, sunglint, cfg)
    r = MP.vrp(mir, mask, cfg)
    X, Y = MP.centros(g)
    rr, cc = np.nonzero(mask)
    with MP.longitudes(cfg):
        bt = ORA.radiancia_a_temperatura(np.asarray(mir, float), cfg["lam_mir"])
    out = {"modo": modo, "motivo_vacio": d.get("motivo"), "n_abs": d.get("n_abs"), "n_p1": d.get("n_p1"),
           "n_p2": d.get("n_p2"), "npix": r["npix"], "vrp_mw": None if r["npix"] == 0 else float(r["VRP_MW"]),
           "pixeles": [[int(a), int(b), int(box[a, b]),
                        round(float(np.hypot(X[a, b] - X0, Y[a, b] - Y0) / 1000.0), 3),
                        round(float(mir[a, b]), 5), round(float(bt[a, b]), 2)] for a, b in zip(rr, cc)],
           "nan_mir": int(np.isnan(mir).sum()), "nan_tir": int(np.isnan(tir).sum()),
           "umbrales_p1": {k: (d.get("pasada1") or {}).get(k) for k in ("u_nti1", "u_nti2", "u_eti1", "u_eti2")}}
    if r["npix"] and semillas:
        v = [MP.vrp(mir, mask, cfg, jitter=1e-6, semilla=s)["VRP_MW"] for s in range(semillas)]
        out["vrp_banda"] = [float(min(v)), float(max(v))]
    return out


def correr_brazos(mir, tir, g, X0, Y0, xc, yc, inner_km, volcan, dayflag, sunglint, semillas=0, brazos=BRAZOS):
    """Todos los brazos sobre una grilla de VIIRS 375. Las BOX repetidas (SENS_PT fuera de PCC y Tupungatito es M14) se
    corren una sola vez y se copian."""
    cfg = MP.SENSORES["VIIRS375"]
    out, hechas = {}, {}
    for b in brazos:
        box = caja(g, b, X0, Y0, xc, yc, inner_km, volcan)
        clave = box.tobytes()
        if clave not in hechas:
            hechas[clave] = correr_box(mir, tir, g, box, X0, Y0, dayflag, sunglint, cfg, semillas=semillas, modo=b)
        r = dict(hechas[clave])
        r["modo"] = b
        r["n_roi2"] = int((box == 2).sum())
        out[b] = r
    return out
