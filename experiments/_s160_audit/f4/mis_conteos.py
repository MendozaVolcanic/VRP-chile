# -*- coding: utf-8 -*-
"""S160 F4: conteos propios sobre la instantanea de d516b9d8c (D:\vrp-trabajo\temporales\s160_audit\main).
Las dos preguntas del instrumento: (1) si lo medido estuviera roto, cada bloque imprime conteos no nulos de control
(total de records, total de filas) para distinguir "no hay" de "no medi"; (2) un cero sale con su denominador.
Uso: python -I mis_conteos.py <raiz_instantanea>
"""
import csv, glob, json, sys, io
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(sys.argv[1])

def parse(ts):
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        pass
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%fZ"):
        try:
            d = datetime.strptime(ts, fmt)
            return d.replace(tzinfo=None)
        except Exception:
            pass
    return None

# ---------- 1. Test 1 integrado en los records (marcas S157: 0 de 3.661 / 0 de 3.687 desde 2026-09-18) ----------
tot = Counter(); t1 = Counter(); fuente = Counter(); fuentes_k = Counter(); n_sin_ts = 0
K = datetime(2026, 9, 18)
claves_ts = None
for f in sorted(glob.glob(str(ROOT / "data/mirova_equivalent/*.json"))):
    vol = Path(f).stem
    recs = json.load(open(f, encoding="utf-8"))
    if isinstance(recs, dict):
        recs = recs.get("records", [])
    for r in recs:
        if claves_ts is None:
            claves_ts = [k for k in r.keys() if "time" in k.lower() or "date" in k.lower() or "utc" in k.lower()]
        ts = r.get("datetime_utc") or r.get("timestamp") or r.get("time_utc") or r.get("acq_time") or ""
        d = parse(ts) if ts else None
        if d is None:
            n_sin_ts += 1
            continue
        reg = "desde_2026-09-18" if d >= K else "antes"
        tot[reg] += 1
        if r.get("triggered_test1"):
            t1[reg] += 1
        src = r.get("final_hotspot_source")
        fuente[(reg, src)] += 1
print("## 1. Test 1 integrado en data/mirova_equivalent (instantanea d516b9d8c)")
print("claves de tiempo vistas:", claves_ts, "| records sin timestamp parseable:", n_sin_ts)
for reg in ("antes", "desde_2026-09-18"):
    print(f"  {reg}: records {tot[reg]} | triggered_test1 {t1[reg]} | final_hotspot_source test1/test1_roi: "
          f"{sum(v for (rg, s), v in fuente.items() if rg == reg and s in ('test1', 'test1_roi'))}")
print("  fuentes (desde K):", {s: v for (rg, s), v in fuente.items() if rg == "desde_2026-09-18"})
print("  fuentes (antes):", {s: v for (rg, s), v in fuente.items() if rg == "antes"})

# ---------- 2. Tope D9 en Chillan MODIS 2026-09-28..10-13 (SINTOMAS: 7 pasadas, todas far, 0,7 a 4,7 km) ----------
f = ROOT / "data/mirova_equivalent/NevadosDeChillan.json"
recs = json.load(open(f, encoding="utf-8"))
if isinstance(recs, dict): recs = recs.get("records", [])
n = 0; capped = []
for r in recs:
    d = parse(r.get("datetime_utc") or r.get("timestamp") or "")
    if d is None or not r.get("sensor", "").startswith("MODIS"): continue
    if datetime(2026, 9, 28) <= d <= datetime(2026, 10, 14):
        n += 1
        pc = r.get("primary_cluster") or {}
        if pc.get("d9_capped"):
            capped.append((r.get("datetime_utc"), r.get("distance_class"), round(r.get("final_hotspot_dist_km") or -1, 2), pc.get("vrp_mw")))
print("\n## 2. Chillan MODIS 2026-09-28 a 2026-10-13: pasadas", n, "| con primary_cluster.d9_capped:", len(capped))
for c in capped: print("   ", c)

# ---------- 3. Tabla sola: D27 marca S151 (1.642 ALERTA_TERMICA 2026-01-11..10-14; 37 entre 13 y 21 UTC; 19 >= 1 MW) ----------
rows = list(csv.DictReader(open(ROOT / "latest_consolidado.csv", encoding="utf-8")))
print("\n## 3. latest_consolidado.csv: filas", len(rows))
def en_ventana(r, a, b):
    d = parse(r["Fecha_Satelite_UTC"]); return d is not None and a <= d <= b
W = (datetime(2026, 1, 11), datetime(2026, 10, 14, 23, 59, 59))
al = [r for r in rows if r["Tipo_Registro"] == "ALERTA_TERMICA" and en_ventana(r, *W)]
tarde = [r for r in al if 13 <= parse(r["Fecha_Satelite_UTC"]).hour <= 21]
prot_tarde = [r for r in tarde if float(r["VRP_MW"] or 0) >= 1.0]
prot_noche = [r for r in al if float(r["VRP_MW"] or 0) >= 1.0 and not (13 <= parse(r["Fecha_Satelite_UTC"]).hour <= 21)]
print(f"  ALERTA_TERMICA en 2026-01-11..2026-10-14: {len(al)} (S151 dijo 1.642)")
print(f"  entre 13 y 21 UTC: {len(tarde)} (S151: 37) | de 1 MW o mas: {len(prot_tarde)} (S151: 19) por sensor {Counter(r['Sensor'] for r in prot_tarde)} por volcan {Counter(r['Volcan'] for r in prot_tarde)}")
print(f"  protegidas de noche (1 MW o mas, fuera de 13-21 UTC): {len(prot_noche)} (S151: 233)")
# control positivo: ventana entera del CSV
al_all = [r for r in rows if r["Tipo_Registro"] == "ALERTA_TERMICA"]
print(f"  control: ALERTA_TERMICA en todo el CSV {len(al_all)}; primera fecha {min(r['Fecha_Satelite_UTC'] for r in rows)} ultima {max(r['Fecha_Satelite_UTC'] for r in rows)}")

# ---------- 4. A119 marca S151: alertas MODIS que dependen del OCR (5, todas Lascar, 4 nocturnas) ----------
ocr = list(csv.DictReader(open(ROOT / "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv", encoding="utf-8")))
print("\n## 4. registro_vrp_ocr.csv: filas", len(ocr), "| tipos:", Counter(r["Tipo_Registro"] for r in ocr))
tabla_idx = {}
for r in rows:
    d = parse(r["Fecha_Satelite_UTC"])
    if d: tabla_idx.setdefault((r["Volcan"], r["Sensor"]), []).append((d, r))
def en_tabla(vol, sen, d, tol=120):
    return any(abs((d - d2).total_seconds()) <= tol and r2["Tipo_Registro"].startswith("ALERTA") for d2, r2 in tabla_idx.get((vol, sen), []))
def mirada_en_tabla(vol, sen, d, tol=120):
    return any(abs((d - d2).total_seconds()) <= tol for d2, r2 in tabla_idx.get((vol, sen), []))
dep = []
for r in ocr:
    if r["Sensor"] != "MODIS" or not r["Tipo_Registro"].startswith("ALERTA"): continue
    d = parse(r["Fecha_Satelite_UTC"])
    if d is None: continue
    if not en_tabla(r["Volcan"], "MODIS", d):
        dep.append((r["Fecha_Satelite_UTC"], r["Volcan"], r["VRP_MW"], r["Tipo_Registro"], "tabla la miro" if mirada_en_tabla(r["Volcan"], "MODIS", d) else "tabla no la tiene"))
print(f"  alertas MODIS del OCR sin alerta en la tabla a 120 s: {len(dep)} (S151: 5, todas Lascar, 4 nocturnas)")
for x in dep: print("   ", x)
noct = sum(1 for x in dep if not (13 <= parse(x[0]).hour <= 21))
print("  nocturnas (fuera de 13-21 UTC):", noct, "| control: alertas MODIS en OCR total", sum(1 for r in ocr if r['Sensor']=='MODIS' and r['Tipo_Registro'].startswith('ALERTA')))
