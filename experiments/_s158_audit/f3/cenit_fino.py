# -*- coding: utf-8 -*-
"""F3: conteo y energía por tramo fino de cenit, VIIRS 375, clase 1 del OSF 2025 (pares de descomp_osf2025.py).
Pregunta: ¿el déficit de conteo existe ya a nadir (detección) o aparece con el ángulo (huella nativa que crece, D17)?
Predicción D17: nuestro n cae con el cenit y el de MIROVA no (su grilla de 375 m reparte la huella oblicua en varias
celdas); a nadir R_N ~ 1. Predicción 'detección menos sensible': R_N < 1 ya a nadir y plano.
Instrumento: si el cenit estuviera mal pareado, la curva de MIROVA y la nuestra no compartirían eje; el pareo se
controló en descomp_osf2025_salida.txt (|Δcenit| mediana 0,07°). Denominador: pasadas clase 1 con >=1 píxel nuestro.
Uso: python -B cenit_fino.py pares_osf2025.csv
"""
import sys
import numpy as np, pandas as pd
d = pd.read_csv(sys.argv[1], parse_dates=["t"])
d = d[(d.pareo == "ok") & (d.b == "V375") & (d.cls == 1) & (d.n_all > 0)].copy()
d["pub_ok"] = d.pub_ok.astype(str) == "True"
f5 = d.f5.fillna(0); pc = d.pc_vrp.fillna(0)
d["pub"] = np.where(d.pub_ok, np.where(f5 > 0, f5, pc), 0.0)
d["dLM"] = d.Lhot_M - d.Lbk_M
d["tr"] = pd.cut(d.zen_M, [0, 10, 20, 30, 40, 50, 60, 75])
GR = {"puntual (Chaiten, Villarrica, Copahue, PP)": ["Chaiten", "Villarrica", "Copahue", "PlanchonPeteroa"],
      "extendido (Lascar, Isluga, Lastarria, PCC)": ["Lascar", "Isluga", "Lastarria", "PuyehueCordonCaulle"]}
for nom, vs in list(GR.items()) + [("TODOS", list(d.vol.unique()))]:
    g0 = d[d.vol.isin(vs)]
    print(f"\n{nom}")
    print("tramo | n | N_M med | n_o med | sum n_o/sum N_M | sum dL_o/sum dL_M | sum pub/sum VRP_M | Lhot_px_M med | Lhot_px_o med")
    for tr, g in g0.groupby("tr", observed=True):
        if len(g) < 8:
            continue
        print(f"{str(tr):9s} | {len(g):4d} | {g.N_M.median():.0f} | {g.n_all.median():.0f} | {g.n_all.sum()/g.N_M.sum():.3f} | "
              f"{g.dL_o.sum()/g.dLM.sum():.3f} | {g.pub.sum()/g.VRP_M.sum():.3f} | {(g.Lhot_M/g.N_M).median():.4f} | {(g.Lhot_o/g.n_all).median():.4f}")
    print(f"Spearman cenit vs N_M {g0.zen_M.corr(g0.N_M, method='spearman'):+.2f}; cenit vs n_o {g0.zen_M.corr(g0.n_all, method='spearman'):+.2f}")
