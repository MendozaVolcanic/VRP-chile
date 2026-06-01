"""S95 — D2-safe: D2 + excepción del píxel-pico (el foco nunca se anula).

Fix de la falla de seguridad detectada (Lascar 0.62MW @0.20km borrado a 0 por D2
puro). Mitigación del design doc §3: garantizar que el píxel más cercano al vent
(el foco) y su vecindad inmediata (<=0.5km) SIEMPRE se conserven. Barre R_core y
reporta ratio por volcán + records-con-match-MIROVA que caen a 0 (debe ser 0).
"""
import sys, os, io, json, math
from statistics import median
REPO=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0,REPO); sys.path.insert(0,os.path.join(REPO,"experiments","_s94_audit"))
_fd=os.dup(1)
from f5_variants import hav, load_vents, parse, baseline
import yaml
from pipeline.mirova_csv_loader import load_mirova_alertas
OUT=io.TextIOWrapper(os.fdopen(_fd,"wb"),encoding="utf-8",write_through=True)

DATA=os.path.join(REPO,"data/_s94_reproc")
CONS=os.path.join(REPO,"latest_consolidado.csv"); OCR=os.path.join(REPO,"data/mirova_reference/registro_vrp_ocr.csv")
TIER=["PuyehueCordonCaulle","Villarrica","Lascar","Copahue","NevadosDeChillan","Llaima","Chaiten","PlanchonPeteroa","Lastarria","Isluga","Tupungatito"]
R_GRID=[0.75,1.0,1.25,1.5]
BT_EXT=295.0

def d2_safe(pixels, vent, r_core, bt_ext=BT_EXT):
    """D2 + el píxel más cercano al vent (foco) y su vecindad <=0.5km siempre quedan."""
    n=len(pixels)
    if n==0: return 0.0
    top=sorted(range(n),key=lambda i:-(pixels[i].get("vrp_mw") or 0))[:5]
    peak=min(top,key=lambda i:hav(pixels[i]["lat"],pixels[i]["lon"],*vent))
    pc=(pixels[peak]["lat"],pixels[peak]["lon"])
    keep=set()
    for i,p in enumerate(pixels):
        d=hav(p["lat"],p["lon"],*pc)
        if d<=r_core or (p.get("bt_k") or 0)>=bt_ext:
            keep.add(i)
    # excepción foco: el píxel más cercano al VENT + su vecindad inmediata <=0.5km
    vnear=min(range(n),key=lambda i:hav(pixels[i]["lat"],pixels[i]["lon"],*vent))
    keep.add(vnear); keep.add(peak)
    for j in range(n):
        if hav(pixels[j]["lat"],pixels[j]["lon"],pixels[vnear]["lat"],pixels[vnear]["lon"])<=0.5:
            keep.add(j)
    return sum(pixels[i].get("vrp_mw") or 0 for i in keep)

vents=load_vents()
per={}; 
for vol in TIER:
    p=os.path.join(DATA,f"{vol}.json")
    if not os.path.exists(p): continue
    d=json.load(open(p,encoding="utf-8")); recs=d.get("records",d) if isinstance(d,dict) else d
    cov=[parse(r.get("datetime_utc")) for r in recs if parse(r.get("datetime_utc"))]
    if not cov: continue
    cmin,cmax=min(cov),max(cov)
    mir=[]
    for a in load_mirova_alertas(CONS,OCR,volcano=vol):
        if a.get("sensor_bucket")!="VIIRS375" or (a.get("vrp_mw") or 0)<=0: continue
        t=parse(a.get("fecha_utc"))
        if t and cmin<=t<=cmax: mir.append((t,a["vrp_mw"]))
    vent=vents.get(vol)
    if not vent or vent[0] is None or not mir: continue
    rows=[]
    for r in recs:
        s=str(r.get("sensor","")).upper()
        if not (s.startswith("VIIRS") and not s.endswith("_750")): continue
        if (r.get("primary_cluster") or {}).get("vrp_mw",0)<=0: continue
        t=parse(r.get("datetime_utc"))
        if not t: continue
        near=[mv for (mt,mv) in mir if abs((t-mt).total_seconds())<=3600]
        if not near: continue
        mv=min(mir,key=lambda x:abs((t-x[0]).total_seconds()))[1]
        if mv<=0: continue
        px=[q for q in (r.get("anomaly_pixels") or []) if q.get("lat") is not None]
        rows.append((px,vent,mv))
    if rows: per[vol]=rows

OUT.write("="*92+"\n")
OUT.write(f"F5' D2-SAFE (excepción píxel-pico) barrido R_core | bt_ext={BT_EXT}\n")
OUT.write("="*92+"\n")
OUT.write(f"{'Volcán':<20}{'n':>4}{'base':>8}"+"".join(f"R={r:>5}" for r in R_GRID)+"\n")
aggr={r:[] for r in R_GRID}; zeros={r:0 for r in R_GRID}
for vol in TIER:
    if vol not in per: continue
    rows=per[vol]; n=len(rows)
    bmed=median([baseline(px,vent)/mv for (px,vent,mv) in rows])
    cells=[]
    for r in R_GRID:
        ratios=[]
        for (px,vent,mv) in rows:
            mag=d2_safe(px,vent,r)
            ratios.append(mag/mv)
            if mag<=0: zeros[r]+=1
        med=median(ratios); aggr[r].append(med); cells.append(med)
    OUT.write(f"{vol:<20}{n:>4}{bmed:>7.2f}×"+"".join(f"{c:>6.2f}×" for c in cells)+"\n")
OUT.write("-"*92+"\n")
OUT.write(f"{'MEDIANA cross-vol':<20}{'':>4}{'':>8}"+"".join(f"{median(aggr[r]):>6.2f}×" for r in R_GRID)+"\n")
OUT.write(f"{'records MIR a 0':<20}{'':>4}{'':>8}"+"".join(f"{zeros[r]:>7}" for r in R_GRID)+"\n")
