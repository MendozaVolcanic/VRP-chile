# Verificador adenda K: duracion de los jobs reproc de las corridas que la adenda cita como costo (§4).
# Lee gh api (jobs JSON por stdin de un archivo por run). Uso: python p5_costos.py <run_id>.json ...
import json, sys, collections, re
from datetime import datetime
def t(s): return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")
for f in sys.argv[1:]:
    jobs = json.load(open(f, encoding="utf-8"))
    por = collections.defaultdict(list); tot = 0.0
    for j in jobs:
        if not j.get("started_at") or not j.get("completed_at") or not j["name"].startswith("reproc"):
            continue
        m = (t(j["completed_at"]) - t(j["started_at"])).total_seconds() / 60
        brazo = "diurno" if "_on" in j["name"] else ("control" if "control" in j["name"] else "?")
        por[brazo].append(m); tot += m
    print(f, "| jobs reproc", sum(len(v) for v in por.values()), "| horas de runner %.1f" % (tot / 60))
    for b, v in sorted(por.items()):
        v.sort(); print("   %-8s n %3d | min %.1f | mediana %.1f | max %.1f" % (b, len(v), v[0], v[len(v)//2], v[-1]))
