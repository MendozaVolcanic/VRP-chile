# -*- coding: utf-8 -*-
"""Une, por pasada VIIRS375 en 2026-05-09..2026-05-20: nuestro record + referencia MIROVA + TIF."""
import sys, json, csv, os, math, collections, datetime as dt
sys.path.insert(0, '.')
sys.path.insert(0, r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile")
from common import TIF2OURS, records, tif_rows, is_iband, REPO
from scripts.referencia_mirova_unificada import cargar_referencia_unificada
import yaml

V0, V1 = "2026-05-09", "2026-05-20"
cfg = {v["name"]: v for v in yaml.safe_load(open(os.path.join(REPO,"volcanoes.yaml"),encoding="utf-8"))["volcanoes"]}

# 1. TIF por (volcan_nuestro, minuto)
tifs = collections.defaultdict(list)
for tr in tif_rows("VIIRS375"):
    tifs[TIF2OURS[tr["volcano"]]].append(tr)

# 2. referencia por (volcan, minuto) - solo VIIRS375
ref = collections.defaultdict(list)
for f in cargar_referencia_unificada():
    if f["sensor_bucket"] == "VIIRS375" and V0 <= f["fecha_utc"][:10] <= V1:
        ref[(f["volcano"], f["fecha_utc"][:16])].append(f)

filas = []
for tv, ov in sorted(TIF2OURS.items()):
    for r in records(ov):
        if not is_iband(r.get("sensor","")): continue
        if not (V0 <= r["datetime_utc"][:10] <= V1): continue
        key = (ov, r["datetime_utc"][:16])
        rr = ref.get(key, [])
        # TIF mas cercano en el tiempo
        best = min(tifs[ov], key=lambda t: abs((t["_t"]-r["_t"]).total_seconds())) if tifs[ov] else None
        dmin = abs((best["_t"]-r["_t"]).total_seconds())/60 if best else None
        pc = r.get("primary_cluster") or {}
        filas.append(dict(
            vol=ov, t=r["datetime_utc"], sensor=r["sensor"], zen=r.get("sensor_zenith_deg"),
            t_bg_k=r.get("t_bg_k"), src=r.get("final_hotspot_source"),
            pc_n=pc.get("n_pixels"), pc_vrp=pc.get("vrp_mw"), pc_lat=pc.get("centroid_lat"),
            pc_lon=pc.get("centroid_lon"), pc_dist=pc.get("centroid_dist_km"), pc_geo=pc.get("geo_class"),
            f5=r.get("f5_core_vrp_mw"), nti_max=r.get("nti_max"),
            inner=cfg[ov]["inner_radius_km"], vent=(cfg[ov]["vent_lat"], cfg[ov]["vent_lon"]),
            ref_tipos=[x["tipo"] for x in rr], ref_vrp=[x["vrp_mw"] for x in rr],
            ref_dist=[x["dist_km"] for x in rr], ref_src=[x["source"] for x in rr],
            tif=best["_abs"] if best else None, tif_rel=best["tif_path"] if best else None,
            tif_t=best["_t"].isoformat() if best else None, tif_tsrc=best["_tsrc"] if best else None,
            tif_dmin=None if dmin is None else round(dmin,1),
            ap=[dict(lat=p["lat"], lon=p["lon"], bt_k=p.get("bt_k"), vrp=p.get("vrp_mw"), d=p.get("dist_km"))
                for p in (r.get("anomaly_pixels") or [])],
        ))
json.dump(filas, open("master.json","w"), indent=0)
print("records VIIRS375 nuestros en ventana:", len(filas))
print("con pasada en referencia MIROVA:", sum(1 for f in filas if f["ref_tipos"]))
print("final_hotspot_source:", collections.Counter(f["src"] for f in filas))
print("tipos de referencia (aplanado):", collections.Counter(t for f in filas for t in f["ref_tipos"]))
print("delta |record - TIF| minutos:", collections.Counter(f["tif_dmin"] for f in filas).most_common(8))
