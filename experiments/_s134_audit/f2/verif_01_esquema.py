# -*- coding: utf-8 -*-
"""VERIF/01 - controles del verificador. Read-only.
C1 anomaly_pixels vs n_anomalous_pixels (truncamiento o semantica?)
C2 alias del CSV + conteo de ALERTAS V375 por volcan en la ventana
C3 index.csv: cobertura temporal y los dos relojes
"""
import os, sys, csv, json, io, datetime as dt, statistics as st, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
sys.path.insert(0, RAIZ)
F2 = os.path.join(RAIZ, "experiments", "_s134_audit", "f2")
D0 = dt.datetime(2026, 6, 1, tzinfo=dt.timezone.utc)
IBAND = ("VIIRS_SNPP", "VIIRS_NOAA20", "VIIRS_NOAA21")
VOLS = ["Lascar","Isluga","PuyehueCordonCaulle","Tupungatito","Lastarria","PlanchonPeteroa",
        "Chaiten","NevadosDeChillan","Villarrica","Copahue","Llaima"]

def pu(s):
    if not s: return None
    try: t = dt.datetime.fromisoformat(str(s).replace("Z","+00:00"))
    except ValueError: return None
    return t.replace(tzinfo=dt.timezone.utc) if t.tzinfo is None else t.astimezone(dt.timezone.utc)

print("="*80); print("C1 - anomaly_pixels vs n_anomalous_pixels")
tot=lt=eq=gt=0; eq_pc=0; con_pc=0; la=[]; na=[]
ej_gt=[]
for v in VOLS:
    for r in json.load(open(os.path.join(RAIZ,"data","mirova_equivalent",v+".json"),encoding="utf-8"))["records"]:
        if r.get("sensor") not in IBAND: continue
        t = pu(r.get("datetime_utc"))
        if t is None or t < D0: continue
        n = r.get("n_anomalous_pixels"); ap = r.get("anomaly_pixels")
        if n is None or ap is None: continue
        tot += 1; L = len(ap); la.append(L); na.append(n)
        if L < n: lt += 1
        elif L == n: eq += 1
        else:
            gt += 1
            if len(ej_gt) < 3: ej_gt.append((v, r.get("datetime_utc"), L, n))
        pc = r.get("primary_cluster") or {}
        if pc.get("n_pixels") is not None:
            con_pc += 1
            if L == pc["n_pixels"]: eq_pc += 1
print("  n=%d records V375 desde 2026-06-01" % tot)
print("  mediana len(anomaly_pixels)=%s  mediana n_anomalous_pixels=%s" % (st.median(la), st.median(na)))
print("  len < n : %d (%.1f%%)   len == n : %d (%.1f%%)   len > n : %d (%.1f%%)" %
      (lt,100*lt/tot, eq,100*eq/tot, gt,100*gt/tot))
print("  len(anomaly_pixels) == primary_cluster.n_pixels : %d de %d (%.1f%%)" % (eq_pc,con_pc,100*eq_pc/con_pc))
print("  ejemplos con len > n (refutarian 'recorte'):", ej_gt if ej_gt else "NINGUNO")
print("  maximo len(anomaly_pixels) = %d  (cap del codigo: top_n=100)" % max(la))

print("="*80); print("C2 - alias del CSV y ALERTAS V375 por volcan en la ventana")
cons = os.path.join(RAIZ,"data","mirova_reference","mirova_v1_snapshot","registro_vrp_consolidado.csv")
ocr  = os.path.join(RAIZ,"data","mirova_reference","mirova_v1_snapshot","registro_vrp_ocr.csv")
for p in (cons, ocr):
    names = sorted(set(row["Volcan"] for row in csv.DictReader(open(p,encoding="utf-8"))))
    print("  %s -> %d nombres:" % (os.path.basename(p), len(names)))
    print("   ", names)
from pipeline.mirova_csv_loader import load_mirova_alertas
print("  ALERTAS VIIRS375 desde 2026-06-01 (loader, CONS u OCR):")
for v in VOLS:
    a = load_mirova_alertas(cons_path=cons, ocr_path=ocr, volcano=v)
    n = sum(1 for x in a if x.get("sensor_bucket")=="VIIRS375"
            and dt.datetime.fromtimestamp(int(x["timestamp"]),dt.timezone.utc) >= D0)
    tot_all = sum(1 for x in a if dt.datetime.fromtimestamp(int(x["timestamp"]),dt.timezone.utc) >= D0)
    buckets = collections.Counter(x.get("sensor_bucket") for x in a
        if dt.datetime.fromtimestamp(int(x["timestamp"]),dt.timezone.utc) >= D0)
    print("    %-21s V375=%-4d  total=%-4d  %s" % (v, n, tot_all, dict(buckets)))
# control: 'Llaima' aparece con alguna grafia rara?
raw = [row for row in csv.DictReader(open(cons,encoding="utf-8")) if "llaim" in row["Volcan"].lower()]
print("  filas CONS cuyo Volcan contiene 'llaim': %d  grafias=%s" % (len(raw), sorted(set(r["Volcan"] for r in raw))))

print("="*80); print("C3 - index.csv: cobertura y los dos relojes")
import re
RE_FN = re.compile(r"(\d{8})_(\d{6})_([A-Za-z0-9]+)(_lm)?\.tif$")
rows = list(csv.DictReader(open(os.path.join(F2,"index.csv"),encoding="utf-8")))
n=0; sin_acq=0; disc=0; con_ambos=0; fechas=[]
for r in rows:
    m = RE_FN.search(r["tif_path"].replace("\\","/"))
    if not m: continue
    n += 1
    tfn = dt.datetime.strptime(m.group(1)+m.group(2),"%Y%m%d%H%M%S").replace(tzinfo=dt.timezone.utc)
    fechas.append(tfn)
    ta = pu(r["acquisition_utc"])
    if ta is None: sin_acq += 1; continue
    con_ambos += 1
    if abs((tfn-ta).total_seconds()) > 60: disc += 1
print("  filas con nombre parseable: %d de %d" % (n, len(rows)))
print("  sin acquisition_utc: %d (%.1f%%)" % (sin_acq, 100*sin_acq/n))
print("  con ambos: %d ; discrepan >60 s: %d (%.1f%%)" % (con_ambos, disc, 100*disc/con_ambos))
print("  rango de fechas (nombre): %s .. %s" % (min(fechas).date(), max(fechas).date()))
por_mes = collections.Counter(f.strftime("%Y-%m") for f in fechas)
print("  por mes:", dict(sorted(por_mes.items())))
