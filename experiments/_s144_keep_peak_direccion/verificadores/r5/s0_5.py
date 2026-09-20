# Reproduccion exacta del conteo de S0: pasadas con patron que tienen pasada cruzada USABLE.
import os, sys, pickle
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
V3 = os.path.abspath(HERE + "/../v3"); V4 = os.path.abspath(HERE + "/../v4")
sys.path.insert(0, V3); sys.path.insert(0, V4); sys.path.insert(0, HERE)
from common3 import *  # noqa
from cruz5 import df, cruzada_de  # noqa
OBJ = {"Copahue":287,"Villarrica":248,"Llaima":242,"NevadosDeChillan":209,"Lastarria":206,
       "PlanchonPeteroa":160,"Chaiten":158,"Tupungatito":123,"Lascar":81,"Isluga":71,"PuyehueCordonCaulle":39}
for nom, sub in (("patron", df[df.patron]), ("patron+pub", df[df.patron & df.pub])):
    pv, n = {}, 0
    for vol, g in sub.groupby("vol"):
        for _, r in g.iterrows():
            cr, why = cruzada_de(vol, r["t"])
            if cr is not None:
                n += 1; pv[vol] = pv.get(vol, 0) + 1
        raster.cache_clear()
    print("%-12s universo=%d  con cruzada USABLE=%d" % (nom, len(sub), n))
    print("   por volcan:", dict(sorted(pv.items(), key=lambda x: -x[1])))
    print("   dif vs S0 :", {v: pv.get(v,0)-OBJ[v] for v in OBJ})
