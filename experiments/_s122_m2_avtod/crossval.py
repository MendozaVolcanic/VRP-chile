# M2 (S122) — cross-validation VRP Chile vs AVTOD (Reath et al. 2019), 2º ground truth.
#
# AVTOD = ASTER Volcanic Thermal Output Database (90 m, manual, grupo Pritchard/Coppola),
# INDEPENDIENTE de MIROVA. Su métrica es °C SOBRE FONDO (no VRP en watts); el máx °C-AB fue
# el mejor análogo del VRP de MIROVA (r²=0.87, Fig 6 del paper).
#
# CAVEAT TEMPORAL (no ocultar): el máx AVTOD es 2000-2017 e incluye erupciones históricas
# (Chaitén 2008, PCC 2011, Copahue 2012); nuestra serie es 2025-26. Comparable solo para la
# salida térmica PERSISTENTE (lava lakes Villarrica/Llaima, Láscar). Por eso se reporta el
# RANKING y la corroboración cualitativa, NO una correlación ingenua sobre 11 puntos.
#
# Magnitud nuestra = primary_cluster.vrp_mw en records summit (regla A10: pc.vrp_mw, NO
# record.vrp_mw que es la suma scene-wide). p95 = robusto frente a outliers path-D.
import json
import io
import sys
import csv
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]

lines = [l for l in open(REPO / "data/mirova_reference/avtod_reath2019_chile.csv",
                        encoding="utf-8") if not l.startswith("#")]
avtod = {r["volcano"]: r for r in csv.DictReader(lines)}

rows = []
for vol, a in avtod.items():
    p = REPO / "data/mirova_equivalent" / f"{vol}.json"
    if not p.exists():
        rows.append((vol, a, None, None, 0))
        continue
    d = json.load(open(p, encoding="utf-8"))
    recs = d["records"] if isinstance(d, dict) and "records" in d else d
    vals = [(r.get("primary_cluster") or {}).get("vrp_mw") or 0
            for r in recs if r.get("distance_class") == "summit"]
    vals = sorted(v for v in vals if v > 0)
    if vals:
        rows.append((vol, a, round(vals[-1], 1),
                     round(vals[int(len(vals) * 0.95)], 2), len(vals)))
    else:
        rows.append((vol, a, 0, 0, 0))

rows.sort(key=lambda x: -float(x[1]["max_temp_above_bkg_c"]))
print("Cross-validation VRP Chile (2025-26) vs AVTOD ASTER (2000-2017)\n")
print(f'{"Volcán":<22}{"AVTOD°C":>8} {"clasif":>10}  |  {"max":>7} {"p95":>7} {"n":>5}')
print("-" * 74)
for vol, a, mx, p95, n in rows:
    sat = "*" if a["saturated"] == "yes" else " "
    print(f'{vol:<22}{a["max_temp_above_bkg_c"]+sat:>8} {a["classification"]:>10}  |  '
          f'{"NA" if mx is None else mx:>7} {"NA" if p95 is None else p95:>7} {n:>5}')
print("\n* = saturado ASTER (>=120 °C, lava lake). AVTOD max incluye erupciones históricas.")

# Correlación de RANKING (Spearman a mano) — solo informativa, con el caveat de arriba.
valid = [(float(a["max_temp_above_bkg_c"]), p95) for _, a, _, p95, n in rows if p95 and n > 50]
if len(valid) >= 5:
    def rank(xs):
        s = sorted(range(len(xs)), key=lambda i: xs[i])
        r = [0] * len(xs)
        for pos, i in enumerate(s):
            r[i] = pos + 1
        return r
    ra, rb = rank([v[0] for v in valid]), rank([v[1] for v in valid])
    n = len(valid)
    d2 = sum((ra[i] - rb[i]) ** 2 for i in range(n))
    rho = 1 - 6 * d2 / (n * (n * n - 1))
    print(f"\nSpearman ranking (n={n}, INFORMATIVO — ventanas temporales distintas): rho = {rho:.2f}")
