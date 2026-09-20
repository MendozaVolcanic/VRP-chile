# Variantes para reproducir el "2.541 con patron / 1.824 con pasada cruzada" de S0. Solo lectura.
import os, sys, pickle
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from base5 import df, idx_v, VOLS  # noqa

OBJ = {"Copahue": 287, "Villarrica": 248, "Llaima": 242, "NevadosDeChillan": 209, "Lastarria": 206,
       "PlanchonPeteroa": 160, "Chaiten": 158, "Tupungatito": 123, "Lascar": 81, "Isluga": 71,
       "PuyehueCordonCaulle": 39}
print("objetivo S0: total %d" % sum(OBJ.values()))

print("\n== variantes de universo 'pasadas con el patron' ==")
cands = {
    "patron": df[df.patron],
    "patron+pub": df[df.patron & df.pub],
    "patron+TIF(+-120s)": df[df.patron & df.tif.notna()],
    "patron+pub+TIF": df[df.patron & df.pub & df.tif.notna()],
    "patron+TIF propio": df[df.patron & df.tif.notna() & (df.own == True)],
}
for k, v in cands.items():
    print("  %-22s %d" % (k, len(v)))

def cruzada(sub, mingap_s):
    por_vol, n = {}, 0
    for _, r in sub.iterrows():
        g = idx_v.get(r["vol"])
        if g is None:
            continue
        t = pd.Timestamp(r["dt"])
        m = (g.acquisition_utc.dt.strftime("%Y-%m-%d") == t.strftime("%Y-%m-%d")) & \
            ((g.acquisition_utc - t).abs().dt.total_seconds() >= mingap_s)
        if m.any():
            n += 1
            por_vol[r["vol"]] = por_vol.get(r["vol"], 0) + 1
    return n, por_vol

for k, v in cands.items():
    for gap in (900,):
        n, pv = cruzada(v, gap)
        dif = {vv: pv.get(vv, 0) - OBJ.get(vv, 0) for vv in OBJ}
        print("\n  %-22s gap>=%ds -> %d   por vol: %s" % (k, gap, n, dict(sorted(pv.items(), key=lambda x: -x[1]))))
        print("      dif vs S0:", dif)
