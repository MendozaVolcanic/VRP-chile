# -*- coding: utf-8 -*-
"""Resume filas_V*.jsonl: por ventana y caso, cuantas corridas dan CUMPLE (veredicto global de K, lectura A, regla
original), con intervalo de Wilson al 95 %, y el rango de la reduccion de la suma de P2 por sensor."""
import json, math, collections
from pathlib import Path
def wilson(k, n, z=1.96):
    if n == 0: return (0, 0)
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); w = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - w) / d, (c + w) / d)
G = collections.defaultdict(list)
for f in sorted(Path(__file__).parent.glob("salidas/placebos/filas_V*.jsonl")):
    for l in open(f, encoding="utf-8"):
        x = json.loads(l); G[(x["ventana"], x["caso"])].append(x)
for (v, c), xs in sorted(G.items()):
    k = sum(x["global_K_A"] == "CUMPLE" for x in xs); lo, hi = wilson(k, len(xs))
    red = [[c0 - kk for c0, kk in zip(x["sumaC0_A"], x["sumaK_A"])] for x in xs]
    veto = sum("veto" in (x["global_K_A"] or "") for x in xs)
    print("%s %-10s n %2d | CUMPLE %2d (%.0f %% [%.0f, %.0f]) | veto %2d | reduccion P2 (MODIS, V375, V750) min %s max %s | controles_ok %s" % (
        v, c, len(xs), k, 100 * k / len(xs), 100 * lo, 100 * hi, veto,
        [min(r[i] for r in red) for i in range(3)], [max(r[i] for r in red) for i in range(3)], {x["controles_ok"] for x in xs}))
