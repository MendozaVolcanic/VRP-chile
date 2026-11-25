"""Área caliente equivalente del foco en el umbral (f x 0,5625 km2, el área nadir del píxel M que usa el coeficiente),
por zona de la caja y temperatura, brazo sin anomalía de la serie R."""
import json
import numpy as np
import comun as C
C.utf8()
regs = [json.loads(x) for x in open(C.AQUI / "resultados.jsonl", encoding="utf-8")]
print("| T_hot K | zona | n | VRP_eq mín mediana (MW) | rango (MW) | f mediana | área caliente mediana (m2) |")
print("|---|---|---|---|---|---|---|")
for T in (1000.0, 600.0):
    for z in (2, 1, 0):
        x = [r for r in regs if r.get("brazo") == "R-sin" and r["T"] == T and r["zona"] == z and r.get("vrp_min")]
        v = np.array([r["vrp_min"] for r in x]); f = np.array([r["f"] for r in x])
        print(f"| {T:.0f} | {z} | {len(x)} | {np.median(v):.2f} | {v.min():.2f} a {v.max():.2f} | {np.median(f):.2e} | "
              f"{np.median(f) * 562500:.0f} |".replace(".", ","))
