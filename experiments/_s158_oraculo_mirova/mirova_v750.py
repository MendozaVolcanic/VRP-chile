# -*- coding: utf-8 -*-
"""Port a Python, línea a línea, del código operacional de MIROVA para VIIRS 750 (S158, oráculo).

Original: MIROVA_VIIRS750_hotspot_detection.m y MIROVA_VIIRS750_VRP.m, Copyright (c) 2026 Diego Coppola, licencia MIT
(copia y LICENSE en experiments/_s158_d17_diseno/osf_codigo_mirova/). Este port conserva el aviso de copyright y la
licencia MIT del original.

POR QUÉ: hasta S158 el proyecto reconstruyó MIROVA desde los papers. El código publicado permite, por primera vez,
correr el detector de MIROVA sobre una matriz y comparar con lo nuestro sin pasar por una lectura. Este módulo no es
producción (no vive en pipeline/): es un instrumento para medir.

Equivalencias MATLAB -> numpy que deciden el resultado, y cómo se resolvieron:
- `colfilt(A, [3 3], 'sliding', @(v) mean(v, 1, 'omitnan'))`: media de la ventana de 3 x 3 CON el píxel central,
  ignorando NaN; MATLAB rellena el borde con ceros, que acá no cambia nada porque el borde del BOX queda excluido
  (sus valores se ponen en NaN antes y después). Se replica con relleno de ceros para ser literal.
- `std(x, 0, 'omitnan')`: normalización N-1 (ddof=1).
- `find(...)`: índices lineales en orden por columnas (Fortran). Se devuelven así.
- `polyfit` y `polyval` de grado 2: numpy.polyfit y numpy.polyval (mismos coeficientes, de mayor a menor grado).
- `imdilate(m, strel('square', k))`: dilatación binaria con un cuadrado de k x k (scipy.ndimage.binary_dilation).
- `fillmissing2(A, 'linear')`: interpolación lineal 2D desde los valores no faltantes. SUPUESTO DECLARADO: se replica
  con scipy.interpolate.griddata lineal sobre la triangulación de los centros no faltantes; las celdas fuera de la
  envolvente quedan NaN. No se verificó contra MATLAB qué hace fillmissing2 ahí; el control de Etna (prueba) sí cubre
  el caso del ejemplo con 0,07 % de diferencia en el fondo (orden de ejes de MATLAB, ver _fillmissing2_linear).
"""
import numpy as np
from scipy.interpolate import griddata
from scipy.ndimage import binary_dilation

WAVELENGTH_M13 = 4.05     # µm, retenido del operacional (README del original)
WAVELENGTH_M15 = 10.763   # µm
MIR_COEFFICIENT = 1.97e7
PIXEL_AREA_KM2 = 0.5625


def radiance_to_temperature(L, wavelength_um):
    """radianceToTemperature del original, con sus constantes (h 6.6256e-34, c 2.9979e8, k 1.38e-23)."""
    h, c, k = 6.6256e-34, 2.9979e8, 1.38e-23
    second = (h * c) / k
    numerator = 2 * h * (c ** 2)
    wl = wavelength_um * 1e-6
    with np.errstate(divide="ignore", invalid="ignore"):
        return second / wl / np.log(numerator / (wl ** 5 * (L * 1e6)) + 1)


def temperature_to_radiance(T, wavelength_um):
    """temperatureToRadiance del original, con su 3,14 en vez de pi."""
    h, c, k = 6.6256e-34, 2.9979e8, 1.38e-23
    first = 2 * 3.14 * h * (c ** 2)
    second = (h * c) / k
    wl = wavelength_um * 1e-6
    with np.errstate(over="ignore", invalid="ignore"):
        exitance = first / (wl ** 5 * (np.exp(second / (wl * T)) - 1)) * 1e-6
    return exitance / 3.14


def _colfilt_mean3(A):
    """colfilt sliding 3x3 con mean omitnan, relleno de ceros (comportamiento de colfilt)."""
    P = np.pad(A, 1, mode="constant", constant_values=0.0)
    n0, n1 = A.shape
    stack = np.stack([P[i:i + n0, j:j + n1] for i in range(3) for j in range(3)], axis=0)
    with np.errstate(invalid="ignore"), np.testing.suppress_warnings() as sup:
        sup.filter(RuntimeWarning)
        return np.nanmean(stack, axis=0)


def _find(mask):
    """find() de MATLAB: índices lineales en orden por columnas."""
    return np.flatnonzero(np.asarray(mask).ravel(order="F"))


def _std(x):
    x = x[np.isfinite(x)]
    return np.std(x, ddof=1) if x.size > 1 else np.nan


def _mean(x):
    x = x[np.isfinite(x)]
    return np.mean(x) if x.size else np.nan


def _contextual_pass(nti_roi, bt_m15, m15, wl_m13, excluded, mask0, mask1, mask2, absolute, previous,
                     s1, s2, n1, n2, e1, e2, devolver_diag=False):
    """contextualDetectionPass del original. Índices lineales en orden por columnas."""
    shape = nti_roi.shape
    vacio = (np.array([], dtype=int),) * 3
    pop = nti_roi.copy().ravel(order="F")
    pop[absolute] = np.nan
    if previous is not None and len(previous):
        pop[previous] = np.nan
    pop = pop.reshape(shape, order="F")

    local = _colfilt_mean3(pop)
    local[excluded] = np.nan
    sc_nti = pop - local
    sc_nti[sc_nti < -0.1] = np.nan
    mu_n, sd_n = _mean(sc_nti.ravel()), _std(sc_nti.ravel())
    thr_n1 = max(mu_n + s1 * sd_n, n1)
    thr_n2 = max(mu_n + s2 * sd_n, n2)

    m13_exp = temperature_to_radiance(bt_m15, wl_m13)
    with np.errstate(invalid="ignore", divide="ignore"):
        nti_exp = (m13_exp - m15) / (m13_exp + m15)
    nti_exp = nti_exp.ravel(order="F")
    nti_exp[absolute] = np.nan
    if previous is not None and len(previous):
        nti_exp[previous] = np.nan
    nti_exp = nti_exp.reshape(shape, order="F")
    nti_exp[excluded] = np.nan

    valid = np.isfinite(nti_exp) & np.isfinite(pop)
    if np.count_nonzero(valid) < 3:
        return vacio if not devolver_diag else (vacio, {})
    coef = np.polyfit(nti_exp[valid], pop[valid], 2)
    ref = np.polyval(coef, nti_exp)
    eti = pop - ref

    local_e = _colfilt_mean3(eti)
    sc_eti = eti - local_e
    sc_eti[excluded] = np.nan
    mu_e, sd_e = _mean(sc_eti.ravel()), _std(sc_eti.ravel())
    thr_e1 = max(mu_e + s1 * sd_e, e1)
    thr_e2 = max(mu_e + s2 * sd_e, e2)

    with np.errstate(invalid="ignore"):
        a0 = _find((sc_nti * mask0 > thr_n1) & (sc_eti * mask0 > thr_e1))
        a1 = _find((sc_nti * mask1 > thr_n1) & (sc_eti * mask1 > thr_e1))
        a2 = _find((sc_nti * mask2 > thr_n2) & (sc_eti * mask2 > thr_e2))
    if devolver_diag:
        return (a0, a1, a2), {"mu_dnti": mu_n, "sd_dnti": sd_n, "mu_deti": mu_e, "sd_deti": sd_e,
                              "thr_dnti_box0_roi1": thr_n1, "thr_dnti_roi2": thr_n2,
                              "thr_deti_box0_roi1": thr_e1, "thr_deti_roi2": thr_e2, "coef": coef.tolist()}
    return a0, a1, a2


def hotspot_detection(zi_m13, zi_m15, box, dayflag, sunglint, devolver_diag=False):
    """MIROVA_VIIRS750_hotspot_detection. Devuelve los índices lineales (orden por columnas) de las alertas,
    concatenados en el mismo orden que el original (sin unique)."""
    diag = {}
    vacio = np.array([], dtype=int)
    if not np.isfinite(sunglint) or sunglint < 12:
        return (vacio, {"rechazo": "sunglint"}) if devolver_diag else vacio
    m13 = np.asarray(zi_m13, dtype=float).copy()
    m15 = np.asarray(zi_m15, dtype=float).copy()
    B = np.asarray(box, dtype=float).copy()
    B[:, [0, -1]] = np.nan
    B[[0, -1], :] = np.nan
    mask0 = np.full(B.shape, np.nan); mask0[B == 0] = 1
    mask1 = np.full(B.shape, np.nan); mask1[B == 1] = 1
    mask2 = np.full(B.shape, np.nan); mask2[B == 2] = 1
    excluded = np.isnan(B)

    bt15 = radiance_to_temperature(m15, WAVELENGTH_M15)
    with np.errstate(invalid="ignore"):
        cold = bt15 <= 200
    bt15[cold] = np.nan
    m15[cold] = np.nan
    with np.errstate(invalid="ignore", divide="ignore"):
        nti = (m13 - m15) / (m13 + m15)
    if nti.size == 0 or np.count_nonzero(np.isnan(nti)) >= nti.size // 2:
        return (vacio, {"rechazo": "escena"}) if devolver_diag else vacio
    nti_roi = nti.copy()
    nti_roi[excluded] = np.nan

    if dayflag == 0:
        k1, s1, s2, n1, n2, e1, e2 = -0.7, 10, 5, 0.02, 0.003, 0.01, 0.003
    else:
        k1, s1, s2, n1, n2, e1, e2 = -0.5, 15, 15, 0.02, 0.02, 0.02, 0.02

    with np.errstate(invalid="ignore"):
        absolute = _find(nti_roi > k1)
    args = (nti_roi, bt15, m15, WAVELENGTH_M13, excluded, mask0, mask1, mask2)
    r1 = _contextual_pass(*args, absolute, None, s1, s2, n1, n2, e1, e2, devolver_diag=devolver_diag)
    if devolver_diag:
        r1, diag["pase1"] = r1
    pass1 = np.concatenate(r1)
    r2 = _contextual_pass(*args, absolute, pass1, s1, s2, n1, n2, e1, e2, devolver_diag=devolver_diag)
    if devolver_diag:
        r2, diag["pase2"] = r2
    alert = np.concatenate([r1[0], r1[1], r1[2], absolute, r2[0], r2[1], r2[2]]).astype(int)
    if devolver_diag:
        diag.update({"n_absolutas": int(absolute.size), "n_pase1": [int(x.size) for x in r1],
                     "n_pase2": [int(x.size) for x in r2], "k1": k1})
        return alert, diag
    return alert


def _fillmissing2_linear(A):
    """SUPUESTO: fillmissing2(A, 'linear') como griddata lineal sobre los centros no faltantes."""
    ok = np.isfinite(A)
    if ok.all():
        return A.copy()
    filas, cols = np.indices(A.shape)
    out = A.copy()
    # Coordenadas en el orden de MATLAB (x = columna, y = fila). En una grilla regular la triangulación tiene empates y
    # el orden de los ejes cambia el resultado: con (fila, columna) el fondo del control de Etna sale 0,7 % alto, con
    # (columna, fila) 0,07 %. Elegido por la convención de MATLAB, y comprobado contra UN solo caso (no es una
    # calibración general).
    out[~ok] = griddata(np.column_stack([cols[ok], filas[ok]]), A[ok],
                        np.column_stack([cols[~ok], filas[~ok]]), method="linear")
    return out


def vrp(zi_m13, alert):
    """MIROVA_VIIRS750_VRP. Devuelve (VRP_MW, npix, deltaL_MIR, ZI_M13bk, L_hot, L_bk)."""
    alert = np.asarray(alert, dtype=int).ravel()
    if alert.size == 0:
        return np.nan, 0, np.nan, None, np.nan, np.nan
    m13 = np.asarray(zi_m13, dtype=float)
    npix = alert.size
    masked = m13.copy().ravel(order="F")
    masked[alert] = np.nan
    masked = masked.reshape(m13.shape, order="F")
    k = 3 if npix <= 4 else (5 if npix <= 30 else 7)
    excl = binary_dilation(np.isnan(masked), structure=np.ones((k, k), dtype=bool))
    masked[excl] = np.nan
    bk = _fillmissing2_linear(masked)
    flat_m13, flat_bk = m13.ravel(order="F"), bk.ravel(order="F")
    l_hot = np.nansum(flat_m13[alert])
    l_bk = np.nansum(flat_bk[alert])
    delta = l_hot - l_bk
    return delta * MIR_COEFFICIENT * PIXEL_AREA_KM2 / 1e6, npix, delta, bk, l_hot, l_bk


def sunglint_angle(sat_zen, sun_zen, sat_azi, sun_azi):
    """Ángulo de sun-glint del README y de run_example.m."""
    c = (np.cos(np.radians(sat_zen)) * np.cos(np.radians(sun_zen))
         - np.sin(np.radians(sat_zen)) * np.sin(np.radians(sun_zen)) * np.cos(np.radians(sun_azi - sat_azi)))
    return float(np.degrees(np.arccos(np.clip(c, -1, 1))))
