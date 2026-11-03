"""Segundo oráculo de MIROVA VIIRS 750 (segunda ronda S158), escrito sin ver experiments/_s158_oraculo_mirova/.

Port literal de experiments/_s158_d17_diseno/osf_codigo_mirova/MIROVA_VIIRS750_hotspot_detection.m y
MIROVA_VIIRS750_VRP.m. Cada bloque cita la línea del .m que traduce.

Dos cosas que el .m no fija y que este port declara en vez de esconder:
1. colfilt(...,'sliding') rellena con ceros fuera de la matriz. Se replica, aunque no llega a ningún píxel que
   pueda alertar: el marco exterior queda en NaN (l. 102-103) y el NaN se omite en la media.
2. fillmissing2(...,'linear') no documenta su triangulación ni su extrapolación (página de MathWorks consultada el
   2026-10-21: sólo dice «Linear interpolation of nonmissing entries»). Este port usa interpolación lineal sobre una
   triangulación de Delaunay (scipy.interpolate.griddata) y, fuera de la envolvente convexa, el vecino más cercano.
   En una grilla regular la triangulación de Delaunay no es única (cuatro puntos cocirculares por celda), así que el
   fondo bajo un píxel puede depender de qué diagonal elige cada implementación: `vrp(..., jitter=...)` permite
   medir esa sensibilidad perturbando las coordenadas.

Índices: el .m devuelve índices lineales de MATLAB (orden por columnas, base 1). `detectar` devuelve una máscara
booleana y, además, la lista en el orden de concatenación del .m (l. 241-248) como índices lineales base 1 por
columnas, para poder compararla con otro port.
"""
from __future__ import annotations

import numpy as np
from scipy.interpolate import griddata
from scipy.ndimage import binary_dilation

# Constantes de Planck del código operacional (.m l. 410-412 y 430-432), no las CODATA.
_H = 6.6256e-34
_C = 2.9979e8
_K = 1.38e-23
LAMBDA_M13 = 4.05     # .m l. 144
LAMBDA_M15 = 10.763   # .m l. 145


def radiancia_a_temperatura(L, lam_um):
    """.m l. 403-421."""
    c2 = (_H * _C) / _K
    num = 2 * _H * (_C ** 2)
    lam = lam_um * 1e-6
    with np.errstate(divide="ignore", invalid="ignore"):
        return c2 / lam / np.log(num / (lam ** 5 * (L * 1e6)) + 1)


def temperatura_a_radiancia(T, lam_um):
    """.m l. 424-444 (con 3,14 en vez de pi, como el original)."""
    c1 = 2 * 3.14 * _H * (_C ** 2)
    c2 = (_H * _C) / _K
    lam = lam_um * 1e-6
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        M = c1 / (lam ** 5 * (np.exp(c2 / (lam * T)) - 1)) * 1e-6
    return M / 3.14


def _media_3x3_omitnan(A):
    """colfilt(A,[3 3],'sliding',@(v) mean(v,1,'omitnan')): relleno con ceros fuera de la matriz."""
    P = np.pad(A, 1, mode="constant", constant_values=0.0)
    n, m = A.shape
    pila = np.stack([P[i:i + n, j:j + m] for i in range(3) for j in range(3)])
    with np.errstate(invalid="ignore"):
        cuenta = np.sum(~np.isnan(pila), axis=0)
        suma = np.nansum(pila, axis=0)
        out = suma / cuenta
    out[cuenta == 0] = np.nan
    return out


def _std_omitnan(x):
    v = x[~np.isnan(x)]
    if v.size < 2:
        return np.nan if v.size == 0 else 0.0
    return float(np.std(v, ddof=1))


def _mean_omitnan(x):
    v = x[~np.isnan(x)]
    return float(v.mean()) if v.size else np.nan


def _pasada_contextual(nti_roi, bt15, m15, excl, m0, m1, m2, excluidos, s1, s2, n1, n2, e1, e2):
    """contextualDetectionPass, .m l. 252-400. Devuelve tres máscaras (BOX0, ROI1, ROI2) y diagnósticos."""
    vacio = np.zeros(nti_roi.shape, bool)
    pob = nti_roi.copy()                       # l. 275
    pob[excluidos] = np.nan                    # l. 276-277
    fondo_loc = _media_3x3_omitnan(pob)        # l. 285-287
    fondo_loc[excl] = np.nan                   # l. 288
    c_nti = pob - fondo_loc                    # l. 293-294
    with np.errstate(invalid="ignore"):
        c_nti[c_nti < -0.1] = np.nan           # l. 298
    mu, sd = _mean_omitnan(c_nti), _std_omitnan(c_nti)   # l. 303-304
    u_nti1 = max(mu + s1 * sd, n1)             # l. 306-308 (MATLAB max ignora NaN)
    u_nti2 = max(mu + s2 * sd, n2)
    if np.isnan(mu + s1 * sd):
        u_nti1 = n1
    if np.isnan(mu + s2 * sd):
        u_nti2 = n2

    m13_esp = temperatura_a_radiancia(bt15, LAMBDA_M13)            # l. 319-320
    with np.errstate(invalid="ignore", divide="ignore"):
        nti_esp = (m13_esp - m15) / (m13_esp + m15)                 # l. 324-326
    nti_esp[excluidos] = np.nan                                     # l. 328-329
    nti_esp[excl] = np.nan                                          # l. 330
    ok = np.isfinite(nti_esp) & np.isfinite(pob)                    # l. 335-337
    diag = {"mu_nti": mu, "sd_nti": sd, "u_nti1": u_nti1, "u_nti2": u_nti2, "n_ajuste": int(ok.sum())}
    if ok.sum() < 3:                                                # l. 339-341
        return vacio, vacio, vacio, diag
    coef = np.polyfit(nti_esp[ok], pob[ok], 2)                      # l. 343-345
    ref = np.polyval(coef, nti_esp)                                 # l. 349-350
    eti = pob - ref                                                 # l. 357-358
    c_eti = eti - _media_3x3_omitnan(eti)                           # l. 362-368
    c_eti[excl] = np.nan                                            # l. 369
    mu_e, sd_e = _mean_omitnan(c_eti), _std_omitnan(c_eti)          # l. 373-374
    u_eti1 = max(mu_e + s1 * sd_e, e1) if np.isfinite(mu_e + s1 * sd_e) else e1   # l. 376-378
    u_eti2 = max(mu_e + s2 * sd_e, e2) if np.isfinite(mu_e + s2 * sd_e) else e2   # l. 380-382
    diag.update({"coef": coef.tolist(), "mu_eti": mu_e, "sd_eti": sd_e, "u_eti1": u_eti1, "u_eti2": u_eti2})
    with np.errstate(invalid="ignore"):
        a0 = (c_nti * m0 > u_nti1) & (c_eti * m0 > u_eti1)          # l. 389-391
        a1 = (c_nti * m1 > u_nti1) & (c_eti * m1 > u_eti1)          # l. 393-395
        a2 = (c_nti * m2 > u_nti2) & (c_eti * m2 > u_eti2)          # l. 397-399
    return a0, a1, a2, diag


def _a_lineal(mask):
    """Máscara -> índices lineales MATLAB (columnas, base 1), en orden creciente como find()."""
    return list(np.flatnonzero(mask.T.ravel()) + 1)


def detectar(m13, m15, box, dayflag, sunglint, devolver_diag=False):
    """MIROVA_VIIRS750_hotspot_detection.m. Devuelve (mascara, lista_lineal[, diag])."""
    m13 = np.asarray(m13, float)
    vacio = np.zeros(m13.shape, bool)

    def _salida(mask, lista, d):
        return (mask, lista, d) if devolver_diag else (mask, lista)

    d = {"motivo": None}
    if not np.isfinite(sunglint) or sunglint < 12:                   # l. 87-89
        d["motivo"] = "sunglint"
        return _salida(vacio, [], d)
    m15 = np.array(m15, float)
    box = np.array(box, float)
    box[:, [0, -1]] = np.nan                                         # l. 102
    box[[0, -1], :] = np.nan                                         # l. 103
    m0 = np.where(box == 0, 1.0, np.nan)                             # l. 132-138
    m1 = np.where(box == 1, 1.0, np.nan)
    m2 = np.where(box == 2, 1.0, np.nan)
    excl = np.isnan(box)                                             # l. 140

    bt15 = radiancia_a_temperatura(m15, LAMBDA_M15)                  # l. 150
    with np.errstate(invalid="ignore"):
        frio = bt15 <= 200                                           # l. 151
    bt15[frio] = np.nan                                              # l. 153
    m15[frio] = np.nan                                               # l. 154
    with np.errstate(invalid="ignore", divide="ignore"):
        nti = (m13 - m15) / (m13 + m15)                              # l. 159
    if nti.size == 0 or np.isnan(nti).sum() >= np.floor(nti.size / 2):   # l. 163-167
        d["motivo"] = "escena_invalida"
        return _salida(vacio, [], d)
    nti_roi = nti.copy()
    nti_roi[excl] = np.nan                                           # l. 170-171

    if dayflag == 0:                                                 # l. 177-199
        u_abs, s1, s2, n1, n2, e1, e2 = -0.7, 10, 5, 0.02, 0.003, 0.01, 0.003
    else:
        u_abs, s1, s2, n1, n2, e1, e2 = -0.5, 15, 15, 0.02, 0.02, 0.02, 0.02

    with np.errstate(invalid="ignore"):
        absol = nti_roi > u_abs                                      # l. 206
    p1 = _pasada_contextual(nti_roi, bt15, m15, excl, m0, m1, m2, absol, s1, s2, n1, n2, e1, e2)   # l. 211-218
    ctx1 = p1[0] | p1[1] | p1[2]
    p2 = _pasada_contextual(nti_roi, bt15, m15, excl, m0, m1, m2, absol | ctx1, s1, s2, n1, n2, e1, e2)  # l. 228-235
    # l. 241-248: orden de concatenación del original
    lista = (_a_lineal(p1[0]) + _a_lineal(p1[1]) + _a_lineal(p1[2]) + _a_lineal(absol)
             + _a_lineal(p2[0]) + _a_lineal(p2[1]) + _a_lineal(p2[2]))
    mask = ctx1 | absol | p2[0] | p2[1] | p2[2]
    d.update({"pasada1": p1[3], "pasada2": p2[3], "n_abs": int(absol.sum()), "n_p1": int(ctx1.sum()),
              "n_p2": int((p2[0] | p2[1] | p2[2]).sum())})
    return _salida(mask, lista, d)


def _fillmissing2_lineal(A, jitter=0.0, semilla=0):
    """fillmissing2(A,'linear') aproximado: Delaunay lineal, vecino más cercano fuera de la envolvente."""
    n, m = A.shape
    yy, xx = np.mgrid[0:n, 0:m].astype(float)
    if jitter:
        rng = np.random.default_rng(semilla)
        yy = yy + rng.uniform(-jitter, jitter, yy.shape)
        xx = xx + rng.uniform(-jitter, jitter, xx.shape)
    ok = ~np.isnan(A)
    pts = np.column_stack([yy[ok], xx[ok]])
    falt = ~ok
    out = A.copy()
    if falt.any():
        q = np.column_stack([yy[falt], xx[falt]])
        v = griddata(pts, A[ok], q, method="linear")
        if np.isnan(v).any():
            vn = griddata(pts, A[ok], q, method="nearest")
            v = np.where(np.isnan(v), vn, v)
        out[falt] = v
    return out


def vrp(m13, mask, jitter=0.0, semilla=0):
    """MIROVA_VIIRS750_VRP.m. Devuelve dict con VRP_MW, npix, L_hot, L_bk, deltaL y el fondo."""
    m13 = np.asarray(m13, float)
    npix = int(mask.sum())                                           # l. 61 (numel del vector de alertas)
    if npix == 0:                                                    # l. 50-52
        return {"VRP_MW": np.nan, "npix": 0, "L_hot": np.nan, "L_bk": np.nan, "deltaL": np.nan, "fondo": None}
    enm = m13.copy()
    enm[mask] = np.nan                                               # l. 64-65
    k = 3 if npix <= 4 else (5 if npix <= 30 else 7)                 # l. 68-74
    excl = binary_dilation(np.isnan(enm), structure=np.ones((k, k), bool))   # l. 76-77
    enm[excl] = np.nan                                               # l. 78
    fondo = _fillmissing2_lineal(enm, jitter=jitter, semilla=semilla)        # l. 81
    L_hot = float(np.nansum(m13[mask]))                              # l. 83
    L_bk = float(np.nansum(fondo[mask]))                             # l. 84
    dL = L_hot - L_bk                                                # l. 85
    return {"VRP_MW": dL * 1.97e7 * 0.5625 / 1e6, "npix": npix, "L_hot": L_hot, "L_bk": L_bk,   # l. 88-91
            "deltaL": dL, "fondo": fondo}


def sunglint_deg(sat_zen, sun_zen, sat_azi, sun_azi):
    """README.txt / run_example.m: ángulo de sun-glint."""
    c = (np.cos(np.radians(sat_zen)) * np.cos(np.radians(sun_zen))
         - np.sin(np.radians(sat_zen)) * np.sin(np.radians(sun_zen)) * np.cos(np.radians(sun_azi - sat_azi)))
    return float(np.degrees(np.arccos(np.clip(c, -1, 1))))
