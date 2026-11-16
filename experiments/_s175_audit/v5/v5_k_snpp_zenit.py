# -*- coding: utf-8 -*-
"""V5-K: 305, causa. ¿Las pasadas SNPP sin fila de MIROVA se concentran en cenit alto (borde de franja)? Si MIROVA solo lista pasadas con buena geometria,
las sin-fila tendrian cenit mayor. Preg 1: si la causa fuera geometria, la mediana de cenit de las sin-fila seria claramente mayor que la de las con-fila.
Preg 2: control: lo mismo en NOAA-20, donde casi todas tienen fila. Universo: recs VIIRS375 2026-06-11..2026-11-07, r['z'] del banco (sensor_zenith_deg)."""
import bisect, collections, os, pickle, statistics as st, sys
from datetime import datetime, timezone
sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8")
B = pickle.load(open(r"C:\Users\nmend\vrp-temporales\s175_audit\f5\f5_base.pkl", "rb"))
idx = collections.defaultdict(list)
for f in B["filas"]:
    t = datetime.strptime(f["fecha_utc"][:19] if len(f["fecha_utc"]) >= 19 else f["fecha_utc"][:16] + ":00", "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    idx[(f["volcano"], f["sensor_bucket"])].append(t)
for v in idx.values(): v.sort()
z = collections.defaultdict(lambda: {"con": [], "sin": []})
for r in B["recs"]:
    if not ("2026-06-11" <= r["noche"] <= "2026-11-07") or r["b"] != "VIIRS375" or r.get("z") is None:
        continue
    ts = idx[(r["vol"], r["b"])]; i = bisect.bisect_left(ts, r["dt"])
    d = min((abs((ts[j] - r["dt"]).total_seconds()) for j in (i - 1, i) if 0 <= j < len(ts)), default=1e9)
    z[r["sensor"]]["con" if d <= 120 else "sin"].append(r["z"])
for s, d in sorted(z.items()):
    q = lambda l: (round(st.median(l), 1), round(sorted(l)[int(0.9 * len(l))], 1)) if l else None
    print(s, "con fila n", len(d["con"]), "mediana/p90 cenit", q(d["con"]), "| sin fila n", len(d["sin"]), "mediana/p90 cenit", q(d["sin"]))
# por volcan en SNPP
pv = collections.defaultdict(lambda: [0, 0])
for r in B["recs"]:
    if not ("2026-06-11" <= r["noche"] <= "2026-11-07") or r["sensor"] != "VIIRS_SNPP":
        continue
    ts = idx[(r["vol"], r["b"])]; i = bisect.bisect_left(ts, r["dt"])
    d = min((abs((ts[j] - r["dt"]).total_seconds()) for j in (i - 1, i) if 0 <= j < len(ts)), default=1e9)
    pv[r["vol"]][0] += d <= 120; pv[r["vol"]][1] += 1
print("SNPP con fila / pasadas por volcan:", {v: f"{a}/{b}" for v, (a, b) in sorted(pv.items())})
