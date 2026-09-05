# -*- coding: utf-8 -*-
"""S134 F3 - El anillo de ANILLO_TIER_A.md, desglosado por final_hotspot_source, 11 Tier A.

Pregunta: los records que forman el anillo a 2,3-2,8 km, ¿vienen del camino Test 1 (source
test1_roi, pc derivado de t1_clusters) o del camino contextual (ctx_cluster, Tests 2∧3)?
Mismo corte que anillo_tier_a.py (VIIRS375, summit, magnitud publicada > 0, desde DESDE),
ancla vent_lat/lon. Se agrega: fraccion de pixeles Test 1 que sobreviven con vrp>0
(n_ap / n_test1_pixels) y cuantos records tienen n_fp=0 con n_sp>0 (recaptura sin
primer pase).
"""
import io, json, math, os, sys, statistics as st
from collections import Counter, defaultdict
import yaml
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
WT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
DATA = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/data/mirova_equivalent"
DESDE = sys.argv[1] if len(sys.argv) > 1 else "2026-06-01"
TIER = ['Lascar','Isluga','Lastarria','Llaima','Villarrica','Copahue','Chaiten',
        'NevadosDeChillan','PlanchonPeteroa','PuyehueCordonCaulle','Tupungatito']

def hav(a,b,c,d):
    p=math.pi/180
    x=math.sin((c-a)*p/2)**2+math.cos(a*p)*math.cos(c*p)*math.sin((d-b)*p/2)**2
    return 2*6371*math.asin(math.sqrt(x))
def med(x): return round(st.median(x),2) if x else None

cfg=yaml.safe_load(io.open(os.path.join(WT,"volcanoes.yaml"),encoding="utf-8"))
vols=cfg["volcanoes"] if isinstance(cfg,dict) and "volcanoes" in cfg else cfg
V={v["name"]:v for v in vols}
out={"desde":DESDE,"por_volcan":{}}
print("%-20s %-5s| %-34s | %-34s | rec n_fp=0&n_sp>0 (all summit V375)"%("volcan","inner","test1_roi: n  d_pc  d_final  ap/t1","ctx_cluster: n  d_pc  d_final  n_fp"))
for vol in TIER:
    v=V[vol]; la,lo=v["vent_lat"],v["vent_lon"]
    d=json.load(io.open(os.path.join(DATA,vol+".json"),encoding="utf-8")); recs=d["records"] if isinstance(d,dict) and "records" in d else d
    por=defaultdict(list); n_all=0; n_sp_sin_fp=0; sp_sin_fp_src=Counter()
    for r in recs:
        if not isinstance(r,dict) or str(r.get("datetime_utc") or "")[:10]<DESDE: continue
        s=str(r.get("sensor") or "")
        if not (s.startswith("VIIRS") and not s.endswith("_750")): continue
        if r.get("distance_class")!="summit": continue
        n_all+=1
        if (r.get("diag_n_first_pass_pixels") or 0)==0 and (r.get("diag_n_second_pass_recapture") or 0)>0:
            n_sp_sin_fp+=1; sp_sin_fp_src[r.get("final_hotspot_source")]+=1
        pc=r.get("primary_cluster") or {}
        m=r.get("f5_core_vrp_mw"); m=pc.get("vrp_mw") if m is None else m
        if not m or m<=0 or pc.get("centroid_lat") is None: continue
        f={"d_pc":hav(pc["centroid_lat"],pc["centroid_lon"],la,lo),
           "d_final":(hav(r["final_hotspot_lat"],r["final_hotspot_lon"],la,lo) if r.get("final_hotspot_lat") is not None else None),
           "n_ap":len(r.get("anomaly_pixels") or []),"n_t1":r.get("n_test1_pixels") or 0,
           "n_fp":r.get("diag_n_first_pass_pixels"),"pc_n":pc.get("n_pixels")}
        por[r.get("final_hotspot_source")].append(f)
    R={"inner":v["inner_radius_km"],"n_summit_v375":n_all,"n_fp0_sp_gt0":n_sp_sin_fp,"n_fp0_sp_gt0_por_source":dict(sp_sin_fp_src),"por_source":{}}
    for s,fs in por.items():
        R["por_source"][s]={"n":len(fs),"d_pc_med":med([f["d_pc"] for f in fs]),
            "d_final_med":med([f["d_final"] for f in fs if f["d_final"] is not None]),
            "frac_500m":round(sum(1 for f in fs if f["d_pc"]<=0.5)/len(fs),3),
            "ap_over_t1_med":med([f["n_ap"]/f["n_t1"] for f in fs if f["n_t1"]]),
            "n_fp_med":med([f["n_fp"] for f in fs if f["n_fp"] is not None]),
            "pc_n_med":med([f["pc_n"] for f in fs if f["pc_n"] is not None])}
    t=R["por_source"].get("test1_roi",{}); c=R["por_source"].get("ctx_cluster",{})
    print("%-20s %-5s| %3s  %5s  %5s  %5s%15s| %3s  %5s  %5s  %5s%15s| %d/%d %s"%(vol,v["inner_radius_km"],
        t.get("n","-"),t.get("d_pc_med","-"),t.get("d_final_med","-"),t.get("ap_over_t1_med","-"),"",
        c.get("n","-"),c.get("d_pc_med","-"),c.get("d_final_med","-"),c.get("n_fp_med","-"),"",n_sp_sin_fp,n_all,dict(sp_sin_fp_src)))
    otros={k:x["n"] for k,x in R["por_source"].items() if k not in ("test1_roi","ctx_cluster")}
    if otros: print("   otros sources:",otros)
    out["por_volcan"][vol]=R
json.dump(out,io.open(os.path.join(HERE,"anillo_por_source.json"),"w",encoding="utf-8"),indent=1,ensure_ascii=False)
