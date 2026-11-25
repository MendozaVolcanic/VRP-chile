"""Resumen agrupado por zona con T_hot 600 K (pre-registrado como secundario) y razón VRP_eq 600 K / 1000 K sin anomalía."""
import json, math
from collections import defaultdict
import numpy as np
import comun as C
C.utf8()
regs = [json.loads(x) for x in open(C.AQUI / "resultados.jsonl", encoding="utf-8")]
regs += [json.loads(x) for x in open(C.AQUI / "resultados_posthoc.jsonl", encoding="utf-8")]
idx = defaultdict(dict)
for r in regs:
    if "brazo" in r:
        idx[(r["escena"], r["serie"], r["d"], r["az"], r["T"])][r["brazo"]] = r
print("| comparación | zona | n | r mediana | r p90 | r máx |")
print("|---|---|---|---|---|---|")
for con, sin, serie in (("R-con", "R-sin", "R"), ("T+-con-1", "T-sin", "T+"), ("T+-con-3", "T-sin", "T+"),
                        ("T+-con-10", "T-sin", "T+"), ("T+-con-30", "T-sin", "T+"), ("N-con", "N-sin", "N")):
    for z in (0, 1, 2):
        rs = [v[con]["vrp_min"] / v[sin]["vrp_min"] for k, v in idx.items() if k[1] == serie and k[4] == 600.0
              and con in v and sin in v and v[sin]["zona"] == z and v[con]["vrp_min"] and v[sin]["vrp_min"]]
        if rs:
            print(f"| {con}/{sin} | {z} | {len(rs)} | {np.median(rs):.3f} | {np.percentile(rs, 90):.3f} | {max(rs):.3f} |")
q = [idx[(k[0], k[1], k[2], k[3], 600.0)]["R-sin"]["vrp_min"] / v["R-sin"]["vrp_min"] for k, v in idx.items()
     if k[1] == "R" and k[4] == 1000.0 and "R-sin" in v and (k[0], k[1], k[2], k[3], 600.0) in idx]
print(f"\nVRP_eq mínimo 600 K / 1000 K (brazo R-sin): mediana {np.median(q):.3f}, rango {min(q):.3f} a {max(q):.3f}, n {len(q)}")
