# -*- coding: utf-8 -*-
"""Replica paso a paso de pipeline.detection_context.first_pass_tests_2_and_3 y second_pass_adjacent, para exponer
los valores intermedios por pixel (dNTI, dETI, umbrales, compuerta). No reemplaza a la funcion de produccion: el probe
llama a la original y exige que esta replica de la MISMA mascara (control de instrumento, PREREGISTRO.md).

Se usan los mismos ayudantes de produccion (compute_eti_scene_quadratic, _nanmean_8neighbors_fast,
build_unsuitable_mask, roi1_summit_mask); lo unico propio es el orden de las cuentas, copiado de
detection_context.py (first_pass: l. 413-560; second_pass: l. 822-960 al 2026-10-21).
"""
import numpy as np

from pipeline.detection_context import (_nanmean_8neighbors_fast, build_unsuitable_mask,
                                        compute_eti_scene_quadratic, roi1_summit_mask)


def replicar_first_pass(nti, nti_app, bt, roi_mask, dist_km, t_bg, bt_sanity_k, *, c1_dnti_summit, c1_deti_summit,
                        c2_dnti_summit, c2_deti_summit, inner_km, roi1_mask=None, c1_dnti_scene=None,
                        c1_deti_scene=None, c2_dnti_scene=None, c2_deti_scene=None, min_bg_pixels=10,
                        test1_mask=None, unsuitable_dnti_floor=-0.1, unsuitable_deti_floor=-0.1,
                        use_prose_branch=False, apply_bt_gate=True, sd_override=None):
    """Devuelve dict con hot y todos los intermedios. sd_override=(sd_dnti, sd_deti) para el contrafactual F4."""
    mask_valid_eti = roi_mask & np.isfinite(nti) & np.isfinite(nti_app)
    eti = compute_eti_scene_quadratic(nti, nti_app, mask_valid_eti)
    mean_nti = _nanmean_8neighbors_fast(nti)
    mean_eti = _nanmean_8neighbors_fast(eti)
    dnti = nti - mean_nti
    deti = eti - mean_eti
    bg_mask = build_unsuitable_mask(roi_mask=roi_mask, dnti=dnti, deti=deti, test1_mask=test1_mask,
                                    dnti_floor=unsuitable_dnti_floor, deti_floor=unsuitable_deti_floor)
    n_bg = int(np.count_nonzero(bg_mask))
    out = {"eti": eti, "mean_nti": mean_nti, "mean_eti": mean_eti, "dnti": dnti, "deti": deti, "n_bg": n_bg,
           "bg_mask": bg_mask}
    if n_bg < min_bg_pixels:
        out["hot"] = np.zeros_like(roi_mask, dtype=bool)
        out["corto"] = True
        return out
    mu_dnti = float(np.mean(dnti[bg_mask]))
    sd_dnti = float(np.std(dnti[bg_mask]))
    mu_deti = float(np.mean(deti[bg_mask]))
    sd_deti = float(np.std(deti[bg_mask]))
    if sd_override is not None:
        sd_dnti, sd_deti = sd_override
    combinar = max if use_prose_branch else min
    is_summit = roi1_summit_mask(dist_km, inner_km, roi1_mask)
    dual = c1_dnti_scene is not None
    if dual:
        thr = {"dnti_sum": combinar(c1_dnti_summit, mu_dnti + c2_dnti_summit * sd_dnti),
               "deti_sum": combinar(c1_deti_summit, mu_deti + c2_deti_summit * sd_deti),
               "dnti_sce": combinar(c1_dnti_scene, mu_dnti + c2_dnti_scene * sd_dnti),
               "deti_sce": combinar(c1_deti_scene, mu_deti + c2_deti_scene * sd_deti)}
        stat = {"dnti_sum": mu_dnti + c2_dnti_summit * sd_dnti, "deti_sum": mu_deti + c2_deti_summit * sd_deti,
                "dnti_sce": mu_dnti + c2_dnti_scene * sd_dnti, "deti_sce": mu_deti + c2_deti_scene * sd_deti}
        c1 = {"dnti_sum": c1_dnti_summit, "deti_sum": c1_deti_summit, "dnti_sce": c1_dnti_scene,
              "deti_sce": c1_deti_scene}
        thr_dnti = np.where(is_summit, thr["dnti_sum"], thr["dnti_sce"])
        thr_deti = np.where(is_summit, thr["deti_sum"], thr["deti_sce"])
    else:
        thr = {"dnti_sum": combinar(c1_dnti_summit, mu_dnti + c2_dnti_summit * sd_dnti),
               "deti_sum": combinar(c1_deti_summit, mu_deti + c2_deti_summit * sd_deti)}
        stat = {"dnti_sum": mu_dnti + c2_dnti_summit * sd_dnti, "deti_sum": mu_deti + c2_deti_summit * sd_deti}
        c1 = {"dnti_sum": c1_dnti_summit, "deti_sum": c1_deti_summit}
        thr_dnti = np.full(nti.shape, thr["dnti_sum"])
        thr_deti = np.full(nti.shape, thr["deti_sum"])
    pass_2 = dnti > thr_dnti
    pass_3 = deti > thr_deti
    gate_bt = (bt > t_bg + bt_sanity_k) if apply_bt_gate else np.isfinite(bt)
    hot = roi_mask & np.isfinite(dnti) & np.isfinite(deti) & pass_2 & pass_3 & gate_bt
    out.update({"hot": hot, "mu_dnti": mu_dnti, "sd_dnti": sd_dnti, "mu_deti": mu_deti, "sd_deti": sd_deti,
                "thr": thr, "stat": stat, "c1": c1, "thr_dnti": thr_dnti, "thr_deti": thr_deti, "pass_2": pass_2,
                "pass_3": pass_3, "gate_bt": gate_bt, "is_summit": is_summit, "corto": False})
    return out


def replicar_second_pass(nti, eti, active_mask, *, c1_dnti, c1_deti, c2_dnti, c2_deti, is_summit=None,
                         c1_dnti_scene=None, c1_deti_scene=None, c2_dnti_scene=None, c2_deti_scene=None,
                         min_bg_pixels=10, conditioned=False, use_prose_branch=False):
    if conditioned and not bool(np.any(active_mask)):
        return {"out": active_mask.copy(), "corto": True}
    nti_for_mean = np.where(active_mask, np.nan, nti)
    eti_for_mean = np.where(active_mask, np.nan, eti)
    dnti = nti - _nanmean_8neighbors_fast(nti_for_mean)
    deti = eti - _nanmean_8neighbors_fast(eti_for_mean)
    bg_mask = (~active_mask) & np.isfinite(dnti) & np.isfinite(deti)
    if int(np.count_nonzero(bg_mask)) < min_bg_pixels:
        return {"out": active_mask.copy(), "corto": True}
    mu_dnti, sd_dnti = float(np.mean(dnti[bg_mask])), float(np.std(dnti[bg_mask]))
    mu_deti, sd_deti = float(np.mean(deti[bg_mask])), float(np.std(deti[bg_mask]))
    dual = (is_summit is not None and c1_dnti_scene is not None and c1_deti_scene is not None
            and c2_dnti_scene is not None and c2_deti_scene is not None)
    combinar = max if use_prose_branch else min
    if dual:
        thr_dnti = np.where(is_summit, combinar(c1_dnti, mu_dnti + c2_dnti * sd_dnti),
                            combinar(c1_dnti_scene, mu_dnti + c2_dnti_scene * sd_dnti))
        thr_deti = np.where(is_summit, combinar(c1_deti, mu_deti + c2_deti * sd_deti),
                            combinar(c1_deti_scene, mu_deti + c2_deti_scene * sd_deti))
    else:
        thr_dnti = np.full(nti.shape, combinar(c1_dnti, mu_dnti + c2_dnti * sd_dnti))
        thr_deti = np.full(nti.shape, combinar(c1_deti, mu_deti + c2_deti * sd_deti))
    pass_2, pass_3 = dnti > thr_dnti, deti > thr_deti
    newly = pass_2 & pass_3 & np.isfinite(dnti) & np.isfinite(deti)
    return {"out": active_mask | newly, "dnti": dnti, "deti": deti, "thr_dnti": thr_dnti, "thr_deti": thr_deti,
            "mu_dnti": mu_dnti, "sd_dnti": sd_dnti, "mu_deti": mu_deti, "sd_deti": sd_deti,
            "n_bg": int(np.count_nonzero(bg_mask)), "pass_2": pass_2, "pass_3": pass_3, "corto": False}
