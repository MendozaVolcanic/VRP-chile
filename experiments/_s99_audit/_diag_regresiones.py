import csv, json
from datetime import datetime
from pathlib import Path
REPO = Path("experiments/_s99_audit").resolve().parents[1]
WIN_S, WIN_E = datetime(2026,4,1), datetime(2026,5,31,23,59,59)
ART = REPO/"experiments/_s99_audit/_ab_full_art"
CSV_CONS = REPO/"latest_consolidado.csv"; CSV_OCR = REPO/"data/mirova_reference/registro_vrp_ocr.csv"
NAMES={"Lascar":["Lascar"],"Lastarria":["Lastarria"],"Isluga":["Isluga"],"PuyehueCordonCaulle":["Puyehue-Cordon Caulle"]}
def fam(s):
    s=s or ""
    if "MODIS" in s: return "MODIS"
    if "750" in s: return "VIIRS750"
    if "VIIRS" in s: return "VIIRS375"
    return s
def pdt(s):
    s=str(s).replace("Z","").strip()
    for f in ("%Y-%m-%d %H:%M:%S","%Y-%m-%dT%H:%M:%S","%Y-%m-%d %H:%M","%Y-%m-%dT%H:%M"):
        try: return datetime.strptime(s[:19] if ":" in s[14:] else s[:16],f)
        except: pass
    return None
def refs(vol):
    out=[]
    for path,typ in [(CSV_CONS,"ALERTA_TERMICA"),(CSV_OCR,"ALERTA_TERMICA_OCR")]:
        if not path.exists(): continue
        for r in csv.DictReader(open(path,encoding="utf-8",errors="replace")):
            if r.get("Volcan") not in NAMES[vol] or r.get("Tipo_Registro")!=typ: continue
            dt=pdt(r.get("Fecha_Satelite_UTC","")); 
            if not dt or not(WIN_S<=dt<=WIN_E): continue
            try: v=float(str(r["VRP_MW"]).replace(",","."))
            except: continue
            out.append({"dt":dt,"sensor":r.get("Sensor",""),"vrp":v})
    return out
def load(prof,vol):
    p=ART/f"s100-{prof}-{vol}"/f"{vol}.json"
    if not p.exists(): return []
    d=json.load(open(p,encoding="utf-8")); return d if isinstance(d,list) else d.get("records",[])
def pcv(recs,r):
    c=[x for x in recs if pdt(x.get("datetime_utc","")) and abs((pdt(x["datetime_utc"])-r["dt"]).total_seconds())<=900 and fam(x.get("sensor",""))==fam(r["sensor"])]
    if not c: return None,None
    b=min(c,key=lambda x:(x.get("primary_cluster") or {}).get("centroid_dist_km",99))
    pc=b.get("primary_cluster") or {}
    return (pc.get("vrp_mw",0) or 0), pc.get("centroid_dist_km")
for vol in NAMES:
    bl=load("_s99_test1_baseline",vol); cp=load("_s99_test1_ctxpeak",vol)
    print(f"\n=== {vol}: records que CAMBIAN baseline->ctxpeak (matched MIROVA) ===")
    for r in refs(vol):
        b,bd=pcv(bl,r); c,cd=pcv(cp,r)
        if b is None: continue
        bdet=(b or 0)>0; cdet=(c or 0)>0
        if bdet!=cdet:  # cambió detección
            print(f"  {r['dt']} {r['sensor']:14} MIROVA={r['vrp']:.2f} | baseline pc={b:.3f}(d={bd}) -> ctxpeak pc={(c or 0):.3f}(d={cd})  {'PERDIDA' if bdet else 'GANADA'}")
