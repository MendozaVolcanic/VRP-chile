# -*- coding: utf-8 -*-
"""Oráculo de MIROVA VIIRS 750 con piezas intercambiables, para la ablación V750-C (S162).

Base: el segundo port de S158 R2 (experiments/_s158_audit_r2/oraculo/mirova_v750_r2.py, rama s159-pruebas), que a su
vez traduce MIROVA_VIIRS750_hotspot_detection.m y MIROVA_VIIRS750_VRP.m, Copyright (c) 2026 Diego Coppola, licencia
MIT (OSF zm62w). Se conservan el aviso y la licencia del original.

POR QUÉ. El código de MIROVA, en su grilla, calla cumbres tibias de un píxel que nuestro detector K encuentra (S159 N,
censo: 1 de 60). Para saber qué pieza las calla, cada pieza del .m se reemplaza, una a la vez, por la de K. Con todas
las piezas en su valor del .m este módulo tiene que dar exactamente lo mismo que el port de R2: es el control de
identidad de ablacion.py.

Piezas (todas apagadas = el .m):
  ocho_vecinos  media local de 8 vecinos SIN el central (K), en vez de 3 x 3 con el central (.m l. 285-287, 362-368)
  reg_p1        el segundo pase reutiliza la regresión del primero (no la recalcula, .m l. 343-345 en el pase 2)
  umbrales_k    K1 -0,8 y mínimo 0,010 fuera de la cumbre (K), en vez de -0,7 y 0,02 / 0,01 (.m l. 177-199)
  compuerta     candidato sólo si BT M13 > t_bg + 3 K, con t_bg la mediana del anillo inner..25 km (D22 de K):
                'ambos' la aplica en los dos pases y en el test absoluto; 'p1' sólo en el primer pase y en el absoluto,
                como K, cuyo segundo pase recaptura sin compuerta (S159 N-4)
  caja          'def' (7 x 7 sensible, .m), 'sens' (21 x 21 sensible), 'circ' (círculo inner_radius_km sensible)
  recorte       VRP como suma de max(L_hot_i - L_bk_i, 0) por píxel (K), en vez de la diferencia de sumas (.m l. 83-85)
  fondo         'codigo' (fillmissing2 bajo halo, .m l. 61-81), 'anillo' (mediana de L M13 del anillo, K),
                'sin_halo' (fillmissing2 sin dilatar el hueco)
"""
from __future__ import annotations

import numpy as np
from scipy.interpolate import griddata
from scipy.ndimage import binary_dilation

_H, _C, _K = 6.6256e-34, 2.9979e8, 1.38e-23
LAMBDA_M13, LAMBDA_M15 = 4.05, 10.763
N, CELDA = 67, 750.0


def rad_a_temp(L, lam_um):
    c2 = (_H * _C) / _K
    num = 2 * _H * (_C ** 2)
    lam = lam_um * 1e-6
    with np.errstate(divide="ignore", invalid="ignore"):
        return c2 / lam / np.log(num / (lam ** 5 * (L * 1e6)) + 1)


def temp_a_rad(T, lam_um):
    c1 = 2 * 3.14 * _H * (_C ** 2)
    c2 = (_H * _C) / _K
    lam = lam_um * 1e-6
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        M = c1 / (lam ** 5 * (np.exp(c2 / (lam * T)) - 1)) * 1e-6
    return M / 3.14


def _media_local(A, ocho):
    P = np.pad(A, 1, mode="constant", constant_values=0.0)
    n, m = A.shape
    idx = [(i, j) for i in range(3) for j in range(3) if not (ocho and i == 1 and j == 1)]
    pila = np.stack([P[i:i + n, j:j + m] for i, j in idx])
    with np.errstate(invalid="ignore", divide="ignore"):
        cuenta = np.sum(~np.isnan(pila), axis=0)
        out = np.nansum(pila, axis=0) / cuenta
    out[cuenta == 0] = np.nan
    return out


def _std(x):
    v = x[~np.isnan(x)]
    return np.nan if v.size == 0 else (0.0 if v.size < 2 else float(np.std(v, ddof=1)))


def _mean(x):
    v = x[~np.isnan(x)]
    return float(v.mean()) if v.size else np.nan


def _umbral(mu, s, sd, piso):
    x = mu + s * sd
    return piso if np.isnan(x) else max(x, piso)


def _pasada(nti_roi, bt15, m15, excl, m0, m1, m2, excluidos, s1, s2, n1, n2, e1, e2, P, coef_fijo=None,
            candidato=None):
    vacio = np.zeros(nti_roi.shape, bool)
    pob = nti_roi.copy()
    pob[excluidos] = np.nan
    fondo_loc = _media_local(pob, P["ocho_vecinos"])
    fondo_loc[excl] = np.nan
    c_nti = pob - fondo_loc
    with np.errstate(invalid="ignore"):
        c_nti[c_nti < -0.1] = np.nan
    mu, sd = _mean(c_nti), _std(c_nti)
    u_n1, u_n2 = _umbral(mu, s1, sd, n1), _umbral(mu, s2, sd, n2)
    m13_esp = temp_a_rad(bt15, LAMBDA_M13)
    with np.errstate(invalid="ignore", divide="ignore"):
        nti_esp = (m13_esp - m15) / (m13_esp + m15)
    nti_esp[excluidos] = np.nan
    nti_esp[excl] = np.nan
    ok = np.isfinite(nti_esp) & np.isfinite(pob)
    d = {"u_nti1": u_n1, "u_nti2": u_n2, "c_nti": c_nti}
    if ok.sum() < 3:
        return vacio, vacio, vacio, d
    coef = np.polyfit(nti_esp[ok], pob[ok], 2) if coef_fijo is None else coef_fijo
    eti = pob - np.polyval(coef, nti_esp)
    c_eti = eti - _media_local(eti, P["ocho_vecinos"])
    c_eti[excl] = np.nan
    mu_e, sd_e = _mean(c_eti), _std(c_eti)
    u_e1, u_e2 = _umbral(mu_e, s1, sd_e, e1), _umbral(mu_e, s2, sd_e, e2)
    d.update({"coef": coef, "u_eti1": u_e1, "u_eti2": u_e2, "c_eti": c_eti})
    cand = np.ones(nti_roi.shape, bool) if candidato is None else candidato
    with np.errstate(invalid="ignore"):
        a0 = (c_nti * m0 > u_n1) & (c_eti * m0 > u_e1) & cand
        a1 = (c_nti * m1 > u_n1) & (c_eti * m1 > u_e1) & cand
        a2 = (c_nti * m2 > u_n2) & (c_eti * m2 > u_e2) & cand
    return a0, a1, a2, d


def dist_km_centro():
    c = N // 2
    r, q = np.indices((N, N))
    return np.hypot(r - c, q - c) * CELDA / 1000.0


def caja(tipo, inner_km=None):
    """'def' y 'sens' como probe_granulos.caja_mirova (S158 R2, SUPUESTO declarado allí: 21 x 21 centrado)."""
    b = np.zeros((N, N))
    c = N // 2
    b[c - 10:c + 11, c - 10:c + 11] = 1
    b[c - 3:c + 4, c - 3:c + 4] = 2
    if tipo == "sens":
        b[b == 1] = 2
    elif tipo == "circ":
        b[b == 2] = 1
        b[dist_km_centro() <= inner_km] = 2
    elif tipo != "def":
        raise ValueError(tipo)
    return b


PIEZAS_MIROVA = {"ocho_vecinos": False, "reg_p1": False, "umbrales_k": False, "compuerta": None, "caja": "def",
                 "recorte": False, "fondo": "codigo"}


def detectar(m13, m15, dayflag, sunglint, P, inner_km=None, devolver_diag=False):
    m13 = np.asarray(m13, float)
    vacio = np.zeros(m13.shape, bool)
    d = {"motivo": None}
    if not np.isfinite(sunglint) or sunglint < 12:
        d["motivo"] = "sunglint"
        return (vacio, d) if devolver_diag else vacio
    m15 = np.array(m15, float)
    box = caja(P["caja"], inner_km)
    box[:, [0, -1]] = np.nan
    box[[0, -1], :] = np.nan
    m0, m1, m2 = (np.where(box == v, 1.0, np.nan) for v in (0, 1, 2))
    excl = np.isnan(box)
    bt15 = rad_a_temp(m15, LAMBDA_M15)
    with np.errstate(invalid="ignore"):
        frio = bt15 <= 200
    bt15[frio] = np.nan
    m15[frio] = np.nan
    with np.errstate(invalid="ignore", divide="ignore"):
        nti = (m13 - m15) / (m13 + m15)
    if nti.size == 0 or np.isnan(nti).sum() >= np.floor(nti.size / 2):
        d["motivo"] = "escena_invalida"
        return (vacio, d) if devolver_diag else vacio
    nti_roi = nti.copy()
    nti_roi[excl] = np.nan
    if dayflag == 0:
        u_abs, s1, s2, n1, n2, e1, e2 = -0.7, 10, 5, 0.02, 0.003, 0.01, 0.003
        if P["umbrales_k"]:
            u_abs, n1, e1 = -0.8, 0.010, 0.010
    else:
        u_abs, s1, s2, n1, n2, e1, e2 = -0.5, 15, 15, 0.02, 0.02, 0.02, 0.02
    cand = None
    if P["compuerta"]:
        bt13 = rad_a_temp(m13, LAMBDA_M13)
        dk = dist_km_centro()
        anillo = (dk > (inner_km or 0)) & (dk <= 25.0) & np.isfinite(bt13)
        t_bg = float(np.median(bt13[anillo])) if anillo.sum() >= 10 else np.nan
        with np.errstate(invalid="ignore"):
            cand = bt13 > t_bg + 3.0
        d["t_bg"] = t_bg
    with np.errstate(invalid="ignore"):
        absol = nti_roi > u_abs
    if cand is not None:
        absol = absol & cand
    a = (nti_roi, bt15, m15, excl, m0, m1, m2)
    p1 = _pasada(*a, absol, s1, s2, n1, n2, e1, e2, P, candidato=cand)
    ctx1 = p1[0] | p1[1] | p1[2]
    coef1 = p1[3].get("coef") if P["reg_p1"] else None
    p2 = _pasada(*a, absol | ctx1, s1, s2, n1, n2, e1, e2, P, coef_fijo=coef1,
                 candidato=cand if P["compuerta"] == "ambos" else None)
    mask = ctx1 | absol | p2[0] | p2[1] | p2[2]
    d.update({"pasada1": p1[3], "pasada2": p2[3], "box": box, "n_abs": int(absol.sum()), "n_p1": int(ctx1.sum()),
              "n_p2": int((p2[0] | p2[1] | p2[2]).sum()), "excluidos_p2": int((absol | ctx1).sum())})
    return (mask, d) if devolver_diag else mask


def _fillmissing2_lineal(A):
    """Igual al port de R2 sin perturbar: Delaunay lineal en (fila, columna), vecino más cercano fuera."""
    n, m = A.shape
    yy, xx = np.mgrid[0:n, 0:m].astype(float)
    ok = ~np.isnan(A)
    out = A.copy()
    falt = ~ok
    if falt.any():
        q = np.column_stack([yy[falt], xx[falt]])
        pts = np.column_stack([yy[ok], xx[ok]])
        v = griddata(pts, A[ok], q, method="linear")
        if np.isnan(v).any():
            v = np.where(np.isnan(v), griddata(pts, A[ok], q, method="nearest"), v)
        out[falt] = v
    return out


def vrp(m13, mask, P, inner_km=None):
    m13 = np.asarray(m13, float)
    npix = int(mask.sum())
    if npix == 0:
        return {"VRP_MW": np.nan, "npix": 0, "L_hot": np.nan, "L_bk": np.nan}
    if P["fondo"] == "anillo":
        dk = dist_km_centro()
        anillo = (dk > (inner_km or 0)) & (dk <= 25.0) & np.isfinite(m13) & ~mask
        fondo = np.full(m13.shape, float(np.median(m13[anillo])))
    else:
        enm = m13.copy()
        enm[mask] = np.nan
        if P["fondo"] == "codigo":
            k = 3 if npix <= 4 else (5 if npix <= 30 else 7)
            enm[binary_dilation(np.isnan(enm), structure=np.ones((k, k), bool))] = np.nan
        elif P["fondo"] != "sin_halo":
            raise ValueError(P["fondo"])
        fondo = _fillmissing2_lineal(enm)
    exceso = m13[mask] - fondo[mask]
    dL = float(np.nansum(np.maximum(exceso, 0.0))) if P["recorte"] else \
        float(np.nansum(m13[mask]) - np.nansum(fondo[mask]))
    return {"VRP_MW": dL * 1.97e7 * 0.5625 / 1e6, "npix": npix, "L_hot": float(np.nansum(m13[mask])),
            "L_bk": float(np.nansum(fondo[mask])), "fondo": fondo}
