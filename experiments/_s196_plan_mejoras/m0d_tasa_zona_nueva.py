# -*- coding: utf-8 -*-
"""Medición previa del P0 (2) del plan S196: cuántas casillas de 1 km «nuevas» salen sin persistencia.

POR QUÉ: la alerta de zona nueva sólo sirve si su tasa es baja; sin persistencia, con N = 30 noches de línea base, se
cuentan las casillas que alertan una noche sin haber alertado en las 30 previas, y cuántas están pegadas a una ya
alertada (jitter de geolocalización, no zona nueva). Script del verificador S196, traído al repo.
Uso: python experiments/_s196_plan_mejoras/m0d_tasa_zona_nueva.py
"""
import json, math, sys, collections, yaml
from datetime import datetime, timedelta
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT=Path(__file__).resolve().parents[2]
vy={v["name"]:v for v in yaml.safe_load((ROOT/"volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}
N=30
for vol in ["Lascar","Villarrica","PuyehueCordonCaulle","Lastarria","Isluga","NevadosDeChillan"]:
    v=vy[vol]; vl=v.get("vent_lat") or v["lat"]; vo=v.get("vent_lon") or v["lon"]
    noche=collections.defaultdict(set)
    for r in json.loads((ROOT/"data/mirova_equivalent"/(vol+".json")).read_text(encoding="utf-8"))["records"]:
        if not r.get("via_codigo_mirova") or not ("2026-01-15"<=r.get("datetime_utc","")[:10]<="2026-11-22"): continue
        if (r.get("diag_codigo_mirova") or {}).get("dayflag")!=0: continue
        d=datetime.strptime(r["datetime_utc"],"%Y-%m-%d %H:%M").date()
        for p in r.get("anomaly_pixels") or []:
            if p.get("lat") is None: continue
            x=(p["lon"]-vo)*111.32*math.cos(math.radians(vl)); y=(p["lat"]-vl)*110.57
            noche[d].add((math.floor(x),math.floor(y)))
    nuevas=vecinas=0
    for d in sorted(noche):
        if d<datetime(2026,3,1).date(): continue
        prev=set().union(*[noche.get(d-timedelta(days=i),set()) for i in range(1,N+1)])
        if not prev: continue
        for c in noche[d]-prev:
            nuevas+=1
            if any((c[0]+a,c[1]+b) in prev for a in (-1,0,1) for b in (-1,0,1)): vecinas+=1
    print("%-20s casillas 'nuevas' (N=%d): %4d; de ellas pegadas (<=1 casilla) a una ya alertada: %4d"%(vol,N,nuevas,vecinas))
