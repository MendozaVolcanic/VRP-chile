# -*- coding: utf-8 -*-
"""S150 auditor D, sonda 5: la guarda de cobertura de auto_audit_weekly.py, frente a un apagon corto.
PREGUNTA 1: si la guarda no viera un apagon, esta sonda lo veria? Si: separa las noches de alerta no
detectadas en (a) sin NINGUN record nuestro ese dia para ese volcan y sensor (no medimos) y (b) con records
(medimos y no vimos), y recalcula la cobertura con la definicion del script.
PREGUNTA 2 (control positivo): simulo un apagon de 10 dias borrando records en memoria y la cobertura del
script tiene que bajar 10/61; si no baja, la definicion no mide dias con datos.
Uso: python d5_cobertura_semanal.py 2026-08-06 2026-10-05"""
import collections, io, json, sys
from datetime import datetime, timezone, date, timedelta
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "scripts"))
import auto_audit_weekly as aw
from pipeline.mirova_csv_loader import load_mirova_alertas
desde, hasta = sys.argv[1:3]; win = (desde, hasta)
coords = aw._coords_por_volcan()
mir = set()
for a in load_mirova_alertas(cons_path=aw.CONS, ocr_path=aw.OCR):
    dt = a["fecha_utc"] or ""
    if not (dt and win[0] <= dt[:10] <= win[1]) or a["sensor_bucket"] not in aw.SENSORS: continue
    lat, lon = coords[a["volcano"]]
    if aw.es_pasada_diurna_descartada(a["sensor_bucket"], lat, lon, datetime.fromisoformat(dt).replace(tzinfo=timezone.utc)): continue
    mir.add((a["volcano"], a["sensor_bucket"], dt[:10]))
recs = {}
for vol in aw.VOLS:
    recs[vol] = [r for r in json.load(open(RAIZ / "data" / "mirova_equivalent" / f"{vol}.json", encoding="utf-8"))["records"]
                 if win[0] <= (r.get("datetime_utc") or "")[:10] <= win[1]]
def medir(apagon=()):
    hay, crater = set(), set()
    for vol, rs in recs.items():
        for r in rs:
            d = r["datetime_utc"][:10]
            if d in apagon: continue
            b = aw.our_bucket(r.get("sensor", ""))
            if b is None: continue
            hay.add((vol, b, d))
            pc = r.get("primary_cluster") or {}
            if 0 < (pc.get("vrp_mw") or 0) <= aw.CAP and pc.get("centroid_dist_km") is not None and pc["centroid_dist_km"] <= aw.INNER[vol]:
                crater.add((vol, b, d))
    dias_script = {d for (_, _, d) in crater}
    return hay, crater, round(100 * len(dias_script) / 61, 1), len({d for (_, _, d) in hay})
hay, crater, cob, dias_con_records = medir()
print("ventana", win, "| cobertura con la definicion del script %.1f %% | dias con CUALQUIER record %d de 61" % (cob, dias_con_records))
for s in aw.SENSORS:
    ks = [k for k in mir if k[1] == s]
    no = [k for k in ks if k not in crater]
    sin_rec = [k for k in no if k not in hay]
    print("%-8s noches alerta %3d | no detectadas %3d | de esas SIN ningun record nuestro %3d: %s" % (s, len(ks), len(no), len(sin_rec), sorted(sin_rec)[:12]))
    if ks:
        print("          recall sin contar las noches sin record: %.1f %%" % (100 * (len(ks) - len(no)) / (len(ks) - len(sin_rec))))
d0 = date.fromisoformat(hasta)
apagon = {(d0 - timedelta(days=i)).isoformat() for i in range(10)}
_, _, cob2, _ = medir(apagon)
print("CONTROL POSITIVO: apagon simulado de los ultimos 10 dias -> cobertura del script %.1f %% (umbral DEGRADADO %.0f %%)" % (cob2, aw.MIN_COVERAGE_PCT))
