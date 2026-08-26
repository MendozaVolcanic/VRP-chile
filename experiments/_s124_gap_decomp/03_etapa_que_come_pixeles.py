# -*- coding: utf-8 -*-
"""En las noches de 1 pixel, el first-pass habia encontrado mas?

Compara los diagnosticos por etapa contra el conteo final.
"""
import sys, os, json, statistics
from collections import defaultdict, Counter
from datetime import datetime, timezone
sys.path.insert(0, os.getcwd())
from pipeline.store import _solar_elevation, _reject_daytime
from pipeline.profile import ENABLE_DAYTIME_MODIS
from pipeline.mirova_csv_loader import load_mirova_alertas
from scripts.auto_audit_weekly import our_bucket, SENSORS, CONS, OCR
import yaml
CO={v["name"]:(v["lat"],v["lon"]) for v in yaml.safe_load(open("volcanoes.yaml",encoding="utf-8"))["volcanoes"]}
WIN=("2026-04-01","2026-08-24")
for vol in ("Lascar","Isluga","Lastarria"):
    lat0,lon0=CO[vol]
    noches=set()
    for a in load_mirova_alertas(cons_path=CONS,ocr_path=OCR,volcano=vol):
        fu=a["fecha_utc"] or ""
        if not (WIN[0]<=fu[:10]<=WIN[1]) or a["sensor_bucket"] not in SENSORS: continue
        s={"MODIS":"MODIS_TERRA","VIIRS375":"VIIRS_SNPP","VIIRS750":"VIIRS_SNPP_750"}[a["sensor_bucket"]]
        if _reject_daytime(s,_solar_elevation(lat0,lon0,datetime.fromisoformat(fu).replace(tzinfo=timezone.utc)),ENABLE_DAYTIME_MODIS): continue
        noches.add((a["sensor_bucket"],fu[:10]))
    d=json.load(open(f"data/mirova_equivalent/{vol}.json",encoding="utf-8"))
    campos=["diag_n_first_pass_pixels","diag_n_second_pass_recapture","diag_n_bt_path",
            "diag_n_nti_path","diag_n_dnti_ctx_path","diag_n_eti_path","n_test1_pixels"]
    ag=defaultdict(list); flags=Counter()
    for r in d["records"]:
        dt=r.get("datetime_utc") or ""
        if not (WIN[0]<=dt[:10]<=WIN[1]): continue
        b=our_bucket(r.get("sensor",""))
        if b is None or (b,dt[:10]) not in noches: continue
        n=len(r.get("anomaly_pixels") or [])
        if n!=1: continue           # SOLO las noches de 1 pixel
        for c in campos: ag[c].append(r.get(c) or 0)
        pc=r.get("primary_cluster") or {}
        for k in ("focal_magnitude","single_pixel_mode","focal_degraded"):
            if pc.get(k): flags[k]+=1
        ag["_n"].append(1)
    if not ag["_n"]: continue
    print(f"\n=== {vol} — noches de 1 pixel (n={len(ag['_n'])}) ===")
    for c in campos:
        v=ag[c]
        print(f"  {c:<32} mediana={statistics.median(v):>5.0f}  max={max(v):>5.0f}")
    print(f"  flags del primary_cluster: {dict(flags)}")
