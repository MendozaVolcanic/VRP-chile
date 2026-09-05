# -*- coding: utf-8 -*-
import io,json,sys,math,statistics as st
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
import yaml
BASE=r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
V=yaml.safe_load(open(BASE+"/volcanoes.yaml",encoding="utf-8"))
vmap={v["name"]:v for v in (V["volcanoes"] if isinstance(V,dict) else V)}
def load(v):
    d=json.load(open(f"{BASE}/data/mirova_equivalent/{v}.json",encoding="utf-8"))
    return d["records"] if isinstance(d,dict) and "records" in d else d
TIER=["Villarrica","Lascar","Copahue","Llaima","NevadosDeChillan","Isluga","Lastarria",
      "Chaiten","PlanchonPeteroa","PuyehueCordonCaulle","Tupungatito"]
print("=== H2: records V375 summit cuyo cluster viene SOLO de la 2a pasada ===")
print("(proxy: diag_n_first_pass_pixels==0 y diag_n_second_pass_recapture>0)")
tot=0
for v in TIER:
    rs=[r for r in load(v) if r.get("sensor","").startswith("VIIRS")
        and not r.get("sensor","").endswith("_750") and r.get("datetime_utc","")>="2026-06-01"
        and r.get("distance_class")=="summit"]
    q=[r for r in rs if (r.get("diag_n_first_pass_pixels") or 0)==0
       and (r.get("diag_n_second_pass_recapture") or 0)>0]
    tot+=len(q)
    if q:
        colder=sum(1 for r in q if (r.get("t_max_i04_k") or 0) < (r.get("t_bg_k") or 0))
        print(f"{v:<22} n={len(q):>4}/{len(rs):<4} t_max<t_bg:{colder:>4}")
print("TOTAL:",tot)
print("\n=== distribucion de n_second_pass_recapture (todos los summit V375) ===")
allr=[]
for v in TIER:
    allr+= [r for r in load(v) if r.get("sensor","").startswith("VIIRS")
            and not r.get("sensor","").endswith("_750") and r.get("datetime_utc","")>="2026-06-01"
            and r.get("distance_class")=="summit"]
sp=[r.get("diag_n_second_pass_recapture") or 0 for r in allr]
fp=[r.get("diag_n_first_pass_pixels") or 0 for r in allr]
print("n records:",len(allr),"| con recapture>0:",sum(1 for x in sp if x>0),
      "| con first_pass==0:",sum(1 for x in fp if x==0))
