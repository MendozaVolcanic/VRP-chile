# -*- coding: utf-8 -*-
"""RA1 (S158 ronda 2): port propio, desde cero, de los dos .m de MIROVA para VIIRS 750 (OSF zm62w).

Fuente: experiments/_s158_d17_diseno/osf_codigo_mirova/MIROVA_VIIRS750_hotspot_detection.m y
MIROVA_VIIRS750_VRP.m, leidos linea a linea en esta sesion. No se leyo ningun port anterior.

Equivalencias MATLAB -> numpy que hay que declarar:
- colfilt(X,[3 3],'sliding',@(v) mean(v,1,'omitnan')): media 3x3 que INCLUYE el pixel central, ignora NaN,
  y rellena con ceros fuera de la imagen (solo afecta al borde, que ya esta excluido por BOX=NaN).
  Se replica con ventanas 3x3 explicitas y relleno cero (zero-pad) para ser literal.
- std(x,0,'omitnan'): desviacion muestral (ddof=1).
- polyfit grado 2 y polyval: numpy.polyfit / polyval.
- imdilate(mask, strel('square',k)): dilatacion binaria con cuadrado k x k (scipy.ndimage.binary_dilation,
  structure ones(k,k)).
- fillmissing2(X,'linear'): interpolacion lineal 2-D sobre los no faltantes. Se aproxima con
  scipy.interpolate.griddata(method='linear') sobre la triangulacion de Delaunay de los puntos validos.
  Los pixeles alertados de la prueba son interiores, asi que no hay extrapolacion en juego.
- Indices lineales de MATLAB son column-major (orden Fortran). Aqui se trabaja con pares (fila, col) y se
  conserva el ORDEN de concatenacion y los DUPLICADOS, igual que el .m (sin unique).
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage
from scipy.interpolate import griddata

H = 6.6256e-34
C = 2.9979e8
K = 1.38e-23
LAMBDA_M13 = 4.05
LAMBDA_M15 = 10.763


def radiance_to_temperature(L, wl_um):
    c2 = (H * C) / K
    num = 2 * H * C ** 2
    wl = wl_um * 1e-6
    with np.errstate(invalid="ignore", divide="ignore"):
        return c2 / wl / np.log(num / (wl ** 5 * (L * 1e6)) + 1)


def temperature_to_radiance(T, wl_um):
    c1 = 2 * 3.14 * H * C ** 2
    c2 = (H * C) / K
    wl = wl_um * 1e-6
    with np.errstate(invalid="ignore", divide="ignore", over="ignore"):
        M = c1 / (wl ** 5 * (np.exp(c2 / (wl * T)) - 1)) * 1e-6
    return M / 3.14


def mean3x3_omitnan_zeropad(X):
    """colfilt sliding 3x3 con media omitnan y relleno cero fuera de la imagen (incluye el central)."""
    P = np.pad(X, 1, mode="constant", constant_values=0.0)
    out = np.full(X.shape, np.nan)
    n, m = X.shape
    for i in range(n):
        for j in range(m):
            w = P[i:i + 3, j:j + 3]
            v = w[~np.isnan(w)]
            out[i, j] = v.mean() if v.size else np.nan
    return out


def _std_sample(x):
    x = x[~np.isnan(x)]
    return float(np.std(x, ddof=1)) if x.size > 1 else np.nan


def contextual_pass(nti_roi, bt_m15, m15, excluded, mask0, mask1, mask2, abs_alerts, prev_alerts,
                    sig1, sig2, min_nti1, min_nti2, min_eti1, min_eti2):
    """Un pase contextual. abs_alerts y prev_alerts son listas de (fila, col). Devuelve 3 listas."""
    pop = nti_roi.copy()
    for (r, c) in abs_alerts:
        pop[r, c] = np.nan
    for (r, c) in prev_alerts:
        pop[r, c] = np.nan

    local_bg = mean3x3_omitnan_zeropad(pop)
    local_bg[excluded] = np.nan
    dnti = pop - local_bg
    dnti[dnti < -0.1] = np.nan

    mu = float(np.nanmean(dnti))
    sd = _std_sample(dnti)
    thr_nti1 = max(mu + sig1 * sd, min_nti1)
    thr_nti2 = max(mu + sig2 * sd, min_nti2)

    m13_exp = temperature_to_radiance(bt_m15, LAMBDA_M13)
    nti_exp = (m13_exp - m15) / (m13_exp + m15)
    for (r, c) in abs_alerts:
        nti_exp[r, c] = np.nan
    for (r, c) in prev_alerts:
        nti_exp[r, c] = np.nan
    nti_exp[excluded] = np.nan

    valid = np.isfinite(nti_exp) & np.isfinite(pop)
    if np.count_nonzero(valid) < 3:
        return [], [], [], {}
    coef = np.polyfit(nti_exp[valid], pop[valid], 2)
    ref = np.polyval(coef, nti_exp)
    eti = pop - ref

    eti_bg = mean3x3_omitnan_zeropad(eti)
    deti = eti - eti_bg
    deti[excluded] = np.nan
    mu_e = float(np.nanmean(deti))
    sd_e = _std_sample(deti)
    thr_eti1 = max(mu_e + sig1 * sd_e, min_eti1)
    thr_eti2 = max(mu_e + sig2 * sd_e, min_eti2)

    def find(mask, tn, te):
        with np.errstate(invalid="ignore"):
            sel = (dnti * mask > tn) & (deti * mask > te)
        # orden column-major como find() de MATLAB
        cols, rows = np.where(sel.T)
        return list(zip(rows.tolist(), cols.tolist()))

    diag = dict(mu_dnti=mu, sd_dnti=sd, thr_nti1=thr_nti1, thr_nti2=thr_nti2,
                mu_deti=mu_e, sd_deti=sd_e, thr_eti1=thr_eti1, thr_eti2=thr_eti2, coef=coef.tolist())
    return find(mask0, thr_nti1, thr_eti1), find(mask1, thr_nti1, thr_eti1), find(mask2, thr_nti2, thr_eti2), diag


def detectar(ZI_M13, ZI_M15, BOX, dayflag, sunglint):
    """Replica de MIROVA_VIIRS750_hotspot_detection.m. Devuelve lista de (fila, col) con duplicados y orden del .m."""
    if not np.isfinite(sunglint) or sunglint < 12:
        return [], {"rechazo": "sunglint"}
    M13 = ZI_M13.astype(float).copy()
    M15 = ZI_M15.astype(float).copy()
    B = BOX.astype(float).copy()
    B[:, [0, -1]] = np.nan
    B[[0, -1], :] = np.nan
    mask0 = np.where(B == 0, 1.0, np.nan)
    mask1 = np.where(B == 1, 1.0, np.nan)
    mask2 = np.where(B == 2, 1.0, np.nan)
    excluded = np.isnan(B)

    bt15 = radiance_to_temperature(M15, LAMBDA_M15)
    cold = bt15 <= 200
    bt15[cold] = np.nan
    M15[cold] = np.nan

    with np.errstate(invalid="ignore", divide="ignore"):
        nti = (M13 - M15) / (M13 + M15)
    max_missing = nti.size // 2
    if nti.size == 0 or np.isnan(nti).sum() >= max_missing:
        return [], {"rechazo": "demasiados NaN"}
    nti_roi = nti.copy()
    nti_roi[excluded] = np.nan

    if dayflag == 0:
        k1, s1, s2 = -0.7, 10, 5
        mn1, mn2, me1, me2 = 0.02, 0.003, 0.01, 0.003
    else:
        k1, s1, s2 = -0.5, 15, 15
        mn1, mn2, me1, me2 = 0.02, 0.02, 0.02, 0.02

    with np.errstate(invalid="ignore"):
        sel = nti_roi > k1
    cols, rows = np.where(sel.T)
    abs_alerts = list(zip(rows.tolist(), cols.tolist()))

    a0, a1, a2, d1 = contextual_pass(nti_roi, bt15, M15, excluded, mask0, mask1, mask2, abs_alerts, [],
                                     s1, s2, mn1, mn2, me1, me2)
    pass1 = a0 + a1 + a2
    b0, b1, b2, d2 = contextual_pass(nti_roi, bt15, M15, excluded, mask0, mask1, mask2, abs_alerts, pass1,
                                     s1, s2, mn1, mn2, me1, me2)
    alert = a0 + a1 + a2 + abs_alerts + b0 + b1 + b2
    diag = {"pass1": d1, "pass2": d2, "n_abs": len(abs_alerts),
            "pass1_box0": a0, "pass1_roi1": a1, "pass1_roi2": a2, "abs": abs_alerts,
            "pass2_box0": b0, "pass2_roi1": b1, "pass2_roi2": b2}
    return alert, diag


def vrp(ZI_M13, alert):
    """Replica de MIROVA_VIIRS750_VRP.m. alert: lista de (fila, col), con duplicados si los hay."""
    if len(alert) == 0:
        return np.nan, 0, np.nan, None
    M13 = ZI_M13.astype(float).copy()
    npix = len(alert)
    masked = M13.copy()
    for (r, c) in alert:
        masked[r, c] = np.nan
    ks = 3 if npix <= 4 else (5 if npix <= 30 else 7)
    excl = ndimage.binary_dilation(np.isnan(masked), structure=np.ones((ks, ks), bool))
    masked[excl] = np.nan

    n, m = M13.shape
    rr, cc = np.meshgrid(np.arange(n), np.arange(m), indexing="ij")
    ok = ~np.isnan(masked)
    bk = masked.copy()
    filled = griddata((rr[ok], cc[ok]), masked[ok], (rr[~ok], cc[~ok]), method="linear")
    bk[~ok] = filled

    L_hot = float(np.nansum([M13[r, c] for (r, c) in alert]))
    L_bk = float(np.nansum([bk[r, c] for (r, c) in alert]))
    dL = L_hot - L_bk
    return dL * 1.97e7 * 0.5625 / 1e6, npix, dL, bk


def sunglint_deg(sat_zen, sun_zen, sun_azi, sat_azi):
    cg = (np.cos(np.radians(sat_zen)) * np.cos(np.radians(sun_zen))
          - np.sin(np.radians(sat_zen)) * np.sin(np.radians(sun_zen)) * np.cos(np.radians(sun_azi - sat_azi)))
    cg = max(-1.0, min(1.0, float(cg)))
    return float(np.degrees(np.arccos(cg)))


if __name__ == "__main__":
    import scipy.io as sio
    import sys
    p = sys.argv[1] if len(sys.argv) > 1 else "experiments/_s158_d17_diseno/osf_codigo_mirova/Example/VIIRS750_example.mat"
    S = sio.loadmat(p)
    sg = sunglint_deg(S["sat_zen"].item(), S["sun_zen"].item(), S["sun_azi"].item(), S["sat_azi"].item())
    alert, diag = detectar(S["ZI_M13"], S["ZI_M15"], S["BOX"], int(S["dayflag"].item()), sg)
    v, npix, dL, bk = vrp(S["ZI_M13"], alert)
    print("acquisition:", S["acquisition_id"][0])
    print("sunglint deg: %.4f" % sg)
    print("n_abs (NTI > K1):", diag.get("n_abs"))
    for k in ("pass1_box0", "pass1_roi1", "pass1_roi2", "pass2_box0", "pass2_roi1", "pass2_roi2"):
        print(k, diag.get(k))
    print("umbrales pase 1:", {k: diag["pass1"][k] for k in diag["pass1"] if k != "coef"})
    print("umbrales pase 2:", {k: diag["pass2"][k] for k in diag["pass2"] if k != "coef"})
    print("alert (fila,col 0-based, orden del .m, con duplicados):", alert)
    print("npix = numel(alert):", npix, "| distintos:", len(set(alert)))
    M13 = S["ZI_M13"]
    print("Tot_Lmir_hot (suma M13 en alert): %.9f" % float(np.nansum([M13[r, c] for r, c in alert])))
    print("Tot_Lmir_bk  (suma fondo fillmissing2 en alert): %.9f" % float(np.nansum([bk[r, c] for r, c in alert])))
    print("deltaL_MIR: %.9f" % dL)
    print("VRP_MW: %.6f" % v)
    for (r, c) in alert:
        print("  px (%d,%d) M13=%.6f bk=%.6f dL=%.6f" % (r, c, M13[r, c], bk[r, c], M13[r, c] - bk[r, c]))
