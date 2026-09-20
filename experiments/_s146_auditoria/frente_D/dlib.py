# -*- coding: utf-8 -*-
"""Frente D (S146): carga compacta de los 11 Tier A, read-only. Construye un cache sin anomaly_pixels
(d_cache.json, unos pocos MB) para no releer 280 MB en cada script.
Instrumento: (1) si la carga estuviera rota, n_records seria 0 y cada script lo imprime; (2) control: el total
por volcan se imprime y se compara con len(records) del JSON crudo al construir."""
import io, json, math, os, sys, csv
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, "experiments"))
VOLS = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan",
        "Llaima", "Villarrica", "Copahue", "PuyehueCordonCaulle", "Chaiten"]
INNER = {"Lastarria": 3, "PlanchonPeteroa": 3, "Copahue": 4, "Tupungatito": 7, "PuyehueCordonCaulle": 20,
         "Lascar": 5, "Isluga": 5, "NevadosDeChillan": 5, "Llaima": 5, "Villarrica": 5, "Chaiten": 5}
CACHE = os.path.join(HERE, "d_cache.json")
KEEP = ["datetime_utc", "sensor", "vrp_mw", "vrp_vent_mw", "distance_class", "triggered_test1", "discarded_reason",
        "final_hotspot_dist_km", "final_hotspot_source", "hotspot_dist_km", "solar_zenith_deg", "f5_core_vrp_mw",
        "t_bg_k", "t_max_k", "diag_nti_max", "diag_mu_dnti", "diag_sd_dnti", "diag_mu_deti", "diag_sd_deti",
        "diag_n_dnti_ctx_path", "diag_n_bt_path", "diag_n_nti_path", "diag_n_eti_path", "n_test1_pixels",
        "test1_k_observed", "diag_n_first_pass_summit", "diag_n_second_pass_recapture", "n_anomalous_pixels",
        "product_version", "diag_vrp_raw_mw", "processed_utc"]

def bucket(s):
    s = (s or "").upper()
    if "MODIS" in s: return "modis"
    if "750" in s: return "v750"
    if "VIIRS" in s: return "v375"
    return None

def build():
    out = {}
    for v in VOLS:
        rs = json.load(open(os.path.join(ROOT, "data", "mirova_equivalent", v + ".json"), encoding="utf-8"))["records"]
        L = []
        for r in rs:
            d = {k: r.get(k) for k in KEEP if r.get(k) is not None}
            pc = r.get("primary_cluster") or {}
            d["pc"] = {k: pc.get(k) for k in ("vrp_mw", "centroid_dist_km", "n_pixels", "geo_class") if pc.get(k) is not None} if r.get("primary_cluster") else None
            L.append(d)
        assert len(L) == len(rs)
        out[v] = L
    json.dump(out, open(CACHE, "w", encoding="utf-8"))
    return out

def cargar():
    if not os.path.exists(CACHE):
        return build()
    return json.load(open(CACHE, encoding="utf-8"))

def es_noche(r):
    sz = r.get("solar_zenith_deg")
    return not (sz is not None and sz < 90)

def pcv(r):
    return ((r.get("pc") or {}).get("vrp_mw")) or 0

def publicado(r, vol=None):
    """Aproximacion Python del predicado del dashboard (mirovaEqVrp + F5): magnitud que se dibuja.
    OJO: es una RECONSTRUCCION (A97 pide node). Se usa solo donde se declara, y se calibra contra la divergencia D13."""
    if r.get("distance_class") != "summit": return 0.0
    if bucket(r.get("sensor")) == "v375" and r.get("f5_core_vrp_mw") is not None:
        return r["f5_core_vrp_mw"] or 0.0
    return pcv(r)

def sin_cerca(r):
    if bucket(r.get("sensor")) == "v375" and r.get("f5_core_vrp_mw") is not None:
        return r["f5_core_vrp_mw"] or 0.0
    return pcv(r)

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    d = build()
    for v in VOLS:
        fs = [r["datetime_utc"][:10] for r in d[v]]
        print(v, len(d[v]), min(fs), max(fs))
    print("total", sum(len(x) for x in d.values()), "cache MB", round(os.path.getsize(CACHE)/1e6, 1))
