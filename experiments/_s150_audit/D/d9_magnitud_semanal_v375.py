# -*- coding: utf-8 -*-
"""S150 auditor D, sonda 9: la auditoria semanal mide la magnitud de VIIRS 375 con pc.vrp_mw; el operador ve
el nucleo F5 (mirovaEqVrpDisplay, A10 matiz S132). Recalculo la razon mediana por volcan con las dos.
PREGUNTA 1: si la semanal midiera otra magnitud que la del tablero, se veria? Si: dos columnas lado a lado.
PREGUNTA 2 (control): la columna pc tiene que reproducir magnitud_ratio_by_vol de latest.json en los volcanes
donde V375 domina (no lo reproduce exacto porque la semanal mezcla los tres sensores).
Uso: python d9_magnitud_semanal_v375.py 2026-08-06 2026-10-05"""
import collections, io, json, statistics as st, sys
from datetime import datetime, timezone
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "scripts"))
import auto_audit_weekly as aw, banco_paridad as bp
from pipeline.mirova_csv_loader import load_mirova_alertas
win = tuple(sys.argv[1:3]); coords = aw._coords_por_volcan(); inner = bp.inner_desde_html()
mir = collections.defaultdict(float)
for a in load_mirova_alertas(cons_path=aw.CONS, ocr_path=aw.OCR):
    dt = a["fecha_utc"] or ""
    if a["sensor_bucket"] != "VIIRS375" or not (win[0] <= dt[:10] <= win[1]): continue
    lat, lon = coords[a["volcano"]]
    if aw.es_pasada_diurna_descartada("VIIRS375", lat, lon, datetime.fromisoformat(dt).replace(tzinfo=timezone.utc)): continue
    k = (a["volcano"], dt[:10]); mir[k] = max(mir[k], a["vrp_mw"] or 0)
casos, cl = [], []
for vol in aw.VOLS:
    for r in json.load(open(RAIZ / "data" / "mirova_equivalent" / f"{vol}.json", encoding="utf-8"))["records"]:
        dt = r.get("datetime_utc") or ""
        if aw.our_bucket(r.get("sensor", "")) != "VIIRS375" or not (win[0] <= dt[:10] <= win[1]): continue
        casos.append([{k: r.get(k) for k in bp.CAMPOS_JS}, inner[vol]]); cl.append((vol, dt[:10], r))
pred = bp.correr_node(casos)
pc_n, disp_n = collections.defaultdict(float), collections.defaultdict(float)
for (vol, d, r), p in zip(cl, pred):
    pc = r.get("primary_cluster") or {}; v = pc.get("vrp_mw") or 0; cd = pc.get("centroid_dist_km")
    if 0 < v <= aw.CAP and cd is not None and cd <= aw.INNER[vol] and (not r.get("distance_class") or r.get("distance_class") == "summit"):
        pc_n[(vol, d)] = max(pc_n[(vol, d)], v)
    if p[4]: disp_n[(vol, d)] = max(disp_n[(vol, d)], p[3])
lat = json.load(open(RAIZ / "data" / "audit_continuous" / "latest.json", encoding="utf-8"))["magnitud_ratio_by_vol"]
print("VIIRS 375, ventana", win, "| razon mediana por volcan (noches con alerta y con publicacion)")
for vol in aw.VOLS:
    a = [pc_n[k] / mir[k] for k in mir if k[0] == vol and pc_n.get(k)]; b = [disp_n[k] / mir[k] for k in mir if k[0] == vol and disp_n.get(k)]
    if a or b:
        print("  %-20s n %3d | con pc.vrp_mw (semanal) %5.2f | con el nucleo del tablero %5.2f | latest.json (3 sensores) %s" % (
            vol, len(a), st.median(a) if a else float("nan"), st.median(b) if b else float("nan"), lat.get(vol)))
