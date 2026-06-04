"""S100 — Auditoría A/B JUSTA: solo records presentes en AMBOS perfiles (mismo
granule), para aislar el efecto del flag del confounder de disponibilidad NASA."""
import csv, json
from datetime import datetime
from pathlib import Path
import statistics as st
REPO=Path("experiments/_s99_audit").resolve().parents[1]
WIN_S,WIN_E=datetime(2026,4,1),datetime(2026,5,31,23,59,59)
import os
ART=REPO/"experiments/_s99_audit"/os.environ.get("VRP_AB_ART","_ab_full_art")
PREFIX=os.environ.get("VRP_AB_PREFIX","s100")  # "s100p" para el run paired
CSV_CONS=REPO/"latest_consolidado.csv"; CSV_OCR=REPO/"data/mirova_reference/registro_vrp_ocr.csv"
VOLS=["Tupungatito","Villarrica","Lascar","Lastarria","Isluga","Llaima","NevadosDeChillan","PlanchonPeteroa","PuyehueCordonCaulle","Chaiten","Copahue"]
CSV_NAMES={"Tupungatito":["Tupungatito"],"Villarrica":["Villarrica"],"Lascar":["Lascar"],"Lastarria":["Lastarria"],"Isluga":["Isluga"],"Llaima":["Llaima"],"NevadosDeChillan":["Nevados de Chillan"],"PlanchonPeteroa":["PlanchonPeteroa","Peteroa"],"PuyehueCordonCaulle":["Puyehue-Cordon Caulle"],"Chaiten":["Chaiten"],"Copahue":["Copahue"]}
def fam(s):
    s=s or ""
    return "MODIS" if "MODIS" in s else "VIIRS750" if "750" in s else "VIIRS375" if "VIIRS" in s else s
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
            if r.get("Volcan") not in CSV_NAMES[vol] or r.get("Tipo_Registro")!=typ: continue
            dt=pdt(r.get("Fecha_Satelite_UTC",""))
            if not dt or not(WIN_S<=dt<=WIN_E): continue
            try: v=float(str(r["VRP_MW"]).replace(",","."))
            except: continue
            out.append({"dt":dt,"sensor":r.get("Sensor",""),"vrp":v})
    return out
def load(prof,vol):
    p=ART/f"{PREFIX}-{prof}-{vol}"/f"{vol}.json"
    d=json.load(open(p,encoding="utf-8")); return d if isinstance(d,list) else d.get("records",[])
def keyset(recs): return set((r.get("datetime_utc",""),str(r.get("sensor",""))) for r in recs)
def best(recs,r,common):
    c=[x for x in recs if (x.get("datetime_utc",""),str(x.get("sensor",""))) in common
       and pdt(x.get("datetime_utc","")) and abs((pdt(x["datetime_utc"])-r["dt"]).total_seconds())<=900
       and fam(x.get("sensor",""))==fam(r["sensor"])]
    if not c: return None
    return min(c,key=lambda x:(x.get("primary_cluster") or {}).get("centroid_dist_km",99))
print("=== A/B JUSTA (solo records comunes a baseline Y ctxpeak) — efecto AISLADO del flag ===")
print(f"{'volcano':20} {'pares':>6} {'rec_bl':>7} {'rec_cp':>7} {'d_rec':>6} {'FN_bl':>6} {'FN_cp':>6} {'rat_bl':>7} {'rat_cp':>7}")
tot={'pares':0,'dr':0,'dfn':0}
for vol in VOLS:
    bl=load("_s99_test1_baseline",vol); cp=load("_s99_test1_ctxpeak",vol)
    common=keyset(bl)&keyset(cp)
    rb=cb=fb=fc=0; ratb=[]; ratc=[]; pares=0
    for r in refs(vol):
        xb=best(bl,r,common); xc=best(cp,r,common)
        if xb is None or xc is None: continue  # alerta sin record comun en ambos
        pares+=1
        vb=(xb.get("primary_cluster") or {}).get("vrp_mw",0) or 0
        vc=(xc.get("primary_cluster") or {}).get("vrp_mw",0) or 0
        if vb>0: rb+=1; (r["vrp"]>0) and ratb.append(vb/r["vrp"])
        elif r["vrp"]>0: fb+=1
        if vc>0: cb+=1; (r["vrp"]>0) and ratc.append(vc/r["vrp"])
        elif r["vrp"]>0: fc+=1
    mb=round(st.median(ratb),2) if ratb else None; mc=round(st.median(ratc),2) if ratc else None
    print(f"{vol:20} {pares:>6} {rb:>7} {cb:>7} {cb-rb:>+6} {fb:>6} {fc:>6} {str(mb):>7} {str(mc):>7}")
    tot['pares']+=pares; tot['dr']+=cb-rb; tot['dfn']+=fc-fb
print("\nTOTAL pares=%d  d_recall(cp-bl)=%+d  d_FN(cp-bl)=%+d" % (tot["pares"], tot["dr"], tot["dfn"]))
