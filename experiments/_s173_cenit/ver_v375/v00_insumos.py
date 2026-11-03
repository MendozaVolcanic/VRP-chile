# -*- coding: utf-8 -*-
"""v00 (verificador V375, S173): inventario de los insumos SIN los helpers del auditor.

POR QUE: antes de parear por mi cuenta tengo que saber que columnas trae la referencia del scraper (nombres del volcan,
columna de fecha, sensor) y que campos trae el JSON de K de produccion (cenit, f5_core, pc.vrp_mw, sha del codigo,
processed_utc), y si hay duplicados por (sensor, minuto). Un pareo escrito sobre nombres supuestos da cero y el cero se
lee como ausencia (A89).
P1: si el JSON no se leyera, los conteos serian 0 y se imprime el total de records (control: > 0).
P2: control positivo de duplicados: se inyecta un duplicado artificial en una copia y el contador debe dar 1 mas.
Uso: python -I v00_insumos.py <raiz copia_main>
"""
import collections, csv, json, sys

ROOT = sys.argv[1].rstrip("/\\")
SNAP = ROOT + "/data/mirova_reference/mirova_v1_snapshot/"
VOL = "NevadosDeChillan"

print("== referencia CONS")
rows = list(csv.DictReader(open(SNAP + "registro_vrp_consolidado.csv", encoding="utf-8", errors="replace")))
print("filas", len(rows))
print("columnas", list(rows[0].keys()))
volcol = [k for k in rows[0] if k.lower().startswith("volc")][0]
fcol = [k for k in rows[0] if "Fecha_Satelite" in k][0]
print("col volcan =", volcol, "| col fecha =", fcol)
nombres = collections.Counter(r[volcol] for r in rows if "hill" in r[volcol].lower())
print("variantes Chillan:", nombres)
ch = [r for r in rows if "hill" in r[volcol].lower()]
print("Chillan: fecha min", min(r[fcol] for r in ch), "max", max(r[fcol] for r in ch))
print("CONS total: fecha max", max(r[fcol] for r in rows))
sens = collections.Counter(r.get("Sensor") for r in ch)
print("Sensor (Chillan):", sens)
tipos = collections.Counter(r.get("Tipo") or r.get("tipo") for r in ch)
print("Tipo (Chillan):", tipos.most_common(12))
print("ejemplo fila:", ch[-1])

print("== referencia OCR")
ocr = list(csv.DictReader(open(SNAP + "registro_vrp_ocr.csv", encoding="utf-8", errors="replace")))
print("filas", len(ocr))
print("columnas", list(ocr[0].keys()))
vo = [k for k in ocr[0] if k.lower().startswith("volc")][0]
fo = [k for k in ocr[0] if "Fecha_Satelite" in k][0]
cho = [r for r in ocr if "hill" in r[vo].lower()]
print("variantes Chillan OCR:", collections.Counter(r[vo] for r in cho))
print("OCR Chillan fecha max", max(r[fo] for r in cho) if cho else None, "| OCR total max", max(r[fo] for r in ocr))
print("ejemplo fila OCR:", cho[-1] if cho else None)

print("== JSON K de produccion")
d = json.load(open(ROOT + "/data/mirova_equivalent/" + VOL + ".json", encoding="utf-8"))
R = d["records"]
print("records", len(R))
print("sensores:", collections.Counter(r.get("sensor") for r in R))
print("campos presentes (muestra):", sorted(R[-1].keys()))
claves = collections.Counter((r.get("sensor"), r.get("datetime_utc")) for r in R)
dup = {k: v for k, v in claves.items() if v > 1}
print("duplicados (sensor, datetime_utc):", len(dup), list(dup.items())[:5])
# control positivo de duplicados
R2 = R + [R[-1]]
c2 = collections.Counter((r.get("sensor"), r.get("datetime_utc")) for r in R2)
print("control positivo duplicados (+1 artificial):", sum(1 for v in c2.values() if v > 1))
v375 = [r for r in R if r.get("sensor", "").startswith("VIIRS") and not r.get("sensor", "").endswith("750")]
print("VIIRS 375 records:", len(v375), "| con sensor_zenith_deg:", sum(1 for r in v375 if r.get("sensor_zenith_deg") is not None))
print("VIIRS 375 con f5_core_vrp_mw no None:", sum(1 for r in v375 if r.get("f5_core_vrp_mw") is not None))
print("codigo_sha (VIIRS375):", collections.Counter((r.get("regimen") or {}).get("codigo_sha") for r in v375).most_common(5))
print("perfil:", collections.Counter((r.get("regimen") or {}).get("perfil") for r in v375))
pu = sorted(r.get("processed_utc") or "" for r in v375)
print("processed_utc min/max (V375):", pu[0], pu[-1])
w = [r for r in v375 if "2026-09-28" <= (r.get("datetime_utc") or "")[:10] <= "2026-11-02"]
print("V375 records 2026-09-28..11-02:", len(w), "| processed_utc min:", min(r.get("processed_utc") or "" for r in w))
print("product_version (ventana):", collections.Counter(r.get("product_version") for r in w))
dts = collections.Counter(r.get("datetime_utc") for r in w)
print("mismo minuto, dos plataformas (ventana):", sum(1 for v in dts.values() if v > 1))
