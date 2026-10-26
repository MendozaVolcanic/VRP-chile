# -*- coding: utf-8 -*-
"""F3: cuando MIROVA alerta N_M = 2 o 3 píxeles y nosotros 1, ¿sus píxeles son el MISMO foco repartido (remuestreo) o
anomalías adicionales (detección más sensible)? Usa mismo_k_filas.csv (pares OSF 2025, clase 1).
Con el fondo por píxel de MIROVA (L_bk_M / N_M) aplicado a nuestro único píxel:
  r_tot = exceso total de MIROVA / exceso de nuestro píxel
  r_px  = exceso medio por píxel de MIROVA / exceso de nuestro píxel
Predicciones: REPARTO conservativo (interpolación lineal de un foco sobre 2-3 celdas): r_tot ~ 1 (o algo más, el
sintético de D17 da 1,40 a nadir), r_px ~ 1/N_M. DUPLICADO (vecino más cercano): r_px ~ 1, r_tot ~ N_M.
ANOMALÍAS EXTRA más débiles: r_tot > 1 creciendo con N_M, r_px entre 1/N_M y 1.
Control positivo: N_M = 1 y n = 1 debe dar r_tot ~ r_px ~ 1 (mismo píxel). Ventana: 2025, noche, V375, cenit <= 30.
Uso: python -B reparto_foco.py mismo_k_filas.csv
"""
import sys
import numpy as np, pandas as pd
D = pd.read_csv(sys.argv[1])
D = D[(D.b == "V375") & (D.zen <= 30) & (D.n_o == 1)].copy()
ex_o = D.top1_o - D.Lbk_px_M
D = D[ex_o > 0]
ex_o = D.top1_o - D.Lbk_px_M
D["r_tot"] = (D.Lhot_px_M - D.Lbk_px_M) * D.N_M / ex_o
D["r_px"] = (D.Lhot_px_M - D.Lbk_px_M) / ex_o
for k in [1, 2, 3, 4]:
    g = D[D.N_M == k] if k < 4 else D[D.N_M >= 4]
    if len(g):
        print(f"N_M {'>=4' if k == 4 else k}: n {len(g)}  r_tot mediana {g.r_tot.median():.3f} [p25 {g.r_tot.quantile(.25):.3f}, p75 {g.r_tot.quantile(.75):.3f}]  "
              f"r_px mediana {g.r_px.median():.3f}  (1/N_M = {1 / max(k, 1):.3f})  volcanes {g.vol.value_counts().to_dict()}")
