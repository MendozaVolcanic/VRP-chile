# -*- coding: utf-8 -*-
"""S158: Npix, energía y fondo de MIROVA en VIIRS 375 contra el cenit, en Vulcano (OSF jepv6, Campus et al. 2024).

POR QUÉ: el código publicado por MIROVA es sólo de VIIRS 750. Para VIIRS 375 lo único con Npix y radiancias por
pasada es el dataset de Campus et al. 2024 (Bull. Volcanol. 86:25), OSF jepv6, archivo S1 (fecha, cenit, azimut,
Npix, L_MIRhot, L_MIRbk, VRP). Si el remuestreo de MIROVA reparte la huella oblicua en varias celdas, Npix debería
crecer con el cenit y la radiancia por celda bajar; si su VRP no depende del ángulo, el remuestreo compensa la huella.

Controles: (1) el coeficiente implícito VRP / (L_hot - L_bk) tiene que dar 18,0 x 140.625 m² = 2.531.250
(CLAUDE.md, calibración S14); (2) la energía se normaliza por la mediana móvil de 61 días de la propia serie, para
que la evolución del unrest no se confunda con el ángulo; (3) n por tramo siempre a la vista.
El archivo de jepv6 no declara licencia: no se copia al repo, se lee desde la ruta que se pase.
Uso: python -I jepv6_cenit.py <ruta a S1_MIROVA_Vulcano.csv>
"""
import sys

import numpy as np
import pandas as pd

df = pd.read_csv(sys.argv[1])
df.columns = ["fecha", "cenit", "azimut", "npix", "lhot", "lbk", "vrp_w"]
df["fecha"] = pd.to_datetime(df["fecha"], format="%d/%m/%y %H:%M")
df = df.sort_values("fecha").reset_index(drop=True)
dl = df["lhot"] - df["lbk"]
k = df["vrp_w"] / dl
print(f"alertas: {len(df)}, de {df.fecha.min():%Y-%m-%d} a {df.fecha.max():%Y-%m-%d}")
print(f"coeficiente implícito VRP/(Lhot-Lbk): mediana {k.median():,.0f}, p1 {k.quantile(.01):,.0f}, p99 {k.quantile(.99):,.0f} (esperado 2.531.250)")
print(f"¿L_MIRhot es suma sobre Npix? razón Lhot/Npix contra Lhot en pasadas de Npix=1 y >1 (medianas): "
      f"{df.loc[df.npix == 1, 'lhot'].median():.3f} / {df.loc[df.npix > 1, 'lhot'].median():.3f} / "
      f"{(df.loc[df.npix > 1, 'lhot'] / df.loc[df.npix > 1, 'npix']).median():.3f}")
s = df.set_index("fecha")["vrp_w"]
ref = s.rolling("61D", center=True, min_periods=5).median()
df["vrp_rel"] = (s / ref).values
df["dl_por_pix"] = dl / df["npix"]
cortes = [0, 20, 40, 50, 70]
df["tramo"] = pd.cut(df["cenit"], cortes, right=True)
print("\ntramo de cenit | n | Npix mediana | Npix media | fracción Npix=1 | VRP relativo mediano | (Lhot-Lbk)/Npix mediano")
for t, g in df.groupby("tramo", observed=True):
    print(f"{str(t):10s} | {len(g):3d} | {g.npix.median():4.1f} | {g.npix.mean():4.2f} | {(g.npix == 1).mean():5.2f} | "
          f"{np.nanmedian(g.vrp_rel):5.2f} | {g.dl_por_pix.median():.4f}")
rho = pd.Series(df["cenit"]).corr(df["npix"], method="spearman")
rho2 = pd.Series(df["cenit"]).corr(df["vrp_rel"], method="spearman")
print(f"\nSpearman cenit-Npix {rho:+.3f}; cenit-VRP relativo {rho2:+.3f} (n = {df.vrp_rel.notna().sum()})")

# Robustez: otras ventanas de normalización, por año y por lado del barrido (signo del azimut).
print("\nrobustez: VRP relativo mediano por tramo de cenit")
print("variante | (0,20] | (20,40] | (40,50] | (50,70] | Spearman")
for ventana in ("31D", "61D", "121D"):
    r = (s / s.rolling(ventana, center=True, min_periods=5).median()).values
    med = [np.nanmedian(r[(df.tramo == t).values]) for t in df.tramo.cat.categories]
    print(f"ventana {ventana:5s} | " + " | ".join(f"{m:5.2f}" for m in med)
          + f" | {pd.Series(df.cenit).corr(pd.Series(r), method='spearman'):+.3f}")
for anio, g in df.groupby(df.fecha.dt.year):
    med = [np.nanmedian(g.vrp_rel[g.tramo == t]) if (g.tramo == t).sum() >= 5 else np.nan for t in df.tramo.cat.categories]
    ns = [int((g.tramo == t).sum()) for t in df.tramo.cat.categories]
    print(f"año {anio}      | " + " | ".join(f"{m:5.2f}" for m in med) + f" | n por tramo {ns}")
for lado, g in df.groupby(np.where(df.azimut > 0, "azimut > 0", "azimut <= 0")):
    med = [np.nanmedian(g.vrp_rel[g.tramo == t]) if (g.tramo == t).sum() >= 5 else np.nan for t in df.tramo.cat.categories]
    print(f"{lado:11s} | " + " | ".join(f"{m:5.2f}" for m in med) + f" | n {len(g)}")
