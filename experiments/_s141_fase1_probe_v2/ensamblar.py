# -*- coding: utf-8 -*-
"""S141, Fase 1 (v2): junta lo capturado en una pasada con el análisis puro.

POR QUÉ UN MÓDULO APARTE. El runner parchea `pipeline.process_viirs` al importarse; importarlo desde la
suite de tests dejaría el pipeline parcheado para todos los demás tests. Esta función recibe la
`Captura` como argumento, así que el ensamblado completo se prueba con las funciones reales de
detección y cúmulo sobre escenas sintéticas, sin red. Plan:
docs/superpowers/plans/2026-09-15-fase1-probe-vecinos-v2.md
"""
import numpy as np

from analisis_v2 import aplicar_filtro_store, identificar_publicado, n_publicado_hoy, nucleo_f5, resumir_pasada
from pipeline.f5_core import es_viirs_iband, f5_core_vrp_mw


def analizar(fila, vol, x, cap, filtro_distancia):
    """Completa la fila con lo que mide el v2. No cambia `ok` (lo decide el pipeline).
    `filtro_distancia`: el flag ENABLE_PIXEL_LEVEL_DISTANCE_FILTER que usa run_pipeline (H5)."""
    rec = cap.record or {}
    inner = vol.get("inner_radius_km")
    iband = es_viirs_iband(rec.get("sensor"))
    rec_f5 = aplicar_filtro_store(rec, vol.get("radius_km"), filtro_distancia)     # store.py:312-313
    nuc = nucleo_f5(rec_f5, inner) if (inner is not None and iband) else {"total": None, "n": None, "pixeles": []}
    f5p = f5_core_vrp_mw(rec_f5, inner) if (inner is not None and iband) else None  # store.py:551-554
    pc = rec.get("primary_cluster") or {}
    pub_mw = f5p if f5p is not None else pc.get("vrp_mw")                          # regla A10
    brecha = None if pub_mw is None else x["osf"]["vrp_mw"] - pub_mw
    fila["filtro_distancia_aplicado"] = bool(filtro_distancia)
    fila["hoy"] = {"n_publicado": n_publicado_hoy(rec_f5, nuc), "publicado_mw": pub_mw, "brecha_mw": brecha,
                   "f5_replica_mw": nuc["total"], "f5_pipeline_mw": f5p, "f5_n": nuc["n"],
                   "single_pixel_mode": pc.get("single_pixel_mode"), "pc_n": pc.get("n_pixels"),
                   "pc_vrp_mw": pc.get("vrp_mw"),
                   "n_anomaly_pixels_descartados_por_distancia": len(rec_f5.get("discarded_anomaly_pixels") or [])}
    fila["corrio"] = cap.corrio()
    fila["test1_gana"] = cap.test1_gana()
    fila["lbg_test1"] = cap.lbg_test1()
    fila["llamadas_cluster"] = [
        {"seq": e["seq"], "ruta": e["ruta"], "n_entrada": int(np.asarray(e["entrada"]).sum()),
         "n_cumulos": len(e["clusters"]),
         "cumulo0": ({k: v for k, v in e["clusters"][0].items() if k != "pixel_indices"} if e["clusters"] else None)}
        for e in cap.de_tipo("cluster")]
    pub = identificar_publicado(cap.de_tipo("cluster"), pc)
    fila["publicado"] = {k: pub.get(k) for k in ("identificado", "ambiguo", "motivo", "ruta", "seq", "n_coincidencias")}
    if not pub.get("identificado"):
        return fila
    fila["publicado"]["indices"] = [list(ij) for ij in pub["indices"]]
    ev = cap.ultimo("test1") or cap.ultimo("first_pass")
    bt = None if ev is None else ev.get("bt")
    if bt is None or pub.get("lat") is None:
        fila["resumen"] = {"grilla_ok": False, "motivo": "sin_bt_o_sin_lat"}
        return fila
    vent = fila.get("vent") or {}
    fila["resumen"] = resumir_pasada(
        bt=np.asarray(bt, float), lat=pub["lat"], lon=pub["lon"], publicado=pub, eventos=cap.eventos,
        npix_osf=x["osf"]["Npix"], osf_lat=x["osf"]["lat"], osf_lon=x["osf"]["lon"], brecha_mw=brecha,
        t_bg_anillo_k=rec.get("t_bg_k"), vent_lat=vol.get("vent_lat", vent.get("ancla_lat")),
        vent_lon=vol.get("vent_lon", vent.get("ancla_lon")), record=rec)
    return fila
