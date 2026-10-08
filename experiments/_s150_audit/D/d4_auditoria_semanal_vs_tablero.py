# -*- coding: utf-8 -*-
"""S150 auditor D, sonda 4: la auditoria semanal (scripts/auto_audit_weekly.py) juzga el recall con un
predicado propio en Python ("crater": pc.vrp_mw > 0 y centroide dentro del inner, SIN mirar
distance_class). Lo que ve el operador es el predicado del tablero (node, frontend/index.html), que oculta
las pasadas `far` aunque el cumulo este en el crater (A46/A81). Esta sonda mide, noche de alerta por
noche de alerta, las tres varas: crater (la que decide el flag), dash (la que el script calcula y no usa
para el flag) y el predicado real del tablero.

PREGUNTAS DEL INSTRUMENTO
 1. Si la auditoria semanal estuviera ciega a lo que oculta el tablero, esta sonda lo veria? Si: lista
    las noches donde "crater" dice detectado y el predicado del tablero dice oculto.
 2. Si la sonda estuviera muerta, se veria distinto? Control positivo: reproduzco las cifras de
    data/audit_continuous/latest.json (recall_crater y recall_dash por sensor) con la misma ventana; si mi
    reimplementacion no las reproduce, la comparacion no vale.

Uso: python d4_auditoria_semanal_vs_tablero.py 2026-08-06 2026-10-05
"""
import collections, io, json, sys
from datetime import datetime, timezone
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "scripts"))
import auto_audit_weekly as aw
import banco_paridad as bp
from pipeline.mirova_csv_loader import load_mirova_alertas

desde, hasta = sys.argv[1:3]
win = (desde, hasta)
coords = aw._coords_por_volcan()
inner_html = bp.inner_desde_html()

mir = collections.defaultdict(float)
for a in load_mirova_alertas(cons_path=aw.CONS, ocr_path=aw.OCR):
    dt = a["fecha_utc"] or ""
    if not (dt and win[0] <= dt[:10] <= win[1]) or a["sensor_bucket"] not in aw.SENSORS:
        continue
    lat, lon = coords[a["volcano"]]
    if aw.es_pasada_diurna_descartada(a["sensor_bucket"], lat, lon, datetime.fromisoformat(dt).replace(tzinfo=timezone.utc)):
        continue
    k = (a["volcano"], a["sensor_bucket"], dt[:10]); mir[k] = max(mir[k], a["vrp_mw"] or 0.0)

ours = collections.defaultdict(lambda: {"crater": 0, "dash": 0, "tablero": 0})
casos, claves = [], []
for vol in aw.VOLS:
    d = json.load(open(RAIZ / "data" / "mirova_equivalent" / f"{vol}.json", encoding="utf-8"))
    for r in d["records"]:
        dt = r.get("datetime_utc") or ""
        if not (win[0] <= dt[:10] <= win[1]):
            continue
        b = aw.our_bucket(r.get("sensor", ""))
        if b is None:
            continue
        pc = r.get("primary_cluster") or {}
        vrp, cd = pc.get("vrp_mw") or 0.0, pc.get("centroid_dist_km")
        k = (vol, b, dt[:10])
        if 0 < vrp <= aw.CAP and cd is not None and cd <= aw.INNER[vol]:
            ours[k]["crater"] = 1
            if not r.get("distance_class") or r.get("distance_class") == "summit":
                ours[k]["dash"] = 1
        slim = {x: r.get(x) for x in bp.CAMPOS_JS}
        casos.append([slim, inner_html[vol]]); claves.append((k, r.get("distance_class"), round(vrp, 3), cd, dt))
pred = bp.correr_node(casos)
detalle = collections.defaultdict(list)
for (k, dc, vrp, cd, dt), p in zip(claves, pred):
    if p[4]:
        ours[k]["tablero"] = 1
    detalle[k].append((dt, dc, vrp, None if cd is None else round(cd, 1), p[4]))

lat = json.load(open(RAIZ / "data" / "audit_continuous" / "latest.json", encoding="utf-8"))
print("ventana", win, "| latest.json ventana", lat["window"], "generado", lat["generated_utc"])
for s in aw.SENSORS:
    ks = [k for k in mir if k[1] == s and k[0] in aw.VOLS]
    n = len(ks)
    c = sum(ours[k]["crater"] for k in ks if k in ours); d_ = sum(ours[k]["dash"] for k in ks if k in ours)
    t = sum(ours[k]["tablero"] for k in ks if k in ours)
    print("%-8s noches alerta %3d | crater %5.1f %% | dash %5.1f %% | TABLERO (node) %5.1f %% | latest.json crater %s dash %s" % (
        s, n, 100 * c / n if n else 0, 100 * d_ / n if n else 0, 100 * t / n if n else 0,
        lat["recall"][s]["recall_crater_pct"], lat["recall"][s]["recall_dash_pct"]))
print("\nNoches de alerta que la vara 'crater' da por detectadas y el TABLERO no publica:")
for k in sorted(mir):
    if k in ours and ours[k]["crater"] and not ours[k]["tablero"]:
        print("  %-18s %-8s %s MIROVA %.2f MW | records: %s" % (k[0], k[1], k[2], mir[k], [x for x in detalle[k] if x[2] and x[2] > 0][:4]))
