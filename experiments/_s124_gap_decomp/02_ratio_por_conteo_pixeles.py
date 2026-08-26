# -*- coding: utf-8 -*-
"""El deficit viene de pixeles FALTANTES o de radiancia por pixel baja?

Discriminante: si faltan pixeles marginales, el ratio debe MEJORAR cuando
detectamos mas pixeles. Si es la radiancia por pixel, el ratio debe ser
~constante contra el conteo.
"""
import sys, os, json, statistics
from collections import defaultdict
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
    mir=defaultdict(float)
    for a in load_mirova_alertas(cons_path=CONS,ocr_path=OCR,volcano=vol):
        fu=a["fecha_utc"] or ""
        if not (WIN[0]<=fu[:10]<=WIN[1]) or a["sensor_bucket"] not in SENSORS: continue
        s={"MODIS":"MODIS_TERRA","VIIRS375":"VIIRS_SNPP","VIIRS750":"VIIRS_SNPP_750"}[a["sensor_bucket"]]
        if _reject_daytime(s,_solar_elevation(lat0,lon0,datetime.fromisoformat(fu).replace(tzinfo=timezone.utc)),ENABLE_DAYTIME_MODIS): continue
        k=(a["sensor_bucket"],fu[:10]); mir[k]=max(mir[k],a["vrp_mw"] or 0)
    d=json.load(open(f"data/mirova_equivalent/{vol}.json",encoding="utf-8"))
    acc=defaultdict(lambda:{"C":0.0,"px":0})
    for r in d["records"]:
        dt=r.get("datetime_utc") or ""
        if not (WIN[0]<=dt[:10]<=WIN[1]): continue
        b=our_bucket(r.get("sensor",""))
        if b is None or (b,dt[:10]) not in mir: continue
        px=[p for p in (r.get("anomaly_pixels") or []) if p.get("lat") is not None]
        if px:
            s_=sum(p.get("vrp_mw") or 0 for p in px)
            if s_>acc[(b,dt[:10])]["C"]:
                acc[(b,dt[:10])]={"C":s_,"px":len(px)}
    bins=defaultdict(list)
    for k,a in acc.items():
        if a["C"]>0 and mir[k]>0:
            n=a["px"]
            b_= "1 px" if n==1 else "2 px" if n==2 else "3-5 px" if n<=5 else "6+ px"
            bins[b_].append(a["C"]/mir[k])
    print(f"\n=== {vol} — ratio escena/MIROVA segun cuantos pixeles detectamos ===")
    for b_ in ("1 px","2 px","3-5 px","6+ px"):
        if bins[b_]:
            print(f"  {b_:<8} n={len(bins[b_]):>4}  ratio mediano={statistics.median(bins[b_]):.2f}")
