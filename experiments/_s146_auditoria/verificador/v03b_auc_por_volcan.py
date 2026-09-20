# -*- coding: utf-8 -*-
"""V-03b: AUC de test1_k_observed DENTRO de cada volcan y sensor (camino propio: estratificar en vez de barajar).
(1) roto? se imprime n_pos/n_neg; estratos con <15 en una clase = SIN DATO. (2) muerto? el AUC global se recalcula y debe repetir 0,762."""
import io, sys, datetime as dt
from vlib import *
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
INNER = {"Lastarria": 3, "PlanchonPeteroa": 3, "Copahue": 4, "Tupungatito": 7, "PuyehueCordonCaulle": 20}
def auc(pos, neg):
    import bisect
    s = sorted(neg); t = 0.0
    for x in pos:
        lo = bisect.bisect_left(s, x); hi = bisect.bisect_right(s, x); t += lo + (hi - lo) / 2
    return t / (len(pos) * len(neg))
D = cargar(); K = set()
for f in referencia(incluir_ocr=False):
    if f["tipo"] != "ALERTA_TERMICA": continue
    d0 = dt.date.fromisoformat(f["fecha"])
    for k in (-1, 0, 1): K.add((f["vol"], str(d0 + dt.timedelta(days=k)), f["b"]))
rows = []
for v in VOLS:
    for r in D[v]:
        f = r["datetime_utc"][:10]
        if not ("2026-01-29" <= f <= "2026-06-25"): continue
        pc = r.get("primary_cluster") or {}
        if (r.get("diag_n_second_pass_recapture") or 0) > 0 and r.get("distance_class") == "summit" and pc.get("centroid_dist_km") is not None and pc["centroid_dist_km"] <= INNER.get(v, 5):
            b = bucket(r["sensor"]); rows.append((v, b, (v, f, b) in K, r.get("test1_k_observed") or 0.0))
print("global", round(auc([x[3] for x in rows if x[2]], [x[3] for x in rows if not x[2]]), 3), "n", len(rows))
pesos = []
for b in ("v375", "v750"):
    for v in VOLS:
        p = [x[3] for x in rows if x[0] == v and x[1] == b and x[2]]; n = [x[3] for x in rows if x[0] == v and x[1] == b and not x[2]]
        if len(p) < 15 or len(n) < 15: print(f"  {b} {v:22s} pos {len(p):4d} neg {len(n):4d} SIN DATO"); continue
        a = auc(p, n); pesos.append((a, len(p) * len(n))); print(f"  {b} {v:22s} pos {len(p):4d} neg {len(n):4d} AUC {a:.3f}")
print("AUC medio dentro de volcan+sensor, ponderado por pares:", round(sum(a * w for a, w in pesos) / sum(w for _, w in pesos), 3), "| estratos:", len(pesos))
