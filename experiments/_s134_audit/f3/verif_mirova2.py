# -*- coding: utf-8 -*-
import io,json,sys,datetime as dt
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
sys.path.insert(0,r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile")
from pipeline.mirova_csv_loader import load_mirova_alertas
BASE=r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
B=BASE+"/data/mirova_reference/mirova_v1_snapshot/"
al=load_mirova_alertas(cons_path=B+"registro_vrp_consolidado.csv",ocr_path=B+"registro_vrp_ocr.csv")
def P(s):
    s=str(s).replace("T"," ").replace("Z","").strip()[:19]
    for f in ("%Y-%m-%d %H:%M:%S","%Y-%m-%d %H:%M"):
        try: return dt.datetime.strptime(s,f)
        except ValueError: pass
    raise ValueError(s)
def load(v):
    d=json.load(open(f"{BASE}/data/mirova_equivalent/{v}.json",encoding="utf-8"))
    return d["records"] if isinstance(d,dict) and "records" in d else d
TIER=["Villarrica","Lascar","Copahue","Llaima","NevadosDeChillan","Isluga","Lastarria",
      "Chaiten","PlanchonPeteroa","PuyehueCordonCaulle","Tupungatito"]
LO,HI=dt.datetime(2026,6,1),max(P(a["fecha_utc"]) for a in al)
print("ventana:",LO.date(),"->",HI.date())
print(f"\n{'volcan':<22}{'ALERTAS375':>11}{'test1_roi n/match':>20}{'ctx n/match':>18}")
for v in TIER:
    idx=sorted(P(a["fecha_utc"]) for a in al if a["volcano"]==v
               and a.get("sensor_bucket")=="VIIRS375" and LO<=P(a["fecha_utc"])<=HI)
    rs=[r for r in load(v) if r.get("sensor","").startswith("VIIRS")
        and not r.get("sensor","").endswith("_750") and r.get("distance_class")=="summit"
        and LO<=P(r["datetime_utc"].replace("T"," ").replace("Z",""))<=HI]
    out=[]
    for src in ("test1_roi","ctx_cluster"):
        sub=[r for r in rs if r.get("final_hotspot_source")==src]
        m=sum(1 for r in sub if any(abs((P(r["datetime_utc"].replace("T"," ").replace("Z",""))-x).total_seconds())<=5400 for x in idx))
        out.append(f"{len(sub)}/{m} ({100*m/max(len(sub),1):.1f}%)")
    print(f"{v:<22}{len(idx):>11}{out[0]:>20}{out[1]:>18}")
