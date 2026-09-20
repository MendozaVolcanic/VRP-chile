# -*- coding: utf-8 -*-
"""V1 (verificador G, item 1) - nulo del Test 1 integrado, escrito sin mirar el script del auditor.

(1) Si lo que mide estuviera roto, ¿fallaria?
    Si el Test 1 NO disparara con ruido puro, el conteo de disparos del brazo "sin senal"
    daria 0 y la afirmacion G-27 quedaria refutada por esta misma salida. El script no
    puede dar 100 % por construccion: llama a la funcion REAL `compute_test1_mir` de
    `pipeline/test1_integrated.py` (importada, no copiada) con los parametros REALES
    leidos de `pipeline.profile`, y cuenta lo que ella devuelve en `triggered`.

(2) Si el instrumento estuviera muerto, ¿se veria distinto?
    Si. El brazo CONTROL-CON-SENAL mete un foco caliente conocido (un pixel a +60 K) que
    el Test 1 DEBE detectar: si ese brazo diera 0 % de disparos, el instrumento estaria
    muerto y ninguna otra cifra de este script valdria. Ademas el brazo
    CONTROL-SIN-DISPERSION (ruido de amplitud 0) debe dar 0 % por el camino
    `zero_sigma_bg`: una salida que diera 100 % ahi delataria que el conteo esta pegado.

Semilla fija = 20146. Todo es en memoria, no escribe cache.
"""
import io
import json
import math
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

import numpy as np

from pipeline.test1_integrated import compute_test1_mir, bt_to_radiance_um
import pipeline.profile as P

SEED = 20146
OUT = os.path.join(os.path.dirname(__file__), "v1_nulo_propio.json")

# Sensores: (nombre, lado del pixel en km, lambda MIR um)
SENSORES = [
    ("VIIRS375_I04", 0.375, 3.74),
    ("VIIRS750_M13", 0.750, 4.05),
    ("MODIS_B21", 1.000, 3.959),
]

VENT_LAT, VENT_LON = -39.420292, -71.939908  # Villarrica, crater real


def grilla(paso_km, semilado_km=6.0):
    """Grilla lat/lon regular centrada en el crater, paso = lado del pixel."""
    n = int(round(2 * semilado_km / paso_km))
    off = (np.arange(n) - (n - 1) / 2.0) * paso_km
    dlat = off / 111.195
    dlon = off / (111.195 * math.cos(math.radians(VENT_LAT)))
    lon2d, lat2d = np.meshgrid(VENT_LON + dlon, VENT_LAT + dlat)
    return lat2d, lon2d


def suavizar(campo, sigma_pix):
    """Correlacion espacial barata: promedio gaussiano separable sin scipy."""
    if sigma_pix <= 0:
        return campo
    r = int(max(1, round(3 * sigma_pix)))
    x = np.arange(-r, r + 1)
    k = np.exp(-0.5 * (x / sigma_pix) ** 2)
    k /= k.sum()
    out = np.apply_along_axis(lambda m: np.convolve(m, k, mode="same"), 0, campo)
    out = np.apply_along_axis(lambda m: np.convolve(m, k, mode="same"), 1, out)
    # renormaliza para conservar la desviacion marginal
    s = out.std()
    return out / s * campo.std() if s > 0 else out


def corrida(nombre, paso_km, lam, bt_base, sigma_K, n_iter, corr_pix=0.0,
            senal_K=0.0, ruido="normal"):
    lat, lon = grilla(paso_km)
    rng = np.random.default_rng(SEED)
    disp = 0
    disp_abs = 0
    disp_rel = 0
    ks = []
    nroi = None
    for _ in range(n_iter):
        if ruido == "normal":
            z = rng.standard_normal(lat.shape)
        elif ruido == "t3":  # colas pesadas
            z = rng.standard_t(3, size=lat.shape) / math.sqrt(3.0)
        else:
            raise ValueError(ruido)
        if corr_pix > 0:
            z = suavizar(z, corr_pix)
        bt = bt_base + sigma_K * z
        if senal_K > 0:  # foco conocido en el pixel central
            c0, c1 = lat.shape[0] // 2, lat.shape[1] // 2
            bt[c0, c1] += senal_K
        r = compute_test1_mir(
            bt=bt, lat=lat, lon=lon, vent_lat=VENT_LAT, vent_lon=VENT_LON,
            lambda_um=lam, roi_km=P.TEST1_ROI_KM,
            inner_ring_km=P.TEST1_INNER_RING_KM,
            k_sigma=P.TEST1_K_SIGMA, mir_relative=P.TEST1_MIR_RELATIVE,
        )
        nroi = r["n_roi"]
        disp += int(r["triggered"])
        disp_abs += int(r["abs_criterion"])
        disp_rel += int(r["rel_criterion"])
        ks.append(r["k_sigma_observed"])
    ks = np.array(ks)
    return {
        "caso": nombre, "paso_km": paso_km, "sigma_K": sigma_K,
        "corr_pix": corr_pix, "senal_K": senal_K, "ruido": ruido,
        "n_iter": n_iter, "n_roi": nroi,
        "tasa_trigger": disp / n_iter,
        "tasa_abs": disp_abs / n_iter,
        "tasa_rel": disp_rel / n_iter,
        "k_obs_mediana": float(np.median(ks)),
        "k_obs_min": float(ks.min()), "k_obs_max": float(ks.max()),
        "k_obs_predicho_0p399_sqrtN": 0.3989422804 * math.sqrt(nroi),
    }


def main():
    res = {"semilla": SEED, "perfil": os.environ["VRP_PROFILE"],
           "parametros_efectivos": {
               "TEST1_K_SIGMA": P.TEST1_K_SIGMA, "TEST1_ROI_KM": P.TEST1_ROI_KM,
               "TEST1_INNER_RING_KM": P.TEST1_INNER_RING_KM,
               "TEST1_MIR_RELATIVE": P.TEST1_MIR_RELATIVE,
               "ENABLE_TEST1_NTI_INTEGRAL": P.ENABLE_TEST1_NTI_INTEGRAL,
               "ENABLE_TEST1_NTI_COVALIDATION": P.ENABLE_TEST1_NTI_COVALIDATION,
           },
           "corridas": []}
    N = 200
    for nom, paso, lam in SENSORES:
        # A) nulo: ruido blanco 1 K sobre fondo 270 K, SIN ninguna fuente
        res["corridas"].append(corrida(f"{nom}/nulo_blanco_1K", paso, lam, 270.0, 1.0, N))
        # B) nulo con correlacion espacial (sigma 1.5 pixeles)
        res["corridas"].append(corrida(f"{nom}/nulo_correlado_1K", paso, lam, 270.0, 1.0, N, corr_pix=1.5))
        # C) nulo con colas pesadas
        res["corridas"].append(corrida(f"{nom}/nulo_t3_1K", paso, lam, 270.0, 1.0, N, ruido="t3"))
        # D) nulo con ruido bajo (0.3 K): el piso relativo deberia frenarlo
        res["corridas"].append(corrida(f"{nom}/nulo_blanco_0p3K", paso, lam, 270.0, 0.3, N))
        # E) barrido de amplitud, para ubicar donde el piso relativo deja de frenar
        for s in (0.5, 0.7, 0.9, 1.1, 1.5, 2.0):
            res["corridas"].append(corrida(f"{nom}/barrido_{s}K", paso, lam, 270.0, s, 60))
        # CONTROL POSITIVO: foco de +60 K en un pixel, DEBE disparar
        res["corridas"].append(corrida(f"{nom}/CONTROL_con_senal_60K", paso, lam, 270.0, 1.0, 40, senal_K=60.0))
        # CONTROL NEGATIVO DURO: sin dispersion -> sigma_bg = 0 -> no puede disparar
        res["corridas"].append(corrida(f"{nom}/CONTROL_sin_dispersion", paso, lam, 270.0, 0.0, 10))
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)
    hdr = f"{'caso':38s} {'n_roi':>5s} {'trig':>6s} {'abs':>6s} {'rel':>6s} {'k_med':>7s} {'k_pred':>7s}"
    print(hdr)
    print("-" * len(hdr))
    for c in res["corridas"]:
        print(f"{c['caso']:38s} {c['n_roi']:5d} {c['tasa_trigger']:6.2f} {c['tasa_abs']:6.2f} "
              f"{c['tasa_rel']:6.2f} {c['k_obs_mediana']:7.3f} {c['k_obs_predicho_0p399_sqrtN']:7.3f}")
    print("\nJSON:", OUT)


if __name__ == "__main__":
    main()
