# PCC vs MIROVA ground truth cross-check S112
import json, csv, collections, math, sys, io
from datetime import datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/"
GT = ROOT+"experiments/_s111_d11/mirova_fresh/"

def bucket(s):
    if s is None: return "unknown"
    if "MODIS" in s: return "MODIS"
    if s.endswith("_750"): return "VIIRS750"
    return "VIIRS375"
def pcv(r):
    pc=r.get("primary_cluster") or {}; return pc.get("vrp_mw",0.0) or 0.0
def pcd(r):
    pc=r.get("primary_cluster") or {}; return pc.get("centroid_dist_km")

# --- Load MIROVA cons + ocr for PCC ---
def load_mirova(path, alert_filter=None):
    rows=[]
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["Volcan"]!="Puyehue-Cordon Caulle": continue
            dt=row["Fecha_Satelite_UTC"]
            if not dt.startswith(("2026-05","2026-06")): continue
            rows.append(row)
    return rows

cons=load_mirova(GT+"cons.csv")
ocr=load_mirova(GT+"ocr.csv")
print(f"=== MIROVA PCC rows May+June: cons={len(cons)} ocr={len(ocr)} ===\n")

# MIROVA detections = VRP>0 (ALERTA) in cons or ocr
def mirova_alerts(rows):
    out=[]
    for r in rows:
        try: vrp=float(r["VRP_MW"])
        except: vrp=0.0
        tipo=r.get("Tipo_Registro","")
        if vrp>0 or "ALERTA" in tipo:
            out.append((r["Fecha_Satelite_UTC"], r["Sensor"], vrp, r.get("Distancia_km"), tipo, r.get("Clasificacion Mirova","")))
    return out

cons_alerts=mirova_alerts(cons)
ocr_alerts=mirova_alerts(ocr)
print(f"MIROVA CONS alerts (VRP>0 or ALERTA): {len(cons_alerts)}")
for a in cons_alerts: print("  CONS", a)
print(f"\nMIROVA OCR alerts: {len(ocr_alerts)}")
for a in sorted(ocr_alerts)[:40]: print("  OCR ", a)

# Sensor breakdown of MIROVA alerts
print("\nMIROVA alert sensors (cons):", collections.Counter(a[1] for a in cons_alerts))
print("MIROVA alert sensors (ocr): ", collections.Counter(a[1] for a in ocr_alerts))
print("MIROVA alert distances (ocr):", sorted(set(round(float(a[3]),1) for a in ocr_alerts if a[3] and a[3] not in('','0.0'))))

# All MIROVA dist values to see max
all_dist=[]
for r in cons+ocr:
    try: dd=float(r["Distancia_km"])
    except: dd=None
    if dd: all_dist.append(dd)
print(f"\nMIROVA reported distances range (all PCC rows): min={min(all_dist):.1f} max={max(all_dist):.1f} (these are MIROVA's own dist-from-Smithsonian)")
