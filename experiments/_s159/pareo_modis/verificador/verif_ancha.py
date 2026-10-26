# -*- coding: utf-8 -*-
"""Verificador S159: con +-390 s, los positivos nuevos son mitades de pasadas ya pareadas?
Pregunta 1: si el pareo ancho rescatara alertas perdidas, apareceria alguna alerta con record a 121-390 s y SIN
record a +-120 s. Las cuento aparte de las que ya tienen record a +-120 s (doble conteo). Ventana 2026-01-10 a
2026-10-21, filas ALERTA (sin ALERTA_SIN_GEOMETRIA_OCR) de horas 00-11 UTC (noche en Chile)."""
import collections, json, sys
from datetime import datetime, timedelta
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
RAIZ = Path(sys.argv[1]); sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "scripts"))
from referencia_mirova_unificada import cargar_referencia_unificada, SNAP_CONS, SNAP_OCR
VOLS = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan",
        "Llaima", "Villarrica", "Copahue", "PuyehueCordonCaulle", "Chaiten"]
def bucket(s):
    return "MODIS" if s.startswith("MODIS") else ("VIIRS750" if s.endswith("_750") else "VIIRS375")
ours = collections.defaultdict(list)
for v in VOLS:
    for r in json.load(open(RAIZ / "data/mirova_equivalent" / f"{v}.json", encoding="utf-8"))["records"]:
        ours[(v, bucket(r["sensor"]))].append(datetime.strptime(r["datetime_utc"][:16], "%Y-%m-%d %H:%M"))
c = collections.Counter(); seen = set()
for f in cargar_referencia_unificada(SNAP_CONS, SNAP_OCR):
    if f["volcano"] not in VOLS or not ("2026-01-10" <= f["fecha_utc"][:10] <= "2026-10-21"): continue
    if not ("00" <= f["fecha_utc"][11:13] <= "11"): continue
    if not (f["tipo"].startswith("ALERTA") and f["tipo"] != "ALERTA_SIN_GEOMETRIA_OCR"): continue
    k = (f["volcano"], f["sensor_bucket"], f["fecha_utc"][:16])
    if k in seen: continue
    seen.add(k)
    t = datetime.strptime(f["fecha_utc"][:16], "%Y-%m-%d %H:%M")
    ds = [abs((x - t).total_seconds()) for x in ours[(f["volcano"], f["sensor_bucket"])]]
    cerca = any(d <= 120 for d in ds); ancha = any(120 < d <= 390 for d in ds)
    c[(f["sensor_bucket"], "a 120" if cerca else "sin 120", "y vecino 121-390" if ancha else "")] += 1
for k in sorted(c): print(k, c[k])
