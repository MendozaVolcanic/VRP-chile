# -*- coding: utf-8 -*-
"""F3 R5b. Filas del consolidado del snapshot (2026-10-05) que ya no estan en latest_consolidado.csv
(2026-10-09), antes del corte del snapshot. P1: si el remoto perdio filas, aparecen aca. P2: control: las
filas del snapshot que si estan deben ser la gran mayoria (si da 0 coincidencias, la clave esta mal)."""
import sys, collections
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "scripts")); sys.path.insert(0, str(RAIZ))
from referencia_mirova_unificada import leer_pasadas, SNAP_CONS
snap = leer_pasadas(SNAP_CONS, "CONS", "snap"); viva = leer_pasadas(RAIZ / "latest_consolidado.csv", "CONS", "viva")
def k(f): return (f["volcano"], f["sensor_bucket"], f["fecha_utc"][:16])
kv = {k(f): f for f in viva}
falt = [f for f in snap if k(f) not in kv]
print("snapshot %d filas, en latest %d, faltan %d" % (len(snap), len(snap) - len(falt), len(falt)))
print("por tipo:", dict(collections.Counter(f["tipo"] for f in falt)))
print("por mes:", dict(sorted(collections.Counter(f["fecha_utc"][:7] for f in falt).items())))
for f in [x for x in falt if x["tipo"].startswith("ALERTA")][:40]:
    print("  ", f["fecha_utc"][:16], f["volcano"], f["sensor_raw"], f["tipo"], f["vrp_mw"], f["dist_km"])
cambio = [(f, kv[k(f)]) for f in snap if k(f) in kv and kv[k(f)]["tipo"] != f["tipo"]]
print("misma pasada con tipo distinto:", len(cambio), [(a["fecha_utc"][:16], a["volcano"], a["tipo"], b["tipo"]) for a, b in cambio[:10]])
