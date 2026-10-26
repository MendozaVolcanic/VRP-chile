# -*- coding: utf-8 -*-
"""VP162 verificador, v06: conteo crudo (sin el agrupador de #903) de alertas OCR VIIRS 375 >= 1 MW sin fila de tabla
a <= 120 s, antes del 2026-10-09; y busqueda de las 6 pasadas en la tabla REMOTA de hoy (no la copia congelada).
Pregunta 1: si el 128 del agrupador fuera artefacto del agrupador, el conteo crudo daria otra cosa.
Pregunta 2: control positivo: el mismo conteo crudo de alertas de la tabla >= 1 MW VIIRS 375 tiene que ser ~104.
"""
import csv, io, sys
from datetime import datetime, timedelta
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
R = Path(__file__).resolve().parents[4]
S = R/"data/mirova_reference/mirova_v1_snapshot"
sys.path.insert(0, str(R))
from pipeline.mirova_csv_loader import normalize_volcano_name, normalize_sensor
def t(s):
    s = s.strip().replace("T", " ")[:19]
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S" if len(s) >= 19 else "%Y-%m-%d %H:%M")
def leer(p):
    with open(p, encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            v = normalize_volcano_name(r.get("Volcan")); sb = normalize_sensor(r.get("Sensor", ""))
            if not v or sb != "VIIRS375": continue
            try: vrp = float(r["VRP_MW"])
            except (ValueError, TypeError): vrp = None
            yield v, t(r["Fecha_Satelite_UTC"]), r["Tipo_Registro"], vrp
cons = []
for p in (S/"registro_vrp_consolidado.csv", S/"registro_vrp_consolidado_respaldo_20260408.csv",
          R/"data/mirova_reference/union_historica/consolidado_filas_perdidas.csv"):
    if p.exists(): cons += list(leer(p))
idx = {}
for v, tt, tipo, vrp in cons: idx.setdefault(v, []).append(tt)
def hay_tabla(v, tt): return any(abs((x-tt).total_seconds()) <= 120 for x in idx.get(v, []))
ocr = list(leer(S/"registro_vrp_ocr.csv"))
alert = ("ALERTA_TERMICA", "ALERTA_TERMICA_OCR")
o1 = {(v, tt) for v, tt, tipo, vrp in ocr if tipo in alert and vrp is not None and vrp >= 1.0 and not hay_tabla(v, tt)}
pre = {x for x in o1 if x[1].strftime("%Y-%m-%d") < "2026-10-09"}
c1 = {(v, tt) for v, tt, tipo, vrp in cons if tipo in alert and vrp is not None and vrp >= 1.0}
print(f"OCR alerta >=1 MW VIIRS375 sin tabla a <=120 s: {len(o1)}; antes del 2026-10-09: {len(pre)}")
print(f"tabla alerta >=1 MW VIIRS375 (filas unicas volcan+instante): {len(c1)}")
rem = Path(sys.argv[1]) if len(sys.argv) > 1 else None
if rem and rem.exists():
    rc = list(leer(rem))
    print(f"\ntabla remota de hoy: {len(rc)} filas VIIRS375 Tier A, hasta {max(x[1] for x in rc)}")
    for v, ts in [("Tupungatito", "2026-08-01 05:00"), ("Lascar", "2026-08-22 05:06"), ("Isluga", "2026-09-09 06:06"),
                  ("Tupungatito", "2026-09-14 06:18"), ("Tupungatito", "2026-09-28 05:18"), ("Tupungatito", "2026-09-29 04:54")]:
        t0 = datetime.strptime(ts, "%Y-%m-%d %H:%M")
        m = [(x[1], x[2], x[3]) for x in rc if x[0] == v and abs((x[1]-t0).total_seconds()) <= 600]
        print(f"  {v} {ts}: filas remotas a <=10 min: {m}")
