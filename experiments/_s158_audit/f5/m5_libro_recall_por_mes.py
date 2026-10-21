# -*- coding: utf-8 -*-
"""F5 medicion 5. libro_de_cuentas.r_recall_v750_dash (copiado sin cambio de logica) partido por MES de la noche de MIROVA.
Pregunta: el 85,06 -> 75,44 de hoy, ¿es el detector K (desde la observacion del 2026-09-18) o el instrumento?
Instrumento 1: la misma funcion en un mes sin cambio de detector tiene que dar lo de siempre. Instrumento 2: cuenta
noches de MIROVA por mes; un mes con 0 noches es SIN DATO, no 0 %."""
import collections, io, json, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = "D:/vrp-trabajo/temporales/s158_d17"
sys.path.insert(0, os.path.join(ROOT, "experiments"))
from _s126_lib import VENTS, bucket, cargar_mirova
mir, diurnas = cargar_mirova(("2026-01-01", "2026-12-31"))
nuestras = set()
for vol in VENTS:
    pth = os.path.join(ROOT, "data", "mirova_equivalent", vol + ".json")
    if not os.path.exists(pth):
        continue
    for r in json.load(open(pth, encoding="utf-8"))["records"]:
        if bucket(r.get("sensor")) != "v750":
            continue
        v = r.get("vrp_mw") or 0
        if not (v > 0 or r.get("triggered_test1") is True):
            continue
        if v == 0 and r.get("discarded_reason") and not r.get("triggered_test1"):
            continue
        dc = r.get("distance_class")
        if dc == "far" or (dc != "summit" and not ((r.get("vrp_vent_mw") or 0) > 0)):
            continue
        nuestras.add((vol, r.get("datetime_utc", "")[:10]))
tot, ac = collections.Counter(), collections.Counter()
for vol in VENTS:
    for (d, b) in (mir.get(vol) or {}):
        if b != "v750":
            continue
        m = d[:7]; tot[m] += 1; ac[m] += (vol, d) in nuestras
print("VENTS:", VENTS)
print("mes | noches MIROVA V750 | con publicacion nuestra | %")
for m in sorted(tot):
    print("  %s %4d %4d %6.1f" % (m, tot[m], ac[m], 100 * ac[m] / tot[m]))
T, A = sum(tot.values()), sum(ac.values())
pre = [m for m in tot if m < "2026-09"]; post = [m for m in tot if m >= "2026-09"]
print("total %d %d %.2f | ene-ago %.2f (n %d) | sep-oct %.2f (n %d)" % (T, A, 100 * A / T,
      100 * sum(ac[m] for m in pre) / sum(tot[m] for m in pre), sum(tot[m] for m in pre),
      100 * sum(ac[m] for m in post) / sum(tot[m] for m in post), sum(tot[m] for m in post)))
