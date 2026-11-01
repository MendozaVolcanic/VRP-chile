# -*- coding: utf-8 -*-
"""F1 (S158): nuestro detector de producción (K) corrido sobre una matriz 67 x 67 ya remuestreada.

POR QUÉ: para comparar paso a paso con el código de MIROVA hace falta correr NUESTRA cadena sobre la MISMA
entrada. Este módulo no reimplementa nada: llama a las funciones de `pipeline/` en el mismo orden y con los
mismos argumentos que `pipeline/process_viirs_mod.py::calculate_vrp` usa con el perfil `mirova_equivalent`
(flags leídos de `pipeline.profile`, no del YAML, A89). Lo único que cambia es el sustrato: la grilla regular
de 750 m en vez del barrido nativo (D17), y que la entrada es radiancia (la de MIROVA) convertida a BT con
nuestra Planck, como si el LUT de la L1B fuera la inversa monocromática.

Líneas de producción espejadas (process_viirs_mod.py): 554-558 NTI; 560-567 t_bg; 669-675 Test 1 absoluto
(sólo para el predicado D9); 856-905 primer pase; 911-965 segundo pase; 1037-1060 VRP con recorte;
1092-1130 cúmulo, tope D9 y modo de un píxel; store.py 514-520 y frontend mirovaEqVrp para lo publicado.
"""
import os
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import numpy as np
import pipeline.profile as P
from pipeline.constants import C1_PLANCK, C2_PLANCK
from pipeline.detection_context import (first_pass_tests_2_and_3, second_pass_adjacent,
                                        compute_nti_and_nti_app, compute_bg_stats, roi1_summit_mask)
from pipeline.clustering import cluster_hotspots
from pipeline.single_pixel_mode import apply_single_pixel_mode
from pipeline.path_d_cap import apply_d9_scene_cap

M13_LAMBDA, M15_LAMBDA = 4.050, 10.763
WOOSTER_COEFF = 19.7
AREA_M2 = 750.0 ** 2


def planck(T, lam):
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        return C1_PLANCK / (lam ** 5 * (np.exp(C2_PLANCK / (lam * T)) - 1))


def planck_inv(L, lam):
    with np.errstate(invalid="ignore", divide="ignore"):
        return C2_PLANCK / (lam * np.log(C1_PLANCK / (L * lam ** 5) + 1))


def grilla(n=67, cell_km=0.75, lat0=37.75, lon0=15.0):
    c = (n - 1) / 2.0
    filas, cols = np.indices((n, n))
    dy = (c - filas) * cell_km   # fila 0 arriba = norte
    dx = (cols - c) * cell_km
    dist = np.hypot(dx, dy)
    lat = lat0 + dy / 111.32
    lon = lon0 + dx / (111.32 * np.cos(np.radians(lat0)))
    return dist, lat, lon


def nuestro_k(zi_m13, zi_m15, inner_km=5.0, roi1_box_half_km=None, cell_km=0.75, apply_bt_gate=True,
              devolver_todo=False):
    """Cadena K de producción sobre la grilla. Devuelve dict con máscaras, VRP y lo publicado."""
    n = zi_m13.shape[0]
    dist, lat, lon = grilla(n, cell_km)
    bt13 = planck_inv(np.asarray(zi_m13, float), M13_LAMBDA)
    bt15 = planck_inv(np.asarray(zi_m15, float), M15_LAMBDA)
    L13 = planck(bt13, M13_LAMBDA)
    L15 = planck(bt15, M15_LAMBDA)
    ok = ~np.isnan(L13) & ~np.isnan(L15) & (L13 + L15 > 0)
    nti = np.full_like(L13, np.nan)
    nti[ok] = (L13[ok] - L15[ok]) / (L13[ok] + L15[ok])
    roi = np.ones_like(dist, dtype=bool)              # bbox radius_km=25 cubre la grilla de 25,125
    bg = (dist >= P.BG_INNER_KM) & (dist <= P.BG_OUTER_KM)
    t_bg, std_bg, n_bg = compute_bg_stats(bt=bt13, bg_mask=bg, nti=nti, nti_k1_threshold=P.NTI_K1_NIGHT,
                                          enable_test1_k1_bg_exclude=P.ENABLE_TEST1_K1_BG_EXCLUDE,
                                          min_bg_pixels=10)
    if t_bg is None:
        return {"rechazo": "t_bg"}
    nti_path = roi & ~np.isnan(nti) & ~np.isnan(bt13) & (nti > P.NTI_K1_NIGHT) & (bt13 > t_bg + P.NTI_BT_SANITY_K)
    _, nti_app = compute_nti_and_nti_app(rad_mir=L13, bt_tir=bt15, lambda_mir_um=M13_LAMBDA,
                                         lambda_tir_um=M15_LAMBDA)
    roi1_mask = None
    if roi1_box_half_km is not None:
        c = (n - 1) / 2.0
        filas, cols = np.indices((n, n))
        roi1_mask = (np.abs(filas - c) * cell_km <= roi1_box_half_km) & (np.abs(cols - c) * cell_km <= roi1_box_half_km)
    fp, diag = first_pass_tests_2_and_3(
        nti=nti, nti_app=nti_app, bt=bt13, roi_mask=roi, dist_km=dist, roi1_mask=roi1_mask, t_bg=t_bg,
        bt_sanity_k=P.NTI_BT_SANITY_K, c1_dnti_summit=P.DNTI_CONTEXTUAL_C1_SUMMIT,
        c1_deti_summit=P.DNTI_CONTEXTUAL_C1_SUMMIT, c2_dnti_summit=P.C2_DNTI_SUMMIT_NIGHT,
        c2_deti_summit=P.C2_DNTI_SUMMIT_NIGHT, inner_km=inner_km,
        c1_dnti_scene=P.DNTI_CONTEXTUAL_C1_SCENE, c1_deti_scene=P.DNTI_CONTEXTUAL_C1_SCENE,
        c2_dnti_scene=P.C2_DNTI_SCENE_NIGHT, c2_deti_scene=P.C2_DNTI_SCENE_NIGHT, test1_mask=None,
        unsuitable_dnti_floor=-0.1, unsuitable_deti_floor=-0.1,
        use_prose_branch=P.ENABLE_TESTS_23_PROSE_BRANCH, apply_bt_gate=apply_bt_gate)
    hot = fp.copy()
    sp = hot
    if P.ENABLE_SECOND_PASS_ADJACENT and diag.get("eti") is not None:
        is_summit = roi1_summit_mask(dist, inner_km, roi1_mask)
        sp = second_pass_adjacent(nti=nti, eti=diag["eti"], active_mask=hot,
                                  c1_dnti=P.DNTI_CONTEXTUAL_C1_SUMMIT, c1_deti=P.DNTI_CONTEXTUAL_C1_SUMMIT,
                                  c2_dnti=P.C2_DNTI_SUMMIT_NIGHT, c2_deti=P.C2_DNTI_SUMMIT_NIGHT,
                                  is_summit=is_summit, c1_dnti_scene=P.DNTI_CONTEXTUAL_C1_SCENE,
                                  c1_deti_scene=P.DNTI_CONTEXTUAL_C1_SCENE, c2_dnti_scene=P.C2_DNTI_SCENE_NIGHT,
                                  c2_deti_scene=P.C2_DNTI_SCENE_NIGHT,
                                  conditioned=P.ENABLE_SECOND_PASS_CONDITIONED,
                                  use_prose_branch=P.ENABLE_TESTS_23_PROSE_BRANCH)
    hot = sp
    rr, cc = np.where(hot)
    out = {"t_bg": t_bg, "n_fp": int(fp.sum()), "n_sp_new": int((sp & ~fp).sum()), "hot": hot,
           "mu_dnti": diag.get("mu_dnti"), "sd_dnti": diag.get("sd_dnti"), "mu_deti": diag.get("mu_deti"),
           "sd_deti": diag.get("sd_deti"), "n_nti_path": int(nti_path.sum())}
    if len(rr) == 0:
        out.update(vrp_record=0.0, pc=None, publicado=0.0, dl_neg_mw=0.0)
        return out
    L_hot = planck(bt13[rr, cc], M13_LAMBDA)
    L_bg = planck(np.float64(t_bg), M13_LAMBDA)
    dl_raw = L_hot - L_bg
    dl = np.maximum(dl_raw, 0.0)
    pp = AREA_M2 * WOOSTER_COEFF * dl / 1e6
    cap_active = (P.PATH_D_ONLY_CAP_MW is not None and t_bg < P.PATH_D_ONLY_CAP_TBG_MAX_K
                  and int(nti_path.sum()) == 0)
    vrp_rec = apply_d9_scene_cap(float(np.nansum(pp)), cap_active, P.PATH_D_ONLY_CAP_MW)
    v2d = np.zeros_like(dist)
    v2d[rr, cc] = pp
    cls = cluster_hotspots(hot, lat, lon, float(lat[n // 2, n // 2]), float(lon[n // 2, n // 2]),
                           vrp_per_pixel=v2d, strategy="vent_anchored", inner_radius_km=inner_km)
    c0 = cls[0]
    vrp_c = float(c0["vrp_mw"])
    if cap_active and vrp_c > P.PATH_D_ONLY_CAP_MW:
        vrp_c = P.PATH_D_ONLY_CAP_MW
    pc = {"n_pixels": c0["n_pixels"], "vrp_mw": round(vrp_c, 3), "centroid_dist_km": c0["centroid_dist_km"]}
    pc = apply_single_pixel_mode(pc, [float(v2d[i, j]) for (i, j) in c0["pixel_indices"]],
                                 enabled=P.ENABLE_SINGLE_PIXEL_SUB_MW_MODE,
                                 threshold_mw=P.SUB_MW_REGIME_THRESHOLD_MW, max_pixels=P.SINGLE_PIXEL_MAX_CLUSTER_PIXELS)
    publicado = pc["vrp_mw"] if c0["centroid_dist_km"] <= inner_km else 0.0
    out.update(vrp_record=vrp_rec, pc=pc, publicado=publicado,
               vrp_sin_recorte=float(np.nansum(AREA_M2 * WOOSTER_COEFF * dl_raw / 1e6)),
               n_clusters=len(cls))
    return out
