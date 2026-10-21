# -*- coding: utf-8 -*-
"""F3, control del instrumento: el L_bk por píxel que reconstruyo (Planck(bt_k, λ) - ΔL, con ΔL = vrp_px / (k*A)) tiene
que coincidir con el fondo de anillo persistido (diag_L_bg_w_m2_sr_um) en los volcanes SIN kernel local y sin recorte.
Si no coincide, la λ o el k*A que uso no son los del pipeline y los factores hot_px / bk_px de ese sensor no valen.
Uso: python -B control_reconstruccion.py pares_osf2025.csv
"""
import sys
import numpy as np, pandas as pd
d = pd.read_csv(sys.argv[1])
d = d[(d.pareo == "ok") & (d.n_all > 0) & (d.n_all == d.n_list) & (d.n_clip == 0) & d.Lbg_local.isna() & d.Lbg_ring.notna()]
d["lbk_rec"] = (d.Lhot_o - d.dL_o) / d.n_all
d["q"] = d.lbk_rec / d.Lbg_ring
print(d.groupby("b").q.describe(percentiles=[.05, .5, .95]).round(4).to_string())
