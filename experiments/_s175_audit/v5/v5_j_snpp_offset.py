# -*- coding: utf-8 -*-
"""V5-J: 305, segundo camino. Histograma del desfase (hora de la fila MIROVA mas cercana - hora de NUESTRA pasada) en minutos, -30..+30, por satelite.
Preg 1: si 'MIROVA no lista SNPP' fuera en realidad convencion de hora, SNPP mostraria un pico en un desfase fijo (p.ej. +-6 min = un gránulo); si es cobertura,
el histograma de SNPP es plano fuera de 0. Preg 2: control: NOAA-20/21 deben mostrar pico en 0 (+-2 min) y fondo bajo; MODIS idem.
Cuenta TODAS las filas de MIROVA (no solo la mas cercana) en una ventana +-30 min, mismo volcan y bucket, por cada pasada nuestra."""
import collections, os, pickle, sys
from datetime import datetime, timezone
sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8")
B = pickle.load(open(r"C:\Users\nmend\vrp-temporales\s175_audit\f5\f5_base.pkl", "rb"))
idx = collections.defaultdict(list)
for f in B["filas"]:
    t = datetime.strptime(f["fecha_utc"][:19] if len(f["fecha_utc"]) >= 19 else f["fecha_utc"][:16] + ":00", "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    idx[(f["volcano"], f["sensor_bucket"])].append(t)
h = collections.defaultdict(collections.Counter); n = collections.Counter()
for r in B["recs"]:
    if not ("2026-06-11" <= r["noche"] <= "2026-11-07") or r["b"] != "VIIRS375":
        continue
    n[r["sensor"]] += 1
    for t in idx.get((r["vol"], r["b"]), []):
        d = (t - r["dt"]).total_seconds() / 60
        if -30 <= d <= 30:
            h[r["sensor"]][round(d / 2) * 2] += 1   # bins de 2 min
print("pasadas por satelite (VIIRS375):", dict(n))
bins = list(range(-30, 31, 2))
print("bin(min): " + " ".join(f"{b:+4d}" for b in bins))
for s in ("VIIRS_SNPP", "VIIRS_NOAA20", "VIIRS_NOAA21"):
    print(f"{s[6:]:7s}: " + " ".join(f"{100*h[s][b]/n[s]:4.0f}" for b in bins), " (% de pasadas con una fila MIROVA en ese desfase)")
