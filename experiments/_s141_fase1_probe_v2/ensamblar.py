# -*- coding: utf-8 -*-
"""S141, Fase 1 (v2): junta lo capturado en una pasada con el análisis puro.

POR QUÉ UN MÓDULO APARTE. El runner parchea `pipeline.process_viirs` al importarse; importarlo desde la
suite de tests dejaría el pipeline parcheado para todos los demás tests. Esta función recibe la
`Captura` como argumento, así que el ensamblado completo (qué llamada publicó, núcleo F5 de la misma
corrida, rótulos dentro de la ruta, fondo y contraste) se prueba con escenas sintéticas sin red y sin
tocar el pipeline. Plan: docs/superpowers/plans/2026-09-15-fase1-probe-vecinos-v2.md
"""
import numpy as np

from analisis_v2 import identificar_publicado, marcado_por_pixel, n_publicado_hoy, nucleo_f5, resumir_pasada
from pipeline.f5_core import es_viirs_iband, f5_core_vrp_mw


def _ultimo(cap, tipo, clave):
    for e in reversed(cap.de_tipo(tipo)):
        if e.get(clave) is not None:
            return e[clave]
    return None


def analizar(fila, vol, x, cap):
    """Completa la fila con lo que mide el v2. No cambia `ok` (lo decide el pipeline)."""
    rec = cap.record or {}
    inner = vol.get("inner_radius_km")
    iband = es_viirs_iband(rec.get("sensor"))
    nuc = nucleo_f5(rec, inner) if (inner is not None and iband) else {"total": None, "n": None, "pixeles": []}
    f5p = f5_core_vrp_mw(rec, inner) if (inner is not None and iband) else None   # como store.py:551-554
    pc = rec.get("primary_cluster") or {}
    pub_mw = f5p if f5p is not None else pc.get("vrp_mw")                          # regla A10
    brecha = None if pub_mw is None else x["osf"]["vrp_mw"] - pub_mw
    fila["hoy"] = {"n_publicado": n_publicado_hoy(rec, nuc), "publicado_mw": pub_mw, "brecha_mw": brecha,
                   "f5_replica_mw": nuc["total"], "f5_pipeline_mw": f5p, "f5_n": nuc["n"],
                   "single_pixel_mode": pc.get("single_pixel_mode"), "pc_n": pc.get("n_pixels"),
                   "pc_vrp_mw": pc.get("vrp_mw")}
    fila["corrio"] = cap.corrio()
    fila["test1_gana"] = cap.test1_gana()
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
    bt = _ultimo(cap, "test1", "bt")
    if bt is None:
        bt = _ultimo(cap, "first_pass", "bt")
    if bt is None or pub.get("lat") is None:
        fila["resumen"] = {"grilla_ok": False, "motivo": "sin_bt_o_sin_lat"}
        return fila
    bt = np.asarray(bt, float)
    vent = fila.get("vent") or {}
    vlat = vol.get("vent_lat", vent.get("ancla_lat"))
    vlon = vol.get("vent_lon", vent.get("ancla_lon"))
    fila["resumen"] = resumir_pasada(
        bt=bt, lat=pub["lat"], lon=pub["lon"], publicado=pub,
        marcado=marcado_por_pixel(pub["ruta"], cap.eventos, bt.shape), npix_osf=x["osf"]["Npix"],
        osf_lat=x["osf"]["lat"], osf_lon=x["osf"]["lon"], vent_lat=vlat, vent_lon=vlon,
        brecha_mw=brecha, t_bg_anillo_k=rec.get("t_bg_k"), mask_contributing=_ultimo(cap, "test1", "mask_contributing"))
    return fila
