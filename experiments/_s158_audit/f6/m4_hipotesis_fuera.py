# -*- coding: utf-8 -*-
"""F6 M4: ¿de donde sale el VRP publicado en las filas V750 con cenit > 50 que no cumplen la identidad?
Hipotesis probadas, cada una con su control (las filas sanas):
 H1 el VRP de la fila de 375 m del mismo volcan y la misma hora;
 H2 un tope que depende del cenit (VRP maximo por banda de cenit);
 H3 una correccion multiplicativa por area de pixel (r = f(cenit) determinista).
Denominador: filas V750 con SatZen > 50 (34.250), OSF v2.5 2012-2025."""
import sys, io
import numpy as np, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
d = pd.read_pickle(sys.argv[1]); full = pd.read_csv(sys.argv[2])
K = 1.97e7 * 0.5625
d["dL"] = d.Tot_Lmir_hot - d.Tot_Lmir_bk
d["kdl"] = K * d.dL
d["r"] = d.VRP / d.kdl
d["fuera"] = (d.r - 1).abs() >= 1e-4
i375 = full[full.Resolution == 375][["IDvolc","timeUTC","VRP","Npix"]].rename(columns={"VRP":"VRP375","Npix":"Npix375"})
m = d.merge(i375, on=["IDvolc","timeUTC"], how="left")
for lab, sub in [("fuera", m[m.fuera]), ("sanas cenit>50", m[(~m.fuera)&(m.SatZen>50)])]:
    con = sub.VRP375.notna()
    q = (sub.VRP[con] / sub.VRP375[con])
    print(f"H1 {lab}: n={len(sub)} con fila 375 a la misma hora: {con.sum()}; VRP750/VRP375 mediana {q.median():.4f}, "
          f"|log10|<0.001: {(np.log10(q).abs()<0.001).sum()}")
# H3: r determinista con el cenit -> dispersion de r dentro de una banda de 1 grado
f = d[d.fuera].copy()
f["zb1"] = f.SatZen.round()
s = f.groupby("zb1").r.agg(["count","median","std","min","max"])
print("\nH3 r por grado de cenit (fuera):"); print(s.to_string())
# H2: ¿el VRP publicado tiene un techo por banda de cenit? comparar el VRP publicado max en sanas y fuera
d["zb"] = pd.cut(d.SatZen, [50,55,60,65,70])
print("\nH2 VRP publicado (MW) por cenit, sanas vs fuera:")
print(d[d.SatZen>50].groupby(["zb","fuera"], observed=True).VRP.describe(percentiles=[.5,.9,.99]).div(1e6).round(1).to_string())
# Relacion VRP_pub con k*dL: ¿VRP_pub = g(k*dL)? correlacion log-log en fuera
x, y = np.log10(f.kdl), np.log10(f.VRP)
print("\nfuera: pendiente log VRP_pub vs log k*dL:", np.polyfit(x, y, 1).round(3), " corr", np.corrcoef(x,y)[0,1].round(3))
# ¿Npix publicado mayor que el que daria un pixel nativo? Lhot/Npix en fuera vs sanas a igual cenit
z = d[d.SatZen>50]
print("\nLhot/Npix mediana: fuera", (z.Tot_Lmir_hot/z.Npix)[z.fuera].median().round(3), " sanas", (z.Tot_Lmir_hot/z.Npix)[~z.fuera].median().round(3))
print("Max_Dist mediana (m): fuera", z.Max_Dist[z.fuera].median(), " sanas", z.Max_Dist[~z.fuera].median())
