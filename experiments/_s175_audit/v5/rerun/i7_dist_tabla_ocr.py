# -*- coding: utf-8 -*-
"""I5/I7: en pasadas que tienen fila de la tabla (CONS) y del OCR a +-120 s, ¿coincide la distancia? Por volcán, sensor y
estrato (antes/desde Mirova-v1#20, 2026-10-09 14:01 UTC). Usa la referencia unificada de la base (leer_pasadas del cargador
de la base, que saca la distancia del OCR de la nota). Salida: i7_dist_tabla_ocr_out.json."""
import collections, json, os, sys, statistics as st
from datetime import datetime
ROOT = r"C:\Users\nmend\vrp-temporales\s175_audit\f5\root"
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
from referencia_mirova_unificada import leer_pasadas, SNAP_CONS, SNAP_OCR
H = os.path.dirname(os.path.abspath(__file__))
cons = leer_pasadas(SNAP_CONS, "CONS", "principal")
ocr = leer_pasadas(SNAP_OCR, "OCR", "principal")
dt = lambda f: datetime.strptime(f["fecha_utc"][:19], "%Y-%m-%d %H:%M:%S")
idx = collections.defaultdict(list)
for f in cons:
    idx[(f["volcano"], f["sensor_bucket"])].append((dt(f), f))
g = collections.defaultdict(list)
for o in ocr:
    if not o["tipo"].startswith("ALERTA_TERMICA") or o["dist_km"] is None:
        continue
    par = [f for t, f in idx.get((o["volcano"], o["sensor_bucket"]), []) if abs((t - dt(o)).total_seconds()) <= 120
           and f["dist_km"] is not None and f["dist_km"] > 0]
    if not par:
        continue
    est = "antes_V31" if o["fecha_utc"][:16] < "2026-10-09 14:01" else "desde_V31"
    g[(o["volcano"], o["sensor_bucket"], est)].append(round(o["dist_km"] - par[0]["dist_km"], 2))
res = {}
for k, l in sorted(g.items()):
    res["|".join(k)] = {"n": len(l), "mediana_ocr_menos_tabla_km": st.median(l), "n_abs_mayor_1km": sum(abs(x) > 1 for x in l),
                        "valores": sorted(l)[:15]}
    print(k, res["|".join(k)])
json.dump(res, open(os.path.join(H, "i7_dist_tabla_ocr_out.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
