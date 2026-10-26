# -*- coding: utf-8 -*-
"""El código de VIIRS 750 de MIROVA (OSF, MIT) aplicado a otro sensor cambiando SÓLO lo que el código hace depender
del sensor. Envoltorio del port validado contra Octave (experiments/_s158_audit_r2/oraculo/mirova_v750_r2.py, «ORA»),
no una copia: la detección y el fondo son las funciones de ORA, sin tocar.

Qué cambia por sensor (y nada más), con la línea del .m que lo fija:
  - longitudes de onda efectivas de la banda MIR y de la TIR (HotspotDetection.m l. 144-145, que entran a
    radianceToTemperature de la TIR y a temperatureToRadiance del modelo espectral). En ORA son las globales
    LAMBDA_M13 y LAMBDA_M15, que las dos funciones leen al llamarse; aquí se fijan y se restauran.
  - coeficiente de VRP y área nominal del píxel (VRP.m l. 88-91: 1,97e7 y 0,5625 km²). Se aplican a deltaL, que ORA
    devuelve sin escala.
  - la grilla y la caja (BOX): fuera del .m (el .m recibe ZI_M13 y BOX ya hechos). Ver `caja`.
Qué queda IGUAL, como hipótesis declarada (PREREGISTRO.md §2): los umbrales (NTI absoluto -0,7 / -0,5, 10 y 5 sigma,
mínimos 0,02 / 0,003 / 0,01), la ventana de 3 x 3 píxeles, el halo k x k del fondo (3, 5, 7 según cuántos alertados),
el piso de escena válida (mitad de NaN), el filtro de TIR fría (200 K) y el sun-glint (12°). Todos son de VIIRS 750.
"""
from __future__ import annotations

import sys
from contextlib import contextmanager
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "experiments/_s158_audit_r2/oraculo"))
import mirova_v750_r2 as ORA  # noqa: E402

# lam_mir, lam_tir: µm. coef: W por unidad de radiancia por km² (forma del .m, 1,97e7). area: km².
# VIIRS 750: los del .m. VIIRS 375 y MODIS: CLAUDE.md, «Reglas científicas» (validados S14 contra el OSF de MIROVA):
#   VIIRS 375 k = 18,0 x 140.625 m²  ->  1,80e7 x 0,140625 km²;  MODIS k = 18,9 x 1e6 m²  ->  1,89e7 x 1,0 km².
# Longitudes de onda: I4 3,74 e I5 11,45 (pipeline/process_viirs.py:80 y :1141); MODIS B22 3,959, B21 3,929 y
# B31 11,03 (pipeline/process_modis.py:75-81).
SENSORES = {
    "VIIRS750": {"lam_mir": 4.05, "lam_tir": 10.763, "coef": 1.97e7, "area": 0.5625},
    "VIIRS375": {"lam_mir": 3.74, "lam_tir": 11.45, "coef": 1.80e7, "area": 0.140625},
    "MODIS": {"lam_mir": 3.959, "lam_tir": 11.03, "coef": 1.89e7, "area": 1.0},
    "MODIS_B21": {"lam_mir": 3.929, "lam_tir": 11.03, "coef": 1.89e7, "area": 1.0},
}
HALF_ROI2_M = 3.5 * 750.0    # 7 celdas de 750 m del .m (README: BOX==2 es el 7 x 7 central), en metros: ±2.625 m
HALF_ROI1_M = 10.5 * 750.0   # 21 celdas de 750 m: ±7.875 m


@contextmanager
def longitudes(cfg):
    viejo = (ORA.LAMBDA_M13, ORA.LAMBDA_M15)
    ORA.LAMBDA_M13, ORA.LAMBDA_M15 = cfg["lam_mir"], cfg["lam_tir"]
    try:
        yield
    finally:
        ORA.LAMBDA_M13, ORA.LAMBDA_M15 = viejo


def centros(g):
    """Centros de celda (X, Y) de la grilla g = {ul_x, ul_y, n, celda}; fila 0 = norte."""
    xs = g["ul_x"] + g["celda"] * (np.arange(g["n"]) + 0.5)
    ys = g["ul_y"] - g["celda"] * (np.arange(g["n"]) + 0.5)
    return np.meshgrid(xs, ys)


def caja(g, X0, Y0, modo="fisica"):
    """BOX del .m (0 fuera, 1 ROI1 con umbrales de escena, 2 ROI2 de cumbre con umbrales sensibles de noche).
    modo="fisica": el mismo tamaño en metros que la caja de VIIRS 750 (±2.625 m y ±7.875 m alrededor del punto de
      referencia X0, Y0 de MIROVA); en VIIRS 750 da exactamente la caja de PG.caja_mirova (se comprueba en
      control_sin_red). VIIRS 375: 14 x 14 y 42 x 42 celdas; MODIS: 5 x 5 y 15 x 15.
    modo="pixel": el mismo tamaño en celdas (7 x 7 y 21 x 21) centrado en la celda más cercana a X0, Y0.
    modo="sensible": la física con todo el ROI1 con umbrales de cumbre (variante del frente N, N-3)."""
    X, Y = centros(g)
    n = g["n"]
    if modo == "pixel":
        i0 = int(np.argmin(np.abs(Y[:, 0] - Y0)))
        j0 = int(np.argmin(np.abs(X[0, :] - X0)))
        b = np.zeros((n, n))
        b[max(i0 - 10, 0):i0 + 11, max(j0 - 10, 0):j0 + 11] = 1
        b[max(i0 - 3, 0):i0 + 4, max(j0 - 3, 0):j0 + 4] = 2
        return b
    dx, dy = np.abs(X - X0), np.abs(Y - Y0)
    b = np.zeros((n, n))
    b[(dx <= HALF_ROI1_M) & (dy <= HALF_ROI1_M)] = 1
    b[(dx <= HALF_ROI2_M) & (dy <= HALF_ROI2_M)] = 2
    if modo == "sensible":
        b[b == 1] = 2
    return b


def detectar(mir, tir, box, dayflag, sunglint, cfg):
    with longitudes(cfg):
        return ORA.detectar(mir, tir, box, dayflag, sunglint, devolver_diag=True)


def vrp(mir, mask, cfg, jitter=0.0, semilla=0):
    r = ORA.vrp(mir, mask, jitter=jitter, semilla=semilla)
    if r["npix"] == 0:
        return {"VRP_MW": np.nan, "npix": 0, "deltaL": np.nan}
    return {"VRP_MW": r["deltaL"] * cfg["coef"] * cfg["area"] / 1e6, "npix": r["npix"], "deltaL": r["deltaL"],
            "L_hot": r["L_hot"], "L_bk": r["L_bk"]}


def correr(mir, tir, g, X0, Y0, dayflag, sunglint, cfg, modo="fisica", semillas=20):
    """Detección + VRP del código en la grilla g. Devuelve un dict serializable."""
    box = caja(g, X0, Y0, modo)
    mask, _lista, d = detectar(mir, tir, box, dayflag, sunglint, cfg)
    r = vrp(mir, mask, cfg)
    X, Y = centros(g)
    rr, cc = np.nonzero(mask)
    with longitudes(cfg):
        bt = ORA.radiancia_a_temperatura(np.asarray(mir, float), cfg["lam_mir"])
    out = {"modo": modo, "motivo_vacio": d.get("motivo"), "n_abs": d.get("n_abs"), "n_p1": d.get("n_p1"),
           "n_p2": d.get("n_p2"), "npix": r["npix"], "vrp_mw": None if r["npix"] == 0 else float(r["VRP_MW"]),
           "pixeles": [[int(a), int(b), int(box[a, b]),
                        round(float(np.hypot(X[a, b] - X0, Y[a, b] - Y0) / 1000.0), 3),
                        round(float(mir[a, b]), 5), round(float(bt[a, b]), 2)] for a, b in zip(rr, cc)],
           "nan_mir": int(np.isnan(mir).sum()), "nan_tir": int(np.isnan(tir).sum()),
           "umbrales_p1": {k: (d.get("pasada1") or {}).get(k) for k in ("u_nti1", "u_nti2", "u_eti1", "u_eti2")}}
    if r["npix"] and semillas:
        v = [vrp(mir, mask, cfg, jitter=1e-6, semilla=s)["VRP_MW"] for s in range(semillas)]
        out["vrp_banda"] = [float(min(v)), float(max(v))]
    return out


def control_sin_red():
    """(1) Con la configuración de VIIRS 750, el envoltorio da lo mismo que ORA sobre una escena sintética, y la caja
    física es la de PG.caja_mirova. (2) Cambiar las longitudes de onda SÍ cambia la detección o el fondo (control
    positivo: si la sustitución no actuara, el port de 375 sería el de 750 con otro coeficiente). (3) Las globales de
    ORA quedan restauradas."""
    sys.path.insert(0, str(RAIZ / "experiments/_s158_audit_r2/granulos"))
    import probe_granulos as PG
    g750 = {"ul_x": 100000.0 - 25187.5 - 187.5, "ul_y": 200000.0 + 25062.5 - 187.5, "n": 67, "celda": 750.0}
    X0, Y0 = 100000.0, 200000.0
    assert np.array_equal(caja(g750, X0, Y0, "fisica"), PG.caja_mirova()), "caja física != caja de VIIRS 750"
    rng = np.random.default_rng(7)
    T = 262 + rng.normal(0, 0.6, (67, 67))
    tir = ORA.temperatura_a_radiancia(T, ORA.LAMBDA_M15)
    mir = ORA.temperatura_a_radiancia(T - 2.5, ORA.LAMBDA_M13)
    mir[33, 33] *= 2.2
    mir[33, 34] *= 1.3
    a = correr(mir, tir, g750, X0, Y0, 0, 100.0, SENSORES["VIIRS750"], semillas=0)
    m, _l, _d = ORA.detectar(mir, tir, PG.caja_mirova(), 0, 100.0, devolver_diag=True)
    b = ORA.vrp(mir, m)
    assert a["npix"] == b["npix"] >= 1 and abs(a["vrp_mw"] - b["VRP_MW"]) < 1e-12, (a["npix"], a["vrp_mw"], b)
    c = correr(mir, tir, g750, X0, Y0, 0, 100.0, SENSORES["VIIRS375"], semillas=0)
    d = detectar(mir, tir, PG.caja_mirova(), 0, 100.0, SENSORES["VIIRS375"])[2]
    e = ORA.detectar(mir, tir, PG.caja_mirova(), 0, 100.0, devolver_diag=True)[2]
    cambia = (d["pasada1"].get("coef") != e["pasada1"].get("coef"))
    assert cambia, "cambiar las longitudes de onda no cambió el ajuste espectral: la sustitución no actúa"
    assert (ORA.LAMBDA_M13, ORA.LAMBDA_M15) == (4.05, 10.763)
    print("CONTROL SIN RED OK: V750 = ORA (npix", a["npix"], "vrp", round(a["vrp_mw"], 6),
          "); con lambdas de 375 el ajuste cambia; npix 375-lambdas", c["npix"], flush=True)


if __name__ == "__main__":
    control_sin_red()
