# Verificador v5 S144: pool + disponibilidad de pasada cruzada. Solo lectura.
import os, sys, math, pickle, time
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
V3 = os.path.abspath(HERE + "/../v3")
V4 = os.path.abspath(HERE + "/../v4")
sys.path.insert(0, V3); sys.path.insert(0, V4)
from common3 import *  # noqa
import base4 as B  # noqa

df = B.df
geomP = B.geomP
idx = B.idx                     # indice TIF VIIRS375 (ya filtrado: size>0, acq no nula, existe)
idx_v = B.idx_v

if __name__ == "__main__":
    print("== horas UTC de las pasadas (definicion de 'noche') ==")
    h = pd.to_datetime(df.dt, utc=True).dt.hour
    print(h.value_counts().sort_index().to_dict())

    print("\n== conteos del embudo ==")
    print("  records nocturnos V375:", len(df))
    print("  con patron:", int(df.patron.sum()))
    print("  con patron y publicados:", int((df.patron & df.pub).sum()))
    print("  patron por volcan:", df[df.patron].vol.value_counts().to_dict())
    print("  patron+pub por volcan:", df[df.patron & df.pub].vol.value_counts().to_dict())

    # --- S0: "de 2.541 pasadas con el patron, 1.824 tienen otra pasada esa noche con TIF"
    print("\n== S0: otra pasada de la misma noche con TIF (SIN filtro de usabilidad ni de 15 min) ==")
    for etiqueta, sub in [("patron", df[df.patron]), ("patron+pub", df[df.patron & df.pub])]:
        n_ok, por_vol = 0, {}
        for _, r in sub.iterrows():
            g = idx_v.get(r["vol"])
            if g is None:
                continue
            t = pd.Timestamp(r["dt"])
            noche = t.strftime("%Y-%m-%d")
            m = (g.acquisition_utc.dt.strftime("%Y-%m-%d") == noche) & \
                ((g.acquisition_utc - t).abs().dt.total_seconds() > 120)
            if m.any():
                n_ok += 1
                por_vol[r["vol"]] = por_vol.get(r["vol"], 0) + 1
        print("  %-12s n=%d  con otra pasada esa noche: %d" % (etiqueta, len(sub), n_ok))
        print("     por volcan:", dict(sorted(por_vol.items(), key=lambda x: -x[1])))
