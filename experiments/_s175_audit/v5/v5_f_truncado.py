# -*- coding: utf-8 -*-
"""V5-F: 307 por otro camino. Lee el CSV OCR crudo (snapshot de la base, sha256 577a336e...) con csv, SIN el cargador de la base, y busca la
nota de truncado con una expresion mas laxa que la del auditor (cualquier 'truncad' o 'real'), para no depender de su regex.
Pregunta 1: si 'nueve alertas OCR 1,0 MW con nota de truncado' fuera falso, el conteo de VRP==1.0 con nota daria otro numero. Pregunta 2: control
positivo: la fila Chillan MODIS 2026-11-06 13:15 (9.0, 'real in [9,10)') tiene que aparecer; si el lector estuviera muerto no apareceria.
Ademas: para cada una, ¿hay fila de la tabla (CONS) de la misma pasada +-120 s y con que VRP? (si hay CONS >=1, la protegida no depende del OCR)."""
import csv, collections, os, re, sys
sys.stdout.reconfigure(encoding="utf-8")
from datetime import datetime
INS = r"C:\Users\nmend\vrp-temporales\s175_audit\insumos"
ocr = list(csv.DictReader(open(os.path.join(INS, "snapshot_ocr_base.csv"), encoding="utf-8")))
cons = list(csv.DictReader(open(os.path.join(INS, "snapshot_consolidado_base.csv"), encoding="utf-8")))
dt = lambda s: datetime.strptime(s[:16], "%Y-%m-%d %H:%M")
def base(v):
    return v.replace(" ", "").replace("-", "").lower()[:8]
notas = [f for f in ocr if re.search(r"trunc|real\s*[∈\u2208]", f.get("Nota_Validacion") or "", re.I)]
print("filas OCR con nota de truncado (laxa):", len(notas), "de", len(ocr))
print(collections.Counter(f["Sensor"] for f in notas), collections.Counter(f["Tipo_Registro"] for f in notas))
print("distribucion de intervalos:", collections.Counter(re.search(r"real\s*[∈\u2208]\s*(\[[^)]*\))", f["Nota_Validacion"]).group(1) if re.search(r"real\s*[∈\u2208]\s*(\[[^)]*\))", f["Nota_Validacion"]) else "?" for f in notas).most_common(12))
uno = [f for f in notas if f["VRP_MW"] and abs(float(f["VRP_MW"]) - 1.0) < 1e-9]
print("con VRP == 1.0 exacto:", len(uno))
for f in uno:
    t = dt(f["Fecha_Satelite_UTC"])
    par = [c for c in cons if base(c["Volcan"]) == base(f["Volcan"]) and c["Sensor"][:4] == f["Sensor"][:4] and abs((dt(c["Fecha_Satelite_UTC"]) - t).total_seconds()) <= 120]
    print(" ", f["Fecha_Satelite_UTC"], f["Volcan"], f["Sensor"], f["Tipo_Registro"], "VRP", f["VRP_MW"], "| nota:", re.sub(r".*(real[^|]*).*", r"\1", f["Nota_Validacion"])[:40],
          "| CONS misma pasada:", [(c["Tipo_Registro"], c["VRP_MW"]) for c in par] or "ninguna")
# todas las notas con intervalo que incluye 1 (real in [1,2) o [0,1)) en cualquier VRP
print("notas cuyo VRP escrito esta en [0.5,2):")
for f in notas:
    v = float(f["VRP_MW"] or 0)
    if 0.5 <= v < 2:
        print(" ", f["Fecha_Satelite_UTC"], f["Volcan"], f["Sensor"], f["Tipo_Registro"], v, re.search(r"real[^|]*", f["Nota_Validacion"]).group(0)[:30])
ctrl = [f for f in notas if f["Fecha_Satelite_UTC"].startswith("2026-11-06 13:15")]
print("CONTROL positivo (Chillan MODIS 2026-11-06 13:15):", [(f["Volcan"], f["VRP_MW"]) for f in ctrl])
