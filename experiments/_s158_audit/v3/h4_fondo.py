# -*- coding: utf-8 -*-
"""V3, F3-H4: fondo por píxel de MIROVA (OSF v2.5 2025, Tot_Lmir_bk/Npix) contra el nuestro, VIIRS 375 clase 1.
Nuestro fondo por píxel = (ΣL_hot nuestro - ΣΔL nuestro)/n, reconstruido de los píxeles listados (BT -> Planck I04,
ΔL = vrp/kA). Sólo pasadas SIN recorte (ningún píxel con vrp=0), porque con recorte esa resta no es el fondo.
CONTROL de reconstrucción (P2): en volcanes sin kernel local, ese fondo debe ser igual a diag_L_bg_w_m2_sr_um
(fondo del anillo persistido). Si no lo es, mi fondo no es el del pipeline y la comparación no vale.
P1: si nuestro fondo fuera igual al de MIROVA, la razón saldría 1; se imprime por volcán con cuartiles.
Contrafactual: (ΣL_hot nuestro - n * fondo/px MIROVA) * kA / VRP_MIROVA, contra la razón actual ΣΔL*kA/VRP_M,
en pasadas con lista completa (incluye las con recorte: MIROVA no recorta por píxel).
"""
import sys, io
from pathlib import Path
import numpy as np, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
KA = 18.0 * 140625
d = pd.read_csv(Path(__file__).with_name("pares_osf2025_v3.csv"), parse_dates=["t"])
d = d[(d.pareo == "ok") & (d.b == "V375") & (d.cls == 1) & (d.n_all > 0) & (d.n_list == d.n_all)].copy()
d["bkM"] = d.Lbk_M / d.N_M
d["bko"] = (d.Lhot_o - d.dL_o) / d.n_all
d["R"] = d.dL_o * KA / 1e6 / d.VRP_M
d["Rcf"] = (d.Lhot_o - d.n_all * d.bkM) * KA / 1e6 / d.VRP_M
nc = d[d.n_clip == 0]
sk = nc[nc.Lbg_local.isna()]
rel = (sk.bko / sk.Lbg_ring - 1).abs()
print(f"CONTROL: pasadas sin recorte y sin kernel local: {len(sk)}; |fondo reconstruido/anillo persistido - 1|: mediana {rel.median():.5f}, p99 {rel.quantile(.99):.5f}")
kk = nc[nc.Lbg_local.notna()]
rel2 = (kk.bko / kk.Lbg_local - 1).abs()
print(f"         con kernel local: {len(kk)}; |fondo reconstruido/mediana local persistida - 1|: mediana {rel2.median():.4f} (no tiene por qué ser 0: la mediana no es la media)")
print("\nvolcán | kernel | n sin recorte | fondo MIROVA/nuestro por px: mediana [p25,p75] | n completas | ΣR actual | ΣR con fondo MIROVA | % pasadas con recorte")
for v, g in d.groupby("vol"):
    h = nc[nc.vol == v]
    ker = h.Lbg_local.notna().mean() if len(h) else np.nan
    q = (h.bkM / h.bko) if len(h) else pd.Series(dtype=float)
    print(f"{v:20s} | {ker:4.2f} | {len(h):4d} | {q.median():.3f} [{q.quantile(.25):.3f},{q.quantile(.75):.3f}] | {len(g):4d} | "
          f"{(g.dL_o.sum()*KA/1e6)/g.VRP_M.sum():.3f} | {((g.Lhot_o - g.n_all*g.bkM).sum()*KA/1e6)/g.VRP_M.sum():.3f} | {(g.n_clip>0).mean():.2%}")

print("\nCenit <= 40, sumas y medianas por pasada: ΣR | ΣR_cf | mediana R | mediana R_cf | n")
for v, g in d[d.zen_M <= 40].groupby("vol"):
    print(f"{v:20s} {(g.dL_o.sum()*KA/1e6)/g.VRP_M.sum():.3f} | {((g.Lhot_o - g.n_all*g.bkM).sum()*KA/1e6)/g.VRP_M.sum():.3f} | "
          f"{g.R.median():.3f} | {g.Rcf.median():.3f} | {len(g)}")
