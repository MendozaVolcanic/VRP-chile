# -*- coding: utf-8 -*-
"""RA1: el fondo del VRP de VIIRS 750 de PRODUCCION aplicado a la matriz de Etna del ejemplo de MIROVA.

Pregunta 1 del instrumento: si el fondo de produccion diera otra magnitud que el .m, esta medicion lo ve,
porque calcula las dos sobre los MISMOS pixeles alertados y la MISMA matriz, y compara con el VRP del OSF.
Pregunta 2: si el instrumento estuviera muerto (por ejemplo, si la funcion de produccion no se importara),
el script falla con excepcion, no devuelve un cero. Control positivo: el fondo por vecinos (D25, flag
apagado en produccion) se calcula tambien y da un tercer numero distinto.

Lo que se reproduce de produccion (pipeline/process_viirs_mod.py, flags efectivos mirova_equivalent):
- t_bg = mediana de BT M13 del anillo 5 a 25 km (compute_bg_stats, detection_context.py:1083; bg_mask en
  process_viirs_mod.py:539 con BG_INNER_KM=5, BG_OUTER_KM=25). Se importa compute_bg_stats tal cual.
- L_bg = Planck(t_bg) escalar (process_viirs_mod.py:1041), bt_to_spectral_radiance importada tal cual.
- ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750 = False (flags_efectivos_mirova_equivalent.txt): no hay fondo por vecinos.
- delta_L = max(L_hot - L_bg, 0) por pixel (process_viirs_mod.py:1056), VRP = area * 19.7 * dL / 1e6 (l. 1057),
  area = 562.500 m2 nadir fijo (ENABLE_NADIR_FIXED_PIXEL_AREA_VIIRS=True; scan_geometry.resolve_viirs_pixel_areas).
- Cumulo: suma de los pixeles del cumulo (clustering.cluster_hotspots) y luego apply_single_pixel_mode
  (single_pixel_mode.py:94): si vrp < 5 MW y n_pixels <= 3, vrp = max por pixel.

Lo que NO se puede reproducir sobre la matriz y como se aproximo:
- La matriz ya esta remuestreada a la grilla de 750 m de MIROVA (67x67, 50 km); produccion trabaja sobre el
  granulo nativo (ENABLE_UTM_REGRID=False) y mide la distancia con haversine sobre lat/lon por pixel. Aqui la
  distancia es (pixeles al centro) x 0,75 km, con el centro en la fila y columna 33 (0-based), que es el centro
  del cuadro BOX==2 (filas y columnas 30 a 36).
- Produccion parte de BT M13 (LUT del L1B). La matriz trae radiancia; se invierte Planck con las constantes del
  pipeline (C1=119104200, C2=14388, lambda 4,05) igual que process_viirs_mod.py:266, y se vuelve a radiancia con
  bt_to_spectral_radiance: la ida y vuelta es identidad numerica, asi que L_bg de produccion es la mediana de la
  radiancia del anillo (Planck es monotona).
- El coeficiente y el area son los mismos que el .m (19,7 x 562.500 = 1,97e7 x 0,5625): no hay nada que aproximar.
"""
from __future__ import annotations

import os
import sys

os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
sys.path.insert(0, os.getcwd())

import numpy as np
import scipy.io as sio

from pipeline.detection_context import compute_bg_stats  # produccion, sin efectos laterales
from pipeline.process_viirs_mod import bt_to_spectral_radiance, M13_LAMBDA, WOOSTER_COEFF, NADIR_PIXEL_AREA_M2
from pipeline.constants import C1_PLANCK, C2_PLANCK
from pipeline.profile import (BG_INNER_KM, BG_OUTER_KM, ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750,
                              ENABLE_SINGLE_PIXEL_SUB_MW_MODE, SUB_MW_REGIME_THRESHOLD_MW,
                              SINGLE_PIXEL_MAX_CLUSTER_PIXELS, VRP_BG_NEIGHBOR_MAX_HALF_PX)
from pipeline.single_pixel_mode import apply_single_pixel_mode
from pipeline.vrp_regimes import neighbor_mean_radiance_background

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from port_mirova_v750 import detectar, vrp as vrp_m, sunglint_deg  # noqa: E402

MAT = "experiments/_s158_d17_diseno/osf_codigo_mirova/Example/VIIRS750_example.mat"
OSF = dict(Npix=5, Tot_Lmir_hot=1.96534218, Tot_Lmir_bk=1.072886152, VRP_W=9889528.362)  # fila id 123853


def radiance_to_bt_pipeline(L, wl=M13_LAMBDA):
    with np.errstate(invalid="ignore", divide="ignore"):
        return C2_PLANCK / (wl * np.log(C1_PLANCK / (L * wl ** 5) + 1))


def main():
    S = sio.loadmat(MAT)
    M13 = S["ZI_M13"].astype(float)
    sg = sunglint_deg(S["sat_zen"].item(), S["sun_zen"].item(), S["sun_azi"].item(), S["sat_azi"].item())
    alert, _ = detectar(S["ZI_M13"], S["ZI_M15"], S["BOX"], int(S["dayflag"].item()), sg)
    v_m, npix, dL_m, bk_m = vrp_m(S["ZI_M13"], alert)
    print("flags: BG_INNER_KM=%s BG_OUTER_KM=%s neighbor_mean_v750=%s single_pixel=%s (<%s MW, <=%s px)" % (
        BG_INNER_KM, BG_OUTER_KM, ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750, ENABLE_SINGLE_PIXEL_SUB_MW_MODE,
        SUB_MW_REGIME_THRESHOLD_MW, SINGLE_PIXEL_MAX_CLUSTER_PIXELS))
    print("coef y area de produccion: WOOSTER_COEFF=%s NADIR_PIXEL_AREA_M2=%s -> k=%.1f ; .m: 1.97e7*0.5625=%.1f" % (
        WOOSTER_COEFF, NADIR_PIXEL_AREA_M2, WOOSTER_COEFF * NADIR_PIXEL_AREA_M2, 1.97e7 * 0.5625))
    print("pixeles alertados por el port del .m (fila,col):", alert, "| Tot_Lmir_hot port=%.9f OSF=%.9f" % (
        sum(M13[r, c] for r, c in alert), OSF["Tot_Lmir_hot"]))

    # --- fondo de produccion ---
    bt = radiance_to_bt_pipeline(M13)
    L_round = bt_to_spectral_radiance(bt, M13_LAMBDA)
    print("ida y vuelta Planck del pipeline, max |L - L'| = %.3e" % np.nanmax(np.abs(L_round - M13)))
    n = M13.shape[0]
    rr, cc = np.meshgrid(np.arange(n), np.arange(n), indexing="ij")
    centro = 33
    dist_km = 0.75 * np.sqrt((rr - centro) ** 2 + (cc - centro) ** 2)
    bg_mask = (dist_km >= BG_INNER_KM) & (dist_km <= BG_OUTER_KM)
    t_bg, std_bg, n_bg = compute_bg_stats(bt=bt, bg_mask=bg_mask, nti=None, min_bg_pixels=10)
    L_bg_prod = float(bt_to_spectral_radiance(np.float64(t_bg), M13_LAMBDA))
    print("anillo 5-25 km: n_bg=%d (de %d en el anillo, NaN=%d), t_bg=%.3f K, std_bg=%.3f K, L_bg=%.6f" % (
        n_bg, int(bg_mask.sum()), int(np.isnan(bt[bg_mask]).sum()), t_bg, std_bg, L_bg_prod))
    print("mediana directa de la radiancia del anillo = %.6f (control de la ida y vuelta)" % np.nanmedian(M13[bg_mask]))

    L_hot = np.array([M13[r, c] for r, c in alert])
    dL_prod = np.maximum(L_hot - L_bg_prod, 0.0)
    vrp_px = NADIR_PIXEL_AREA_M2 * WOOSTER_COEFF * dL_prod / 1e6
    vrp_prod_sum = float(np.nansum(vrp_px))
    pc = apply_single_pixel_mode({"vrp_mw": vrp_prod_sum, "n_pixels": len(alert)}, vrp_px.tolist(),
                                 enabled=ENABLE_SINGLE_PIXEL_SUB_MW_MODE, threshold_mw=SUB_MW_REGIME_THRESHOLD_MW,
                                 max_pixels=SINGLE_PIXEL_MAX_CLUSTER_PIXELS)
    print("\nPor pixel (fila,col): L_hot | fondo .m (fillmissing2 ~ griddata) | fondo produccion (escalar)")
    for (r, c), lh, dp in zip(alert, L_hot, dL_prod):
        print("  (%d,%d) L=%.6f  bk_m=%.6f dL_m=%+.6f | bk_prod=%.6f dL_prod=%+.6f (recortado=%s)" % (
            r, c, lh, bk_m[r, c], lh - bk_m[r, c], L_bg_prod, lh - L_bg_prod, (lh - L_bg_prod) < 0))
    print("\nSUMA fondo sobre alertados: .m port=%.9f | OSF Tot_Lmir_bk=%.9f | produccion=%.9f" % (
        sum(bk_m[r, c] for r, c in alert), OSF["Tot_Lmir_bk"], len(alert) * L_bg_prod))
    print("deltaL: .m port=%.6f | OSF=%.6f | produccion=%.6f" % (
        dL_m, OSF["Tot_Lmir_hot"] - OSF["Tot_Lmir_bk"], float(dL_prod.sum())))
    print("VRP MW: .m port=%.4f | OSF=%.4f | produccion suma=%.4f | produccion pc tras single_pixel_mode=%.4f (modo=%s)" % (
        v_m, OSF["VRP_W"] / 1e6, vrp_prod_sum, pc["vrp_mw"], pc["single_pixel_mode"]))
    print("razon produccion/OSF = %.4f ; port/OSF = %.4f" % (vrp_prod_sum / (OSF["VRP_W"] / 1e6), v_m / (OSF["VRP_W"] / 1e6)))

    # --- control positivo: fondo por vecinos (D25, apagado en produccion) ---
    amask = np.zeros_like(M13, bool)
    for r, c in alert:
        amask[r, c] = True
    rows = np.array([r for r, _ in alert]); cols = np.array([c for _, c in alert])
    l_bk_vec, _ = neighbor_mean_radiance_background(bt, amask, rows, cols, M13_LAMBDA, max_half_px=VRP_BG_NEIGHBOR_MAX_HALF_PX)
    dL_vec = np.maximum(L_hot - l_bk_vec, 0.0)
    print("\nCONTROL (flag apagado): fondo por vecinos D25 max_half_px=%d: suma bk=%.6f, VRP=%.4f MW" % (
        VRP_BG_NEIGHBOR_MAX_HALF_PX, float(np.nansum(l_bk_vec)), float((NADIR_PIXEL_AREA_M2 * WOOSTER_COEFF * dL_vec / 1e6).sum())))

    # --- sensibilidad: que pasa con el fondo de produccion si el anillo fuera mas calido/frio ---
    # (Etna en mayo: el anillo regional es MAS FRIO que el entorno inmediato del crater o no?)
    vec8 = []
    for r, c in alert:
        w = M13[max(r - 1, 0):r + 2, max(c - 1, 0):c + 2]
        m = amask[max(r - 1, 0):r + 2, max(c - 1, 0):c + 2]
        vec8.append(np.nanmean(w[~m]))
    print("media de vecinos 3x3 no alertados por pixel: %s" % np.round(vec8, 6).tolist())
    print("fondo produccion %.6f vs mediana del entorno inmediato %.6f: el anillo regional es %s que el entorno del crater" % (
        L_bg_prod, float(np.median(vec8)), "MAS FRIO" if L_bg_prod < np.median(vec8) else "MAS CALIDO"))


if __name__ == "__main__":
    main()
