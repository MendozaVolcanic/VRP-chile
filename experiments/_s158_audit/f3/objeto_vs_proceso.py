# -*- coding: utf-8 -*-
"""F3: separar lo del OBJETO (oclusión del cráter profundo) de lo del PROCESO (huella nativa, D17) con el ángulo.
Predicción física: la oclusión por las paredes de Láscar baja la radiancia que ven LOS DOS sistemas, así que
  (a) la magnitud propia de MIROVA (VRP / mediana móvil de 61 días del volcán) cae con el cenit más en Láscar que en
      volcanes sin cráter profundo (PCC, Isluga), y
  (b) la RAZÓN nuestra/MIROVA no cae más en Láscar que en esos otros: el objeto se cancela en la razón.
Si en cambio la razón de Láscar cae más que la de los otros, hay un efecto del proceso que interactúa con el cráter.
Instrumento: (1) si la normalización temporal fallara, la mediana del VRP relativo por volcán no estaría cerca de 1;
se imprime. (2) Se usan los mismos pares (clase 1, VIIRS 375, 2025) que el resto del frente.
Uso: python -B objeto_vs_proceso.py pares_osf2025.csv
"""
import sys
import numpy as np, pandas as pd
d = pd.read_csv(sys.argv[1], parse_dates=["t"])
d = d[(d.pareo == "ok") & (d.b == "V375") & (d.cls == 1)].copy()
d["pub_ok"] = d.pub_ok.astype(str) == "True"
f5 = d.f5.fillna(0); pc = d.pc_vrp.fillna(0)
d["pub"] = np.where(d.pub_ok, np.where(f5 > 0, f5, pc), 0.0)
parts = []
for v, g in d.groupby("vol"):
    g = g.sort_values("t").copy()
    s = g.set_index("t")["VRP_M"]
    g["relM"] = (s / s.rolling("61D", center=True, min_periods=5).median()).values
    parts.append(g)
d = pd.concat(parts)
d["tr"] = pd.cut(d.zen_M, [0, 20, 40, 50, 60, 75])
print("volcán | n | mediana relM (control ~1) | relM por tramo (0-20,20-40,40-50,50-60,60-75) | rho(cenit,relM) | Lhot/px MIROVA por tramo | razón sum pub/sum M por tramo | rho(cenit, pub/M) sólo publicadas")
for v in ["Lascar", "PuyehueCordonCaulle", "Isluga", "Lastarria", "PlanchonPeteroa", "Chaiten"]:
    g = d[d.vol == v]
    rel = [f"{g.relM[g.tr == c].median():.2f}" if (g.tr == c).sum() >= 5 else "--" for c in g.tr.cat.categories]
    lh = [f"{(g.Lhot_M / g.N_M)[g.tr == c].median():.3f}" if (g.tr == c).sum() >= 5 else "--" for c in g.tr.cat.categories]
    rz = [f"{g.pub[g.tr == c].sum() / g.VRP_M[g.tr == c].sum():.2f}" if (g.tr == c).sum() >= 5 else "--" for c in g.tr.cat.categories]
    p = g[g.pub > 0]
    print(f"{v:20s} | {len(g)} | {g.relM.median():.2f} | {' '.join(rel)} | {g.zen_M.corr(g.relM, method='spearman'):+.2f} | {' '.join(lh)} | {' '.join(rz)} | {p.zen_M.corr(p.pub / p.VRP_M, method='spearman'):+.2f}")
