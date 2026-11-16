#!/usr/bin/env python
"""V2 S175: F2-204 por otro camino. De los V375 publicados que el tablero marca «MIROVA confirmo» (+-60 min),
los que no tienen fila de alerta de su propia pasada (+-120 s): cuantos tienen RUTINA propia, a que distancia en
minutos esta la alerta que los confirma, y cuantos de los 647 vienen de otra plataforma en la misma noche.
P1: control positivo: los conteos 2225 y 647 del auditor tienen que reaparecer (si no, el script esta mal).
P2: el conteo se hace sobre data/mirova/<vol>.json (lo que carga index.html l. 992); un archivo vacio aborta.
Uso: python v2_conf204.py <arbol> <ini> <fin> <salida>"""
import bisect, collections, json, os, sys
from datetime import datetime, timezone
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ARBOL = Path(sys.argv[1]).resolve(); INI, FIN, OUT = sys.argv[2], sys.argv[3], Path(sys.argv[4])
sys.path.insert(0, str(ARBOL / "scripts")); sys.path.insert(0, str(ARBOL)); os.environ["VRP_PROFILE"] = "mirova_equivalent"
import banco_paridad as bp
def ms(s): return datetime.fromisoformat(str(s).replace(" ", "T")[:16]).replace(tzinfo=timezone.utc).timestamp()
recs = [r for r in bp.cargar_nuestros(bp._coords_por_volcan(), bp.inner_desde_html(), (INI, FIN)) if r["b"] == "VIIRS375" and r["pub"]]
alert, rut = {}, {}
c = collections.Counter(); off = []
for vol in bp.VOLS:
    mir = json.load(open(ARBOL / "data" / "mirova" / f"{vol}.json", encoding="utf-8"))["records"]
    assert len(mir) > 100, vol
    a, ru = [], []
    for m in mir:
        if str(m.get("sensor") or m.get("Sensor") or "").upper() != "VIIRS375": continue
        cls = str(m.get("clasificacion") or m.get("Clasificacion") or "").upper()
        try: v = float(m.get("VRP_MW") if m.get("VRP_MW") is not None else (m.get("vrp_mw") or 0))
        except (TypeError, ValueError): v = 0.0
        t = ms(m["datetime_utc"])
        if cls == "RUTINA": ru.append(t)
        elif cls != "NULO" and v > 0: a.append((t, v))
    alert[vol] = sorted(a); rut[vol] = sorted(ru)
dist_noche = collections.Counter()
for r in recs:
    t = r["dt"].timestamp(); a = alert[r["vol"]]; ts = [x[0] for x in a]
    cerca = a[bisect.bisect_left(ts, t - 3600):bisect.bisect_right(ts, t + 3600)]
    if not cerca: continue
    c["confirmado"] += 1
    if any(abs(x - t) <= 120 for x, _ in cerca): continue
    c["sin_alerta_propia"] += 1
    if any(abs(x - t) <= 120 for x in rut[r["vol"]]): c["con_RUTINA_propia"] += 1
    mn = min(abs(x - t) for x, _ in cerca) / 60; off.append(mn)
    if mn <= 20: c["alerta_a_<=20min"] += 1
    elif mn <= 45: c["alerta_a_20-45min"] += 1
    else: c["alerta_a_45-60min"] += 1
    if r["z"] is not None and r["z"] >= 50: c["de_ellos_z>=50"] += 1
    dist_noche[r["sensor"]] += 1
off.sort()
L = [f"V375 publicados {len(recs)} | {dict(c)}", f"por plataforma de los 647: {dict(dist_noche)}",
     f"minutos a la alerta mas cercana: mediana {off[len(off)//2]:.1f} min, p10 {off[len(off)//10]:.1f}, p90 {off[9*len(off)//10]:.1f}"]
OUT.write_text("\n".join(L) + "\n", encoding="utf-8"); print("\n".join(L))
