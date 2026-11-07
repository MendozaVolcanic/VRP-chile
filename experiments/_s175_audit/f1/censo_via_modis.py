#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""F1 (auditoría S175): censo de los records MODIS de producción por detector efectivo.

Pregunta 1 del instrumento: si la vía cayera a K en silencio (records `via_codigo_mirova` "sin_grilla",
"sin_mxd03", "geo_distinta") o si un record declarara una cosa y trajera otra, ¿este censo lo vería? Sí: cuenta
cada valor de la clave, cruza con `regimen.perfil`, `product_version`, `processed_utc` y los campos que sólo
escribe la vía (`diag_codigo_mirova`, `final_hotspot_source == "codigo_mirova"`).
Pregunta 2: si el instrumento estuviera muerto, ¿se vería distinto? Un control sintético (record con
"sin_mxd03" posterior al encendido) se inyecta en modo --control y tiene que aparecer en el conteo; y el
mismo censo corrido sobre 79f410697 (datos del 2026-11-02 19:29, antes del encendido) tiene que dar 0 de la vía.

Uso: python censo_via_modis.py <carpeta con los 11 JSON de mirova_equivalent> <etiqueta commit> [--control]
Salida: JSON por stdout (se guarda al lado con > ).
"""
import json
import os
import sys
from collections import Counter, defaultdict

VOLS = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan",
        "Llaima", "Villarrica", "Copahue", "PuyehueCordonCaulle", "Chaiten"]
ENCENDIDO = "2026-11-02T20:11:43Z"   # guardia_modis_latest.json en e75a7d52d, encendido_modis_utc (se re-mide abajo)


def clasificar(r):
    """Detector efectivo según la definición de auto_audit_weekly.es_record_via_modis + lo que trae el record."""
    v = r.get("via_codigo_mirova", "<ausente>")
    if v is True:
        decl = "VIA"
    elif v == "<ausente>":
        decl = "K_sin_clave"
    else:
        decl = f"K_caida:{v}"
    # huellas de la vía en el contenido
    huellas = {
        "diag_codigo_mirova": "diag_codigo_mirova" in r,
        "fhs_codigo_mirova": r.get("final_hotspot_source") == "codigo_mirova",
        "pix_sin_vrp": bool(r.get("anomaly_pixels")) and all("vrp_mw" not in p for p in r["anomaly_pixels"]),
        "pix_con_vrp": bool(r.get("anomaly_pixels")) and any("vrp_mw" in p for p in r["anomaly_pixels"]),
        "f5_core": "f5_core_vrp_mw" in r,
        "diag_sigma_bg_k": "diag_sigma_bg_k" in r,
    }
    # contenido: ¿el record parece de la vía por su contenido?
    contenido = "VIA" if (huellas["diag_codigo_mirova"] or huellas["fhs_codigo_mirova"]) else "K"
    return decl, contenido, huellas


def main():
    carpeta, etiqueta = sys.argv[1], sys.argv[2]
    control = "--control" in sys.argv
    out = {"commit": etiqueta, "carpeta": carpeta, "control_sintetico": control}
    por_decl = Counter()
    por_decl_post = Counter()
    incoherentes = []
    caidas_post = []
    via_proc = []
    via_primera_obs = None
    n_modis = 0
    por_vol = defaultdict(Counter)
    prod_ver_en_encendido = Counter()
    perfiles = Counter()
    via_sin_pc_con_pix = 0
    via_vrp_vs_pc = Counter()
    for vol in VOLS:
        with open(os.path.join(carpeta, vol + ".json"), encoding="utf-8") as fh:
            recs = json.load(fh).get("records") or []
        if control and vol == "Lascar":
            recs = recs + [{"sensor": "MODIS_AQUA", "datetime_utc": "2026-11-06 05:00",
                            "processed_utc": "2026-11-06T06:00:00Z", "via_codigo_mirova": "sin_mxd03",
                            "regimen": {"perfil": "mirova_equivalent"}, "product_version": "nrt",
                            "primary_cluster": None, "vrp_mw": 0.0, "_sintetico": True}]
        for r in recs:
            if not str(r.get("sensor") or "").startswith("MODIS"):
                continue
            n_modis += 1
            decl, contenido, huellas = clasificar(r)
            por_decl[decl] += 1
            por_vol[vol][decl] += 1
            perfiles[(decl, (r.get("regimen") or {}).get("perfil"))] += 1
            p = r.get("processed_utc") or ""
            post = p >= ENCENDIDO
            if post:
                por_decl_post[decl] += 1
            if (decl == "VIA") != (contenido == "VIA"):
                incoherentes.append({"vol": vol, "dt": r.get("datetime_utc"), "decl": decl, "contenido": contenido,
                                     "huellas": huellas, "processed_utc": p})
            if decl.startswith("K_caida") and post:
                caidas_post.append({"vol": vol, "dt": r.get("datetime_utc"), "marca": r.get("via_codigo_mirova"),
                                    "processed_utc": p, "product_version": r.get("product_version"),
                                    "sintetico": r.get("_sintetico", False)})
            if decl == "VIA":
                via_proc.append(p)
                d = r.get("datetime_utc") or ""
                via_primera_obs = d if via_primera_obs is None or d < via_primera_obs else via_primera_obs
                if p == ENCENDIDO:
                    prod_ver_en_encendido[r.get("product_version")] += 1
                pc = r.get("primary_cluster")
                if pc is None and r.get("anomaly_pixels"):
                    via_sin_pc_con_pix += 1
                if pc:
                    via_vrp_vs_pc["pc.vrp_mw == vrp_mw" if pc.get("vrp_mw") == r.get("vrp_mw") else "distinto"] += 1
    out.update({
        "n_records_modis": n_modis,
        "por_detector_declarado": dict(por_decl),
        "por_detector_declarado_processed_desde_encendido": dict(por_decl_post),
        "encendido_usado": ENCENDIDO,
        "encendido_remedido_min_processed_via": min(via_proc) if via_proc else None,
        "primera_observacion_via": via_primera_obs,
        "product_version_de_los_records_via_con_processed_igual_al_encendido": dict(prod_ver_en_encendido),
        "declarado_vs_contenido_incoherentes": incoherentes,
        "caidas_a_k_processed_desde_encendido": caidas_post,
        "perfil_por_detector": {f"{k[0]}|{k[1]}": v for k, v in perfiles.items()},
        "por_volcan": {v: dict(c) for v, c in por_vol.items()},
        "via_sin_primary_cluster_con_pixeles": via_sin_pc_con_pix,
        "via_pc_vrp_vs_vrp": dict(via_vrp_vs_pc),
    })
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
