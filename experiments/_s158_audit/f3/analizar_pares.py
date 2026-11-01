# -*- coding: utf-8 -*-
"""F3: lee pares_osf2025.csv (de descomp_osf2025.py) y parte la razón nuestra/MIROVA en factores físicos.

Factores (medianas por volcán, sensor y tramo de cenit; sólo pasadas pareadas con >=1 píxel nuestro y n_all<=100,
para que los píxeles listados sean todos los alertados):
  R_pub   = magnitud publicada nuestra / VRP MIROVA                         (lo que ve el operador)
  R_esc   = ΔL de TODOS nuestros alertados / ΔL MIROVA                      (sin selección)
  sel     = R_pub / R_esc                                                    (selección: cúmulo, F5', inner)
  R_N     = n nuestro / Npix MIROVA                                          (conteo)
  hot_px  = L_hot medio por píxel nuestro / el de MIROVA                     (cuán calientes son los elegidos)
  bk_px   = L_bk medio por píxel nuestro / el de MIROVA                      (fondo; sólo pasadas sin recorte)
  exc_px  = exceso medio por píxel nuestro / el de MIROVA
  R_cf    = (ΣL_hot nuestro - n * L_bk medio de MIROVA) / ΔL MIROVA         (nuestros píxeles con el fondo de MIROVA)
Identidad de control: R_esc = R_N * exc_px (se imprime el máximo error relativo; si no es ~0 la descomposición está rota).
Uso: python -B analizar_pares.py pares_osf2025.csv [sensor]
"""
import sys
import numpy as np
import pandas as pd

df = pd.read_csv(sys.argv[1], parse_dates=["t"])
SEN = sys.argv[2] if len(sys.argv) > 2 else "V375"
KA = {"V375": 18.0 * 140625, "V750": 19.7 * 562500, "MODIS": 18.9 * 1e6}[SEN]
CLS = int(sys.argv[3]) if len(sys.argv) > 3 else None   # clase del OSF: 1 = cerca del volcán (Max_Dist mediana 1,6 km), 0 = distal (21 km)
df["pub_ok"] = df.pub_ok.astype(str) == "True"
# magnitud publicada = mirovaEqVrpCore: F5' si > 0 (V375), si no el cúmulo; 0 si mirovaEqVrp da 0
pcv = df.pc_vrp.fillna(0)
f5v = df.f5.where(df.b == "V375")
df["pub_o"] = np.where(df.pub_ok, np.where(f5v.fillna(0) > 0, f5v.fillna(0), pcv), 0.0)
d = df[(df.pareo == "ok") & (df.b == SEN) & ((df.cls == CLS) if CLS is not None else True)].copy()
print("clase OSF:", CLS)
print(f"sensor {SEN}; pares {len(d)}; con >=1 píxel nuestro {int((d.n_all > 0).sum())}; con n_all>100 (top-100 incompleto) {int((d.n_all > 100).sum())}")
d = d[(d.n_all > 0) & (d.n_all <= 100) & (d.n_list == d.n_all)]
dLM = d.Lhot_M - d.Lbk_M
d["R_pub"] = d.pub_o / d.VRP_M
d["R_esc"] = d.dL_o / dLM
d["sel"] = d.R_pub / d.R_esc
d["R_N"] = d.n_all / d.N_M
d["hot_px"] = (d.Lhot_o / d.n_all) / (d.Lhot_M / d.N_M)
lbk_o = (d.Lhot_o - d.dL_o) / d.n_all
d["bk_px"] = np.where(d.n_clip == 0, lbk_o / (d.Lbk_M / d.N_M), np.nan)
d["exc_px"] = (d.dL_o / d.n_all) / (dLM / d.N_M)
d["R_cf"] = (d.Lhot_o - d.n_all * d.Lbk_M / d.N_M) / dLM
d["clipfrac"] = d.n_clip / d.n_all
err = np.nanmax(np.abs(d.R_esc - d.R_N * d.exc_px) / d.R_esc.abs().clip(lower=1e-9))
print(f"identidad R_esc = R_N*exc_px, error relativo máximo: {err:.2e}  (n={len(d)})")
d["tramo"] = pd.cut(d.zen_M, [0, 40, 75], labels=["<=40", ">40"])
cols = ["R_pub", "R_esc", "sel", "R_N", "hot_px", "bk_px", "exc_px", "R_cf", "clipfrac"]
TIPO = {"Villarrica": "lago de lava", "Lascar": "crater profundo", "PuyehueCordonCaulle": "lacolito difuso",
        "Llaima": "nevado debil", "Copahue": "nevado debil", "NevadosDeChillan": "nevado debil",
        "Isluga": "fumarolico alt.", "Lastarria": "fumarolico", "PlanchonPeteroa": "multi-crater", "Chaiten": "domo"}
pd.set_option("display.width", 250)
out = []
for (vol, tr), g in d.groupby(["vol", "tramo"], observed=True):
    if len(g) < 5:
        continue
    row = {"vol": vol, "tipo": TIPO.get(vol, ""), "tramo": tr, "n": len(g), "N_M_med": g.N_M.median(),
           "n_o_med": g.n_all.median(), "pub_ok%": round(100 * g.pub_ok.mean())}
    row.update({c: round(g[c].median(), 3) for c in cols})
    out.append(row)
for tr, g in d.groupby("tramo", observed=True):
    row = {"vol": "TODOS", "tipo": "", "tramo": tr, "n": len(g), "N_M_med": g.N_M.median(), "n_o_med": g.n_all.median(),
           "pub_ok%": round(100 * g.pub_ok.mean())}
    row.update({c: round(g[c].median(), 3) for c in cols})
    out.append(row)
print(pd.DataFrame(out).to_string(index=False))
print("\nrazón de SUMAS (no mediana de razones), por tramo: sum(pub_o)/sum(VRP_M), sum(dL_o)/sum(dL_M), sum(n)/sum(N_M); y mediana de R_pub sólo donde publicamos")
for tr, g in d.groupby("tramo", observed=True):
    p = g[g.pub_o > 0]
    print(f"  {tr}: n {len(g)}  sum_pub/sum_M {g.pub_o.sum() / g.VRP_M.sum():.3f}  sum_dL {g.dL_o.sum() / (g.Lhot_M - g.Lbk_M).sum():.3f}  sum_n {g.n_all.sum() / g.N_M.sum():.3f}  publicadas {len(p)}  R_pub|pub {p.R_pub.median():.3f}  sel|pub {p.sel.median():.3f}")
d.to_csv(sys.argv[1].replace(".csv", f"_{SEN}_factores.csv"), index=False)
