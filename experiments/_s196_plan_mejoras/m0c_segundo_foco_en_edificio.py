# -*- coding: utf-8 -*-
"""Medición previa del P0 del plan S196, segunda vuelta: segundo foco dentro del edificio, no fuera del radio interno.

POR QUÉ: m0b exigía que el segundo cúmulo quedara fuera del radio interno; en Cordón Caulle ese radio es de 20 km y
«fuera» cae casi en el borde de la grilla (verificador S196, debilidad 1 del §2b). Aquí: principal a 3 km o menos del
cráter y otro cúmulo a 3 km o más de él pero dentro del radio interno. Script del verificador S196, traído al repo.
Uso: python experiments/_s196_plan_mejoras/m0c_segundo_foco_en_edificio.py
"""
import importlib.util, json, sys, yaml
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location("m0b",ROOT/"experiments/_s196_plan_mejoras/m0b_cumulos_multiples.py"); M=importlib.util.module_from_spec(s); s.loader.exec_module(M)
bp=M.bp; inner=bp.inner_desde_html()
vy={v["name"]:v for v in yaml.safe_load((ROOT/"volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}
for vol in bp.VOLS:
    v=vy[vol]; vlat,vlon=v.get("vent_lat") or v["lat"], v.get("vent_lon") or v["lon"]
    k=0
    for r in json.loads((bp.DATA/("%s.json"%vol)).read_text(encoding="utf-8"))["records"]:
        if not r.get("via_codigo_mirova") or not ("2026-03-01"<=r.get("datetime_utc","")[:10]<="2026-11-22"): continue
        if (r.get("diag_codigo_mirova") or {}).get("dayflag")!=0: continue
        pix=[p for p in (r.get("anomaly_pixels") or []) if p.get("fila") is not None and p.get("lat") is not None]
        cs=M.cumulos(pix) if pix else []
        if len(cs)<2: continue
        pr=max(cs,key=lambda c:max((p.get("bt_k") or 0) for p in c)); pc=M.centroide(pr)
        if bp._hav_km(*pc,vlat,vlon)>3: continue
        if any(bp._hav_km(*M.centroide(c),*pc)>=3 and bp._hav_km(*M.centroide(c),vlat,vlon)<=inner[vol] for c in cs if c is not pr): k+=1
    print("%-20s inner %4.1f km: principal a <=3 km del cráter y otro cúmulo a >=3 km de él DENTRO del inner: %d"%(vol,inner[vol],k))
