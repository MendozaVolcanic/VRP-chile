# -*- coding: utf-8 -*-
import io,json,sys,math,datetime as dt
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
sys.path.insert(0,r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile")
from pipeline.mirova_csv_loader import load_mirova_alertas
BASE=r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
CONS=BASE+"/data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv"
OCR =BASE+"/data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv"
def load(v):
    d=json.load(open(f"{BASE}/data/mirova_equivalent/{v}.json",encoding="utf-8"))
    return d["records"] if isinstance(d,dict) and "records" in d else d
def parse(s):
    s=str(s).replace("Z","").replace("T"," ").strip()
    for f in ("%Y-%m-%d %H:%M:%S","%Y-%m-%d %H:%M","%Y-%m-%d"):
        try: return dt.datetime.strptime(s[:19],f)
        except: pass
    return None
al=load_mirova_alertas(cons_path=CONS,ocr_path=OCR)
print("ALERTAS cargadas:",len(al))
mx=max((parse(a["timestamp"]) for a in al if parse(a["timestamp"])),default=None)
print("ultima ALERTA en el CSV:",mx)
TIER=["Villarrica","Lascar","Copahue","Llaima","NevadosDeChillan","Isluga","Lastarria",
      "Chaiten","PlanchonPeteroa","PuyehueCordonCaulle","Tupungatito"]
# ventana comun: hasta la ultima ALERTA disponible
END=mx
print("\n=== % de pasadas nuestras que MIROVA tambien publico (V375, +-90 min) ===")
print(f"{'volcan':<22}{'src':<12}{'n':>5}{'match':>7}{'%':>7}")
for v in TIER:
    idx=sorted(parse(a["timestamp"]) for a in al
               if a["volcano"]==v and (a.get("sensor_bucket") or "").upper().find("375")>=0
               and parse(a["timestamp"]))
    if not idx:
        idx=sorted(parse(a["timestamp"]) for a in al if a["volcano"]==v and parse(a["timestamp"]))
    rs=[r for r in load(v) if r.get("sensor","").startswith("VIIRS")
        and not r.get("sensor","").endswith("_750") and r.get("distance_class")=="summit"
        and parse(r.get("datetime_utc")) and parse(r["datetime_utc"])>=dt.datetime(2026,6,1)
        and (END is None or parse(r["datetime_utc"])<=END)]
    for src in ("test1_roi","ctx_cluster"):
        sub=[r for r in rs if r.get("final_hotspot_source")==src]
        if not sub: continue
        m=0
        for r in sub:
            t=parse(r["datetime_utc"])
            if any(abs((t-x).total_seconds())<=5400 for x in idx): m+=1
        print(f"{v:<22}{src:<12}{len(sub):>5}{m:>7}{100*m/len(sub):>6.1f}%")
