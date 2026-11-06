"""S167: reparto del tiempo de un job del NRT entre buscar y bajar gránulos y procesarlos, y gránulos procesados.

POR QUÉ: si la sombra corriera en el mismo job compartiendo búsqueda y gránulos, sólo sumaría el proceso; este reparto
dice cuánto pesa cada parte. Lee el log de un job (gh api repos/.../actions/jobs/<id>/logs).

Uso: python experiments/_s167_sombra/fases.py <log del job>
"""
import re
import sys
from collections import Counter
from datetime import datetime


def ts(l):
    return datetime.fromisoformat(l[:26] + "+00:00") if re.match(r"\d{4}-\d\d-\d\dT", l) else None


lines = open(sys.argv[1], encoding="utf-8", errors="replace").read().splitlines()
days, cur = [], None
gran = Counter()
for l in lines:
    m = re.search(r"  ([A-Z0-9_]+): kept (\d+) of (\d+) granules", l)
    if m:
        gran[m.group(1)] += int(m.group(2))
    t = ts(l)
    if t is None:
        continue
    if "AUTH_START" in l:
        if cur:
            days.append(cur)
        cur = {"ini": t, "last_dl": t, "end": t}
    elif cur:
        if "DOWNLOAD_DONE" in l or "SEARCH_" in l or "DOWNLOAD_START" in l:
            cur["last_dl"] = t
        if "Cleaned up" in l:
            cur["end"] = t
            days.append(cur)
            cur = None
if cur:
    days.append(cur)
tb = sum((d["last_dl"] - d["ini"]).total_seconds() for d in days)
tp = sum((d["end"] - d["last_dl"]).total_seconds() for d in days)
print(f"{len(days)} dias  busqueda+descarga {tb / 60:.1f} min  proceso {tp / 60:.1f} min")
v375 = sum(n for k, n in gran.items() if k.startswith("VIIRS") and not k.endswith("_750"))
v750 = sum(n for k, n in gran.items() if k.endswith("_750"))
modis = sum(n for k, n in gran.items() if k.startswith("MODIS"))
print(f"granulos nocturnos procesados: {sum(gran.values())} (VIIRS 375 {v375}, VIIRS 750 {v750}, MODIS {modis})")
print("por plataforma:", dict(sorted(gran.items())))
