#!/usr/bin/env python3
"""V3: el 'dash' del audit (summit/None + centroide en inner, l. 415-420) es un predicado RECONSTRUIDO.
Se compara, por noche con alerta de MIROVA, contra el predicado real del tablero ejecutado con node (banco_paridad).
P1: si la reconstruccion fuera fiel, las dos columnas coinciden en todas las noches; se cuentan discordancias.
P2: n impreso; control: el banco de node no puede dar todo 0 (se imprime cuantas noches publica)."""
import json, os, sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
AQUI = Path(__file__).resolve().parent; REPO = AQUI.parents[2]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts")); sys.stdout.reconfigure(encoding="utf-8")
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import auto_audit_weekly as aw, banco_paridad as bp
hoy = datetime(2026, 10, 19).date(); win = ((hoy - timedelta(days=60)).isoformat(), hoy.isoformat())
coords = aw._coords_por_volcan(); inner = bp.inner_desde_html()
mir = {}
for a in aw.alertas_mirova(str(AQUI / "ref_fresca/registro_vrp_consolidado.csv"), str(AQUI / "ref_fresca/registro_vrp_ocr.csv"), str(AQUI / "historico_combinado.csv")):
    dt = a["fecha_utc"] or ""
    if not (win[0] <= dt[:10] <= win[1]) or a["sensor_bucket"] not in aw.SENSORS: continue
    ll = coords[a["volcano"]]
    if aw.es_pasada_diurna_descartada(a["sensor_bucket"], ll[0], ll[1], datetime.fromisoformat(dt).replace(tzinfo=timezone.utc)): continue
    mir[(a["volcano"], a["sensor_bucket"], dt[:10])] = 1
recs = bp.cargar_nuestros(coords, inner, win)
node_pub = defaultdict(int)
for r in recs: node_pub[(r["vol"], r["b"], r["noche"])] |= r["pub"]
dash = set()
for vol in aw.VOLS:
    for r in json.load(open(REPO / "data/mirova_equivalent" / f"{vol}.json", encoding="utf-8"))["records"]:
        dt = r.get("datetime_utc")
        if not (dt and win[0] <= dt[:10] <= win[1]): continue
        pc = r.get("primary_cluster") or {}; v = pc.get("vrp_mw") or 0; c = pc.get("centroid_dist_km")
        if 0 < v <= aw.CAP and c is not None and c <= aw.INNER[vol] and r.get("distance_class") in (None, "summit"):
            dash.add((vol, aw.our_bucket(r["sensor"]), dt[:10]))
for s in aw.SENSORS:
    ks = [k for k in mir if k[1] == s and k[0] in aw.VOLS]
    a = sum(k in dash for k in ks); b = sum(node_pub[k] for k in ks)
    disc = [(k, k in dash, node_pub[k]) for k in ks if (k in dash) != bool(node_pub[k])]
    print(f"{s}: noches_alerta={len(ks)} dash_audit={a} publica_node={b} discordantes={len(disc)}")
    for d in sorted(disc)[:12]: print("   ", d)
