#!/usr/bin/env python3
"""F3: recall del auto-audit (por noche UTC, predicados 'crater' y 'dash' de auto_audit_weekly) partido
por régimen (C0 noche < 2026-09-18, K desde ahí), ventana de hoy 2026-08-20..2026-10-19.
Replica main() pasos 1-2 de scripts/auto_audit_weekly.py con sus funciones; no escribe nada en data/.
P1: si K perdiera noches, recall_K < recall_C0 y se vería. P2: n_noches = 0 -> SIN DATO (None)."""
import sys, os, json
from collections import defaultdict
from datetime import datetime, timezone
sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts")); sys.path.insert(0, ROOT)
import auto_audit_weekly as aw  # noqa
win = ("2026-08-20", "2026-10-19")
inw = lambda dt: bool(dt) and win[0] <= dt[:10] <= win[1]
coords = aw._coords_por_volcan()
mir = defaultdict(float)
for a in aw.alertas_mirova():
    dt = a["fecha_utc"] or ""
    if not inw(dt) or a["sensor_bucket"] not in aw.SENSORS: continue
    ll = coords.get(a["volcano"])
    try: o = datetime.fromisoformat(dt).replace(tzinfo=timezone.utc)
    except ValueError: o = None
    if ll and o and aw.es_pasada_diurna_descartada(a["sensor_bucket"], ll[0], ll[1], o): continue
    k = (a["volcano"], a["sensor_bucket"], dt[:10]); mir[k] = max(mir[k], a["vrp_mw"] or 0.0)
ours = defaultdict(lambda: {"crater": [], "dash": []}); vistos = set()
for vol in aw.VOLS:
    for rec in json.load(open(os.path.join(ROOT, "data", "mirova_equivalent", vol + ".json"), encoding="utf-8"))["records"]:
        dt = rec.get("datetime_utc")
        if not inw(dt): continue
        b = aw.our_bucket(rec.get("sensor", ""))
        if b is None: continue
        vistos.add((vol, b, dt[:10]))
        pc = rec.get("primary_cluster") or {}; vrp = pc.get("vrp_mw") or 0.0; cd = pc.get("centroid_dist_km")
        if (0 < vrp <= aw.CAP) and cd is not None and cd <= aw.INNER[vol]:
            ours[(vol, b, dt[:10])]["crater"].append(vrp)
            if not rec.get("distance_class") or rec.get("distance_class") == "summit":
                ours[(vol, b, dt[:10])]["dash"].append(vrp)
res = {"todo": aw.recall_por_sensor(mir, vistos, ours, aw.SENSORS, set(aw.VOLS))}
for reg, f in (("C0", lambda d: d < "2026-09-18"), ("K", lambda d: d >= "2026-09-18")):
    m = {k: v for k, v in mir.items() if f(k[2])}
    res[reg] = aw.recall_por_sensor(m, vistos, ours, aw.SENSORS, set(aw.VOLS))
for k, v in res.items():
    print(k, json.dumps(v))
# noches K perdidas (crater) V375 y MODIS, con VRP MIROVA
perd = sorted([(k, round(v, 3)) for k, v in mir.items() if k[2] >= "2026-09-18" and k in vistos and not ours.get(k, {}).get("crater")])
print("noches K con alerta y sin crater:", perd)
res["perdidas_K"] = perd
json.dump(res, open(os.path.join(os.path.dirname(__file__), "recall_por_regimen.json"), "w", encoding="utf-8"), indent=1)
