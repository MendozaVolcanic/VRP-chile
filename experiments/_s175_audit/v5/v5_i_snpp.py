# -*- coding: utf-8 -*-
"""V5-I: 305. ¿La tabla de MIROVA no lista la mayoria de pasadas de Suomi NPP, o es convencion de hora?
Preg 1: si fuera solo convencion de hora (offset de minutos), las pasadas SNPP sin fila a +-120 s tendrian fila de MIROVA del mismo volcan/bucket a
2..20 min; si es cobertura real, la fila mas cercana esta a decenas de minutos (otro satelite) o a horas. Preg 2: control: NOAA-20, que el auditor
muestra con ~10-20 % sin fila: su distribucion de |dt| al vecino debe verse distinta de la de SNPP (si el instrumento fuera ciego daria igual).
Universo: recs del banco 2026-06-11..2026-11-07 (f5_base.pkl) contra TODAS las filas de la referencia unificada (CONS+OCR, B['filas']) del mismo (volcan,bucket)."""
import bisect, collections, os, pickle, sys
from datetime import datetime, timezone
sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"C:\Users\nmend\vrp-temporales\s175_audit\f5\root"
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import banco_paridad as bp
B = pickle.load(open(r"C:\Users\nmend\vrp-temporales\s175_audit\f5\f5_base.pkl", "rb"))
idx = collections.defaultdict(list)
for f in B["filas"]:
    t = datetime.strptime(f["fecha_utc"][:19] if len(f["fecha_utc"]) >= 19 else f["fecha_utc"][:16] + ":00", "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    idx[(f["volcano"], f["sensor_bucket"])].append(t)
for v in idx.values(): v.sort()
print("TOL_S de la base:", bp.TOL_S)
res = collections.defaultdict(lambda: collections.Counter())
for r in B["recs"]:
    if not ("2026-06-11" <= r["noche"] <= "2026-11-07"):
        continue
    base = r["sensor"].replace("_750", "")
    ts = idx.get((r["vol"], r["b"]), [])
    i = bisect.bisect_left(ts, r["dt"])
    cand = [ts[j] for j in (i - 1, i) if 0 <= j < len(ts)]
    dmin = min((abs((t - r["dt"]).total_seconds()) for t in cand), default=1e9)
    k = (base, r["b"])
    res[k]["n"] += 1
    if dmin <= bp.TOL_S:
        res[k]["con_fila_120s"] += 1
    else:
        res[k]["sin_fila"] += 1
        m = dmin / 60
        res[k]["vecina_2_20min" if m <= 20 else "vecina_20_60min" if m <= 60 else "vecina_mas_1h"] += 1
for (s, b), c in sorted(res.items()):
    n = c["n"]
    print(f"{s:14s} {b:9s} n {n:5d} con_fila {c['con_fila_120s']:5d} ({100*c['con_fila_120s']/n:4.0f}%) sin_fila {c['sin_fila']:5d} | de las sin fila: 2-20 min {c['vecina_2_20min']:4d}, 20-60 min {c['vecina_20_60min']:4d}, >1 h {c['vecina_mas_1h']:4d}")
# etiqueta por satelite y mes (denominador de negativos)
lab = collections.defaultdict(collections.Counter)
for r in B["recs"]:
    lab[(r["sensor"], r["noche"][:7])][r["lab"]] += 1
print("\nneg_limpio / pasadas, por satelite (VIIRS 375) y mes:")
for s in ("VIIRS_SNPP", "VIIRS_NOAA20", "VIIRS_NOAA21"):
    print(s, {m: f"{lab[(s,m)]['neg_limpio']}/{sum(lab[(s,m)].values())}" for m in ("2026-06", "2026-07", "2026-08", "2026-09", "2026-10")})
