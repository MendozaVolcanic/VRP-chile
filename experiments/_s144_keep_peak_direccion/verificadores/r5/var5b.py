# Mas variantes para 2.541 / 1.824. Solo lectura.
import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from base5 import df, idx_v  # noqa

OBJ = {"Copahue": 287, "Villarrica": 248, "Llaima": 242, "NevadosDeChillan": 209, "Lastarria": 206,
       "PlanchonPeteroa": 160, "Chaiten": 158, "Tupungatito": 123, "Lascar": 81, "Isluga": 71,
       "PuyehueCordonCaulle": 39}

d = df.copy()
d["t"] = pd.to_datetime(d.dt, utc=True)
d["noche"] = d.t.dt.strftime("%Y-%m-%d")

# variante: "otra pasada" = otro RECORD nuestro de la misma noche con TIF pareado
print("== 'otra pasada' = otro record nuestro de la misma noche con TIF pareado ==")
for uni_name, uni in [("patron", d[d.patron]), ("patron+pub", d[d.patron & d.pub])]:
    n, pv = 0, {}
    for _, r in uni.iterrows():
        g = d[(d.vol == r["vol"]) & (d.noche == r["noche"]) & d.tif.notna()]
        gap = (g.t - r["t"]).abs().dt.total_seconds()
        if (gap >= 900).any():
            n += 1
            pv[r["vol"]] = pv.get(r["vol"], 0) + 1
    print("  %-12s n=%d -> %d  %s" % (uni_name, len(uni), n, dict(sorted(pv.items(), key=lambda x: -x[1]))))
    print("     dif vs S0:", {v: pv.get(v, 0) - OBJ[v] for v in OBJ})

# variante: universo = records de noches con >=2 records nuestros
print("\n== tamano de universo segun filtros ==")
cnt = d.groupby(["vol", "noche"]).size().rename("npas")
d2 = d.merge(cnt, on=["vol", "noche"])
print("  patron con >=2 records esa noche:", int((d2.patron & (d2.npas >= 2)).sum()))
print("  patron con TIF en el volcan (idx no vacio):", int(d.patron.sum()))
# records por noche
print("  distribucion de records por (vol,noche):", cnt.value_counts().sort_index().to_dict())
